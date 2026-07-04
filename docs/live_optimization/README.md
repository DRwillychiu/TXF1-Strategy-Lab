# Live Strategy Optimization

This folder tracks verification and optimization work on **live (deployed) strategies**.

Distinct from `strategies/research/` (new strategy development) — this is for
upgrading architecture, tuning parameters, or redesigning existing live strategies
that are already deployed on MC9.

## Active

| Strategy | Version | Status | Folder |
|----------|---------|--------|--------|
| L4 ConsolidationShort | v14.4 review | CLOSED: V15.0 failed + V14.6 AdaptSL failed, v14.4 retained | L4_v15_matrix_range_capture/ |

## Completed

| Strategy | Version | Date | Result |
|----------|---------|------|--------|
| L3 ConsolidationLong | v13.4 -> v14.1 | 2026-07-04 | DEPLOYED: +194% net, PF 1.470, Net/MDD 5.41 |
| L1 TrendLong | v2.6 -> v2.7 | 2026-07-02 | Plan A (SP 500) deployed, Plan C rejected |
| L2 TrendShort | v5.2 review | 2026-07-02 | No changes needed (best in portfolio) |
