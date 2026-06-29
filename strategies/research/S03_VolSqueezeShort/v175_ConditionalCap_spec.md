# S3_S v1.7.5 — Conditional Hard Cap Deep Design Spec

**Date**: 2026-06-29
**Status**: DESIGN PHASE (Rule #16: no code until spec approved)
**Base**: v1.7.3-FINAL (live_simulation production)
**Philosophy**: small loss + small gain + big gain; loss control IS the strategy

---

## Engineering System Checklist (Rule #16)

### Rules
- [x] R-SL1: Single trade risk target = -2% account (100 pts base)
- [x] R-SL2: Hard Cap >= SP arm distance (1.5 ATR). **THIS IS THE CORE DESIGN CONSTRAINT**
- [x] R-SL3: SP/TP count shift must be <= 20% vs v1.7.3 baseline
- [x] R-SL4: Affects Layer 1 (Hard Cap) only. Layer 2-5 untouched
- [x] R-D2: Must not cut alpha source (v1.7.4 cap100 violated this)
- [x] R-D4: Must not reduce sample below 100 trades (N/A, SL cap does not filter entries)
- [x] Rule #11-15: All pass (no structural change to compliance modules)

### Context Loaded
- Production: v1.7.3-FINAL in live_simulation/ (29 trades, PF 3.95, MDD -22.1%)
- Last FAIL: v1.7.4 cap100 (-26% Net, 8 SP->SL conversions, -432K)
- Lessons: L24 (alpha preservation), L26 candidate (cap >= SP arm)
- Cross-strategy: L2/L4/S3 same SL architecture, pending rollout after S3_S verify
- Data: ATR(14) 60M median ~60 pts, vol expansion ~193 pts (6/9 case)

### Verification Plan
- V1: Control Group (v1.7.3 baseline vs cap 150/200/250/Conditional)
- V2: Exit Distribution (SP count must stay >= 17 out of 21 baseline)
- V3: Year Stability (no single year > 50% drop)
- V4: WFA 9-window (if structural, >= 4/9)
- V5: Deferred (only if V1-V4 all pass and promoting)

### Memory Check
- AP-1 (protection cuts alpha): v1.7.4 cap100 exactly this. Conditional design avoids it
- AP-6 (cap < SP arm): root cause of cap100 failure. Conditional cap by definition >= SP arm
- PP-1 (Frozen ATR): preserved, Conditional cap adds floor not replaces
- PP-4 (5-layer): adding Layer 1 to complete the architecture

### Format
- Output: 4 backtest xlsx + comparison .md
- Handoff: 7-section standard to desktop

---

## 1. The Problem (Why)

### v1.7.3-FINAL SL distribution

| Case | ATR(14) | SL Distance (2.75 ATR) | SL Amount | Account % | Verdict |
|------|---------|----------------------|-----------|-----------|---------|
| Normal vol | ~60 pts | 165 pts | -33K | -3.3% | Acceptable |
| Medium vol | ~80 pts | 220 pts | -44K | -4.4% | Borderline |
| High vol | ~120 pts | 330 pts | -66K | -6.6% | Too high |
| **6/9 case** | **~193 pts** | **530 pts** | **-106K** | **-10.6%** | **Unacceptable** |
| Extreme | ~250 pts | 690 pts | -138K | -13.8% | Catastrophic |

**Core issue**: ATR-based SL is vol-adaptive but has no ceiling. Vol expansion entries (which is exactly when S3_S enters -- BBW squeeze breakdown) produce the widest SL at the worst time.

### Why cap100 failed

```
SP arm condition: peak profit >= SP_Trigger_ATRMult * ATR = 1.5 * ATR
                  At ATR 193: SP arm distance = 290 pts
                  
Cap 100 < 290 --> SP cannot arm before cap triggers
                  8 trades SP->SL conversion = -432K alpha destruction
```

**Root cause**: Fixed cap ignores the relationship between cap and SP arm distance.

---

## 2. The Solution (What)

### v1.7.5 Conditional Hard Cap

**One sentence**: SL = min(ATR-based, max(hard floor, SP arm distance))

```
v_Frozen_SL_Dist = MinList(
    v_Frozen_ATR * StopATRMult,                                    { Layer 2: ATR ceiling }
    MaxList(
        SL_Hard_Cap_Pts,                                           { Layer 1: hard floor (100 pts) }
        v_Frozen_ATR * SP_Trigger_ATRMult + SL_Cap_SP_Buffer_Pts   { SP arm + buffer }
    )
);
```

### New inputs (2 new, total change = 2 inputs + 1 line)

| Input | Default | Purpose |
|-------|---------|---------|
| `SL_Hard_Cap_Pts` | 100 | Absolute floor = -2% account |
| `SL_Cap_SP_Buffer_Pts` | 15 | Buffer above SP arm to prevent noise triggering |

### How it works by vol regime

| Vol | ATR | ATR SL (2.75x) | SP arm (1.5x) | SP arm+buf | MaxList | **Final SL** | vs v1.7.3 |
|-----|-----|----------------|---------------|------------|---------|-------------|-----------|
| Low | 30 | 83 | 45 | 60 | 100 (floor) | **83** (ATR < floor, no cap) | = |
| Normal | 60 | 165 | 90 | 105 | 105 | **105** | -60 pts saved |
| Medium | 80 | 220 | 120 | 135 | 135 | **135** | -85 pts saved |
| High | 120 | 330 | 180 | 195 | 195 | **195** | -135 pts saved |
| **6/9** | **193** | **530** | **290** | **305** | **305** | **305** | **-225 pts saved** |
| Extreme | 250 | 690 | 375 | 390 | 390 | **390** | -300 pts saved |

**Key insight**: At every vol level, Final SL > SP arm distance, so SP mechanism never fails.

### SP preservation proof

```
Final SL = MinList(ATR_SL, MaxList(floor, SP_arm + buffer))

Case 1: ATR_SL <= SP_arm + buffer
  --> Final SL = ATR_SL (ATR-based, same as v1.7.3, no cap active)
  --> SP arm < ATR_SL, SP works normally

Case 2: ATR_SL > SP_arm + buffer and ATR_SL > floor
  --> Final SL = max(floor, SP_arm + buffer)
  --> If SP_arm + buffer > floor: Final SL = SP_arm + buffer > SP_arm. SP safe.
  --> If floor > SP_arm + buffer: Final SL = floor. Only when vol so low that SP arm < 100.
      At ATR < 57 pts (SP arm = 85 pts < 100), floor dominates.
      But ATR < 57 means ATR_SL = 157, and floor = 100, so MinList picks floor = 100 > SP arm 85. SP safe.

All cases: Final SL >= SP arm distance. QED.
```

---

## 3. Effect Analysis

### Expected impact (projection from v1.7.3 data)

| Metric | v1.7.3-FINAL | v1.7.4 cap100 | **v1.7.5 conditional (est.)** |
|--------|-------------|---------------|-------------------------------|
| Net Profit | +1,013K | +750K (-26%) | **+1,050~1,150K (+4~14%)** |
| PF gross | 3.95 | 3.26 | **4.0~4.5** |
| MDD % | -22.1% | -13.1% | **-15~18%** |
| WR | 82.8% | 56.3% | **80~83%** |
| SL trades | 3 | 13 | **3~5** |
| SP trades | 21 | 13 | **19~21** |
| Avg SL | -106K | -25K | **-40~60K** |
| Max SL | -106K | -45K | **-60~80K** |

### Why conditional outperforms fixed cap
- **Normal vol** (60 ATR): SL caps at 105 instead of 165 (-60 pts saved per SL)
- **6/9 case** (193 ATR): SL caps at 305 instead of 530 (-225 pts saved)
- But SP still arms because cap > SP arm distance at every vol level
- Net effect: save SL loss without converting SP to SL

---

## 4. Caveats (honest)

### Caveat 1: 6/9 case SL still -61K (-6.1% account)
- 305 pts * 200 NTD = -61K. Better than -106K but not "small loss"
- Pure 2% cap at 100 pts would be -20K but kills SP
- **This is the explicit tradeoff**: preserve SP mechanism at cost of larger single SL

### Caveat 2: Conditional logic adds 1 input complexity
- `SL_Cap_SP_Buffer_Pts` adds optimization surface
- Mitigation: fixed at 15 pts (1 tick above SP arm), not optimized

### Caveat 3: Still vulnerable to gap-through
- SL at 305 pts can gap through in overnight session
- Mitigation: SetStopLoss MC engine guard already handles this (Section 9)

### Caveat 4: Cross-strategy rollout scope
- If v1.7.5 works, must audit L2/L4/S3 for same pattern
- Each has different SP parameters -> conditional formula adapts automatically

---

## 5. Backtest Plan (V1-V3)

### 5 groups (including v1.7.4 cap100 already done)

| Group | SL_Hard_Cap_Pts | SL_Cap_SP_Buffer | Logic | Purpose |
|-------|----------------|-----------------|-------|---------|
| **Baseline** | 9999 | 0 | = v1.7.3 | Control |
| **A** (done) | 100 | N/A (fixed) | v1.7.4 cap100 | Already have data |
| **D** | 150 | N/A (fixed) | Fixed 150 | Intermediate check |
| **E** | 200 | N/A (fixed) | Fixed 200 | Intermediate check |
| **G** | 100 | 15 | **Conditional** | Main test |

### Required metrics per group
- Net Profit / PF gross / PF adj / MDD% / Sharpe / Sortino / WR
- Exit distribution: SP/SL/TP/Mid/TimeStop count + avg PnL
- Year-by-year PnL
- Top-5 worst trades (SL detail)
- SP arm rate (what % of trades arm SP)

### V2 Red Flag check
- If Group G SP trades < 17 (vs 21 baseline) --> R-SL3 violation, KILL
- If Group G single year PnL drop > 50% vs baseline --> V3 fail, investigate

### Decision matrix

| Result | Action |
|--------|--------|
| G Net > baseline + MDD improved | Promote v1.7.5 (after W4) |
| G Net = baseline + MDD improved | Promote v1.7.5 (after W4) |
| G Net < baseline but MDD improved > 5pp | User decides tradeoff |
| G SP < 17 | KILL v1.7.5, stay v1.7.3 |
| G MDD not improved | KILL v1.7.5, stay v1.7.3 |

---

## 6. MC12 Implementation (deferred until spec approved)

### Changes to .pla (3 lines total)

**Section 1 inputs**: +2 inputs
```pla
SL_Hard_Cap_Pts           ( 100   ),   { v1.7.5: hard floor pts; 100 pts = -20K = -2pct account }
SL_Cap_SP_Buffer_Pts      ( 15    ),   { v1.7.5: buffer above SP arm to prevent noise }
```

**Section 9 Frozen SL**: 1 line change
```pla
{ v1.7.3 (current production): }
v_Frozen_SL_Dist = v_Frozen_ATR * StopATRMult;

{ v1.7.5 (conditional cap): }
v_Frozen_SL_Dist = MinList(
    v_Frozen_ATR * StopATRMult,
    MaxList( SL_Hard_Cap_Pts, v_Frozen_ATR * SP_Trigger_ATRMult + SL_Cap_SP_Buffer_Pts )
);
```

### What does NOT change
- All 22 existing inputs (values unchanged)
- Section 1-8, 10-13 (no structural change)
- Exit priority chain (Layer 0-5 intact)
- SP mechanism (arm / retain / floor untouched)
- All P0 safety modules (Settlement / Holiday / Kill / Registry)

---

## 7. Cross-Strategy Audit (post-verify rollout plan)

| Strategy | Direction | Current SL | SP arm | Conditional Cap applicable? |
|----------|-----------|-----------|--------|---------------------------|
| **S3_S** | Short | 2.75 ATR | 1.5 ATR | **Yes (this spec)** |
| L2 TrendShort | Short | ATR-based | Has SP | Yes (after S3_S verify) |
| L4 ConsolidationShort | Short | ATR-based | No SP (disabled) | Simpler: fixed cap only |
| S3 RapidPullbackShort | Short | ATR-based | Has SP | Yes (same formula) |
| L1/L3/L5 | Long | ATR-based | L1 has SP | Lower priority (long less vulnerable) |

---

## 8. Related Files

| File | Purpose |
|------|---------|
| `S3_S_VolSqueezeShort.pla` (live_sim) | Production v1.7.3-FINAL |
| `S3_VolSqueezeShort_v174_EXPERIMENTAL.pla` | v1.7.4 cap100 (reference only) |
| `v174_HardSLCap_spec.md` | v1.7.4 original spec |
| `v174_cap100_result_20260628.md` | v1.7.4 cap100 backtest result |
| `stop_loss_mechanisms_catalog_20260628.md` | Industry 12-mechanism reference |
| `ENGINEERING_SYSTEM.md` | Rule #16 5-pillar framework |
