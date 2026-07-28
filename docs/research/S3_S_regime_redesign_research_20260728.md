# S3_S Regime Redesign Research (2026-07-28)

> **Strategy**: S3_S_VolSqueezeShort v1.9.6-OPT-PROD
> **Scope**: Regime filter architecture review, timeframe experiment, fundamental redesign direction
> **Status**: Research phase — no code changes made

---

## 1. Strategic Questions Raised

### Q1: Are there other suitable regimes beyond Strong Bull / Bear?
- Current: Strong Bull (>1.05) + Bear (<0.98) allowed, Range (0.98-1.02) + Weak Bull (1.02-1.05) blocked
- Range PF=0.73 (losing money), Weak Bull PF=1.61 (marginal)
- Weak Bull zone (1.02-1.05) worth backtesting for high-quality subsets
- "Regime transition detection" (ratio crossing from bull to bear) is a higher-dimensional improvement direction
- Conclusion: Current five-zone design is logically sound but boundary values may need recalibration

### Q2: Regime defense gap during holding — CONFIRMED
- Code audit (1124 lines, full read): regime is **entry-only** (line:899)
- Zero regime references in any exit condition, including all 11 factors of 1M Multi-Layer Exit
- E3 "Volatility Regime Shift" factor measures 1M ATR ratio, NOT the daily MA regime
- Regime variables are recalculated every 1M bar but only consumed at entry gate
- **Design gap**: Trade entered in Strong Bull can persist through regime drift to Range/Bear with no adaptive response
- **Design gap**: 1M exit scoring has no macro-direction awareness

### Q3: Should short strategies use smaller operation timeframe?
- Short moves are faster than bull moves (market asymmetry)
- 60M entry: waits for bar close, may miss the initial breakdown
- v1.9.6 already has 1M execution layer for exits
- **Conclusion**: Squeeze detection should stay at structural timeframe (60M), but entry trigger can be improved with 1M-level breakdown detection (hybrid architecture concept)

### Q4: BB squeeze dependency — structural blind spots
- Scenario #4 (no squeeze → crash): Strategy misses entirely — structural limitation, not a bug
- Scenario #5 (gradual decline): BB bands walk down, no squeeze formed — entire trend missed
- Scenario #9 (flash crash): 60M bar hasn't closed → miss or enter at tail end
- **Conclusion**: These blind spots define S3_S's role boundary. Coverage requires new strategies (e.g., S4 MACDDivergence), not modification of S3_S's core thesis

---

## 2. Regime Code Audit Results

Full line-by-line audit of regime implementation in S3_S_VolSqueezeShort.pla:

| Check | Result | Location |
|-------|--------|----------|
| Ratio calculation | PASS | line:543-547, MA(Fast)/MA(Slow) of Data3[1] |
| Data binding | PASS | Data3 = Daily, [1] = previous completed bar |
| Zone classification | PASS | line:551-552, no overlap/gap at boundaries |
| Entry gate check | PASS | line:899, v_Regime_OK in 8-condition AND |
| Bypass possibility | NONE | Only via Use_Regime_Filter=False (intentional) |
| Race condition | NONE | Section 5.5 executes before Section 10 |
| Holding period regime | ZERO references | Sections 7,9,9.5,11,12 — none use regime |
| Exit regime | ZERO references | All 11 ML factors + all exit conditions — none |
| BWPctile | PASS | Circular buffer, percentile rank, warm-up guard (line:593-604) |
| BWRank Guard | PASS | Equal-BW edge case handled (line:610-613) |

---

## 3. Timeframe Experiment: Daily → 4H Regime

### Setup
- Data3 changed from TXF1 Daily to TXF1 240M (4H)
- Regime_FastMA: 15 → 60, Regime_SlowMA: 40 → 160
- Intention: Maintain same calendar coverage (15day/40day) with 4x faster update frequency
- All other parameters unchanged

### Results

| Metric | Daily MA15/40 (baseline) | 4H MA60/160 (experiment) | Change |
|--------|-------------------------|--------------------------|--------|
| Net Profit | +731,000 | +854,800 | +16.9% |
| Profit Factor | 1.749 | 1.373 | **-21.5%** |
| Trades | 71 | 67 | -5.6% |
| Win Rate | 49.3% | 43.3% | **-12.2%** |
| Sharpe | 0.549 | 0.079 | **-85.6%** |
| MDD (equity) | -17.17% | -17.90% | -4.3% |
| Avg Trade | ~10,296 | 12,758 | +23.9% |
| Max Consec Loss | — | 8 trades / -404K | — |

### Diagnosis
- Net profit increase driven by earlier entry in crash events (4H updates faster than Daily)
- Quality metrics (PF, WR, Sharpe) all deteriorated significantly
- 4H regime flips more frequently near zone boundaries → admits low-quality trades
- Sharpe collapse (0.549 → 0.079) indicates monthly return variance dramatically increased
- Recent trades (2026-07-23/24): 5 trades, 4 losses — 4H regime admitted trades Daily would block

---

## 4. Daily Bar Data Integrity Issue

### Problem identified
- Daily bars on TXF1 in MC12 exhibit irregular K-bar duplication ("不定周K棒重複出現")
- This potentially corrupts the Daily MA calculation, causing regime to get stuck or misclassify
- After switching to 4H, trades appeared after 2026-06-08 (zero trades on Daily version post-6/8 for S3_RapidPullbackShort, potentially related issue for S3_S)

### User ruling
- **Daily bar excluded** as Data3 source due to inherent data integrity issues
- 4H confirmed as direction, but MA parameters and zone boundaries need proper calibration
- Timeframe for Data2 (operation) and Data3 (observation) both remain open questions

---

## 5. Fundamental Architecture Issues Identified

### Issue 1: MA ratio noise/lag tradeoff is inherent
- Short MA = responsive but noisy (too many false regime transitions)
- Long MA = stable but laggy (same problem as Daily)
- Optimizing MA length on 4H will produce monotonically improving results with longer SlowMA
- This is curve-fitting, not genuine improvement — longer SlowMA just recreates Daily behavior

### Issue 2: Trend and volatility dimensions are independent
- Regime (MA ratio) only answers "bull or bear?" — direction dimension
- BBW percentile only answers "is bandwidth narrow?" — volatility dimension
- **No interaction between the two**: A squeeze in strong bull is treated identically to a squeeze in range
- This is confirmed as the biggest real-world problem by user observation

### Issue 3: Missing volatility path memory
- Current BBW percentile treats all squeezes equally regardless of how they formed
- "Persistent low vol" squeeze ≠ "Expansion → Contraction" squeeze
- Post-expansion squeezes are higher quality (proven market energy + institutional repositioning)
- No mechanism exists to distinguish squeeze path/quality

### Institutional regime standards (for reference)
| Level | Method | What it determines |
|-------|--------|-------------------|
| Trend direction | MA alignment / price position | Bull or Bear |
| Trend strength | ADX / MA slope / momentum | Strong trend or range |
| Volatility state | ATR range / historical vol percentile | Low/Normal/High/Crisis |
| Market structure | Higher highs + higher lows / structure breaks | Structural bull or bear |
| Statistical regime | Markov Regime Switching / GARCH | Probability-based state classification |

---

## 6. Redesign Direction (User-Confirmed)

The regime mechanism needs to answer **three questions**, not one:

| Question | Current owner | Gap |
|----------|--------------|-----|
| Direction: bull or bear? | MA ratio (crude) | No structural judgment, only two MAs |
| Volatility: contracting or expanding? | BBW percentile (independent) | No interaction with direction |
| **Volatility path: how did we get here?** | **Nobody** | Cannot distinguish persistent low-vol vs expansion→contraction |

### User requirements for redesign
1. Must have both **trend** and **structural** capability
2. Must account for volatility path (expansion → contraction = high quality)
3. Daily bar excluded — alternative timeframe required
4. Operation timeframe (Data2) open for reconsideration (60M vs 30M)
5. Observation timeframe (Data3) open for reconsideration

### Next steps
- Define what "trend + structure" means concretely for regime classification
- Design volatility path memory mechanism (detect expansion → contraction sequences)
- Choose appropriate timeframes for each dimension
- Prototype and backtest

---

## Appendix: Parameter Reference

### 4H experiment parameters (from MC12 settings sheet)
```
(45, 2.0, 120, 40, 14, 3.25, 2, 35, true, 2, 2.0, 70, 80, 85, 90, 1, false, 0.15, 4,
 true, 60, 160, true, true, 415, 1270101, false, 1230, 20, 35, 3, 2, 15, 5, 30, 3, 90,
 2.5, false, 1.3, 2200, 500, false, 2, true, 5, 1, 0, 0, false, 15)
```
Original capital: 2,000,000 NTD | Slippage: 1000/contract | Commission: none
