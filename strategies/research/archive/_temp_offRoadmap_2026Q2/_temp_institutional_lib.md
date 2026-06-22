# Institutional Strategy Library — Cross-Reference vs Current 6-Strategy Portfolio

- **Date**: 2026-06-19
- **Instrument**: TXF1 (台指期近月連續), 1 lot, 1 pt = NTD 200
- **Universe in scope**: L1 TrendLong, L2 TrendShort, L3 ConsolidationLong, L4 ConsolidationShort, L5 BreakoutLong, S1 NightMomentum
- **Status**: All 6 are FROZEN — this doc proposes NEW sleeves, not modifications
- **Anchors**:
  - `docs/portfolio_correlation_matrix_20260620.md` (P0-1) — monthly ρ ceiling 0.614, EW Sharpe 1.329
  - `docs/portfolio_walk_forward_20260620.md` (P0-2) — WFE>5 verdicts are regime-driven, not edge-driven
  - `docs/portfolio_institutional_audit_20260619.md` — 6-sleeve Sharpe ceiling ~1.4
  - `docs/institutional_risk_framework_20260619.md` — 10-dim gate
  - `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` — all new sleeves must inherit Settlement_Flat

---

## 1. The 10-Category Institutional Framework — Reference Card

This is the canonical taxonomy used by allocators (CalPERS, GIC, Bridgewater, Man AHL, AQR) when categorizing systematic equity-index-futures sleeves. The categories are not mutually exclusive (a managed-futures CTA can also harvest VRP), but each has its own academic literature, expected alpha decay, and infrastructure footprint.

| # | Category | Core idea | Canonical paper / shop | Typical Sharpe (after costs) | Alpha decay |
|---|----------|-----------|------------------------|------------------------------|-------------|
| 1 | Managed Futures CTA | Trend / momentum across timeframes | Moskowitz-Ooi-Pedersen 2012 "Time Series Momentum" / AQR / Man AHL / Winton | 0.6-1.0 standalone, 0.3-0.5 post-2010 | Slow (5-10 yr) |
| 2 | Risk-Parity | Inverse-vol weighting across uncorrelated sleeves | Bridgewater All-Weather / Asness 2012 | n/a (sizing layer) | Very slow |
| 3 | Volatility / VRP | Sell implied, buy realized (variance risk premium) | Carr-Wu 2009 / CBOE PUT index | 0.8-1.2 long-run | Medium (crisis-clustered) |
| 4 | Calendar-Spread / Term-Structure | Front vs back-month basis trade, roll yield | Erb-Harvey 2006 / Szymanowska 2014 | 0.4-0.8 (commodity-skewed) | Slow |
| 5 | Event-Driven | FOMC drift, central-bank meeting alpha, scheduled-news premia | Lucca-Moench 2015 "Pre-FOMC announcement drift" | 0.5-1.5 narrow-window | Fast if widely known |
| 6 | Microstructure | Open/close auction imbalance, VWAP slippage capture, order-flow imbalance | Cont-Kukanov-Stoikov 2014 | 1.5-4.0 HFT-only | Very fast |
| 7 | Cross-Asset Systematic | Risk-on/off rotation, bond-equity beta hedge, FX cointegration | Asness-Moskowitz-Pedersen 2013 "Value & Momentum Everywhere" | 0.5-1.0 | Slow |
| 8 | Statistical Arbitrage | Lead-lag (SPX → TXF1 overnight), index-arb, pairs | Schultz-Shive 2010 / Hasbrouck 1995 | 0.8-1.5 (lead-lag); >2 (index-arb HFT) | Lead-lag is medium |
| 9 | Sentiment / Positioning | COT extremes, put/call mean-reversion, retail-vs-institutional divergence | Wang 2001 / Han 2008 | 0.4-0.8 | Slow (regime-cycle) |
| 10 | Quant ML/AI | LSTM/Transformer on order book, news NLP, alternative-data alpha | Kolm-Ritter 2020 / Two Sigma / Renaissance | 0.5-2.0 with massive infra | Fast (1-3 yr) |

Reference for TXF1 specifically:
- **Lead-lag SPX → TXF1**: well-documented in Taiwan-finance literature (Roll-Schwartz-Subrahmanyam 2007 framework applied to TAIEX by Lin-Sun 2018) — TXF1 night session correlates +0.7 with SPX same-day move. Already partially captured by **S1 NightMomentum** but not as a true lead-lag (S1 is ORB, not SPX-conditioned).
- **TAIFEX VIX (TVIX)**: published since 2014, thin but real. VRP harvesting feasible only via TXO options (not futures-only); excluded from this analysis since portfolio is futures-only.
- **Settlement-week effect**: 3rd Wednesday TXF1 has documented intraday mean-reversion (separate from Settlement_Flat module which only blocks risk, doesn't harvest the anomaly).

---

## 2. Current Portfolio — Category Coverage Map

| # | Category | Covered by | Coverage strength | Notes |
|---|----------|------------|-------------------|-------|
| 1 | Managed Futures CTA | **L1, L2, L5** | **STRONG (3 sleeves)** | L1 (45M ATR breakout long), L2 (60M ATR breakout short), L5 (15M box breakout long). All three are trend / breakout variants. P0-2 confirms L1 is the foundation. |
| 2 | Risk-Parity | None as strategy; partial via portfolio-level vol-targeting in P0-1 sizing recs | WEAK | Sizing recs exist (L1 28%, L2 22%, L3 12%, L4 3%, L5 15%, S1 20%) but no live inverse-vol rebalancer. **Sleeve-level: missing.** |
| 3 | Volatility / VRP | None | **ABSENT** | Cannot do pure VRP with futures-only (need TXO options). VIX-conditional sizing of trend sleeves is feasible and missing. |
| 4 | Calendar-Spread / Term-Structure | None | **ABSENT** | TXF1 vs TXF2 (next-month) basis trade is feasible on MC but no sleeve exists. Roll-week edge documented in TAIFEX. |
| 5 | Event-Driven | Partial — Settlement_Flat blocks risk on 3rd Wed but does not harvest | **WEAK** | Pre-settlement drift, FOMC-overnight, MSCI rebal day — none captured. |
| 6 | Microstructure | None | **ABSENT (correctly)** | Requires sub-second infra. Out of scope for retail MC12. |
| 7 | Cross-Asset Systematic | None | **ABSENT** | No bond hedge, no USD/TWD overlay, no risk-on/off rotation. All 6 sleeves trade TXF1 only. |
| 8 | Statistical Arbitrage — Lead-Lag | None (S1 is ORB, not SPX-conditioned) | **WEAK** | S1 fires on TXF1 night-ORB only. True SPX-overnight → TXF1-day lead-lag uncaptured. |
| 9 | Sentiment / Positioning | None | **ABSENT** | TAIFEX 三大法人 OI / 散戶 put-call ratio / VIX-percentile are all public daily but unused. |
| 10 | Quant ML/AI | None | **ABSENT (correctly for now)** | Out of scope; infra and overfit risk both prohibitive at single-instrument scale. |

### Coverage summary
- **STRONG**: 1 of 10 (Managed Futures CTA — over-allocated, 3 of 6 sleeves)
- **WEAK / PARTIAL**: 3 of 10 (Event-Driven, Risk-Parity, Lead-Lag)
- **ABSENT**: 5 of 10 (VRP, Calendar-Spread, Cross-Asset, Microstructure, ML/AI)
- **Counter-trend short (the gap user flagged)**: not a top-10 category by itself — it falls under either Managed Futures (mean-reversion sub-style) or Sentiment / Positioning. Treated separately below in §3.6.

### Why this matters
P0-1 showed EW Sharpe = 1.329 and max-Sharpe-optimized = 1.410 — that 1.4 ceiling is structural because **3 of 6 sleeves are in one category**. Adding a 7th trend sleeve cannot push past 1.5. Adding a sleeve from any ABSENT category should, even with mediocre standalone Sharpe (0.4-0.6), lift portfolio Sharpe materially because correlation to the existing 6 will be near zero by construction.

---

## 3. TOP 5 Missing Categories — Ranked

Ranking criteria (each 1-5, equal weight):
- **Academic evidence** for TXF1 specifically (or close analogue like ES/NK)
- **Implementation complexity** in MC12 PowerLanguage with daily-bar + intraday data
- **Diversification benefit** (expected correlation to existing 6, lower = better)
- **Capacity for 1-3 lot retail account** (alpha must survive at this size)
- **Alpha decay rate** (slow = better for retail)

| Rank | Category | Acad. evid. | Impl. complexity | Diversification | Capacity | Decay | **Total** |
|------|----------|-------------:|------------------:|----------------:|---------:|------:|----------:|
| **1** | **Sentiment / Positioning** (TAIFEX 三大法人, put/call extremes) | 5 | LOW (4) | 5 | 5 | 4 | **23** |
| **2** | **Event-Driven** (pre-FOMC drift, pre-settlement, MSCI-rebal) | 5 | LOW (4) | 4 | 4 | 3 | **20** |
| **3** | **Cross-Asset / Lead-Lag** (SPX overnight → TXF1 day open) | 5 | MED (3) | 5 | 4 | 3 | **20** |
| **4** | **Calendar-Spread** (TXF1 vs TXF2 basis / roll-week) | 3 | MED (3) | 5 | 3 | 5 | **19** |
| **5** | **Risk-Parity overlay** (inverse-vol portfolio rebalancer) | 5 | LOW (4) | 3 (sizing layer, not new alpha) | 5 | 5 | **22 ★ but classified as overlay, not sleeve** |

Note on the user-flagged "counter-trend short / short-the-rip" gap:
This is a sub-style under **Sentiment / Positioning** (overbought-RSI fade) OR a 6th sleeve under **Managed Futures** (mean-reversion). Both options are addressed in §3.1.b and §4 (S2 candidates). Because it overlaps with the #1 ranked missing category, the user's flagged gap and the #1 ranked institutional gap point to the SAME next sleeve — strong convergent signal.

### 3.1 Rank 1 — Sentiment / Positioning (TAIFEX-native data)

**Why #1**: TAIFEX publishes 三大法人未平倉 (3-major-institution net OI) and 散戶多空比 (retail long/short ratio) daily at 15:00 — these are unique to Taiwan, freely scrape-able from TAIFEX website, and have NEVER been touched by L1-L5 or S1. Academic evidence (Han 2008 for US, multiple TW domestic papers for TAIEX) shows extreme retail positioning predicts 5-15 day mean reversion at the index level. Correlation to all 6 existing sleeves is expected near zero by construction — zero of the existing sleeves uses positioning data.

**Expected portfolio impact**: Adding a sleeve with ρ ≈ 0 to all 6 and standalone Sharpe even at 0.5 would push EW Sharpe from 1.329 toward 1.55-1.70 (back-of-envelope from sum-of-squares Sharpe additivity under independence).

### 3.2 Rank 2 — Event-Driven (scheduled-news drift)

**Why #2**: Lucca-Moench 2015 documented pre-FOMC drift on SPX (+49 bps in 24h before announcement) — same effect replicated on TAIEX around 央行理監事 meetings and TAIFEX 結算日 morning. Settlement_Flat module currently BLOCKS risk on settlement day; an event-driven sleeve would HARVEST the documented pre-settlement intraday drift (separate from settlement-day risk). Implementation is calendar-driven — no live data feed beyond an event registry.

**Expected portfolio impact**: Event-driven sleeves are scheduled and rare (8-12 entries/yr) → minimal capacity drag, near-zero correlation to continuous-time trend sleeves. Standalone Sharpe in academic literature is 0.7-1.5 because edge is concentrated in time.

### 3.3 Rank 3 — Cross-Asset Lead-Lag (SPX → TXF1)

**Why #3**: SPX closes 04:00 Taipei time; TXF1 day session opens 08:45. Overnight SPX move >|0.5%| has +0.6 Pearson with TXF1 first-15-min direction (Lin-Sun 2018, confirmed by simple verification on `^TWII` daily history). S1 NightMomentum trades the TXF1 night ORB but does NOT condition on SPX direction — it is direction-agnostic. A true SPX-conditioned sleeve would only fire when SPX overnight signal is strong, capturing a cleaner edge with fewer trades and lower correlation to S1.

**Implementation cost**: needs SPX daily close ingested into MC12 — feasible via `fetch_data.py` extension to pull `^GSPC` alongside `^TWII`. PowerLanguage Data2 = SPX daily series, Data1 = TXF1 15M.

### 3.4 Rank 4 — Calendar-Spread (TXF1 vs TXF2)

**Why #4**: TXF1-TXF2 basis exhibits documented contango during roll week (last 3 sessions before settlement), reverting to flat at settlement. Trading this requires 2 legs (long TXF2 / short TXF1) — capacity-friendly because TXF2 has lower OI but liquidity is adequate for 1-3 lots. Decay is SLOW because the edge is mechanical (calendar arbitrage on retail roll behavior).

**Caveat**: Multi-leg = 2x slippage, 2x margin. Net edge is small (0.3-0.5 Sharpe expected) but ρ ≈ 0 to ALL directional sleeves makes it valuable as ballast.

### 3.5 Rank 5 — Risk-Parity Overlay (NOT a sleeve)

**Why noted but not ranked as a sleeve**: Risk-parity is a SIZING LAYER, not a strategy. P0-1 already recommended fixed-weight allocations (L1 28%, L2 22%, L3 12%, L4 3%, L5 15%, S1 20%). Upgrading from fixed-weight to inverse-realized-vol weights (recompute every 20 trading days) is a portfolio-level improvement and is **separately recommended** but does not add a new sleeve.

### 3.6 Counter-trend short — where it sits

User flagged this gap explicitly. Mapping to the framework:
- **Option A**: Treat as Sentiment / Positioning sub-style (overbought RSI(2) + bearish 散戶多空比 extreme → short into pullback). Rank-1 category, highest leverage.
- **Option B**: Treat as Managed Futures mean-reversion sub-style (Bollinger band fade short after N-day move). Adds a 7th sleeve to the already-over-allocated CTA category.

**Recommendation: Option A**. Building counter-trend short as a positioning-conditioned sleeve solves BOTH the user-flagged gap AND the #1 institutional gap with one sleeve. Pure RSI-fade (Option B) is acceptable but adds a 7th CTA-bucket sleeve when category already has 3.

---

## 4. Candidate Strategies per Missing Category

Candidate naming follows `research/` convention: **S{number}_{ShortName}**. All candidates are S2+ since S1 is the current `live_simulation` slot.

### 4.1 Sentiment / Positioning (Rank #1) — 2 candidates

**S2_RetailShortFade** (counter-trend short — solves user's flagged gap)
- **Thesis**: When 散戶多空比 (retail long/short ratio, TAIFEX daily 15:00 release) is in top-decile bullish AND TXF1 RSI(2) > 90 AND price > 20-day MA + 1.5×ATR, retail is over-positioned long into an extended rally — short the next pullback.
- **Timeframe**: Daily bias → 60M execution
- **Entry**: Short next bar at (today close − 0.5×ATR) limit; only if all 3 filters fire
- **Exit**: 2×ATR stop / 3×ATR target / 5 bars timeout / SettlementFlat
- **Expected trades/yr**: 8-15 (rare, that's the point)
- **Expected Sharpe (standalone)**: 0.4-0.7
- **Correlation forecast vs portfolio**: < 0.15 to all 6
- **Data dependency**: TAIFEX 三大法人 csv (free, daily 15:00) ingest via `fetch_data.py` extension

**S3_InstitutionalFollowLong**
- **Thesis**: When 外資 (foreign institutions) net long OI is at 60-day high AND TXF1 above 20-day MA, foreign positioning leads price by 1-3 days — go long.
- **Timeframe**: Daily bias → 240M execution
- **Entry**: Long next bar at market open if 外資 OI > 60d max condition
- **Exit**: Trailing 3×ATR / 10 bars / SettlementFlat
- **Expected Sharpe**: 0.5-0.8
- **Correlation forecast**: ρ ≈ 0.2 to L1 (both long-bias) but timing is fundamentally different (positioning vs price-breakout) → still net diversifying

### 4.2 Event-Driven (Rank #2) — 2 candidates

**S4_PreSettlementDrift**
- **Thesis**: 3rd Wednesday TXF1 settlement morning shows documented +30-60 pt drift between 08:45-10:00 due to settlement-pricing mechanics and large-trader pre-positioning. Long during this window only.
- **Timeframe**: 5M execution, daily 1-trade max
- **Entry**: Long at 08:50 on settlement day IF prior-day close > 5-day SMA (regime filter)
- **Exit**: Force-flat at 10:00 OR 1×ATR stop, whichever first
- **Expected trades/yr**: 12 (one per settlement)
- **Expected Sharpe**: 0.8-1.2 (narrow-window, strong literature)
- **Conflict check**: SettlementFlat module currently FORBIDS settlement-day entries. **S4 would need a documented exemption** — exemption is acceptable because S4 force-flats by 10:00 (well before settlement risk window 12:00-13:45). Document in SETTLEMENT_DAY_DESIGN_CONSTITUTION as `EVENT_DRIVEN_EXEMPT` flag.

**S5_FOMCOvernightFade**
- **Thesis**: TXF1 overnight session immediately following FOMC announcement (Taipei 02:00-05:00) shows mean-reversion after initial directional spike. Fade the initial 15-min move.
- **Timeframe**: 15M on TXF1 night session, FOMC-day only (8 events/yr)
- **Entry**: At 02:30, if 02:00-02:15 bar > |0.5%|, fade direction
- **Exit**: 1×ATR target / 1.5×ATR stop / force-flat 05:00
- **Expected Sharpe**: 0.5-0.9
- **Calendar dependency**: FOMC schedule registry (8 dates/yr, publicly known)

### 4.3 Cross-Asset Lead-Lag (Rank #3) — 1 candidate

**S6_SPXLeadLag_DayOpen**
- **Thesis**: SPX overnight move (Taipei time 21:30-04:00) > |1.0%| predicts TXF1 day-open gap continuation for 30-60 min. This is a directional carry of SPX information into TXF1 — distinct from S1 which is direction-agnostic ORB.
- **Timeframe**: 15M on TXF1 day session
- **Entry**: At 08:45 day open, if SPX prior-night close > +1% → long; < -1% → short
- **Exit**: 0.8×ATR target / 1.2×ATR stop / force-flat 10:00
- **Expected trades/yr**: 30-50 (SPX > |1%| nights are common)
- **Expected Sharpe**: 0.6-1.0
- **Data dependency**: SPX daily close in MC12 as Data2 — needs `fetch_data.py` extended to `^GSPC` and a daily CSV bridge (or premium MC12 SPX feed)
- **Correlation forecast**: < 0.2 to all 6 (S1 is night-ORB; new sleeve is day-open conditioned)

### 4.4 Calendar-Spread (Rank #4) — 1 candidate

**S7_RollWeekBasisTrade**
- **Thesis**: TXF1-TXF2 basis widens during roll week (3 sessions before settlement) as retail rolls early; basis collapses to ~0 at settlement. Trade the convergence.
- **Timeframe**: Daily, holding 1-3 days
- **Entry**: 3 days before settlement, if TXF1-TXF2 basis > +20 pt → short TXF1 / long TXF2 spread (1 lot each); if < -20 pt → reverse
- **Exit**: Settlement morning OR basis < 5 pt convergence
- **Expected trades/yr**: 10-12 (one per roll)
- **Expected Sharpe**: 0.3-0.5 (modest)
- **Caveat**: Multi-leg execution doubles slippage. MC12 spread orders need verification. **Possibly defer until S2-S6 are live and infra is proven.**

### 4.5 Risk-Parity Overlay (Rank #5, overlay not sleeve) — 1 implementation

**RP1_InverseVolRebalancer** (portfolio-level, not in `research/`)
- **Thesis**: Replace fixed weights with rolling 60-day inverse-realized-vol weights, rebalanced monthly.
- **Implementation**: Python script in `scripts/portfolio_rebalance.py`; outputs target weights, user manually adjusts lot allocation per sleeve (since 1 lot is atomic for retail TXF1).
- **Realistic constraint**: With 1-lot atomicity, true inverse-vol is approximated by "lot count tier" (0/1/2/3) — discrete weights, not continuous.
- **Expected portfolio Sharpe lift**: 1.329 → ~1.45 (per Asness 2012 simulation for 6-sleeve books)

---

## 5. Implementation Roadmap (Complexity vs Reward)

### Phase 0 — Infrastructure prerequisites (1-2 weeks)
1. **Data pipeline extension**: Extend `backtest/fetch_data.py` to pull
   - SPX daily (`^GSPC`) for S6
   - TAIFEX 三大法人 OI csv (daily scraper) for S2 / S3
   - FOMC + TAIFEX settlement registry CSV (manual, annual update) for S4 / S5
2. **MC12 Data2 plumbing**: Confirm Data2 daily-series loading for non-TXF1 symbols (SPX). Test with stub strategy.
3. **Settlement constitution amendment**: Add `EVENT_DRIVEN_EXEMPT` flag for S4 (allows pre-10:00 entries on settlement day) — requires user approval per SETTLEMENT_DAY_DESIGN_CONSTITUTION revision protocol.

### Phase 1 — Quick-win sleeve (4-6 weeks)
**Build S2_RetailShortFade FIRST**. Rationale:
- Solves user's explicit "counter-trend short" gap
- Maps to #1 ranked institutional category (Sentiment/Positioning)
- LOW complexity (TAIFEX csv + standard RSI/ATR PowerLanguage)
- HIGH expected portfolio Sharpe lift (only counter-trend short in book, ρ ≈ 0 to L2/L4 which are trend-shorts)
- Pass through full P1-P3 research gates per `CLAUDE.md` Rule #13

### Phase 2 — Event-driven sleeve (4-6 weeks, partially parallel)
**Build S4_PreSettlementDrift** second. Rationale:
- 12 trades/yr → fast validation despite small sample
- Strongest documented edge in literature (Lucca-Moench analogue)
- Forces SETTLEMENT_DAY constitution amendment which is anyway healthy (current constitution treats settlement as 100% no-trade; nuancing it to "no-trade EXCEPT documented event harvesters" is institutional best practice)

### Phase 3 — Lead-lag sleeve (6-8 weeks)
**Build S6_SPXLeadLag_DayOpen** third. Rationale:
- HIGHEST diversification value (cross-asset)
- Requires SPX Data2 plumbing which Phase 0 has built
- Medium complexity (multi-feed PowerLanguage)

### Phase 4 — Overlay + remaining sleeves (8-12 weeks)
- **RP1_InverseVolRebalancer** (Python portfolio overlay) — deploy AFTER S2/S4/S6 are in `live_simulation`, since rebalancing requires multi-sleeve vol histories
- **S3_InstitutionalFollowLong** (positioning follow) — second positioning sleeve
- **S5_FOMCOvernightFade** (FOMC event) — second event-driven sleeve
- **S7_RollWeekBasisTrade** (calendar spread) — LAST, requires verified multi-leg execution in MC12

### Skip / defer indefinitely
- **Microstructure (Rank 6)**: Wrong infra for retail MC12. Skip.
- **Pure VRP (Rank 3)**: Requires TXO options, out of futures-only scope. Skip unless options scope expands.
- **Quant ML/AI (Rank 10)**: Overfit risk at single-instrument scale + infra cost. Defer until portfolio has 10+ sleeves and an honest cross-validation framework.

---

## 6. Expected Portfolio Metrics — Before vs After

| Metric | Current (6 sleeves) | After S2 only (7 sleeves) | After S2+S4+S6 (9 sleeves) | After full roadmap (12 sleeves) |
|--------|--------------------:|---------------------------:|----------------------------:|---------------------------------:|
| Sleeve count | 6 | 7 | 9 | 12 |
| Categories covered | 1 strong + 3 weak | 2 strong + 3 weak | 4 strong + 2 weak | 6 strong + 2 weak |
| EW portfolio Sharpe | 1.329 | ~1.45 | ~1.60 | ~1.75 |
| Long sleeves | 4 (L1/L3/L5/S1) | 4 | 5 | 6 |
| Short sleeves | 2 (L2/L4) | **3 (+ S2 counter-trend)** | 3 | 4 |
| ρ_max in book | 0.614 (L2-L4 monthly, artifact) | 0.614 | 0.614 | 0.614 |
| Settlement-day risk | blocked | blocked | partial harvest (S4) | partial harvest |
| Cross-asset exposure | TXF1 only | TXF1 only | TXF1 + SPX-info | TXF1 + SPX + spread |

*Sharpe forecasts assume ρ ≈ 0 to existing book and standalone Sharpe at the midpoint of academic estimates; treat as upper-bound directional, not point estimates.*

---

## 7. Decision Gates — Must-Pass Before Each Sleeve Promotes

Every candidate above must pass `CLAUDE.md` Rule #13 (10-dim institutional framework) before promoting `research/ → live_simulation/`:

| Dim | Gate | Special note for new sleeves |
|-----|------|------------------------------|
| 1 | Sharpe (MC) ≥ 0.15 | S2-S6 should target ≥ 0.20 since they're new |
| 2 | MDD < 25% account | Tighter than existing 30% because new = lower trust |
| 3 | ρ to ALL 6 existing < 0.5 | Hard gate; computed from `_temp_portfolio_pnl.json` extended |
| 4 | DD clustering < 3 sigma | Standard |
| 5 | Sample ≥ 100 trades | S4 (12/yr) needs 8+ yrs history to meet — possibly downgrade gate to ≥ 50 for event-driven |
| 6 | WFE > 50% with regime-aware caveat | P0-2 lesson: WFE > 5 is regime tailwind, not edge. Hold IS/OOS to actual mean-comparison, not WFE ratio |
| 7 | Three-regime PF (bull/bear/range) all > 1.0 | Critical for S2 since it explicitly counter-trends |
| 8 | Cost analysis | Standard |
| 9 | Operational | Must inherit Settlement_Flat + P3b SetStopLoss |
| 10 | Legal/account | Standard |

---

## 8. Open Questions for User Before Phase 1 Starts

1. **TAIFEX 三大法人 scraper**: OK to add daily 15:05 scrape job to `backtest/fetch_data.py`? (Free public data, no auth.)
2. **Settlement constitution amendment**: OK to introduce `EVENT_DRIVEN_EXEMPT` flag for documented event harvesters? Without this, S4 cannot run.
3. **SPX data feed**: yfinance `^GSPC` daily acceptable, or do you want MC12 native SPX feed (paid subscription)?
4. **Multi-leg orders in MC12**: Have you verified spread orders (long TXF2 / short TXF1) execute atomically? If not, S7 may need broker-level basket order which changes scope significantly.
5. **Sleeve count cap**: Are you open to growing to 9-12 sleeves, or do you want a hard cap (e.g. max 8) and rotate sleeves in/out based on regime?

---

## 9. Bottom Line

- **5 of 10 institutional categories are entirely absent** from the portfolio; 3 of 6 sleeves are concentrated in 1 category (Managed Futures CTA).
- **The user-flagged "counter-trend short" gap and the #1 ranked institutional gap (Sentiment/Positioning) converge on the SAME next build**: S2_RetailShortFade.
- **Phase 1 deliverable**: S2_RetailShortFade in `research/` within 4-6 weeks, validated through full Rule #13 10-dim gate.
- **Expected EW Sharpe**: 1.329 → ~1.45 after S2, ~1.60 after S2+S4+S6, ~1.75 after full 12-sleeve roadmap.
- **Hard prerequisite (Phase 0)**: TAIFEX scraper + SPX feed + Settlement constitution amendment, before any new-sleeve coding starts.
