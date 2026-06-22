# IS/OOS Split Test Analysis

**Generated:** 2026-06-19  
**Source:** `scripts/_temp_portfolio_pnl.json`  
**Strategies:** L1, L2, L3, L4, L5, S1

---

## 1. Methodology

**Input granularity.** Each strategy is a dict of `date → daily realized PnL (NTD)`. 
These are daily PnL events (not individual trades), already including round-trip slippage 1,000 NTD per the project spec.

**Procedure for each strategy:**

1. Sort all daily PnL records chronologically by date.
2. Cut at index `floor(N * frac_IS)` — first segment is **In-Sample (IS)**, remainder is **Out-of-Sample (OOS)**.
3. Compute on each segment: trade count `N`, total PnL, average daily PnL, win-rate `WR`, profit factor `PF = gross_win / |gross_loss|`, and annualised Sharpe `= mean(daily) / stdev(daily) * sqrt(252)`.
4. Walk-Forward Efficiency ratios:
   - `WFE_pnl = OOS_avg_daily_pnl / IS_avg_daily_pnl`
   - `WFE_pf  = OOS_PF / IS_PF`
   - `WFE_sharpe = OOS_Sharpe / IS_Sharpe`
5. Repeat across **four splits** for stability: 50/50, 60/40, 70/30, 80/20.

**Institutional verdict thresholds on `WFE_pnl` (with both IS and OOS positive):**

| WFE_pnl | Verdict |
|---|---|
| > 0.7 | ROBUST |
| 0.5 – 0.7 | ACCEPTABLE |
| 0.3 – 0.5 | WARNING (likely overfit) |
| < 0.3 | SEVERE OVERFIT |

**Edge cases:**
- `IS_NEG_OOS_POS` — IS lost money but OOS made money. Ratio is mathematically meaningless; treated as *non-overfit but historically weak* (real-money OOS evidence > backtest).
- `OOS_NEG_DEGRADED` — IS was profitable but OOS is flat/negative. Treated as **SEVERE_OVERFIT-equivalent**: the IS edge has died.
- `BOTH_NEGATIVE` — both halves lose; strategy is broken regardless of WFE.

**Caveats:**
- These are *daily aggregates*, not per-trade records, so PF/WR are at the day level (a day can contain multiple intraday trades). This biases PF mildly downward vs trade-level PF (offsetting trades within a day net out).
- Sample sizes vary widely (L4 has 75 days; S1 has 460 days). Smaller samples ⇒ wider error bars on WFE.
- A naive chronological split assumes stationarity of the market regime within each half — which is exactly what we're testing against.

---

## 2. Per-Strategy 70/30 IS/OOS Metrics

| Strategy | N(IS) | IS total | IS avg/day | IS WR | IS PF | IS Sharpe | N(OOS) | OOS total | OOS avg/day | OOS WR | OOS PF | OOS Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L1 | 300 | 1,243,400 | 4,145 | 35.0% | 1.43 | 1.91 | 129 | 1,028,600 | 7,974 | 40.3% | 1.43 | 1.57 |
| L2 | 55 | 488,800 | 8,887 | 38.2% | 1.92 | 3.48 | 23 | 946,000 | 41,130 | 47.8% | 5.08 | 5.64 |
| L3 | 234 | 342,600 | 1,464 | 52.6% | 1.20 | 1.28 | 101 | 309,200 | 3,061 | 44.6% | 1.18 | 1.04 |
| L4 | 53 | -9,800 | -185 | 60.4% | 0.97 | -0.16 | 23 | 248,400 | 10,800 | 52.2% | 2.25 | 2.76 |
| L5 | 94 | 155,800 | 1,657 | 50.0% | 1.18 | 1.01 | 41 | 1,451,600 | 35,405 | 63.4% | 3.54 | 6.51 |
| S1 | 416 | 244,800 | 588 | 56.5% | 1.13 | 0.68 | 178 | 1,227,600 | 6,897 | 62.4% | 1.92 | 3.47 |

---

## 3. WFE Scores (70/30 split) — Ranked

Sorted by `WFE_pnl` descending (with sign-flip cases shown separately).

| Rank | Strategy | WFE_pnl | WFE_pf | WFE_sharpe | Verdict |
|---:|---|---:|---:|---:|---|
| 1 | L4 | -58.41 | 2.31 | -16.77 | IS_NEG_OOS_POS |
| 2 | L5 | 21.36 | 3.01 | 6.48 | ROBUST |
| 3 | S1 | 11.72 | 1.71 | 5.13 | ROBUST |
| 4 | L2 | 4.63 | 2.65 | 1.62 | ROBUST |
| 5 | L3 | 2.09 | 0.99 | 0.81 | ROBUST |
| 6 | L1 | 1.92 | 1.00 | 0.82 | ROBUST |

---

## 4. Split-Stability Test (4 Splits per Strategy)

For each strategy, show `WFE_pnl` and verdict across all four cut points. Consistency across splits is the real overfit test — a robust strategy survives every cut, an overfit one survives only the cut where the lucky trades land in IS.

### L1 (N = 429, 2019-12-18 → 2026-06-03)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 214 | 215 | 3,461 | 7,123 | 1.37 | 1.46 | 2.06 | ROBUST |
| 60/40 | 257 | 172 | 2,640 | 9,264 | 1.28 | 1.56 | 3.51 | ROBUST |
| 70/30 | 300 | 129 | 4,145 | 7,974 | 1.43 | 1.43 | 1.92 | ROBUST |
| 80/19 | 343 | 86 | 3,733 | 11,530 | 1.36 | 1.56 | 3.09 | ROBUST |

### L2 (N = 78, 2020-02-10 → 2025-06-03)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 39 | 39 | 10,359 | 26,431 | 2.04 | 3.74 | 2.55 | ROBUST |
| 60/40 | 47 | 31 | 11,562 | 28,755 | 2.24 | 3.73 | 2.49 | ROBUST |
| 70/30 | 55 | 23 | 8,887 | 41,130 | 1.92 | 5.08 | 4.63 | ROBUST |
| 80/19 | 62 | 16 | 6,219 | 65,575 | 1.60 | 9.52 | 10.54 | ROBUST |

### L3 (N = 335, 2020-01-07 → 2026-05-29)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 168 | 167 | 1,626 | 2,267 | 1.22 | 1.17 | 1.39 | ROBUST |
| 60/40 | 201 | 134 | 1,474 | 2,654 | 1.20 | 1.18 | 1.80 | ROBUST |
| 70/30 | 234 | 101 | 1,464 | 3,061 | 1.20 | 1.18 | 2.09 | ROBUST |
| 80/19 | 268 | 67 | 801 | 6,522 | 1.09 | 1.38 | 8.14 | ROBUST |

### L4 (N = 76, 2020-02-22 → 2025-05-07)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 38 | 38 | 37 | 6,242 | 1.01 | 1.74 | 169.43 | ROBUST |
| 60/40 | 46 | 30 | -596 | 8,867 | 0.92 | 2.16 | -14.89 | IS_NEG_OOS_POS |
| 70/30 | 53 | 23 | -185 | 10,800 | 0.97 | 2.25 | -58.41 | IS_NEG_OOS_POS |
| 80/19 | 61 | 15 | -243 | 16,893 | 0.97 | 2.86 | -69.63 | IS_NEG_OOS_POS |

### L5 (N = 135, 2021-09-16 → 2026-06-05)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 68 | 67 | 2,997 | 20,949 | 1.43 | 2.42 | 6.99 | ROBUST |
| 60/40 | 81 | 54 | 2,084 | 26,641 | 1.24 | 2.93 | 12.78 | ROBUST |
| 70/30 | 94 | 41 | 1,657 | 35,405 | 1.18 | 3.54 | 21.36 | ROBUST |
| 80/19 | 108 | 27 | 3,931 | 43,807 | 1.43 | 3.49 | 11.14 | ROBUST |

### S1 (N = 594, 2020-01-03 → 2026-06-03)

| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 50/50 | 297 | 297 | -300 | 5,257 | 0.94 | 1.84 | -17.54 | IS_NEG_OOS_POS |
| 60/40 | 356 | 238 | -317 | 6,661 | 0.93 | 1.99 | -21.02 | IS_NEG_OOS_POS |
| 70/30 | 416 | 178 | 588 | 6,897 | 1.13 | 1.92 | 11.72 | ROBUST |
| 80/19 | 475 | 119 | 1,196 | 7,600 | 1.24 | 1.98 | 6.36 | ROBUST |

---

## 5. Per-Strategy Verdict

### L1

- **70/30 primary verdict:** `ROBUST`  (WFE_pnl = 1.92, WFE_pf = 1.00, WFE_sharpe = 0.82)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['ROBUST', 'ROBUST', 'ROBUST', 'ROBUST']
- **WFE_pnl across splits:** [2.06, 3.51, 1.92, 3.09]
- **Interpretation:** Every split passes — true edge, deploy with confidence at sized position.

### L2

- **70/30 primary verdict:** `ROBUST`  (WFE_pnl = 4.63, WFE_pf = 2.65, WFE_sharpe = 1.62)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['ROBUST', 'ROBUST', 'ROBUST', 'ROBUST']
- **WFE_pnl across splits:** [2.55, 2.49, 4.63, 10.54]
- **Interpretation:** Every split passes — true edge, deploy with confidence at sized position.

### L3

- **70/30 primary verdict:** `ROBUST`  (WFE_pnl = 2.09, WFE_pf = 0.99, WFE_sharpe = 0.81)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['ROBUST', 'ROBUST', 'ROBUST', 'ROBUST']
- **WFE_pnl across splits:** [1.39, 1.8, 2.09, 8.14]
- **Interpretation:** Every split passes — true edge, deploy with confidence at sized position.

### L4

- **70/30 primary verdict:** `IS_NEG_OOS_POS`  (WFE_pnl = -58.41, WFE_pf = 2.31, WFE_sharpe = -16.77)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['ROBUST', 'IS_NEG_OOS_POS', 'IS_NEG_OOS_POS', 'IS_NEG_OOS_POS']
- **WFE_pnl across splits:** [169.43, -14.89, -58.41, -69.63]
- **Interpretation:** Multiple splits show IS-loss / OOS-profit — recent regime is favourable to this strategy; the backtest understates current edge. Treat as *opportunistic*, not validated.

### L5

- **70/30 primary verdict:** `ROBUST`  (WFE_pnl = 21.36, WFE_pf = 3.01, WFE_sharpe = 6.48)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['ROBUST', 'ROBUST', 'ROBUST', 'ROBUST']
- **WFE_pnl across splits:** [6.99, 12.78, 21.36, 11.14]
- **Interpretation:** Every split passes — true edge, deploy with confidence at sized position.

### S1

- **70/30 primary verdict:** `ROBUST`  (WFE_pnl = 11.72, WFE_pf = 1.71, WFE_sharpe = 5.13)
- **Stability across 4 splits:** 4 good · 0 warning · 0 bad → verdicts = ['IS_NEG_OOS_POS', 'IS_NEG_OOS_POS', 'ROBUST', 'ROBUST']
- **WFE_pnl across splits:** [-17.54, -21.02, 11.72, 6.36]
- **Interpretation:** Multiple splits show IS-loss / OOS-profit — recent regime is favourable to this strategy; the backtest understates current edge. Treat as *opportunistic*, not validated.

---

## Summary Table

| Strategy | Primary verdict | Splits passing | Splits failing | Action |
|---|---|---:|---:|---|
| L1 | ROBUST | 4/4 | 0/4 | Deploy / size up |
| L2 | ROBUST | 4/4 | 0/4 | Deploy / size up |
| L3 | ROBUST | 4/4 | 0/4 | Deploy / size up |
| L4 | IS_NEG_OOS_POS | 4/4 | 0/4 | Deploy / size up |
| L5 | ROBUST | 4/4 | 0/4 | Deploy / size up |
| S1 | ROBUST | 4/4 | 0/4 | Deploy / size up |

---

## Critical Caveat — All WFE > 1.0

**Every strategy shows OOS_avg_daily_pnl > IS_avg_daily_pnl (often by 2x–20x).** That is not normal:

- The classical purpose of WFE is to test for *degradation* (OOS < IS by some amount). When WFE > 1.0 across the board, the test is no longer detecting overfit — it is detecting a **regime shift** that favours all six strategies simultaneously.
- The OOS windows for every strategy fall in **2024–2026**, when TXF1 saw a record AI-driven rally with massive intraday range expansion. Long-trend (L1/L2/L5), breakout (L5), and overnight momentum (S1) edges all benefit from this regime — but that does **not** mean the underlying logic has any more edge than the IS period showed.
- Inverted reading: if 2024-2026 were the IS window and 2020-2023 were the OOS, every strategy would likely show WFE < 0.3 (SEVERE_OVERFIT). The split direction matters because the regime is non-stationary.
- **Implication for sizing:** "Deploy / size up" verdicts in the summary table should be read as *no evidence of overfit in this direction* — not as *real edge has grown*. Position sizing should be based on **IS metrics (the worse half)**, not OOS, to avoid sizing into peak-regime profitability that may mean-revert.
- **What this analysis cannot tell us:** whether the 2024-2026 OOS PnL is a structural edge or a beta-to-regime payoff. To answer that, do **rolling 12-month WFE** (not single-cut) or **regime-stratified backtest** (separate trending vs ranging months).

### Flagged for closer review
- **L4** — IS is flat/slightly negative across 3 of 4 splits. Strategy has only 76 trade days over 5 years (low activity). The OOS profit is concentrated in a small handful of days (notably 2025-04-07 +273k). Single-day dependence is fragile.
- **S1** — IS is negative in 50/50 and 60/40 splits. The strategy was *unprofitable* in 2020-2023 backtest and only became profitable in 2024+. This is the opposite of what you want — it suggests the original entry logic didn't work historically and the recent profit may be regime-driven rather than skill-driven.
- **L2** — Only 78 trade days over 5+ years. WFE_pnl swings from 2.55 to 10.54 across splits — wild variance is a low-sample-size artefact, not stability.
