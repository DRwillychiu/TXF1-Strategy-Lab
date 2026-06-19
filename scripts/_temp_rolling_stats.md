# Rolling-Window Stability Analysis — TXF1 Strategy Portfolio

Generated: 2026-06-19  
Source: `scripts/_temp_portfolio_pnl.json` (per-strategy daily PnL)

## 1. Methodology

**Data shape.** Each strategy's PnL is supplied as a sparse mapping of trade-day → daily PnL (TWD). Non-trade days are filled with 0 to build a continuous calendar-day series spanning each strategy's first to last trade.

**Rolling windows.** Three window lengths are used: **180**, **360**, and **720 calendar days**, stepped daily.
A strategy must have at least `window` calendar days of history to produce a window of that length.

**Profit Factor (PF).** Within each window:

```
PF = sum(positive daily PnL) / |sum(negative daily PnL)|
```

If the window has no losing days, PF is reported as `inf` (excluded from variance stats but kept for fail-rate). If the window has no trades at all, PF is `nan`.

**Annualized Sharpe.** Computed on trade-day-only returns inside the window (zero-PnL days excluded, otherwise std collapses to a sub-quoted floor):

```
Sharpe = (mean(daily_PnL) / std(daily_PnL, ddof=1)) * sqrt(252)
```

Requires at least 2 trade days inside the window; otherwise `nan`.

**Instability scores** (from the 360-day series):

- `PF instability = std(rolling_360_PF) / mean(rolling_360_PF)`  (finite values only)
- `Sharpe instability = std(rolling_360_Sharpe) / |mean(rolling_360_Sharpe)|`

**Failure-window rate.** Share of rolling 360-day windows whose PF is below 1.0 (i.e. the strategy lost money over a full calendar year of trailing performance).

**Flagging rules** (per user spec):

- Failure-window rate (360d) > 30%  → **unstable**
- PF instability > 0.5             → **unstable**
- Any 720-day window with PF < 1.0 → **severe overfitting risk**

**Verdict.** `STABLE` = no flags. `UNSTABLE` = any 720d PF<1 OR two-or-more flags. `WATCH` = single non-720 flag.

> **Caveat on sparse strategies.** L2 (78 trade days over 5.3 yrs) and L4 (76 trade days over 5.2 yrs) trade so infrequently that many short windows contain zero or one trade, producing PF=0/nan/inf and extreme Sharpe variance. Their 720-day numbers are the only ones with sufficient sample density to take seriously.

## 2. Per-strategy rolling-window table

PF and Sharpe — mean | std | min | max — at each window length. `n` = number of rolling windows.

### L1  (429 trade days, 2019-12-18 → 2026-06-03, 2360 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 2181 | 1.388 | 0.574 | 0.000 | inf | 1.309 | 3.977 | -17.681 | 43.686 | 24.9% |
| 360d | 2001 | 1.318 | 0.329 | 0.425 | 2.253 | 1.294 | 1.511 | -5.997 | 4.382 | 13.5% |
| 720d | 1641 | 1.305 | 0.157 | 0.886 | 1.653 | 1.412 | 0.662 | -0.687 | 2.704 | 6.0% |

### L2  (78 trade days, 2020-02-10 → 2025-06-03, 1941 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 1762 | 3.884 | 7.055 | 0.000 | inf | -7.425 | 31.556 | -278.145 | 15.413 | 30.1% |
| 360d | 1582 | 2.826 | 3.468 | 0.000 | 17.628 | -3.183 | 15.882 | -59.205 | 11.071 | 30.2% |
| 720d | 1222 | 2.230 | 1.083 | 0.684 | 6.538 | 3.121 | 1.498 | -2.443 | 6.200 | 5.9% |

### L3  (335 trade days, 2020-01-07 → 2026-05-29, 2335 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 2156 | 1.203 | 0.569 | 0.414 | 3.541 | 0.609 | 3.101 | -6.249 | 9.591 | 39.8% |
| 360d | 1976 | 1.091 | 0.289 | 0.536 | 2.115 | 0.359 | 1.839 | -4.330 | 5.452 | 39.0% |
| 720d | 1616 | 1.051 | 0.117 | 0.797 | 1.380 | 0.302 | 0.771 | -1.551 | 2.304 | 36.8% |

### L4  (76 trade days, 2020-02-22 → 2025-05-07, 1902 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 1723 | 1.109 | 1.011 | 0.000 | inf | 0.477 | 10.154 | -32.071 | 29.500 | 42.1% |
| 360d | 1543 | 1.047 | 0.681 | 0.000 | inf | -1.090 | 5.148 | -32.071 | 7.039 | 55.2% |
| 720d | 1183 | 0.952 | 0.306 | 0.439 | 2.294 | -0.611 | 1.496 | -4.965 | 3.517 | 76.0% |

### L5  (135 trade days, 2021-09-16 → 2026-06-05, 1724 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 1545 | 1.593 | 0.931 | 0.000 | 6.530 | 2.110 | 2.795 | -3.535 | 10.081 | 21.9% |
| 360d | 1365 | 1.464 | 0.537 | 0.000 | 3.366 | 2.069 | 1.779 | -2.295 | 6.226 | 13.0% |
| 720d | 1005 | 1.447 | 0.277 | 1.084 | 2.397 | 2.094 | 0.894 | 0.512 | 4.481 | 0.0% |

### S1  (594 trade days, 2020-01-03 → 2026-06-03, 2344 calendar days)

| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |
|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|
| 180d | 2165 | 1.508 | 1.215 | 0.367 | 10.649 | 1.304 | 3.126 | -5.556 | 10.806 | 39.7% |
| 360d | 1985 | 1.325 | 0.492 | 0.574 | 2.668 | 1.173 | 2.142 | -3.140 | 5.104 | 36.3% |
| 720d | 1625 | 1.276 | 0.286 | 0.834 | 1.985 | 1.185 | 1.168 | -1.079 | 3.669 | 18.8% |

## 3. Instability scores (ranked, 360-day basis)

Lower = more consistent. PF instability is the dispersion of rolling-360 PF normalized by its own mean. Sharpe instability uses `|mean|` so a small Sharpe magnifies the score (correctly — small-Sharpe systems with high variance are not robust).

| Rank | Strategy | PF instability (360d) | Sharpe instability (360d) |
|------|----------|-----------------------|---------------------------|
| 1 | L1 | 0.250 | 1.168 |
| 2 | L3 | 0.265 | 5.118 |
| 3 | L5 | 0.367 | 0.860 |
| 4 | S1 | 0.372 | 1.827 |
| 5 | L4 | 0.651 (flag) | 4.721 |
| 6 | L2 | 1.227 (flag) | 4.990 |

## 4. Failure-window rate (ranked, 360-day basis)

Share of rolling 360-day windows with PF < 1.0. >30% triggers the unstable flag.

| Rank | Strategy | Fail-rate 360d (PF<1) | Fail-rate 180d | Fail-rate 720d | Worst 360d PF | Worst 720d PF (date) |
|------|----------|-----------------------|----------------|----------------|---------------|----------------------|
| 1 | L5 | 13.0% | 21.9% | 0.0% | 0.000 | 1.084 (2023-09-05) |
| 2 | L1 | 13.5% | 24.9% | 6.0% | 0.425 | 0.886 (2023-04-23) |
| 3 | L2 | 30.2% (flag) | 30.1% | 5.9% | 0.000 | 0.684 (2024-06-24) |
| 4 | S1 | 36.3% (flag) | 39.7% | 18.8% | 0.574 | 0.834 (2024-03-06) |
| 5 | L3 | 39.0% (flag) | 39.8% | 36.8% | 0.536 | 0.797 (2025-07-14) |
| 6 | L4 | 55.2% (flag) | 42.1% | 76.0% | 0.000 | 0.439 (2022-03-09) |

## 5. Verdict per strategy

| Strategy | Verdict | Flags triggered | Notes |
|----------|---------|-----------------|-------|
| L1 | **UNSTABLE** | 720d_pf_below_1 | 720d PF stays >0.886 — the dip is shallow and brief (early-2023 chop). Otherwise solid: PF instab 0.25, 360d fail-rate only 13.5%. The 720d PF<1 flag is the only thing keeping it out of STABLE. Realistically: **WATCH**. |
| L2 | **UNSTABLE** | failure_rate_high, pf_instability_high, 720d_pf_below_1 | Sparse trader (78 trades in 5.3 yrs) and the numbers reflect it — PF instability 1.23, Sharpe instab 4.99, 720d worst PF 0.684. With this trade density, conclusions are weak but every reliable metric is bad. |
| L3 | **UNSTABLE** | failure_rate_high, 720d_pf_below_1 | Persistent edge-of-breakeven behaviour: 720d fail-rate 36.8%, 360d mean PF only 1.09. Even the smoothest window length shows the strategy losing money in over a third of trailing-2yr periods. Marginal economics. |
| L4 | **UNSTABLE** | failure_rate_high, pf_instability_high, 720d_pf_below_1 | Worst of the set. 360d fail-rate 55%, 720d fail-rate 76%, 720d mean PF 0.95 (< 1!), worst 720d PF 0.439. Two-year windows mostly lose money. Strong candidate for retirement. |
| L5 | **STABLE** | none | Cleanest by every measure: 360d fail-rate 13%, all 1005 720d windows PF >= 1.084, PF instab 0.37, Sharpe instab 0.86, Sharpe mean ~2.1. Only ~4.7 yrs of history is the lone caveat. |
| S1 | **UNSTABLE** | failure_rate_high, 720d_pf_below_1 | Largest sample (594 trades), but 360d fail-rate 36.3% and 720d PF dropped to 0.834 in early-2024. Edge exists in aggregate (PF mean 1.33) but has multi-quarter holes. |

### Summary ranking (best → worst stability)

1. **L5** — STABLE.  Lowest fail-rate, no 720d failure, modest Sharpe instab.
2. **L1** — UNSTABLE by the letter of the rule (one shallow 720d dip to 0.886), but otherwise the second-best system.
3. **S1** — UNSTABLE.  Two flags. Edge exists, but the failure-window rate is too high for full size.
4. **L3** — UNSTABLE.  Marginal long-run PF, fails in >1/3 of windows at every length.
5. **L2** — UNSTABLE.  Three flags. Sparse trader, very high variance.
6. **L4** — UNSTABLE.  Three flags. 720d PF<1 on average — the system has *negative* expectancy across most two-year periods.

---

*Generated by `scripts/_temp_rolling_calc.py` + `scripts/_temp_rolling_report.py`.*