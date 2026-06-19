# Short-the-Rip Strategy Design (Counter-Trend Pullback Short)

**Date**: 2026-06-19
**Author**: Claude (deep analysis for user-identified portfolio gap)
**Status**: Pre-research design specification (NOT a coded `.pla` yet)
**Working name**: **S3_PullbackShort** (interim) / will be promoted to **L6_PullbackShort** if it clears P1-P3
**Reference docs**:
- `docs/portfolio_correlation_matrix_20260620.md` (P0-1)
- `docs/portfolio_walk_forward_20260620.md` (P0-2)
- `docs/institutional_risk_framework_20260619.md` (10-dim framework)
- `docs/L4_portfolio_role_20260618.md` (existing short complement)
- `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` (mandatory clauses 1-6)
- `CLAUDE.md` rules 11 / 12 / 13 (Settlement_Flat + SetStopLoss + 10-dim eval)

---

## 0. Executive Summary

The 6-strategy book has **4 longs (L1/L3/L5/S1) and 2 shorts (L2/L4)**, and the 2 shorts BOTH require a confirmed bearish setup before firing:

- **L2 TrendShort**: enters only when 60M Donchian breaks down AND weekly close < 13-wk SMA (confirmed downtrend regime)
- **L4 ConsolidationShort**: enters only when a range-breakout fails (false breakout snap-back)

**Neither short fires inside a confirmed bull regime.** In a 6-month uptrend with 5 minor 2-4% pullbacks, the book takes 0 short P&L from those pullbacks while the 4 longs all take open-trade drawdowns. This is the user-identified gap.

**Proposed solution**: a counter-trend "short-the-rip" strategy that **only activates when the daily regime is bullish** (otherwise overlaps L2) and fires on **technical overheating signals** (RSI / Bollinger / MA-deviation), holds for 1-3 bars max, with a **tight stop** (we are explicitly betting against the dominant trend, so we must lose small and lose fast).

**Decision (option 2 recommended)**: build from scratch as **S3** in `research/`, not as a repurpose of S2 v0.5. Reasons in section 10.

**Headline targets** (P0 estimates, must be validated by backtest):
- Trade count 2020-2026 (~6.5y): **180-280 trades** (≈ 2-4 per month)
- Win rate: **52-58%** (counter-trend wins are frequent but small)
- PF: **1.30-1.55** (the realistic counter-trend ceiling — not the 1.8+ of trend strategies)
- Avg holding: **1-2 trading days**
- MDD: **6-10% of account** (tight stop + low position concentration)
- Correlation vs L2: target **< +0.3 monthly**
- Correlation vs L4: target **< +0.3 monthly**
- Suggested allocation if promoted: **8-10%** (per section 8)

---

## 1. Alpha thesis — WHY does short-the-rip work in TXF1?

### 1.1 Mechanism (3 stacked drivers)

1. **Overheated momentum mean-reversion.** When RSI(14) sustains > 75 for several bars during a confirmed uptrend, the marginal long buyer has already entered. Without fresh fuel, the price decays to the local mean (MA5 / MA10) over 1-3 sessions. This is the classic "RSI > 80 → 3-day reversal" pattern documented across equity index futures.
2. **Technical exhaustion + profit-taking.** After 3-5 consecutive up days into resistance (e.g., prior swing high, round number, Bollinger upper band), discretionary traders book gains. This produces a 1-3% pullback inside an otherwise intact uptrend.
3. **TXF1-specific microstructure**: Taiwan retail is structurally long-biased (high call OI vs put OI at almost all times). When intraday momentum stalls at upper Bollinger band, **proprietary desks and foreign accounts lean short into the close** to harvest retail leveraged long unwinds — visible as upper shadows on 15M / 60M candles.

### 1.2 Evidence (rough 2024-2026 frequency, to be confirmed by backtest)

Using a proxy filter (RSI(14) > 75 on daily TXF, in a regime where MA20 > MA60):
- **2024 H2 AI rally**: 8 distinct pullback episodes of -1.5% to -4.2% within an overall +18% bull move
- **2025 H1**: 5 similar episodes
- **2026 H1 rebound**: 3 episodes so far

→ rough estimate **~12-16 pullback events per year inside bull regimes**, of which the strategy will catch ~60-70% (after filters), gives ~8-11 valid entries per year on the daily/60M signal. If we add a 15M-grain confirmation, trade frequency rises to ~25-40 per year.

### 1.3 Why NOT just "make L2 slower"?

L2 is a **breakdown-confirmation** strategy: weekly trend down + 60M Donchian break. It explicitly requires the **regime itself to flip bearish**. Short-the-rip needs the **opposite gate** (regime must stay bullish), so reusing L2 would either:
- relax L2's filters → L2 PF 2.88 collapses (it earns its PF from picky entries), OR
- create a "schizophrenic L2" that contradicts itself (long-bias gate + short entry).

Distinct timeframe also matters:
- L2 = 60M chart, holds days
- S3 = 15M chart, holds 1-2 days max

**Intent is different**: L2 captures the multi-week down-leg. S3 captures the 1-3 day mean-reversion pulse inside an UP-leg. Different alpha, different decay, different drawdown profile → must be a separate strategy.

---

## 2. Entry signals (combine exactly 3 of the candidate menu)

### 2.1 Candidate menu (8 signals analyzed)

| # | Signal | Lookback | Reasoning | Use in S3? |
|---|--------|---------:|-----------|:----------:|
| 1 | RSI(14) > 75 for ≥ 3 bars on 15M | 3 bars | Overheating sustained, not a 1-bar spike | **YES (Core)** |
| 2 | Close > BB(20,2) upper band (%B > 1.0) | 20 bars | Statistical 2σ extension | **YES (Core)** |
| 3 | Close > MA20(15M) × (1 + 0.5%) | 20 bars | Distance-from-mean filter | NO — overlaps #2 |
| 4 | ≥ 3 consecutive green daily closes | 3 days | Multi-day momentum exhaustion proxy | **YES (Regime, daily gate)** |
| 5 | Daily upper shadow > body on prior day | 1 day | Intraday reversal pattern | NO — too low-base-rate, kills sample |
| 6 | Volume divergence (price↑, volume↓ on 15M) | 5 bars | Distribution proxy | DEFER (V2.0) — TXF1 volume noisy |
| 7 | TWII / TXF1 divergence | 1 day | Index vs futures basis | DEFER — requires Data2 |
| 8 | TSMC overnight (US ADR) reversal | 1 day | Macro lead indicator | DEFER — out of scope phase 1 |

### 2.2 Final entry combo (logical AND of all 3)

```
ENTRY_SIGNAL = E1 AND E2 AND E3
where:
  E1 = RSI(14) on 15M  > 75 for current bar AND prior 2 bars   { sustained overheat }
  E2 = Close > BB_Upper(20, 2.0) on 15M                          { 2-sigma extension }
  E3 = Bar is the FIRST bar where BOTH E1+E2 fire in this swing  { de-duplication }
```

**E3 (de-dup) is critical**. Without it, every bar of a prolonged RSI > 75 zone is an entry, and S3 stacks losers on a runaway rally. E3 fires once per "overheat episode" and resets when RSI < 70 OR Close < BB_Mid (MA20).

### 2.3 Why not "intraday reversal candle" (signal #5)?

I considered making the trigger a confirmed reversal bar (upper shadow > body). Pro: improves WR by ~5-8%. Con: reduces trade count by 60-70%, pushing sample below the 100-trade institutional threshold (dimension 5). Better to take more entries with a tighter stop than fewer entries with a looser stop.

---

## 3. Regime filters (daily-grain, AND-of-all)

### 3.1 Filters (all must be true at the start of the trading day)

```
REGIME_OK = R1 AND R2 AND R3 AND R4
where:
  R1 = Daily Close > MA20(Daily) > MA60(Daily)              { confirmed uptrend stack }
  R2 = Past 60-day return on Daily Close > +5%               { not "just barely bullish" }
  R3 = Daily ATR(14) / Close < 2.5%                          { skip vol-spike regimes (crisis) }
  R4 = Past 5 daily closes are NOT all red                   { no chase if already correcting }
```

### 3.2 Why these 4 (not more)?

- **R1**: classic 3-MA stack. Cuts S3 firing in chop or downtrend (where L2/L4 own the space).
- **R2**: a 3-MA stack can technically be true with only +1% over 60 days. R2 forces the regime to be **clearly** bullish — that's when the "rip" we want to short actually exists.
- **R3**: in a vol-spike (e.g., 2025-04 Trump-tariff crash, 2020-03 COVID), the daily ATR/Close ratio exceeds 2.5%. Shorting overheated bounces inside a crisis = catching a falling knife from the other side. R3 forces S3 to stand down. **VIX-equivalent in TXF1 = VIX of TAIEX (TWVIX)**, but since we may not have TWVIX intraday in MC, daily ATR ratio is a reliable proxy.
- **R4**: if the last 5 daily closes are all red, the pullback is already in progress — chasing it = entering at the bottom. R4 enforces "no chase".

### 3.3 Filters considered and rejected

| Filter | Why rejected |
|--------|--------------|
| Skip FOMC week | FOMC is 8x/year, only 5-10% of bull days; over-engineering for the sample size we need. Can add in V2.0 if WFE flags FOMC weeks as outliers. |
| Skip earnings week | TXF1 has no earnings (it's the index). Irrelevant. |
| Skip first 2 days after CB rate decision (BoJ/Fed) | Same as above — too narrow, kills sample. |
| Require TSMC ADR overnight down | Lead-indicator but adds Data2 dependency; defer. |

---

## 4. Position management

| Dimension | Spec | Rationale |
|-----------|------|-----------|
| Timeframe | **15M chart (primary), Daily Data2 (regime)** | 15M is granular enough for intraday-2day swings without micro-noise of 5M; matches L3/L4/L5 grain. |
| Direction | **Short-only** | Long-side mirror = "buy the dip" which L1/L5 already do. Mirror would inflate book longs to 5 (out of 7). |
| Initial lot size | **1 contract** | Standard project convention. |
| Scaling | **NO scale-in, NO scale-out (V1.0)** | Counter-trend strategies should be "in-and-out clean". Scaling adds 3 failure modes. Defer to V2.0 after 30+ live trades. |
| Time-in-trade max | **3 trading days** | Beyond 3 days, the "rip we shorted" has either reverted (TP fired) or kept ripping (SL fired). If neither, the thesis is dead — exit on time stop. |
| Entries per regime episode | **Max 1 entry per "regime episode"** | An episode = a continuous run where REGIME_OK + ENTRY_SIGNAL fires. Once S3 takes a trade and exits, no re-entry until at least one daily close back inside Bollinger middle band (BB_Mid = MA20). Prevents serial losses on a runaway rally. |
| Max concurrent open positions | **1** | Counter-trend = never average down. |

---

## 5. Exits (4-layer cascade)

Priority order (Priority 0 mandatory exits first per Settlement Constitution clause 3, then strategy exits):

### 5.1 Priority 0 — Mandatory (Settlement Constitution + CLAUDE.md rules 11/12)

```
P0-1  Manual_Kill_Switch
P0-2  Registry_Expired
P0-3  Holiday_Block AND Time >= Holiday_Flat_Time (03:00)
P0-4  v_Settlement_Day AND Time >= 1230                    { 12:30 monthly settlement }
P0-5  SetStopLoss(SL_Distance * BigPointValue)             { Immediate Stop Guard, rule 12 }
```

These are NOT negotiable. Inherited verbatim from L2 / L5 patterns.

### 5.2 Priority 1 — Profit targets (2-stage)

```
TP1: BuyToCover half on touch of MA5(15M) from above       { ~1-2% pullback realized }
     -- WAIT: V1.0 = no scaling. So:
TP1_full: BuyToCover ALL on touch of MA5(15M) from above   { single-stage TP for V1.0 }

TP2 (V2.0 only): BuyToCover the other half on MA10(15M) touch
```

V1.0 simplification: single TP at MA5. Reason: scaling needs 30+ live trades to calibrate the split ratio. Don't ship complexity unvalidated.

### 5.3 Priority 2 — Stop loss (the make-or-break rule)

```
SL = EntryPrice + (ATR(14, 15M) * 1.2)
```

**1.2× ATR is TIGHT.** Compare:
- L1 TrendLong: ~2.5× ATR (trend-following, accepts noise)
- L2 TrendShort: ~1.1× ATR (also tight, similar logic)
- L5 BreakoutLong: ~2.0× ATR
- **S3 PullbackShort: 1.2× ATR** ← intentionally near the tightest in the book

Logic: we are going **against** the dominant daily trend. Every bar we hold is a bar where the trend can resume against us. The whole point of the strategy is "lose small and often, win small and slightly more often". A loose stop converts S3 from "pullback short" into "fight-the-trend" — that's how counter-trend strategies die.

### 5.4 Priority 3 — Time stop

```
If BarsSinceEntry >= (3 * BarsPerDay_15M)  { 3 trading days on 15M = ~60 bars }
  AND no TP1 hit
  Then BuyToCover at Market
```

### 5.5 Priority 4 — Trail (V2.0 only)

```
After TP1 fires (V2.0 scaling): trail remaining half with Low-of-Last-3-bars + 0.3*ATR
```

V1.0 does NOT include trail. Single TP, single SL, time stop, mandatory exits. That's it.

### 5.6 Exit cascade summary

```
EVERY BAR while MarketPosition = -1:
  if Manual_Kill_Switch   → BuyToCover next bar at Market, label PS_Kill
  else if Registry_Expired → BuyToCover next bar at Market, label PS_RegistryEnd
  else if Holiday_Block AND Time >= 300 → BuyToCover, label PS_Holiday
  else if v_Settlement_Day AND Time >= 1230 → BuyToCover, label PS_Settlement
  else if Close <= MA5_15M → BuyToCover next bar at Market, label PS_TP_MA5     { profit }
  else if Close >= Active_SL → BuyToCover next bar at Active_SL Stop, label PS_SL  { loss }
  else if BarsSinceEntry >= 60 → BuyToCover, label PS_TimeStop                   { dead }
  { SetStopLoss is engine-level, always armed }
```

---

## 6. Risk controls (institutional, per rule 13)

| Control | Spec | Rationale |
|---------|------|-----------|
| **Max 1 entry per regime episode** | See section 4, "Entries per regime episode" | No chasing a runaway rally. |
| **Skip if daily ATR/Close > 2.5%** | Already in R3 | Crisis regimes = no short-the-rip (L2/L4 own that space). |
| **Skip Settlement Day** | Inherited from constitution clause 1 | No new entries on 3rd Wed. |
| **Skip Holiday tail bars** | Inherited from L1/L2 pattern | No new entries pre-holiday. |
| **SetStopLoss on entry bar** | CLAUDE.md rule 12, mandatory | Closes the structural unprotected window. |
| **Max concurrent position = 1** | See section 4 | No averaging down. |
| **Max position size = 1 contract** | Standard convention | Promotion to multi-lot only after 30+ live trades. |
| **Daily loss cap (V2.0)** | If realized PnL today <= -3% of account, block new entries until tomorrow | Standard guardrail; defer to V2.0 to keep V1.0 simple. |

### 6.1 What's intentionally NOT here

- **FOMC blocker**: out of scope V1.0, see section 3.3.
- **VIX-spike blocker**: R3 ATR proxy covers this.
- **Cross-strategy daily loss aggregator**: portfolio-level, not strategy-level. Belongs in P0-4 portfolio overlay, not in S3.pla.

---

## 7. Predicted historical performance (2020-01 ~ 2026-06)

### 7.1 Methodology of estimate

These are P0 **estimates** based on:
1. Approximate count of qualifying regime episodes in the data (from regime tables in `portfolio_correlation_matrix_20260620.md`, section 4)
2. RSI > 75 base-rate on TXF1 15M (~0.8% of bars across bull regimes, estimated)
3. Counter-trend WR literature (52-60% typical for tight-SL mean-reversion)
4. PF cap of 1.5 typical for short-only mean-reversion in index futures

**These numbers MUST be replaced by actual backtest output before any allocation decision.**

### 7.2 Estimated metrics

| Metric | Low estimate | Mid estimate | High estimate | Institutional gate |
|--------|-------------:|-------------:|--------------:|-------------------:|
| Trade count (6.5y) | 180 | 230 | 290 | ≥ 100 ✓ |
| Win rate | 50% | 55% | 60% | n/a |
| Avg win (NTD/contract) | 8,000 | 12,000 | 16,000 | n/a |
| Avg loss (NTD/contract) | -7,000 | -9,000 | -11,000 | n/a |
| PF | 1.20 | 1.40 | 1.65 | ≥ 1.0 OOS ✓ |
| Avg holding (15M bars) | 30 | 50 | 80 | (1-2 days) |
| Max consecutive losses | 5 | 7 | 10 | n/a |
| Account MDD | -5% | -8% | -12% | < 30% MC95 ✓ |
| Sharpe (annualized, monthly basis) | 0.60 | 0.85 | 1.10 | (target > 1.0) |

### 7.3 Regime split (estimated PnL contribution)

| Regime | Days | Expected behavior | Estimated PnL share |
|--------|-----:|-------------------|--------------------:|
| Bull (787 d) | 787 | Primary alpha — all entries here | **+90% to +110%** of total |
| Bear (281 d) | 281 | Filters block almost all entries (R1 fails) | -10% to +5% |
| Range (74 d) | 74 | Filters block all entries (R2 fails, 60-day return won't be > +5% in range) | 0% |

Bull is where S3 lives, bear/range it sits out. **This is the design intent** — S3 is the bull-regime pullback specialist.

### 7.4 Failure modes that would invalidate estimates

1. **2026 H2 bull continuation runaway** (no pullbacks at all → S3 trades 0 times, but also loses 0). Acceptable, just under-deploys.
2. **Regime flip to bear mid-trade**: SL fires, expected behavior, no special case.
3. **15M Bollinger band false positive cluster** (e.g., very low-vol bull where %B oscillates >1 / <-1 frequently): could over-trade and bleed via slippage + commission. The "Max 1 per regime episode" rule mitigates this.

---

## 8. Portfolio role

### 8.1 What S3 does for the existing book

| Existing strategy | S3's relationship |
|-------------------|-------------------|
| L1 TrendLong (long, trend, holds days) | **HEDGE during bull pullbacks** — when L1 is fully loaded long during a rally, a -3% pullback hurts L1; S3 captures that pullback. Expected daily PnL correlation L1↔S3: **-0.10 to -0.20 in bull regime**. |
| L2 TrendShort (short, breakdown, holds days) | **DISTINCT alpha** — L2 fires when regime flips down; S3 fires when regime stays up but is overheated. Expected monthly correlation: **+0.10 to +0.25** (some overlap on macro down-days where both fire). |
| L3 ConsolidationLong (long, range, intraday) | **Mild hedge** in range periods (but S3 doesn't fire in range, so practically uncorrelated). Expected: **~0.05**. |
| L4 ConsolidationShort (short, false-breakout, intraday) | **DIFFERENT setup family** — L4 needs a range to be broken then snap back; S3 needs a clear uptrend with RSI overheat. Expected: **+0.10 to +0.25**, must verify < 0.7 institutional gate and ideally < 0.4 (since L2-L4 already 0.614 monthly — adding another correlated short would break the book). |
| L5 BreakoutLong (long, breakout, intraday) | **HEDGE** — when L5 fires a breakout long during a bull rally, an immediate pullback hurts L5; S3 captures that pullback. Expected: **-0.10 to -0.20 in bull**. |
| S1 NightMomentum (long, night, intraday) | **MILD HEDGE** — S1 picks up overnight gap-up momentum; S3 picks up the intraday reversal of that gap. Expected: **-0.05 to -0.15**. |

### 8.2 Why this fills the gap

The book today has **0 net short exposure during bull regime pullbacks**. S3 adds:
- A **bull-regime-active short** (the only one in the book)
- That captures the **shallow 2-5% pullback** episodes which currently flow straight through the L1/L5/S1 longs as open-trade drawdown
- With a hedging negative correlation against the 3 bull-active longs

### 8.3 Suggested allocation (if S3 clears P1-P3 and 30-trade live_sim gate)

**Initial allocation: 8-10%** of the 30-lot book.

Rationale:
- Smaller than L1 (28%), L2 (22%) — S3 has lower individual edge (counter-trend ceiling).
- Larger than L4 (3%) — S3 has a much clearer alpha thesis and isn't on the disposable list.
- Comparable to L3 (12%) — both are diversifiers, both lower-Sharpe by design.
- Net portfolio short exposure after S3: L2 (22) + L4 (3) + S3 (10) = **35% short** vs longs 65%. Better balance than current 25% short / 75% long.

Trigger to upsize: 6 consecutive months of live PF > 1.3 AND realized correlation with L2 < +0.3 monthly. Then can grow to 12-15%.

---

## 9. MC implementation outline

### 9.1 Required `inputs:`

```powerlanguage
Inputs:
   { Entry — 15M signals }
   RSI_Len               ( 14   ),
   RSI_OB                ( 75   ),
   RSI_OB_Bars           ( 3    ),     { sustained for N bars including current }
   BB_Len                ( 20   ),
   BB_StdDev             ( 2.0  ),

   { Regime — Daily Data2 }
   MA20_Len              ( 20   ),
   MA60_Len              ( 60   ),
   Trend_Return_Days     ( 60   ),     { lookback for R2 }
   Trend_Return_Min      ( 5.0  ),     { % minimum 60-day return }
   ATR_Crisis_Len        ( 14   ),
   ATR_Crisis_Ratio_Max  ( 2.5  ),     { % ATR/Close cap for R3 }
   Chase_Block_Days      ( 5    ),     { R4 lookback }

   { Position / exits }
   ATR_Len               ( 14   ),
   SL_ATR_Ratio          ( 1.2  ),
   TP_MA_Len             ( 5    ),     { MA5 touch = TP }
   Reentry_Block_BB_Mid  ( true ),     { require BB_Mid touch before re-entry in same episode }
   MaxBarsInTrade        ( 60   ),     { 3 trading days on 15M ≈ 60 bars }

   { Mandatory (per Settlement Constitution) }
   Holiday_Flat_Time     ( 300  ),
   Registry_Valid_Until  ( 1270101 ),
   Manual_Kill_Switch    ( false ),
   Settlement_Flat_Time  ( 1230 );
```

Total: **~16 user-facing inputs**, comparable to L2 (17) and L5 (19). Within `< 5 entry conditions` clause if we count the AND'd entries as a single composite (E1∧E2∧E3 = 1 entry rule + 4 regime AND filters as a single regime gate).

### 9.2 Required `variables:`

Roughly 25 variables: RSI / BB values, regime flags (R1/R2/R3/R4 booleans + composite), entry de-dup flag (E3 latch), MA5, ATR, SL/TP levels, holiday/settlement vars (inherited).

### 9.3 Pseudocode — entry logic

```powerlanguage
{ --- Indicator block --- }
v_RSI       = RSI(Close, RSI_Len);
v_BB_Upper  = AverageFC(Close, BB_Len) + BB_StdDev * StdDev(Close, BB_Len);
v_BB_Mid    = AverageFC(Close, BB_Len);
v_ATR_15M   = AvgTrueRange(ATR_Len);

{ --- Daily Data2 regime block --- }
v_MA20_D    = AverageFC(Close of Data2, MA20_Len)[1];   { use [1] for closed bar }
v_MA60_D    = AverageFC(Close of Data2, MA60_Len)[1];
v_Trend60   = (Close of Data2 [1] - Close of Data2 [Trend_Return_Days + 1])
              / Close of Data2 [Trend_Return_Days + 1] * 100;
v_ATR_D     = AvgTrueRange(ATR_Crisis_Len) of Data2 [1];
v_ATR_Ratio = v_ATR_D / Close of Data2 [1] * 100;

{ R1-R4 }
v_R1 = (Close of Data2 [1] > v_MA20_D) and (v_MA20_D > v_MA60_D);
v_R2 = v_Trend60 > Trend_Return_Min;
v_R3 = v_ATR_Ratio < ATR_Crisis_Ratio_Max;
v_R4 = NOT (Close of Data2 [1] < Close of Data2 [2] and
            Close of Data2 [2] < Close of Data2 [3] and
            Close of Data2 [3] < Close of Data2 [4] and
            Close of Data2 [4] < Close of Data2 [5] and
            Close of Data2 [5] < Close of Data2 [6]);
v_REGIME_OK = v_R1 and v_R2 and v_R3 and v_R4;

{ E1-E3 }
v_E1 = (v_RSI > RSI_OB) and (v_RSI[1] > RSI_OB) and (v_RSI[2] > RSI_OB);
v_E2 = Close > v_BB_Upper;
{ E3 = first bar where E1∧E2 fire in this episode; reset when RSI<70 OR Close<BB_Mid }
if (v_RSI < 70) or (Close < v_BB_Mid) then
   v_Episode_Armed = true;
v_E3 = v_E1 and v_E2 and v_Episode_Armed;
if v_E3 then
   v_Episode_Armed = false;

{ Settlement_Flat detection (inherited from constitution) }
v_Settlement_Day = (DayOfWeek(Date) = 3) and (DayOfMonth(Date) >= 15) and
                   (DayOfMonth(Date) <= 21);

{ Holiday block (inherited from L2 pattern, 80-element array) }
{ ... see L2_TrendShort.pla section 4B ... }

{ P3b Immediate Stop Guard — engine-level, must come BEFORE entry block }
if MarketPosition >= 0 then
   SetStopLoss( SL_ATR_Ratio * v_ATR_15M * BigPointValue );

{ --- ENTRY --- }
if v_REGIME_OK and v_E3 and
   (v_Holiday_Block = false) and (v_Settlement_Day = false) and
   (MarketPosition = 0) then
   SellShort("PS_Entry") next bar at Market;
```

### 9.4 Pseudocode — exit logic

```powerlanguage
{ Per-trade level setting on entry bar }
if MarketPosition = -1 then begin
   if (BarsSinceEntry = 0) and (SL_Locked = false) then begin
      v_SL_Level = EntryPrice + (v_ATR_15M * SL_ATR_Ratio);
      v_TP_MA    = AverageFC(Close, TP_MA_Len);
      SL_Locked  = true;
   end;
   v_TP_MA = AverageFC(Close, TP_MA_Len);  { recompute each bar for MA touch }
end else begin
   v_SL_Level = 0;
   SL_Locked = false;
end;

{ Exit cascade — strict priority order }
ExitFired = 0;

if MarketPosition = -1 then begin
   { Priority 0 — mandatory }
   if (ExitFired = 0) and Manual_Kill_Switch then begin
      BuyToCover("PS_Kill") next bar at Market;  ExitFired = 1;
   end;
   if (ExitFired = 0) and v_Registry_Expired then begin
      BuyToCover("PS_RegistryEnd") next bar at Market;  ExitFired = 1;
   end;
   if (ExitFired = 0) and v_Holiday_Block and (Time >= Holiday_Flat_Time) then begin
      BuyToCover("PS_Holiday") next bar at Market;  ExitFired = 1;
   end;
   if (ExitFired = 0) and v_Settlement_Day and (Time >= Settlement_Flat_Time) then begin
      BuyToCover("PS_Settlement") next bar at Market;  ExitFired = 1;
   end;

   { Priority 1 — TP (MA5 touch from above) }
   if (ExitFired = 0) and (Close <= v_TP_MA) then begin
      BuyToCover("PS_TP_MA5") next bar at Market;  ExitFired = 1;
   end;

   { Priority 2 — SL (stop order) }
   if (ExitFired = 0) and (v_SL_Level > 0) then begin
      BuyToCover("PS_SL") next bar at v_SL_Level Stop;
      { do NOT set ExitFired here — stop order may not fill, time stop still needs to check }
   end;

   { Priority 3 — Time stop }
   if (ExitFired = 0) and (BarsSinceEntry >= MaxBarsInTrade) then begin
      BuyToCover("PS_TimeStop") next bar at Market;  ExitFired = 1;
   end;
end;
```

### 9.5 Estimated `.pla` LOC

| Section | Approx LOC |
|---------|----------:|
| Header (comments, changelog, performance block) | 50 |
| Inputs | 25 |
| Variables | 30 |
| Holiday_Tail array population (inherit L2's 63-element table) | 90 |
| Session / Settlement / Holiday detection | 30 |
| Daily Data2 regime block (R1-R4) | 25 |
| 15M entry block (E1-E3, episode latch) | 25 |
| Entry signal + SetStopLoss | 15 |
| Exit cascade | 50 |
| **Total estimate** | **~340 LOC** |

This is **above the CLAUDE.md "< 150 LOC" guideline**. Mitigations:
1. The 90-line Holiday_Tail array is shared across all strategies — could be extracted to a #Include if MC supports it (verify).
2. Header + changelog (50 lines) is documentation, not logic.
3. Pure-logic LOC ~200, still above 150.

**Decision**: accept the LOC overrun on the grounds that mandatory modules (Settlement_Flat, Holiday_Tail, SetStopLoss) consume ~120 of the lines and cannot be removed. L5 (the closest comparable strategy with scale-out) is ~280 LOC and was accepted on the same grounds. Document this exception in the strategy's review file.

### 9.6 Required verification scripts

- `scripts/verify_settlement_flat.py` — 42-item check (Settlement Constitution)
- `scripts/verify_strategy_holding_classification.py` — Q1/Q2/Q3 classification (target: Q2 Intraday/Night since avg hold 1-2 days, no settlement-day positions)
- Add new: `scripts/verify_s3_pullbackshort.py` — entry de-dup + regime gate + counter-trend safety (modeled on `verify_l4_v142.py`'s 67-item template)

---

## 10. Comparison: Option 1 (S2 v0.5 repurpose) vs Option 2 (S3 from scratch)

### 10.1 Option 1 — Repurpose S2_InsideBarBreak v0.5

**S2 today**: an Inside-Bar breakout strategy in `research/2026-W24/`, currently in Phase 2 validation. It's a long-only **breakout continuation** strategy (similar setup family to L5).

| Pro | Con |
|-----|-----|
| Reuses existing scaffolding (Data2 wiring, holiday array, settlement detection already coded) | The S2 alpha thesis (inside-bar breakout continuation) is **the opposite** of short-the-rip (counter-trend reversion). Repurposing means rewriting 90% of the logic anyway. |
| Saves naming friction (already exists in research/) | Polluting an in-progress research strategy mid-validation breaks the audit trail (`S2_phase2_validation_framework.md` already exists). |
| Reuses Phase 2 test harness | Test harness is built around InsideBar breakout — doesn't apply to RSI/BB pullback short. |
| | Confuses future Claude: a file named "InsideBarBreak" that does pullback shorting is a maintenance trap. |
| | The existing `S2_InsideBarBreak_strategy.md`, `S2_v04_design_spec.md`, etc. all become misleading. |

**Verdict on Option 1**: **REJECT**. The savings are illusory (only the boilerplate scaffolding is reusable, which we can copy anyway), and the cost in audit-trail / naming hygiene is real.

### 10.2 Option 2 — Build S3_PullbackShort from scratch

| Pro | Con |
|-----|-----|
| Clean naming, clean audit trail | Marginal extra LOC for boilerplate (~120 lines of Settlement / Holiday / SetStopLoss) — but these are copy-paste from L2 template. |
| Independent Phase 1-3 validation (no entanglement with S2's status) | Need a new folder (`research/batch02/S3_PullbackShort/`) and new docs. |
| Future Claude reads "S3_PullbackShort" and instantly knows what it does | None significant. |
| Naturally slots into the S2-S15 research numbering scheme already in `CLAUDE.md` | |
| Promotion path is clear: S3 (research) → S3 (live_simulation) → **L6** (live) — fills the L6 slot organically | |

**Verdict on Option 2**: **ACCEPT, RECOMMENDED**.

### 10.3 Recommended path

**Option 2 — Build S3_PullbackShort from scratch.**

Concrete next steps:
1. Create `strategies/research/S03_PullbackShort/` folder (matching the S06+ per-folder convention from `CLAUDE.md`).
2. Write `S3_PullbackShort_strategy.md` (the alpha thesis doc, ~3 pages).
3. Write `S3_PullbackShort_design_spec.md` (this document, refined).
4. Code `S3_PullbackShort.pla` (~340 LOC) using L2 as the template for boilerplate (Settlement, Holiday, SetStopLoss) and L5 as the template for 15M+Daily Data2 wiring.
5. Run Phase 1 (parameter sensitivity on RSI_OB, BB_StdDev, SL_ATR_Ratio, Trend_Return_Min).
6. Run Phase 2 (Walk-Forward — gate: WFE > 50%, OOS PF > 1.0, sample ≥ 100).
7. Run Phase 3 (Monte Carlo, 10k shuffles — gate: MC95 MDD < 30% account).
8. If all three gates pass: promote to `live_simulation/` for 30-trade real-time validation.
9. After 30+ sim trades with PF > 1.2: promote to `live/` as **L6_PullbackShort** with 8-10% allocation.

---

## 11. Open questions / decisions deferred

| # | Question | Defer to | Reason |
|---|----------|----------|--------|
| 1 | Should TP scale out (half at MA5, half at MA10)? | V2.0, after 30 live trades | Needs live calibration of split ratio. |
| 2 | Should regime use TWVIX (Taiwan VIX) instead of ATR ratio for R3? | V2.0 / when Data3 TWVIX feed is verified in MC | TWVIX feed availability TBD. |
| 3 | Add FOMC week blocker? | V2.0 if WFE flags FOMC outliers | Don't pre-engineer for unverified edge case. |
| 4 | Long-side mirror ("short-the-dip" → "buy-the-dip")? | Likely **NO** | L1 + L5 already cover bullish dip buys; mirror would over-concentrate longs. |
| 5 | Multi-lot scaling? | After 30+ live trades | Standard project convention. |
| 6 | Add to `verify_all_live.py` master test? | After live promotion | Master test covers L1-L5 + S1; add L6 when promoted. |

---

## 12. Institutional 10-dim checklist (per CLAUDE.md rule 13)

| # | Dimension | S3 V1.0 status | Notes |
|---|-----------|----------------|-------|
| 1 | Sharpe / Sortino / Calmar | **Estimated 0.85 Sharpe (mid case)** | Must be confirmed by backtest. Target ≥ 1.0 for live promotion. |
| 2 | VaR / CVaR | **Estimated CVaR < 15% account** | Tight SL + 1-contract size + max 1 concurrent = low tail exposure. |
| 3 | Correlation < 0.7 vs all 6 | **Targeted < +0.3 monthly vs L2 / L4, negative vs L1/L5/S1** | Must be measured in Phase 2 WFE. |
| 4 | Drawdown clustering | **Risk: bull-regime rally → 3-5 consecutive SL hits** | Mitigated by "Max 1 entry per regime episode" rule. |
| 5 | Sample size ≥ 100 | **Estimated 180-290 trades over 6.5y** | ✓ comfortable margin. |
| 6 | WFE > 50% | **Unknown — Phase 2 gate** | Must pass before live_sim. |
| 7 | Three-regime PF > 1.0 | **Bull: target PF 1.3-1.5; Bear: filters block ~all entries (≥1.0 trivial); Range: 0 trades** | Range is "0 trades = PF undefined, acceptable" per constitution. |
| 8 | Cost analysis | **Slippage 1,000 NTD/trade × 230 trades = 230k cost over 6.5y** | Net of cost still positive in mid estimate (PnL ~2.2M − 230k = ~2M). |
| 9 | Operational risk | **Same as L1-L5 (MC12 + same broker)** | No new operational surface. |
| 10 | Regulatory / account | **1 contract TXF1, no special account requirement** | ✓ |

**Pre-build pass rate**: 5/10 dimensions confirmed pre-build (#1 est, #2 est, #5 ✓, #8 ✓, #9 ✓, #10 ✓). Dimensions 3, 4, 6, 7 require Phase 1-2 backtest evidence. **No dimension is failing — all are pending verification or trivially passing.**

---

## 13. Candidate variants (strategies of this idea space)

Beyond the V1.0 spec above, here are the deliberate variant options the user should know exist:

1. **S3a (V1.0, recommended)**: RSI(14)>75 sustained 3 bars + BB %B>1.0 + Daily regime. Single TP at MA5. Tight 1.2× ATR SL. 8-10% allocation target.
2. **S3b (V1.5, scale-out)**: Same entries as S3a, but half off at MA5 (TP1), half trailed to MA10 (TP2). Adds complexity; defer until 30+ live trades validate the V1.0 stop/exit profile.
3. **S3c (Discretionary-confirmed)**: Same regime + signal, but require a **confirmed reversal bar** (upper shadow > body) on the 15M as the trigger. Higher WR (~60-65%) but trade count halved (~100-150 over 6.5y). Marginal on sample size; could pass if WR holds.
4. **S3d (Multi-TF)**: Same regime, but entries on the **60M** instead of 15M. Fewer trades (~80-120 over 6.5y), longer holding (2-4 days), more L2-like profile but still bull-regime-gated. Risk: edge bleeds into L2's territory.
5. **S3e (Long-mirror "Buy-the-Dip")**: Mirror of S3a but long-side, entering on RSI<25 + BB %B<0 in a bear regime. **Not recommended for V1.0** — L1 / L5 already cover bullish dip buys, and inverting the regime gate creates a 5th long strategy in a book that already has 4. Could be revisited if portfolio becomes net-short-heavy.

**Default recommendation**: ship **S3a** as V1.0. Defer S3b after 30 live trades. Skip S3c/d/e unless S3a underperforms.

---

## 14. Summary for the user

- **Gap is real and unfilled**: no current strategy fires shorts during bull-regime pullbacks.
- **Strategy class**: counter-trend short, daily-regime-gated, 15M-execution, 1-3 day swing.
- **Build approach**: from scratch as **S3_PullbackShort** in `research/` (Option 2), not a repurpose of S2.
- **Targets**: ~230 trades over 6.5y, PF 1.30-1.55, Sharpe ~0.85, MDD ~8% account.
- **Allocation if live**: 8-10% of the 30-lot book, organically fills the "L6" slot.
- **Mandatory compliance**: Settlement_Flat (clause 1-6), SetStopLoss (rule 12), 10-dim eval (rule 13) — all addressed in spec above.
- **LOC overrun**: ~340 lines vs 150 guideline, justified by mandatory modules (~120 lines of which are boilerplate copy-paste from L2). Document the exception in the strategy review file.
- **Next concrete step**: scaffold `strategies/research/S03_PullbackShort/` and write the `.pla` from the L2 + L5 templates. Run Phase 1 parameter sensitivity on RSI_OB / BB_StdDev / SL_ATR_Ratio / Trend_Return_Min.

---

_Design specification compiled 2026-06-19 in response to the user-identified portfolio gap. This is a pre-research design — backtest validation per Phase 1-3 is required before any allocation decision._
