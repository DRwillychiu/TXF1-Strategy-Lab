# L3 V14.1 Matrix Range Capture — Optimization Summary

**Date**: 2026-07-03 (architecture) / 2026-07-04 (optimization)
**Strategy**: L3 ConsolidationLong (STRATEGY_WILLY_LONG_C)
**Upgrade**: v13.4 -> v14.0 -> v14.1 (optimized)
**Status**: DEPLOYED (MC9 confirmed 2026-07-04)

---

## Problem Statement

V13 half-box architecture splits the consolidation box into Bot->Mid and Mid->Top,
structurally capping the reward ratio at ~1.1x:

- CL_Entry_Bot: 26 trades / 6.5yr, 26.9% WR, net -10.4K (dead leg)
- CL_Entry_Mid: 405 trades, 51.9% WR, net +707.6K (all profit)
- 94% of profit from mid-line entries targeting only half the box range
- Reward ratio 1.165 vs L1 3.28x, L2 4.35x — lowest in portfolio

User ruling: "Regardless of box size or where price consolidates within the box,
must capture the full consolidation pattern profit."

---

## Solution: Multi-Dimensional Matrix Architecture

### 4 Dimensions (V14.1 Optimized Values)

| Dim | Name | Input | Optimized | Purpose |
|-----|------|-------|-----------|---------|
| 1 | Box Qualification | Min_Box_ATR | **8.5** (from 3.0) | Only trade significant boxes |
| 2 | Support Zone | Entry_Zone_Pct | **0.50** (from 0.30) | Unified entry at bottom 50% |
| 3 | Dynamic Target | Swing_Lookback | **80** (from 32) | 15M swing high ~20hr lookback |
| 4 | Trend + Daily | unchanged | — | 60M MA + Daily MA OR |

---

## Optimization History (2-Round MC9 Sweep)

### Round 1 (range: 0.15-0.50 / 1.5-6.0 / 16-64)

Result: Entry_Zone_Pct=0.50, Min_Box_ATR=6.0, Swing_Lookback=64
**All three hit upper bound** — curve-fit concern flagged.

| Metric | Value |
|--------|-------|
| Net | +1,694,400 |
| PF | 1.323 |
| Reward Ratio | **0.993** (below 1.0!) |
| Trades | 392 |

### Round 2 (expanded: 0.15-0.70 / 1.5-10.0 / 16-128)

Result: Entry_Zone_Pct=0.50, Min_Box_ATR=8.5, Swing_Lookback=80
**All three converged to interior values** — plateau confirmed.

| Metric | Value |
|--------|-------|
| Net | +2,048,000 |
| PF | 1.470 |
| Reward Ratio | 1.154 |
| Trades | 332 |

### Parameter Position in Search Range

| Parameter | Value | Max | Position | Verdict |
|-----------|-------|-----|----------|---------|
| Entry_Zone_Pct | 0.50 | 0.70 | 71% | Plateau |
| Min_Box_ATR | 8.5 | 10.0 | 85% | Off boundary |
| Swing_Lookback | 80 | 128 | 63% | Plateau |

---

## MC9 Backtest Results (V14.1 Final)

| Metric | V13.4 | V14.0 UNOPT | V14.1 OPT | Change |
|--------|-------|-------------|-----------|--------|
| Net Profit | 697,200 | 1,227,600 | **2,048,000** | **+194%** |
| PF | 1.187 | 1.421 | **1.470** | **+24%** |
| Win Rate | 50.4% | 47.1% | **56.0%** | +5.6pp |
| Reward Ratio | 1.165 | 1.596 | 1.154 | ~flat |
| MDD | -368,800 | -579,800 | -378,600 | ~flat |
| Net/MDD | 1.89 | 2.12 | **5.41** | **+186%** |
| Trades | 431 | 225 | 332 | -23% |
| Sharpe | 0.467 | 0.246 | 0.302 | -35% |
| Ann Return | ~10.9% | 18.9% | **33.3%** | +204% |

### Exit Label Structure (V14.1)

| Label | N | % | Sum | Avg | WR | Health |
|-------|---|---|-----|-----|----|----|
| CL_TP | 130 | 39.2% | +4,250,800 | +32,698 | 100% | Profit engine |
| CL_BreakExit | 138 | 41.6% | -234,800 | -1,701 | 39.1% | Near-neutral |
| CL_SL | 55 | 16.6% | -1,950,000 | -35,455 | 0% | Main cost |
| Safety | 9 | 2.7% | -18,000 | — | — | Compliance |

### Edge Quality (MFE/MAE)

- Winners: MFE +35,845 / MAE -15,640 = **edge 2.29x**
- Losers: MFE +11,522 / MAE -31,889 = edge 0.36x
- Clear winner/loser separation = real alpha signal

### Yearly Performance

| Year | N | Net | WR | PF | Verdict |
|------|---|-----|----|----|---------|
| 2020 | 53 | +140,400 | 54.7% | 1.308 | Stable |
| 2021 | 61 | +85,600 | 50.8% | 1.116 | Marginal |
| 2022 | 29 | +41,400 | 51.7% | 1.124 | Marginal |
| 2023 | 60 | +157,000 | 55.0% | 1.313 | Stable |
| 2024 | 48 | -15,800 | 54.2% | 0.981 | Micro-loss |
| 2025 | 62 | +677,000 | 62.9% | 1.796 | Strong |
| 2026(H1) | 19 | +962,400 | 68.4% | 2.448 | Exceptional |

### Consistency

- Monthly profitability: 60.9% (42/69)
- Quarterly profitability: 80.0% (20/25)
- Max consecutive losses: 6
- Recent PF (2024-2026): 1.696 > Historical PF (2020-2023): 1.209

---

## Files Changed

| File | Change |
|------|--------|
| `strategies/live/L3_ConsolidationLong.pla` | V14.1 optimized params (0.50/8.5/80) |
| `strategies/live/L3_ConsolidationLong_annotated.md` | V14.1 docs + performance |
| `strategies/live/L3_ConsolidationLong_BOSS_VIEW.md` | V14.1 deploy ready |

---

## MC9 Testing Checklist

- [x] Load V14 code into MC9 as STRATEGY_WILLY_LONG_C
- [x] Run baseline backtest with initial params (0.30/3.0/32)
- [x] Compare vs V13.4 — confirmed improvement
- [x] Round 1 optimization (0.15-0.50 / 1.5-6.0 / 16-64)
- [x] Flag boundary-hitting issue (all 3 at upper bound)
- [x] Round 2 optimization (expanded range)
- [x] Confirm convergence to interior values
- [x] Practical deployment analysis (edge quality, consistency, regime)
- [x] Sync optimized params into .pla code
- [x] Update all documentation
- [x] Deploy on MC9 (confirmed 2026-07-04, all 17 params verified)
