# Overfit Detection Report

Statistical overfit / robustness tests on per-strategy daily PnL series.
Source: `_temp_portfolio_pnl.json`  -  Strategies: L1, L2, L3, L4, L5, S1

## 1. Methodology

**Bootstrap robustness (1000 iterations, seed=42)**
- Each strategy's daily PnL series is resampled with replacement 1000 times.
- For each resample, the total PnL is computed.
- `Robustness Score` = fraction of bootstrap resamples whose total PnL > 0.
- `p5` = 5th percentile of bootstrap total PnL (worst-case lucky).
- If `p5 < 0`, the observed track record could plausibly have been a losing one given random reordering of trades.

**Probabilistic Sharpe Ratio (simplified)**
- `Sharpe = mean(daily PnL) / stdev(daily PnL)` (raw, not annualised, no risk-free rate).
- `PSR ~= Phi(Sharpe * sqrt(N-1))` where `Phi` is standard normal CDF and N = number of trade days.
- This is a coarse estimate of P(true Sharpe > 0).
- Threshold: `PSR < 0.95` = not statistically significant at 95% confidence.

**Streak analysis**
- `max_loss_streak` = longest run of consecutive losing days.
- `loss_streak_vs_wins_ratio = max_loss_streak / total winning days`.
- Threshold: ratio > 0.5 = high tail risk (one bad run could wipe out most winners).

**Profit concentration (Gini)**
- Gini computed on the distribution of positive-PnL days only.
- 0 = profits evenly distributed; 1 = one trade holds all profit.
- Threshold: Gini > 0.6 = lottery-dependency (a few outliers carry the strategy).
- Also reported: `top10_share` = % of total positive PnL contributed by top-10% winning days.

**Combined overfit-risk score** (heuristic, lower = better)
- Penalties stack from: (0.95 - robustness), (0.95 - PSR)*0.3, max(0, Gini-0.6), max(0, ratio-0.5)*5, max(0, top10-0.5)*5.
- Verdict bands: `< 1.0 ROBUST`, `1.0-3.0 WATCH`, `>= 3.0 OVERFIT_RISK`.

## 2. Bootstrap Robustness Ranked

| Rank | Strategy | N days | Total PnL | Bootstrap p5 | Bootstrap p50 | Bootstrap p95 | Robustness |
|---:|:---|---:|---:|---:|---:|---:|---:|
| 1 | L5 | 135 | +1,607,400 | +699,000 | +1,600,000 | +2,754,600 | 100.0% |
| 2 | S1 | 594 | +1,472,400 | +622,800 | +1,460,600 | +2,386,400 | 100.0% |
| 3 | L2 | 78 | +1,434,800 | +469,000 | +1,379,200 | +2,564,400 | 99.8% |
| 4 | L1 | 429 | +2,272,000 | +559,600 | +2,233,800 | +4,216,800 | 99.1% |
| 5 | L3 | 335 | +651,800 | -238,400 | +636,200 | +1,568,800 | 88.6% |
| 6 | L4 | 76 | +238,600 | -234,400 | +210,800 | +837,600 | 76.5% |

Strategies with `p5 < 0` (could be lucky): **L3, L4**

## 3. Probabilistic Sharpe Ratio Ranked

| Rank | Strategy | N | Sharpe (per-day) | PSR | Significant (>= 0.95)? |
|---:|:---|---:|---:|---:|:---:|
| 1 | S1 | 594 | 0.1183 | 0.9980 | YES |
| 2 | L5 | 135 | 0.2204 | 0.9946 | YES |
| 3 | L2 | 78 | 0.2566 | 0.9878 | YES |
| 4 | L1 | 429 | 0.1007 | 0.9814 | YES |
| 5 | L3 | 335 | 0.0653 | 0.8837 | NO |
| 6 | L4 | 76 | 0.0853 | 0.7699 | NO |

PSR < 0.95 (not statistically significant): **L3, L4**

## 4. Streak Analysis Ranked

| Rank | Strategy | Wins | Losses | Max Win Streak | Max Loss Streak | LossStreak / Wins |
|---:|:---|---:|---:|---:|---:|---:|
| 1 | L2 | 32 | 46 | 5 | 6 | 18.8% |
| 2 | L1 | 157 | 272 | 6 | 15 | 9.6% |
| 3 | L4 | 44 | 32 | 7 | 4 | 9.1% |
| 4 | L5 | 73 | 61 | 7 | 5 | 6.8% |
| 5 | L3 | 168 | 167 | 6 | 7 | 4.2% |
| 6 | S1 | 346 | 248 | 12 | 8 | 2.3% |

No strategy exceeds the 50% loss-streak-to-wins ratio threshold.

## 5. Profit Concentration (Gini) Ranked

| Rank | Strategy | Gini (positive PnL) | Top-10% share | Lottery? |
|---:|:---|---:|---:|:---:|
| 1 | L4 | 0.619 | 52.6% | YES |
| 2 | L2 | 0.575 | 41.3% | NO |
| 3 | L5 | 0.532 | 38.9% | NO |
| 4 | S1 | 0.522 | 39.7% | NO |
| 5 | L1 | 0.470 | 36.8% | NO |
| 6 | L3 | 0.391 | 31.7% | NO |

Gini > 0.6 (lottery dependency): **L4**

## 6. Combined Overfit-Risk Score

| Rank | Strategy | Robustness | PSR | Gini | LossStreak/Wins | Top10% | Score | Verdict |
|---:|:---|---:|---:|---:|---:|---:|---:|:---:|
| 1 | L1 | 99.1% | 0.981 | 0.470 | 9.6% | 36.8% | 0.00 | ROBUST |
| 2 | L2 | 99.8% | 0.988 | 0.575 | 18.8% | 41.3% | 0.00 | ROBUST |
| 3 | L5 | 100.0% | 0.995 | 0.532 | 6.8% | 38.9% | 0.00 | ROBUST |
| 4 | S1 | 100.0% | 0.998 | 0.522 | 2.3% | 39.7% | 0.00 | ROBUST |
| 5 | L3 | 88.6% | 0.884 | 0.391 | 4.2% | 31.7% | 0.84 | ROBUST |
| 6 | L4 | 76.5% | 0.770 | 0.619 | 9.1% | 52.6% | 2.71 | WATCH |

## 7. Verdict Per Strategy

### L1 — **ROBUST** (score 0.00)
- Trades/days: **429** | Total PnL: **+2,272,000** | per-day mean: +5,296, sd: 52,595
- Bootstrap: robustness **99.1%**, p5 +559,600, p50 +2,233,800, p95 +4,216,800
- Sharpe(per-day): 0.1007 | PSR: **0.9814**
- Streaks: wins 157, losses 272, max win 6, max loss **15** (ratio 9.6%)
- Gini(positive PnL): **0.470** | Top-10% share: 36.8%
- Flags: none

### L2 — **ROBUST** (score 0.00)
- Trades/days: **78** | Total PnL: **+1,434,800** | per-day mean: +18,395, sd: 71,685
- Bootstrap: robustness **99.8%**, p5 +469,000, p50 +1,379,200, p95 +2,564,400
- Sharpe(per-day): 0.2566 | PSR: **0.9878**
- Streaks: wins 32, losses 46, max win 5, max loss **6** (ratio 18.8%)
- Gini(positive PnL): **0.575** | Top-10% share: 41.3%
- Flags: none

### L3 — **ROBUST** (score 0.84)
- Trades/days: **335** | Total PnL: **+651,800** | per-day mean: +1,946, sd: 29,783
- Bootstrap: robustness **88.6%**, p5 -238,400, p50 +636,200, p95 +1,568,800
- Sharpe(per-day): 0.0653 | PSR: **0.8837**
- Streaks: wins 168, losses 167, max win 6, max loss **7** (ratio 4.2%)
- Gini(positive PnL): **0.391** | Top-10% share: 31.7%
- Flags: bootstrap robustness 88.6% < 95%; bootstrap p5 < 0 (could be lucky); PSR 0.884 < 0.95

### L4 — **WATCH** (score 2.71)
- Trades/days: **76** | Total PnL: **+238,600** | per-day mean: +3,139, sd: 36,815
- Bootstrap: robustness **76.5%**, p5 -234,400, p50 +210,800, p95 +837,600
- Sharpe(per-day): 0.0853 | PSR: **0.7699**
- Streaks: wins 44, losses 32, max win 7, max loss **4** (ratio 9.1%)
- Gini(positive PnL): **0.619** | Top-10% share: 52.6%
- Flags: bootstrap robustness 76.5% < 95%; bootstrap p5 < 0 (could be lucky); PSR 0.770 < 0.95; Gini 0.619 > 0.6 (lottery-dependent); top-10% days carry 52.6% of positive PnL

### L5 — **ROBUST** (score 0.00)
- Trades/days: **135** | Total PnL: **+1,607,400** | per-day mean: +11,907, sd: 54,034
- Bootstrap: robustness **100.0%**, p5 +699,000, p50 +1,600,000, p95 +2,754,600
- Sharpe(per-day): 0.2204 | PSR: **0.9946**
- Streaks: wins 73, losses 61, max win 7, max loss **5** (ratio 6.8%)
- Gini(positive PnL): **0.532** | Top-10% share: 38.9%
- Flags: none

### S1 — **ROBUST** (score 0.00)
- Trades/days: **594** | Total PnL: **+1,472,400** | per-day mean: +2,479, sd: 20,952
- Bootstrap: robustness **100.0%**, p5 +622,800, p50 +1,460,600, p95 +2,386,400
- Sharpe(per-day): 0.1183 | PSR: **0.9980**
- Streaks: wins 346, losses 248, max win 12, max loss **8** (ratio 2.3%)
- Gini(positive PnL): **0.522** | Top-10% share: 39.7%
- Flags: none
