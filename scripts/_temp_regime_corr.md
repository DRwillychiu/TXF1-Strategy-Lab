# Regime-Based Correlation Analysis — TXF1 Strategy Portfolio

Source data: `C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json`
Strategies: **L1, L2, L3, L4, L5, S1** (6 strategies)
Date universe: union of all trade dates = **1,142 days** (2019-12-18 → 2026-06-05)

---

## 1. Regime Classification Rule

A **calendar-year proxy** is used (since TWII series is not available in the PnL file). Each trade date is mapped to one of three regimes:

| Period | Regime | Rationale |
|---|---|---|
| 2019-12 ~ 2020-06 | **range** | COVID shock / 區間震盪 |
| 2020-07 ~ 2021-12 | **bull** | 後疫情大多頭 |
| 2022 全年 | **bear** | Fed 升息循環 |
| 2023 ~ 2024 全年 | **bull** | AI 行情 |
| 2025 H1 (1-6 月) | **bull** | AI 延續 |
| 2025 H2 (7-12 月) | **bear** | Trump 關稅戰 |
| 2026 H1 | **bull** | 反彈年 |

Resulting bucket sizes (union of trade dates):

- **bull**: 787 days
- **bear**: 281 days
- **range**: 74 days

Daily PnL series: for each strategy `s` and each date `d` in the union, value = trade PnL on that day, **0 if the strategy did not trade**. Pearson correlation is then computed across the daily-PnL vectors within each regime bucket.

> Caveat: because most strategies trade only on a small fraction of days, raw correlations are compressed toward zero (sparse vectors share many `0,0` pairs). Interpretation should therefore focus on **relative** differences across regimes rather than absolute magnitudes.

---

## 2. Bull Regime Correlation Matrix (787 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.005 | +0.013 | +0.001 | -0.004 | -0.036 |
| **L2**| -0.005 | +1.000 | -0.005 | **+0.389** | -0.005 | +0.003 |
| **L3**| +0.013 | -0.005 | +1.000 | +0.015 | -0.030 | +0.078 |
| **L4**| +0.001 | **+0.389** | +0.015 | +1.000 | -0.003 | -0.016 |
| **L5**| -0.004 | -0.005 | -0.030 | -0.003 | +1.000 | +0.131 |
| **S1**| -0.036 | +0.003 | +0.078 | -0.016 | +0.131 | +1.000 |

**Bull take-aways**
- **L2 ↔ L4** are strongly co-moving (+0.389). They likely fire on the same kind of bullish-breakout setup — partial concentration risk in bull regimes.
- L5 ↔ S1 (+0.131) — both pick up momentum on trend days.
- L1 is essentially uncorrelated with the rest in bull — diversifying engine.

---

## 3. Bear Regime Correlation Matrix (281 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.003 | +0.008 | -0.000 | +0.009 | **-0.129** |
| **L2**| -0.003 | +1.000 | +0.014 | +0.045 | -0.003 | -0.013 |
| **L3**| +0.008 | +0.014 | +1.000 | -0.004 | +0.039 | +0.107 |
| **L4**| -0.000 | +0.045 | -0.004 | +1.000 | +0.001 | -0.040 |
| **L5**| +0.009 | -0.003 | +0.039 | +0.001 | +1.000 | +0.157 |
| **S1**| **-0.129** | -0.013 | +0.107 | -0.040 | +0.157 | +1.000 |

**Bear take-aways**
- The L2 ↔ L4 bond **collapses from +0.389 to +0.045** — they decouple sharply in bear regimes. Good news for portfolio risk: their joint drawdowns are mostly a bull-regime phenomenon.
- **L1 ↔ S1** becomes meaningfully negative (-0.129) — the short engine truly hedges the L1 long engine when markets are falling. Exactly the desired behavior.
- L5 ↔ S1 (+0.157) actually *strengthens* slightly — both profit from sustained downward trends.

---

## 4. Range Regime Correlation Matrix (74 days)

|       | L1     | L2     | L3     | L4     | L5     | S1     |
|-------|--------|--------|--------|--------|--------|--------|
| **L1**| +1.000 | -0.013 | -0.071 | **-0.112** | n/a | -0.045 |
| **L2**| -0.013 | +1.000 | -0.021 | +0.171 | n/a | +0.026 |
| **L3**| -0.071 | -0.021 | +1.000 | -0.041 | n/a | +0.111 |
| **L4**| **-0.112** | +0.171 | -0.041 | +1.000 | n/a | -0.089 |
| **L5**| n/a    | n/a    | n/a    | n/a    | +1.000 | n/a    |
| **S1**| -0.045 | +0.026 | +0.111 | -0.089 | n/a | +1.000 |

> L5 has **zero trades** in the range bucket (it went live 2021-09, after COVID range) — its row/column is structurally zero and excluded from interpretation.

**Range take-aways**
- L2 ↔ L4 stays positive (+0.171) but is far below the +0.389 bull reading — most of their co-movement is bull-regime breakout days.
- **L1 ↔ L4** goes mildly negative (-0.112) in range — L4 tends to chop while L1 catches the rare swing.
- S1 is mostly uncorrelated with everything in range — it just bleeds (small negative average) when there is no trend.

---

## 5. TOP 5 Pairs by Regime-Correlation Spread

| Rank | Pair | Bull | Bear | Range | Max−Min spread | Sign flip? |
|------|------|------|------|-------|---------------:|:----------:|
| 1 | **L2 ↔ L4** | **+0.389** | +0.045 | +0.171 | **0.345** | no |
| 2 | **L5 ↔ S1** | +0.131 | **+0.157** | 0.000* | 0.157 | (n/a in range) |
| 3 | **L1 ↔ L4** | +0.001 | -0.000 | **-0.112** | 0.113 | yes (range goes negative) |
| 4 | **L1 ↔ S1** | -0.036 | **-0.129** | -0.045 | 0.093 | no (negative everywhere) |
| 5 | **L1 ↔ L3** | +0.013 | +0.008 | **-0.071** | 0.084 | yes (positive→negative) |

*L5 ↔ S1 in range = 0 because L5 has no trades there.

**Interpretation of the flips**

- **L2 ↔ L4 (#1)** is the single biggest regime-dependent relationship. They look like one trade in bull markets (concentration risk), but become genuinely independent in bear and partly independent in range. Implication: position-size them as **half-pair** during bull regimes, but as full sleeves in bear/range.

- **L1 ↔ S1 (#4)** is the cleanest **hedge pair** — negative in all three regimes, *most* negative in bear (-0.129). This is the textbook long/short pair you want in the book.

- **L1 ↔ L3, L1 ↔ L4** flip sign in range — both go *negative* when L1 finally catches a swing during a quiet market while the breakout strategies whipsaw. Useful diversification but only material in range months.

---

## 6. Strategies That Thrive in Each Regime

Per-strategy stats inside each regime (n = trade count, WR = win rate, avg = mean PnL per trade):

### Bull regime (787 days)

| Strategy | Total PnL | n | WR | Avg/trade |
|---|---:|---:|---:|---:|
| **L1** | **+1,930,400** | 334 | 37.1% | +5,780 |
| L5 | +1,443,200 | 99 | 55.6% | +14,578 |
| S1 | +1,250,400 | 394 | 59.1% | +3,174 |
| L2 | +962,800 | 37 | 43.2% | +26,022 |
| L3 | +414,800 | 243 | 49.4% | +1,707 |
| L4 | +262,600 | 38 | 55.3% | +6,911 |

→ **L1 / L5 / L2** are the bull-regime workhorses. L2 has by far the highest per-trade expectancy ($26k) but trades thinly.

### Bear regime (281 days)

| Strategy | Total PnL | n | WR | Avg/trade |
|---|---:|---:|---:|---:|
| **S1** | **+305,400** | 162 | 58.0% | +1,885 |
| L2 | +291,600 | 33 | 42.4% | +8,836 |
| L1 | +214,800 | 74 | 35.1% | +2,903 |
| L5 | +164,200 | 35 | 51.4% | +4,691 |
| L3 | +96,600 | 69 | 47.8% | +1,400 |
| **L4** | **-51,200** | 31 | 61.3% | -1,652 |

→ **S1** is the dominant bear engine, as designed. **L4 is the one strategy that loses money in bear** — high WR (61%) but small wins / large losses asymmetry. Worth a deeper dive into L4's bear-regime stop logic.

### Range regime (74 days, COVID 2020 H1)

| Strategy | Total PnL | n | WR | Avg/trade |
|---|---:|---:|---:|---:|
| **L2** | **+180,400** | 8 | 25.0% | +22,550 |
| L3 | +140,400 | 23 | 65.2% | +6,104 |
| L1 | +126,800 | 21 | 33.3% | +6,038 |
| L4 | +27,200 | 7 | 57.1% | +3,886 |
| L5 | 0 | 0 | — | — |
| **S1** | **-83,400** | 38 | 50.0% | -2,195 |

→ Range months reward selective breakout-catchers (L2 with 25% WR but huge winners, L3 with 65% WR). **S1 bleeds in range** — its short-trend logic gets chopped up; this is the known weakness of trend-following short systems.

---

## 7. Robust Hedges — Pairs Negative Across All Regimes

Filtering for pairs whose correlation is **≤ 0 in bull AND bear AND range**:

| Pair | Bull | Bear | Range | Verdict |
|------|------|------|-------|---------|
| **L1 ↔ S1** | -0.036 | **-0.129** | -0.045 | True hedge — long/short engine pair, strongest in bear (as desired) |
| **L1 ↔ L5** | -0.004 | +0.009 | n/a (L5=0) | Near-zero, not a real hedge |
| **L1 ↔ L2** | -0.005 | -0.003 | -0.013 | Negligible negative — diversifier, not a hedge |
| **L3 ↔ L4** | +0.015 | -0.004 | -0.041 | Mostly uncorrelated, mild diversification |
| **L4 ↔ S1** | -0.016 | -0.040 | -0.089 | Consistent mild hedge — L4 (long-breakout) vs S1 (short-trend) |

### Conclusions

1. **The only meaningful structural hedge in the book is L1 ↔ S1.** It is negative in every regime and most negative (-0.129) in bear — exactly the asymmetry you want. Keep this as the portfolio's core balance.

2. **L4 ↔ S1** is a secondary, mild hedge (always negative, deepest in range). Useful for smoothing range-regime drawdowns where S1 bleeds.

3. **L2 ↔ L4** is **not** a hedge — it is the portfolio's biggest *concentration* in bull regimes (+0.389). If running risk parity, dial back joint exposure during confirmed bull regimes.

4. **L5 has zero range-regime data** (went live 2021-09). Any future range-regime stress test must caveat that L5's behavior in chop is unknown — recommend a synthetic 2020-style replay before sizing L5 heavily.

5. **L4 is the only strategy losing money in bear (-$51k)** despite a 61% WR — the loss-skew issue (small wins, large losses) deserves a dedicated diagnostic. This is more impactful than any correlation finding.

6. Overall regime contribution:
   - Bull (787 d) = +$6.26 M (74% of cumulative book)
   - Bear (281 d) = +$1.02 M
   - Range (74 d) = +$0.39 M

   The book is **bull-regime dominant** by construction. The bear hedge (S1 + L1 negative correlation) is functioning, but L4 and L5 need bear-regime improvement work.
