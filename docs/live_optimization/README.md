# Live Strategy Optimization

This folder tracks verification and optimization work on **live (deployed) strategies**.

Distinct from `strategies/research/` (new strategy development) — this is for
upgrading architecture, tuning parameters, or redesigning existing live strategies
that are already deployed on MC9.

## Active

(none)

## Completed

| Strategy | Version | Date | Result |
|----------|---------|------|--------|
| L5 BreakoutLong | v19.8 review | 2026-07-05 | CLOSED: v19.9 Cooldown-D+GA Trail FAILED (PF 1.03 vs prod 1.85), Stage1_BE FAILED (PF<1.0), v19.8 production retained |
| L4 ConsolidationShort | v14.4 review | 2026-07-04 | CLOSED: V15.0 + V14.6 AdaptSL both failed, v14.4 retained, MC9 SP=0 confirmed |
| L3 ConsolidationLong | v13.4 -> v14.1 | 2026-07-04 | DEPLOYED: +194% net, PF 1.470, Net/MDD 5.41 |
| L1 TrendLong | v2.6 -> v2.7 | 2026-07-02 | Plan A (SP 500) deployed, Plan C rejected |
| L2 TrendShort | v5.2 review | 2026-07-02 | No changes needed (best in portfolio) |
