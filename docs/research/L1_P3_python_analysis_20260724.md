# L1 P3 Python Analysis Report — 2026-07-24

**Author**: Subagent analysis (Python: pandas 2.2.2 / numpy 1.26.4 / matplotlib 3.9.2)
**Purpose**: Evaluate the P3 stop-loss architecture proposal for L1 TrendLong (Layer 1 replacement + Layer 1b halving trigger) using empirical daily-bar data.
**Baseline**: L1 V3.0 T200 = Net 2,074K TWD, PF 1.348, MDD -493K (-21.7%), 508 trades, avg loss -94 pts. Current SL = `min(ATR20_45M × 1.5, Daily_ATR20 × 0.5)` frozen at entry.

## Data Verification

| Field | Value |
|---|---|
| CSV path | `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\backtest\twii_daily.csv` |
| Rows loaded | 1558 |
| Date range | 2020-01-02 to 2026-06-05 |
| Columns | Date, Open, High, Low, Close, Volume |
| Requested range | 2019-12-16 to 2026-07-23 |
| Actual coverage | Head short by 12 trading days; tail short by ~35 trading days |

**Caveat**: CSV covers slightly less than the requested L1 backtest window. Head (2019-12-16 to 2020-01-01) is a low-vol period pre-COVID — its absence is immaterial. Tail (2026-06-06 to 2026-07-23) is the most recent live regime — its absence weakens the "recent regime" slice (n=100 instead of ~130). Analysis proceeds; note this in interpretation.

**Proxy note**: TWII daily is used as a proxy for TXF1 daily (basis is small at index level, but recent divergence around ex-div dates can distort magnitudes ±100-300 pts). Daily bars are used as a proxy for the 45M timeframe in Task 3 — this is a first-order signal, not a definitive 45M answer.

---

## Task 1 — Correlation Study (T1.1)

### Full-period Pearson correlation with ATR20 (Daily, simple average of TR to match MC's `AvgTrueRange`)

| Formula | Definition | Corr vs ATR20 | Over 0.85? |
|---|---|---|---|
| L1_a | 10-day peak-to-trough = max(H) - min(L) over last 10 bars | **0.846** | NO (0.004 below) |
| L1_b | 10-day max daily range = max(H[k]-L[k]) | **0.882** | YES |
| L1_c | 10-day max close-to-close drawdown | **0.542** | NO |
| L1_d | 10-day P75 of daily ranges | **0.924** | YES |

### Rolling 60-day correlation (stability of relationship)

| Formula | Min | Median | Max |
|---|---|---|---|
| L1_a | -0.635 | 0.402 | 0.927 |
| L1_b | -0.677 | 0.554 | 0.985 |
| L1_c | -0.554 | 0.322 | 0.935 |
| L1_d | -0.500 | 0.627 | 0.973 |

**Interpretation**: even the "high correlation" formulas (L1_b, L1_d) show wide rolling swings — including negative correlation windows. The full-period Pearson number hides regime-dependent divergence. L1_c has the lowest median rolling correlation (0.322).

### Descriptive statistics (points)

| Stat | L1_a | L1_b | L1_c | L1_d | ATR20 |
|---|---|---|---|---|---|
| Mean | 1071 | 408 | 529 | 269 | 274 |
| Median | 837 | 324 | 357 | 223 | 225 |
| Std | 812 | 290 | 554 | 177 | 164 |
| P25 | 610 | 238 | 208 | 165 | 168 |
| P50 | 837 | 324 | 357 | 223 | 225 |
| P75 | 1219 | 446 | 652 | 298 | 317 |
| P95 | 2717 | 1111 | 1563 | 676 | 632 |

Histogram saved to: `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\docs\research\L1_P3_python_analysis_20260724_hist.png`

### Kill decision (Task 1)

**NOT all four formulas are ATR reskins.** L1_c is genuinely decoupled (r=0.542), and L1_a is borderline (0.846). L1_b (0.882) and L1_d (0.924) are effectively ATR-in-disguise for practical purposes.

- **Recommendation**: reject L1_b and L1_d as candidates (they add complexity without adding a new mechanism). Retain L1_a and L1_c for further evaluation.
- **Do not flag CRITICAL** — the concept of "recent-N-day pullback × ratio" is defensible with L1_c or L1_a, not with L1_b/L1_d.

---

## Task 2 — 4 Formula Behavior Comparison (T1.3)

### Regime medians (points)

| Regime | Bars | L1_a | L1_b | L1_c | L1_d | ATR20 | Close (median) |
|---|---|---|---|---|---|---|---|
| Low-vol 2020H2-2021H1 | 139 | 715 | 240 | 208 | 171 | 163 | 13,222 |
| High-vol 2022 Fed shock | 106 | 861 | 315 | 539 | 195 | 226 | 14,740 |
| Recent 2026 (partial) | 100 | 3,052 | 1,382 | 751 | 812 | 807 | 33,805 |

### Cross-regime coefficient of variation (std of medians / mean of medians)

| Formula | CV | Interpretation |
|---|---|---|
| L1_a | 0.693 | Moderately regime-sensitive |
| L1_b | 0.808 | Highest sensitivity (largest swing across regimes) |
| L1_c | **0.448** | Most stable — the only formula whose regime response is not dominated by index level |
| L1_d | 0.755 | High sensitivity, but nearly identical to ATR20's CV (which is ~0.75) — confirming L1_d ≈ ATR |

### Extreme values — what they capture

**L1_a (peak-to-trough) TOP 10**: 8 of top 10 come from 2026-04 to 2026-06 (recent regime, index at 36-46K). Extreme values here are index-level-scaled — mostly noise from being in a higher price regime, not a distinct signal.

**L1_b (max daily range) TOP 10**: 10 of 10 come from 2026-04-23 through 2026-05-07 (single event window — a 1,757 pt daily range on 2026-04-23). Highly event-clustered, less generalizable.

**L1_c (max C2C drawdown) TOP 10**: 8 of 10 from 2025-04 (April 2025 crash: Close 17,391 → captures 4,881 pt drawdown over the 10-day window). This is the **only** formula whose extremes reliably identify actual price collapse events rather than volatility regime. It captured the April 2025 tariff crash and the 2026-03 recent decline — both real dislocation events, not just high-vol backdrops.

**L1_d (P75 daily range) TOP 10**: 10 of 10 from 2026-04 to 2026-06. Same regime-clustering as L1_a/L1_b. Behaves as a smoothed ATR proxy.

### Ranking + recommendation

| Rank | Formula | Reason |
|---|---|---|
| **1st** | **L1_c** | Genuinely decoupled from ATR (r=0.542). Extremes capture actual drawdown events, not vol regime. Lowest cross-regime CV means its behavior is not dominated by index level scaling. Best represents the "recent pullback" concept the architecture wants. |
| 2nd | L1_a | Borderline correlated (r=0.846) but wider distribution than L1_d. Simpler formula (peak-trough) than L1_c. Could serve as a fallback if L1_c behaves poorly in backtest. |
| 3rd (reject) | L1_d | r=0.924 with ATR20, CV 0.755 nearly identical to ATR20's own regime pattern. It IS ATR, wearing a different label. |
| 4th (reject) | L1_b | r=0.882 with ATR20. Extreme events (top 10) all cluster in single week, indicating it captures point-in-time noise more than any recurring signal. |

**Recommended Layer 1 direction**: adopt L1_c (10-day max close-to-close drawdown) as the pullback magnitude. Formula: `L1_c[t] = max(Close[j] - Close[k])` for `j < k` with `k` in `[t-9, t]`. Multiply by user's target ratio to derive SL distance.

---

## Task 3 — Fire-Quality Proxy (T1b.5)

### Setup

- **Sample**: naive long entries on days where `Close > SMA(Close, 61)` AND yesterday was below → new "hold" started. Yields 33 discrete holds over 2020-2026.
- **Hold end**: 20 bars OR Close falls >3% below entry.
- **Trigger A**: 3 consecutive Close<Open with total Open[t-2] − Close[t] > 100 pts.
- **Trigger B**: Close < prev Open AND |Close − Open| > 2 × avg(|Close − Open|, last 20 bars).
- **Fire outcome (next 5 bars)**: `saved` if price rebounds > entry; `killed` if price drops >100 pts (proxy halved SL) below fire price; else `neutral`.

### Fire count

| Year | Fires |
|---|---|
| 2020 | 6 |
| 2021 | 28 |
| 2022 | 12 |
| 2023 | 9 |
| 2024 | 11 |
| 2025 | 15 |
| **Total** | **81** |

**Statistical significance check** (spec: ≥ 20 fires per architecture spec):
- Total fires 81 over 6.5 years → **passes** total threshold if interpreted as "≥20 total".
- Per-year: only 2021 exceeds 20 → **fails** if interpreted as "≥20 per year for stable statistics".
- **Conclusion**: fire count is on the marginal side of significance. Sample sizes are small enough that the pct rates below should be treated as directional, not definitive.

### Save vs Kill matrix (all fires, n=81)

| | Hold was WINNER | Hold was LOSER | Row total |
|---|---|---|---|
| Fire → **saved** (rebound > entry) | 36 | 5 | 41 (50.6%) |
| Fire → **killed** (down > 100 pts) | 2 | 31 | 33 (40.7%) |
| Fire → **neutral** (in between) | 0 | 7 | 7 (8.6%) |
| Column total | 38 (46.9%) | 43 (53.1%) | 81 |

**Read of the matrix**:
- **False-halving rate** = fires in a hold that was ultimately a winner = 46.9% (38/81).
- **True-halving rate** = fires in a hold that was ultimately a loser = 53.1% (43/81).
- **Saved rate** = 50.6% — half the fires would immediately regret themselves (price bounces back above entry within 5 bars).
- **Killed rate** = 40.7% — fire correctly identified continued weakness.
- **Saved-loser count** = 5 (fire fired in a loser hold but price still bounced short-term).
- **Killed-winner count** = 2 (fire fired in a winner hold and price briefly dipped 100+ pts).
- Ratio saved-loser / killed-winner = 2.50 (favorable in raw count).

Fire distance histogram saved to: `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\docs\research\L1_P3_python_analysis_20260724_fire_hist.png`

### Kill decision (Task 3)

Architecture spec V1b.5-6 rejection criteria:
- Fire → halved-SL-trigger rate < 40% → REJECT
- Fire → immediate-rebound rate > 40% → REJECT

Observed:
- Killed rate (halved-SL-trigger proxy): 40.7% — **JUST barely meets** the ≥40% threshold (0.7 pp margin).
- Saved rate (immediate-rebound proxy): 50.6% — **CLEARLY EXCEEDS** the ≤40% threshold (10.6 pp over).

**Verdict: REJECT Layer 1b** based on this Daily proxy.

**Reasoning in plain language**:
- Half the time Layer 1b fires, the price would have recovered without any tightening. Halving the SL in those cases increases whipsaw risk and gives back winners.
- The killed rate barely clears the 40% floor, meaning even in the other half, only 4 in 10 fires would have correctly justified the tightening.
- The 46.9% false-halving rate (fires in a hold that ended as a winner) is nearly 1:1 with the true-halving rate — Layer 1b as specified does not distinguish winners from losers with acceptable precision on daily data.
- Statistical significance is marginal — only 2021 has ≥ 20 fires. This weakens confidence but does not overturn the direction.

**Important**: this is a **Daily proxy**. The 45M timeframe carries 3-9× more bars per day and may yield more/finer triggers with different rebound windows. Because the proxy verdict is clearly negative (saved > 40% threshold by 10.6 pp), **the confidence to kill Layer 1b as currently specified is high**. Any resurrection attempt should first tighten Trigger A/B specifications (e.g., require higher body multiple, longer consecutive down-close count) and re-test.

---

## Overall Recommendations

### Layer 1 direction: PROCEED with L1_c

- **Adopt** L1_c (10-day max close-to-close drawdown) as the pullback magnitude in the SL formula. It is genuinely decoupled from ATR20 (r=0.542) and its extreme values track real dislocation events, not vol regime.
- **Reject** L1_b and L1_d as candidates — they are ATR proxies with r=0.88 and 0.92.
- **Keep L1_a** as a simpler fallback (r=0.846, borderline) in case L1_c behaves unexpectedly in the L1 backtest.
- **Next step**: run MC PowerLanguage backtest of L1 with SL = `L1_c × ratio` at 3 ratio candidates (e.g., 0.6 / 0.8 / 1.0) over the full 2020-2026 range. Compare Net / PF / MDD / avg loss to V3.0 T200 baseline.

### Layer 1b direction: DO NOT PROCEED as currently specified (proxy verdict)

- Daily proxy shows 50.6% of fires would trigger while price is about to rebound above entry. This exceeds the 40% rejection threshold by a clear margin.
- Killed rate barely clears the 40% floor (40.7%), so even the "correct" fires are borderline.
- **Recommendation**: shelve Layer 1b in current spec. If Willy still wants to pursue behavioral triggering:
  1. Redesign trigger stringency (higher body multiple for B, longer consecutive count for A, add trend-filter gate).
  2. Re-simulate on the actual 45M timeframe (not Daily proxy) to reject or confirm.
  3. Do not proceed to MC coding until the 45M sim shows saved rate < 40% AND killed rate > 40% by a comfortable margin.

### Blockers encountered

None. All data present, all libraries available, analysis completed within budget. One caveat noted: CSV coverage falls ~35 trading days short at the tail (2026-06-05 vs requested 2026-07-23) which slightly weakens the "recent regime" sample in Task 2 but does not affect the direction of any conclusion.

### Next steps if any block encountered

- If Willy wants to run this on 45M data for Task 3, source 45M bars for TXF1 or TWII covering the same range. Re-run the same fire-detection logic with adjusted forward-look window (e.g., 15 bars instead of 5, given 3× bar density).
- If Willy wants tighter statistical rigor, expand the entry filter (Task 3) from naive SMA61 crossover to something closer to the real L1 entry conditions, which will yield more holds and more fires per year.

---

## Appendix

### Data caveats

1. **TWII as TXF1 proxy**: index vs futures basis is negligible at intraday resolution, but can distort daily magnitudes by ±100-300 pts around ex-div and rollover. All analyses here use price differences not absolute levels, which mitigates most of this. But formula L1_c's exact absolute values will differ slightly on real TXF1.
2. **Daily as 45M proxy in Task 3**: 45M has ~5.5 bars per RTH day → the true architecture would generate 3-9× more fires per calendar year. This proxy is a directional signal only. The direction (saved rate too high) is likely to be preserved because the underlying market reactivity behavior does not fundamentally change with timeframe, but exact percentages will shift.
3. **CSV coverage**: 2020-01-02 to 2026-06-05. Head (2019-12-16 to 2020-01-01, 12 trading days) and tail (2026-06-06 to 2026-07-23, ~35 trading days) missing. Neither affects direction of conclusions.
4. **ATR20 method**: simple average of True Range (matches MC PowerLanguage's `AvgTrueRange` function). Wilder smoothing (RMA) would give slightly different values but similar correlations.
5. **Task 3 halved-SL proxy = 100 pts**: chosen as a round-number proxy for what a halved SL might be at 15-16K index level. At 40-48K current level the actual halved SL would be 250-500 pts. If the study were re-run with a larger halved-SL threshold, killed rate would drop (harder to reach) and saved rate would rise — strengthening the reject verdict.

### Python code used

Full analysis script preserved at:
`C:\Users\WILLYC~1\AppData\Local\Temp\claude\C--Users-WILLY-CHIU\d1fdcfb7-3a61-4213-9a3f-6623bab16531\scratchpad\l1_p3_analysis.py`

Key intermediate outputs (CSV) for audit:
- `<scratchpad>\l1_indicators.csv` — daily series: Date, OHLC, ATR20, L1_a..d
- `<scratchpad>\fires.csv` — every detected fire event with entry, fire date, trigger flags, outcome
- `<scratchpad>\holds.csv` — every simulated hold (entry, exit, outcome)
- `<scratchpad>\results.json` — full numeric results object

Core computations (excerpt):

```python
# 4 Layer 1 formulas (rolling 10-day window ending at t inclusive)
WINDOW = 10
df["L1_a"] = df["High"].rolling(WINDOW).max() - df["Low"].rolling(WINDOW).min()
df["L1_b"] = (df["High"] - df["Low"]).rolling(WINDOW).max()

def rolling_max_c2c_drawdown(c, w):
    n = len(c); out = np.full(n, np.nan); vals = c.values
    for t in range(w - 1, n):
        window = vals[t - w + 1 : t + 1]
        cummax = np.maximum.accumulate(window)
        drops = cummax - window
        out[t] = drops.max()
    return pd.Series(out, index=c.index)
df["L1_c"] = rolling_max_c2c_drawdown(df["Close"], WINDOW)
df["L1_d"] = (df["High"] - df["Low"]).rolling(WINDOW).quantile(0.75)

# ATR20 (simple average of TR, matching MC's AvgTrueRange)
df["tr"] = df.apply(lambda r: max(
    r["High"] - r["Low"],
    abs(r["High"] - r["prev_close"]) if pd.notna(r["prev_close"]) else 0,
    abs(r["Low"] - r["prev_close"]) if pd.notna(r["prev_close"]) else 0
), axis=1)
df["ATR20"] = df["tr"].rolling(20).mean()

# Task 3: Trigger A and Trigger B detection (per bar within hold)
# Trigger A: 3 consecutive Close<Open, total decline > 100 pts
three_red = (c0 < o0) and (c1 < o1) and (c2 < o2)
total_decline = (o2 - c0)  # open of first bar to close of last bar
trigger_a = three_red and (total_decline > 100)

# Trigger B: Close < prev Open, body > 2 * avg body of last 20 bars
body = abs(close_now - open_now)
avg_body = df["avg_body_20"].shift(1)  # avg of prior 20 bars, excluding current
trigger_b = (close_now < prev_open) and (body > 2 * avg_body)
```

### Output files

| File | Path |
|---|---|
| This report | `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\docs\research\L1_P3_python_analysis_20260724.md` |
| L1 formula histograms | `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\docs\research\L1_P3_python_analysis_20260724_hist.png` |
| Fire distance histogram | `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\docs\research\L1_P3_python_analysis_20260724_fire_hist.png` |
| Analysis script | `C:\Users\WILLYC~1\AppData\Local\Temp\claude\C--Users-WILLY-CHIU\d1fdcfb7-3a61-4213-9a3f-6623bab16531\scratchpad\l1_p3_analysis.py` |
| Intermediate CSVs | `C:\Users\WILLYC~1\AppData\Local\Temp\claude\C--Users-WILLY-CHIU\d1fdcfb7-3a61-4213-9a3f-6623bab16531\scratchpad\` |
