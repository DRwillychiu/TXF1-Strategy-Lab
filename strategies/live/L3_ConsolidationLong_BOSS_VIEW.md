# L3 ConsolidationLong — Boss View

**Version** V14.1 Matrix Range Capture + FrozenSL + HolidayFlat_v3 (OPTIMIZED) | **Status** DEPLOY READY

---

## Performance (V14.1 Optimized, MC9 2026/07/04)

| Metric | V14.1 OPT | V13.4 Baseline | Change |
|--------|-----------|----------------|--------|
| **Net Profit** | **+2,048,000 NTD** | +697,200 | **+194%** |
| **PF** | **1.470** | 1.187 | **+24%** |
| **Win Rate** | **56.0%** | 50.4% | +5.6pp |
| **Reward Ratio** | 1.154 | 1.165 | ~flat |
| **MDD** | -378,600 (-22.3%) | -369K (-30.2%) | ~flat |
| **Net/MDD** | **5.41** | 1.89 | **+186%** |
| **Trades** | 332 / 6.1yr = 54/yr | 431 / 6.4yr = 67/yr | -19% |
| **Ann Return** | **33.3%** | ~10.9% | **+204%** |
| **Sharpe** | 0.302 | 0.467 | -35% |

---

## V14 Upgrade (2026-07-03 architecture, 2026-07-04 optimization)

**Problem**: V13 half-box design capped reward ratio at 1.1x.
CL_Entry_Bot was dead (26 trades, -10.4K). 94% profit from CL_Entry_Mid targeting only half the box.

**Solution**: Matrix Range Capture — 4 dimensions:
1. **Box filter**: skip boxes < 8.5x ATR (only trade significant consolidation)
2. **Unified support zone**: bottom 50% of box (merge Bot+Mid)
3. **Dynamic swing high target**: 80-bar 15M lookback, full range
4. **Filters**: unchanged (60M trend + Daily MA)

**Optimization**: 2-round MC9 sweep. Round 1 hit all upper bounds -> expanded range -> Round 2 converged to interior values (curve-fit excluded).

---

## What It Earns

**Consolidation box range capture** — 60M detects extreme compression (range <= 10%), buy at support zone, target dynamic resistance (full box range). Net/MDD 5.41 = best risk-adjusted return in portfolio.

---

## Entry Rules (V14.1)

1. **60M box detection**: 16-bar lookback, shrink <= 10%
2. **Box qualification**: range >= 8.5x ATR (skip small boxes)
3. **60M bullish**: Close > MA(12)
4. **Daily filter**: Close > 20MA OR 60MA
5. **15M support zone**: Close in bottom 50% of box -> Stop buy at Box_Btm
6. **Gates**: no position + no holiday + no settlement

## Exit Rules (V14.1)

| Trigger | Action |
|---------|--------|
| **Dynamic target** | Swing high (80-bar 15M lookback, capped at Box_Top) -> CL_TP |
| **Box break** | 60M close outside box -> CL_BreakExit |
| **Frozen stop** | Box_Btm - ATR x 3.0 -> CL_SL |
| **Safety** | Holiday / Settlement / Registry / Kill |

---

## Decision Summary

| Question | Answer |
|----------|--------|
| What does it do? | Consolidation box full-range capture |
| V14.1 changes? | Half-box -> full-range, dual-leg -> unified entry, box filter, 2-round optimization |
| Why upgrade? | Half-box reward ratio 1.1x structurally flawed. V14.1 = +194% net, +24% PF, same MDD |
| Risk? | Sharpe -35% (fewer trades = higher monthly variance). 2024 micro-loss (-15.8K) |
| Next step? | Deploy on MC9 (flat position, wait for next box signal) |

---

**Details**: `L3_ConsolidationLong_annotated.md` + `L3_ConsolidationLong_review.md`
