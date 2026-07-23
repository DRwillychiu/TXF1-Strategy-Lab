# L1 IOG Migration Spec — V3.0 Architectural Upgrade

| Field | Value |
|---|---|
| Status | DRAFT v2 — gap detection fix applied, adversarial audit 22/22 PASS |
| Date | 2026-07-23 |
| Target | L1_TrendLong.pla V2.9.1 → V3.0 |
| Prerequisite | None (spec only, no code changes) |

## 1. Problem Statement

L1 IOG=false evaluates strategy logic ONLY at 45-minute bar close.
This creates a ~90 minute blind spot for profit protection:

- P7 threshold check `(Close - Entry_P) >= 500` misses intrabar peaks
- P7 peak tracking `posbleProfit_Long` only captures bar-close peaks
- P4 trail updates only at bar close (ratchet upgrade blocked)
- Exit orders placed at bar close wait until next bar to execute

User's trade 2026-07-22: entry 44,739, intrabar High +466 pts, bar Close
max +416 pts. P7 threshold 500 never reached. Trade exited at -89 pts.
With IOG, P7 would have tracked the +466 intrabar peak in real-time.

## 2. IOG Core Mechanics Reference

### 2.1 Price Variables Under IOG=true

| Variable | IOG=false (bar close only) | IOG=true (every tick) |
|---|---|---|
| `Close` | Bar close price | **Current tick price** |
| `High` | Bar high | **Developing bar high** |
| `Low` | Bar low | **Developing bar low** |
| `Open` | Bar open | Bar open (unchanged) |

### 2.2 BarStatus(1) Values

| Value | Meaning | Use |
|---|---|---|
| 0 | First tick of bar (bar open) | Gap detection |
| 1 | Middle tick | Normal intrabar |
| 2 | Last tick of bar (bar close) | Guard indicator calc / entries |
| -1 | Recalculation after bar close | Rare edge case |

### 2.3 Order Behavior — CRITICAL CHANGE

| Syntax | IOG=false | IOG=true |
|---|---|---|
| `next bar at X Stop` | Active from next 45M bar | Active from **next tick** |
| `next bar at Market` | Fills at next bar open | Fills at **next tick** |
| `this bar at ...` | Normal | **PROHIBITED intrabar** |

Implication: exit stop orders now update every tick and can fill within the
same 45M bar. Entry market orders fill within 1 tick of signal.

### 2.4 IntraBarPersist — CRITICAL

Without `IntraBarPersist`, variables **RESET on each tick** to their
bar-open value. Any variable that accumulates across ticks within a bar
MUST be declared with this attribute.

```
{ WRONG — resets every tick, ratchet fails silently }
variables: posbleProfit_Long(0);

{ CORRECT — persists across ticks within bar }
variables: IntraBarPersist posbleProfit_Long(0);
```

**Failure mode**: without IntraBarPersist, posbleProfit_Long resets to its
bar-open value on every tick. P7 cannot ratchet-track intrabar peaks.
The strategy APPEARS to work (compiles, runs) but P7 is silently broken.
This is the single highest-risk item in this migration.

### 2.5 Multi-Data Behavior

IOG operates on **Data1 only**. Data2 (daily) and Data3 (weekly) update
only at their own bar close, NOT on every Data1 tick.

| Reference | Behavior with IOG |
|---|---|
| `Close of Data2` | Returns developing daily bar value (unstable intrabar) |
| `Close of Data3` | Returns developing weekly bar value (unstable intrabar) |
| `AvgTrueRange(N) of Data2` | Recalculates with developing daily bar |

All Data2/Data3 references must be guarded with `BarStatus(1) = 2`.

### 2.6 Backtesting with IOG

| Mode | Behavior | Accuracy |
|---|---|---|
| IOG=true, no Bar Magnifier | 4 evaluations per bar (O, H, L, C) | LOW — simulated, not real tick sequence |
| IOG=true + Bar Magnifier 1M | Evaluates at every 1-min bar close | MEDIUM — good for most strategies |
| IOG=true + Bar Magnifier tick | Evaluates at every tick | HIGH — requires tick data |

**MANDATORY**: enable Bar Magnifier (1 minute minimum) in MC strategy
properties for any IOG=true backtest. Without it, results are unreliable.

### 2.7 SetStopLoss and IOG

SetStopLoss is engine-level. With IOG=true, the engine monitors stop
price on every tick regardless. The script's `SetStopLoss()` call sets
the level; the engine enforces it continuously.

Current L1 flow with IOG:
1. BarStatus=2: indicators calculate, SetStopLoss called (MP=0)
2. BarStatus=2: entry condition evaluates, Buy placed
3. First tick of next bar: Buy fills, MP=1
4. SetStopLoss no longer called (MP>0 guard), engine holds the level
5. Engine-level stop active from fill tick — no gap

## 3. L1 Code Changes — Line-by-Line

### 3.1 Strategy Attribute (line 184)

```
{ BEFORE }
[IntrabarOrderGeneration = false]

{ AFTER }
[IntrabarOrderGeneration = true]
```

### 3.2 Variable Declarations — IntraBarPersist (lines 226-268)

Add IntraBarPersist to these existing variables:

```
{ P7 peak tracking — MUST persist across ticks }
IntraBarPersist posbleProfit_Long(0),
IntraBarPersist stopProfitPrice_L(0),

{ P4 ratchet — new variable, MUST persist }
IntraBarPersist v_Trail_High(0),
```

Variables that must NOT have IntraBarPersist (keep normal):
- `v_SL_Locked` — one-time flag, guarded by BarStatus=2
- `v_Frozen_SL` — frozen value, set once at BarStatus=2
- `v_Weekly_Filter` — recalculated at BarStatus=2
- `v_Holiday_Block` — recalculated at BarStatus=2

### 3.3 MUST GUARD — BarStatus(1) = 2

#### 3.3a Core Indicators (lines 383-389)

```
{ BEFORE }
maBase  = Average(Close, Length60);
maTrail = Average(Close, Length20);
Current_ATR = AvgTrueRange(ATR_Length) of Data1;
Daily_ATR   = AvgTrueRange(ATR_Length) of Data2;
Breakout_Level = maBase + (Current_ATR * Entry_Multiplier);

{ AFTER }
if BarStatus(1) = 2 then begin
    maBase  = Average(Close, Length60);
    maTrail = Average(Close, Length20);
    Current_ATR = AvgTrueRange(ATR_Length) of Data1;
    Daily_ATR   = AvgTrueRange(ATR_Length)[1] of Data2;  { V3.0: [1] fix, Rule 3 }
    Breakout_Level = maBase + (Current_ATR * Entry_Multiplier);
end;
```

Note: `Daily_ATR` gets the `[1]` fix (previous completed daily bar) as
part of this migration. See Section 3.8 for rationale.

#### 3.3b Weekly Filter (lines 398-405)

```
{ AFTER }
if BarStatus(1) = 2 then begin
    v_Weekly_MA_Fast = Average(Close, Weekly_MA_Fast) of Data3;
    v_Weekly_MA_Slow = Average(Close, Weekly_MA_Slow) of Data3;
    if (Close of Data3 > v_Weekly_MA_Fast) or
       (Close of Data3 > v_Weekly_MA_Slow) then
        v_Weekly_Filter = true
    else
        v_Weekly_Filter = false;
end;
```

#### 3.3c Entry Logic (lines 466-489)

```
{ AFTER }
if BarStatus(1) = 2 then begin
    Cond_Breakout = (Close Crosses Over Breakout_Level);

    if MP = 0 and
       Cond_Breakout and
       (v_Weekly_Filter = true) and
       (v_Holiday_Block = false) and
       (v_Settlement_Day = false) then begin
        Buy ("TL_Entry") next bar at Market;
    end;
end;
```

`Crosses Over` in IOG uses tick-to-tick comparison = extreme noise.
BarStatus=2 guard restores bar-close-to-bar-close comparison.

#### 3.3d P3 Frozen SL Lock (lines 503-508)

```
{ AFTER }
if BarStatus(1) = 2 then begin
    if v_SL_Locked = False then begin
        Exit_Price_ATR = Entry_P - (Current_ATR * SL_Multiplier);
        Exit_Price_Cap = Entry_P - (Daily_ATR * Daily_Cap_Multiplier);
        v_Frozen_SL    = MaxList(Exit_Price_ATR, Exit_Price_Cap);
        v_SL_Locked    = True;
    end;
end;
```

P3 must freeze with stable bar-close ATR values, not tick ATR.

#### 3.3e Holiday Loop (lines 415-434)

```
{ AFTER — guard reduces 80-iteration loop from every-tick to bar-close }
if BarStatus(1) = 2 then begin
    v_Holiday_Block = False;
    if Time <= 500 then begin
        for idx = 1 to 80 begin
            if Date = Holiday_Tail[idx] then
                v_Holiday_Block = True;
        end;
    end;
    v_Registry_Expired = False;
    if Date > Registry_Valid_Until then begin
        v_Registry_Expired = True;
        v_Holiday_Block    = True;
    end;
end;
```

#### 3.3f MDD Visualizer (lines 595-640)

```
{ AFTER — wrap entire MDD section }
if BarStatus(1) = 2 then begin
    { ... existing MDD code unchanged ... }
end;
```

### 3.4 MUST ALLOW INTRABAR — No Guard

#### 3.4a P7 Profit Tracking (lines 516-521)

```
{ AFTER — runs every tick, tracks real-time peaks }
{ posbleProfit_Long and stopProfitPrice_L declared IntraBarPersist }
if (Close - Entry_P) >= stopProfitPoints_Long then begin
    if (Close - Entry_P) > posbleProfit_Long then
        posbleProfit_Long = Close - Entry_P;
    stopProfitPrice_L = Entry_P +
        (posbleProfit_Long * (1.0 - profitReturnPrcnt_Long / 100.0));
end;
```

This is the core purpose of the IOG migration. `Close` = tick price,
so P7 now captures intrabar peaks in real-time.

#### 3.4b P4 Trail + Ratchet (line 528-530)

```
{ BEFORE }
Exit_Price_Trail = maTrail - TrailOffset;

{ AFTER — ratchet: v_Trail_High declared IntraBarPersist }
{ Note: maTrail is guarded by BarStatus=2, so it only updates at
  bar close. The ratchet checks on every tick but uses the latest
  bar-close maTrail value. This is correct: the ratchet locks the
  highest bar-close MA55 level, not noisy tick-level MA. }
v_Trail_High = MaxList(v_Trail_High, maTrail - TrailOffset);
Exit_Price_Trail = v_Trail_High;

Final_Exit_Price = MaxList(Exit_Price_Trail,
                   MaxList(Exit_Price_SL, stopProfitPrice_L));
```

Design choice: maTrail updates at bar close (stable), ratchet only
moves up. The ratchet value persists across ticks (IntraBarPersist).

#### 3.4c Exit Order Placement (lines 535-549)

Exits run on every tick — this is the IOG payoff: stops can fill
intrabar as soon as price reaches the level.

**Gap detection fix** (line 535): detect at bar CLOSE, not bar open.

Original draft proposed `BarStatus(1) = 0` (bar open). Adversarial audit
(Test F, 2026-07-23) proved this is dead code: at bar open, the pending
stop from the previous tick fires BEFORE the script evaluates, so MP=0
and the if-MP>0 block never executes. If the bar gaps UP above the stop,
the stop doesn't fill but Close > Final_Exit_Price, so the gap condition
is also false. Either way, the code is unreachable.

The real gap scenario: at BarStatus=2, indicators recalculate and stop
level JUMPS above Close (e.g. maTrail ratchets up). Price is already
below the new stop. A stop order can't fill downward from below; market
order guarantees exit.

```
{ BEFORE }
if Close < Final_Exit_Price then begin

{ AFTER v2 — gap = bar CLOSE recalc pushed stop above Close }
if BarStatus(1) = 2 and Close < Final_Exit_Price then begin
    if Final_Exit_Price >= Entry_P then
        Sell ("TL_SP_Gap") next bar at Market
    else
        Sell ("TL_SL_Gap") next bar at Market;
end else begin
    { Normal: stop order on every tick }
    if AbsValue(Final_Exit_Price - Exit_Price_SL) < 0.001 then
        Sell ("TL_SL") next bar at Final_Exit_Price Stop
    else if stopProfitPrice_L > 0 and
            AbsValue(Final_Exit_Price - stopProfitPrice_L) < 0.001 then
        Sell ("TL_SP") next bar at Final_Exit_Price Stop
    else if Exit_Price_Trail >= Entry_P then
        Sell ("TL_TP") next bar at Final_Exit_Price Stop
    else
        Sell ("TL_TSL") next bar at Final_Exit_Price Stop;
end;
```

Why BarStatus=2 is correct:
- Intrabar (BarStatus=1): indicators don't recalculate, stop level stable.
  If price crosses below stop, the stop order fills on the next tick. No
  gap scenario possible — handled by the else branch's stop order.
- Bar close (BarStatus=2): indicators recalculate, stop may jump. If jump
  pushes stop above Close, market order guarantees immediate exit.
- Bar open (BarStatus=0): pending stop from previous tick fills before
  script runs (if price <= stop) or doesn't fire (if price > stop). Gap
  detection at bar open is unreachable dead code.

Behavioral difference from V2.9.1: when the gap fires at bar close,
the market order fills at the first tick of the next bar. In V2.9.1,
this same scenario placed a market order at bar close, filling at the
next bar open. Timing is identical. Label semantics preserved.

#### 3.4d Forced Flat Exits (lines 572-588)

Holiday/Settlement/Registry/Kill exits run on every tick — immediate
execution is desired for safety exits.

#### 3.4e SetStopLoss / SetStopContract (lines 478-481)

No change needed. SetStopLoss runs every tick when MP<=0, using the
latest bar-close ATR values (since indicators are BarStatus-guarded).
Engine-level protection is active from the fill tick.

### 3.5 Flat Reset (lines 552-558)

```
{ AFTER — add v_Trail_High reset }
v_SL_Locked       = False;
v_Frozen_SL       = 0;
posbleProfit_Long = 0;
stopProfitPrice_L = 0;
v_Trail_High      = 0;    { P4 ratchet reset }
```

### 3.6 NO CHANGE NEEDED

| Lines | Section | Reason |
|---|---|---|
| 186-271 | Inputs / Variables / Array | Declarations (except IntraBarPersist additions) |
| 292-377 | Holiday Registry Init | `Init_Done` one-time guard protects |
| 443-445 | Settlement Detection | `DayOfWeek`/`DayOfMonth` constant intrabar |

### 3.7 P7 Threshold Change

```
{ BEFORE }
stopProfitPoints_Long(500),

{ AFTER — V3.0 baseline }
stopProfitPoints_Long(200),
```

Backtest parameter sweep (to be run by user):
- Threshold: 50, 100, 150, 200, 250, 300, 400, 500 (8 levels)
- Giveback %: 10, 15, 20, 25, 30, 35, 40, 45 (8 levels)
- Total: 64 combinations

### 3.8 Daily_ATR [1] Fix (line 387 / 505)

```
{ BEFORE }
Daily_ATR = AvgTrueRange(ATR_Length) of Data2;

{ AFTER }
Daily_ATR = AvgTrueRange(ATR_Length)[1] of Data2;
```

Rationale: Rule 3 compliance. Data2 current bar incomplete during
intraday trading. `[1]` references previous completed daily bar.
Impact: P3 frozen SL uses stable, finalized daily ATR.

Note: the `[1]` syntax on cross-data functions should be verified in
MC12. If `AvgTrueRange(N)[1] of Data2` does not compile, alternative:

```
v_Daily_ATR_Raw = AvgTrueRange(ATR_Length) of Data2;
{ Use v_Daily_ATR_Raw[1] in the P3 calculation: }
Exit_Price_Cap = Entry_P - (v_Daily_ATR_Raw[1] * Daily_Cap_Multiplier);
```

## 4. Architecture Summary

```
IOG=true: script evaluates on every Data1 tick
    |
    +-- BarStatus(1) = 2 (bar close only):
    |       Indicators (MA, ATR, Breakout_Level)
    |       Weekly filter (Data3)
    |       Entry conditions (Crosses Over)
    |       P3 frozen SL lock
    |       Holiday / Registry detection
    |       MDD visualizer
    |
    +-- Every tick (no guard):
    |       P7 profit tracking (IntraBarPersist)
    |       P4 ratchet trail (IntraBarPersist)
    |       Final_Exit_Price calculation
    |       Exit order placement (stop orders)
    |       Forced flat exits (market orders)
    |       SetStopLoss engine guard
    |
    +-- BarStatus(1) = 2 (bar close, gap detection):
            If indicator recalc pushes stop above Close
            → market order (TL_SL_Gap / TL_SP_Gap)
```

## 5. Backtest Configuration

### 5.1 MC Strategy Properties

```
IntrabarOrderGeneration = true
Bar Magnifier = enabled
Bar Magnifier Resolution = 1 Minute (minimum) or 1 Tick (ideal)
```

### 5.2 Data Requirements

MC12 must have **1-minute data** for TXF1 covering the full backtest
period (2020-01-01 to today). Check MC Data Manager for availability.

### 5.3 Validation Method

1. Run V2.9.1 (IOG=false) baseline → record all trades, P&L, labels
2. Run V3.0 (IOG=true) with SAME parameters → compare
3. Expected differences:
   - More P7 activations (intrabar peaks captured)
   - Different exit timing (intrabar stops vs next-bar stops)
   - Entry count should be IDENTICAL (BarStatus=2 guard)
4. If entry count differs → BarStatus guard has a bug, investigate

## 6. Risk Assessment

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | IntraBarPersist omission | **CRITICAL** | Audit every variable in P7/P4 ratchet. Without it, ratchet silently resets every tick. |
| 2 | Entry false signals | HIGH | BarStatus=2 guard on ALL entry conditions. Verify entry count matches V2.9.1. |
| 3 | P3 frozen SL drift | HIGH | BarStatus=2 guard. Verify frozen SL values match V2.9.1 for same trades. |
| 4 | Gap label misfire | MEDIUM | BarStatus=2 guard (v2 fix). Gap fires only when bar-close indicator recalc pushes stop above Close. Verify label distribution. |
| 5 | Backtest/live inconsistency | MEDIUM | Always use Bar Magnifier. Compare IOG-on backtest vs live behavior. |
| 6 | Data2/Data3 instability | MEDIUM | BarStatus=2 guard. Weekly filter must not flip intrabar. |
| 7 | Performance degradation | LOW | TXF1 tick rate is moderate (~1-5 ticks/sec). Monitor CPU. |

## 7. Verification Checklist (User Runs)

Pre-deployment checklist — ALL must PASS:

- [ ] MC12 compiles V3.0 without errors
- [ ] V3.0 entry count = V2.9.1 entry count (same period, same params)
- [ ] P3 frozen SL values identical for matched trades
- [ ] P7 activates on trades where intrabar High >= Entry + threshold
- [ ] posbleProfit_Long tracks intrabar peaks (check via MC debugger)
- [ ] Weekly filter does NOT flip during intrabar evaluation
- [ ] Holiday/Settlement exits fire at correct times
- [ ] Gap labels (TL_SL_Gap, TL_SP_Gap) only appear when bar-close recalc pushes stop above Close
- [ ] v_Trail_High resets to 0 on each new trade (flat reset)
- [ ] No duplicate entries within same bar
- [ ] Bar Magnifier enabled (1 min minimum)
- [ ] ASCII verification passes (`verify_pla_ascii.py --strict`)

## 8. Deferred Items (Not in V3.0)

These are queued for subsequent versions:

1. **P7 threshold + giveback % optimization**: 64-combo parameter sweep
   (after V3.0 IOG baseline is validated)
2. **P4 MA type**: SMA vs EMA vs ZLEMA comparison + length sweep 30-80
   (after V3.0 ratchet baseline is validated)
3. **P4 entry-bar tightness**: activation threshold for ratchet
4. **P4 MA spike protection**: max step limit per bar
5. **P3 initial stop alternatives**: non-ATR stop designs

## 9. Implementation Order

```
Step 1: Write V3.0 code (apply all changes in this spec)
Step 2: Backup V2.9.1 → L1_TrendLong.pla.bak_20260723
Step 3: MC12 compile
Step 4: Run V2.9.1 baseline backtest (record trades)
Step 5: Run V3.0 backtest (Bar Magnifier ON)
Step 6: Compare entry counts, frozen SL values, label distributions
Step 7: If mismatch → investigate, do NOT proceed
Step 8: If match + P7 improved → user approves
Step 9: MC9 deployment (user action, flat only)
Step 10: First 3 trades: verify stop distances, labels, P7 activation
```

## 10. Adversarial Self-Audit (2026-07-23)

Zero risk tolerance. 22 tests across 7 categories. 22 PASS / 0 FINDING.

### Category A: IntraBarPersist Coverage (4/4 PASS)
- A1: posbleProfit_Long declared IntraBarPersist — PASS
- A2: stopProfitPrice_L declared IntraBarPersist — PASS
- A3: v_Trail_High declared IntraBarPersist — PASS
- A4: No other tick-updated variable missing IntraBarPersist — PASS
  (v_SL_Locked, v_Frozen_SL are BarStatus=2 guarded; Exit_Price_Trail,
   Final_Exit_Price are recalculated from IntraBarPersist vars each tick)

### Category B: BarStatus Guard Completeness (4/4 PASS)
- B1: Indicators (MA, ATR, Breakout_Level) — BarStatus=2 guarded — PASS
- B2: Weekly filter (Data3) — BarStatus=2 guarded — PASS
- B3: Entry (Crosses Over, Buy) — BarStatus=2 guarded — PASS
- B4: P3 frozen SL lock — BarStatus=2 guarded — PASS

### Category C: Entry Bar Safety (3/3 PASS)
- C1: P3b SetStopLoss fires from fill tick (engine-level) — PASS
- C2: P3 frozen SL locks at entry bar close (BarStatus=2) — PASS
- C3: No entry-bar gap where position is unprotected — PASS
  (SetStopLoss covers fill-tick to first bar close; P3 locks at close)

### Category D: Data Boundary (2/2 PASS)
- D1: Data2 (Daily) BarStatus=2 guarded, [1] fix applied — PASS
- D2: Data3 (Weekly) BarStatus=2 guarded — PASS

### Category E: Stuck State Prevention (3/3 PASS)
- E1: Flat reset clears all IntraBarPersist vars — PASS
- E2: v_Trail_High = 0 on flat — PASS
- E3: v_SL_Locked = False on flat — PASS

### Category F: Gap Detection (4/4 PASS)
- F1: BarStatus=2 guard correct (v2 fix) — PASS
  (v1 draft had BarStatus=0 → dead code. Fixed to BarStatus=2:
   detects indicator-recalc stop jump above Close at bar close)
- F2: Normal intrabar exits handled by stop order — PASS
- F3: Market order at bar close fills at next tick = V2.9.1 parity — PASS
- F4: Labels TL_SL_Gap / TL_SP_Gap preserved for true gap events — PASS

### Category G: Order Semantics (2/2 PASS)
- G1: "next bar" = next tick in IOG, entries guarded to BarStatus=2 — PASS
- G2: "this bar" orders not used anywhere — PASS

### Audit Note

Original v1 draft had 21 PASS / 1 FINDING (F1: BarStatus=0 dead code).
v2 fix applied BarStatus=2 guard. Re-audit confirms 22/22 PASS.

## 11. Source References

- [MC IOG Explained](https://www.multicharts.com/trading-software/index.php?title=Intra-Bar_Order_Generation_(IOG)_Explained)
- [MC BarStatus](https://www.multicharts.com/trading-software/index.php?title=BarStatus)
- [MC IntraBarPersist](https://www.multicharts.com/trading-software/index.php?title=IntraBarPersist)
- [MC Calculation per Bar](https://www.multicharts.com/trading-software/index.php/4.6.6_Calculation_per_Bar)
- [MC Bar Magnifier](https://www.multicharts.com/trading-software/index.php/Bar_Magnifier)
