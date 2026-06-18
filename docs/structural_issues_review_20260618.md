# Cross-Strategy Structural Issues Review (2026-06-18)

**Context**: After completing P3b Immediate Stop Guard across all 6 strategies,
user requested a full structural issue audit from an institutional perspective.

---

## Resolved Structural Issues

| # | Issue | Solution | Enforcement |
|---|-------|----------|-------------|
| 1 | Settlement day position risk | Settlement_Flat module | CLAUDE.md Rule #11 + Constitution |
| 2 | Holiday position risk | HolidayFlat_v3 module | Per-strategy changelog |
| 3 | Entry-bar stop gap (IOG=false) | P3b SetStopLoss | CLAUDE.md Rule #12 (2026-06-18) |

---

## Open Structural Issues (A-E)

### A. Layer 3 — Broker-side hard stop — RESOLVED BY USER

**User decision**: Cloud computer (always-on) eliminates hardware/network
failure risk. MC engine-level SetStopLoss sufficient as long as MC process
is running. No further action needed.

### B. Cross-strategy directional concentration — ACCEPTED BY DESIGN

**User decision**: L1/L3/L5 (Long) and L2/L4 (Short) each capture different
market conditions. Simultaneous positions in the same direction means the
market genuinely fits all those strategies. No portfolio-level position cap
needed at this stage.

### C. Gap-through stop orders — NEEDS FURTHER WORK

**Problem**: Stop orders fill at open price when gapped through. A stop at
23,000 with open at 22,800 = 200 pts additional unintended loss. SetStopLoss
does NOT fix this — it's an exchange-level structural limitation.

**User's current approach**: Exit as early as possible at session open to
minimize exposure.

**Institutional approaches discussed**:

1. **Volatility-adaptive stop width** (ALREADY IN PLACE)
   - ATR-based SL naturally widens in high-vol → reduces gap-through probability
   - All 6 strategies already use this

2. **Time-window exposure management** (PARTIALLY IN PLACE)
   - HolidayFlat: exits before known closures ✅
   - Settlement_Flat: exits before settlement ✅
   - NOT COVERED: daily 05:00→08:45 overnight gap window for L1-L5

3. **Disaster Stop — maximum single-trade loss hard cap** (NEXT PRIORITY)
   - Concept: absolute loss ceiling regardless of gap size
   - Normal SL = ~150 pts; Disaster Stop = ~300 pts (2x normal)
   - If open already beyond Disaster Stop → immediate market exit
   - Implementable in MC with additional if-check on entry bar
   - **This is the recommended next structural optimization**

4. **Options hedging** (USER DECISION, NOT CODE)
   - OTM PUT/CALL for tail risk protection
   - Requires separate options account; personal trading decision

### D. MC crash / recovery SOP — NEEDS DOCUMENTATION

**User assessment**: Limited knowledge on how to handle this.

**Proposed solution (3 layers)**:

1. **Prevention**: Windows Task Scheduler auto-restart MC on crash
2. **Reconciliation**: After restart, compare MC position vs broker actual
   position. MC has manual position sync if mismatch detected.
3. **Checklist document**: Step-by-step SOP for MC abnormal restart.
   Ensures no steps are missed under stress.

**Status**: Not yet written. Low code complexity, mainly documentation.

### E. Portfolio monitoring dashboard — FUTURE PROJECT

**User vision**: GitHub Pages website with:
- Automated performance data updates
- Real-time entry/exit status
- Charts and equity curves

**Status**: Acknowledged as valuable but separate from current structural
safety work. User already has Chip Radar TW on GitHub Pages as precedent.

---

## Priority Queue (next actions)

1. **C-3: Disaster Stop hard cap** — next structural optimization
   - Same defense system as P3b, natural extension
   - Pure code solution, no external dependencies
   - Design discussion needed before implementation

2. **D: MC crash recovery SOP** — documentation task
   - Can be written in parallel with C-3
   - Low risk, high value for operational resilience

3. **E: Portfolio dashboard** — separate project scope
   - Deferred until safety-critical items complete

---

## Session Handoff Notes (for continuation from home)

- All 6 strategies have P3b SetStopLoss committed and pushed
- CLAUDE.md Rule #12 is in place
- Commits: 339ef8b (L1) → a79db05 (S1) → a939088 (L2) → d49dea7 (L3/L4/L5) → 61c81c2 (CLAUDE.md)
- S2 v0.6 still needs MC12 backtest (remove old strategy, reload .pla, verify inputs)
- No code changes pending — all discussion items need design-first approach
