# Portfolio Sharpe Analysis (Multi-Weight)

- Source data: `C:\Users\User\Desktop\TXF1-Strategy-Lab\scripts\_temp_portfolio_pnl.json`
- Strategies analyzed: L1, L2, L3, L4, L5, S1  (n = 6)
- Time grid: 79 months from 2019-12 to 2026-06
- Annualization: monthly stats x sqrt(12)
- Missing months filled with zero PnL (strategy idle)

## 1. Individual Strategy Sharpe (Annual)

| Strategy | Mean Monthly NTD | Std Monthly NTD | Annual Sharpe | Total PnL | Active Months |
|---|---:|---:|---:|---:|---:|
| L1 | 28,759 | 106,425 | 0.936 | 2,272,000 | 69 |
| L2 | 18,162 | 78,857 | 0.798 | 1,434,800 | 29 |
| L3 | 8,251 | 52,389 | 0.546 | 651,800 | 71 |
| L4 | 3,020 | 37,041 | 0.282 | 238,600 | 28 |
| L5 | 20,347 | 91,080 | 0.774 | 1,607,400 | 37 |
| S1 | 18,638 | 69,002 | 0.936 | 1,472,400 | 77 |

## 2. Sum of Individual Sharpe

- Sum of individual annual Sharpe: **4.272**
- Note: this is *not* the achievable portfolio Sharpe — it's a benchmark for diversification analysis.

## 3. Equal-Weight Portfolio (1/6 each)

- Mean monthly: **16,196 NTD**
- Std monthly: **42,217 NTD**
- Annual Sharpe: **1.329**

## 4. Optimized-Weight Portfolio (Max Sharpe, grid 0.1 step)

- Annual Sharpe: **1.410**
- Mean monthly: 17,574 NTD
- Std monthly: 43,189 NTD
- Weights:
  - L1: 20%
  - L2: 30%
  - L3: 30%
  - L4: 0%
  - L5: 10%
  - S1: 10%

## 5. Min-Variance Portfolio (grid 0.1 step)

- Annual Sharpe: **0.754**
- Mean monthly: 6,322 NTD
- Std monthly: 29,031 NTD
- Monthly variance: 842,822,693
- Weights:
  - L1: 0%
  - L2: 0%
  - L3: 30%
  - L4: 60%
  - L5: 10%
  - S1: 0%

## 5b. Naive Risk-Parity Portfolio (w_i proportional to 1/std_i)

- Annual Sharpe: **1.263**
- Mean monthly: 13,169 NTD
- Std monthly: 36,130 NTD
- Weights:
  - L1: 10.0%
  - L2: 13.5%
  - L3: 20.4%
  - L4: 28.8%
  - L5: 11.7%
  - S1: 15.5%

## 6. Diversification Benefit

| Metric | Value |
|---|---:|
| Sum of individual annual Sharpe | 4.272 |
| Equal-weight portfolio Sharpe | 1.329 |
| Max-Sharpe portfolio Sharpe | 1.410 |
| Min-Variance portfolio Sharpe | 0.754 |
| Risk-parity portfolio Sharpe | 1.263 |
| Diversification ratio (EW / Sum-of-Sharpe) | 0.311 |
| Diversification ratio (MaxSharpe / Sum-of-Sharpe) | 0.330 |

**Interpretation:** Because individual Sharpe values do *not* add (Sharpe scales with mean/sigma and sigma is sub-additive when correlations < 1), a diversification ratio >> 1 indicates the portfolio is materially more efficient than the average of its parts.

### 6b. Correlation Matrix (monthly PnL)

| | L1 | L2 | L3 | L4 | L5 | S1 |
|---|---:|---:|---:|---:|---:|---:|
| L1 | 1.00 | -0.01 | 0.05 | -0.01 | 0.52 | 0.18 |
| L2 | -0.01 | 1.00 | -0.03 | 0.61 | -0.06 | 0.34 |
| L3 | 0.05 | -0.03 | 1.00 | 0.02 | 0.02 | 0.29 |
| L4 | -0.01 | 0.61 | 0.02 | 1.00 | -0.01 | 0.29 |
| L5 | 0.52 | -0.06 | 0.02 | -0.01 | 1.00 | 0.50 |
| S1 | 0.18 | 0.34 | 0.29 | 0.29 | 0.50 | 1.00 |

## 7. Drop-One Marginal Contribution (vs. Equal-Weight)

For each strategy, recompute equal-weight Sharpe on the remaining 5. The drop in Sharpe = that strategy's marginal value.

| Dropped Strategy | Sharpe Without | Marginal Value (EW - Without) | Verdict |
|---|---:|---:|---|
| L1 | 1.189 | +0.140 | ESSENTIAL (large drop without it) |
| L2 | 1.201 | +0.128 | ESSENTIAL (large drop without it) |
| L3 | 1.272 | +0.057 | Valuable |
| L4 | 1.357 | -0.028 | Disposable (portfolio improves without it) |
| L5 | 1.330 | -0.001 | Roughly neutral |
| S1 | 1.309 | +0.020 | Valuable |

Ranked by marginal value (highest = most essential):
- L1: +0.140
- L2: +0.128
- L3: +0.057
- S1: +0.020
- L5: -0.001
- L4: -0.028

## 8. Recommended Weights

### Three plausible allocations

| Strategy | Max-Sharpe | Min-Variance | Risk-Parity | Equal-Weight |
|---|---:|---:|---:|---:|
| L1 | 20% | 0% | 10.0% | 16.7% |
| L2 | 30% | 0% | 13.5% | 16.7% |
| L3 | 30% | 30% | 20.4% | 16.7% |
| L4 | 0% | 60% | 28.8% | 16.7% |
| L5 | 10% | 10% | 11.7% | 16.7% |
| S1 | 10% | 0% | 15.5% | 16.7% |
| **Sharpe** | **1.410** | **0.754** | **1.263** | **1.329** |

### Discussion

- **Essential strategies** (dropping them hurts the portfolio significantly): L1, L2
- **Disposable strategies** (portfolio Sharpe actually improves without them): L4

**Recommended live allocation (operator's judgment, blending Max-Sharpe with diversification floor):**

- For **maximum risk-adjusted return** under this dataset: use the **Max-Sharpe** weights above.
- For **lower drawdown / steadier equity curve**: use **Min-Variance** weights.
- For a **balanced, robust** allocation that doesn't depend on one strategy's edge holding up: use **Risk-Parity** weights — it gives each strategy similar risk contribution and is less prone to overfitting.

### Flagged high-correlation pairs (|rho| > 0.30)

- L1 vs L5: rho = +0.52
- L2 vs L4: rho = +0.61
- L2 vs S1: rho = +0.34
- L5 vs S1: rho = +0.50
