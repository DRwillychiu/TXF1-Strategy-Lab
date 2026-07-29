# S16_S v1.7.1 Exit Mechanism Full Audit (2026-07-29)

## Scope
782-line code audit of S16_S_MACrossShort_v1.7.1.pla covering all 9 exit
signals, SL calculation, re-entry mechanism, and state management.

## Finding Groups

### Group A: ATR Inflation Cascade (HIGH RISK)

Root cause: Three mechanisms use UNFROZEN v_ATR. After a trade exits
(especially via stop loss), the exit event's price volatility inflates ATR.
If re-entry fires within a few bars, all three mechanisms inherit the
inflated ATR, simultaneously weakening the defense:

**A1: Initial SL Widened (:523 v_SL_Level)**
- Status: OPEN
- SL = EntryPrice + v_ATR * StopATRMult, capped by SL_Pct=1.0%
- Normal ATR=56: SL=224 pts. Inflated ATR=120: SL=400 pts (capped). Ratio 1.78x.
- Impact: Re-entry max loss up to 178% of main entry max loss.

**A2: BE Trailing Activation Delayed (:728-733 unfrozen v_ATR)**
- Status: OPEN
- BE Tier1 threshold = 2.5 * v_ATR, Tier2 = 3.5 * v_ATR
- Normal: 140/196 pts profit needed. Inflated: 300/420 pts. Ratio 2.14x.
- Impact: Breakeven protection effectively disabled for re-entry trades.

**A3: Multi-Layer Activation Delayed (:675 v_StopDist unfrozen)**
- Status: OPEN
- ML activation = v_StopDist * 20% = v_ATR * StopATRMult * 20%
- Normal: 44.8 pts loss. Inflated: 96.0 pts. Ratio 2.14x.
- Impact: Second-line defense delayed when losses accelerate fastest.

### Group B: Re-Entry Chain (MEDIUM RISK)

**B1: Unbounded Re-Entry Chain (:480-483 / :512)**
- Status: OPEN
- Exit from re-entry re-arms at re-entry's EntryPrice (updated at :512).
- No max count. Bearish structure gates (ZLEMA + MinSlope) are the only
  control. In a persistent bearish trend with repeated washouts, multiple
  re-entries accumulate losses with progressively inflated ATR.

### Group C: Unaffected Mechanisms (SAFE)

| Mechanism | Basis | Re-Entry Behavior |
|-----------|-------|-------------------|
| P1a QuickStop Loss | EntryPrice * QS% | Normal (percentage, no ATR) |
| P1b QuickStop Time | Bar count + price | Normal (fresh v_EntryBar) |
| P4 GoldenCross | ZLEMA cross | Normal (pure signal) |
| P5 TimeStop | Bar count | Normal (fresh 24-bar count) |
| P0.5 TailFlat | Time window | Normal (pure time gate) |

### Group D: Low Risk / Cosmetic

**D1: Dead variable v_ML_Loss (:333)**
- Status: OPEN (LOW)
- Declared but never used. ML uses v_Loss instead.

**D2: v_ReEntry_Armed not reset on fill (:523)**
- Status: OPEN (LOW)
- Functionally safe (entry block requires MP=0). Semantically unclean.

**D3: SL_Pct dual-track calculation (:518 vs :546)**
- Status: KNOWN DESIGN (v1.5)
- Frozen SL uses EntryPrice; engine guard uses Close. Intentional.

**D4: v_BE_Stop_Tier1/Tier2 unnecessary persistent (:354-355)**
- Status: OPEN (LOW)
- Recomputed every bar. Could be local. No functional impact.

## Resolution Priority

1. A1 (SL widened) — must fix before live_simulation
2. B1 (chain limit) — must fix before live_simulation
3. A2 + A3 (BE + ML delayed) — should fix, same root cause as A1
4. D1-D4 (cosmetic) — defer to next version cleanup

## Solution Options for A1 (Re-Entry SL)

Five approaches analyzed, from conservative to radical:

### Option 1: Inherit Original Frozen ATR (Conservative)
- New variable v_Original_Frozen_ATR, saved at main entry, used at re-entry.
- Re-entry SL = EntryPrice + v_Original_Frozen_ATR * StopATRMult, cap SL_Pct.
- Solves: A1 + A2 + A3 (if BE/ML also use frozen ATR).
- Does NOT solve: B1 (chain limit).
- New params: 0. Code change: small (1 var, SL setup branch).

### Option 2: Cap Re-Entry SL at Main Entry SL Distance (Pragmatic)
- New variable v_Original_SL_Dist, saved at main entry.
- Re-entry SL = MinList(normal ATR calc, v_Original_SL_Dist), cap SL_Pct.
- Allows tighter SL if ATR drops, caps if ATR inflates.
- Solves: A1 only. Does NOT solve: A2, A3, B1.
- New params: 0. Code change: small (1 var, 1 MinList).

### Option 3: Separate Re-Entry ATR Multiplier (Neutral)
- New input ReEntry_StopATRMult (e.g. 2.0 vs main 4.0).
- Re-entry SL = EntryPrice + v_ATR * ReEntry_StopATRMult, cap SL_Pct.
- Lower multiplier offsets ATR inflation. If ATR doubles, 2.0*2 = 4.0.
- Solves: A1 only. Does NOT solve: A2, A3, B1.
- New params: 1 (needs optimization). Code change: small.

### Option 4: Pure Percentage SL for Re-Entry (Aggressive)
- New input ReEntry_SL_Pct (e.g. 0.50%).
- Re-entry SL = EntryPrice * (1 + ReEntry_SL_Pct / 100). No ATR involved.
- Completely immune to ATR inflation. Cross-era consistent.
- Solves: A1 only. Does NOT solve: A2, A3, B1.
- New params: 1. Code change: medium (SL setup forks).

### Option 5: Redesign Re-Entry Exit Framework (Radical / Out-of-Box)
- Re-entry thesis: "washout over, trend resumes." If correct, should profit
  fast. If wrong, exit fast. Does NOT need main entry's 24-bar hold / wide SL.
- Design: Re-entry gets fully independent exit path:
  - QuickStop: unchanged (already percentage-based, ATR-immune)
  - Initial SL: fixed percentage (e.g. 0.5%), no ATR
  - Multi-Layer: disabled (QS covers this role)
  - BE Trailing: fixed percentage thresholds, no ATR
  - TimeStop: 12 bars (not 24 — thesis must play out faster)
  - Chain limit: max 1 re-entry per death cross signal
- Solves: A1 + A2 + A3 + B1 (all four issues at once).
- New params: 3-4. Code change: large (v_IsReEntry flag + exit path fork).
- Aligns with user's stated goal: "re-entry should match manual trading logic."

### Comparison Matrix

| Option | A1 SL | A2 BE | A3 ML | B1 Chain | New Params | Change Size |
|--------|-------|-------|-------|----------|------------|-------------|
| 1. Inherit Frozen ATR | YES | YES | YES | no  | 0 | small  |
| 2. Cap SL Distance    | YES | no  | no  | no  | 0 | small  |
| 3. Separate Multiplier | YES | no  | no  | no  | 1 | small  |
| 4. Pure Percentage SL  | YES | no  | no  | no  | 1 | medium |
| 5. Redesign Framework   | YES | YES | YES | YES | 3-4 | large |

### Key Insight

Options 1-4 are "patches" — they fix A1 but leave A2/A3/B1 for separate work.
Option 5 is a "redesign" — it reframes re-entry as a "verification trade"
(fast-in, fast-out) rather than a "second main entry." This eliminates the
ATR dependency entirely because re-entry no longer uses ATR for any purpose.

The fundamental question: in manual trading, after a washout stop, would you
re-enter with the same 24-bar hold and wider stop, or with a tighter stop
and faster exit?

## Resolution Log

### 2026-07-29: v1.8.0-v1.8.4 created for A/B testing
- 5 .pla files generated from v1.7.1 base (QS_MaxLoss_Pct default updated to 0.25)
- All variants add v_IsReEntry flag to distinguish main vs re-entry trades
- v1.8.0 (802 lines): Inherit original frozen ATR - solves A1+A2+A3
- v1.8.1 (798 lines): Cap SL at original distance - solves A1
- v1.8.2 (799 lines): Separate ReEntry_StopATRMult=2.0 - solves A1
- v1.8.3 (803 lines): Pure ReEntry_SL_Pct=0.50% - solves A1
- v1.8.4 (838 lines): Full redesign (SL/BE/ML/TimeStop/chain) - solves A1+A2+A3+B1
- All 5 files pass ASCII verification (Rule #15)
- Next: MC12 compile + backtest on desktop, compare vs v1.6.2 and v1.7.1

### 2026-07-29: Audit completed, options documented
- 782-line full code audit completed
- 7 findings categorized (A1-A3, B1, D1-D4)
- 5 solution options for A1 analyzed and documented
- Priority: A group first, D group deferred
