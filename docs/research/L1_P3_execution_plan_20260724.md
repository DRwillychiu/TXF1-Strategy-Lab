# L1 P3 Execution Plan — 2026-07-24

> Framework: Adversarial Engineering SOP (Step 0 self-verification + Step 7 Before/After/Expected).
> Input: L1_P3_initial_SL_architecture_20260723.md (design spec) + L1_v3.0_backtest_analysis_20260723.md (baseline).
> Output: per-layer task breakdown, verification criteria, expected results, alternative angles.
> Status: PLANNING ONLY. No code changes until user ruling on Section 9 questions.

---

## 0. Adversarial Pre-check (Step 0 of SOP)

Assume the entire 4-layer plan is wrong. Answer 3 questions before any layer is executed.

| # | Question | Answer |
|---|----------|--------|
| Q1 | If the whole plan is wrong, worst outcome? | Layer 1b becomes the 35th sealed "SL tighten" variant. Layer 1 becomes ATR-in-disguise. Net effect = same or worse than V3.0 T200 baseline, wasted 1-2 weeks. |
| Q2 | What evidence would prove it wrong? | (a) Corr(10-day pullback, ATR20) > 0.85 → Layer 1 = ATR reskin. (b) Layer 1b halving fires < 20 times over 2020-2026 → statistically insignificant. (c) Backtest Net Profit within +/-10% of baseline → no signal. (d) MDD reduction < 15% while trade PnL degrades > 5% → wrong tradeoff. |
| Q3 | Rollback path? | Baseline commit `18facd4` (V3.0 T200). Full revert via `git revert`, restore all L1 .pla to that state. |

### Bug propagation between stages

| Stage → Stage | Assumption inherited | Independent verification |
|---------------|----------------------|--------------------------|
| Layer 1 formula → Layer 1b threshold | Layer 1b threshold = SL × 20%, so if Layer 1 formula is wrong, Layer 1b threshold is also wrong | Test Layer 1b independently with fixed-distance SL (e.g., 200 pts) first, isolate the trigger logic from the SL magnitude |
| Layer 1 backtest → Full architecture | Layer 1 alone must beat baseline BEFORE adding Layer 1b | Two-stage validation: {L0+L1 only} vs {L0+L1+L1b}. If L1 alone regresses, do NOT stack L1b on top. |

---

## 1. Sealed Items Compliance Check (Data Death Penalty)

Per architecture spec (line 14-21), the following are permanently sealed. Any element of the new plan must be checked against these to avoid becoming variant #35.

| Sealed Item | Layer 1 exposure? | Layer 1b exposure? | Verdict |
|-------------|-------------------|--------------------|---------|
| 停損收緊 34 variants | Layer 1 REPLACES ATR — not a "tighten" | Layer 1b IS a tighten mechanism | ⚠️ **HIGH RISK — see Section 5** |
| Fixed point % cap | Layer 1 uses recent pullback × ratio, not fixed % | N/A | LOW |
| Daily cap (V2.8) | N/A | N/A | LOW |
| P3b buffer | N/A | N/A | LOW |
| Narrow-range reclaim | N/A | N/A | LOW |
| Broad re-entry (Plan C) | N/A | N/A | LOW |

**Critical question to user**: The 34 sealed "tighten" variants — did any include a K-bar behavioral trigger (連三黑 / engulfing / MA break)? If YES, Layer 1b is likely variant #35 and should be rejected pre-implementation. If NO (all 34 were price-based, time-based, or point-based), Layer 1b's behavioral trigger is genuinely novel and worth testing.

**Verification action**: grep `docs/research/L1_stop_forensics_20260722.md` and `L1_stop_mechanism_deep_research_20260722.md` for "engulfing", "consecutive", "K-bar", "pattern", "behavioral" to confirm sealed-list coverage. **Do this BEFORE any code work.**

---

## 2. Baseline (T200, V3.0, 2019-12-16 to 2026-07-23)

Reference numbers for all Before/After comparisons.

| Metric | Value |
|--------|-------|
| Net Profit | 2,074,000 TWD |
| Profit Factor | 1.348 |
| MDD | -493,200 (-21.7%) |
| Trades | 508 |
| Win Rate | 36.4% |
| Avg Win | +217 pts |
| Avg Loss | -93 pts |
| EV / trade | +20.4 pts |
| Sharpe | 0.879 |

### Loss Composition (bleed sources)

| Exit label | Count | Total loss (pts) | Total loss (TWD) |
|------------|-------|------------------|------------------|
| TL_SL | 258 | -24,252 | -4,850,400 |
| TL_TSL | 31 | -2,852 | -570,400 |
| TL_SL_Gap | 25 | -2,625 | -525,000 |
| **Loss subtotal** | **314** | **-29,729** | **-5,945,800** |

**P3 optimization target**: reduce TL_SL total loss without cannibalizing TL_SP (P7, +150 avg) or TL_TP (P4, +241 avg).

---

## 3. Layer 0 — ATR Wall (existing, retain)

**No changes.** Currently `min(ATR20_45M × 1.5, Daily_ATR20 × 0.5)`, frozen at entry.

Verification-only tasks:
- Confirm Layer 1 output is always tighter than Layer 0 in ≥ 95% of trades. If Layer 1 is wider more than 5% of the time, Layer 0 becomes binding too often → Layer 1 is not doing its job.
- Metric to log: `layer0_binding_ratio = (# trades where Layer 0 < Layer 1) / total trades`. Target < 5%.

---

## 4. Layer 1 — Primary SL (Recent Pullback Amplitude)

### 4.1 Open questions from architecture spec

| # | Question | Options |
|---|----------|---------|
| Q1.1 | "Recent 10-day pullback" — exact definition? | (a) 10-day max peak-to-trough (b) 10-day max daily range Hi-Lo (c) 10-day max close-to-close drawdown (d) 10-day percentile P75 of daily ranges |
| Q1.2 | Ratio applied to pullback? | (a) 0.5 (b) 0.7 (c) 1.0 (d) sweep |
| Q1.3 | Floor minimum? | (a) 150 pts (b) 200 pts (c) 0.4% of entry price (d) tie to Layer 0 minimum |
| Q1.4 | Frozen at entry, or refreshed each bar? | Frozen (per spec). If refreshed, complicates Layer 1b halving flag semantics. |
| Q1.5 | Lookback window? | (a) 10 days (per spec) (b) 5 days (c) 20 days (d) sweep |

### 4.2 Execution tasks (in dependency order)

| # | Task | Estimated time | Dependency |
|---|------|----------------|------------|
| T1.1 | Correlation study: 10-day max pullback vs ATR20 on Data2, 2020-2026 | 30 min (Python) | None |
| T1.2 | If Corr > 0.85 → **STOP and reconsider**. Layer 1 is ATR reskin. | Immediate ruling | T1.1 |
| T1.3 | Compute 4 candidate Layer 1 formulas (Q1.1 options a-d) on historical daily data. Plot distributions vs ATR20. | 45 min (Python) | T1.1 |
| T1.4 | User rules on formula choice (Q1.1) | Blocking on user | T1.3 |
| T1.5 | Parameter sweep: ratio × floor × window (Q1.2, Q1.3, Q1.5) using Python daily proxy | 2 hr | T1.4 |
| T1.6 | Select top 3 param combos from sweep | Analysis | T1.5 |
| T1.7 | Implement Layer 1 in .pla (V3.1) — no Layer 1b yet | 1 hr coding + 30 min ASCII/Rule#11-15 check | T1.6 |
| T1.8 | MC12 full backtest V3.1 (Layer 0 + Layer 1 only), 3 param combos | 3 x 15 min = 45 min | T1.7 |
| T1.9 | If V3.1 does NOT beat V3.0 baseline on Net Profit AND MDD → **STOP**. Layer 1 is not helping. | Ruling | T1.8 |

### 4.3 Verification criteria (Layer 1 in isolation)

| # | Criterion | Threshold | Rationale |
|---|-----------|-----------|-----------|
| V1.1 | MDD reduction | ≥ 15% (from -493K to ≤ -420K) | If < 15%, complexity not justified |
| V1.2 | Net Profit degradation | ≤ 5% (≥ 1,970,000 TWD) | Trading MDD for PnL is acceptable up to 5% |
| V1.3 | PF change | ≥ 1.30 (was 1.348) | Small degradation OK, structural degradation NOT |
| V1.4 | TL_SL avg loss magnitude | ≤ -80 pts (was -94) | Direct proof Layer 1 tightens the average loss |
| V1.5 | Trade count change | +/- 10% (458 to 559) | Sudden trade count spike = Layer 1 firing too often |
| V1.6 | Sample cross-year distribution | Every year 2020-2025 not < -50% of baseline | Prevents recent-year overfit |
| V1.7 | Parameter plateau width | Ratio +/- 20% same-direction result | Peak = overfit; plateau = robust |
| V1.8 | Layer 0 binding ratio | < 5% | See Section 3 |

### 4.4 Before / After / Expected (Layer 1 alone)

| Metric | Before (V3.0 T200) | After (V3.1 estimate) | Confidence | Source |
|--------|--------------------|-----------------------|-------------|--------|
| Net Profit | 2,074K TWD | 1,950K - 2,100K | **Low** | Python proxy only, no MC12 native |
| PF | 1.348 | 1.30 - 1.40 | Low | Same |
| MDD | -493K (-21.7%) | -380K to -450K (-17% to -20%) | **Medium** | Directional confidence high, magnitude Low |
| TL_SL avg | -94 pts | -70 to -85 pts | Medium | Direct effect of tighter Layer 1 |
| TL_SL count | 258 | 260 - 300 | Medium | Tighter SL fires more often |
| Trades | 508 | 500 - 560 | Low | Depends on re-entry effect |

**Confidence disclaimer**: All "After" numbers assume Python daily proxy is representative. MC12 native backtest with Bar Magnifier 1 Min will produce the real numbers. Do not treat these as commitments.

---

## 5. Layer 1b — Behavioral Tightening

### 5.1 ⚠️ Sealed-item compliance red flag

Per Section 1: Layer 1b IS a "tighten" mechanism. Sealed list has 34 tighten variants. **Layer 1b must prove genuine novelty against the sealed list, or it is variant #35 by default.**

**Blocking action before any Layer 1b code work**: verify against sealed list (see Section 1 verification action). If not novel → skip Layer 1b entirely, ship Layer 1 only.

### 5.2 Open questions from architecture spec

| # | Question | Options |
|---|----------|---------|
| Q1b.1 | 連三黑 threshold (total decline) | (a) SL × 20% (b) SL × 30% (c) 50 pts (d) 0.15% of entry |
| Q1b.2 | Engulfing avg body window | (a) 10 bars (b) 20 bars (c) 5 bars |
| Q1b.3 | Engulfing body multiplier | (a) 2.0x (b) 1.5x (c) 3.0x |
| Q1b.4 | Fire on Trigger A OR B (per spec) or require confluence? | (a) OR (per spec) (b) require confluence (higher bar, fewer false halvings) |
| Q1b.5 | Halved SL new location — from Entry, or from current price? | (a) Entry - (SL/2) per spec (b) Current price - some buffer |
| Q1b.6 | If Layer 1b fires on the entry bar itself (entry K-bar is 3rd bearish), fire or not? | (a) Fire (spec) (b) Suppress until N bars after entry |

### 5.3 Execution tasks

| # | Task | Estimated time | Dependency |
|---|------|----------------|------------|
| T1b.1 | **Blocking**: sealed-list novelty check (see Section 1 action) | 30 min grep + user ruling | None |
| T1b.2 | If sealed → SKIP everything below, close Section 5 | Immediate | T1b.1 |
| T1b.3 | Statistical significance: count expected Layer 1b fires 2020-2026 with default params | 30 min (Python on 45M bars) | T1b.1 |
| T1b.4 | If expected fires < 20 → statistically thin, reconsider | Ruling | T1b.3 |
| T1b.5 | Fire-quality study: for each expected fire, look at next 20 bars — how often did the halved SL trigger? How often did we abort a winner? | 1 hr | T1b.3 |
| T1b.6 | Parameter sweep on Q1b.1, Q1b.2, Q1b.3 | 1.5 hr (Python) | T1b.5 |
| T1b.7 | Implement Layer 1b in .pla (V3.2 = V3.1 + Layer 1b) | 1 hr coding + verification | T1b.6 |
| T1b.8 | MC12 full backtest V3.2 (3 param combos) | 3 x 15 min = 45 min | T1b.7 |
| T1b.9 | Compare V3.2 vs V3.1 (Layer 1b marginal effect) | 30 min analysis | T1b.8 |
| T1b.10 | If V3.2 does NOT beat V3.1 → SHIP V3.1 without Layer 1b | Ruling | T1b.9 |

### 5.4 Verification criteria (Layer 1b marginal contribution)

| # | Criterion | Threshold |
|---|-----------|-----------|
| V1b.1 | V3.2 Net Profit vs V3.1 | ≥ +3% marginal gain |
| V1b.2 | V3.2 MDD vs V3.1 | ≥ 5% additional reduction |
| V1b.3 | Winner cannibalization rate | < 15% of TL_SP + TL_TP trades affected |
| V1b.4 | Layer 1b fire count | 20 - 60 fires over 2020-2026 |
| V1b.5 | Fire → halved SL trigger ratio | > 40% (proves fire was meaningful) |
| V1b.6 | Fire → immediate rebound (halved SL not triggered) ratio | < 40% (limits false-halving damage) |

### 5.5 Before / After / Expected (Layer 1b marginal, on top of Layer 1)

| Metric | V3.1 (L1 only, estimate) | V3.2 (L1 + L1b, estimate) | Confidence | Rationale |
|--------|--------------------------|---------------------------|-------------|-----------|
| Net Profit | 2,000K | 2,050K - 2,120K | **Very low** | Depends heavily on false-halving rate |
| MDD | -420K | -370K - -400K | Low | If Layer 1b works, this is where the gain shows |
| Trades | 530 | 530 (Layer 1b doesn't change entry) | High | Layer 1b only affects exits |
| TL_SL avg | -78 pts | -60 to -75 pts | Low | Tighter halved SL catches more medium losses |

**Explicit uncertainty**: Layer 1b is the highest-risk element in this plan. It could easily be net-negative if false halvings kill winners more than true halvings save losers. **Do not commit to Layer 1b before T1b.5 (fire-quality study) confirms the fire pattern is sound.**

---

## 6. Alternative Angles (Innovation / Out-of-box)

Per user directive: "不斷進行假設以及提出創新跳脫思維的邏輯方式". Six alternative framings to challenge the current design.

### A. Regime-first vs Layer-based

**Current design**: One 4-layer stack for all market conditions.
**Alternative**: Classify regime at entry (trending / choppy / shock), apply different SL rules per regime.
- Trending: wide Layer 1, no Layer 1b
- Choppy: tight Layer 1, aggressive Layer 1b
- Shock: Layer 0 only, other layers disabled

Pro: Directly addresses "same ATR means different things in different regimes."
Con: Regime classifier itself is a new overfit surface.
Recommendation: Backlog. Test after V3.2 is baseline-locked.

### B. Percentile vs Max (Layer 1 formula)

**Current design**: Layer 1 uses 10-day MAX pullback.
**Alternative**: Use P75 or P90 of daily ranges over 20 days.

Pro: Max is a single extreme point → sensitive to one outlier day. Percentile is robust.
Con: Still a volatility proxy — may not decouple from ATR.
Recommendation: **Include as Q1.1 option (d)**. Cost: adding one more sweep dimension.

### C. Absolute % + Volatility Dual Constraint

**Current design**: Layer 1 = recent pullback × ratio (volatility-based).
**Alternative**: `SL = min(entry × K1%, ATR × K2)` — hard cap by % of price.

Pro: Directly solves the "% varies across index levels" root cause.
Con: K1 is a new fixed-percent parameter → **may fall under Sealed Item "Fixed point % cap"**. Requires sealed-list confirmation.
Recommendation: Confirm sealed-list status before spending time.

### D. Volume-weighted Behavioral Signal

**Current design**: Layer 1b fires on 連三黑 by price pattern only.
**Alternative**: 連三黑 with expanding volume = real distribution (fire). 連三黑 with shrinking volume = meaningless (skip).

Pro: Signal quality much higher.
Con: Requires Volume data on Data1 (already available in MC12 for TXF1). Adds one condition.
Recommendation: **Include as Q1b.7 (new option)**. Low cost to test.

### E. MA Break vs K-bar Pattern

**Current design**: 連三黑 / engulfing K-bar patterns.
**Alternative**: 45M MA20 breaks below Close during hold → weakness signal.

Pro: More systematic, less pattern-recognition noise.
Con: MA break is a lagging indicator.
Recommendation: **A/B backtest as Q1b.8**. Compare fire quality vs K-bar pattern.

### F. Time-of-day Conditional SL

**Current design**: Same SL regardless of entry time.
**Alternative**: Open 30 min = wider Layer 1; midday = tighter; night session = ATR-only.

Pro: TXF1 known intraday volatility structure justifies this.
Con: New parameter dimension, easy to overfit.
Recommendation: Backlog. Post-V3.2.

### G. Removal Test: {L0 + L1 only} vs {L0 + L1 + L1b}

**Current design**: All 3 layers stacked.
**Alternative**: Test if Layer 1b adds ANY marginal value. If not, ship without it.

Pro: Occam's razor. Simpler = fewer future maintenance risks.
Con: None.
Recommendation: **This is already built into the plan (T1b.10). Enforce strictly.**

---

## 7. Today-Executable vs Multi-day Split

**User request**: "希望今天就能測試完成". Reality check.

### Executable today (2026-07-24, single day)

| Task | Duration | Deliverable |
|------|----------|-------------|
| T1b.1 Sealed-list novelty check | 30 min | User ruling on Layer 1b viability |
| T1.1 Correlation study L1 vs ATR | 30 min | Corr coefficient; keep-or-kill decision on Layer 1 |
| T1.3 4 formula candidates plot | 45 min | Distribution comparison |
| T1.4 User rules on Q1.1 | Live discussion | Formula lock |
| T1.5 Layer 1 param sweep (Python proxy) | 2 hr | Top 3 param combos |
| T1b.3 Layer 1b fire count study | 30 min | Statistical viability check |
| T1b.5 Fire-quality study | 1 hr | Fire vs winner cannibalization ratio |

**Total: ~5.5 hr of Python analysis + user decisions.** Realistic for one day.

### Not-today (multi-day)

| Task | Reason |
|------|--------|
| T1.7 .pla implementation V3.1 | Requires Q1.1-Q1.5 fully locked; can start end-of-day if ruling comes in |
| T1.8 MC12 backtest V3.1 | User runs manually in MC12 (not automatable from here) |
| T1b.6-1b.10 Layer 1b full pipeline | Depends on T1.8 result and sealed-list ruling |
| Full architecture validation + PROMOTE checklist | Multi-day per Rule #19 |

**Verdict**: One day is NOT enough for full test-to-ship. One day IS enough for the analytical foundation and go/no-go on Layer 1 formula + Layer 1b viability.

---

## 8. "最理想?" Judgment — Default = NO

Per SOP Step 7 rules. This plan is NOT yet "最理想" and cannot be claimed as such until:

**Blockers to "最理想" claim:**

1. Sealed-list novelty check for Layer 1b — undone
2. Corr study for Layer 1 vs ATR — undone
3. MC12 native full backtest (not Python proxy) — undone
4. Cross-year decomposition (2020-2025 individually) — undone
5. Parameter plateau confirmation — undone
6. User ruling on Q1.1 through Q1b.6 — pending
7. Rule #18 5-piece validation (MC + Bootstrap + Stress + Regime + Robust) — post-implementation

**Residual risks:**
- Layer 1 may be ATR reskin (Q1 in Section 0)
- Layer 1b may be sealed variant #35 (Section 5.1)
- Python daily proxy accuracy vs MC12 IOG with 1M Bar Magnifier is unknown
- Backtest range 2020-2026 is only 1.5 index cycles (12K to 48K)

**Necessary conditions to claim "ship-ready":**
1. All 6 blockers resolved
2. Rule #19 PROMOTE_CHECKLIST 6-item pass
3. Rule #16 5-pillar engineering check
4. Rule #13 10-dimension institutional risk
5. User explicit ruling ("promote V3.x to live_simulation")

Execution flow explicitly must NOT auto-claim ship-ready.

---

## 9. Three Blocking Questions for User Ruling

Before starting T1.1 today:

**Q-USER-1**: Do you want me to run T1b.1 (sealed-list novelty check) FIRST, or trust the architecture spec's assertion that Layer 1b is novel and proceed to formula work?

Rationale: If sealed variant #35, all Layer 1b work is wasted. 30-min check upfront is cheap insurance.

**Q-USER-2**: For Layer 1 formula (Q1.1 options a-d in Section 4.1), do you want:
- (i) me to run all 4 options and let the correlation/distribution data decide
- (ii) you pre-select 1-2 to focus on, saving time

Rationale: (i) = more robust, 45 min more Python work. (ii) = faster if user has strong prior.

**Q-USER-3**: Alternative Angles B (Percentile), D (Volume-weighted), E (MA-break) — include in today's sweep or backlog?

Rationale: Each adds ~30 min of analysis. Broader net = better; more options = more decision fatigue.

---

## Appendix — File / Rule References

- Baseline: `strategies/live/L1_TrendLong.pla` (commit 18facd4)
- Architecture spec: `docs/research/L1_P3_initial_SL_architecture_20260723.md`
- Backtest analysis: `docs/research/L1_v3.0_backtest_analysis_20260723.md`
- Forensics (loss origin): `docs/research/L1_stop_forensics_20260722.md`
- Deep research (SL mechanisms): `docs/research/L1_stop_mechanism_deep_research_20260722.md`
- SOP: `.claude/skills/adversarial-engineering-sop`
- Rules invoked: #11 Settlement_Flat, #12 SetStopLoss, #13 Institutional risk, #15 ASCII, #16 5-pillar, #17 Multi-layer SL SOP, #18 5-piece validation, #19 PROMOTE_CHECKLIST
