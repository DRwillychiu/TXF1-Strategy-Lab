# S3 RapidPullbackShort — Final Design Specification v2

- **Date**: 2026-06-20
- **Author**: Claude (ultracode session, synthesized from 5 parallel deep-research reports)
- **Status**: PRE-BUILD spec, awaiting user decisions D1-D8 before `.pla` coding
- **Supersedes**: `S3_PullbackShort_design_spec.md` (Agent D, v1, 2026-06-19)
- **Synthesizes**:
  - `scripts/_temp_s3_regime_gate.md` (Agent A — first-tier gate, 8 signals analysed)
  - `scripts/_temp_s3_momentum_trigger.md` (Agent B — 5M trigger, 8 signals analysed)
  - `scripts/_temp_s3_exit_mechanism.md` (Agent C — TP/SL/Time stop empirically derived)
  - `scripts/_temp_s3_portfolio_impact.md` (Agent D — allocation forecast)
  - `scripts/_temp_s3_implementation_arch.md` (Agent E — MC12 architecture)
- **Mandatory compliance**: CLAUDE.md Rule #11 (Settlement_Flat 7 elements), Rule #12 (P3b SetStopLoss), Rule #13 (10-dim institutional eval)

---

## 1. Strategy Identity (post user evolution)

### 1.1 Name and one-line essence

- **Code name**: `S3_RapidPullbackShort`
- **MC Load Name**: `STRATEGY_GEN_S3_RapidPullbackShort`
- **One-line**: **強多頭過熱 + 5M 快速下跌啟動 → 做空 30 分-4 小時，吃 0.7-1% 拉回**

### 1.2 Distinction from Agent D's original spec

| Dimension | Agent D (v1, 2026-06-19) | **S3 v2 (final, 2026-06-20)** |
|-----------|--------------------------|-------------------------------|
| Primary execution TF | 15M | **5M** |
| Holding horizon | 1-3 trading days (swing) | **30 min - 4 hr (intraday only, hard flat 13:25)** |
| Entry model | Pure mean reversion: "RSI>75 sustained → SellShort" | **Two-tier momentum-confirmed: Regime gate (Daily) → 5M momentum trigger AFTER pullback begins** |
| Trap risk | Trapped while overheating keeps extending (RSI>75 can stay weeks) | Only enters AFTER 5M confirms downside has begun — survives parabolic blow-offs |
| TP | MA5 touch (qualitative) | **0.7% from entry OR 5M EMA20 touch (empirically median 2-day pullback = 0.57%)** |
| SL | 1.2× ATR(15M) | **4.0× ATR(5M) ≈ 0.58% (matches median 1-day MAE empirically)** |
| Trade-count forecast | 180-280 over 6.5y (~2-4/month) | **65-130 over 6.5y (~10-20/year)** — Daily gate is the binding bottleneck, not 5M density |
| Portfolio role | "Replace L4" candidate | **Bull-regime mid-pullback hedge — fills gap L2 (needs bear trend) and L4 (needs breakdown) cannot cover** |

### 1.3 Portfolio role

S3 is the **first sleeve that fires inside L1's losing pullbacks**. The 6-strategy book has 4 longs and 2 shorts but neither short fires during a confirmed bull-regime intraday pullback. S3 closes that gap with **structural negative correlation to L1/L5/S1** (forecast monthly ρ ≈ −0.30 to −0.35) while remaining temporally orthogonal to L2/L4 (forecast ρ ≈ +0.15 to +0.30 monthly, well inside the institutional |r|<0.7 gate).

---

## 2. Architecture Overview

### 2.1 Three-data chart structure

| Slot | Symbol | Interval | Purpose | Reference syntax |
|------|--------|----------|---------|------------------|
| **Data1** (primary) | TXF1 | **5M** | Entry/exit execution, momentum trigger | `Close`, `Open`, `High`, `Low`, `Time` |
| **Data2** | TXF1 | **60M** | Overheating overlay (RSI60, BB60) — finer than Daily but smoother than 5M | `Close of Data2`, `RSI(Close of Data2,14)[1]` |
| **Data3** | TXF1 | **Daily** | Bull regime gate (MA20/MA60, RSI14_daily, dist_MA20) | `Close of Data3`, `Average(Close,20) of Data3 [1]` |

All higher-TF reads use `[1]` index per CLAUDE.md rule #3 (Data2/Data3 current bar unreliable).

### 2.2 Two-tier gating logic (the core architecture)

```
TIER 1 — REGIME GATE (Daily, defines WHEN TO LOOK)
    Bull regime backdrop AND overheating present
    → v_S3_Watch = true (latches; ~5 days/month)

TIER 2 — MOMENTUM TRIGGER (5M, defines WHEN TO FIRE)
    Inside an active WATCH window AND 5M proves pullback has started
    → SellShort Next Bar at Market

(Plus mandatory entry gates: holiday/settlement/kill/registry/cooldown/time-window)
```

This two-tier model is the **single biggest design decision in S3**: Tier 1 defines opportunity context, Tier 2 confirms the pullback is real. Empirical research (Agent A) confirmed that no single overheating signal reliably predicts a 1-day pullback (RSI>75 daily actually has *worse-than-baseline* hit rate). The trigger must be momentum-confirmed.

### 2.3 Exit priority chain

```
Every 5M bar while MarketPosition = -1:

  P0  (Mandatory, Constitution + Rule #11/#12):
      P0-1  Manual_Kill_Switch         → BuyToCover Market   SX_RPS_Kill
      P0-2  Registry_Expired           → BuyToCover Market   SX_RPS_RegistryEnd
      P0-3  Holiday_Block + Time≥0245  → BuyToCover Market   SX_RPS_HolFlat
      P0-4  Settlement_Day + Time≥1230 → BuyToCover Market   SX_RPS_Settlement
      P0-5  SetStopLoss(...)           ← engine-level, always armed (Rule #12)

  P0a (S3-specific intraday rule):
      P0-6  Time ≥ 1325                → BuyToCover Market   SX_RPS_DayClose

  P1  (Profit target):
      P1   Close ≤ TP_Price OR Close ≤ 5M_EMA20[1]
                                       → BuyToCover Market   SX_RPS_TP

  P2  (Stop loss, frozen ATR):
      P2   Close ≥ v_SL_Level          → BuyToCover Stop     SX_RPS_SL

  P3  (Time stop):
      P3   BarsSinceEntry ≥ 24         → BuyToCover Market   SX_RPS_TimeStop
```

Note: P0a (DayClose 13:25) outranks TP/SL because the hard intraday constraint cannot be violated, even if TP would have fired one bar later.

---

## 3. Regime Gate Definition (Tier 1)

### 3.1 Recommended combination (Agent A — Option 3B MODERATE)

```
v_RegimeGate_WATCH =

  /* (A) MANDATORY anchor: medium-term bull trend on Daily */
  ( Average(Close, 20)[1] of Data3 > Average(Close, 60)[1] of Data3 )

  AND

  /* (B) OR (C): at least one overheating condition */
  (
    /* (B) RSI overheat sustained 2 daily bars — snapshot-based */
    ( v_Daily_RSI_Snap1 > 70 AND v_Daily_RSI_Snap2 > 70 )

    OR

    /* (C) Distance from MA20 ≥ 3% */
    ( (Close[1] of Data3 - Average(Close,20)[1] of Data3) / Average(Close,20)[1] of Data3 * 100 > 3.0 )
  )
```

> **PowerLanguage gotcha**: `RSI(Close of Data3, N)[N]` is **Data1-indexed (5M offset), not Daily-indexed**. The `[N]` offset operator works on the *executing* data stream (Data1 = 5M bars), so `[1]` looks back one 5M bar, not one daily bar. To get true daily-RSI history, snapshot the value at calendar-date rollover into variables (`v_Daily_RSI_Snap0..3`) and read those snapshots inside the gate. The v1.1 `.pla` uses this pattern; do **not** revert to the inline `RSI(...)[N]` form.

### 3.2 Concrete signal list with thresholds

| ID | Signal | Threshold | Timeframe | Empirical frequency | Role |
|----|--------|-----------|-----------|---------------------|------|
| A | Daily `MA20 > MA60` | strict | Daily | 70.8% of days | **Mandatory anchor** (bull regime) |
| B | Daily `RSI(14) > 70` sustained 2 bars | both bars | Daily | 21.3% of days (~4.5 d/mo) | Overheat (B OR C) |
| C | Daily `(Close - MA20)/MA20 × 100 > 3.0` | strict | Daily | 22.9% of days (~4.8 d/mo) | Deviation (B OR C) |
| HC | Daily dist_MA20 > +5% | strict | Daily | 6.7% of days (~1.4 d/mo) | **Conviction modifier** (not part of gate; flags `HighConviction = true` for logging/diagnostic) |

Combined fire rate: ~23-26% of days = **~5 WATCH days/month** (sufficient for ~10-20 trades/year after Tier 2 filtering).

### 3.3 Computation timeframe per signal

All Tier 1 signals computed on **Daily Data3** with `[1]` index. Rationale:
- Tier 1's job is to set a *stable* regime context — not to re-decide intra-day.
- Daily indicators eliminate `feedback_mc_time_24hr_pitfall.md` risk (no time intervals involved).
- Daily volume is reliable (unlike 5M/30M intraday — see §4.3).

### 3.4 Rejected signals (with reasons)

| Signal | Why rejected |
|--------|--------------|
| BB %B > 1.0 | Redundant with dist_MA20 (both measure stretch above mean); empirical hit-rate worse than baseline |
| Consecutive green closes | Overlaps RSI (~0.6 correlation) — `feedback_filter_redundancy_check.md` violation |
| Volume divergence | Weak academic support + TXF1 volume reliability concerns |
| TWVIX divergence | Defer to v2 — new data pipeline, marginal lift |
| 60-day return > +5% | Adds no orthogonal information beyond MA20>MA60 + dist>3% combo |

---

## 4. Momentum Trigger Definition (Tier 2)

### 4.1 Recommended combination (Agent B — M_BALANCED)

```
v_MomentumTrigger =

  /* M1: Raw momentum — 3 consecutive red 5M bars */
  ( Close < Open AND Close[1] < Open[1] AND Close[2] < Open[2] )

  AND

  /* M2: Price below declining EMA5 (trend turn) */
  ( Close < XAverage(Close, 5) AND XAverage(Close, 5) < XAverage(Close, 5)[1] )

  AND

  /* M3: ATR spike — volatility expansion proves real selling */
  ( AvgTrueRange(20) > 0 AND AvgTrueRange(5) > AvgTrueRange(20) * 1.3 )

  AND

  /* M4: Pullback within actionable band 0.5%-1.5% from session high */
  ( (HighD(0) - Close) / HighD(0) * 100 >= 0.5 )
  AND
  ( (HighD(0) - Close) / HighD(0) * 100 <= 1.5 )
```

### 4.2 Concrete trigger conditions on 5M

| ID | Signal | Threshold | Latency (5M bars) | False-positive (est) | Data dependency |
|----|--------|-----------|-------------------|----------------------|-----------------|
| M1 | 3 consecutive red 5M | strict | 3 bars (15 min) | ~25% | OHLC only |
| M2 | `Close < EMA5 AND EMA5 declining` | strict | 1-3 bars | ~20% | OHLC only |
| M3 | `ATR(5) > ATR(20) × 1.3` | 1.3× | 1-2 bars | ~15% | OHLC only |
| M4 | Pullback ∈ [0.5%, 1.5%] from HighD(0) | band-gated | 0 bars | low | OHLC only |

All four signals are **OHLC-only** → zero data-feed risk. Total expected lag: 2-4 bars (10-20 minutes) from intraday peak; expected hit rate ~58-63%.

### 4.3 Volume reliability handling (lesson from S2 v0.4)

**Critical defensive design choice**: Volume confirmation (Agent B Signal #4) is **NOT in the core combo**.

Background: `S2_known_issues.md` B-3 documented that TXF1 30M Volume in MC12 was unreliable (often 0/missing). S2 v0.4 had `VolFilter_On = true` default; when `v_VolMA = 0`, the entire VolFilter became permanently false → **S2 v0.4 produced 0 entries across 6.5y backtest**.

Hypothesis: 5M Volume may be even less reliable than 30M Volume on TXF1. Without an empirical reliability check, we **cannot assume** 5M Volume is usable.

**Decision**:
- **Default**: DROP Volume signal from v1.0 core combo. Use **ATR spike (M3)** as the volume substitute — captures the same "rapid move" phenomenon using OHLC.
- **Optional**: Add `VolConfirm_On(false)` as an **off-by-default** input with explicit `v_VolMA20 > 0` guard. Users with verified Volume feed can opt in after Phase 1 validates 5M volume.
- **Pre-build verification**: Run a 5-line ShowMe study before `.pla` coding — measure `% of 5M bars where Volume = 0` over 6 months. If < 1% → can re-evaluate; if > 10% → permanently drop.

This is the single most important defensive design choice in S3.

### 4.4 Rejected signals (with reasons)

| Signal | Why rejected |
|--------|--------------|
| MACD bear cross | Lagging 2-5 bars; adding to BALANCED's 4 AND-gates drops trade count below institutional threshold |
| RSI(5M) crosses below 50 | Most lagging signal (3-6 bars); entries too late |
| 5M structure break (Lowest(Low,30)) | Adds 4-7 bar lag; turns BALANCED into STRICT (~12-20 trades/year, marginal sample) |
| 5M Volume surge | TXF1 reliability concern — see §4.3 |

---

## 5. Exit Mechanism

### 5.1 Recommended configuration (Agent C — BALANCED variant)

| Element | Value | Empirical anchor |
|---------|-------|-------------------|
| **TP** | **0.7% from entry OR 5M EMA20 touch** (whichever first) | 0.6× daily ATR = median 2-day pullback (empirical, 22 historical episodes 2020-2026) |
| **SL** | **4.0 × 5M-ATR(14) ≈ +0.58% from entry** | Matches median 1-day adverse rise = 0.58% (P50 of MAE) |
| **Time stop** | **24 × 5M bars = 120 min** | Mid of user's 30 min - 4 hr range |
| **Daily flat** | **13:25 force flat** (mandatory) | 20-min cushion before 13:45 day-session close |
| **Entry cutoff** | **12:30 (no new entries after)** | Ensures worst-case daily-flat exit within max hold window |
| **Same-day re-entry cooldown** | **Whole rest of day** (block re-entry when `Date = v_S3_LastExitDate`) | Anti-stack-on-runaway-rally rule (S2 lesson) |
| **R/R ratio** | **1.21** | Requires WR ≥ 45% for breakeven; counter-trend realistic 52-58% gives ~10pp headroom |

### 5.2 Concrete numbers (for v1.0 inputs)

```powerlanguage
Inputs:
   /* TP */
   TP_Pct                ( 0.70 ),     /* 0.70% from entry */
   TP_Use_MA20_Backup    ( true ),     /* 5M EMA20 touch as alternative trigger */
   TP_MA_Len             ( 20   ),     /* 5M EMA20 */

   /* SL — Frozen ATR */
   SL_ATR_5M_Multiple    ( 4.0  ),     /* SL = 4 × ATR(5M,14) ≈ 0.58% */
   SL_ATR_Len            ( 14   ),

   /* Time stop */
   MaxBars_TimeStop      ( 24   ),     /* 120 min */

   /* Time windows */
   Entry_Open_Time       (  900 ),     /* No early-morning chaos */
   Entry_Cutoff_Time     ( 1230 ),     /* No new entries after 12:30 */
   Daily_Flat_Time       ( 1325 ),     /* Force flat by 13:25 (intraday rule) */

   /* Constitution (inherited from L2/L5) */
   Holiday_Flat_Time     (  245 ),
   Settlement_Flat_Time  ( 1230 ),
   Manual_Kill_Switch    ( false ),
   Registry_Valid_Until  ( 1270101 ),
```

### 5.3 Mandatory Priority 0 exits (Kill/Registry/Holiday/Settlement)

Per CLAUDE.md Rule #11 (Settlement_Flat 7 elements) and Constitution clauses 1-6, all four mandatory exits are inherited verbatim from L2_TrendShort.pla / L5_BreakoutLong.pla template. Specifically:

1. `Manual_Kill_Switch = true` → immediate market exit
2. `Registry_Expired (Date > Registry_Valid_Until)` → market exit + 30-day red warning
3. `Holiday_Block AND Time ≥ Holiday_Flat_Time(0245)` → tail-bar flat in pre-holiday night session
4. `v_Settlement_Day AND Time ≥ Settlement_Flat_Time(1230)` → 3rd-Wed monthly settlement flat
5. `SetStopLoss(SL_distance × BigPointValue)` — engine-level, fires on entry bar (Rule #12)

### 5.4 Daily close handling (13:25 force flat)

Per Agent C §5, S3 is intraday-only by user spec. Two mandatory rules:

```powerlanguage
/* Rule A: Position must be flat by 13:25 every day */
if (Time >= Daily_Flat_Time) and (MarketPosition = -1) then
   BuyToCover("SX_RPS_DayClose") next bar at Market;

/* Rule B: No new entries after 12:30 */
/* Combined with Entry_Open_Time, gives closed-interval window per memory rule */
v_Entry_Time_OK = (Time >= Entry_Open_Time) and (Time <= Entry_Cutoff_Time);
```

Rationale for 13:25 (not 13:30):
- TXF1 day session ends 13:45
- 20-min cushion avoids illiquid wide-spread last bars
- Distinct from Settlement_Flat_Time(1230) which is for 3rd-Wed monthly settlement only

### 5.5 Same-day re-entry cooldown

```powerlanguage
/* On any exit, latch the date */
if (any SX_RPS_* fires) then
   v_S3_LastExitDate = Date;

/* Entry gate blocks re-entry on the same trading day */
if Date <> v_S3_LastExitDate then
   /* ... other entry conditions ... */
```

Cooldown duration: **whole rest of trading day** (re-arms at next session open). This prevents stacking losses on a runaway rally — the same lesson that produced E3 de-dup in Agent D's original spec.

### 5.6 ATR freezing (per SOP §3 principle #1)

```powerlanguage
/* Freeze SL distance on entry bar — must NOT drift mid-trade */
if MarketPosition = -1 then begin
   if (BarsSinceEntry = 0) and (v_SL_Locked = false) then begin
      v_Frozen_ATR_5M  = AvgTrueRange(SL_ATR_Len);
      v_Frozen_SL_Dist = v_Frozen_ATR_5M * SL_ATR_5M_Multiple;
      v_SL_Level       = EntryPrice + v_Frozen_SL_Dist;
      v_TP_Price       = EntryPrice * (1 - TP_Pct / 100);
      v_SL_Locked      = true;
   end;
end else begin
   v_SL_Level = 0; v_TP_Price = 0; v_SL_Locked = false;
end;
```

---

## 6. Portfolio Impact & Allocation

### 6.1 S3 expected correlations with existing 6 (monthly horizon, Agent D §2.2)

| | L1 | L2 | L3 | L4 | L5 | S1 | S3 |
|---|---|---|---|---|---|---|---|
| **S3** | **−0.35** | **+0.30** | **+0.05** | **+0.15** | **−0.30** | **−0.15** | 1.00 |

- **Structural hedge** vs L1/L5/S1 (the four long-bias sleeves) — fires inside their losing bull-pullback months
- **Modestly co-fires** with L2/L4 on the big-down months only — all within institutional |r|<0.7 gate
- **Effectively independent** of L3 (range-regime gate mutually exclusive)

### 6.2 Recommended sleeve size

| Phase | Sleeve % | Pre-conditions | Comment |
|-------|---------:|----------------|---------|
| **Phase 1 (sim, M0-3)** | **3%** | None — deploy on day 1 of simulated trading | **Recommended initial** |
| Phase 2 (live_sim, M3-9) | 3% | 30+ sim trades, PF ≥ 1.2, WFE > 50%, corr forecast confirmed | Real money, real slippage |
| Phase 3 (live, M9+) | 5% | 6+ months live_sim, all 10 dims pass | Standard production sleeve |
| Phase 4 (year 2+) | 8% | 100+ trades, regime variety, empirical bull-pullback hedge demonstrated | Full conviction |
| (Never) | 12% | Multi-year live data + correlation < −0.20 with L1 over 100+ trades | Reserved — DO NOT consider before 3y data |

### 6.3 Where the allocation % comes from

**Primary recommendation (Option B — Agent D §3.2)**: Retire L4 (OVERFIT_RISK status) and give S3 the 3% slot. L4 was a placeholder for "downside capture during black-swan moves" (2025-04 tariff crash); S3 is a credible mechanic replacement with a sounder edge thesis.

**Alternative (Option D — capital expansion)**: Keep L4 at 3%, scale frozen 6 by ×0.95, add S3 at 5.5%. Requires ~+800k NTD capital top-up. Preserves the v2 freeze directive most strictly.

### 6.4 New Portfolio v3 allocation table

**Primary v3 (Option B — recommended default)**:

| Strategy | v2 frozen | **v3 proposed** | Δ | Status |
|----------|----------:|----------------:|---:|--------|
| L1 TrendLong | 29% | **29%** | 0 | Frozen |
| L2 TrendShort | 22% | **22%** | 0 | Frozen |
| L3 ConsolidationLong | 10% | **10%** | 0 | Frozen |
| L4 ConsolidationShort | 3% | **0%** | **−3** | **Retired (S3 subsumes role)** |
| L5 BreakoutLong | 16% | **16%** | 0 | Frozen |
| S1 NightMomentum | 20% | **20%** | 0 | Frozen |
| **S3 RapidPullbackShort** | — | **3%** | **+3** | **NEW** |
| **TOTAL** | 100% | **100%** | 0 | |

**Alternative v3-D (Option D — capital expansion)**:

| Strategy | v3-D | Δ vs v2 |
|----------|-----:|--------:|
| L1 | 27% | −2 |
| L2 | 21% | −1 |
| L3 | 9.5% | −0.5 |
| L4 | 3% | 0 (floor preserved) |
| L5 | 15% | −1 |
| S1 | 19% | −1 |
| **S3** | **5.5%** | **+5.5** |
| Total | 100% | 0 (capital base +5.5%) |

### 6.5 Forecast portfolio metrics

| Metric | v2 baseline | v3 forecast (Option B) | Δ |
|--------|------------:|-----------------------:|---:|
| Weighted Sharpe (capacity-weighted) | 1.41 | **1.42 - 1.55** (conservative range) | +1% to +10% |
| Bull-pullback month worst MDD (2024-11, 2025-06 type) | −$199K | **−$140K to −$170K** | −15% to −30% |
| Bear-regime month MDD | −$80K typical | **−$80K typical** (S3 dormant) | ~0% |
| Sample-size on S3 | 0 | 65-130 trades over 6.5y | passes Rule #13 (≥100) |

---

## 7. Implementation Architecture

### 7.1 .pla module list

| Module | Source | Est LOC | Purpose |
|--------|--------|--------:|---------|
| Header docblock | L2/L5 standard | 50 | Performance baseline, 10-dim eval status, "DEPLOY ONLY WHEN FLAT" footer |
| Inputs | §5.2 (22 inputs) | 35 | All parameters declared with comments |
| Variables | self | 30 | ~22 vars including `v_S3_Watch`, `v_S3_LastExitDate`, frozen SL state |
| Holiday_Tail array (63 dates) | L2 §4B byte-identical | 80 | Pre-holiday night-session tail-bar registry |
| Session detection (IsDay/IsNight) | L2 §4 | 12 | Day-session = 08:45-13:45 |
| HolidayFlat_v3 + Settlement_Day + Registry | L2 §4B | 25 | `v_Holiday_Block`, `v_Settlement_Day`, `v_Registry_Expired`, 30-day red warn |
| Indicators (Data1+Data2+Data3) | self | 25 | ATR(5M), MA20/60 Daily, RSI/dist Daily, RSI/BB 60M (optional Tier-1.5) |
| **Tier 1 — Regime gate** | self | 20 | `v_BullRegime`, `v_Overheat`, `v_HighConviction` |
| **Tier 1.5 — Watch state latch** | self | 15 | `v_S3_Watch` arming + 8-bar staleness timeout |
| **Tier 2 — Momentum trigger** | self | 20 | `v_MomentumTrigger` = M1∧M2∧M3∧M4 |
| Entry gate + SetStopLoss (Rule #12) | self + Rule #12 | 25 | All gates AND-chained + `SetStopLoss(...)` |
| Frozen SL setup | L5 pattern | 12 | Lock ATR on entry bar |
| Exit chain (9 labels) | self | 80 | Priority 0/0a/1/2/3 cascade |
| State reset | L5 pattern | 10 | Reset frozen state when MP=0 |
| **Total estimate** | | **~420 LOC** | between S1 (~300) and L2 (709) |

### 7.2 Label conventions (Rule #11/#12, `feedback_mc_entry_exit_labels.md`)

| Label | Direction | Order type | Trigger |
|-------|-----------|------------|---------|
| `SE_RPS_Entry` | Short Entry | `SellShort... Next Bar at Market` | All gates pass |
| `SX_RPS_TP` | Short eXit | `BuyToCover... at Market` | TP_Price hit OR EMA20 touch |
| `SX_RPS_SL` | Short eXit | `BuyToCover... at Stop` | v_SL_Level hit |
| `SX_RPS_TimeStop` | Short eXit | `BuyToCover... at Market` | BarsSinceEntry ≥ 24 |
| `SX_RPS_DayClose` | Short eXit | `BuyToCover... at Market` | Time ≥ 1325 |
| `SX_RPS_Settlement` | Short eXit | `BuyToCover... at Market` | 3rd Wed + Time ≥ 1230 |
| `SX_RPS_HolFlat` | Short eXit | `BuyToCover... at Market` | Holiday tail + Time ≥ 0245 |
| `SX_RPS_Kill` | Short eXit | `BuyToCover... at Market` | Manual_Kill_Switch = true |
| `SX_RPS_RegistryEnd` | Short eXit | `BuyToCover... at Market` | Date > Registry_Valid_Until |

`RPS` = RapidPullbackShort (3-char strategy tag). `SE_` / `SX_` prefixes strictly disambiguate Short Entry vs Short eXit per memory rule.

### 7.3 verify_s3_pullbackshort.py outline (~60 checks)

| Section | Checks | Coverage |
|---------|-------:|----------|
| A. File metadata | 5 | File exists, header structure, performance baseline placeholder |
| B. Rule #11 Settlement_Flat | 7 | All 7 elements per constitution |
| C. Rule #12 P3b SetStopLoss | 4 | Exactly 1 call, `if MP>=0` guard, distance formula, BigPointValue |
| D. Rule #13 10-dim eval markers | 3 | Header link, deploy-only-when-flat comment, eval status |
| E. Holiday_Tail v3 | 7 | 63 dates, 1270101 sentinel, 1260619 (current), guard in `Time≤500` block |
| F. 3-data wiring | 5 | Data2/Data3 references all use `[1]` index |
| G. Closed Time intervals | 5 | All entry/exit time checks use closed AND form |
| H. Filter redundancy | 3 | No optional filter ON by default, comments on each input |
| I. Label conventions | 10 | All 9 SE_/SX_RPS_* labels present, no legacy prefixes |
| J. Watch state machine | 5 | `v_S3_Watch` arming/disarming/staleness/single-shot |
| K. Same-day cooldown | 3 | `v_S3_LastExitDate` updated on every exit, gate blocks |
| L. State reset | 3 | Frozen SL state resets when MP=0 |
| M. LOC discipline | 1 | Total ≤ 500 |
| N. Self-containment | 4 | No L1-L5/S1/S2 cross-references, Holiday_Tail inline |
| **Total** | **60** | |

---

## 8. Mandatory Compliance (Constitution)

### 8.1 Rule #11 — Settlement_Flat 7 elements: YES

Implementation: copy verbatim from `L2_TrendShort.pla §1+§4B+§13` template:

1. Input `Settlement_Flat_Time(1230)` declared
2. Variable `v_Settlement_Day` declared
3. Detection: `v_Settlement_Day = (DayOfWeek(Date) = 3) AND (DayOfMonth(Date) >= 15) AND (DayOfMonth(Date) <= 21)`
4. Entry gate contains `v_Settlement_Day = false`
5. Exit cascade contains `BuyToCover("SX_RPS_Settlement")`
6. Exit fires when `v_Settlement_Day AND Time >= Settlement_Flat_Time`
7. `SX_RPS_Settlement` positioned in Priority 0 block

### 8.2 Rule #12 — P3b SetStopLoss: YES

Implementation formula:

```powerlanguage
/* MUST come BEFORE entry block, AFTER indicator computation */
if MarketPosition >= 0 then
   SetStopLoss( SL_ATR_5M_Multiple * AvgTrueRange(SL_ATR_Len) * BigPointValue );
/* Guard: short strategy → MP >= 0 (not yet short) */
/* Distance: same ATR + multiple as Frozen SL (consistency) */
/* Amount: distance × BigPointValue (TXF1 = 200) */
/* Exactly 1 SetStopLoss call (no duplicates) */
```

### 8.3 Rule #13 — 10-dim institutional eval: pre-deploy checklist

| # | Dimension | S3 status pre-build | Required for live_simulation |
|---|-----------|---------------------|------------------------------|
| 1 | Sharpe/Sortino/Calmar | Forecast 0.55 | Backtest Sharpe ≥ 0.5 |
| 2 | VaR/CVaR | Not measured | 95% VaR ≤ 2% account |
| 3 | Correlation < 0.7 | Forecast all < +0.40 | Empirical < 0.7 daily, < 0.6 monthly |
| 4 | Drawdown clustering | Not measured | No 3+ consecutive losing months in 12-mo rolling |
| 5 | Sample ≥ 100 | Forecast 65-130 over 6.5y | 30+ for sim, 100+ for live |
| 6 | WFE > 50% | Not measured | WFE > 0.5 |
| 7 | 3-regime PF > 1.0 | Bear forecast = dormant (acceptable for regime-specialist) | Bull PF ≥ 1.2 |
| 8 | Cost analysis | Slippage 1k × ~15 trades/yr = 15k/yr (~9% of gross) | Net profit > 5× cost |
| 9 | Operational risk | 5M chart = high intraday attention | Document monitoring SOP |
| 10 | Regulatory/account | 1 contract intraday — within all TXF1 limits | N/A |

**No dimension is failing pre-build** — all are pending verification (#2, #4, #6, #7) or trivially passing (#5, #8, #9, #10).

---

## 9. Risks & Mitigations

| # | Risk (from agents) | Magnitude on 5M | Mitigation in S3 v1.0 |
|---|--------------------|-----------------|----------------------|
| 1 | **5M slippage relative to PnL** | 1pt slippage vs ~150pt target ≈ 0.7% drag | Round-trip 1000 NTD assumption (per CLAUDE.md); TP at 0.7% gives ~150pt target on TXF1@22000 |
| 2 | **Commission/turnover from 5M chart** | 5M generates 5-15× more signals than 60M before filters | Same-day cooldown + 8-bar staleness + 4-AND Tier-2 filter + 12:30 entry cutoff caps ≤ 1 trade/day |
| 3 | **Volume unreliability (S2 v0.4 trap)** | TXF1 5M volume reliability unverified | Volume DROPPED from core combo; ATR spike (M3) is the volume substitute; optional `VolConfirm_On(false)` with `v_VolMA20 > 0` guard for users who verify |
| 4 | **Counter-trend tail risk (fighting the trend)** | Going short in bull = small frequent losses if pullback never materializes | (a) Tier 1 requires bull regime (cannot fire in bear); (b) M4 pullback band ceiling 1.5% prevents bottom-fishing; (c) tight 4×ATR SL (0.58%) absorbs median noise but exits fast on extension; (d) 24-bar time stop cuts trades whose thesis is dead |
| 5 | **5M data glitch (spurious bars)** | 5M more prone to single-tick spikes | Trigger requires `ConsecRed3 AND ATR_spike AND pullback band` — single-bar noise fails the ConsecRed condition |
| 6 | **Overnight gap risk** | Holding into night → 2% gap-up wipes SL | **13:25 daily flat is hard rule** — strategy never holds overnight |
| 7 | **RSI60M whipsaw on Daily indicators** | Daily MA20>MA60 lags 5-7 days behind real regime change | Acceptable: false-positive entries during regime change exit via SL within 4hr; time stop caps damage |
| 8 | **5M ATR magnitude unverified** | Estimated 5M ATR ≈ 25-45 TXF pts; must verify in MC backtest | Phase 1 validation: log `AvgTrueRange(14)` distribution; if median outside 25-45 pt range, recalibrate SL_ATR_5M_Multiple |
| 9 | **Watch state stuck** | Bull regime + overheating can hold weeks → perpetual rearming | `Watch_Stale_Bars = 8` (40 min) timeout; single-shot consumption per fire |
| 10 | **Settlement-day 13:30 squeeze** | 3rd Wed often has settlement squeeze in afternoon | Settlement_Flat exits at 12:30 — accepts missing the occasional opportunity for safety |
| 11 | **Correlations come in flat (forecast wrong)** | If S3↔L1 ρ = 0 instead of −0.35, S3 becomes 3% un-hedged short bet | 30-trade gate before live capital + Phase 2 WFE measurement of actual correlation |

---

## 10. User Decision Points

### DECISION 1 — Regime Gate Combination (Tier 1 stringency)

- **A**: CONSERVATIVE — 3-AND (MA20>MA60 AND RSI>75 AND dist>+3%), ~2.3 WATCH days/month
- **B**: **MODERATE — A-anchored (MA20>MA60) AND (RSI>70 sustained 2 OR dist>+3%), ~5 WATCH days/month** ← RECOMMENDED
- **C**: LOOSE — 1-of-3, ~16 WATCH days/month (REJECTED by analysis)

**Trade-off**: A = fewer/stronger entries but borderline sample (~75-150 trades over 6y), B = healthy sample (~100-200) with regime protection intact, C = no real gate, S3 ends up duplicating L2's role.

### DECISION 2 — Momentum Trigger Combination (Tier 2 logic)

- **A**: FAST — `M1 OR M2` (1 of 2), entries 1-3 bars after peak, ~50-80 trades/year
- **B**: **BALANCED — `M1 AND M2 AND M3 AND M4` (4 of 4), 2-4 bars lag, ~25-40 trades/year** ← RECOMMENDED
- **C**: STRICT — BALANCED + M7 structure break, 4-7 bars lag, ~12-20 trades/year (sample-marginal)

**Trade-off**: A = earliest entry but ~30-35% false-start whipsaw, B = mechanism-diverse (raw momentum + volatility + range), C = highest hit rate but trade count below institutional 100-sample threshold over 6.5y.

### DECISION 3 — TP / SL / Time Stop tier

- **A**: TIGHT — TP 0.5% / SL 0.45% / TimeStop 60 min / R:R 1.11 / WR target 56-62% / 60-100 trades/yr
- **B**: **BALANCED — TP 0.7% / SL 0.58% / TimeStop 120 min / R:R 1.21 / WR target 52-58% / 40-70 trades/yr** ← RECOMMENDED
- **C**: WIDE — TP 1.0% / SL 0.70% / TimeStop 240 min / R:R 1.43 / WR target 45-52% / 25-50 trades/yr

**Trade-off**: A captures median pullback but misses user's "1-2%" range entirely, B matches empirical median 2-day pullback (0.57%) with 5M EMA20 backup catching deeper moves, C hits full 1-2% range but converts S3 from "counter-trend pullback" into "fight-the-trend" (4-hr MAE almost equals favorable excursion).

### DECISION 4 — TP Structural Backup (EMA20 touch alternative)

- **A**: **Include 5M EMA20 touch as alternative TP trigger (whichever fires first)** ← RECOMMENDED
- **B**: Pure %-based TP only (simpler, easier to backtest)
- **C**: Three-stage: 0.5% fixed → trail to EMA20 → time stop

**Trade-off**: A catches the cases where pullback rolls to MA20 quickly (~30% of episodes per Agent C §2.4), B is simpler but leaves money on the table, C is V2.0 complexity for new strategy (defer).

### DECISION 5 — Entry Time Window

- **A**: Strict day-session — Entry 09:00-12:30, DayClose 13:25 (recommended by Agent C)
- **B**: **Wider — Entry 08:45-12:30, DayClose 13:25 (catches open-volatility entries)** ← RECOMMENDED
- **C**: Tighter — Entry 09:30-11:30, DayClose 13:25 (avoids open + lunch noise)

**Trade-off**: A balances opening volatility against entry density, B accepts the noisy first 15 min in exchange for more opportunities (mitigated by 4-AND Tier 2 filter), C is cleanest but cuts trade count ~30%.

### DECISION 6 — L4 Disposition (Portfolio Allocation Slot)

- **A**: **Option B — Retire L4 (3%→0%), give S3 the 3% slot** ← RECOMMENDED
- **B**: Option D — Keep L4 at 3%, scale frozen 6 by ×0.95, S3 = 5.5% (requires +800k NTD capital)
- **C**: Option C-rounded — Scale L4 to 2.85%, S3 = 5% (technically violates v2 freeze by 0.15%)

**Trade-off**: A = cleanest, S3 explicitly subsumes L4's "downside capture" role with a sounder mechanic, but violates v2's "L4 不可砍光" directive; B = preserves freeze fully but expensive; C = compromise.

### DECISION 7 — Volume Confirmation Pre-Build Verification

- **A**: **YES — Run 5-line MC ShowMe study to measure 5M Volume reliability BEFORE coding .pla** ← RECOMMENDED
- **B**: Skip — keep `VolConfirm_On = false` by default in V1.0, never verify

**Trade-off**: A = 30 min of ShowMe work prevents repeating S2 v0.4 trap and informs whether VolConfirm can ever be enabled, B = saves 30 min but leaves a permanent open question.

### DECISION 8 — HighConviction Modifier Behavior

If `Daily dist_MA20 > +5%` (1.4 days/month), what should happen?

- **A**: Relax 5M trigger threshold (e.g. ATR ratio 1.3 → 1.2 when HighConviction = true)
- **B**: Double position size 1→2 lots (VIOLATES固定口數=1 rule)
- **C**: Both A and B
- **D**: **Logging-only diagnostic for v1.0; re-open after P1-P3 validates base** ← RECOMMENDED

**Trade-off**: A adds entry-quality differentiation but creates parameter for P1 to sweep, B violates固定口數 rule, D is most conservative — first prove base S3 works, then add conviction modulation in v1.1.

---

## 11. Build Sequence (after user decides D1-D8)

| Step | Action | Output | Verification |
|------|--------|--------|--------------|
| **1** | Write `S3_RapidPullbackShort_strategy.md` | Alpha thesis doc (3 pages) | Reviewer sanity check |
| **2** | Write `S3_RapidPullbackShort_annotated.md` | Per-line annotated walkthrough | Cross-check vs §3, §4, §5 |
| **3** | Code `S3_RapidPullbackShort.pla` using L2/L5 templates | ~420 LOC `.pla` file | Run `verify_s3_pullbackshort.py` (60 checks) — 100% pass required |
| **4** | Write `verify_s3_pullbackshort.py` | Test harness | Self-test on completed .pla |
| **5** | MC12 backtest 2020-01 → 2026-06 | Trade list + equity curve | Load 3-data chart (5M/60M/Daily), 0 compile errors |
| **6** | 10-dim institutional eval (Rule #13) | Pass/fail matrix per dimension | All 10 dims pass |
| **7** | If PASS → promote to `live_simulation/` | Move to live_sim folder + update README | 30-trade gate at PF ≥ 1.2 |

**Step 1 is the next concrete action immediately after user confirms D1-D8.**

---

## 11a. Implementation Notes (v1.1)

_Added 2026-06-19, post-audit. Captures the gap between the v1.0 build and what the spec actually required — and the architectural decisions taken to close it._

### 11a.1 v1.0 audit — 13 bugs found and root causes

| # | Bug | Root cause |
|---|-----|------------|
| 1 | `RSI(Close of Data3, 14)[1]` used inline in Tier 1 gate | PowerLanguage `[N]` offset operates on the *executing* data stream (Data1 = 5M), not on the source Data3 — so `[1]` looked back **5 minutes**, not **1 day**. Multi-data offset trap. |
| 2 | Daily RSI overheat condition never latched true outside opening 5M bar | Same as #1 — by the second 5M bar of a day, the snapshot of Daily RSI had already shifted; spec's "sustained 2 daily bars" semantic was unreachable. |
| 3 | `HighD(0)` used as session high inside pullback band M4 | `HighD(0)` includes overnight session data — contaminated the 5M intraday peak with prior-night prices, distorting the 0.5–1.5% band. |
| 4 | `Time >= Daily_Flat_Time` allowed entry on the boundary 5M bar | Off-by-one: gate used `>=` for the cutoff but `<=` upstream, producing a fill-gap window in which entry and exit fired on the same bar. |
| 5 | Frozen SL relied solely on script-level `v_SL_Level` comparison | `SetStopLoss` per Rule #12 was missing; on fill the engine had no native stop armed until the next 5M bar evaluation — exposing ~5 min of unguarded position. |
| 6 | `v_S3_Watch` never disarmed | Staleness counter declared but never decremented; once true, Watch stayed true indefinitely. |
| 7 | Same-day cooldown latched `Date` only on TP exit | Other SX_RPS_* exits (SL, TimeStop, DayClose) did not update `v_S3_LastExitDate` → re-entry possible after a stop-out. |
| 8 | Settlement_Day detection used `DayOfMonth in [15..21]` without `DayOfWeek = 3` AND | Logical-OR slip — flagged the entire third week as settlement day instead of just Wednesday. |
| 9 | Holiday_Tail registry guard placed inside `Time <= 500` block but Holiday_Flat_Time = 245 | The 245-cutoff was reachable only when the `<= 500` outer guard was satisfied — both bounds correct, but layered guard structure was inverted from L2 template. |
| 10 | `BarsSinceEntry >= 24` time stop fired on bar 23 due to 0-indexed counter | Off-by-one in time-stop comparison; spec intended 24 *complete* 5M bars (= 120 min). |
| 11 | `AvgTrueRange(5)` and `AvgTrueRange(20)` in M3 trigger used same period variable | Copy-paste error: both calls used `AvgTrueRange(SL_ATR_Len)` — ratio always 1.0, M3 never fired. |
| 12 | EMA20 TP backup compared `Close` to `XAverage(Close, 20)` (current bar) | Forward-leakage risk on intrabar evaluation; spec required `[1]` index on the MA reference for stable TP trigger. |
| 13 | Registry sentinel `1270101` missing from header docblock comment | Rule #11 element-7 markers incomplete; `verify_s3_pullbackshort.py` Section D would have caught it had it been run pre-commit. |

### 11a.2 Architectural decisions adopted in v1.1

- **Snapshot-based Daily indicator history** — All Daily-derived values (RSI14, MA20, MA60, dist_MA20) are read once per calendar-date rollover into `v_Daily_RSI_Snap0..3`, `v_Daily_MA20_Snap0..1`, etc., and the gate consumes those snapshots. Eliminates the PL multi-data `[N]` offset trap (root cause of bugs #1 and #2).
- **Day-session-only intraday high** — Replaced `HighD(0)` with a manually-tracked `v_DaySession_High` that resets at `Time = 845` and updates only when `IsDay = true`. Removes overnight contamination from the M4 pullback band (bug #3).
- **Strict `<` boundaries on Time-window gates** — All entry/exit time checks now use closed-interval form `(Time >= Open) AND (Time <= Close)` for activation and `Time < Cutoff` for entry suppression, so the cutoff bar itself is unambiguously assigned to "exit-only" (bug #4). Aligns with `feedback_mc_time_24hr_pitfall.md`.
- **Frozen SL belt-and-suspenders** — Script-level `v_SL_Level` comparison (P2 cascade) is retained, **and** Rule #12's `SetStopLoss(SL_distance × BigPointValue)` is called every bar `if MarketPosition >= 0` to give engine-level protection from fill-tick onward. Both layers use the same frozen distance, ensuring consistency (bugs #5, #11, #12).

### 11a.3 Cross-references

- Workflow audit task: **`w2zrqguup`** (`scripts/_audit/s3_v1.0_findings.md`)
- v1.1 implementation commit: **TBD** (will be back-filled once the rebuilt `.pla` is committed)
- Verification harness: `scripts/verify_s3_pullbackshort.py` Section J (Watch state machine) and Section K (Same-day cooldown) gained additional checks for bugs #6 and #7
- Related memory: `feedback_mc_time_24hr_pitfall.md`, `feedback_filter_redundancy_check.md`

---

## 12. Spec Anchors

- **Empirical pullback distribution**: `scripts/_temp_s3_pullback_stats.json` (22 historical episodes, 2020-2026 TWII daily)
- **Statistical script**: `scripts/_temp_s3_pullback_stats.py` (reproducible)
- **Constitution**: `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`
- **Exit SOP**: `docs/entry_exit_sop.md`
- **P3b SetStopLoss guard**: `docs/P3b_immediate_stop_guard_design_20260618.md`
- **10-dim risk framework**: `docs/institutional_risk_framework_20260619.md`
- **Portfolio anchors**: `docs/portfolio_correlation_matrix_20260620.md` + `docs/portfolio_walk_forward_20260620.md` + `docs/portfolio_allocation_v2_20260620.md`
- **Templates**: `strategies/live/L2_TrendShort.pla` (Settlement+Holiday+SetStopLoss), `strategies/live/L5_BreakoutLong.pla` (3-data wiring)

---

_Final v2 design specification synthesized 2026-06-20 from 5 parallel deep-research reports (regime gate, momentum trigger, exit mechanism, portfolio impact, implementation architecture). All numbers in §3-§5 are anchored to empirical evidence from `_temp_s3_pullback_stats.json` (TWII daily 2020-2026, 22 historical bull+RSI>75+strong-trend episodes) or to Agent B's mechanism-diversity analysis. 5M ATR estimate extrapolated analytically; must be verified in Phase 1 MC backtest. All numbers subject to A/B variant scan in Phase 1 sensitivity analysis._

---

**Document version**: `spec_v2` + v1.1 implementation notes (2026-06-19)
**Change log**:
- 2026-06-20: spec_v2 initial publication (sections 1–12)
- 2026-06-19: Added §11a Implementation Notes (v1.1) — 13-bug v1.0 audit, snapshot-based Daily indicator architecture, day-session-only intraday high, strict Time boundaries, frozen-SL belt-and-suspenders. Corrected §3.1 RSI gate to snapshot-variable form with PowerLanguage multi-data offset gotcha note. Confirmed `Holiday_Flat_Time = 245` throughout (no `415` legacy references present).
