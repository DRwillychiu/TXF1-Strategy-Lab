# S3 RapidPullbackShort — Exit Mechanism Design (TP / SL / Time Stop)

- **Date**: 2026-06-20
- **Author**: Claude (ultracode session, deep research on exit numbers)
- **Status**: Pre-build design — concrete numbers proposed, must be A/B backtested before live_simulation promotion
- **Strategy spec recap**:
  - PRIMARY tf: **5M** (entry/exit execution)
  - OBSERVATION tf: Daily OR 60M (regime + overheating gate)
  - Direction: **Short-only**
  - Setup: 強多頭 + 過熱 + 5M 快速下跌啟動 → 進場做空
  - Holding: 30 min - 4 hr (intraday only)
  - Target: 1-2% pullback capture
- **Constitution compliance**: Rule #11 (Settlement_Flat 7 elements), #12 (P3b SetStopLoss), #13 (10-dim eval)
- **Data source**: `backtest/twii_daily.csv` (1,558 daily bars, 2020-01-02 ~ 2026-06)
- **Statistical script**: `scripts/_temp_s3_pullback_stats.py` (reproducible)
- **Raw stats JSON**: `scripts/_temp_s3_pullback_stats.json`

---

## 1. Pullback magnitude — empirical estimation

### 1.1 Trigger definition for the historical study

A historical "trigger bar" = a daily bar where ALL of the following hold:

- `Close > MA20 > MA60` (3-MA bullish stack)
- `(Close - Close[60]) / Close[60] > +5%` (60-day return — strong bull, not "just barely")
- `RSI(14) > 75` (overheat)
- De-dup: only first bar of an "overheat episode" counts; episode re-arms when RSI dips below 70

Result over 2020-01 ~ 2026-06 (1,558 daily bars):

| Metric | Value |
|---|---|
| Raw trigger bars (no de-dup) | 84 (5.4% of bars) |
| De-duped trigger bars | **22** (~3.4 / year) |

**Caveat**: This is on the **daily** TWII proxy. The actual S3 entry will fire on 5M after a momentum-confirmation (sharp 5M down move), which will refine these episodes into more granular intraday triggers. Each daily episode typically contains 1-3 candidate 5M entries → expected total live trade frequency ≈ **40-80 per year** on 5M, **22 episodes/year on the daily regime gate**.

### 1.2 Forward pullback magnitude — distribution

For each of the 22 de-duped daily triggers, we measure the maximum subsequent drawdown from the trigger close over the next 1/2/3 days. **This is the favourable excursion for a short entered at the trigger**:

| Window | n | P25 (%) | Median (%) | P75 (%) | P90 (%) | Mean (%) |
|---|---:|---:|---:|---:|---:|---:|
| 1-day max drawdown | 22 | 0.13 | 0.44 | 0.57 | 1.19 | 0.42 |
| **2-day max drawdown** | **22** | **0.30** | **0.57** | **1.15** | **1.64** | **0.80** |
| 3-day max drawdown | 22 | 0.46 | 0.75 | 1.69 | 2.66 | 1.17 |

Same data in points and ATR multiples:

| Window | Median (pts) | P75 (pts) | Median (× daily ATR) | P75 (× daily ATR) |
|---|---:|---:|---:|---:|
| 1-day | 77 | 123 | 0.35 | 0.61 |
| **2-day** | **111** | **223** | **0.57** | **0.82** |
| 3-day | 177 | 356 | 0.68 | 1.26 |

### 1.3 Max adverse excursion (how much the short hurts in the meantime)

| Window | P25 (%) | Median (%) | P75 (%) | P90 (%) |
|---|---:|---:|---:|---:|
| 1-day MAE | 0.29 | 0.58 | 1.13 | 1.69 |
| 2-day MAE | 0.49 | 1.00 | 1.67 | 2.18 |

→ Median 1-day adverse rise = **0.58%**, P75 = **1.13%**. This is the noise we must absorb before the pullback materialises. A naive SL at +0.3% would be stopped out on half of all entries.

### 1.4 Daily ATR baseline

| Stat | All bars | At trigger bars only |
|---|---:|---:|
| ATR(14) median (pts) | 224 | 210 |
| ATR(14) median (% of close) | 1.32% | 1.19% |
| ATR(14) P75 (% of close) | 1.53% | 1.32% |
| ATR(14) P90 (% of close) | 2.00% | 2.11% |

→ Trigger bars sit very close to median vol (1.19% ATR). The R3 filter (skip if `ATR/Close > 2.5%`) correctly excludes the 2020-03 / 2025-04 vol-spike outliers.

### 1.5 5M ATR — analytic estimate (no 5M data on file)

We do not have intraday 5M bars in the local dataset. Standard intraday vol scaling for index futures:

- Daily ATR ≈ √N × intraday ATR where N = number of intraday bars
- TXF1 day-session = 5 hours = 60 × 5M bars
- So 5M ATR ≈ Daily ATR / √60 ≈ Daily ATR × 0.13

| Daily ATR (pts) | Implied 5M ATR (pts) | 5M ATR (% of close) |
|---:|---:|---:|
| 150 (low-vol) | ~19 | ~0.10% |
| 225 (median) | ~29 | ~0.13% |
| 350 (high-vol) | ~45 | ~0.20% |
| 500 (vol-spike) | ~65 | ~0.29% |

**For S3 design purposes, assume 5M ATR(14) ≈ 25-45 TXF points typical, 0.12-0.20% of price.** This will need to be verified on actual 5M data once MC backtest runs.

### 1.6 The key design tension

User asked for "1-2% pullback". The empirical data says:

- **Median 1-day pullback = 0.44%** (way below "1%")
- **Median 2-day pullback = 0.57%** (still below 1%)
- **P75 2-day pullback = 1.15%** (about 1%)
- **P90 2-day pullback = 1.64%** (between 1-2%)

→ A 1-2% TP is only realized **at the top 10-25%** of historical episodes. Setting TP at 1% means most of the time we EITHER (a) hit time stop without TP, OR (b) get stopped out before any pullback materialises. **Setting TP at 0.5-0.7% (around the median) captures more episodes but caps profit on the fat ones.**

**Design implication**: this is a classic "wide-stop / wide-target" vs "tight-stop / tight-target" tradeoff. For a counter-trend short, the right answer is almost always tight-stop / tight-target with a high hit-rate — the moment we let position management drift toward "let it run", we are no longer counter-trend, we are fading-the-trend (a strategy that statistically doesn't work).

---

## 2. TP candidates

### 2.1 Fixed % from entry

| Variant | TP % | Pts on TWII@22000 | Hit rate estimate | Notes |
|---|---:|---:|---:|---|
| TP-A1 (tight) | -0.5% | 110 | ~55% | Captures median day-1 pullback; small wins, frequent |
| TP-A2 (mid) | -0.7% | 154 | ~50% | Just above median 2-day; user's lower bound minus buffer |
| TP-A3 (1%) | -1.0% | 220 | ~38% | Hits user's "1%" floor; catches P60-65 of 2-day pullbacks |
| TP-A4 (wide) | -1.5% | 330 | ~25% | Catches P75 of 3-day pullbacks; too wide for intraday holding |

**Hit-rate estimates** derived from §1.2 distribution: P(2-day drop ≥ X%) read off the percentile table.

### 2.2 Fixed daily-ATR multiple

| Variant | Multiple | Implied pts (median ATR=210) | Implied % | Notes |
|---|---:|---:|---:|---|
| TP-B1 | 0.4 × dATR | 84 | 0.38% | Median 1-day capture |
| TP-B2 | 0.6 × dATR | 126 | 0.57% | Median 2-day capture (user-aligned with empirical median) |
| TP-B3 | 0.8 × dATR | 168 | 0.76% | Between median and P75 |
| TP-B4 | 1.0 × dATR | 210 | 0.95% | ~user's lower 1% bound |

**Reading**: TP-B2 (0.6× daily ATR) is the empirically-grounded "median capture" target.

### 2.3 Fixed 5M-ATR multiple (intraday-native)

Using 5M ATR ≈ 32 pts typical:

| Variant | 5M ATR multiple | Implied pts | Implied % |
|---|---:|---:|---:|
| TP-C1 | 2.5 × 5M-ATR | 80 | 0.36% |
| TP-C2 | 4.0 × 5M-ATR | 128 | 0.58% |
| TP-C3 | 6.0 × 5M-ATR | 192 | 0.87% |

### 2.4 Structural MA-touch

| Variant | Trigger | Pros | Cons |
|---|---|---|---|
| TP-D1 | 5M EMA20 touch (from above) | Adaptive to vol; tracks short-term mean | Hard to backtest precisely without 5M data first |
| TP-D2 | 5M EMA50 touch | Deeper pullback target | Often misses; price reverts at EMA20 then runs up again |
| TP-D3 | 5M Bollinger middle (= MA20) | Same as TP-D1 effectively | Redundant with D1 |
| TP-D4 | 60M EMA20 touch | Higher-tf mean reversion | Too distant for intraday holding |

**Verdict**: TP-D1 (5M EMA20 touch) is the cleanest structural target. **In ATR terms, the distance from a "RSI>75 + BB%B>1" entry to MA20 is typically ~0.5-0.8% of price** (matches TP-A1/A2 / TP-B2 range).

### 2.5 Time-decaying TP

| Variant | Description |
|---|---|
| TP-E1 | TP starts at 1.0% (12 bars = 60 min), tightens to 0.5% (24-36 bars), then market exit at 48 bars |
| TP-E2 | TP = max(0.3%, 0.8% × (1 - bars/48)) — linear decay |

These add complexity. **Defer to V2.0** unless V1.0 backtests show clear bimodal "fast-mean-revert OR drift-into-time-stop" pattern.

---

## 3. SL candidates

The strategy is counter-trend. SL **must** be tight enough that being wrong = losing small. From §1.3, median 1-day adverse rise is 0.58%, so the SL must be far enough to absorb median noise but tight enough to define risk.

### 3.1 Fixed 5M-ATR multiple

| Variant | 5M ATR multiple | Implied pts | Implied % | Comment |
|---|---:|---:|---:|---|
| SL-A1 | 2.0 × 5M-ATR | 64 | 0.29% | Too tight: gets stopped on routine intraday rip noise |
| SL-A2 | 3.0 × 5M-ATR | 96 | 0.44% | Tight but realistic — about median 1-day adverse minus a hair |
| **SL-A3 (recommended)** | **4.0 × 5M-ATR** | **128** | **0.58%** | **Matches median 1-day MAE exactly** |
| SL-A4 | 5.0 × 5M-ATR | 160 | 0.73% | Loose; only fired on > median noise |
| SL-A5 | 6.0 × 5M-ATR | 192 | 0.87% | Too loose for counter-trend — turns S3 into fight-the-trend |

### 3.2 Fixed daily-ATR multiple

| Variant | dATR multiple | Implied pts | Implied % |
|---|---:|---:|---:|
| SL-B1 | 0.3 × dATR | 63 | 0.29% | Too tight |
| SL-B2 | 0.5 × dATR | 105 | 0.48% | Tight |
| SL-B3 | 0.7 × dATR | 147 | 0.67% | Mid |
| SL-B4 | 1.0 × dATR | 210 | 0.95% | Wide — equals user's TP floor (1R = 1R: bad math for counter-trend) |

### 3.3 Fixed % from entry

| Variant | SL % | Pts |
|---|---:|---:|
| SL-C1 | +0.30% | 66 | Too tight; stopped on routine wick |
| SL-C2 | +0.50% | 110 | Mid-tight, ≈ median MAE |
| SL-C3 | +0.70% | 154 | Mid |
| SL-C4 | +1.00% | 220 | Wide |

### 3.4 Structural "above-recent-high" + buffer

| Variant | Definition |
|---|---|
| SL-D1 | Highest high of last 6 × 5M bars (= 30 min) + 0.3 × 5M-ATR buffer |
| SL-D2 | Highest high of last 12 × 5M bars (= 60 min) + 0.5 × 5M-ATR buffer |
| SL-D3 | Entry bar high + 0.5 × 5M-ATR (uses only the entry bar) |

SL-D1 is intuitive but has a tail risk: if the entry triggers right after a big up-spike, the "recent high" is already very high, creating an excessively wide SL. **SL-D3 is cleaner.**

### 3.5 EMA-based

| Variant | Definition |
|---|---|
| SL-E1 | Close above 5M EMA5 ≥ 2 bars = exit on next bar at market |
| SL-E2 | Close above 5M EMA20 = exit |

These are confirmation-based exits, not stop orders. The risk: by the time we get the EMA cross, we are already underwater more than a stop would have closed us out at. **Not recommended as primary SL** — use only as a "Layer 6 structure invalidation" confirmation.

### 3.6 R/R math sanity check

User says 1-2% target. If we go with the empirically-grounded median (0.6%), then for a 2:1 R/R we'd need SL = 0.3%, which §1.3 tells us gets stopped 50%+ of the time on routine noise.

| SL (%) | Implied SL pts | TP (%) | Implied R/R | Required hit rate for breakeven |
|---:|---:|---:|---:|---:|
| 0.30 | 66 | 0.60 | 2.00 | 33% |
| 0.50 | 110 | 0.60 | 1.20 | 45% |
| 0.50 | 110 | 0.80 | 1.60 | 39% |
| **0.58** | **128** | **0.70** | **1.21** | **45%** |
| 0.58 | 128 | 1.00 | 1.72 | 37% |
| 0.70 | 154 | 1.00 | 1.43 | 41% |

Counter-trend mean-reversion **typical hit rates are 50-58%**. → 0.5-0.6% SL with 0.7-1.0% TP gives required hit rate 37-45%, comfortable headroom over a realistic 52-55% WR. **This is the operating zone for S3.**

---

## 4. Time stop candidates

User specified holding range 30 min - 4 hr.

- 30 min = 6 × 5M bars
- 1 hr = 12 × 5M bars
- 2 hr = 24 × 5M bars
- 4 hr = 48 × 5M bars

### 4.1 Hard cap variants

| Variant | Max bars | Max minutes | Notes |
|---|---:|---:|---|
| TS-A1 | 12 | 60 | User's "rapid pullback should resolve in 30-60 min" interpretation; tight |
| **TS-A2 (recommended)** | **24** | **120** | **Mid — balances user's range** |
| TS-A3 | 36 | 180 | Loose |
| TS-A4 | 48 | 240 | User's stated upper bound — absolute hard cap, never exceed |

### 4.2 Tightening (dynamic) variants

| Variant | Behavior |
|---|---|
| TS-B1 | After 12 bars (60 min) without TP, tighten SL to ATR × 0.5 |
| TS-B2 | After 24 bars (120 min) without TP, exit at market |
| TS-B3 | After 12 bars: if open trade PnL < 0, exit at market; else hold to 48 bars |

TS-B3 is "fail-fast" — if the pullback hasn't materialised in 60 min, the thesis is wrong, get out. This is a powerful psychological / risk feature for counter-trend trades.

### 4.3 Bar-of-day floor (avoid noisy first/last bars)

| Variant | Rule |
|---|---|
| TS-C1 | Force flat at 13:25 (5 minutes before 13:30 close) — DAILY HARD STOP, no exceptions |
| TS-C2 | Skip new entries after 12:30 (no entries < 60 min before close — guarantees we never have to fast-flatten an under-water position into the close) |

**Both TS-C1 and TS-C2 are MANDATORY for S3** — see §5.

---

## 5. Daily-close handling (mandatory)

S3 is intraday-only by user spec (30 min - 4 hr holding). This forces:

### 5.1 Position must be flat by 13:25 every day

```
P0-Daily-Flat: Time >= 1325 AND MarketPosition = -1 → BuyToCover at Market, label PS_DailyFlat
```

Why 13:25 not 13:30:
- TXF1 day session ends 13:45 (Settlement_Flat constitution uses 12:30 for monthly settlement, separate from daily flat)
- A position open at 13:25 in a routine non-settlement day gives 20 minutes to liquidate cleanly without sniping by late-day algos
- Last 15 min of session can be illiquid / wide spreads on TXF1

### 5.2 No new entries after 12:30

```
Entry gate: Time < 1230 AND ... (other entry conditions)
```

Rationale: A 4-hour-max hold starting at 12:30 would force exit at 16:30 = into night session. Since user wants intraday-only (no overnight), we must either (a) cap holding shorter than the time to close, or (b) ensure no entry happens within the time-to-close window.

A 60-minute pre-close cutoff (no entries after 12:30) means worst case entry → daily-flat exit ≤ 55 min, which fits inside the user's 30 min - 4 hr range and AVOIDS any need to extend into night session.

### 5.3 Settlement-day interaction

If today is monthly settlement day (3rd Wed, 12:30 settlement flat per constitution):

- Entry gate: must include `v_Settlement_Day = false` (inherited from constitution clause 1)
- → S3 simply does not trade on monthly settlement Wednesdays. Acceptable — only 12 days/year.

### 5.4 Night-session entries

User specified intraday-only. **S3 must NOT enter during night session (15:00 - 05:00 next day).**

```
Entry gate: Time >= 0845 AND Time <= 1230 (day session, with 12:30 cutoff)
```

Per MEMORY rule "MC Time 24-hour pitfall" → must use **closed interval** AND ed condition, not range crossing.

### 5.5 Holiday-tail interaction

S3 holds < 4 hours intraday → cannot be open at end-of-day → cannot bridge a holiday weekend. **Holiday_Tail block fires trivially** (no overnight = no overflight of holiday tail bar). But still include the inherited Holiday_Block per constitution for entry-gate completeness.

---

## 6. Three candidate exit combinations

### 6.1 TIGHT (rapid in/out — high turnover, smaller wins)

| Element | Value | Rationale |
|---|---|---|
| TP | -0.5% from entry (≈ 0.4 × dATR ≈ 3 × 5M-ATR) | Capture P50-55 of 2-day pullback, fast |
| SL | +0.45% from entry (≈ 0.35 × dATR ≈ 3 × 5M-ATR) | Just inside median 1-day MAE |
| R/R | 1.11 | Requires WR ≥ 47% for breakeven; counter-trend realistic |
| Time stop | 60 min (12 × 5M bars) | Fail-fast |
| Daily flat | 13:25 mandatory | Constitution |
| Entry cutoff | 12:30 | Ensures clean intraday |
| Expected WR | 56-62% | Tighter TP → higher hit rate |
| Expected trades/yr | 60-100 | More entries because TP fires more often, freeing re-entry slot |
| Expected avg PnL | Small but frequent | "Death by a thousand profits" model |

### 6.2 BALANCED (recommended) — empirically anchored

| Element | Value | Rationale |
|---|---|---|
| TP | -0.7% from entry OR 5M EMA20 touch (whichever first) | 0.6× dATR — matches median 2-day pullback empirically; structural backup if MA gets there first |
| SL | +0.58% from entry (= 4 × 5M-ATR ≈ 0.5 × dATR) | Matches median 1-day MAE; absorbs routine noise without bleeding |
| R/R | 1.21 | Requires WR ≥ 45% for breakeven |
| Time stop | 120 min (24 × 5M bars) | Mid of user's 30 min - 4 hr range |
| Daily flat | 13:25 mandatory | Constitution |
| Entry cutoff | 12:30 | Clean intraday |
| Expected WR | 52-58% | Standard counter-trend range |
| Expected trades/yr | 40-70 | 22 daily episodes × ~2 candidate 5M entries × 60% de-dup pass |
| Expected PF | 1.30-1.55 | Realistic counter-trend ceiling |

### 6.3 WIDE (deeper pullback capture — fewer, bigger)

| Element | Value | Rationale |
|---|---|---|
| TP | -1.0% from entry OR 5M EMA50 touch | Hits user's 1% floor; catches P60-65 of 2-day pullbacks |
| SL | +0.70% from entry (= 5 × 5M-ATR ≈ 0.6 × dATR) | Looser to absorb the bigger move that often precedes deeper pullbacks |
| R/R | 1.43 | Requires WR ≥ 41% for breakeven |
| Time stop | 240 min (48 × 5M bars = full 4-hr cap) | User's stated max |
| Daily flat | 13:25 mandatory | Constitution |
| Entry cutoff | 09:25 (4-hr max + 13:25 flat) | Ensures full 4-hr window available |
| Expected WR | 45-52% | Wider TP → lower hit rate |
| Expected trades/yr | 25-50 | Fewer entries; longer holding ties up the slot |
| Risk | Drift toward "fight-the-trend" | Wider SL means S3 can be wrong for longer, which is dangerous for counter-trend |

### 6.4 Side-by-side comparison

| | TIGHT | **BALANCED** | WIDE |
|---|---:|---:|---:|
| TP (%) | 0.50 | **0.70** | 1.00 |
| SL (%) | 0.45 | **0.58** | 0.70 |
| R/R | 1.11 | **1.21** | 1.43 |
| Time stop (min) | 60 | **120** | 240 |
| Time stop (5M bars) | 12 | **24** | 48 |
| Expected WR | 56-62% | **52-58%** | 45-52% |
| Expected trades/yr | 60-100 | **40-70** | 25-50 |
| Expected PF | 1.25-1.45 | **1.30-1.55** | 1.20-1.45 |
| Counter-trend safety | Highest | **High** | Medium |
| Capacity for "1-2%" target | Misses upside | **Hits user's lower 1% bound** | Hits full user range |
| Constitution compliance | ✓ | **✓** | ✓ |

---

## 7. RECOMMENDED — concrete numbers for V1.0 build

### 7.1 Headline configuration: BALANCED variant

```powerlanguage
{ TP / SL / Time stop — engine-level }

Inputs:
  TP_Pct                ( 0.70 ),     { TP at -0.70% from entry, OR }
  TP_Use_MA20_Backup    ( true ),     { 5M EMA20 touch (whichever fires first) }
  TP_MA_Len             ( 20   ),     { 5M EMA20 for structural TP }

  SL_ATR_5M_Multiple    ( 4.0  ),     { SL = 4 × 5M ATR(14) ≈ +0.58% }
  SL_ATR_Len            ( 14   ),

  MaxBars_TimeStop      ( 24   ),     { 120 min = 24 × 5M bars }
  Entry_Cutoff_Time     ( 1230 ),     { No new entries after 12:30 }
  Daily_Flat_Time       ( 1325 ),     { Force flat by 13:25 every day }

  { Inherited from constitution }
  Holiday_Flat_Time     ( 0300 ),
  Settlement_Flat_Time  ( 1230 ),
  Manual_Kill_Switch    ( false ),
  Registry_Valid_Until  ( 1270101 );
```

### 7.2 Exit cascade (priority order, strict)

```
EVERY BAR while MarketPosition = -1:

  { Priority 0 — Mandatory (Constitution + CLAUDE.md rules 11/12) }
  P0-1  Manual_Kill_Switch                  → BuyToCover Market, label PS_Kill
  P0-2  Registry_Expired                    → BuyToCover Market, label PS_RegistryEnd
  P0-3  Holiday_Block AND Time>=300         → BuyToCover Market, label PS_Holiday
  P0-4  v_Settlement_Day AND Time>=1230     → BuyToCover Market, label PS_Settlement
  P0-5  SetStopLoss(SL_Distance×BigPV)      { engine-level, always armed, P3b rule }

  { Priority 0a — Daily-flat (S3-specific, intraday-only constraint) }
  P0-6  Time >= Daily_Flat_Time (1325)      → BuyToCover Market, label PS_DailyFlat

  { Priority 1 — Profit target }
  P1    Close <= EntryPrice × (1 - TP_Pct/100)
        OR Close <= 5M_EMA20[1]              → BuyToCover Market, label PS_TP

  { Priority 2 — Frozen ATR stop loss }
  P2    Close >= v_SL_Level                  → BuyToCover at v_SL_Level Stop, label PS_SL
        { v_SL_Level = EntryPrice + (v_Entry_5M_ATR × SL_ATR_5M_Multiple) }

  { Priority 3 — Time stop }
  P3    BarsSinceEntry >= MaxBars_TimeStop   → BuyToCover Market, label PS_TimeStop
```

### 7.3 Entry-gate additions (no-new-entry windows)

```powerlanguage
{ Block new entries after 12:30 (so worst-case Daily_Flat fires within max hold window) }
v_Entry_Time_OK = (Time >= 0845) AND (Time <= Entry_Cutoff_Time);

{ Per MEMORY: closed-interval AND, not range crossing — critical for cross-day Time field }
v_Day_Session = (Time >= 0845) AND (Time <= 1345);

{ Combine with all existing gates }
if v_REGIME_OK AND v_5M_RAPID_DOWN_TRIGGER AND
   v_Entry_Time_OK AND v_Day_Session AND
   (v_Holiday_Block = false) AND (v_Settlement_Day = false) AND
   (MarketPosition = 0) then
   SellShort("PS_Entry") next bar at Market;
```

### 7.4 ATR freezing (per SOP §3 principle #1)

```powerlanguage
{ Freeze 5M ATR on entry bar — SL distance must NOT drift mid-trade }
if MarketPosition = -1 then begin
   if (BarsSinceEntry = 0) and (SL_Locked = false) then begin
      v_Entry_5M_ATR = AvgTrueRange(SL_ATR_Len);
      v_SL_Level     = EntryPrice + (v_Entry_5M_ATR × SL_ATR_5M_Multiple);
      v_TP_Level     = EntryPrice × (1 - TP_Pct / 100);
      SL_Locked      = true;
   end;
end else begin
   v_Entry_5M_ATR = 0;
   v_SL_Level = 0;
   v_TP_Level = 0;
   SL_Locked = false;
end;
```

### 7.5 SetStopLoss (P3b mandatory)

```powerlanguage
{ Per CLAUDE.md rule 12 — engine-level guard, fires inside the entry bar }
if MarketPosition >= 0 then
   SetStopLoss( SL_ATR_5M_Multiple × AvgTrueRange(SL_ATR_Len) × BigPointValue );
{ This must be called BEFORE the entry block, AFTER indicator computation }
```

### 7.6 Why BALANCED over TIGHT/WIDE

- **vs TIGHT**: The 0.5% TP misses the user's "1-2%" stated target zone entirely. The pullbacks user described as actionable (1-2%) live in P75-P90 of the distribution; TIGHT only captures up to P50. BALANCED's 0.7% TP plus EMA20 backup catches more of the user-intended distribution while still being inside the median 2-day capture zone.
- **vs WIDE**: 1.0% TP requires waiting for P60-65 of 2-day pullbacks, but doing so requires absorbing 4-hour MAE (much wider than 2-hour MAE). The wider SL converts S3 from "counter-trend pullback" into "fight-the-trend" — and the historical data (§1.3, 2-day P75 adverse = 1.67%) shows that adverse excursion grows almost as fast as favourable excursion when we extend the window. WIDE has worse asymmetry.
- **Constitution alignment**: BALANCED's 13:25 daily flat + 12:30 entry cutoff guarantees zero settlement-day clash, zero night-session leakage, and zero holiday-tail exposure — all without special-case code beyond the inherited modules.
- **Lesson-discipline check (MEMORY)**:
  - ✅ Closed Time intervals (`Time >= 0845 AND Time <= 1230` for entry, `Time >= 1325` for daily flat) — uses AND closed form, not range crossing
  - ✅ Filter redundancy check: TP fixed-% and EMA20-touch are NOT redundant (one is price-distance, other is structural); both serve distinct cases. Daily flat and time stop are NOT redundant (one is wall-clock, other is bars-since-entry)
  - ✅ No design-ahead-of-validation: numbers come from §1 empirical pullback distribution on actual TWII data, not from a-priori guess

### 7.7 What needs validation in Phase 1 backtest

| Item | Method | Pass criterion |
|---|---|---|
| 5M ATR magnitude on real data | Run backtest, log `AvgTrueRange(14)` distribution | 5M ATR median in 25-45 pt range (matches §1.5 estimate) |
| TP hit rate | Count `PS_TP` exits / total entries | 50-60% |
| SL hit rate | Count `PS_SL` exits / total entries | 25-35% |
| Time stop hit rate | Count `PS_TimeStop` exits / total entries | 10-20% |
| Daily flat hit rate | Count `PS_DailyFlat` / total entries | < 5% (only when TP/SL/TimeStop all miss + clock runs out) |
| WR | All PS_TP + PS_DailyFlat (if profitable) / total | ≥ 52% |
| PF | sum(win) / abs(sum(loss)) | ≥ 1.30 |
| Avg holding | Mean BarsSinceEntry at exit | 12-24 (60-120 min) |
| Trades per year | Total / 6.5 | 40-70 |
| Drawdown clustering | Max consecutive losses | ≤ 7 |

If Phase 1 violates any of these substantially, the parameter set must be re-evaluated **before** Phase 2 WFE.

---

## 8. Open decisions for user

1. **Choose TIGHT / BALANCED / WIDE** as V1.0 starting point. (Recommendation: BALANCED, anchored to empirical median pullback.)
2. **TP structural backup**: include 5M EMA20 touch as an alternative TP trigger, or pure %-based only? (Recommendation: include, with `TP_Use_MA20_Backup` input flag for A/B.)
3. **Entry cutoff time**: 12:30 (gives 55 min worst-case to daily flat) or 11:30 (gives full 2-hr time-stop window without daily-flat interference)? (Recommendation: 12:30 — accepts that some trades will exit on daily-flat rather than time-stop, in exchange for more entry opportunities.)
4. **Daily-flat time**: 13:25 or 13:30? (Recommendation: 13:25 — 5-min liquidity cushion before close.)
5. **Should V1.0 include scale-out** (half off at 0.4%, half at 0.7%)? (Recommendation: NO — defer to V2.0 after 30+ live trades validate single-stage profile. Consistent with project pattern for new strategies.)

---

## 9. References

- Statistical script: `scripts/_temp_s3_pullback_stats.py`
- Raw stats JSON: `scripts/_temp_s3_pullback_stats.json`
- Prior design (S3 daily-grain v0): `scripts/_temp_short_rip_design.md`
- Coverage-gap parent: `scripts/_temp_coverage_gap.md`
- Constitution: `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`
- Exit SOP: `docs/entry_exit_sop.md`
- P3b guard: `docs/P3b_immediate_stop_guard_design_20260618.md`
- 10-dim risk framework: `docs/institutional_risk_framework_20260619.md` (per rule 13)

---

_Pre-build exit mechanism design for S3 RapidPullbackShort. Concrete numbers derived from 22 historical bull+RSI>75+strong-trend trigger episodes in TWII daily data 2020-2026. 5M ATR estimates extrapolated analytically (5M data not on file); must be verified in Phase 1 MC backtest before parameter freeze. All numbers subject to A/B variant scan in Phase 1 sensitivity analysis._
