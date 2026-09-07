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
