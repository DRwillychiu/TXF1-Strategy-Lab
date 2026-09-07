"""L1_TrendLong —— 移植自 `WILLY_ATR_LONG_45M_V32_RESEARCH` v3.2。

行為等同 live v3.1（v3.2 的 re-entry 腿以 `ReEntry_On = 0` 出貨，完全惰性）。

規格表：`docs/specs/L1_TrendLong_spec.md`

## ★ 已知限制：本移植在 K 棒收盤評估，不是逐 tick

L1 是五支裡唯一 `IntrabarOrderGeneration = true` 的策略。原始碼把
**指標 / 週線濾網 / 假日偵測 / 進場 / P3 凍結 / 跳空分支**包在
`BarStatus(1) = 2` 內（每根一次），而**P7 峰值追蹤 / P4 棘輪 / 出場下單**
在守衛外逐 tick 執行。

`engine/context.py` 尚未實作，所以本移植**全部在收盤評估**。後果：

    P7 只看得到收盤價的峰值，看不到盤中的
    -> posbleProfit_Long 偏低
    -> stopProfitPrice_L 偏低
    -> TL_SP 觸發次數是**下限**，不是實際值

V3.0 把 SP 門檻從 500 降到 200 **正是因為 IOG 讓更低的門檻可行**，
所以用 200 跑收盤評估，既不是 V2.7 也不是 V3.2 的行為。

> **這個落差是結構性的，不是參數問題。** 對帳時必須把它算進去，
> 修法是實作 `engine/context.py` 的 tick 生命週期。
"""

from __future__ import annotations

from dataclasses import dataclass

from txfcore.indicators.core import average, avg_true_range, crosses_over
from txfcore.strategies.base import (
    MarketView, Mode, PerSessionState, PerTradeState, Strategy,
    StrategyConfig, StrategyState,
)
from txfcore.types.orders import (
    Decision, MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side,
)

STRATEGY_NAME = "L1_TrendLong"

DEFAULT_PARAMS: dict = {
    # P2 進場
    "Length60": 61,
    "Entry_Multiplier": 2.0,
    # P3 三層停損
    "SL_Multiplier": 1.5,
    "Daily_Cap_Multiplier": 0.5,
    "SL_Pct": 0.5,
    # P4 追蹤
    "Length20": 55,
    "TrailOffset": 50,
    # P7 峰值回吐
    "stopProfitPoints_Long": 200,     # V3.0 把 500 降到 200，因為 IOG 讓它可行
    "profitReturnPrcnt_Long": 55,
    "ATR_Length": 20,
    # P6 週線（**OR**，L5 是 AND）
    "Weekly_MA_Fast": 20,
    "Weekly_MA_Slow": 60,
    # Group R：re-entry 模組，出貨即關閉。
    #
    # **2026-09-07 稽核發現我原本只移植了 ReEntry_On，其餘六個 input 全缺。**
    # 後果：有人把 ReEntry_On 設成 1 時，我的移植會**靜默地什麼都不做**，
    # 而 MC 會發 TL_ReEntry 單。惰性 != 不存在。
    #
    # 全部宣告為數值 0/1 而非布林：**MC12 的最佳化器完全不列出
    # TrueFalse 型別的 input**，凡是需要被掃描或 A/B 的都必須是數字。
    "ReEntry_On": 0,                 # 主開關。0 = 腿關閉（anchor）
    "ReEntry_Close_Gate": 1,         # Close <= v_ReEntry_Price
    "ReEntry_Trend_Gate": 1,         # v_TrendRatio >= ReEntry_Trend_Ratio
    "ReEntry_Weekly_Gate": 1,        # 週線濾網仍為真
    "ReEntry_MABase_Gate": 0,        # W2：maBase 不低於進場時的值。出貨關閉
    "ReEntry_WeeklyTier_Gate": 0,    # W3：週線層級未降級。出貨關閉
    "ReEntry_Trend_Ratio": 0.20,     # MC 掃描 0.0–1.0，2026-08-22 採用 0.20
    "live_block_last_n_bars": 0,
}

LABEL_TOLERANCE = 0.001   # 標籤路由的浮點容差。**照抄，不可改成等號**


@dataclass(slots=True)
class L1PerTrade(PerTradeState):
    sl_locked: bool = False
    frozen_sl: float = 0.0
    # IntraBarPersist 的三個變數。本移植在收盤更新（見模組說明）
    posble_profit: float = 0.0
    stop_profit_price: float = 0.0
    trail_high: float = 0.0

    def reset(self) -> None:
        self.sl_locked = False
        for n in ("frozen_sl", "posble_profit", "stop_profit_price", "trail_high"):
            setattr(self, n, 0.0)


@dataclass(slots=True)
class L1PerSession(PerSessionState):
    weekly_filter: bool = False
    # re-entry 用，必須存活過平倉。ReEntry_On = 0 時全部惰性
    frozen_gap: float = 0.0
    frozen_mabase: float = 0.0
    frozen_sl_orig: float = 0.0
    last_entry_price: float = 0.0
    reentry_armed: bool = False
    reentry_price: float = 0.0
    is_reentry: bool = False        # 本筆是否為 re-entry（停損繼承用）
    wk_entry_fast: bool = False     # W3 參考
    wk_entry_slow: bool = False


class L1TrendLong(Strategy[L1PerTrade, L1PerSession]):
    """45M 執行 · 日線 ATR 上限 · 週線 OR 濾網 · 純多 · **單一停損架構**。

    與 L2/L4 的優先級鏈不同：L1 把三層保護合成**一個價位**
    `MaxList(Trail, FrozenSL, StopProfit)`，效果相同結構不同。
    """

    def __init__(self, config: StrategyConfig | None = None) -> None:
        cfg = config or StrategyConfig(
            name=STRATEGY_NAME, instrument="TXF",
            holiday_flat_time=345,      # 五支裡最早。45M 網格 03:45 觸發
            params=dict(DEFAULT_PARAMS),
        )
        for k, v in DEFAULT_PARAMS.items():
            cfg.params.setdefault(k, v)
        super().__init__(cfg)

    def initial_state(self) -> StrategyState[L1PerTrade, L1PerSession]:
        return StrategyState(per_trade=L1PerTrade(), per_session=L1PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        """V2.7 標頭：476 筆 / 3,018,400，回測 2019/12/16 - 2026/07/02。

        > V3.2 明載：「Trade counts in the older documents were taken on an
        > earlier bar set and are **NOT a valid baseline**. TWO runs are required.」

        另有一組 451 筆 / 3,938K。兩組矛盾。
        **而且本移植是收盤評估，與 V3.2 的 IOG 行為不同**（見模組說明）。
        """
        return (451, 476)

    # ------------------------------------------------------------------
    def on_bar(
        self, view: MarketView, state: StrategyState[L1PerTrade, L1PerSession]
    ) -> tuple[StrategyState[L1PerTrade, L1PerSession], Decision]:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        d1, d2, d3 = view.data1, view.data2, view.data3
        decision = Decision()
        pos = view.position
        cal = view.calendar
        t = view.mc_time

        if d2 is None or d3 is None:
            state.prev_market_position = pos.market_position
            return state, decision
        if (len(d1) < p["Length60"] + 2
                or len(d2) < p["ATR_Length"] + 2
                or len(d3) < p["Weekly_MA_Slow"] + 2):
            state.prev_market_position = pos.market_position
            return state, decision

        # ===== 1. 核心指標 =====
        ma_base = average(d1.close, p["Length60"])
        ma_base_prev = average(d1.close, p["Length60"], offset=1)
        ma_trail = average(d1.close, p["Length20"])
        atr = avg_true_range(d1, p["ATR_Length"])
        atr_prev = avg_true_range(d1, p["ATR_Length"], offset=1)
        # **[1] 指向前一根已完成的日線** —— V3.0 的修正
        daily_atr = avg_true_range(d2, p["ATR_Length"], offset=1)

        breakout = ma_base + atr * p["Entry_Multiplier"]
        breakout_prev = ma_base_prev + atr_prev * p["Entry_Multiplier"]
        cond_breakout = crosses_over(d1.close, breakout, breakout_prev)

        # ===== P6 週線濾網（OR。L5 用 AND）=====
        wk_fast = average(d3.close, p["Weekly_MA_Fast"])
        wk_slow = average(d3.close, p["Weekly_MA_Slow"])
        ps.weekly_filter = d3.close[0] > wk_fast or d3.close[0] > wk_slow

        close = d1.close[0]
        in_pos = pos.market_position is MarketPosition.LONG

        # ===== 2. P3b 引擎停損。**MinList of DISTANCES = 較緊的那條腿** =====
        # V2.9 修正：舊版用 MaxList 取到較鬆的腿，寬 1.6–2.8 倍，
        # 橫跨整個 V2.6+ 世代未被發現——**而驗證器把 bug 編碼進去了**。
        if pos.market_position is not MarketPosition.LONG:
            legs = [atr * p["SL_Multiplier"], daily_atr * p["Daily_Cap_Multiplier"]]
            if p["SL_Pct"] > 0:
                legs.append(close * p["SL_Pct"] / 100.0)
            decision.protective = ProtectiveStop(
                strategy=STRATEGY_NAME, distance=min(legs), per_contract=True,
                signal_date=view.mc_date, signal_time=view.mc_time,
            )

        # ===== 2.5 re-entry 狀態（ReEntry_On = 0 時完全惰性）=====
        # **順序是承重的**：新週期重置必須在兩個進場區塊之前執行，
        # 主進場與 re-entry 才會互斥。沒有顯式的互斥旗標。
        if (state.prev_market_position is MarketPosition.LONG
                and pos.market_position is MarketPosition.FLAT
                and ps.frozen_gap > 0):
            ps.reentry_armed = True
            ps.reentry_price = ps.last_entry_price
        if ps.reentry_armed:
            trend_ratio = ((close - ma_base) / ps.frozen_gap
                           if ps.frozen_gap > 0 else 0.0)
            if trend_ratio <= 0 or not ps.weekly_filter:
                ps.reentry_armed = False
                ps.reentry_price = 0.0
        if cond_breakout:
            ps.reentry_armed = False
            ps.reentry_price = 0.0

        # W3：週線濾網是兩支的 OR。進場時兩支都真、re-entry 時只剩一支，
        # 是高時間框架的降級，而 45M 結構還沒登記到。
        wk_now_fast = d3.close[0] > wk_fast
        wk_now_slow = d3.close[0] > wk_slow
        wk_tier_ok = not (ps.wk_entry_fast and not wk_now_fast) and \
                     not (ps.wk_entry_slow and not wk_now_slow)
        trend_ratio = ((close - ma_base) / ps.frozen_gap
                       if ps.frozen_gap > 0 else 0.0)

        # ===== 主進場 =====
        if (pos.market_position is MarketPosition.FLAT
                and cond_breakout
                and ps.weekly_filter
                and not cal.holiday_block
                and not cal.settlement_day
                and not self._live_entry_block(view)):
            decision.add(OrderIntent(
                strategy=STRATEGY_NAME, label="TL_Entry", side=Side.BUY,
                order_type=OrderType.MARKET,
                signal_date=view.mc_date, signal_time=view.mc_time,
                seq=state.next_seq()))
            ps.is_reentry = False
        # ===== v32 re-entry 腿 =====
        # **每個閘門寫成 `(開關關閉 or 條件)`**，所以全部打開時
        # 這個區塊退化成單純的條件式——那正是 ReEntry_On = 0 的 anchor
        # 可重現的原因。
        #
        # 合規閘門（假日 / 結算）**必須與主進場完全相同**。這是手動同步的：
        # 在主進場加一道而忘了這裡，就會開一個「主進場被擋但 re-entry 仍發單」的洞。
        elif (pos.market_position is MarketPosition.FLAT
                and p["ReEntry_On"] != 0
                and ps.reentry_armed
                and (p["ReEntry_Close_Gate"] == 0 or close <= ps.reentry_price)
                and (p["ReEntry_Trend_Gate"] == 0
                     or trend_ratio >= p["ReEntry_Trend_Ratio"])
                and (p["ReEntry_Weekly_Gate"] == 0 or ps.weekly_filter)
                and (p["ReEntry_MABase_Gate"] == 0 or ma_base >= ps.frozen_mabase)
                and (p["ReEntry_WeeklyTier_Gate"] == 0 or wk_tier_ok)
                and not cal.holiday_block
                and not cal.settlement_day):
            ps.is_reentry = True
            decision.add(OrderIntent(
                strategy=STRATEGY_NAME, label="TL_ReEntry", side=Side.BUY,
                order_type=OrderType.STOP, price=ps.reentry_price,
                signal_date=view.mc_date, signal_time=view.mc_time,
                seq=state.next_seq()))

        # ===== 3. 出場管理 =====
        if in_pos:
            entry = pos.entry_price
            ps.last_entry_price = entry

            # P3 三層凍結停損。**MaxList of PRICES = 最緊**
            if not pt.sl_locked:
                px_atr = entry - atr * p["SL_Multiplier"]
                px_cap = entry - daily_atr * p["Daily_Cap_Multiplier"]
                px_pct = entry - entry * p["SL_Pct"] / 100.0 if p["SL_Pct"] > 0 else 0.0
                # **同一筆交易繼續，所以用同一組風險參數。**
                # MaxList 取最高價 = 多單最緊。取「繼承的」與「重算的」較緊者，
                # 停損就永遠不會比原始的更鬆——那正是 Plan C 在 2026-07 被
                # 診斷出來的失敗：「re-entry 部位的停損價比原始突破進場更差」。
                #
                # **獲利保護狀態刻意不繼承**，因為建立它的那段行情已經被吐回去了。
                if ps.is_reentry and ps.frozen_sl_orig > 0:
                    pt.frozen_sl = max(ps.frozen_sl_orig, px_atr, px_cap, px_pct)
                else:
                    pt.frozen_sl = max(px_atr, px_cap, px_pct)
                    ps.frozen_sl_orig = pt.frozen_sl
                    ps.frozen_gap = entry - ma_base
                    ps.frozen_mabase = ma_base
                    ps.wk_entry_fast = d3.close[0] > wk_fast
                    ps.wk_entry_slow = d3.close[0] > wk_slow
                pt.sl_locked = True

            exit_sl = pt.frozen_sl

            # P7 峰值回吐。**本移植用收盤價，IOG 版用當下成交價**
            if (close - entry) >= p["stopProfitPoints_Long"]:
                pt.posble_profit = max(pt.posble_profit, close - entry)
                pt.stop_profit_price = entry + pt.posble_profit * (
                    1.0 - p["profitReturnPrcnt_Long"] / 100.0)

            # P4 MA55 追蹤，單向棘輪
            pt.trail_high = max(pt.trail_high, ma_trail - p["TrailOffset"])
            exit_trail = pt.trail_high

            final = max(exit_trail, exit_sl, pt.stop_profit_price)

            # ===== 標籤路由（V2.9.1）=====
            # **虧損側標籤只能標虧損出場，獲利了結必須用不同標籤。**
            # 側別在**下單時**判定；跳空穿過進場價仍可能讓獲利標籤成交在小虧，
            # 標頭記錄為 documented edge，不是重疊。
            if close < final:
                # 跳空分支。原始碼在 BarStatus = 2 內，本移植等價
                label = "TL_SP_Gap" if final >= entry else "TL_SL_Gap"
                decision.add(self._sell(view, state, label, OrderType.MARKET))
            else:
                if abs(final - exit_sl) < LABEL_TOLERANCE:
                    label = "TL_SL"
                elif (pt.stop_profit_price > 0
                      and abs(final - pt.stop_profit_price) < LABEL_TOLERANCE):
                    label = "TL_SP"
                elif exit_trail >= entry:
                    label = "TL_TP"
                else:
                    label = "TL_TSL"
                decision.add(self._sell(view, state, label, OrderType.STOP, final))
        else:
            pt.reset()

        # ===== 4. 強制平倉。**Section 3 必發一張，這裡再發，所以一根最多三張** =====
        if in_pos:
            safety = None
            if cal.registry_expired:
                safety = "TL_RegistryEnd"
            elif cal.holiday_block and t >= self.config.holiday_flat_time:
                safety = "TL_Holiday"
            elif cal.settlement_day and t >= self.config.settlement_flat_time:
                safety = "TL_Settlement"
            if safety:
                decision.add(self._sell(view, state, safety, OrderType.MARKET))
            # **[J-3] Kill 在 else 鏈外。標頭自承可一根發兩張全額市價單。**
            # 加互斥旗標會改變行為並破壞 anchor —— 刻意不修。
            if self.config.mc_manual_kill_switch:
                decision.add(self._sell(view, state, "TL_Kill", OrderType.MARKET))

        # ===== 最末行：CLAUDE.md Rule #8 =====
        state.prev_market_position = pos.market_position
        return state, decision

    # ------------------------------------------------------------------
    def _sell(self, view, state, label: str, otype: OrderType,
              price: float | None = None) -> OrderIntent:
        return OrderIntent(
            strategy=STRATEGY_NAME, label=label, side=Side.SELL,
            order_type=otype, price=price,
            signal_date=view.mc_date, signal_time=view.mc_time,
            seq=state.next_seq(),
        )

    def _live_entry_block(self, view: MarketView) -> bool:
        if self.config.mode is Mode.MC12:
            return False
        return bool(self.config.params.get("live_block_last_n_bars", 0)) and False
