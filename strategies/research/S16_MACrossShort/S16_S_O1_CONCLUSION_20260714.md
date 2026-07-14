# O-1 MinSlope Percentage Optimization — Conclusion

**Date**: 2026-07-14
**Status**: REJECTED
**Strategy**: S16_S v1.0-PROD (MinSlope=28pts fixed)
**Related Issue**: A4 (OPEN_ISSUES_20260713.md)

---

## Objective

Convert MinSlope from fixed points to percentage basis to normalize entry strictness across index levels, eliminating the year-by-year bias caused by different index price levels.

## Parameter Range Design

MinSlope_Pct 0.03% ~ 0.25%, step 0.01%, 23 combinations (Exhaustive GA).

Range rationale — derived from v1.0 fixed 28pts equivalence at historical index levels:

| Index Level | 28pts Equivalent % | Role in Range |
|---|---|---|
| 47,000 (2026 current) | 0.06% | Current equivalence point |
| 35,000 (2024) | 0.08% | Mid-range |
| 20,000 (2022) | 0.14% | Historical mid |
| 12,000 (2020) | 0.23% | Historical strictest |

- Lower bound 0.03%: test looser than current equivalence
- Upper bound 0.25%: cover historical strictest + 2-step safety margin
- Step 0.01%: 23 combos = exhaustive for single-parameter search

## GA Results Summary

| MinSlope_Pct | Net Profit | Trades | Trades/yr | PF | MDD | Calmar |
|---|---|---|---|---|---|---|
| 0.03% | -2,190K | 1773 | 247 | 0.78 | -3,217K | Loss |
| 0.06% | +294K | 541 | 75 | 1.07 | -665K | 0.06 |
| 0.08% | +743K | 291 | 41 | 1.33 | -367K | 0.28 |
| 0.12% | +560K | 104 | 14 | 1.61 | -232K | 0.34 |
| 0.13% | +621K | 83 | 12 | 1.82 | -190K | 0.46 |
| 0.15% | +716K | 45 | 6 | 2.94 | -159K | 0.63 |
| **0.16%** | **+735K** | **37** | **5** | **3.32** | **-159K** | **0.64** |
| 0.17% | +517K | 30 | 4 | 2.82 | -159K | 0.45 |
| 0.19% | +581K | 22 | 3 | 4.54 | -140K | 0.58 |
| 0.22-0.25% | +347~390K | 9-10 | 1 | 5.1-5.6 | -133K | 0.36-0.41 |

v1.0 baseline (28pts fixed): Net +1,029K, 106 trades, 17/yr, PF 1.89, MDD -272K, Calmar 0.60

Backtest period: 2019/05/10 ~ 2026/07/14 (~7.18 years), MC12 actual execution.

## Conclusion

1. **No single percentage value beats v1.0 across all dimensions** (net profit + trade count + Calmar). Best Calmar (0.16%, Calmar 0.644) has only 37 trades in 7 years — statistically insufficient.

2. **The percentage premise failed.** The assumption was "same percentage strictness = same quality entries." In reality, a 1% drop at index 20,000 = 200 pts, while at index 40,000 = 400 pts — absolute magnitude differs 2x. Bearish momentum dynamics do not distribute proportionally to index level.

3. **Both percentage and fixed points share the same fundamental limitation under 5M structure:** each parameter value is optimal for specific years' index environment, not universally applicable across all index levels. Percentage conversion did not solve this problem — it merely redistributed which years are favored.

4. **Why v1.0 fixed 28pts performs better:** It automatically becomes stricter at low index levels (less noise) and looser at high index levels (more entries in alpha-rich periods). This non-proportional filtering accidentally matches the real alpha distribution.

## Decision

**O-1 REJECTED. Maintain v1.0 MinSlope=28pts fixed points.**

v1.1-PCT code retained with `UsePercentSlope = False` for backward compatibility.

## Why WFA Is Not Suitable for Percentage Validation

WFA tests temporal parameter stability. But the percentage parameter's instability is structural (different time periods = different index levels = different optimal percentages), not overfitting. WFA cannot distinguish "regime-driven valid variation" from "curve fitting."

## Future Monitoring

| Index Level | 28pts Effective % | Action |
|---|---|---|
| <= 50,000 | >= 0.056% | No action (current state) |
| 55,000 | 0.051% | Monitor — flag for observation |
| 60,000 | 0.047% | Trigger re-optimization evaluation |
| 70,000+ | 0.040% | Mandatory MinSlope re-optimization |

Re-optimization direction: GA search for new fixed-point optimal, NOT percentage conversion.

## Lessons Learned

1. Theoretically correct normalization does not guarantee better real-world performance — market dynamics may not follow proportional assumptions.
2. A parameter "flaw" (fixed points scaling with index level) can be an accidental advantage when it matches the empirical alpha distribution.
3. Exhaustive GA with 23 combinations is the cleanest way to validate/reject such hypotheses — more convincing than theoretical arguments alone.
4. Low-frequency strategies (17 trades/year) cannot support regime-segmented parameter optimization — sample size per segment is statistically insufficient.
