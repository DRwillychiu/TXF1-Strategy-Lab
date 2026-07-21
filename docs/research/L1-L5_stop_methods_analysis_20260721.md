# L1-L5 Initial Stop Methods Analysis — Beyond ATR

- **Date**: 2026-07-21
- **Context**: Tier 1 structural audit (P1+P3+P4 work package A) exploration
- **Prerequisite**: `docs/research/L1-L5_structural_audit_20260721.md`
- **Status**: Discussion phase — no code changes. Pending user confirmation before implementation.

---

## Framework: Rule 17 Multi-Layer Architecture

```
Layer 1 (innermost, tightest):  Structure / Pattern / Time  → catches immediate failures
Layer 2 (middle):               Fixed % or session-based    → catches trades going nowhere
Layer 3 (outermost, ATR):       ATR × multiplier            → last resort safety net

Backtest formula: Stop = Min(Layer 1, Layer 2, Layer 3)  → tightest wins
```

ATR remains the foundation (Rule 17: "ATR = last line of defense"). Inner layers provide faster exits for clearly failing trades BEFORE they reach the full ATR stop distance. This does NOT modify exit-side logic (trail, SP, BE) — it modifies the initial risk boundary.

---

## L1 TrendLong — 45M Trend Following

**Current stop**: `Max(ATR_45M × 1.5, Daily_ATR × 0.5)`, frozen. Normal ~200 pts / High vol ~400 pts

| Method | Logic | Tightness vs ATR | Top-10 Risk | Recommendation |
|--------|-------|-----------------|-------------|----------------|
| Swing low | Lowest low of last N bars (45M, e.g. N=5 ≈ 3.75 hr) below entry | 30-50% tighter | MEDIUM — early trend pullbacks may trigger | Inner defense |
| Previous day low | Prior trading day's Low as support reference | Variable ±30% | LOW — mega-trends don't break prior day low to start | Inner defense |
| Fixed % | Entry × (1 - X%). 0.5% ≈ 230 pts @ 46,000 | Similar to normal ATR | MEDIUM — tighter than ATR in high vol | Alternative |
| Daily MA20 | Daily close below MA20 AND close < entry → exit | Wider (daily scale) | LOW | Filter assist |
| Consecutive bearish bars | N consecutive 45M bars close bearish (e.g. N=3) | 40-60% tighter | HIGH — normal trend oscillations trigger | Not recommended |
| Entry bar low | Entry bar's Low on 45M | Extremely tight (50-100 pts) | HIGH — 45M noise too large | Not recommended |

**Best combination for L1**: ATR (foundation) + swing low OR previous day low (inner). Trend strategies need wide stops to survive pullbacks. Structure-based support is more meaningful than fixed % because a trend breaking its recent swing low = trend may be ending.

---

## L2 TrendShort — 60M Trend Following Short

**Current stop**: `DC_Lower + ATR × 1.1`, frozen. Normal ~155 pts / High vol ~400 pts

| Method | Logic | Tightness vs ATR | Top-10 Risk | Recommendation |
|--------|-------|-----------------|-------------|----------------|
| Swing high | Highest high of last N bars (60M) above entry | 20-40% tighter | LOW — bearish trends don't frequently make new highs | Inner defense |
| DC upper rail | Price rises to Donchian upper channel = short thesis dead | Wider (channel scale) | VERY LOW — DC upper = full trend reversal | Outer validation |
| Previous day high | Prior day's High + small buffer | 20-50% tighter | LOW | Inner defense |
| Fixed % | Entry × (1 + X%). 0.4% ≈ 184 pts | Similar to normal ATR | MEDIUM | Alternative |
| Bullish engulfing | 60M bullish engulfing pattern appears → bearish momentum gone | Situational | MEDIUM — bounce engulfing doesn't always mean reversal | Inner defense |

**Best combination for L2**: ATR (foundation) + swing high (inner). L2 trades extremely rarely (83 trades / 6.5 years), so inner defense must be very conservative to avoid reducing already sparse signals. Swing high is the most natural structural invalidation point for shorts.

---

## L3 ConsolidationLong — 15M Range Capture

**Current stop**: `Box_Btm - ATR(9,15M) × 3.0`, frozen. Normal ~150 pts / High vol ~450 pts

| Method | Logic | Tightness vs ATR | Top-10 Risk | Recommendation |
|--------|-------|-----------------|-------------|----------------|
| Box bottom (no buffer) | `Box_Btm` itself. Break below = consolidation thesis dead | 60-80% tighter | MEDIUM — false breaks below box are common in consolidation | Inner defense |
| Box bottom + small buffer | `Box_Btm - ATR(9) × 0.5` (vs current 3.0) | 50-70% tighter | LOW — retains noise room but much tighter | Inner defense |
| Fixed % | Entry × (1 - X%). 0.3% ≈ 138 pts @ 46,000 | Similar to normal ATR | LOW — consolidation strategy has no mega-winner dependency | Alternative |
| Previous session low | Prior session (day/night) lowest price | 30-50% tighter | LOW | Inner defense |
| Candlestick reversal | Bearish engulfing or long upper shadow on 15M after entry | Situational | LOW — consolidation targets are limited | Inner defense |
| Time stop | N bars (15M) without profit (e.g. N=20 ≈ 5 hr) | Time dimension | LOW — consolidation trades should resolve quickly | Inner defense |

**Best combination for L3**: ATR (foundation) + box bottom with small buffer (inner) + time stop (second inner). L3 is a consolidation strategy that does NOT depend on fat tails — Top-10 kill risk is lowest among all 5 strategies. The current ATR(9) × 3.0 multiplier is excessively wide for a consolidation thesis. This strategy is the best candidate for tighter inner stops.

---

## L4 ConsolidationShort — 15M Range Capture Short

**Current stop**: `Locked_Top + ATR(60,15M) × 2.0`, frozen. Normal ~100 pts / High vol ~200 pts

| Method | Logic | Tightness vs ATR | Top-10 Risk | Recommendation |
|--------|-------|-----------------|-------------|----------------|
| Box top (no buffer) | `Locked_Top` itself. Breakout above = short thesis dead | 50-70% tighter | MEDIUM — false breakouts above box are common | Inner defense |
| Box top + small buffer | `Locked_Top + ATR(60) × 0.5` (vs current 2.0) | 40-60% tighter | LOW — retains false-breakout tolerance | Inner defense |
| Fixed % | Entry × (1 + X%). 0.3% ≈ 138 pts | Similar to normal ATR | LOW — no mega-winner dependency | Alternative |
| Previous session high | Prior session highest price + buffer | 20-40% tighter | LOW | Inner defense |
| Bullish engulfing | 15M bullish engulfing + close > box midline → bearish momentum gone | Situational | LOW | Inner defense |
| Tighten existing time stop | Currently `Time_Stop_Bars(60)`. Consider 40 bars (≈ 10 hr) | Time dimension | LOW | Tighten existing |

**Best combination for L4**: ATR (foundation) + box top with small buffer (inner) + tighten time stop. L4's ATR(60) × 2.0 is already the mildest multiplier among all 5 strategies. However, the CS_BreakExit structural loss (P10, -377.8K = 158% of net profit) suggests the box top buffer may need smarter logic (combining volume or momentum confirmation, not just price level).

---

## L5 BreakoutLong — 15M Box Breakout

**Current stop**: `Mid/Bot - ATR(35) × 4.5`, frozen. Normal ~180 pts / High vol ~450 pts

| Method | Logic | Tightness vs ATR | Top-10 Risk | Recommendation |
|--------|-------|-----------------|-------------|----------------|
| Box bottom invalidation | For Mid entry → stop = Box_Btm. Break below = breakout thesis dead | 50-70% tighter | MEDIUM — some mega-winners retest box bottom in Stage 1 | Inner defense |
| Swing low (entry zone) | Lowest low of last 10 bars (15M, ≈ 2.5 hr) below entry | 40-60% tighter | MEDIUM — Stage 1 pullbacks may trigger | Inner defense |
| Fixed % | Entry × (1 - X%). 0.5% ≈ 230 pts / 0.3% ≈ 138 pts | 0.3% is 25% tighter than normal ATR | HIGH — 0.3% almost certainly kills some Top-10 | High risk |
| Stage-based stop | Stage 1: Box_Btm + small buffer. Stage 2: switch to trail (requires P5 fix) | Stage 1 tighter / Stage 2 dynamic | LOW — Stage 2 trail takes over protection | Staged defense |
| Bar structure break | 2 consecutive 15M lower lows + close < box midline → breakout failure | Situational | MEDIUM — needs condition tuning | Inner defense |
| Volume decay | Post-entry N bars (15M) volume consistently < 50% of entry bar → fake breakout | Situational | LOW — real breakouts sustain volume | Inner defense |
| Tighten time stop | Currently 31 bars (≈ 7.75 hr). Stage 1 could use 16 bars (4 hr) | Time dimension | MEDIUM — some mega-winners need longer gestation | Tightable |

**Best combination for L5**: ATR 4.5x (foundation) + stage-based stop (Stage 1 = box bottom + small buffer, Stage 2 = trail [requires P5 fix]) + volume decay detection (fake breakout filter). L5 is HIGHLY fat-tail dependent (88% net profit in Top-10), so fixed % is the most dangerous here. But Stage 1's thesis is "buy support in box" — the box bottom IS the natural invalidation line, allowing a much tighter stop than the current 4.5x ATR during Stage 1 specifically.

---

## Cross-Strategy Summary Matrix

| Method | L1 | L2 | L3 | L4 | L5 |
|--------|:--:|:--:|:--:|:--:|:--:|
| Structure-based (swing/box/session) | Y | Y | Y | Y | Y |
| Fixed % | ? | ? | Y | Y | N |
| Candlestick pattern | N | ? | Y | Y | Y |
| Time stop | N | N | Y | Exists | Exists |
| Volume-based | N | N | ? | ? | Y |

Legend: Y = recommended, ? = needs backtest verification, N = not suitable, Exists = already present (can tighten)

### Key Insights

1. **Structure-based stops are the universal best inner layer** — every strategy has a "thesis invalidation line" (swing point, box boundary, session extreme). These have market meaning, not just statistical calculation.

2. **Fixed % only fits consolidation strategies (L3/L4)** — they don't depend on fat tails, so truncation risk is low. L5's 88% net profit in Top-10 makes fixed % almost certainly destructive. L1/L2 need backtest verification.

3. **Candlestick patterns fit 15M strategies (L3/L4/L5), not 45M/60M (L1/L2)** — 15M generates enough bars for statistically meaningful patterns. 45M/60M bars are too few and too large for reliable pattern detection.

4. **L3 is the safest strategy to add inner stops** — no fat-tail dependency, consolidation thesis has clear invalidation points, and the current ATR(9) × 3.0 is excessively wide for a range-capture strategy.

5. **L5 benefits most from stage-based stops** — Stage 1 (pre-breakout) can use tighter box-based stops; Stage 2 (post-breakout) needs trail (P5 fix). This avoids the binary choice between "too tight kills mega-winners" and "too wide causes big losses."

---

## Next Steps

- [ ] User review and confirmation of method selection per strategy
- [ ] Design spec for work package A: risk budget gate (P1) + daily loss cap (P3) + selected inner stop methods
- [ ] Backtest impact analysis (especially Top-10 retention for L1/L5)
- [ ] Implementation (Rule 4: audit before coding, user physical verification after)

---

## Relationship to Existing Rules

- **Rule 17**: This analysis IS the Rule 17 multi-layer architecture applied to each strategy. ATR remains the outermost layer.
- **feedback_trend_let_profits_run**: Inner stops are INITIAL risk boundaries, NOT exit-side profit protection (trail/SP/BE). The permanently closed direction is trailing/SP/BE, not initial stop placement.
- **feedback_sl_fine_dining_philosophy**: "ATR = last line of defense, not primary exit mechanism." Inner layers ARE the primary mechanism.
- **feedback_target_profile_small_win_big_win**: Inner stops convert some "big losses" (full ATR hit) into "small losses" (inner layer hit), directly serving the target profile.
