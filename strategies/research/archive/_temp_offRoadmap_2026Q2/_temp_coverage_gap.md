# TXF1 Portfolio — Multidimensional Market Coverage Gap Analysis

- **Date**: 2026-06-19
- **Universe**: 6 strategies — L1 TrendLong, L2 TrendShort, L3 ConsolidationLong, L4 ConsolidationShort, L5 BreakoutLong, S1 NightMomentum
- **Anchor reports**:
  - `docs/portfolio_correlation_matrix_20260620.md` (P0-1)
  - `docs/portfolio_walk_forward_20260620.md` (P0-2)
  - `docs/institutional_risk_framework_20260619.md` (10-dim framework)
  - `docs/L4_portfolio_role_20260618.md`
- **Trigger**: User identified portfolio gap — "no counter-trend short / short-the-rip strategy" to fade intraday pullbacks within a bull regime
- **Method**: Map 8-dimensional tradeable-state space → identify uncovered cells → rank by frequency × impact → propose candidates
- **FROZEN strategies**: All 6 above are not modified — this report only proposes NEW slots

---

## 1. Methodology: Multidimensional Coverage Matrix

### 1.1 Why 8 dimensions

A backtest-PF view of "diversification" sees only **return-stream correlations**. The deeper question is **which market states does the book have a planted-foot in?** Two strategies with low Pearson can still both go silent in the *same regime* (e.g. neither fires in low-vol range), leaving a tradeable state structurally uncovered. The 8 dimensions below come from cross-referencing:

1. The user's brief (direction / regime / timeframe / session)
2. The 10-dim institutional risk framework (vol regime, sample size, regulatory)
3. The actual entry triggers in each .pla file (pattern type, catalyst, holding behavior)

### 1.2 Coverage states per dimension

For each dimension, every strategy is classified as:
- **PRIMARY** (state is its core hunting ground; >50% of edge comes from here)
- **SECONDARY** (state is in-scope but not core; <50% of edge)
- **INCIDENTAL** (occasional fills; not designed for it)
- **BLOCKED** (cannot fire here — by entry gate, time filter, or direction)

### 1.3 Ranking formula for gaps

For each uncovered cell:

```
gap_score = frequency_in_2020_2026 × severity_when_uncovered
                                       (PnL drag, MDD contribution, or missed alpha)
```

Frequency proxy uses calendar days from the regime buckets in P0-1 §4 (bull 787 / bear 281 / range 74, total 1,142 days).

### 1.4 Cross-check against P0-1 / P0-2 findings

The book's three structural redundancy axes (L2-L4 +0.614 monthly, L1-L5 +0.524, L5-S1 +0.504 — though P0-2 showed L2-L4 was artifact-driven) all map back to the same dimensional clusters this report identifies as **overcovered**. Conversely, gaps below align with the cells where every existing strategy is BLOCKED or INCIDENTAL.

---

## 2. Eight-Dimension Coverage Analysis

### 2.1 Dimension 1: Direction

| State | L1 | L2 | L3 | L4 | L5 | S1 | Coverage |
|-------|----|----|----|----|----|----|----------|
| Long-only | PRIMARY | BLOCKED | PRIMARY | BLOCKED | PRIMARY | PRIMARY | **4 strategies** |
| Short-only | BLOCKED | PRIMARY | BLOCKED | PRIMARY | BLOCKED | BLOCKED | 2 strategies |
| Bidirectional / regime-flip | — | — | — | — | — | — | **0 strategies** |

**Coverage**: 4 longs / 2 shorts / 0 bidirectional. The book is **structurally long-biased**.

**Gaps**:
- **G-D1.a — Counter-trend short / short-the-rip in bull regime** (user's stated gap). L2 only fires after ATR breakdown (trend-confirmed short); L4 only fires on consolidation false-breakout. Neither fades a pullback inside a confirmed uptrend. → **HIGHEST PRIORITY** (this is the explicit user-identified hole)
- **G-D1.b — Direction-agnostic regime-flip engine** that goes long in bull and short in bear off the *same* setup. No book strategy can pivot without changing its identity. Frequency: every regime transition (~2-3 per year). Severity: each missed pivot costs the equivalent of one strategy's monthly mean (~$20-30k).

### 2.2 Dimension 2: Regime

Buckets per P0-1 §4: bull 787 d / bear 281 d / range 74 d / transition (~12 days/yr inferred from regime bucket boundaries) / crisis (2020-03, 2022-10, 2024-08, 2025-04 = 4-6 single-day events in 6 years).

| Regime | L1 | L2 | L3 | L4 | L5 | S1 | Per-regime PnL leader |
|--------|----|----|----|----|----|----|---|
| Bull (787 d) | PRIMARY ($1.93M) | SECONDARY | SECONDARY | INCIDENTAL | PRIMARY ($1.44M) | PRIMARY ($1.25M) | L1 |
| Bear (281 d) | SECONDARY | PRIMARY ($292k) | INCIDENTAL | **NEGATIVE (-$51k)** | SECONDARY | PRIMARY ($305k) | S1 |
| Range (74 d) | SECONDARY | PRIMARY ($180k) | PRIMARY ($140k) | INCIDENTAL | **BLOCKED (0 trades)** | **NEGATIVE (-$83k)** | L2 |
| Transition (~70 d) | INCIDENTAL | INCIDENTAL | INCIDENTAL | INCIDENTAL | INCIDENTAL | INCIDENTAL | **none** |
| Crisis (~6 single days) | INCIDENTAL | SECONDARY | INCIDENTAL | PRIMARY (2025-04 +$273k) | INCIDENTAL | SECONDARY (gap-down nights) | L4 |

**Gaps**:
- **G-D2.a — Transition regime (regime-flip days)**. No strategy is designed for the days where bull→bear or range→trend is being decided. These are the same days where L1/L5 give back gains and L2/L4 fire false starts. Estimated ~70-100 days/yr based on TWII rolling-90d regime classifier. Severity: high (these days produce the worst joint drawdowns).
- **G-D2.b — Range regime is undercovered going forward**. L5 has zero range data (started 2021-09, post-COVID). S1 *loses money* in range (-$83k over 74 days). If 2020-style COVID chop returns, only L2 and L3 carry the book — frequency in next regime cycle plausibly 60-90 days.
- **G-D2.c — Crisis tail-event capture** is L4-only and event-dependent (P0-2 showed L4's 2025-04 single day = $273k of the year's $294k). Frequency: 1-2 events/yr. Severity: $200k-$500k per event. Single-strategy dependency = fragility.

### 2.3 Dimension 3: Timeframe Horizon

Per L4_portfolio_role doc and live README:

| Horizon | L1 | L2 | L3 | L4 | L5 | S1 |
|---------|----|----|----|----|----|----|
| Intraday (<1 day) | — | — | PRIMARY | PRIMARY | PRIMARY | PRIMARY |
| Swing (1-5 days) | SECONDARY | PRIMARY | INCIDENTAL | INCIDENTAL | INCIDENTAL | — |
| Cross-day trend (5-30 days) | PRIMARY | SECONDARY | — | — | — | — |
| Position (1-3 months) | — | — | — | — | — | — |

**Coverage**: 4 intraday / 2 swing / 1 cross-day / **0 position**.

**Gaps**:
- **G-D3.a — Position-horizon strategies entirely absent**. The book has zero exposure to multi-week / multi-month edges (e.g. monthly OPEX seasonality, semiconductor cycle leaning, Fed-meeting drift). Frequency: every month / every Fed cycle. Severity: lost diversification — long-horizon edges are typically uncorrelated with intraday tape-reading edges.
- **G-D3.b — Cross-day SHORT trend is single-source (L2 only)**. If L2 enters one of its "sparse-trader" drought windows (P0-2 noted only 78 trades in 5.3 years), there is no backup cross-day short. Frequency: roughly half of every year (L2 only trades 16 + 13 + 48 zero months = 14 positive months out of 79 = 18%).

### 2.4 Dimension 4: Session

Day session = 08:45-13:45 (5 hours). Night session = 15:00-05:00 (14 hours). Cross-session = positions held through the 13:45-15:00 break.

| Session | L1 | L2 | L3 | L4 | L5 | S1 |
|---------|----|----|----|----|----|----|
| Day-only (intraday close before 13:45) | — | — | SECONDARY | INCIDENTAL | PRIMARY (with day-session fade) | BLOCKED |
| Night-only (15:00-05:00) | INCIDENTAL | SECONDARY (16-bar night) | — | BLOCKED (Night_Block_On=true 02:00-04:59) | — | **PRIMARY** |
| Day+Night (cross 13:45-15:00 hold) | PRIMARY | PRIMARY | INCIDENTAL | INCIDENTAL | PRIMARY | BLOCKED |

**Coverage**: Day-session fully covered (L1/L3/L5). Night-session covered ONLY by S1 (single point of failure). Day-night transition (13:45-15:00) not actively traded by anyone.

**Gaps**:
- **G-D4.a — Night-session single-point-of-failure (S1 only)**. If S1 goes offline or its 2024+ edge mean-reverts, the entire night session (14 hours, 58% of trading clock) has zero coverage. P0-2 flagged S1 as IS_NEG in 2 of 4 splits — its edge is regime-driven not skill-driven, making the single-point risk acute.
- **G-D4.b — Night-session SHORT entirely uncovered**. S1 is long-only. Night-session short-the-rally or gap-down momentum is unmonitored. Frequency: gap-down nights occur ~30-40 times/yr based on TWII overnight returns.
- **G-D4.c — Day-night transition (13:45-15:00) untraded**. This is a 75-minute window where TXF1 *does* trade (with reduced liquidity) but no strategy targets it. The handoff often shows reversal patterns (overnight catalysts pricing in vs day-session momentum exhausting).

### 2.5 Dimension 5: Volatility Regime

Defined by ATR(20)/Close percentile:
- Low-vol (<25th pctile, ~285 days in 6yr): ATR/Close < 0.7%
- Normal (25-75 pctile, ~570 days): ATR/Close 0.7-1.3%
- High-vol (75-95 pctile, ~228 days): ATR/Close 1.3-2.0%
- Spike (>95 pctile, ~60 days): ATR/Close > 2.0% (COVID-2020, 2022-10, 2025-04)

| Vol regime | L1 | L2 | L3 | L4 | L5 | S1 |
|-----------|----|----|----|----|----|----|
| Low-vol | INCIDENTAL | BLOCKED (ATR breakout doesn't fire) | PRIMARY (range reversal) | SECONDARY | INCIDENTAL | INCIDENTAL |
| Normal | PRIMARY | SECONDARY | PRIMARY | PRIMARY | PRIMARY | PRIMARY |
| High-vol | PRIMARY | PRIMARY | INCIDENTAL | INCIDENTAL | PRIMARY | SECONDARY |
| Spike | SECONDARY (ATR adjusts up) | PRIMARY | BLOCKED (range broken) | PRIMARY (crisis captures) | INCIDENTAL | SECONDARY |

**Gaps**:
- **G-D5.a — Low-vol regime is L3-only with 0.55 Sharpe**. P0-1 §4.5 range table (74 days) shows L3 +$140k as range PnL leader, but L3 has 720d rolling fail-rate 37% (P0-2 §2.2). Low-vol days produce ~50 days/yr of book-wide stalls; only L3 earns, and L3 is borderline.
- **G-D5.b — Vol-expansion timing (low→high transition)**. The day a multi-week low-vol regime breaks into high-vol expansion is the highest-alpha day in the cycle. Strategies that wait for confirmation (L1/L2 ATR breakout, L5 box breakout) all enter late. Frequency: 6-10 transitions/yr. Severity: each captured expansion = ~100-300 TXF points.
- **G-D5.c — Sustained high-vol grind**. Periods of high-vol *without* clean trend (e.g. 2022 Q3-Q4) hurt L1/L5 (whipsaws) and don't help L3 (range broken). Estimated 30-50 days/yr.

### 2.6 Dimension 6: Pattern Type

| Pattern | L1 | L2 | L3 | L4 | L5 | S1 |
|---------|----|----|----|----|----|----|
| Trend continuation | PRIMARY | PRIMARY | — | — | SECONDARY | SECONDARY (overnight momentum) |
| Mean-reversion | — | — | PRIMARY (range reversal) | PRIMARY (false-breakout) | — | — |
| Breakout (box / channel) | — | — | — | — | PRIMARY | — |
| Event-driven | — | — | — | INCIDENTAL (crisis capture) | — | — |
| Time-of-day / session edge | — | — | — | — | — | PRIMARY (ORB night) |
| Volatility expansion / contraction | — | — | — | — | — | — |
| Multi-timeframe confluence | — | — | — | — | — | — |
| Statistical / quant-factor | — | — | — | — | — | — |

**Coverage**: Trend, mean-reversion, breakout, time-of-day all covered. Event-driven only via L4-incidental. Volatility-explicit, multi-TF confluence, and quant-factor patterns absent.

**Gaps**:
- **G-D6.a — Volatility-explicit strategies absent**. No strategy enters/exits *based on* ATR expansion/contraction itself (vs using ATR as a sizing input). Examples missing: VIX-equivalent percentile filter, BBand-squeeze breakout, vol-cone breach. Frequency: continuous. Severity: cross-cuts with G-D5.b/c.
- **G-D6.b — No multi-timeframe confluence engine**. Each strategy uses one timeframe (L1=45M, L2=60M, L3-L5=15M, S1=15M). No strategy requires alignment across 15M+60M+Daily before entering. Frequency: confluence setups occur ~3-5 times/month. These setups historically have the highest hit rate.
- **G-D6.c — No event-driven sleeve as a primary**. L4's crisis capture is incidental — design intent was reversal-short, the 2025-04 win was lucky. No strategy is *designed* around calendar events (Fed, CPI, settlement, ex-div).

### 2.7 Dimension 7: Catalyst

| Catalyst | L1 | L2 | L3 | L4 | L5 | S1 |
|---------|----|----|----|----|----|----|
| Pure technical (price/vol) | PRIMARY | PRIMARY | PRIMARY | PRIMARY | PRIMARY | PRIMARY |
| Macro release (CPI/Fed/NFP) | INCIDENTAL | INCIDENTAL | — | — | INCIDENTAL | INCIDENTAL |
| Earnings / TSMC ex-div | — | — | — | — | — | — |
| Geopolitical (Trump tariff, Taiwan-strait) | INCIDENTAL | INCIDENTAL | — | INCIDENTAL (caught 2025-04) | — | INCIDENTAL |
| Settlement-cycle (monthly TXF) | BLOCKED (Settlement_Flat 12:30) | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Overnight gap (US session spillover) | — | — | — | — | — | PRIMARY |

**Coverage**: All technical. Settlement_Flat *blocks* trading the highest-edge intraday window (12:30-13:30 monthly settlement). Macro and earnings catalysts are entirely incidental.

**Gaps**:
- **G-D7.a — Settlement-cycle alpha entirely blocked by design**. The constitution mandates Settlement_Flat 12:30 = no entries after 12:30 on monthly settlement Wednesday. This is correct for safety, but it *creates* a permanent untraded window (12:30-13:30, 1 hour × 12 months = ~12 hours/yr). The 1-day-before-settlement and 1-day-after-settlement windows are also untraded by any specialist. Frequency: 12 × 3 days = 36 days/yr with edge potential.
- **G-D7.b — Macro-event positioning untraded**. Fed meetings (8/yr), CPI prints (12/yr), NFP (12/yr), TSMC earnings (4/yr). Strategies could *enter pre-release* with a defined-risk setup or *fade the first 30 min* post-release. None do. Frequency: ~36-40 events/yr.
- **G-D7.c — Overnight US-spillover short missing**. S1 captures gap-up momentum long; the mirror image (US closed weak → fade Taiwan night open up, or ride gap-down continuation short) is uncovered. Frequency: ~30% of nights with material US move.

### 2.8 Dimension 8: Holding Behavior

| Behavior | L1 | L2 | L3 | L4 | L5 | S1 |
|---------|----|----|----|----|----|----|
| Hold-to-target (fixed TP) | INCIDENTAL | — | SECONDARY | SECONDARY | — | — |
| Trail (trailing stop) | PRIMARY | PRIMARY | INCIDENTAL | — | PRIMARY | — |
| Time-stop (fixed exit time) | SECONDARY (HolidayFlat) | SECONDARY | SECONDARY | SECONDARY | SECONDARY | PRIMARY (05:00 daily flat) |
| Stop-only (let runners run until SL) | SECONDARY | INCIDENTAL | — | — | SECONDARY | — |
| Scale-out (partial profit-taking) | — | — | — | — | — | — |
| Pyramid (add-on positions) | — | — | — | — | — | — |
| Hedged exit (with opposite leg) | — | — | — | — | — | — |

**Coverage**: Trail-heavy, time-stop universal. Scale-out, pyramid, and hedged exits entirely absent.

**Gaps**:
- **G-D8.a — No scale-out / partial-profit strategy**. Every strategy is all-or-nothing exit (1 lot in, 1 lot out). Scale-out at 1R/2R/3R is a well-known PF-booster missing from the book. Frequency: every trade. Severity: estimated +10-20% PF improvement if applied.
- **G-D8.b — No pyramiding / position-adding logic**. Strong trends (e.g. 2024 Q3-Q4) are captured by L1 with just 1 lot. Pyramiding would 1.5x-2x the trend-year PnL.
- **G-D8.c — No paired-leg hedged exit**. Settlement Wednesday or Fed-day positions could be partially hedged with TXO options instead of flat-and-wait. Out of scope for the .pla strategies but flag-able as a missing book-level capability.

---

## 3. Top 5 Priority Gaps (Ranked)

Ranking by combined **frequency** (days/yr) × **severity** (NTD impact or strategic risk), normalized to a 0-10 score per axis.

| Rank | Gap ID | Description | Frequency (days/yr) | Severity score | Combined |
|------|--------|-------------|---------------------:|---------------:|---------:|
| **1** | **G-D1.a + G-D7.c** | **Counter-trend short / short-the-rip in bull regime** (user-identified) + overnight US-spillover short mirror | 60-100 | 9 (alpha + portfolio symmetry) | **9.0** |
| **2** | **G-D2.a + G-D5.b** | **Transition / regime-flip days** + vol-expansion timing | 70-100 | 8 (worst joint-DD days) | **8.5** |
| **3** | **G-D4.a + G-D4.b** | **Night-session single-point-of-failure (S1 only)** + night-short missing | 250 (every trading night) | 7 (single failure can decapitate night book) | **8.0** |
| **4** | **G-D7.b** | **Macro-event positioning** (Fed/CPI/NFP/TSMC) untraded | 36-40 | 7 (each event = potential 100-300 pt swing) | **7.5** |
| **5** | **G-D6.a + G-D5.a** | **Volatility-explicit strategies absent** + low-vol regime is L3-only fragile | 285 low-vol days/yr + continuous vol signal | 6 (chronic drag, not acute) | **7.0** |

### Gap #1 detail — Counter-trend short / short-the-rip

**Why #1**: This is the user's explicit identified gap, and it solves three problems at once:
- Direction symmetry (D1.a)
- Bull-regime short coverage (currently L2 only fires when bull is breaking, not within bull)
- Overnight gap-down ride (D7.c partial)

**Historical pain examples**:
- **2024-11**: Joint −$199k month in the book (P0-1 §3 quoted "biggest joint-loss months"). L1/L5/S1 long, multi-week pullback inside the AI rally. L2 sat out (no breakdown). L4 broke even (no false-breakout setup). A short-the-rip strategy would have *netted* the pullback while L1/L5 gave back.
- **2025-06**: Joint −$151k month, same pattern.
- **2024-08 fat-tail joint month** (P0-2 §4.1 named this in the L2-L4 artifact list): yen-carry unwind sell-off mid-uptrend. All longs hit drawdown; no counter-trend short fired in time.

**Estimated frequency**: pullbacks ≥1.5 ATR inside confirmed uptrends occur 8-15 times/yr on TWII; in raw days, accounts for ~60-100 trading days.

### Gap #2 detail — Transition / regime-flip days + vol expansion

**Why #2**: P0-1 §4.4 (regime-spread analysis) showed L1↔L4 correlation **flips sign** in range regime (+0.001 bull / −0.112 range) and L1↔L3 likewise. These sign-flips happen on transition days where the book's correlation structure breaks down. No strategy is designed for these days; entries fire on stale-regime assumptions.

**Historical pain**:
- **2022 January**: bull → bear transition. L1 lost momentum but L2 hadn't ATR-confirmed yet → 3-week vacuum.
- **2026 Q1-Q2**: bear (Trump tariff) → bull (rebound) transition. L1 entered late, L2 stayed in (got squeezed).

**Frequency**: ~6-10 regime transitions × 7-10 days each = 70-100 days/yr.

### Gap #3 detail — Night-session resilience + night-short

**Why #3**: S1 is the *only* night-session strategy, and P0-2 §3.2 noted "IS negative in 50/50 and 60/40 splits — original entry logic didn't work in 2020-2023; profit is regime-driven, not skill-driven". If S1's 2024+ edge mean-reverts, the entire night session (14 hours, 58% of clock) goes uncovered.

**Severity**: Operationally, the book becomes day-session-only on the night S1 fails. That doubles drawdown velocity (no overnight diversification).

**Frequency**: Continuous (every night). The "fail" is a regime risk, not a daily one — but the exposure is daily.

### Gap #4 detail — Macro-event positioning

**Why #4**: 36-40 scheduled releases/yr where edge exists from either *positioning into* or *fading the first 30 min after*. Currently all 6 strategies treat these days as "normal technical days" — they enter on whatever signal fires, which means the strategy is *vulnerable to* the release rather than *trading* it.

**Examples**:
- 2025-04-02 (Trump tariff "Liberation Day"): L4 caught it incidentally with $273k. A purpose-built event-fade would have caught it deliberately with sizing.
- TSMC ex-div quarterly: TXF1 typically opens with mechanical down-shift; no strategy captures this.

**Frequency**: 40 events/yr × 1 high-leverage day each = 40 days/yr.

### Gap #5 detail — Volatility-explicit + low-vol fragility

**Why #5**: Chronic, not acute. Low-vol grind days (~285/yr) leave the book over-reliant on L3 (PSR 0.884, borderline). No strategy uses BBand width, ATR percentile, or realized-vol cone as primary entry signal — meaning the **structural cycle of vol contraction → expansion → contraction is not directly monetized**.

**Frequency**: ATR percentile crosses are continuous. Low-vol days = ~285/yr.

---

## 4. Candidate Strategy Concepts per Gap

Naming convention: `S{NN}_{ShortName}` continuing from S15 (last archived research strategy). All candidates are new slots, no existing strategy modified.

### Gap #1 — Counter-trend short / short-the-rip

- **S16_PullbackFadeShort**: Inside a confirmed 20-day uptrend, short the first 15M bar that closes below the prior swing high after an RSI(14) reading > 70. Exit on either (a) RSI < 50, (b) re-break of swing high, or (c) 3-bar time stop. Target the *intraday pullback*, not the regime change. — Direct fill for user's stated gap.
- **S17_OvernightGapDownShort**: When TXF1 night open gaps down >0.5% on a US-weak catalyst, ride the gap-down momentum for the first 90 minutes of night session. Mirror of S1 logic, short-side. — Partial coverage of D7.c.

### Gap #2 — Transition / regime-flip + vol expansion

- **S18_RegimeShiftBreakout**: Use a 60-day MA slope reversal + ATR(20) percentile crossing 50→75 as composite signal. Enter in the direction of the new slope on first 60M close-bar confirmation. Stop = prior ATR low. — Captures regime turns deliberately rather than incidentally.
- **S19_BBandSqueezeRelease**: Bollinger Band width contracts below 20th percentile for 5+ bars, then releases (close outside band). Long or short in direction of release. — Vol-expansion timing, direction-agnostic.

### Gap #3 — Night-session resilience + night-short

- **S20_NightFadeShort**: Mirror of S1. Night ORB (15:00-16:30 range), if price closes *below* the ORB low after a US-weak overnight, short on next bar with ATR stop and 05:00 daily flat. Reduces S1 single-point risk *and* covers G-D4.b.
- **S21_NightMeanReversionBoth**: If night session extends >2 ATR from VWAP in either direction within first 3 hours, fade back to VWAP. Bidirectional, smaller size. — Defends against S1's gap-momentum failure mode while staying in same session.

### Gap #4 — Macro-event positioning

- **S22_FedDayFade**: On FOMC announcement days (calendar lookup), wait for first 30 min post-2:00 AM TW time, then fade the initial move if it exceeds 1 ATR. 1-hour time stop. — Highest known event-day edge in S&P literature, plausibly portable to TWII via correlation.
- **S23_TSMCExDivShort**: On TSMC ex-dividend day (4/yr), short TXF1 open and exit at 11:00. Mechanical edge from dividend reflection in index. — Cleanest event arb in TW market.

### Gap #5 — Volatility-explicit + low-vol fragility

- **S24_LowVolBreakoutWaiter**: In low-vol regime (ATR pctile < 25), wait for the first bar that prints ATR > 75th pctile, then enter in direction of bar. Long or short. — Direct play on vol expansion off compressed base.
- **S25_VolConeMeanRev**: When realized 20-day vol exceeds 90th percentile, fade extreme moves back toward 20-day vol mean. — Counter-cyclical to S24.

---

## 5. Cross-Gap Synergies

Mapping candidates to gaps they address (primary / secondary):

| Candidate | Gap #1 | Gap #2 | Gap #3 | Gap #4 | Gap #5 |
|-----------|:------:|:------:|:------:|:------:|:------:|
| S16 PullbackFadeShort | **P** | s | — | — | — |
| S17 OvernightGapDownShort | **P** | — | **P** | — | — |
| S18 RegimeShiftBreakout | s | **P** | — | — | s |
| S19 BBandSqueezeRelease | — | **P** | — | — | **P** |
| S20 NightFadeShort | **P** | — | **P** | — | — |
| S21 NightMeanReversionBoth | — | — | **P** | — | s |
| S22 FedDayFade | s | s | — | **P** | — |
| S23 TSMCExDivShort | — | — | — | **P** | — |
| S24 LowVolBreakoutWaiter | — | s | — | — | **P** |
| S25 VolConeMeanRev | — | — | — | — | **P** |

**Highest-leverage candidates** (cover ≥2 gaps as PRIMARY):
- **S17 OvernightGapDownShort** — covers Gap #1 + Gap #3 (direction symmetry **and** night-session resilience)
- **S20 NightFadeShort** — covers Gap #1 + Gap #3 (same logic, different trigger flavor)
- **S19 BBandSqueezeRelease** — covers Gap #2 + Gap #5 (transition timing **and** vol-explicit)

**Pair recommendation for portfolio**: If only 2-3 new strategy slots will be greenlit through the institutional 10-dim review, the highest expected coverage uplift per slot comes from:
1. **S16 PullbackFadeShort** (direct fix to stated gap, isolated test)
2. **S17 OvernightGapDownShort** (double-duty: gap #1 + gap #3)
3. **S19 BBandSqueezeRelease** (double-duty: gap #2 + gap #5)

These three together would lift coverage from 3 dimensions adequately filled (D1/D6/D8 by existing book) to 6 dimensions (adding D2 transition / D4 night-resilience / D5 vol-regime).

### Anti-synergies / cannibalization risk

- **S20 NightFadeShort** and **S17 OvernightGapDownShort** both fire on US-weak nights → potentially highly correlated; if both built, would need correlation cap.
- **S22 FedDayFade** and **S18 RegimeShiftBreakout** could fire opposite directions on the same FOMC day → require precedence rule.
- **S24 LowVolBreakoutWaiter** is conceptually similar to **L5 BreakoutLong** (both wait for box-expansion); needs explicit ATR-percentile gate to differentiate from L5's box-breakout trigger.

---

## 6. Methodological Caveats

- **Frequency proxies are calendar-based**, not trade-count-based. A strategy could be PRIMARY in a regime but only fire 5 times/yr (e.g. L2 in bear). Severity ranking partially compensates.
- **2020-2026 data is bull-biased** (P0-2 §3.4: every WFE > IS). Gap #1 severity may be understated because the book's bull-period drawdowns (the exact pain that counter-trend shorts solve) are themselves the dataset.
- **Range-regime data is COVID-only** (74 days, all 2019-12 ~ 2020-06). Any candidate that targets range or low-vol regimes (S19, S24, S25) cannot be reliably backtested on the existing dataset — they need synthetic 2020-replay tests before sizing.
- **No options / hedging dimension considered**. The book is futures-only by current scope; D8.c (hedged exit) is a flag, not a candidate, until that scope expands.
- **Candidate proposals are 1-line concepts, not designed strategies**. Each must pass the institutional 10-dim framework before any live promotion — particularly D3 (correlation < 0.7 with existing 6), D6 (WFE > 50%), D7 (PF > 1.0 in all three regimes).

---

## 7. Recommended Next Step

Run a **P1 Concept Triage** on the 10 candidates above with this gate:
1. **Estimable backtest** (data exists for the trigger condition in 2020-2026)
2. **Trigger fires ≥100 times** in 6 years (institutional D5 sample-size gate)
3. **Concept-correlation with existing 6 ≤ 0.5** at the daily level (lower than the 0.7 institutional cap, since concept-stage uncertainty is wider)

Candidates passing all three move to Phase 1 sensitivity scan. Expected pass-rate: 4-6 of the 10.

The user's stated gap (#1) is the natural starting point — S16 + S17 first, then re-evaluate the dimensional coverage map with those two added before launching candidates #18+.

---

_Compiled 2026-06-19 from P0-1 correlation matrix, P0-2 walk-forward stability, L4_portfolio_role, institutional_risk_framework, settlement constitution, and all 6 live/live_simulation .pla designs. No existing strategy modified. All candidate names start at S16 to continue the existing research-archive numbering (last was S15)._
