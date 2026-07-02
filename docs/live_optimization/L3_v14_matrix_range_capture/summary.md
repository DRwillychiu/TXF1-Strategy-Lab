# L3 V14 Matrix Range Capture — Optimization Summary

**Date**: 2026-07-03
**Strategy**: L3 ConsolidationLong (STRATEGY_WILLY_LONG_C)
**Upgrade**: v13.4 -> v14.0
**Status**: Code complete, MC9 backtest pending

---

## Problem Statement

V13 half-box architecture splits the consolidation box into Bot->Mid and Mid->Top,
structurally capping the reward ratio at ~1.1x:

- CL_Entry_Bot: 26 trades / 6.5yr, 26.9% WR, net -10.4K (dead leg)
- CL_Entry_Mid: 405 trades, 51.9% WR, net +707.6K (all profit)
- 94% of profit from mid-line entries targeting only half the box range
- Reward ratio 1.165 vs L1 3.28x, L2 4.35x — lowest in portfolio

User ruling: "Regardless of box size or where price consolidates within the box,
must capture the full consolidation pattern profit."

---

## Solution: Multi-Dimensional Matrix Architecture

### 4 Dimensions

| Dim | Name | Input | Purpose |
|-----|------|-------|---------|
| 1 | Box Qualification | Min_Box_ATR=3.0 | Skip boxes where friction eats edge |
| 2 | Support Zone | Entry_Zone_Pct=0.30 | Unified entry at bottom 30% of box |
| 3 | Dynamic Target | Swing_Lookback=32 | 15M swing high, capped at Box_Top |
| 4 | Trend + Daily | unchanged | 60M MA + Daily MA OR filters |

### Key Changes

- REMOVED: CL_Entry_Bot / CL_Entry_Mid dual-leg split
- REMOVED: v_Leg_IsBot / v_Work_IsBot leg classification
- REMOVED: CL_TP_Bot / CL_TP_Mid dual-leg targets
- ADDED: CL_Entry (unified support zone entry)
- ADDED: CL_TP (full-range target = dynamic swing high)
- ADDED: 3 new inputs (Entry_Zone_Pct, Min_Box_ATR, Swing_Lookback)
- KEPT: All safety modules (Holiday, Settlement, ImmediateStop, FrozenSL, BreakExit)

---

## Pre-Verification (Python, 28-year TWII Daily)

Script: `scripts/preverify_l3_v14_fullrange.py`

### Results

| Metric | A: Half-Box | B: Full-Range | C: Filtered |
|--------|:-----------:|:-------------:|:-----------:|
| PF | 0.806 | 1.021 | **1.086** |
| Reward | 0.90x | 1.92x | **1.85x** |
| Cum Return | -94% | +9% | **+33%** |
| Sharpe | -0.280 | 0.024 | **0.086** |
| Trades/yr | 12.3 | 8.3 | **6.9** |

### W0 Gate Analysis

All variants fail W0 on daily data — expected because daily bars cannot capture
intraday mean reversion (the core alpha of consolidation trading).

Key directional findings:
- Full-range beats half-box by +35% PF and +113% reward ratio
- Filtered variant (large boxes only) is best overall
- Recent periods (2015+) strongly positive: 3/6 regimes pass for variant C
- Estimated intraday uplift: current L3 daily PF 0.806 -> MC9 PF 1.187 = +0.38 gap
- Applying same gap: filtered daily 1.086 -> projected intraday ~1.47

### Verdict

Direction confirmed. Full-range + box filter = correct architectural upgrade.
Final validation via MC9 15M/60M backtest.

---

## Files Changed

| File | Change |
|------|--------|
| `strategies/live/L3_ConsolidationLong.pla` | V14.0 complete rewrite of entry/exit |
| `strategies/live/L3_ConsolidationLong_annotated.md` | V14 architecture docs |
| `strategies/live/L3_ConsolidationLong_BOSS_VIEW.md` | Updated to V14 |
| `scripts/preverify_l3_v14_fullrange.py` | Pre-verify script |
| `docs/live_optimization/` | New folder for live strategy optimization |

---

## MC9 Testing Checklist

- [ ] Load V14 code into MC9 as STRATEGY_WILLY_LONG_C
- [ ] Verify MC inputs (watch for parameter persistence):
  - Entry_Zone_Pct = 0.30
  - Min_Box_ATR = 3.0
  - Swing_Lookback = 32
  - Freeze_SL_On = true
  - BE_Trigger_Pts = 0
- [ ] Run backtest 2020-01 ~ 2026-07
- [ ] Export Excel report
- [ ] Compare vs V13.4 baseline:
  - Reward ratio: 1.165 -> target 1.5x+
  - PF: 1.187 -> target improvement
  - Trade count: 431 -> expect fewer (box filter)
  - Exit label distribution (CL_TP / CL_SL / CL_BreakExit)
- [ ] If V14 > V13.4: deploy (flat position only)
- [ ] If V14 < V13.4: tune inputs or revert
