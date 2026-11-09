"""L4_ConsolShort v14.10（10/5 上架定案版）—— 組裝檔。

規則全部在 `txfcore/modules/`，參數在 `config/strategies/L4_v14.10.toml`。
考題：`tests/test_port_l4_v14_10.py`（T8 報表 135 列逐列相同）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.config.loader import load_strategy
from txfcore.indicators.core import avg_true_range
from txfcore.modules.exits.core import (
    box_break_exit_short, breakeven_floor_short, forced_exit, retain_floor_short,
    time_exit_raw, tp1_price_short,
)
from txfcore.modules.gates.basic import Cooldown, calendar_flags, in_window, is_killed
from txfcore.modules.gates.loss_streak import StreakSkip
from txfcore.modules.gates.trend_filter import DailyMaBlock, below_ma
from txfcore.modules.signals.core import CloseInvalidatedBox, TrapZone, spring_trigger
from txfcore.modules.stops.core import cap_short, engine_stop_distance, ratchet_lowest_low_short
from txfcore.strategies.base import (
    PerSessionState, PerTradeState, Strategy, StrategyConfig, StrategyState,
)
from txfcore.types.orders import (
    Decision, MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side,
)

STRATEGY_NAME = "L4_ConsolShort"
VERSION = "v14.10"
CONFIG = load_strategy("L4_v14.10")
DEFAULT_PARAMS: dict = CONFIG["params"]
FLAT_STOP = 999999.0
MAX_BARS_BACK = 100      # 圖表設定：每個資料序列 ≥ 100 根才開始計算


@dataclass(slots=True)
class L4PerTrade(PerTradeState):
    def reset(self) -> None:
        pass


@dataclass(slots=True)
class L4PerSession(PerSessionState):
    daily: DailyMaBlock = field(default_factory=DailyMaBlock)
    box: CloseInvalidatedBox = field(default_factory=CloseInvalidatedBox)
    trap: TrapZone = field(default_factory=TrapZone)
    cooldown: Cooldown = field(default_factory=Cooldown)
    streak: StreakSkip = field(default_factory=StreakSkip)
    locked_top: float = 0.0
    locked_btm: float = 0.0
    lowest_low: float = 999999.0
    trail: bool = False
    sl_locked: bool = False
    frozen_atr: float = 0.0
    frozen_top: float = 0.0
    stop_level: float = FLAT_STOP
    peak: float = 0.0
    be_armed: bool = False
    sp_armed: bool = False
    tp1_px: float = 0.0
    tp1_done: bool = False


class L4ConsolShortV1410(Strategy[L4PerTrade, L4PerSession]):
    """15 分執行、60 分箱體、日線趨勢封鎖、純空、IOG 關、2 口。"""

    def __init__(self, config: StrategyConfig | None = None, static_settlement: bool = True) -> None:
        # True ＝ .pla 靜態結算日（對 MC）；實盤改 False，用資料推得的結算日（含遞延）
        self.static_settlement = static_settlement
        cfg = config or StrategyConfig(name=STRATEGY_NAME, instrument="TXF",
                                       holiday_flat_time=415, params=dict(DEFAULT_PARAMS))
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)

    def initial_state(self):
        return StrategyState(per_trade=L4PerTrade(), per_session=L4PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        return (135, 135)

    def on_bar(self, view, state):
        p, ps = self.config.params, state.per_session
        d1, d2, d3, pos, d = view.data1, view.data2, view.data3, view.position, Decision()
        if d2 is None or d3 is None or len(d2) < MAX_BARS_BACK or len(d3) < MAX_BARS_BACK:
            state.prev_market_position = pos.market_position
            return state, d
        t, dte = view.mc_time, view.mc_date
        flat = pos.market_position is MarketPosition.FLAT
        short = pos.market_position is MarketPosition.SHORT
        close = d1.close[0]

        # 188–269 行事曆、Kill、深夜封鎖、日線封鎖、60 分箱與趨勢
        holiday, registry_expired, settle = calendar_flags(dte, t, p["Registry_Valid_Until"],
                                                       self.static_settlement)
        kill = is_killed(p["Manual_Kill_Switch"], self.config.mc_manual_kill_switch)
        night = bool(p["Night_Block_On"]) and in_window(t, 200, 500)
        macro_block = ps.daily.update(d3.close, p["Daily_FastMA_Len"], p["Daily_SlowMA_Len"],
                                      p["Macro_Mode"])
        trend_down = below_ma(d2.close, p["Weekly_MA_Len"])
        ps.box.update(d2, p["Lookback_Bars"], p["Range_Shrink_Rate"])
        atr = avg_true_range(d1, p["ATR_Length"])

        # 278–304 R1 連虧跳過（預設關）、冷卻
        ps.streak.update(flat, pos.total_trades, pos.net_profit, dte,
                         p["Streak_Skip_N"], p["State_Start_Date"])
        cool = ps.cooldown.update(flat, state.prev_market_position is MarketPosition.FLAT)

        # 306–353 箱內：誘多區、引擎停損、S_Spring 進場
        if ps.box.valid:
            ps.trap.update(d1.high[0], ps.box.top, p["Time_Limit_Bars"])
            if not short:
                g = engine_stop_distance(ps.box.top + atr * p["ATR_Stop_Mult"], close,
                                         p["SL_Pct"], p["SL_Max_Pts"])
                d.protective = ProtectiveStop(strategy=STRATEGY_NAME, distance=g,
                                              per_contract=True, signal_date=dte, signal_time=t)
            if (flat and cool >= p["Cooldown_Bars"] and trend_down and not macro_block
                    and ps.trap.active
                    and spring_trigger(close, ps.box.top, atr, p["i_Buffer_ATR_Mult"])
                    and not holiday and not night and not settle and not kill):
                if not ps.streak.consume():
                    self._order(d, state, view, "CS_Entry", Side.SELL_SHORT)
                ps.trap.active = False

        # 357–376 空手：鎖箱、重置
        if flat:
            if ps.box.active:
                ps.locked_top, ps.locked_btm = ps.box.top, ps.box.btm
            ps.lowest_low, ps.stop_level = 999999.0, FLAT_STOP
            ps.trail = ps.sl_locked = ps.be_armed = ps.sp_armed = ps.tp1_done = False
            ps.frozen_atr = ps.frozen_top = ps.peak = ps.tp1_px = 0.0

        # 378–508 持倉管理與出場鏈
        if short:
            self._manage_and_exit(view, state, d, p, atr, close, kill,
                                  registry_expired, holiday, settle)

        state.prev_market_position = pos.market_position
        return state, d

    def _manage_and_exit(self, view, state, d, p, atr, close, kill,
                         registry_expired, holiday, settle) -> None:
        ps, pos, t = state.per_session, view.position, view.mc_time
        entry = pos.entry_price
        ps.lowest_low = min(ps.lowest_low, view.data1.low[0])
        if ps.lowest_low <= ps.locked_btm:
            ps.trail = True
        if p["Freeze_SL_On"] and not ps.sl_locked:
            ps.frozen_atr, ps.frozen_top, ps.sl_locked = atr, ps.locked_top, True
        if ps.trail:
            ps.stop_level = ratchet_lowest_low_short(ps.stop_level, ps.lowest_low, atr,
                                                     p["Trail_ATR_Mult"])
        elif p["Freeze_SL_On"]:
            ps.stop_level = ps.frozen_top + p["ATR_Stop_Mult"] * ps.frozen_atr
        else:
            ps.stop_level = ps.locked_top + p["ATR_Stop_Mult"] * atr
            if 0 < ps.box.top < ps.locked_top:
                ps.locked_top = ps.box.top
        ps.stop_level = cap_short(ps.stop_level, entry, p["SL_Pct"], p["SL_Max_Pts"])

        ps.peak = max(ps.peak, entry - close)
        if ps.tp1_px == 0:
            ps.tp1_px = tp1_price_short(entry, ps.locked_btm, p["TP1_Room_Pct"])
        if pos.max_contracts > 1 and pos.current_contracts < pos.max_contracts:
            ps.tp1_done = True
        if (p["TP1_BE_On"] and ps.tp1_done) or (p["BE_Trigger_Pts"] > 0 and ps.peak >= p["BE_Trigger_Pts"]):
            ps.be_armed = True
        if p["SP_Trigger_Pts"] > 0 and ps.peak >= p["SP_Trigger_Pts"]:
            ps.sp_armed = True
        be_floor = breakeven_floor_short(entry, p["BE_Offset_Pts"]) if ps.be_armed else 0.0
        sp_floor = retain_floor_short(entry, ps.peak, p["SP_Retain_Pct"]) if ps.sp_armed else 0.0

        cover = lambda lbl, px=None, ot=OrderType.STOP, qty=None: self._order(
            d, state, view, lbl, Side.BUY_TO_COVER, px, ot, qty)
        lbl = forced_exit("CS", kill, registry_expired, holiday, settle, t,
                          p["Holiday_Flat_Time"], p["Settlement_Flat_Time"])
        if lbl:
            return cover(lbl)
        if box_break_exit_short(ps.box.active, view.data2.close[0], ps.locked_top):
            return cover("CS_BreakExit")
        if not ps.trail and time_exit_raw(pos.bars_since_entry, p["Time_Stop_Bars"]):
            return cover("CS_TimeExit")
        if (p["TP1_Room_Pct"] > 0 and ps.tp1_px > 0 and not ps.tp1_done
                and pos.max_contracts > 1 and pos.current_contracts == pos.max_contracts):
            cover("CS_TP1", ps.tp1_px, OrderType.LIMIT, 1)
        eff = ps.stop_level
        if ps.sp_armed and 0 < sp_floor < eff:
            cover("CS_SP", sp_floor)
        elif ps.be_armed and 0 < be_floor < eff:
            cover("CS_BE", be_floor)
        else:
            cover("CS_SL", eff)

    def _order(self, d, state, view, label, side, price=None, order_type=None, qty=None) -> None:
        ot = OrderType.MARKET if price is None else (order_type or OrderType.STOP)
        d.add(OrderIntent(strategy=STRATEGY_NAME, label=label, side=side, order_type=ot,
                          price=price, exit_quantity=qty, signal_date=view.mc_date,
                          signal_time=view.mc_time, seq=state.next_seq()))
