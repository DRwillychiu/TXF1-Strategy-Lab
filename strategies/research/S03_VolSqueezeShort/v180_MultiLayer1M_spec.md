# S3_S v1.8.0 — Multi-Layer 1M Exit Monitoring Spec

**Date**: 2026-06-29
**Status**: EXPERIMENTAL (research, not promoted)
**Base**: v1.7.3-FINAL (entry/regime logic unchanged)
**SOP**: `docs/methodology/extreme_sl_multilayer_sop_20260629.md`

---

## 1. Problem Statement

v1.7.3-FINAL uses a static ATR stop order (SetStopLoss) as the sole initial SL mechanism. During extreme volatility (500-1000 pt swings on 60M), program trading stop cascades cause 100-300+ pts slippage beyond intended SL. The strategy is "blind" to intrabar action between 60M evaluations.

v1.8.0 adds a 1M multi-factor scoring system that detects adverse momentum BEFORE price reaches the ATR SL level, enabling preemptive exit to avoid the cascade zone.

---

## 2. Architecture Changes

| Component | v1.7.3-FINAL | v1.8.0 |
|-----------|-------------|--------|
| Data feeds | Data1=60M, Data2=Daily | Data1=60M, Data2=Daily, **Data3=1M** |
| IOG | False | **True** |
| Exit layers | 5 (P0/SL/SP/Mid/TP/Time) | **6** (+1M preemptive) |
| SL mechanism | Static stop order only | Static stop + **1M multi-factor preemptive** |
| Entry evaluation | Every 60M bar | **Gated to BarStatus(1)=2** (60M close only) |
| Mid/Time exit | Every 60M bar | **Gated to BarStatus(1)=2** (60M close only) |
| SP state | Normal variables | **IntraBarPersist** (IOG compatibility) |

---

## 3. New Inputs (10)

| Input | Default | Purpose |
|-------|---------|---------|
| ML_ActivationPct | 40 | Gate 1: % of SL dist to activate scoring |
| ML_ScoreTrigger | 65 | Gate 2: score % to trigger preemptive exit |
| ML_MinCategories | 3 | Gate 3: min categories for cross-gate |
| ML_VolSpikeMult | 2.5 | A1/B1: volume spike multiplier |
| ML_VolAvgLen | 20 | A1/B1: 1M volume average lookback |
| ML_SpeedBars | 5 | C1/C2: speed lookback bars |
| ML_SpeedThreshPts | 80 | C2: speed threshold in points |
| ML_ATR_Short_Len | 5 | E3: short-term 1M ATR |
| ML_ATR_Long_Len | 60 | E3: long-term 1M ATR |
| ML_ATR_Ratio | 2.0 | E3: vol regime shift ratio |

---

## 4. Scoring System (11 Factors, Max 30 pts)

### 1F K-bar (max 11 pts)
| Factor | Pts | Detection |
|--------|-----|-----------|
| A1 Vol+Lower Shadow | 3 | 1M bullish bar, shadow > 2x body, vol > N x avg |
| A2 Bullish Engulfing | 3 | Close > prev Open, Open < prev Close |
| A4 Consecutive Bullish | 2 | 2+ consecutive rising closes on 1M |
| A6 Expanding Bullish | 3 | 3 bullish bars with increasing body size |

### 2F Volume (max 6 pts)
| Factor | Pts | Detection |
|--------|-----|-----------|
| B1 Volume Spike+Up | 3 | Vol > N x avg on bullish 1M bar |
| B2 Rising Vol+Price | 3 | 3 bars: vol and price both rising |

### 3F Momentum (max 6 pts)
| Factor | Pts | Detection |
|--------|-----|-----------|
| C1 Acceleration | 3 | Rate of change increasing over N bars |
| C2 Speed Threshold | 3 | Move > threshold pts in N bars |

### 4F Structure (max 4 pts)
| Factor | Pts | Detection |
|--------|-----|-----------|
| D2 Gap Up | 2 | 1M Open > prev High |
| D3 Break Entry | 2 | 1M Close > EntryPrice |

### 5F Environment (max 3 pts)
| Factor | Pts | Detection |
|--------|-----|-----------|
| E3 Vol Regime Shift | 3 | ATR_1M(5) > ATR_1M(60) x ratio |

---

## 5. Three-Gate Trigger

All three gates must pass simultaneously:

1. **Activation**: Unrealized loss > 40% of frozen SL distance (prevents false signals during normal breathing)
2. **Score**: Weighted score >= 65% of max 30 pts (= 20 pts)
3. **Cross-category**: >= 3 of 5 categories contributing (prevents single-dimension false alarm)

---

## 6. Exit Priority (updated)

| Priority | Label | Type | Condition |
|----------|-------|------|-----------|
| P0-1 | SX_VS_Kill | Market | Manual kill switch |
| P0-2 | SX_VS_RegistryEnd | Market | Registry expired |
| P0-3 | SX_VS_HolFlat | Market | Holiday tail |
| P0-4 | SX_VS_Settlement | Market | Settlement day |
| **S-0** | **SX_VS_1M_Exit** | **Market** | **1M multi-layer trigger (NEW)** |
| S-1 | SX_VS_TP | Limit | ATR x TargetMult |
| S-2 | SX_VS_Mid | Market | Close > MidBand (bar close only) |
| S-3 | SX_VS_TimeStop | Market | BarsHeld >= MaxBars (bar close only) |
| S-4 | SX_VS_SP / SX_VS_SL | Stop | Trailing SP or initial SL |

---

## 7. MC12 Chart Setup

1. Data1: TXF1 60 Minutes
2. Data2: TXF1 Daily (existing regime filter)
3. **Data3: TXF1 1 Minute** (new, for exit monitoring)
4. MaxBarsBack: increase to cover 1M lookback requirements (minimum 60 bars for ATR_Long)
5. Format > Properties > check "Enable IntraBar Order Generation"

---

## 8. Backtest Considerations

- **Speed**: ~60x slower (each 60M bar = 60 evaluations via 1M ticks)
- **Data depth**: 1M data history may be shorter than 60M (verify before backtest)
- **Expected impact**: Fewer SL exits, more SX_VS_1M_Exit exits with smaller losses
- **Risk**: False positive exits could reduce net profit (tune ML_ScoreTrigger)
- **Baseline comparison**: v1.7.3-FINAL backtest must be reproduced with IOG=True for fair comparison

---

## 9. Files

| File | Purpose |
|------|---------|
| `S3_VolSqueezeShort_v180_EXPERIMENTAL.pla` | PowerLanguage source (1043 lines) |
| `v180_MultiLayer1M_spec.md` | This spec document |
| `docs/methodology/extreme_sl_multilayer_sop_20260629.md` | SOP reference |

---

## 10. What Does NOT Change

- Entry logic (60M BBW squeeze breakdown + regime filter)
- TP exit (ATR x TargetMult limit)
- Mid exit logic (thesis fail, now gated to bar close)
- Time stop logic (MaxBars, now gated to bar close)
- SP mechanism (trailing stop profit)
- P0 safety modules (Settlement/Holiday/Kill/Registry)
- ATR SetStopLoss (remains as Layer E safety net)
- All existing inputs and their defaults
