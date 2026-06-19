# TXF1 6-Strategy Daily PnL Correlation Analysis

Generated from `_temp_portfolio_pnl.json` on union of trade dates (1142 unique dates, 2019-12-18 ~ 2026-06-05).

## 1. Methodology

- **Source**: per-strategy daily PnL dict (strategy -> date -> NTD).
- **Universe**: 6 strategies — L1 (TrendLong), L2 (TrendShort), L3 (ConsolidationLong), L4 (ConsolidationShort), L5 (BreakoutLong), S1 (NightMomentum, simulation).
- **Index**: sorted union of all trading dates that appear in any strategy's PnL series. Cells are NaN when that strategy did not trade that day.
- **Formula**: Pearson product-moment correlation `r = cov(X, Y) / (std(X) * std(Y))`.
- **Two NaN treatments**:
  1. *Trade-days only (pairwise dropna)*: for each pair, keep only rows where both strategies traded. This measures co-movement *given* both strategies were active. `min_periods=10` to avoid spurious small-sample noise.
  2. *Zero-filled*: replace NaN with 0 (no trade = 0 PnL = no opinion). This measures portfolio-level daily co-movement, which is what actually drives portfolio variance.
- **Rolling stability**: 90-trading-day rolling Pearson (on zero-filled series), then take the median of the rolling series per pair. Stable pairs have rolling median close to the static estimate.
- **Thresholds** (per request):
  - `|r| > 0.5` -> NOTABLE
  - `|r| > 0.7` -> REDUNDANT_WARN (overlapping exposure, fails CLAUDE.md institutional risk gate: cross-strategy correlation < 0.7)
  - `r < -0.3` -> HEDGE_VALUE (meaningful negative correlation)

### Trade-day coverage per strategy

| Strategy | Trade days | First trade | Last trade |
|---|---|---|---|
| L1 | 429 | 2019-12-18 | 2026-06-03 |
| L2 | 78 | 2020-02-10 | 2025-06-03 |
| L3 | 335 | 2020-01-07 | 2026-05-29 |
| L4 | 76 | 2020-02-22 | 2025-05-07 |
| L5 | 135 | 2021-09-16 | 2026-06-05 |
| S1 | 594 | 2020-01-03 | 2026-06-03 |

### Pairwise trade-day overlap (both strategies active)

| | L1 | L2 | L3 | L4 | L5 | S1 |
|---|---|---|---|---|---|---|
| **L1** | 429.00 | 4.00 | 109.00 | 7.00 | 32.00 | 160.00 |
| **L2** | 4.00 | 78.00 | 7.00 | 25.00 | 0.00 | 20.00 |
| **L3** | 109.00 | 7.00 | 335.00 | 6.00 | 44.00 | 131.00 |
| **L4** | 7.00 | 25.00 | 6.00 | 76.00 | 0.00 | 30.00 |
| **L5** | 32.00 | 0.00 | 44.00 | 0.00 | 135.00 | 41.00 |
| **S1** | 160.00 | 20.00 | 131.00 | 30.00 | 41.00 | 594.00 |

## 2. Trade-days-only correlation (pairwise dropna)

Pearson r computed only on dates where *both* strategies have a fill. Answers: *when both are active, do their daily P&Ls move together?*

| | L1 | L2 | L3 | L4 | L5 | S1 |
|---|---|---|---|---|---|---|
| **L1** | 1.00 | NaN | 0.07 | NaN | 0.13 | -0.18 |
| **L2** | NaN | 1.00 | NaN | 0.58 | NaN | 0.10 |
| **L3** | 0.07 | NaN | 1.00 | NaN | -0.12 | 0.24 |
| **L4** | NaN | 0.58 | NaN | 1.00 | NaN | -0.37 |
| **L5** | 0.13 | NaN | -0.12 | NaN | 1.00 | 0.74 |
| **S1** | -0.18 | 0.10 | 0.24 | -0.37 | 0.74 | 1.00 |

## 3. Zero-filled correlation

Pearson r on the full union calendar with NaN -> 0. Answers: *at the portfolio level, do their daily contributions move together?*

| | L1 | L2 | L3 | L4 | L5 | S1 |
|---|---|---|---|---|---|---|
| **L1** | 1.00 | -0.01 | 0.01 | 0.00 | -0.00 | -0.05 |
| **L2** | -0.01 | 1.00 | -0.00 | 0.34 | -0.00 | 0.00 |
| **L3** | 0.01 | -0.00 | 1.00 | 0.01 | -0.02 | 0.08 |
| **L4** | 0.00 | 0.34 | 0.01 | 1.00 | -0.00 | -0.02 |
| **L5** | -0.00 | -0.00 | -0.02 | -0.00 | 1.00 | 0.13 |
| **S1** | -0.05 | 0.00 | 0.08 | -0.02 | 0.13 | 1.00 |

## 4. Notable pairs

All 15 unordered pairs, sorted by max(|r_pairwise|, |r_zerofill|) descending.

| Pair | Overlap days | r (trade-days) | r (zero-fill) | r (rolling 90d median) | Tags |
|---|---|---|---|---|---|
| L5-S1 | 41 | 0.74 | 0.13 | 0.10 | REDUNDANT_WARN (|r|>0.7) |
| L2-L4 | 25 | 0.58 | 0.34 | 0.00 | NOTABLE (|r|>0.5) |
| L4-S1 | 30 | -0.37 | -0.02 | -0.03 | HEDGE_VALUE (r<-0.3) |
| L3-S1 | 131 | 0.24 | 0.08 | 0.09 | - |
| L1-S1 | 160 | -0.18 | -0.05 | -0.06 | - |
| L1-L5 | 32 | 0.13 | -0.00 | 0.00 | - |
| L3-L5 | 44 | -0.12 | -0.02 | 0.08 | - |
| L2-S1 | 20 | 0.10 | 0.00 | 0.00 | - |
| L1-L3 | 109 | 0.07 | 0.01 | -0.00 | - |
| L3-L4 | 6 | NaN | 0.01 | -0.01 | INSUFFICIENT_DATA |
| L1-L2 | 4 | NaN | -0.01 | -0.00 | INSUFFICIENT_DATA |
| L2-L5 | 0 | NaN | -0.00 | 0.00 | INSUFFICIENT_DATA |
| L2-L3 | 7 | NaN | -0.00 | 0.01 | INSUFFICIENT_DATA |
| L4-L5 | 0 | NaN | -0.00 | -0.00 | INSUFFICIENT_DATA |
| L1-L4 | 7 | NaN | 0.00 | 0.00 | INSUFFICIENT_DATA |

### 4a. Pairs with |r| > 0.7 (REDUNDANT_WARN)

- **L5-S1**: trade-days r=0.74, zero-fill r=0.13, rolling median r=0.10

### 4b. Pairs with 0.5 < |r| <= 0.7 (NOTABLE)

- **L2-L4**: trade-days r=0.58, zero-fill r=0.34, rolling median r=0.00

### 4c. Pairs with r < -0.3 (HEDGE_VALUE)

- **L4-S1**: trade-days r=-0.37, zero-fill r=-0.02, rolling median r=-0.03

## 5. Rolling 90-day correlation stability

Median of 90-trading-day rolling Pearson (on zero-filled series). Compare against section 3 (zero-fill static r) to gauge whether the relationship is stable over time or driven by a few regime episodes.

| | L1 | L2 | L3 | L4 | L5 | S1 |
|---|---|---|---|---|---|---|
| **L1** | 1.00 | -0.00 | -0.00 | 0.00 | 0.00 | -0.06 |
| **L2** | -0.00 | 1.00 | 0.01 | 0.00 | 0.00 | 0.00 |
| **L3** | -0.00 | 0.01 | 1.00 | -0.01 | 0.08 | 0.09 |
| **L4** | 0.00 | 0.00 | -0.01 | 1.00 | -0.00 | -0.03 |
| **L5** | 0.00 | 0.00 | 0.08 | -0.00 | 1.00 | 0.10 |
| **S1** | -0.06 | 0.00 | 0.09 | -0.03 | 0.10 | 1.00 |

### Stability deltas (|rolling_median - zero_fill_static|)

| Pair | r_zerofill | r_rolling_median | |delta| | Verdict |
|---|---|---|---|---|
| L2-L4 | 0.34 | 0.00 | 0.33 | UNSTABLE / REGIME-DEPENDENT |
| L3-L5 | -0.02 | 0.08 | 0.10 | STABLE |
| L5-S1 | 0.13 | 0.10 | 0.03 | VERY STABLE |
| L3-L4 | 0.01 | -0.01 | 0.02 | VERY STABLE |
| L2-L3 | -0.00 | 0.01 | 0.01 | VERY STABLE |
| L1-S1 | -0.05 | -0.06 | 0.01 | VERY STABLE |
| L1-L3 | 0.01 | -0.00 | 0.01 | VERY STABLE |
| L2-L5 | -0.00 | 0.00 | 0.01 | VERY STABLE |
| L3-S1 | 0.08 | 0.09 | 0.01 | VERY STABLE |
| L4-S1 | -0.02 | -0.03 | 0.01 | VERY STABLE |
| L1-L2 | -0.01 | -0.00 | 0.00 | VERY STABLE |
| L2-S1 | 0.00 | 0.00 | 0.00 | VERY STABLE |
| L1-L5 | -0.00 | 0.00 | 0.00 | VERY STABLE |
| L4-L5 | -0.00 | -0.00 | 0.00 | VERY STABLE |
| L1-L4 | 0.00 | 0.00 | 0.00 | VERY STABLE |

## 6. Interpretation

### Headline read

- 1 pair(s) breach the |r|>0.7 institutional redundancy gate. Review whether both strategies are paying separate slippage for the same exposure.

### Strongest positive co-movement (zero-fill basis)

- L2-L4: r=0.34 (trade-days r=0.58). Long-long or short-short pair.
- L5-S1: r=0.13 (trade-days r=0.74). Cross-direction pair.
- L3-S1: r=0.08 (trade-days r=0.24). Cross-direction pair.

### Strongest negative co-movement (zero-fill basis)

- L1-S1: r=-0.05 (trade-days r=-0.18).
- L4-S1: r=-0.02 (trade-days r=-0.37).
- L3-L5: r=-0.02 (trade-days r=-0.12).

### Trade-days vs zero-fill divergence

- L5-S1: trade-days r=0.74 vs zero-fill r=0.13 (delta=+0.61). Large delta means co-movement on overlapping days differs from the diluted portfolio-level view — overlap is rare, so the zero-fill number is the one to use for sizing.
- L4-S1: trade-days r=-0.37 vs zero-fill r=-0.02 (delta=-0.35). Large delta means co-movement on overlapping days differs from the diluted portfolio-level view — overlap is rare, so the zero-fill number is the one to use for sizing.
- L2-L4: trade-days r=0.58 vs zero-fill r=0.34 (delta=+0.24). Large delta means co-movement on overlapping days differs from the diluted portfolio-level view — overlap is rare, so the zero-fill number is the one to use for sizing.

### Recommendation

- **Pairwise dropna r** answers a behavioral question (do they react the same way to the same day's tape?). Useful for entry-condition redundancy diagnosis.
- **Zero-filled r** answers a risk question (does my book have concentrated daily exposure?). This is the number that should drive position sizing and the institutional |r|<0.7 gate.
- **Rolling median** answers a stability question. Any pair where rolling_median diverges from the static estimate by >0.20 is regime-dependent — its diversification benefit may evaporate in the next regime, so do not lean on it.
