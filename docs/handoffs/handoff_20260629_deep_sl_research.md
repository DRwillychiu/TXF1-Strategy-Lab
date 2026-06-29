# Handoff — 2026-06-29 Deep SL Research Session

## 1. Status

- **Session type**: Laptop deep research (no backtest execution)
- **Primary deliverable**: Extreme market multi-layer SL SOP + v1.8+ architecture direction
- **v1.7.5 .pla**: Created and pushed (conditional cap — superseded by v1.8+ direction)
- **Engineering System**: Rule #16 created and enforced

## 2. What Changed

### New files (4)
| File | Purpose |
|------|---------|
| `docs/methodology/ENGINEERING_SYSTEM.md` | Rule #16 five-pillar framework |
| `docs/methodology/extreme_sl_multilayer_sop_20260629.md` | Extreme market multi-layer SL SOP (permanent methodology) |
| `strategies/research/S03_VolSqueezeShort/v175_ConditionalCap_spec.md` | v1.7.5 conditional cap spec (superseded) |
| `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v175_EXPERIMENTAL.pla` | v1.7.5 .pla (superseded by v1.8+ direction) |

### Modified files (2)
| File | Change |
|------|--------|
| `CLAUDE.md` | Added Rule #16 (Engineering System 5-pillar) |
| `docs/README.md` | Added ENGINEERING_SYSTEM.md + extreme SL SOP to methodology index |

### Git log (today's commits)
```
820c873 Add extreme market multi-layer SL SOP (Fine Dining architecture)
c862664 S3_S v1.7.5 EXPERIMENTAL .pla: Conditional Hard Cap (fix v1.7.4 SP destruction)
0012ff4 S3_S v1.7.5 Conditional Cap spec: deep SL design with Rule #16 checklist
e76f0bf Rule #16: Engineering System — five-pillar framework
```

## 3. Current State

### v1.7.5 status: SUPERSEDED
- v1.7.5 conditional cap (.pla + spec) technically correct but user redirected direction
- User 2026-06-29 ruling: fixed-point caps (100 pts, 15 pts) are design contradiction in vol-adaptive architecture
- v1.7.5 files preserved as reference, not promoted

### v1.8+ direction: CONFIRMED
- Architecture upgrade from single-TF (60M only) to multi-TF (60M + 1M)
- ATR SetStopLoss demoted to Layer E safety net (last resort)
- 1M multi-factor scoring system becomes active defense (Layers A-D)
- Implementation target: Scenario 1 (real extreme move, multi-category confluence exit)

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
1. **v1.8.0 spec document**: Formal spec for 1M multi-factor preemptive exit
   - Define exact parameters for each of 11 factors (N values, thresholds, lookbacks)
   - Define scoring weights and trigger threshold
   - IOG architecture design for MC12
   - Data2 = 1M setup requirements
2. **Scenario 1 detailed walkthrough**: Map Scenario 1 to exact MC12 PowerLanguage logic
3. **Backtest feasibility**: Assess 1M data availability depth and backtest speed impact

### Dependencies
- MC12 1M data feed for TXF1 (verify availability and history depth)
- IOG testing on simple cases before full implementation
- May need v1.7.3-FINAL as baseline comparison (production unchanged)

### Risk
- 1M backtest ~60x slower (each 60M bar = 60 evaluations)
- 1M data history may be shorter than 60M (limiting backtest period)
- IOG changes all order execution timing, needs careful testing

## 6. Files Reference

### Production (unchanged)
- `strategies/live_simulation/S3_S_VolSqueezeShort.pla` — v1.7.3-FINAL (29 trades, PF 3.95)

### Research (today)
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
