# L5 v19.9 Removed Code Archive (2026-06-25)

> Purpose: Complete record of all code removed from L5_BreakoutLong.pla
> when simplifying for 1-contract operation. Restore these sections
> when scaling to multi-contract (5+ contracts recommended).

## Why removed

At 1 contract (100W capital):
- `ScaleOut_Size = Round(1 * 0.4, 0) = 0` -- scale-out never fires
- TP exits (BL_TP_Bot/Mid) require ScaleOut_Size > 0 -- dead code
- SP module permanently disabled since v19.8 (all 5 variants FAILED)
- Fallback block requires `CurrentContracts < MaxContracts` -- impossible at 1 contract
- 88% of exits were SL/TimeExit, Trail only 12%, TP/SP/Fallback = 0%

## Performance baseline (before removal)

| Metric | 1 contract | 2 contracts |
|--------|-----------|-------------|
| Net Profit | +1,049,200 | +1,652,200 |
| PF | 1.553 | 1.425 |
| MDD | -336,200 (-22.1%) | -724,400 (-24.2%) |
| Sharpe | 0.207 | 0.178 |
| TP fires | 0 | 6 |
| P3b StopLoss | 0 | 7 |

Conclusion: 2 contracts doubled risk but only +57% net. Risk-adjusted
returns (PF, Sharpe, MDD%) all WORSE at 2 contracts.

---

## Removed inputs

```
{ [SEC-4] Scale-Out Settings }
ScaleOut_Percent(0.4),
```

```
{ [SEC-9] v19.8 Pre-Trail StopProfit (L1 SP philosophy, A/B engine).
          VERDICT 2026-06-13: All 5 SP variants (B/C/D/E/F)
          FAILED net-vs-baseline. Best variant D was -14 pct
          net + Top-10 retention only 50 pct. SP permanently
          disabled in production. Code preserved for
          archival/research only. See L5_v198_variant_results.md }
SP_Trigger_Pts(0),             { PERMANENT 0 = off. All A/B variants FAILED.
                                 B/C/D/E/F all killed 3 mega-winners
                                 (2026-04-07 +376K, 2026-03-31 +177K,
                                 2026-03-12 +131K) reducing them to +7~+38K. }
SP_Retain_Pct(50);             { inert while SP_Trigger_Pts = 0 }
```

## Removed variables

```
{ [SEC-4] Position sizing }
v_ScaleOut_Size(0),
```

```
{ [SEC-9] v19.8 Pre-Trail StopProfit }
v_Peak_Profit(0),              { close-based MFE in points }
v_SP_Armed(false),
v_SP_Floor(0),
```

## Removed code blocks

### 1. SP arming logic (inside `if MarketPosition = 1`)

```
{ v19.8: SP arming (permanently disabled, SP_Trigger_Pts=0) }
if Close - EntryPrice > v_Peak_Profit then
    v_Peak_Profit = Close - EntryPrice;
if SP_Trigger_Pts > 0 and v_Peak_Profit >= SP_Trigger_Pts then
    v_SP_Armed = true;
if v_SP_Armed then
    v_SP_Floor = EntryPrice +
        (v_Peak_Profit * (1 - SP_Retain_Pct / 100));
```

### 2. ScaleOut_Size calculation

```
v_ScaleOut_Size = Round(MaxContracts * ScaleOut_Percent, 0);
if MaxContracts > 1 and v_ScaleOut_Size = 0 then
    v_ScaleOut_Size = 1;
```

### 3. TP exits (inside Stage 1)

```
if v_ScaleOut_Size > 0 then begin
    Sell ("BL_TP_Bot") v_ScaleOut_Size contracts
        from Entry ("BL_Entry_Bot") next bar at v_Target_Bot Limit;
    Sell ("BL_TP_Mid") v_ScaleOut_Size contracts
        from Entry ("BL_Entry_Mid") next bar at v_Target_Mid Limit;
end;
```

### 4. SP branches in Stage 1 SL

Original (SP > SL priority):
```
if v_SP_Armed and v_SP_Floor > v_Bot_Base_Stop then
    Sell ("BL_SP_Bot") CurrentContracts contracts
        from Entry ("BL_Entry_Bot")
        next bar at v_SP_Floor Stop
else
    Sell ("BL_SL_Bot") CurrentContracts contracts
        from Entry ("BL_Entry_Bot")
        next bar at v_Bot_Base_Stop Stop;

if v_SP_Armed and v_SP_Floor > v_Mid_Base_Stop then
    Sell ("BL_SP_Mid") CurrentContracts contracts
        from Entry ("BL_Entry_Mid")
        next bar at v_SP_Floor Stop
else
    Sell ("BL_SL_Mid") CurrentContracts contracts
        from Entry ("BL_Entry_Mid")
        next bar at v_Mid_Base_Stop Stop;
```

Simplified to (direct SL only):
```
Sell ("BL_SL_Bot") CurrentContracts contracts
    from Entry ("BL_Entry_Bot")
    next bar at v_Bot_Base_Stop Stop;

Sell ("BL_SL_Mid") CurrentContracts contracts
    from Entry ("BL_Entry_Mid")
    next bar at v_Mid_Base_Stop Stop;
```

### 5. SP branch in Trail block (Trail > SP > BE priority)

Original:
```
{ Trail > SP > BE priority (highest stop wins for long) }
if v_Dynamic_Stop > MaxList(EntryPrice, v_SP_Floor) then begin
    Sell ("BL_Trail_Bot") ...
    Sell ("BL_Trail_Mid") ...
end else if v_SP_Armed and v_SP_Floor > EntryPrice then begin
    Sell ("BL_TrailSP_Bot") ...
    Sell ("BL_TrailSP_Mid") ...
end else begin
    Sell ("BL_TrailBE_Bot") ...
    Sell ("BL_TrailBE_Mid") ...
end;
```

Simplified to (Trail > BE only):
```
if v_Dynamic_Stop > EntryPrice then begin
    Sell ("BL_Trail_Bot") ...
    Sell ("BL_Trail_Mid") ...
end else begin
    Sell ("BL_TrailBE_Bot") ...
    Sell ("BL_TrailBE_Mid") ...
end;
```

### 6. Entire Fallback block

```
{ Fallback: inside consolidation, partial position, trail not yet active }
end else if CurrentContracts < MaxContracts then begin
    if v_SP_Armed and v_SP_Floor > EntryPrice then begin
        Sell ("BL_HoldSP_Bot") CurrentContracts contracts
            from Entry ("BL_Entry_Bot")
            next bar at v_SP_Floor Stop;
        Sell ("BL_HoldSP_Mid") CurrentContracts contracts
            from Entry ("BL_Entry_Mid")
            next bar at v_SP_Floor Stop;
    end else begin
        Sell ("BL_HoldBE_Bot") CurrentContracts contracts
            from Entry ("BL_Entry_Bot") next bar at EntryPrice Stop;
        Sell ("BL_HoldBE_Mid") CurrentContracts contracts
            from Entry ("BL_Entry_Mid") next bar at EntryPrice Stop;
    end;
end;
```

### 7. SP state reset

```
v_Peak_Profit         = 0;
v_SP_Armed            = false;
v_SP_Floor            = 0;
```

## Removed exit labels

| Label | Block | Purpose |
|-------|-------|---------|
| BL_TP_Bot | Stage 1 | Scale-out partial profit at target (Limit) |
| BL_TP_Mid | Stage 1 | Scale-out partial profit at target (Limit) |
| BL_SP_Bot | Stage 1 | StopProfit floor replaces SL when SP armed |
| BL_SP_Mid | Stage 1 | StopProfit floor replaces SL when SP armed |
| BL_TrailSP_Bot | Trail | SP floor in trail block (between Trail and BE) |
| BL_TrailSP_Mid | Trail | SP floor in trail block (between Trail and BE) |
| BL_HoldSP_Bot | Fallback | SP floor for partial position in consolidation |
| BL_HoldSP_Mid | Fallback | SP floor for partial position in consolidation |
| BL_HoldBE_Bot | Fallback | Breakeven floor for partial position |
| BL_HoldBE_Mid | Fallback | Breakeven floor for partial position |

---

## Restoration guide (for multi-contract scaling)

When scaling to 5+ contracts:

1. Re-add `ScaleOut_Percent` input (recommended: 0.4 = 40%)
2. Re-add `v_ScaleOut_Size` variable and calculation
3. Re-add TP exits in Stage 1 (`if v_ScaleOut_Size > 0`)
4. Re-add Fallback block for partial position state
5. Optionally re-evaluate SP module (was FAILED in v19.8 A/B)
6. Change Stage 1 condition back to `v_is_in_consolidation and CurrentContracts = MaxContracts`
7. Change Trail condition back to include `CurrentContracts < MaxContracts`
8. Re-run full GA optimization with new contract count

Minimum recommended contract count for scale-out: 5 contracts
(ScaleOut_Size = Round(5 * 0.4) = 2, keeping 3 for trail)

---

## v19.9 Cooldown-D mechanism (added in same version)

### Problem

182 trades, 39 clusters (102 trades = 56% of total).
27 losing clusters: 73 trades, net **-719,400 NTD** (38% of gross loss).

Worst example: T58-T63 at @20249 (2024-03-27~28)
- 6 entries at identical price in 2 days
- 5 losses, net -44,000
- Root cause: SL exit, Box unchanged, entry condition immediately re-satisfied

### Solution: Plan D (Same-box ban + New-box time delay)

| Rule | Trigger | Action |
|------|---------|--------|
| Same-box ban | `v_Box_Top = v_LastExit_BoxTop` | Block entry permanently until box changes |
| New-box delay | Different box but `BarNumber - v_LastExit_BarNum < Cooldown_Bars` | Wait N bars |

### Implementation

New input:
```
Cooldown_Bars(3)   { GA range: 1-10, step 1 }
```

New variables:
```
v_Cooldown_OK(true)       { computed each bar before entry check }
v_LastExit_BarNum(0)      { BarNumber at last exit }
v_LastExit_BoxTop(0)      { Box_Top of the box that generated last exit }
v_Entry_BoxTop(0)         { Box_Top captured on entry bar }
```

Entry gate:
```
v_Cooldown_OK = true;
if v_LastExit_BarNum > 0 then begin
    if v_Box_Top = v_LastExit_BoxTop then
        v_Cooldown_OK = false
    else if BarNumber - v_LastExit_BarNum < Cooldown_Bars then
        v_Cooldown_OK = false;
end;
```

Exit tracking (in MarketPosition = 0 reset):
```
if v_Highest_Since_Entry > 0 then begin
    v_LastExit_BarNum = BarNumber;
    v_LastExit_BoxTop = v_Entry_BoxTop;
end;
```

### Expected impact

- Same-box clusters (e.g., T58-T63) fully eliminated
- New-box whipsaw reduced by Cooldown_Bars delay
- Estimated gross loss reduction: 400K-600K NTD
- PF improvement: 1.55 -> estimated 1.8-2.0+
- Requires GA optimization of Cooldown_Bars after deployment
