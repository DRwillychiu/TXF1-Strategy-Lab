# S16_S v1.7 Research Log — Percentage Parameter Conversion (2026-07-29)

## 1. Research Question

S16_S_MACrossShort v1.6.2 uses two fixed-point parameters that are
index-level-dependent:

| Parameter | Fixed Value | @9,000 | @20,000 | @40,000 |
|-----------|-------------|--------|---------|---------|
| MinSlope  | 28 pts/bar  | 0.31%  | 0.14%   | 0.07%   |
| QS_MaxLoss| 60 pts      | 0.67%  | 0.30%   | 0.15%   |

**Question**: Can converting these to percentage improve cross-era consistency
and overall performance?

**Prior art**: v0.6-REJECTED (2026-07-10) attempted ATR-based adaptive
MinSlope. Failed because ATR tracks VOLATILITY, not INDEX LEVEL — threshold
varied with market noise rather than structural price level. This research
uses ZLEMA-percentage instead: threshold scales with index level only.

## 2. Methodology — Isolated A/B Testing

### 2.1 Design Principle: Change One Thing at a Time

Three isolated variants created from v1.6.2 baseline to separate the effect
of each parameter change:

| Version | MinSlope Change | QS_MaxLoss Change | Purpose |
|---------|-----------------|--------------------|-----------------------------|
| v1.7    | 28 pts -> Pct   | unchanged (60 pts) | Isolate MinSlope% effect    |
| v1.7.1  | unchanged (28)  | 60 pts -> Pct      | Isolate QS_MaxLoss% effect  |
| v1.7.2  | 28 pts -> Pct   | 60 pts -> Pct      | Combined effect             |

This isolation ensures that if v1.7.2 underperforms, we know WHICH parameter
change caused the degradation.

### 2.2 Three-Phase Evaluation

**Phase 1 — Unoptimized defaults**: Run each variant with manually calculated
default values that match v1.6.2 behavior at current index level (~40,000).
This reveals the structural impact of the conversion itself.

- MinSlope_Pct default: 28/40000*100 = 0.07%
- QS_MaxLoss_Pct default: 60/40000*100 = 0.15%

**Phase 2 — Parameter optimization**: Sweep the full parameter space to find
each variant's best possible configuration. This prevents premature rejection
based on unoptimized defaults alone.

- Single parameter: exhaustive sweep (all combinations tested)
- Two parameters: GA optimization (population 300, crossover 0.95,
  mutation 0.05, 20 generations)

**Phase 3 — Optimized comparison**: Compare each variant's best optimized
result against v1.6.2 baseline on multiple criteria: Net Profit, PF, MDD,
trade count, avg trade, robustness of parameter neighborhood.

### 2.3 Selection Criteria (multi-dimensional, not single-metric)

1. Net Profit — must exceed baseline
2. Profit Factor — must not materially degrade (>1.7)
3. Trade count — must remain in same order of magnitude as baseline
4. Parameter robustness — neighboring values should produce similar results
5. MDD — acceptable if Net/MDD ratio holds
6. Exit signal distribution — structural consistency with baseline

## 3. Phase 1 Results — Unoptimized Defaults

### v1.6.2 Baseline
- Net: +2,006,800 | PF: 1.775 | MDD: -456,000 | Trades: 112

### Unoptimized Results

| Version | Params | Net | Trades | PF | MDD | vs Base |
|---------|--------|-----|--------|----|-----|---------|
| v1.7    | Slope%=0.07 | +749,600 | 412 | 1.111 | -1,414K | -62.6% |
| v1.7.1  | QS%=0.15 | +2,074,000 | 126 | 1.671 | -515K | +3.3% |
| v1.7.2  | both defaults | +717,600 | 426 | 1.110 | -1,456K | -64.2% |

**Observation**: v1.7 and v1.7.2 show massive trade count inflation (3.7x)
and PF collapse. v1.7.1 already exceeds baseline net profit with default
parameters.

**Critical lesson**: These results alone are NOT conclusive. Unoptimized
defaults may not represent the best possible configuration for each variant.
Parameter optimization is mandatory before rejection.

## 4. Phase 2 — Parameter Optimization

### 4.1 v1.7.2 GA Optimization (MinSlope_Pct + QS_MaxLoss_Pct)

Ranges:
- MinSlope_Pct: 0.03 to 0.35, step 0.02
- QS_MaxLoss_Pct: 0.05 to 0.40, step 0.025

GA settings: Population 300, Crossover 0.95, Mutation 0.05, 20 generations.
130 parameter combinations evaluated.

Top 5 results by Net Profit:

| MinSlope% | QS% | Net | Trades | PF | MDD | vs Base |
|-----------|-----|-----|--------|----|-----|---------|
| 0.07 | 0.40 | +702,800 | 410 | 1.100 | -1,544K | -65.0% |
| 0.11 | 0.325 | +690,400 | 136 | 1.257 | -554K | -65.6% |
| 0.15 | 0.275 | +490,000 | 47 | 1.606 | -320K | -75.6% |
| 0.09 | 0.125 | +370,800 | 225 | 1.102 | -798K | -81.5% |
| 0.15 | 0.15 | +354,800 | 48 | 1.453 | -317K | -82.3% |

**Verdict**: ENTIRE v1.7.2 parameter space fails to match baseline.
Best result is only 35% of baseline net profit.

MinSlope_Pct band analysis revealed the fundamental problem:
- Low (0.03-0.07): 410-2073 trades, no filtering
- Medium (0.11-0.15): 47-136 trades, decent PF but -65% net
- High (0.21+): 4-21 trades, strategy nearly dead at current levels

### 4.2 v1.7.1 Exhaustive Optimization (QS_MaxLoss_Pct only)

Range: QS_MaxLoss_Pct 0.05 to 0.40, step 0.025 (16 combinations).
MinSlope fixed at 28 pts.

Full results sorted by Net Profit:

| QS% | Net | Trades | PF | MDD | Avg Trade | vs Base |
|-----|-----|--------|----|-----|-----------|---------|
| 0.250 | +2,413,200 | 122 | 1.773 | -561K | 19,780 | +20.2% |
| 0.275 | +2,402,800 | 122 | 1.767 | -587K | 19,695 | +19.7% |
| 0.225 | +2,361,200 | 122 | 1.763 | -580K | 19,354 | +17.7% |
| 0.300 | +2,360,000 | 121 | 1.743 | -596K | 19,504 | +17.6% |
| 0.375 | +2,265,600 | 121 | 1.693 | -647K | 18,724 | +12.9% |
| 0.350 | +2,263,200 | 121 | 1.692 | -618K | 18,704 | +12.8% |
| 0.325 | +2,250,000 | 121 | 1.685 | -618K | 18,595 | +12.1% |
| 0.400 | +2,245,200 | 121 | 1.682 | -659K | 18,555 | +11.9% |
| 0.125 | +2,154,000 | 127 | 1.715 | -542K | 16,961 | +7.3% |
| 0.175 | +2,143,600 | 125 | 1.681 | -520K | 17,149 | +6.8% |
| 0.100 | +2,142,000 | 129 | 1.716 | -515K | 16,605 | +6.7% |
| 0.200 | +2,140,000 | 123 | 1.680 | -550K | 17,398 | +6.6% |
| 0.150 | +2,074,000 | 126 | 1.671 | -515K | 16,460 | +3.3% |
| 0.050 | +1,671,200 | 133 | 1.578 | -655K | 12,565 | -16.7% |
| 0.075 | +1,576,000 | 131 | 1.528 | -655K | 12,031 | -21.5% |

**Key finding**: ALL values from 0.100 to 0.400 beat baseline in net profit.
The 0.225-0.275 sweet spot is extremely robust (3 values within 2.2%).

## 5. Phase 3 — Optimized Results Comparison

### 5.1 Performance Summary

| Metric | v1.6.2 Base | v1.7 OPT | v1.7.1 OPT | v1.7.2 OPT |
|--------|-------------|----------|-------------|------------|
| Params | Slope=28, QS=60pts | Slope%=? | Slope=28, QS%=0.250 | Slope%=0.07, QS%=0.40 |
| Net Profit | +2,007K | +1,118K | **+2,413K** | +703K |
| vs Baseline | — | -44.3% | **+20.2%** | -65.0% |
| Gross Profit | — | +6,336K | +5,536K | +7,706K |
| Gross Loss | — | -5,218K | -3,122K | -7,003K |
| Trades | 112 | 310 | 122 | 410 |
| Profit Factor | 1.775 | 1.214 | **1.773** | 1.100 |
| MDD | -456K | -954K | -561K | -1,544K |
| MDD % | — | -42.7% | -23.4% | -70.9% |
| Net/MDD Ratio | 4.40 | 1.17 | **4.30** | 0.46 |
| ROA | — | 124.7% | **524.2%** | 47.8% |
| Avg Trade | 17,918 | 3,605 | **19,780** | 1,714 |
| Annualized | — | 7.39% | **15.97%** | 4.65% |

### 5.2 Exit Signal Distribution (optimized)

| Exit Signal | v1.7 (310T) | v1.7.1 (122T) | v1.7.2 (410T) |
|-------------|-------------|---------------|---------------|
| QuickStop_Tim | 139 (44.8%) | 44 (36.1%) | 221 (53.9%) |
| QuickStop_Los | 81 (26.1%) | 42 (34.4%) | 58 (14.1%) |
| TimeStop | 57 (18.4%) | 26 (21.3%) | 72 (17.6%) |
| GoldenCross | 9 (2.9%) | 4 (3.3%) | 15 (3.7%) |
| SL | 7 (2.3%) | 2 (1.6%) | 11 (2.7%) |
| ML_Exit | 6 (1.9%) | 0 (0.0%) | 17 (4.1%) |
| BE_Trail1 | 4 (1.3%) | 2 (1.6%) | 4 (1.0%) |
| TailFlat | 4 (1.3%) | 1 (0.8%) | 7 (1.7%) |
| BE_Trail2 | 3 (1.0%) | 1 (0.8%) | 5 (1.2%) |
| **Re-Entry** | 16 (5.2%) | 8 (6.6%) | 17 (4.1%) |

v1.7.1 notable: QuickStop_Los ratio (34.4%) is higher than v1.7 (26.1%) and
v1.7.2 (14.1%), confirming QS%=0.250 is more actively cutting bad trades
rather than indiscriminately stopping everything.

### 5.3 Improvement from Unoptimized to Optimized

| Version | Unopt Net | Opt Net | Change | MDD Change |
|---------|-----------|---------|--------|------------|
| v1.7    | +750K     | +1,118K | +49.1% | -1,414K -> -954K |
| v1.7.1  | +2,074K   | +2,413K | +16.3% | -515K -> -561K |
| v1.7.2  | +718K     | +703K   | **-2.1%** | -1,456K -> -1,544K |

v1.7.2 optimization actually made it WORSE — the parameter space is
exhausted with no viable combination.

## 6. Key Findings

### 6.1 MinSlope Must Stay Fixed (28 pts)

Fixed MinSlope = 28 pts has a beneficial non-linear property:

| Index Level | 28 pts as % | Effect |
|-------------|-------------|--------|
| 9,000  | 0.31%/bar | Very strict — blocks weak signals at low levels |
| 20,000 | 0.14%/bar | Moderate filtering |
| 40,000 | 0.07%/bar | Relaxed — allows entries at high levels |

This asymmetry PROTECTS the strategy: it's naturally conservative when index
is low (smaller moves, noisier signals) and permissive when index is high
(larger absolute moves, cleaner signals). Percentage conversion linearizes
this relationship and destroys the protection.

This is fundamentally DIFFERENT from the v0.6 ATR-based approach which
failed for a different reason (volatility != price level). MinSlope's
non-linearity is a feature, not a bug.

### 6.2 QS_MaxLoss Percentage Works

Original fixed QS_MaxLoss = 60 pts behavior:

| Index Level | 60 pts as % | Problem |
|-------------|-------------|---------|
| 9,000  | 0.67% | Too loose — slow to cut losses |
| 20,000 | 0.30% | Reasonable |
| 40,000 | 0.15% | Too tight — cuts winning trades early |

New QS_MaxLoss_Pct = 0.250% behavior:

| Index Level | 0.250% as pts | vs old 60 pts |
|-------------|---------------|---------------|
| 9,000  | 22.5 pts | Tighter (cuts losses faster) |
| 20,000 | 50 pts   | Slightly tighter |
| 40,000 | 100 pts  | Looser (lets winners breathe) |

This makes economic sense: the QuickStop's job is to exit when the trade
shows immediate adverse movement. "Immediate adverse" should scale with
price level, not be a fixed absolute amount.

### 6.3 QuickStop Mechanism Detail

QuickStop monitors the first 4 bars (20 minutes on 5M chart) after entry:

- **P1a Loss-based**: At any bar, if unrealized loss > EntryPrice * 0.250%,
  exit immediately. At 40,000 index: triggers at 100 pts loss (vs old 60 pts).
  At 10,000: triggers at 25 pts (vs old 60 pts).

- **P1b Time-based**: After 4 bars (20 min), if Close >= EntryPrice (short
  position has no profit), exit. This catches trades where price doesn't move
  against the short direction — a sign the signal was wrong.

### 6.4 What v1.7.1 Changed vs v1.6.2

| Aspect | v1.6.2 | v1.7.1 (QS=0.250%) | Impact |
|--------|--------|---------------------|--------|
| Net Profit | +2,007K | +2,413K | +20.2% |
| PF | 1.775 | 1.773 | Flat (quality maintained) |
| MDD | -456K | -561K | +23% larger (tradeoff) |
| Net/MDD | 4.40 | 4.30 | Flat (risk-adjusted held) |
| Trades | 112 | 122 | +8.9% (slight increase) |
| Avg Trade | 17,918 | 19,780 | +10.4% (better per-trade) |
| ROA | — | 524.2% | Strong |
| Annualized | — | 15.97% | Strong |

**Net effect**: +20% more profit with essentially the same risk-adjusted
efficiency. MDD is larger in absolute terms but proportional to the higher
net profit.

## 7. Selected Configuration

**v1.7.1 with QS_MaxLoss_Pct = 0.250** is the accepted candidate.

Changes from v1.6.2:
- Input: `QuickStop_MaxLoss_Pts (60)` -> `QS_MaxLoss_Pct (0.25)`
- Section 10 P1a: `v_Loss > QuickStop_MaxLoss_Pts` -> `v_Loss > EntryPrice * QS_MaxLoss_Pct / 100`
- All other parameters, logic, and signal labels unchanged.

File: `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.7.1.pla`

## 8. Archived (Rejected)

- `archive/S16_S_MACrossShort_v1.7_REJECTED.pla` — MinSlope% only
- `archive/S16_S_MACrossShort_v1.7.2_REJECTED.pla` — Both parameters %
- `archive/V17_RESEARCH_CONCLUSION_20260729.md` — Summary conclusion

## 9. Research Methodology Template

This research followed a systematic process that can be reused for future
parameter conversion or optimization studies:

### Step 1: Isolate Variables
Create separate variants that each change ONE parameter. Never test combined
changes without first understanding individual effects. Even if you plan to
change both, isolating them reveals which change helps and which hurts.

### Step 2: Calculate Equivalent Defaults
Convert fixed-point defaults to percentage using current index level as
reference. This gives a fair starting point for comparison.

### Step 3: Run Unoptimized First
Run all variants with equivalent defaults against baseline. This reveals the
STRUCTURAL impact of the conversion. BUT — do not reject based on
unoptimized results alone. The default may not be the best configuration.

### Step 4: Optimize Each Variant Fairly
- Single parameter: exhaustive sweep (test every combination)
- Two parameters: GA optimization (cover the 2D space efficiently)
- Set ranges wide enough to include both tighter and looser than original

### Step 5: Evaluate on Multiple Criteria
Never select on net profit alone. Check:
1. Net Profit (absolute improvement)
2. Profit Factor (quality of edge)
3. Trade count (structural consistency)
4. MDD and Net/MDD ratio (risk-adjusted efficiency)
5. Parameter robustness (neighbors produce similar results?)
6. Exit signal distribution (does the strategy still behave the same way?)

### Step 6: Verify Parameter Robustness
A valid parameter should have a "plateau" — nearby values should produce
similar results. A sharp peak means the parameter is fragile and likely
curve-fitted. The v1.7.1 sweet spot (0.225-0.275, within 2.2%) passed
this test.

### Step 7: Archive with Full Documentation
Move rejected variants to archive/ with REJECTED suffix. Create a
conclusion document recording what was tested, what worked, what failed,
and WHY. The "why" is critical — it prevents future researchers from
re-testing the same failed approach.

## 10. Open Issue: Re-Entry Stop Loss

Deferred from this research phase. The re-entry mechanism uses the same
SL code path as main entry (ATR x 4.0 capped by SL_Pct = 1.0%), but ATR
is inflated post-exit, creating wider stops. Documented max loss ratio:
re-entry can lose up to 1.78x vs main entry. This will be addressed in
the next research phase.
