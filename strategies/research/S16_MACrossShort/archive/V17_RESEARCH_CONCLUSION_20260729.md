# S16_S v1.7 Research Conclusion (2026-07-29)

## Objective
Convert fixed-point parameters to percentage-based for cross-era consistency.
Two parameters tested: MinSlope (28 pts) and QS_MaxLoss (60 pts).

## Versions Tested

| Version | Change | Optimized Params |
|---------|--------|------------------|
| v1.7    | MinSlope -> MinSlope_Pct only | MinSlope_Pct GA sweep |
| v1.7.1  | QS_MaxLoss -> QS_MaxLoss_Pct only | QS_MaxLoss_Pct = 0.250 |
| v1.7.2  | Both changes combined | MinSlope_Pct=0.07, QS_Pct=0.40 |

## Results vs v1.6.2 Baseline (Net +2,007K, PF 1.775, MDD -456K, 112T)

| Version | Net Profit | vs Base | PF    | MDD     | Trades | Verdict  |
|---------|-----------|---------|-------|---------|--------|----------|
| v1.7    | +1,118K   | -44.3%  | 1.214 | -954K   | 310    | REJECTED |
| v1.7.1  | +2,413K   | +20.2%  | 1.773 | -561K   | 122    | ACCEPTED |
| v1.7.2  | +703K     | -65.0%  | 1.100 | -1,544K | 410    | REJECTED |

## Key Finding
MinSlope fixed 28 pts has a natural non-linear property: more restrictive at
low index levels (0.31%/bar @9K), less restrictive at high levels (0.06%/bar
@45K). This asymmetry PROTECTS the strategy. Percentage conversion destroys it.

QS_MaxLoss percentage conversion WORKS because the loss threshold SHOULD scale
with index level: 0.250% = 100 pts @40K (looser, lets winners run) vs 25 pts
@10K (tighter, cuts losses faster). Original fixed 60 pts was too tight at
high levels and too loose at low levels.

## Archived Files
- S16_S_MACrossShort_v1.7_REJECTED.pla (MinSlope% only)
- S16_S_MACrossShort_v1.7.2_REJECTED.pla (both%)
- v1.7.1 remains in research/ as the active candidate
