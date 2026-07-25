# Lesson L27 — Breakeven Mechanism Incompatible with Consolidation Strategies

**Codified**: 2026-07-25
**Origin**: L3 ConsolidationLong V15.0 breakeven mechanism research
**Lesson**: L27 (cumulative L1-L27; L1-L26 see prior docs)

---

## L27: Breakeven (BE) is structurally incompatible with consolidation strategies

**A breakeven mechanism that moves SL to entry price after N% unrealized profit
creates a re-entry whipsaw loop in consolidation strategies, destroying alpha.**

### Hypothesis (MFE analysis — theoretical)

MFE (Maximum Favorable Excursion) analysis of 376 V15.0 trades showed:

- 202 losing trades, of which 139 (69%) had unrealized profit before reversal
- At BE_Trigger = 0.15% of entry, estimated 103 losers saved (+4.86M)
  with only 7 winners at risk (-18K)
- Sweet spot appeared to be 0.10%–0.20%, predicting net +4.8M improvement
- Analysis converted from fixed-point (BE_Trigger_Pts) to percentage-based
  (BE_Trigger_Pct) for index-level adaptivity

### Reality (MC9 optimization — actual)

MC9 sweep of BE_Trigger_Pct 0.00–0.40 (step 0.01, 41 combinations):

| BE_Trigger_Pct | Net Profit | Trades | PF   | MDD        |
|:--------------:|:----------:|:------:|:----:|:----------:|
| 0.00 (off)     | +2,431,600 | 375    | 1.25 | -810,800   |
| 0.01           | -2,899,600 | 945    | 0.64 | -2,903,200 |
| 0.05           | -2,223,200 | 748    | 0.73 | -2,306,800 |
| 0.10           | -740,400   | 563    | 0.91 | -1,156,400 |
| 0.15           | +19,600    | 492    | 1.00 | -1,154,800 |
| 0.20           | +854,000   | 462    | 1.11 | -970,400   |
| 0.25           | +1,062,000 | 450    | 1.13 | -968,400   |
| 0.30           | +1,036,000 | 423    | 1.13 | -985,200   |
| 0.39           | +1,715,600 | 401    | 1.20 | -914,400   |
| 0.40           | +1,604,000 | 400    | 1.19 | -914,400   |

**No BE trigger value beats the baseline (0.00).** Every metric — net profit,
PF, MDD — is worse with any BE enabled.

### Root cause: Re-entry whipsaw loop

When BE triggers, the position exits at entry price (breakeven). But in a
consolidation box, the price is STILL in the support zone (bottom of box).
The entry conditions remain valid:

1. BE exit at entry price (in support zone)
2. Close < v_Support_Zone still true
3. Close > v_Box_Btm - v_ATR_Buffer still true
4. Strategy immediately re-enters
5. Price oscillates -> BE triggers again -> repeat

Each re-entry costs 1,000 NTD slippage (round-trip). At BE=0.01%:
- 945 trades vs 375 baseline = 570 extra trades
- 570 x 1,000 NTD = 570,000 NTD pure friction cost
- Plus lost profits from winners that got BE'd out before reaching TP

### Why MFE analysis failed to predict this

MFE analysis treats each trade as independent. It calculates "if we had exited
at breakeven, we save this loss." But it does NOT account for:

1. **Re-entry**: after BE exit, strategy enters again in the same bar/box
2. **Friction accumulation**: each re-entry has its own slippage cost
3. **Winner disruption**: winners that oscillate through entry price get
   stopped out and re-entered, fragmenting one profitable trade into
   multiple friction-heavy trades

### Why BE works for trend strategies but not consolidation

| Factor | Trend (L1/L5) | Consolidation (L3/L4) |
|--------|:------------:|:--------------------:|
| Price after BE trigger | Moves AWAY from entry | Oscillates AROUND entry |
| Re-entry after BE exit | Unlikely (price left zone) | Immediate (still in box) |
| Alpha source | Directional momentum | Support/resistance bounce |
| BE contradiction | None (protects momentum) | Contradicts support thesis |

In trend strategies, BE works because:
- Price breaks out -> moves away from entry -> no re-entry opportunity
- BE protects gains from mean-reversion after breakout

In consolidation strategies, BE fails because:
- Price oscillates within box -> frequently crosses entry price
- BE is equivalent to saying "I don't trust support" which contradicts
  the entry logic of "buy at support"

### Conclusion on all three exit mechanisms for L3

| Mechanism | Status | Rationale |
|-----------|:------:|-----------|
| Initial SL (SL_Pct) | LIVE | ATR + 0.55% dual-layer cap. Proven effective |
| Breakeven (BE) | REJECTED | Re-entry loop. Structurally incompatible |
| Profit pullback / trailing | NOT NEEDED | Fixed TP target (box top). Trailing contradicts fixed target |

L3's exit architecture is binary by design: **hit TP (box top) or hit SL
(box break).** Any intermediate exit mechanism creates friction without
improving outcomes. The box structure itself IS the risk framework.

### Rule

1. NEVER add breakeven mechanisms to consolidation/range strategies
2. Before implementing BE on any strategy, verify re-entry conditions
   are NOT met after BE exit — if entry conditions persist, BE creates loops
3. MFE analysis is necessary but NOT sufficient — always validate with
   actual MC9 optimization before drawing conclusions
4. BE is appropriate ONLY for directional strategies (trend, momentum,
   breakout) where price moves away from entry after trigger

### Applicability

- L3 ConsolidationLong: CONFIRMED INCOMPATIBLE (this research)
- L4 ConsolidationShort: APPLY by default (same box structure)
- L1 TrendLong: CANDIDATE for future BE research (directional strategy)
- L5 BreakoutLong: CANDIDATE for future BE research (directional strategy)
- S1 NightMomentum: CANDIDATE for future BE research (momentum strategy)

---

## Code disposition

BE_Trigger_Pct was implemented in commit `84bb796` and reverted in the
subsequent commit. The original `BE_Trigger_Pts(0)` code is preserved
in L3 V15.0 as disabled (default 0). No code was permanently added.

## Related lessons

- L25: Time filter cascade effect (opening block)
- L26: Consolidation strategy day-session opening avoidance
- L24: Risk overlay alpha preservation (SL cap design)
