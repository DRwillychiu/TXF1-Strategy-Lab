# TXF1 Candidate Strategy Pipeline — Unified Consolidation

- **Date**: 2026-06-19
- **Purpose**: Merge 5 deep-discovery reports into one ranked development pipeline
- **Source reports**:
  1. `_temp_coverage_gap.md` (Agent A — 8-dim coverage gap, 10 candidates S16-S25)
  2. `_temp_alpha_taxonomy.md` (Agent B — 10 factor families, 5 candidates L6/L8/L10/L11/L13)
  3. `_temp_txf_anomalies.md` (Agent C — 12 TXF-native anomalies, 5 candidates S_NEW_1..5)
  4. `_temp_short_rip_design.md` (Agent D — full S3 PullbackShort design spec)
  5. `_temp_institutional_lib.md` (Agent E — 10-cat institutional library, 6 candidates S2-S7)
- **Frozen base**: L1 TrendLong, L2 TrendShort, L3 ConsolidationLong, L4 ConsolidationShort, L5 BreakoutLong, S1 NightMomentum

---

## 1. Methodology

### 1.1 Consolidation steps

1. **Extract**: Pull every named candidate from the 5 reports → raw list of 38 entries.
2. **De-duplicate**: Cluster candidates that are mechanically identical or trivially mergeable. Each cluster becomes ONE unique candidate. Different reports used different naming (e.g. agent D's S3_PullbackShort = agent A's S16_PullbackFadeShort = agent B's L6_RipShort_Intraday = agent C's S_NEW_1 = agent E's S2_RetailShortFade option B); these collapse into a single canonical entry.
3. **Re-name**: Adopt one canonical naming. Use `C##_ShortName` to distinguish CANDIDATE pool from live (L#), live_sim (S1), and the research folder convention. Final promoted names will follow project convention later.
4. **Classify**: Assign each candidate's primary alpha source per Agent B's 10-family taxonomy, plus implementation complexity and diversification value.
5. **Score**: Combined-EV ranking. Formula:
   ```
   EV_score = (Diversification × 3) + (Evidence × 2) + (Capacity × 1)
              − (Complexity × 2) − (Overlap_with_existing_6 × 2)
              + UserGap_bonus (3 if directly addresses Short-the-Rip)
              + Convergence_bonus (1 per additional report that named it)
   ```
   Each axis scored 1-5. Maximum theoretical score ≈ 35.
6. **Recommend**: Top 7 placed onto Q1-Q4 schedule based on prerequisite chain (data feeds, infra, constitution amendments) and parallelizability.

### 1.2 Mandatory rule #11/12/13 compliance gate

Every candidate is pre-screened for:
- **Rule 11** — must include Settlement_Flat module (7 elements)
- **Rule 12** — must include P3b Immediate Stop Guard (`SetStopLoss`)
- **Rule 13** — must pass institutional 10-dim eval before live_simulation

Special-case: candidates that explicitly TRADE settlement-day or holiday-tail edges (e.g. PreSettlementDrift, PreHolidayRally) need a documented constitution exemption flag (`EVENT_DRIVEN_EXEMPT`) — flagged in the table.

---

## 2. Full candidate list — all 22 unique candidates after de-dup

### 2.1 De-duplication map (38 raw → 22 unique)

| Canonical | Source aliases (across 5 reports) | Notes |
|-----------|-----------------------------------|-------|
| **C01 PullbackShort** | A:S16_PullbackFadeShort, B:L6_RipShort_Intraday, C:S_NEW_1 L6_PullbackShort, D:S3_PullbackShort, E:S2_RetailShortFade (Option B) | **5-of-5 convergence**. The user-flagged short-the-rip. Agent D has full design spec. |
| **C02 SPX_Overnight_DayOpen** | A:— (not named), B:L13_SPX_Overnight_Aligner, C:S_NEW_4 X2_SpxOvernightContinuation, E:S6_SPXLeadLag_DayOpen | 3-of-5 convergence. SPX→TXF1 day-open momentum carry. |
| **C03 NightFadeShort / NightGapDownShort** | A:S17_OvernightGapDownShort + S20_NightFadeShort | Both fire on US-weak nights; A flagged them as cannibalizing. Merge into one bidirectional spec. |
| **C04 PreSettlementHarvest** | A:— (Settlement_Flat noted as forfeit), C:S_NEW_2 L7_SettlementReversal, E:S4_PreSettlementDrift | 3-of-5 convergence. Needs constitution exemption. |
| **C05 TSMC_ADR_GapFade** | A:— (not in scope), C:S_NEW_3 X1_TsmcAdrGapFade | TSM ADR overnight → TXF1 09:00 gap fade. |
| **C06 TurnOfMonth_Long** | A:— (noted under D7 calendar but no candidate), B:L10_TurnOfMonth_Long, E:— | Calendar overlay. Zero-corr diversifier. |
| **C07 ForeignPositionFade** | B:L11_ForeignPositionFade, E:S2_RetailShortFade (Option A positioning sub-style), E:S3_InstitutionalFollowLong (mirror direction) | Merge B+E Option A. Mirror long (S3) split to C08. |
| **C08 InstitutionalFollowLong** | E:S3_InstitutionalFollowLong only | Long-side counterpart to C07; kept separate because direction + horizon differ. |
| **C09 BasisCarry_Intraday** | B:L8_BasisCarry_Intraday, E:S7_RollWeekBasisTrade (different mechanism — calendar spread) | Both use TXF basis. B is intraday TXF1-vs-TWSE-cash. E is TXF1-vs-TXF2 calendar spread. Kept as ONE entry for ranking — split in implementation if both pass triage. |
| **C10 BBandSqueezeRelease** | A:S19_BBandSqueezeRelease only | Vol-expansion timing, direction-agnostic. |
| **C11 RegimeShiftBreakout** | A:S18_RegimeShiftBreakout only | 60-day MA slope flip + ATR percentile gate. |
| **C12 NightMeanReversion_Both** | A:S21_NightMeanReversionBoth + C:A3 (Night Dead-Zone Mean Reversion) — A3 not given a named candidate by C | 2-of-5 convergence. Bidirectional night fade, defensive vs S1 single-point risk. |
| **C13 FedDayFade / FOMC_Overnight** | A:S22_FedDayFade, E:S5_FOMCOvernightFade | Both fade post-FOMC initial move. Merge. |
| **C14 TSMC_ExDiv_Short** | A:S23_TSMCExDivShort only | TSMC ex-div day mechanical short. 4 trades/yr. |
| **C15 LowVolBreakoutWaiter** | A:S24_LowVolBreakoutWaiter only | Wait for first ATR>75pct bar after low-vol regime. |
| **C16 VolConeMeanRev** | A:S25_VolConeMeanRev only | Fade post-vol-spike extreme back to mean. |
| **C17 PostHolidayGapFade** | C:S_NEW_5 H1_PostHolidayGapFade only | Post-CNY/long-holiday gap fade. ~5 events/yr. |
| **C18 PreLongHolidayRally** | C:A4 (Pre-Long-Holiday Rally) — not named as candidate | 2 days before CNY/National long. Currently FORFEITED by HolidayFlat. Needs exemption. |
| **C19 LunchTimeMeanReversion** | C:A7 (Lunch Volatility Compression) — not named as candidate | 11:30-12:30 range fade. Very small edge per trade. |
| **C20 USD_TWD_Reverse_Day** | A:— (noted under D-cross-asset but no candidate), B:L14_USD_TWD_Multiday, C:A8 (USD/TWD Big Move) | 2-of-5. FX leakage signal. |
| **C21 VIX_Spike_Decay_Buy** | C:A11 (VIX Spike Decay) only | External vol spike → next-day TXF1 mean-reversion long. |
| **C22 AuctionOpen_Imbalance_Fade** | C:A12 (Auction Open Spike Fade) only | 08:45 open spike fade. Very short hold. |

**Discarded (raw items not promoted to candidate level)**:
- Agent E's RP1_InverseVolRebalancer — overlay/sizing layer, not a strategy. Recommended separately, not in this pipeline.
- Agent B's "Last-Bar Imbalance Signal" — explicitly described as S1 enhancement, not a sleeve.
- Agent B's "Short-Straddle Overlay" — out of futures-only scope.
- Agent A's pattern recognition (signal #5 single candle) — agent A itself rejected.
- Agent C's A6 (Month-End Window Dressing) — partially overlaps C06 TurnOfMonth, merged into C06.

### 2.2 Full classification table (22 candidates)

| # | Canonical name | Primary alpha source (per Agent B taxonomy) | Direction | Horizon | Complexity | Diversification | Overlap w/ 6 | Rule 11/12/13 | UserGap | Convergence count |
|---|----------------|---------------------------------------------|-----------|---------|:----------:|:----------------:|:------------:|:--------------:|:-------:|:-----------------:|
| C01 | PullbackShort (short-the-rip) | Mean Reversion (conditional, in-trend) | Short | 1-3 days | MED | **HIGH** | LOW (negative-ρ to L1/L5/S1) | OK + std rules apply | **YES** | **5** |
| C02 | SPX_Overnight_DayOpen | Cross-Asset / Statistical Arbitrage (lead-lag) | Both | Intraday (<2h) | MED (needs SPX feed) | **HIGH** | LOW (ρ ≈ 0 to all) | OK + std | partial | 3 |
| C03 | NightFadeShort / NightGapDown | Liquidity / Microstructure (mirror of S1) | Short | Intraday-night | LOW | MED | MED (anti-correlated with S1, but same session) | OK + std | partial | 2 |
| C04 | PreSettlementHarvest | Event-Driven (calendar) | Both | Intraday | MED | **HIGH** | LOW (constitution forfeits this window) | NEEDS EXEMPTION on rule 11 | NO | 3 |
| C05 | TSMC_ADR_GapFade | Cross-Asset (lead-lag, single-name proxy) | Both (fade) | 30 min | MED (needs ADR feed) | **HIGH** | LOW | OK + std | NO | 1 |
| C06 | TurnOfMonth_Long | Calendar Effects | Long | 5-7 days | **LOW** | **HIGH** (ρ ≈ 0) | LOW (positional, no price-action signal) | OK + std | NO | 1 |
| C07 | ForeignPositionFade | Sentiment / Positioning | Both | 2-7 days | MED (needs TAIFEX 三大法人 scraper) | **HIGH** | LOW | OK + std | partial | 2 |
| C08 | InstitutionalFollowLong | Sentiment / Positioning | Long | 1-3 days | MED (needs same scraper) | MED (ρ ≈ 0.2 to L1) | LOW | OK + std | NO | 1 |
| C09 | BasisCarry / RollWeek | Carry / Term-Structure | Both | Intraday-3day | HIGH (Data2 cash index OR multi-leg) | **HIGH** | LOW | OK + std | NO | 2 |
| C10 | BBandSqueezeRelease | Volatility (long vol breakout) | Both | 1-3 days | LOW | MED | MED (overlaps L5 box breakout family) | OK + std | NO | 1 |
| C11 | RegimeShiftBreakout | Trend / Momentum (regime-flip filter) | Both | 1-3 weeks | MED | MED | MED (overlaps L1/L2 timeframe) | OK + std | NO | 1 |
| C12 | NightMeanReversion_Both | Mean Reversion (intra-session) | Both | <4 hours | LOW | MED | MED (S1 fires opposite regime) | OK + std | NO | 2 |
| C13 | FedDayFade / FOMC_Overnight | Event-Driven (macro release) | Both (fade) | <2 hours | MED (needs FOMC registry) | **HIGH** | LOW | OK + std | NO | 2 |
| C14 | TSMC_ExDiv_Short | Event-Driven (calendar, mechanical) | Short | Intraday | LOW | MED (low-N, 4/yr) | LOW | OK + std | NO | 1 |
| C15 | LowVolBreakoutWaiter | Volatility (post-contraction expansion) | Both | 1-2 days | MED | MED | MED (overlaps L5) | OK + std | NO | 1 |
| C16 | VolConeMeanRev | Volatility (post-spike fade) | Both | 1-3 days | MED | MED | LOW | OK + std | NO | 1 |
| C17 | PostHolidayGapFade | Event-Driven (calendar) | Both (fade) | Intraday | LOW | MED (low-N, 5/yr) | LOW | OK + std | NO | 1 |
| C18 | PreLongHolidayRally | Calendar Effects | Long | 1-2 days | LOW | MED | MED (currently blocked by HolidayFlat) | NEEDS EXEMPTION on holiday-flat rule | NO | 1 |
| C19 | LunchTimeMeanReversion | Microstructure (low-vol session) | Both | 30-60 min | LOW | LOW | LOW | OK + std | NO | 1 |
| C20 | USD_TWD_Reverse_Day | Cross-Asset (FX leakage) | Both | 1-3 days | HIGH (needs FX feed) | **HIGH** | LOW | OK + std | NO | 3 |
| C21 | VIX_Spike_Decay_Buy | Volatility (post-spike fade, cross-asset) | Long | 1-day | MED (needs VIX feed) | MED | LOW | OK + std | NO | 1 |
| C22 | AuctionOpen_Imbalance_Fade | Microstructure (open auction) | Both (fade) | 15-30 min | HIGH (5M execution, low edge per trade) | LOW | LOW | OK + std | NO | 1 |

### 2.3 EV scoring (top 12 shown; full computation in Appendix)

Scoring axes 1-5 (5 = best). Formula in §1.1.

| # | Candidate | Div | Evid | Cap | Cplx | Ovlp | UserGap | Conv | **EV** |
|---|-----------|----:|-----:|----:|-----:|-----:|--------:|-----:|-------:|
| C01 | PullbackShort | 5 | 5 | 4 | 3 | 1 | +3 | +4 | **33** |
| C02 | SPX_Overnight_DayOpen | 5 | 5 | 4 | 3 | 1 | 0 | +2 | **27** |
| C06 | TurnOfMonth_Long | 5 | 5 | 5 | 1 | 1 | 0 | 0 | **26** |
| C07 | ForeignPositionFade | 5 | 5 | 5 | 3 | 1 | 0 | +1 | **24** |
| C04 | PreSettlementHarvest | 5 | 4 | 4 | 3 | 1 | 0 | +2 | **23** |
| C13 | FedDayFade / FOMC | 5 | 5 | 4 | 3 | 1 | 0 | +1 | **23** |
| C03 | NightFadeShort | 4 | 4 | 4 | 2 | 3 | 0 | +1 | **20** |
| C09 | BasisCarry | 5 | 4 | 4 | 5 | 1 | 0 | +1 | **19** |
| C05 | TSMC_ADR_GapFade | 5 | 3 | 4 | 3 | 1 | 0 | 0 | **19** |
| C20 | USD_TWD_Reverse | 5 | 3 | 4 | 5 | 1 | 0 | +2 | **18** |
| C16 | VolConeMeanRev | 3 | 4 | 4 | 3 | 1 | 0 | 0 | **17** |
| C12 | NightMeanReversion_Both | 3 | 3 | 4 | 2 | 3 | 0 | +1 | **16** |

---

## 3. Top 10 ranked with rationale

| Rank | Candidate | EV | Rationale |
|-----:|-----------|---:|-----------|
| **1** | **C01 PullbackShort** | 33 | **5-of-5 convergence**. Directly solves user-identified gap. Negatively correlated with the 4 long sleeves in bull-regime pullbacks (the book's biggest open-trade DD source). Agent D already wrote full design spec (340 LOC, S3 working name). No new data feed required. Tight 1.2× ATR SL keeps tail risk in check. The single highest-EV candidate by a wide margin. |
| **2** | **C02 SPX_Overnight_DayOpen** | 27 | 3-of-5 convergence + grade-A academic evidence (Lin-Sun 2018, Lucca-Moench framework). ρ ≈ 0 to all 6 (no current sleeve reads SPX). Captures the SAME mechanism Agent C ranked #4 (SPX overnight range break) and Agent E ranked #3 (SPX→TXF1 lead-lag). Needs SPX daily feed via `^GSPC` yfinance extension — LOW infra cost. |
| **3** | **C06 TurnOfMonth_Long** | 26 | Lowest-complexity candidate in the pool. Grade-A evidence (Chen-Lim 2018 specifically replicated TOM on TXF1). Near-zero correlation with everything because the signal is calendar-only, no price action read. Standalone Sharpe is modest (0.4-0.7) but EV-per-LOC is the highest in the list. Ideal early-quarter ship. |
| **4** | **C07 ForeignPositionFade** | 24 | Maps to Agent E's #1 ranked institutional gap (Sentiment/Positioning). TAIFEX 三大法人 csv is free, daily, never-used by current book. Different data channel = different alpha decay curve. Frequency is low (3-8 trades/yr at |z|>2 cutoff) so sample-size gate (≥100 over 6.5y) is borderline — must validate Phase 1. |
| **5** | **C04 PreSettlementHarvest** | 23 | 3-of-5 convergence. Documented edge (Lucca-Moench analogue + TXF settlement microstructure). BUT requires SETTLEMENT_DAY_DESIGN_CONSTITUTION amendment (adds `EVENT_DRIVEN_EXEMPT` flag for documented event harvesters). Amendment requires user approval. Quarantine until rule 11 path is clarified. |
| **6** | **C13 FedDayFade / FOMC** | 23 | Strongest event-driven evidence in literature. Low trade count (~8/yr) caps standalone Sharpe contribution but ρ ≈ 0 to everything makes it valuable as portfolio insurance on macro nights. Combines two reports' candidates (A:S22 + E:S5) into one execution. |
| **7** | **C03 NightFadeShort** | 20 | Defensive value: covers two gaps (D1.a short-the-rip mirror + D4.a S1 single-point-of-failure). Lower upside than C01 because intra-night reversal is noisier than daily-regime-gated pullback short. Lower complexity though, and Agent A flagged both Q-versions (S17 + S20) as essentially the same idea. |
| **8** | **C09 BasisCarry / RollWeek** | 19 | Strong orthogonality (carry is a different information channel) but HIGH complexity — either needs cash-index Data2 alignment (intraday version) or multi-leg execution (calendar-spread version). Defer until other low-complexity wins are deployed. |
| **9** | **C05 TSMC_ADR_GapFade** | 19 | Clean cross-asset edge (TSMC = 25% of TWII). Needs ADR data feed setup, which Agent C estimated as medium effort. Risk: the 09:00-09:30 window is also where C02 (SPX_Overnight_DayOpen) fires — potential overlap requiring precedence rule. |
| **10** | **C20 USD_TWD_Reverse** | 18 | Grade-B evidence (FX leakage), high diversification, BUT high complexity (needs reliable FX feed + slow signal = small sample). Defer to V2.0 of cross-asset suite (after C02 proves the SPX-feed pattern works). |

Candidates 11-22 are deferred or rejected — see §5.

---

## 4. TOP 7 development pipeline — Q1/Q2/Q3/Q4 schedule

Schedule logic:
- **Q1**: Highest-EV + lowest-complexity-or-prerequisite candidates. Ship 2 in parallel.
- **Q2**: Build on Q1 infrastructure (TAIFEX scraper, SPX feed). Ship 2.
- **Q3**: Constitution-amendment-dependent items (event-driven) — after user approval cycle.
- **Q4**: Larger-infra items (cross-asset multi-feed) once base patterns are proven.

| Slot | Quarter | Candidate | Why this slot | Prerequisites | Target promotion gate |
|------|---------|-----------|---------------|---------------|------------------------|
| **#1** | **Q1** | **C01 PullbackShort** | THE user-flagged gap; 5-of-5 convergence; Agent D has full spec; no new data feed; biggest single Sharpe lift | None (uses existing TXF1 + daily Data2 already in MC12) | Phase 1-3 within Q1; promote to live_sim by end of Q1 |
| **#2** | **Q1** | **C06 TurnOfMonth_Long** | Lowest-complexity quick win; parallel to #1 because no shared infra; ZERO correlation with C01; great Q1 confidence-builder | None | Phase 1-3 within Q1; promote to live_sim by end of Q1 |
| **#3** | **Q2** | **C02 SPX_Overnight_DayOpen** | Biggest cross-asset alpha; requires SPX feed extension to `fetch_data.py` (medium build) | Phase 0 deliverable: extend `fetch_data.py` for `^GSPC`; verify Data2 daily-series in MC12 for non-TXF1 symbol | Phase 1-3 within Q2; promote to live_sim by end of Q2 |
| **#4** | **Q2** | **C07 ForeignPositionFade** | Maps to #1 institutional gap; TAIFEX scraper build runs in parallel with SPX feed; orthogonal data channel | Phase 0 deliverable: daily 15:05 scraper for 三大法人 csv (free, no auth) | Phase 1-3 within Q2; cautious — sample-size near threshold |
| **#5** | **Q3** | **C04 PreSettlementHarvest** | Needs SETTLEMENT_DAY_DESIGN_CONSTITUTION amendment (user approval) — Q3 allows time for amendment discussion + implementation; high standalone Sharpe in literature | Phase 0: constitution amendment introducing `EVENT_DRIVEN_EXEMPT` flag; user sign-off | Phase 1-3 within Q3; sample-size gate may need relaxation to ≥50 trades for event-driven |
| **#6** | **Q3** | **C13 FedDayFade / FOMC** | Same EV as C04, parallel-ship; needs FOMC registry CSV (8 dates/yr, manual annual update); shares event-driven validation framework with C04 | Phase 0: FOMC + ECB + BoJ calendar registry CSV (manual one-time build) | Phase 1-3 within Q3; sample-size relaxation likely needed |
| **#7** | **Q4** | **C03 NightFadeShort** | Defensive: covers S1 single-point-of-failure; deployment late means C01 + C02 have already populated short-side coverage, so urgency is lower; LOW complexity makes it a Q4-finisher | None (reuses S1 night-session infra) | Phase 1-3 within Q4; correlation-cap vs C01 + S1 must be verified |

### 4.1 Pipeline dependency graph

```
Q1: [C01 PullbackShort]   [C06 TurnOfMonth]
        |                       |
        |                       |
Q2: [C02 SPX_Overnight]   [C07 ForeignPositionFade]
        |     (SPX feed)        |     (TAIFEX scraper)
        |                       |
Q3: [C04 PreSettlementHarvest]  [C13 FOMC_Fade]
        |     (constitution     |     (FOMC registry)
        |      amendment)       |
        |                       |
Q4: [C03 NightFadeShort]
        (reuse S1 night infra)
```

### 4.2 Resource commitments per quarter

- **Q1**: ~6 weeks for C01 (per Agent D Phase 1-3 plan) + ~2 weeks for C06 (calendar-only).
- **Q2**: ~3 weeks Phase 0 infra (SPX feed + TAIFEX scraper) + 6 weeks parallel sleeve dev.
- **Q3**: ~2 weeks constitution amendment cycle (discussion + sign-off) + 6 weeks parallel sleeve dev.
- **Q4**: ~4 weeks C03 (reuses infra) + slack time for live_sim observation of Q1-Q3 promotions.

### 4.3 Mid-cycle review checkpoints

- End-Q2: Review C01 + C06 30-trade live_sim performance. Decide whether to upsize allocation or hold.
- End-Q3: Reassess pipeline based on live_sim data from Q1-Q2 candidates. May reorder Q4 if any Q1-Q2 sleeve underperforms and a replacement is needed.
- End-Q4: Full portfolio recompute (12-sleeve correlation matrix, EW Sharpe estimate) once 5 of 7 new sleeves have ≥30 trades.

---

## 5. Rejected candidates with rejection reason

| # | Candidate | Reason for rejection / deferral |
|---|-----------|----------------------------------|
| C05 | TSMC_ADR_GapFade | Borderline. Defer to **post-pipeline** (year 2). High overlap with C02 in the 09:00-09:30 window. If C02 ships and there is residual edge in TSM ADR specifically, revisit. |
| C08 | InstitutionalFollowLong | Long-side mirror of C07. Book already has 4 longs (L1/L3/L5/S1); adding a 5th long is anti-diversification per coverage gap report. Reject until book becomes net-short-heavy. |
| C09 | BasisCarry / RollWeek | **Defer to year 2**. HIGH complexity (multi-leg or cash-index Data2). Modest Sharpe (0.3-0.5). EV/effort ratio worse than top 7. Revisit after MC12 multi-leg execution is verified by another use case. |
| C10 | BBandSqueezeRelease | Material overlap with L5 BreakoutLong (both wait for vol expansion off compressed base). Risk of cannibalization. Reject for V1 pipeline; could be re-examined as an L5 sizing modulator rather than a new sleeve. |
| C11 | RegimeShiftBreakout | Timeframe overlaps L1 (45M) and L2 (60M). Whatever edge exists is likely double-counted by the existing trend sleeves' WFE-validated regime adaptation. Reject. |
| C12 | NightMeanReversion_Both | Defensive value, low standalone Sharpe. C03 already addresses S1 single-point risk with a clearer mechanism (gap-down momentum mirror). Reject as redundant with C03. |
| C14 | TSMC_ExDiv_Short | Frequency is only 4 trades/yr. Below institutional sample-size gate (≥100 over 6.5y → max ≈ 26 trades from 4/yr × 6.5y). Could survive only with a sample-size exemption AND a very high win rate. Reject as standalone; could be a sizing modulator on existing shorts during ex-div day. |
| C15 | LowVolBreakoutWaiter | Overlaps L5 box breakout family AND C10 BBandSqueeze. The "low-vol → expansion" trade is already in the book's DNA via L1/L5. Reject. |
| C16 | VolConeMeanRev | Standalone idea is fine but the 95th-percentile vol-spike sample is ~30 events/6yr — borderline. Defer; could revisit if data becomes richer or as an L4 enhancement. |
| C17 | PostHolidayGapFade | Only ~5 events/yr — sample-size deal-breaker. Edge per event is high (40-100 bp) but won't pass institutional dim-5 gate even with 6.5y backtest. Reject as standalone. |
| C18 | PreLongHolidayRally | Currently FORBIDDEN by HolidayFlat rule (rule #11-adjacent). Would need HolidayFlat amendment AND a 6-events/yr sample-size exemption. Two exemptions for a 30-80 bp edge is not worth the governance cost. Reject. |
| C19 | LunchTimeMeanReversion | 5-8 bp edge per trade. After slippage (1000 NTD round-trip = 5 pt = 25 bp on a 20pt expected move), edge is gone. Reject. |
| C20 | USD_TWD_Reverse | Highest complexity (FX feed + low signal frequency). Defer to year 2 cross-asset expansion phase. |
| C21 | VIX_Spike_Decay_Buy | VIX data feed for TWVIX is sparse; SPX VIX as proxy duplicates information already in C02 (SPX overnight signal). Reject — likely subsumed by C02. |
| C22 | AuctionOpen_Imbalance_Fade | Requires sub-minute execution; out of scope for MC12 retail infrastructure. Reject. |

### 5.1 Year-2 revival list

If/when book reaches 9 sleeves and the pipeline cadence permits, these are top revival candidates:
- **C09 BasisCarry** — if multi-leg infra matures
- **C20 USD_TWD_Reverse** — if FX feed becomes available
- **C05 TSMC_ADR_GapFade** — if residual edge after C02 deployment

---

## 6. Summary

- **22 unique candidates** consolidated from 38 raw entries across 5 deep-discovery reports.
- **Strongest convergence signal**: C01 PullbackShort (named by ALL 5 reports under different aliases). This is the unambiguous Q1 #1 priority.
- **Top 7 pipeline** spans Q1-Q4 of next 12 months, balancing user-stated gap (C01), institutional gap #1 sentiment/positioning (C07), best-evidence cross-asset (C02), best-evidence event-driven (C04 + C13), zero-corr calendar (C06), and defensive night coverage (C03).
- **Two constitution amendments required** (C04 EVENT_DRIVEN_EXEMPT for settlement-day harvest, pre-Q3). User sign-off is the gating dependency.
- **Three Phase-0 infra builds required** (SPX feed Q2, TAIFEX 三大法人 scraper Q2, FOMC registry Q3). All are low-complexity and free-data.
- **Expected portfolio EW Sharpe trajectory**: 1.329 (current 6) → ~1.45 after C01 → ~1.60 after C01+C02+C07 → ~1.75 after full 7-sleeve pipeline (assumes ρ ≈ 0 to existing book — must be validated per sleeve).
- **All 7 pass mandatory rules 11/12/13** with two flagged exemption requests (C04 settlement-day, C18 holiday-tail — but C18 is rejected so only one exemption remains in scope).
- **The user-flagged gap and the #1 institutional gap converge on the same Q1 #1 candidate** — strongest possible signal for build order.

---

_Compiled 2026-06-19 from 5 deep-discovery agent outputs. All complexity / diversification / EV scores are best-effort consolidated judgments; each candidate must independently pass Phase 1-3 + 10-dim institutional gate before any live_simulation promotion. No existing strategy modified by this pipeline._
