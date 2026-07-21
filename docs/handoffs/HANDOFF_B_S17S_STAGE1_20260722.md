# Handoff B: S17_S SwingShort60M Stage-1 Deep Discussion

**Date**: 2026-07-22
**From**: Desktop main session
**To**: Parallel session B (dedicated to S17_S strategy design)
**Repo**: `C:/Users/User/Desktop/TXF1-Strategy-Lab/` (git main, latest commit `b4cd66b`)

---

## 1. Mission

You are continuing the S17_S SwingShort60M Stage-1 design discussion. Topic 1 (entry philosophy) has initial consensus + 9-point Q&A completed. Your job is to:

1. Continue Topics 2-6 of Stage-1 discussion
2. After all 6 topics reach consensus, write W1 strategy spec
3. Then design W0 Python pre-verify (alpha existence proof before writing .pla)

**This is pure discussion and design — no .pla code writing yet.**

---

## 2. Key Files to Read First

| File | Content |
|------|---------|
| `strategies/research/S17_SwingShort60M/S17_S_STAGE1_DISCUSSION_20260720.md` | **START HERE** — Topic 1 consensus, 5 hidden risks, 6 topics list |
| `strategies/research/S17_SwingShort60M/S17_S_STAGE1_LAPTOP_HANDOFF_20260721.md` | Laptop session: 11-dim comparison, 9-point Q&A, 7 rebound scenarios, user rulings |
| `docs/policies/OFFICIAL_ROADMAP.md` | S17_S entry at line ~80, decision history at bottom |
| `docs/methodology/STRATEGY_RD_SOP.md` or `STRATEGY_RD_SOP_v2.md` | Strategy R&D SOP (9-point intake) |

---

## 3. What S17_S Is

**One-line**: 60M native-designed mid-speed short strategy that captures "post-bounce-failure continuation decline profit" in any market condition.

**Portfolio gap it fills**: July 2026 DD post-mortem revealed a "mid-speed short" structural hole:
- S16_S only catches explosive first bars (minute-level burst)
- L2's 13-week SMA had 0 trades in all of 2026 (too slow)
- S16_S had only 3 trades in 2022 slow bear (slope too flat)
- **S17_S earns the staircase money between these two extremes**

**Key distinction from S16_S 10M experiment**: S17_S is NOT S16_S ported to 60M. The 10M experiment proved same-strategy-different-timeframe = correlation 0.89 = duplicate bet. S17_S must be a natively designed different alpha on 60M.

---

## 4. Topic 1 Consensus (Entry Philosophy)

### Adopted: B+C Dual-Layer Architecture

```
Layer 1 (C): Daily environment filter — "Is this a declining environment?"
  - Example: Close < MA(20) AND MA(20) declining
  - MC12: Data2 = TXF1 Daily

Layer 2 (B): 60M K-bar trigger — "Did a bounce just fail?"
  - Example: Engulfing pattern after bounce attempt, or bounce hits resistance and falls back
  - MC12: Data1 = TXF1 60min
```

### Rejected: Direction A (ZLEMA family)
- Same family as S16_S → expected monthly P&L correlation > 0.7
- 10M experiment proof: same architecture different timeframe = 0.89 correlation

### Deferred: Volume
- User wants volume-price patterns eventually
- Phase 1: pure price structure only (validate alpha exists first)
- Phase 2: add volume as enhancement
- TXF1 futures volume has 3 traps: contract rollover, thin night session, settlement day anomaly

### Key Principle Established
K-bar pattern reliability scales with timeframe:
- 5M: noisy, patterns unreliable → pure math (S16_S uses ZLEMA slope)
- 60M: 1 bar = 1 hour of institutional battle → patterns meaningful (S17_S)
- Daily: most robust → C layer uses daily-level statistics

### Alpha Nature
- NOT predicting the START of a decline → judging CONTINUATION of a decline
- Alpha source = "statistically, ~70% of bounces in a downtrend are traps"
- Earns the 7 trap bounces, pays insurance on the 3 real reversals

---

## 5. User Rulings (from laptop 9-point Q&A)

| Ruling | Date | Content |
|--------|------|---------|
| Overnight risk | 2026-07-21 | NOT a problem for S17_S, not a design obstacle |
| Trade frequency | 2026-07-21 | Just needs to be non-interfering between S16_S and S17_S |
| S17_S alpha | 2026-07-21 | Post-bounce-failure continuation decline, not MA transition moment |
| Entry principle | 2026-07-21 | Operating timeframe determines strategy condition form |

---

## 6. Identified Hidden Risks (must address in Topics 2-6)

1. **Gap risk** (BIGGEST): Swing holds overnight → gap opens can blow through stops. 60M normal vol is 50-100 pts/bar.
2. **Holiday rule conflict**: Current iron rule = flatten before all holidays. Swing holds for days → forced mid-trend exit kills alpha.
3. **V-reversal**: Looks like failed bounce but is actually V-turn bottom → short into rising market.
4. **Trend end detection**: When to switch from "hold through temporary bounce" to "trend reversed, must exit"?
5. **Futures volume quality**: Contract rollover, thin night session, settlement day anomaly.

---

## 7. Rebound Scenarios (from laptop Q&A)

| Threat Level | Type | Why Dangerous |
|-------------|------|---------------|
| FATAL | V-shaped reversal | All short signals correct, but structure flips. 60M bar-close wait = severe loss |
| FATAL | Short squeeze cascade | Daily environment still bearish, but violent upward |
| HIGH | Policy event rebound | Sudden, unpredictable, strong |
| HIGH | Gap-up open | Stop orders jumped over, 200+ pt gap |
| MEDIUM | Technical bounce (support) | Core S17_S judgment: real or fake? |
| MEDIUM | Month-end window dressing | Short (1-3 days) but significant force |
| LOW-MED | Ex-dividend distortion | Looks like decline but just dividend adjustment |

---

## 8. Remaining Topics (Continue From Here)

| Topic | Subject | Status | Key Question |
|-------|---------|--------|--------------|
| 1 | Entry philosophy | ✅ B+C consensus | — |
| **2** | **Boundary separation** | **NEXT** | How to guarantee S17_S doesn't become slow-S16_S or fast-L2? Monthly P&L correlation acceptance line? |
| 3 | Holding/exit philosophy | ⏳ | Holiday flatten rule vs swing holding = fundamental conflict. How to resolve? |
| 4 | Rally handling | ⏳ | Endure (give room) vs exit-and-re-enter? Determines MDD character |
| 5 | Insurance cost budget | ⏳ | Bull-year loss: where and how much is acceptable? |
| 6 | W0 verification design | ⏳ | Python pre-verify with daily data (S16 skipped W0 but new alpha must prove existence first) |

### Laptop also added 3 priority items:
- Priority 1: Market condition suitability (home field / away field / no-go zone)
- Priority 2: Stop loss architecture (P3b distance, bar-close stop, daily flip, BE scaling)
- Priority 3: Rebound scenario handling SOP (each of 7 types: detect/respond/endure?)

These overlap with Topics 3-5 — integrate them.

---

## 9. S16_S Reference (for comparison during design)

| Dimension | S16_S v1.4 | S17_S (target) |
|-----------|-----------|----------------|
| Timeframe | 5M only | 60M + Daily |
| Holding | Minutes to 2hr max | Days |
| Frequency | 19/yr | Est. 12-18/yr |
| Entry | ZLEMA slope > 28 (pure math) | B+C (K-bar pattern + daily filter) |
| Exit layers | QuickStop → ML → BE → GoldenCross → TimeStop → ATR | TBD (needs full design) |
| MDD | -228K (-18.3%) | TBD |
| Correlation target | — | Monthly P&L vs S16_S < 0.5 |

---

## 10. Constraints and Rules

- **Language**: Conversational replies in Traditional Chinese; code/identifiers in English
- **Git discipline**: "update git" = commit + push always
- **No break questions**: User manages own rest schedule
- **SOP discipline**: Stage-1 discussion BEFORE writing spec (S16_L lesson: no skipping steps)
- **Correlation lock**: S17_S vs S16_S monthly P&L < 0.5 (pre-locked constraint)
- **Holiday iron rule**: All TXF1 strategies must flatten before market closure + block eve-of-holiday night session entries. Dates per TAIFEX official calendar ONLY.
- **Trend strategy feedback**: Do NOT suggest profit-pullback protection for trend strategies (user ruling from feedback_trend_let_profits_run)
- Read CLAUDE.md at repo root for all 19 rules

---

## 11. Immediate Action

**Start with Topic 2 (Boundary Separation)**:
- Define concrete metrics that separate S17_S from S16_S and L2
- Propose acceptance criteria for "different enough" (correlation, holding period distribution, market condition overlap)
- Check: does B+C architecture naturally create separation, or do we need explicit guards?

Then proceed through Topics 3-6 sequentially. After all 6 topics have user consensus, write W1 strategy spec document.
