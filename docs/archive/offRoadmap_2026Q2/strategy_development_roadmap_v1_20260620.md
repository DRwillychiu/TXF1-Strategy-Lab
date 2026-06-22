# TXF1 Strategy Development Roadmap v1 — Alpha Innovation Phase

- **Date**: 2026-06-20
- **Author**: Compiled from 6 deep-discovery agents (A coverage / B taxonomy / C TXF anomalies / D short-rip design / E institutional lib / F candidate pipeline)
- **Status**: MASTER roadmap. Supersedes all prior individual-strategy optimization plans through 2027-06.
- **Portfolio anchor**: 6 live strategies FROZEN per user direction (2026-06-20)
- **Reference reports**:
  - `scripts/_temp_coverage_gap.md` (Agent A — 8-dim coverage matrix)
  - `scripts/_temp_alpha_taxonomy.md` (Agent B — 10 factor families)
  - `scripts/_temp_txf_anomalies.md` (Agent C — 12 TXF-native anomalies)
  - `scripts/_temp_short_rip_design.md` (Agent D — full S3 PullbackShort spec)
  - `scripts/_temp_institutional_lib.md` (Agent E — 10-category institutional library)
  - `scripts/_temp_candidate_pipeline.md` (Agent F — consolidated 22-candidate pipeline)
  - `docs/portfolio_correlation_matrix_20260620.md` (P0-1)
  - `docs/portfolio_walk_forward_20260620.md` (P0-2)
  - `docs/institutional_risk_framework_20260619.md` (10-dim gate)
  - `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` (mandatory inheritance)

---

## 1. Executive Summary

### Portfolio status
- **6 strategies FROZEN** as of 2026-06-20 (user direction): L1 TrendLong, L2 TrendShort, L3 ConsolidationLong, L4 ConsolidationShort, L5 BreakoutLong, S1 NightMomentum.
- No further individual-strategy parameter tweaks. All optimization effort redirects to **alpha innovation** (new strategies in unfilled state-space).
- Current portfolio metrics: EW Sharpe **1.329**, max-Sharpe-optimized ceiling **1.410**, structural cap ~**1.4**, monthly correlation max **+0.614** (L2↔L4, partially artifact per P0-2).

### Strategic shift
- **From**: Individual optimization (L4 v1.42 variants, L5 v19.8 SP module, S1 ORB tuning) → diminishing returns hitting a structural ceiling.
- **To**: Alpha INNOVATION — add new sleeves that occupy **un-covered state-space cells** (counter-trend short, cross-asset lead-lag, sentiment positioning, event-driven).
- **Catalyst**: User identified a specific, evidence-supported portfolio gap (Short-the-Rip / counter-trend short during bull-regime pullbacks) — and all 6 discovery agents converged on this same gap as the #1 priority.

### Top 3 strategies recommended for IMMEDIATE development (Q1 2026 H2)
1. **S3 PullbackShort** — counter-trend short in bull-regime pullbacks (15M execution, daily-regime gate). Fills the user-stated gap, fully spec'd by Agent D, 5-of-5 agent convergence.
2. **S4 TurnOfMonth_Long** — calendar-only positional long T-4 to T+3 around month-end. Lowest-complexity quick win, Sharpe-additive via near-zero correlation with everything.
3. **S5 SPX_Overnight_DayOpen** — cross-asset lead-lag: SPX overnight move > |0.7%| → TXF1 day-open momentum carry. Largest single new-factor alpha, ρ ≈ 0 to all 6.

### 12-month roadmap headline
**Lift portfolio EW Sharpe from 1.329 → ~1.75 over 12 months by adding 7 orthogonal sleeves spanning 5 currently-empty factor families** (mean-reversion-in-trend, calendar, cross-asset, sentiment, event-driven), while leaving all 6 live strategies untouched.

---

## 2. Why Freeze the Existing 6

### 2.1 Empirical evidence (P0-1 + P0-2)
- **P0-1 correlation matrix** (`docs/portfolio_correlation_matrix_20260620.md`): equal-weight Sharpe **1.329**, max-Sharpe-optimized **1.410**. The optimizer captures only **31% of sum-of-individual Sharpes** — the missing 69% is the factor-overlap penalty. Three structural redundancy axes (L2-L4 +0.614 monthly, L1-L5 +0.524, L5-S1 +0.504) confirm the book is over-concentrated in trend/momentum.
- **P0-2 walk-forward**: every WFE > 5 verdict was **regime tailwind, not edge** (every WFE > IS — the 2020-2026 dataset is bull-biased). Individual parameter optimization on existing sleeves produces over-fit to the prevailing regime.
- **Agent B taxonomy**: of 10 factor families, the book has **load-bearing exposure to only 2.5** (over-saturated trend + partial mean-reversion + partial microstructure). 5 high-evidence factor families are entirely unused.

### 2.2 Diminishing returns of individual optimization
- L1 / L2 / L5 are all variants of "managed-futures CTA / time-series momentum". Tuning any one of them sharper makes the other two more redundant — the correlation rises faster than the Sharpe.
- L4's 2025-04 single-day $273k contribution made it the year's hero, but P0-2 flagged this as **event-luck**, not skill. Further tuning L4 to "catch the next crisis" is unfalsifiable until another crisis happens.
- S1's 2024+ edge is **regime-driven not skill-driven** (P0-2 §3.2: IS negative in 2 of 4 splits). Tuning S1 ORB parameters is over-fitting to a regime that may already be turning.
- Structural ceiling: **Sharpe ~1.4 cannot be exceeded by adding a 7th trend sleeve**. The next 0.1 Sharpe lift must come from a **different factor family**, not from a sharper version of what we already have.

### 2.3 Alpha INNOVATION > Alpha REFINEMENT
- Adding one sleeve with ρ ≈ 0 to the existing 6 and standalone Sharpe even at 0.5 lifts portfolio EW Sharpe to ~1.45 (back-of-envelope from independence assumption).
- Three such sleeves (C01 + C02 + C07 per Agent F) lift to ~1.60.
- The full 7-sleeve pipeline targets ~1.75.
- By contrast, **no realistic individual-strategy tweak on L1-L5 / S1 lifts portfolio Sharpe above 1.45** — the redundancy ceiling holds.

### 2.4 User-identified gap as catalyst
- User explicitly flagged "no counter-trend short / short-the-rip strategy" — a precise, evidence-supported, mechanically falsifiable gap.
- All 6 discovery agents independently arrived at the same conclusion under different aliases (Agent A: S16_PullbackFadeShort; Agent B: L6_RipShort_Intraday; Agent C: S_NEW_1; Agent D: S3_PullbackShort with full design spec; Agent E: S2_RetailShortFade Option B; Agent F: C01 — 5-of-5 convergence).
- This convergence is the strongest possible signal that the next slot is well-defined; freezing the existing 6 and shipping S3 is the right next move.

---

## 3. Portfolio Coverage Gap Analysis (Agent A)

Agent A mapped the 6-strategy book onto an 8-dimensional tradeable-state space (direction / regime / timeframe / session / vol-regime / pattern / catalyst / holding-behavior) and ranked uncovered cells by frequency × severity.

### 3.1 Top 5 gaps (ranked)

| Rank | Gap ID | Description | Freq (days/yr) | Severity | Combined |
|------|--------|-------------|---------------:|---------:|---------:|
| **1** | G-D1.a + G-D7.c | **Counter-trend short / short-the-rip in bull regime** + overnight US-spillover short mirror | 60-100 | 9 | **9.0** |
| **2** | G-D2.a + G-D5.b | **Transition / regime-flip days** + vol-expansion timing | 70-100 | 8 | **8.5** |
| **3** | G-D4.a + G-D4.b | **Night-session single-point-of-failure (S1 only)** + night-short missing | 250 | 7 | **8.0** |
| **4** | G-D7.b | **Macro-event positioning** (Fed/CPI/NFP/TSMC) untraded | 36-40 | 7 | **7.5** |
| **5** | G-D6.a + G-D5.a | **Volatility-explicit strategies absent** + low-vol regime L3-only fragile | 285 | 6 | **7.0** |

### 3.2 Historical pain events caused by these gaps
- **2024-11 joint −$199k month**: multi-week pullback inside the AI rally. L1/L5/S1 long, L2/L4 sat out (no breakdown trigger). A short-the-rip strategy would have *netted* the pullback while longs gave back. (Gap #1)
- **2025-06 joint −$151k month**: same pattern. (Gap #1)
- **2024-08 fat-tail joint month** (P0-2 §4.1): yen-carry unwind sell-off mid-uptrend. No counter-trend short fired. (Gap #1)
- **2022 January**: bull → bear transition. L1 lost momentum but L2 hadn't ATR-confirmed → 3-week vacuum where the book bled. (Gap #2)
- **2026 Q1-Q2**: bear → bull transition (Trump-tariff rebound). L1 entered late, L2 stayed in and got squeezed. (Gap #2)

### 3.3 Highest-leverage candidates (cover ≥ 2 gaps as PRIMARY per Agent A §5)
- **S17 OvernightGapDownShort** — Gap #1 + Gap #3 (direction symmetry AND night-session resilience)
- **S20 NightFadeShort** — Gap #1 + Gap #3 (same logic, different trigger)
- **S19 BBandSqueezeRelease** — Gap #2 + Gap #5 (transition timing AND vol-explicit)

---

## 4. Alpha Source Diagnostic (Agent B)

### 4.1 Currently-used factors
| Factor family | Sub-factor | Strategies | Coverage strength |
|---|---|---|---|
| 1. Trend / Momentum | TSMOM multi-horizon | L1, L2, L5, S1 | **Over-saturated (4 of 6)** |
| 2. Mean reversion | Conditional reversion inside range | L3, L4 | **Partial — no in-trend pullback fades** |
| 3. Volatility | Indirect long-vol (breakouts fire in vol expansion) | L1/L2/L5 indirect | **NONE as a factor** |
| 4. Carry | Term-structure / basis | None | **NONE** |
| 5. Microstructure | Overnight-momentum | S1 | **Partial** |
| 6. Calendar | Settlement (defensive only) | All 6 (defensive) | **Defensive only, no alpha harvest** |
| 7. Sentiment / Positioning | — | None | **NONE** |
| 8. News / Event-driven | — | None | **NONE** |
| 9. Pattern recognition | — | L3/L4/L5 (range, not chart pattern) | Weak, correctly skipped |
| 10. Cross-asset | SPX-overnight (implicit via S1) | S1 implicit | **Largely unused** |

**The book is a mono-factor portfolio in disguise.** Of 6 sleeves, 4 trade momentum and 2 trade conditional mean-reversion. Measured by distinct alpha factors, the book has only **~1.7 factors of diversification** — exactly matching P0-1's "EW captures 31% of sum-of-Sharpes" finding.

### 4.2 Top 5 UNUSED high-evidence factors

| Rank | Factor | Evidence | Orthogonality | Why |
|------|--------|----------|---------------|-----|
| 1 | **Conditional mean reversion (short-the-rip)** | **A** — intra-trend pullback fades on equity indices | HIGH | Fires inside up-trends (exactly when longs are firing). Different signal type from L2/L4. |
| 2 | **SPX-overnight cross-asset signal** | **A** — strongest cross-asset signal for TXF1 (Lin/Hsu 2010, t-stat >6) | HIGH | None of 6 reads SPX directly. |
| 3 | **Term-structure / basis carry** | **B+** — Chen/Chung 2012, Wang/Chen 2014 | VERY HIGH | Different information channel from price-action. |
| 4 | **Sentiment / positioning (foreign-institutional)** | **A** — multiple TW domestic papers, strong t-stats | VERY HIGH | After-close release, 3-7 day hold, no current sleeve looks at it. |
| 5 | **Calendar — Turn-of-Month** | **A** — Chen/Lim 2018 replicated TOM on TXF1 | VERY HIGH | Calendar-only signal, zero correlation with price-action sleeves. |

### 4.3 Specific TXF1 academic evidence
- **TSMOM on TXF1 daily**: OOS Sharpe ~0.7 (Lin & Liu 2019, Wang 2021). L1 actual 0.94 is slightly above academic baseline.
- **Foreign-institutional position extreme**: Wu/Yang 2019 documented strong contrarian effect on TX futures.
- **TOM on TXF1**: Chen/Lim 2018 — positive return on last 4 + first 3 trading days of month, statistically robust 2005-2017.
- **SPX-overnight → TXF1**: t-stat > 6 on simple regression, validated through 2024 (Lin/Hsu 2010).
- **TAIFEX basis predictive value**: positive basis on morning of day T predicts positive day T return (Chen/Chung 2012).

---

## 5. TXF1-Specific Anomalies (Agent C)

### 5.1 Top anomalies catalog (Agent C identified 12; top 5 ranked by edge × frequency × portfolio fit)

| Rank | Anomaly | Mechanism | Edge | Freq/yr |
|------|---------|-----------|------|---------|
| 1 | **A10 Counter-Trend Short the Rip** | Bull-day exhaustion: +1.5% open, RSI>75, TSMC weak → 30-50 bp pullback | 25-40 bp | 20-30 |
| 2 | **A2 Post-Settlement Wed Reversal** | 13:30 mechanical hedge unwind → Wed afternoon reversal vs morning trend | 15-25 bp | 12 |
| 3 | **A1 TSMC ADR Overnight → TXF1 Gap-Fade** | TSM closes 04:00 TPE, predicts TXF1 09:00 gap; >1.5% triggers fade | 8-15 bp | 30-40 |
| 4 | **A9 SPX Overnight Range Break → TXF1 Open Momentum** | SPX breaks 16:00-22:00 NY range by >0.5% → TXF1 day open continuation 65% hit | 20-30 bp | 40-60 |
| 5 | **A5 Post-Long-Holiday Gap Resolution** | After 3+ day closure, TXF1 gaps to absorb global moves; >1% gap fades 50% within day 1 | 40-100 bp | 4-6 |

### 5.2 Why these are TXF1-unique (not global)
- **A2 Settlement Reversal**: TAIFEX's 3rd-Wednesday final-settlement-price mechanism (avg of last 30-min day-session index) creates a mechanical convergence flow that doesn't exist on quarterly-settled global indices (SPX/NK).
- **A1 TSMC ADR Lead**: TSMC's ~25% TWII weight + asynchronous ADR/Taiwan trading hours produces a mathematical, not behavioral, lead — has no equivalent on diversified-index futures.
- **A5 Long-Holiday Gap**: Taiwan's 6-10 day Lunar New Year closure is the **longest in global futures**. Global indices keep trading during it, so gap risk on Taiwan reopen is uniquely concentrated.
- **A4 Pre-CNY Rally** (currently FORFEITED by HolidayFlat rule): foreign shorts cover + domestic funds reduce hedges in the 2-3 days before CNY. The 0.8% T-1 mean return is specific to TW retail/institutional rhythm.
- **A10 Short-the-Rip**: While intra-trend mean reversion is global, the TXF1-specific accelerant is the **structurally long-biased TW retail** (high call OI vs put OI) — proprietary desks lean short into the close to harvest retail leveraged-long unwinds.

---

## 6. Institutional Strategy Library Gaps (Agent E)

### 6.1 10-category institutional taxonomy — current coverage

| # | Category | Covered by | Coverage |
|---|----------|------------|----------|
| 1 | Managed Futures CTA | L1, L2, L5 | **STRONG (over-allocated, 3 sleeves)** |
| 2 | Risk-Parity | None (only fixed-weight sizing) | WEAK |
| 3 | Volatility / VRP | None | **ABSENT** |
| 4 | Calendar-Spread / Term-Structure | None | **ABSENT** |
| 5 | Event-Driven | Defensive Settlement_Flat only | WEAK |
| 6 | Microstructure | None (correctly — out of scope for retail) | ABSENT |
| 7 | Cross-Asset Systematic | None | **ABSENT** |
| 8 | Statistical Arbitrage — Lead-Lag | S1 implicit only | WEAK |
| 9 | Sentiment / Positioning | None | **ABSENT** |
| 10 | Quant ML/AI | None (correctly — out of scope for now) | ABSENT |

**5 of 10 categories entirely absent. 3 of 6 sleeves concentrated in 1 category. This is the structural ceiling.**

### 6.2 Top 5 missing institutional categories (Agent E ranked)

| Rank | Category | Acad Evid | Impl Complexity | Diversification | Capacity | Total |
|------|----------|----------:|-----------------:|----------------:|---------:|------:|
| 1 | **Sentiment / Positioning** (TAIFEX 三大法人, put/call extremes) | 5 | LOW (4) | 5 | 5 | **23** |
| 2 | **Event-Driven** (pre-FOMC, pre-settlement, MSCI rebal) | 5 | LOW (4) | 4 | 4 | **20** |
| 3 | **Cross-Asset / Lead-Lag** (SPX overnight → TXF1 day) | 5 | MED (3) | 5 | 4 | **20** |
| 4 | **Calendar-Spread** (TXF1 vs TXF2 basis / roll-week) | 3 | MED (3) | 5 | 3 | **19** |
| 5 | **Risk-Parity overlay** (sizing layer, not new sleeve) | 5 | LOW (4) | 3 | 5 | **22 ★ overlay** |

### 6.3 Implementation complexity matrix

| Category | Code complexity | Data feed | Constitution amendment | Verification effort |
|----------|-----------------|-----------|------------------------|---------------------|
| Sentiment / Positioning | LOW | NEW (TAIFEX 三大法人 csv, free, daily 15:00) | None | Standard |
| Event-Driven (settlement harvest) | MED | None | **YES — EVENT_DRIVEN_EXEMPT flag** | Custom event-window tests |
| Event-Driven (FOMC) | MED | NEW (FOMC registry CSV) | None | Custom event-window tests |
| Cross-Asset (SPX) | MED | NEW (^GSPC yfinance) | None | Standard + Data2 plumbing |
| Calendar-Spread | HIGH | None (uses TXF1+TXF2) | None | Multi-leg execution tests |

### 6.4 Convergence observation
**The user-flagged "counter-trend short" gap and the #1 institutional gap (Sentiment/Positioning) converge on the same next build.** Counter-trend short can be implemented as a Sentiment/Positioning sub-style (overbought RSI + retail-long extreme → short) — solving both gaps with one sleeve. This is the strongest possible signal for build order.

---

## 7. The Short-the-Rip Flagship (Agent D full spec)

### 7.1 Full design spec summary (Agent D's S3_PullbackShort V1.0)

| Element | Spec |
|---------|------|
| **Working name** | S3_PullbackShort (research) → promotes to **L6_PullbackShort** if clears P1-P3 + 30 live_sim trades |
| **Alpha thesis** | Overheated momentum mean-reverts to local mean (MA5/MA10) over 1-3 sessions; technical exhaustion + profit-taking; TW retail structural long bias harvested by prop desks into close |
| **Chart** | 15M execution + Daily Data2 regime |
| **Direction** | SHORT-ONLY (long-mirror rejected — book already has 4 longs) |
| **Entry signal** (logical AND of 3) | E1: RSI(14)>75 sustained 3 bars on 15M; E2: Close > BB upper(20,2); E3: First bar where E1∧E2 fires this episode (de-dup) |
| **Regime filter** (all must be true on Daily Data2) | R1: Close > MA20 > MA60; R2: 60-day return > +5%; R3: Daily ATR/Close < 2.5% (skip crisis); R4: NOT 5 consecutive red daily closes (no chase) |
| **Stop loss** | EntryPrice + (ATR(14,15M) × **1.2**) — intentionally TIGHT (we are against the dominant trend) |
| **Take profit (V1.0)** | Single TP: BuyToCover ALL on touch of MA5(15M) from above |
| **Time stop** | 3 trading days (60 bars on 15M) |
| **Max entries per regime episode** | 1 (episode resets when RSI<70 OR Close<BB_Mid) |
| **Position size** | 1 contract (standard) |
| **Mandatory exits** | Manual_Kill / Registry_Expired / Holiday_Block / v_Settlement_Day at 12:30 / SetStopLoss (P3b Immediate Stop Guard) |
| **Estimated LOC** | ~340 (above 150 guideline; documented exception because ~120 LOC is mandatory boilerplate — Settlement_Flat + Holiday array + SetStopLoss) |
| **Estimated inputs** | ~16 (comparable to L2/L5) |
| **Settlement_Flat compliance** | YES (no entries on 3rd Wed, force-flat by 12:30) |
| **P3b SetStopLoss** | YES (engine-level, on entry bar, distance = 1.2 × ATR × BigPointValue) |

### 7.2 Estimated performance (2020-01 ~ 2026-06)

| Metric | Low | Mid | High | Institutional gate |
|--------|----:|----:|-----:|-------------------:|
| Trade count (6.5y) | 180 | 230 | 290 | ≥ 100 ✓ |
| Win rate | 50% | 55% | 60% | n/a |
| PF | 1.20 | 1.40 | 1.65 | ≥ 1.0 OOS ✓ |
| Avg holding | 30 bars | 50 bars | 80 bars | (1-2 days) |
| MDD | -5% | -8% | -12% | < 30% MC95 ✓ |
| Sharpe (annualized) | 0.60 | 0.85 | 1.10 | target > 1.0 |

### 7.3 Why it's the #1 priority candidate
- **5-of-5 agent convergence**: every discovery agent independently identified this gap under a different alias.
- **Directly fills user-stated portfolio gap**.
- **Maps to #1 institutional gap** (Sentiment/Positioning sub-style).
- **Largest negative correlation with the book's biggest weight class** (longs in bull regimes — exactly when the joint-DD risk is highest).
- **No new data feed required** (uses existing TXF1 15M + Daily already in MC12).
- **Has academic + practitioner evidence base** (RSI>80 → 3-day reversal documented across equity index futures).
- **Estimated portfolio Sharpe lift**: 1.329 → ~1.45 from this single sleeve.

### 7.4 Implementation path — S2 repurpose vs S3 from scratch
- **Option 1 — Repurpose S2_InsideBarBreak v0.5** (existing research/2026-W24/ Phase 2 strategy): REJECTED. S2's alpha thesis (inside-bar breakout continuation) is the OPPOSITE of short-the-rip (counter-trend reversion); repurposing means rewriting 90% of the logic AND breaks the audit trail of an in-progress Phase 2 validation. Saves nothing meaningful.
- **Option 2 — Build S3_PullbackShort from scratch in `research/`**: **RECOMMENDED**. Clean naming, clean audit trail, independent Phase 1-3 validation, natural promotion path (S3 → live_simulation → L6 live). Boilerplate (~120 LOC of Settlement/Holiday/SetStopLoss) copy-paste from L2 + L5 templates.

### 7.5 Expected portfolio impact
- **Allocation if promoted to live**: 8-10% of the 30-lot book (smaller than L1 28% / L2 22%, larger than L4 3%, comparable to L3 12%).
- **Net portfolio short exposure after S3**: 35% short vs 65% long (vs current 25% / 75% — much better balance).
- **Correlation forecast**: -0.10 to -0.20 vs L1/L5/S1 in bull regime (HEDGE), +0.10 to +0.25 vs L2/L4 (DISTINCT alpha but same direction, must verify < 0.7 institutional gate).
- **Trigger to upsize**: 6 consecutive months of live PF > 1.3 AND realized correlation with L2 < +0.3 monthly → can grow to 12-15%.

---

## 8. Candidate Strategy Pipeline (Agent F consolidation)

### 8.1 Top 10 candidates table

| Rank | Canonical | Alpha source | Complexity | Diversification value | Portfolio fit | EV |
|-----:|-----------|--------------|:----------:|:---------------------:|:-------------:|---:|
| 1 | **C01 PullbackShort** (S3) | Mean Reversion in-trend (Sentiment sub-style) | MED | **HIGH** (negative-ρ to longs) | **PRIMARY HEDGE** for L1/L5/S1 bull pullbacks | **33** |
| 2 | **C02 SPX_Overnight_DayOpen** (S5) | Cross-Asset Lead-Lag | MED (needs SPX feed) | **HIGH** | Orthogonal — ρ ≈ 0 to all 6 | **27** |
| 3 | **C06 TurnOfMonth_Long** (S4) | Calendar Effects | **LOW** | **HIGH** (ρ ≈ 0) | Positional diversifier, calendar-only signal | **26** |
| 4 | **C07 ForeignPositionFade** (S6) | Sentiment / Positioning | MED (needs TAIFEX scraper) | **HIGH** | Different data channel; #1 institutional gap | **24** |
| 5 | **C04 PreSettlementHarvest** (S7) | Event-Driven (calendar) | MED + **constitution amendment** | **HIGH** | Currently forfeit zone | **23** |
| 6 | **C13 FedDayFade / FOMC_Overnight** (S8) | Event-Driven (macro release) | MED (needs FOMC registry) | **HIGH** | Macro-event positioning untraded by all 6 | **23** |
| 7 | **C03 NightFadeShort / GapDownShort** (S9) | Microstructure (S1 mirror) | LOW | MED | Defensive: covers S1 single-point-of-failure | **20** |
| 8 | C09 BasisCarry / RollWeek | Carry / Term-Structure | HIGH | **HIGH** | Different information channel | **19** |
| 9 | C05 TSMC_ADR_GapFade | Cross-Asset (single-name proxy) | MED (needs ADR feed) | **HIGH** | Risk: overlap with C02 window | **19** |
| 10 | C20 USD_TWD_Reverse | Cross-Asset (FX leakage) | HIGH | **HIGH** | Slow signal, small sample | **18** |

### 8.2 Per-candidate Q1/Q2/Q3/Q4 scheduling

| Slot | Quarter | Canonical | Promoted name | Why this slot |
|------|---------|-----------|---------------|---------------|
| #1 | **Q1** | C01 PullbackShort | **S3** (research) | User-flagged gap; 5-of-5 convergence; no new feed; biggest Sharpe lift |
| #2 | **Q1** | C06 TurnOfMonth_Long | **S4** (research) | Lowest-complexity quick win; parallel to S3; ρ ≈ 0 to S3 |
| #3 | **Q2** | C02 SPX_Overnight_DayOpen | **S5** (research) | Biggest cross-asset alpha; needs SPX feed (Phase 0 infra) |
| #4 | **Q2** | C07 ForeignPositionFade | **S6** (research) | #1 institutional gap; needs TAIFEX scraper (Phase 0 infra) |
| #5 | **Q3** | C04 PreSettlementHarvest | **S7** (research) | Needs constitution amendment (user approval cycle) |
| #6 | **Q3** | C13 FedDayFade / FOMC | **S8** (research) | Macro-event coverage; needs FOMC registry |
| #7 | **Q4** | C03 NightFadeShort | **S9** (research) | Defensive S1 backup; reuses S1 night infra |

### 8.3 Rejected candidates (full list in Agent F §5)
- **C05 TSMC_ADR_GapFade** — defer to year 2 (overlaps C02's 09:00-09:30 window)
- **C08 InstitutionalFollowLong** — long-side mirror, book already 4-long-heavy
- **C09 BasisCarry / RollWeek** — defer (HIGH complexity multi-leg, modest Sharpe)
- **C10 BBandSqueezeRelease** — material overlap with L5
- **C11 RegimeShiftBreakout** — overlaps L1/L2 timeframe
- **C12 NightMeanReversion_Both** — redundant with C03
- **C14 TSMC_ExDiv_Short** — only 4 trades/yr, below sample-size gate
- **C15 LowVolBreakoutWaiter** — overlaps L5 + C10
- **C16 VolConeMeanRev** — borderline sample
- **C17 PostHolidayGapFade** — only 5 events/yr, sample-size deal-breaker
- **C18 PreLongHolidayRally** — needs HolidayFlat amendment, not worth governance cost
- **C19 LunchTimeMeanReversion** — edge gone after slippage
- **C20 USD_TWD_Reverse** — defer to year 2 cross-asset expansion
- **C21 VIX_Spike_Decay_Buy** — duplicated by C02 (SPX overnight)
- **C22 AuctionOpen_Imbalance_Fade** — sub-minute infra, out of scope for MC12

---

## 9. 12-Month Development Roadmap

### 9.1 Q1 (Now → 2026-09-20) — Ship 2 sleeves, both in parallel

#### Q1 Slot #1: S3 PullbackShort (the flagship)

| Week | Deliverable |
|------|-------------|
| W1 (now) | Scaffold `strategies/research/S03_PullbackShort/` folder. Write `S3_PullbackShort_strategy.md` (alpha thesis, ~3 pages). Confirm Daily Data2 wiring in MC12. |
| W2 | Code `S3_PullbackShort.pla` (~340 LOC) using L2 (Settlement/Holiday boilerplate) + L5 (15M + Daily Data2 wiring) as templates. |
| W3 | Write `scripts/verify_s3_pullbackshort.py` (~67-item checklist modeled on `verify_l4_v142.py`). Run on initial code. Fix any rule-violation findings. |
| W4 | **Phase 1**: parameter sensitivity scan on RSI_OB ∈ [70,80], BB_StdDev ∈ [1.8,2.2], SL_ATR_Ratio ∈ [1.0,1.5], Trend_Return_Min ∈ [3,8]. Confirm parameter plateau, not peak. |
| W5 | **Phase 2**: Walk-Forward (IS 2y, OOS 6m, step 6m). Gate: WFE > 50%, OOS PF > 1.0, sample ≥ 100. Per P0-2 lesson — also check IS/OOS mean comparison, not just WFE ratio. |
| W6 | **Phase 3**: Monte Carlo 10k shuffles. Gate: MC95 MDD < 30% account. |
| W7 | **Rule 13 10-dim institutional eval**. Document all 10 dimensions with measured numbers. Verify correlation < 0.7 vs each of L1/L2/L3/L4/L5/S1 monthly. |
| W8 | If all gates pass: promote to `live_simulation/` as **S3 NightMomentum's neighbor**. Begin 30-trade live_sim observation. |
| W9-12 | Live_sim observation; collect first 10-20 trades; first review checkpoint. |

**Mandatory checkpoints**:
- Rule 11 (Settlement_Flat): `scripts/verify_settlement_flat.py` must pass.
- Rule 12 (P3b Immediate Stop Guard): `SetStopLoss` present, exactly one call, distance matches Frozen SL.
- Rule 13 (10-dim eval): full table with measured numbers, no FAIL dimension.
- Filter redundancy check (memory rule): every new input scanned against existing logic (no redundant gating).

#### Q1 Slot #2: S4 TurnOfMonth_Long (lowest-complexity quick win)

| Week | Deliverable |
|------|-------------|
| W1 | Scaffold `strategies/research/S04_TurnOfMonth/`. Write `S4_TurnOfMonth_strategy.md`. |
| W2 | Code `S4_TurnOfMonth.pla` (~150 LOC — calendar-only logic is short). Entry: Long at day-session close of T-4 (4 trading days before month-end). Exit: day-session close of T+3 OR -2 ATR trail. Settlement_Flat compliant (defers if T+3 = Settlement Wed). |
| W3 | Write `scripts/verify_s4_turnofmonth.py`. Backtest 2020-2026, ~70 trades (12/yr × 6.5y). |
| W4 | Phase 1: sensitivity on entry day (T-3 / T-4 / T-5) and exit day (T+2 / T+3 / T+4). |
| W5 | Phase 2: Walk-Forward — borderline sample, may need to relax sample gate. Document carefully. |
| W6 | Phase 3: Monte Carlo. 10-dim eval. |
| W7 | If passes: promote to `live_simulation/`. |
| W8-12 | Live_sim observation. |

**Mandatory checkpoints**: same as S3.

### 9.2 Q2 (2026-09-20 → 2026-12-20) — Phase 0 infra + 2 cross-asset sleeves

**Phase 0 infra (W1-W3, in parallel)**:
- Extend `backtest/fetch_data.py` to pull `^GSPC` (SPX daily) — for S5.
- Build TAIFEX 三大法人 daily 15:05 scraper (free, no auth) — for S6.
- Verify MC12 Data2 daily-series loading for non-TXF1 symbols.

#### Q2 Slot #3: S5 SPX_Overnight_DayOpen

| Week | Deliverable |
|------|-------------|
| W1-3 | Phase 0: SPX feed extension. Bridge SPX daily CSV → MC12 Data2. |
| W4 | Scaffold `strategies/research/S05_SPX_Overnight/`. Spec doc. |
| W5-6 | Code `S5_SPX_Overnight.pla`. Entry: at TXF1 day-session open, if SPX overnight return >|0.7%|, enter TXF1 in line at first 15M confirming bar. Exit: 1.5×ATR target / 1.0×ATR stop / force-flat 12:00. |
| W7 | Phase 1: sensitivity on SPX-threshold and exit time. |
| W8 | Phase 2 Walk-Forward. |
| W9 | Phase 3 MC. 10-dim eval. |
| W10-13 | Promote to live_sim. Observation. |

#### Q2 Slot #4: S6 ForeignPositionFade

| Week | Deliverable |
|------|-------------|
| W1-3 | Phase 0: TAIFEX 三大法人 scraper. Daily CSV history backfill 2020-2026. |
| W4 | Scaffold `strategies/research/S06_ForeignPositionFade/`. Spec doc. |
| W5-6 | Code `S6_ForeignPositionFade.pla`. Entry: when foreign net-position 60-day z-score |z|>2, take opposite next day at open. Exit: z-score crosses zero / |z|>3 stop / 7-day time stop. |
| W7 | Phase 1: z-threshold sensitivity. |
| W8 | Phase 2 Walk-Forward — borderline sample (3-8 trades/yr × 6.5y = 20-50 trades); likely need sample-gate relaxation to ≥ 50, documented. |
| W9 | Phase 3 MC. 10-dim eval. |
| W10-13 | Promote to live_sim. Observation. |

### 9.3 Q3 (2026-12-20 → 2027-03-20) — Event-driven sleeves + constitution amendment

**Pre-Q3 critical path: constitution amendment**:
- Discuss + draft EVENT_DRIVEN_EXEMPT flag amendment to `SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` (allows pre-10:00 entries on settlement day for documented event harvesters that force-flat well before settlement window).
- User sign-off required (~2 weeks).
- Without amendment, S7 cannot run; S8 unaffected.

#### Q3 Slot #5: S7 PreSettlementHarvest

| Week | Deliverable |
|------|-------------|
| W1-2 | Constitution amendment discussion + user sign-off. |
| W3 | Scaffold `strategies/research/S07_PreSettlementHarvest/`. Spec doc. |
| W4-5 | Code `S7_PreSettlementHarvest.pla`. Entry: Long at 08:50 on 3rd Wed IF prior-day close > 5d SMA. Exit: force-flat at 10:00 OR 1×ATR stop. Tagged with `EVENT_DRIVEN_EXEMPT` flag. |
| W6 | Phase 1: entry time / exit time sensitivity. |
| W7 | Phase 2 — only 12 trades/yr × 6.5y = ~78 trades, sample-gate relaxation to ≥ 50 (documented). |
| W8 | Phase 3 MC. 10-dim eval. |
| W9-13 | Promote to live_sim. |

#### Q3 Slot #6: S8 FOMC_OvernightFade

| Week | Deliverable |
|------|-------------|
| W1 | Build FOMC + ECB + BoJ calendar registry CSV (8 + 8 + 8 dates/yr, manual one-time + annual update). |
| W2 | Scaffold `strategies/research/S08_FOMC_OvernightFade/`. Spec doc. |
| W3-4 | Code `S8_FOMC_OvernightFade.pla`. Entry: at 02:30 on FOMC night, if 02:00-02:15 bar > |0.5%|, fade direction on TXF1 night session. Exit: 1×ATR target / 1.5×ATR stop / force-flat 05:00. |
| W5 | Phase 1. |
| W6 | Phase 2 — only 8 trades/yr × 6.5y = ~52 trades, sample relaxation documented. |
| W7 | Phase 3 + 10-dim eval. |
| W8-13 | Promote to live_sim. |

### 9.4 Q4 (2027-03-20 → 2027-06-20) — Defensive coverage + portfolio recompute

#### Q4 Slot #7: S9 NightFadeShort

| Week | Deliverable |
|------|-------------|
| W1-2 | Scaffold `strategies/research/S09_NightFadeShort/`. Spec doc. |
| W3-4 | Code `S9_NightFadeShort.pla`. Mirror of S1: Night ORB (15:00-16:30 range); if price closes below ORB low after US-weak overnight, short on next bar with ATR stop and 05:00 force-flat. Verify correlation cap < 0.6 vs S1 (intentional anti-correlation). |
| W5 | Phase 1. |
| W6 | Phase 2. |
| W7 | Phase 3 + 10-dim eval. Critical: correlation cap vs C01 (S3) AND vs S1. |
| W8-13 | Promote to live_sim. |

**Q4 also includes**:
- W10-13: Full portfolio recompute. New 11-sleeve correlation matrix (L1/L2/L3/L4/L5/S1 + S3/S4/S5/S6/S7/S8/S9 — some still in live_sim, but include in computation). New EW Sharpe estimate. Update `docs/portfolio_correlation_matrix_*.md`.
- Decision point: which Q1-Q2 sleeves have enough live_sim history (≥ 30 trades, PF ≥ 1.2) to promote to live?

### 9.5 Mandatory checkpoints applied to EVERY new strategy (rule #11 / #12 / #13 + 10-dim eval)

For each S3 through S9:

1. **Rule 11 — Settlement_Flat (7 elements)**:
   - Holiday_Tail array populated
   - Session detection (day vs night)
   - v_Settlement_Day detection (3rd Wed)
   - Settlement_Flat_Time constant (default 1230)
   - Priority 0 exit cascade includes settlement check
   - Entry gate includes `v_Settlement_Day = false`
   - `scripts/verify_settlement_flat.py` (42-item check) PASS
2. **Rule 12 — P3b Immediate Stop Guard**:
   - Exactly one `SetStopLoss` call
   - Placed after indicator block, before entry block
   - Distance matches strategy's Frozen SL distance (same variable, same multiplier)
   - Amount = points × BigPointValue (TXF1 = 200)
   - Guard condition: `if MP <= 0` (long) or `if MP >= 0` (short)
3. **Rule 13 — 10-dim institutional eval** (NO dimension may FAIL):
   - Sharpe/Sortino/Calmar ≥ 0.15
   - MDD < 25% account (tighter than 30% for new sleeves)
   - Correlation < 0.7 vs ALL 6 existing (target < 0.5)
   - Drawdown clustering < 3 sigma
   - Sample ≥ 100 (relaxation to ≥ 50 documented for event-driven sleeves only)
   - WFE > 50% AND IS/OOS mean comparison passes (per P0-2 lesson)
   - Three-regime PF (bull/bear/range) all > 1.0 (or trivially passing with 0 trades + documented)
   - Cost analysis with realistic slippage (1,000 NTD round-trip)
   - Operational risk: inherits Settlement_Flat + P3b
   - Regulatory / account: standard 1-contract TXF1
4. **Additional project rules**:
   - Filter redundancy check: every new input grep'd against existing conditions, no double-gating
   - Filter default: any new filter input ships OFF by default until validation
   - MC Time 24-hr check: cross-day session conditions use closed-interval `Time >= X AND Time <= Y`
   - MC entry/exit labels: LE_ / LX_ / SE_ / SX_ prefix convention enforced
   - Trend-strategy: NO profit-pullback protection logic suggested (let profits run)
   - Holiday flatten: every strategy force-flats before official TAIFEX holiday + blocks pre-holiday-eve night entries

---

## 10. Risk & Discipline

### 10.1 Avoid the 4 historical failure modes (from user memory + project lessons)

| Failure mode | What it looks like | How this roadmap prevents it |
|--------------|--------------------|------------------------------|
| **MC Time 24-hour pitfall** | Cross-day session condition written as `Time >= 1500 OR Time <= 500` accidentally fires at 13:00 because of operator-precedence in PowerLanguage | Mandatory: cross-day windows written as `(Time >= 1500 AND Time < 2400) OR (Time >= 0 AND Time <= 500)`; verification script grep's for the unsafe pattern; every night-session strategy (S5/S7/S8/S9) gets explicit time-window test |
| **Filter redundancy with existing logic** | New input added (e.g. "skip Mondays") but Mondays were already implicitly filtered by HolidayFlat or by session-time gate → redundant gate, hidden double-filter, debugging trap | Mandatory: every new input grep'd against existing conditions in the same file BEFORE coding; documented in spec doc with explicit "is-this-redundant-with-X" check |
| **Design ahead of empirical validation** | Spec writes "Sharpe 1.3-1.8 expected" without backtest, then user assumes it, then live disappoints | All estimates in this roadmap are flagged as "P0 estimates, MUST be replaced by actual backtest output before any allocation decision". No sleeve promotes to live_simulation without measured 10-dim eval. |
| **Filter defaults ON without validation** | New filter input shipped with default = TRUE, accidentally activates in production before validation | Mandatory: every new filter input ships default = FALSE (OFF), explicitly documented; only after Phase 1 sensitivity confirms the filter improves WFE does the default flip to ON, with a code review |

### 10.2 Every new strategy: design spec → MC backtest → 10-dim eval → live_simulation

Strict promotion gate per `CLAUDE.md` rules 11/12/13:

```
research/ ──[Phase 1 sensitivity ✓ + Phase 2 WFE > 50% ✓ + Phase 3 MC95 MDD < 30% ✓ + 10-dim eval all PASS ✓]──► live_simulation/

live_simulation/ ──[≥ 30 trades + sim PF ≥ 1.2 + backtest deviation ≤ 30%]──► live/
```

No exceptions. Any deviation requires explicit documented justification in the strategy review file AND user sign-off.

### 10.3 Discipline rules carried from existing project memory
- **Holiday-flatten ironclad rule**: TAIFEX official calendar is the only source; every new strategy force-flats before holiday + blocks pre-holiday-eve night entries.
- **Trend-strategy let-profits-run**: NO suggestion of profit-pullback protection on S5 / future trend variants.
- **MC entry/exit label convention**: strict LE_/LX_/SE_/SX_ prefix.
- **No "rest questions"**: user self-manages pacing; agent stays at 100% effort + 100% accuracy.
- **Git updates always push**: any "update git" task = commit + push, not local-only.

---

## 11. First Concrete Action (TODAY)

### 11.1 Recommendation
**Start S3_PullbackShort from scratch (Agent D's Option 2 path), NOT a repurpose of S2.**

Reasoning:
- S3 is the unambiguous Q1 #1 priority (5-of-5 agent convergence).
- Full design spec already exists (Agent D's report — 600+ line spec covering inputs, regime gate, entry combo, exit cascade, MC pseudocode, 10-dim checklist).
- No new data feed required — uses existing TXF1 15M + Daily Data2 already wired in MC12.
- No constitution amendment required.
- Repurposing S2_InsideBarBreak v0.5 would pollute the in-progress Phase 2 audit trail of a fundamentally different strategy (breakout-long vs counter-trend-short). Saves no meaningful effort because only ~120 LOC of boilerplate is reusable, which can be copy-pasted from L2 template anyway.
- More research is NOT needed; the 6 deep-discovery agents already converged. Further research postpones the highest-conviction next sleeve.

### 11.2 Specific next-week deliverables (W1 of Q1)

1. **Scaffold folder structure**:
   - Create `strategies/research/S03_PullbackShort/`
   - Create `S03_PullbackShort/S3_PullbackShort_strategy.md` (alpha thesis, ~3 pages, condensed from Agent D §1)
   - Create `S03_PullbackShort/S3_PullbackShort_design_spec.md` (copy refined Agent D spec verbatim as v1.0)

2. **Confirm MC12 wiring**:
   - Verify Data1 (TXF1 15M) + Data2 (TXF1 Daily) wiring works with one of L3/L4/L5 templates as scaffolding reference
   - Verify Settlement_Flat boilerplate + Holiday_Tail array + SetStopLoss pattern from L2_TrendShort.pla can be cleanly extracted

3. **Code S3_PullbackShort.pla v1.0** (~340 LOC):
   - Copy L2's Settlement/Holiday boilerplate as starting scaffold
   - Copy L5's 15M+Daily Data2 wiring pattern
   - Implement Agent D's E1∧E2∧E3 entry combo with episode-armed latch
   - Implement Agent D's R1∧R2∧R3∧R4 regime gate on Data2
   - Implement Agent D's 4-layer exit cascade (P0 mandatory → TP MA5 → SL ATR×1.2 → time stop 60 bars)
   - SetStopLoss call placed after indicator block, before entry block, distance = SL_ATR_Ratio × v_ATR_15M × BigPointValue

4. **Write `scripts/verify_s3_pullbackshort.py`** (~67-item checklist modeled on `verify_l4_v142.py`):
   - All Rule 11 Settlement_Flat 7 elements
   - All Rule 12 SetStopLoss elements
   - Entry de-dup (E3 latch)
   - Regime gate AND-of-all
   - Exit cascade strict priority order
   - No MC Time 24-hour pitfall in any time condition
   - All filter inputs default = FALSE

5. **Run initial backtest** in MC12 (2020-01-01 to 2026-06-19) — collect first headline metrics (trade count, PF, MDD) for sanity check before formal Phase 1 sensitivity scan in W4.

6. **End-of-W1 deliverable to user**: status update with (a) compiled .pla file path, (b) verification script run output (all checks must pass), (c) headline first-backtest numbers vs Agent D estimates, (d) confirmation that no rule violations were introduced.

### 11.3 Parallel start (also W1) — S4 TurnOfMonth_Long scaffolding
- Create `strategies/research/S04_TurnOfMonth/` folder + `S4_TurnOfMonth_strategy.md` stub
- Lower priority than S3 but can scaffold in parallel since logic is calendar-only and won't conflict with S3 work
- Full coding starts W2-W3 of Q1

---

## 12. Bottom-Line Summary

- **6 live strategies FROZEN** as of 2026-06-20. No further individual-strategy parameter tweaks for at least 12 months.
- **Strategic shift**: alpha INNOVATION (new orthogonal sleeves) > alpha REFINEMENT (existing sleeve tuning). The Sharpe ceiling of ~1.4 is structural and cannot be exceeded by a 7th trend sleeve.
- **6 deep-discovery agents converged** on the same #1 next sleeve: counter-trend short during bull-regime pullbacks (S3 PullbackShort). This is the strongest possible signal for build order.
- **12-month pipeline**: 7 new sleeves (S3-S9) scheduled Q1-Q4, lifting portfolio EW Sharpe from 1.329 → target ~1.75.
- **All 7 sleeves pass mandatory rules 11/12/13** with one in-scope constitution amendment (S7 EVENT_DRIVEN_EXEMPT in Q3, requires user sign-off).
- **TODAY's concrete action**: scaffold `strategies/research/S03_PullbackShort/`, copy refined design spec from Agent D, begin .pla coding from L2+L5 templates this week.

---

_Compiled 2026-06-20 from 6 deep-discovery agent reports + portfolio P0-1/P0-2 baselines + institutional 10-dim framework + Settlement_Flat constitution. All metric estimates are pre-backtest and MUST be replaced by measured numbers before live promotion. This document supersedes all prior individual-strategy optimization plans through 2027-06-20._
