# Handoff — 2026-06-29 Deep SL Research Session

## 1. Status

- **Session type**: Laptop deep research + implementation + backtest analysis
- **Primary deliverable**: Extreme market multi-layer SL SOP + v1.8.0 .pla implementation
- **v1.8.0 .pla**: Created — 1M multi-layer exit monitoring (IOG + Data3 + 11-factor scoring)
- **v1.8.0 backtest**: COMPLETED on Laptop MC12 — **CRITICAL: SX_VS_1M_Exit = 0 triggers**
- **v1.7.5 .pla**: Created and pushed (conditional cap — superseded by v1.8.0)
- **Engineering System**: Rule #16 created and enforced
- **CLAUDE.md**: Rule #17 added (extreme SL SOP mandatory)

## 2. What Changed

### New files (6)
| File | Purpose |
|------|---------|
| `docs/methodology/ENGINEERING_SYSTEM.md` | Rule #16 five-pillar framework |
| `docs/methodology/extreme_sl_multilayer_sop_20260629.md` | Extreme market multi-layer SL SOP (permanent methodology) |
| `strategies/research/S03_VolSqueezeShort/v175_ConditionalCap_spec.md` | v1.7.5 conditional cap spec (superseded) |
| `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v175_EXPERIMENTAL.pla` | v1.7.5 .pla (superseded by v1.8.0) |
| `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v180_EXPERIMENTAL.pla` | v1.8.0 .pla (1M multi-layer exit, 1043 lines) |
| `strategies/research/S03_VolSqueezeShort/v180_MultiLayer1M_spec.md` | v1.8.0 spec document |

### Modified files (3)
| File | Change |
|------|--------|
| `CLAUDE.md` | Added Rule #16 (Engineering System) + Rule #17 (extreme SL SOP mandatory) |
| `docs/README.md` | Added ENGINEERING_SYSTEM.md + extreme SL SOP to methodology index |
| `docs/handoffs/handoff_20260629_deep_sl_research.md` | Updated with v1.8.0 implementation |

### Git log (today's commits)
```
bf96e5a Rule #17: extreme market multi-layer SL SOP mandatory for all volatile strategies
feab813 Update SOP Section 3 with user-approved building metaphor floor descriptions
820c873 Add extreme market multi-layer SL SOP (Fine Dining architecture)
c862664 S3_S v1.7.5 EXPERIMENTAL .pla: Conditional Hard Cap (fix v1.7.4 SP destruction)
0012ff4 S3_S v1.7.5 Conditional Cap spec: deep SL design with Rule #16 checklist
e76f0bf Rule #16: Engineering System — five-pillar framework
(+ v1.8.0 commit pending)
```

## 3. Current State

### v1.7.5 status: SUPERSEDED
- v1.7.5 conditional cap (.pla + spec) technically correct but user redirected direction
- User 2026-06-29 ruling: fixed-point caps (100 pts, 15 pts) are design contradiction in vol-adaptive architecture
- v1.7.5 files preserved as reference, not promoted

### v1.8.0: IMPLEMENTED + BACKTESTED (Laptop MC12)
- Architecture upgrade from single-TF (60M only) to multi-TF (60M + Daily + 1M)
- ATR SetStopLoss demoted to Layer E safety net (last resort)
- 1M 11-factor scoring system becomes active defense (5 floors, 3-gate trigger)
- IOG=True, Data3=1M, entry/mid/time gated to BarStatus(1)=2
- IntraBarPersist on SP/SL state variables for IOG compatibility
- New exit label: SX_VS_1M_Exit (priority S-0, between P0 safety and S-1 TP)

### v1.8.0 Backtest Results (Laptop MC12, 2021/1/28 - 2026/5/26)

#### CRITICAL: SX_VS_1M_Exit = 0 triggers (the 1M monitoring never fired)

| Metric | v1.7.3-FINAL (baseline) | v1.8.0 | Delta |
|--------|------------------------|--------|-------|
| Period | 2020-2026 (6.3y) | 2021/1-2026/5 (~5.3y) | -1y (Data3 depth) |
| Trades | 29 | 15 | -14 (-48%) |
| Net Profit | +1,013,600 | +481,400 | -532,200 (-52%) |
| Profit Factor | 3.95 | 4.88 | +0.93 |
| Max DD | -22.1% | -10.76% | +11.34% (improved) |
| Win Rate | ~72% | 86.67% | +15% |
| Sortino | 1.08 | 0.686 | -0.39 |

#### Exit Signal Distribution (v1.8.0)
| Signal | Count | P/L Sum | Note |
|--------|-------|---------|------|
| SX_VS_SP | 11 (73%) | +262,600 | Trailing stop |
| SX_VS_TP | 2 (13%) | +343,000 | Target profit |
| SX_VS_SL | 2 (13%) | -124,200 | Initial stop loss |
| **SX_VS_1M_Exit** | **0 (0%)** | **0** | **NEVER TRIGGERED** |

#### 2 SL Trades (1M exit should have intercepted)
| # | Date | Entry | Exit | P/L | MAE | Note |
|---|------|-------|------|-----|-----|------|
| 1 | 2021/1/28 | 15264 | 15520 | -53,200 | -52,200 | First trade in backtest |
| 13 | 2025/3/31 | 20818 | 21163 | -71,000 | -70,000 | 345 pts adverse, 1M should have fired |

#### Diagnosis: Two Independent Issues

**Issue 1 — SX_VS_1M_Exit = dead code (3-gate thresholds too strict)**
- ML_ScoreTrigger=65% requires 20/30 pts = 6-7 factors simultaneously
- ML_SpeedThreshPts=80 pts in 5 bars = extreme (16 pts/min)
- ML_VolSpikeMult=2.5 = requires 2.5x average volume
- Trade #13 had 345 pts adverse move yet scored below threshold

**Issue 2 — Trade count 15 vs expected ~24 (after period adjustment)**
- ~5 trades lost from shorter data period (5.3y vs 6.3y)
- ~9 trades unaccounted for — possible IOG + BarStatus(1)=2 entry gate issue
- Need control test: v1.7.3-FINAL on same 2021/1-2026/5 period

#### Backtest Settings Confirmed
```
Parameters: (45, 2.0, 120, 25, 14, 2.75, 3.5, 35, true, 2, 1.5, 70, 1, true, 15, 40,
  true, true, 415, 1270101, false, 1230, 40, 65, 3, 2.5, 20, 5, 80, 5, 60, 2.0)
Capital: 1,000,000 | Slippage: 1,000 NTD/contract | Look-Inside-Bar: disabled
```

### SL design philosophy: LOCKED
- Saved as permanent SOP: `docs/methodology/extreme_sl_multilayer_sop_20260629.md`
- Saved in Claude memory: `feedback_sl_fine_dining_philosophy.md`
- Core: multi-layer fine dining, ATR is last line, 1M is active defense
- Anti-false-signal: 3-gate design (activation threshold + score + cross-category)

## 4. Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| v1.7.5 conditional cap superseded | Fixed-point cap contradicts vol-adaptive design philosophy |
| Real problem = execution risk, not SL distance | Extreme vol cascade slippage, not ATR calculation |
| 1M multi-factor scoring system | 18 factors cataloged, 11 low-noise selected (all High reliability + Low noise) |
| All 11 factors included | Already filtered set; removing any weakens coverage without reducing noise |
| 3-gate anti-false-signal | Activation (loss > 40% SL) + Score (>= 65%) + Cross-category (>= 3 categories) |
| Scenario 1 as implementation target | Real extreme move: 8 factors fire, 73% score, 5 categories, correct exit |

## 5. Next Steps (Desktop session)

### Step 1 — Control Test (HIGHEST PRIORITY)
Run v1.7.3-FINAL on same period (2021/1/28-2026/5/26) to establish fair baseline:
- How many trades does v1.7.3 produce in this exact period?
- If v1.7.3 also shows ~15 trades, the trade count drop is from data period, not IOG
- If v1.7.3 shows ~24+, then IOG + BarStatus gate is killing entries

### Step 2 — Diagnose 1M Scoring (add Commentary/Print)
Add `Print` statements in Section 9.5 to output per-bar diagnostic:
- v_1M_Score, v_1M_Score_Pct, v_1M_CatCount, v_1M_Gate1/2/3
- Individual factor scores (v_Score_A1, A2, A4, A6, B1, B2, C1, C2, D2, D3, E3)
- This reveals whether factors are scoring but not reaching threshold, or not scoring at all

### Step 3 — Lower Thresholds and Retest
If Step 2 confirms factors are scoring low:
- ML_ScoreTrigger: 65 -> 45 (14/30 pts = ~4-5 factors)
- ML_SpeedThreshPts: 80 -> 40 (8 pts/min, more realistic)
- ML_VolSpikeMult: 2.5 -> 1.8 (less extreme volume requirement)
- ML_ActivationPct: 40 -> 30 (activate earlier)

### Step 4 — Parameter Sweep (if Step 3 shows promise)
GA optimization on ML_ inputs with constraints:
- ML_ActivationPct (25-50), ML_ScoreTrigger (35-65), ML_SpeedThreshPts (30-80)

### Dependencies
- MC12 Desktop with 1M data feed for TXF1
- MaxBarsBack setting must cover 1M lookback (min 60 bars)

### Risk
- 1M backtest ~60x slower (each 60M bar = 60 evaluations)
- Over-lowering thresholds may cause false positive exits on winning trades
- Need to monitor: SX_VS_1M_Exit count AND whether it cuts winners or only losers

## 6. Files Reference

### Production (unchanged)
- `strategies/live_simulation/S3_S_VolSqueezeShort.pla` — v1.7.3-FINAL (29 trades, PF 3.95)

### Research (today)
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v180_EXPERIMENTAL.pla` — v1.8.0 (1M multi-layer, 1043 lines)
- `strategies/research/S03_VolSqueezeShort/v180_MultiLayer1M_spec.md` — v1.8.0 spec
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v175_EXPERIMENTAL.pla` — superseded
- `strategies/research/S03_VolSqueezeShort/v175_ConditionalCap_spec.md` — superseded

### Methodology (permanent)
- `docs/methodology/extreme_sl_multilayer_sop_20260629.md` — active SOP
- `docs/methodology/ENGINEERING_SYSTEM.md` — Rule #16

## 7. v1.8.0 All 15 Trades (Laptop Backtest Reference)

| # | Date | Entry | Exit Signal | P/L (NTD) | MAE (NTD) |
|---|------|-------|-------------|-----------|-----------|
| 1 | 2021/1/28 | 15264 | SX_VS_SL | -53,200 | -52,200 |
| 2 | 2022/5/9 | 16077 | SX_VS_SP | +17,000 | -6,600 |
| 3 | 2022/6/30 | 14669 | SX_VS_SP | +19,400 | -6,400 |
| 4 | 2022/7/1 | 14380 | SX_VS_SP | +21,600 | -5,600 |
| 5 | 2022/9/23 | 14007 | SX_VS_SP | +11,400 | -10,600 |
| 6 | 2022/9/26 | 13841 | SX_VS_SP | +12,000 | -11,000 |
| 7 | 2022/10/11 | 13177 | SX_VS_SP | +16,800 | -11,200 |
| 8 | 2022/11/28 | 14495 | SX_VS_SP | +3,000 | -21,200 |
| 9 | 2024/8/5 | 19393 | SX_VS_SP | +78,200 | -75,600 |
| 10 | 2025/3/27 | 22031 | SX_VS_SP | +15,600 | -5,200 |
| 11 | 2025/3/28 | 21575 | SX_VS_TP | +64,200 | -15,000 |
| 12 | 2025/3/31 | 20914 | SX_VS_SP | +24,600 | -17,600 |
| 13 | 2025/3/31 | 20818 | SX_VS_SL | -71,000 | -70,000 |
| 14 | 2025/4/7 | 19167 | SX_VS_TP | +278,800 | -1,000 |
| 15 | 2026/1/30 | 31912 | SX_VS_SP | +43,000 | -79,800 |

## 8. Git State

- Branch: `main`
- HEAD: updated after backtest analysis commit
- Working tree: clean
- Remote: synced (push after this update)
