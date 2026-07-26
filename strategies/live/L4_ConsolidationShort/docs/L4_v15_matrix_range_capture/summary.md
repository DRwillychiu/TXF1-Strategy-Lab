# L4 Optimization Attempts (2026-07-04) — CLOSED

**Strategy**: L4 ConsolidationShort (STRATEGY_WILLY_SHORT_CTEST2)
**Status**: CLOSED — v14.4 retained as production, no changes deployed

---

## Attempt 1: V15.0 Matrix Range Capture — FAILED

Mirror L3 Matrix architecture (resistance zone short + swing low target).

**MC9 result**: Net -69K vs V14.4 +170K.
**Root cause**: L3 mirror structurally unsuitable for shorts.
Market asymmetry: support holds (L3 wins), resistance breaks (L4 loses).
CS_SL changed from trailing profit-capture (+448K) to fixed loss-limiter (-97.6K).

## Attempt 2: V14.6 Adaptive SL 0.20% — FAILED

Deep analysis found MAE < 0.20% of entry = 100% WR across 2021-2025.
Added `Adaptive_SL_Pct(0.20)` stop at entry * 1.002.

**MC9 result**: 88 trades, Net +175K (vs V14.4 +170K, delta +4.8K).
CS_AdaptSL fired 46 times, ALL losers (0% WR, -406K).
**Root cause**: 0.20% is a classification boundary, not a stop level.
Many winners temporarily exceed 0.20% MAE before recovering.
35 of 46 intercepted trades would have been profitable in V14.4.

## Attempt 3: V14.6 Adaptive SL MC9 Optimization — NO ALPHA

MC9 optimized Adaptive_SL_Pct to 1.40%.

**MC9 result**: 79 trades, Net +451K, PF 1.553, Sharpe 0.343.
Appears +281K better than V14.4 baseline, BUT:

**Confounding variable discovered**: V14.4 MC9 baseline had `SP_Trigger_Pts=50`
(enabled), while V14.6 code defaults `SP_Trigger_Pts=0` (disabled).
The improvement is entirely from SP being off (V14.2B production decision),
not from adaptive SL. CS_AdaptSL at 1.40% fired only 1 trade (-64K).

## Final Verdict

| Metric | V14.4 (SP=50) | V14.6 (0.20%) | V14.6 (1.40%) |
|--------|---------------|---------------|---------------|
| Net | +170,600 | +175,400 | +451,600 |
| Trades | 80 | 88 | 79 |
| WR | 60.0% | 21.6% | 43.0% |
| PF | 1.291 | 1.297 | 1.553 |
| MDD | -188,400 | -190,000 | -258,400 |

**Decision**: Roll back to V14.4. Adaptive SL has no alpha at any threshold.
User action: confirm MC9 has `SP_Trigger_Pts = 0` (V14.2B production setting).

## Lessons

- L24: MAE% classification boundary != stop-loss level. Trades that stay
  below the boundary are guaranteed winners, but many winners temporarily
  cross it. The boundary is a FILTER concept, not a STOP concept.
- L25: Always check MC9 input settings match .pla code defaults before A/B.
  SP_Trigger_Pts=50 in MC9 vs 0 in code created a confounding variable.
