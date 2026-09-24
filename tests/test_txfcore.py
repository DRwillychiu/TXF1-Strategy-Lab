"""txfcore 測試。

重點不在覆蓋率，在於把規格表的承諾變成會叫的東西。
每個測試都標了它守的是哪一條。
"""

from __future__ import annotations

from datetime import date

import pytest

from txfcore.costs.fees import cost_in_points, round_trip_cost, tax
from txfcore.instruments.spec import TMF, TXF, get
from txfcore.indicators.core import avg_true_range, average, highest, lowest
from txfcore.metrics.drawdown import compute, equity_curve, portfolio_mdd
from txfcore.strategies.base import MarketView, PositionView, StrategyState
from txfcore.strategies.l2_trendshort import L2PerSession, L2PerTrade, L2TrendShort
from txfcore.tradecal.gates import evaluate, is_holiday_tail, is_settlement_day
from txfcore.tradecal.registry import HOLIDAY_TAIL, REGISTRY_VALID_UNTIL
from txfcore.types.bar import Bar, BarSeries, FutureDataError, Series
from txfcore.types.mctime import (
    DayOfWeek,
    day_of_week,
    mc_date_to_date,
    trading_day,
)
from txfcore.types.orders import MarketPosition, OrderIntent, OrderType, Side


# ====================================================================
# 型別層：未來資料必須「寫不出來」，不是「測得出來」
# ====================================================================

def test_negative_offset_is_future_data():
    s = Series([1.0, 2.0, 3.0])
    assert s[0] == 3.0
    assert s[1] == 2.0
    with pytest.raises(FutureDataError):
        _ = s[-1]


def test_bar_series_blocks_future():
    bs = BarSeries("data1")
    bs.push(Bar(1260101, 1245, 1, 2, 0, 1))
    with pytest.raises(FutureDataError):
        _ = bs[-1]


def test_window_semantics_match_powerlanguage():
    """window(3, 1) 應等於 [1], [2], [3]，也就是排除當根。"""
    s = Series([10.0, 20.0, 30.0, 40.0])
    assert s.window(3, 1) == [30.0, 20.0, 10.0]


# ====================================================================
# 時間層：trading_day 是全系統唯一實作
# ====================================================================

def test_mc_date_conversion():
    assert mc_date_to_date(1260906) == date(2026, 9, 6)
    assert mc_date_to_date(1190913) == date(2019, 9, 13)


def test_day_of_week_is_sunday_zero():
    """PowerLanguage: Sun=0 .. Sat=6。L5 v19.7 FIX 1 記錄了 7 是死碼。"""
    assert day_of_week(1260906) is DayOfWeek.SUN   # 2026-09-06 是週日
    assert day_of_week(1260904) is DayOfWeek.FRI


def test_trading_day_night_tail_rolls_back():
    """00:00-05:00 的 K 棒日期戳是隔天，交易日要退回前一曆日。"""
    assert trading_day(1260907, 300) == date(2026, 9, 6)
    assert trading_day(1260907, 1245) == date(2026, 9, 7)
    # 邊界：05:00 仍屬前一交易日，05:01 之後不再是尾段
    assert trading_day(1260907, 500) == date(2026, 9, 6)


# ====================================================================
# 行事曆層：五支共用
# ====================================================================

def test_registry_has_63_entries():
    assert len(HOLIDAY_TAIL) == 63
    assert HOLIDAY_TAIL[-1] == REGISTRY_VALID_UNTIL


def test_holiday_tail_only_matches_night_segment():
    """.pla 只在 Time <= 500 掃描。日盤同一天不得命中。"""
    assert is_holiday_tail(1260212, 300) is True
    assert is_holiday_tail(1260212, 1245) is False


def test_settlement_is_third_wednesday():
    # 2026-09-16 是九月第三個週三
    assert is_settlement_day(1260916) is True
    assert is_settlement_day(1260909) is False   # 第二個週三
    assert is_settlement_day(1260917) is False   # 週四


def test_registry_expiry_fails_safe():
    """走出已驗證的地圖之外必須同時封鎖進場，不是只警告。"""
    st = evaluate(1270102, 1245)
    assert st.registry_expired is True
    assert st.holiday_block is True


# ====================================================================
# 指標層
# ====================================================================

def test_lowest_with_offset_excludes_current_bar():
    """DC_Lower = Lowest(Low[1], 30) 必須排除當根。"""
    s = Series([5.0, 4.0, 3.0, 99.0])
    assert lowest(s, 3, offset=1) == 3.0


def test_average_matches_sma():
    s = Series([1.0, 2.0, 3.0, 4.0])
    assert average(s, 4) == 2.5


def test_atr_is_simple_average_not_wilder():
    """MC 的 AvgTrueRange = Average(TrueRange, n)，不是 Wilder 平滑。"""
    bs = BarSeries("d1")
    for i in range(5):
        bs.push(Bar(1260101, 1245, 100.0, 110.0, 90.0, 100.0))
    assert avg_true_range(bs, 3) == pytest.approx(20.0)


# ====================================================================
# 成本層
# ====================================================================

def test_tax_scales_with_price_not_constant():
    """期交稅按契約金額課，不可能是常數 —— 試算表的固定 42 是近似值。"""
    assert tax(TMF, 22000) == pytest.approx(4.4)
    assert tax(TMF, 20000) == pytest.approx(4.0)
    assert tax(TMF, 22000) != tax(TMF, 20000)


def test_micro_round_trip_cost():
    """微台 22000 點：(12 + 4.4) x 2 = 32.8，不是試算表用的 42。"""
    assert round_trip_cost(TMF, 22000, 22000, 1) == pytest.approx(32.8)


def test_cost_in_points_for_big_contract():
    """CLAUDE.md 的「成本門檻常數必須 >= 10 點」是為大台訂的。"""
    pts = cost_in_points(TXF, 22000, 22000)
    assert pts == pytest.approx((32 + 22000 * 200 * 0.00002) * 2 / 200)


# ====================================================================
# 回撤指標：定義見規劃書
# ====================================================================

def test_drawdown_denominator_is_rolling_peak():
    """分母是滾動峰值，不是期初資金。值域必須有界在 100% 以內。"""
    eq = [100.0, 120.0, 60.0, 130.0]
    r = compute(eq)
    assert r.drawdown[2] == pytest.approx(0.5)      # (120-60)/120
    assert r.max_drawdown == pytest.approx(0.5)
    assert r.max_drawdown_amount == pytest.approx(60.0)
    assert max(r.drawdown) <= 1.0


def test_mdd_picks_largest_percentage_not_largest_amount():
    """金額最大與百分比最大不是同一對峰谷。**MDD 取百分比。**

    **裁決 2026-09-08（選項 A）：金額跟著百分比走。**

    `max_drawdown_amount` 改為「最大百分比那一點的金額」，
    不再是獨立追蹤的最大絕對金額。理由：MDD 的定義是
    「每日動態回撤曲線中的最高點」——那是一個時點，
    而那個時點的金額只有一個。

    最大絕對金額保留為 `peak_to_valley_amount`，
    **但它衡量的是規模不是風險**——固定口數下，
    權益成長後晚期的絕對金額必然更大。
    """
    eq = [100.0, 50.0, 500.0, 440.0]
    r = compute(eq)
    assert r.max_drawdown == pytest.approx(0.5)           # 100 -> 50
    assert r.max_drawdown_index == 1
    assert r.max_drawdown_amount == pytest.approx(50.0)   # **該點的金額**
    assert r.peak_to_valley_amount == pytest.approx(60.0)  # 500 -> 440
    assert r.peak_to_valley_index == 3
    # 一致性：金額必須等於該點的 峰值 − 權益
    i = r.max_drawdown_index
    assert r.max_drawdown_amount == pytest.approx(r.peak[i] - r.equity[i])


def test_mdd_equals_peak_of_daily_drawdown_curve():
    """MDD 天生等於每日回撤曲線的最高點，兩者永不矛盾。"""
    eq = equity_curve(300000, [-10000, 5000, -40000, 20000, -5000])
    r = compute(eq)
    assert r.max_drawdown == pytest.approx(max(r.drawdown))


def test_portfolio_mdd_is_not_the_sum_of_parts():
    """各支的最深回撤發生在不同時間點，相加會高估。"""
    # 兩支各自回撤 100 並完全回復，但發生在不同時間點
    a = [-100.0, 100.0, 0.0, 0.0]
    b = [0.0, 0.0, -100.0, 100.0]
    combined = portfolio_mdd(1000, [a, b])
    sep_a = compute(equity_curve(1000, a)).max_drawdown_amount
    sep_b = compute(equity_curve(1000, b)).max_drawdown_amount
    assert combined.max_drawdown_amount < sep_a + sep_b


def test_portfolio_requires_aligned_series():
    with pytest.raises(ValueError):
        portfolio_mdd(1000, [[1.0, 2.0], [1.0]])


# ====================================================================
# 訂單型別
# ====================================================================

def test_market_order_must_not_carry_price():
    with pytest.raises(ValueError):
        OrderIntent(
            strategy="X", label="L", side=Side.BUY,
            order_type=OrderType.MARKET, price=100.0,
        )


def test_stop_order_must_carry_price():
    with pytest.raises(ValueError):
        OrderIntent(
            strategy="X", label="L", side=Side.BUY,
            order_type=OrderType.STOP,
        )


def test_strategy_output_carries_no_quantity():
    """裁決 2026-09-06：口數由風險層決定。

    策略輸出口數的話，風險層只能否決不能調整。
    型別上拿掉 quantity，這件事就不可能被繞過。
    """
    from dataclasses import fields as _fields
    assert "quantity" not in {f.name for f in _fields(OrderIntent)}


def test_sized_order_requires_positive_quantity():
    from txfcore.types.orders import SizedOrder
    intent = OrderIntent(
        strategy="X", label="L", side=Side.BUY, order_type=OrderType.MARKET
    )
    with pytest.raises(ValueError):
        SizedOrder(intent=intent, quantity=0)
    assert SizedOrder(intent=intent, quantity=2).idem_key == intent.idem_key


def test_instrument_has_no_capital_field():
    """**資金不在 Instrument 上。** 單一來源是 capital.py。

    2026-09-10 移除 backtest_capital：它是 9/6 的舊裁決，與 capital.py 並存
    導致同一份資料跑不同工具會得到不同的百分比。
    """
    from dataclasses import fields
    from txfcore.instruments.spec import Instrument
    assert "backtest_capital" not in {f.name for f in fields(Instrument)}


def test_fees_are_the_confirmed_broker_rates():
    """券商實際費率，2026-09-10 確認：TXF 32 · MXF 15 · TMF 12 元/口/邊。"""
    from txfcore.instruments.spec import get
    assert get("TXF").fee_per_side == 32.0
    assert get("MXF").fee_per_side == 15.0
    assert get("TMF").fee_per_side == 12.0

def test_instrument_tick_size():
    """L5 的 v_TickSize = MinMove / PriceScale。"""
    assert get("TXF").tick_size == 1.0


def test_idem_key_is_stable_and_distinct():
    kw = dict(
        strategy="L2_TrendShort", label="TS_Entry", side=Side.SELL_SHORT,
        order_type=OrderType.MARKET,
        signal_date=1260906, signal_time=1245,
    )
    a = OrderIntent(**kw, seq=1)
    b = OrderIntent(**kw, seq=1)
    c = OrderIntent(**kw, seq=2)
    assert a.idem_key == b.idem_key
    assert a.idem_key != c.idem_key


# ====================================================================
# L2 策略層
# ====================================================================

def _build_view(bars: BarSeries, position: PositionView) -> MarketView:
    cur = bars[0]
    return MarketView(
        data1=bars,
        position=position,
        calendar=evaluate(cur.mc_date, cur.mc_time),
        mc_date=cur.mc_date,
        mc_time=cur.mc_time,
    )


def _flat_market(n: int = 60, close: float = 20000.0) -> BarSeries:
    bs = BarSeries("data1")
    for _ in range(n):
        bs.push(Bar(1260901, 1245, close, close + 1, close - 1, close))
    return bs


def test_l2_registers_expected_trigger_range():
    """判官 (4)：預期觸發次數必須事前登記。"""
    # 2026-09-07 修正：anchor 文件給的是 77，標頭的 78 是另一次量測
    assert L2TrendShort().expected_trigger_range() == (77, 77)


def test_l2_holiday_flat_time_is_300_not_415():
    """五支的 Holiday_Flat_Time 不共用：L1=345 L2=300 L3/L4/L5=415。"""
    assert L2TrendShort().config.holiday_flat_time == 300


def test_l2_no_entry_without_weekly_filter():
    """暖機未滿 13 週時 filter_ok 為 False，不得進場。"""
    s = L2TrendShort()
    state = s.initial_state()
    bars = _flat_market()
    state, decision = s.on_bar(_build_view(bars, PositionView()), state)
    assert decision.orders == []
    assert state.per_session.filter_ok is False


def test_l2_sets_protective_stop_when_flat():
    """P3b 引擎停損只在非空手時設定，建倉後凍結。"""
    s = L2TrendShort()
    state = s.initial_state()
    bars = _flat_market()
    _, decision = s.on_bar(_build_view(bars, PositionView()), state)
    assert decision.protective is not None
    assert decision.protective.per_contract is True

    short = PositionView(
        market_position=MarketPosition.SHORT, entry_price=20000.0
    )
    _, decision2 = s.on_bar(_build_view(bars, short), s.initial_state())
    assert decision2.protective is None


def test_l2_per_trade_state_clean_after_flat():
    """跨交易狀態殘留是規格表第六節點名的缺陷類別。"""
    pt = L2PerTrade()
    pt.sl_locked = True
    pt.tsl_line = 19000.0
    pt.reset()
    pt.assert_clean()


def test_l2_exit_chain_is_single_order():
    """ExitFired 短路：L2 保證單根單張。這是它與 L1/L3/L5 的關鍵差異。"""
    s = L2TrendShort()
    state = s.initial_state()
    bars = _flat_market()
    short = PositionView(
        market_position=MarketPosition.SHORT,
        entry_price=20000.0,
        bars_since_entry=5,
    )
    _, decision = s.on_bar(_build_view(bars, short), state)
    assert len(decision.orders) <= 1


def test_l2_settlement_day_forces_cover():
    """優先級 0d：結算日 Time >= 1230 強制平倉。"""
    s = L2TrendShort()
    state = s.initial_state()
    bs = BarSeries("data1")
    for _ in range(60):
        bs.push(Bar(1260916, 1245, 20000, 20001, 19999, 20000))  # 第三個週三
    short = PositionView(
        market_position=MarketPosition.SHORT, entry_price=20000.0, bars_since_entry=3
    )
    _, decision = s.on_bar(_build_view(bs, short), state)
    assert [o.label for o in decision.orders] == ["TS_Settlement"]


def test_l2_settlement_day_blocks_entry_all_day():
    """結算日整天封鎖進場，不只 12:30 之後。"""
    s = L2TrendShort()
    state = s.initial_state()
    state.per_session.filter_ok = True
    state.per_session.wk_bar_count = 13
    bs = BarSeries("data1")
    for _ in range(60):
        bs.push(Bar(1260916, 945, 20000, 20001, 19999, 20000))
    _, decision = s.on_bar(_build_view(bs, PositionView()), state)
    assert all(o.label not in ("TS_Entry", "TS_ReEntry") for o in decision.orders)


def test_l2_1345_bar_is_night():
    """[D-6] 13:45 那根落在 IsNight，走優先級 6 而非 5。"""
    s = L2TrendShort()
    state = s.initial_state()
    state.per_trade.sl_trig = 20500.0
    state.per_trade.active_sl = 20500.0
    state.per_trade.sl_src = 2
    bs = BarSeries("data1")
    for _ in range(60):
        bs.push(Bar(1260901, 1345, 21000, 21001, 20999, 21000))
    short = PositionView(
        market_position=MarketPosition.SHORT, entry_price=20000.0, bars_since_entry=5
    )
    _, decision = s.on_bar(_build_view(bs, short), state)
    labels = [o.label for o in decision.orders]
    assert "TS_InitSL_D" not in labels


# ====================================================================
# 變數歷史：PowerLanguage 的每個變數都自帶 [1]
# ====================================================================

def test_var_history_matches_powerlanguage():
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    x = vb.declare("v_X", 0.0)
    x.set(10.0); vb.commit_all()
    x.set(20.0); vb.commit_all()
    x.set(30.0)
    assert x[0] == 30.0
    assert x[1] == 20.0
    assert x[2] == 10.0


def test_var_returns_initial_when_history_short():
    """MC 的行為：歷史不足時回傳初始值，不報錯。

    暖機期的行為差異會讓早期交易對不上，所以必須照抄。
    """
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    x = vb.declare("v_X", 999.0)
    x.set(1.0)
    assert x[5] == 999.0


def test_var_blocks_future_offset():
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    x = vb.declare("v_X", 0.0)
    with pytest.raises(FutureDataError):
        _ = x[-1]


def test_l4_trailing_ratchet_semantics():
    """L4 的 v_Stop_Level = MinList(v_Stop_Level[1], ...) 靠歷史值。

    取錯了追蹤停損整條錯掉，而且不會報錯。
    """
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    stop = vb.declare("v_Stop_Level", 0.0)
    stop.set(20500.0); vb.commit_all()
    stop.set(min(stop[1], 20400.0)); vb.commit_all()   # 收緊
    assert stop.value == 20400.0
    stop.set(min(stop[1], 20600.0))                    # 想放鬆，被棘輪擋住
    assert stop.value == 20400.0


def test_varbook_snapshot_roundtrip():
    """state/ 持久化只存當根值，歷史由重放重建。"""
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    a = vb.declare("a", 0.0)
    b = vb.declare("b", False)
    a.set(1.5); b.set(True)
    snap = vb.snapshot()
    vb2 = VarBook()
    a2 = vb2.declare("a", 0.0)
    b2 = vb2.declare("b", False)
    vb2.restore(snap)
    assert a2.value == 1.5 and b2.value is True


# ====================================================================
# 移植版本對照 —— 裁決 2026-09-06：全部只移植 research 版
# ====================================================================

def test_all_five_targets_are_research_versions():
    """五支的 research 版正好都是 live 版加一層可觀測性。"""
    from txfcore.strategies.versions import PORTING_TARGETS
    assert len(PORTING_TARGETS) == 5
    expected = {
        "L1": ("V3.1", "v3.2"), "L2": ("5.3", "v5.4"), "L3": ("v15.0", "v15.1"),
        "L4": ("v14.6", "v14.7"), "L5": ("v19.9", "v19.9-R1"),
    }
    for v in PORTING_TARGETS:
        live_prefix, research = expected[v.key]
        assert v.live_version.startswith(live_prefix), v.key
        assert v.research_version == research, v.key


def test_baseline_hashes_are_pinned():
    """雜湊變了 → 該支對帳作廢重跑。防 L3 基準線事故的唯一機制。"""
    from txfcore.strategies.versions import PORTING_TARGETS
    for v in PORTING_TARGETS:
        assert len(v.live_sha256) == 64
        assert v.live_sha256 == v.live_sha256.upper()


def test_porting_order_matches_measured_complexity():
    """L2 最單純，L1 最難。執行層能力按這個順序疊加。"""
    from txfcore.strategies.versions import BY_KEY, PORTING_ORDER
    assert PORTING_ORDER == ("L2", "L4", "L3", "L5", "L1")
    assert set(PORTING_ORDER) == set(BY_KEY)


def test_failed_branches_are_recorded_not_forgotten():
    """L4 的 v15/v16 研究線已關閉，v18 是零觸發事故的原型。

    記錄「不採用的」與「採用的」同等重要——否則六個月後會有人重試一次。
    """
    from txfcore.strategies.versions import REJECTED_BRANCHES
    assert "L4_v18.0" in REJECTED_BRANCHES
    assert all("FAILED" in REJECTED_BRANCHES[k] or "前代" in REJECTED_BRANCHES[k]
               or "非 production" in REJECTED_BRANCHES[k] or "事故" in REJECTED_BRANCHES[k]
               for k in REJECTED_BRANCHES)


def test_l2_config_matches_its_porting_target():
    """已完成移植的 L2，其設定必須對得上版本表。"""
    from txfcore.strategies.l2_trendshort import L2TrendShort
    from txfcore.strategies.versions import BY_KEY
    assert BY_KEY["L2"].research_version == "v5.4"
    assert L2TrendShort().config.holiday_flat_time == 300   # L2 專屬，非 415


# ====================================================================
# 出場口數是策略決策 —— 2026-09-07 修正
# ====================================================================

def test_exit_quantity_is_a_strategy_decision():
    """**「口數由風險層決定」那個裁決只適用於進場。**

        進場口數   風險決策 —— 要下多大
        出場口數   策略決策 —— 要平掉部位的多少

    L5 的 40% 分批是策略的結構決定。把兩者合成一件事的後果：
    `FixedLotRiskGate` 把分批的 1 口覆寫成 2 口，於是每次分批都變成全平，
    **Stage 2/3 的 MFE 三階追蹤從未執行**——而那正是 L5 賺錢的機制。

    實測：修正前持倉 6008 根，Stage 2/3 = 0 根、分批 0 組。
    """
    o = OrderIntent(strategy="L5", label="BL_TP_Bot", side=Side.SELL,
                    order_type=OrderType.MARKET, from_entry="BL_Entry_Bot",
                    exit_quantity=1)
    assert o.exit_quantity == 1


def test_entry_intent_cannot_carry_exit_quantity():
    """進場單不得指定 exit_quantity —— 那是風險層的職責。"""
    with pytest.raises(ValueError, match="風險決策"):
        OrderIntent(strategy="X", label="E", side=Side.BUY,
                    order_type=OrderType.MARKET, exit_quantity=2)


def test_risk_gate_honours_strategy_exit_quantity():
    from txfcore.runtime.backtest import FixedLotRiskGate
    g = FixedLotRiskGate(2)
    entry = OrderIntent(strategy="X", label="E", side=Side.BUY,
                        order_type=OrderType.MARKET)
    partial = OrderIntent(strategy="X", label="TP", side=Side.SELL,
                          order_type=OrderType.MARKET, exit_quantity=1)
    assert g.size(entry).quantity == 2 and g.size(entry).sized_by == "fixed_lot"
    assert g.size(partial).quantity == 1
    assert g.size(partial).sized_by == "strategy_exit"


def test_orphaned_leg_order_must_not_block_siblings():
    """綁到不存在的腿時該單作廢，**不能中止整批**。

    2026-09-07 由 tools/signals.py 抓到：L5 的部位掛了 3416 根，
    而 Time_Stop_Bars 是 31——因為 BL_TimeExit_Bot 綁在不存在的 Bot 腿上，
    處理它之後就 break，Mid 那筆永遠處理不到。
    """
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "tools" / "signals.py"
           ).read_text(encoding="utf-8")
    assert "if leg is None:" in src and "continue" in src


# ====================================================================
# 結算日曆接上 —— 2026-09-08，孤兒模組修正
# ====================================================================

def test_gates_use_the_data_derived_settlement_calendar():
    """**我建了更準的日曆，然後從來沒接上去。**

    `gates.evaluate()` 一直用靜態規則，而那條規則漏標 2 天
    （2023-01-30 · 2026-02-23，農曆年後遞延）。
    **那兩天策略不知道是結算日，實盤上不會強制平倉。**

    典型的孤兒模組：寫好了、更準、沒人用。
    """
    from txfcore.tradecal.gates import evaluate, static_settlement_rule
    for d in (1230130, 1260223):
        assert evaluate(d, 1245).settlement_day is True
        assert static_settlement_rule(d) is False       # 靜態規則漏掉


def test_static_rule_still_available_for_mc12_mode():
    """mc12 模式要重現 MC 的行為，所以靜態規則必須保留。"""
    from txfcore.tradecal.gates import evaluate
    assert evaluate(1230130, 1245, use_data_settlement=False).settlement_day is False


# ====================================================================
# 期交所保證金　資料資產 —— 2026-09-08
# ====================================================================

def test_margin_chain_has_no_break():
    """**每筆的「調整前」必須等於前一筆的「調整後」。**

    斷鏈代表漏了一則公告。漏了就會用錯保證金，
    **而數字看起來仍然合理**——那是最危險的一類錯。
    """
    from txfcore.instruments.margin import verify_chain
    assert verify_chain() == []


def test_margin_ratio_equals_point_value_ratio():
    """**保證金比例恆等於點值比例 TX : MTX : TMF = 20 : 5 : 1。**

    六個時點全部成立。打破它代表期交所改了計算方式，或資料抄錯。
    """
    from txfcore.instruments.margin import POINT_VALUE, verify_ratio
    assert verify_ratio() == []
    assert POINT_VALUE["TX"] // POINT_VALUE["TMF"] == 20
    assert POINT_VALUE["MTX"] // POINT_VALUE["TMF"] == 5


def test_margin_refuses_dates_before_verified_range():
    """**超出已驗證範圍就拒絕，不外插也不猜。**

    與結算日曆同一個原則。
    """
    from datetime import date
    from txfcore.instruments.margin import MarginOutOfRange, as_of
    with pytest.raises(MarginOutOfRange):
        as_of(date(2020, 1, 1))
    assert as_of(date(2026, 5, 1)).initial == 26300      # 4/22 生效那筆
    assert as_of(date(2026, 9, 8)).initial == 35050      # 8/12 生效那筆


def test_backtest_uses_current_margin():
    """裁決 2026-09-08：**回測用當前最新保證金，不做歷史查表。**

    理由：回測是為了實戰，而實戰用的是現在的保證金。
    歷史序列留給 M6 的組合監控與事後歸因。
    """
    from txfcore.instruments.margin import ANNOUNCEMENTS, current
    assert current("TMF").initial == 35050
    assert current("TMF") == ANNOUNCEMENTS[-1].after["TMF"]


def test_short_account_cannot_hold_four_lots_at_current_margin():
    """空單帳戶 10 萬，4 口需 140,200 = 140%。

    **但 L2 是趨勢空頭，只在週 K 20MA 之下啟動**，
    多頭週期本來就不觸發，所以 4 口同時開倉是罕見情況。
    這個事實登記在此，供 M6 的組合監控使用。
    """
    from txfcore.instruments.margin import current, max_lots
    assert max_lots(100_000) == 2
    assert current().initial * 4 > 100_000


def test_margin_source_hash_pins_the_data():
    """改了資料而沒改雜湊，就是有人偷改。"""
    from txfcore.instruments.margin import source_hash
    h = source_hash()
    assert len(h) == 64 and h == h.upper()


def test_no_non_ascii_filenames_in_repo():
    """**Windows 的 tar 解不開中文檔名。**

    2026-09-08 實測：六份保證金 PDF 全部 "Invalid empty pathname"，
    而**解壓縮失敗時前面的檔案已經解好了，所以工具照樣能跑，
    只是資料不完整**——那是最難察覺的一種。
    """
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    bad = []
    for d in ("txfcore", "tools", "tests", "docs"):
        p = root / d
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if "__pycache__" in str(f):
                continue
            if not f.name.isascii():
                bad.append(str(f.relative_to(root)))
    assert not bad, f"非 ASCII 檔名，Windows tar 會失敗：{bad}"


def test_margin_pdf_hashes_are_pinned():
    """PDF 改名不改內容，雜湊可據此驗證安裝完整。"""
    from txfcore.instruments.margin import ANNOUNCEMENTS, PDF_SHA256
    assert len(PDF_SHA256) == 6
    for a in ANNOUNCEMENTS:
        assert a.source in PDF_SHA256, a.source
    for h in PDF_SHA256.values():
        assert len(h) == 64 and h == h.upper()


def test_drawdown_amount_always_matches_its_percentage_point():
    """**金額與百分比永遠指向同一個時點。**

    2026-09-08 實測（組合 ③ 曲線）曾出現：
      最大百分比 14.84% 於 2021-03-10，金額 704,970
      最大金額 1,290,274 於 2026-06-12，佔比僅 7.06%
    相差 1,920 天、585,304 元——**並列時極易誤讀**。
    """
    for eq in ([100, 120, 60, 200, 150],
               [1000, 900, 1100, 700, 1200, 1150],
               [50, 100, 25, 300, 290]):
        r = compute([float(x) for x in eq])
        i = r.max_drawdown_index
        assert r.max_drawdown_amount == pytest.approx(r.peak[i] - r.equity[i])
        assert r.peak_to_valley_amount >= r.max_drawdown_amount


# ====================================================================
# 資金配置　雙帳戶 —— 2026-09-08 定案
# ====================================================================

def test_capital_scales_by_point_value_ratio():
    """**點值比 = 資金比**，三商品的「可承受點數」必須相同。

    2026-09-08 修正：原規劃小台 240,000，比例是 1:4:20，
    可承受點數只有 2,400，**比另外兩個少 20%**。
    """
    from txfcore.instruments.capital import allocation
    a = [allocation(x) for x in ("TMF", "MXF", "TXF")]
    cushions = {round(x.points_of_cushion) for x in a}
    assert cushions == {3000}, cushions
    assert [x.per_strategy_nominal for x in a] == [60_000, 300_000, 1_200_000]
    assert [x.total for x in a] == [300_000, 1_500_000, 6_000_000]


def test_two_accounts_not_one_pool():
    """**多單與空單是兩個帳號。**

    2026-09-08 得知，先前全部按單帳戶做，已重寫。
    """
    from txfcore.instruments.capital import (
        LONG_ACCOUNT, SHORT_ACCOUNT, account_of, allocation, max_lots)
    a = allocation("TMF")
    assert a.long_account == 200_000 and a.short_account == 100_000
    assert a.long_account + a.short_account == a.total
    for k in ("L1", "L3", "L5"):
        assert account_of(k) == LONG_ACCOUNT
    for k in ("L2", "L4"):
        assert account_of(k) == SHORT_ACCOUNT
    assert max_lots(LONG_ACCOUNT) == 6 and max_lots(SHORT_ACCOUNT) == 4


def test_nominal_per_strategy_differs_from_account_split():
    """**名目分攤與帳戶配置刻意不一致。**

    帳戶 A 有 3 支但配 200,000（名目應為 180,000），
    帳戶 B 有 2 支卻只配 100,000（名目應為 120,000）。
    理由：多單出手機率高，所以多分配給多單帳戶。
    """
    from txfcore.instruments.capital import allocation
    a = allocation("TMF")
    assert a.per_strategy_nominal * 3 != a.long_account
    assert a.per_strategy_nominal * 2 != a.short_account
    assert a.per_strategy_nominal * 5 == a.total


def test_mc_capital_is_separate_from_our_allocation():
    """MC12 的 2,000,000 / 2 口大台是**它的設定**，只用於 anchor 對帳。

    我們的等比例配置是大台每支 1,200,000。**兩者不可混用。**
    """
    from txfcore.instruments.capital import MC_BACKTEST_CAPITAL, allocation
    assert MC_BACKTEST_CAPITAL == 2_000_000
    assert allocation("TXF").per_strategy_nominal == 1_200_000
    assert MC_BACKTEST_CAPITAL != allocation("TXF").per_strategy_nominal


def test_unknown_instrument_is_refused():
    from txfcore.instruments.capital import allocation
    with pytest.raises(ValueError, match="未知商品"):
        allocation("TXO")
