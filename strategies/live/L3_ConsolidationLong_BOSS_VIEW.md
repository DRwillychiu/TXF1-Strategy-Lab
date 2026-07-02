# L3 ConsolidationLong — Boss View

**Version** V14.0 Matrix Range Capture + FrozenSL + HolidayFlat_v3 | **Status** PENDING MC9 VALIDATION

---

## Performance (V13.4 Baseline — V14 backtest pending)

| Metric | Value |
|--------|-------|
| **Net Profit** | **+697,200 NTD** |
| **PF** | 1.187 |
| **Win Rate** | 50.4% |
| **Reward Ratio** | 1.165 |
| **MDD** | -369K (-30.2%) |
| **Trades** | 431 / 6.4yr = 67/yr |
| **Sharpe** | 0.467 |

---

## V14 Upgrade (2026-07-03)

**Problem**: V13 half-box design capped reward ratio at 1.1x.
CL_Entry_Bot was dead (26 trades, -10.4K). 94% profit from CL_Entry_Mid targeting only half the box.

**Solution**: Matrix Range Capture — 4 dimensions:
1. **Box filter**: skip boxes < 3x ATR (friction eats edge)
2. **Unified support zone**: bottom 30% of box (merge Bot+Mid)
3. **Dynamic swing high target**: full range instead of half
4. **Filters**: unchanged (60M trend + Daily MA)

**Pre-verify (28yr TWII)**: Full-range PF 1.086 vs half-box 0.806 (+35%). Reward ratio 0.90x -> 1.92x.

---

## What It Earns

**Consolidation box range capture** — 60M detects extreme compression (range <= 10%), buy at support zone, target dynamic resistance (full box range). V14 aims to double reward ratio from 1.1x to 2.0x+.

---

## Entry Rules (V14)

1. **60M box detection**: 16-bar lookback, shrink <= 10%
2. **Box qualification**: range >= 3.0x ATR (skip small boxes)
3. **60M bullish**: Close > MA(12)
4. **Daily filter**: Close > 20MA OR 60MA
5. **15M support zone**: Close in bottom 30% of box -> Stop buy at Box_Btm
6. **Gates**: no position + no holiday + no settlement

## Exit Rules (V14)

| Trigger | Action |
|---------|--------|
| **Dynamic target** | Swing high (32-bar 15M lookback, capped at Box_Top) -> CL_TP |
| **Box break** | 60M close outside box -> CL_BreakExit |
| **Frozen stop** | Box_Btm - ATR x 3.0 -> CL_SL |
| **Safety** | Holiday / Settlement / Registry / Kill |

---

## Decision Summary

| Question | Answer |
|----------|--------|
| What does it do? | Consolidation box full-range capture |
| V14 changes? | Half-box -> full-range, dual-leg -> unified entry, box filter added |
| Why upgrade? | Half-box reward ratio 1.1x structurally flawed, pre-verify confirms full-range +35% PF |
| Risk? | V14 is new architecture — must validate via MC9 backtest before deploy |
| Next step? | Load V14 in MC9, backtest, compare vs V13.4 baseline |

---

**Details**: `L3_ConsolidationLong_annotated.md` + `L3_ConsolidationLong_review.md`
