"""L5_BreakoutLong —— 移植自 `_Research_L5_v19_9_R1_BreakoutLong`。

行為等同 live v19.9（R1 只加 Print 與三個計數器，**不發任何單**）。

規格表：`docs/specs/L5_BreakoutLong_spec.md`

**部位模型最複雜的一支**：雙腿進場、40% 分批出場、28 處 `from Entry` 綁定。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.indicators.core import average, avg_true_range, highest, lowest
from txfcore.instruments.spec import get as get_instrument
from txfcore.strategies.base import (
    MarketView, Mode, PerSessionState, PerTradeState, Strategy,
    StrategyConfig, StrategyState,
)
from txfcore.types.mctime import DayOfWeek, day_of_week
from txfcore.types.orders import (
    Decision, MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side,
)

STRATEGY_NAME = "L5_BreakoutLong"
BOT, MID = "BL_Entry_Bot", "BL_Entry_Mid"

# **標籤寫成顯式常數，不用 f-string 組。**
#
# 2026-09-07 稽核發現：原本用 f"BL_TP_{sfx}" 組字串，於是 .pla 裡的
# 24 個標籤在 Python 裡一個都 grep 不到——**打錯前綴不會有任何檢查抓得到**。
# 現在每個標籤都是字面值，`tools/audit_port.py` 才能逐一比對。
LABELS: dict[str, tuple[str, str]] = {
    "BL_Kill":        ("BL_Kill_Bot",        "BL_Kill_Mid"),
    "BL_RegistryEnd": ("BL_RegistryEnd_Bot", "BL_RegistryEnd_Mid"),
    "BL_Holiday":     ("BL_Holiday_Bot",     "BL_Holiday_Mid"),
    "BL_Settlement":  ("BL_Settlement_Bot",  "BL_Settlement_Mid"),
    "BL_TP":          ("BL_TP_Bot",          "BL_TP_Mid"),
    "BL_SP":          ("BL_SP_Bot",          "BL_SP_Mid"),
    "BL_SL":          ("BL_SL_Bot",          "BL_SL_Mid"),
    "BL_TimeExit":    ("BL_TimeExit_Bot",    "BL_TimeExit_Mid"),
    "BL_Trail":       ("BL_Trail_Bot",       "BL_Trail_Mid"),
    "BL_BE":          ("BL_BE_Bot",          "BL_BE_Mid"),
    "BL_BreakExit":   ("BL_BreakExit_Bot",   "BL_BreakExit_Mid"),
}
LEGS = ((BOT, 0), (MID, 1))     # (進場標籤, LABELS 的索引)

DEFAULT_PARAMS: dict = {
    # Data2 = **Daily**（L3/L4 是 60M）
    "Lookback_Bars": 4,
    "Range_Shrink_Rate": 0.6,
    "Daily_MA_Len": 60,
    "Min_RR_Bull": 1.1,
    # 風險
    "ATR_Length": 35,
    "ATR_Stop_Mult": 4.5,
    "FrontRun_Ticks": 5,
    "Time_Stop_Bars": 31,
    "SL_Pct": 1.0,
    # 分批
    "ScaleOut_Percent": 0.4,
    # God Mode MFE 三階
    "Trail_Start_Mult": 2.5,
    "MFE_ATR_Tier_1": 3.0,
    "MFE_ATR_Tier_2": 6.0,
    "MFE_ATR_Tier_3": 10.0,
    # Data3 週線（**AND**，L1 是 OR）
    "Weekly_MA_Fast": 20,
    "Weekly_MA_Slow": 60,
    "Freeze_SL_On": True,
    # SP 死碼。五個變體 B–F 全部失敗，三筆超級贏家被砍到 +7K~+38K
    "SP_Trigger_Pts": 0,
    "SP_Retain_Pct": 50,
    "live_block_last_n_bars": 0,
}

NIGHT_BLOCK_START = 400   # L4 是 200–500，且方向相反（L5 夜盤獲利）
NIGHT_BLOCK_END = 500


@dataclass(slots=True)
class L5PerTrade(PerTradeState):
    highest_since_entry: float = 0.0
    trail_active: bool = False
    dynamic_trail_mult: float = 3.0
    sl_locked: bool = False
    frozen_atr: float = 0.0
    frozen_atr_buffer: float = 0.0
    peak_profit: float = 0.0
    sp_armed: bool = False
    sp_floor: float = 0.0
    bot_base_stop: float = 0.0
    mid_base_stop: float = 0.0
    sl_pct_floor: float = 0.0

    def reset(self) -> None:
        self.dynamic_trail_mult = 3.0
        for n in ("trail_active", "sl_locked", "sp_armed"):
            setattr(self, n, False)
        for n in ("highest_since_entry", "frozen_atr", "frozen_atr_buffer",
                  "peak_profit", "sp_floor", "bot_base_stop",
                  "mid_base_stop", "sl_pct_floor"):
            setattr(self, n, 0.0)


@dataclass(slots=True)
class L5PerSession(PerSessionState):
    in_consolidation: bool = False
    in_consolidation_prev: bool = False
    box_top: float = 0.0
    box_btm: float = 0.0
    trend_dir: int = 0
    weekly_filter: bool = False
    episode_id: int = 0
    episode_entries: int = 0


class L5BreakoutLong(Strategy[L5PerTrade, L5PerSession]):
    """15M 執行 · **日線**箱體 · 週線 AND 濾網 · 純多 · 雙腿 + 分批。"""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        cfg = config or StrategyConfig(
            name=STRATEGY_NAME, instrument="TXF",
            holiday_flat_time=415,
            params=dict(DEFAULT_PARAMS),
        )
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)
        self._inst = get_instrument(cfg.instrument)

    def initial_state(self) -> StrategyState[L5PerTrade, L5PerSession]:
        return StrategyState(per_trade=L5PerTrade(), per_session=L5PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        """v19.6 基線 162 筆。MC12 於 2026-08-26 的執行為 171 筆進場。

        標頭註明「to be re-verified after v19.7 MC9 deployment」。
        """
        return (162, 171)

    # ------------------------------------------------------------------
    def on_bar(
        self, view: MarketView, state: StrategyState[L5PerTrade, L5PerSession]
    ) -> tuple[StrategyState[L5PerTrade, L5PerSession], Decision]:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        d1, d2, d3 = view.data1, view.data2, view.data3
        decision = Decision()
        pos = view.position
        cal = view.calendar
        in_pos = pos.market_position is MarketPosition.LONG
        t = view.mc_time

        if d2 is None or d3 is None:
            state.prev_market_position = pos.market_position
            return state, decision
        if (len(d2) < p["Daily_MA_Len"] + 2
                or len(d3) < p["Weekly_MA_Slow"] + 2
                or len(d1) < p["ATR_Length"] + 2):
            state.prev_market_position = pos.market_position
            return state, decision

        # ===== SEC-0 時間濾網 =====
        allow_entry = True
        if NIGHT_BLOCK_START <= t <= NIGHT_BLOCK_END:
            allow_entry = False
        # v19.7 移除了三處 DayOfWeek = 7 —— PL 回傳 0-6，7 永不成立
        if day_of_week(view.mc_date) is DayOfWeek.SAT and t >= 1330:
            allow_entry = False
        if cal.holiday_block or cal.settlement_day:
            allow_entry = False

        # ===== SEC-1 Commander（Data2 = Daily）=====
        ref_high = highest(d2.high, p["Lookback_Bars"], offset=1)
        ref_low = lowest(d2.low, p["Lookback_Bars"], offset=1)
        curr_range = d2.high[0] - d2.low[0]
        ref_range = ref_high - ref_low
        daily_ma = average(d2.close, p["Daily_MA_Len"])
        ps.trend_dir = 1 if d2.close[0] > daily_ma else -1

        ps.in_consolidation_prev = ps.in_consolidation
        if d2.high[0] <= ref_high and d2.low[0] >= ref_low:
            if ref_range > 0 and (curr_range / ref_range) <= p["Range_Shrink_Rate"]:
                ps.in_consolidation = True
                ps.box_top = ref_high
                ps.box_btm = ref_low
        if ps.in_consolidation:
            # **用 High/Low 判定失效。L3/L4 用 Close** —— 形狀相同語意不同
            if d2.high[0] > ps.box_top or d2.low[0] < ps.box_btm:
                ps.in_consolidation = False

        if ps.in_consolidation and not ps.in_consolidation_prev:
            ps.episode_id += 1
            ps.episode_entries = 0

        # ===== SEC-2 ATR 快取 =====
        atr = avg_true_range(d1, p["ATR_Length"])
        atr_buffer = atr * p["ATR_Stop_Mult"]
        atr_trail_start = atr * p["Trail_Start_Mult"]
        tier1 = atr * p["MFE_ATR_Tier_1"]
        tier2 = atr * p["MFE_ATR_Tier_2"]
        tier3 = atr * p["MFE_ATR_Tier_3"]

        # ===== SEC-6 週線濾網（AND，L1 是 OR）=====
        wk_fast = average(d3.close, p["Weekly_MA_Fast"])
        wk_slow = average(d3.close, p["Weekly_MA_Slow"])
        ps.weekly_filter = d3.close[0] > wk_fast and d3.close[0] > wk_slow

        close = d1.close[0]
        tick = self._inst.tick_size     # MinMove / PriceScale

        if ps.in_consolidation and ps.box_top > ps.box_btm:
            mid_line = (ps.box_top + ps.box_btm) / 2
            reward = (ps.box_top - ps.box_btm) / 2
            risk = atr_buffer
            rr = reward / risk if risk > 0 else 0.0
            target_bot = mid_line - p["FrontRun_Ticks"] * tick
            target_mid = ps.box_top - p["FrontRun_Ticks"] * tick

            # P3b。**SL_Pct 錨在 v_Box_Btm，其餘四支錨在 Close**
            if pos.market_position is not MarketPosition.LONG:
                guard = abs(close - (ps.box_btm - atr_buffer))
                if p["SL_Pct"] > 0:
                    guard = min(guard, ps.box_btm * p["SL_Pct"] / 100.0)
                decision.protective = ProtectiveStop(
                    strategy=STRATEGY_NAME, distance=guard, per_contract=True,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                )

            # ===== SEC-3 進場：**兩條腿，可各自成交** =====
            if (pos.market_position is MarketPosition.FLAT and allow_entry
                    and not self._live_entry_block(view)):
                if (ps.trend_dir == 1 and ps.weekly_filter
                        and rr >= p["Min_RR_Bull"]):
                    if close < ps.box_btm and close > ps.box_btm - atr_buffer:
                        decision.add(OrderIntent(
                            strategy=STRATEGY_NAME, label=BOT, side=Side.BUY,
                            order_type=OrderType.STOP, price=ps.box_btm,
                            signal_date=view.mc_date, signal_time=view.mc_time,
                            seq=state.next_seq()))
                    if close < mid_line and close > mid_line - atr_buffer:
                        decision.add(OrderIntent(
                            strategy=STRATEGY_NAME, label=MID, side=Side.BUY,
                            order_type=OrderType.STOP, price=mid_line,
                            signal_date=view.mc_date, signal_time=view.mc_time,
                            seq=state.next_seq()))

            # ===== SEC-4 出場 =====
            if in_pos:
                if pt.highest_since_entry == 0:
                    pt.highest_since_entry = pos.entry_price
                pt.highest_since_entry = max(pt.highest_since_entry, d1.high[0])
                mfe = pt.highest_since_entry - pos.entry_price

                # 追蹤啟動：**必須突破箱頂**
                if d1.high[0] > ps.box_top + atr_trail_start:
                    pt.trail_active = True

                if p["Freeze_SL_On"] and not pt.sl_locked:
                    pt.frozen_atr = atr
                    pt.frozen_atr_buffer = pt.frozen_atr * p["ATR_Stop_Mult"]
                    pt.sl_locked = True

                # SP（production 永久關閉）
                pt.peak_profit = max(pt.peak_profit, close - pos.entry_price)
                if p["SP_Trigger_Pts"] > 0 and pt.peak_profit >= p["SP_Trigger_Pts"]:
                    pt.sp_armed = True
                if pt.sp_armed:
                    pt.sp_floor = pos.entry_price + pt.peak_profit * (
                        1 - p["SP_Retain_Pct"] / 100.0)

                scale = round(pos.max_contracts * p["ScaleOut_Percent"])
                if pos.max_contracts > 1 and scale == 0:
                    scale = 1

                # Priority 0：**每次發兩張，每腿各一**
                safety = None
                if self.config.mc_manual_kill_switch:
                    safety = "BL_Kill"
                elif cal.registry_expired:
                    safety = "BL_RegistryEnd"
                elif cal.holiday_block and t >= self.config.holiday_flat_time:
                    safety = "BL_Holiday"
                elif cal.settlement_day and t >= self.config.settlement_flat_time:
                    safety = "BL_Settlement"
                if safety:
                    for leg, i in LEGS:
                        decision.add(self._sell(view, state, LABELS[safety][i],
                                                leg, OrderType.MARKET))

                if pos.current_contracts == pos.max_contracts:
                    # ---- Stage 1 全倉 ----
                    if scale > 0:
                        decision.add(self._sell(view, state, LABELS["BL_TP"][0],
                                                BOT, OrderType.LIMIT,
                                                target_bot, scale))
                        decision.add(self._sell(view, state, LABELS["BL_TP"][1],
                                                MID, OrderType.LIMIT,
                                                target_mid, scale))
                    buf = (pt.frozen_atr_buffer
                           if (p["Freeze_SL_On"] and pt.sl_locked) else atr_buffer)
                    pt.bot_base_stop = ps.box_btm - buf
                    pt.mid_base_stop = mid_line - buf
                    if p["SL_Pct"] > 0:
                        pt.sl_pct_floor = pos.entry_price * (1 - p["SL_Pct"] / 100.0)
                        pt.bot_base_stop = max(pt.bot_base_stop, pt.sl_pct_floor)
                        pt.mid_base_stop = max(pt.mid_base_stop, pt.sl_pct_floor)
                    for leg, i, base in ((BOT, 0, pt.bot_base_stop),
                                         (MID, 1, pt.mid_base_stop)):
                        if pt.sp_armed and pt.sp_floor > base:
                            decision.add(self._sell(view, state, LABELS["BL_SP"][i],
                                                    leg, OrderType.STOP, pt.sp_floor,
                                                    pos.current_contracts))
                        else:
                            decision.add(self._sell(view, state, LABELS["BL_SL"][i],
                                                    leg, OrderType.STOP, base,
                                                    pos.current_contracts))
                    if pos.bars_since_entry >= p["Time_Stop_Bars"]:
                        for leg, i in LEGS:
                            decision.add(self._sell(view, state,
                                                    LABELS["BL_TimeExit"][i], leg,
                                                    OrderType.MARKET))
                else:
                    # ---- Stage 2/3 分批後的跑單 ----
                    if pt.trail_active:
                        if mfe > tier3:
                            pt.dynamic_trail_mult = 0.8
                        elif mfe > tier2:
                            pt.dynamic_trail_mult = 1.5
                        elif mfe > tier1:
                            pt.dynamic_trail_mult = 2.0
                        else:
                            pt.dynamic_trail_mult = 3.0
                        dyn = pt.highest_since_entry - atr * pt.dynamic_trail_mult
                        # 優先級 Trail > SP > BE
                        if dyn > max(pos.entry_price, pt.sp_floor):
                            kind, px = "BL_Trail", dyn
                        elif pt.sp_armed and pt.sp_floor > pos.entry_price:
                            kind, px = "BL_SP", pt.sp_floor
                        else:
                            kind, px = "BL_BE", pos.entry_price
                    else:
                        if pt.sp_armed and pt.sp_floor > pos.entry_price:
                            kind, px = "BL_SP", pt.sp_floor
                        else:
                            kind, px = "BL_BE", pos.entry_price
                    for leg, i in LEGS:
                        decision.add(self._sell(view, state, LABELS[kind][i], leg,
                                                OrderType.STOP, px,
                                                pos.current_contracts))
        else:
            # 箱體失效
            if in_pos:
                for leg, i in LEGS:
                    decision.add(self._sell(view, state,
                                            LABELS["BL_BreakExit"][i],
                                            leg, OrderType.MARKET))

        # ===== SEC-5 空手重置 =====
        if pos.market_position is MarketPosition.FLAT:
            pt.reset()

        state.prev_market_position = pos.market_position
        return state, decision

    # ------------------------------------------------------------------
    def _sell(self, view, state, label: str, from_entry: str,
              otype: OrderType, price: float | None = None,
              qty: int | None = None) -> OrderIntent:
        """`qty` 是**出場口數**（策略決策）。None = 平掉該腿全部。

        **只有分批出場需要設它。** 風險層必須遵守——
        2026-09-07 之前風險層會覆寫它，使 L5 的分批從未生效。
        """
        """所有出場單都帶 `from Entry(...)` 綁定。全案 28 處，只有 L5 有。

        **改進場標籤會讓綁在它上面的出場單全部失效，部位失去所有停損**——
        這正是 L5 用 Print 日誌而不用 re-entry 標籤的理由。
        """
        return OrderIntent(
            strategy=STRATEGY_NAME, label=label, side=Side.SELL,
            order_type=otype, price=price, from_entry=from_entry,
            exit_quantity=qty,
            signal_date=view.mc_date, signal_time=view.mc_time,
            seq=state.next_seq(),
        )

    def _live_entry_block(self, view: MarketView) -> bool:
        if self.config.mode is Mode.MC12:
            return False
        return bool(self.config.params.get("live_block_last_n_bars", 0)) and False
