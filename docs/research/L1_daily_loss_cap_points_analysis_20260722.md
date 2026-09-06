# L1 Daily Loss Cap — Points-Based Analysis (Continued Session)

- **Date**: 2026-07-22 (continued from earlier session)
- **Strategy**: L1_TrendLong V2.7
- **Prerequisite**: `L1_v2.8_backtest_verdict_20260722.md` (V2.8 REJECT), `L1_daily_loss_cap_design_20260722.md`
- **Status**: **PAUSED** — data analysis complete, pending user decision on whether L1 needs a daily cap at all

---

## 1. MDD Correction: Strategy vs Closed-Trade

Previous analysis incorrectly used Strategy MDD (includes unrealized intraday drawdown) as the anchor. Corrected to use Closed-Trade MDD (realized-only) for daily cap derivation.

| Metric | L1 | L2 | L3 | L4 | L5 |
|--------|---:|---:|---:|---:|---:|
| Strategy MDD (pts) | 2,538 | 1,211 | 2,386 | 1,983 | 4,562 |
| Closed-Trade MDD (pts) | 2,038 | 748 | 2,146 | 1,706 | 3,597 |
| Difference (pts) | 500 | 463 | 240 | 277 | 965 |
| Strategy MDD date | 2026-07-21* | 2022-09-22 | 2026-07-02 | 2025-04-07 | 2026-06-11 |
| Closed MDD date | 2026-07-16 | 2022-09-08 | 2026-06-24 | 2025-04-01 | 2026-07-03 |

*L1 Strategy MDD includes open position unrealized drawdown (open P&L: +192,400 NTD / +962 pts at report time).

**Why Closed-Trade MDD**: Daily loss cap mechanism monitors closed-trade losses only; it cannot see or act on unrealized drawdown.

---

## 2. Latest Backtest Data (Points, 1 pt = 200 NTD)

Source: MC12 XLS exports, 2026-07-22. All values verified from raw cell reads.

| Metric | L1 V2.7 | L2 V5.2 | L3 V14.1 | L4 V14.4 | L5 V19.8 |
|--------|--------:|--------:|---------:|---------:|---------:|
| Net Profit (pts) | 10,136 | 7,206 | 3,468 | 1,118 | 4,440 |
| PF | 1.349 | 2.882 | 1.210 | 1.316 | 1.314 |
| Annual Return | 34.2% | 21.0% | 10.6% | 5.3% | 18.0% |
| Sharpe | 0.258 | 0.245 | 0.108 | 0.078 | 0.177 |
| Closed MDD (pts) | 2,038 | 748 | 2,146 | 1,706 | 3,597 |
| Net/Closed MDD | 4.97:1 | 9.63:1 | 1.62:1 | 0.66:1 | 1.23:1 |
| Net/Strategy MDD | 3.99:1 | 5.95:1 | 1.45:1 | 0.56:1 | 0.97:1 |
| Target | 5:1 | 5:1 | 10:1 | 10:1 | 5:1 |
| Trades | 424(1 open) | 78 | 272 | 54 | 171 |
| Win Rate | 31.1% | 42.3% | 56.3% | 42.6% | 56.1% |
| Avg Win (pts) | 297 | 334 | 131 | 202 | 194 |
| Avg Loss (pts) | 99 | 85 | 139 | 114 | 189 |
| W/L Ratio | 2.98 | 3.93 | 0.94 | 1.77 | 1.03 |
| Max Win (pts) | 3,342 | 2,232 | 1,213 | 1,365 | 1,834 |
| Max Loss (pts) | 726 | 199 | 944 | 463 | 1,109 |
| Max Loss / Closed MDD | 35.6% | 26.6% | 44.0% | 27.1% | 30.8% |
| Period | 5Y 11M | 6Y 10M | 6Y 7M | 4Y 2M | 4Y 11M |

---

## 3. Daily Trade Frequency (L1-L5)

Trading window: 15:00 night session open -> next day 13:45 close.

| Metric | L1 | L2 | L3 | L4 | L5 |
|--------|---:|---:|---:|---:|---:|
| Total entries | 425 | 78 | 272 | 54 | 171 |
| Trading windows | 375 | 76 | 266 | 51 | 151 |
| 1 trade/day | 326 (86.9%) | 74 (97.4%) | 260 (97.7%) | 48 (94.1%) | 132 (87.4%) |
| 2 trades/day | 48 (12.8%) | 2 (2.6%) | 6 (2.3%) | 3 (5.9%) | 18 (11.9%) |
| 3 trades/day | 1 (0.3%) | 0 | 0 | 0 | 1 (0.7%) |
| >= 2 trades/day | 49 (13.1%) | 2 (2.6%) | 6 (2.3%) | 3 (5.9%) | 19 (12.6%) |

L1 and L5 have ~13% multi-trade days — the daily cap's "action zone". L2/L3/L4 have <6%.

---

## 4. L1 Multi-Trade Day P&L Analysis (Critical Finding)

49 multi-trade days analyzed. ALL first trades on multi-trade days are losses (100%) — the 2nd trade exists because the 1st was stopped out.

### 2nd Trade Profile vs L1 Overall

| Metric | 2nd Trade (49) | L1 Overall (424) |
|--------|---------------:|-----------------:|
| Win Rate | 36.7% | 31.1% |
| Avg Win (pts) | +440 | +297 |
| Avg Loss (pts) | -97 | -99 |
| W/L Ratio | 4.54 | 2.98 |
| EV per trade (pts) | **+100** | +24 |
| Max Win (pts) | +3,342 | +3,342 (same trade) |
| Max Loss (pts) | -445 | -726 |
| Total P&L (pts) | +4,919 | — |

**The 2nd trade after a stop-out is L1's highest expected-value entry pattern.** Higher win rate, much higher W/L ratio, and L1's all-time biggest winner (+3,342 pts on 2026-04-07) was a 2nd trade.

### Hypothetical: Block All 2nd Trades After 1st Loss

| Impact | Trades | Points | NTD |
|--------|-------:|-------:|----:|
| Losses avoided | 31 | +2,994 | +598,800 |
| Wins missed | 19 | -8,038 | -1,607,600 |
| **Net impact** | **50** | **-5,044** | **-1,008,800** |

Blocking 2nd trades would destroy 49.8% of L1's total net profit.

### Multi-Trade Day Aggregate

| Metric | Value |
|--------|------:|
| Net positive days | 11 (22.4%) |
| Net negative days | 38 (77.6%) |
| Total sum | -57 pts (~breakeven) |
| Max day loss | -787 pts |
| Max day gain | +3,053 pts |
| Asymmetry ratio | 3.88x (gain/loss) |

Multi-trade days are net breakeven (-57 pts over 6 years), not a bleeding problem.

---

## 5. Conclusion and Decision Point

**Data does not support an entry-blocking daily loss cap for L1.**

- The 2nd trade after stop-out has positive EV (+100 pts/trade)
- Blocking it destroys ~50% of net profit
- Multi-trade days are net breakeven, not a risk hotspot
- L1's real risk is single-trade max loss (726 pts), already managed by SL system

### Pending User Decision (3 options presented):

1. **No daily cap for L1** — data does not support it
2. **Extreme disaster circuit breaker** (1,500+ pts) — only for black swan events SL cannot handle
3. **Defer L1, analyze L2-L5 first** — determine which strategies actually need daily caps

**Status**: PAUSED at user request (2026-07-22). Resume with user decision.

---

## 6. Lessons

- **L28**: For low-frequency trend strategies, the re-entry after stop-out is the highest-EV trade — blocking it is structurally destructive. Daily loss caps must never interfere with this pattern.
- **L29**: Strategy MDD vs Closed-Trade MDD distinction is critical for daily cap design. The cap mechanism operates on closed trades; anchoring to Strategy MDD (which includes unrealized drawdown) overestimates available headroom.
