# Re-Entry Module Spec v1.0

**Date**: 2026-07-30
**Source**: S16_S v1.9.0 extraction
**Purpose**: Cross-strategy reusable re-entry logic for MultiCharts PowerLanguage

---

## 1. Module Scope

### Module Provides (strategy-independent)
- State machine: Armed -> Entry -> In-Position -> Exit -> (Re-Armed or Disarmed)
- Price tracking: v_Last_EntryPrice, v_ReEntry_Price
- ATR inheritance: v_Original_Frozen_ATR storage + retrieval for re-entry
- P7 engine guard alignment: v_Guard_Distance cap when re-entry armed
- Counter: v_ReEntry_Count + MaxReEntries cap per signal cycle
- v_IsReEntry flag: tells downstream code this trade is a re-entry
- ReEntry_On master switch

### Strategy Provides (hook points)
- Direction: Long or Short
- Primary signal: what triggers a new cycle (e.g. death cross, squeeze breakout)
- Counter-signal: what invalidates re-entry (e.g. golden cross, structure lost)
- Entry conditions: strategy-specific gates (slope, time, compliance)
- ATR calculation: how v_ATR is computed (period, method)
- Stop multiplier: StopATRMult value
- **Exit chain: entirely strategy-defined** (module does NOT dictate exit logic)

---

## 2. State Machine

```
         [Primary Signal]
              |
         MAIN ENTRY (v_IsReEntry=False)
              |
         IN POSITION (MP != 0)
              |
         EXIT (any strategy exit)
              |
    +----[Structure intact?]----+
    |                           |
   YES                         NO
    |                           |
  ARMED                     DISARMED
 (wait for price)          (cycle ends)
    |
    +----[Counter < Max?]---+
    |                       |
   YES                     NO
    |                       |
  RE-ENTRY                DISARMED
 (v_IsReEntry=True)      (cycle ends)
    |
  IN POSITION
    |
  EXIT -> back to [Structure intact?]
```

---

## 3. Inputs (Module adds 2)

| Input | Default | Description |
|-------|---------|-------------|
| ReEntry_On | True | Master switch. False = module inactive. |
| MaxReEntries | 1 | Max re-entries per primary-signal cycle. Reset on new primary signal. |

All other inputs (ATR_Len, StopATRMult, SL_Pct, entry conditions) are strategy-owned.

---

## 4. Variables (Module adds 6)

| Variable | Init | Description |
|----------|------|-------------|
| v_ReEntry_Armed | False | Currently waiting for re-entry? |
| v_ReEntry_Price | 0 | Stop order price (= last entry price) |
| v_ReEntry_Count | 0 | Entries this cycle |
| v_Last_EntryPrice | 0 | Most recent EntryPrice (set on entry bar only) |
| v_IsReEntry | False | Is current trade a re-entry? |
| v_Original_Frozen_ATR | 0 | ATR frozen at main entry, inherited by re-entries |

---

## 5. Integration Points

### 5.1 Arming (after signal detection, before entries)

```
{ HOOK: Strategy defines the primary signal (v_Death_Cross, v_Squeeze, etc.) }
{ HOOK: Strategy defines the counter-signal (v_Golden_Cross, structure lost) }

{ --- Module code --- }
if v_Prev_MP <> 0 and MarketPosition = 0 and ReEntry_On = True then begin
    v_ReEntry_Armed = True;
    v_ReEntry_Price = v_Last_EntryPrice;
end;

{ Disarm on counter-signal }
if v_ReEntry_Armed = True then begin
    if [COUNTER_SIGNAL] then begin
        v_ReEntry_Armed = False;
        v_ReEntry_Price = 0;
    end;
end;

{ Disarm + reset counter on new primary signal (new cycle) }
if [PRIMARY_SIGNAL] then begin
    v_ReEntry_Armed = False;
    v_ReEntry_Price = 0;
    v_ReEntry_Count = 0;
end;
```

**NOTE on direction**:
- `v_Prev_MP <> 0 and MarketPosition = 0` is direction-neutral
- Short: v_Prev_MP was -1; Long: v_Prev_MP was 1. Both correctly detect "just exited"

### 5.2 Frozen ATR Setup (on entry bar)

```
{ --- Module code inside the SL lock block --- }
if v_SL_Locked = False then begin
    v_Last_EntryPrice = EntryPrice;
    if v_IsReEntry = True and v_Original_Frozen_ATR > 0 then
        v_Frozen_ATR = v_Original_Frozen_ATR
    else begin
        v_Frozen_ATR = v_ATR;
        v_Original_Frozen_ATR = v_ATR;
    end;
    { ... strategy computes v_Frozen_SL_Dist, v_SL_Level from v_Frozen_ATR ... }
    v_SL_Locked = True;
end;
```

**KEY**: v_Original_Frozen_ATR is NOT reset in the flat (else) block. It must persist across the exit-to-re-entry gap.

### 5.3 P7 Engine Guard Alignment

```
{ --- Module addition to P7 block --- }
v_Guard_Distance = v_ATR * StopATRMult;
if v_ReEntry_Armed = True and v_Original_Frozen_ATR > 0 then
    v_Guard_Distance = MinList(v_Guard_Distance,
                               v_Original_Frozen_ATR * StopATRMult);
{ ... strategy applies SL_Pct cap if applicable ... }
```

### 5.4 Re-Entry Entry Block

```
if MarketPosition = 0 and
   v_ReEntry_Armed       = True and
   v_ReEntry_Count       < MaxReEntries and
   [STRUCTURE_INTACT] and           { HOOK: strategy checks bearish/bullish structure }
   [ENTRY_CONDITIONS] and           { HOOK: slope, time, compliance gates }
   [PRICE_GATE] then begin          { HOOK: directional price gate (see 5.5) }
    v_IsReEntry = True;
    v_ReEntry_Count = v_ReEntry_Count + 1;
    v_ReEntry_Armed = False;
    [ENTRY_ORDER];                  { HOOK: direction-specific order (see 5.5) }
end;
```

### 5.5 Long vs Short Differences (only 3 places)

| Item | Short | Long |
|------|-------|------|
| Entry order | `sell short next bar at Price stop` | `buy next bar at Price stop` |
| Price gate | `Close >= v_ReEntry_Price` (price above, wait for drop) | `Close <= v_ReEntry_Price` (price below, wait for rise) |
| SL direction | `v_SL_Level = Entry + Dist` (above entry) | `v_SL_Level = Entry - Dist` (below entry) |

All other logic (arming, disarming, ATR inheritance, counter, P7 cap) is identical.

### 5.6 Flat-State Cleanup

```
{ --- In the else block (when MP = 0) --- }
else begin
    v_SL_Locked = False;
    v_Frozen_ATR = 0;
    v_Frozen_SL_Dist = 0;
    v_SL_Level = 0;
    v_IsReEntry = False;        { Module: reset flag }
    { v_Original_Frozen_ATR: NOT reset here (persists for re-entry) }
    { v_ReEntry_Count: NOT reset here (persists until new primary signal) }
    { v_ReEntry_Armed: NOT reset here (persists during flat period) }
end;
```

---

## 6. Exit Integration (hook-based, NOT hardcoded)

The module does NOT define any exit conditions. Each strategy owns its full exit chain.

What the module provides to exits:

| Variable | Used By Exit For |
|----------|-----------------|
| v_Frozen_ATR | Any ATR-based exit calculation (SL distance, ML activation, BE trigger) |
| v_Original_Frozen_ATR | v1.8.0 inheritance: re-entry uses same ATR as main entry |
| v_IsReEntry | Strategy can differentiate exit behavior if needed (optional) |
| v_SL_Level | Frozen SL price (computed by strategy using module's ATR) |

Exit chain examples from different strategies:

**S16_S (Short, 10 layers)**:
QS_Loss -> QS_Time -> ML -> BE -> GoldenCross -> TimeStop -> FrozenSL -> SetStopLoss

**Hypothetical L1 (Long, 5 layers)**:
QS_Loss -> TrailStop -> TimeStop -> FrozenSL -> SetStopLoss

**Hypothetical S3_S (Short, 7 layers)**:
QS_Loss -> ML -> BE -> SqueezeEnd -> TimeStop -> FrozenSL -> SetStopLoss

The module guarantees that whichever exit fires, the ATR-dependent calculations use the correct (inherited) ATR. The strategy decides which exits exist and their priority order.

---

## 7. Integration Checklist

When adding re-entry to a new strategy:

- [ ] Add 2 inputs: ReEntry_On, MaxReEntries
- [ ] Add 6 variables: v_ReEntry_Armed, v_ReEntry_Price, v_ReEntry_Count, v_Last_EntryPrice, v_IsReEntry, v_Original_Frozen_ATR
- [ ] Add v_Prev_MP variable if not present (set at script end: `v_Prev_MP = MarketPosition`)
- [ ] Insert arming block after signal detection, before entries
- [ ] Define COUNTER_SIGNAL (what disarms) and PRIMARY_SIGNAL (what resets cycle)
- [ ] Insert ATR inheritance in frozen SL setup (v_SL_Locked = False block)
- [ ] Move v_Last_EntryPrice inside v_SL_Locked = False block
- [ ] Add P7 guard cap (MinList when v_ReEntry_Armed)
- [ ] Add re-entry entry block with counter gate + direction-correct price gate + order
- [ ] Add v_IsReEntry = False in flat-state else block
- [ ] v_Original_Frozen_ATR: do NOT reset in flat block
- [ ] Set v_IsReEntry = False in main entry block
- [ ] Existing exit chain: replace hardcoded ATR with v_Frozen_ATR where appropriate
- [ ] Run ASCII verification
- [ ] Backtest: compare with/without re-entry (ReEntry_On True vs False)

---

## 8. Known Constraints

1. **IOG=False assumed**: Arming/disarming runs once per bar at close. Intra-bar exits that would arm mid-bar are deferred to next bar close.

2. **Single re-entry price**: Uses last EntryPrice only. No support for multiple price levels or adaptive re-entry prices.

3. **No re-entry-specific exits**: Re-entry trades share the same exit chain as main entries. If a strategy needs different exit behavior for re-entries, use `v_IsReEntry` to branch inside the exit logic (strategy's responsibility, not the module's).

4. **P7 cap direction**: MinList works for both Long and Short because v_Guard_Distance is always a positive distance. SetStopLoss takes an absolute dollar amount, direction-independent.

---

**End of REENTRY_MODULE_SPEC v1.0**
