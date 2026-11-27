# L1-L5 Structural Optimization — User Review + Deep Q&A

- **Date**: 2026-07-22
- **Context**: User review of 7/21 structural audit (15 consolidated problems)
- **Status**: Research phase — no .pla changes. User decisions annotated per strategy.
- **Prerequisite**: `docs/research/L1-L5_structural_audit_20260721.md`

---

## Cross-Strategy Decisions (User 7/22 Rulings)

| Decision | Scope | Detail |
|----------|-------|--------|
| Fixed lots / risk budget gate | ALL | Deferred to 2026/9/15. Current plan: 1 lot + 1x margin. Capital increase = proportional lot increase. Will schedule after strategy testing passes. |
| Daily loss cap | ALL | Confirmed: implement per-strategy daily loss cap. Calculation window: **previous day 15:00 → next day 13:45** (aligns with night session → day session full trading day). |
| Stop mechanism review | ALL | Every strategy's FULL stop architecture (initial stop + trailing stop + all exits) must be re-examined. Not just adding inner layers — comprehensive review. |
| Cooldown / consecutive loss breaker | L1/L3/L5 | Needs deep analysis of both sides before implementation. Not a rush item. |

---

## L1 TrendLong (45M, Long only, V2.7, MC9 live)

### Needs Optimization

| # | Issue | User Decision | Status |
|---|-------|--------------|--------|
| 1 | Fixed 1 lot, high-vol risk 25-38% of account | **Deferred to 9/15.** Current plan is 1 lot + 1x margin. Capital increase = proportional scaling. | DEFERRED |
| 2 | Weekly filter OR logic (Close > W20 OR W60), allows longs in early declines | **Needs deep backtest research.** User concern: if we wait for full trend confirmation, profit capture will be too low and opportunities missed. | RESEARCH |
| 3 | No daily loss cap | **Confirmed: add per-strategy daily loss cap.** Window: 15:00 → next day 13:45. | CONFIRMED |
| 4 | ATR x 1.5 produces 300-450 pt stops in high vol | **Strict optimization required.** Not just inner layers — full review of initial stop + trailing stop mechanisms. Also consider adding fixed % as an option. | CONFIRMED |
| 5 | No cooldown after stop-out | **Needs deep two-sided analysis.** Trade-off: cooldown protects against consecutive losses BUT may miss the next big winner right after a stop-out. | RESEARCH |
| 6 | No consecutive loss breaker (max 18 consecutive losses, -394,600) | **Needs deep analysis with realistic market scenarios.** Must consider what happens in various market conditions. | RESEARCH |

### How to Optimize

1. **Daily loss cap** — per-strategy cumulative P&L counter, reset at 15:00 each day, halt new entries when cap breached, resume next trading day
2. **Stop architecture full review** — re-examine initial stop (ATR x 1.5 formula), trailing stop behavior, and all exit mechanisms. Add fixed % as candidate inner layer alongside structure-based (swing low / previous day low)
3. **OR→AND filter research** — backtest both configurations, measure Top-10 retention and overall profitability impact. User explicitly wants to understand the cost of stricter filtering.
4. **Cooldown deep study** — analyze: (a) how many times did a winning trade immediately follow a stop-out? (b) what's the net expectation of cooldown vs no-cooldown? (c) is there a conditional cooldown that preserves winners?
5. **Consecutive loss breaker study** — model different thresholds (3/5/8 consecutive losses) across historical market regimes

### Priority: Daily loss cap → Stop architecture review → Filter research → Cooldown/breaker study

---

## L2 TrendShort (60M, Short only, V5.2, MC9 live)

### Needs Optimization

| # | Issue | User Decision | Status |
|---|-------|--------------|--------|
| 1 | Fixed 1 lot, high-vol risk 26-39% | **Deferred to 9/15** (same as L1). | DEFERRED |
| 2 | 13-week SMA filter → 2026 full year 0 trades | **Critical. Strategy is effectively dead.** User asks: why wasn't this discovered? | CRITICAL |
| 3 | No daily loss cap | **Confirmed** (same framework as L1). | CONFIRMED |
| 4 | No cooldown | Needs analysis. | RESEARCH |
| 5 | Trailing stop uses unfrozen ATR | **Full stop review needed.** User asks: what IS the initial stop? What happens during rapid bounces? | CONFIRMED |

### Deep Q&A

**Q: Is the 13-week SMA really only updating once? Why is this strategy dead?**

A: The filter updates **once per week**, on Friday at 15:00 (night session opening bar). The mechanism:

- L2 does NOT use MC's built-in weekly data. Instead, it manually simulates weekly closes on the 60M chart (lines 349-403).
- `IsNewWeek = True` only triggers when the previous bar satisfies BOTH `Time = 1245` AND `DayOfWeek = 5` (Friday's last day-session 60M bar).
- `FilterOK` is initialized to `False` (line 128) and can only change on that one Friday bar.
- In 2026's bull market, **every single Friday close has been above the 13-week SMA**, so `FilterOK` has never flipped to True.
- Entry condition (line 443) requires `FilterOK = True` → never passes → 0 trades all year.

**Q: So this is a dead strategy? How was this not noticed?**

A: Yes, L2 has been effectively paralyzed since at least 2026 Q1. It wasn't noticed because:
- A strategy that doesn't trade doesn't generate losses, doesn't trigger alerts, doesn't appear in trade logs
- The filter was designed to be conservative (only short in confirmed bearish weekly trend), which is the correct thesis
- But the implementation is too rigid: weekly-only update + bull market = permanent lockout
- This is a **silent failure mode** — the strategy appears to be "running" in MC9 but is actually doing nothing

**Q: What is L2's initial stop design? What happens during rapid bounces?**

A: Initial stop (frozen at entry, lines 459-464):
```
SL_Trig = DC_Lower + ATR(21) x 1.1
```
- DC_Lower = 30-period Donchian lower rail (Lowest Low of last 30 bars)
- Frozen: ATR and DC values locked at entry, never recalculated during the trade

Trailing stop (TSL, lines 509-544):
```
New_TSL = Lowest(Close[1], 9) + ATR(21) x 1.0    (recalculated every bar)
TSL_Line = MinList(TSL_Line, New_TSL)               (ratchet: only goes lower)
Active_TSL = TSL_Line + ATR(21) x 1.1              (live ATR — breathes with vol)
```

**During rapid bounces**: ATR rises → `Active_TSL = fixed_TSL_Line + rising_ATR * 1.1` → stop pushed HIGHER → more room → **slower exit**. The trailing stop "gives way" during volatility spikes, which means in a V-shaped bounce, L2 exits later than it would with frozen ATR, giving back more profit.

L2 has **12 exit labels across 7 priority levels** — the full exit chain needs comprehensive review.

### How to Optimize

1. **[MOST URGENT] Fix the filter** — options: (a) accelerate update frequency (daily instead of weekly), (b) use MC Data2 weekly data directly instead of manual simulation, (c) add a secondary faster filter that can override FilterOK in extreme bearish conditions
2. **Daily loss cap** — same framework as L1
3. **Full stop architecture review** — initial stop + trailing stop + all 12 exit mechanisms. Specifically: should Active_TSL use frozen or live ATR? A/B test needed.
4. **Trailing stop ATR freeze A/B** — compare production (live ATR) vs frozen ATR variant on historical data

### Priority: Fix filter (restore trading ability) → Full stop review → Daily loss cap → TSL ATR freeze test

---

## L3 ConsolidationLong (15M, Long only, v14.1, MC9 live)

### Needs Optimization

| # | Issue | User Decision | Status |
|---|-------|--------------|--------|
| 1 | v14.1 deployed without formal review | **User asks: WHY was this unreviewed?** | ANSWERED |
| 2 | Fixed 1 lot, high-vol 25-38% | **Deferred to 9/15** (same as L1). | DEFERRED |
| 3 | Daily filter OR logic (Close > MA20 OR MA60) | **Needs deep backtest.** | RESEARCH |
| 4 | No daily loss cap | **Confirmed.** | CONFIRMED |
| 5 | ATR(9) only 2.25hr memory, short-term spikes freeze oversized stops | **Full stop review needed** — initial stop, trailing, everything. | CONFIRMED |
| 6 | No cooldown | Needs analysis. | RESEARCH |

### Deep Q&A

**Q: Why was v14.1 deployed without review?**

A: It was NOT completely unreviewed — but it went through a **different, lighter review path** than v13.2B. The full story:

- v13.2B had a comprehensive review: 431-trade per-trade analysis, 4 acceptance gates, variant D rejection, variant B approval. This review lives in `L3_ConsolidationLong_review.md`.
- v14.1 was developed 7/2-7/4 as part of a "live optimization" sprint covering all 5 strategies. It went through its OWN workflow:
  - Dedicated folder: `docs/live_optimization/L3_v14.1_matrix_range_capture/`
  - 147-line summary.md with problem statement, matrix design, 2 optimization rounds, MC9 backtest comparison, 11-item deployment checklist (all checked)
  - Python pre-verify script (536 lines, 28-year TWII daily direction confirmation)
  - Detailed commit messages with design rationale

**The gap is NOT "no review"** — it's:
1. `_review.md` was never updated to reference v14.1 → anyone reading only `_review.md` thinks v13.2B is production
2. v14.1's review was "performance verification" (MC9 backtest numbers look good), not "risk and structure full review" (per-trade analysis, edge case examination, exit mechanism stress test)
3. Two documentation tracks that don't know about each other

**v14.1 changes vs v13.2B:**
- Removed dual-leg entry (CL_Entry_Bot + CL_Entry_Mid → unified CL_Entry support zone)
- Changed targets from fixed box levels to dynamic swing high
- Added 3 new matrix inputs: Entry_Zone_Pct=0.50, Min_Box_ATR=8.5, Swing_Lookback=80
- Trades: 431 → 332, PF: 1.187 → 1.470, Net/MDD ratio: 1.89 → 5.41
- Safety modules (Holiday, Settlement, FrozenSL, ImmediateStop) all preserved

**Q: Is "safest to add inner stops" the same as "parameter settings are wrong"?**

A: Not exactly a parameter problem — it's a **thesis-stop mismatch**. ATR(9) x 3.0 was designed as a "maximum noise filter" (last line of defense per Rule 17), which is correct architecture. But for a consolidation strategy, this means the stop is 3x the 15M noise level below the box bottom. A consolidation trade that breaks box bottom by 3x ATR is not just "noisy" — it's a failed trade that should have been exited much earlier. The inner layers (box bottom + small buffer, time stop) provide that earlier exit. The parameter 3.0 itself isn't "wrong" — it's the ATR layer doing its job as the outermost defense. What's missing is the inner layers that should catch failures before they reach that outer wall.

### How to Optimize

1. **v14.1 status resolution** — decide: keep v14.1 with a proper full review, or rollback to v13.2B. User needs to confirm which version is currently running in MC9.
2. **Daily loss cap** — same framework
3. **Full stop architecture review** — initial stop (ATR(9) x 3.0 formula), all exits, add Box bottom + small buffer (inner layer) + time stop (consolidation should resolve quickly)
4. **OR→AND filter research** — same approach as L1
5. **Cross-reference documentation** — update `_review.md` to point to v14.1 materials regardless of decision

### Priority: v14.1 status resolution → Full stop review → Daily loss cap → Filter research

---

## L4 ConsolidationShort (15M, Short only, v14.4, MC9 live)

### Needs Optimization

| # | Issue | User Decision | Status |
|---|-------|--------------|--------|
| 1 | Fixed 1 lot, high-vol 12-17% (mildest of 5) | **Deferred to 9/15.** | DEFERRED |
| 2 | Macro Block golden cross residual locks shorts for weeks | **User asks: why wasn't this caught before?** | ANSWERED |
| 3 | No daily loss cap | **Confirmed.** | CONFIRMED |
| 4 | CS_BreakExit: 20 trades, 0% WR, -377,800 = 158% of net profit | **User asks: is this supposed to be breakeven but acts like full stop?** | ANSWERED |
| 5 | Trailing stop uses unfrozen ATR | **Full stop review needed.** | CONFIRMED |

### Deep Q&A

**Q: Why wasn't the Macro Block golden cross residual caught before deployment?**

A: The Macro Block code (lines 425-431):
```
if ((Close of Data3 > v_Daily_SlowMA) and (v_Daily_SlowMA >= v_Daily_SlowMA[1]))
   or (v_Daily_FastMA > v_Daily_SlowMA) then
    v_Macro_Block = true;
```

Two conditions connected by OR:
- Condition A: Close > MA60 AND MA60 rising (strong bull)
- Condition B: MA20 > MA60 (golden cross)

**Why the "residual" persists**: When price starts falling, Condition A can flip to false within 1-2 days (price drops below MA60 or MA60 stops rising). But Condition B (MA20 > MA60) needs **2-4 weeks of continuous decline** before the death cross occurs (MA20 crosses below MA60). During that gap: Condition A = false, Condition B = true → OR = true → v_Macro_Block = true → shorts blocked.

**Why not caught**: The Macro Block was designed in v14.0 as a "conservative macro defense" and brought directly into production. Subsequent versions (v14.1-v14.4) focused entirely on exit mechanisms and never re-examined the entry filter. The overlap issue was only accidentally discovered in v14.5, when an attempt to add a "Strong Long Block" filter turned out to be 100% redundant with the existing Macro Block condition.

**Q: Is CS_BreakExit supposed to be breakeven but actually acts like a full stop loss?**

A: **No, CS_BreakExit is NOT a breakeven exit.** It's a dedicated "thesis failure admission" exit. The code (lines 631-637):
```
if (ExitFired = 0) and (v_is_in_consolidation = false) and
   (Close of Data2 > v_Locked_Top) then
    BuyToCover ("CS_BreakExit") next bar at Market;
```

Trigger: consolidation broken + 60M close above locked box top → "the fake breakout turned into a REAL breakout, our short thesis is dead."

**0% win rate is logically inevitable**: the trigger condition itself means "price is above our short entry" — a short position cannot be profitable when price is above entry. This is a stop-loss mechanism wearing a "BreakExit" label.

The -377,800 is the structural cost of L4's thesis: "short fake breakouts above box top." When the fake breakout turns real, the trade is a full loss. v14.5 tried to fix this with a Fast BreakExit (15M level early exit) but it caused 27 false triggers vs 5 real ones, worsening total loss from -378K to -535K.

**Review file classifies this as "unpatchable thesis cost"** (review line 152).

**Q: What is L4's initial stop design? What happens during rapid bounces?**

A: Initial stop (frozen, lines 565-567):
```
v_Stop_Level = v_Frozen_LockedTop + ATR(60) x 2.0
```
Frozen at entry: both LockedTop and ATR(60) locked at entry bar, never recalculated.

For rapid bounces: the initial stop doesn't move (frozen), so it provides consistent protection. But the trailing stop uses live ATR — same issue as L2.

**Q: Has the time stop 60→40 change been backtested?**

A: **No.** Currently only 4 trades have hit CS_TimeExit (-22,400 total), sample too small to assess. The audit's suggestion was directional, not validated. Key risk: CS_SL (the main stop) has 65% win rate because many of those are actually "trail locked profit" exits. Shortening time stop from 60 to 40 bars could convert some CS_SL winners (trades that activate trail between bar 40-60) into CS_TimeExit losers. **Must backtest in MC12 before implementing.**

### How to Optimize

1. **Daily loss cap** — same framework
2. **Full stop architecture review** — initial stop (ATR(60) x 2.0), trailing stop (unfrozen ATR), all 8 exit mechanisms (6 active, 2 OFF). Every mechanism scrutinized.
3. **P10 (CS_BreakExit) evaluation** — this is a strategy viability question: if structural cost exceeds net profit, is L4 worth keeping? Need long-term data analysis.
4. **Macro Block filter redesign** — options: (a) remove Condition B entirely, (b) add decay timer to golden cross memory, (c) use faster MA pair, (d) change OR to AND
5. **Time stop change** — requires MC12 backtest first, NOT blind implementation

### Priority: Full stop review → Daily loss cap → Macro Block redesign → P10 viability assessment → Time stop backtest

---

## L5 BreakoutLong (15M, Long only, v19.8, MC9 live)

### Needs Optimization

| # | Issue | User Decision | Status |
|---|-------|--------------|--------|
| 1 | Trail system dead at 1 contract | **Critical. Trail rewrite needed.** User notes: position sizing approach same as L1 (deferred to 9/15). | CONFIRMED |
| 2 | Fixed 1 lot, high-vol 30-38% | **Deferred to 9/15** (same as L1). | DEFERRED |
| 3 | ATR x 4.5 high-vol stops 360-450 pts | **Reference L1 stop approach.** Full review needed. | CONFIRMED |
| 4 | No daily loss cap | **Confirmed.** | CONFIRMED |
| 5 | Re-entry clusters: 39 clusters, 102/182 trades, -719,400 | **User asks: what does this mean?** | ANSWERED |
| 6 | No consecutive loss breaker | Needs analysis. | RESEARCH |
| 7 | Stage 1 zero profit protection (58 trades, 1,826,000 wasted) | **Blocked — 3 independent attempts failed, direction permanently closed.** | BLOCKED |

### Deep Q&A

**Q: What are "re-entry clusters"? (plain language)**

A: L5 enters long at box bottom/midline. When stopped out, if the **box is still valid** (hasn't been broken), the entry conditions immediately re-qualify on the next bar. The strategy then enters again at the same price, gets stopped out again, enters again... like a shredder eating money.

**Worst case**: 2024-03-27 to 03-28, the strategy entered **6 times at the exact same price @20249**, got stopped out 5 times, net loss -44,000 NTD. The box didn't change during those 2 days, so entry conditions kept re-triggering.

**Scale**: 39 such clusters exist across 182 total trades, containing 102 trades (56% of all trades). 27 of these clusters are losing clusters totaling **-719,400 NTD** (38% of gross losses).

This is why cooldown + "same-box ban" is important for L5 specifically. The v19.9 Cooldown-D design addressed this but was rejected along with the rest of v19.9 — the cooldown component could potentially be extracted independently.

**Q: You say fixed % is ineffective for this breakout strategy. What's the data?**

A: Hard data from v19.8 SP module A/B testing (`L5_v19.8_variant_results.md`):

The 3 largest winning trades across all 5 SP variants were ALL truncated:
- 2026-04-07: baseline +376,400 → best SP variant only +15,800 (-96% truncated)
- 2026-03-31: baseline +177,600 → best variant +38,000 (-79%)
- 2026-03-12: baseline +131,000 → best variant +13,800 (-89%)

**Just these 3 trades lost -680,400 to SP truncation.** SP trigger thresholds are 60-100 points. Fixed % at 0.3% (about 138 points) is a tighter restriction than SP, meaning **fixed % would truncate even earlier in the trade lifecycle**.

L5's typical price path is "breakout → pullback → real breakout → extension." The pullback phase routinely exceeds 0.3-0.5% from entry. Fixed % would kill the trade during the pullback, before the real move begins.

**L5's net profit concentration**: 88% in Top-10 trades (v19.8, 164 trades). Updated to **92.6%** after Cooldown-D filtering (93 trades). Any mechanism that truncates these mega-winners destroys the strategy's entire edge.

For comparison: L3/L4 (consolidation strategies) have much lower Top-10 concentration and no fat-tail dependency → fixed % is safe for them. L5's extreme concentration makes fixed % almost certainly lethal.

### How to Optimize

1. **Trail rewrite for 1-contract operation** (Package B) — most critical single fix. Must find a way to activate Stage 2/3 trail without depending on TP partial exit. Preserving Top-10 mega-winners is the #1 constraint.
2. **Daily loss cap** — same framework
3. **Full stop architecture review** — initial stop (ATR x 4.5 formula) + stage-based approach (Stage 1: box bottom + buffer, Stage 2: trail from rewrite)
4. **Cooldown + same-box ban** — extract from v19.9 Cooldown-D design. Deep analysis of trade-off needed.
5. **Volume decay detection** — fake breakout filter (post-entry volume < 50% of entry bar → likely fake)
6. **DO NOT use fixed %** — evidence from SP A/B testing shows truncation of Top-10 mega-winners

### Priority: Trail rewrite → Full stop review → Daily loss cap → Cooldown study → Volume decay filter

---

## Summary: Optimization Priority by Urgency

| Rank | Action | Strategies | Type | Status |
|------|--------|------------|------|--------|
| 1 | L3 v14.1 status resolution | L3 | Operational | **Pending user MC9 confirmation** |
| 2 | L2 filter fix (restore trading) | L2 | Code change | **Needs design spec** |
| 3 | Daily loss cap design | ALL 5 | Code change | **User confirmed, needs spec** |
| 4 | Full stop architecture review | ALL 5 | Research | **User confirmed, needs per-strategy deep dive** |
| 5 | L5 trail rewrite for 1 contract | L5 | Code change | **Needs design spec** |
| 6 | Macro Block filter redesign | L4 | Research + code | **Needs design spec** |
| 7 | OR→AND filter research | L1/L3 | Research | **Needs backtest** |
| 8 | Cooldown + breaker deep study | L1/L3/L5 | Research | **Two-sided analysis needed** |
| 9 | P10 CS_BreakExit viability | L4 | Research | **Strategy-level question** |
| 10 | Risk budget gate | ALL 5 | Code change | **DEFERRED to 9/15** |

---

## Pending Confirmations (from 7/17, still unverified)

- [ ] L3: which version is currently running in MC9? (v14.1 or v13.2B?)
- [ ] 20% circuit breaker: has lot count been reduced?
- [ ] MC9 July trade detail export (exit label attribution)
- [ ] Contract type: micro x2 or mini x2?
- [ ] MC9 running code = git HEAD?
- [ ] Current account balance (236K was 7/17 figure)

---

## Document Purpose

This document serves as:
1. **User-reviewed optimization checklist** — every item has user's explicit decision
2. **Deep Q&A archive** — technical questions answered with code-level evidence
3. **Future audit reference** — template for pre/post-deployment review of any strategy
4. **Decision log** — what was confirmed, deferred, or needs research, with rationale
