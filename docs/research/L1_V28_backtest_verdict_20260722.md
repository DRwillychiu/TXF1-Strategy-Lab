# L1 V2.8 Daily Loss Cap — Backtest Verdict

- **Date**: 2026-07-22
- **Strategy**: L1_TrendLong V2.7 vs V2.8
- **Module**: P8 Daily Loss Cap (DailyLoss_Enable=True, MaxCount=3, MaxNTD=100000)
- **Backtest**: MC12, TXF1 45M, 2019/12 ~ 2026/07, 1 lot, 1M initial
- **Status**: **REJECT** — V2.8 harmful, pending redesign decision

---

## 1. Verdict: REJECT

V2.8 (P8 Daily Loss Cap) is **net harmful** for L1. All primary metrics degraded.

---

## 2. Performance Comparison

| Metric | V2.7 | V2.8 | Delta | Direction |
|--------|------:|------:|------:|-----------|
| Net Profit (NTD) | 2,292,800 | 2,125,800 | -167,000 | **Worse** |
| Profit Factor | 1.383 | 1.357 | -0.027 | **Worse** |
| Max Drawdown (NTD) | -502,200 | -602,400 | -100,200 | **Worse** |
| Total Trades | 455 | 453 | -2 | |
| Win Rate | 31.43% | 31.35% | -0.08% | ~Same |
| Avg Trade (NTD) | 5,039 | 4,693 | -346 | **Worse** |
| Annual Return | 34.78% | 32.24% | -2.54% | **Worse** |
| Sharpe | 0.263 | 0.257 | -0.006 | **Worse** |
| Adj PF | 1.200 | 1.176 | -0.024 | **Worse** |
| Return/MDD | 4.57x | 3.53x | -1.04x | **Worse** |
| Gross Profit | 8,276,200 | 8,088,600 | -187,600 | **Worse** |
| Gross Loss | -5,983,400 | -5,962,800 | +20,600 | Better |
| Select PF | 1.333 | 1.340 | +0.006 | Better |
| Trade Std Dev | 135,977 | 130,080 | -5,897 | Better |

V2.8 wins on only 3 minor metrics. All primary metrics (Net, PF, MDD, Sharpe, Return) are worse.

---

## 3. Blocked Trades Analysis

P8 blocked exactly 2 trades out of 455:

### Blocked #1: Loss Avoided (saved -20,600)
- V2.7 trade #121: 2021-09-07 03:45 @17,550 -> 09:30 @17,457 [TL_SL]
- PnL: -20,600 NTD
- Trigger mechanism: **Unclear** — window should have been clean (count=0, NTD=0)
- Needs MC chart investigation to determine exact trigger

### Blocked #2: Winner Missed (lost +187,600)
- V2.7 trade #449: 2026-06-18 11:00 @46,630 -> 06-19 04:30 @47,578 [TL_Holiday]
- PnL: +187,600 NTD
- Trigger: **NTD cap** — prior trade #448 lost -100,600 (TL_SL_Gap), exceeding -100K threshold
- Context: trade #448 entered 03:45 @46,400, gap-down exit at 04:30 @45,907

### Net Impact
- Gross saved: +20,600 (1 blocked loss)
- Gross missed: -187,600 (1 blocked winner)
- **Net damage: -167,000 NTD**
- MDD chain reaction: missed +187,600 winner lowered equity curve -> July 2026 crash produced deeper MDD (-602K vs -502K)

---

## 4. Root Cause Analysis

### Why NTD trigger is structurally incompatible with L1:
1. **Single-loss threshold breach**: L1 ATR-based stops produce 80-100K losses in normal-high vol. NTD threshold at 100K = one normal large stop triggers the cap.
2. **Post-loss re-entry is L1's highest-EV pattern**: Review Section 9.5 showed <6h re-entry has 34.7% win rate (highest). Blocking re-entry after a loss cuts the most profitable entry type.
3. **MDD worsened by equity chain**: Missing a +187,600 winner lowered the equity curve, amplifying the subsequent drawdown.

### Why Count trigger is ineffective for L1:
- L1 trades 0.29 times/day. Getting 3 entries in one window is near-impossible.
- Count trigger (MaxCount=3) never fired in 6.5 years of backtest.

---

## 5. Discussion: Points vs NTD Design (User-Initiated 2026-07-22)

User raised critical design question: should daily loss cap use points or NTD?

### Decision: Points-based is correct
- User plans to deploy strategies on TXF (1pt=200), MXF (1pt=50), and potentially micro contracts
- Points-based threshold is contract-size-agnostic — same parameter works across all contract sizes
- Aligns with the "iron rule": all entry/exit logic is points-based

### User's Risk Framework
- Trend strategies (L1, L2, L5): MDD target **20-25%** of allocated capital
- Consolidation strategies (L3, L4): MDD target **10-15%** of allocated capital
- Return target: **5:1** Return/MDD ratio (trend strategies)

### Key Finding: Daily Loss Cap is wrong tool for L1 MDD control

MDD% = (Strategy MDD points x BigPointValue x Lots) / Allocated Capital

L1 historical MDD = 2,511 points (fixed strategy behavior). To achieve MDD <= 25%:
- TXF 1 lot: need >= 2,008,800 NTD allocated
- MXF 1 lot: need >= 502,200 NTD allocated

The correct MDD control for L1 is **contract sizing + capital allocation**, not daily loss cap.

Daily loss cap role for L1: at most an **extreme disaster circuit breaker** (1,200-1,500 points), not regular risk control.

---

## 6. Next Steps (Pending User Decision)

1. **V2.8 code status**: P8 module remains in L1_TrendLong.pla (not reverted yet). User will decide after points-based redesign discussion.
2. **Points-based redesign**: Continue on laptop session — redesign daily loss cap using points, tied to capital allocation framework.
3. **Cross-strategy evaluation**: L3/L4 (consolidation, higher frequency) may still benefit from daily loss cap. Test independently.
4. **Contract sizing analysis**: Calculate optimal contract size per strategy based on user's MDD targets (20-25% trend, 10-15% consolidation).

---

## 7. Lessons

- **L25**: Daily loss cap (NTD-based, 100K) is net harmful for low-frequency trend strategies. Single ATR-based stop can breach threshold, blocking highest-EV re-entry pattern. Correct MDD control tool for trend strategies is contract sizing, not entry gate restriction.
- **L26**: Risk parameters must be derived top-down from capital allocation framework (account -> per-strategy allocation -> MDD budget -> parameter), not bottom-up from backtest curve fitting.
- **L27**: When deploying across multiple contract sizes (TXF/MXF/micro), all risk thresholds must be in points to maintain portability. NTD-based thresholds require recalibration per contract.
