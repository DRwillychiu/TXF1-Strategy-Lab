# Colleague Live Strategies Reference

> Source: colleague's production portfolio (confirmed profitable, already deployed)
> Date received: 2026-07-30
> Purpose: logic reference only, not for direct replication

---

## Strategy Overview

| # | Name     | Timeframe | Category              | Max Pos | Key Mechanism                |
|---|----------|-----------|-----------------------|---------|------------------------------|
| 1 | Neo Capricorn   | 1H        | Price Channel          | -       | Breakout at key time points  |
| 2 | Petis    | 450S      | Price Channel          | -       | Trend-sensitive, reduced chop trades |
| 3 | Aquila   | 60M       | Price Channel          | -       | Channel +/- ATR breakout     |
| 4 | Hurricane| 3600S     | Moving Average         | 2       | Mean-reversion + momentum add-on |
| 5 | Rime     | 450S      | Indicator Composite    | -       | Multi-factor directional bias |
| 6 | Storm    | 33M       | Channel + Indicator    | -       | Volatility + custom CDP + regression |
| 7 | Boya     | 90M       | Price Channel (BB)     | -       | Bollinger mid-line breakout  |
| 8 | Song Zhiwen | 60M   | Indicator (Divergence) | -       | Dynamic divergence model     |
| 9 | Yang Jiong | 440S   | Statistical            | -       | Discriminant analysis clustering |

---

## 1. Neo Capricorn (1H Price Channel)

- **Type**: Trend / Breakout
- **Timeframe**: 1 Hour
- **Session**: Full session (day + night)
- **Entry**: Capture breakouts at specific time-based highs/lows; trades both long and short
- **Exit**:
  - Small fixed stop-loss
  - Dynamic trailing stop using ATR-based trailing profit points
- **Edge**: Time-specific breakout targeting with tight risk control

---

## 2. Petis (450S Price Channel)

- **Type**: Trend / Price Channel
- **Timeframe**: 450 Seconds
- **Entry**: High trend sensitivity; aggressively probes when trend potential detected; reduces frequency during consolidation to avoid whipsaw losses
- **Exit**:
  - Trailing profit stop
  - Max percentage stop-loss
- **Edge**: Adaptive aggression -- active in trending markets, passive in chop

---

## 3. Aquila (60M Price Channel)

- **Type**: Trend / Breakout
- **Timeframe**: 60 Minutes
- **Session**: Full session (day + night)
- **Entry**:
  - Long: price breaks above channel high + ATR
  - Short: price breaks below channel low - ATR
- **Exit**:
  - Dynamic trailing profit stop
  - ATR-based stop-loss
- **Edge**: ATR-filtered channel breakout reduces false signals

---

## 4. Hurricane (3600S Moving Average)

- **Type**: Mean-Reversion + Momentum
- **Timeframe**: 3600 Seconds
- **Max Position**: 2 contracts
- **Entry**:
  - Primary: detects price-to-MA divergence magnitude; enters counter-trend at identified extreme values when reversal conditions met
  - Secondary: when price deviates from norm but doesn't meet counter-trend threshold, interprets as extreme momentum and enters with-trend (chase)
- **Add-on**: Pyramiding mechanism for strong continuation moves -- high explosive potential in large swing markets
- **Exit**:
  - Trailing profit stop
  - Max percentage stop-loss
- **Edge**: Dual-mode (reversal + chase) with pyramiding for outsized gains

---

## 5. Rime (450S Indicator Composite)

- **Type**: Multi-Factor / Directional
- **Timeframe**: 450 Seconds
- **Entry**: Aggregates multiple technical indicators for rapid signal generation; when enough factors align, executes predictive entry; calculates optimal direction between with-trend and counter-trend based on win rate; concentrates trades in one direction for enhanced trend exposure
- **Exit**: Not specified (likely trailing + percentage)
- **Edge**: Concentrated directional betting amplifies trend capture

---

## 6. Storm (33M Channel + Indicator)

- **Type**: Volatility + Custom Indicator
- **Timeframe**: 33 Minutes
- **Entry**: Uses volatility combined with a custom CDP-like key price level indicator to establish importance weights at different price zones; regression analysis calculates critical breakout levels; cross-references with current indicator zone to assess entry probability
- **Exit**:
  - Proportional stop-loss (ratio-based)
- **Edge**: Multi-layer price importance mapping via regression + custom CDP

---

## 7. Boya (90M Price Channel / Bollinger)

- **Type**: Trend / Bollinger Band
- **Timeframe**: 90 Minutes
- **Entry (long example)**:
  - Price crosses above Bollinger mid-line AND upper band has positive slope -> enter long
  - Reverse logic for short
  - Filter: if price instantly pierces extreme std-dev band -> skip entry (potential black swan event)
- **Exit (long example)**:
  - After entry, sets a strict Bollinger-based percentage retracement zone (mid-line to lower band)
  - If price reverses into this zone -> stop-loss triggered
  - After stop-loss, re-evaluates price action before re-entering (no immediate flip to avoid whipsaw in volatile markets)
- **Unsuitable for**: Instruments that chronically trade sideways (causes frequent in/out)
- **Edge**: Bollinger slope filter + no-flip-after-stop discipline

---

## 8. Song Zhiwen (60M Indicator / Divergence)

- **Type**: Mean-Reversion / Divergence
- **Timeframe**: 60 Minutes
- **Entry**: Detects extreme market sentiment and price deviation using a Dynamic Divergence Model to identify trend exhaustion points; low-frequency by design -- filters most market noise, enters only at high confidence levels; holds positions for extended periods to capture full value-reversion swings
- **Stop-Loss (3-layer)**:
  - a. Hard Stop: absolute max loss boundary per trade
  - b. Volatility Stop: ATR / volatility-adjusted dynamic exit to survive extreme moves
  - c. Pattern Stop: exits when the entry's technical pattern logic is invalidated (e.g., support breaks) -- independent of price data
- **Take-Profit (multi-stage dynamic)**:
  - Pullback profit lock
  - Max volatility satisfaction point
  - Pattern completion profit target
  - Preserves upside extension in large moves
- **Settlement**: Forced exit on settlement day, no rollover -- eliminates month-switch spread risk and liquidity issues
- **Edge**: Low-frequency high-conviction divergence with 3-layer risk architecture

---

## 9. Yang Jiong (440S Statistical)

- **Type**: Statistical / Machine Learning-like
- **Timeframe**: 440 Seconds
- **Entry**: Applies Discriminant Analysis from multivariate statistics for dimensionality reduction and clustering of complex market data; mimics ML logic to auto-identify current "high win-rate direction"; concentrates consecutive same-direction trades in that direction for efficiency and signal accuracy
- **Stop-Loss (3-layer)**: Same as Song Zhiwen
  - a. Hard Stop
  - b. Volatility Stop (ATR-based)
  - c. Pattern Stop
- **Take-Profit (multi-stage dynamic)**: Same as Song Zhiwen
  - Pullback lock + max volatility satisfaction + pattern completion
- **Settlement**: Forced exit on settlement day, no rollover
- **Edge**: Statistical classification for directional conviction + concentrated same-direction trading

---

## Cross-Strategy Observations

### Common Exit Patterns
- **Trailing profit** appears in 6/9 strategies (Neo Capricorn, Petis, Aquila, Hurricane, Song Zhiwen, Yang Jiong)
- **ATR-based stops** in at least 4 strategies
- **Max percentage stop-loss** in at least 3 strategies
- **3-layer stop architecture** (Hard + Volatility + Pattern) shared by Song Zhiwen & Yang Jiong

### Timeframe Distribution
- Sub-minute (450S, 440S): 3 strategies -- scalp/short-term
- Mid-range (33M, 60M, 90M): 4 strategies -- intraday swing
- Longer (1H, 3600S): 2 strategies -- position/swing

### Strategy Type Mix
- Price Channel / Breakout: 4 (Neo Capricorn, Petis, Aquila, Boya)
- Indicator / Multi-Factor: 3 (Rime, Storm, Song Zhiwen)
- Mean-Reversion / Statistical: 2 (Hurricane, Yang Jiong)

### Notable Design Choices
- Hurricane is the only strategy with explicit pyramiding (max 2 contracts)
- Boya has a unique "no immediate flip after stop" rule to avoid whipsaw
- Song Zhiwen & Yang Jiong share identical exit frameworks but differ entirely in entry logic (divergence vs. discriminant analysis)
- Settlement-day forced exit (no rollover) is explicitly stated for Song Zhiwen & Yang Jiong; likely common across all
