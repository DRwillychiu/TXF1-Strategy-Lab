# S16_S v0.5 — W5 Five-Pack Validation Report

**Date**: 2026-07-09
**Config**: F25/S70/Slope28 + QS(4,60) MH24 ATR4.0
**Source**: MC12 backtest, 102 trades (2020-03-23 ~ 2026-07-06)
**Backtest evidence**: `TXF1 S16_S_MACrossShort 策略回測績效報告.xls`

---

## Performance Summary

| Metric | Value |
|--------|-------|
| Net Profit | +1,075,800 |
| Profit Factor | 1.982 |
| Max Drawdown | -271,600 (27.2% of 1M) |
| Calmar Ratio | 3.961 |
| Trades | 102 (23W / 79L) |
| Win Rate | 22.5% |
| Avg Win / Avg Loss | 94,391 / -13,863 = 6.81:1 |
| Median Loss | -13,600 |
| Max Single Loss | -42,600 (4.26%) |

## Exit Signal Distribution

| Exit | Trades | % | Net | WR |
|------|--------|---|-----|-----|
| TimeStop | 20 | 19.6% | +2,103,000 | 100% |
| GoldenCross | 2 | 2.0% | +67,600 | 100% |
| BE_Trail2 | 6 | 5.9% | -20,400 | 17% |
| BE_Trail1 | 5 | 4.9% | -33,600 | 0% |
| QuickStop_Tim | 29 | 28.4% | -195,000 | 0% |
| QuickStop_Los | 40 | 39.2% | -845,800 | 0% |

**Structure**: 20 TimeStop trades = 100% of alpha (+2,103K). Other 82 trades = -1,027K.

---

## Five-Pack Results

### Original SOP Thresholds (Claude-designed, not user-approved)

| Test | Verdict | Key Metric | Threshold |
|------|---------|------------|-----------|
| Monte Carlo | FAIL | 95% MDD = -392,800 (-39.3%) | < 30% |
| Bootstrap | FAIL | PF CI = [0.924, 3.534] | lower > 1.0 |
| Stress Test | FAIL | Jun26 cluster loss = -323,200 | < 15% capital |
| Regime | FAIL | Bull Net = -106,400 (PF 0.70) | no regime > 10% loss |
| Robustness | PASS | 5/7 checks within tolerance | >= 70% |

**Original verdict: 1/5 PASS = ARCHIVE**

### Root Cause of 4 FAIL

The original SOP thresholds implicitly assume WR >= 30-40% (wave/trend strategies).
S16_S is a **low-WR sniper** (22.5% WR, 6.81:1 reward/risk) — structurally incompatible
with standard statistical thresholds. Even with genuine alpha, Monte Carlo and Bootstrap
will always fail because the heavy-tail distribution (20 big wins among 102 trades)
cannot survive traditional confidence interval tests at small sample sizes.

### User Ruling (2026-07-09)

User identified that validation criteria must be strategy-type-adaptive:
- Standard thresholds designed for trend/wave strategies are inappropriate for sniper types
- Key focus for sniper: ruin avoidance, per-trade risk cap, positive expectancy
- Saved as memory: `feedback_validation_precheck`

### Sniper-Adapted Criteria (User-Approved)

| Criterion | Result | Verdict |
|-----------|--------|---------|
| Ruin probability < 1% | 0.03% | PASS |
| Single trade loss < 5% capital | 4.26% max | PASS |
| Kelly criterion > 0 | 11.2% | PASS |
| Expected value > 0 | +10,547/trade | PASS |
| Bear regime PF > 2.0 | 3.79 | PASS |
| Volatile regime PF > 1.0 | 2.13 | PASS |
| Max consecutive loss < 20% capital | -162,400 (16.2%) | PASS |
| Robustness 5/7 | 5/7 | PASS |

**Adapted verdict: 8/8 PASS**

---

## Losing Streak Analysis

| Streak | Period | Trades | Total Loss | Avg Loss | Cause |
|--------|--------|--------|------------|----------|-------|
| 1 | 2026-03-06~03-26 | 13 | -162,400 | -12,492 | Consolidation range (32K-34K) |
| 2 | 2026-06-09~06-23 | 8 | -159,600 | -19,950 | High-vol but no sustained drop |
| 3 | 2026-06-24~07-02 | 9 | -126,800 | -14,089 | Volatile chop after big win |
| 4 | 2025-04-11~10-13 | 7 | -97,000 | -13,857 | Bull regime false signals |
| 5 | 2026-04-24~05-08 | 5 | -96,400 | -19,280 | Recovery after tariff event |
| 6 | 2024-10-04~25-03-31 | 6 | -81,400 | -13,567 | Bull regime (20K-23K) |

**Key finding**: All streak losses are small (-600 to -41,600). No "blow-up" trade.
QuickStop is doing its job: capping each loss at ~60 pts + slippage.

---

## Regime Performance

| Regime | Trades | Net | PF | WR | Avg Trade |
|--------|--------|-----|-----|-----|-----------|
| Bear | 22 | +590,600 | 3.79 | 31.8% | +26,845 |
| Volatile | 45 | +591,600 | 2.13 | 20.0% | +13,147 |
| Bull | 35 | -106,400 | 0.70 | 20.0% | -3,040 |

Alpha concentrated in Bear + Volatile regimes. Bull = structural insurance cost.

---

## Parameter Sensitivity (from 1024-combo GA)

| Parameter | Sensitivity | Level |
|-----------|------------|-------|
| ZLEMA_Fast | 0.353 | HIGH |
| MinSlope | 0.265 | HIGH |
| ZLEMA_Slow | 0.117 | LOW |
| MaxHoldingBars | 0.059 | LOW |
| QS_MaxLoss_Pts | 0.035 | LOW |
| QS_MaxBars | 0.030 | LOW |
| StopATRMult | 0.010 | LOW |

Fast + Slope = 86% of total sensitivity. 4 exit params all LOW.
Known cliffs: Slope30 (-27.4%), S80 (-33.5%).

---

## Conclusion

S16_S v0.5 passes sniper-adapted criteria (8/8). Strategy is structurally sound for
its intended purpose: capturing momentum burst short opportunities in bear/volatile
regimes with strict per-trade risk control.

**Remaining risk**: 22.5% WR means frequent losing streaks (up to 13 consecutive).
Operator must tolerate sustained drawdowns without manual intervention.

**Next step**: User ruling on promote eligibility to live_simulation.
