# L1 TrendLong — P3 Initial Stop Loss Architecture Design (2026-07-23)

## Background

V3.0 IOG migration complete. P7=T200 decided. P3 initial stop loss is the primary optimization target.

### Core Problem (Live Trading Discovery, June-July 2026)

1. ATR-based SL at 40-48K index level produces 500-1000 pt stops (0.78% avg vs 0.35% at 10-15K)
2. ATR scales FASTER than index level — non-linear acceleration at high prices
3. Choppy/declining market + high ATR = repeated massive stops before alpha emerges
4. Strategy bleeds MDD in observation phase before trend can develop

### Sealed Items (DO NOT REOPEN — Data Death Penalty 2026-07-22)

- 停損收緊 34 variants
- Fixed point % cap
- Daily cap (V2.8)
- P3b buffer
- Narrow-range reclaim
- Broad re-entry (Plan C)

## Design Process

### Stop Loss Philosophy Framework (5 Categories)

| Category | Question Answered | Examples |
|----------|------------------|----------|
| 波動率錨 | "I lost how much?" | ATR, fixed pts |
| 指數位階錨 | "What % of price?" | Fixed % of entry |
| 結構錨 | "Is entry thesis still valid?" | Breakout level, swing low, bar low |
| 行為錨 | "Did something change?" | Reversal bar, time stop |
| Regime 錨 | "What kind of market is this?" | Trend vs choppy classification |

### Four Dimensions Evaluated

1. **Distance basis** — What determines the SL distance?
2. **Time dimension** — Frozen vs evolving vs dynamic?
3. **Conditional vs universal** — Same for all trades or situational?
4. **Interface with P4/P7** — How does SL hand off to trail/profit protection?

### Key User Rulings During Design

1. ATR should be black swan insurance (ground floor security), NOT primary SL
2. Fixed % alone is insufficient — ignores volatility state
3. Should observe recent (1-2 week) oscillation amplitude for calibration
4. Engulfing K alone not enough — need combo patterns (e.g., 連三黑)
5. Time stop NOT suitable for trend strategy (trends need time to develop)
6. Price-based breakeven in 0-199 range would kill trend strategy's core edge
7. Behavioral trigger + SL halving (Option C) selected over breakeven
8. SL halving executes ONCE only (flag lock)

### Critical Insight: The Vacuum Problem

```
Entry → [Initial SL only] → ??? → [P4 Trail] → [P7 Profit Protection]
                              ↑
                    0 to +199 pts: NO protection
```

- P7=200 activates at +200 profit (giveback to +90)
- P4 MA55 trail needs significant price movement to form useful level
- Between 0 and +199 profit: only initial SL (potentially -300 pts away) protects

**Resolution**: Not price-based breakeven (kills trend edge), but BEHAVIORAL tightening — only tighten when market shows weakness signals.

## Final Architecture: 4-Layer + 1 Sub-Layer

### Layer 0: ATR Outer Wall (Last Defense)

| Item | Detail |
|------|--------|
| Role | Black swan / flash crash / gap — absolute max loss |
| Formula | Current: `min(ATR20_45M × 1.5, Daily_ATR20 × 0.5)` |
| Freeze | Calculated at entry bar, permanently frozen |
| Trigger | IOG + Bar Magnifier 1 Min (checked every minute) |
| Position | Should rarely trigger. If triggered = extreme market, accept loss |
| Gap | Price gaps through → accept slippage, market reality |

### Layer 1: Primary SL (Recent Pullback Amplitude)

| Item | Detail |
|------|--------|
| Role | Day-to-day first line of defense, based on actual recent market behavior |
| Basis | Max pullback depth over recent 10 trading days (Data2 Daily) |
| Concept | `Max drawdown within last 10 days × ratio` |
| Freeze | Calculated at entry, permanently frozen |
| Cap | Cannot exceed Layer 0 ATR wall (take the tighter) |
| Floor | Minimum threshold to prevent excessively tight SL in low-vol |
| Position | Replaces ATR as the PRIMARY stop loss |

Relationship to Layer 0:
```
Primary SL (Layer 1) ≤ ATR Wall (Layer 0)

Normal: Layer 1 effective (tighter)
Extreme: Layer 1 output too wide → ATR wall caps it
Ultra-low vol: Layer 1 output too tight → floor catches it
```

### Layer 1b: Behavioral Tightening (K-Bar Pattern Trigger)

| Item | Detail |
|------|--------|
| Role | Detect weakness during holding → reduce exposure |
| Trigger A | 連三黑: 3 consecutive Close < Open, total decline > Primary SL × 20% |
| Trigger B | Large engulfing: Close < prev Open, body > recent avg body × 2 |
| Logic | A **OR** B, either triggers |
| Action | Primary SL distance HALVED (e.g., -300 → -150) |
| Execution | **ONE TIME ONLY** — boolean flag locks after first trigger |
| Direction | Only tighten, never loosen |
| Timing | Checked at BarStatus(1)=2 (bar close confirmation) |

New SL position after trigger:
```
New SL = Entry - (Original Primary SL Distance / 2)
```

### Layer 2: P7 Profit Protection (Existing — T200 Ruling)

| Item | Detail |
|------|--------|
| Role | Profit protection after threshold reached |
| Params | stopProfitPoints_Long=200, profitReturnPrcnt_Long=55 |
| Trigger | Unrealized profit ≥ 200 pts |
| Exit | Profit drops to 200 × 45% = 90 pts → full exit |
| Status | T200 user ruling (2026-07-23), not being modified |

### Layer 3: P4 Trend Trail (Existing)

| Item | Detail |
|------|--------|
| Role | Long-term trend profit tracking |
| Params | MA55-based, TrailOffset=50, V3.0 ratchet mechanism |
| Trigger | MA55 trail forms effective protection level |
| Status | To be optimized independently after P3 work |

## Layer Coverage on Price Axis

```
              Loss ← ──────── Entry ──────── → Profit

Price:  43700    43850    44000         44200      44400+
          │        │        │             │          │
Layer 0:  ATR Wall │        │             │          │
Layer 1:  ···Primary SL···  │             │          │
Layer 1b: ·······Halved SL  │             │          │
                             │             │          │
Layer 2:                     │         P7=200 start  │
                             │         (floor +90)   │
Layer 3:                     │             │      P4 trail
```

## Trade Lifecycle Trigger Sequence

```
Entry → Layer 0 + Layer 1 both active (Layer 1 tighter, guards)
  │
  ├─ Price drops directly → Layer 1 triggers → exit
  │
  ├─ Flash crash / gap → Layer 0 triggers → exit
  │
  ├─ Price oscillates, 連三黑 or engulfing appears
  │    → Layer 1b triggers → SL halved → continue holding
  │    → If continues down → halved SL triggers → exit
  │    → If rebounds → halved SL stays, no loosening
  │
  ├─ Profit reaches +200
  │    → Layer 2 (P7) activates → drops to +90 → exit
  │
  └─ Strong trend develops
       → Layer 3 (P4) trail tracks up → trend ends → exit
```

## Self-Verification: Problem & Resolution Matrix

| Problem | Severity | Resolution | Cost |
|---------|----------|------------|------|
| Layer 1b triggers multiple times → SL over-tightened | High | Execute once only, boolean flag lock | 1 bool variable |
| Layer 1b triggers while already losing | Low | Correct behavior — weakness + losing = exit | None |
| Tiny black K bars false-trigger 連三黑 | Medium | Total decline > SL×20% threshold | Tied to SL, no extra param |
| Large bearish bar confirmed only at bar close | Low | ATR wall handles extreme intrabar, Layer 1b handles medium-term | None |
| False signal → irreversible tightening → miss winner | Medium | Accept as cost, backtest to verify net positive | Needs backtest |
| Conflict with P4/P7 | None | Independent layers, whichever triggers first fires | None |

## Pending Items (Next Session)

| # | Item | Status |
|---|------|--------|
| 1 | Layer 1: Exact calculation formula for recent pullback depth | Concept confirmed, formula TBD |
| 2 | Layer 1: Floor minimum value | TBD |
| 3 | Layer 1: Pullback-to-SL ratio (× what %) | Needs backtest |
| 4 | Layer 1b: 連三黑 total decline threshold (SL×20% or other) | Needs backtest |
| 5 | Layer 1b: Engulfing average body calculation period | TBD |
| 6 | Full architecture backtest validation | To execute |

## Priority After P3

1. P4 trailing stop optimization (MA type, length sweep, TrailOffset)
2. P7 threshold sweep (only if P3/P4 results warrant)
3. Reclaim mechanism (deferred)
