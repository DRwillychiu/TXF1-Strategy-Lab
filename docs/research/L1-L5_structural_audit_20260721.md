# L1-L5 Full Structural Audit — 15 Consolidated Problems

- **Audit date**: 2026-07-21
- **Scope**: All 5 live strategies (L1 V2.7, L2 V5.2, L3 v14.1, L4 v14.4, L5 v19.8)
- **Method**: 3-way parallel subagent full-code audit (L1+L2 / L3+L4 / L5)
- **Raw findings**: 62 (L1: 12, L2: 11, L3: 12, L4: 11, L5: 13, Cross-strategy: 3)
- **Consolidated**: 15 independent structural problems
- **Context**: Account 300K -> 236K NTD (-21.3%), 20% circuit breaker triggered, boss-identified "small win big loss" pattern
- **Prerequisite**: `docs/research/portfolio_DD_postmortem_202607_L1-L5.md` (2026-07-17 3-layer diagnosis)

---

## Summary

| Severity | Count | Direct big-loss contributors |
|----------|------:|:-:|
| CRITICAL | 6 | 6/6 |
| HIGH     | 5 | 3/5 |
| MODERATE | 4 | 0/4 |
| **Total** | **15** | **9** |

**Root cause chain**: Fixed lot sizing (P1) + permissive OR filters in decline (P2) + no portfolio loss cap (P3) + ATR stops widening in high vol (P4) = guaranteed big losses during volatile regimes. All 5 strategies share this structure.

---

## TIER 1: CRITICAL — Direct cause of big losses (fix first)

### P1 — No risk normalization (ALL 5 strategies)

**Raw findings**: L1-F1, L2-F1, L3-F3, L4-F3, L5-F2

All 5 strategies use fixed 1 lot with zero position sizing. No calculation of risk-per-trade vs account equity exists anywhere. When ATR widens (high volatility), dollar risk per trade scales linearly upward while lot size stays fixed. At account 236K:

| Strategy | ATR formula | Normal stop | High-vol stop | % of 236K (high vol) |
|----------|-------------|-------------|---------------|---------------------|
| L1 | Max(ATR45M*1.5, D_ATR*0.5) | 150-250 pts | 300-450 pts | 25-38% |
| L2 | DC_Lower + ATR*1.1 | ~155 pts | 310-465 pts | 26-39% |
| L3 | Box_Btm - ATR(9)*3.0 | ~150 pts | 300-450 pts | 25-38% |
| L4 | Locked_Top + ATR(60)*2.0 | 80-100 pts | 140-200 pts | 12-17% |
| L5 | Mid/Bot - ATR(35)*4.5 | 180 pts | 360-450 pts | 30-38% |

**Fix direction**: Pre-entry risk budget gate. Calculate `stop_distance * point_value * lots / account_equity`. If exceeds budget (e.g. 2%), skip the trade. This preserves ATR stop placement (noise filter) while capping NTD risk. Does NOT touch exit logic (Rule 17 compliant).

### P2 — Filter asymmetry: longs OR, shorts locked (L1 L2 L3 L4)

**Raw findings**: L1-F4, L2-F3, L3-F1, L4-F1, XS-F1

Long-side filters use OR logic (permissive in early declines):
- L1: Weekly `Close > W20 OR Close > W60` (L1_TrendLong.pla:340-341)
- L3: Daily `Close > MA20 OR Close > MA60` (L3_ConsolidationLong.pla:277-281)

Short-side filters are structurally locked:
- L2: 13-week SMA, only updates on Friday 12:45 rollover -> 2026 full year = 0 trades (L2_TrendShort.pla:395-401)
- L4: Macro Block `(Close>MA60 AND MA60 rising) OR (MA20>MA60)` -> golden cross residual locks out shorts for weeks into declines (L4_ConsolidationShort.pla:425-431)

**Result**: During early-to-mid declines, portfolio is forced net-long (3 long strategies open, 2 short strategies locked). July 2026 = textbook case.

**Fix direction**: Regime brake (cross-strategy). Options: (a) change OR to AND on long filters (needs backtest for Top-10 impact), (b) add ATR/VIX regime gate that blocks all long entries when vol exceeds threshold, (c) speed up L2/L4 filter update frequency.

### P3 — No portfolio-level loss limits (ALL 5 strategies)

**Raw findings**: L1-F3, L2-F2, L3-F5, L4-F5

No strategy has any awareness of:
- Daily cumulative P&L
- Weekly cumulative P&L
- Cross-strategy aggregate exposure
- Number of open positions across strategies

The 20% account circuit breaker exists only as a manual rule (position_sizing_and_capacity.md:208-213), not in strategy code. Multiple strategies can enter simultaneously, compounding total risk to 42%+ of account. Single-day multi-strategy stop cascades have no programmatic brake.

**Fix direction**: Portfolio-level daily/weekly loss cap. Implementation options: (a) shared global variable in MC, (b) external risk monitor, (c) per-strategy daily loss counter (simpler but per-strategy, not aggregate).

### P4 — ATR multiplied stops create outsized per-trade risk (L1 L3 L5)

**Raw findings**: L1-F2, L3-F2, L5-F4

ATR multipliers range from 1.5x (L1) to 4.5x (L5). At high volatility, single-trade stop distances reach 300-450 points. Combined with P1 (fixed lot sizing), a single stop hit in high vol can breach the 20% circuit breaker on its own.

L3's ATR(9) on 15M is particularly reactive — only 2.25 hours of memory. Short-term volatility spikes produce outsized frozen stop values.

**Fix direction**: P1's risk budget gate already covers this — if stop distance * lots exceeds budget, the trade is skipped. No need to change ATR calculation itself (it serves a valid noise-filtering purpose). The multiplier values may have overfitting concern but need separate parametric analysis.

### P5 — L5 3-tier trail system dead at 1 contract (L5 only)

**Raw findings**: L5-F1, L5-F12

`ScaleOut_Size = Round(1 * 0.4, 0) = 0` -> TP limit exits never fire -> `CurrentContracts` never drops below `MaxContracts` -> entire Stage 2/3 trail block (L5_BreakoutLong.pla:611-667) is unreachable.

**Production L5 has ZERO dynamic trailing stop.** The MFE tracking variables compute every bar but are never consumed in any live code path. The "God Mode" trail engine is purely decorative at current sizing.

Exit mechanisms actually available at 1 contract:
1. Initial stop (Box_Btm/Mid - Frozen_ATR_Buffer)
2. Time stop (31 bars = ~7.75 hours)
3. BreakExit (box invalidation)
4. Settlement/Holiday/Registry flat

**Fix direction**: Rewrite trail activation path for 1-contract operation. Must preserve Top-10 mega-winners (88% of net profit). The existing trail multipliers (3.0/2.0/1.5/0.8) need re-evaluation for single-lot exit mechanics.

### P6 — L3 v14.1 deployed without review (L3 only)

**Raw findings**: L3-F6

L3_ConsolidationLong_review.md covers v13.2B (dual-leg, 431 trades). The deployed code is v14.1 — a complete architecture redesign:
- Removed dual-leg split (CL_Entry_Bot/CL_Entry_Mid merged)
- Added matrix dimensions (Entry_Zone_Pct, Min_Box_ATR, Swing_Lookback)
- Changed targets from fixed box levels to dynamic swing high
- Reduced trades from 431 to 332
- Changed PF from 1.187 to 1.470

Deployed 7/3-7/4, first real trade hit July 7 crash (-1,077 pts, 8th largest single-day TWSE drop). Risk characteristics of the production version are completely unknown and unvalidated.

**Fix direction**: Immediate — stop or rollback to v13.2B. Then complete v14.1 review before re-deployment.

**Status (2026-07-17 handoff)**: Listed as high-priority action item. Execution NOT VERIFIED as of 2026-07-21.

---

## TIER 2: HIGH — Amplifies losses

### P7 — No cooldown mechanism (L1 L3 L5)

**Raw findings**: L1-F5, L2-F6, L3-F4, L5-F5

L1, L3, L5 have no cooldown between trades. After stop-out, entry conditions can re-qualify immediately.

L5 quantification (v19.9 archive): 39 re-entry clusters containing 102 of 182 trades (56%). 27 losing clusters totaling -719,400 NTD. Worst cluster: 6 entries at identical price @20249 over 2 days, 5 losses, net -44,000 NTD.

L4 has `Cooldown_Bars(8)` = 2 hours, which is the only cooldown in the live portfolio.

**Fix direction**: Add `Cooldown_Bars` input to L1/L3/L5. L5's v19.9 Cooldown-D design (same-box ban + new-box delay) was designed but rejected with the rest of v19.9 — the cooldown component could be extracted independently.

### P8 — No consecutive loss breaker (ALL 5 strategies)

**Raw findings**: L1-F5, L5-F6

No strategy tracks consecutive losses or has an automatic pause mechanism. L1's maximum observed consecutive loss streak is 18 trades (-394,600 NTD). The only circuit breaker is the manual 20% account rule.

**Fix direction**: Per-strategy consecutive loss counter. After N consecutive SL exits, pause for M bars or until next session. Requires careful calibration to avoid blocking recovery entries.

### P9 — L5 Stage 1 zero profit protection (L5 only)

**Raw findings**: L5-F3

Stage 1 (full position, pre-breakout) has MFE tracking but no mechanism to protect unrealized gains. The SP module (5 variants) ALL FAILED because they killed Top-10 mega-winners. Stage1_BE (v19.9) was rejected after -19K MC9 A/B result.

Quantification: 58 trades with MFE > 0 ended at or below zero, totaling 1,826,000 NTD of wasted profit. Worst case: 2024-05-03, MFE +244 pts -> exit at breakeven -10 pts.

**Fix direction**: Out-of-ideas on exit side (3 independent attempts failed, direction permanently closed per feedback_trend_let_profits_run.md). Partially mitigated if P5 (trail rewrite) activates a 1-contract trail path. Otherwise, this is accepted structural cost of the breakout thesis.

### P10 — L4 CS_BreakExit structural loss = 158% of net profit (L4 only)

**Raw findings**: L4-F4

20 trades, 0% win rate, -377,800 NTD = 158% of strategy's net profit (+239K). v14.5 attempted 4 configurations to fix -> all failed. Codified as unpatchable thesis cost.

**Fix direction**: Strategy-level existential question. If the structural cost exceeds net profit, the strategy's viability needs re-evaluation. However, this is a long-term question, not an immediate fix.

### P11 — Capital inadequacy (portfolio level)

**Raw findings**: XS-F3

Individual strategy MDDs vs 236K account:
- L1: -548K (232% of account)
- L3: -379K (161%)
- L4: -240K (102%)
- L5: -202K (86%)
- L2: -269K (114%)
- Combined L1-L5: -375K (159%)

Repo's own allocation docs state <300K = "do not trade live". Recommended capital for full portfolio = 1.5M NTD.

**Fix direction**: Either increase capital or reduce strategy count. At 236K, the maximum defensible allocation (per repo docs) is 1-2 strategies at minimum lot size, not 5 strategies.

---

## TIER 3: MODERATE — Indirect risk / code quality

### P12 — L2/L4 trailing stop uses unfrozen ATR (L2 L4)

**Raw findings**: L2-F4, L4-F8

L2's TSL buffer recalculates with current ATR every bar. L4's trail uses current ATR by design. During volatility spikes, trail protection loosens (stops move further from price), giving back more profit. L2's review flagged this for A/B testing.

### P13 — Settlement day detection missing holiday shifts (L3 L4 L5)

**Raw findings**: L3-F10, L4-F7, L5-F10

All three strategies detect settlement as `DayOfWeek=3 AND DayOfMonth>=15 AND <=21`. When a national holiday falls on the 3rd Wednesday, TAIFEX shifts the settlement date. The heuristic misses these shifted dates. Per feedback_settlement_holiday_rule.md, this is a known gap.

### P14 — P3b SetStopLoss vs Frozen SL one-bar mismatch (L2 L3 L5)

**Raw findings**: L2-F9, L3-F8, L5-F9

P3b fires on bar N using bar N's values. Frozen SL locks on bar N+1 using bar N+1's values. In fast markets, ATR can change between bars, creating brief guard/stop divergence. Not a primary risk but could cause unexpected exit prices in extreme moves.

### P15 — Code quality issues (L2 L3 L5)

**Raw findings**: L2-F7, L3-F7, L5-F11, L5-F12, L5-F13, L3-F11, L4-F10

- IOG not explicitly declared in L2 and L3 (MC default is false, but L1/L4 declare it explicitly)
- L5 has ~130 lines of dead code (SP module permanently OFF + ScaleOut at 1 contract = 0)
- L5 file is 696 lines vs 150-line project limit (Rule 10)
- L3 MC load name `STRATEGY_WILLY_LONG_C` violates `STRATEGY_GEN_` convention
- L4 MC load name `STRATEGY_WILLY_SHORT_CTEST2` contains "TEST" in production

---

## Recommended Attack Sequence

| Step | Problem | Action | Type |
|------|---------|--------|------|
| 1 | P6 | Stop/rollback L3 v14.1 in MC9 | Operational (no code change) |
| 2 | P1 | Design spec: pre-entry risk budget gate | Design spec -> implementation |
| 3 | P3 | Design spec: portfolio-level daily loss cap | Design spec -> implementation |
| 4 | P2 | Backtest: OR->AND filter impact on Top-10 retention | Research -> design spec |
| 5 | P5 | Rewrite L5 trail path for 1-contract | Code change (audit required) |
| 6 | P7+P8 | Add cooldown + consecutive loss breaker | Code change (audit required) |

**Constraint**: All code changes to .pla files require Rule 4 (audit: data x logic x position x backtest limits x cross-machine paths) + user physical verification (compile + runtime + log). No code change can be declared "done" without MC9 verification.

**Constraint**: P9 (Stage 1 profit protection) is blocked — 3 independent exit-side attempts failed and the direction is permanently closed. Partially addressed by P5 if trail rewrite succeeds.

**Constraint**: P11 (capital inadequacy) is a business decision, not a code fix.

---

## Appendix: Raw Finding Cross-Reference

| Consolidated | Raw Findings |
|-------------|-------------|
| P1 | L1-F1, L2-F1, L3-F3, L4-F3, L5-F2 |
| P2 | L1-F4, L2-F3, L3-F1, L4-F1, XS-F1 |
| P3 | L1-F3, L2-F2, L3-F5, L4-F5 |
| P4 | L1-F2, L3-F2, L5-F4 |
| P5 | L5-F1, L5-F12 |
| P6 | L3-F6 |
| P7 | L1-F5, L2-F6, L3-F4, L5-F5 |
| P8 | L1-F5, L5-F6 |
| P9 | L5-F3 |
| P10 | L4-F4 |
| P11 | XS-F3 |
| P12 | L2-F4, L4-F8 |
| P13 | L3-F10, L4-F7, L5-F10 |
| P14 | L2-F9, L3-F8, L5-F9 |
| P15 | L2-F7, L3-F7, L5-F11, L5-F13, L3-F11, L4-F9, L4-F10 |

## Unverified Items (carried from 2026-07-17 handoff)

- [ ] 20% circuit breaker execution (lots reduced?)
- [ ] L3 v14.1 stop/rollback execution
- [ ] MC9 July trade detail export (exit label attribution)
- [ ] Contract type / lots confirmation (micro x2 vs mini x2)
- [ ] MC9 running version = repo HEAD confirmation
- [ ] Account current balance (236K was 7/17 figure, now 7/21)
