"""風險度量與組合層保護器。

外部借鑑：
  metrics/risk       skfolio —— CDaR · Ulcer Index · CVaR · 平均回撤
  risk/protections   freqtrade —— MaxDrawdown · StoplossGuard · Cooldown
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from txfcore.metrics.drawdown import compute, equity_curve
from txfcore.metrics.risk import (
    average_drawdown, cdar, cvar, profile, ulcer_index, worst_realization,
)
from txfcore.risk.protections import (
    CooldownPeriod, ExposureLimit, MaxDrawdownGuard, ProtectionStack,
    StoplossGuard, TradeOutcome, Verdict,
)

D = date(2026, 9, 7)


# ==================================================================
# 風險度量 —— 單一數字會騙人，一組不會
# ==================================================================

def test_ulcer_distinguishes_curves_with_same_max_drawdown():
    """**這是 Ulcer Index 存在的理由。**

    兩條曲線 max_drawdown 相同，但一條很快回復、一條拖很久。
    MDD 分不出來，Ulcer Index 分得出來。
    """
    quick = compute([100, 50, 100, 100, 100, 100])       # 掉一半後立刻回復
    slow = compute([100, 50, 55, 60, 65, 100])           # 掉一半後拖很久
    assert quick.max_drawdown == pytest.approx(slow.max_drawdown)
    assert ulcer_index(slow.drawdown) > ulcer_index(quick.drawdown)


def test_cdar_is_more_stable_than_max_drawdown():
    """CDaR 取最壞 5% 的平均，單一極端值不會主導它。"""
    dd = [0.01] * 95 + [0.50] * 5
    assert cdar(dd, 0.95) == pytest.approx(0.50)
    assert average_drawdown(dd) < cdar(dd, 0.95)
    assert average_drawdown(dd) == pytest.approx(0.0345)


def test_cvar_and_worst_realization_are_positive_losses():
    rets = [0.02, -0.01, 0.03, -0.08, 0.01]
    assert worst_realization(rets) == pytest.approx(0.08)
    assert cvar(rets, 0.8) > 0


def test_profile_exposes_the_whole_family():
    """76 天實戰紀錄：max_dd 31.53% 完全看不出 underwater 96.7%。"""
    eq = equity_curve(300_000, [-10_000, 5_000, -40_000, -5_000, 20_000])
    p = profile(compute(eq))
    assert 0 <= p.max_drawdown <= 1
    assert p.average_drawdown <= p.max_drawdown
    assert p.ulcer_index <= p.max_drawdown
    assert 0 <= p.underwater_ratio <= 1
    assert "水下比例" in p.summary()


def test_average_drawdown_never_exceeds_max():
    eq = equity_curve(1000, [-100, 50, -200, 300, -50])
    r = compute(eq)
    assert average_drawdown(r.drawdown) <= r.max_drawdown


# ==================================================================
# 組合層保護器 —— MC 從來沒有這一層
# ==================================================================

def _stop(day_offset: int, strategy="L2") -> TradeOutcome:
    return TradeOutcome(strategy, D - timedelta(days=day_offset), -50_000, True)


def test_stoploss_guard_catches_what_single_trade_stops_cannot():
    """L2 標頭與實戰紀錄都是最大連續虧損 9 次。

    **單筆停損管不到「連續九次」——那需要這一層。**
    """
    g = StoplossGuard(lookback_days=7, max_stops=4)
    assert g.check(D, [_stop(i) for i in range(3)], []).allowed
    d = g.check(D, [_stop(i) for i in range(5)], [])
    assert d.verdict is Verdict.BLOCK_ENTRY and "停損 5 次" in d.reason


def test_stoploss_guard_respects_lookback_window():
    g = StoplossGuard(lookback_days=7, max_stops=2)
    old = [_stop(30), _stop(40), _stop(50)]
    assert g.check(D, old, []).allowed          # 全在窗口外


def test_max_drawdown_guard_halts_not_just_blocks():
    """回撤超過門檻是**停止全部**，不只擋新進場。

    這是唯一能防止災難性虧損的機制——策略層的停損只管單筆。
    """
    eq = [300_000, 320_000, 200_000]            # 從 320K 掉到 200K = 37.5%
    d = MaxDrawdownGuard(threshold=0.25).check(D, [], eq)
    assert d.verdict is Verdict.HALT_ALL
    assert "37.50%" in d.reason


def test_max_drawdown_guard_would_have_fired_on_live_record():
    """76 天實戰：max_drawdown 31.53%。門檻 25% 時中途就會觸發。"""
    eq = [300_000, 310_000, 212_000]            # 約 31.6%
    assert not MaxDrawdownGuard(threshold=0.25).check(D, [], eq).allowed
    assert MaxDrawdownGuard(threshold=0.40).check(D, [], eq).allowed


def test_cooldown_defaults_to_per_strategy_matching_mc():
    """L4 的 Cooldown_Bars = 8 是策略層內建的。

    本保護器是組合層的。預設只擋該支，與 MC 行為一致；
    改成擋全部才是新行為，屬 v2 模式。
    """
    c = CooldownPeriod(days=1)
    assert c.per_strategy is True
    assert not c.check(D, [_stop(0)], []).allowed
    assert c.check(D, [_stop(5)], []).allowed


def test_exposure_limit_is_layer3_invariant_one():
    e = ExposureLimit(max_total_contracts=10)
    e.observe(8)
    assert e.check(D, [], []).allowed
    e.observe(10)
    assert not e.check(D, [], []).allowed


def test_stack_returns_the_most_severe_verdict():
    """HALT_ALL 優先於 BLOCK_ENTRY —— 與策略層的優先級鏈同一原則。"""
    s = ProtectionStack([
        StoplossGuard(max_stops=1),                       # 會 BLOCK
        MaxDrawdownGuard(threshold=0.10),                 # 會 HALT
    ])
    d = s.check(D, [_stop(0)], [300_000, 200_000])
    assert d.verdict is Verdict.HALT_ALL


def test_default_stack_thresholds_are_guesses_not_measurements():
    """**預設門檻是猜的。** 事前登記才算數。"""
    s = ProtectionStack.default()
    assert len(s.protections) == 3
    assert isinstance(s.protections[0], MaxDrawdownGuard)
