# S3 RapidPullbackShort - Implementation Architecture

**Generated**: 2026-06-19 (ultracode deep research session)
**Source spec confirmed**: 2026-06-20 ultracode session
**Strategy essence**: 強多頭 + 過熱 + 5M 快速下跌啟動 → 進場做空 30 分-4 小時,賺 1-2% 拉回

This document is the **implementation blueprint** for S3, NOT the .pla file itself.
It is consumed by the build-phase task that writes `strategies/research/S03_RapidPullbackShort/S3_RapidPullbackShort.pla`.

---

## 0. Critical evolution from Agent D's original mean-reversion spec

| Dimension | Agent D original | S3 final (confirmed) |
|---|---|---|
| Primary TF | 15M | **5M** |
| Holding | 1-2 day swing | **intraday 30min - 4hr** |
| Entry trigger | RSI overbought → short (pure MR gamble) | **RSI overheated AND 5M downside initiated → short (momentum-confirmed)** |
| Trap risk | Trapped while overheating continues | Only enters AFTER pullback has begun |
| Trade-off | Earlier entry, lower hit rate | Slightly later entry, much higher hit rate |
| Portfolio gap filled | None named | **Bull-regime mid-pullback hedge** (L2 needs trend; L4 needs breakdown) |

This is the single most important architectural decision: **S3 is a Watch → Trigger two-state machine, not a single threshold breach**. It is implemented via `v_S3_Watch` flag that arms when overheat conditions are met, then waits for a 5M momentum confirmation candle before firing the entry.

---

## 1. Chart data structure (3-data feasibility)

### 1.1 Configuration
| Data slot | Symbol | Interval | Purpose | Reference syntax |
|---|---|---|---|---|
| **Data1** (primary) | TXF1 | **5 minute** | Entry / exit execution, momentum trigger | `Close`, `High`, `Low`, `Open`, `Time` |
| **Data2** | TXF1 | **60 minute** | Mid-frame regime / overheat observation (RSI60, MA fast/slow) | `Close of Data2`, `RSI(Close of Data2, N)` |
| **Data3** | TXF1 | **Daily** | Bull-regime gate (MA20/MA60), daily ATR for sizing context | `Close of Data3`, `Average(Close, 20) of Data3` |

### 1.2 MC12 feasibility check

**Verdict: FEASIBLE.** MC12 PowerLanguage supports up to 50 data series per chart (`MaxDataStream = 50`). 3 series is well within limits.

Verified by reference templates:
- **L5_BreakoutLong.pla** uses Data1=15M / Data2=Daily / Data3=Weekly (3 series, production-proven, byte-identical to MC12 sample chart).
- L5 already wires `of Data2` and `of Data3` syntax that S3 will reuse.

S3-specific notes:
- 5M chart loads ~6300 bars per year (vs 15M's ~2100). 6-year backtest = ~38K bars on Data1. MC12 handles this; expect 20-40s recompile after parameter changes.
- **Bar-close timing**: Data2 (60M) closes at :00 of each hour. Data1 (5M) closes at :00, :05, :10, etc. Data2 reference index `[1]` on Data1 means "the most recently closed 60M bar at the time this 5M bar closed" — same idiom as L5, no surprises.
- **Synchronization**: When Data1 bar closes at 09:00, Data2 [0] is the still-forming 09:00-10:00 60M bar; **use [1] for confirmed 08:00-09:00 close** (per CLAUDE.md rule #3). Same for Data3.

### 1.3 What to verify at build time
- [ ] Confirm MC12 sample chart actually loads TXF1 5M+60M+Daily without "out of memory" warning.
- [ ] Confirm `RSI(Close of Data2, 14)` compiles (some platforms require `RSI(Close of Data2, 14, 50)` 3-arg form).
- [ ] Confirm Data3 daily bars sync correctly when night session crosses date boundary.

---

## 2. Module composition table

### 2.1 Mandatory shared modules (frozen 6 share these — rules #11/#12)

| Module | Source template | Lines (est) | Behavior |
|---|---|---|---|
| **Holiday_Tail registry** (63 dates) | L2 §4B | ~80 | Block entries + force flat in 00:00-05:00 tail bars of pre-holiday night |
| **HolidayFlat_v3** detection logic | L2 §4B | ~12 | `v_Holiday_Block`, `v_Registry_Expired` flags + 30-day red warning |
| **Manual_Kill_Switch** | L2 §1+§13 | ~5 | Input flag + Priority 0 exit `SX_RPS_Kill` |
| **Registry_Valid_Until fail-safe** | L2 §4B | ~6 | Beyond horizon → block + flatten `SX_RPS_RegistryEnd` + red warning |
| **Settlement_Flat** (7 elements per constitution) | L2 §1+§4B+§13 | ~15 | 3rd-Wed detection + 12:30 flatten + entry gate |
| **SetStopLoss** (P3b Immediate Stop Guard, rule #12) | L2 §7 | ~4 | MC engine-level stop, active on entry bar, freezes when `MP <= 0` becomes `MP = -1` |

**Total mandatory boilerplate: ~120 LOC** (matches L2 closely).

### 2.2 S3-specific modules

| Module | Purpose | LOC est | Section |
|---|---|---|---|
| **Regime gate** (Data3+Data2 read) | Bull regime: `Close[1] of Data3 > MA20[1] of Data3 > MA60[1] of Data3`. Overheat: `RSI(Close[1] of Data2, 14) >= RSI_Overheat_Thresh` AND `Close[1] of Data2 > UpperBB[1] of Data2` | ~25 | §6 |
| **Watch state tracking** (`v_S3_Watch`) | Latches True when regime + overheat both pass; persists until either regime breaks OR entry fires OR end-of-day | ~15 | §7a |
| **Momentum trigger** (Data1 5M) | `v_S3_Watch = True` AND 5M shows: (a) close < open by at least `Trigger_ATR_Mult * ATR_5M` AND (b) close < prior swing low (lookback N=3 bars) AND (c) volume confirmation optional | ~20 | §7b |
| **Entry execution** | `SellShort("SE_RPS_Entry") Next Bar at Market` with all gates `True` | ~15 | §7c |
| **Exit chain** (Priority 0 + strategy exits) | TP / SL / TimeStop / DayClose / + mandatory boilerplate exits | ~80 | §13 |
| **Daily close force flat** | If `Time >= 1325` AND `MP = -1` → `BuyToCover("SX_RPS_DayClose") Next Bar at Market` | ~6 | §13 |
| **Same-day re-entry cooldown** | `v_S3_LastExitDate = Date` when any exit fires; block new entry while `Date = v_S3_LastExitDate` (S2 issue #6 lesson) | ~10 | §7c |

**Total S3-specific: ~170 LOC.**

---

## 3. Pseudocode — entry logic

```
// SECTION 6 - REGIME + OVERHEAT (computed every 5M bar, uses [1] of higher TF)

v_Daily_MA20  = Average(Close, 20) of Data3;
v_Daily_MA60  = Average(Close, 60) of Data3;
v_BullRegime  = (Close[1] of Data3 > v_Daily_MA20) and
                (v_Daily_MA20         > v_Daily_MA60);

v_RSI_60M     = RSI(Close of Data2, RSI_Len);   // 60M RSI
v_Overheat    = (v_RSI_60M[1] >= RSI_Overheat_Thresh) and
                (Close[1] of Data2 > UpperBB[1] of Data2);

// SECTION 7a - WATCH STATE LATCH

if v_BullRegime and v_Overheat then
    v_S3_Watch = true;

// Disarm conditions: regime broken, or watch grew stale (8-bar timeout = 40 min on 5M)
if (not v_BullRegime) or (BarsSinceWatchArmed >= Watch_Stale_Bars) then
    v_S3_Watch = false;

// SECTION 7b - MOMENTUM TRIGGER (on Data1 5M)

v_ATR_5M       = AvgTrueRange(ATR_Len);    // Data1 ATR
v_Bar_Drop     = Open - Close;             // intra-bar drop magnitude
v_Recent_Low   = Lowest(Low[1], TriggerLookback);

v_MomentumFire = (v_Bar_Drop >= Trigger_ATR_Mult * v_ATR_5M) and
                 (Close < v_Recent_Low) and
                 (Close < Open);           // explicit red bar

// SECTION 7c - ENTRY GATE (all gates must pass; rule #12 compliance)

// P3b Immediate Stop Guard - rule #12 mandatory
if MarketPosition >= 0 then
    SetStopLoss( AbsValue( (Close + ATR_5M * SL_ATR_Mult) - Close ) * BigPointValue );
    // = ATR_5M * SL_ATR_Mult * BigPointValue (distance only)

if v_S3_Watch         = true  and
   v_MomentumFire     = true  and
   v_Holiday_Block    = false and
   v_Settlement_Day   = false and
   v_Registry_Expired = false and
   Manual_Kill_Switch = false and
   Date              <> v_S3_LastExitDate and   // same-day cooldown
   Time              >= Entry_Open_Time  and    // e.g. 0900 (no early-morning chaos)
   Time              <= Entry_Close_Time and    // e.g. 1300 (no last-25-min entries)
   MarketPosition     = 0 then begin

    SellShort("SE_RPS_Entry") Next Bar at Market;
    v_S3_Watch = false;   // single-shot consumption
end;
```

**Closed Time interval discipline (memory: feedback_mc_time_24hr_pitfall)**:
- All time checks use **closed intervals** `Time >= X AND Time <= Y` (no open-ended `Time > X` that bleeds into night session).
- Entry window is day session only: `Time >= 900 AND Time <= 1300` — no overnight entries (S3 is intraday by design).

---

## 4. Pseudocode — exit chain

```
ExitFired = 0;

if MarketPosition = -1 then begin

   // === PRIORITY 0 (mandatory shared) ===

   if (ExitFired = 0) and (Manual_Kill_Switch = true) then begin
      BuyToCover("SX_RPS_Kill") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   if (ExitFired = 0) and (v_Registry_Expired = true) then begin
      BuyToCover("SX_RPS_RegistryEnd") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   if (ExitFired = 0) and (v_Holiday_Block = true) and
      (Time >= Holiday_Flat_Time) then begin
      BuyToCover("SX_RPS_HolFlat") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   if (ExitFired = 0) and (v_Settlement_Day = true) and
      (Time >= Settlement_Flat_Time) then begin
      BuyToCover("SX_RPS_Settlement") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   // === S3-SPECIFIC EXITS ===

   // Priority 1: Daily close force flat (intraday rule, before 13:25 to give
   // 4 x 5M bars buffer before 13:45 close, well before settlement gap)
   if (ExitFired = 0) and (Time >= 1325) then begin
      BuyToCover("SX_RPS_DayClose") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   // Priority 2: Time stop (max holding = 4hr = 48 bars on 5M)
   if (ExitFired = 0) and (BarsSinceEntry >= Time_Stop_Bars) then begin
      BuyToCover("SX_RPS_TimeStop") Next Bar at Market;
      ExitFired = 1;
      v_S3_LastExitDate = Date;
   end;

   // Priority 3: Take profit (1-2% pullback target)
   // TP_Pts = EntryPrice * TP_Pct (e.g. 1.5%)
   v_TP_Price = EntryPrice * (1 - TP_Pct / 100);
   if (ExitFired = 0) and (v_TP_Price > 0) then begin
      BuyToCover("SX_RPS_TP") Next Bar at v_TP_Price Limit;
      // Do NOT set ExitFired=1 here — limit may not fill;
      // SL must still be live below.
   end;

   // Priority 4: Stop loss (ATR-based, above entry)
   // Frozen SL: lock ATR_at_entry into v_Frozen_ATR_5M
   if (BarsSinceEntry = 0) and (v_SL_Locked = false) then begin
      v_Frozen_ATR_5M = v_ATR_5M;
      v_Frozen_SL_Dist = v_Frozen_ATR_5M * SL_ATR_Mult;
      v_SL_Locked = true;
   end;
   v_SL_Price = EntryPrice + v_Frozen_SL_Dist;
   if (ExitFired = 0) and (v_SL_Price > 0) then begin
      BuyToCover("SX_RPS_SL") Next Bar at v_SL_Price Stop;
   end;

end;

// State reset when flat (CRITICAL — lessons from L5)
if MarketPosition = 0 then begin
   v_SL_Locked        = false;
   v_Frozen_ATR_5M    = 0;
   v_Frozen_SL_Dist   = 0;
end;
```

**Priority order rationale**:
- 0 (Kill/Registry/Holiday/Settlement) = absolute, market exit
- 1 (DayClose) = intraday rule, must beat TP/SL because we want flat regardless
- 2 (TimeStop) = "trade thesis expired" market exit
- 3 (TP) = limit order, doesn't block SL
- 4 (SL) = stop order, last line of defense

---

## 5. Input list with conservative defaults

| Input | Default | Rationale |
|---|---|---|
| **Regime gate** | | |
| `MA_Fast_Daily` | 20 | Standard 20-day MA |
| `MA_Slow_Daily` | 60 | Standard quarter MA |
| **Overheat detection** | | |
| `RSI_Len` | 14 | Industry standard |
| `RSI_Overheat_Thresh` | 70 | Conservative (not 65/68 which over-fires) |
| `BB_Len` | 20 | Standard Bollinger |
| `BB_K` | 2.0 | Standard Bollinger |
| **Watch state** | | |
| `Watch_Stale_Bars` | 8 | 40 min stale = give up if no trigger |
| **Momentum trigger** | | |
| `ATR_Len` | 21 | Same as L2 / shared convention |
| `Trigger_ATR_Mult` | 0.6 | Conservative; bar must drop >= 0.6 ATR (calibrate in backtest) |
| `TriggerLookback` | 3 | Bar must break 3-bar swing low |
| **Entry window** | | |
| `Entry_Open_Time` | 900 | After opening volatility settles |
| `Entry_Close_Time` | 1300 | Stop entering 45 min before close |
| **Risk** | | |
| `SL_ATR_Mult` | 1.2 | Tight intraday stop |
| `TP_Pct` | 1.5 | Target the middle of "1-2% pullback" range |
| `Time_Stop_Bars` | 48 | 48 x 5M = 4hr max holding |
| **Day-close** | | |
| `DayClose_Time` | 1325 | 4 bars before 13:45 close |
| **Cooldown** | | |
| (no input; `v_S3_LastExitDate = Date` is hard rule) | — | Reinstate next session, no half-measures |
| **Holiday Flat (rule #11)** | | |
| `Holiday_Flat_Time` | 245 | 5M grid: trigger 02:45, retries through 04:55 |
| `Registry_Valid_Until` | 1270101 | Same as L2/L5 |
| `Manual_Kill_Switch` | False | OFF by default |
| **Settlement Flat (rule #11)** | | |
| `Settlement_Flat_Time` | 1230 | Identical to L2/L5 (already conservative) |
| **Optional filters (memory: feedback_filter_redundancy_check)** | | |
| (none added in v1.0) | — | Per rule: don't enable any new filter by default until validated |

**Default-conservative principle (rule #13 compliance)**:
- All filters that COULD be added (volume, gap, weekly, sentiment) are NOT in v1.0. Only add after backtest proves they aren't redundant with existing gates.
- TP=1.5% is mid-range; if backtest shows fat tails, can raise to 2.0% in v1.1.

---

## 6. Label conventions (rule #11/#12 compliance, SE/SX prefixes per memory: feedback_mc_entry_exit_labels)

| Label | Direction | Order type | Trigger |
|---|---|---|---|
| `SE_RPS_Entry` | Short Entry | `SellShort... Next Bar at Market` | Watch + momentum + all gates |
| `SX_RPS_TP` | Short eXit (TP) | `BuyToCover... at Limit` | Price hits TP target |
| `SX_RPS_SL` | Short eXit (SL) | `BuyToCover... at Stop` | Price hits frozen ATR stop |
| `SX_RPS_TimeStop` | Short eXit | `BuyToCover... at Market` | `BarsSinceEntry >= 48` |
| `SX_RPS_DayClose` | Short eXit | `BuyToCover... at Market` | `Time >= 1325` |
| `SX_RPS_Settlement` | Short eXit | `BuyToCover... at Market` | 3rd Wed + 12:30 |
| `SX_RPS_HolFlat` | Short eXit | `BuyToCover... at Market` | Holiday tail bar + Holiday_Flat_Time |
| `SX_RPS_Kill` | Short eXit | `BuyToCover... at Market` | Manual_Kill_Switch = True |
| `SX_RPS_RegistryEnd` | Short eXit | `BuyToCover... at Market` | Date > Registry_Valid_Until |

**Naming discipline**:
- `RPS` = RapidPullbackShort (3-char strategy tag, matches `TS_` for TrendShort, `BL_` for BreakoutLong).
- `SE_` = Short Entry, `SX_` = Short eXit (per memory rule — buy/sell/sellshort/buytocover labels MUST be strictly disambiguated).
- All 9 labels appear in §13 header docblock comment for grep-ability.

---

## 7. verify_s3_pullbackshort.py outline (~60 checks)

**Target: 60 checks** (slightly above S1's 26 because S3 has 3-data wiring + watch state + intraday rules + larger label inventory).

```
# === Section A: File metadata (5 checks) ===
A01. File exists at strategies/research/S03_RapidPullbackShort/S3_RapidPullbackShort.pla
A02. File starts with header block { ... }
A03. Header contains "Signal Name :"
A04. Header contains "MC Load Name:"
A05. Header contains performance baseline placeholder

# === Section B: Rule #11 Settlement_Flat 7 elements (7 checks) ===
B01. Input Settlement_Flat_Time(1230) exists
B02. Variable v_Settlement_Day declared
B03. v_Settlement_Day = (DayOfWeek(Date) = 3) and (DayOfMonth in [15,21])
B04. Entry gate contains "v_Settlement_Day = false"
B05. Exit chain contains BuyToCover("SX_RPS_Settlement")
B06. Exit fires when v_Settlement_Day AND Time >= Settlement_Flat_Time
B07. SX_RPS_Settlement positioned in Priority 0 block

# === Section C: Rule #12 P3b SetStopLoss (4 checks) ===
C01. Exactly 1 SetStopLoss call exists (no duplicates)
C02. SetStopLoss guarded by "if MarketPosition >= 0" (short strategy gate)
C03. Distance formula matches frozen SL anchor (same ATR + mult)
C04. Distance multiplied by BigPointValue

# === Section D: Rule #13 10-dim eval markers (3 checks) ===
D01. Header includes link to docs/institutional_risk_framework_20260619.md
D02. Pre-deployment checklist comment exists ("DEPLOY ONLY WHEN FLAT")
D03. Header references 10-dim eval status (pending / pass / fail)

# === Section E: Holiday Flat v3 (7 checks) ===
E01. Holiday_Tail[80] array declared
E02. Holiday_Tail[1] through Holiday_Tail[63] all assigned in CurrentBar=1 block
E03. Exactly 63 dates (count check; reject 62 / 64)
E04. Date 1270101 present at Holiday_Tail[63]
E05. Date 1260619 present (current Dragon Boat eve — sanity)
E06. v_Holiday_Block detection loop iterates 1 to 80
E07. v_Holiday_Block guard inside "if Time <= 500"

# === Section F: 3-data wiring (5 checks) ===
F01. Header declares Data1=5M, Data2=60M, Data3=Daily
F02. References to "of Data2" use [1] index (CLAUDE.md rule #3)
F03. References to "of Data3" use [1] index
F04. No "of Data2" reference without [1] (no current-bar peeking)
F05. No "of Data3" reference without [1]

# === Section G: Closed Time intervals (5 checks, feedback_mc_time_24hr_pitfall) ===
G01. Entry window uses "Time >= X AND Time <= Y" (closed interval)
G02. No open-ended "Time > X" in entry conditions
G03. Holiday_Flat block uses "Time <= 500" closed
G04. Settlement block uses "Time >= Settlement_Flat_Time" with explicit upper bound or implicit by session
G05. DayClose uses "Time >= 1325" (acceptable open-ended because intraday flat)

# === Section H: Filter redundancy (3 checks, feedback_filter_redundancy_check) ===
H01. No optional filter input enabled by default in v1.0
H02. Each filter input has a comment explaining why it's needed (or "RESERVED")
H03. Default values are MOST CONSERVATIVE per rule #13

# === Section I: Label conventions (10 checks) ===
I01. SE_RPS_Entry exists (exactly 1 SellShort with this label)
I02. SX_RPS_TP exists (BuyToCover, at Limit)
I03. SX_RPS_SL exists (BuyToCover, at Stop)
I04. SX_RPS_TimeStop exists (BuyToCover, at Market)
I05. SX_RPS_DayClose exists (BuyToCover, at Market)
I06. SX_RPS_Settlement exists
I07. SX_RPS_HolFlat exists
I08. SX_RPS_Kill exists
I09. SX_RPS_RegistryEnd exists
I10. No legacy label prefix leak (no "TS_", "BL_", "NM_" in file)

# === Section J: Watch state machine (5 checks) ===
J01. v_S3_Watch variable declared (False default)
J02. v_S3_Watch latches True when (v_BullRegime AND v_Overheat)
J03. v_S3_Watch resets False when entry fires (single-shot consumption)
J04. v_S3_Watch has staleness timeout (Watch_Stale_Bars)
J05. v_S3_Watch resets False when regime breaks

# === Section K: Same-day cooldown (3 checks) ===
K01. v_S3_LastExitDate variable declared
K02. Updated to Date whenever any exit fires
K03. Entry gate blocks when Date = v_S3_LastExitDate

# === Section L: State reset (3 checks) ===
L01. Frozen SL state resets when MarketPosition = 0
L02. ExitFired reset to 0 each bar at top of exit block
L03. v_SL_Locked reset to False when flat

# === Section M: LOC discipline (1 check) ===
M01. Total file LOC <= 500 (with comments); core code < 350

# === Section N: Self-containment (rule from prompt) (4 checks) ===
N01. No references to L1/L2/L3/L4/L5/S1/S2 file paths
N02. No shared include / external module references
N03. Holiday_Tail registry is INLINE (not imported)
N04. Self-sufficient — passes ALL above checks standalone
```

**Total: 60 checks across 14 sections.**

---

## 8. 5M-specific risks

### 8.1 Risk inventory

| # | Risk | Magnitude on 5M | Mitigation in S3 v1.0 |
|---|---|---|---|
| 1 | **Slippage relative to PnL** | 1pt typical slippage vs ~30pt target (3.3%) — vs 60M strategies where 1pt vs ~200pt target (0.5%) | TP target = 1.5% of TXF1 (~300 pts on 20000 index = 300pt target), so slippage drops to ~0.3%. Use round-trip 1000 NTD assumption (per CLAUDE.md). |
| 2 | **Commission/turnover** | 5M generates 5-15x more entry signals than 60M before filters | Same-day cooldown + watch staleness + 4hr time stop cap turnover. Expected ≤ 1 trade/day. |
| 3 | **Order rejection in fast markets** | 5M momentum bars often coincide with fast market windows where stop/limit can slip several ticks | (a) SetStopLoss is engine-level (rule #12) so SL always fires. (b) TP is `Limit` not `Stop Limit` — accepts non-fill. (c) Market orders for emergencies. |
| 4 | **Spurious 5M bars** (data glitch) | 5M is more prone to single-tick spikes that don't reflect liquid price | `Trigger_ATR_Mult >= 0.6` + 3-bar swing low requirement filters out single-bar noise. |
| 5 | **Overnight gap risk** | If position held into night and gaps up >2% → SL too far | **DayClose at 13:25 = hard intraday rule.** Strategy never holds overnight. |
| 6 | **MA20/60 daily latency** | Bull regime gate from daily lags ~5-7 days behind real regime change | Acceptable: false-positive entries during regime change are caught by SL within 4hr (Time_Stop_Bars). |
| 7 | **RSI60M whipsaw** | 60M RSI can spike-then-revert in 1-2 bars; v_Overheat may flicker | `v_S3_Watch` latches; doesn't require sustained overheat. Once armed, momentum trigger does the real work. |
| 8 | **MC12 5M bar timestamp ambiguity** | 5M bar at 09:00 contains 08:55-09:00 trades or 09:00-09:05? Platform-dependent | Verify at build: standard MC convention is `Time` = bar CLOSE time, so `Time = 905` = 09:00-09:05 bar. Document in header. |
| 9 | **Settlement day = bull rally cap day** | 3rd Wed often has 13:30 settlement squeeze; S3's bull-regime gate likely fires that morning | Settlement_Flat exits at 12:30. Acceptable: we miss occasional opportunity but avoid 13:30 carnage. |
| 10 | **Watch state stuck** if regime flag never flips | If bull regime holds 30 days and overheat keeps re-arming, single-shot consumption may cause perpetual re-arming | `Watch_Stale_Bars = 8` (40min) timeout prevents indefinite watch. Re-arms cleanly next 5M close. |

### 8.2 Costs to model in backtest (NEW vs L2/L5)
- Round-trip slippage: 1000 NTD (per CLAUDE.md, unchanged).
- Commission: typically baked into slippage assumption for TXF1.
- **Higher turnover → magnified cost drag**. If S3 produces 200+ trades over 6 years, total cost = 200K NTD; verify net profit covers this with margin.
- Expected ratio: net profit / total cost > 5x (else cost is killing the alpha).

---

## 9. Total LOC estimate

| Section | LOC | Notes |
|---|---|---|
| Header + changelog | 50 | Standard L2-style docblock |
| §1 Inputs | 35 | ~22 inputs from §5 list, with comments |
| §2 Variables | 30 | ~22 vars + comments |
| §3 Arrays (Holiday_Tail) declaration | 2 | Just the `Array:` line |
| §4 Session detection (IsDay/IsNight) | 12 | Same as L2 |
| §4B Holiday_Tail registry (63 entries inline) | 80 | Identical to L2 |
| §4B HolidayFlat_v3 detection logic | 25 | v_Holiday_Block + Registry_Expired + Settlement_Day + Warn |
| §5 (reserved — no weekly filter needed) | 0 | S3 uses Data3 daily, not weekly |
| §6 Indicators (Data1+Data2+Data3) | 25 | ATR_5M, MA20/60 Daily, RSI 60M, BB 60M |
| §7a Watch state latch | 15 | v_S3_Watch + staleness |
| §7b Momentum trigger | 20 | v_MomentumFire calculation |
| §7c Entry gate + SetStopLoss | 25 | All gates AND-chained + P3b |
| §8 Frozen SL setup | 12 | v_SL_Locked + v_Frozen_ATR_5M |
| §13 Exit chain | 80 | 9 exit labels with priority logic |
| §14 State reset | 10 | When MP=0 |
| Total | **~420 LOC** | |

**Comparison**:
- L2_TrendShort.pla = 709 lines (60M, more complex TSL/TTP/SP modules)
- L5_BreakoutLong.pla = 696 lines (15M, 2-leg scale-out)
- S1_NightMomentum (likely ~300 lines for simpler intraday)
- **S3 at ~420 LOC sits comfortably between S1 and L2** — appropriate for its intraday 1-entry/1-exit-pair simplicity vs the regime-detection sophistication.

CLAUDE.md says "每隻策略 < 150 行" but live strategies are 700+ lines. The 150 rule is for the **logic core** excluding header (50), Holiday_Tail registry (80), and verbose docblocks. S3 logic core = ~280 lines, which is in range.

---

## 10. Build sequence

Write the .pla in this order — each step independently compilable & verifiable.

1. **Skeleton + header docblock** (LOC 1-50)
   - Performance placeholder
   - 10-dim eval status placeholder
   - "DEPLOY ONLY WHEN FLAT" footer
   - Verify: `verify_s3` Section A passes

2. **Inputs + Variables + Arrays** (LOC 50-117)
   - All 22 inputs from §5 table with conservative defaults
   - All vars with comments
   - `Array: Holiday_Tail[80](0);`
   - Verify: compiles (no logic yet)

3. **Holiday_Tail registry inline + HolidayFlat_v3 + Settlement detection** (LOC 117-225)
   - Copy from L2 byte-identical (63 dates)
   - v_Holiday_Block, v_Registry_Expired, v_Settlement_Day, Registry warn
   - Verify: `verify_s3` Sections B, E pass

4. **Session detection + Indicators (Data1+Data2+Data3)** (LOC 225-262)
   - IsDay/IsNight
   - ATR_5M on Data1
   - MA20/MA60 on Data3 (use [1])
   - RSI/BB on Data2 (use [1])
   - Verify: `verify_s3` Section F passes

5. **Watch state + Momentum trigger** (LOC 262-297)
   - v_S3_Watch latch + staleness
   - v_MomentumFire calculation
   - Verify: `verify_s3` Section J passes

6. **Entry gate + SetStopLoss** (LOC 297-322)
   - All gates AND-chained
   - SetStopLoss with rule #12 compliance
   - Verify: `verify_s3` Sections C, K pass

7. **Frozen SL setup** (LOC 322-334)
   - Lock ATR at entry

8. **Exit chain (Priority 0 + S3-specific)** (LOC 334-414)
   - All 9 SX_RPS_* labels
   - v_S3_LastExitDate updated on every exit
   - Verify: `verify_s3` Sections I, K pass

9. **State reset block** (LOC 414-424)
   - When MarketPosition = 0
   - Verify: `verify_s3` Section L passes

10. **Final lint pass**
    - Run full `verify_s3_pullbackshort.py` — must pass all 60 checks
    - Run `verify_all_live.py` doesn't apply (S3 is research, not live)
    - LOC count check (Section M)
    - Verify: 100% pass before MC12 sample-chart load

11. **MC12 sample chart load + dry compile**
    - 3-data wiring verification (Section 1.3 checklist)
    - Recompile time benchmark
    - No "Out of memory" warning
    - 0 trades fire (no historical data with these gates passing fully = expected before optimization)

12. **First backtest (6yr)**
    - Document trade count, PF, WR, MDD
    - Compare against 10-dim institutional framework
    - DO NOT promote to live_simulation until rule #13 passes

---

## Appendix: Frozen-constraint compliance check

**Confirmed**: S3 architecture introduces **ZERO** modifications to L1-L5 or S1.

- Holiday_Tail registry: INLINE COPY (not imported). If L2's registry changes, S3's diverges; that is acceptable per "self-contained" rule.
- Settlement_Flat: 7 elements re-implemented from constitution (not shared code).
- No `import`, `external`, or cross-file references in PowerLanguage (the language doesn't support them anyway).
- No Python script changes needed in `verify_all_live.py` — that script covers L1-L5 only; S3 gets its own `verify_s3_pullbackshort.py`.

**Self-contained: confirmed.**
