# S16_S v0.2-GA-OPT Issue Registry (2026-07-08)

**Strategy**: S16_S_MACrossShort Candidate E (F15/S50/Slope16/MaxHold144)
**Backtest**: Net 1,095,600 / PF 2.24 / MDD -508K / 84 trades / WR 21.4%
**Source**: Code audit + backtest analysis after W4 GA optimization (1,028 combos)

---

## P0 - Critical (Code Bugs - Must Fix Before Proceeding)

| ID | Category | Issue | Impact | Location |
|----|----------|-------|--------|----------|
| F1 | CODE | **M7 Breakeven Trail structurally dead** - Profit condition (`Close <= Entry - ATR`) and exit condition (`Close >= Entry - Buffer_Pts`) are mutually exclusive on the same bar. ATR ~50-150 pts but Buffer = 5 pts. Needs state variable to remember threshold was reached. Backtest: 1/84 BE_Trail1 exits (edge case), was a loss. | P3 exit chain broken | .pla:408-424 |
| F2 | CODE | **v_Slope uses AbsValue - direction-blind** - `AbsValue(v_ZLEMA_Slow - v_ZLEMA_Slow[1])` passes upward slopes equally for a SHORT strategy. Should check negative slope only. Explains user observation of entries on flat/rising slopes. | Wrong entry signals | .pla:214 |
| F3 | CODE | **M6 effective threshold is 4/5 not 3/5** - 5 binary categories produce Score_Pct of 0/20/40/60/80/100. `ML_ScoreTrigger=65` requires >=65%, but 3/5=60% fails. `ML_MinCategories=3` is dead code. Backtest: 0/84 M6 exits. | P2 exit chain too strict | .pla:390-396 |

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
| D1 | DESIGN | **v_Slope measures Slow ZLEMA, not Fast** - Death cross momentum should be measured by Fast ZLEMA slope (the signal line). Slow ZLEMA is sluggish by definition. | Entry quality | .pla:214 |
| D2 | DESIGN | **MaxHold=144 (12hr) contradicts "short-term profit" philosophy** - User positioned strategy as short-term. Actual avg holding = 11.4 bars (57min), winning = 28.7 bars (2.4hr). MaxHold=144 is mostly unused safety net. | Philosophy mismatch | Parameters |
| D3 | DESIGN | **M6 Multi-Layer: 0 triggers in 84 trades** - Combined with F3 (effective 4/5) and F1 (M7 dead), exit chain P2+P3 completely broken. Profit protection relies solely on GoldenCross (P4). | Defense gap | Backtest data |
| D4 | COST | **Commission=0 in backtest** - Settings show commission=0, slippage=1000/contract. If 1000 slippage is all-inclusive then OK. If commission needs separate addition (~100-300/RT), 84 trades x 200 = -16,800 additional cost. Minor but should confirm. | Cost underestimate | Backtest settings |
| D5 | DESIGN | **QuickStop_Time: 24 trades all losing (-117,600)** - QS_MaxBars=4 + QS_Pts=50. Trades not losing 50pts within 4 bars but still underwater get force-exited. All losses suggest some could have reversed to profit if held longer. | Potentially cutting meat | Backtest data |
| D6 | DESIGN | **Single event dependency: 2025-04-03 crash = 35.3% of net** - 387K from a rare systemic crash. Not predictable or repeatable. "Normal" earning power (ex-crash) = 708,600. | Non-repeatable | Backtest data |
| D7 | DESIGN | **MinSlope=16 still allows flat-slope entries (user observation)** - Combined with F2 (AbsValue) and D1 (measures Slow), effective filtering power may be far below expected. | Entry quality | User observation |

---

## P3 - Low (Observations / Future Considerations)

| ID | Category | Issue | Impact | Location |
|----|----------|-------|--------|----------|
| O1 | STAT | Night session = 66% of net profit (725K/1,096K) but WR only 18.4%. Alpha concentrated in night session big swings. | Observation | Backtest data |
| O2 | STAT | Win/Loss ratio 8.2x is unusually high (healthy range 2-4x). Suggests extreme "small loss big win" structure that typically degrades in OOS. | Risk flag | Backtest data |
| O3 | STAT | Avg holding 11.4 bars vs MaxHold 144 bars - setting largely idle. 0 TimeStop exits. MaxHold=144 is pure safety net. | Efficiency | Backtest data |
| O4 | RULE | Settlement day calculation assumes 3rd Wednesday without checking national holidays. Known simplification per feedback_settlement_holiday_rule. Low frequency impact. | Low-freq risk | .pla:164-177 |

---

## Action Plan

1. **Fix P0 (F1 + F2 + F3)** -> code changes to .pla
2. **Re-run backtest** after P0 fixes (performance data will change significantly, especially F2)
3. **Evaluate S1 (MDD)** - M7 fix may reduce MDD; if still >30%, adjust parameters
4. **Re-run GA or targeted optimization** if F2 slope fix changes entry signal fundamentally
5. **W5 Rule #18 5-pack** only after stable parameter set established

---

**End of Registry - 2026-07-08**
