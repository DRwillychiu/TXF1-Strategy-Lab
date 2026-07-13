# S16_S v1.0-PROD — Open Issues for Future Discussion

**Date**: 2026-07-13
**Status**: v1.0-PROD deployed in live_simulation, issues logged for future optimization
**Context**: User review session identified design gaps worth tracking

---

## Issue List

### I-1. MinSlope fixed points does not scale with index level
- **Problem**: MinSlope=28 is fixed points. At TXF 12,000 (2020) = 0.23%/bar (very strict). At TXF 47,000 (2026) = 0.06%/bar (relatively loose). Trade frequency and profit concentration biased toward high-index periods.
- **Impact**: Trade count artificially low in earlier years; strategy may over-trade at higher index levels
- **Attempted**: v0.6-ADAPTIVE (ATR-based) REJECTED — ATR measures volatility range, not directional slope
- **Potential direction**: Percentage-based MinSlope (e.g. 0.06%/bar), or index-level normalization
- **Priority**: Medium — does not break current operation but affects forward robustness
- **Related**: S16_S_10M experiment may reveal if this is a timeframe issue disguised as a scaling issue

### I-2. No explicit take-profit mechanism
- **Problem**: Strategy has no fixed-amount or percentage-based TP. Profit entirely depends on how far price drops within 2-hour TimeStop window.
- **Impact**: Profit per trade varies wildly (20K to 370K). At high index levels, profits naturally inflate.
- **User ruling (2026-07-13)**: Current design (time-based exit only) is accepted as intentional — simplicity and repeatability > complexity. No TP to be added at this stage.
- **Priority**: Low — user confirmed current design is preferred

### I-3. ZLEMA_Slow=70 exceeds pure 5M scope
- **Problem**: Slow(70) = 350 min = 5.8 hours. Original MA deep research recommended Slow <= 50 for pure 5M meaning. Current parameter is borderline 10M territory.
- **Impact**: Strategy may be better suited to 10M timeframe, which would change its portfolio classification
- **Potential direction**: S16_S_10M experiment — if 10M performs equal or better, confirms Slow=70 belongs in 10M scope
- **Priority**: Medium — S16_S_10M is the current ROADMAP active item

### I-4. Entry quality pre-screening — can we filter out structurally bad entries?
- **Problem**: Average 4.1 losing trades before 1 winner. Some entries may be predictably bad based on macro context (e.g. OTC index extremely strong, bull momentum across all sectors).
- **Impact**: Reducing false entries from 4.1 avg to 2-3 avg would significantly improve equity curve smoothness
- **Potential direction**: Macro environment pre-filter (OTC strength, sector breadth, daily trend alignment). BUT this conflicts with Layer 3 Option A ruling (no regime filter) and Lesson L24 (no sub-filter stacking).
- **Constraint**: Any pre-filter must not delay entry (5M burst timing is critical) and must not reduce alpha (20 TimeStop trades must not be filtered out)
- **Priority**: Medium-High — directly affects operator psychology and strategy sustainability
- **Risk**: Adding filters caused failure in 6 prior attempts (ATR/Volume/consecutive slope/daily regime/time-of-day/distance). New approach needed if pursued.

### I-5. Day vs Night session performance breakdown unknown
- **Problem**: Backtest does not separate day session vs night session performance. Slippage may differ (night spread wider), alpha source may differ.
- **Impact**: Cannot assess if night session is net positive or net negative contributor
- **Potential direction**: Post-trade analysis splitting by session time; or MC12 session-specific backtest
- **Priority**: Low — strategy runs both sessions by design, but data would inform future tuning

### I-6. Operator discipline risk during losing streaks
- **Problem**: Max 13 consecutive losses, avg 4.1. Operator temptation to manually shut down during streaks. Data shows large wins frequently follow streaks (post-streak avg win: 43K to 370K).
- **Impact**: Manual intervention during streaks will destroy strategy edge
- **Mitigation**: Documented in risk disclosure (Section 7 of Strategy Text). No code-level solution — this is a human discipline issue.
- **Priority**: Ongoing — monitor during live_simulation period

---

## Resolution Roadmap

| Issue | Depends On | Earliest Resolution |
|-------|-----------|-------------------|
| I-1 | S16_S_10M experiment | After 10M experiment completes |
| I-2 | User ruling | CLOSED — current design accepted |
| I-3 | S16_S_10M experiment | After 10M experiment completes |
| I-4 | New filter research | Future optimization cycle |
| I-5 | Session-split analysis | Can be done anytime with trade list |
| I-6 | Live simulation experience | Ongoing monitoring |
