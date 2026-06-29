# Extreme Market Initial Stop Loss — Multi-Layer SOP

**Date**: 2026-06-29
**Status**: METHODOLOGY (permanent SOP, referenced by all extreme market strategies)
**Author**: User design directive + Claude Code documentation
**Scope**: Any strategy operating in extreme volatility environments (500-1000 pt swings)

---

## 1. Design Philosophy: Fine Dining

Initial stop loss is a multi-course fine dining experience, not a single dish.
Every layer must be perfectly presented with independent logic, independent trigger conditions,
and independent noise protection. The goal is a logically rich architecture, not a simple
off-the-shelf fixed-point approach.

**Core principles:**
1. ATR is the LAST defense line, not the primary exit mechanism
2. Before ATR, multiple active defense lines monitor real-time price action
3. Fixed-point stops (e.g., cap at 100 pts) are prohibited in vol-adaptive architectures
4. Extreme market strategies require more flexible AND more rigorous SL design than normal strategies
5. All extreme market SL designs must be formally documented as SOP for future reference

---

## 2. The Problem This SOP Solves

### Why static stop orders fail in extreme markets

When a short position hits its ATR-based stop loss during extreme volatility:
1. The stop order sits at a fixed price level at the exchange
2. In 500-1000 pt swings, the price approaches the SL level rapidly
3. Other program trading stops cluster around similar levels
4. All stops fire simultaneously, creating a **stop cascade**
5. Slippage amplifies: actual fill price is 100-300+ pts worse than intended SL
6. The trader's actual loss = intended SL distance + cascade slippage

### Why 60M timeframe amplifies this risk

- 60M bars mean the strategy evaluates once per hour
- Between evaluations, extreme moves happen without the strategy reacting
- The strategy is "blind" to intrabar price action
- A static stop order is the only protection, but it's vulnerable to cascade slippage

---

## 3. Multi-Layer Defense Architecture (User Approved 2026-06-29)

Initial stop loss is a structural stop (like a commercial office building).
The foundation is the 60M ATR stop. The upper floors are 1M multi-layer real-time monitoring.

### Foundation — 60M ATR Stop Loss (SetStopLoss)
The absolute last resort safety net. ATR x multiplier, placed at the exchange level.

### 1F — K-bar Pattern Monitoring
Detect 1M reversal patterns: volume + long lower shadow, bullish engulfing, consecutive bullish bars,
expanding bullish bars. Confirms that buy-side is aggressively intervening.

### 2F — Volume-Price Monitoring
Detect 1M sudden volume spike + up, rising volume + rising price synchronization.
Confirms that adverse momentum has real volume support, not a short-side false breakout.

### 3F — Momentum Speed Monitoring
Detect 1M price acceleration increasing, per-unit-time advance exceeding threshold.
Enables maximum avoidance of stop cascade risk.

### 4F — Structure Break Monitoring
Detect 1M gap up, price breaking above short entry price.
Confirms price structure has flipped. (When this condition fires, exit is 100% guaranteed to be a losing exit.)

### 5F — Volatility Environment Monitoring
Detect 1M ATR suddenly jumping to multiples of recent average.
Indicates overall market structure is undergoing regime change (vol expansion turning to contraction / vol secondary expansion).

### Trigger Mechanism
All five floors operate independently, using a weighted scoring system.
No intervention during normal conditions (does not activate until unrealized loss exceeds threshold).
When multiple floors light up simultaneously (>= 3 floors + score >= 65%),
preemptive market exit BEFORE price reaches the ATR stop level, avoiding the stop cascade zone.

---

## 4. 1M Reversal Factor Catalog (Short Position: Detecting Adverse Upward Move)

> For Long positions, mirror all directions (detect adverse downward move).

### Category A — Candlestick Patterns (K-bar)

| # | Factor | Description | Detection Logic | Reliability | Noise |
|---|--------|-------------|-----------------|-------------|-------|
| A1 | Volume + Long Lower Shadow | 1M bullish bar with long lower shadow, buy support at low | Shadow > 2x body AND vol > N x avg | High | Low |
| A2 | Bullish Engulfing | Current 1M bullish bar fully engulfs previous bearish bar | Close > prev Open AND Open < prev Close | High | Low |
| A3 | Large Body Bullish (Marubozu) | Near-shadowless large bullish 1M bar, complete buyer dominance | Body > X x ATR_1M, shadows < 10% body | Medium | Medium |
| A4 | Consecutive Bullish Bars | 3-5 consecutive 1M bars with rising closes | Close[0] > Close[1] > Close[2]... for N | High | Low |
| A5 | Bullish Bar Ratio Imbalance | > 70% of recent N bars are bullish, sustained buy pressure | Count(bullish) / N > threshold | Medium | Medium |
| A6 | Expanding Bullish Bars | Each successive bullish bar larger than previous, accelerating | Body[0] > Body[1] > Body[2] all bullish | High | Low |

### Category B — Volume-Price

| # | Factor | Description | Detection Logic | Reliability | Noise |
|---|--------|-------------|-----------------|-------------|-------|
| B1 | Sudden Volume Spike + Up | 1M volume jumps to N x average on bullish bar, program trading signal | Vol > N x AvgVol AND Close > Open | High | Low |
| B2 | Rising Volume + Rising Price | N consecutive 1M bars with both volume and price rising | Vol[0] > Vol[1] AND Close[0] > Close[1] | High | Low |
| B3 | Bearish Volume Drying | Volume on bearish bars declining, sellers exhausted | Bearish bars: Vol decreasing over N bars | Medium | Medium |
| B4 | Volume-Price Divergence | Price falling but volume shrinking, bearish exhaustion | Lower lows BUT declining volume | Medium | High |

### Category C — Momentum / Speed

| # | Factor | Description | Detection Logic | Reliability | Noise |
|---|--------|-------------|-----------------|-------------|-------|
| C1 | Price Acceleration | Points per minute increasing, cascade precursor | Rate of change increasing over N bars | High | Low |
| C2 | Speed Threshold | > X pts in Y minutes, extreme move by definition | Close - Close[N] > threshold | High | Low |
| C3 | Short-term Momentum Flip | 1M MA5 crosses above MA15, 1M trend turns bullish | MA5_1M > MA15_1M crossover | Medium | Medium |
| C4 | V-Shape Reversal | Sharp V-bottom recovery on 1M, short squeeze dynamics | Low[N] = N-bar low AND recovery > X x ATR_1M | Medium | Medium |

### Category D — Structure Break

| # | Factor | Description | Detection Logic | Reliability | Noise |
|---|--------|-------------|-----------------|-------------|-------|
| D1 | Break 1M Swing High | Price breaks above recent N-bar high, structural breakout | Close > Highest(High, N) of 1M | High | Medium |
| D2 | 1M Gap Up | 1M gap up (Open > prev High), news/large order driven | Open > High[1] on 1M | High | Low |
| D3 | Break Entry Price | 1M price breaks above short entry price, all profit gone | Close_1M > EntryPrice | High | Low |

### Category E — Contextual / Environmental

| # | Factor | Description | Detection Logic | Reliability | Noise |
|---|--------|-------------|-----------------|-------------|-------|
| E1 | Opening 5-min Spike | Day session open with consecutive 1M jumps, overnight news | Time 0845-0850 AND adverse > X pts | Medium | Medium |
| E2 | US Market Open Linkage | 21:30 US open drives TXF linkage spike | Time = 2130 AND 1M range > X x ATR_1M | Medium | High |
| E3 | Volatility Regime Shift | 1M ATR suddenly jumps to X x recent average, market structure changing | ATR_1M(5) > ATR_1M(60) x X | High | Low |

---

## 5. Recommended Configuration: Low-Noise Factors Only

### Selected factors (11 total, all Noise = Low)

| # | Factor | Category | Weight |
|---|--------|----------|--------|
| A1 | Volume + Long Lower Shadow | K-bar | 3 |
| A2 | Bullish Engulfing | K-bar | 3 |
| A4 | Consecutive Bullish Bars | K-bar | 2 |
| A6 | Expanding Bullish Bars | K-bar | 3 |
| B1 | Sudden Volume Spike + Up | Volume | 3 |
| B2 | Rising Volume + Rising Price | Volume | 3 |
| C1 | Price Acceleration | Momentum | 3 |
| C2 | Speed Threshold | Momentum | 3 |
| D2 | 1M Gap Up | Structure | 2 |
| D3 | Break Entry Price | Structure | 2 |
| E3 | Volatility Regime Shift | Environment | 3 |

**Max score**: 30 points
**Trigger threshold**: 65% = 20 points
**Cross-category gate**: must have >= 3 different categories contributing

### Activation threshold

The 1M scoring system only activates when:
- Unrealized loss > 40-60% of SL distance (not during normal early-trade fluctuation)
- This prevents false signals during the natural "breathing" period after entry

---

## 6. Scoring System: Probability Early Warning

### Three zones

| Zone | Score % | Action |
|------|---------|--------|
| SAFE (0-30%) | 0-9 pts | Normal fluctuation, no intervention |
| WARNING (30-65%) | 9-19 pts | Alert: "X% trigger probability", heightened monitoring |
| TRIGGER (65-100%) | 20-30 pts | Preemptive market exit, do not wait for ATR SL |

### MC12 implementation concept

- Each 1M bar: scan all 11 factors, calculate weighted score
- Plot score on chart for visual backtesting review
- Alert/Commentary output for real-time warnings
- Exit order: market order when score >= trigger threshold

---

## 7. What Does NOT Change

- **Entry logic**: unchanged (60M BBW squeeze breakdown, regime filter, etc.)
- **TP exit**: unchanged (ATR x TargetATRMult limit order)
- **Mid exit**: unchanged (MidExit logic)
- **Time stop**: unchanged (MaxBars)
- **SP mechanism**: unchanged (trailing stop profit)
- **P0 safety modules**: unchanged (Settlement/Holiday/Kill/Registry)
- **ATR SetStopLoss**: remains as Layer E safety net

Only the initial stop loss EXECUTION METHOD changes:
from passive (static stop order) to active (1M multi-factor preemptive exit).

---

## 8. MC12 Architecture Requirements

| Requirement | Detail |
|-------------|--------|
| Data1 | 60M (entry signals, regime filter, ATR calc) |
| Data2 | 1M (intrabar exit quality monitoring) |
| IOG | IntrabarOrderGeneration = True |
| IntrabarPersist | Required for all tracking variables |
| MaxBarsBack | Increase to accommodate 1M lookback |
| Backtest speed | ~60x slower per run (each 60M bar = 60 evaluations) |

---

## 9. Cross-Strategy Applicability

This SOP applies to any strategy that:
1. Operates in extreme volatility environments
2. Uses ATR-based initial stop loss
3. Holds positions across periods of potential 500-1000 pt swings
4. Is vulnerable to program trading stop cascades

Current candidates:
- S3_S VolSqueezeShort (primary — designed for vol expansion entries)
- Any future extreme market strategy (S6 FlashCrashMomentum, S9 VolExplosion, etc.)

---

## 10. Related Documents

| File | Purpose |
|------|---------|
| `docs/methodology/entry_exit_sop.md` | 9-layer exit architecture (this SOP adds Layer 1 detail) |
| `docs/methodology/ENGINEERING_SYSTEM.md` | Rule #16 5-pillar framework |
| `docs/policies/P3b_immediate_stop_guard_design_20260618.md` | SetStopLoss = Layer E safety net |
| `docs/research/stop_loss_mechanisms_catalog_20260628.md` | Industry 12-mechanism reference |
| `strategies/research/S03_VolSqueezeShort/v175_ConditionalCap_spec.md` | v1.7.5 (superseded by this SOP) |

---

## 11. Version History

| Date | Change |
|------|--------|
| 2026-06-29 | Initial SOP created. 5-category 18-factor catalog. Low-noise 11-factor recommended set. |
