"""對帳層測試。

黃金測試集是 **G2 kill gate**：判官必須先抓得到每一個已知歷史事故，
才准去驗證新東西。這一條 fail 就代表不准往下做。
"""
from __future__ import annotations

import pytest

from txfcore.lineage.stamp import Lineage, LineageMismatch
from txfcore.parity.diff import (
    Tier, Tolerance, TradeRecord, compare, merge_split_exits,
)
from txfcore.parity.golden import CASES, run_golden

ZERO = Tolerance(Tier.DECISION, max_diff_trades=0, commit="test")


def _t(ed, et, xd, xt, d=-1, q=2, ep=20000.0, xp=19900.0):
    return TradeRecord(ed, et, xd, xt, d, q, ep, xp)


# ==================================================================
# G2 kill gate
# ==================================================================

def test_golden_set_must_pass_before_any_parity_work():
    """★ 判官的判官。全過才准進入對帳。"""
    ok, report = run_golden()
    assert ok, f"判官不合格，不得用於驗證任何新東西：\n{report}"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.code)
def test_each_golden_case(case):
    passed, err = case.run()
    assert passed, f"{case.code} {case.title} 未抓到：{err}　·　{case.why}"


def test_golden_covers_every_known_incident():
    """新事故出現時必須加進來，否則判官會逐漸落後於現實。"""
    assert len(CASES) >= 12
    codes = {c.code for c in CASES}
    assert len(codes) == len(CASES)      # 編號不得重複


# ==================================================================
# 三層完成定義
# ==================================================================

def test_decision_tier_ignores_price():
    """決策層比時間 / 方向 / 單型 / 口數，**不比價格**。"""
    a = [_t(1260601, 945, 1260601, 1145, ep=20000, xp=19900)]
    b = [_t(1260601, 945, 1260601, 1145, ep=20005, xp=19895)]
    assert compare(a, b, Tier.DECISION, ZERO).passed


def test_fill_tier_compares_price_within_tolerance():
    a = [_t(1260601, 945, 1260601, 1145, ep=20000, xp=19900)]
    b = [_t(1260601, 945, 1260601, 1145, ep=20005, xp=19895)]
    tol5 = Tolerance(Tier.FILL, max_diff_trades=0, max_price_diff_pts=5, commit="t")
    tol1 = Tolerance(Tier.FILL, max_diff_trades=0, max_price_diff_pts=1, commit="t")
    assert compare(a, b, Tier.FILL, tol5).passed
    assert not compare(a, b, Tier.FILL, tol1).passed


def test_performance_tier_sets_no_standard():
    """績效層不設標準——MC 不是判官，它的成交假設從未被檢驗。"""
    a = [_t(1260601, 945, 1260601, 1145)]
    b = []
    r = compare(a, b, Tier.PERFORMANCE, ZERO)
    assert r.passed
    assert any("不是判官" in n for n in r.notes)


# ==================================================================
# 分批合併 —— 已發生過的事故
# ==================================================================

def test_merge_split_exits_weights_by_quantity():
    parts = [
        _t(1260601, 945, 1260601, 1045, q=1, xp=19950),
        _t(1260601, 945, 1260601, 1145, q=3, xp=19850),
    ]
    (m,) = merge_split_exits(parts)
    assert m.quantity == 4
    assert m.exit_price == pytest.approx((19950 * 1 + 19850 * 3) / 4)
    assert (m.exit_date, m.exit_time) == (1260601, 1145)   # 取最後一次出場


def test_compare_merges_splits_by_default_and_records_it():
    ours = [_t(1260601, 945, 1260601, 1145, q=2)]
    theirs = [
        _t(1260601, 945, 1260601, 1045, q=1),
        _t(1260601, 945, 1260601, 1145, q=1),
    ]
    naive = compare(ours, theirs, Tier.DECISION, ZERO, merge_splits=False)
    merged = compare(ours, theirs, Tier.DECISION, ZERO)
    assert not naive.passed          # 不合併 → 誤判為兩邊筆數不同
    assert merged.passed
    assert any("合併分批" in n for n in merged.notes)


# ==================================================================
# 血緣守門
# ==================================================================

def test_diff_refuses_when_lineage_differs():
    t = [_t(1260601, 945, 1260601, 1145)]
    a = Lineage("c", "cfg", "d1", "cal")
    b = Lineage("c", "cfg", "d2", "cal")
    with pytest.raises(LineageMismatch):
        compare(t, t, Tier.DECISION, ZERO, ours_lineage=a, theirs_lineage=b)


def test_report_prints_tolerance_commit():
    """事後放寬容差是最常見的自欺。報告開頭印出來讓它無所遁形。"""
    r = compare([], [], Tier.DECISION,
                Tolerance(Tier.DECISION, 0, commit="abc1234"))
    assert "abc1234" in r.report()


def test_report_flags_unregistered_tolerance():
    r = compare([], [], Tier.DECISION, Tolerance(Tier.DECISION, 0))
    assert "未登記" in r.report()


# ==================================================================
# 差異分類
# ==================================================================

def test_only_ours_and_only_theirs_are_separated():
    ours = [_t(1260601, 945, 1260601, 1145), _t(1260602, 945, 1260602, 1145)]
    theirs = [_t(1260601, 945, 1260601, 1145), _t(1260603, 945, 1260603, 1145)]
    r = compare(ours, theirs, Tier.DECISION, ZERO)
    assert r.matched == 1
    assert len(r.only_ours) == 1 and len(r.only_theirs) == 1
    assert r.diff_count == 2 and not r.passed


def test_field_diff_names_the_offending_fields():
    ours = [_t(1260601, 945, 1260601, 1145, q=2)]
    theirs = [_t(1260601, 945, 1260601, 1345, q=4)]
    r = compare(ours, theirs, Tier.DECISION, ZERO)
    _, _, bad = r.field_diffs[0]
    assert set(bad) == {"exit_time", "quantity"}


# ==================================================================
# 不變量 —— 判官 (2)。唯一不需要對照組就能抓錯的判官
# ==================================================================

def test_iron_rule_assertion_checks_close_not_trigger():
    """**這條斷言我第一次寫錯了。**

    .pla：「03:00 觸發，03:00 成交，04:00 重試，always flat before the
    05:00 close」——訂單在 03:00 掛出，**下一根才成交**。

    斷言若寫成 `Time >= 300 不得持倉`，會誤報（2026-09-06 實測誤報 2 次）。
    正確的是檢查 05:00 收盤。
    """
    import inspect
    from txfcore.parity import invariants
    src = inspect.getsource(invariants.L2Invariants.check)
    assert "t >= 500" in src, "Iron Rule 必須檢查 05:00 收盤，不是觸發時刻"
    assert "t >= 300" not in src


def test_known_defects_are_not_counted_as_failures():
    """規格表已記錄的落差（照抄的）標為 KNOWN，不混進 FAIL。

    否則每次跑都有一堆紅字，真正的新問題會被淹沒。
    """
    from txfcore.parity.invariants import InvariantLog, Severity
    log = InvariantLog()
    log.record("L2-3 追蹤停損放鬆", 1190806, 100, "known", Severity.KNOWN)
    log.record("新問題", 1190806, 100, "unexpected", Severity.FAIL)
    assert len(log.violations) == 2
    assert len(log.failures()) == 1


def test_invariant_log_reports_first_occurrence():
    """報告要指出首例的日期時間，才查得下去。"""
    from txfcore.parity.invariants import InvariantLog
    log = InvariantLog()
    log.checks_run = 100
    log.record("X", 1190806, 100, "detail-a")
    log.record("X", 1190807, 200, "detail-b")
    r = log.report()
    assert "1190806" in r and "detail-a" in r
    assert "2 次" in r or "    2" in r


# ==================================================================
# MC12 對帳基準 —— 2026-09-07 從 repo 的 anchor 文件挖出
# ==================================================================

def test_anchors_all_carry_an_export_date():
    """每個 anchor 都必須註明它是哪一次執行的產物。

    L2 / L4 來自 `docs/research/` 的 anchor 文件（最可信）。
    L3 目前只有標頭的 PERFORMANCE 區塊，且該檔內部矛盾
    （376/2,446,000 vs v15.1 CHANGELOG 的 360/1,389,600）。
    """
    from txfcore.parity.anchors import ANCHORS
    for a in ANCHORS.values():
        assert a.export_date > 1260000
        assert a.source_doc


def test_backtest_window_is_per_strategy():
    """**視窗的影響比成交假設、對齊規則、換月假象加起來都大。**

    L3 實測：同程式碼同資料，視窗 2019-12-16 -> 2020-05-12
    使筆數差距從 +23 掉到 +3。
    """
    from txfcore.parity.anchors import ANCHORS
    assert ANCHORS["L3"].backtest_start == 1200512     # v14.1 標頭明載
    assert ANCHORS["L2"].backtest_start == 1191216     # 未載明，沿用 L1
    assert ANCHORS["L3"].backtest_start != ANCHORS["L2"].backtest_start


def test_l4_anchor_is_82_not_79():
    """**79 是 CS_Entry 的數量，不是總筆數。**

    我先前拿 79 當總數比，於是「多 4 筆」——實際只多 1 筆。
    """
    from txfcore.parity.anchors import L4_V147
    from txfcore.strategies.l4_consolshort import L4ConsolShort
    assert L4_V147.total_trades == 82
    assert L4_V147.entry_labels == {"CS_Entry": 79, "CS_ReEntry": 3}
    assert sum(L4_V147.entry_labels.values()) == 82
    assert L4ConsolShort().expected_trigger_range() == (82, 82)


def test_l2_entry_split_is_57_20_not_55_22():
    """標頭那組 55/22 是事前登記，anchor 文件的 R-2 已推翻。"""
    from txfcore.parity.anchors import L2_V54
    from txfcore.strategies.l2_trendshort import L2TrendShort
    assert L2_V54.entry_labels == {"TS_Entry": 57, "TS_ReEntry": 20}
    assert sum(L2_V54.entry_labels.values()) == 77
    assert L2TrendShort().expected_trigger_range() == (77, 77)


def test_l4_exit_labels_are_recorded():
    """v14.7 文件給了完整的出場標籤分布，那是最強的對帳訊號。"""
    from txfcore.parity.anchors import L4_V147
    assert L4_V147.exit_labels == {"CS_SL": 38, "CS_BreakExit": 30, "CS_TimeExit": 14}
    assert sum(L4_V147.exit_labels.values()) == 82


def test_two_l4_anchors_have_different_data_windows():
    """v14.7（82 筆 / 800,000）與 v18.0（79 筆 / 877,200）資料區間不同。

    v14.7 的文件明載「舊量測時 live 淨利是 877,200，本次是 800,000」。
    **兩者的筆數與淨利不可直接比較。**
    """
    from txfcore.parity.anchors import L4_V147, L4_V180
    assert L4_V147.total_trades != L4_V180.total_trades
    assert L4_V147.net_profit != L4_V180.net_profit
    assert L4_V147.export_date != L4_V180.export_date


def test_label_distance():
    from txfcore.parity.anchors import label_distance
    assert label_distance({"a": 3}, {"a": 3}) == 0
    assert label_distance({"a": 3, "b": 1}, {"a": 2}) == 2


def test_l3_anchor_and_reentry_range():
    """re-entry 無法事前登記精確值——「同一 episode」需要 K 棒資料。

    登記為區間 20 <= CL_ReEntry <= 115。**超過 115 代表 episode 閘門沒作用。**
    """
    from txfcore.parity.anchors import L3_V150
    from txfcore.strategies.l3_consollong import L3ConsolLong
    assert L3_V150.total_trades == 376
    assert L3ConsolLong().expected_reentry_range() == (20, 115)
    assert L3ConsolLong().expected_trigger_range() == (360, 376)


def test_l3_disarm_is_structural_not_price_based():
    """**L4 v18 零觸發是因為價格解除被自己的停損蘊含。**

    L3 完全不測價格——episode 變了就解除，所以避開了那個陷阱。
    原始碼註解明載這一點。
    """
    import inspect
    from txfcore.strategies import l3_consollong
    src = inspect.getsource(l3_consollong.L3ConsolLong.on_bar)
    assert "ps.episode_id != ps.reentry_episode" in src
    assert "reentry_armed = False" in src


# ==================================================================
# 樣本內外切分 —— 2026-09-07 發現先前全部跑錯窗口
# ==================================================================

def test_live_start_is_the_real_trading_start():
    """**2026-06-17 是真實下單開始的日子**（實戰紀錄檔名 `260617開始`）。

    先前所有回測都跑到 2026-09-05，把樣本內外混在一起——
    **樣本外的衰退完全看不出來**。
    """
    from txfcore.parity.windows import BACKTEST_END, LIVE_START
    assert LIVE_START == 1260617
    # 2026-09-07 會議裁決：回測至 06/17 為止，之後是實戰。**不留空窗。**
    assert BACKTEST_END == 1260616
    assert BACKTEST_END + 1 == LIVE_START


def test_split_puts_every_trade_in_exactly_one_bucket():
    from txfcore.parity.windows import split
    from txfcore.engine.accounting import ClosedTrade
    from txfcore.types.orders import MarketPosition

    def t(d):
        return ClosedTrade("X", "E", "X", MarketPosition.LONG, 2,
                           20000, 20100, d, 945, d, 1145, 0.0)
    ins, out, gap = split([t(1250101), t(1260616), t(1260701)])
    assert len(ins) == 2 and len(out) == 1
    assert not gap                       # 不留空窗，每筆都歸在其中一邊


def test_completeness_names_the_consequence_of_each_gap():
    """**只列「缺什麼」沒有用，要說「缺了會怎樣」。**"""
    from txfcore.parity.completeness import CAPABILITIES, summary
    done, total = summary()
    assert total == 12 and done == 5
    for c in CAPABILITIES:
        assert c.why, c.protocol


def test_orphan_modules_are_registered():
    """**寫好但沒有呼叫者的模組，比沒寫更危險**——它看起來像有。"""
    from txfcore.parity.completeness import ORPHANS
    names = {f for f, _ in ORPHANS}
    assert "risk/protections.py" in names
    assert "timing/latency.py" in names
