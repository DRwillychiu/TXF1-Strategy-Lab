# S16_S v0.3-P0FIX Issue Registry (2026-07-08, updated)

**Strategy**: S16_S_MACrossShort Candidate E (F15/S50/Slope16/MaxHold144)
**Code Version**: v0.3-P0FIX (commit aa4f8c7)
**Pre-fix Backtest**: Net 1,095,600 / PF 2.24 / MDD -508K / 84 trades / WR 21.4%
**Source**: Code audit + backtest analysis after W4 GA optimization (1,028 combos)
**Post-fix Audit**: 10-point deep audit PASS (all logic clean, no new bugs found)

---

## P0 - Critical (Code Bugs) -- ALL FIXED (commit aa4f8c7)

| ID | Category | Issue | Status | Fix |
|----|----------|-------|--------|-----|
| F1 | CODE | **M7 Breakeven Trail structurally dead** - Profit/exit conditions mutually exclusive on same bar. | **FIXED** | Added latching state vars `v_BE_Tier1_Active` / `v_BE_Tier2_Active`. Activation runs before exit checks. |
| F2 | CODE | **v_Slope uses AbsValue - direction-blind** - Passed upward slopes for a SHORT strategy. Also measured Slow (sluggish) instead of Fast (signal line). | **FIXED** | Changed to `v_ZLEMA_Fast[1] - v_ZLEMA_Fast` (positive = falling = bearish). Also resolves D1 and D7. |
| F3 | CODE | **M6 effective threshold is 4/5 not 3/5** - `ML_ScoreTrigger=65` required 80% (4/5), making `ML_MinCategories=3` dead. | **FIXED** | Lowered `ML_ScoreTrigger` to 60. Now 3/5 (60%) correctly triggers. |

---

## P1 - High (Structural/Statistical - Blocks W5 Validation)

| ID | Category | Issue | Impact | Location |
|----|----------|-------|--------|----------|
| S1 | RULE | **MDD -508,200 (50.8%) violates Rule #13 threshold (30%)** - Directly blocks promote to live_simulation. MC 95% MDD will be even higher. | Rule #13 FAIL | Backtest data |
| S2 | STAT | **Time concentration: 2026 = 78.6% of trades (66/84)** - 2020-2024: 9 trades, all losing (-66,200). 2022-2023: zero trades. Strategy only works in recent high-vol bearish environment. | Stability FAIL | Backtest data |
| S3 | STAT | **Profit concentration: Top 3 = 81%, Top 5 = 117.7%** - Remaining 79 trades are net negative. Remove largest trade (387K crash) -> net drops to 709K. | Overfitting risk | Backtest data |
| S4 | STAT | **Longest flat period: 2 years 9 months (2021-05 ~ 2024-02)** - Near 3 years with no signal. Capital efficiency (time in market = 0.35%) extremely low. | Capital efficiency | Backtest data |
| S5 | STAT | **Only 18 winning trades out of 84** - Insufficient sample to confirm edge. Bootstrap resampling confidence interval will be very wide. | Statistical fragility | Backtest data |
| S6 | STAT | **GA is in-sample only, no OOS validation** - 1,028 combos optimized on same data period. No Walk-Forward split. Rule #18 WFE expected <= 50%. | Overfitting risk | Methodology |

---

## P2 - Medium (Design Concerns - Should Address)

| ID | Category | Issue | Impact | Location |
|----|----------|-------|--------|----------|
| D1 | DESIGN | ~~v_Slope measures Slow ZLEMA, not Fast~~ | **RESOLVED by F2** | .pla:218 |
| D2 | DESIGN | **MaxHold=144 (12hr) contradicts "short-term profit" philosophy** - User positioned strategy as short-term. Actual avg holding = 11.4 bars (57min), winning = 28.7 bars (2.4hr). MaxHold=144 is mostly unused safety net. | Philosophy mismatch | Parameters |
| D3 | DESIGN | **M6 Multi-Layer: 0 triggers in 84 trades** - F3 fix (ScoreTrigger 60) + F1 fix (M7 latching) should improve. Re-verify after re-GA. | Improved by F1+F3, pending re-test | Backtest data |
| D4 | COST | **Commission=0 in backtest** - Settings show commission=0, slippage=1000/contract. If 1000 slippage is all-inclusive then OK. If commission needs separate addition (~100-300/RT), 84 trades x 200 = -16,800 additional cost. Minor but should confirm. | Cost underestimate | Backtest settings |
| D5 | DESIGN | **QuickStop_Time: 24 trades all losing (-117,600)** - QS_MaxBars=4 + QS_Pts=50. Trades not losing 50pts within 4 bars but still underwater get force-exited. All losses suggest some could have reversed to profit if held longer. | Potentially cutting meat | Backtest data |
| D6 | DESIGN | **Single event dependency: 2025-04-03 crash = 35.3% of net** - 387K from a rare systemic crash. Not predictable or repeatable. "Normal" earning power (ex-crash) = 708,600. | Non-repeatable | Backtest data |
| D7 | DESIGN | **MinSlope=16 semantics changed** - F2 fix changed slope from `AbsValue(Slow)` to `Fast[1]-Fast`. MinSlope=16 now means "Fast ZLEMA must fall 16 pts/bar". Needs re-calibration via GA. | **Root cause resolved by F2**, param needs re-GA | User observation |

---

## P3 - Low (Observations / Future Considerations)

| ID | Category | Issue | Impact | Location |
|----|----------|-------|--------|----------|
| O1 | STAT | Night session = 66% of net profit (725K/1,096K) but WR only 18.4%. Alpha concentrated in night session big swings. | Observation | Backtest data |
| O2 | STAT | Win/Loss ratio 8.2x is unusually high (healthy range 2-4x). Suggests extreme "small loss big win" structure that typically degrades in OOS. | Risk flag | Backtest data |
| O3 | STAT | Avg holding 11.4 bars vs MaxHold 144 bars - setting largely idle. 0 TimeStop exits. MaxHold=144 is pure safety net. | Efficiency | Backtest data |
| O4 | RULE | Settlement day calculation assumes 3rd Wednesday without checking national holidays. Known simplification per feedback_settlement_holiday_rule. Low frequency impact. | Low-freq risk | .pla:164-177 |
| O5 | CODE | `v_Prev_MP` declared, updated every bar (line 470), but never read anywhere. Dead code. | No impact, cleanup optional. | .pla:470 |

---

## Action Plan (updated after P0 fix)

1. ~~Fix P0 (F1 + F2 + F3)~~ **DONE** (commit aa4f8c7)
2. ~~Post-fix code audit~~ **DONE** (10/10 clean)
3. **Re-compile in MC12** and verify basic functionality (user manual step)
4. **Re-run GA optimization** - F2 fundamentally changed entry signals; all prior GA results invalidated. MinSlope range needs adjustment (new semantics = Fast ZLEMA pts/bar drop).
5. **Evaluate S1-S6** after re-GA with new performance data
6. **W5 Rule #18 5-pack** only after stable parameter set established

---

**End of Registry - 2026-07-08 (v0.3-P0FIX update)**
