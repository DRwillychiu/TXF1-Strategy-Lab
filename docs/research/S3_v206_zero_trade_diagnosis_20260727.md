# S3 v2.0.6 Zero-Trade Diagnosis (2026-07-27)

> **Strategy**: S3_RapidPullbackShort v2.0.6
> **Symptom**: 6/8 ~ 7/27 (49 calendar days, ~35 trading days) zero trades
> **Prior trade frequency**: 17 trades in backtest (2020-12 ~ 2026-06), 89% concentrated in 2026 H1
> **Diagnosis**: v2.0.4 parameter lock-in re-introduced the exact restrictiveness v2.0 was designed to fix

---

## 1. Root Cause: Overfitting Cycle

| Version | RSI Threshold | Timeframe | Trades/yr | Outcome |
|---------|-------------|-----------|-----------|---------|
| v1.1 | 70 | Daily | 9 | PF net = -0.92 (too few trades) |
| v2.0 original | **65** | 60M | 25-50 (target) | Intentional loosening |
| v2.0.4 lock-in | **70** | 60M | 17 total (backtest) | Re-tightened based on 17-trade sample |
| v2.0.6 live | 70 | 60M | **0 since 6/8** | Same problem as v1.1 |

### The contradiction

The v2.0 annotated design spec explicitly states:

> "60M scale RSI is more volatile; a threshold of 70 would be too strict"
> -- S3_RapidPullbackShort_annotated.md, line 78

Yet v2.0.4 locked the threshold back to 70, based on a 17-trade backtest
where 89% of trades came from the 2026 H1 strong rally period.

**When the rally cooled after 6/8, the regime gate shut completely.**

---

## 2. Gate-by-Gate Blockage Analysis

### Regime Gate: A AND (B OR C)

| Gate | Condition | Post-6/8 likelihood | Verdict |
|------|-----------|---------------------|---------|
| A: Trend OK | 60M MA20 > MA60 | Likely PASS in normal bull | OK |
| **B: RSI sustained** | **RSI(14,60M) > 70 for 2 consecutive hours** | **Very rare outside rally** | **PRIMARY BLOCKER** |
| C: Dist OK | Price > 1.5% above 60M MA20 | Uncommon in normal market | SECONDARY BLOCKER |
| Secular Bull | Daily Close>MA60 AND Close>MA200 AND MA60>MA200 | Likely PASS (TW in bull structure) | OK |

**Path B requires extreme overbought conditions sustained for 2 full 60M bars.**
In non-rally market, 60M RSI rarely crosses 70, let alone holds it for 2 hours.

**Path C (alternative) also requires significant overextension** -- 1.5% above
the 20-hour moving average is not trivial in a normal trending market.

Both paths blocked = regime gate never fires.

### Additional restrictiveness from v2.0.4

| Parameter | v2.0 original | v2.0.4 locked | Direction | Impact |
|-----------|--------------|---------------|-----------|--------|
| H60_RSI_Threshold | 65 | **70** | Tighter | 60M RSI>70 sustained 2hr = extreme rarity |
| Pullback_Min_Pct | 0.3% | **0.5%** | Tighter | Needs bigger pullback, but strong rally = small pullbacks |
| Entry_Cutoff_Time | 1325 | **1230** | Tighter | Lost 55 minutes of scanning window |
| ATR_Spike_Mult | 1.3 | 1.0 | Looser | M3 easier (positive, but irrelevant if regime blocks) |

**Triple tightening**: RSI + Pullback + Time window all moved restrictive.
Even if regime fires, the remaining gates further reduce the probability.

---

## 3. The Fundamental Tension

S3's thesis is "counter-trend short during overheated bull pullback."
This creates an inherent contradiction in the signal chain:

1. **Regime requires EXTREME bullishness** (RSI > 70 for 2 hours)
2. **Trigger requires a PULLBACK** (3 red candles, 0.5-1.5% drop, below EMA5)
3. These are statistically anti-correlated: when market is extremely overbought,
   pullbacks are less frequent and smaller in magnitude

The v2.0 original design (RSI > 65) balanced this tension better.
The v2.0.4 lock-in (RSI > 70) pushed the regime requirement so high that
the pullback probability within that regime drops to near-zero.

---

## 4. Full Code Audit Results (20 items)

Performed a line-by-line mathematical audit of all calculations:

| Category | Items | Result |
|----------|-------|--------|
| Section 2: 60M Tier 1 (MA/RSI/Dist/Regime) | 5 | All correct |
| Section 2b: Secular Bull Filter (Daily) | 2 | All correct |
| Section 3: 5M Tier 2 (M1-M4 momentum) | 5 | All correct |
| Section 4: RSI Snapshot + Cooldown | 3 | All correct |
| Section 5: Stop Guard (Rule #12) | 4 | 3 correct, 1 gap |
| Section 7: Exit Chain (TP/SL math) | 4 | 3 correct, 1 design note |

### Confirmed correct (17/20)

- All mathematical formulas (distances, percentages, levels) correct for SHORT
- Data binding: `(... of Data2/Data3)[1]` explicit parens idiom consistent
- RSI snapshot boundary detection via Data2 own timestamp tuple
- Frozen SL direction: `EntryPrice + ATR*mult` (above entry for short)
- TP direction: `EntryPrice * (1 - TP_Pct/100)` (below entry for short)
- EMA20 backup TP: cross-from-above detection with 3 guards
- v2.0.6 CB-1/CB-2 fixes properly implemented
- Cooldown reset gated by Entry_Open_Time (night session safe)
- Exit chain priority order correct
- SetStopLoss guard `MP >= 0` correct per Rule #12 short variant
  (cross-verified against S1/S3_L/S3_S/S16_S -- all consistent)

### Functional gap (1/20)

- **SL_Pct = 0 (disabled)**: Rule #12 three-component architecture is in place
  but the percentage ceiling has not been activated. Needs MC sweep 0.00-5.00
  step 0.25 to find convergence value. ATR can spike in extreme vol with no cap.

### Design notes (2/20)

- `MP >= 0` engine stop guard: correct per Rule #12, but means engine stop
  is NOT updated during trade (relies on pre-entry frozen value). By design.
- `Time <= 1345` hardcoded in DaySess_High tracking: functionally correct
  (Entry_Cutoff=1230 is well before), but not parameterized.

---

## 5. Possible Remediation Paths

### Path A: Revert to v2.0 original design intent

Restore the parameters that v2.0 explicitly loosened:
- H60_RSI_Threshold: 70 -> 65
- Pullback_Min_Pct: 0.5 -> 0.3
- Entry_Cutoff_Time: 1230 -> 1325

**Rationale**: The annotated design doc already established that these values
are the correct calibration for 60M timeframe. The v2.0.4 lock-in was based
on a biased sample (17 trades, 89% from one regime period).

### Path B: Add diagnostic Print to confirm bottleneck

Before changing parameters, add Section 9 diagnostics to log regime gate
status daily. Run MC12 for 1-2 weeks to confirm which gate is blocking:

```
Print("S3v2 DIAG ", Date:8:0, " T=", Time:4:0,
      " regime=", v_Regime_Watch,
      " trendOK=", v_Trend_OK,
      " rsiOK=", v_RSI_OK, " snap0=", v_H60_RSI_Snap0:0:1,
      " distOK=", v_Dist_OK, " dist=", v_H60_Dist_Pct:0:2,
      " secular=", v_Secular_Bull_OK,
      " trigger=", v_Trigger_Fired);
```

### Path C: Structural redesign

If the thesis itself is too restrictive (overheated bull + pullback = rare),
consider whether S3 should move to a different trigger mechanism or thesis.

---

## 6. Recommendation

**Path A is the strongest move.** The v2.0 design rationale was sound and
well-documented. The v2.0.4 lock-in was a classic overfitting error:
optimizing to a 17-trade sample dominated by one market regime.

The 17-trade backtest PF of 9.43 was likely an artifact of the 2026 H1
concentration, not a generalizable signal. Reverting to the v2.0 defaults
trades some backtest PF for survivability across market regimes.

---

## Appendix: Version History Reference

| Version | Date | Key Change |
|---------|------|------------|
| v1.1 | pre-2026-06 | Daily regime, 9 trades/yr |
| v2.0 | 2026-06-20 | 60M regime, RSI 65, Pullback 0.3 |
| v2.0.1 | 2026-06-20 | MC12 Data2 binding fix |
| v2.0.2 | 2026-06-20 | Secular Bull Filter (60M, retired) |
| v2.0.3 | 2026-06-20 | Secular Bull Filter (Daily Data3) |
| v2.0.4 | 2026-06-20 | USER-MANDATED parameter lock-in (17 trades) |
| v2.0.5 | 2026-07-26 | SetStopContract + SL_Pct architecture |
| v2.0.6 | 2026-07-27 | CB-1 Kill Switch gate + CB-2 cooldown fix |
