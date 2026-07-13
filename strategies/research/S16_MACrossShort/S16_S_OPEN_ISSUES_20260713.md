# S16_S v1.0-PROD — Potential Issues & Risk Register

**Date**: 2026-07-13
**Status**: v1.0-PROD deployed in live_simulation
**Context**: User review session — comprehensive issue list for boss discussion
**Strategy Text Reference**: `S16_S_STRATEGY_TEXT_20260713.md`

---

## A. Parameter Issues

### A1. Slow line parameter exceeds pure 5M scope
- ZLEMA_Slow=70 = 350 min = 5.8 hours lookback, approaching 10M territory
- Original MA deep research recommended Slow <= 50 for pure 5M meaning
- **Impact**: Strategy may be "misplaced" on 5M; 10M may be more appropriate
- **Resolution**: Launch S16_S_10M experiment as comparison. Do not modify current 5M version.

### A2. Slow line parameter is a narrow peak
- ZLEMA_Slow=80: performance drops -33.5%
- **Impact**: Parameter stability weaker than plateau-type strategies. Market structure changes could invalidate parameter without warning.
- **Resolution**: Documented as known risk. Monitor during simulation period.

### A3. MinSlope is 2 steps from cliff
- MinSlope=30: performance drops -27.4%. Current value = 28.
- **Impact**: Safety margin is thin.
- **Resolution**: Same as A2. Monitor during simulation.

### A4. MinSlope fixed points does not scale with index level
- 28 pts at TXF 12,000 (2020) = 0.23%/bar (very strict)
- 28 pts at TXF 47,000 (2026) = 0.06%/bar (relatively loose)
- **Impact**: Trade count artificially low in earlier years, higher in recent years. Profit concentration biased toward high-index periods.
- **Attempted**: v0.6 ATR-based adaptive — REJECTED (ATR measures volatility range, not directional slope)
- **Resolution**: Research percentage-based MinSlope approach. Not urgent — does not break current operation.

---

## B. Performance Structure Issues

### B1. Alpha concentrated in 20 trades
- 20 TimeStop exits = +2,103K = ALL alpha. Remaining 86 trades = -1,075K.
- **Impact**: Missing 2-3 big wins (system downtime, manual intervention) turns strategy from profitable to breakeven or loss. System uptime is a survival requirement.
- **Resolution**: Ensure MC12 100% uptime. No manual intervention.

### B2. Profit concentrated in 2025-2026
- 94% of profit from the last 2 years.
- **Impact**: May be benefiting from high index level (see A4). Performance could decline during lower-index periods.
- **Resolution**: WFA 77.4% cross-validated OOS profitability across 9 windows, partially mitigating this concern.

### B3. Longest flat period: 1 year 10 months
- 2020/05 ~ 2022/03: equity curve made no new high.
- **Impact**: Operator must endure extended periods with no return on allocated capital.
- **Resolution**: Portfolio allocation capped at 3%. Does not impair overall capital utilization.

---

## C. Operational Risk Issues

### C1. Losing streak psychological pressure
- Max consecutive losses: 13 (total loss 162K = 16.2% of capital)
- Average consecutive losses: 4.1
- **Impact**: Operator may manually shut down strategy during streaks, missing subsequent large wins. Data shows post-streak wins average 43K to 370K.
- **Resolution**: Discipline issue, no code-level solution. Documented in risk disclosure.

### C2. Bull regime is structural insurance cost
- Bull regime: PF 0.70, 35 trades, net -106K
- **Impact**: During extended bull markets, strategy bleeds consistently. WFA W6 showed -43.4% MDD in AI bull + BoJ regime.
- **Resolution**: Pair with long-side strategies (e.g. S3_L) in portfolio for hedge.

### C3. Day vs Night session contribution unknown
- Backtest does not separate day session vs night session performance.
- **Impact**: Cannot assess whether night session is net alpha or net cost contributor.
- **Resolution**: Post-trade analysis with trade list (session time split). Low priority.

---

## D. Design Philosophy Issues

### D1. No explicit take-profit mechanism
- Profit exit relies entirely on TimeStop (2 hours) and GoldenCross (MA reversal).
- No fixed-amount or percentage-based TP.
- **Impact**: Per-trade profit varies widely (20K to 370K).
- **User ruling (2026-07-13)**: Current design ACCEPTED. Simplicity and repeatability > complexity.

### D2. Entry quality cannot be pre-screened
- Average 4.1 losing trades before 1 winner.
- 6 filter types tested and ALL failed (ATR/Volume/consecutive slope/daily regime/time-of-day/distance).
- **Impact**: Equity curve has visible sawtooth pattern. Psychological cost is high.
- **Potential direction**: Optimize "post-entry judgment speed" rather than "pre-entry filtering" — make QuickStop faster/cheaper, not add more gates.
- **Constraint**: Any new approach must not delay entry (5M burst timing is critical) and must not filter out the 20 TimeStop alpha trades.

---

## E. Overall Assessment

### Strengths
- WFA 77.4% STRONG PASS (strongest in entire portfolio)
- Ruin probability 0.03%, max single loss only 4.26% of capital
- Reward/risk ratio 6.44, recovery factor 3.79
- QuickStop loss control effective (72 trades avg loss only -14K)

### Core Risks
- Alpha highly concentrated (20 trades carry all profit)
- Parameter stability is narrow (S70 narrow peak + Slope30 cliff)
- Requires extreme operator discipline (no intervention during streaks + patience during flat periods)

### Recommendation
- Maintain 3% cap allocation, no adjustment during live_simulation
- Launch S16_S_10M experiment to resolve A1/A4
- Comprehensive re-evaluation after 30+ simulation trades accumulated

---

## Resolution Roadmap

| Issue | Depends On | Earliest Resolution |
|-------|-----------|-------------------|
| A1 | S16_S_10M experiment | After 10M experiment completes |
| A2 | Live simulation data | Ongoing monitoring |
| A3 | Live simulation data | Ongoing monitoring |
| A4 | New filter research | Future optimization cycle |
| B1 | System uptime | Operational requirement |
| B2 | Time + more data | WFA partially addressed |
| B3 | Portfolio design | Managed by 3% cap |
| C1 | Operator discipline | Ongoing |
| C2 | Portfolio hedge | Pair with long strategies |
| C3 | Session-split analysis | Can be done anytime |
| D1 | User ruling | CLOSED — current design accepted |
| D2 | QuickStop optimization | Future optimization cycle |
