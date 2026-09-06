# HANDOFF — L1 V3.1 SL_Pct Optimization (2026-07-24 EOD)

## Status: P3 Initial SL DONE, MDD Research NEXT

---

## 1. What Changed Today

### V3.1 SL_Pct = Fixed Percentage Initial Stop Cap
- **Problem**: At 40K-48K index level, ATR-based P3 initial stop = 500-1000 pts (too wide)
- **Solution**: Added `SL_Pct` input — third leg in P3, `EntryPrice * SL_Pct / 100`
- **Winner**: SL_Pct = 0.5% (optimizer sweep 0.3-1.5, step 0.1)
- **Result**: Net +57K (+3.1%), PF 1.321 -> 1.330, 5/7 years improved
- **File**: `strategies/research/L1_v3.1/L1_TrendLong_v3.1.pla` (commit `cc5071f`)

### Abandoned: L1_c (daily drawdown approach)
- Diagnostic log proved L1_c scales WITH volatility (same direction as ATR)
- At Ratio=0.7, L1_c only bound 8.7% of trades — useless
- Backup: `strategies/research/L1_v3.1/L1_TrendLong_v3.1_L1c.pla.bak_20260724`

### Rule #18 Five-Suite Validation: 2/5 PASS
- All 3 FAILs are structural L1 characteristics (capital adequacy, wide CI, gap crash)
- Equally present in V3.0 — V3.1 did not regress any of them
- Full report: `docs/research/L1_v3.1_rule18_validation_20260724.md`

---

## 2. Current State

| Item | State |
|------|-------|
| V3.1 .pla | Committed (`cc5071f`), pushed to origin/main |
| Optimization summary | Committed (`f041fa8`), pushed |
| Rule #18 validation | This commit |
| L1_c approach | KILLED, backup exists |
| Initial stop (P3) optimization | **DONE** |

---

## 3. Decisions Made (by user)

1. L1_c abandoned — fixed percentage (SL_Pct) adopted instead
2. SL_Pct = 0.5% selected as winner from 13-combo optimizer sweep
3. "今天不會做任何減碼" — no position sizing / partial exits
4. "出場就是直接出場" — exits are full exits until 2026-09-15 gate
5. Rule #18 run acknowledged — FAILs are L1 structural, not V3.1 regression

---

## 4. Next: MDD Research

### MDD Anatomy (discovered at session end)

The V3.1 MDD = -476,600 TWD (strategy level) / -422,200 (closed trade level).

**Root cause identified**: NOT a single catastrophic loss, but a 37-trade
grinding drawdown over 6 months (2025-02 to 2025-08).

| Finding | Detail |
|---------|--------|
| Period | 2025-02-21 to 2025-08-18 |
| Trades | 37 (almost all TL_SL exits) |
| Per-trade loss | -12K to -25K (small, SL_Pct already helping) |
| Index range | 22,000-24,400 |
| Market character | Choppy/ranging — trend strategy keeps entering and getting stopped |
| Core problem | **Entry quality**, not stop width |

### Key insight for next session
- Stop width is already solved (V3.1 SL_Pct caps each loss)
- MDD is driven by QUANTITY of consecutive losses in choppy markets
- This is an entry-side problem, not a stop-side problem
- Possible angles: entry filter for ranging markets, drawdown circuit breaker, regime detection
- User constraint: no position sizing, no partial exits

### All drawdowns > 200K in V3.1

| Peak Trade | Peak Date | Max DD |
|------------|-----------|--------|
| #141 | 2022-12-02 | -245,400 |
| #343 | 2025-02-21 | **-422,200** (THE MDD) |
| #398 | 2025-10-30 | -280,800 |
| #455 | 2026-05-07 | -208,600 |
| #470 | 2026-06-18 | -280,800 |

---

## 5. Files Created/Modified

| File | Role |
|------|------|
| `strategies/research/L1_v3.1/L1_TrendLong_v3.1.pla` | V3.1 with SL_Pct (MODIFIED from V3.0) |
| `docs/research/L1_v3.1_SL_Pct_optimization_summary_20260724.md` | Optimization summary |
| `docs/research/L1_v3.1_rule18_validation_20260724.md` | Rule #18 validation report |
| `docs/handoffs/HANDOFF_L1_v3.1_20260724_EOD.md` | This handoff |
| `strategies/research/L1_v3.1/L1_TrendLong_v3.1_L1c.pla.bak_20260724` | Abandoned L1_c backup |
| `strategies/research/L1_v3.1/v31_sl_log.txt` | L1_c diagnostic log (historical) |

---

## 6. Git State

- Branch: main
- Latest commit: (this commit, after handoff)
- Remote: origin/main (up to date after push)
- No uncommitted changes
