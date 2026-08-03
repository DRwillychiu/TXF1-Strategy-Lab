# HANDOFF — S16_S v1.11.0 Profit-Taking Exit Review (2026-08-03)

## Status: Exit Chain Audit DONE, Profit-Taking Optimization NEXT

---

## 1. What Changed This Session

### True Breakeven Default Update
- `BE_Trigger_Pct` default: 0.10 -> **0.80** (commit `2cdc450`)
- MC12 sweep result: Pct 0.80 / Cost 5 = optimal
- Rationale: 0.10% triggered too easily (60/140 trades = 43%), most were noise -> loss on BE exit

### Dead Code Cleanup
- Removed `v_StopDist` (declared + assigned, never referenced) (commit `552ad33`)

### ATR Audit — All PASS
- All modules use `v_Frozen_ATR` / `v_Original_Frozen_ATR` correctly (v1.8.0 inheritance)
- Third-party independent verification: confirmed
- Exception: P7 Engine Guard uses raw `v_ATR` by design (engine-level, updates when flat)

---

## 2. Complete Exit Chain (10 mechanisms, audited)

| Priority | Name | Type | Trigger | Order | ExitFired | v1.11.0(0.80) Count |
|----------|------|------|---------|-------|-----------|---------------------|
| P0 | Kill/Registry/Holiday/Settlement | Compliance | Manual/calendar | Market | Yes | 0 |
| P0.5 | TailFlat | Compliance | Time >= 0440 daily | Market | Yes | 2 (2%) |
| P1a | QS_Loss | Stop-loss | Loss > EP * 0.25% | Market | Yes | 44 (34%) |
| P1b | QS_Time | Stop-loss | Bars >= 4 AND no profit | Market | Yes | 44 (34%) |
| P2 | ML_Exit | Stop-loss | 5-layer score while losing | Market | Yes | 0 (0%) |
| P3 | BE | Breakeven | Profit >= EP * 0.80% | Stop | No | 5 (4%) |
| P4 | GoldenCross | Neutral | ZLEMA fast x-over slow | Market | Yes | 5 (4%) |
| P5 | TimeStop | Neutral | Bars >= 24 (2hr) | Market | Yes | 27 (21%) |
| P6 | FrozenSL | Stop-loss | Price hits frozen ATR level | Stop | No | 2 (2%) |
| P7 | Engine Guard | Stop-loss | MC engine SetStopLoss | Engine | N/A | 0 (0%) |

### Architecture Summary
- **Stop-loss**: 5 layers (P1a, P1b, P2, P6, P7)
- **Breakeven**: 1 layer (P3, fixed at EntryPrice -5 pts, does NOT trail)
- **Neutral**: 4 layers (P0, P0.5, P4, P5)
- **Profit-taking**: 0 layers <-- GAP

---

## 3. Key Q&A Clarifications (this session)

1. **P0.5 TailFlat = daily, not weekend-only**. Fires every day at 04:40-05:00 to avoid crossing the 05:00-08:45 morning break.
2. **P7 Engine Guard vs P6 FrozenSL**: P7 is MC engine-level (`SetStopLoss`), fires intra-bar regardless of IOG setting. P6 is script-level stop order, only evaluated at bar close (IOG=False). P7 = last safety net.
3. **BE does NOT deactivate FrozenSL**: Both P3 (stop at EP-5) and P6 (stop at EP + frozen ATR dist) coexist. When BE activates, P3 stop (EP-5) is closer to current price than P6 stop, so P3 fires first. P6 becomes redundant but stays alive as safety net.
4. **GoldenCross and TimeStop are NOT profit-taking mechanisms**: They don't check P&L. They happen to harvest profit when the trade is winning, but provide zero "profit grows -> protection grows" logic.

---

## 4. Performance Data (4-version comparison)

| Metric | v1.7.1 | v1.8.1 | v1.11.0 (0.10) | v1.11.0 (0.80) |
|--------|--------|--------|----------------|----------------|
| NP | 2,074,000 | 2,413,200 | 1,300,800 | **2,478,000** |
| PF | 1.6706 | 1.7729 | 1.4607 | **1.7425** |
| Trades | 126 | 122 | 140 | 129 |
| WR | 23.81% | 27.05% | 16.43% | 25.58% |
| W/L Ratio | 5.35 | 4.78 | 7.43 | 5.02 |
| Avg Trade | 16,460 | 19,780 | 9,291 | 19,209 |
| MDD | -515,200 | -561,200 | -721,600 | -561,200 |
| Annual Return | 13.72% | 15.97% | 8.58% | **16.35%** |
| Sharpe | 0.1323 | 0.1342 | 0.0842 | **0.1360** |

### Exit Signal Distribution (v1.11.0 optimized)
DC:118 RE:11 | QS_Los:44 QS_Tim:44 TS:27 GC:5 BE:5 SL:2 TF:2

---

## 5. Next Steps — Profit-Taking Optimization

### The Core Problem
Between BE activation (~376 pts profit) and actual exit (GoldenCross or TimeStop), ALL accumulated profit beyond +5 pts is fully exposed to reversal. No mechanism tightens protection as profit grows.

### Candidate Directions (not yet started)
1. **Trailing Stop**: move stop upward as profit increases (ATR-based or fixed-step)
2. **Profit Target**: fixed take-profit level (conflicts with "let profits run" philosophy)
3. **Time-based tightening**: as holding bars increase, narrow the stop
4. **Hybrid**: BE trails after activation instead of staying fixed at EP-5

### Constraints to Respect
- "Let profits run" philosophy: no hard profit cap that truncates big winners
- Max single win = 602,800 NTD across all versions — must not degrade this
- TimeStop 27 trades = 21% of exits, historically 100% WR — don't break this
- IOG=False: any trailing stop must work on bar-close logic

---

## 6. Files

| File | State |
|------|-------|
| `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.11.0.pla` | Current, 789 lines |
| `docs/handoffs/HANDOFF_S16S_V1110_PROFIT_EXIT_REVIEW_20260803.md` | This file |

## 7. Git

Latest pushed commits:
- `552ad33` S16_S v1.11.0: remove dead code v_StopDist
- `2cdc450` S16_S v1.11.0: update BE_Trigger_Pct default 0.10 -> 0.80
- `1872a50` S16_S v1.11.0: true breakeven redesign (base v1.8.0)
