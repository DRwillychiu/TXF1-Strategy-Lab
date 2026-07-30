# HANDOFF — Colleague Live Strategies Analysis (2026-07-30)

## Status: Research DONE (4 docs), no code touched. Roadmap compliance blocker identified.

Machine handoff: laptop -> desktop. Pull before starting.

---

## 1. What Changed Today

Analyzed 9 TXF strategies from a colleague's production portfolio (plain-text logic
descriptions only, no source code, no performance data). Produced 4 research docs.
**Zero .pla files touched. Zero backtests run.**

### Documents created (all in `docs/research/`)

| File | Content |
|---|---|
| `colleague_live_strategies_reference_20260730.md` | Raw logic structured (9 strategies, EN/ZH name mapping) |
| `colleague_strategies_deep_analysis_20260730.md` | Alpha source / suitable regime / transferable items ranked S/A/B |
| `colleague_strategies_factor_decomposition_20260730.md` | ~45 factors classified P/V/M/S/T/E/R/X, cross-referenced to our 10 strategies |
| `colleague_strategies_default_params_and_roadmap_fit_20260730.md` | Default parameter table + **roadmap compliance mapping** |

### Portfolio inventory (subagent scan, evidence-based)

Full inventory of live (L1-L5) + live_simulation (S1/S3_RPS/S3_L/S3_S/S16_S) +
research (S17_S/S16_L/S16_S_10M) with timeframes, entry logic, exit matrices,
contract counts, all with `file:line` evidence. Embedded in the deep_analysis doc.

---

## 2. Current State

| Item | State |
|---|---|
| 4 research docs | Written, **this commit** |
| Any .pla change | **None** |
| Any backtest | **None** |
| Colleague performance data | **Does not exist** — 0 numbers provided (see §3 D1) |
| Roadmap status | Unchanged. S17_S still CURRENT. Nothing added, nothing jumped. |
| Version drift issue | **Found, not fixed** — task chip spawned (see §5) |
| Contract count contradiction | **Found, unresolved** — needs manual MC9/MC12 check (see §5) |

---

## 3. Key Findings

### D1. Performance data: completely absent

Zero numbers across all 9 strategies except one: Hurricane max 2 contracts.
No net profit, win rate, PF, MDD, trade count, sample period, slippage assumption.
**"Already deployed and profitable" is a verbal claim, not verified evidence.**
Parameter disclosure rate approx 1/45 approx 2%.

### D2. Three factor families we have ZERO coverage of

| Family | Colleague | Ours |
|---|---|---|
| **S** Statistical (regression, discriminant analysis) | 2/9 | **0/10** |
| **E** Event (extreme std-dev entry filter) | 1/9 | **0/10** |
| **R** Pyramiding | 1/9 | **0/10** |

### D3. Highest-value transferable item: 1+1 pyramiding

All our live strategies use flat 2 contracts. Changing to 1 initial + 1 confirmed
add-on = same max exposure, but only 1 contract stopped out on losers, full size on
winners. Directly serves the target profit profile (small win + big win + small loss).
**Pyramiding is entry-side**, so it does not touch the exit-side protection ground
that died 3 times.

### D4. ROADMAP COMPLIANCE BLOCKER (read this before doing anything)

Rule #14 forbids inventing strategy names, skipping numbers, parallel development.
Mapping the 9 colleague strategies onto the unstarted roadmap queue:

| Colleague strategy | Roadmap slot | Verdict |
|---|---|---|
| Aquila (60M channel + ATR) | **S10_L/S10_S AdaptiveBreakout** (30M) | STRONG match |
| Boya (90M Bollinger) | **S15_L/S15_S BBReversion** (60M) | MEDIUM — **directional thesis may be inverted**, see D5 |
| Neo Capricorn / Storm / Petis | S11 / S13 / S10 | WEAK |
| **Song Zhiwen (60M divergence)** | **S4 MACDDivergence — KILLED 2026-07-07** | **CONFLICT** |
| **Hurricane counter-trend leg** | Same killed family (D class) | **CONFLICT** |
| **Yang Jiong (discriminant analysis)** | **No slot exists** | **NONE** — roadmap has no statistical-classification family |
| Rime (multi-indicator) | No slot | NONE (also unreconstructible) |

**Consequence: cannot "build 9 new strategies."** Must be either mechanism injection
into existing strategies (Path A, fully legal) or reference designs for future
roadmap numbers (Path B, docs only).

### D5. Two items requiring verification against archive

1. **S15 BBReversion vs Boya**: S15 is named "Reversion" but Boya's logic is
   Bollinger **trend continuation** (crosses above midline + upper band positive
   slope). Rule #14 requires alignment with archive original description.
   **Must read** `strategies/research/archive/batch03_S11-S15/S15_BBReversion/`.
2. **S10 AdaptiveBreakout original spec**: confirm 30M vs Aquila's 60M, and whether
   "adaptive" means ATR-adaptive threshold.
   **Must read** `strategies/research/archive/batch02_S6-S10/S10_AdaptiveBreakout/`.

### D6. Divergence family conflict has a legal workaround

The 2026-07-07 S4 KILL ruling says "MACD concept unsuitable as standalone strategy,
**retained only as a judgment indicator**" (`OFFICIAL_ROADMAP.md:47`).
So divergence CAN be used as a regime gate / filter, just not as the primary entry
signal. This is exactly how Hurricane's with-trend leg uses it (dual-threshold on
divergence magnitude as a regime measurement). Directly applicable to the in-progress
`S3_S_regime_redesign_research_20260728.md`.

### D7. Trailing stop parameters must NOT be swept

The optimizer will always find in-sample-attractive trailing parameters — that is
precisely how S1 Trail_B (-385K), L5 SP five variants, and L5 Stage1_BE (-19K) were
produced. Parameter sweeping cannot distinguish "genuinely protects profit" from
"happens to fit the historical path". If a strategy needs trailing, use a fixed
conservative value and keep it out of the Phase 1 sweep list.

---

## 4. Decisions Made (by user)

1. Store colleague strategy logic as .md in the TXF research directory (2026-07-30)
2. Target directory confirmed: `docs/research/` inside TXF1-Strategy-Lab
3. All 9 strategies confirmed to be TXF (Taiwan index futures) strategies
4. **Ruling on parameters**: "參數因為那是對方的細節，我認為是可以透過預設參數然後我再去
   做參數範圍最佳化，去取得我自己希望的結果" — accepted as directionally correct;
   maps onto existing W0 pre-verify + Phase 1 plateau test. Three caveats recorded
   in the default_params doc §1 (calibration vs architecture vs missing-model
   parameters; 3/9 strategies fall into "missing model" and cannot use this route).

---

## 5. Open Items Found During Scan (not fixed)

### 5.1 Version drift — .pla ahead, docs behind

| Strategy | .pla | README | BOSS_VIEW |
|---|---|---|---|
| L1 | V3.1 | V2.6 | V2.7 |
| L3 | v15.0 | v13.4 | V14.1 |
| L4 | v14.6 | v14.6 | v14.2B |
| S16_S | v1.6.2 | v1.5 | v1.5 |
| S3_RPS | v2.0.6 | v2.0.4 | v2.0.4 |

Impact: cannot read current state from BOSS_VIEW/README when making optimization
decisions. Task chip spawned for this (separate session).

### 5.2 Contract count contradiction — NEEDS MANUAL CHECK

| Source | Says |
|---|---|
| `CLAUDE.md:10` (tech spec) | 1 contract |
| `CLAUDE.md:176` (Rule #12, added 2026-07-26) | 2 contracts on live |
| L1-L5 .pla source | all self-describe 2 contracts |
| `docs/methodology/position_sizing_and_capacity.md:16-20` (2026-06-07) | all 1 contract |
| **S16_S**: `.pla:11` | "trades 2 contracts" |
| **S16_S**: `S16_S_MACrossShort_DEPLOYMENT.md:192,37` | "fixed 1 contract" |

**This blocks the 1+1 pyramiding work (D3).** Only Willy can resolve it — requires
checking actual order size in MC9 / MC12.

### 5.3 Other

- No strategy implements a daily loss cap, though research docs exist
  (`L1_daily_loss_cap_design_20260722.md`)
- L5 `BL_BreakExit_Bot/Mid` (`L5_BreakoutLong.pla:707-708`) trigger conditions not
  traced; not mentioned in BOSS_VIEW exit rules table
- `strategies/batch01/` at top level appears to predate the 3-tier reorg, not
  recorded in CLAUDE.md directory structure

---

## 6. Next Session — Recommended Order

First 6 items require **no .pla changes**.

| # | Action | Blocked by |
|---|---|---|
| 1 | Ask colleague the 15 questions (deep_analysis §6 + factor_decomposition §7). Priority: Q10 — how does his divergence model differ from plain MACD divergence? This decides whether D4's CONFLICT needs an override | none |
| 2 | **Manually verify MC9/MC12 actual order size** (§5.2) | only Willy |
| 3 | Cross-strategy whipsaw audit — pull backtest logs, find days where a Long strategy stopped out and a Short strategy entered same day (or reverse), sum the P&L. Pure data analysis | none |
| 4 | Read archive originals for S10 and S15 (D5) to determine Path B viability | none |
| 5 | Write Hurricane dual-threshold + divergence-as-regime-gate into `S3_S_regime_redesign_research_20260728.md` candidate list (D6) | none |
| 6 | Extreme-sigma day P&L check — find days with single-bar range > N sigma, sum our 10 strategies' P&L on those days | none |
| 7 | L5 1+1 pyramiding A/B design | #2 and #1-Q5 |
| 8 | Three-layer stop institutionalization proposal (Hard + Vol + Pattern; 7/10 strategies lack the pattern layer) | §5.1 doc sync |
| 9 | Path B reference design docs for S10 / S15 | #4 |

---

## 7. Files

### Created this session
```
docs/research/colleague_live_strategies_reference_20260730.md
docs/research/colleague_strategies_deep_analysis_20260730.md
docs/research/colleague_strategies_factor_decomposition_20260730.md
docs/research/colleague_strategies_default_params_and_roadmap_fit_20260730.md
docs/handoffs/HANDOFF_COLLEAGUE_STRATEGIES_20260730.md   (this file)
```

### Read for evidence (not modified)
```
docs/policies/OFFICIAL_ROADMAP.md:40-114
CLAUDE.md  (Rules #12/#13/#14/#16/#18, Phase 1-4 workflow, quality gates)
docs/research/stop_loss_mechanisms_catalog_20260628.md
strategies/live/*/*.pla + *_BOSS_VIEW.md          (5 strategies)
strategies/live_simulation/*/*.pla + *_BOSS_VIEW.md  (5 strategies)
strategies/research/  (S17_S, S16_L, S16_S_10M)
docs/methodology/position_sizing_and_capacity.md
```

### Modified / deleted
**None.**

---

## 8. Git

- Branch: see commit
- This commit: 4 research docs + this handoff
- No .pla, no config, no policy file changed
- Nothing to roll back — additive only
