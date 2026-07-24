# L1 Layer 1b — KILL Summary (2026-07-24)

**Status**: KILLED
**Killed by**: User ruling on 2026-07-24 after adversarial engineering SOP GATE 1 + GATE 2 (Fire-Quality Proxy) + framework constraint check.
**Origin**: Proposed in `docs/research/L1_P3_initial_SL_architecture_20260723.md` (lines 101-117) as a behavioral tightening sub-layer.
**Analysis basis**: `docs/research/L1_P3_python_analysis_20260724.md`.
**Related sealed lineage**: 停損收緊 34 variants (Family A-E) documented in `docs/research/L1_stop_mechanism_deep_research_20260722.md`.

---

## 1. Original Design (rejected)

Layer 1b was proposed as a behavioral trigger that, once fired during a hold, halves the Primary SL distance (execute-once, boolean lock).

| Element | Original Spec |
|---------|---------------|
| Trigger A | 3 consecutive Close < Open on 45M bars, total decline > Primary SL × 20% |
| Trigger B | Close < prev Open AND body > recent avg body × 2 (engulfing) |
| Fire logic | A OR B |
| Action | Primary SL distance HALVED (e.g., -300 → -150) |
| Execution | ONE TIME ONLY, boolean flag lock |
| Direction | Only tighten, never loosen |
| Timing | BarStatus(1)=2 (bar close confirmation) |

---

## 2. Four Independent Kill Reasons

Any single reason below is sufficient for kill. Four independent reasons make the kill decision definitive.

### 2.1 GATE 1 — Trigger Detection Duplicates Sealed Variants

Source: `docs/research/L1_stop_mechanism_deep_research_20260722.md` §2.5

- **Trigger A (連三黑) ↔ Family E**: `連續收低 k=3/4/5` were tested and rejected. k=5 result: -1,726 pts net over 999 winners killed / 31 losers saved.
- **Trigger B (engulfing) ↔ Family C**: 大陰吞噬 2 variants tested; ungated variant killed 127 winners for -5,370 pts net (worst-performing family in the study).

The trigger detection Layer 1b relies on is not novel. It is a re-run of two of the 34 sealed variants under a slightly different action (halve instead of exit).

### 2.2 L33 Systemic Principle — 45M K-bar Signals Cannot Distinguish Winner/Loser

Source: same file line 158, 253 (Lesson L33).

> L1 is a 31% win rate trend system: 144 winners carry the entire net profit. In the 0-500 pts region, the path of a winner (pullback, break of swing low, print of large bearish bar, sideways chop) is **statistically indistinguishable** from a loser's path. Distinction only happens at outcome.

> "Adding a smarter inner stop layer" is a systemic illusion for this architecture.

This principle applies to any 45M behavioral signal regardless of consequence (exit vs tighten). The halved-SL action softens the penalty per fire but does not solve the underlying signal-quality problem.

Complementary evidence from `docs/research/L1-L5_stop_methods_analysis_20260721.md` line 127:
> Candlestick patterns fit 15M strategies (L3/L4/L5), not 45M/60M (L1/L2) — 45M/60M bars are too few and too large for reliable pattern detection.

### 2.3 GATE 2 — Fire-Quality Proxy Rejects on Merits

Source: `docs/research/L1_P3_python_analysis_20260724.md` §Task 3.

Daily-bar proxy study, 2020-2026, 81 detected fires across 33 synthetic holds:

| Fire outcome (next 5 bars) | Hold was WINNER | Hold was LOSER | Row Total |
|----------------------------|-----------------|----------------|-----------|
| Saved (rebound > entry) | 36 | 5 | **41 (50.6%)** |
| Killed (dropped > 100 pts) | 2 | 31 | 33 (40.7%) |
| Neutral | 0 | 7 | 7 (8.6%) |
| Column total | 38 (46.9%) | 43 (53.1%) | 81 |

Architecture spec V1b.5-6 rejection thresholds:
- Fire → halved-SL-trigger rate < 40% → REJECT
- Fire → immediate-rebound rate > 40% → REJECT

Result:
- Killed rate 40.7% — barely clears the ≥ 40% floor (+0.7 pp margin)
- Saved rate 50.6% — **CLEARLY EXCEEDS the ≤ 40% ceiling by 10.6 pp**
- False-halving rate 46.9% — nearly 1:1 with true-halving; Layer 1b does not distinguish winners from losers with acceptable precision on daily data

The saved rate margin (10.6 pp over threshold) is large enough that even accounting for Daily-to-45M proxy uncertainty, the reject direction is high-confidence.

### 2.4 Framework Constraint — 減碼 Forbidden Until 2026-09-15

User ruling on 2026-07-24: "今天不會做任何減碼。出場就是直接出場。減碼是後續這些上架策略通過 2026/9/15 的檢驗，能夠賺錢後，才會開始規畫的事情。"

Layer 1b's "halve SL distance" is functionally a partial position management maneuver from the trader's perspective — even though the trade remains at 1 contract, the action moves the SL closer to reduce forward exposure while retaining upside. In the current framework of "exit = exit, no scaling", partial risk-reduction mechanisms are not permitted.

This constraint alone would suffice to kill Layer 1b under the current framework, independent of the other three reasons.

---

## 3. What Is NOT Sealed by This Decision

Explicit scope so future proposals are not incorrectly blocked:

| NOT sealed | Rationale |
|------------|-----------|
| Layer 1 (recent-N-day pullback × ratio) | Layer 1 is a static SL replacement, not a dynamic modification. Independently validated (L1_c decoupled from ATR, r=0.542). Proceeding to V3.1. |
| Layer 0 (ATR wall) | Unchanged. Continues as black-swan defense. |
| Layer 2 (P7 profit protection, T200) | Unchanged. User ruled T200 on 2026-07-23. |
| Layer 3 (P4 MA55 trail) | Unchanged. Independent P3 optimization pending. |
| ATR-based emergency mechanisms | Layer 0 is the ATR-based emergency; this is retained. |

The "no dynamic SL modification post-entry" implication is narrower than it may appear: Layer 3 (P4 trail) legitimately updates the trailing floor on every tick as a **ratchet-up-only** mechanism. Ratchet-up (never regressing) is fundamentally different from Layer 1b's proposed conditional-tighten action. Ratchet-up remains permitted.

---

## 4. Resurrection Conditions (if Layer 1b Is Ever Reproposed)

To reopen this decision, ALL of the following must be satisfied. Any missing condition = auto-block.

| # | Condition | Rationale |
|---|-----------|-----------|
| R1 | 減碼 explicitly permitted by user after 2026-09-15 gate | Framework constraint (Reason 2.4) |
| R2 | Trigger detection is genuinely novel (not in the 34 sealed variants) | Reason 2.1 — MA-break, Volume-weighted confluence, Regime-classifier are the known novel routes |
| R3 | 45M-native fire-quality study (not Daily proxy) shows: fire→halved-SL-trigger > 50% AND fire→immediate-rebound < 30% | Comfortable margin over the barely-passing 40% floor |
| R4 | Study demonstrates statistical significance: ≥ 30 fires per year in ≥ 3 out of last 5 years | Current study had only 2021 exceeding 20/year |
| R5 | Prior belief that L33 principle can be overcome — explicit argument for why THIS proposal escapes the "smarter inner stop = systemic illusion" verdict | Reason 2.2 — needs to be addressed head-on, not sidestepped |
| R6 | Full Rule #17 multi-layer SL SOP compliance if trigger is behavioral | Existing regulation |
| R7 | Passes Rule #18 5-piece validation before any promote | Existing regulation |

**Anti-pattern warnings** (things that should NOT be sufficient to reopen):
- "New trigger threshold" (SL × 30% instead of 20%) — same detection family, will produce similar false-halving pattern
- "Different halving ratio" (1/3 instead of 1/2) — action-side tweak that does not address signal quality
- "Combined with time filter" (only fire after N bars into hold) — adds conditional gate but core signal-indistinguishability remains
- "Different bar timeframe" (60M or 30M instead of 45M) — L33 applies to slow trend systems, not just to 45M specifically

---

## 5. Reference Documentation Trail

| Document | Role |
|----------|------|
| `docs/research/L1_P3_initial_SL_architecture_20260723.md` | Original 4-layer + 1b design (2026-07-23) |
| `docs/research/L1_P3_execution_plan_20260724.md` | SOP-driven execution plan flagging Layer 1b as variant #35 risk (2026-07-24 morning) |
| `docs/research/L1_stop_mechanism_deep_research_20260722.md` | 34 sealed variants enumeration and L33 principle |
| `docs/research/L1_stop_forensics_20260722.md` | 456-trade forensic reconstruction that anchored the "loss context, not stop width" verdict |
| `docs/research/L1-L5_stop_methods_analysis_20260721.md` | Cross-strategy stop methods analysis (candlestick patterns not for 45M/60M) |
| `docs/research/L1_P3_python_analysis_20260724.md` | GATE 2 Fire-Quality Proxy study (this kill's data source) |
| `docs/handoffs/HANDOFF_L1_STOP_CAMPAIGN_20260722_EOD.md` | End-of-day handoff sealing the 34 variants |

---

## 6. Signatures

Kill authority: User ruling on 2026-07-24 after review of GATE 1 (Sealed-list novelty check) + GATE 2 (Fire-Quality Proxy) + Framework constraint (減碼 forbidden until 2026-09-15).

Adversarial engineering SOP compliance:
- Step 0 self-verification questions answered in execution plan
- GATE 1 executed by Explore subagent (10 files audited, 34 variants enumerated)
- GATE 2 executed by general-purpose subagent (Python analysis, 3 tasks, 17KB report)
- Kill decision derived from evidence, not from directive

Next action on the L1 P3 track: V3.1 spec authoring for Layer 1 (L1_c formula) with three-layer architecture (Layer 0 + Layer 1 + Layer 2 + Layer 3). Layer 1b slot in the original design is now retired.
