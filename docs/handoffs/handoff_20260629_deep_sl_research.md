# Handoff — 2026-06-29 Deep SL Research Session

## 1. Status

- **Session type**: Laptop deep research + implementation
- **Primary deliverable**: Extreme market multi-layer SL SOP + v1.8.0 .pla implementation
- **v1.8.0 .pla**: Created — 1M multi-layer exit monitoring (IOG + Data3 + 11-factor scoring)
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

### v1.8.0: IMPLEMENTED
- Architecture upgrade from single-TF (60M only) to multi-TF (60M + Daily + 1M)
- ATR SetStopLoss demoted to Layer E safety net (last resort)
- 1M 11-factor scoring system becomes active defense (5 floors, 3-gate trigger)
- IOG=True, Data3=1M, entry/mid/time gated to BarStatus(1)=2
- IntraBarPersist on SP/SL state variables for IOG compatibility
- New exit label: SX_VS_1M_Exit (priority S-0, between P0 safety and S-1 TP)

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

## 5. Next Steps

### Immediate (next session)
1. **v1.8.0 backtest on Desktop MC12**: Load .pla with Data1=60M + Data2=Daily + Data3=1M
   - Verify 1M data availability and history depth for TXF1
   - Run baseline comparison: v1.7.3-FINAL vs v1.8.0 (same period)
   - Check for false positive SX_VS_1M_Exit exits
2. **Parameter optimization**: If baseline looks clean, GA on ML_ inputs
   - ML_ActivationPct (40-60), ML_ScoreTrigger (55-75), ML_SpeedThreshPts (60-120)
3. **IOG edge case testing**: Verify entry gating works correctly at bar boundaries

### Dependencies
- MC12 Desktop with 1M data feed for TXF1 (verify availability and history depth)
- MaxBarsBack setting must cover 1M lookback (min 60 bars)

### Risk
- 1M backtest ~60x slower (each 60M bar = 60 evaluations)
- 1M data history may be shorter than 60M (limiting backtest period)
- False positive 1M exits could reduce net profit (monitor SX_VS_1M_Exit count/PnL)

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

## 7. Git State

- Branch: `main`
- HEAD: `820c873`
- Working tree: clean (after this handoff commit)
- Remote: synced
