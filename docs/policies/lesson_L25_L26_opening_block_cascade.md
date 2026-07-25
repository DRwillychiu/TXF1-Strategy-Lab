# Lesson L25 & L26 — Opening Block Cascade & Consolidation Opening Avoidance

**Codified**: 2026-07-25
**Origin**: L3 ConsolidationLong V15.0 opening volatility filter research
**Lessons**: L25-L26 (cumulative L1-L26; L1-L24 see prior docs)

---

## L25: Time Filter Cascade Effect

**When implementing a time-based entry block, the FIRST bar after the block
window becomes a new toxic slot due to cascade.**

### Evidence

L3 V15 first pass: `Open_Block_End=930` (block 08:45-09:30)
- Eliminated 48 toxic opening entries (PF 0.73, WR 29%, Net -452K)
- But 19 NEW entries appeared at 09:45 (WR 10.5%, Net -604K)
- Cascade mechanism: strategy is flat during blocked window, first available
  signal at Time=930 fires, fill at 09:45 inherits the same opening toxicity

Second pass: `Open_Block_End=945` (block 08:45-09:45)
- Eliminated cascade at 09:45
- 10:xx entries (cascade target): 22T, WR 41%, Net +134K — PROFITABLE
- Cascade stopped: 10:00 is the first time slot where institutional opening
  pressure has dissipated

### Rule

1. Always test time filters in TWO iterations minimum
2. After implementing a block, check the FIRST bar after the window
3. Extend until the cascade target slot is demonstrably profitable
4. Expect trade count to decrease less than the blocked count
   (new replacement entries appear from flat-during-block)

---

## L26: Consolidation Strategy Day-Session Opening Avoidance

**Consolidation (box/range) strategies must avoid day-session opening.
The strategy's support/resistance logic is structurally invalid during
institutional open.**

### Why

TXF1 consolidation strategies rely on box bottom as support. During day-session
opening (08:45-09:45):

1. Institutional market-on-open orders test box boundaries with volume
   the 15M box detection cannot distinguish from genuine breaks
2. TXF1 is a "leader" during day session — institutions probe/hunt box bottoms
   rather than following international cues
3. Gap-open from overnight moves can trigger entries that immediately reverse
4. Engine stops (same-bar entry-exit) concentrate in this window: 6/9 pre-filter

During night session, TXF1 is a "follower" — it tracks international markets.
Box bottoms represent genuine support because the market respects them while
following offshore cues. This is why night PF (1.32) >> day PF (1.03).

### Data (V15.0 w/ OB945)

| Period | Trades | WR | PF | Net |
|--------|-------:|---:|---:|----:|
| Day 08:45-13:45 | 58 | 41.4% | 1.03 | +62,800 |
| Night 15:00-05:00 | 318 | 47.2% | 1.32 | +2,383,200 |

### Applicability

- L3 ConsolidationLong: CONFIRMED (Open_Block_End=945)
- Any future consolidation/range strategy on TXF1: APPLY by default
- Trend-following strategies (L1, L5): likely NOT needed (different alpha source)
- Short-side consolidation: evaluate separately (different institutional dynamics)

---

## Remaining Consolidation Strategy Structural Issues

Documented here for future reference, NOT yet actioned:

### 1. Whipsaw / Multi-Loss Days (MDD Driver)
- 16 days with 2+ losses, 22 excess trades, -1.4M excess loss
- Max consecutive losses: 13 trades
- Potential fix: daily max-1 loss limit (discussed but not implemented)
- Risk: max-1 limit could miss recovery entries on reversal days

### 2. Day Session Alpha Deficit
- Day PF 1.03 is barely breakeven even after opening block
- 13:00 hour: 12T WR 33.3% Net -360K (day-session close institutional pressure)
- Question: is day session worth trading at all?

### 3. Level-Scaling Risk
- SL_Pct=0.55% is level-adaptive in percentage but NTD impact scales:
  index 20,000 -> 22K/contract loss, index 25,000 -> 27.5K/contract
- Recent losses (2026) are 3-4x larger in NTD than 2020 losses
- Not a bug, but MDD grows with index level even if strategy edge is stable

### 4. Regime Dependence (Unfixable)
- 2024 PF 0.76 (worst year) — strong trending market
- Consolidation strategies inherently underperform in trending regimes
- This is a design tradeoff, NOT an optimization target
- Portfolio-level solution: pair with trend strategies (L1, L5)
