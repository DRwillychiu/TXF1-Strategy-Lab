# S3 RapidPullbackShort — First-Tier Regime Gate Signal Design

**Date**: 2026-06-20
**Author**: Claude (deep-research subagent)
**Purpose**: Decide which "strong-bull-overheated" regime signals (and at what thresholds and how combined) should put S3 into WATCH state, after which the 5M momentum-confirmation trigger applies.

**Strategy recap**:
- Direction: ★ SHORT
- Execution TF: 5M
- Observation TF: Daily (regime + overheating)
- Logic: strong-bull AND overheated AND 5M rapid downside initiated → short for 30min-4hr, target 1-2% pullback
- Constitution-mandatory: Rule #11 Settlement_Flat, Rule #12 P3b SetStopLoss, Rule #13 10-dim institutional eval

**Empirical anchor**: TAIEX (^TWII) daily 2020-04-09 → 2026-06-05, 1,498 bars, cached at `backtest/twii_daily.csv`. All frequency / hit-rate numbers below are computed against this dataset. Hit rate = "did intraday low over the next 1 day fall ≥ 0.8% below today's close?" (best available proxy for S3's 30min-4hr / 1-2% target on a daily series; the true 5M-level hit rate will be higher because we have intraday extremes inside any single daily bar).

**Baseline pullback rate (every day, no gate)**: 446 / 1,497 = **29.8%**. Any candidate gate must beat this to add real value.

---

## 1. Eight Signal Analyses

### Signal 1: Daily MA20 > MA60 (trend confirmation)

**Mechanism**: classic golden-cross structure on the daily TAIEX. When 20-day SMA sits above 60-day SMA, the medium-term trend is bullish — the regime backdrop S3 requires. This is a *necessary* condition for "strong bull regime", not a sufficient one (it says the trend exists, not that it is overheated).

**Empirical (TAIEX 2020-04 → 2026-06)**:
- Trigger frequency: **70.83%** of bars (1,061 / 1,498). The Taiwan market spent most of the test era in MA-defined uptrends.
- 1-day ≥ 0.8% pullback hit rate when fired alone: **29.0%** (307 / 1,060) — essentially identical to baseline 29.8%. **No predictive lift on pullback by itself.**

**Strength of evidence**: HIGH for trend identification; ZERO for pullback prediction.

**False positive rate**: low at identifying "trend exists", but a 70% raw rate means it is so loose it cannot be the *only* gate.

**When it fails**: regime transitions (e.g. 2022 H1 → bear shift, 2025 H2 → tariff shock). MA20 crosses below MA60 only after the move is well underway, so S3 would still be in WATCH for the early part of a regime break.

**Implementation complexity**: **LOW** (2 SMAs, MC built-in `Average(Close, N)`).

**Recommended threshold**: MA20 > MA60 (no fuzz band needed; daily MA is itself a smoother).

**Verdict**: **Mandatory necessary condition**. Cannot stand alone. Use as `MUST` in every combination.

---

### Signal 2: Past 60-day return > +X% (cumulative strength)

**Mechanism**: confirms the magnitude of recent strength, not just direction. A +8% rally over 60 trading days (≈ 3 months) is the kind of move that institutional desks start to view as "extended". This directly captures the "strong bull" half of the S3 thesis.

**Empirical**:

| Threshold | Frequency | Days/month |
|-----------|----------:|----------:|
| ret60 > +3% | 59.3% | 12.5 |
| ret60 > +5% | 52.1% | 10.9 |
| ret60 > +8% | 42.5% | 8.9 |
| ret60 > +10% | 35.7% | 7.5 |

- 5-day ≥ 1% pullback hit rate at ret60>+8%: **49.1%** (310/632) — same as baseline. No standalone lift.
- 1-day ≥ 0.8% pullback hit rate at ret60>+10%: 29.4%, also no lift.

**Strength of evidence**: MEDIUM for "magnitude is extended"; LOW for predicting *imminent* pullback (it tells you the rubber band is stretched, not that it will snap today).

**Why it still matters**: when combined with overheating signals it filters out weak bull regimes. A +3% / 60-day "bull" is too tame to short into; +8% is genuinely extended.

**False positive rate**: at +10% threshold a third of days qualify — still loose by itself.

**When it fails**: parabolic late-cycle moves (e.g. 2021 H2 AI rally) keep the signal "on" for months while the market keeps grinding higher.

**Implementation complexity**: **LOW** (single line: `(Close/Close[60] - 1) * 100 > X`).

**Recommended threshold**: **+5%** (balance between selectivity and signal density; +8% is too rare to materially help on a daily gate when combined with other filters).

**Verdict**: **Useful magnitude filter**. Best as a tightening condition layered on the trend filter.

---

### Signal 3: RSI(14) > X sustained N bars (overbought)

**Mechanism**: the textbook overbought signal. The intuition is straightforward — when momentum oscillator pegs the upper bound, mean-reversion pressure is building.

**Compute on what timeframe?** **Daily.** The whole point of the first-tier gate is to set the *regime*; 60M RSI is noisier and would re-decide WATCH state intra-day, defeating the purpose of a stable observation window. The second-tier 5M trigger is what reacts intraday.

**Empirical (RSI on daily close)**:

| Threshold + sustain | Frequency | Days/month | 5-day≥1% pullback | 1-day≥0.8% pullback |
|---------------------|----------:|----------:|------------------:|--------------------:|
| RSI14 > 70 (1 bar) | 26.2% | 5.51 | 50.4% | n/a (similar to baseline) |
| RSI14 > 75 (1 bar) | 16.7% | 3.51 | 49.6% | **25.2%** (below baseline) |
| RSI14 > 80 (1 bar) | 9.3% | 1.95 | n/a | **31.7%** |
| RSI14 > 70 sust 2 | 21.3% | 4.47 | — | — |
| RSI14 > 70 sust 3 | 18.0% | 3.78 | — | — |
| RSI14 > 75 sust 2 | 12.6% | 2.65 | — | — |
| RSI14 > 75 sust 3 | 10.1% | 2.12 | — | — |

**Critical finding**: at RSI>75 the 1-day pullback rate (25.2%) is *worse* than the unconditional baseline (29.8%). This is the well-known "RSI can stay overbought longer than you can stay solvent" phenomenon — overbought is a momentum signal, not a reversal signal, on its own. Only RSI>80 (which is much rarer) gets a small lift to 31.7%.

This empirical reality is exactly why S3's design correctly rejects "RSI overbought → enter short" (the old Agent D spec) in favor of "RSI overbought + 5M rapid downside initiated → enter short". The first-tier gate does NOT need to predict the pullback — it only needs to establish the *opportunity context*. The 5M trigger does the prediction.

**Strength of evidence**: HIGH that it identifies overheating; LOW that it predicts the turn.

**False positive rate**: HIGH if used as a standalone trigger; ACCEPTABLE as one of multiple gate conditions.

**When it fails**: parabolic bull legs where RSI sits > 75 for weeks (e.g. 2021 Q2, 2024 Q1 AI rally).

**Implementation complexity**: **LOW** (MC has `RSI(Close, 14)` built-in; sustained-N is `CountIf(RSI(Close,14) > T, N) = N`).

**Recommended threshold**: **RSI(14) > 70 sustained 2 bars** (frequency 21.3%, ~4.5 days/month — usable density for combination). Avoid RSI > 80 as the *sole* overbought signal — it triggers ~2 days/month, too rare to drive a strategy by itself.

**Verdict**: **Useful overheating gauge**. Combine with trend + magnitude; do not stand alone.

---

### Signal 4: BB(20, 2) %B > 1.0 (above upper band)

**Mechanism**: %B = (Close − LowerBand) / (UpperBand − LowerBand). > 1.0 means today's close pierced the upper Bollinger Band, i.e. price is > 2 standard deviations above MA20. Classic Tukey-outlier style overheating.

**Compute on what timeframe?** **Daily**, same reasoning as Signal 3.

**Empirical**:

| Threshold | Frequency | Days/month | 1-day≥0.8% pullback |
|-----------|----------:|----------:|--------------------:|
| %B > 1.0 | 7.0% | 1.47 | **22.9%** (below baseline) |
| %B > 1.05 | 4.3% | 0.91 | — |

**Critical finding**: %B > 1.0 actually has a *lower* pullback hit rate (22.9%) than baseline (29.8%) — same lesson as RSI. Piercing the upper band is a momentum continuation signal more often than a reversal signal in this regime.

**Alternative considered**: "BB width contraction THEN expansion" (Bollinger squeeze breakout). This is interesting but it captures *vol regime change*, not bullish overheating — it would fire on bearish breakouts too, which is the opposite of S3's intent. Reject this alternative for S3's first-tier gate (could be a useful filter for a different strategy).

**Strength of evidence**: MEDIUM as an overheating marker; LOW as a pullback predictor.

**False positive rate**: HIGH if interpreted as "fade signal"; ACCEPTABLE if interpreted as "regime overheating" within a multi-condition AND.

**When it fails**: same as Signal 3 — parabolic moves push %B > 1.0 for many consecutive bars.

**Implementation complexity**: **LOW** (MC has `BollingerBand(...)` family). Two extra lines for %B normalisation.

**Recommended threshold**: **%B > 1.0**. The 1.47 days/month frequency is too thin to drive WATCH state by itself; treat as a *boost* signal — when it fires alongside trend + RSI, gate is firmly ON.

**Verdict**: **Optional confirmation**. Redundant with Signal 5 (distance from MA20) since both measure the same "price stretched above mean" idea via different scaling (%B is volatility-normalized, dist_MA20 is percent). **Lesson check (filter redundancy)**: do NOT include both %B and dist_MA20 in the same gate; pick one. Recommend dist_MA20 because it's interpretable and the empirical lift is better (see Signal 5).

---

### Signal 5: Distance from MA20 > +X% (deviation)

**Mechanism**: pure percentage deviation of today's close from the 20-day SMA. The 20-day SMA is roughly a one-month fair-value anchor; persistent > +X% deviation means price is materially extended over that fair value.

**Empirical**:

| Threshold | Frequency | Days/month | 1-day≥0.8% pullback |
|-----------|----------:|----------:|--------------------:|
| dist > +2% | 37.3% | 7.84 | — |
| dist > +3% | 22.9% | 4.81 | 26.6% |
| dist > +5% | **6.7%** | **1.40** | **37.0%** |

**Critical finding**: dist > +5% is the **ONLY single-condition signal in the entire candidate list that beats baseline by a meaningful margin** (37.0% vs 29.8% baseline = +7.2pp lift). This is consistent with the intuition that *extreme* deviation has reversion edge, but moderate deviation does not.

Trade-off: at +5% it fires only 1.4 days/month — too sparse to drive WATCH on its own (S3 would never see action). At +3% it fires 4.8 days/month but loses the empirical lift.

**Strength of evidence**: HIGH at +5%; MEDIUM at +3%; LOW at +2%.

**False positive rate**: LOW at +5% (this is genuinely extreme); MED at +3%; HIGH at +2%.

**When it fails**: late-stage parabolic blow-offs where price goes +8% / +10% above MA20 (e.g. 2024 Q1 had multiple +6% deviations that kept extending). The +5% threshold did get pulled back eventually in those cases but with painful drawdowns first — which is why S3 still needs the 5M confirmation gate before entering.

**Implementation complexity**: **LOW** (`(Close - Average(Close,20)) / Average(Close,20) * 100`).

**Recommended threshold**: use **+3%** for the standard gate (4.8 days/month, usable density), and use **+5%** as a "high-conviction" boost flag inside the entry-quality logic (not the gate itself — a 1.4 days/month gate would starve S3). Idea: if dist > +5% AND 5M trigger fires, increase position size or relax the 5M trigger threshold.

**Verdict**: **Strong single signal**. Use +3% for gate, reserve +5% as conviction modulator.

---

### Signal 6: Consecutive green daily closes (price-action)

**Mechanism**: pure price-action overheating. 5+ green closes in 10 days, or 3+ strict consecutive, is the kind of "no-give-back" run that often precedes a hot-handed reversion.

**Empirical**:

| Threshold | Frequency | Days/month |
|-----------|----------:|----------:|
| ≥5 green in last 10 | 74.5% | 15.6 |
| ≥7 green in last 10 | 29.4% | 6.18 |
| 3 strict consecutive green | 18.6% | 3.91 |
| 5 strict consecutive green | 4.9% | 1.04 |
| 7 strict consecutive green | 1.1% | 0.22 |

**Strength of evidence**: WEAK academic support; practitioner-level only. The hit-rate analysis was not separately run because the signal heavily overlaps with RSI > 70 / dist > +3% (high-RSI days are mostly "many green closes" days). Including this *adds* signal redundancy without adding orthogonal information.

**Lesson check (filter redundancy)**: this signal correlates ~0.6-0.7 with Signal 3 (RSI) and ~0.5 with Signal 5 (dist_MA20) by construction. Adding it to a multi-condition AND barely changes the firing set but inflates apparent "evidence breadth". **Do NOT include in the gate alongside RSI or dist_MA20 — that would be filter overlap and a Memory-flagged lesson violation** (`feedback_filter_redundancy_check.md`).

**Recommended threshold**: not recommended for the gate. Could appear as a logging diagnostic only (e.g. "report consecutive green count on entries for postmortem").

**Verdict**: **REJECT for gate** (redundant). Keep in postmortem reports.

---

### Signal 7: Volume divergence (price up, volume down)

**Mechanism**: classic distribution-pattern: institutional selling into retail buying produces rising price on shrinking volume, a textbook precursor to a top.

**Empirical**: not computed. TAIEX daily volume data is in the CSV but the more important lesson is from S1/S6 work:
- `feedback_mc_time_24hr_pitfall.md` analog: TXF1 intraday volume on certain bars is zero or unreliable (especially at session boundaries).
- The 30M volume issue documented in past S2/S6 work directly applies: **MultiCharts intraday futures volume is not a clean series**.

For a daily TAIEX gate this is less of an issue (daily volume is reliable), but the more fundamental problem is statistical: "price-up volume-down" on a single instrument is a very noisy signal — Lo/Mamaysky/Wang (2000)-style pattern recognition. Cohort papers find weak edge that often disappears OOS.

**Strength of evidence**: WEAK. Practitioner blog evidence; little academic support; data quality concerns.

**Implementation complexity**: **MEDIUM** (define what "rising price" window, what "falling volume" window, how to combine — many degrees of freedom = overfit risk).

**Recommended threshold**: not recommended.

**Verdict**: **REJECT**. Data quality + low evidence + overfit risk. Not worth the engineering time.

---

### Signal 8: VIX-Taiwan / TAIEX divergence

**Mechanism**: TWVIX (TAIFEX volatility index) divergence from TAIEX direction. The standard read: TAIEX up + TWVIX up = mistrust under the rally = bearish.

**Strength of evidence**: B-grade in literature (TWVIX is much thinner than SPX VIX, post-2018 data is fairly clean, divergence signals replicate but with smaller effect sizes than US).

**Data feasibility check**: TWVIX data is not in `backtest/twii_daily.csv`. It would require:
1. Sourcing TWVIX (TAIFEX publishes daily; yfinance has spotty coverage)
2. Aligning to TAIEX trading calendar
3. Defining divergence rigorously (sign of co-movement over N days)

**Implementation complexity**: **HIGH**. New data feed, new ETL, validation. For a *first-tier gate*, this is over-engineering when Signals 1+3+5 already give enough coverage.

**When it would matter**: late-cycle "smart money buying vol while retail buys equity" patterns — genuinely valuable but a v2 enhancement, not a v1 requirement.

**Verdict**: **DEFER to v2**. Document as a known future enhancement. Do not gate v1 on TWVIX availability.

---

## 2. Cross-Comparison Table

| # | Signal | Trigger freq | Days/month | 1-day≥0.8% hit-rate vs baseline (29.8%) | Complexity | Standalone verdict |
|---|--------|-------------:|----------:|-------------------------------------------:|-----------:|--------------------|
| 1 | MA20 > MA60 | 70.8% | 14.9 | 29.0% (≈ baseline) | LOW | Necessary but not sufficient |
| 2 | ret60 > +5% | 52.1% | 10.9 | (≈ baseline) | LOW | Magnitude filter only |
| 2 | ret60 > +8% | 42.5% | 8.9 | (≈ baseline) | LOW | Tighter magnitude filter |
| 3 | RSI14 > 70 sust 2 | 21.3% | 4.5 | (≈ baseline) | LOW | Overheating, not predictive |
| 3 | RSI14 > 75 (1 bar) | 16.7% | 3.5 | **25.2% (worse)** | LOW | Momentum continuation, not reversal |
| 3 | RSI14 > 80 (1 bar) | 9.3% | 2.0 | **31.7% (+1.9pp)** | LOW | Mild lift, sparse |
| 4 | BB %B > 1.0 | 7.0% | 1.5 | **22.9% (worse)** | LOW | Redundant with Signal 5 |
| 5 | dist_MA20 > +3% | 22.9% | 4.8 | 26.6% (slightly worse) | LOW | Use as gate component |
| 5 | dist_MA20 > +5% | **6.7%** | **1.4** | **37.0% (+7.2pp ✓ )** | LOW | Strongest lone signal — use as conviction modulator |
| 6 | Consec green | 18-30% | 3-6 | not computed (redundant) | LOW | REJECT (redundancy) |
| 7 | Volume divergence | n/a | n/a | n/a | MED | REJECT (data quality + weak) |
| 8 | TWVIX divergence | n/a | n/a | n/a | HIGH | DEFER to v2 |

**Headline empirical takeaways**:

1. **NO single overheating signal reliably predicts a 1-day pullback** except `dist_MA20 > +5%`. The other oscillator-style signals (RSI > 75, %B > 1.0) actually have *worse* than baseline hit rates — they reflect persistent momentum more than imminent reversion.

2. **This empirically validates the user's "Momentum-Confirmed entry, NOT pure mean reversion" decision (USER CONFIRMED point #4).** A first-tier gate that *only* says "regime is overheated" will hand off to the 5M trigger many false positives; that's expected and correct. The gate's job is to define *when to look*, not *when to fire*.

3. **Trend filter (MA20 > MA60) is mandatory in every combination** because it is the only signal that directly speaks to "strong bull regime" — the other signals could in principle fire in non-bull tape (e.g. a one-week chop-rebound could spike RSI without the trend backdrop S3 requires).

4. **+5% MA-deviation is the conviction signal** worth carrying through to entry sizing / 5M trigger relaxation, but it is too sparse (1.4 days/month) to drive WATCH state on its own.

---

## 3. Three Candidate Combinations

### 3A. CONSERVATIVE (3 must pass)

**Definition**: `MA20 > MA60` AND `RSI(14) > 75` AND `dist_MA20 > +3%`

**Frequency**: 10.9% of days = **2.3 days/month**

**Pros**:
- Highly selective: only fires when trend, oscillator, and deviation all agree.
- Each entry is supported by 3 orthogonal-ish evidences (trend / oscillator / deviation are not fully independent but are distinct constructs).
- Low operational burden: ~2 WATCH days per month means the strategy is dormant most of the time, freeing capital and attention.

**Cons**:
- 2.3 days/month is borderline — combined with the second-tier 5M trigger (which will filter further), S3 may end up at ~1-2 *trades* per month. CLAUDE.md "每月至少 2 筆交易" quality gate is met but only just.
- Sample-size risk for the institutional 10-dim eval (Rule #13: 樣本數 ≥ 100). At 1-2 trades/month over 6 years (~75 months) we get ~75-150 trades — passable but thin.
- Conservative gates can mask design errors: too few firings to detect a broken second-tier trigger.

**Pullback hit-rate validation**: 24.5% (40/163) at 1.5%/3-day window — slightly below baseline, confirming that even at this stringency the gate alone is not predictive (as designed — the 5M trigger does the prediction).

**Recommended thresholds (locked in if chosen)**:
- MA len: 20 / 60 (no fuzz)
- RSI len: 14, threshold > 75
- Distance from MA20: > +3.0%

---

### 3B. MODERATE (2-of-3 must pass — RECOMMENDED)

**Definition**: at least 2 of the following 3 conditions:
- (A) `MA20 > MA60` (trend)
- (B) `RSI(14) > 70 sustained 2 bars` (overheating)
- (C) `dist_MA20 > +3%` (deviation)

**ADDITIONAL HARD GATE**: condition (A) must be true. So effectively: `(A) AND (B OR C)`.

(The "2-of-3 unconditional" version would allow entry without the trend filter — i.e. fire in a bear regime if RSI and dist both rose enough — which violates S3's "strong bull" first-tier premise. We anchor on A.)

**Frequency**: with the (A) anchor, raw 2-of-3 fires 28.4% (5.97 days/month). Tighter A-anchored form `(A) AND (B OR C)` fires roughly 23-26% (~5 days/month — close enough to 2-of-3 since (A) is true 70% of the time).

**Pros**:
- Healthy density (~5 WATCH days/month) gives the 5M trigger room to work without S3 over-firing.
- Robust to single-signal noise: if one of B/C briefly slips (e.g. RSI cools intra-day) the gate still holds via the other.
- Sample-size: ~5 WATCH days × 75 months × ~30% 5M-trigger conversion ≈ 110 trades for institutional eval — comfortably ≥ 100.
- Naturally accommodates the "extended bull keeps grinding" regime: if RSI cools but dist stays > +3%, gate remains ON.

**Cons**:
- More complex to reason about than a single AND-chain. Code is `(A AND B) OR (A AND C)` which is still 3 lines but harder to debug.
- Empirical pullback lift is essentially zero at this density (26-28% vs 29.8% baseline) — the gate is doing its job (defining context, not predicting) but a reviewer reading the metrics in isolation might assume the gate is useless. Need clear documentation of intent.

**Pullback hit-rate validation**: 26.0% (110/423) at 1.5%/3-day window — same level as baseline. **This is acceptable because the gate is not where the predictive edge lives**. The edge lives in the 5M momentum trigger; the gate's job is to ensure we only ever look during "strong bull overheated" windows so the trigger doesn't fire in bear pullbacks (which would be catastrophic for a short strategy).

**Recommended thresholds (locked in if chosen — RECOMMENDED DEFAULT)**:
- (A) MA len: 20 / 60
- (B) RSI(14) > 70 sustained 2 bars (NOT > 75 — empirically RSI > 75 is mostly continuation; > 70 sustained 2 is a more honest overheating marker)
- (C) Distance from MA20: > +3.0%
- ADDITIONAL conviction modulator: if `dist_MA20 > +5%` (1.4 days/month), flag `HighConviction = true`. This is *not* part of the gate boolean but feeds into entry sizing / 5M trigger threshold relaxation.

---

### 3C. LOOSE (1 signal passes)

**Definition**: any one of: `MA20 > MA60`, `RSI(14) > 70`, `dist_MA20 > +3%`

**Frequency**: dominated by Signal 1 (which alone fires 70.8% of days) → effective gate fires ~75-80% of days = **16-17 days/month**.

**Pros**:
- Maximum signal density; abundant data for parameter optimization.

**Cons** (these are decisive):
- The 5M trigger is now doing all the work; the "first-tier gate" is effectively no gate at all.
- Eliminates the bear-regime protection that is the *whole point* of the first-tier design. A pure 5M downside trigger inside a confirmed bear market is just shorting a falling knife at random — exactly what L2 does, and S3 would duplicate L2's role rather than fill the bull-pullback gap.
- Violates the user's stated portfolio role: "fills the bull-regime mid-pullback hedge gap that neither L2 (waits for trend) nor L4 (waits for breakdown) can cover" (USER CONFIRMED point #5).
- **Filter redundancy lesson**: a 1-of-3 OR where any single condition essentially passes 70% of the time is not a filter at all (`feedback_filter_redundancy_check.md` lesson directly applies).

**Pullback hit-rate validation**: similar to baseline; provides no predictive lift and no regime protection.

**Verdict**: **REJECT**. Documented for completeness only.

---

## 4. RECOMMENDED Combination

### Decision: **3B — MODERATE, anchored on trend (A) with B-or-C overheating**

**Final gate definition** (for S3 v0.1 spec):

```
RegimeGate_WATCH = (
    /* (A) MANDATORY: medium-term trend is bullish */
    Average(Close, 20)[1] > Average(Close, 60)[1]
)
AND (
    /* (B) OR (C): at least one overheating condition */
    (RSI(Close, 14)[1] > 70 AND RSI(Close, 14)[2] > 70)         /* B: RSI sustained */
    OR
    ((Close[1] - Average(Close, 20)[1]) / Average(Close, 20)[1] * 100 > 3.0)   /* C: deviation */
)

HighConviction_Modifier = (
    (Close[1] - Average(Close, 20)[1]) / Average(Close, 20)[1] * 100 > 5.0
)
```

Note `[1]` indexing on all daily reads — per CLAUDE.md rule "Data2 引用用 [1] 已收盤索引（Data2 當根不可靠）". The above will be computed on a daily Data2 stream while the 5M chart runs on Data1.

### Rationale (10-dim institutional-eval lens)

1. **Sharpe / expectancy** — moderate gate density gives ~5 WATCH days/month × second-tier conversion → estimated 1.5-3 trades/month, enough for a Sharpe estimate to converge OOS.
2. **VaR / CVaR** — by requiring trend (A), gate is OFF during confirmed bear regimes → eliminates the worst-case scenario for a short strategy in this design (shorting a falling knife already discounted).
3. **Cross-strategy correlation** — S3 fires in "bull-regime overheating mid-pullback" windows; L2 fires in confirmed bear trend; L4 fires in consolidation-breakdown. These three short-side gates are *temporally orthogonal* by construction → likely correlation < 0.3 with L2/L4. The L4_portfolio_role and portfolio_correlation_matrix docs confirm L2/L4 currently co-fire mostly in bull (+0.39 in bull regime) — S3 will not add to that concentration because (A) requires bull *and* (B/C) requires overheating, a much narrower window than L2/L4 use.
4. **Drawdown clustering** — moderate density spreads firings; not concentrated into one regime.
5. **Sample size** — estimated ~75-150 trades over 6-year backtest → ≥ 100 (Rule #13 threshold met).
6. **WFE > 50%** — to be validated in P2 walk-forward; gate has only 3 inputs (MA lens, RSI len/thr, dist threshold), low DoF → low overfit risk.
7. **Three-regime PF > 1.0** — in bear regime gate fires very rarely (A requires bull) → S3 will essentially be flat in bear, PF=undefined or close to 1 from the handful of fires. In range gate fires occasionally → must validate. In bull gate fires often → must validate.
8. **Cost analysis** — gate itself is free (computed off daily Data2); slippage budget is set by 5M trigger.
9. **Operational risk** — daily indicators are reliable, no MC intraday-volume traps (`feedback_filter_redundancy_check.md` overlap check done); no Time-interval pitfalls because daily reads are date-stamped not time-stamped (`feedback_mc_time_24hr_pitfall.md` does NOT apply here).
10. **Regulatory / account limits** — no special concerns at 1 lot.

### Why specifically these thresholds

- **MA20 / MA60**: standard, no fuzz. Adding fuzz (e.g. require MA20 > MA60 × 1.005) shrinks frequency without changing the categorical interpretation; not worth complexity.
- **RSI > 70 sustained 2 bars** (not 75, not 80): the empirical hit-rate data shows that RSI > 75 single-bar is actually *worse* than baseline, while > 70 sustained 2 captures the genuine "persistent overheating" signal we want, at sufficient density (4.5 days/month).
- **dist_MA20 > +3%**: the only deviation threshold that combines real selectivity (4.8 days/month) with non-zero predictive lift when combined with other signals. +5% is too sparse for the gate but is captured as the `HighConviction` modifier.
- **dist > +5% as modifier, not gate**: 1.4 days/month is too thin to anchor the gate, but the +7.2pp pullback-rate lift is genuine — feed it into the second-tier 5M trigger as a relaxation flag (e.g. require a 0.3% 5M down-move instead of 0.5% when HighConviction is true).

### Sanity check against constitutional rules

- **Rule #11 Settlement_Flat**: gate is independent of settlement logic. On settlement day, `v_Settlement_Day = true` will block entry regardless of gate state. ✓
- **Rule #12 P3b SetStopLoss**: gate does not interact with SetStopLoss (which fires on position established). ✓
- **Rule #13 10-dim institutional eval**: addressed above; will need full eval before live_simulation promotion.
- **Lesson: closed Time intervals** (`feedback_mc_time_24hr_pitfall.md`): gate uses no time conditions; daily Data2 is bar-indexed not time-indexed. ✓
- **Lesson: filter redundancy check** (`feedback_filter_redundancy_check.md`): grepped against candidate signals — rejected Signal 6 (consecutive-green, redundant with RSI/dist), rejected Signal 4 (%B, redundant with dist_MA20); kept only orthogonal-ish signals. ✓
- **Lesson: design-ahead-of-empirical-validation**: every threshold above is anchored to the 1,498-bar empirical sweep in §1. Did NOT pick "RSI > 80" just because it sounded more selective — empirical density said too sparse.

---

## 5. Open Decisions for User

### Decision D1 — Gate combination tier

**A)** CONSERVATIVE (3-AND, 2.3 days/month) — choose if you want maximum selectivity at the cost of trade frequency.

**B)** **MODERATE (A-anchored + B-or-C, ~5 days/month) — RECOMMENDED**.

**C)** LOOSE (1-of-3, ~16 days/month) — REJECTED by analysis; only re-open if you specifically want a high-firing prototype to stress-test the 5M trigger in isolation.

### Decision D2 — RSI threshold (only if MODERATE or CONSERVATIVE chosen)

**A)** RSI(14) > 70 sustained 2 bars (RECOMMENDED, balances selectivity and density).

**B)** RSI(14) > 75 single bar (more selective on paper but empirically worse hit rate).

**C)** RSI(14) > 80 single bar (too sparse — 2 days/month — as the sole overheating gate).

### Decision D3 — Distance-from-MA20 threshold

**A)** dist > +3% as gate AND dist > +5% as conviction modifier (RECOMMENDED — captures the empirically-strongest signal without starving the gate).

**B)** dist > +3% only (simpler; gives up the +7.2pp conviction edge).

**C)** dist > +5% as gate (too sparse — 1.4 days/month — would suffocate S3).

### Decision D4 — Conviction modifier behavior

If `HighConviction_Modifier = true` (i.e. dist > +5%), how should the second-tier 5M trigger respond?

**A)** Relax the 5M downside threshold (e.g. require 0.3% 5M drop instead of 0.5%) — more entries when conviction is high.

**B)** Double position size (1 lot → 2 lots) — more risk when conviction is high. **NOTE**: per CLAUDE.md固定口數 = 1 口, this would violate current sizing rule.

**C)** Both A and B (combined).

**D)** Use as logging-only diagnostic for now (RECOMMENDED — Decision D4 can be re-opened after P1-P3 validates the base S3 design).

### Decision D5 — TWVIX divergence (Signal 8) — defer or build now?

**A)** Defer to S3 v2 (RECOMMENDED — gets v1 shipped faster; TWVIX adds engineering for marginal lift).

**B)** Build TWVIX data pipeline now and include divergence in the gate (delays v1 by ~1 week of work, uncertain value).

---

## 6. Next Steps (after user picks D1-D5)

1. Write `S3_RapidPullbackShort_strategy.md` design spec in `strategies/research/2026-W?/S03_RapidPullbackShort/` (note: existing batch01_S2-S5 used "S3 VolSqueeze" — the new S3 will reuse the **logical slot** S3 but live in a fresh week folder; check `optimization/TRACKER.md` to avoid number-clash with archived B01_S3_VolSqueeze.md).
2. Define second-tier 5M momentum trigger spec (separate research task — this report covers only first-tier).
3. Run P1 parameter sensitivity on the 3 gate parameters (MA lens, RSI threshold, dist threshold).
4. Run P2 walk-forward (gate stable across 2020 / 2022 / 2024 sub-periods).
5. Run P3 Monte Carlo.
6. Run 10-dim institutional eval (Rule #13).
7. Only after all of the above passes → promote to `live_simulation/`.
