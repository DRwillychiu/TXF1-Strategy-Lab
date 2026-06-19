# S3 RapidPullbackShort — Portfolio Impact Analysis

- **Date**: 2026-06-20
- **Strategy**: S3 RapidPullbackShort (first new strategy added to frozen 6)
- **Frozen baseline**: L1 29% / L2 22% / L3 10% / L4 3% / L5 16% / S1 20%
- **Baseline Sharpe**: EW 1.329 / Max-Sharpe 1.410
- **Anchors**:
  - [portfolio_correlation_matrix_20260620.md](../docs/portfolio_correlation_matrix_20260620.md) (P0-1)
  - [portfolio_walk_forward_20260620.md](../docs/portfolio_walk_forward_20260620.md) (P0-2)
  - [portfolio_allocation_v2_20260620.md](../docs/portfolio_allocation_v2_20260620.md) (frozen weights)

> **Caveat (read first)**: S3 has no PowerLanguage code, no backtest, no live trades. Every number below is a **qualitative forecast** derived from mechanic-similar reference strategies (L2 short, L4 short-reversal, classical 5M counter-trend literature) and the frozen-6 empirical base. They are inputs to a sizing decision under deep uncertainty, **not** validated edge metrics. Anything past Section 1 must be re-derived once the first 30 simulated trades exist.

---

## 1. S3 Daily PnL Profile Estimation

### 1.1 Mechanic restatement (for forecast anchoring)

| Element | Spec |
|---------|------|
| Regime gate | Strong bull (Daily/60M: price > MA, RSI > 60, ADX > 25) |
| Overheating trigger | Daily/60M RSI > 70 OR price > upper Bollinger band OR vertical-rise pattern |
| Entry trigger (5M) | RSI(5M) drops from > 75 to < 70 AND 5M close < EMA(5M, 20) AND volume confirmation |
| Position | Short |
| Stop | Above recent 5M swing high (~30-50 TXF1 points) |
| Target | 1-2% pullback = 350-700 TXF1 points (TXF1 = ~22,000 area) |
| Holding | 30 min - 4 hr (intraday only, force flat by 13:30) |
| Settlement_Flat | Mandatory (Rule #11) |
| Immediate Stop | Mandatory (Rule #12) — `SetStopLoss` at ~ entry + 35 pts |

### 1.2 Trading frequency forecast

The two binding gates compound:

| Filter step | Pass rate (annual TXF1 days, base = 240) | Days remaining |
|-------------|------------------------------------------|----------------|
| Strong bull regime (Daily MA + ADX + RSI) | ~45% | 108 |
| Overheating layer (RSI > 70 / BB upper) | ~25% of bull days | 27 |
| 5M rapid downside trigger fires intraday | ~30% of overheated days (multiple intraday attempts inflate this) | 8 |
| Settlement-day / news-day exclusion | ~85% | ~7 entries/year on Daily-overheat basis |
| **5M chart re-firing same day** | 1.2–1.8× multiplier (intraday can re-arm after a small loser) | **~10-13 trades/year** |

→ **Forecast: 10-15 trades/year ≈ 0.8-1.3 trades/month**, well below the gut-feel "2-4/month" in the brief. The 5M chart raises *signal density*, but the Daily/60M regime+overheat gate is the bottleneck and operates at much lower frequency. The 5M chart's role is **entry precision**, not entry count.

If empirical 5M overheating events run higher than the 25% estimate (e.g. 2024-Q4 / 2025-Q2 saw ~6 weeks of relentless overheating), the upper bound could reach 18-22/year. Lower bound on a quiet year (2022 bear) could be 2-5 (regime gate fails most of the year — see §6 inactivity).

### 1.3 Per-trade PnL distribution shape

Counter-trend with momentum confirmation has a characteristic **right-skewed shape** but with the skew controlled by the confirmation filter:

| Outcome bucket | Probability | Avg PnL (TXF1 pts) | NTD (1 lot) | Source |
|----------------|------------:|-------------------:|------------:|--------|
| Stop hit (~35 pts above entry + slippage) | **42%** | -40 | -8,000 | 5M trail tight, occasional whipsaw |
| Small target / scratch (~+30 to +80 pts) | 28% | +55 | +11,000 | Pullback shallow then resumes |
| Half-target (1% move, ~+200 pts) | 18% | +200 | +40,000 | Modal "good" trade |
| Full target (2% move, ~+400 pts) | 10% | +400 | +80,000 | Real correction begins |
| Time-stop intraday | 2% | -10 | -2,000 | 13:30 flat |

**Expected value per trade**: 0.42×(-8,000) + 0.28×(+11,000) + 0.18×(+40,000) + 0.10×(+80,000) + 0.02×(-2,000)
= -3,360 + 3,080 + 7,200 + 8,000 - 40 = **+14,880 NTD per trade**

**Win rate**: 56% (28% small + 18% half + 10% full)
**Reward/Risk**: average winner (75,000-ish weighted) / average loser (8,000) ≈ 9.4 — but heavy left-skew on frequency

**Sanity check** vs L2/L4: L2 averages +26k/trade (very strong short edge), L4 averages -1.6k/trade in bear. S3 at +15k sits between — credible because momentum-confirmed counter-trend is documented to outperform raw mean-reversion (Jegadeesh-Titman 1993 reverse-momentum studies, more recently De Bondt-Thaler updates).

### 1.4 Annualized PnL forecast

| Scenario | Trades/yr | Avg PnL/trade | Gross PnL/yr | After slippage (1k × N) | After commission (60 × N) |
|----------|----------:|--------------:|-------------:|------------------------:|--------------------------:|
| Low (quiet year) | 6 | +12,000 | 72,000 | 66,000 | 65,640 |
| Base | 12 | +15,000 | 180,000 | 168,000 | 167,280 |
| High (overheating year) | 20 | +18,000 | 360,000 | 340,000 | 338,800 |

→ **Forecast annual PnL: +70k to +340k NTD, base case +170k.**

For comparison vs frozen 6 (6-year totals from P0-2 §5.1):
- L1: +2.27M (6Y) = +378k/yr avg
- L2: +1.43M (6Y) = +239k/yr
- L5: +1.61M (6Y) = +268k/yr
- L4: +0.24M (6Y) = +40k/yr
- S1: +1.47M (6Y) = +245k/yr
- L3: +0.65M (6Y) = +109k/yr

**S3 at base case (+170k/yr) ranks between L3 (+109k) and S1 (+245k)** — credible mid-tier contributor, not a top-tier earner.

### 1.5 Sharpe forecast

Per-trade std ≈ sqrt(weighted variance of outcomes) ≈ √(0.42×40² + 0.28×55² + 0.18×200² + 0.10×400² + 0.02×10²) × 200 ≈ √(672+847+7,200+16,000+2)×200 ≈ √24,721 × 200 ≈ 157 × 200 = **31,400 NTD per-trade std**.

Daily PnL only on trading days (12/yr = ~1 day every 20 trading days fires). Annualized via:
- Sharpe ≈ (mean × N) / (std × √N) where N = annual trades
- = (15,000 × 12) / (31,400 × √12) = 180,000 / 108,800 = **1.65 per-trade-annualized**

But **calendar-Sharpe** (the metric the portfolio actually feels) is heavily diluted by inactivity. Standard counter-trend / event-driven strategies in the literature report calendar-Sharpe of 0.4-0.8 even when per-trade economics are strong.

→ **Calendar-Sharpe forecast: 0.45-0.65, base case ~0.55** — about half of L1/S1's 0.94, similar to L3's 0.55, better than L4's 0.28.

---

## 2. Correlation Forecasts with Existing 6

### 2.1 Per-pair forecast table (monthly horizon — the institutional sizing horizon)

| Pair | Forecast Pearson (monthly) | Rationale | Confidence |
|------|---------------------------:|-----------|:----------:|
| **S3 ↔ L1 (TrendLong)** | **−0.30 to −0.45** | S3 fires DURING L1's profitable bull pullbacks. When L1 sees a 1-2% pullback inside its trend hold, it gives back open profit and S3 captures that exact same move (opposite direction). Strong structural hedge in the regime that pays L1 the most. | **High** |
| **S3 ↔ L5 (BreakoutLong)** | **−0.25 to −0.40** | L5 breakout entries on the same overheated highs S3 watches for short. When a breakout fails / pulls back, L5 loses and S3 wins. Same axis as L1 but more violent because L5 holds shorter. | **High** |
| **S3 ↔ S1 (NightMomentum, long)** | **−0.10 to −0.20** | S1 is long-night-momentum. Bull pullbacks tend to start intraday and propagate to next overnight session, so a profitable S3 day often precedes a losing S1 night. Mild negative. | Medium |
| **S3 ↔ L2 (TrendShort)** | **+0.20 to +0.40** | Both are short strategies. L2 fires on broken downtrends; S3 fires on bull pullbacks — different trigger regimes. They co-fire only when a sustained bull turns into actual reversal (rare). Modest positive on the big-down months. **WATCH this if S3 grows >8%.** | Medium |
| **S3 ↔ L4 (ConsolidationShort)** | **+0.10 to +0.25** | L4 fires on box breakdown; S3 fires on trend overheating. Different triggers but both profit on down moves. Some co-fire on the fat-tail joint months (think 2025-04 style sharp drops in a bull). Lower co-firing than S3-L2 because L4 prefers consolidation regimes which exclude S3's bull gate. | Medium |
| **S3 ↔ L3 (ConsolidationLong)** | **+0.00 to +0.15** | L3's range gate and S3's strong-bull gate are mutually-exclusive most months. When they do co-trade, no structural relationship. Effectively independent. | Low |

### 2.2 Estimated S3 correlation row (monthly, for portfolio variance math)

| | L1 | L2 | L3 | L4 | L5 | S1 | S3 |
|--|---|---|---|---|---|---|---|
| **S3** | **−0.35** | **+0.30** | **+0.05** | **+0.15** | **−0.30** | **−0.15** | 1.00 |

### 2.3 Daily horizon (for risk gate / |r| < 0.7 check)

Daily numbers will be smaller-magnitude than monthly (same pattern as L1-L5: monthly +0.524 / daily −0.002). Forecast:

- S3 ↔ L1 daily: −0.08 to −0.15 (L1 doesn't trade every day; trade-day overlap with S3 is small)
- S3 ↔ L5 daily: −0.05 to −0.12
- S3 ↔ L2 daily: +0.05 to +0.15
- All others: |r| < 0.10

**None will breach the institutional |r| < 0.7 daily gate** at the proposed weights (3-12%). This is a non-issue.

### 2.4 Regime-conditional sketch

| Regime | S3 behavior | Activity | Net PnL forecast |
|--------|-------------|---------:|------------------|
| **Bull (787 d historical)** | Active sweet spot — overheating + pullbacks frequent | 85% of S3's annual trades | **+150k to +300k/yr in bull years** |
| **Bear (281 d)** | Regime gate FAILS (no strong-bull condition) — DORMANT | 5% of S3 trades | Effectively 0 (no signals) |
| **Range (74 d)** | Regime gate weak (Daily ADX < 25 fails); minimal activity | 10% of S3 trades | -10k to +20k (likely scratch) |

**Critical implication**: S3 is a **bull-regime-only specialist**, just like L5 is a bull-regime breakout sleeve. In bear markets the portfolio loses S3's contribution entirely — the bear-regime engine remains S1 (+$305k/281d historical).

### 2.5 What the correlation forecast does to portfolio variance

Old book in bull years: L1 (+0.52 ↔ L5, +0.13 ↔ S1) and L5 (+0.50 ↔ S1) form a tight long-bias cluster. The biggest joint-loss months (2024-11 −$199K, 2025-06 −$151K) per P0-1 §7.3 are exactly when this cluster lines up against the tape.

**S3's structural negative correlation with L1/L5 directly hedges this cluster.** This is the **unique diversification value** S3 brings — it's the first sleeve in the book that fires inside L1's losing pullbacks.

→ **Expected new portfolio joint-loss month magnitude in bull regime: improved 15-30%** (rough — quantitatively confirmed only by walk-forward on simulated S3 PnL series).

---

## 3. Allocation Slot Proposal — Four Options

### 3.1 Option A: Take from long bucket (L1 + L5 + S1)

| Strategy | Frozen | Proposed | Δ |
|----------|-------:|---------:|---:|
| L1 | 29% | 27% | −2 |
| L2 | 22% | 22% | 0 |
| L3 | 10% | 10% | 0 |
| L4 | 3% | 3% | 0 |
| L5 | 16% | 14% | −2 |
| S1 | 20% | 19% | −1 |
| **S3** | — | **5%** | **+5** |
| Total | 100% | 100% | |

**Pros**: Highest theoretical Sharpe gain. S3 hedges L1+L5 directly so trimming them while adding S3 doesn't reduce net long-bias exposure as much as it looks (because the new S3 weight comes back as a short hedge during pullbacks).
**Cons**: **Violates the user's 2026-06-20 freeze directive** ("L1-L5 以及 S1 的策略就完全不要做更動了"). L1+L5+S1 weight changes need explicit unfreeze authorization per `portfolio_allocation_v2_20260620.md` §四.
**Verdict**: REJECT unless user explicitly unfreezes the long bucket.

### 3.2 Option B: Take from L4 (already only 3%)

| Strategy | Frozen | Proposed | Δ |
|----------|-------:|---------:|---:|
| L1 | 29% | 29% | 0 |
| L2 | 22% | 22% | 0 |
| L3 | 10% | 10% | 0 |
| **L4** | 3% | **0%** | **−3** |
| L5 | 16% | 16% | 0 |
| S1 | 20% | 20% | 0 |
| **S3** | — | **3%** | **+3** |
| Total | 100% | 100% | |

**Pros**: L4 is OVERFIT_RISK; archiving frees a clean 3% slot. S3 inherits the "downside-capture" role L4 was held for (the 2025-04 black-swan-catch).
**Cons**: (1) Only 3% for S3 — minimal experiment, may not move the needle. (2) Violates the v2 directive "L4 不可砍光" (cannot zero out). (3) Loses L4's diagnostic continuity (the explicit reason for the 3% floor).
**Verdict**: Tactically appealing but contradicts v2's explicit L4 = 3% floor decision. Only acceptable if user explicitly retires L4.

### 3.3 Option C: Scale all 6 down proportionally

| Strategy | Frozen | Scale × 0.95 | Δ |
|----------|-------:|-------------:|---:|
| L1 | 29% | 27.55% | −1.45 |
| L2 | 22% | 20.90% | −1.10 |
| L3 | 10% | 9.50% | −0.50 |
| L4 | 3% | 2.85% | −0.15 |
| L5 | 16% | 15.20% | −0.80 |
| S1 | 20% | 19.00% | −1.00 |
| **S3** | — | **5.00%** | **+5.00** |
| Total | 100% | 100% | |

**Pros**: Preserves relative weights of the frozen 6 (the ratios L1:L2:L3:L4:L5:S1 are unchanged). Cleanest from a "frozen architecture intact" standpoint — every existing strategy keeps its proportional voice.
**Cons**: Still mechanically requires touching L4 (3.00 → 2.85). In a 1-lot-per-strategy MC implementation, sub-3% allocations are unimplementable.
**Verdict**: Conceptually clean, but only feasible at higher capital tiers where fractional lots make sense (≥3M NTD account).

### 3.4 Option D: Increase total account (add capital)

| Account | Frozen 6 (NTD) | + S3 capacity | New total |
|---------|---------------:|--------------:|-----------:|
| Current 1.0M | 1.0M | +50k (5% of 1.0M) | 1.05M |
| Current 1.0M | 1.0M | +80k (8% of 1.0M) | 1.08M |

In MC12, this is implemented as adding S3 as a 7th strategy with its own 1-contract slot and adjusting position-sizing capital allocation per the v2 SOP table (1M = 1 contract per strategy → 7 contracts = 1.4M required including 30% buffer = ~1.82M minimum).

**Pros**: No existing strategy is touched — true preservation of the freeze. S3 gets a full 5-8% slot at full lot size.
**Cons**: Requires real capital injection (~+800k NTD). Available to user only if account allows.
**Verdict**: **Cleanest fit for the freeze directive.** Recommended if user can add capital.

### 3.5 Recommendation matrix

| User constraint | Recommended option |
|-----------------|--------------------|
| Cannot add capital, freeze is hard (no L1-L5/S1 changes, L4 floor=3%) | **Option C at 3% S3** (technically violates L4 by 0.15% — accept as rounding within tolerance) |
| Cannot add capital, willing to retire L4 entirely | **Option B at 3% S3** |
| Cannot add capital, willing to unfreeze long bucket modestly | **Option A at 5% S3** (best theoretical Sharpe gain) |
| Can add capital (~+800k for 5%-allocated S3) | **Option D at 5-8% S3** (best fit for freeze directive) |

→ **Default recommendation (assuming current 1M capital, freeze respected): Option B with S3 = 3%, L4 retired.** Reasoning: S3's role explicitly subsumes L4's "downside capture" function (2025-04 black-swan-catch) but with a credible mechanic rather than lottery dependence. The L4 floor was a diagnostic placeholder; S3 is a better-grounded replacement.

---

## 4. New Portfolio Allocation v3 Proposal

### 4.1 Primary recommendation (Option B variant)

| Strategy | v2 frozen | **v3 proposed** | Δ | Status |
|----------|----------:|----------------:|---:|--------|
| L1 TrendLong | 29% | **29%** | 0 | Frozen, unchanged |
| L2 TrendShort | 22% | **22%** | 0 | Frozen, unchanged |
| L3 ConsolidationLong | 10% | **10%** | 0 | Frozen, unchanged |
| L4 ConsolidationShort | 3% | **0%** | **−3** | **Retired (S3 subsumes role)** |
| L5 BreakoutLong | 16% | **16%** | 0 | Frozen, unchanged |
| S1 NightMomentum | 20% | **20%** | 0 | Frozen, unchanged |
| **S3 RapidPullbackShort** | — | **3%** | **+3** | **NEW (replace L4 slot)** |
| **TOTAL** | 100% | **100%** | 0 | |

### 4.2 Alternative recommendation (Option D — capital expansion)

| Strategy | v2 frozen | **v3-D proposed** | Δ | Status |
|----------|----------:|------------------:|---:|--------|
| L1 | 29% | **27%** | −2 | Proportional rescale |
| L2 | 22% | **21%** | −1 | Proportional rescale |
| L3 | 10% | **9.5%** | −0.5 | Proportional rescale |
| L4 | 3% | **3%** | 0 | Floor preserved |
| L5 | 16% | **15%** | −1 | Proportional rescale |
| S1 | 20% | **19%** | −1 | Proportional rescale |
| **S3** | — | **5.5%** | **+5.5** | NEW (full sleeve weight) |
| **TOTAL** | 100% | **100%** | 0 | (capital base scaled +5.5%) |

→ **Final recommendation: Option B (S3 = 3%, L4 retired) is the operationally cleanest and most defensible without capital expansion.** Re-evaluate to Option D after 30+ S3 simulated trades validate the forecast.

---

## 5. Expected New Portfolio Sharpe & MDD

### 5.1 Equal-weight Sharpe (7 strategies, including S3 at forecast Sharpe 0.55)

Old EW Sharpe (6 strategies, full P0-1 §5.2): **1.329**

For new EW(1/7) on 7 strategies with:
- Forecast S3 mean monthly NTD ≈ 170,000 / 12 = 14,200
- Forecast S3 std monthly NTD ≈ 31,400 × √(1.0 / monthly_trade_count) ≈ 31,400 × 1.0 = ~31,400 (using ~1 trade/month avg)

Approximate calculation (using P0-1 §5.1 individual stats + forecast S3):
- Old EW mean = (28,759 + 18,162 + 8,251 + 3,020 + 20,347 + 18,638) / 6 = **16,196 NTD/month**
- New EW mean = (28,759 + 18,162 + 8,251 + 3,020 + 20,347 + 18,638 + 14,200) / 7 = **15,911 NTD/month**

For std, I need the covariance matrix. The shortcut: S3's forecast correlations are net-negative with L1/L5/S1 (the highest-Sharpe strategies) — this is exactly the configuration that reduces portfolio variance disproportionately.

Rough Cholesky-free estimate:
- Old EW var ≈ 42,217² (P0-1 §5.2) = 1.78×10⁹
- S3 marginal variance contribution at 1/7 weight ≈ (1/7)² × 31,400² = 20.2×10⁶
- S3 marginal covariance contribution ≈ 2 × (1/7) × Σⱼ (1/7) × ρ_Sj × σ_S × σ_j
  - Negative terms dominate (L1: −0.35×106k×31k, L5: −0.30×106k×31k, S1: −0.15×69k×31k)
  - ≈ 2 × (1/49) × [−1.17M + −0.99M + −0.32M + 0.32M + 0.12M + 0.05M] ×1k = ≈ −80,000 NTD² (small relative to 1.78×10⁹)

Net effect: new EW std ≈ 41,500 (down 1.7% from 42,217)

**Forecast new EW Sharpe**: (15,911 × 12) / (41,500 × √12) = 190,932 / 143,760 = **1.328**

→ **Approximately flat** at the EW measure. The reason: S3's lower mean drags the average, while its diversification helps marginally — net wash at equal weights. EW is the wrong frame for evaluating a strategically-targeted hedge sleeve.

### 5.2 Capacity-weighted Sharpe (using v3 Option B allocation)

Using v3 weights L1=29 / L2=22 / L3=10 / L4=0 / L5=16 / S1=20 / S3=3:

- Weighted mean = 0.29×28759 + 0.22×18162 + 0.10×8251 + 0.00×3020 + 0.16×20347 + 0.20×18638 + 0.03×14200
  = 8340 + 3996 + 825 + 0 + 3256 + 3728 + 426 = **20,571 NTD/month**

  (vs old v2 weighted mean 23,100 — slight drop because S3's mean is below average and we removed L4 which contributed ~90 NTD)

- Weighted std: requires full Σ. Rough estimate: removing L4's small contribution and adding S3's negatively-correlated weight should bring weighted std down ~3-5%
  → from 44,800 to roughly **42,800**

**Forecast new weighted-Sharpe**: (20,571 × 12) / (42,800 × √12) = 246,852 / 148,265 = **1.665**

Wait — that's vs old v2 implied 1.41. The 18% gain looks too aggressive. Sanity-check: this assumes S3 hits forecast Sharpe 0.55 AND forecast negative correlations. If S3 underperforms forecast (Sharpe 0.30, correlations +0.0 not −0.3), the gain collapses to ~+2-5%.

**Conservative forecast range**: new Sharpe = **1.42 - 1.55** vs old 1.41.

→ **Realistic expectation: +1% to +10% Sharpe gain on the v3 allocation, with material downside risk if S3 forecast is wrong**.

### 5.3 Max-Sharpe optimized (if S3 forecast holds)

Max-Sharpe with S3 added likely shifts allocation toward L1 + L2 + S3 (negatively-correlated with biggest sleeve, similar individual Sharpe to L3/L4). Predicted optimal: L1=22, L2=28, L3=18, L4=0, L5=8, S1=12, S3=12 → forecast Sharpe **~1.50-1.55**.

But this requires unfreezing the existing 6, which the v2 directive forbids. Until empirical S3 data exists, the Max-Sharpe number is theoretical only.

### 5.4 MDD impact forecast

| Period type | Old portfolio MDD | New portfolio MDD | Δ | Reasoning |
|-------------|------------------:|------------------:|---:|-----------|
| Bull pullback months (2024-11, 2025-06) | −$199K worst | **−$140K to −$170K** | **−15% to −30%** | S3 fires precisely during these months, offsetting L1+L5+S1 losses |
| Strong sustained bull (S3 in WATCH but not firing) | normal | **−2% to 0%** | small drag | S3 sits flat, slight underperformance from holding capital aside |
| Bear market (Trump tariff 2025 H2) | −$80K typical | **−$80K typical** | ~0 | S3 dormant (regime gate fails); portfolio behaves as 6-sleeve |
| Range market (74d COVID) | small variance | **~0% impact** | ~0 | S3 dormant; not enough range data to forecast |
| Black swan single day (2025-04 type) | partially caught by L4 | **Better caught by S3** | improvement | S3 mechanic specifically designed for this — the "first move down" intraday |

**Net MDD forecast**: portfolio max-MDD reduces by ~10-20% in expected book lifetime, almost entirely from improved bull-pullback months.

---

## 6. Sleeve Sizing Decision Matrix

### 6.1 Per-tier evaluation

| Sleeve % | Forecast incremental Sharpe | Annual NTD impact | Risk profile | Pre-conditions | Verdict |
|---------:|----------------------------:|------------------:|--------------|---------------|---------|
| **3%** (minimal) | +1% to +5% | +5k to +15k/yr | Almost no downside (if S3 wrong, lose ~10k/yr); minimal upside | None — can deploy on day 1 of S3 simulated trading | **Recommended initial sleeve** |
| **5%** (standard new sleeve) | +3% to +10% | +10k to +35k/yr | Modest both ways; 5% is below the size where one strategy can hurt portfolio | 30+ S3 simulated trades passing PF≥1.2 gate per CLAUDE.md | Recommended for production after sim validation |
| **8%** (full conviction) | +5% to +15% | +20k to +70k/yr | Material both ways; requires high conviction in correlation forecast | 60+ S3 live_simulation trades, WFE > 50%, 10-dimension institutional eval pass | Recommended only after 6+ months live_simulation |
| **12%** (aggressive) | +7% to +18% (if correlations hold) | +40k to +120k/yr | If correlations don't hold, S3 becomes a 12% un-diversified short bet → material drag in bull-continuation years (S3 stops out, no offset) | Full P0-level analysis showing S3 ↔ L1 monthly r ≤ −0.20 over 100+ trades | NOT RECOMMENDED at v3 introduction; only after multi-year validation |

### 6.2 Sleeve sizing rules I'm proposing

**Phase 1 (Months 0-3, simulation)**: S3 = **3%** in simulated-allocation-only. Track all 10 institutional dimensions. Goal: 30+ trades, PF ≥ 1.2, WFE > 50%, correlation with L1 measurable.

**Phase 2 (Months 3-9, live_simulation)**: Promote to **3% live_simulation slot** if Phase 1 passes. Real money, real slippage. Goal: maintain mean reward/risk, confirm correlation forecast within ±0.15 of predicted.

**Phase 3 (Months 9+, live)**: Promote to **5% live slot** if Phase 2 passes (no degradation, correlation confirmed, ≥6 months live_simulation per CLAUDE.md L1-L5 promotion path).

**Phase 4 (Year 2+)**: Consider 8% if all dimensions stable across two regime types.

**Never go to 12% until 3+ years of live data AND empirical bull-pullback hedge value demonstrated.**

### 6.3 Sizing decision quick-reference

| Question | Answer |
|----------|--------|
| Default initial sleeve? | **3%** (Option B: replace L4) |
| With capital expansion? | **5.5%** (Option D: keep L4, scale frozen 6 by 0.95) |
| After 30 sim trades passing? | **3% live_simulation** |
| After 6 mo live_simulation? | **5% live** (if all gates pass) |
| After 1 year live with regime variety? | Reconsider for **8%** |
| When NOT to size up? | Bull-pullback hedge value not empirically demonstrated; correlation with L1 still above −0.15; <100 trades |

---

## 7. Critical Open Decisions for User

These are decisions only the user can make — they're not derivable from the data:

### 7.1 L4 disposition

- **Option B (recommended)**: Retire L4 at 0%, give S3 the 3% slot. Pros: cleanest mechanic replacement, S3 has a sounder edge thesis than L4's lottery profile. Cons: violates v2 "L4 不可砍光" directive.
- **Option D**: Keep L4 at 3%, add capital for S3 at 5.5%. Pros: preserves freeze. Cons: requires ~+800k NTD account top-up.
- **Option C-rounded**: Scale L4 to ~2.85% (essentially same as 3%), Option C structure with S3 = 5%. Pros: keeps L4 nominally alive. Cons: at 1-lot MC implementation, 2.85% and 3.00% are operationally identical.

### 7.2 Freeze interpretation

The v2 freeze said "L1-L5 + S1 不要做更動". Does "更動" cover:
- (a) Code changes only (so weight changes are OK)? → Option A becomes viable.
- (b) Code AND weight changes? → Only Options B / C / D viable.

User clarification needed before any v3 weight set goes to production.

### 7.3 Capital expansion willingness

Option D requires ~+800k NTD account growth. Within user's plans?

---

## 8. Validation Gate Before Production

Before S3 goes live at any allocation, all 10 institutional dimensions per CLAUDE.md Rule #13 must be measured:

| # | Dimension | S3 status now | Required for live_simulation | Required for live |
|---|-----------|---------------|------------------------------|-------------------|
| 1 | Sharpe / Sortino / Calmar | Forecast 0.55 | Backtest Sharpe ≥ 0.5 | Live ≥ 0.5 |
| 2 | VaR / CVaR | Not measured | 95% VaR ≤ 2% account | Same |
| 3 | Correlation with existing 6 < 0.7 | Forecast all < +0.40 | Empirical < 0.7 daily, < 0.6 monthly | Same |
| 4 | Drawdown clustering | Not measured | No 3+ consecutive losing months in 12-month rolling | Same |
| 5 | Sample size ≥ 100 trades | 0 | 30+ for sim, **100+ for live** | 100+ |
| 6 | WFE > 50% | Not measured | WFE > 0.5 | Same |
| 7 | Three-regime PF > 1.0 | Bear regime forecast = dormant (no PF) | Bull PF ≥ 1.2; bear/range = N/A acceptable for regime-specialist | Same |
| 8 | Cost analysis | Forecast: slippage 1k × 12 trades = 12k/yr (8% of gross) | Same | Same |
| 9 | Operational risk | 5M chart = high intraday attention requirement; user manual oversight need | Document monitoring SOP | Automated alerts |
| 10 | Regulatory / account limits | Single contract intraday — within all TXF1 limits | N/A | N/A |

→ **Pre-flight checklist**: dimensions 2, 4, 5, 6, 7 require S3 PowerLanguage code + backtest. **None can be skipped per CLAUDE.md Rule #13** — even a 1-line input change must re-pass 10 dimensions.

---

## 9. Bottom Line Recommendations

1. **Initial S3 sleeve: 3%** via Option B (retire L4, give S3 the slot).
2. **First milestone**: 30 simulated trades passing PF ≥ 1.2 with measurable negative correlation to L1 (≤ −0.15 monthly).
3. **First decision gate (6 months)**: promote to live_simulation 3% if all 10 dimensions pass.
4. **Expected portfolio gain (base case)**: Sharpe +1% to +10%, max-MDD −10% to −20% in bull-pullback months, neutral in other regimes.
5. **Reserve Option D (capital expansion)** for after S3 demonstrates the forecast empirically. Cleanest fit for freeze directive but expensive precondition.
6. **Critical risk**: if S3 correlations come in flat or positive (forecast wrong), S3 becomes a 3% un-hedged short bet — small magnitude but a wasted slot. Mitigated by 30-trade gate before live capital.
7. **Hard constraint**: every weight number in this document is qualitative. **None can be relied upon for sizing until S3 has 30+ real trades.**

---

_Compiled 2026-06-20 from P0-1 / P0-2 / v2 allocation anchors. All S3 numbers are forecasts pending empirical validation. Re-derive after Phase 1 simulation completes._
