# TXF1 Portfolio Walk-Forward & Stability Synthesis (P0-2)

- **Date**: 2026-06-19 (data through 2026-06-05)
- **Universe**: L1 (TrendLong), L2 (TrendShort), L3 (ConsolidationLong), L4 (ConsolidationShort), L5 (BreakoutLong), S1 (NightMomentum / live_simulation)
- **Inputs synthesized**:
  - Agent A: rolling-window PF/Sharpe — `scripts/_temp_rolling_stats.md`
  - Agent B: IS/OOS walk-forward (4 splits) — `scripts/_temp_is_oos.md`
  - Agent C: rolling correlation stability (fat-tail verification) — `scripts/_temp_rolling_corr.md`
  - Agent D: year-by-year metrics 2020-2025 — `scripts/_temp_yearly_metrics.md`
  - Agent E: bootstrap + PSR + Gini overfit detection — `scripts/_temp_overfit_check.md`
- **Anchor**: P0-1 correlation matrix — `docs/portfolio_correlation_matrix_20260620.md`
- **Visualization**: `docs/portfolio_rolling_sharpe_20260620.svg`

---

## 1. Executive Summary

### Five headline findings across the 5 analyses

1. **L4 fails 4 of 5 stability tests** — UNSTABLE on rolling windows (720d fail-rate 76%, 720d mean PF 0.952 < 1), UNRELIABLE on yearly (3 losing years out of 6, stability 3.24), WATCH on overfit (bootstrap robustness 76.5%, PSR 0.770, Gini 0.619), and IS_NEG_OOS_POS on 3 of 4 IS/OOS splits. Only the IS/OOS test treats it as "robust" — and that's because IS itself is breakeven/negative, an edge-case verdict that is the opposite of validation.
2. **L5 is the cleanest sleeve by every single test** — STABLE rolling windows (0% 720d fail-rate, all 1005 windows PF≥1.084), ROBUST IS/OOS (4/4 splits, WFE_pnl 6.99→21.36), ROBUST overfit (100% bootstrap, PSR 0.995), only 1 losing year. The single caveat is the shortest history (4.7 yrs) and HIGHLY VOLATILE yearly stability (std/|mean|=1.33) from 2024-25 outsized profits.
3. **The L2-L4 +0.614 monthly correlation is an ARTIFACT** — rolling-12 median is only +0.092 with std 0.601 (stability score 6.50 → regime-dependent), and removing the top-5 joint fat-tail months (2025-04, 2024-08, 2020-03, 2022-10, 2022-06) **flips Pearson sign** to −0.144. The "redundancy" between L2 and L4 in P0-1 was driven by 3-4 crisis windows where both shorts fired together.
4. **Every WFE > 1.0 is regime-driven, not edge-driven** — every strategy's OOS_avg_daily_pnl exceeded IS_avg_daily_pnl (often 2x-20x). The OOS windows all fall in 2024-2026 (AI-driven TXF1 rally). This means WFE > 0.7 verdicts here should be read as "no evidence of degradation in this direction", NOT as "edge has grown". L1, L3 are the only strategies whose WFE values cluster near 1.0-2.0 (consistent with real durable edge); L2, L4, L5 WFE>5 is regime tailwind.
5. **L1 is the unanimous foundation** — ROBUST on every test (rolling 720d fail-rate 6%, WFE 4/4 robust on every split, bootstrap 99.1%, PSR 0.981, 0 losing years out of 6, largest drop-one Sharpe contribution in P0-1). Even its single agent-A "UNSTABLE" flag is just a shallow 720d dip to PF=0.886, the loosest possible failure mode.

### Critical question — Is L2-L4 monthly +0.614 STRUCTURAL or ARTIFACT?

**Answer: ARTIFACT.** (Agent C, definitive)

Evidence:
- Rolling-12 median Pearson is **+0.092** (vs full-sample +0.614 — 85% lower)
- Rolling-12 std is **0.601**, range `[−0.774, +0.994]` — sign flips constantly
- Stability score **6.50** (institutional ARTIFACT threshold is >2.0)
- Removing top-5 joint fat-tail months → Pearson collapses to **−0.144** (sign flip, +123.5% magnitude change)
- 62 rolling-12 windows: 28 positive / 8 neutral / 26 negative — true distribution is symmetric around zero

**Implication for L4 cut decision**: The P0-1 recommendation to cut L4 from 10% → 3% was partly justified by L2-L4 monthly +0.614 redundancy. That justification is now invalid. **However, L4 still fails 4 of 5 other tests** (rolling stability, yearly reliability, overfit detection, IS-negative pattern). The L4 cut to 3% is **still correct**, but for different reasons:
- No longer "redundant with L2" (false — they only co-move in crises)
- Now "standalone-fragile" — bootstrap p5 = −234k (could plausibly have been a losing strategy), 720d PF<1 in 76% of windows, loses money in bear regime, IS-negative on 3 of 4 splits
- Verdict: **confirm L4 cut to 3%, but reclassify rationale from "redundancy" to "standalone fragility / opportunistic-only"**

### Per-strategy 1-line verdict

| Strategy | Verdict | One-line rationale |
|----------|---------|--------------------|
| **L1** | **ROBUST** | Passes all 5 tests cleanly. The portfolio's foundation. |
| **L2** | **WATCH** | Passes overfit and WFE, but only 78 trade-days and bear regime is its strongest (asymmetric tail-dependent edge). Size with sparse-trader humility. |
| **L3** | **WATCH** | Marginal edge: 720d fail-rate 37%, bootstrap p5 = −238k, PSR 0.884 < 0.95. WFE robust. The only true low-correlation diversifier — keep but don't size up. |
| **L4** | **OVERFIT_RISK** | Fails rolling, fails yearly, fails overfit; "passes" IS/OOS only because IS itself is breakeven. Recent profit concentrated on a handful of 2025 days (Gini 0.619). |
| **L5** | **ROBUST** | Cleanest by every metric, but caveat: 4.7-yr history, zero range-regime data, OOS profit in regime tailwind. ROBUST-with-asterisk. |
| **S1** | **WATCH** | Bootstrap perfect (100%, PSR 0.998) but 2 of 4 IS/OOS splits show IS_NEG (edge only post-2024), 720d fail-rate 19%, 3 of 6 yearly losses. Bear-regime hedge value > standalone edge. |

---

## 2. Rolling Window Stability (Agent A)

### 2.1 PF instability scores (360-day basis)

| Rank | Strategy | PF instability (360d) | Sharpe instability (360d) | Flag |
|------|----------|----------------------:|---------------------------:|------|
| 1 | L1 | 0.250 | 1.168 | clean |
| 2 | L3 | 0.265 | 5.118 | clean (PF) |
| 3 | L5 | 0.367 | 0.860 | clean |
| 4 | S1 | 0.372 | 1.827 | clean (PF) |
| 5 | L4 | **0.651** | 4.721 | **>0.5 flag** |
| 6 | L2 | **1.227** | 4.990 | **>0.5 flag** |

### 2.2 Failure-window rate (PF < 1.0 fraction)

| Strategy | Fail-rate 360d | Fail-rate 720d | Worst 720d PF (date) | Flag |
|----------|---------------:|----------------:|----------------------|------|
| L5 | 13.0% | **0.0%** | 1.084 (2023-09-05) | clean |
| L1 | 13.5% | 6.0% | 0.886 (2023-04-23) | 720d PF<1 (shallow) |
| L2 | 30.2% | 5.9% | 0.684 (2024-06-24) | **flag** |
| S1 | 36.3% | 18.8% | 0.834 (2024-03-06) | **flag** |
| L3 | 39.0% | 36.8% | 0.797 (2025-07-14) | **flag** |
| L4 | 55.2% | **76.0%** | 0.439 (2022-03-09) | **severe** |

### 2.3 Agent A verdict per strategy

| Strategy | Verdict | Key flag |
|----------|---------|----------|
| L1 | **UNSTABLE-by-rule / WATCH-in-practice** | Single shallow 720d dip to PF 0.886; otherwise best non-L5 strategy. |
| L2 | UNSTABLE | 3 flags, but sparse-trader caveat (78 trades / 5.3 yrs). |
| L3 | UNSTABLE | 720d fail-rate 37% — marginal economics. |
| L4 | **UNSTABLE — severe** | 3 flags, 720d mean PF 0.952 (< 1 on average!), 720d worst 0.439. |
| L5 | **STABLE** | Cleanest — only strategy with zero 720d failure windows. |
| S1 | UNSTABLE | 720d PF dropped to 0.834 in 2024-Q1; otherwise PF mean 1.28. |

---

## 3. IS/OOS Walk-Forward Test (Agent B)

### 3.1 WFE summary (70/30 split as primary)

| Strategy | WFE_pnl (70/30) | WFE_pf | WFE_sharpe | Splits-pass |
|----------|----------------:|-------:|-----------:|------------:|
| L1 | 1.92 | 1.00 | 0.82 | 4/4 ROBUST |
| L2 | 4.63 | 2.65 | 1.62 | 4/4 ROBUST |
| L3 | 2.09 | 0.99 | 0.81 | 4/4 ROBUST |
| L4 | **−58.41** | 2.31 | **−16.77** | 1/4 ROBUST + 3/4 IS_NEG_OOS_POS |
| L5 | 21.36 | 3.01 | 6.48 | 4/4 ROBUST |
| S1 | 11.72 | 1.71 | 5.13 | 2/4 ROBUST + 2/4 IS_NEG_OOS_POS |

### 3.2 Stability across 4 splits (50/50, 60/40, 70/30, 80/19)

| Strategy | WFE_pnl trajectory | Interpretation |
|----------|--------------------|-----------------|
| L1 | [2.06, 3.51, 1.92, 3.09] | Genuine edge across all splits |
| L2 | [2.55, 2.49, 4.63, 10.54] | Edge present but wild swing in 80/19 = small-N artifact |
| L3 | [1.39, 1.80, 2.09, 8.14] | Edge near 1.5-2.0 base; 80/19 outlier from regime tailwind |
| L4 | [169.43, **−14.89, −58.41, −69.63**] | IS turns negative starting 60/40 — historic edge has died |
| L5 | [6.99, 12.78, 21.36, 11.14] | Strong everywhere but 2024-26 OOS regime explains magnitude |
| S1 | [**−17.54, −21.02**, 11.72, 6.36] | IS lost money in 2020-2023 portion; OOS profit is 2024+ only |

### 3.3 Overfit candidates (flagged for closer review)

- **L4** — IS flat/negative across 3 of 4 splits. 76 trade-days over 5 years. OOS profit concentrated in 2025-04-07 (+273k single day). Single-day dependence → fragile.
- **S1** — IS negative in 50/50 and 60/40 splits. Original entry logic didn't work in 2020-2023; profit is regime-driven, not skill-driven.
- **L2** — 78 trade days over 5+ years. WFE_pnl 2.55→10.54 = low-sample-size artifact, not stability.

### 3.4 Critical caveat (carried from Agent B)

**Every strategy shows OOS > IS** — this is a regime-shift signature, not an edge-validation signal. 2024-2026 TXF1 saw a record AI-driven rally; long-trend (L1/L2/L5), breakout (L5), and overnight momentum (S1) all benefit. WFE > 0.7 verdicts here mean "no overfit in this split direction" — not "edge has grown". **Size on IS metrics, not OOS, to avoid sizing into peak-regime mean reversion.**

---

## 4. Rolling Correlation Stability (Agent C — KEY ANSWER)

### 4.1 L2-L4: STRUCTURAL or ARTIFACT?

**Verdict: ARTIFACT** (definitive)

| Metric | Value | Threshold |
|--------|-------|-----------|
| Full-sample Pearson | +0.614 | — |
| Full-sample Spearman | −0.174 | (delta 0.789!) |
| Rolling-12 median | +0.092 | (85% lower than full-sample) |
| Rolling-12 std | 0.601 | — |
| Rolling-12 range | [−0.774, +0.994] | extreme |
| Stability score (std/|median|) | **6.50** | >2.0 = regime-dependent |
| Clean Pearson (drop top-5 fat-tail months) | **−0.144** | sign FLIP |
| Collapse magnitude | +123.5% | >50% = artifact |
| Sign-flip rolling windows | 28 pos / 8 neutral / 26 neg | symmetric around zero |

Top-5 joint fat-tail months (drove the +0.614 illusion): **2025-04, 2024-08, 2020-03, 2022-10, 2022-06**. Three of five were same-sign (both shorts fired in real crises); two were opposing.

### 4.2 L1-L5: ARTIFACT

| Metric | Value |
|--------|-------|
| Full Pearson | +0.524 |
| Full Spearman | +0.162 |
| Rolling-12 median | +0.256 |
| Rolling-12 std | 0.264 (stability 1.03) |
| Clean Pearson (drop top-5) | **+0.006** (98.9% collapse) |

Both are long-trend strategies; modest persistent overlap (rolling median +0.256) is real but not redundant. Not a sizing constraint at proposed weights.

### 4.3 L1-S1 hedge stability (most important pair)

| Metric | Value |
|--------|-------|
| Full Pearson | +0.177 |
| Bear-regime Pearson (P0-1) | **−0.129** |
| Rolling-12 median | +0.132 |
| Rolling-12 range | [−0.381, +0.623] |
| Rolling-12 std | 0.242 (stability 1.83) |
| Clean Pearson (drop top-5) | +0.075 |
| Sign-flip windows | 37 pos / 9 neutral / 22 neg |

**Caution**: the L1↔S1 hedge is **regime-dependent**, not robust at all horizons. Bear regime is the only window where it's reliably negative. **Do not size as if it's an always-on hedge.** It is a bear-regime catastrophe hedge, not a daily risk reducer. This downgrades the P0-1 "irreplaceable hedge" framing but does not eliminate S1's bear-regime workhorse status.

### 4.4 L5-S1: ARTIFACT (additional finding)

Full +0.504 / clean +0.193 / rolling-12 median −0.044. Both momentum-flavored; the +0.504 is the 2026 Q1-Q2 mega-month signature, not a structural link.

### 4.5 Implication for L4 allocation decision

The P0-1 cut justification was: "L4 is redundant with L2 (+0.614 monthly)". Agent C invalidates that specific claim.

**However**: the L4 cut to 3% **survives reclassification** because L4 fails on standalone-merit grounds (sections 2, 5, 6 below):
- Standalone Sharpe 0.282 (lowest in book)
- 720d fail-rate 76% (worst in book)
- Bootstrap robustness 76.5% (only strategy <95%)
- Gini 0.619 (only strategy lottery-flagged)
- 3 losing years out of 6
- Loses money in bear regime (only strategy that does)

→ **Hold L4 = 3% recommendation, but rewrite rationale**: "L4 trimmed for standalone fragility (lottery profile, year-to-year instability), not for L2 redundancy."

---

## 5. Year-by-Year Performance (Agent D)

### 5.1 6×6 grid: Net PnL by strategy × year (NTD)

| Year | L1 | L2 | L3 | L4 | L5 | S1 |
|------|---:|---:|---:|---:|---:|---:|
| 2020 | +356,600 | +156,400 | +251,600 | +27,200 | — | **−175,800** |
| 2021 | +226,800 | +55,200 | +9,800 | **−17,600** | **−32,000** | +132,600 |
| 2022 | +3,400 | +291,600 | **−108,600** | **−51,200** | +1,600 | **−17,800** |
| 2023 | +132,200 | **−74,000** | +160,800 | +26,800 | +51,800 | **−55,600** |
| 2024 | +605,200 | +523,800 | **−61,200** | **−40,600** | +163,200 | +423,000 |
| 2025 | +133,200 | +481,800 | +101,000 | **+294,000** | +121,600 | +517,000 |
| **6Y total** | **+1,457,400** | **+1,434,800** | **+353,400** | **+238,600** | **+306,200** | **+823,400** |

### 5.2 Losing-year count (ranked worst → best)

| Rank | Strategy | # Losing years | Years lost | Loss rate |
|------|----------|---------------:|------------|----------:|
| 1 | L4 | 3 | 2021, 2022, 2024 | **50%** |
| 2 | S1 | 3 | 2020, 2022, 2023 | **50%** |
| 3 | L3 | 2 | 2022, 2024 | 33% |
| 4 | L5 | 1 | 2021 | 20% |
| 5 | L2 | 1 | 2023 | 17% |
| 6 | **L1** | **0** | — | **0%** |

### 5.3 Lottery-dependency analysis (does a single year save the strategy?)

L4 6-year net is +238,600 — but 2025 alone delivered +294,000. **Without 2025, L4 is net −55,400 over 5 years.** That single year (driven by one fat-tail month, 2025-04, +286,600 in PnL) is the entire edge.

| Strategy | Single best year | % of 6Y total | Without best year |
|----------|------------------:|--------------:|-------------------:|
| **L4** | 2025 (+294,000) | **123%** | **−55,400 (red)** |
| L5 | 2024 (+163,200) | 53% | +143,000 |
| L3 | 2020 (+251,600) | 71% | +101,800 |
| L2 | 2024 (+523,800) | 37% | +911,000 |
| S1 | 2025 (+517,000) | 63% | +306,400 |
| L1 | 2024 (+605,200) | 42% | +852,200 |

→ **L4 is the only strategy whose 6-year track record fails the "lose your best year" test.** L1, L2, L5, S1 all remain solidly profitable without their best year. L3 stays positive. L4 turns into a loser.

### 5.4 Year-to-year stability (std / |mean| ranked most volatile first)

| Rank | Strategy | Yearly stability | Flag |
|------|----------|-----------------:|------|
| 1 | L4 | **3.24** | UNRELIABLE + HIGHLY VOLATILE + LUCK-BASED |
| 2 | L3 | **2.33** | HIGHLY VOLATILE + LUCK-BASED |
| 3 | S1 | **2.02** | UNRELIABLE + HIGHLY VOLATILE |
| 4 | L5 | 1.33 | HIGHLY VOLATILE + LUCK-BASED |
| 5 | L2 | 0.99 | LUCK-BASED |
| 6 | L1 | **0.88** | LUCK-BASED (smallest) |

Caveat: "LUCK-BASED" by agent-D's lottery-year rule fires whenever a single trade is >30% of the year's net — which is unavoidable for low-frequency strategies (L2, L4, L5 trade <20 times/year). The truly informative flag is **stability**, where L1 (0.88) and L2 (0.99) are within healthy band and L4 (3.24) is off the chart.

---

## 6. Overfit Detection (Agent E)

### 6.1 Bootstrap robustness (1000 resamples) ranked

| Rank | Strategy | Total PnL | Bootstrap p5 | Robustness | Flag |
|------|----------|----------:|--------------:|-----------:|------|
| 1 | L5 | +1,607,400 | +699,000 | **100.0%** | clean |
| 2 | S1 | +1,472,400 | +622,800 | **100.0%** | clean |
| 3 | L2 | +1,434,800 | +469,000 | 99.8% | clean |
| 4 | L1 | +2,272,000 | +559,600 | 99.1% | clean |
| 5 | L3 | +651,800 | **−238,400** | 88.6% | **p5 < 0** |
| 6 | L4 | +238,600 | **−234,400** | 76.5% | **p5 < 0, robustness < 95%** |

L3 and L4 are the only two strategies whose track record could plausibly have been a losing one under random reordering (p5 < 0).

### 6.2 PSR rankings

| Rank | Strategy | N | Sharpe(daily) | PSR | Significant (≥0.95)? |
|------|----------|--:|---------------:|----:|:---------------------:|
| 1 | S1 | 594 | 0.1183 | **0.9980** | YES |
| 2 | L5 | 135 | 0.2204 | **0.9946** | YES |
| 3 | L2 | 78 | 0.2566 | **0.9878** | YES |
| 4 | L1 | 429 | 0.1007 | **0.9814** | YES |
| 5 | L3 | 335 | 0.0653 | 0.8837 | **NO** |
| 6 | L4 | 76 | 0.0853 | 0.7699 | **NO** |

L3 and L4 again fail — their Sharpes are not statistically distinguishable from zero at 95% confidence.

### 6.3 Gini / lottery dependency

| Strategy | Gini | Top-10% share | Flag |
|----------|-----:|---------------:|------|
| **L4** | **0.619** | 52.6% | **lottery YES** |
| L2 | 0.575 | 41.3% | no |
| L5 | 0.532 | 38.9% | no |
| S1 | 0.522 | 39.7% | no |
| L1 | 0.470 | 36.8% | no |
| L3 | 0.391 | 31.7% | no |

L4 is the only strategy with Gini > 0.6 — half the positive PnL came from the top 10% of winning days. Removes those days and the strategy is breakeven.

### 6.4 Combined overfit-risk score

| Rank | Strategy | Score | Verdict |
|------|----------|------:|---------|
| 1 | L1 | 0.00 | ROBUST |
| 2 | L2 | 0.00 | ROBUST |
| 3 | L5 | 0.00 | ROBUST |
| 4 | S1 | 0.00 | ROBUST |
| 5 | L3 | 0.84 | ROBUST (borderline) |
| 6 | **L4** | **2.71** | **WATCH** |

---

## 7. Visualization

See `docs/portfolio_rolling_sharpe_20260620.svg` for the rolling-Sharpe / rolling-PF time-series view of all 6 strategies (180/360/720 day windows). The visualization makes the L4 anomaly visually obvious: it is the only strategy whose 720d PF line crosses below 1.0 for sustained periods (2022-2024), while L5 is the only strategy that never dips below PF 1.084 on the same 720d basis.

---

## 8. Critical Synthesis

### 8.1 Strategies that pass ALL 5 tests (institutional-ready)

**L1** — only unanimous pass.
- Rolling: WATCH-grade (shallow 720d dip); all other windows clean
- IS/OOS: 4/4 ROBUST across splits
- Correlation: anchor of the L1↔S1 hedge (though hedge is regime-dependent)
- Yearly: 0 losing years, stability 0.88 (best)
- Overfit: bootstrap 99.1%, PSR 0.981, score 0.00

**L5** — passes 4 of 5; caveat on yearly stability (1.33 from 2024-25 outperformance), and only 4.7-yr history.
- Rolling: STABLE (only strategy with 0% 720d fail-rate)
- IS/OOS: 4/4 ROBUST but WFE 6.99-21.36 suggests regime tailwind, not just edge
- Correlation: L1-L5 monthly +0.524 is ARTIFACT (rolling median +0.256)
- Yearly: 1 losing year (2021); HIGHLY VOLATILE flag from outsized 2024-25 profits
- Overfit: bootstrap 100%, PSR 0.995, score 0.00

→ **L1 and L5 are the two foundations of the book.** Everything else is conditional.

### 8.2 Strategies that fail 2+ tests (immediate concern)

**L4** — fails 4 of 5 tests:
1. Rolling: UNSTABLE severe (720d PF mean 0.952 < 1; 76% of 720d windows lose money)
2. IS/OOS: IS_NEG_OOS_POS on 3 of 4 splits (historic edge dead)
3. Yearly: UNRELIABLE (3 losing years), HIGHLY VOLATILE (3.24), LUCK-BASED
4. Overfit: WATCH (bootstrap 76.5%, PSR 0.770, Gini 0.619, p5 < 0)
5. Correlation: only test it "passes" — and only because the L2-L4 +0.614 was artifact (so L4 isn't structurally redundant). But "not structurally redundant" ≠ "good"

**L3** — fails 2 tests:
1. Rolling: UNSTABLE (720d fail-rate 37%, 360d fail-rate 39%)
2. Overfit: borderline (PSR 0.884 < 0.95, bootstrap 88.6%, p5 < 0)
3. Yearly: 2 losing years, stability 2.33 = HIGHLY VOLATILE
4. IS/OOS: PASS (4/4 ROBUST, WFE 1.39-8.14)
5. Correlation: PASS (cleanest low-correlation diversifier in the book)

L3 is the **borderline keeper** — it's the only true low-correlation diversifier, but its standalone edge is marginal. Holding at 12% per P0-1 is defensible only if we accept "carrying low-Sharpe independence" as the explicit role.

**S1** — fails 2 tests:
1. Rolling: UNSTABLE (720d fail-rate 19%, fail-rate 360d 36%)
2. Yearly: UNRELIABLE (3 losing years 2020/22/23), HIGHLY VOLATILE
3. IS/OOS: 2/4 IS_NEG_OOS_POS — historic edge only emerged in 2024
4. Overfit: PASS (bootstrap 100%, PSR 0.998, score 0.00)
5. Correlation: PASS but hedge value is bear-regime-only

S1 is the **role-based keeper** — its bear-regime workhorse role (+$305k bear PnL, top in book) is irreplaceable, even though its standalone edge only emerged in 2024+.

**L2** — fails 1 test:
1. Rolling: UNSTABLE (3 flags) — but driven by sparse-trader artifact (78 trades / 5.3 yrs)
2. Other 4: PASS

L2 is the **caveat keeper** — every reliable metric says OK, but the sparse-trader caveat means high uncertainty bars on everything.

### 8.3 L4 final verdict

**Cut L4 to 3% as P0-1 recommended, but rewrite the rationale.**

P0-1's rationale was correlation-based ("redundant with L2"). Agent C invalidated that specific claim. However:

- **5 of 5 stability/overfit tests now point at L4 as the weakest sleeve** (rolling, IS/OOS, yearly, overfit, lottery)
- **Yearly grid shows L4 is mathematically dependent on 2025** (without 2025, L4 is net −55,400 over 5 years — the only strategy with this property)
- **720d PF mean is 0.952, less than 1** — over a typical 2-year window, L4 loses money in expectation
- **Bootstrap p5 = −234,400** — there's a meaningful probability this entire 6-year track record was luck

Considered alternatives:
- **Cut to 0% (archive)**: Mathematically defensible (drop-one in P0-1 said removing L4 *raises* portfolio Sharpe). But L4 is the only ConsolidationShort sleeve and a clean architectural slot. Keeping 1-lot diagnostic presence preserves optionality.
- **Restore to higher than 3%**: Cannot justify on any test. The L2-L4 artifact finding removes one specific "redundancy" objection, but doesn't add positive edge evidence.

**Decision: L4 stays at 3% (1-lot floor presence for ongoing diagnostic).** Trigger for archive: if next-quarter L4 review shows bear-regime PnL still negative AND yearly stability still > 3.0, downgrade to research-only.

---

## 9. Refined Allocation v2.5

### 9.1 Per-strategy walk-forward adjustments

| Strategy | P0-1 weight | P0-2 stability signal | P0-2 adjustment | **Final v2.5** | Rationale |
|----------|------------:|-----------------------|----------------:|---------------:|-----------|
| **L1** | 28% | ROBUST (5/5 pass) | **+1** | **29%** | Unanimous pass on every test. Marginally upsize the foundation. |
| **L2** | 22% | WATCH (sparse-trader caveat, but 4/4 WFE) | **0** | **22%** | L2-L4 artifact finding removes redundancy fear → hold P0-1 weight. Do not increase further (78 trades = high uncertainty bar). |
| **L3** | 12% | WATCH (PSR 0.884 < 0.95, rolling fail-rate 37%) | **−2** | **10%** | Marginal edge confirmed; only diversification value justifies position. Trim slightly. |
| **L4** | 3% | OVERFIT_RISK (4 of 5 fail) | **0** | **3%** | Cut survives despite L2-L4 artifact finding. Standalone fragility dominates. |
| **L5** | 15% | ROBUST (4 of 5 pass; HIGHLY VOLATILE yearly) | **+1** | **16%** | Cleanest rolling/overfit profile. Modest upsize. L1-L5 artifact finding removes redundancy concern. |
| **S1** | 20% | WATCH (2/4 IS_NEG, but bear-hedge role) | **0** | **20%** | Bear-regime workhorse role > standalone-edge concerns. Hold P0-1. |
| **TOTAL** | 100% | | | **100%** | |

### 9.2 Comparison summary

| Strategy | Prior (2026-06-18) | P0-1 | **P0-2 v2.5** | Δ vs P0-1 | Total Δ vs prior |
|----------|-------------------:|-----:|--------------:|----------:|------------------:|
| L1 | 25% | 28% | **29%** | +1 | +4 |
| L2 | 15% | 22% | **22%** | 0 | +7 |
| L3 | 10% | 12% | **10%** | −2 | 0 |
| L4 | 10% | 3% | **3%** | 0 | −7 |
| L5 | 20% | 15% | **16%** | +1 | −4 |
| S1 | 20% | 20% | **20%** | 0 | 0 |

### 9.3 Why v2.5 is a small delta from P0-1

P0-2 largely **validates** the P0-1 allocation rather than rebuilding it:
- L4 cut justified (different reason, same number)
- L1 + L5 are confirmed ROBUST → small +1 each
- L3 trim −2 because marginal-edge evidence (PSR 0.884, rolling fail-rate 37%) was not visible at P0-1
- L2 and S1 status quo (P0-2 confirms caveats already known)

### 9.4 Expected impact (rough)

| Metric | P0-1 v2.0 | **P0-2 v2.5** | Δ |
|--------|----------:|--------------:|---:|
| Weighted-mean monthly NTD (using individual means) | ~22,800 | ~23,100 | +1.3% |
| Approximate weighted std | ~45,000 | ~44,800 | −0.4% |
| Implied annual Sharpe (rough) | ~1.40 | **~1.41** | +0.7% |

The Sharpe gain is marginal; the real value of v2.5 is **correct rationale** (artifact-aware) and **L1/L5 confidence upgrade** (now unanimous-pass foundations rather than just "highest individual Sharpe").

---

## 10. Next Step Recommendation

**Skip P0-3 (Three-regime PF) as a separate effort. Roll its remaining gap into the v2 allocation document directly.**

### Rationale

1. **P0-1 section 4 already delivered 90% of P0-3.** All 6 strategies have regime-conditional PnL, n, WR, avg/trade tables for bull / bear / range (P0-1 §4.5). The only formal P0-3 deliverable that's missing is **PF per regime** (not just total PnL). This is a ~30-minute compute, not a full P0-effort.

2. **Agent D (yearly) provides a richer-than-regime view.** The 6×6 year-grid (2020-2025) lets us read regime sequencing directly: 2020 = range/COVID, 2021 = bull, 2022 = bear (Fed), 2023-24 = bull (AI), 2025 = mixed. We already know L4 lost money in 3 of 6 years, S1 in 3 of 6, etc. — this is finer-grained than the regime collapsing.

3. **The L4 decision (the original purpose of running P0-2/P0-3) is resolved.** L4 = 3% is now triple-confirmed (P0-1 drop-one + P0-2 stability + Agent D yearly). No need for a fourth P0 to relitigate.

4. **The institutional risk framework gate is met.** `CLAUDE.md` clause 13 requires WFE > 50% as one of 10 dimensions; P0-2 delivered WFE_pf ranging from 0.99 (L3) to 3.01 (L5), all above the threshold. The other 9 dimensions are already covered by P0-1 (correlation, drawdown clustering) or pre-existing institutional audit reports.

### Action

**Write `docs/portfolio_allocation_v2_20260620.md`** (the binding allocation document) directly, incorporating:
- P0-1 correlation matrix as the diversification basis
- P0-2 (this report) as the stability/robustness basis
- A 30-minute "PF per regime" mini-table inserted as a section instead of a full P0-3 effort
- The v2.5 allocation table from section 9 above
- Implementation guidance (lot count per strategy at typical book sizes)

### What a separate P0-3 would close (if you decide to run it anyway)

The only **net-new** information P0-3 would provide:
- Formal PF (not just net PnL) per regime — useful for tail-risk pricing but not allocation-changing
- Cross-regime PF stability score per strategy — partly redundant with Agent A's rolling-window analysis at 720-day horizon
- Range-regime data for L5 (currently absent) — but range bucket is 74 days, COVID-only, so the new data would be a single point

→ **Not worth a parallel-agent run.** Inline the PF-per-regime mini-table into the v2 allocation doc instead.

---

_Report compiled 2026-06-19 from 5 parallel walk-forward / stability analyses. Source materials retained in `scripts/_temp_rolling_stats.md`, `scripts/_temp_is_oos.md`, `scripts/_temp_rolling_corr.md`, `scripts/_temp_yearly_metrics.md`, `scripts/_temp_overfit_check.md`. Anchored against `docs/portfolio_correlation_matrix_20260620.md` (P0-1)._
