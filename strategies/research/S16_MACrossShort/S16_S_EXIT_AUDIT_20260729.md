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

## Resolution Log

(To be updated as fixes are implemented)
