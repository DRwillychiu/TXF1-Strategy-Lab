"""L2_TrendShort —— 移植自 Trendbearish_V54_RESEARCH (v5.4)。

行為等同 v5.3：v5.4 的 CHANGELOG 明載「untouched to the character」，
只改 label 字串。

規格表：docs/specs/L2_TrendShort_spec.md
本檔的區段編號與 .pla 的 SECTION 一一對應，方便逐段對照。

**MC12 模式一律照抄，包含已知缺陷。** 規格表第十節列出的 D-1 到 D-10
在本檔中全部原樣保留，每一處都標了 `# [D-n]`。修正只能進 V2 模式。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.indicators.core import (
    avg_true_range,
    average,
    lowest,
    highest,
    xaverage,
    zlema_comp_price,
)
from txfcore.strategies.base import (
    MarketView,
    Mode,
    PerSessionState,
    PerTradeState,
    Strategy,
    StrategyConfig,
    StrategyState,
)
from txfcore.types.bar import Series
from txfcore.types.mctime import DayOfWeek, day_of_week
from txfcore.types.orders import (
    Decision,
    MarketPosition,
    OrderIntent,
    OrderType,
    ProtectiveStop,
    Side,
)

STRATEGY_NAME = "L2_TrendShort"

# --- SECTION 1  INPUTS（.pla 的 inputs 全部搬到這裡）---
DEFAULT_PARAMS: dict = {
    "WkSMA_Len": 13,
    "DC_Len": 30,
    "ZLEMA_Len": 20,
    "ZLEMA_Lag": 9,
    "ATR_Len": 21,
    "C0_ATR_Filter": 0.45,
    "SL_ATR_Ratio": 1.1,
    "Accel_M": 0.5,
    "NLow_N": 15,
    "MinBars": 3,
    "TSL_K": 9,
    "TSL_M": 1.0,
    "TP_N": 30,
    "TTP_MinAtr": 4.0,
    "TTP_RebPct": 1.5,
    "stopProfitPoints_Shrt": 250,
    "profitReturnPrcnt_Shrt": 55,
    "SL_Pct": 1.25,
    # --- LIVE 模式專用，MC12 模式一律忽略 ---
    # 「收盤前兩根禁止進場」。60M 週期上是否套用尚未拍板，預設關閉。
    "live_block_last_n_bars": 0,
}

# --- SECTION 4  時段判定 ---
# [D-6] IsDay 上限 1245，所以 13:45 那根落在 IsNight。
#       後果：日盤收盤那根走優先級 6（收盤確認 + 次根市價），
#       而次根開盤在 15:00，中間 1 小時 15 分無自訂停損單。
#       下限 845 永不生效 —— 60M 網格上沒有 845..944 的戳記。
IS_DAY_LOWER = 845
IS_DAY_UPPER = 1245

# 週線取樣觸發點。[D-4] 取的是週五 12:45 收盤，不是註解宣稱的 13:45。
WEEKLY_SAMPLE_TIME = 1245


@dataclass(slots=True)
class L2PerTrade(PerTradeState):
    """平倉時必須全部回到初始值。assert_clean() 會檢查。"""

    # S8 初始停損
    sl_line: float = 0.0
    sl_trig: float = 0.0
    sl_locked: bool = False
    # S9 TSL 啟動
    accel: bool = False
    nlow: bool = False
    c1_bar: bool = False
    c1_bar_prev: bool = False
    tsl_armed: bool = False
    # S10 TSL 追蹤
    tsl_line: float = 0.0
    active_tsl: float = 0.0
    active_sl: float = 0.0
    sl_src: int = 0  # 0=空手 1=追蹤 2=凍結初始
    # S11 回抽停利
    lowest_close: float = 0.0
    ttp_gate: bool = False
    ttp_fire: bool = False
    # S12 峰值回吐保護
    posble_profit: float = 0.0
    stop_profit_price: float = 0.0

    def reset(self) -> None:
        for name, value in (
            ("sl_line", 0.0), ("sl_trig", 0.0), ("sl_locked", False),
            ("accel", False), ("nlow", False), ("c1_bar", False),
            ("c1_bar_prev", False), ("tsl_armed", False),
            ("tsl_line", 0.0), ("active_tsl", 0.0), ("active_sl", 0.0),
            ("sl_src", 0), ("lowest_close", 0.0), ("ttp_gate", False),
            ("ttp_fire", False), ("posble_profit", 0.0),
            ("stop_profit_price", 0.0),
        ):
            setattr(self, name, value)


@dataclass(slots=True)
class L2PerSession(PerSessionState):
    """跨交易存活。週線陣列與 EMA 狀態永不隨平倉重置。"""

    # S5 週線濾網。索引 0 不用，1..13 有效，完全比照 .pla 的 WkCloses[21]。
    wk_closes: list[float] = field(default_factory=lambda: [0.0] * 21)
    wk_bar_count: int = 0
    wk_sma_sum: float = 0.0
    filter_ok: bool = False
    # S6 指標。MC 的 XAverage 內部帶狀態，這裡顯式保存。
    zlema_val: float = 0.0
    zlema_prev: float = 0.0
    ema20_val: float = 0.0
    zlema_seeded: bool = False
    ema20_seeded: bool = False
    comp_price: Series = field(default_factory=Series)
    # S7 re-entry 標籤狀態（v5.4，無行為影響）
    last_entry_price: float = 0.0
    reentry_armed: bool = False
    reentry_price: float = 0.0


class L2TrendShort(Strategy[L2PerTrade, L2PerSession]):
    """60 分鐘、單一資料流、純空、IOG = false。

    五支裡最單純的一支：無 Data2/Data3、無未來函數、
    ExitFired 保證單根單張、單一部位。
    """

    def __init__(self, config: StrategyConfig | None = None) -> None:
        cfg = config or StrategyConfig(
            name=STRATEGY_NAME,
            instrument="TXF",
            holiday_flat_time=300,  # L2 是 03:00，不是其他四支的 415
            params=dict(DEFAULT_PARAMS),
        )
        for key, value in DEFAULT_PARAMS.items():
            cfg.params.setdefault(key, value)
        super().__init__(cfg)

    # ------------------------------------------------------------------
    def initial_state(self) -> StrategyState[L2PerTrade, L2PerSession]:
        return StrategyState(per_trade=L2PerTrade(), per_session=L2PerSession())

    def expected_trigger_range(self) -> tuple[int, int]:
        """事前登記（判官 4）。**來源是 anchor 文件，不是標頭。**

        `docs/research/L2_v5.4_label_anchor_result_20260825.md`：
        77 筆 / 2,670,000 / PF 2.7456，進場拆分 **TS_Entry 57 + TS_ReEntry 20**。

        標頭那組 55 / 22 是**事前登記**，該文件的 R-2 已推翻它。

        自 2025-06-03 起 **443 天零交易**——移植驗收：那之後必須也是 0 筆。
        """
        return (77, 77)

    # ------------------------------------------------------------------
    def on_bar(
        self, view: MarketView, state: StrategyState[L2PerTrade, L2PerSession]
    ) -> tuple[StrategyState[L2PerTrade, L2PerSession], Decision]:
        p = self.config.params
        pt, ps = state.per_trade, state.per_session
        bars = view.data1
        decision = Decision()

        # ===== SECTION 4  時段判定 =====
        is_day = IS_DAY_LOWER <= view.mc_time <= IS_DAY_UPPER
        is_night = not is_day  # [D-6] 13:45 那根落在這裡

        # ===== SECTION 4B  行事曆（由 tradecal 提供，五支共用） =====
        cal = view.calendar

        # ===== SECTION 5  週線濾網 =====
        self._weekly_filter(view, ps, p)

        # ===== SECTION 6  指標 =====
        atr = avg_true_range(bars, p["ATR_Len"])
        dc_lower = lowest(bars.low, p["DC_Len"], offset=1)  # Lowest(Low[1], 30)

        ps.comp_price.push(zlema_comp_price(bars.close, p["ZLEMA_Lag"]))
        ps.zlema_prev = ps.zlema_val
        ps.zlema_val = xaverage(
            ps.comp_price, p["ZLEMA_Len"], ps.zlema_val if ps.zlema_seeded else None
        )
        ps.zlema_seeded = True
        ps.ema20_val = xaverage(
            bars.close, p["ZLEMA_Len"], ps.ema20_val if ps.ema20_seeded else None
        )
        ps.ema20_seeded = True

        close = bars.close[0]
        pos = view.position

        # ===== SECTION 7  進場條件 =====
        c0 = close < (dc_lower - atr * p["C0_ATR_Filter"])
        c_a = ps.zlema_val < ps.zlema_prev
        c_b = ps.zlema_val < ps.ema20_val

        # --- P3b 引擎停損（只在非空手時設定，建倉後凍結）---
        # [D-1] 錨點是訊號棒的 Close，而 S8 的自訂停損錨在 EntryPrice。
        #       兩者在不同 K 棒上計算，DC_Lower 與 ATR 值不同。
        #       .pla 註解明載理由（EntryPrice 在成交前不存在），屬刻意設計。
        if pos.market_position is not MarketPosition.SHORT:
            guard = abs((dc_lower + atr * p["SL_ATR_Ratio"]) - close)
            if p["SL_Pct"] > 0:
                guard = min(guard, close * p["SL_Pct"] / 100.0)
            decision.protective = ProtectiveStop(
                strategy=STRATEGY_NAME,
                distance=guard,
                per_contract=True,  # SetStopContract
                signal_date=view.mc_date,
                signal_time=view.mc_time,
            )

        # --- re-entry 標籤狀態（v5.4，無行為影響）---
        if pos.market_position is MarketPosition.SHORT:
            ps.last_entry_price = pos.entry_price
        if (
            state.prev_market_position is MarketPosition.SHORT
            and pos.market_position is MarketPosition.FLAT
        ):
            # <= 0 而非 < 0：兩口的最小虧損正好是毛 0，
            # 用 <= 讓判斷在毛/淨兩種口徑下一致。
            ps.reentry_armed = pos.prev_position_profit <= 0
            ps.reentry_price = ps.last_entry_price

        entry_blocked_live = self._live_entry_block(view)

        if (
            ps.filter_ok
            and c0
            and c_a
            and c_b
            and not cal.holiday_block
            and not cal.settlement_day
            and pos.market_position is MarketPosition.FLAT
            and not entry_blocked_live
        ):
            is_reentry = (
                ps.reentry_armed
                and ps.reentry_price > 0
                and close <= ps.reentry_price
            )
            decision.add(
                OrderIntent(
                    strategy=STRATEGY_NAME,
                    label="TS_ReEntry" if is_reentry else "TS_Entry",
                    side=Side.SELL_SHORT,
                    order_type=OrderType.MARKET,
                    signal_date=view.mc_date,
                    signal_time=view.mc_time,
                    seq=state.next_seq(),
                )
            )
            ps.reentry_armed = False

        in_short = pos.market_position is MarketPosition.SHORT

        # ===== SECTION 8  初始停損（進場當根鎖定） =====
        if in_short:
            if pos.bars_since_entry == 0 and not pt.sl_locked:
                pt.sl_line = dc_lower
                pt.sl_trig = pt.sl_line + atr * p["SL_ATR_Ratio"]
                if p["SL_Pct"] > 0:
                    # 空單取較低天花板 = 較緊。方向正確。
                    pt.sl_trig = min(
                        pt.sl_trig,
                        pos.entry_price + pos.entry_price * p["SL_Pct"] / 100.0,
                    )
                pt.sl_locked = True
        else:
            pt.sl_line = 0.0
            pt.sl_trig = 0.0
            pt.sl_locked = False

        # ===== SECTION 9  TSL 啟動 =====
        if in_short:
            open_ = bars.open[0]
            pt.c1_bar_prev = pt.c1_bar
            pt.accel = (open_ - close) > (atr * p["Accel_M"]) and close < open_
            pt.nlow = close < lowest(bars.close, p["NLow_N"], offset=1)
            pt.c1_bar = pt.accel and pt.nlow
            if (
                not pt.tsl_armed
                and pt.c1_bar
                and pt.c1_bar_prev
                and pos.bars_since_entry >= p["MinBars"]
            ):
                pt.tsl_armed = True
        else:
            pt.accel = False
            pt.nlow = False
            pt.c1_bar = False
            pt.c1_bar_prev = False
            pt.tsl_armed = False

        # ===== SECTION 10  TSL 追蹤 =====
        if in_short:
            if pt.tsl_armed:
                new_tsl = lowest(bars.close, p["TSL_K"], offset=1) + atr * p["TSL_M"]
                pt.tsl_line = new_tsl if pt.tsl_line == 0 else min(pt.tsl_line, new_tsl)
                pt.active_tsl = pt.tsl_line + atr * p["SL_ATR_Ratio"]
                # [D-2] 比較的是 tsl_line，使用的是 active_tsl，兩者差 ATR*1.1。
                #       所以 active_sl 不是單調收緊的：
                #         機制一 啟動瞬間可從 sl_trig 跳到更高（更鬆）的 active_tsl
                #         機制二 active_tsl 掛著當根 ATR，ATR 擴張時停損往上跑
                # [D-3] SL_Pct 沒有套用在 active_tsl 上 —— 標頭宣稱
                #       "Applied to BOTH engine and custom stop" 並不包含追蹤路徑。
                if pt.tsl_line < pt.sl_trig:
                    pt.active_sl = pt.active_tsl
                    pt.sl_src = 1
                else:
                    pt.active_sl = pt.sl_trig
                    pt.sl_src = 2
            else:
                pt.tsl_line = 0.0
                pt.active_tsl = 0.0
                pt.active_sl = pt.sl_trig
                pt.sl_src = 2
        else:
            pt.tsl_line = 0.0
            pt.active_tsl = 0.0
            pt.active_sl = 0.0
            pt.sl_src = 0

        # ===== SECTION 11  回抽停利 =====
        if in_short:
            if pos.bars_since_entry == 0:
                pt.lowest_close = close
            else:
                pt.lowest_close = min(pt.lowest_close, close)
            wave_profit = pos.entry_price - pt.lowest_close
            # [D-7] min_profit_pts 用當根 ATR，且 ttp_gate 不閂鎖。
            #       ATR 上升會讓已達標的交易退回未達標。
            min_profit_pts = atr * p["TTP_MinAtr"]
            ttp_line = pt.lowest_close * (1.0 + p["TTP_RebPct"] / 100.0)
            pt.ttp_gate = wave_profit >= min_profit_pts
            pt.ttp_fire = pt.ttp_gate and close > ttp_line
        else:
            pt.lowest_close = 0.0
            pt.ttp_gate = False
            pt.ttp_fire = False

        # ===== SECTION 12  峰值回吐保護 =====
        if pos.market_position is MarketPosition.FLAT:
            pt.posble_profit = 0.0
            pt.stop_profit_price = 0.0
        if in_short:
            profit = pos.entry_price - close
            if profit >= p["stopProfitPoints_Shrt"]:
                pt.posble_profit = max(pt.posble_profit, profit)
                pt.stop_profit_price = pos.entry_price - (
                    pt.posble_profit
                    * (1.0 - p["profitReturnPrcnt_Shrt"] / 100.0)
                )

        # ===== SECTION 13  出場鏈（ExitFired 短路，保證單根單張） =====
        if in_short:
            self._exit_chain(view, state, decision, is_day, is_night)

        # ===== 最末行：CLAUDE.md Rule #8 =====
        state.prev_market_position = pos.market_position
        return state, decision

    # ------------------------------------------------------------------
    def _weekly_filter(
        self, view: MarketView, ps: L2PerSession, p: dict
    ) -> None:
        """SECTION 5。

        [D-4] 觸發點是「週五 12:45 那根的下一根」，取的是 Close[1]
              = 週五 12:45 的收盤，不是註解宣稱的 13:45 日盤收盤。
              偏移一致所以 SMA 內部自洽，但照註解寫 Python 會錯。
        """
        bars = view.data1
        if len(bars) < 2:
            return
        prev = bars[1]
        is_new_week = (
            prev.mc_time == WEEKLY_SAMPLE_TIME
            and day_of_week(prev.mc_date) is DayOfWeek.FRI
        )
        if not is_new_week:
            return

        n = p["WkSMA_Len"]
        for i in range(n, 1, -1):  # 陣列右移
            ps.wk_closes[i] = ps.wk_closes[i - 1]
        ps.wk_closes[1] = prev.close
        if ps.wk_bar_count < n:
            ps.wk_bar_count += 1
        ps.wk_sma_sum = sum(ps.wk_closes[1 : ps.wk_bar_count + 1])
        if ps.wk_bar_count >= n:
            ps.filter_ok = ps.wk_closes[1] < (ps.wk_sma_sum / n)
        else:
            ps.filter_ok = False  # 暖機保護

    def _live_entry_block(self, view: MarketView) -> bool:
        """LIVE / V2 模式的「收盤前兩根禁止進場」。

        MC12 模式永遠回傳 False —— 這條規則 MC 沒有，套用會對不上帳。
        60M 週期是否套用尚未拍板（規格表第十二節第 6 項），預設關閉。
        """
        if self.config.mode is Mode.MC12:
            return False
        n = self.config.params.get("live_block_last_n_bars", 0)
        return bool(n) and False  # 待拍板後實作網格判定

    def _exit_chain(
        self,
        view: MarketView,
        state: StrategyState[L2PerTrade, L2PerSession],
        decision: Decision,
        is_day: bool,
        is_night: bool,
    ) -> None:
        """SECTION 13。優先級 0 到 6，ExitFired 短路。

        [D-5] 優先級 4 一旦成立，5 與 6 永不執行 —— 自訂停損單不再掛出，
              保護只剩凍結的 P3b 引擎停損。標頭統計 45 筆虧損出場中有
              4 筆是 "engine Stop Loss"，應即此路徑。
        """
        p = self.config.params
        pt = state.per_trade
        cal = view.calendar
        close = view.data1.close[0]

        def cover(label: str, price: float | None = None) -> None:
            decision.add(
                OrderIntent(
                    strategy=STRATEGY_NAME,
                    label=label,
                    side=Side.BUY_TO_COVER,
                    order_type=OrderType.MARKET if price is None else OrderType.STOP,
                    price=price,
                    signal_date=view.mc_date,
                    signal_time=view.mc_time,
                    seq=state.next_seq(),
                )
            )

        # 優先級 0
        if self.config.mc_manual_kill_switch:
            return cover("TS_Kill")
        if cal.registry_expired:
            return cover("TS_RegistryEnd")
        if cal.holiday_block and view.mc_time >= self.config.holiday_flat_time:
            return cover("TS_Holiday")
        if cal.settlement_day and view.mc_time >= self.config.settlement_flat_time:
            return cover("TS_Settlement")

        # 優先級 1  週線濾網強制出場
        ps = state.per_session
        n = p["WkSMA_Len"]
        if (
            day_of_week(view.mc_date) is DayOfWeek.FRI
            and view.mc_time == WEEKLY_SAMPLE_TIME
            and ps.wk_bar_count >= n
            and close > (ps.wk_sma_sum / n)
        ):
            return cover("TS_WeeklyExit")

        # 優先級 2  結構反轉停利
        if close > highest(view.data1.close, p["TP_N"], offset=1):
            return cover("TS_StructureTP")

        # 優先級 3  回抽停利
        if pt.ttp_fire:
            return cover("TS_TTP")

        # 優先級 4  峰值回吐保護  [D-5] 遮蔽 5 與 6
        if pt.stop_profit_price > 0:
            return cover("TS_StopProfit", price=pt.stop_profit_price)

        # 優先級 5  日盤停價單
        if is_day and pt.active_sl > 0:
            label = "TS_TSL_D" if pt.sl_src == 1 else "TS_InitSL_D"
            return cover(label, price=pt.active_sl)

        # 優先級 6  夜盤收盤確認 + 次根市價
        if is_night and pt.active_sl > 0 and close > pt.active_sl:
            label = "TS_TSL_N" if pt.sl_src == 1 else "TS_InitSL_N"
            return cover(label)
