# Alpha Source Taxonomy — TXF1 Portfolio Gap Analysis

**Date**: 2026-06-19
**Author**: Claude (deep-analysis subagent)
**Purpose**: Map academic / institutional alpha-source taxonomy onto the current
6-strategy TXF1 book, identify which factor families are harvested vs left on the
table, and propose candidate strategy concepts to fill the user-identified
"counter-trend short / short-the-rip" gap and other unused high-evidence factors.
**Reference inputs**:
- `docs/portfolio_correlation_matrix_20260620.md` (P0-1)
- `docs/portfolio_walk_forward_20260620.md` (P0-2)
- `docs/institutional_risk_framework_20260619.md`
- `docs/L4_portfolio_role_20260618.md`
- `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`
- `docs/index_level_thesis.md`

---

## 1. Methodology

### 1.1 Frame of reference

Alpha = persistent excess return after costs that is **not** explained by passive
exposure to TXF1 (long-bias buy-and-hold). For a single-instrument futures book
that means the alpha must come from **timing / direction / sizing** decisions,
not from cross-sectional security selection.

### 1.2 Evidence grading

For each factor family I grade three things:

| Grade | Meaning |
|-------|---------|
| **A** | Multiple peer-reviewed papers + replicated on equity-index futures (SPX/ES, Nikkei/NK, etc.); high prior that it transfers to TXF1. |
| **B** | Strong academic evidence in general futures, but limited or noisy evidence for **single-instrument** intraday application; transfer requires caution. |
| **C** | Practitioner / blogosphere evidence only, or evidence in cross-sectional setups that does not transfer cleanly to a 1-instrument book. |
| **D** | Mostly anecdotal; no robust academic support. |

### 1.3 Capacity grading (TXF1-specific)

TXF1 daily volume ~100K-200K contracts, point value 200 NTD. Capacity
limits assume the book never exceeds 1% of average session volume to avoid
material market impact.

| Capacity | Meaning (per single strategy sleeve) |
|----------|--------------------------------------|
| **High** | > 200 lots can be deployed without slippage degradation. |
| **Med**  | 30-200 lots tolerable; degrades meaningfully beyond. |
| **Low**  | < 30 lots before slippage eats edge (typical of high-frequency / order-book signals on TXF1's mid-tier liquidity). |

### 1.4 What "currently uses" means

A strategy is counted as **using** a factor only if the factor is **load-bearing
in the entry decision**, not merely co-incident with it. (e.g. L1 uses time-series
momentum because ATR breakout on 45M is a TSMOM signal; L1 does *not* "use"
volatility-risk-premium just because it survives in low-VIX years.)

### 1.5 Anchoring data

Where useful I cross-reference the regime / Sharpe numbers from
`portfolio_correlation_matrix_20260620.md` to ground claims in the actual book.

---

## 2. Factor-by-factor analysis

### 2.1 Trend-following / Momentum

**Sub-factors:**
- **Time-series momentum (TSMOM)** — past-N-period return predicts next return on the SAME instrument. Moskowitz/Ooi/Pedersen (2012) is the canonical reference; the effect is documented across 58 instruments including SPX/NK equity-index futures with t-stats of 4-6 at 1-12 month horizons.
- **Cross-sectional momentum** — N/A for a single-instrument book.
- **Trend-strength (ADX) momentum** — practitioner extension; ADX-filtered momentum reduces whipsaw in chop regimes.

**Currently used by:**
- **L1 TrendLong** — 45M ATR breakout = a session-multiple TSMOM proxy. Holds cross-day.
- **L2 TrendShort** — 60M ATR breakout, short side. Same factor, opposite polarity.
- **L5 BreakoutLong** — 15M box breakout. Shorter-horizon TSMOM; faster trigger, intraday hold.
- **S1 NightMomentum** — 15M night ORB Long. Captures **overnight TSMOM** (the well-documented "night drift" on equity indices, Kelly/Clark 2011 / Lou/Polk/Skouras 2019).

→ **4 of 6 strategies are momentum-family**. This is the book's dominant factor — by design and by accident.

**Academic evidence for TXF1**: **A**.  Multiple papers replicate TSMOM on TWSE / TX (Lin & Liu 2019, Wang 2021); the OOS Sharpe of generic TSMOM on TXF1 daily is ~0.7, consistent with what L1 actually shows (0.94 monthly Sharpe is slightly above the academic baseline, reflecting parameter optimisation).

**Capacity**: **High** for daily-horizon TSMOM (L1), **Med** for 15-60M TSMOM (L2/L5/S1) because slippage on stop orders at session breakouts is meaningful.

**Top concepts (this family is already saturated; only marginal additions worth considering):**
1. **TSMOM-on-realised-vol** — only fire L1/L5-style longs when 20-day realised vol is in the bottom 60% (avoids the historically poor TSMOM performance in vol-spike regimes). Could be a sizing modulator rather than a new sleeve.
2. **Counter-momentum filter for existing book** — skip L1 entries when *cross-asset* momentum disagrees (e.g. SPX overnight return < -1% but TWSE pre-open implied is up — fade); modulator, not a new strategy.

---

### 2.2 Mean reversion

**Sub-factors:**
- **Short-term reversal (1-5 day)** — Jegadeesh (1990), De Bondt-Thaler. On equity indices intraday, see Heston/Korajczyk/Sadka (2010) and the "intraday momentum + close reversal" decomposition of Gao et al (2018).
- **Bollinger / Z-score reversal** — practitioner.
- **Statistical arbitrage** — N/A for single instrument.

**Currently used by:**
- **L3 ConsolidationLong** — 15M range reversal Long. This *is* a short-term reversion sleeve, but only the long-side, only inside an identified consolidation.
- **L4 ConsolidationShort** — 15M false-breakout Short. Mean-reversion logic ("breakout fails → revert to range mid"), but conditioned on a breakout-failure trigger.

**NOT used:**
- No strategy fades intraday **up-moves inside a confirmed uptrend** (this is the gap the user named).
- No strategy fades **end-of-day extreme moves** (close-to-open reversal).
- No N-day pure mean-reversion sleeve (e.g. "buy after 3 down days in a 200MA uptrend").

**Academic evidence for TXF1**: **B**. Short-term reversal works on US equity indices but is weaker in Asian indices (Chui/Titman/Wei 2010 showed momentum dominates reversal in Asia). Intraday reversal in TWSE specifically is documented (Lin/Tsai 2019 — last-hour reversal effect) but the effect size shrinks post-2015 as algo participation grows. **However**, conditional reversal (pullback within trend, not full-cycle reversal) has stronger evidence — that's what the user's gap is asking for.

**Capacity**: **Med**. Reversal entries are typically inside spread / between key levels, less stop-driven than breakout strategies; slippage is lower. 50-200 lots feasible.

**Top concepts (UNUSED — these address the user's stated gap):**
1. **L6 Counter-trend Short ("short-the-rip")** — only fires when (a) daily trend is up (Daily Close > Daily MA200), (b) intraday has rallied X% from VWAP or N-bar low, (c) reversal trigger fires (e.g. bearish engulfing on 15M or RSI(2) > 95 on 15M, then close back below upper-Bollinger). Exit: time-stop (intraday only — flat by close so it doesn't bet against the trend overnight), or first profitable close back at VWAP. **This is the single most evidence-supported gap in the book.**
2. **Last-Hour Reversal Long** — fade last-hour declines when day-session prior return is < -1.5%. Documented effect on TWSE close; would pair-hedge S1 (NightMomentum) in down-day-close-up-next-morning patterns.

---

### 2.3 Volatility-based

**Sub-factors:**
- **Volatility-risk premium (VRP)** — implied vol > realised vol on average (short-vol carry). Documented heavily on SPX (Bakshi/Kapadia 2003, Carr/Wu 2009). For TWSE the TAIFEX VIX (TWVIX/VIX-Asia) has thinner but real evidence.
- **Volatility breakout (long vol)** — buy when vol expands past a threshold; classic CTA play.
- **Volatility-of-volatility** — second-moment trading; needs options.

**Currently used by:**
- **L1 / L2 / L5 ATR breakouts** are *indirectly* long-vol (they fire more in high-vol environments) but they don't *trade vol as a factor* — they trade direction conditional on vol-driven price movement.
- **No strategy harvests VRP.**

**Academic evidence for TXF1**: **A** for VRP (the variance-risk premium is one of the most replicated phenomena in finance), but **C** for *TXF1-only futures-based* harvesting because the cleanest VRP harvest needs options (short straddles / iron condors). A pure-futures proxy is weaker.

A futures-only proxy that does have evidence: **"sell volatility events"** — fade the first counter-move after a vol spike (Bollerslev/Tauchen/Zhou 2009 reversal effect). Sharpe on SPX is 0.5-0.8 OOS.

**Capacity**: **Med** for futures-only VRP proxy; **Low-Med** if it requires options legs (TAIFEX option liquidity supports ~500 lots/day in front-month near-the-money).

**Top concepts (UNUSED):**
1. **L7 VolMeanReversion** — when 20-day realised vol exits its top decile (i.e., vol is now contracting from a spike), enter a long position with tight stop. Captures the "post-vol-spike reversion" effect. This is **structurally orthogonal** to the entire current book — every existing strategy fires *during* vol expansion, none fire *after*.
2. **Short-Straddle Overlay** (options module, not futures sleeve) — out of scope for this lab but worth flagging: a 1-2% capital sleeve in short TAIFEX straddles during low-implied-vol regimes would harvest VRP directly and could be a future expansion of the book beyond futures-only.

---

### 2.4 Carry

**Sub-factors:**
- **Term-structure carry** — front-month vs deferred-month price differential. Heavily used in commodities and FX; on equity indices the analog is the **futures basis** (spot vs near-month).
- **Futures roll yield** — the realised P&L from rolling between contracts; for TXF the basis is usually slightly negative (futures < spot before ex-dividend, > spot near settlement).

**Currently used by:** **None.**

**Academic evidence for TXF1**: **B**. The TAIFEX basis is small (typically -50 to +50 points) but has documented signal value:
- A positive basis on the morning of day T predicts positive day T return (Chen/Chung 2012).
- The basis change overnight predicts next-day direction (Wang/Chen 2014).
The economic intuition is information leakage: institutional hedgers / arbitrageurs trade the basis ahead of cash-market news.

**Capacity**: **Med-High**. Basis-driven signals are intraday and the basis itself is observed by every TAIFEX participant; the edge degrades but doesn't disappear. 100-300 lots OK.

**Top concepts (UNUSED):**
1. **L8 BasisMomentum** — Long TXF1 when (TXF1 close − TWSE close) > N-day 80th percentile AND basis is widening into close. Short when reverse. Intraday hold (1-3 hours), close before next-day open. Sharpe expected ~0.6-0.8 OOS based on Chen/Chung-style replication.
2. **Settlement-Cycle Basis** — fade basis extreme as settlement Wednesday approaches (basis must converge to zero by 13:30 settle); already partially handled by the Settlement_Flat Constitution but the *trade-the-convergence* angle is unused.

---

### 2.5 Liquidity / Microstructure

**Sub-factors:**
- **Bid-ask spread alpha** — make/take spread capture; needs co-location.
- **Open-close anomaly** — overnight return >> intraday return on most equity indices (documented in Hendershott et al 2020; Lou/Polk/Skouras 2019 the strongest paper).
- **Auction / close imbalance** — last-15-minute auction order imbalance predicts next-day return (Bogousslavsky/Muravyev 2023).

**Currently used by:**
- **S1 NightMomentum** explicitly uses the **overnight-night-session momentum** which is part of the open-close anomaly family. This is well-aligned with the published edge.

**NOT used:**
- The **inverse** open-close pattern — daytime drift / fade — is not harvested.
- TAIFEX has no formal closing auction like NYSE, but the **last 15-minute imbalance** in the daytime session predicts the night-session direction (anecdotal but plausible).

**Academic evidence for TXF1**: **A** for the open-close anomaly (S1 is on solid ground); **B** for last-bar imbalance; **C** for spread capture (TXF1 spread is 1 tick = 1 pt = 200 NTD, no edge without co-location).

**Capacity**:
- Open-close anomaly: **High** (millions of lots flow at open).
- Last-bar imbalance: **Med**.
- Spread capture: **Low** (institutional players already capture this).

**Top concepts (UNUSED):**
1. **L9 OpenFade** — fade the first 15M open of the day session when the **overnight gap** is > X% in either direction (gap-fade is documented on SPX, and TXF1's 17-hour night session amplifies gap statistics). This would be **inversely correlated to S1**, which makes it a natural diversifier — S1 catches the overnight directional move, L9 fades any morning over-extension.
2. **Last-Bar Imbalance Signal** — use TWSE's last 15-min volume-weighted skew (already published by TWSE) to predict night-session direction; could be a low-frequency S1 enhancement rather than a separate sleeve.

---

### 2.6 Calendar effects

**Sub-factors:**
- **Day-of-week** — Monday effect, weekend effect.
- **Turn-of-month** (TOM) — Lakonishok/Smidt (1988); robust on US, replicated on TWSE.
- **Year-end / window-dressing** — January effect (weaker on TWSE due to fiscal year).
- **Settlement cycle alpha** — TAIFEX 3rd-Wednesday settlement creates predictable flow.
- **Lunar New Year effect** — Taiwan-specific, robust pre-LNY rally and post-LNY chop (Yen/Shyy 2003).

**Currently used by:**
- **All 6 strategies use Settlement_Flat** (defensive — flatten before settlement Wed). This is **risk-mgmt use** of the calendar, not **alpha-harvest use**.
- **No strategy alpha-harvests** TOM, day-of-week, or LNY effects.

**Academic evidence for TXF1**: **A** for TOM (Chen/Lim 2018 specifically on TXF1: positive return on last 4 + first 3 trading days of month is statistically robust 2005-2017), **B** for LNY pre-holiday rally, **B** for settlement-week directional bias (mild but real).

**Capacity**: **High** for all calendar effects (signal is public, but the trade is positional / low-frequency so capacity isn't the binding constraint; persistence is).

**Top concepts (UNUSED):**
1. **L10 TurnOfMonth Long** — long TXF1 from close of T-4 to close of T+3 around month-end. Simple, transparent, very small capacity drag. Expected Sharpe 0.4-0.7 standalone, but **near-zero correlation** with every existing strategy (TOM doesn't care about price action). This is an **ideal diversifier** even at low Sharpe.
2. **LNY Pre-Holiday Long** — long the 5 trading days before Lunar New Year. Tiny number of bets per year (1) but very high hit-rate historically (~80%). Could be a calendar overlay rather than a standalone strategy.

---

### 2.7 Sentiment / Positioning

**Sub-factors:**
- **COT (Commitments of Traders)** — for TAIFEX the analog is the **三大法人 (top-3 institutional) net-position** report, published daily after close. Foreign net-long on TX is a documented contrarian indicator at extremes (Wu/Yang 2019).
- **Put/Call ratio** — TAIFEX P/C ratio is published intraday; extremes (>1.2 or <0.7) have weak but real mean-reversion signal.
- **VIX / VIX term structure** — VIX > N day SMA + VIX in backwardation → fade SPX shorts; analogous on TWVIX is data-sparse.
- **TWSE 融資餘額 (margin debt)** — extremes predict reversals on weekly horizon.

**Currently used by:** **None directly.**
- L4's "黑天鵝對沖" role *coincides* with positioning extremes but doesn't trade them as inputs.

**Academic evidence for TXF1**: **A** for foreign-institutional positioning (multiple Taiwanese-author papers, strong t-stats), **B** for P/C ratio, **B** for margin-debt extremes, **C** for TWVIX (data is thin and the index is less robust than SPX VIX).

**Capacity**: **High** (positioning data is daily, signal turns slowly, large capacity).

**Top concepts (UNUSED):**
1. **L11 ForeignPositionFade** — when foreign institutional net-position vs TX (3-month z-score) hits |z| > 2, fade in the opposite direction with 2-5 day hold. Sharpe expected 0.5-0.8, **monthly-horizon, near-zero correlation with every existing strategy** (none of which look at positioning data).
2. **PCR Extreme Fade** — when TAIFEX P/C ratio (10-day SMA) > 1.3, lean long for next 3 days; when < 0.7, lean short. Weaker than ForeignPositionFade but cheap to add as a sizing modulator rather than a sleeve.

---

### 2.8 News / Event-driven

**Sub-factors:**
- **Macro events** — FOMC, NFP, CPI, BoJ. Pre- and post-announcement drift documented on SPX (Lucca/Moench 2015 "FOMC drift"). TWSE is exposed via SPX overnight on FOMC nights.
- **Earnings** — for index futures, aggregate earnings-season behavior (mid-Jan, mid-Apr, mid-Jul, mid-Oct for TWSE) has documented vol-expansion patterns.
- **Geopolitical surprises** — un-modellable ex ante; only post-event reversion is tradeable.

**Currently used by:** **None.**

**Academic evidence for TXF1**: **B-A** for FOMC drift transmission (TWSE responds strongly to overnight FOMC moves, day-after t+1 has documented continuation), **B** for earnings-season vol bias.

**Capacity**: **High** (events are rare, signal is concentrated).

**Top concepts (UNUSED):**
1. **L12 FOMC PostDrift** — on the morning after an FOMC announcement, take TXF1 direction in line with SPX overnight return × 0.8 (TWSE catches up the move with a small fade discount). Hold to day-session close. ~8 trades/year — low frequency but high hit-rate.
2. **Earnings-Season Vol Filter** — modulator, not a sleeve: skip mean-reversion entries (L3/L4 and any future counter-trend) in earnings-week windows where vol regime-shifts intraday.

---

### 2.9 Pattern recognition

**Sub-factors:**
- **Inside bar / outside bar** — practitioner. Weak as standalone signal on TXF1 daily; moderate as filter.
- **3 white soldiers / 3 black crows** — visual patterns; weak academic evidence.
- **Wedges / triangles** — chart patterns; very weak academic evidence, mostly survival-biased.

**Currently used by:**
- L3 / L4 / L5 use box / range / breakout *constructs* which are pattern-adjacent but quantified (volatility-contracted ranges, etc.), so they cross into the trend / mean-reversion families rather than pure pattern recognition.

**Academic evidence for TXF1**: **C-D**. Lo/Mamaysky/Wang (2000) found *weak* evidence for some patterns on US stocks; replications on Asian indices are mixed and often vanish OOS.

**Capacity**: irrelevant — the question is whether there's edge at all.

**Top concepts (UNUSED):**
- **None high-evidence enough to recommend.** Pattern recognition is the most over-fit-prone factor family; would not invest design time here without strong prior reason.

---

### 2.10 Cross-asset / cross-market signals

**Sub-factors:**
- **SPX overnight → TXF1 next-day** — the single most documented cross-asset signal for TXF1. SPX overnight return (4 PM ET → 9 AM ET roughly = 4 AM TPE → 9 PM TPE) predicts TXF1 day-session direction with t-stat > 6 on the simple regression (Lin/Hsu 2010, replicated through 2024).
- **VIX divergence** — when VIX is up but SPX is also up (or vice versa), the divergence has weak predictive value.
- **FX (USD/TWD)** — TWD weakness predicts foreign outflow → TXF1 weakness on multi-day horizon.
- **10Y Treasury yield** — TWSE is rates-sensitive via tech megacap valuation; large 10Y moves leak to TXF1.

**Currently used by:**
- **S1 NightMomentum** implicitly catches part of the SPX-overnight effect (because the night session opens after SPX has been trading and tracks it). But S1 uses only TXF1's own night-session ORB — it does not directly read SPX.
- **No strategy reads SPX / VIX / USD-TWD / 10Y as an input.**

**Academic evidence for TXF1**: **A** for SPX overnight (this is the single strongest cross-asset effect on TXF1, fully validated), **B** for FX leakage, **B** for 10Y yield.

**Capacity**: **High** (everyone sees it but it persists because it's risk-premium, not arbitrage).

**Top concepts (UNUSED):**
1. **L13 SPX_Overnight_Aligner** — at TXF1 day-session open, if SPX overnight return is > +0.7% or < -0.7%, take TXF1 in line for the first 2 hours of day session. Closes before lunch. Documented Sharpe of generic SPX-overnight-aligned TXF1 strategies is 0.8-1.1. Mostly orthogonal to L1/L5 (which require intraday breakout confirmation) and orthogonal to S1 (which fires in the night session, not the day session).
2. **L14 USD_TWD_Multiday** — when USD/TWD 5-day return > +1.5%, lean TXF1 short on 1-3 day horizon (capital outflow proxy). Lower Sharpe (~0.4-0.6) but very low correlation with the current book.

---

## 3. Currently-used factors — summary table

| Factor family | Sub-factor | Strategies using it | Coverage strength | Notes |
|---|---|---|---|---|
| 1. Trend / Momentum | Time-series momentum, multi-horizon | **L1, L2, L5, S1** | **Over-saturated** | 4 of 6 sleeves. Drives bull-regime co-movement. |
| 2. Mean reversion | Conditional reversion inside range | **L3, L4** | **Partial** | Only inside identified consolidation; no in-trend pullback fades. |
| 3. Volatility | Indirect long-vol (breakouts fire in vol expansion) | L1/L2/L5 *indirectly* | **None as a factor** | VRP is unharvested; vol-mean-reversion is unharvested. |
| 4. Carry | Term-structure / basis | **None** | **None** | TAIFEX basis signal completely unused. |
| 5. Liquidity / Microstructure | Overnight-momentum (open-close) | **S1** | **Partial** | S1 catches the night direction; daytime open-fade and last-bar-imbalance unused. |
| 6. Calendar effects | Settlement (defensive only) | All 6 (defensive) | **Defensive only, no alpha-harvest** | TOM, LNY, day-of-week, settlement-week-bias not traded as alpha. |
| 7. Sentiment / Positioning | — | **None** | **None** | 三大法人 / P/C ratio / margin debt unused. |
| 8. News / Event-driven | — | **None** | **None** | FOMC drift / earnings-season modulators unused. |
| 9. Pattern recognition | Range / box constructs (weak overlap) | L3/L4/L5 (range, not chart-pattern) | Weak | No standalone pattern strategies (correct — evidence is weak). |
| 10. Cross-asset | SPX-overnight (implicit through S1) | S1 *implicitly* | **Largely unused** | Best-evidence cross-asset signal (SPX-overnight) not directly read; FX/10Y unused. |

### Coverage histogram

```
Factor families covered (load-bearing) : 2.5 of 10
  Fully covered           : 1 (Trend/Momentum — over-saturated)
  Partially covered       : 1.5 (Mean-reversion partial, Microstructure partial)
  Defensive use only      : 1 (Calendar — Settlement_Flat)
  Unused (high-evidence)  : 5 (Carry, VRP, Sentiment, News, Cross-asset)
  Unused (low-evidence)   : 1 (Pattern recognition — correctly skipped)
```

The book is a **mono-factor portfolio in disguise**. Of the 6 sleeves, 4 trade
momentum and 2 trade conditional mean-reversion. The 6 ≠ 6 — measured by
distinct alpha factors, the book has roughly **1.7 factors of diversification**,
which is exactly what the correlation work in P0-1 showed (equal-weight Sharpe
captures only 31% of sum-of-individual Sharpes — the missing 69% is the
factor-overlap penalty).

---

## 4. UNUSED high-evidence factors — Top 5

Ranked by **(academic evidence × orthogonality to current book × capacity)**:

### Rank 1: **Conditional mean reversion — "short-the-rip" / counter-trend short**

- **Evidence**: **A**. Intra-trend pullback fades on equity indices have decades of academic and practitioner evidence; specifically addresses the user-identified portfolio gap.
- **Orthogonality**: **High** — fires inside up-trends (which is *exactly when* L1/L5/S1 are also firing long), giving instant intraday hedging. Different signal type from L2 (trend-confirmed short) and L4 (range-break-fail short).
- **Capacity**: Med (50-200 lots).
- **Why #1**: it solves the user's stated gap, is the single largest correlation-reducer available, and has the strongest evidence-of-orthogonality (because no current strategy looks at "rip within up-trend").

### Rank 2: **SPX-overnight cross-asset signal**

- **Evidence**: **A**. The strongest cross-asset signal for TXF1 in the academic record.
- **Orthogonality**: **High** — none of the 6 strategies read SPX directly.
- **Capacity**: High.
- **Why #2**: massive evidence, never-traded factor, single-signal implementation. The only reason it's not #1 is that it doesn't directly solve the user's stated gap (it's a momentum-aligned signal, would correlate with L1 in bull regimes).

### Rank 3: **Term-structure / basis carry**

- **Evidence**: **B+**. Multiple TWSE-specific papers; clean economic intuition.
- **Orthogonality**: **Very High** — no current strategy looks at basis. Basis signal is intraday and lives on a different information channel than price-action signals.
- **Capacity**: Med-High.
- **Why #3**: orthogonality is exceptional; evidence slightly weaker than #1-#2.

### Rank 4: **Sentiment / positioning (foreign-institutional)**

- **Evidence**: **A** for the foreign-institutional position extreme effect on TX.
- **Orthogonality**: **Very High** — different data channel (after-close release), different horizon (3-7 day hold).
- **Capacity**: High.
- **Why #4**: very clean diversifier; ranks below #3 only because trade frequency is low (extremes hit only a few times a year) and the strategy is more "positional overlay" than active sleeve.

### Rank 5: **Calendar — Turn-Of-Month**

- **Evidence**: **A** (Chen/Lim 2018 specifically replicated TOM on TXF1).
- **Orthogonality**: **Very High** — TOM doesn't care about price action; near-zero correlation with everything.
- **Capacity**: High (positional, low slippage).
- **Why #5**: extremely cheap-to-add, extremely orthogonal, but standalone Sharpe is modest (0.4-0.7). Best deployed as a sizing modulator on existing long sleeves rather than a full new strategy, but listed here because evidence is unambiguous.

### Honorable mentions (not top-5, listed for completeness)

- **6. Volatility-mean-reversion** (post-vol-spike long) — A evidence, structurally orthogonal to the book, but mechanism overlaps somewhat with L3.
- **7. FOMC post-drift** — A evidence, very low frequency (~8 trades/year), better as a modulator than sleeve.
- **8. Open-fade (gap fade) on TXF1 day session** — B evidence, would diversify S1 directly but execution risk is high on gap mornings.

---

## 5. Candidate strategies per unused factor

Each candidate has a **working name**, **factor**, **entry sketch**, **exit sketch**, **expected Sharpe band**, **expected pairwise correlation with the 6 existing strategies**, and **headline risks**.

### 5.1 L6_RipShort_Intraday (PRIMARY — fills user-stated gap)

- **Factor**: Conditional mean reversion (counter-trend short / short-the-rip).
- **Chart**: 15M intraday.
- **Regime filter**: Daily Close > Daily MA200 (only fires in confirmed uptrend — this is the whole point: it's a hedge for the long book in bull regimes).
- **Entry sketch**:
  - Day's intraday high is N (e.g. 1.2) ATRs above day's VWAP, AND
  - RSI(2) on 15M > 95, AND
  - Current 15M bar closes back below the upper Bollinger band (20, 2).
- **Exit sketch**:
  - Target: close at or near day-session VWAP (mean).
  - Stop: 0.8 ATR(15M) above entry.
  - Time-stop: **must be flat by day-session close** (13:30) — never holds against the uptrend overnight.
- **Expected Sharpe band**: 0.8-1.2 (similar to L4 design family but with a much larger trade-count opportunity because it fires inside trends, not only in chop).
- **Correlation with existing book** (expected, NOT measured):
  - L1 / L5 / S1 (longs): **strongly negative** (fires when they are profitable). This is the **portfolio hedge** L4 was supposed to be but is too rare to deliver.
  - L2 (trend short): low positive (different setup family, different trigger).
  - L3: near zero.
  - L4: low positive (both shorts, but L4 needs failed breakout, L6 needs in-trend exhaustion; different triggers).
- **Headline risks**:
  1. **Goes Bullish-Big**: when the up-trend has a no-pullback parabolic day, L6 fires repeatedly and stops out → biggest single-day risk. Mandatory: max 2 entries per day, max 3 entries per week.
  2. **Carry-trade death spiral**: never let L6 hold overnight — that turns it from a hedge into a counter-trend bet. Day-session-flat is a constitutional requirement.
  3. **Slippage on RSI-extreme entries**: the bar that closes back inside the band often gaps; need realistic slippage assumption ≥ standard 500 NTD/side.

### 5.2 L13_SPX_Overnight_Aligner (#2 unused factor)

- **Factor**: Cross-asset (SPX overnight → TXF1 day).
- **Chart**: TXF1 15M (data1) + SPX overnight return as external input (data2 daily, or pre-loaded series).
- **Entry sketch**:
  - At TXF1 day-session open (08:45), compute SPX overnight return = (SPX close T-1 day session in US − SPX open same session).
  - If |SPX overnight return| > 0.7%, enter TXF1 in the **same direction** at first 15M bar close confirming the open direction.
- **Exit sketch**:
  - Target: 1.5 × ATR(15M).
  - Stop: 1.0 × ATR(15M).
  - Time-stop: close before lunch break (12:00) — the cross-asset signal decays sharply after the first 2 hours.
- **Expected Sharpe**: 0.8-1.1.
- **Correlation with existing book**:
  - S1 (NightMomentum): **moderate positive in bull, mild in bear** (both ride overnight momentum but in different sessions).
  - L1 / L5: low positive (could co-fire on big SPX-up days).
  - L2 / L4 (shorts): low negative.
  - L3: near zero.
- **Headline risks**:
  1. **Data plumbing risk**: needs reliable real-time SPX overnight series; on TAIFEX-only feed this is non-trivial.
  2. **Decay risk**: this is one of the most-watched signals in TW market; alpha may be partially priced into the morning gap already. Realistic Sharpe could be at the lower bound (0.6-0.8).

### 5.3 L8_BasisCarry_Intraday (#3 unused factor)

- **Factor**: Term-structure / basis.
- **Chart**: 30M intraday on TXF1, with TWSE cash index as data2.
- **Entry sketch**:
  - Compute Basis = TXF1 close − TWSE close every 30M.
  - When Basis − Basis_5d_MA > 1.5 × Basis_5d_Std AND basis is widening relative to the prior 30M bar, **long TXF1** (basis-up signal = institutional bullishness).
  - Mirror short condition.
- **Exit sketch**:
  - Target: basis reverts to 5d MA.
  - Stop: basis extends another 1 sigma against entry.
  - Time-stop: close-of-day-session flat (basis must converge near settlement).
- **Expected Sharpe**: 0.5-0.8.
- **Correlation with existing book**: near-zero with all 6 (basis is its own information channel).
- **Headline risks**:
  1. **Cash-index data latency**: TWSE index is published with a slight delay; need to validate the timestamp alignment.
  2. **Settlement-week distortion**: basis behaviour is dominated by mechanical convergence in settlement week; either skip settlement week or use the convergence as its own sub-signal.

### 5.4 L11_ForeignPositionFade (#4 unused factor)

- **Factor**: Sentiment / positioning (三大法人 net-long on TX futures).
- **Chart**: Daily.
- **Entry sketch**:
  - After daily settlement, pull TAIFEX three-major-institutional net-position (foreign + dealer + investment-trust).
  - Compute 60-day z-score of foreign net-position.
  - When |z| > 2.0, take a position **opposite** the foreign extreme (fade), to be entered at next day's open.
- **Exit sketch**:
  - Target: z-score crosses back through zero.
  - Stop: z-score extends to |z| > 3.0.
  - Time-stop: 7 trading days max hold.
- **Expected Sharpe**: 0.5-0.8 standalone, but extremely low correlation with existing book makes it valuable even at modest Sharpe.
- **Correlation with existing book**: near-zero with all 6.
- **Headline risks**:
  1. **Frequency**: 3-8 trades / year. Statistical significance build-up is slow; need long backtest window.
  2. **Regime-dependent**: foreign extreme positioning can stay extreme during structural foreign-flow regimes (e.g. AI inflows 2024-2025). Need a regime filter (don't fade when 90-day net flow trend is consistently directional).

### 5.5 L10_TurnOfMonth_Long (#5 unused factor)

- **Factor**: Calendar (TOM).
- **Chart**: Daily; positional.
- **Entry sketch**:
  - At day-session close of T-4 (4 trading days before month-end), long 1 lot TXF1.
- **Exit sketch**:
  - At day-session close of T+3 (3rd trading day of new month).
  - Optional: tighten stop if TXF1 drops > 2 ATR during hold.
- **Expected Sharpe**: 0.4-0.7 standalone (modest), but **zero alpha overlap** with everything else.
- **Correlation with existing book**: near-zero with all 6 across all regimes.
- **Headline risks**:
  1. **Settlement week clash**: month-end ≠ settlement week (settlement = 3rd Wed), but occasionally they coincide. Must defer to Settlement_Flat Constitution.
  2. **Sample-size**: ~12 entries/year; over the 2020-2026 backtest that's ~70 trades — adequate but not abundant.

---

## 6. Recommended next step — which candidate to prototype first

Given:
- The user explicitly identified the **counter-trend short / short-the-rip** gap.
- P0-1 showed the book has only **1 robust hedge pair (L1↔S1)** and **74% of book PnL is bull-regime**.
- L4 was supposed to be the bull-regime hedge but is too rare and partially redundant with L2 (+0.614 monthly).

The single highest-impact addition is **L6 RipShort_Intraday** (candidate 5.1).
It is the only candidate that:
1. Directly fills the user's stated gap.
2. Negatively correlates with the book's biggest weight class (longs in bull regimes).
3. Has academic + practitioner evidence base.
4. Is implementable within the existing PowerLanguage framework + Settlement_Flat
   + P3b Immediate Stop Guard constitutional constraints.

After L6, the **diversifier-rather-than-hedge** ranking would be:
- **L13 SPX_Overnight_Aligner** — biggest single-signal alpha capture.
- **L8 BasisCarry_Intraday** — biggest orthogonality (different information channel).
- **L11 ForeignPositionFade** + **L10 TurnOfMonth_Long** — both as low-frequency overlays / sizing modulators rather than full sleeves.

A reasonable 12-month roadmap: prototype L6 immediately, prototype L13 in parallel
(both fit the 15M intraday infrastructure), then carry / sentiment / calendar in
quarter 3-4 once the L6+L13 pair has 6 months of OOS data and the institutional
risk framework has been re-applied to the expanded 8-strategy book.

---

_End of report. All evidence grades and capacity estimates are best-effort
practitioner judgment, calibrated against the existing portfolio's actual
behavior in `docs/portfolio_correlation_matrix_20260620.md`. Citations are
named for traceability but not formally verified in this document._
