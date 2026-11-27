# S17_S Stage-1 Laptop Handoff — 2026-07-21

**From**: Laptop session (parameter audit + deep Q&A)
**To**: Desktop session (continue Stage-1 deep discussion)
**Status**: Stage-1 Topic 1 consensus confirmed + 9-point Q&A completed

---

## Part A: S16_S v1.4 Parameter Audit (pre-requisite work)

### Finding: Code is consistent, documentation has stale numbers

**Code vs Code**: research .pla and live_simulation .pla — ALL 31 input parameter values IDENTICAL.
Only structural diff: `Debug_On` exists only in research (by design, G1 diagnostic).

**Documentation internal inconsistency (STRATEGY_TEXT_20260718.md)**:
Parts 1-2 tables updated to 718 baseline. Parts 3, 5, 7 narrative sections carry stale numbers:

| Metric | Parts 1-2 (correct 718) | Parts 3/5/7 (stale) | Stale source |
|--------|------------------------|---------------------|--------------|
| TimeStop trades | 23 | 21 | v1.3 |
| TimeStop total profit | +2,187,600 | +1,986,200 | v1.3 |
| TimeStop avg profit | +95,113 | +94,581 | v1.3 |
| Win Rate | 27.10% | 22.73% | v1.0 |
| Reward:Risk | 5.14 | 5.68 | v1.0 |
| QuickStop trades | 76 | 75 | v1.3 |
| QuickStop percentage | 71% | 68% | v1.3 |

**OPEN_ISSUES_20260713.md**: Sections B1 and E carry v1.0 data (20 TimeStop / RR 6.44).

**Both .pla files**: Stale comment on MaxHoldingBars claiming "31 trades / avg +72K" — no matching version. Cosmetic only.

**Action required**: Fix stale numbers in STRATEGY_TEXT Parts 3/5/7 and OPEN_ISSUES B1/E. NOT blocking S17_S work.

---

## Part B: S16_S vs S17_S Structural Comparison (11 dimensions)

### Alpha Structure

| Dimension | S16_S | S17_S |
|-----------|-------|-------|
| Alpha source | First-bar explosive momentum (minute-level burst) | Post-bounce-failure continuation decline (day-level) |
| Entry philosophy | Predict the START of a decline | Confirm CONTINUATION of a decline |
| Analysis family | G (pure math momentum cross) | B+C (K-bar pattern + statistical filter) |
| What it earns | "The money from the violent first bar" | "The staircase money after the bounce fails" |

### Time Structure

| Dimension | S16_S | S17_S |
|-----------|-------|-------|
| Operating timeframe | 5M only (no Data2) | 60M (Data1) + Daily (Data2) |
| Holding period | Minutes to hours (MaxHold 24x5M = 2hr) | Days (swing) |
| Trade frequency | 19/yr (v1.4 baseline) | TBD, est. 12-18/yr |
| MC12 workspace | Data1: TXF1 5min only | Data1: TXF1 60min + Data2: TXF1 Daily |

### Risk Structure

| Dimension | S16_S | S17_S |
|-----------|-------|-------|
| Stop loss | Mature: QuickStop + ML + BE + ATR x4 | TBD: needs independent design |
| MDD | -228K (-18.31%) | TBD |
| Overnight risk | Low (short holding, rarely overnight) | User ruling: NOT a problem (2026-07-21) |

### Market Condition Suitability

| Condition | S16_S | S17_S |
|-----------|-------|-------|
| Flash crash | CORE — designed for this | Partial — can relay after S16_S |
| Slow decline | WEAK — 2022 only 3 trades (slope too flat) | CORE — designed for this |
| Bull pullback 5-8% | Catches explosion segment only | Daily filter confirms, captures continuation |
| Strong bull | Few entries, controlled loss | RISK: V-reversal (fake bounce failure = real bottom) |

### Portfolio Complementarity

- S16_S catches the START of declines (minutes)
- S17_S catches the CONTINUATION after bounces fail (days)
- Same decline, different segments — relay relationship but independently operated
- Correlation target: monthly P&L < 0.5 (locked constraint)

---

## Part C: 9-Point Q&A Summary (User Rulings + Clarifications)

### Q1: What does S17_S earn? (CLARIFIED)

**Previous (too narrow)**: "MA alignment transition from bullish to tangled/bearish"
**Corrected**: S17_S earns "post-bounce-failure continuation decline profit."

Not limited to bull-to-bear transitions. Works in:
- Established downtrends (Nth bounce failure)
- Post-rally exhaustion
- Any environment where daily filter confirms downtrend

Core alpha = "statistically, ~70% of bounces in a downtrend are traps."

### Q2: Entry design principle (CONFIRMED)

**Principle**: Operating timeframe determines strategy condition form.
- 5M: noisy, patterns unreliable -> pure math indicators (S16_S ZLEMA)
- 60M: 1 bar = 1 hour of institutional battle -> K-bar patterns meaningful (S17_S)
- Same-family + different timeframe = duplicate bet (S16_S 10M proof: correlation 0.89)

Three directions evaluated:
- A. Direct ZLEMA port to 60M -> REJECTED (correlation 0.89 proven)
- B. ZLEMA as filter + different trigger -> viable, essentially B+C variant
- C. Pure B+C (daily stat filter + 60M K-bar) -> ADOPTED

### Q3: Discovery and problem-solving approach (USER INTENT)

Goal: discover problems, solve them, clearly understand what you're doing and earning.
Not abstract concept exploration — practical clarity.

### Q4: Analysis family classification (STATUS)

Family classification was introduced ad-hoc in S17_S Stage-1 discussion.
NOT formally applied to all strategies in the repo (L1-L5, S1, S3_L, S3_S).
Full classification is a portfolio-management task — user decides whether to pursue.

| Family | Dimension | Example |
|--------|-----------|---------|
| G | Momentum cross (math indicators) | S16_S: ZLEMA fast/slow cross + slope |
| B | K-bar patterns (price structure) | S17_S Layer 2: bounce failure pattern |
| C | Statistical environment (trend/range/vol state) | S17_S Layer 1: daily MA direction |

### Q5: S17_S MC12 workspace setup (DEFINED)

- Data1: TXF1 60min (primary: K-bar pattern recognition, entry/exit)
- Data2: TXF1 Daily (environment filter: downtrend confirmation)
- S16_S comparison: Data1 only (5M), no Data2

### Q6: S16_S -> S17_S relay in backtesting (CLARIFIED)

Theoretical relay: S16_S catches fast drop first, S17_S catches continuation days later.
BUT they operate INDEPENDENTLY — S17_S does not wait for or depend on S16_S.
S17_S can trigger alone (slow decline where S16_S slope threshold not met).
Portfolio analysis combines equity curves after individual backtests.

### Q7: S16_S stop loss layers (EXPLAINED)

| Layer | Name | Chinese | Function |
|-------|------|---------|----------|
| 1st | QuickStop | Quick recognition of loss | 4 bars or 60pts loss within entry -> immediate exit |
| 2nd | ML (Multi-Layer) | Multi-dimensional real-time monitoring | 5 categories weighted score >= 60% + >= 3 categories -> exit |
| 3rd | BE (Break-Even) | Profit lock at cost basis | Profit >= 2.5xATR -> stop moves to entry+15pt; >= 3.5xATR -> entry+20pt |
| Last | ATR x 4 | Absolute last resort | P3b SetStopLoss engine-level, active from entry moment |

### Q8: S17_S stop loss — can it avoid big losses? (HONEST ANSWER)

**Status: NOT YET DESIGNED. Cannot claim "yes."**

Core tension: 60M normal volatility is 50-100 pts per bar.
- Too tight stop = whipsawed constantly
- Too wide stop = big loss on V-reversal

Framework direction (needs backtesting validation):

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| 1st | P3b SetStopLoss (engine-level) | Absolute floor, active from entry |
| 2nd | 60M bar-close confirmation stop | Not whipsawed by intrabar noise, but confirmed reversal = exit |
| 3rd | Daily environment flip stop | C-layer flips bullish = unconditional exit |
| Protection | BE profit lock (scaled for 60M) | Lock profit after threshold reached |

**Every layer's specific values require MC12 backtest data to determine.**

### Q9: Rebound scenarios for 60M short strategy (LISTED)

| Threat | Type | Characteristics | Why dangerous |
|--------|------|-----------------|---------------|
| FATAL | V-shaped reversal | Fast drop then instant full reversal | All short signals correct, but structure flips. 60M bar-close wait = severe loss |
| FATAL | Short squeeze cascade | Mass short covering, non-fundamental | Daily environment still bearish, but short-term violent upward |
| HIGH | Policy event rebound | Central bank / official intervention | Sudden, unpredictable, strong, unknown duration |
| HIGH | Gap-up open | Overnight international bullish news | Stop orders jumped over, 200+ pt gap |
| MEDIUM | Technical bounce (support/resistance) | Buying at prior lows / round numbers | Core S17_S judgment: real or fake bounce? |
| MEDIUM | Month-end institutional window dressing | Month/quarter-end settlement manipulation | Short (1-3 days) but significant force |
| LOW-MED | Ex-dividend distortion | Mass ex-dividend changes index calculation | Looks like decline but just dividend adjustment |

**Core risk**: Misjudging a real reversal as a fake bounce = hold short into a rising market = big loss.

---

## Part D: Pending Discussion Topics (Desktop Continue)

### Priority 1 — Market Condition Suitability Definition
- Define S17_S "home field" (what conditions it thrives in)
- Define S17_S "away field" (what conditions to endure)
- Define S17_S "no-go zone" (what conditions to avoid entirely)

### Priority 2 — Stop Loss Architecture Design
- Concrete P3b distance for 60M structure
- Bar-close confirmation stop specifics
- Daily environment flip criteria
- BE threshold scaling for swing holding

### Priority 3 — Rebound Scenario Handling SOP
- Each of the 7 rebound types: detect, respond, or endure?
- Which rebounds trigger exit vs. which are noise to hold through?

### Still Pending from Stage-1
- Topic 2: Boundary separation (S16_S vs S17_S delineation)
- Topic 3: Holding/exit philosophy + holiday rule conflict
- Topic 4: Rally handling (endure vs exit-and-re-enter)
- Topic 5: Insurance cost budget (bull-year loss budget)
- Topic 6: W0 verification design (Python pre-verify)

---

## Part E: User Rulings This Session

| Ruling | Date | Content |
|--------|------|---------|
| Overnight risk | 2026-07-21 | NOT a problem for S17_S, not a design obstacle |
| Trade frequency | 2026-07-21 | Just needs to be non-interfering between S16_S and S17_S |
| S17_S alpha | 2026-07-21 | Post-bounce-failure continuation decline, not MA transition moment |
| Entry principle | 2026-07-21 | Operating timeframe determines strategy condition form |

---

## Part F: Files Modified/Created This Session

| File | Action | Content |
|------|--------|---------|
| `S17_S_STAGE1_LAPTOP_HANDOFF_20260721.md` | NEW | This handoff document |

No .pla files modified. No existing documents modified.
S16_S STRATEGY_TEXT/OPEN_ISSUES stale number fixes deferred (not blocking).
