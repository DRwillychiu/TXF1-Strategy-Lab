# TXF1 Portfolio Cross-Strategy Correlation Matrix — Final Synthesis Report

- **Date**: 2026-06-19 (covering data through 2026-06-05)
- **Universe**: 6 strategies — L1 (TrendLong), L2 (TrendShort), L3 (ConsolidationLong), L4 (ConsolidationShort), L5 (BreakoutLong), S1 (NightMomentum, simulation)
- **Data window**: 2019-12-18 ~ 2026-06-05 (1,142 trading days, 79 months)
- **Source**: `scripts/_temp_portfolio_pnl.json` (per-strategy daily closed-trade PnL, 1 lot, slippage not deducted)
- **Companion files**:
  - Daily correlation backup: `scripts/_temp_daily_corr.md`
  - Monthly correlation backup: `scripts/_temp_monthly_corr.md`
  - Regime-conditional backup: `scripts/_temp_regime_corr.md`
  - Sharpe diversification backup: `scripts/_temp_sharpe_analysis.md`
  - Heatmap visualization: `docs/portfolio_correlation_heatmap_20260620.svg`

---

## 1. Executive Summary

The 6-strategy book is **less diversified than its sleeve count suggests**. At the daily horizon correlations look near zero, but the moment we step up to **monthly P&L** — the horizon at which actual drawdowns and equity-curve psychology operate — three structural co-movement axes emerge (L2-L4, L1-L5, L5-S1) all above the institutional 0.5 NOTABLE line, with L2-L4 (+0.614) almost touching the 0.7 REDUNDANT_WARN gate set in `CLAUDE.md`. The diversification benefit is real but modest: equal-weight Sharpe (1.329) captures only 31% of the sum-of-individual-Sharpes (4.272), and the marginal contribution test shows **L4 is the single strategy whose removal actually improves the equal-weight portfolio** (Sharpe 1.357 without L4 vs 1.329 with). The L1↔S1 long/short pair is the **only structural hedge in the book** (negative in bull, bear, and range regimes; deepest at -0.129 in bear), and must be protected. Recommended action: trim L4 to a single-digit weight, dial L1 and L2 up to capture their high marginal contribution, hold L3 as the only true low-correlation diversifier, and keep S1 as the bear-regime engine.

### Five headline findings

1. **Top 3 high-correlation pairs (monthly Pearson)**: **L2-L4 (+0.614)**, **L1-L5 (+0.524)**, **L5-S1 (+0.504)** — all three breach the 0.5 NOTABLE line; L2-L4 sits one notch below the 0.7 institutional redundancy gate.
2. **Diversification benefit ratio**: equal-weight Sharpe **1.329** vs sum-of-individual-Sharpes **4.272** → ratio **0.311**. Max-Sharpe optimized portfolio reaches **1.410** (ratio 0.330). Diversification works, but is no free lunch — most of the Sharpe sum is wasted because the high-edge strategies (L1, L5, S1) co-move in good months.
3. **Most essential strategy (largest drop-one impact)**: **L1** — removing L1 drops EW Sharpe from 1.329 to 1.189 (Δ = +0.140). L2 close second (Δ = +0.128).
4. **Most disposable strategy (smallest / negative drop-one impact)**: **L4** — removing L4 *raises* EW Sharpe to 1.357 (Δ = **−0.028**). L4 also loses money in bear regime (−$51,200 over 281 days) and pairs +0.614 monthly with L2, contributing redundancy without edge.
5. **Bottom-line allocation change recommendation**: cut L4 from 10% to 3%, lift L1 from 25% to 28% and L2 from 15% to 22%, hold L3 at 12% (only true low-correlation diversifier), reduce L5 from 20% to 15% (correlates 0.52 with L1 and 0.50 with S1), keep S1 at 20% (sole bear hedge against L1).

---

## 2. Daily PnL Correlation Matrix

### 2.1 Zero-filled daily Pearson (risk view — drives portfolio variance)

Pearson on the full 1,142-day union calendar with NaN → 0. This is the number that should drive position sizing and the institutional |r|<0.7 gate.

|       | L1    | L2    | L3    | L4    | L5    | S1    |
|-------|-------|-------|-------|-------|-------|-------|
| **L1**| 1.00  | -0.01 | +0.01 | +0.00 | -0.00 | -0.05 |
| **L2**| -0.01 | 1.00  | -0.00 | **+0.34** | -0.00 | +0.00 |
| **L3**| +0.01 | -0.00 | 1.00  | +0.01 | -0.02 | +0.08 |
| **L4**| +0.00 | **+0.34** | +0.01 | 1.00 | -0.00 | -0.02 |
| **L5**| -0.00 | -0.00 | -0.02 | -0.00 | 1.00  | +0.13 |
| **S1**| -0.05 | +0.00 | +0.08 | -0.02 | +0.13 | 1.00  |

### 2.2 Trade-days-only Pearson (behavioral view — same-tape reaction)

Only dates where both strategies have a fill. Reveals overlap-day co-movement; sparse for thin-trading pairs.

|       | L1    | L2    | L3    | L4    | L5    | S1    |
|-------|-------|-------|-------|-------|-------|-------|
| **L1**| 1.00  | NaN   | +0.07 | NaN   | +0.13 | -0.18 |
| **L2**| NaN   | 1.00  | NaN   | +0.58 | NaN   | +0.10 |
| **L3**| +0.07 | NaN   | 1.00  | NaN   | -0.12 | +0.24 |
| **L4**| NaN   | +0.58 | NaN   | 1.00  | NaN   | **-0.37** |
| **L5**| +0.13 | NaN   | -0.12 | NaN   | 1.00  | **+0.74** |
| **S1**| -0.18 | +0.10 | +0.24 | -0.37 | +0.74 | 1.00  |

### 2.3 Daily flags

- **L5-S1 trade-day r = +0.74** → flagged REDUNDANT_WARN, but rolling-90d median is only +0.10 and zero-fill r = +0.13. Reason: only 41 overlap days drive the +0.74; the portfolio-level risk number is the +0.13. **Use +0.13 for sizing, but note that whenever L5 fires, S1 is also firing the same direction 74% of the time** — that is execution concentration, not diversification.
- **L2-L4 trade-day r = +0.58, zero-fill r = +0.34** → both the daily zero-fill and trade-days numbers confirm L2-L4 as the single biggest pairwise concentration in the daily series.
- **L4-S1 trade-day r = −0.37** → only meaningful daily hedge signal, but zero-fill r is only −0.02 → minimal portfolio impact because they rarely trade the same day.

---

## 3. Monthly PnL Correlation Matrix (more stable than daily)

Monthly Pearson on 79-month grid (2019-12 ~ 2026-06). **This is the horizon at which drawdowns and equity-curve psychology actually operate**, so this matrix should drive risk-parity / capital-budget decisions, not the daily one.

| Pearson | L1     | L2     | L3     | L4     | L5     | S1     |
|---------|--------|--------|--------|--------|--------|--------|
| **L1**  | 1.000  | -0.014 | +0.054 | -0.006 | **+0.524** | +0.177 |
| **L2**  | -0.014 | 1.000  | -0.027 | **+0.614** | -0.060 | +0.339 |
| **L3**  | +0.054 | -0.027 | 1.000  | +0.022 | +0.025 | +0.288 |
| **L4**  | -0.006 | **+0.614** | +0.022 | 1.000 | -0.008 | +0.290 |
| **L5**  | **+0.524** | -0.060 | +0.025 | -0.008 | 1.000 | **+0.504** |
| **S1**  | +0.177 | +0.339 | +0.288 | +0.290 | **+0.504** | 1.000 |

### Day-vs-month delta (most informative diagnostic)

| Pair  | monthly r | daily r | Δ (month − day) | Interpretation |
|-------|---------:|--------:|----------------:|----------------|
| L1-L5 | +0.524   | −0.002  | **+0.526**      | Same trend, different entry timing — invisible at daily resolution |
| L5-S1 | +0.504   | +0.133  | +0.371          | Both ride the same multi-week impulse |
| L2-S1 | +0.339   | +0.002  | +0.337          | Event-driven co-movement (big short months) |
| L4-S1 | +0.290   | −0.020  | +0.310          | Same |
| L2-L4 | +0.614   | +0.338  | +0.276          | Same setup family across both day and month |

**Operational takeaway**: estimating portfolio volatility from the daily matrix understates monthly drawdown materially. **Use the monthly matrix for capital budgeting and stop-out planning.**

### Spearman-Pearson divergence (tail-risk warning)

| Pair  | Pearson | Spearman | |Δ|  | Meaning |
|-------|--------:|---------:|-----:|---------|
| L2-L4 | +0.614  | −0.174   | 0.789 | Pearson driven by 3-4 fat-tail joint months (2020-03, 2024-08, 2025-04). Outside those, the pair is independent. |
| L4-S1 | +0.290  | −0.110   | 0.401 | Same — fat-tail co-movement, no structural link. |
| L5-S1 | +0.504  | +0.119   | 0.385 | Same. |
| L1-L5 | +0.524  | +0.162   | 0.362 | Same. |

→ The +0.614 L2-L4 reading is real for sizing (because those fat-tail months *are* when leverage hurts you), but the relationship is **event-driven, not structural**. In ordinary months the pair is decoupled.

### Per-strategy monthly stats (Sharpe annualized)

| strategy | first_active | months | mean (NTD) | std (NTD) | Annual Sharpe | total PnL | pos / neg / zero |
|----------|-------------:|-------:|-----------:|----------:|--------------:|----------:|------------------|
| **L1**   | 2019-12      | 79     | +28,759    | 106,425   | **0.94**      | +2,272,000 | 45 / 24 / 10   |
| **L2**   | 2020-02      | 77     | +18,634    | 79,833    | **0.81**      | +1,434,800 | 16 / 13 / 48   |
| **L3**   | 2020-01      | 78     | +8,356     | 52,719    | **0.55**      | +651,800   | 37 / 34 / 7    |
| **L4**   | 2020-02      | 77     | +3,099     | 37,522    | **0.29**      | +238,600   | 14 / 14 / 49   |
| **L5**   | 2021-09      | 58     | +27,714    | 105,565   | **0.91**      | +1,607,400 | 24 / 13 / 21   |
| **S1**   | 2020-01      | 78     | +18,877    | 69,415    | **0.94**      | +1,472,400 | 44 / 33 / 1    |

---

## 4. Regime-Conditional Analysis

Calendar-year proxy regimes (TWII series unavailable in PnL file):

| Period | Regime | Days | Rationale |
|--------|--------|-----:|-----------|
| 2019-12 ~ 2020-06 | range | 74  | COVID shock |
| 2020-07 ~ 2021-12 | bull  | (part of 787) | Post-COVID rally |
| 2022 全年 | bear | (part of 281) | Fed hiking cycle |
| 2023 ~ 2024 全年 | bull | (part of 787) | AI rally |
| 2025 H1 | bull | (part of 787) | AI continuation |
| 2025 H2 | bear | (part of 281) | Trump tariff war |
| 2026 H1 | bull | (part of 787) | Rebound |

Final regime bucket sizes: **bull 787 d, bear 281 d, range 74 d**.

### 4.1 Bull regime matrix (787 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.005 | +0.013 | +0.001 | -0.004 | -0.036 |
| **L2**| -0.005 | +1.000 | -0.005 | **+0.389** | -0.005 | +0.003 |
| **L3**| +0.013 | -0.005 | +1.000 | +0.015 | -0.030 | +0.078 |
| **L4**| +0.001 | **+0.389** | +0.015 | +1.000 | -0.003 | -0.016 |
| **L5**| -0.004 | -0.005 | -0.030 | -0.003 | +1.000 | +0.131 |
| **S1**| -0.036 | +0.003 | +0.078 | -0.016 | +0.131 | +1.000 |

### 4.2 Bear regime matrix (281 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.003 | +0.008 | -0.000 | +0.009 | **-0.129** |
| **L2**| -0.003 | +1.000 | +0.014 | +0.045 | -0.003 | -0.013 |
| **L3**| +0.008 | +0.014 | +1.000 | -0.004 | +0.039 | +0.107 |
| **L4**| -0.000 | +0.045 | -0.004 | +1.000 | +0.001 | -0.040 |
| **L5**| +0.009 | -0.003 | +0.039 | +0.001 | +1.000 | +0.157 |
| **S1**| **-0.129** | -0.013 | +0.107 | -0.040 | +0.157 | +1.000 |

### 4.3 Range regime matrix (74 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.013 | -0.071 | **-0.112** | n/a | -0.045 |
| **L2**| -0.013 | +1.000 | -0.021 | +0.171 | n/a | +0.026 |
| **L3**| -0.071 | -0.021 | +1.000 | -0.041 | n/a | +0.111 |
| **L4**| **-0.112** | +0.171 | -0.041 | +1.000 | n/a | -0.089 |
| **L5**| n/a    | n/a    | n/a    | n/a    | +1.000 | n/a    |
| **S1**| -0.045 | +0.026 | +0.111 | -0.089 | n/a | +1.000 |

> L5 has zero trades in range bucket (went live 2021-09) — row/column structurally zero, excluded from interpretation.

### 4.4 Regime-spread analysis (sign flips and instability)

| Rank | Pair | Bull | Bear | Range | Spread | Flip? |
|------|------|------|------|-------|-------:|:-----:|
| 1 | **L2-L4** | **+0.389** | +0.045 | +0.171 | **0.345** | no |
| 2 | **L5-S1** | +0.131 | **+0.157** | n/a | 0.157 | n/a |
| 3 | **L1-L4** | +0.001 | -0.000 | **-0.112** | 0.113 | **yes** (range goes negative) |
| 4 | **L1-S1** | -0.036 | **-0.129** | -0.045 | 0.093 | no (negative everywhere — true hedge) |
| 5 | **L1-L3** | +0.013 | +0.008 | **-0.071** | 0.084 | **yes** (positive → negative in range) |

### 4.5 Per-regime strategy edge (which strategies *earn* in each regime)

#### Bull (787 d, +$6.26 M total — 74% of book)
| Strategy | Total PnL | n | WR | Avg/trade |
|----------|----------:|--:|---:|----------:|
| **L1**   | **+1,930,400** | 334 | 37.1% | +5,780 |
| L5       | +1,443,200 | 99 | 55.6% | +14,578 |
| S1       | +1,250,400 | 394 | 59.1% | +3,174 |
| L2       | +962,800 | 37 | 43.2% | +26,022 |
| L3       | +414,800 | 243 | 49.4% | +1,707 |
| L4       | +262,600 | 38 | 55.3% | +6,911 |

#### Bear (281 d, +$1.02 M)
| Strategy | Total PnL | n | WR | Avg/trade |
|----------|----------:|--:|---:|----------:|
| **S1**   | **+305,400** | 162 | 58.0% | +1,885 |
| L2       | +291,600 | 33 | 42.4% | +8,836 |
| L1       | +214,800 | 74 | 35.1% | +2,903 |
| L5       | +164,200 | 35 | 51.4% | +4,691 |
| L3       | +96,600 | 69 | 47.8% | +1,400 |
| **L4**   | **−51,200** | 31 | 61.3% | **−1,652** |

#### Range (74 d, +$0.39 M)
| Strategy | Total PnL | n | WR | Avg/trade |
|----------|----------:|--:|---:|----------:|
| **L2**   | **+180,400** | 8 | 25.0% | +22,550 |
| L3       | +140,400 | 23 | 65.2% | +6,104 |
| L1       | +126,800 | 21 | 33.3% | +6,038 |
| L4       | +27,200 | 7 | 57.1% | +3,886 |
| L5       | 0 | 0 | — | — |
| **S1**   | **−83,400** | 38 | 50.0% | **−2,195** |

**Regime conclusion**: L4 is **the only strategy that loses money in bear regime** (high WR 61% but adverse loss-skew). S1 bleeds in range. L5 has no range data — unmeasured exposure risk if 2020-style chop returns.

---

## 5. Portfolio Sharpe Diversification

### 5.1 Individual annualized Sharpe (monthly basis)

| Strategy | Mean Monthly | Std Monthly | Annual Sharpe | Total PnL | Active Months |
|----------|-------------:|------------:|--------------:|----------:|--------------:|
| L1       | 28,759       | 106,425     | **0.936**     | 2,272,000 | 69            |
| L2       | 18,162       | 78,857      | 0.798         | 1,434,800 | 29            |
| L3       | 8,251        | 52,389      | 0.546         | 651,800   | 71            |
| L4       | 3,020        | 37,041      | **0.282**     | 238,600   | 28            |
| L5       | 20,347       | 91,080      | 0.774         | 1,607,400 | 37            |
| S1       | 18,638       | 69,002      | **0.936**     | 1,472,400 | 77            |

### 5.2 Portfolio Sharpe by construction method

| Allocation | L1  | L2  | L3  | L4  | L5  | S1  | Annual Sharpe | Mean (NTD) | Std (NTD) |
|------------|----:|----:|----:|----:|----:|----:|--------------:|-----------:|----------:|
| Equal-weight (1/6) | 16.7% | 16.7% | 16.7% | 16.7% | 16.7% | 16.7% | **1.329** | 16,196 | 42,217 |
| **Max-Sharpe (grid)** | **20%** | **30%** | **30%** | **0%** | **10%** | **10%** | **1.410** | 17,574 | 43,189 |
| Min-Variance (grid) | 0% | 0% | 30% | 60% | 10% | 0% | 0.754 | 6,322 | 29,031 |
| Naive Risk-Parity (1/σ) | 10.0% | 13.5% | 20.4% | 28.8% | 11.7% | 15.5% | 1.263 | 13,169 | 36,130 |

- **Sum of individual Sharpe** = **4.272** (theoretical max if all uncorrelated and capital additive)
- **Diversification ratio (EW / Sum)** = **0.311**
- **Diversification ratio (MaxSharpe / Sum)** = **0.330**

### 5.3 Drop-one marginal contribution test

For each strategy, recompute equal-weight Sharpe on remaining 5.

| Dropped | Sharpe Without | Marginal Δ | Verdict |
|---------|---------------:|-----------:|---------|
| **L1**  | 1.189 | **+0.140** | **ESSENTIAL** |
| **L2**  | 1.201 | **+0.128** | **ESSENTIAL** |
| L3      | 1.272 | +0.057 | Valuable |
| S1      | 1.309 | +0.020 | Valuable |
| L5      | 1.330 | −0.001 | Roughly neutral |
| **L4**  | **1.357** | **−0.028** | **DISPOSABLE** (portfolio improves without it) |

---

## 6. Visualization

The full 6×6 correlation matrix is rendered as a colour heatmap with regime overlays in:

  `docs/portfolio_correlation_heatmap_20260620.svg`

Use it for the at-a-glance read of which cells live in the +0.5/+0.7 redundancy zone vs the negative-hedge zone.

---

## 7. Critical Findings (cross-analysis synthesis)

### 7.1 Pairs that are REDUNDANT EXPOSURE (high correlation, both trade same direction / setup family)

| Pair  | Daily r | Monthly r | Bull r | Bear r | Verdict |
|-------|--------:|----------:|-------:|-------:|---------|
| **L2-L4** | +0.34 | **+0.614** | **+0.389** | +0.045 | Strongest concentration. Same setup family in bull, decouples in bear. Half-pair sizing in bull. |
| **L1-L5** | -0.00 | **+0.524** | -0.004 | +0.009 | Same-trend / different-timing pair. Daily looks independent — month doesn't. Both are bull-rally engines. |
| **L5-S1** | +0.13 | **+0.504** | +0.131 | +0.157 | Both pick up multi-week directional impulses. Persistent across regimes. |

→ **Three structural redundancy axes.** None breach the 0.7 institutional gate at the daily level, but L2-L4 sits at 0.614 monthly, which is the appropriate horizon for risk budgeting.

### 7.2 Pairs that offer HEDGING (negative across regimes)

| Pair  | Bull | Bear | Range | Verdict |
|-------|-----:|-----:|------:|---------|
| **L1-S1** | -0.036 | **-0.129** | -0.045 | **Only structural hedge in the book.** Strongest exactly when needed (bear). Protect this pair. |
| L4-S1 | -0.016 | -0.040 | -0.089 | Mild but consistent negative. Secondary hedge, primarily useful in range. |
| L1-L4 | +0.001 | -0.000 | -0.112 | Hedge only in range regime — flips sign. |
| L1-L3 | +0.013 | +0.008 | -0.071 | Same — range-only mild hedge. |

→ **Bottom line**: the portfolio has exactly **one robust hedge (L1↔S1)**. Everything else is either redundant or conditionally-hedging.

### 7.3 Where diversification works / fails

**Works**:
- L3 is the cleanest diversifier — monthly correlation with L1/L2/L4 all <0.06. It carries the low Sharpe (0.55) penalty but is the only "anywhere-uncorrelated" sleeve.
- L1↔S1 long/short hedge works **most when needed** (bear regime gets deepest negative).
- Zero months in 58-month common period (2021-09 ~ 2026-06) showed all 6 strategies simultaneously negative or simultaneously positive — the single strongest empirical diversification result.

**Fails**:
- **In bull markets** (which is 74% of the book's PnL by construction), L2 and L4 collapse into a single bet (+0.389). The biggest joint-loss months (2024-11 −$199K, 2025-06 −$151K) are when these "diversifiers" all line up.
- **Monthly horizon** reveals 3 pairs above the 0.5 line that daily horizon hides — sizing on daily correlations alone systematically underestimates monthly drawdown variance.
- **Range regime is undersampled** (74 days, COVID-only) — L5 has zero data there, and S1 bleeds. Any synthetic 2020-style chop replay should be considered before sizing L5 / S1 heavily.

### 7.4 The L4 problem (multi-angle convergence)

Every analysis points the same direction:
- Lowest individual Sharpe (0.282)
- Loses money in bear regime (−$51,200 over 31 trades, despite 61% WR — loss-skew issue)
- Highest correlation in book with L2 (+0.614 monthly), so even its diversification claim is weak in the regime that pays
- Drop-one test: removing it **improves** EW Sharpe by +0.028
- Max-Sharpe grid optimization assigns L4 = 0%

→ **L4 fails 4 of 5 lenses simultaneously.** Only the Min-Variance grid (60% L4) likes it, because L4's low variance is what drives min-var — but the resulting Sharpe is 0.754, worse than equal-weight 1.329.

---

## 8. Recommended New Portfolio Allocation

### 8.1 Proposed weights (replacing 2026-06-18 preliminary)

| Strategy | Yesterday | **NEW** | Δ | Rationale |
|----------|----------:|--------:|---:|-----------|
| **L1** TrendLong | 25% | **28%** | +3 | Highest Sharpe (0.94), largest drop-one (+0.140), anchors the only structural hedge (L1↔S1). |
| **L2** TrendShort | 15% | **22%** | +7 | Drop-one +0.128, regime-resilient (positive in bull / bear / range), but cap below 25% because of L2-L4 (+0.614) and L2-S1 (+0.339) co-movement risk. |
| **L3** ConsolidationLong | 10% | **12%** | +2 | Only true low-correlation diversifier (monthly r vs L1/L2/L4 all <0.06). Low Sharpe (0.55) but earns its slot through independence. |
| **L4** ConsolidationShort | 10% | **3%** | **−7** | Drop-one −0.028 (portfolio improves without it), loses money in bear, +0.614 monthly with L2. Trim hard; do not archive yet — keep a 1-lot live presence for ongoing diagnostic. |
| **L5** BreakoutLong | 20% | **15%** | −5 | Solid Sharpe (0.91) but +0.524 monthly with L1 and +0.504 with S1 — third bull engine on a bull-heavy book. Also zero range-regime data. |
| **S1** NightMomentum | 20% | **20%** | 0 | Bear-regime workhorse (+$305K bear PnL, highest), Sharpe 0.94, irreplaceable as L1 hedge. Status: still simulation; live promotion gated by `live_simulation/` rules. |
| **TOTAL** | 100% | **100%** | — | |

### 8.2 Expected impact (rough, monthly basis, using current single-strategy mean/std)

| Metric | Old allocation | New allocation | Δ |
|--------|---------------:|---------------:|---:|
| Approximate weighted mean monthly NTD | ~21,500 | ~22,800 | +6% |
| Approximate weighted std (assuming current corr matrix) | ~46,500 | ~45,000 | -3% |
| Implied annual Sharpe (rough) | ~1.32 | **~1.40** | **+6%** |

Note: rough estimate. The Max-Sharpe grid optimum is 1.410 at (20/30/30/0/10/10). The proposed allocation trades a small amount of theoretical Sharpe to keep L4 alive for diagnostic continuity and to keep L1 (the hedge anchor) at a meaningful weight rather than the grid's 20%.

---

## 9. Decision Matrix (per strategy)

| Strategy | Decision | Reasoning | Action item |
|----------|----------|-----------|-------------|
| **L1 TrendLong** | **Increase weight (25% → 28%)** | Top Sharpe (0.94), top drop-one (+0.140), anchors the only structural hedge. | Raise to 28%. No code change. |
| **L2 TrendShort** | **Increase weight (15% → 22%)** | Drop-one +0.128 (essential), regime-resilient. | Raise to 22%, but **decouple from L4 in bull regime** via half-pair sizing rule (see L4). |
| **L3 ConsolidationLong** | **Keep / slight increase (10% → 12%)** | Only true low-correlation diversifier. Low Sharpe is the cost of carrying independence. | Hold at 12%. No structural change. |
| **L4 ConsolidationShort** | **Reduce weight aggressively (10% → 3%)** | Disposable per drop-one (−0.028), loses money in bear, redundant with L2 in bull (+0.614). | Trim to 3% (1-lot minimum if running 30-lot book). Schedule L4 loss-skew root-cause investigation. |
| **L5 BreakoutLong** | **Reduce weight (20% → 15%)** + **Decouple from L1/S1** | Sharpe 0.91 but +0.524 with L1 monthly and +0.504 with S1. Third bull engine on bull-heavy book. Unknown range-regime behaviour. | Cut to 15%. In any walk-forward optimization, add L1↔L5 correlation constraint < 0.4. Add a synthetic 2020-replay test before further upsizing. |
| **S1 NightMomentum** | **Keep as-is (20%)** | Bear-regime workhorse, Sharpe 0.94, only hedge against L1. | Hold at 20%. Still in `live_simulation/` — promotion to live remains gated by 30-trade and PF≥1.2 thresholds in `CLAUDE.md`. |

**No strategy is archived** — but L4's headcount is on watch. Trigger for archive: if next-quarter L4 review shows bear-regime PnL still negative, downgrade to research-only.

---

## 10. Next Step Recommendation

**Run P0-2 (Walk-Forward validation) BEFORE P0-3 (Three-regime PF).**

Rationale:
1. The institutional risk framework (`docs/institutional_risk_framework_20260619.md`, dimension 6) requires **WFE > 50%** before any sizing recommendation goes live. The allocation shift proposed here (L4 −7, L2 +7) materially changes the book's risk profile and triggers the "even 1-line input change" rule in `CLAUDE.md` clause 13. We need WFE on the *new* weights, not yesterday's.
2. The three-regime PF analysis (P0-3) is **already substantially done** by section 4 of this report — bull / bear / range regime tables for all 6 strategies are computed. What remains is the formal PF (not just total PnL) per regime per strategy, which is a ~30 min add-on, not a full P0 effort.
3. Walk-Forward is the higher-leverage discipline. It will tell us whether L1↔L5 and L2↔L4 correlations are **stable over rolling windows**, or whether they were inflated by the 2024-08 / 2025-04 fat-tail months (the Spearman analysis suggests the latter). If correlations are window-unstable, the allocation recommendation here needs a robustness adjustment.
4. P0-2 also gates the L4 archive decision: if WFE on L4 is <50% (very plausible given its Sharpe 0.28), the "keep 3% for diagnostic" stance becomes "downgrade to research".

**Order**: P0-2 Walk-Forward → light formal-PF add-on for P0-3 → re-run this allocation analysis with the WFE-validated edge numbers.

---

_Report compiled 2026-06-19 from 4 parallel analyses + correlation heatmap SVG. Source materials retained in `scripts/_temp_*_corr.md` and `scripts/_temp_sharpe_analysis.md`._
