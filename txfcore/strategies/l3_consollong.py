"""L3_ConsolLong —— 移植自 `_Backtest_Adaptive_Farmer_v14_PureLong` v15.1。

行為等同 live v15.0（v15.1 只加 re-entry 標籤，`零 behaviour change`）。

規格表：`docs/specs/L3_ConsolLong_spec.md`
分層圖：`docs/specs/L3_layers.md`

**與 L2 / L4 最大的結構差異：無 ExitFired，常態同時掛 TP 限價 + SL 停價。**
執行層第一次被迫支援 OCO——一張成交，另一張作廢。

MC12 模式一律照抄，包含已知缺陷。規格表第十節的 D-1 到 D-3 原樣保留。
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

STRATEGY_NAME = "L3_ConsolLong"

DEFAULT_PARAMS: dict = {
    # Data2 60M 箱體
    "Lookback_Bars": 16,
    "Range_Shrink_Rate": 0.1,     # L4 是 0.7、L5 是 0.6 —— 差七倍
    "MA_Len": 12,
    # v14 矩陣維度
    "Entry_Zone_Pct": 0.50,       # 支撐區 = 箱體下半部（掃描 0.30 -> 0.50）
    "Min_Box_ATR": 8.5,           # 箱寬須 >= N x ATR（掃描 3.0 -> 8.5，85% 分位）
    "Swing_Lookback": 80,         # 15M 根數，動態擺盪高點（掃描 32 -> 80）
    # Data1 15M 風險
    "ATR_Length": 9,
    "ATR_Stop_Mult": 3.0,         # v_ATR_Buffer = 3.0 x ATR(9)
    "SL_Pct": 0.55,
    "Open_Block_End": 945,
    "Min_RR": 1.0,
    # Data3 日線
    "Daily_MA_Fast": 20,
    "Daily_MA_Slow": 60,
    # 凍結
    "Freeze_SL_On": True,
    # 死碼（production 關閉）
    "BE_Trigger_Pts": 0,
    "BE_Offset_Pts": 5,
    "live_block_last_n_bars": 0,
}


@dataclass(slots=True)
class L3PerTrade(PerTradeState):
    sl_locked: bool = False
    frozen_sl: float = 0.0
    frozen_target: float = 0.0
    sl_pct_floor: float = 0.0
    be_armed: bool = False
    be_is_floor: bool = False
    work_sl: float = 0.0
    work_target: float = 0.0

    def reset(self) -> None:
        for n in ("sl_locked", "be_armed", "be_is_floor"):
            setattr(self, n, False)
        for n in ("frozen_sl", "frozen_target", "sl_pct_floor",
                  "work_sl", "work_target"):
            setattr(self, n, 0.0)


@dataclass(slots=True)
class L3PerSession(PerSessionState):
    # 箱體。sticky —— 只有 Data2 收盤穿出才失效（L5 用 High/Low）
    in_consolidation: bool = False
    in_consolidation_prev: bool = False    # v_is_in_consolidation[1]
    box_top: float = 0.0
    box_btm: float = 0.0
    trend_dir: int = 0
    daily_filter: bool = False
    # v15.1 re-entry 狀態（純標籤）
    episode_id: int = 0
    mkt_exit_ordered: bool = False
    last_entry_price: float = 0.0
    reentry_armed: bool = False
    reentry_price: float = 0.0
    reentry_episode: int = 0


class L3ConsolLong(Strategy[L3PerTrade, L3PerSession]):
    """15M 執行 · 60M 箱體 · 日線濾網 · 純多 · IOG = false（未宣告）。"""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        cfg = config or StrategyConfig(
            name=STRATEGY_NAME, instrument="TXF",
            holiday_flat_time=415,          # 同 L4 L5；L1=345 L2=300
            params=dict(DEFAULT_PARAMS),
        )
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)

    def initial_state(self) -> StrategyState[L3PerTrade, L3PerSession]:
        return StrategyState(per_trade=L3PerTrade(), per_session=L3PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        """事前登記（判官 4）。

        v15.1 的 CHANGELOG：「ANCHOR: must reproduce v15.0 exactly
        -- **360 trades / 1,389,600**」。

        > **標頭內部矛盾**：同一份檔案的 PERFORMANCE 區塊寫
        > 376 筆 / 2,446,000（MC9 2026/07/25）。
        > 採用 CHANGELOG 那組（2026-08-25，較新）。

        re-entry **無法事前登記精確值**——「同一 episode」需要 K 棒資料，
        交易清單沒有。改登記為區間 `20 <= CL_ReEntry <= 115`，預期靠近下限。
        **超過 115 代表 episode 閘門沒作用。**
        """
        return (360, 376)

    def expected_reentry_range(self) -> tuple[int, int]:
        return (20, 115)

    # ------------------------------------------------------------------
    def on_bar(
        self, view: MarketView, state: StrategyState[L3PerTrade, L3PerSession]
    ) -> tuple[StrategyState[L3PerTrade, L3PerSession], Decision]:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        d1, d2, d3 = view.data1, view.data2, view.data3
        decision = Decision()
        pos = view.position
        cal = view.calendar
        in_pos = pos.market_position is MarketPosition.LONG

        if d2 is None or d3 is None:
            state.prev_market_position = pos.market_position
            return state, decision
        if (len(d2) < p["Lookback_Bars"] + 2
                or len(d3) < p["Daily_MA_Slow"] + 2
                or len(d1) < p["Swing_Lookback"] + 2):
            state.prev_market_position = pos.market_position
            return state, decision

        # ===== 1. Commander Logic（Data2 60M 箱體偵測）=====
        ref_high = highest(d2.high, p["Lookback_Bars"], offset=1)
        ref_low = lowest(d2.low, p["Lookback_Bars"], offset=1)
        curr_range = d2.high[0] - d2.low[0]
        ref_range = ref_high - ref_low

        ma60 = average(d2.close, p["MA_Len"])
        ps.trend_dir = 1 if d2.close[0] > ma60 else -1

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

        # episode 計數器。sticky 箱體的 false->true 轉換 = 一個新 episode
        if ps.in_consolidation and not ps.in_consolidation_prev:
            ps.episode_id += 1

        # v_MktExit_Ordered **只在持倉時重置**，所以轉為空手那一根仍帶著
        # 最後一次在倉的值——那正是 latch 要讀的東西
        if in_pos:
            ps.mkt_exit_ordered = False

        # ===== 1b. re-entry 狀態（純標籤）=====
        if in_pos:
            ps.last_entry_price = pos.entry_price
        if (state.prev_market_position is MarketPosition.LONG
                and pos.market_position is MarketPosition.FLAT):
            ps.reentry_armed = (
                pos.prev_position_profit <= 0 and not ps.mkt_exit_ordered
            )
            ps.reentry_price = ps.last_entry_price
            ps.reentry_episode = ps.episode_id
        # **唯一的解除，而且是結構性的不是價格的。**
        # L4 v18 零觸發正是因為它的價格解除被自己的停損蘊含；
        # 這裡完全不測價格，所以避開了那個陷阱。
        if ps.reentry_armed and ps.episode_id != ps.reentry_episode:
            ps.reentry_armed = False
            ps.reentry_price = 0.0

        # ===== 2. 箱體合格矩陣（Dim 1）=====
        atr = avg_true_range(d1, p["ATR_Length"])
        atr_buffer = p["ATR_Stop_Mult"] * atr
        box_range = 0.0
        box_qualified = False
        mid_line = 0.0
        support_zone = 0.0
        if ps.in_consolidation and ps.box_top > ps.box_btm:
            box_range = ps.box_top - ps.box_btm
            mid_line = (ps.box_top + ps.box_btm) / 2
            if atr > 0 and (box_range / atr) >= p["Min_Box_ATR"]:
                box_qualified = True
            support_zone = ps.box_btm + box_range * p["Entry_Zone_Pct"]

        # ===== 3. Data3 日線濾網（OR，不是 AND）=====
        d_fast = average(d3.close, p["Daily_MA_Fast"])
        d_slow = average(d3.close, p["Daily_MA_Slow"])
        ps.daily_filter = d3.close[0] > d_fast or d3.close[0] > d_slow

        close = d1.close[0]
        t = view.mc_time

        # ===== 4. 執行區塊（需要有效箱體，不需要合格）=====
        if ps.in_consolidation and ps.box_top > ps.box_btm:
            # P3b 引擎停損
            # [D-1] SetStopContract 在 if v_is_in_consolidation **之內**。
            #       L5 的註解寫「must be outside conditional」。
            #       若 L5 正確，這裡的位置是錯的。照抄。
            if box_qualified and pos.market_position is not MarketPosition.LONG:
                dist = abs(close - (ps.box_btm - atr_buffer))
                if p["SL_Pct"] > 0:
                    dist = min(dist, close * p["SL_Pct"] / 100.0)
                decision.protective = ProtectiveStop(
                    strategy=STRATEGY_NAME, distance=dist, per_contract=True,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                )

            # 開盤波動封鎖。擋的是「成交會落在禁區」的訊號，不是訊號本身的時間
            opening_block = False
            if p["Open_Block_End"] > 0:
                if t == 500:                              # 夜盤末根 -> 09:00 成交
                    opening_block = True
                if 900 <= t < p["Open_Block_End"]:        # -> 09:15..09:45 成交
                    opening_block = True

            # 報酬風險比閘門
            rr_qualified = True
            if p["Min_RR"] > 0 and p["SL_Pct"] > 0 and box_range > 0:
                if box_range < p["Min_RR"] * ps.box_btm * p["SL_Pct"] / 100.0:
                    rr_qualified = False

            # --- 進場（Dim 2：統一支撐區）---
            if box_qualified and pos.market_position is MarketPosition.FLAT:
                if (ps.trend_dir == 1
                        and ps.daily_filter
                        and not cal.holiday_block
                        and not cal.settlement_day
                        and not opening_block
                        and rr_qualified
                        and not self._live_entry_block(view)):
                    if close < support_zone and close > ps.box_btm - atr_buffer:
                        is_re = (
                            ps.reentry_armed
                            and ps.reentry_price > 0
                            and ps.episode_id == ps.reentry_episode
                            and ps.box_btm <= ps.reentry_price
                        )
                        # 訂單價 **就是 v_Box_Btm**，下單當下已知——
                        # 不像 L2 要比一個還不存在的成交價
                        decision.add(OrderIntent(
                            strategy=STRATEGY_NAME,
                            label="CL_ReEntry" if is_re else "CL_Entry",
                            side=Side.BUY, order_type=OrderType.STOP,
                            price=ps.box_btm,
                            signal_date=view.mc_date, signal_time=view.mc_time,
                            seq=state.next_seq(),
                        ))

            # --- 出場（Dim 3：動態目標）。**bracket，常態兩張單** ---
            if in_pos:
                if p["Freeze_SL_On"]:
                    if not pt.sl_locked:
                        pt.frozen_sl = ps.box_btm - atr_buffer
                        if p["SL_Pct"] > 0:
                            pt.sl_pct_floor = pos.entry_price * (1 - p["SL_Pct"] / 100.0)
                            # MaxList 取較高價 = 多單較緊
                            pt.frozen_sl = max(pt.frozen_sl, pt.sl_pct_floor)
                        swing = highest(d1.high, p["Swing_Lookback"])
                        pt.frozen_target = min(swing, ps.box_top)
                        # 兜底：目標太靠近中線就直接用箱頂
                        if pt.frozen_target < mid_line + atr:
                            pt.frozen_target = ps.box_top
                        pt.sl_locked = True
                    pt.work_sl = pt.frozen_sl
                    pt.work_target = pt.frozen_target
                else:
                    pt.work_sl = ps.box_btm - atr_buffer
                    if p["SL_Pct"] > 0:
                        pt.sl_pct_floor = pos.entry_price * (1 - p["SL_Pct"] / 100.0)
                        pt.work_sl = max(pt.work_sl, pt.sl_pct_floor)
                    swing = highest(d1.high, p["Swing_Lookback"])
                    pt.work_target = min(swing, ps.box_top)
                    if pt.work_target < mid_line + atr:
                        pt.work_target = ps.box_top

                # BE 層（production 關閉，BE_Trigger_Pts = 0）
                pt.be_is_floor = False
                if p["BE_Trigger_Pts"] > 0:
                    if (close - pos.entry_price) >= p["BE_Trigger_Pts"]:
                        pt.be_armed = True
                    if pt.be_armed and (pos.entry_price + p["BE_Offset_Pts"] > pt.work_sl):
                        pt.work_sl = pos.entry_price + p["BE_Offset_Pts"]
                        pt.be_is_floor = True

                # **兩張單同時掛出。執行層必須支援 OCO。**
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME, label="CL_TP", side=Side.SELL,
                    order_type=OrderType.LIMIT, price=pt.work_target,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME,
                    label="CL_BE" if pt.be_is_floor else "CL_SL", side=Side.SELL,
                    order_type=OrderType.STOP, price=pt.work_sl,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
        else:
            # ===== 5. 箱體失效 =====
            # [D-2] 這裡是 else 分支，所以上面的 TP / SL **兩張都不再掛出**。
            #       只剩市價 BreakExit。移植時極易漏。
            if in_pos:
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME, label="CL_BreakExit", side=Side.SELL,
                    order_type=OrderType.MARKET,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
                ps.mkt_exit_ordered = True

        # ===== 6. 安全出場（Priority 0，永遠有效）=====
        if in_pos:
            safety = None
            if cal.registry_expired:
                safety = "CL_RegistryEnd"
            elif cal.holiday_block and t >= self.config.holiday_flat_time:
                safety = "CL_Holiday"
            elif cal.settlement_day and t >= self.config.settlement_flat_time:
                safety = "CL_Settlement"
            if safety:
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME, label=safety, side=Side.SELL,
                    order_type=OrderType.MARKET,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
                ps.mkt_exit_ordered = True
            # [D-3] Kill 是**獨立的 if，不在 else 鏈上**。與 L1 的 J-3 同型。
            #       一根最多四張：TP + SL + 安全出場 + Kill。
            if self.config.mc_manual_kill_switch:
                decision.add(OrderIntent(
                    strategy=STRATEGY_NAME, label="CL_Kill", side=Side.SELL,
                    order_type=OrderType.MARKET,
                    signal_date=view.mc_date, signal_time=view.mc_time,
                    seq=state.next_seq(),
                ))
                ps.mkt_exit_ordered = True

        # ===== 7. 空手重置 =====
        if pos.market_position is MarketPosition.FLAT:
            pt.reset()

        state.prev_market_position = pos.market_position
        return state, decision

    def _live_entry_block(self, view: MarketView) -> bool:
        if self.config.mode is Mode.MC12:
            return False
        return bool(self.config.params.get("live_block_last_n_bars", 0)) and False
