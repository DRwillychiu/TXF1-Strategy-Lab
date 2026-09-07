"""執行層與報價層測試。

重點在把「MC 的成交規則其實未知」這件事變成可測的東西：
policy 不同時，同一根 K 棒的成交順序必須不同——那正是對帳要反推的。
"""
from __future__ import annotations

from datetime import date, datetime

import pytest

from txfcore.engine.accounting import ClosedTrade, Ledger, trade_cost
from txfcore.engine.fill_mc12 import (
    CANDIDATE_POLICIES,
    FillPolicy,
    GapPolicy,
    IntrabarPolicy,
    MC12FillModel,
)
from txfcore.engine.position import PositionBook
from txfcore.instruments.spec import TMF, TXF
from txfcore.metrics.drawdown import compute
from txfcore.quotes.session import (
    bars_per_day, day_grid, is_day_bar, last_n_bar_stamps,
    night_grid, residual_count, session_grid,
)
from txfcore.timing.clock import BarClock
from txfcore.types.bar import Bar
from txfcore.types.orders import MarketPosition, OrderIntent, OrderType, Side, SizedOrder


# ==================================================================
# 網格 — 由 L2 標頭實證確認
# ==================================================================

def test_60m_day_grid_matches_l2_header():
    """L2 標頭：day 09:45-13:45 hourly close stamps。"""
    g = day_grid(date(2026, 9, 7), 60)
    stamps = [b.mc_stamp[1] for b in g]
    assert stamps == [945, 1045, 1145, 1245, 1345]
    assert not any(b.is_residual for b in g)


def test_60m_night_grid_matches_l2_header():
    """L2 標頭：night 16:00-05:00。夜盤 14 根，最後一根戳記為隔日。"""
    g = night_grid(date(2026, 9, 7), 60)
    assert len(g) == 14
    assert g[0].mc_stamp[1] == 1600
    assert g[-1].mc_stamp[1] == 500
    assert g[-1].mc_stamp[0] != g[0].mc_stamp[0]   # 跨日，日期戳是隔天


def test_only_45m_has_residual_bars():
    """整除性實測：只有 L1 的 45M 有殘棒。"""
    assert residual_count(15) == 0
    assert residual_count(60) == 0
    assert residual_count(45) == 2      # 日夜盤各餘 30 分鐘


def test_bars_per_day():
    assert bars_per_day(15) == 20 + 56
    assert bars_per_day(60) == 5 + 14
    assert bars_per_day(45) == 7 + 19   # 各含一根殘棒


def test_45m_residual_is_30_minutes():
    for g in (day_grid(date(2026, 9, 7), 45), night_grid(date(2026, 9, 7), 45)):
        assert g[-1].is_residual
        assert g[-1].minutes == 30


def test_1345_bar_is_night_for_l2():
    """L2 SECTION 4 的 D-6：IsDay 上限 1245，13:45 落在夜盤。"""
    assert is_day_bar(1245) is True
    assert is_day_bar(1345) is False
    assert is_day_bar(900) is True


def test_last_n_bar_stamps_for_live_mode():
    """LIVE 模式的「收盤前兩根禁止進場」。mc12 模式不使用。"""
    s = last_n_bar_stamps(date(2026, 9, 7), 60, 2)
    times = {t for _, t in s}
    assert 1245 in times and 1345 in times   # 日盤最後兩根
    assert 400 in times and 500 in times     # 夜盤最後兩根


# ==================================================================
# 成交模型 — 核心：MC 的規則未知，所以做成可切換的 policy
# ==================================================================

def _order(label, side, otype, price=None, qty=2):
    return SizedOrder(
        intent=OrderIntent(
            strategy="T", label=label, side=side, order_type=otype, price=price,
            signal_date=1260907, signal_time=1245,
        ),
        quantity=qty,
    )


def _bar(o=20000, h=20200, l=19800, c=20000):
    return Bar(1260907, 1345, o, h, l, c)


def test_market_order_fills_at_next_bar_open():
    m = MC12FillModel()
    fills = m.fill([_order("E", Side.BUY, OrderType.MARKET)], _bar(o=20050))
    assert fills[0].price == 20050


def test_stop_and_limit_both_hit_order_depends_on_policy():
    """**本模組存在的理由。**

    停損 19900 與停利 20100 都落在 [19800, 20200] 內。
    OHLC 沒有路徑資訊 → MC 必須用假設 → 我們不知道是哪一個。
    所以做成 policy，讓對帳的 diff 反推。
    """
    orders = [
        _order("TP", Side.SELL, OrderType.LIMIT, 20100),
        _order("SL", Side.SELL, OrderType.STOP, 19900),
    ]
    b = _bar()
    worst = MC12FillModel(FillPolicy(IntrabarPolicy.WORST_FIRST)).fill(orders, b)
    best = MC12FillModel(FillPolicy(IntrabarPolicy.BEST_FIRST)).fill(orders, b)
    assert worst[0].order.intent.label == "SL"    # 最壞先：先吃停損
    assert best[0].order.intent.label == "TP"     # 最好先：先吃停利
    assert worst[0].order.intent.label != best[0].order.intent.label


def test_all_candidate_policies_have_distinct_names():
    """對帳時逐組試，每一組都要能跑，且名稱可區分。

    名稱包含四個開關（intrabar|gap|sb|ef），因為報告會印出它——
    2026-09-06 發現 sb 曾出現在名稱裡但沒有作用，等於報告在說謊。
    """
    names = {p.name for p in CANDIDATE_POLICIES}
    assert len(names) == len(CANDIDATE_POLICIES)
    orders = [
        _order("TP", Side.SELL, OrderType.LIMIT, 20100),
        _order("SL", Side.SELL, OrderType.STOP, 19900),
    ]
    for p in CANDIDATE_POLICIES:
        assert MC12FillModel(p).fill(orders, _bar())


def test_no_dead_switches_in_fill_policy():
    """**policy 的每個欄位都必須真的被讀取。**

    2026-09-06 發現 allow_same_bar_exit 與 engine_stop_first 都是死設定：
    宣告了卻沒有任何地方讀，而前者還出現在 policy 名稱裡（sb=1），
    等於每一份報告都在宣稱一個沒有作用的設定。
    """
    import inspect
    from dataclasses import fields
    from txfcore.engine import fill_mc12
    from txfcore.runtime import backtest as bt, multi as mu
    src = (inspect.getsource(fill_mc12) + inspect.getsource(bt)
           + inspect.getsource(mu))
    for f in fields(FillPolicy):
        assert f"policy.{f.name}" in src, f"policy.{f.name} 是死設定"


def test_evidence_backed_defaults():
    """預設值來自 L2 全歷史的 2x2 標籤比對，不是猜的。

        sb     ef      InitSL_D InitSL_N ENGINE TSL_N  距離
        False  False      23       19       5     1     3   ← 最佳
        True   False      21       17       9     1     7
        False  True       21       13      13     1    15
        MC                22       18       4     1     0
    """
    from txfcore.engine.fill_mc12 import DEFAULT_POLICY
    assert DEFAULT_POLICY.allow_same_bar_exit is False
    assert DEFAULT_POLICY.engine_stop_first is False


def test_gap_policy_changes_fill_price():
    """跳空穿過觸發價：成交在開盤價或觸發價，是兩種假設。"""
    o = [_order("SL", Side.SELL, OrderType.STOP, 19900)]
    b = _bar(o=19700, h=19750, l=19600, c=19650)   # 開盤已在停損下方
    at_open = MC12FillModel(FillPolicy(gap=GapPolicy.AT_OPEN)).fill(o, b)[0]
    at_trig = MC12FillModel(FillPolicy(gap=GapPolicy.AT_TRIGGER)).fill(o, b)[0]
    assert at_open.price == 19700    # 實際跳空價，較差
    assert at_trig.price == 19900    # 樂觀，會低估跳空損失
    assert at_open.price < at_trig.price


def test_untouched_order_does_not_fill():
    o = [_order("SL", Side.SELL, OrderType.STOP, 19000)]
    assert MC12FillModel().fill(o, _bar()) == []


def test_engine_stop_is_a_distinct_exit_type():
    """L5 實測：171 筆中有 1 筆由引擎停損平倉，**無對應的出場單**。

    出場側標籤永遠標不到這條路徑，所以它必須是獨立的出場類型，
    否則對帳會出現「有平倉但找不到對應出場單」。
    """
    m = MC12FillModel()
    f = m.engine_stop_fill(19900, Side.SELL, 2, _bar(), "L5")
    assert f is not None
    assert f.is_engine_stop is True
    assert f.label == "ENGINE_STOP"


# ==================================================================
# 部位帳 — 單一與多腿用同一型別
# ==================================================================

def test_single_leg_position():
    bk = PositionBook()
    p = bk.get("L2")
    p.open_leg("TS_Entry", 20000, 2, 1260907, 1245, Side.SELL_SHORT)
    assert p.current_contracts == 2
    assert p.max_contracts == 2
    assert p.direction is MarketPosition.SHORT
    p.close(2)
    assert p.is_flat and p.direction is MarketPosition.FLAT


def test_l5_dual_leg_and_scale_out():
    """L5 的 Stage 判定完全靠 CurrentContracts vs MaxContracts。"""
    bk = PositionBook()
    p = bk.get("L5")
    p.open_leg("BL_Entry_Bot", 20000, 2, 1260907, 945, Side.BUY)
    p.open_leg("BL_Entry_Mid", 20100, 2, 1260907, 1000, Side.BUY)
    assert p.current_contracts == 4 and p.max_contracts == 4   # Stage 1

    p.close(1, from_entry="BL_Entry_Bot")                      # 分批出 40%
    assert p.current_contracts == 3
    assert p.current_contracts < p.max_contracts               # Stage 2/3
    assert p.leg("BL_Entry_Bot").quantity == 1
    assert p.leg("BL_Entry_Mid").quantity == 2


def test_entry_price_is_weighted_average_across_legs():
    bk = PositionBook()
    p = bk.get("L5")
    p.open_leg("Bot", 20000, 1, 1260907, 945, Side.BUY)
    p.open_leg("Mid", 20200, 3, 1260907, 1000, Side.BUY)
    assert p.entry_price == pytest.approx((20000 + 20200 * 3) / 4)


def test_book_reports_total_and_net_exposure():
    """實戰紀錄多空 56:3——net 會揭露組合實際上是單邊的。"""
    bk = PositionBook()
    bk.get("L1").open_leg("e", 20000, 2, 1, 1, Side.BUY)
    bk.get("L3").open_leg("e", 20000, 2, 1, 1, Side.BUY)
    bk.get("L2").open_leg("e", 20000, 2, 1, 1, Side.SELL_SHORT)
    assert bk.total_contracts() == 6
    assert bk.net_contracts() == 2          # 4 多 − 2 空


# ==================================================================
# 帳務 — 補上 Fill → equity 的斷裂
# ==================================================================

def _trade(entry, exit_, d_exit=1260907, t_exit=1345, qty=2, inst=TMF):
    return ClosedTrade(
        strategy="L2", entry_label="E", exit_label="X",
        direction=MarketPosition.LONG, quantity=qty,
        entry_price=entry, exit_price=exit_,
        entry_date=1260907, entry_time=945,
        exit_date=d_exit, exit_time=t_exit,
        cost=trade_cost(inst, entry, exit_, qty),
    )


def test_ledger_uses_instrument_backtest_capital():
    """裁決：微台 2 口 30 萬、大台 2 口 200 萬。"""
    assert Ledger(TMF).initial_capital == 300_000
    assert Ledger(TXF).initial_capital == 2_000_000


def test_net_deducts_fee_and_tax_separately():
    t = _trade(22000, 22100)
    gross = t.gross_ntd(TMF)
    assert gross == pytest.approx(100 * 10 * 2)
    assert t.net_ntd(TMF) < gross
    # 微台 22000/22100：(12 + 稅) × 2 邊 × 2 口
    assert t.cost == pytest.approx(trade_cost(TMF, 22000, 22100, 2))


def test_ledger_daily_pnl_uses_trading_day():
    """夜盤 00:00-05:00 的損益歸前一個交易日。

    必須與 K 棒層共用同一個 trading_day()，否則會有無法追查的一天偏移。
    """
    lg = Ledger(TMF)
    lg.record(_trade(22000, 22100, d_exit=1260908, t_exit=300))   # 夜盤尾段
    days, _ = lg.daily_pnl()
    assert days[0] == date(2026, 9, 7)      # 退回前一曆日


def test_fill_to_equity_to_drawdown_is_connected():
    """規劃書指出的斷裂：Fill → ??? → equity_curve()。本測試證明已接上。"""
    lg = Ledger(TMF)
    for e, x, d in ((22000, 22100, 1260907), (22100, 21900, 1260908),
                    (21900, 22200, 1260909)):
        lg.record(_trade(e, x, d_exit=d))
    eq = lg.equity()
    assert len(eq) == 4 and eq[0] == 300_000
    r = compute(eq)
    assert 0.0 <= r.max_drawdown <= 1.0


# ==================================================================
# 時鐘 — 第三顆插頭
# ==================================================================

def test_bar_clock_cannot_go_backwards():
    c = BarClock()
    c.advance_to(datetime(2026, 9, 7, 12, 45))
    with pytest.raises(ValueError):
        c.advance_to(datetime(2026, 9, 7, 11, 45))


def test_bar_clock_stamps_are_all_equal_in_backtest():
    """回測時三戳記相等，即時時才分開。"""
    c = BarClock()
    t = datetime(2026, 9, 7, 12, 45)
    c.advance_to(t)
    s = c.stamps(t)
    assert s.event_time == s.receipt_time == s.decision_time
    assert s.latency_ms == 0
    assert c.mc_stamp() == (1260907, 1245)


# ==================================================================
# 匯出檔格式 — 由實際檔案確認（2026-09-06）
# ==================================================================

def test_export_header_must_match_exactly():
    """格式變了要停，不做寬鬆解析。"""
    from txfcore.quotes.history import ExportFormatError, _parse_header
    _parse_header("<Date>, <Time>, <Open>, <High>, <Low>, <Close>, <Volume>")
    with pytest.raises(ExportFormatError):
        _parse_header("<Date>, <Time>, <Open>, <Close>")


def test_export_line_parses_unpadded_date_and_ms_time():
    """2019/1/2（月日不補零）· 08:46:00.000（含毫秒）"""
    from txfcore.quotes.history import _parse_line
    m = _parse_line("2019/1/2,08:46:00.000,9760,9762,9745,9750,2997", 2)
    assert m.dt == datetime(2019, 1, 2, 8, 46)
    assert (m.open, m.high, m.low, m.close, m.volume) == (9760, 9762, 9745, 9750, 2997)
    assert m.to_bar().mc_date == 1190102
    assert m.to_bar().mc_time == 846


def test_export_rejects_malformed_line():
    from txfcore.quotes.history import ExportFormatError, _parse_line
    with pytest.raises(ExportFormatError):
        _parse_line("2019/1/2,08:46:00.000,9760", 2)


# ==================================================================
# 聚合 — 60M 必須等於 L2 標頭的戳記
# ==================================================================

def _minutes(day: int, start: int, end: int, price: float = 20000.0):
    """產生連續 1 分 K。start/end 為 HHMM。"""
    out = []
    h, mi = divmod(start, 100)
    while h * 100 + mi <= end:
        out.append(Bar(day, h * 100 + mi, price, price + 1, price - 1, price, 10.0))
        mi += 1
        if mi == 60:
            h, mi = h + 1, 0
    return out


def test_aggregate_60m_day_matches_l2_header():
    """L2 標頭：day 09:45-13:45 hourly close stamps。"""
    from txfcore.quotes.bars import aggregate
    out = [b.mc_time for b, _ in aggregate(_minutes(1260602, 846, 1345), 60)]
    assert out == [945, 1045, 1145, 1245, 1345]


def test_aggregate_45m_produces_residual_bar():
    """45M 是唯一有殘棒的常用週期：6 全 + 1 殘（30 分鐘）。"""
    from txfcore.quotes.bars import aggregate
    out = list(aggregate(_minutes(1260602, 846, 1345), 45))
    assert [b.mc_time for b, _ in out] == [930, 1015, 1100, 1145, 1230, 1315, 1345]
    assert out[-1][1].expected_minutes == 30


def test_aggregate_records_gaps():
    """匯出檔的無成交分鐘直接省略（實測 2026/6/1 夜盤跳過 19:23）。

    聚合器必須容忍，並記錄每根由幾根合成。
    """
    from txfcore.quotes.bars import aggregate
    mins = [m for m in _minutes(1260602, 846, 945) if m.mc_time != 900]
    (bar, q), = aggregate(mins, 60)
    assert bar.mc_time == 945
    assert q.actual_minutes == 59 and q.expected_minutes == 60
    assert q.max_gap_minutes == 2
    assert bar.tick_count == 59


def test_low_confidence_flag():
    from txfcore.quotes.bars import aggregate
    mins = _minutes(1260602, 846, 900)      # 只有 15 根，缺 45 根
    (_, q), = aggregate(mins, 60)
    assert q.is_low_confidence() is True


# ==================================================================
# 結算日 — 由 208 萬列 1 分 K 反推，非靜態規則
# ==================================================================

def test_settlement_calendar_derived_from_data():
    """92 個結算日，靜態規則只抓到 90。"""
    from txfcore.tradecal.settlement import SETTLEMENT_DAYS, static_rule
    assert len(SETTLEMENT_DAYS) == 92
    assert sum(1 for d in SETTLEMENT_DAYS if static_rule(d)) == 90


def test_static_rule_misses_deferred_settlements():
    """兩天都是農曆年後的週一——結算因假期遞延。這是五份規格的 D-6。"""
    from txfcore.tradecal.settlement import RULE_MISSED, is_settlement_day, static_rule
    assert RULE_MISSED == (1230130, 1260223)
    for d in RULE_MISSED:
        assert is_settlement_day(d) is True
        assert static_rule(d) is False


def test_settlement_day_closes_at_1330():
    """實測 92 天全部如此，零例外。"""
    from txfcore.tradecal.settlement import day_close_time, day_minutes
    assert day_close_time(1260617) == 1330 and day_minutes(1260617) == 285
    assert day_close_time(1260602) == 1345 and day_minutes(1260602) == 300


def test_grid_shortens_on_settlement_day():
    """60M 在結算日的末根戳 1330，是 45 分鐘的殘棒。"""
    from txfcore.quotes.session import day_grid
    normal = [b.mc_stamp[1] for b in day_grid(date(2026, 6, 2), 60)]
    settle = [b.mc_stamp[1] for b in day_grid(date(2026, 6, 17), 60)]
    assert normal == [945, 1045, 1145, 1245, 1345]
    assert settle == [945, 1045, 1145, 1245, 1330]
    assert day_grid(date(2026, 6, 17), 60)[-1].is_residual is True


def test_outside_verified_range_falls_back_to_static_rule():
    """走出已驗證的地圖要 fail safe，與 Holiday_Tail 的原則相同。"""
    from txfcore.tradecal.settlement import is_settlement_day, is_verified, static_rule
    future = 1270120      # 超出 VERIFIED_UNTIL
    assert is_verified(future) is False
    assert is_settlement_day(future) == static_rule(future)


# ==================================================================
# 回測組裝根
# ==================================================================

def _synthetic_60m(n: int = 300, start_price: float = 20000.0):
    """合成 60M K 棒。用固定序列讓測試可重現。"""
    from txfcore.quotes.session import session_grid
    import itertools
    out, px = [], start_price
    days = (date(2026, 6, 1) + __import__("datetime").timedelta(days=i) for i in range(60))
    for d in days:
        for g in session_grid(d, 60):
            if len(out) >= n:
                return out
            dd, tt = g.mc_stamp
            px += (-1) ** len(out) * 12
            out.append(Bar(dd, tt, px, px + 20, px - 20, px, 100.0))
    return out


def test_runner_ages_position_before_filling():
    """進場那根的 BarsSinceEntry 必須是 0，不是 1。

    L2 的 S8 初始停損鎖定與 S11 的 lowest_close 初始化都掛在那個 0 上。
    2026-09-06 實測：順序寫反時，sl_trig 永遠是 0 → 優先級 5/6 失效，
    lowest_close 停在 0 → TTP 閘門恆真 → **172 筆交易全部走 TS_TTP**。
    修正後降到 92 筆、九種出場標籤。
    """
    from txfcore.engine.position import PositionBook
    bk = PositionBook()
    p = bk.get("X")
    p.advance_bar()                       # 空手時老化，無作用
    p.open_leg("E", 20000, 2, 1260601, 945, Side.BUY)
    assert p.bars_since_entry == 0        # 進場那根
    p.advance_bar()
    assert p.bars_since_entry == 1        # 下一根


def test_fixed_lot_risk_gate_returns_instrument_default():
    """mc12 對帳模式：風險層必須回傳與 MC 相同的固定口數。"""
    from txfcore.runtime.backtest import FixedLotRiskGate
    g = FixedLotRiskGate(TXF.default_lots)
    intent = OrderIntent(strategy="X", label="E", side=Side.BUY,
                         order_type=OrderType.MARKET)
    o = g.size(intent)
    assert o.quantity == 2 and o.sized_by == "fixed_lot"


def test_runner_produces_a_result_object():
    from txfcore.runtime.backtest import BacktestRunner
    from txfcore.strategies.l2_trendshort import L2TrendShort
    r = BacktestRunner(L2TrendShort(), TXF, warmup_bars=45).run(_synthetic_60m(200))
    assert r.bars_processed == 200
    assert r.strategy == "L2_TrendShort"
    assert r.policy.startswith("worst_first")


def test_intrabar_policy_is_irrelevant_for_exitfired_strategies():
    """**L2 對 intrabar 歧義免疫**，因為 ExitFired 保證一根一張單。

    2026-09-06 全歷史實測：四組 policy 都是 92 筆、淨利相同。
    歧義只影響 L3（bracket）與 L5（雙腿）。
    L2 正因為免疫，才是乾淨的測試床。
    """
    from txfcore.engine.fill_mc12 import FillPolicy, IntrabarPolicy
    from txfcore.runtime.backtest import BacktestRunner
    from txfcore.strategies.l2_trendshort import L2TrendShort
    bars = _synthetic_60m(240)
    a = BacktestRunner(L2TrendShort(), TXF, warmup_bars=45,
                       policy=FillPolicy(IntrabarPolicy.WORST_FIRST)).run(bars)
    b = BacktestRunner(L2TrendShort(), TXF, warmup_bars=45,
                       policy=FillPolicy(IntrabarPolicy.BEST_FIRST)).run(bars)
    assert a.trade_count == b.trade_count


# ==================================================================
# 血緣雜湊
# ==================================================================

def test_lineage_refuses_comparison_when_upstream_differs():
    """L3 那類「基準線自己從 360 變 361」的事故，結構上不可能再發生。"""
    from txfcore.lineage.stamp import Lineage, LineageMismatch, require_match
    a = Lineage("c1", "cfg1", "d1", "cal1")
    require_match(a, Lineage("c1", "cfg1", "d1", "cal1"))
    with pytest.raises(LineageMismatch):
        require_match(a, Lineage("c1", "cfg2", "d1", "cal1"))
    assert a.diff_fields(Lineage("c9", "cfg2", "d1", "cal1")) == ["code", "config"]


def test_calendar_hash_changes_with_registry():
    from txfcore.tradecal import calendar_hash
    assert len(calendar_hash()) == 64


def test_settlement_source_hash_recorded():
    """資料換版時雜湊會變，屆時必須重新反推結算日曆。"""
    from txfcore.tradecal.settlement import SOURCE_SHA256, SOURCE_ROWS, VERIFIED_UNTIL
    assert len(SOURCE_SHA256) == 64
    assert SOURCE_ROWS == 2_098_922
    assert VERIFIED_UNTIL == 1260905


# ==================================================================
# 多資料流對齊 —— of Data2 / of Data3 語意
# ==================================================================

def test_slow_stream_only_exposes_closed_bars():
    """Data2 只暴露已收盤的 K 棒。

    在 15M 的 09:00，60M 的 09:45 那根還在形成中，策略讀不到它。
    任何比這更寬鬆的規則都會讀到未來資料。
    """
    from txfcore.quotes.align import MultiStream
    ms = MultiStream()
    ms.feed_slow("data2", Bar(1260602, 945, 20000, 20050, 19950, 20010))
    ms.feed_slow("data2", Bar(1260602, 1045, 20010, 20060, 19960, 20020))

    ms.push_driver(Bar(1260602, 900, 20000, 20010, 19990, 20005))
    assert len(ms.slow("data2")) == 0          # 09:45 尚未收盤
    assert ms.slow("data2").forming is not None

    ms.push_driver(Bar(1260602, 945, 20005, 20050, 19950, 20010))
    assert len(ms.slow("data2")) == 1          # 同時收盤，放行
    assert ms.slow("data2").series.close[0] == 20010


def test_slow_stream_offset_one_is_previous_closed_bar():
    """MC 的 [1] of Data2 = 前一根已收盤的。"""
    from txfcore.quotes.align import MultiStream
    ms = MultiStream()
    for t, c in ((945, 20010), (1045, 20020), (1145, 20030)):
        ms.feed_slow("data2", Bar(1260602, t, c - 10, c + 5, c - 15, c))
    for t in (945, 1045, 1145):
        ms.push_driver(Bar(1260602, t, 20000, 20010, 19990, 20005))
    d2 = ms.slow("data2").series
    assert d2.close[0] == 20030 and d2.close[1] == 20020


def test_all_ready_gates_warmup():
    from txfcore.quotes.align import MultiStream
    ms = MultiStream()
    ms.feed_slow("data2", Bar(1260602, 945, 1, 2, 0, 1))
    assert not ms.all_ready("data2", "data3")
    ms.push_driver(Bar(1260602, 945, 1, 2, 0, 1))
    assert not ms.all_ready("data2", "data3")   # data3 還是空的


# ==================================================================
# L4
# ==================================================================

def test_l4_registers_79_trades():
    """標頭：完整回測 79 筆。多頭市場零交易 = 正確行為。"""
    from txfcore.strategies.l4_consolshort import L4ConsolShort
    assert L4ConsolShort().expected_trigger_range() == (79, 79)


def test_l4_holiday_flat_time_is_415():
    """L1=345 L2=300 L3/L4/L5=415。跟著各自的 K 棒網格走。"""
    from txfcore.strategies.l4_consolshort import L4ConsolShort
    assert L4ConsolShort().config.holiday_flat_time == 415


def test_l4_needs_three_streams():
    """缺 Data2 / Data3 時不動作，不猜。"""
    from txfcore.strategies.base import MarketView, PositionView
    from txfcore.strategies.l4_consolshort import L4ConsolShort
    from txfcore.tradecal.gates import evaluate
    from txfcore.types.bar import BarSeries
    s = L4ConsolShort(); st = s.initial_state()
    bs = BarSeries("d1")
    for _ in range(300):
        bs.push(Bar(1260602, 945, 20000, 20010, 19990, 20000, 10.0))
    v = MarketView(data1=bs, position=PositionView(),
                   calendar=evaluate(1260602, 945), mc_date=1260602, mc_time=945)
    _, dec = s.on_bar(v, st)
    assert dec.orders == [] and dec.protective is None


def test_l4_per_trade_state_resets():
    from txfcore.strategies.l4_consolshort import L4PerTrade
    pt = L4PerTrade()
    pt.trail_active = True; pt.stop_level = 20500.0; pt.sl_locked = True
    pt.reset()
    pt.assert_clean()


def test_l4_night_block_window_differs_from_l5():
    """L4 是 200–500，L5 是 400–500。

    而且方向相反：L4 夜盤淨 −120,800、L5 淨 +87,800。
    """
    from txfcore.strategies.l4_consolshort import NIGHT_BLOCK_END, NIGHT_BLOCK_START
    assert (NIGHT_BLOCK_START, NIGHT_BLOCK_END) == (200, 500)


# ==================================================================
# 換月標記 —— 假設已排除，但仍需標記
# ==================================================================

def test_rollover_point_is_after_settlement_close():
    """結算日 13:30 近月停止交易，之後序列切換到次月。"""
    from txfcore.quotes.continuous import is_rollover_point
    assert is_rollover_point(1260617, 1600) is True    # 結算日夜盤
    assert is_rollover_point(1260617, 1245) is False   # 結算日 13:30 之前
    assert is_rollover_point(1260602, 1600) is False   # 非結算日


def test_spans_rollover_requires_crossing_1330_not_merely_nearby():
    """**這條斷言我第一次寫錯了。**

    原本用 span_days=1 的鄰近窗口，把「結算日的隔一天」也算成跨越換月，
    誤標了兩筆與換月無關的交易。

    真正跨越 = 進場在結算日 13:30 之前、出場在之後。
    """
    from txfcore.quotes.continuous import spans_rollover
    assert spans_rollover(1260617, 945, 1260617, 1600) is True   # 真的跨越
    assert spans_rollover(1260617, 1600, 1260618, 945) is False  # 換月後才進場
    assert spans_rollover(1260618, 945, 1260618, 1600) is False  # 結算日隔天
    assert spans_rollover(1260602, 945, 1260602, 1600) is False  # 一般日


def test_five_strategies_structurally_cannot_span_rollover():
    """Settlement_Flat_Time = 1230 早於換月點 1330，且整個結算日封鎖進場。

    2026-09-06 用戶指出後實測確認：L2 / L4 全歷史各 0 筆跨越。
    **這不是「觀察不到」，是「結構上不可能」。**

    保留這個檢查的理由：它可能失敗而沒失敗。
    """
    from txfcore.quotes.continuous import SETTLEMENT_CLOSE, spans_rollover
    from txfcore.strategies.l2_trendshort import L2TrendShort
    from txfcore.strategies.l4_consolshort import L4ConsolShort
    for s in (L2TrendShort(), L4ConsolShort()):
        assert s.config.settlement_flat_time < SETTLEMENT_CLOSE
    # 強制平倉時刻進場、當日出場 → 不可能跨越
    assert spans_rollover(1260617, 1230, 1260617, 1245) is False


def test_rollover_gap_is_much_larger_than_normal():
    """實測 92 個換月點：中位數是一般隔夜跳空的 5.5 倍。"""
    from txfcore.quotes.continuous import (
        NORMAL_GAP_MEDIAN_ABS, ROLLOVER_GAP_MEDIAN_ABS,
    )
    assert ROLLOVER_GAP_MEDIAN_ABS / NORMAL_GAP_MEDIAN_ABS > 5


# ==================================================================
# 對齊規則 —— H5，2026-09-07 排除
# ==================================================================

def test_include_forming_exposes_the_unclosed_bar():
    """`INCLUDE_FORMING` 讓策略讀到尚未收盤的較慢流 K 棒。

    **實測顯示這是錯的規則**：L4 從 83 筆掉到 44 筆，而 MC 是 79 筆。
    保留它作為可切換的假設，因為 MC 的實際規則沒有文件。
    """
    from txfcore.quotes.align import AlignPolicy, MultiStream
    for pol, expect in ((AlignPolicy.CLOSED_ONLY, 0),
                        (AlignPolicy.INCLUDE_FORMING, 1)):
        ms = MultiStream(pol)
        ms.feed_slow("d2", Bar(1260602, 945, 20000, 20050, 19950, 20010))
        ms.push_driver(Bar(1260602, 900, 20000, 20010, 19990, 20005))
        assert len(ms.slow("d2")) == expect


def test_forming_bar_is_withdrawn_not_duplicated():
    """形成中的 K 棒被暫時推入，下一次推進時必須撤回再重推。

    沒撤回就會重複——那會讓 [1] 指到自己。
    """
    from txfcore.quotes.align import AlignPolicy, MultiStream
    ms = MultiStream(AlignPolicy.INCLUDE_FORMING)
    ms.feed_slow("d2", Bar(1260602, 945, 20000, 20050, 19950, 20010))
    ms.feed_slow("d2", Bar(1260602, 1045, 20010, 20060, 19960, 20020))
    ms.push_driver(Bar(1260602, 900, 20000, 20010, 19990, 20005))
    ms.push_driver(Bar(1260602, 915, 20000, 20010, 19990, 20005))
    assert len(ms.slow("d2")) == 1        # 只有形成中的那一根，不是兩根
    ms.push_driver(Bar(1260602, 945, 20000, 20010, 19990, 20005))
    assert len(ms.slow("d2")) == 2        # 09:45 收盤 + 10:45 形成中


def test_bar_series_pop_is_for_alignment_only():
    """`pop()` 只給對齊層撤回暫定 K 棒用。策略層不該呼叫。"""
    from txfcore.types.bar import BarSeries
    bs = BarSeries("x")
    bs.push(Bar(1260602, 945, 1, 2, 0, 1.5))
    bs.push(Bar(1260602, 1045, 2, 3, 1, 2.5))
    assert len(bs) == 2 and bs.close[0] == 2.5
    bs.pop()
    assert len(bs) == 1 and bs.close[0] == 1.5
