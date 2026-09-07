"""L4_ConsolShort —— 移植自 `_Research_L4_v14.7_SpringOnly`。

行為等同 live v14.6（v14.7 只改 label 字串）。

規格表：`docs/specs/L4_ConsolShort_spec.md`
分層圖：`docs/specs/L4_layers.md`

**與 L2 同構**：ExitFired 短路保證單根單張、單一部位、IOG = false（明宣告）。
**比 L2 多的**：三資料流（15M / 60M / Daily）、變數歷史 `v_Stop_Level[1]`。

MC12 模式一律照抄，包含已知缺陷。規格表第十節的 D-1 到 D-4
在本檔中原樣保留，每一處標了 `# [D-n]`。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.indicators.core import average, avg_true_range, highest, lowest
from txfcore.strategies.base import (
    MarketView, Mode, PerSessionState, PerTradeState, Strategy,
    StrategyConfig, StrategyState,
)
from txfcore.types.orders import (
    Decision, MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side,
)

STRATEGY_NAME = "L4_ConsolShort"

DEFAULT_PARAMS: dict = {
    # Data3 日線總體濾網
    "Daily_FastMA_Len": 20,
    "Daily_SlowMA_Len": 60,
    # Data2 60M 箱體
    "Lookback_Bars": 15,
    "Range_Shrink_Rate": 0.7,      # L3 是 0.1，差七倍
    "Weekly_MA_Len": 48,
    # Data1 15M 風險
    "ATR_Length": 60,
    "ATR_Stop_Mult": 2.0,
    # 戰術進場
    "i_Buffer_ATR_Mult": 0.4,
    "Time_Limit_Bars": 6,
    # 進階管理
    "Cooldown_Bars": 8,
    "Time_Stop_Bars": 60,
    "Trail_ATR_Mult": 1.0,
    "Freeze_SL_On": True,
    # Path A 深夜封鎖
    "Night_Block_On": True,
    # Path B 死碼（production 關閉，A/B 全部失敗）
    "BE_Trigger_Pts": 0,
    "BE_Offset_Pts": 5,
    "SP_Trigger_Pts": 0,
    "SP_Retain_Pct": 50,
    # v14.6
    "SL_Pct": 1.50,                # 兩支空頭都比多頭寬（L1=0.5 L3=0.55 L5=1.0）
    "live_block_last_n_bars": 0,
}

NIGHT_BLOCK_START = 200          # L5 是 400，區間不同且方向相反
NIGHT_BLOCK_END = 500


@dataclass(slots=True)
class L4PerTrade(PerTradeState):
    lowest_low: float = 999999.0
    trail_active: bool = False
    sl_locked: bool = False
    frozen_atr: float = 0.0
    frozen_locked_top: float = 0.0
    # [D-4] .pla 沒有把 v_Stop_Level 列入空手重置清單。照抄。
    stop_level: float = 0.0
    stop_level_prev: float = 0.0   # v_Stop_Level[1]，追蹤棘輪的全部
    sl_pct_ceil: float = 0.0
    peak_profit_pts: float = 0.0
    be_armed: bool = False
    sp_armed: bool = False
    be_floor: float = 0.0
    sp_floor: float = 0.0

    def reset(self) -> None:
        self.lowest_low = 999999.0
        for n in ("trail_active", "sl_locked", "be_armed", "sp_armed"):
            setattr(self, n, False)
        for n in ("frozen_atr", "frozen_locked_top", "stop_level",
                  "stop_level_prev", "sl_pct_ceil", "peak_profit_pts",
                  "be_floor", "sp_floor"):
            setattr(self, n, 0.0)


@dataclass(slots=True)
class L4PerSession(PerSessionState):
    # 箱體。sticky —— 成立後只有 Close of Data2 突破才失效
    in_consolidation: bool = False
    in_consolidation_prev: bool = False
    box_top: float = 0.0
    box_btm: float = 0.0
    trend_dir: int = 0
    macro_block: bool = False
    # 誘多區
    in_trap_zone: bool = False
    trap_counter: int = 0
    # 只在空手時快照
    locked_top: float = 0.0
    locked_btm: float = 0.0
    # 冷卻，需 MarketPosition[1]
    bars_since_exit: int = 999
    # v14.7 re-entry 計數
    episode_id: int = 0
    episode_entries: int = 0


class L4ConsolShort(Strategy[L4PerTrade, L4PerSession]):
    """15M 執行 · 60M 箱體 · 日線總體濾網 · 純空 · IOG = false（明宣告）。"""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        cfg = config or StrategyConfig(
            name=STRATEGY_NAME, instrument="TXF",
            holiday_flat_time=415,          # 同 L3 L5；L1=345 L2=300
            params=dict(DEFAULT_PARAMS),
        )
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)

    def initial_state(self) -> StrategyState[L4PerTrade, L4PerSession]:
        return StrategyState(per_trade=L4PerTrade(), per_session=L4PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        """事前登記（判官 4）。**來源是 anchor 文件，不是標頭。**

        `docs/research/L4_v14.7_anchor_result_20260826.md`：
        **總筆數 82** = CS_Entry 79 + CS_ReEntry 3。
        淨利 800,000 / PF 1.4150 / 勝率 42.6829%。

        > **2026-09-07 修正**：我先前寫 79，那是 `CS_Entry` 的數量不是總筆數。
        > 拿它當總數比，於是「多 4 筆」——實際只多 1 筆。

        出場標籤 CS_SL 38 / CS_BreakExit 30 / CS_TimeExit 14。

        標頭明載「L4 的 alpha 只存在於空頭/中性陷阱訊號。
        **多頭市場零交易 = 正確行為。**」
        """
        return (82, 82)

    # ------------------------------------------------------------------
    def on_bar(
        self, view: MarketView, state: StrategyState[L4PerTrade, L4PerSession]
    ) -> tuple[StrategyState[L4PerTrade, L4PerSession], Decision]:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        d1, d2, d3 = view.data1, view.data2, view.data3
        decision = Decision()
        pos = view.position
        cal = view.calendar

        # 三資料流都要有足夠歷史才動作
        if d2 is None or d3 is None:
            state.prev_market_position = pos.market_position
            return state, decision
        need_d2 = p["Lookback_Bars"] + 2
        if len(d2) < need_d2 or len(d3) < p["Daily_SlowMA_Len"] + 2:
            state.prev_market_position = pos.market_position
            return state, decision

        # ===== Path A 深夜封鎖 =====
        night_block = (
            bool(p["Night_Block_On"])
            and NIGHT_BLOCK_START <= view.mc_time < NIGHT_BLOCK_END
        )

        # ===== Phase 0 總體濾網（Data3 日線）=====
        fast = average(d3.close, p["Daily_FastMA_Len"])
        slow = average(d3.close, p["Daily_SlowMA_Len"])
        slow_prev = average(d3.close, p["Daily_SlowMA_Len"], offset=1)
        ps.macro_block = (
            (d3.close[0] > slow and slow >= slow_prev) or (fast > slow)
        )

        # ===== Phase 1 箱體（Data2 60M）=====
        ref_high = highest(d2.high, p["Lookback_Bars"], offset=1)
        ref_low = lowest(d2.low, p["Lookback_Bars"], offset=1)
        curr_range = d2.high[0] - d2.low[0]
        ref_range = ref_high - ref_low

        wk_ma = average(d2.close, p["Weekly_MA_Len"]) if len(d2) >= p["Weekly_MA_Len"] else d2.close[0]
        ps.trend_dir = -1 if d2.close[0] < wk_ma else 1

        ps.in_consolidation_prev = ps.in_consolidation
        if d2.high[0] <= ref_high and d2.low[0] >= ref_low:
            if ref_range > 0 and (curr_range / ref_range) <= p["Range_Shrink_Rate"]:
                ps.in_consolidation = True
                ps.box_top = ref_high
                ps.box_btm = ref_low
        if ps.in_consolidation:
            # 用 Close 判定失效。L5 用 High/Low —— 形狀相同語意不同
            if d2.close[0] > ps.box_top or d2.close[0] < ps.box_btm:
                ps.in_consolidation = False

        # v14.7 episode 計數（label only）
        if ps.in_consolidation and not ps.in_consolidation_prev:
            ps.episode_id += 1
            ps.episode_entries = 0
        if (
            state.prev_market_position is not MarketPosition.SHORT
            and pos.market_position is MarketPosition.SHORT
        ):
            ps.episode_entries += 1

        # ===== Phase 2 戰術執行（Data1 15M）=====
        atr = avg_true_range(d1, p["ATR_Length"])
        close = d1.close[0]

        # 冷卻計數。需要 MarketPosition[1]
        if pos.market_position is not MarketPosition.FLAT:
            ps.bars_since_exit = 0
        elif state.prev_market_position is not MarketPosition.FLAT:
            ps.bars_since_exit = 1
        else:
            ps.bars_since_exit += 1

        in_box = ps.in_consolidation and ps.box_top > ps.box_btm
        if in_box:
            # 誘多偵測。用 High 不是 Close —— 影線碰到箱頂就算
            if d1.high[0] > ps.box_top:
                ps.in_trap_zone = True
                ps.trap_counter = 0
            if ps.in_trap_zone:
                ps.trap_counter += 1
                if ps.trap_counter > p["Time_Limit_Bars"]:
                    ps.in_trap_zone = False

            # P3b 引擎停損
            # [D-1] SetStopContract 在頂層無條件，但 SetStopLoss 在
            #       if v_is_in_consolidation 之內 —— 非盤整期間不設定。照抄。
            if pos.market_position is not MarketPosition.SHORT:
                guard = abs((ps.box_top + atr * p["ATR_Stop_Mult"]) - close)
                if p["SL_Pct"] > 0:
                    guard = min(guard, close * p["SL_Pct"] / 100.0)
                decision.protective = ProtectiveStop(
                    strategy=STRATEGY_NAME, distance=guard, per_contract=True,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                )

            trigger_price = ps.box_top - atr * p["i_Buffer_ATR_Mult"]

            if (
                pos.market_position is MarketPosition.FLAT
                and ps.bars_since_exit >= p["Cooldown_Bars"]
                and ps.trend_dir == -1
                and not ps.macro_block
                and ps.in_trap_zone
                and close < trigger_price
                and not cal.holiday_block
                and not night_block
                and not cal.settlement_day
                and not self._live_entry_block(view)
            ):
                label = "CS_ReEntry" if ps.episode_entries >= 1 else "CS_Entry"
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME, label=label, side=Side.SELL_SHORT,
                    order_type=OrderType.MARKET,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
                ps.in_trap_zone = False

        # ===== Phase 3 出場邏輯 =====
        if pos.market_position is MarketPosition.FLAT:
            if ps.in_consolidation:
                ps.locked_top = ps.box_top
                ps.locked_btm = ps.box_btm
            pt.reset()

        if pos.market_position is MarketPosition.SHORT:
            self._manage(view, state, atr)
            self._exit_chain(view, state, decision)

        state.prev_market_position = pos.market_position
        return state, decision

    # ------------------------------------------------------------------
    def _manage(self, view: MarketView, state, atr: float) -> None:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        d1 = view.data1
        entry = view.position.entry_price

        if d1.low[0] < pt.lowest_low:
            pt.lowest_low = d1.low[0]
        if pt.lowest_low <= ps.locked_btm:
            pt.trail_active = True

        # [D-2] 凍結的是**中間變數**（ATR 與箱頂），不是最終價位。
        #       L1/L2/L3 凍結價位。當 locked_top 在持倉期間變動時兩者分岔。
        if p["Freeze_SL_On"] and not pt.sl_locked:
            pt.frozen_atr = atr
            pt.frozen_locked_top = ps.locked_top
            pt.sl_locked = True

        pt.stop_level_prev = pt.stop_level
        if pt.trail_active:
            # v_Stop_Level = MinList(v_Stop_Level[1], ...) —— 棘輪的全部。
            # 歷史值取錯，整條追蹤停損失效且不報錯。
            new = pt.lowest_low + p["Trail_ATR_Mult"] * atr
            pt.stop_level = min(pt.stop_level_prev, new) if pt.stop_level_prev > 0 else new
        elif p["Freeze_SL_On"]:
            pt.stop_level = pt.frozen_locked_top + p["ATR_Stop_Mult"] * pt.frozen_atr
        else:
            pt.stop_level = ps.locked_top + p["ATR_Stop_Mult"] * atr
            if 0 < ps.box_top < ps.locked_top:
                ps.locked_top = ps.box_top

        # SL_Pct **統一套用全部路徑**（凍結/動態/追蹤）。L2 只封頂初始停損。
        if p["SL_Pct"] > 0:
            pt.sl_pct_ceil = entry + entry * p["SL_Pct"] / 100.0
            pt.stop_level = min(pt.stop_level, pt.sl_pct_ceil)

        # Path B 死碼（production 兩者皆 0，路徑不執行）
        profit = entry - d1.close[0]
        if profit > pt.peak_profit_pts:
            pt.peak_profit_pts = profit
        if p["BE_Trigger_Pts"] > 0 and pt.peak_profit_pts >= p["BE_Trigger_Pts"]:
            pt.be_armed = True
        if p["SP_Trigger_Pts"] > 0 and pt.peak_profit_pts >= p["SP_Trigger_Pts"]:
            pt.sp_armed = True
        if pt.be_armed:
            pt.be_floor = entry - p["BE_Offset_Pts"]
        if pt.sp_armed:
            pt.sp_floor = entry - pt.peak_profit_pts * (1 - p["SP_Retain_Pct"] / 100.0)

    def _live_entry_block(self, view: MarketView) -> bool:
        if self.config.mode is Mode.MC12:
            return False
        return bool(self.config.params.get("live_block_last_n_bars", 0)) and False

    def _exit_chain(self, view: MarketView, state, decision: Decision) -> None:
        """ExitFired 短路，保證單根單張。與 L2 同構。"""
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        cal = view.calendar
        d2 = view.data2

        def cover(label: str, price: float | None = None) -> None:
            decision.add(OrderIntent(
                strategy=STRATEGY_NAME, label=label, side=Side.BUY_TO_COVER,
                order_type=OrderType.MARKET if price is None else OrderType.STOP,
                price=price, signal_date=view.mc_date, signal_time=view.mc_time,
                seq=state.next_seq(),
            ))

        # 優先級 0
        if self.config.mc_manual_kill_switch:
            return cover("CS_Kill")
        if cal.registry_expired:
            return cover("CS_RegistryEnd")
        if cal.holiday_block and view.mc_time >= self.config.holiday_flat_time:
            return cover("CS_Holiday")
        if cal.settlement_day and view.mc_time >= self.config.settlement_flat_time:
            return cover("CS_Settlement")

        # 優先級 1  災難控制
        # [D-3] **只認向上突破**。箱體向下失效（對空單有利）不出場。
        if d2 is not None and not ps.in_consolidation and d2.close[0] > ps.locked_top:
            return cover("CS_BreakExit")

        # 優先級 2  時間停損
        if not pt.trail_active and view.position.bars_since_entry >= p["Time_Stop_Bars"]:
            return cover("CS_TimeExit")

        # 優先級 3  標籤停損。空單「更低 = 更緊」
        eff = pt.stop_level
        if pt.sp_armed and 0 < pt.sp_floor < eff:
            return cover("CS_SP", price=pt.sp_floor)
        if pt.be_armed and 0 < pt.be_floor < eff:
            return cover("CS_BE", price=pt.be_floor)
        return cover("CS_SL", price=eff)
