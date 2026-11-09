"""L2_TrendShort v5.11（10/5 上架定案版）—— 組裝檔。

規則全部在 `txfcore/modules/`，參數在 `config/strategies/L2_v5.11.toml`。
本檔只決定「用哪些模組、什麼順序」，順序與 .pla 一致（行號標在每段）。
考題：`tests/test_port_l2_v5_11.py`（MC v5.10 報表 96 筆逐筆相同）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.config.loader import load_strategy
from txfcore.indicators.core import avg_true_range, lowest
from txfcore.modules.exits.core import (
    PeakGivebackShort, forced_exit, retrace_tp_short, structure_tp_short,
    time_exit, weekly_exit_short,
)
from txfcore.modules.gates.basic import calendar_flags, in_closed_window, is_killed
from txfcore.modules.gates.loss_streak import SkipNextRun
from txfcore.modules.gates.trend_filter import WeeklySmaFilter
from txfcore.modules.signals.core import CrashLeg, Zlema, channel_breakdown
from txfcore.modules.stops.core import (
    LowestCloseTrail, TwoBarArm, accel_newlow_bar, cap_short, engine_stop_distance,
    hard_stop_short, initial_stop_short, ratchet_lowest_low_short,
)
from txfcore.strategies.base import (
    PerSessionState, PerTradeState, Strategy, StrategyConfig, StrategyState,
)
from txfcore.types.orders import (
    Decision, MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side,
)

STRATEGY_NAME = "L2_TrendShort"
VERSION = "v5.11"
CONFIG = load_strategy("L2_v5.11")
DEFAULT_PARAMS: dict = CONFIG["params"]
POS_CRASH, POS_BEAR = 1, 2


@dataclass(slots=True)
class L2PerTrade(PerTradeState):
    def reset(self) -> None:        # 狀態在 session，空手時由組裝檔依 .pla 重置
        pass


@dataclass(slots=True)
class L2PerSession(PerSessionState):
    bar_no: int = 0
    wk: WeeklySmaFilter = field(default_factory=lambda: WeeklySmaFilter(13))
    zl: Zlema = field(default_factory=Zlema)
    skip: SkipNextRun = field(default_factory=SkipNextRun)
    crash: CrashLeg = field(default_factory=CrashLeg)
    arm: TwoBarArm = field(default_factory=TwoBarArm)
    trail: LowestCloseTrail = field(default_factory=LowestCloseTrail)
    pg: PeakGivebackShort = field(default_factory=PeakGivebackShort)
    sl_trig: float = 0.0
    sl_locked: bool = False
    active_sl: float = 0.0
    sl_src: int = 0
    lowest_close: float = 0.0
    ttp_fire: bool = False
    crash_ll: float = 0.0
    crash_stop: float = 0.0
    pend_type: int = 0
    pend_bar: int = 0
    pos_type: int = 0


class L2TrendShortV511(Strategy[L2PerTrade, L2PerSession]):
    """60 分單一資料流、純空、IOG 關。"""

    def __init__(self, config: StrategyConfig | None = None, static_settlement: bool = True) -> None:
        # True ＝ .pla 靜態結算日（對 MC）；實盤改 False，用資料推得的結算日（含遞延）
        self.static_settlement = static_settlement
        cfg = config or StrategyConfig(name=STRATEGY_NAME, instrument="TXF",
                                       holiday_flat_time=300, params=dict(DEFAULT_PARAMS))
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)

    def initial_state(self):
        s = StrategyState(per_trade=L2PerTrade(), per_session=L2PerSession())
        s.per_session.wk = WeeklySmaFilter(int(self.config.params["WkSMA_Len"]))
        return s

    def expected_trigger_range(self) -> tuple[int, int]:
        return (96, 96)

    def on_bar(self, view, state):
        p, ps = self.config.params, state.per_session
        bars, pos, d = view.data1, view.position, Decision()
        ps.bar_no += 1
        t, dte = view.mc_time, view.mc_date
        close, open_, high, low = bars.close[0], bars.open[0], bars.high[0], bars.low[0]
        short = pos.market_position is MarketPosition.SHORT
        flat = pos.market_position is MarketPosition.FLAT
        entry, bse = pos.entry_price, pos.bars_since_entry

        # 197–312 時段、行事曆、Kill
        is_day = in_closed_window(t, 845, 1245)
        holiday, registry_expired, settle = calendar_flags(dte, t, p["Registry_Valid_Until"],
                                                       self.static_settlement)
        kill = is_killed(p["Manual_Kill_Switch"], self.config.mc_manual_kill_switch)
        gates_ok = not holiday and not settle and not kill

        # 329–372 週線濾網、指標
        ps.wk.update(bars)
        atr = avg_true_range(bars, p["ATR_Len"])
        dc_lower = lowest(bars.low, p["DC_Len"], offset=1)
        ps.zl.update(bars.close, p["ZLEMA_Len"], p["ZLEMA_Lag"])

        # 376–406 部位類型、連虧計數（只算空頭單）、舊版暫停
        if ps.pend_bar > 0 and ps.pend_bar == ps.bar_no - 1:
            ps.pos_type = ps.pend_type
        ps.skip.count(pos.total_trades, pos.net_profit, ps.pos_type != POS_CRASH,
                      p["Bear_Pause_N"], p["Pause_Mode"], p["Skip_K"], ps.bar_no)
        ps.skip.release_pause(ps.wk.ok, p["Bear_Pause_Bars"], ps.bar_no)

        # 409–449 空頭訊號
        bear_sig = ((ps.wk.ok or p["Wk_Entry_Filter"] == 0)
                    and channel_breakdown(close, dc_lower, atr, p["C0_ATR_Filter"])
                    and ps.zl.falling and ps.zl.below_ema)
        allowed = ps.skip.allow(bear_sig, gates_ok, flat)   # 每根都要呼叫（無訊號時重置跳過段）
        bear_entry = bear_sig and gates_ok and flat and allowed

        # 452–487 暴跌腿
        ps.crash.update_leg(high, ps.bar_no, p["Crash_Leg_Reset_Bars"])
        crash_fire = ps.crash.check(
            p["Crash_On"] != 0 and flat and not ps.wk.ok and not bear_sig and gates_ok,
            close, open_, atr, bars.high, p["Crash_Lookback"], p["Crash_Drop_Pct"],
            p["Crash_Body_ATR"], p["Crash_ATRPct_Min"], p["Crash_SL_Pct"],
            p["SL_Max_Pts"], p["Crash_Leg_Max"], ps.bar_no)

        # 491–513 引擎停損距離、進場（空頭優先）
        if not short:
            g = engine_stop_distance(dc_lower + atr * p["SL_ATR_Ratio"], close,
                                     p["SL_Pct"], p["SL_Max_Pts"])
            if crash_fire:
                g = ps.crash.dist
            d.protective = ProtectiveStop(strategy=STRATEGY_NAME, distance=g, per_contract=True,
                                          signal_date=dte, signal_time=t)
        if bear_entry:
            self._order(d, state, view, "TS_Entry", Side.SELL_SHORT)
            ps.pend_type, ps.pend_bar = POS_BEAR, ps.bar_no
        elif crash_fire:
            self._order(d, state, view, "CR_Entry", Side.SELL_SHORT)
            ps.pend_type, ps.pend_bar = POS_CRASH, ps.bar_no

        # 517–612 初始停損、追蹤停損啟動與追蹤、450 上限
        if short:
            if bse == 0 and not ps.sl_locked:
                ps.sl_trig = initial_stop_short(dc_lower, atr, p["SL_ATR_Ratio"], entry,
                                                p["SL_Pct"], p["SL_Max_Pts"])
                ps.sl_locked = True
            ps.arm.update(accel_newlow_bar(open_, close, atr, p["Accel_M"], bars.close, p["NLow_N"]),
                          bse, p["MinBars"])
            ps.active_sl, ps.sl_src = ps.trail.active_stop(
                ps.arm.armed, bars.close, p["TSL_K"], p["TSL_M"], atr, p["SL_ATR_Ratio"], ps.sl_trig)
            if ps.active_sl > 0:
                ps.active_sl = cap_short(ps.active_sl, entry, 0, p["SL_Max_Pts"])
        else:
            ps.sl_trig, ps.sl_locked = 0.0, False
            ps.arm.reset()
            ps.trail.reset()
            ps.active_sl, ps.sl_src = 0.0, 0

        # 615–664 回抽停利、峰值回吐
        if short:
            ps.lowest_close = close if bse == 0 else min(ps.lowest_close, close)
            ps.ttp_fire = retrace_tp_short(entry, ps.lowest_close, close, atr,
                                           p["TTP_MinAtr"], p["TTP_RebPct"])
        else:
            ps.lowest_close, ps.ttp_fire = 0.0, False
        if flat:
            ps.pg.reset()
        if short:
            thr = entry * p["SP_Pct"] / 100 if p["SP_Pct"] > 0 else p["stopProfitPoints_Shrt"]
            ps.pg.update(entry, close, thr, p["profitReturnPrcnt_Shrt"])

        # 667–674 暴跌單停損
        if short and ps.pos_type == POS_CRASH:
            if bse == 0:
                ps.crash_ll, ps.crash_stop = low, entry + ps.crash.dist
            else:
                ps.crash_ll = min(ps.crash_ll, low)
            ps.crash_stop = ratchet_lowest_low_short(ps.crash_stop, ps.crash_ll, atr,
                                                     p["Crash_Trail_ATR"])

        # 679–777 出場鏈
        if short:
            self._exits(view, state, d, p, kill, registry_expired, holiday, settle,
                        is_day, close, entry, bse)

        state.prev_market_position = pos.market_position
        return state, d

    def _exits(self, view, state, d, p, kill, registry_expired, holiday, settle,
               is_day, close, entry, bse) -> None:
        ps, t = state.per_session, view.mc_time
        cover = lambda lbl, px=None: self._order(d, state, view, lbl, Side.BUY_TO_COVER, px)
        lbl = forced_exit("TS", kill, registry_expired, holiday, settle, t,
                          p["Holiday_Flat_Time"], p["Settlement_Flat_Time"])
        fired = lbl is not None
        if fired:
            cover(lbl)
        if ps.pos_type == POS_CRASH:
            if not fired:
                if time_exit(bse, p["Crash_Time_Bars"]):
                    cover("CR_Time")
                else:
                    cover("CR_Stop", ps.crash_stop)
            fired = True
        if not fired:
            if weekly_exit_short(p["Wk_Exit_On"] != 0, view.mc_date, t, close,
                                 ps.wk.ready, ps.wk.sma if ps.wk.ready else 0.0):
                cover("TS_WeeklyExit")
            elif structure_tp_short(close, view.data1.close, p["TP_N"]):
                cover("TS_StructureTP")
            elif ps.ttp_fire:
                cover("TS_TTP")
            elif ps.pg.price > 0:
                cover("TS_StopProfit", ps.pg.price)
            elif is_day and ps.active_sl > 0:
                cover("TS_TSL_D" if ps.sl_src == 1 else "TS_InitSL_D", ps.active_sl)
            elif not is_day and ps.active_sl > 0 and close > ps.active_sl:
                cover("TS_TSL_N" if ps.sl_src == 1 else "TS_InitSL_N")
        if p["Hard_Stop_On"] != 0 and p["SL_Max_Pts"] > 0:          # 鏈外，每根都掛
            cover("TS_HardSL", hard_stop_short(entry, p["SL_Max_Pts"]))

    def _order(self, d, state, view, label, side, price=None) -> None:
        d.add(OrderIntent(strategy=STRATEGY_NAME, label=label, side=side,
                          order_type=OrderType.MARKET if price is None else OrderType.STOP,
                          price=price, signal_date=view.mc_date, signal_time=view.mc_time,
                          seq=state.next_seq()))
