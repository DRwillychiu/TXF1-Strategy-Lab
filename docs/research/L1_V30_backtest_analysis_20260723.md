# L1 TrendLong V3.0 Backtest Analysis (2026-07-23)

## Context
- V3.0 = IOG migration from V2.9.1 (tick-level P7/P4, BarStatus guards)
- Backtest period: 2020-08 ~ 2026-07, TAIFEX 45M chart
- Two runs compared: P7 threshold=500 (old param persisted in MC) vs threshold=200 (V3.0 intended)

## Run 1: T500 (MC parameter override kept old value)
- **Net P&L**: 2,203,200 TWD | **PF**: 1.38 | **MDD**: -498,000
- **Trades**: 425 | **Win rate**: 31.3% | **W:L**: 3.03x | **Avg/trade**: 5,184
- TL_SP (P7 exits): 14 trades, +953,600

## Run 2: T200 (V3.0 intended parameter)
- **Net P&L**: 1,843,400 TWD | **PF**: 1.32 | **MDD**: -480,000
- **Trades**: 474 | **Win rate**: 36.7% | **W:L**: 2.27x | **Avg/trade**: 3,889
- TL_SP (P7 exits): 105 trades, +3,172,200

## Exit Label Migration (T500 -> T200)
| Label | T500 | T200 | Delta | Impact |
|-------|------|------|-------|--------|
| TL_SP | 14 | 105 | +91 | P7 aggressively capturing profits |
| TL_TP | 96 | 52 | -44 | Big winners cut short by P7 |
| TL_TSL | 38 | 28 | -10 | Round-trip losses reduced |
| TL_SL | 221 | 239 | +18 | More re-entries from early P7 exit |
| TL_SL_Gap | 25 | 25 | 0 | Unchanged |
| TL_Holiday | 16 | 14 | -2 | — |
| TL_Settlement | 15 | 11 | -4 | P7 exits before settlement |

## 2026 Monthly Comparison
| Month | T500 | T200 | Diff | Verdict |
|-------|------|------|------|---------|
| Jan | -82K | +9K | +91K | P7 saved losing month |
| Feb | +485K | +213K | -272K | P7 cut big winner |
| Mar | +7K | -34K | -41K | Slight negative |
| Apr | +713K | +756K | +43K | P7 helped |
| May | -156K | +25K | +181K | P7 turned loss to profit |
| Jun | +450K | +27K | -423K | P7 severely cut big runner |
| Jul | -309K | -45K | +264K | P7 significantly reduced loss |

Protection gain (Jan/May/Jul): +536K
Truncation cost (Feb/Jun): -695K
Net 2026: -157K worse with T200

## Key Finding: P7 Double-Edged Sword
- P7=200 with giveback=55% -> minimum floor at Entry+90pts
- Converts many 300-1000pt potential winners into 90-170pt exits
- Protection value is real (bad months improved) but truncation cost exceeds protection gain
- Core trade-off for parameter sweep: threshold x giveback combinations

## T200 TL_SP P&L Distribution (105 trades)
- 50-100pts: 27 trades (avg 88pts) — bare-minimum protection
- 100-150pts: 36 trades (avg 123pts)
- 150-200pts: 23 trades (avg 171pts)
- 200-300pts: 12 trades (avg 232pts)
- 300-500pts: 6 trades (avg 386pts)
- 104 wins / 1 loss

## Yearly P&L Comparison
| Year | T500 | T200 | Diff |
|------|------|------|------|
| 2020 | +185K | +128K | -56K |
| 2021 | +224K | +159K | -65K |
| 2022 | +35K | +5K | -30K |
| 2023 | +109K | -15K | -124K |
| 2024 | +397K | +495K | +98K |
| 2025 | +145K | +120K | -25K |
| 2026 | +1,108K | +951K | -157K |

## MC Parameter Persistence Note
V3.0 code default changed to stopProfitPoints_Long(200), but MC strategy properties
retained the old override of 500. First backtest run was effectively T500.
Must manually update parameter in MC Strategy Properties to apply code default.

## Next Steps (queued)
1. P7 parameter sweep: threshold x giveback (64 combinations)
2. P4 MA type comparison (SMA vs EMA vs ZLEMA) + length sweep 30-80
3. P3 initial stop optimization (non-ATR alternatives)
4. Reclaim mechanism (after entry/stop optimization)
