# P3b Immediate Stop Guard Design Discussion (2026-06-18)

**Status**: PHASE 1 IN PROGRESS — L1 implemented (2026-06-18), S1 next
**Trigger**: User discovered L1 entry fill had no initial stop on chart
**Root cause**: IOG=false + stop computed in `if MP>0` block = entry bar has 0 protection

---

## 1. Problem Statement

All 6 strategies (L1-L5, S1) share the same structural vulnerability:

```
IOG = false (all 6 strategies)
  -> Script evaluates at bar CLOSE only
  -> Entry fills at bar N+1 OPEN
  -> Stop computed at bar N+1 CLOSE (if MP>0 block)
  -> Stop active from bar N+2
  -> Entry bar (bar N+1) = 45 minutes with ZERO stop protection
     (15 minutes for S1)
```

### Impact at scale

```
1 contract:   500 pts adverse move × 200 NTD/pt = 100,000 NTD unprotected loss
              vs intended SL ~150 pts = 30,000 NTD
              excess = 70,000 NTD (2.3x intended risk)

500 contracts: 500 pts × 200 × 500 = 50,000,000 NTD unprotected
               intended SL = 15,000,000 NTD
               excess = 35,000,000 NTD — entirely avoidable
```

This is NOT a probability issue. It is an architectural defect.

---

## 2. Institutional Defense-in-Depth Model

```
Layer 3 (outermost): Broker-side hard stop
  - OCO / bracket orders at exchange level
  - Survives: MC crash, power failure, network outage
  - Implementation: manual broker setup after each entry

Layer 2 (middle): SetStopLoss engine-level guard
  - MC engine applies stop immediately on fill
  - Survives: script logic errors, IOG=false delay
  - Implementation: 1 line per strategy in .pla

Layer 1 (innermost): Frozen SL + Trail/SP/BE strategy logic
  - Precise stop management with ratchet mechanisms
  - Active from bar N+2 onward
  - Implementation: existing V2.5/V2.6 code
```

Current state: Layer 1 only. Layer 3 = user manual operation.
**Layer 2 = the gap this design fills.**

---

## 3. Proposed Solution: SetStopLoss Integration

### Mechanism

```powerlanguage
{ Computed every bar when flat, frozen when position established }
if MarketPosition <= 0 then
    SetStopLoss(stop_distance_points * BigPointValue);
```

- `BigPointValue` = 200 for TXF1 (1 point = 200 NTD)
- `SetStopLoss` is an MC ENGINE function, not a script-level order
- It creates a stop relative to EntryPrice (auto-adjusts to actual fill)
- When not re-called (MP > 0), retains last value = FROZEN

### Per-strategy formulas

| Strategy | Bar | Direction | Stop Distance Formula | SetStopLoss Call |
|----------|-----|-----------|----------------------|-----------------|
| L1 | 45M | Long | `MaxList(ATR×1.5, D_ATR×0.5)` | `MaxList(Current_ATR*SL_Multiplier, Daily_ATR*Daily_Cap_Multiplier) * BigPointValue` |
| L2 | 45M | Short | `DC_Lower + ATR×1.1 - Entry` | `AbsValue(DC_Lower + ATR_Val*SL_ATR_Ratio - Close) * BigPointValue` |
| L3 | 45M | Long | `Entry - (Box_Btm - ATR×3.0)` | `AbsValue(Close - (v_Box_Btm - v_Current_ATR*ATR_Stop_Mult)) * BigPointValue` |
| L4 | 45M | Short | `(Locked_Top + ATR×2.0) - Entry` | `AbsValue((v_Locked_Top + v_Current_ATR*ATR_Stop_Mult) - Close) * BigPointValue` |
| L5 | 45M | Long | `Entry - (Box_Btm - ATR×4.5)` | `AbsValue(Close - (v_Box_Btm - v_Current_ATR*ATR_Stop_Mult)) * BigPointValue` |
| S1 | 15M | Long | `ATR × 2.75` | `v_ATR * StopATRMult * BigPointValue` |

### Complexity tiers

- **Simple (pure ATR distance)**: L1, S1 — exact match to existing SL formula
- **Moderate (anchor-based)**: L2 — stop anchored to DC_Lower, uses Close as Entry proxy
- **Complex (box-based)**: L3, L4, L5 — stop anchored to box structure, Close proxy has gap risk

### Close-as-Entry-proxy error

For L2/L3/L4/L5, SetStopLoss computes distance from Close (signal bar),
but actual entry is at Open (next bar). Gap between Close and Open
introduces error:

```
Gap up  100 pts: SL distance 150 → effective distance from entry = 50 (too tight)
Gap down 100 pts: SL distance 150 → effective distance from entry = 250 (too wide)
No gap:           SL distance 150 → effective distance from entry = 150 (exact)
```

For disaster protection, "too wide" (gap down) is acceptable — still better
than NO protection. "Too tight" (gap up) could cause false stops on the
entry bar. Mitigation: add a buffer multiplier (e.g., 1.2x) to SetStopLoss
amount for box-based strategies.

---

## 4. Freezing Behavior Analysis (V2.5 Compatibility)

### User concern

> V2.5 was designed to FREEZE initial SL at entry time (stop no longer
> drifts with ATR during the trade). Does SetStopLoss maintain this?

### Answer: YES

```
SetStopLoss freezing mechanism:

  MP = 0:  SetStopLoss called every bar → updates with latest ATR
           (ready for next entry)

  MP > 0:  SetStopLoss NOT called → retains last value
           = signal bar ATR → FROZEN

  This is analogous to V2.5 Frozen SL, offset by 1 bar:
    SetStopLoss freezes at signal bar (Bar N) ATR
    Frozen SL   freezes at entry bar  (Bar N+1) ATR
    Difference  = ATR(20) change in 1 bar ≈ 2-5 pts (negligible)
```

### Timeline: which layer protects when

```
Bar N+1 (entry bar):
  SetStopLoss = SOLE protector (frozen at signal-bar ATR)
  Custom stop = not yet placed

Bar N+2 (first full bar):
  SetStopLoss = still frozen at signal-bar ATR (e.g., 23,850)
  Frozen SL   = frozen at entry-bar ATR    (e.g., 23,848)
  Custom stop = Sell next bar at 23,848 Stop
  MC takes tighter → depends on which is higher, ~same level

Bar N+5+ (trail/SP active):
  Custom stop = tightened by Trail/SP to e.g., 23,900
  SetStopLoss = still at 23,850 (frozen, now wider)
  MC takes tighter → custom stop wins (23,900)
  SetStopLoss = dormant backup floor (never triggered)
```

### V2.5 Frozen SL core principle preserved

"Stop does not drift with volatility after entry" — both SetStopLoss and
Frozen SL achieve this through different mechanisms:
- SetStopLoss: stops being called (if MP<=0 guard)
- Frozen SL: v_SL_Locked flag prevents recalculation

---

## 5. Backtest Impact

Adding SetStopLoss WILL change historical performance:
- Trades where entry bar Low < stop level → now stopped out on bar N+1
- Previously these trades survived to bar N+2 (some recovered, some didn't)
- Net effect unpredictable without running the backtest

### Required A/B comparison

For each strategy:
- Variant A: current code (no SetStopLoss) → known baseline
- Variant B: with SetStopLoss → new performance

Compare: PF, MDD, WR, total trades, net profit

### Deployment rule

Same as V2.5: deploy ONLY WHEN FLAT (changes historical exits = chart
recalculation will disagree with any live open position).

---

## 6. Implementation Plan (pending user approval)

### Phase 1: L1 + S1 (simple, pure ATR distance)
- Zero approximation error
- Fastest to validate
- L1 is the highest-impact strategy (67.3% of Settlement PnL)

### Phase 2: L2 (moderate, DC_Lower anchor)
- Close-as-Entry proxy introduces small error
- May need buffer multiplier

### Phase 3: L3, L4, L5 (complex, box-based anchor)
- Box position + Close proxy = larger potential error
- Consider safety buffer (1.2x multiplier)
- L5 has 2 entry legs (Bot/Mid) with different stop levels

### Post-implementation
- Write verify_immediate_stop_guard.py (analogous to verify_settlement_flat.py)
- Write into CLAUDE.md as mandatory rule #12
- Write design constitution amendment

---

## 7. Open Questions (for next discussion)

1. **Buffer multiplier for box-based strategies**: should SetStopLoss use
   1.0x (exact match) or 1.2x (safety margin against gap-up false stops)?

2. **L5 dual-leg complication**: L5 has Bot and Mid entries with different
   stop distances. SetStopLoss can only set ONE value. Use the WIDER of
   the two? Or the average?

3. **Should this become CLAUDE.md rule #12?** Same enforcement level as
   Settlement_Flat (rule #11)?

4. **Broker-side Layer 3**: does your broker support OCO/bracket orders?
   If yes, should we document the manual SOP for setting broker-side stops?

---

## 8. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-18 | Identified entry-bar stop gap | User observed L1 live fill with no visible stop |
| 2026-06-18 | Confirmed all 6 strategies affected | IOG=false is universal across L1-L5+S1 |
| 2026-06-18 | Selected SetStopLoss as Layer 2 solution | Engine-level, relative to EntryPrice, frozen when not called |
| 2026-06-18 | Confirmed V2.5 Frozen SL compatibility | SetStopLoss freezes via if-guard, same principle |
| 2026-06-18 | Design phase — NO code changes yet | User requires thorough discussion before implementation |
| 2026-06-18 | L1 Phase 1 implemented | SetStopLoss added to L1_TrendLong.pla, 17/17 verification pass |
