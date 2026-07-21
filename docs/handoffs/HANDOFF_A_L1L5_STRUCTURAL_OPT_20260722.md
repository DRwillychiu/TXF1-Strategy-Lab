# Handoff A: L1-L5 Structural Optimization Sprint

**Date**: 2026-07-22
**From**: Desktop main session
**To**: Parallel session A (dedicated to L1-L5 live strategy optimization)
**Repo**: `C:/Users/User/Desktop/TXF1-Strategy-Lab/` (git main, latest commit `b4cd66b`)

---

## 1. Mission

You are continuing an L1-L5 live strategy structural optimization sprint. A full 3-way parallel audit was completed on 2026-07-21 (laptop session), producing 62 raw findings consolidated into 15 problems. Your job is to:

1. **Present the stop methods analysis tables** to the user for deep review (user explicit request from handoff)
2. **Discuss and confirm** method selection per strategy with the user
3. **Design Package A spec**: risk budget gate + daily loss cap + selected inner stop methods
4. **Address pending items from 7/17**: L3 v14.1 status, circuit breaker execution, contract type/lots, MC9 July trade export

---

## 2. Key Files to Read First

| File | Content |
|------|---------|
| `docs/research/L1-L5_structural_audit_20260721.md` | **START HERE** — 15 consolidated problems, priority matrix, work packages |
| `docs/research/L1-L5_stop_methods_analysis_20260721.md` | Per-strategy stop method analysis tables (user wants these shown immediately) |
| `docs/handoffs/handoff_20260721_structural_audit_and_stop_methods.md` | Full handoff from laptop session with decisions and next steps |
| `docs/research/portfolio_DD_postmortem_202607_L1-L5.md` | Prior: 3-layer DD diagnosis from 7/17 session |

---

## 3. The 15 Problems (Summary)

### TIER 1 CRITICAL (P1-P6)
- **P1**: No risk normalization — fixed lots x ATR scaling = uncontrolled NTD risk (ALL 5 strategies)
- **P2**: Filter asymmetry — longs OR (permissive), shorts strict/locked, forced net-long in declines (ALL 5)
- **P3**: No portfolio-level loss limits — no daily/weekly cap, no cross-strategy awareness (ALL 5)
- **P4**: ATR stops widen in high vol — covered by P1 fix (risk budget gate) (ALL 5)
- **P5**: L5 trail dead at 1 contract — ScaleOut=Round(1*0.4,0)=0, trail block unreachable (L5 only)
- **P6**: L3 v14.1 deployed without review — risk characteristics unknown (L3 only)

### TIER 2 HIGH (P7-P11)
- P7: No drawdown recovery mode
- P8: L1/L2 45M+60M bars too coarse for stop precision
- P9: No intraday momentum filter
- P10: No volatility regime adaptation
- P11: No correlation-aware position sizing

### TIER 3 MODERATE (P12-P15)
- P12: Hardcoded time windows
- P13: No partial profit-taking framework
- P14: No market microstructure awareness
- P15: No systematic performance monitoring

### Work Packages (confirmed by user)
- **Package A (P1+P3+P4)**: Risk management module — pre-entry risk budget gate + daily loss cap. All 5 strategies. Does NOT touch exit logic.
- **Package B (P5)**: L5 trail rewrite for 1-contract operation.
- **Package C (P2)**: Filter research — OR->AND impact on Top-10. Requires backtest.

---

## 4. Stop Methods Analysis Key Findings

1. Structure-based stops (swing/box/session) = universal best inner layer for all 5 strategies
2. Fixed % only fits L3/L4 (no fat-tail dependency). Dangerous for L5 (88% profit in Top-10).
3. Candlestick patterns fit 15M strategies (L3/L4/L5), not 45M/60M (L1/L2).
4. L3 = safest to add inner stops (no fat-tail dependency, clear invalidation points).
5. L5 benefits most from stage-based stops (Stage 1 tight, Stage 2 trail via P5 fix).

---

## 5. User Decisions Already Made

- Work package grouping: P1+P3+P4 = one module (Package A)
- P2, P5 separate packages requiring independent research
- All code changes require Rule 4 audit + user MC9 physical verification
- Rule 17 multi-layer architecture is the framework — ATR remains outermost layer
- Target profile = small win + big win + small loss (saved to memory)

---

## 6. Constraints and Rules

- **Language**: Conversational replies in Traditional Chinese; code/identifiers in English
- **Git discipline**: "update git" = commit + push always (never local-only commit)
- **No break questions**: User manages own rest schedule; 100% effort + 100% accuracy
- **These are MC9 LIVE strategies** (real money) — any .pla changes require extreme caution
- All 19 rules in CLAUDE.md apply (especially Rule #11 Settlement, #12 SetStopLoss, #15 ASCII, #17 multi-layer SL)
- Read CLAUDE.md at repo root for full rule set

---

## 7. Strategy Quick Reference (L1-L5)

| Strategy | Type | Timeframe | Direction | Status |
|----------|------|-----------|-----------|--------|
| L1 TrendLong | Trend following | 45M | Long only | MC9 live |
| L2 TrendShort | Trend following | 60M | Short only | MC9 live |
| L3 ConsolidationLong | Mean reversion | 15M | Long only | MC9 live (v14.1 unreviewed) |
| L4 ConsolidationShort | Mean reversion | 15M | Short only | MC9 live |
| L5 BreakoutLong | Breakout | 15M | Long only | MC9 live |

All strategies located in `strategies/live/*.pla` with corresponding `_annotated.md` and `_review.md`.

---

## 8. Immediate Action

**Step 1**: Read `docs/research/L1-L5_stop_methods_analysis_20260721.md` and present the full tables to the user.
**Step 2**: Facilitate deep discussion on method selection per strategy.
**Step 3**: Based on confirmed selections, begin Package A design spec.

Do NOT modify any .pla files without explicit user approval. This is research and design phase first.
