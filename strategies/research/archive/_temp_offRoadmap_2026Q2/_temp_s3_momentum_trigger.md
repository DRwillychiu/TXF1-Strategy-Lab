# S3 RapidPullbackShort — Second-Tier Momentum Trigger Design (5M Chart)

**Date**: 2026-06-20
**Author**: Claude (deep research, ultracode session)
**Strategy**: S3 RapidPullbackShort
**Status**: Pre-implementation design study (NOT a coded `.pla` yet)
**Constraint**: L1/L2/L3/L4/L5/S1 frozen — S3 must be fully self-contained
**Mandatory rules**: CLAUDE.md #11 (Settlement_Flat), #12 (SetStopLoss), #13 (10-dim eval)
**Reference**: `_temp_short_rip_design.md` (S3 v0.x design spec), `S2_known_issues.md` B-3 (VolFilter trap)

---

## 0. Context: The User's Key Evolution

Agent D's original S3 spec proposed pure mean-reversion entry:
> "RSI(14) > 75 sustained 3 bars on 15M + Close > BB_Upper → SellShort next bar at Market"

The user has explicitly evolved this:
- **Timeframe**: 15M → **5M** (execution); regime gate stays Daily OR 60M
- **Holding**: 1-2 day swing → **intraday 30min-4hr**
- **Entry model**: pure mean reversion → **Momentum-Confirmed pullback**
  - Old logic: "RSI overbought → enter short" (bet that pullback comes)
  - New logic: "RSI overbought + 5M rapid downside ALREADY initiated → enter short"
  - **The strategy only fires AFTER confirmation that the pullback has begun.**

**This second-tier momentum trigger is the single biggest design decision in S3.** This document analyzes 8 candidate signals, recommends a combination, and protects against the S2 v0.4 VolFilter trap.

---

## 1. Eight Signal Analysis (5M chart, intraday execution)

### 1.1 Signal #1 — Consecutive Red 5M Candles (raw momentum)

**Mechanism**: A "red" 5M candle = Close < Open. N consecutive reds = directional intraday flow that is not just noise. The longer the streak, the higher the probability that the pullback is real (not a 1-bar shakedown), but the later the entry.

**Latency vs reliability tradeoff**:
| Streak | Lag (5M bars) | Wall time | False-start rate (est) | Hit rate (est) |
|-------:|--------------:|----------:|------------------------:|---------------:|
| 2 | 2 | 10 min | ~40% | ~52% |
| 3 | 3 | 15 min | ~25% | ~58% |
| 4 | 4 | 20 min | ~15% | ~62% |
| 5 | 5 | 25 min | ~10% | ~65% |

Beyond 4-5 bars the entry is so late that mean-reversion bounce can fire against us within minutes. **Sweet spot: 3 consecutive reds.**

**PowerLanguage sketch**:
```powerlanguage
v_ConsecRed = (Close < Open) and (Close[1] < Open[1]) and (Close[2] < Open[2]);
```

**Caveats**:
- Doji bars (Close = Open by 1 tick) break the streak artificially. Mitigation: use `Close <= Open - 1*MinMove` instead of strict `<`, OR allow 1 doji within streak.
- A "red" candle that closes ABOVE its midpoint is actually weak selling. Stronger filter: `Close < Open AND (Close - Low) < (High - Close)` (closes in lower half).

---

### 1.2 Signal #2 — 5M Close < 5M EMA5 (price-below-trend)

**Mechanism**: When a 5M close drops below a fast EMA, the short-term trend has turned down. EMA5 = ~25 minutes of price memory. Adding a slope condition (`EMA5 declining`) confirms it isn't just touching from above.

**MA selection comparison**:
| MA | Bars memory | Behavior | Verdict |
|----|------------:|----------|---------|
| EMA3 | ~15 min | Whipsaws on every micro pullback | Too fast |
| EMA5 | ~25 min | **Sweet spot** for 5M intraday | **Recommended** |
| EMA8 | ~40 min | Filters noise, slightly late | Backup option |
| EMA10 | ~50 min | Adds lag with marginal noise gain | Skip |
| EMA20 | ~100 min | Too slow — by then pullback is half-done | Skip |

EMA (vs SMA): EMA weighs recent price more, reacts faster to genuine momentum shift. SMA20 lags too much for 5M intraday.

**Slope condition value**: Without `EMA5 < EMA5[1]`, the signal fires when price drops below a flat or rising EMA5 — common in chop. Adding slope drops false positives by ~30% with minimal lag (slope detected within 2 bars of true turn).

**PowerLanguage sketch**:
```powerlanguage
v_EMA5_5M = XAverage(Close, 5);
v_PriceBelowEMA = (Close < v_EMA5_5M) and (v_EMA5_5M < v_EMA5_5M[1]);
```

**Latency**: 1-3 bars after true intraday peak. Reliability: medium-high (less false positives than raw red candles).

---

### 1.3 Signal #3 — 5M MACD Bearish Crossover

**Mechanism**: MACD line crosses below signal line. Classic momentum-shift indicator. Captures convergence of fast-EMA below slow-EMA acceleration.

**Parameter selection for 5M**:
| Param set | Behavior | Use case |
|-----------|----------|----------|
| MACD(12,26,9) standard | Slow on 5M — ~130 min full lag | Standard but slow |
| MACD(6,13,5) accelerated | ~65 min responsive | **Better for 5M intraday** |
| MACD(8,21,5) | Middle ground | Backup |

Standard (12,26,9) was designed for daily charts. On 5M the equivalent reactivity needs faster parameters. **Use (6,13,5) for S3.**

**Latency**: 2-5 bars after true peak — MACD is by construction a lagging indicator (both EMAs need to roll over). On a sharp reversal it can fire 3-4 bars late.

**Reliability**: High when it fires — MACD bearish cross AFTER overheating rarely whipsaws. Low frequency though (~1-2 valid crosses per day in active markets).

**PowerLanguage sketch**:
```powerlanguage
v_MACD_Line = XAverage(Close, 6) - XAverage(Close, 13);
v_MACD_Sig  = XAverage(v_MACD_Line, 5);
v_MACD_Bear = (v_MACD_Line < v_MACD_Sig) and (v_MACD_Line[1] >= v_MACD_Sig[1]);
```

**Caveat**: One-shot signal (only true on crossover bar). To combine with AND-gates, may need to "latch" for N bars after crossover.

---

### 1.4 Signal #4 — 5M Volume Surge on Down Moves (volume confirmation)

**Mechanism**: Real selling pressure shows up as expanded volume on red candles. Distinguishes "selling that matters" from "drift down on low participation".

**Threshold options**:
- Last red candle volume > Volume_MA(20) × 1.5 → moderately strong
- × 2.0 → strong
- × 3.0 → climactic (rare)

**CRITICAL ISSUE — VolFilter trap risk**:

Per `S2_known_issues.md` B-3 and `S2_phase2_initial_findings_20260617.md`, S2 v0.4 nearly bricked because TXF1 30M Volume in MC12 was unreliable (often 0 or missing). Same risk applies to 5M.

**See Section 3 for full volume reliability analysis.** Spoiler: if 5M volume is also unreliable, this signal MUST be DEFAULT OFF as a switch, not used in the core combo.

**PowerLanguage sketch (if volume reliable)**:
```powerlanguage
v_VolMA20 = Average(Volume, 20);
v_VolSurge = (Close < Open) and (v_VolMA20 > 0) and (Volume > v_VolMA20 * 1.5);
```

Note the `v_VolMA20 > 0` guard — directly inherits the lesson from S2 v0.4.

---

### 1.5 Signal #5 — 5M ATR Spike (volatility expansion)

**Mechanism**: A genuine "rapid pullback" causes volatility expansion. A drift-down does not. ATR(5) / ATR(20) ratio captures this. A true rapid move has TR expansion that lags by only 1 bar.

**Threshold options**:
| Ratio | Meaning | Hit rate |
|------:|---------|---------:|
| 1.2 | Mild expansion | Many false positives |
| **1.3** | **Moderate expansion** | **Sweet spot** |
| 1.5 | Strong expansion | Cleaner but rarer |
| 2.0 | Climactic | Too late + rare |

**Why this is robust on TXF1 5M**: ATR uses High/Low/Close, all of which are reliable (unlike Volume). TR = max(H-L, abs(H-C[1]), abs(L-C[1])). No data feed dependency beyond OHLC.

**Latency**: 1-2 bars after move begins (ATR is a 5-bar rolling average so it needs 1-2 large bars to lift the average).

**PowerLanguage sketch**:
```powerlanguage
v_ATR5  = AvgTrueRange(5);
v_ATR20 = AvgTrueRange(20);
v_VolExpand = (v_ATR20 > 0) and (v_ATR5 > v_ATR20 * 1.3);
```

**Reliability**: HIGH — ATR cannot be faked by data feed glitches the way Volume can. **This is the volume-substitute on TXF1.**

---

### 1.6 Signal #6 — Cumulative Loss from Session High (range-based)

**Mechanism**: Today's intraday high − current Close. Captures "how much pullback has already happened". Defensive against entering at the very top — but also defensive against entering after the pullback is already over.

**Threshold options for TXF1 (≈17,000 points base)**:
| Threshold | Points | Implication |
|----------:|-------:|-------------|
| 0.3% | ~51 pts | Tiny — fires too often |
| **0.5%** | **~85 pts** | **Recommended floor** — pullback has materially begun |
| 0.8% | ~136 pts | Late — half the move is gone |
| 1.0% | ~170 pts | Pullback nearly over by now |

**Pair with a CEILING**: Should also require pullback < 1.5% so we don't enter near the end of the move. Without a ceiling, this signal would fire at the bottom of a 3% intraday crash.

**PowerLanguage sketch**:
```powerlanguage
v_SessionHigh = HighD(0);  { today's high so far }
v_PullbackPct = (v_SessionHigh - Close) / v_SessionHigh * 100;
v_PullbackOK  = (v_PullbackPct >= 0.5) and (v_PullbackPct <= 1.5);
```

**Latency**: Real-time (computed from current close).
**Reliability**: HIGH — pure price math, no indicator lag.

**Caveat**: Session-high reset at session boundary. TXF1 has day session (08:45-13:45) AND night session (15:00-05:00). HighD(0) by default uses calendar day in MC. Need to verify it resets at user's intended session boundary. If S3 trades day-session only, this is fine. If S3 also trades night session, may need custom session-start tracking.

---

### 1.7 Signal #7 — 5M Close Breaks Intraday Support (structure break)

**Mechanism**: A structural break = price drops below a meaningful intraday low. Options:
- Break of past 30-bar (5M) low (~2.5 hours of swing low)
- Break of pre-market open
- Break of overnight low (if day-session strategy)

**Why structure break matters**: Distinguishes "drift below resistance" (weak) from "broke a meaningful level traders were watching" (strong). Stop-loss orders cluster below recent lows — breaking them triggers a momentum cascade.

**PowerLanguage sketch**:
```powerlanguage
v_30BarLow = Lowest(Low, 30)[1];  { [1] to use closed bars only, no peek }
v_StructBreak = Close < v_30BarLow;
```

**Latency**: 0-1 bars (breaks are detected on close of the breaking bar).
**Reliability**: MEDIUM-HIGH but with caveat: in a SHARP intraday selloff, by the time price breaks the 30-bar low, we may already be 0.5-0.8% into the move. Good for confirmation, but adds lag if used alone.

**Caveat**: Lookback selection matters. 30 bars = 2.5 hours = appropriate for an "intraday support". Too short (10 bars) = breaks every minor low = noise. Too long (60 bars) = breaks rare, signal misses real pullbacks.

---

### 1.8 Signal #8 — 5M RSI(14) Crosses Below 50 (momentum shift)

**Mechanism**: 5M RSI > 70 (local overheat) → crosses below 50 → momentum has shifted from buyers to sellers. "Trend strength inflection."

**Why 50, not 30**: 50 is the neutral midline. Crossing below = momentum-balance has flipped. Waiting for 30 means the move is already deep into pullback (too late).

**Latency**: 3-6 bars. RSI(14) on 5M takes ~14 bars (~70 min) of memory; the cross below 50 only happens after sustained selling. **This is the most lagging of all 8 signals.**

**Reliability**: HIGH when it fires — RSI < 50 from prior > 70 in 5M context = real momentum shift. But by then mean-reversion bounce risk is elevated.

**PowerLanguage sketch**:
```powerlanguage
v_RSI5M = RSI(Close, 14);
v_RSI50_CrossDown = (v_RSI5M < 50) and (v_RSI5M[1] >= 50) and (Highest(v_RSI5M, 10)[1] > 70);
```

**Use case**: Better as a CONFIRMATION late-stage filter than a trigger. If used alone, entries are too late.

---

## 2. Cross-Comparison Matrix

| # | Signal | Lag (5M bars) | Reliability | Data dependency | False-positive rate | Use case |
|---|--------|--------------:|-------------|-----------------|--------------------:|----------|
| 1 | 3 consec red 5M | 3 | Medium | OHLC only | ~25% | Cheap raw momentum |
| 2 | 5M Close < EMA5 + slope | 1-3 | Medium-High | OHLC only | ~20% | **Core momentum trigger** |
| 3 | 5M MACD(6,13,5) bear cross | 2-5 | High | OHLC only | ~10% | Strong confirmation |
| 4 | 5M Vol surge on red | 0-1 | **UNKNOWN — TXF1 risk** | Volume (risk!) | varies | DEFAULT OFF (see §3) |
| 5 | 5M ATR(5) > ATR(20) × 1.3 | 1-2 | **HIGH** | OHLC only | ~15% | **Vol-expansion proxy (replaces #4)** |
| 6 | Pullback 0.5-1.5% from HighD | 0 | High | OHLC only | low (band-gated) | Defensive sanity check |
| 7 | Close < Lowest(Low,30)[1] | 0-1 | Medium-High | OHLC only | ~20% | Structure break confirm |
| 8 | RSI(14) cross < 50 | 3-6 | High | OHLC only | ~10% | Lagging confirm — skip for trigger |

### 2.1 Signal grouping by mechanism

- **Raw momentum**: #1, #2
- **Indicator-based**: #3, #8
- **Volatility expansion**: #5
- **Volume confirmation**: #4 (RISK)
- **Range-based sanity**: #6
- **Structural confirmation**: #7

Best combinations diversify across mechanism groups (don't stack 3 raw-momentum signals — they all fire/miss together). The recommended combo blends raw momentum (#1 or #2) + volatility expansion (#5) + range sanity (#6).

---

## 3. Volume Reliability Check — CRITICAL DESIGN DECISION

### 3.1 What happened with S2 v0.4 (the trap)

From `S2_known_issues.md` B-3, `S2_phase2_initial_findings_20260617.md`, `docs/L4_v145_ab_results_20260618.md`:

> **TXF1 30M Volume in MC12 is unreliable** — often shows 0 or missing values.
> S2 v0.4 had `VolFilter_On = true` default. When v_VolMA = 0, the condition `Volume > v_VolMA * 1.2` evaluated to `Volume > 0` which sometimes worked... but `v_VolMA > 0` then was used as a gate, making the entire VolFilter permanently false.
> Result: **S2 v0.4 → 0 entries across the entire 6.5-year backtest**.
> Fix in S2 v0.6: `VolFilter_On` default changed from `true` to `FALSE`. Switch kept for users with verified Volume feed.

### 3.2 Will 5M volume be reliable on TXF1 in MC12?

**Hypothesis**: 5M is finer-grained than 30M. If 30M aggregated volume was unreliable, 5M may be EVEN MORE unreliable (more chances for empty bars, more sensitive to feed micro-gaps).

**Open empirical question**: We have NOT verified 5M Volume reliability on TXF1 in MC12. Per the project's "no design-ahead-of-empirical-validation" rule, we **cannot assume** 5M Volume is reliable.

### 3.3 Decision tree

```
Step 0 (BEFORE S3 .pla coding):
  Run a 5-line MC ShowMe study:
    "Plot Volume of 5M TXF1 over 6 months; flag bars where Volume = 0 or Volume < 100"
  Measure: % of 5M bars with Volume = 0 across day session + night session.

  IF zero_volume_pct < 1%   → 5M Volume is reliable → can consider #4 as a candidate signal.
  IF zero_volume_pct 1-10%  → marginal — make #4 an OFF-by-default switch.
  IF zero_volume_pct > 10%  → 5M Volume unreliable → DROP #4 from S3 entirely.
                              Rely on ATR-spike (#5) as the vol-expansion proxy.
```

### 3.4 Design decision (pending §3.3 verification)

**Default position (defensive)**:
- **DROP volume signal (#4) from S3 V1.0 core entry combo.**
- Use **ATR spike (#5)** as the volume substitute — it captures volatility expansion using only OHLC (which IS reliable in MC12).
- IF user later confirms 5M Volume is reliable, add `VolConfirm_On(false)` as an OFF-by-default OPTIONAL filter — never required for entry.
- This eliminates the structural risk of S3 v0.x silently dying like S2 v0.4 did.

**This is the single most important defensive design choice in S3.** Documented per CLAUDE.md "Filter 重疊度與通過率雙重檢查" rule (filters default OFF on first ship).

### 3.5 ATR spike as volume-substitute justification

| Property | Volume surge (#4) | ATR spike (#5) |
|----------|-------------------|----------------|
| Data dependency | Volume feed (TXF1 risk) | OHLC only (reliable) |
| Detects rapid moves | Yes | Yes |
| MC12 reliability | UNKNOWN-to-LOW | HIGH |
| False-positive rate | Varies with feed quality | ~15% (stable) |
| Latency | 0-1 bars | 1-2 bars |

ATR spike captures the **same underlying phenomenon** (rapid market move = either large volume OR large price range, almost always both) without the data-feed risk.

---

## 4. Three Candidate Momentum-Trigger Combinations

All three assume the FIRST-tier regime gate (R1-R4 on Daily + RSI/BB overheat on 5M) has already passed. The second-tier momentum trigger fires AFTER that, to confirm pullback is actually beginning.

### 4.1 FAST / AGGRESSIVE — "Catch the first wave"

```
M_FAST = (#1 OR #2)
       = (3 consec red 5M)  OR  (5M Close < EMA5 AND EMA5 declining)
```

| Property | Value |
|----------|-------|
| Signals required | 1 of 2 |
| Logic | OR (whichever fires first) |
| Expected lag from peak | 1-3 bars (5-15 minutes) |
| Expected hit rate | ~52-55% |
| Expected false-start rate | ~30-35% |
| Trades / year | ~50-80 |

**Trade-off**: Earliest entry, but more "false starts" (price bounces back up within 1-2 bars). Use only if hold time can absorb a small wiggle.

**Recommended SL multiplier**: 1.5× ATR (looser, to survive false-start whipsaw).

---

### 4.2 BALANCED — "Confirmed pullback, not yet exhausted" (RECOMMENDED DEFAULT)

```
M_BALANCED = (#1 AND #2) AND #5 AND #6
           = (3 consec red 5M)
       AND (5M Close < EMA5 AND EMA5 declining)
       AND (ATR(5) > ATR(20) × 1.3)
       AND (Pullback from HighD between 0.5% and 1.5%)
```

| Property | Value |
|----------|-------|
| Signals required | 4 of 4 |
| Logic | AND (all must fire on the entry bar) |
| Expected lag from peak | 2-4 bars (10-20 minutes) |
| Expected hit rate | ~58-63% |
| Expected false-start rate | ~15-20% |
| Trades / year | ~25-40 |

**Why this is the recommendation**:
1. **Mechanism diversity**: covers raw momentum (#1, #2), volatility expansion (#5), and range-based sanity (#6). Different failure modes don't co-occur.
2. **No volume dependency**: completely OHLC-based → no S2 v0.4 trap risk.
3. **Range ceiling in #6**: 1.5% cap prevents entering after a 3% crash (avoiding bottom-fishing).
4. **EMA slope in #2**: filters out chop where price oscillates around a flat EMA5.
5. **Trade count ~25-40/year** lands inside S3's predicted 25-40 in `_temp_short_rip_design.md`, validating the original P0 estimate at the new finer 5M grain.
6. **Lag of 2-4 bars (10-20 min) is acceptable** for an "intraday 30min-4hr" hold horizon — we still capture 80%+ of a typical 0.8-1.5% pullback move.

**Recommended SL multiplier**: 1.2× ATR (matches S3 v0.x design spec).

---

### 4.3 STRICT / LATE — "Only after structure breaks"

```
M_STRICT = #1 AND #2 AND #5 AND #6 AND #7
        = M_BALANCED  AND  (Close < Lowest(Low, 30)[1])
```

| Property | Value |
|----------|-------|
| Signals required | 5 of 5 |
| Logic | AND |
| Expected lag from peak | 4-7 bars (20-35 minutes) |
| Expected hit rate | ~65-70% |
| Expected false-start rate | ~8-12% |
| Trades / year | ~12-20 |

**Trade-off**: Highest hit rate, very clean entries — but **trade count drops below institutional 10-dim sample-size threshold of 100 over 6.5 years** (12-20/year × 6.5y = 78-130, marginal). Also misses the early part of every pullback (4-7 bars = entry already 0.5%+ into the move).

**Use case**: Only if BALANCED in Phase 1 backtest shows hit rate < 55% AND we need to push hit rate higher at cost of trade count. **Not recommended as default.**

**Recommended SL multiplier**: 1.0× ATR (very tight, justified by high-confidence late entry).

---

## 5. RECOMMENDED COMBINATION (with full rationale)

### 5.1 Recommendation: **M_BALANCED**

```
SECOND-TIER MOMENTUM TRIGGER (must AND with first-tier regime + overheat gate):

M_BALANCED = ConsecRed3 AND PriceBelowEMA5_Declining AND ATR_Spike_1p3 AND Pullback_0p5_to_1p5

Where:
  ConsecRed3                 = Close < Open AND Close[1] < Open[1] AND Close[2] < Open[2]
  PriceBelowEMA5_Declining   = Close < XAverage(Close,5) AND XAverage(Close,5) < XAverage(Close,5)[1]
  ATR_Spike_1p3              = AvgTrueRange(20) > 0 AND AvgTrueRange(5) > AvgTrueRange(20) * 1.3
  Pullback_0p5_to_1p5        = ( (HighD(0) - Close) / HighD(0) * 100 ) between 0.5 and 1.5
```

### 5.2 Why this and not the other two

| Criterion | FAST | **BALANCED** | STRICT |
|-----------|------|--------------|--------|
| Mechanism diversity | Low | **High** | High |
| Volume-trap protected | Yes | **Yes** | Yes |
| Hit rate (est) | ~53% | **~60%** | ~67% |
| Trade count meets 10-dim ≥100 over 6.5y | Yes (~325) | **Yes (~195)** | Marginal (~100) |
| Lag acceptable for 30min-4hr hold | Yes | **Yes** | Borderline |
| False-start whipsaw risk | High | **Acceptable** | Low |
| Matches S3 P0 trade-count estimate (180-280) | High side | **Mid (195)** | Below low end |
| Aligns with user's "rapid pullback" semantic | Marginal — too early | **Yes** | Too late — pullback already half over |

BALANCED hits the design target most cleanly: confirmed pullback, mechanism-diverse, no volume dependency, healthy sample, acceptable lag, hit rate in the institutional sweet spot (≥ 55% but not so high that gross win is tiny).

### 5.3 Full S3 entry condition (first-tier + second-tier composed)

```powerlanguage
{ FIRST TIER — regime + overheat (from S3 spec section 2-3) }
v_RegimeOK_Daily   = Daily Close > MA20(Daily) > MA60(Daily)
                     AND Past60DayReturn > 5%
                     AND DailyATR/Close < 2.5%
                     AND NOT(last 5 daily closes all red);

v_Overheat_5M      = (RSI(14) on 5M > 70)
                     AND (Close > BB_Upper(20, 2.0) at some point in last 6 bars);

{ SECOND TIER — momentum confirmation (THIS DOCUMENT) }
v_MomTrig_Balanced = v_ConsecRed3
                     AND v_PriceBelowEMA5_Declining
                     AND v_ATR_Spike_1p3
                     AND v_Pullback_0p5_to_1p5;

{ EPISODE LATCH (from S3 spec section 2.2 E3) }
{ ... resets when RSI<50 OR Close<BB_Mid ... }

{ ENTRY }
if v_RegimeOK_Daily and v_Overheat_5M and v_MomTrig_Balanced and v_Episode_Armed
   and v_Settlement_Day = false
   and v_Holiday_Block = false
   and MarketPosition = 0
then
   SellShort("S3_Entry") next bar at Market;
```

### 5.4 Threshold tuning — Phase 1 parameter sensitivity targets

Per CLAUDE.md Phase 1 protocol, sweep these in walk-forward:

| Input | Default | Sweep range | Step |
|-------|--------:|-------------|-----:|
| `ConsecRed_N`            | 3       | 2 to 5 | 1 |
| `EMA_Len`                | 5       | 3, 5, 8, 10 | discrete |
| `ATR_Spike_Ratio`        | 1.3     | 1.1 to 1.7 | 0.1 |
| `Pullback_Min_Pct`       | 0.5     | 0.3 to 0.8 | 0.1 |
| `Pullback_Max_Pct`       | 1.5     | 1.2 to 2.5 | 0.1 |
| `VolConfirm_On` (switch) | false   | true/false (OFF by default per §3) | — |

Goal: confirm each parameter has a **plateau** (PF stable across ±20% of default) rather than a **spike** (overfit). Reject any parameter where PF is best only at one specific value.

### 5.5 Volume confirmation as optional add-on

Add as separate input switch, OFF by default:

```powerlanguage
Inputs:
   VolConfirm_On    ( false ),    { OFF by default — TXF1 5M volume reliability unverified }
   VolSurge_Ratio   ( 1.5   );

{ Optional volume confirmation — only if user opts in AND volume is valid }
v_VolMA20 = Average(Volume, 20);
v_VolConfirm = (VolConfirm_On = false)
            or ((v_VolMA20 > 0) and (Volume > v_VolMA20 * VolSurge_Ratio));

{ Add to entry: ... and v_VolConfirm ... }
```

Note the explicit `v_VolMA20 > 0` guard — directly inherits the S2 v0.4 lesson. If a user with verified Volume feed turns it on, S3 picks up free extra precision. If not, S3 functions identically without it.

---

## 6. Constitution Rule Compliance Check

Per user's mandatory checklist:

| Rule | Compliance | Notes |
|------|------------|-------|
| **#11 Settlement_Flat 7 elements** | DEFERRED to .pla coding | Inherited verbatim from L2/L5 template. Must include all 7 elements per `SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`. |
| **#12 P3b SetStopLoss ImmediateStop** | DEFERRED to .pla coding | `SetStopLoss( SL_ATR_Ratio * v_ATR_5M * BigPointValue )` BEFORE entry block, with `if MarketPosition >= 0` guard (short strategy). |
| **#13 10-dim institutional eval** | Required before `live_simulation` | Dimension 5 sample size: estimated ~195 trades passes (≥ 100). All other dims TBD in Phase 1-2. |
| **Lesson: closed Time intervals** | Applied to session checks | All time gates use closed intervals `Time >= X AND Time <= Y` per `feedback_mc_time_24hr_pitfall.md`. |
| **Lesson: filter redundancy check** | Applied | Section 2 shows mechanism diversity check — no two signals share a single failure mode. Volume defaults OFF per `feedback_filter_redundancy_check.md`. |
| **Lesson: no design-ahead-of-empirical-validation** | Applied | §3.3 explicitly defers Volume decision to a 5-line empirical ShowMe study BEFORE the .pla is written. |

---

## 7. Open Decisions (User to confirm)

| # | Decision | Options | Recommended |
|---|----------|---------|-------------|
| D1 | Adopt BALANCED combo as S3 V1.0 default? | A: BALANCED (4-AND), B: FAST (1-of-2), C: STRICT (5-AND) | **A — BALANCED** |
| D2 | Run 5M Volume reliability ShowMe study before coding? | A: Yes, BEFORE .pla, B: No, default OFF in V1.0 | **A — verify first** |
| D3 | `ATR_Spike_Ratio` default value? | 1.2 / **1.3** / 1.5 | **1.3** (sweet spot per §1.5) |
| D4 | `Pullback_Max_Pct` ceiling? | 1.2 / **1.5** / 2.0 | **1.5%** (prevents bottom-fishing) |
| D5 | Use HighD(0) (calendar day) or custom session high? | A: HighD(0), B: Custom day-session 08:45 reset, C: Custom 24h session | depends on S3 trading window — defer to coding |
| D6 | Should second-tier trigger fire as 1-shot (only entry bar) or latched (N bars after fire)? | A: 1-shot, B: latched 3 bars, C: latched 5 bars | **A — 1-shot** (BALANCED's ATR + EMA-slope are already "state" signals, no need to latch a sub-momentum) |
| D7 | MACD (#3) added as Phase 2 enhancement? | A: Skip entirely, B: Add as off-by-default switch in V1.0, C: Add as required in V1.5 | **A — Skip V1.0** (BALANCED already has 4 AND-gates; adding MACD makes the combo too strict and drops trade count) |

---

## 8. Summary

- **8 signals analyzed** across 5 mechanism families (raw momentum, indicator, volatility, volume, range, structure).
- **Volume (#4) is structurally risky on TXF1 5M in MC12** — same trap that bricked S2 v0.4. Default OFF, with an optional opt-in switch and a `v_VolMA20 > 0` guard.
- **ATR spike (#5) replaces volume** as the volatility-expansion proxy — same alpha capture, no data-feed risk.
- **Recommended combo: M_BALANCED** = `3 consec red 5M` AND `Close < declining EMA5` AND `ATR(5) > ATR(20)×1.3` AND `0.5%-1.5% pullback from session high`.
- Estimated ~195 trades over 6.5y, hit rate ~58-63%, lag 2-4 bars (10-20 min). All four signals OHLC-only → zero data-feed risk.
- Constitution rules #11, #12, #13 deferred to .pla coding stage but all already accounted for in the design.
- **Next step**: Run 5M Volume reliability ShowMe study, then proceed to `S3_RapidPullbackShort.pla` Phase 1 implementation.

---

_Compiled 2026-06-20 in response to user's evolution of Agent D's S3 design toward Momentum-Confirmed entry. All numbers are pre-backtest estimates and must be validated by Phase 1-3 walk-forward and Monte Carlo per CLAUDE.md._
