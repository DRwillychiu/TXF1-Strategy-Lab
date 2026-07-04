# L4 V15.0 Matrix Range Capture (Short) — Optimization Summary

**Date**: 2026-07-04
**Strategy**: L4 ConsolidationShort (STRATEGY_WILLY_SHORT_CTEST2)
**Upgrade**: v14.4 Spring Trap -> v15.0 Matrix Range Capture
**Status**: PENDING MC9 BACKTEST

---

## Problem Statement

V14.x Spring Trap architecture had a structural CS_BreakExit bleed that could not be fixed:

- CS_BreakExit: 28 trades, 0% WR, -378K to -545K (= total net profit lost)
- 7 A/B variants tested (A-G), only Night Block (Path A) helped
- v14.5 filter attempts (Strong Long Block + Fast BreakExit) both failed and rolled back
- Only 84 trades in 6.4 years, Sharpe 0.058 (portfolio weakest)

User ruling (2026-07-04): "Consolidation earns oscillation money.
L3 buys at support zone, L4 shorts at resistance zone."

---

## Solution: Mirror L3 V14 Matrix Architecture for Shorts

### 4 Dimensions (V15.0 Initial Values)

| Dim | Name | Input | Value | Purpose |
|-----|------|-------|-------|---------|
| 1 | Box Qualification | Min_Box_ATR | 8.5 | Only trade significant boxes |
| 2 | Resistance Zone | Entry_Zone_Pct | 0.50 | Short at top 50% of box |
| 3 | Dynamic Target | Swing_Lookback | 80 | 15M swing low ~20hr lookback |
| 4 | Trend + Daily | unchanged | — | 60M MA + Daily Macro Block |

### Key Architecture Changes (v14.4 -> v15.0)

| Removed | Added |
|---------|-------|
| Spring Trap detection | Resistance zone entry |
| Trailing stop (Trail_ATR_Mult) | Dynamic swing low target (CS_TP) |
| Time stop (Time_Stop_Bars) | Frozen target at entry |
| BE/SP mechanism (rejected) | Box qualification filter |
| Night block (trap-specific) | Box_Top Limit order |
| i_Buffer_ATR_Mult | Min_Box_ATR / Swing_Lookback |

### Entry Mechanism

```
Resistance_Zone = Box_Top - Box_Range * Entry_Zone_Pct (0.50)
Condition: Close > Resistance_Zone AND Close < Box_Top + ATR * 3.0
Order: SellShort at Box_Top Limit
  - In resistance zone (Close < Box_Top): fills when price reaches Box_Top
  - Above box (false breakout): fills at open
```

### Exit Mechanism

```
CS_TP: BuyToCover at Frozen_Target Limit (dynamic swing low, capped at Box_Btm)
CS_SL: BuyToCover at Frozen_BoxTop + ATR * 2.0 Stop
CS_BreakExit: 60M close > Frozen_BoxTop (box broke upward)
Safety: Kill > Registry > Holiday > Settlement (unchanged)
```

---

## L3 vs L4 Symmetry

| Aspect | L3 (Long) V14.1 | L4 (Short) V15.0 |
|--------|-----------------|-------------------|
| Zone | Support (bottom 50%) | Resistance (top 50%) |
| Entry order | Buy at Box_Btm Stop | SellShort at Box_Top Limit |
| Target | Swing HIGH, capped at Box_Top | Swing LOW, capped at Box_Btm |
| Stop loss | Box_Btm - ATR*3.0 | Box_Top + ATR*2.0 |
| Daily filter | Close > 20MA OR 60MA | Macro Block (bull = no shorts) |
| 60M trend | Close > MA(12) = bullish | Close < MA(48) = bearish |

---

## Parameters Kept from V14

| Parameter | Value | Why kept |
|-----------|-------|----------|
| Lookback_Bars | 15 | L4-specific box detection (L3 uses 16) |
| Range_Shrink_Rate | 0.7 | L4-specific consolidation threshold (L3 uses 0.1) |
| Weekly_MA_Len | 48 | L4-specific 60M trend (L3 uses MA_Len=12) |
| ATR_Length | 60 | L4-specific longer ATR (L3 uses 9) |
| ATR_Stop_Mult | 2.0 | L4-specific tighter stop (L3 uses 3.0) |
| Cooldown_Bars | 8 | Prevent re-entry after SL above box |
| Daily_FastMA_Len | 20 | Macro Block unchanged |
| Daily_SlowMA_Len | 60 | Macro Block unchanged |

---

## MC9 Testing Checklist

- [x] Write V15 code (matrix architecture)
- [x] ASCII verification (24/24 PASS)
- [ ] Load V15 into MC9 as STRATEGY_WILLY_SHORT_CTEST2
- [ ] Run baseline backtest with initial params (0.50/8.5/80)
- [ ] Compare vs V14.4 — evaluate improvement
- [ ] If promising: MC9 parameter optimization
- [ ] Sync optimized params into .pla code
- [ ] Update all documentation
- [ ] Deploy on MC9
