# P0-1 Rolling Correlation Analysis (Fat-Tail Verification)

_Generated: 2026-06-19_

---

## 1. Methodology

**Question**: For pairs where Pearson and Spearman disagree (esp. L2-L4 Pearson +0.614 vs Spearman -0.174),
is the Pearson correlation a genuine structural link or an artifact driven by a handful of fat-tail months?

**Data**:
- Daily PnL from `_temp_portfolio_pnl.json`
- Date range: 2019-12-18 ~ 2026-06-05
- Aggregated to monthly sums (N = 79 months)

**Tests per pair**:
1. **Rolling 12-month Pearson correlation** — monthly series, 12-month window
2. **Rolling 6-month Pearson correlation** — faster sensitivity to regime shifts
3. **Top-5 fat-tail months** — ranked by joint magnitude `|pnl_A| * |pnl_B|`
4. **Outlier-removal Pearson** — recompute correlation after dropping those 5 months
5. **Stability score** = `std(rolling_12mo_corr) / |median(rolling_12mo_corr)|`
   - <0.5: very stable; 0.5-1.0: stable; 1.0-2.0: unstable; >2.0: regime-dependent

**Verdict logic**:
- **STRUCTURAL**: rolling correlation stable, sign doesn't flip, outlier removal preserves Pearson
- **ARTIFACT**: full-sample Pearson collapses (>50% magnitude loss or sign flip) when 5 outliers removed
- **TIME-VARYING**: rolling correlation crosses zero with meaningful positive AND negative regimes (each >2 months at |r|>0.1)

---

## 2. Per-Pair Rolling Correlation Series

| Pair | Full Pearson | Full Spearman | Roll-12 Median | Roll-12 Std | Roll-12 Min | Roll-12 Max | Roll-6 Median | Roll-6 Std | Stability |
|------|-------------:|--------------:|---------------:|------------:|------------:|------------:|--------------:|-----------:|----------:|
| **L2-L4** | +0.614 | -0.174 | +0.092 | 0.601 | -0.774 | +0.994 | +0.233 | 0.695 | 6.50 |
| **L1-L5** | +0.524 | +0.162 | +0.256 | 0.264 | -0.406 | +0.662 | +0.359 | 0.432 | 1.03 |
| **L5-S1** | +0.504 | +0.119 | -0.044 | 0.274 | -0.654 | +0.582 | -0.000 | 0.406 | 6.18 |
| **L1-S1** | +0.177 | +0.164 | +0.132 | 0.242 | -0.381 | +0.623 | +0.043 | 0.364 | 1.83 |

### Rolling-12 regime distribution

How many 12-month windows show positive (>+0.1), neutral, or negative (<-0.1) correlation:

| Pair | Pos windows | Neutral | Neg windows | Total | Sign-flip? |
|------|------------:|--------:|------------:|------:|:----------:|
| **L2-L4** | 28 | 8 | 26 | 62 | YES |
| **L1-L5** | 44 | 7 | 6 | 57 | YES |
| **L5-S1** | 19 | 18 | 20 | 57 | YES |
| **L1-S1** | 37 | 9 | 22 | 68 | YES |

---

## 3. Outlier-Month Removal Test

For each pair, the 5 months with highest joint magnitude `|pnl_A| * |pnl_B|` are dropped.
If full-sample Pearson collapses, the original number was fat-tail driven (artifact).

| Pair | Full Pearson | Clean Pearson (-5 outliers) | Collapse % | Clean Spearman | Diagnosis |
|------|-------------:|----------------------------:|-----------:|---------------:|:----------|
| **L2-L4** | +0.614 | -0.144 | +123.5% | -0.308 | Sign FLIPPED — strong artifact |
| **L1-L5** | +0.524 | +0.006 | +98.9% | +0.152 | Severe collapse |
| **L5-S1** | +0.504 | +0.193 | +61.8% | +0.087 | Moderate collapse |
| **L1-S1** | +0.177 | +0.075 | +57.7% | +0.187 | Moderate collapse |

### Top-5 joint-magnitude months per pair

#### L2-L4

| Month | L2 PnL | L4 PnL | Joint magnitude | Same sign? |
|-------|--------:|--------:|----------------:|:----------:|
| 2025-04 | +439,000 | +286,600 | 125,817,400,000 | YES |
| 2024-08 | +436,600 | +57,600 | 25,148,160,000 | YES |
| 2020-03 | +238,200 | +26,200 | 6,240,840,000 | YES |
| 2022-10 | +75,400 | -72,800 | 5,489,120,000 | no (opposing) |
| 2022-06 | +68,800 | -45,600 | 3,137,280,000 | no (opposing) |

#### L1-L5

| Month | L1 PnL | L5 PnL | Joint magnitude | Same sign? |
|-------|--------:|--------:|----------------:|:----------:|
| 2026-04 | +618,200 | +667,600 | 412,710,320,000 | YES |
| 2025-11 | -228,600 | -94,800 | 21,671,280,000 | YES |
| 2026-05 | -102,000 | +146,200 | 14,912,400,000 | no (opposing) |
| 2024-06 | +178,600 | +53,400 | 9,537,240,000 | YES |
| 2025-01 | +156,800 | -51,000 | 7,996,800,000 | no (opposing) |

#### L5-S1

| Month | L5 PnL | S1 PnL | Joint magnitude | Same sign? |
|-------|--------:|--------:|----------------:|:----------:|
| 2026-04 | +667,600 | +246,400 | 164,496,640,000 | YES |
| 2026-03 | +349,200 | +251,600 | 87,858,720,000 | YES |
| 2026-05 | +146,200 | +233,200 | 34,093,840,000 | YES |
| 2025-11 | -94,800 | +187,600 | 17,784,480,000 | no (opposing) |
| 2026-01 | +89,600 | -175,600 | 15,733,760,000 | no (opposing) |

#### L1-S1

| Month | L1 PnL | S1 PnL | Joint magnitude | Same sign? |
|-------|--------:|--------:|----------------:|:----------:|
| 2026-04 | +618,200 | +246,400 | 152,324,480,000 | YES |
| 2025-11 | -228,600 | +187,600 | 42,885,360,000 | no (opposing) |
| 2026-05 | -102,000 | +233,200 | 23,786,400,000 | no (opposing) |
| 2025-09 | +256,000 | +56,000 | 14,336,000,000 | YES |
| 2024-08 | +51,000 | +205,400 | 10,475,400,000 | YES |

---

## 4. Verdict Per Pair

| Pair | Full Pearson | Clean Pearson | Roll-12 Stability | Verdict |
|------|-------------:|--------------:|------------------:|:--------|
| **L2-L4** | +0.614 | -0.144 | 6.50 | **ARTIFACT** |
| **L1-L5** | +0.524 | +0.006 | 1.03 | **ARTIFACT** |
| **L5-S1** | +0.504 | +0.193 | 6.18 | **ARTIFACT** |
| **L1-S1** | +0.177 | +0.075 | 1.83 | **ARTIFACT** |

### L2-L4 → ARTIFACT

- Full-sample Pearson: **+0.614**, Spearman: **-0.174** (delta +0.789)
- Rolling-12 median: **+0.092**, range `[-0.774, +0.994]`, std 0.601
- After removing top-5 fat-tail months: Pearson **-0.144** (+123.5% change)
- Sign-flip windows: 28 positive / 26 negative

### L1-L5 → ARTIFACT

- Full-sample Pearson: **+0.524**, Spearman: **+0.162** (delta +0.362)
- Rolling-12 median: **+0.256**, range `[-0.406, +0.662]`, std 0.264
- After removing top-5 fat-tail months: Pearson **+0.006** (+98.9% change)
- Sign-flip windows: 44 positive / 6 negative

### L5-S1 → ARTIFACT

- Full-sample Pearson: **+0.504**, Spearman: **+0.119** (delta +0.385)
- Rolling-12 median: **-0.044**, range `[-0.654, +0.582]`, std 0.274
- After removing top-5 fat-tail months: Pearson **+0.193** (+61.8% change)
- Sign-flip windows: 19 positive / 20 negative

### L1-S1 → ARTIFACT

- Full-sample Pearson: **+0.177**, Spearman: **+0.164** (delta +0.013)
- Rolling-12 median: **+0.132**, range `[-0.381, +0.623]`, std 0.242
- After removing top-5 fat-tail months: Pearson **+0.075** (+57.7% change)
- Sign-flip windows: 37 positive / 22 negative

---

## 5. Implication for L4 Keep-or-Cut Decision

### L2-L4 finding (verdict: **ARTIFACT**)

- The headline Pearson **+0.614** vs Spearman **-0.174** divergence is now explained.
- After removing 5 joint fat-tail months, Pearson collapses to **-0.144**, 
  confirming the +0.614 was driven by a few overlapping crisis windows where both shorts (L2, L4) 
  fired together. In normal months they are uncorrelated or mildly negative.
- **Implication**: L4's diversification penalty against L2 is overstated by Pearson. 
  The portfolio benefit of keeping L4 may be larger than the Pearson-based correlation matrix suggests.

### L1-L5 finding (verdict: **ARTIFACT**)

- Daily 0.00 vs Monthly +0.524 was the largest day-month delta. Rolling-12 median **+0.256**.
- Outlier-clean Pearson: **+0.006**
- Both are long strategies, so monthly co-movement is expected. The L4 decision is unaffected by this pair.

### L5-S1 finding (verdict: **ARTIFACT**)

- Full Pearson +0.504 / clean Pearson **+0.193** / rolling-12 median **-0.044**.
- Both L5 (breakout long) and S1 (night momentum) are momentum-flavored; modest persistent overlap is plausible.

### L1-S1 hedge (verdict: **ARTIFACT**)

- Bear-regime correlation was -0.129; full-sample Pearson here **+0.177**, clean **+0.075**.
- Rolling-12 median **+0.132**, range `[-0.381, +0.623]`.
- **Caution**: the hedge depends on outlier months; do not over-rely on it for risk budgeting.

### Bottom line for L4 keep-or-cut

- The L2-L4 +0.614 Pearson is an **ARTIFACT** of a handful of joint fat-tail months. Spearman -0.174 is closer to the truth.
- **Recommendation**: do NOT cut L4 on correlation grounds alone. The diversification penalty Pearson signaled is overstated.
- The L4 decision should pivot back to standalone-merit criteria (PF, MDD, sample size, WFE) rather than the inflated Pearson.

**Action**: Recompute the portfolio correlation matrix using either Spearman or outlier-trimmed Pearson before making cut decisions.
