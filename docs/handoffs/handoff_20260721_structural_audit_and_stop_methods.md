# Handoff 2026-07-21 — L1-L5 Structural Audit + Stop Methods Analysis (Laptop -> Desktop)

## 1. Status

- **Full structural audit completed**: 3-way parallel subagent audit of all 5 live strategies.
- 62 raw findings -> **15 consolidated problems** (6 CRITICAL, 5 HIGH, 4 MODERATE).
- Stop methods analysis completed: per-strategy table of alternative initial stop methods beyond ATR.
- **No .pla code changes** — pure research and discussion.
- User confirmed: 2-day optimization plan starting from this analysis.

## 2. Changed

- New: `docs/research/L1-L5_structural_audit_20260721.md` (15 consolidated problems, priority matrix)
- New: `docs/research/L1-L5_stop_methods_analysis_20260721.md` (per-strategy stop method options)
- New: this handoff
- No .pla modifications

## 3. State

### Structural Audit (15 Problems)

**TIER 1 CRITICAL (P1-P6):**
- P1: No risk normalization — all 5 strategies, fixed lots x ATR scaling = uncontrolled NTD risk
- P2: Filter asymmetry — longs OR (permissive), shorts strict/locked, forced net-long in declines
- P3: No portfolio-level loss limits — no daily/weekly cap, no cross-strategy awareness
- P4: ATR stops widen in high vol — covered by P1 fix (risk budget gate)
- P5: L5 trail dead at 1 contract — ScaleOut=Round(1*0.4,0)=0, trail block unreachable
- P6: L3 v14.1 deployed without review — risk characteristics unknown

**Work packages:**
- **Package A (P1+P3+P4)**: Risk management module — pre-entry risk budget gate + daily loss cap. All 5 strategies. Does not touch exit logic.
- **Package B (P5)**: L5 trail rewrite for 1-contract operation.
- **Package C (P2)**: Filter research — OR->AND impact on Top-10. Requires backtest.

### Stop Methods Analysis

Per-strategy analysis of alternative initial stop methods. Key findings:
1. Structure-based stops (swing/box/session) = universal best inner layer for all 5 strategies
2. Fixed % only fits L3/L4 (no fat-tail dependency). Dangerous for L5 (88% profit in Top-10).
3. Candlestick patterns fit 15M strategies (L3/L4/L5), not 45M/60M (L1/L2).
4. L3 = safest to add inner stops (no fat-tail dependency, clear invalidation points).
5. L5 benefits most from stage-based stops (Stage 1 tight, Stage 2 trail via P5 fix).

**User instruction**: Next session should start by presenting the full stop methods analysis tables for continued deep discussion and confirmation.

## 4. Decisions

- Work package grouping confirmed by user: P1+P3+P4 = one module (Package A).
- P2, P5 are separate packages requiring independent research/implementation.
- All code changes require Rule 4 audit + user MC9 physical verification.
- Rule 17 multi-layer architecture is the framework — ATR remains outermost layer.
- "Target profile = small win + big win + small loss" saved to memory (feedback_target_profile_small_win_big_win.md).

## 5. Next (Desktop session)

1. **[FIRST]** Present stop methods analysis tables (user explicit request: "show all tables immediately after pulling latest git").
2. **[Discussion]** User deep review and confirmation of method selection per strategy.
3. **[Design spec]** Write Package A spec: risk budget gate + daily loss cap + selected inner stop methods.
4. **[Still pending from 7/17]** Confirm: L3 v14.1 running? Circuit breaker executed? Contract type/lots? MC9 July trade export?

## 6. Files

- `docs/research/L1-L5_structural_audit_20260721.md` — 15 consolidated problems, priority matrix
- `docs/research/L1-L5_stop_methods_analysis_20260721.md` — per-strategy stop method analysis
- `docs/research/portfolio_DD_postmortem_202607_L1-L5.md` — prior: 3-layer DD diagnosis (7/17)
- `docs/handoffs/handoff_20260721_structural_audit_and_stop_methods.md` — this file

## 7. Git

- Start: `f6eb949` (S17_S SwingShort60M)
- This session: `4e29677` (structural audit) + this commit (stop methods + handoff)
- Untracked: various `.bak_*` files (intentionally not committed)
