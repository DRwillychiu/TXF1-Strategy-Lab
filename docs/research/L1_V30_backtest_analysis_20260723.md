# L1 TrendLong V3.0 Backtest Analysis (2026-07-23)

## Context
- V3.0 = IOG migration from V2.9.1 (tick-level P7/P4, BarStatus guards)
- Backtest period: 2019-12-16 ~ 2026-07-23, TAIFEX 45M chart, Bar Magnifier 1 Min
- Two MC12 runs compared: P7 threshold=500 vs threshold=200
- Source: MC12 strategy performance report exports (verified on desktop)

## Run 1: T500

| Metric | Value |
|--------|-------|
| Net P&L | 2,399,000 TWD |
| PF | 1.396 |
| MDD | -498,000 (-18.2%) |
| Trades | 458 |
| Win rate | 31.4% |
| W:L ratio | 3.04x |
| Annual Sharpe | 0.927 |
| Sortino | 0.647 |
| Slippage paid | 916,000 |

## Run 2: T200 (V3.0 code default)

| Metric | Value |
|--------|-------|
| Net P&L | 2,074,000 TWD |
| PF | 1.348 |
| MDD | -493,200 (-21.7%) |
| Trades | 508 |
| Win rate | 36.4% |
| W:L ratio | 2.35x |
| Annual Sharpe | 0.879 |
| Sortino | 0.583 |
| Slippage paid | 1,016,000 |

## Exit Label Comparison

| Label | T500 | T200 | Delta | Impact |
|-------|------|------|-------|--------|
| TL_SL | 239 | 258 | +19 | More re-entries from early P7 exit |
| TL_SP | 14 | 109 | +95 | P7 aggressively capturing profits |
| TL_TP | 105 | 57 | -48 | Big winners cut short by P7 |
| TL_TSL | 41 | 31 | -10 | Round-trip losses reduced |
| TL_SL_Gap | 25 | 25 | 0 | Unchanged |
| TL_Holiday | 17 | 15 | -2 | — |
| TL_Settlement | 17 | 13 | -4 | P7 exits before settlement |

## Yearly P&L Comparison

| Year | T500 | T200 | Diff |
|------|------|------|------|
| 2019 | +16K | +16K | 0 |
| 2020 | +426K | +366K | -60K |
| 2021 | +224K | +159K | -65K |
| 2022 | +35K | +5K | -30K |
| 2023 | +109K | -15K | -124K |
| 2024 | +397K | +495K | +98K |
| 2025 | +122K | +97K | -25K |
| 2026 | +1,070K | +951K | -119K |

## 2026 Monthly Comparison

| Month | T500 | T200 | Diff | Effect |
|-------|------|------|------|--------|
| Jan | -82K | +9K | +91K | Protection |
| Feb | +485K | +213K | -272K | Truncation |
| Mar | +7K | -34K | -41K | Slight negative |
| Apr | +703K | +756K | +53K | Slight positive |
| May | -165K | +25K | +190K | Protection |
| Jun | +450K | +27K | -423K | Truncation |
| Jul | -329K | -45K | +284K | Protection |

Protection gain (Jan/May/Jul): +565K
Truncation cost (Feb/Jun): -695K
Net 2026: -119K worse with T200

## R:R Analysis by Exit Type (T200)

| Exit Type | n | Avg P&L | Avg MAE | R:R |
|-----------|---|---------|---------|-----|
| TL_SP | 109 | +150 pts | -62 pts | 2.42x |
| TL_TP | 57 | +241 pts | -31 pts | 7.88x |
| TL_TSL | 31 | -92 pts | -94 pts | 0.98x |
| TL_SL | 258 | -94 pts | -91 pts | 1.04x |
| TL_SL_Gap | 25 | -105 pts | -120 pts | 0.87x |
| TL_Settlement | 13 | +528 pts | -21 pts | 25.12x |
| TL_Holiday | 15 | +212 pts | -34 pts | 6.25x |

Overall T200: avg win +217 pts, avg loss -93 pts, R:R 2.35x, EV +20.4 pts/trade
Overall T500: EV +26.2 pts/trade

## P7 Capture Efficiency

| Metric | TL_SP (P7) | TL_TP (trail) |
|--------|-----------|---------------|
| Avg captured | 150 pts | 241 pts |
| Avg MFE | 363 pts | 418 pts |
| Capture rate | 41.4% | 57.7% |

P7=200 leaves avg 213 pts on the table per trade.

## P7 Chase-Back Cycle Analysis (T200)

After P7 exits, the strategy re-enters and attempts to capture remaining move:

- Re-entry price gap: avg +48 pts higher (67% chase up)
- Re-entry R:R: 2.08x (41.7% WR, avg win +267, avg loss -129)
- Re-entry EV: +31.3 pts/attempt (after slippage)
- Chase success rate: 62% of cycles net positive
- Chain depth: 45% chase back on 1st attempt, 55% need 2+ attempts
- Failure mode: 30% of cycles hit 2+ consecutive SL after P7
  - Avg: P7 +130 pts then 3.2x SL = net -227 pts
  - Worst: P7 +30 pts then 2x SL = net -758 pts

## SL Distribution (T200)

| Range | Count | % |
|-------|-------|---|
| 0 to -100 pts | 184 | 71.3% |
| -101 to -200 pts | 59 | 22.9% |
| -201 to -300 pts | 8 | 3.1% |
| -301 to -400 pts | 4 | 1.6% |
| -400+ pts | 3 | 1.2% |

Median SL: -73 pts. SL mechanism effectively controls per-trade risk.

## Decision: P7=T200 (User Ruling 2026-07-23)

**Ruling**: Adopt T200 (stopProfitPoints_Long=200) as V3.0 baseline.

**Rationale** (user reasoning):
1. T500 historical outperformance is backward-looking. Future regime may produce
   shorter trends (<500 pts) where T500 offers zero protection.
2. P7 is not the primary optimization target. Stop loss (P3/P4) controls risk
   regardless of re-entry price. R:R is the real lever.
3. The chase-back mechanism has positive expected value (+31 pts/attempt),
   and each re-entry has controlled downside via SL (median -73 pts).
4. P7 threshold x giveback sweep (64 combos) is DEPRIORITIZED.

**Decision NOT to pursue**: P7 parameter sweep. Focus shifts to P3 optimization.

## Next Steps (Updated Priority)

1. **P3 initial stop optimization** — SL_Multiplier and Daily_Cap_Multiplier sweep,
   non-ATR alternatives, R:R framework analysis
2. **P4 trailing stop optimization** — MA type (SMA/EMA/ZLEMA), length sweep 30-80,
   TrailOffset sensitivity
3. P7 threshold sweep — DEPRIORITIZED (only if P3/P4 results warrant revisit)
4. Reclaim mechanism — deferred (after P3/P4 optimization)
