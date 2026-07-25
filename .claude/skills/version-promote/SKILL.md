---
name: version-promote
description: Live strategy version upgrade workflow. Archive old version to research, deploy new version to live, update defaults. Ensures every past version is recoverable.
---

# Version Promote SKILL

## When to use

When upgrading a live strategy (L1-L5) from version Vx to Vy, or rolling back
to a prior version. This workflow ensures the old version is archived in
research/ and always recoverable.

## Directory convention

```
strategies/
  live/
    L1_TrendLong.pla              <-- always the CURRENT production version
  research/
    L1_v30/                       <-- archived V3.0
      L1_TrendLong_v30.pla
    L1_v31/                       <-- archived V3.1 (also the source for current live)
      L1_TrendLong_v31.pla
      L1_V32_X4_FINAL_VERDICT.md  <-- killed experiment docs stay with their base version
```

Naming: `L{N}_v{MAJOR}{MINOR}/L{N}_TrendLong_v{MAJOR}{MINOR}.pla`
- Major = breaking change or new feature (V3.0 -> V3.1)
- Minor omit if 0 (v30, v31, v291)

## Promote checklist (mandatory steps in order)

### Step 1: Archive current live version

```bash
mkdir strategies/research/L{N}_v{OLD}/
cp strategies/live/L{N}_{Name}.pla strategies/research/L{N}_v{OLD}/L{N}_{Name}_v{OLD}.pla
```

This preserves the exact production code before overwrite.

### Step 2: Run PROMOTE_CHECKLIST (Rule #19)

Run all 6 checks on the NEW version before deploying:
- Check 1: Placeholder scan (grep for hardcoded gates)
- Check 2: Rule #11 Settlement_Flat 7/7
- Check 3: Rule #12 SetStopLoss guard
- Check 4: Rule #15 ASCII 100%
- Check 5: Rule #13 10 dimensions + Rule #18 5 pieces
- Check 6: Sniper conditions (if <20 trades/yr)

Fail Check 1-4 = REJECT. Check 5 needs >= 4/5 pieces pass.

### Step 3: Update parameter defaults

Per memory rule `feedback_param_must_sync`: optimized input values must be
updated in the .pla default. Code = deploy = docs must be in sync.

Example: `SL_Pct(0)` -> `SL_Pct(0.5)` if 0.5 is the production value.

### Step 4: Update version string

Remove "research" from version header if present:
`V3.1 research (...)` -> `V3.1 (...)`

### Step 5: Deploy to live

```bash
cp strategies/research/L{N}_v{NEW}/L{N}_{Name}_v{NEW}.pla strategies/live/L{N}_{Name}.pla
```

### Step 6: Verify deployment

- ASCII check on deployed file
- Confirm version string
- Confirm parameter defaults match production values

### Step 7: Commit + push

Single commit with message pattern:
```
promote L{N} V{OLD} -> V{NEW}: {one-line summary}
```

Include both the archived old version and the deployed new version in the commit.

## Rollback procedure

To revert to a prior version:

```bash
cp strategies/research/L{N}_v{OLD}/L{N}_{Name}_v{OLD}.pla strategies/live/L{N}_{Name}.pla
```

Every version ever deployed is findable in `strategies/research/L{N}_v{XX}/`.

## Version history (L1 TrendLong)

| Version | Date | Location | Key change |
|---------|------|----------|------------|
| V3.0 | 2026-07-23 | `research/L1_v30/` | IOG migration, tick-level SP/trail |
| V3.1 | 2026-07-25 | `research/L1_v31/` + `live/` | SL_Pct percentage stop cap (0.5%) |
| V3.2 | KILLED | `research/L1_v31/L1_V32_X4_FINAL_VERDICT.md` | X4 Breakout Quality Filter (cross-TF cliff-edge) |

## Notes

- FINAL_VERDICT docs for killed experiments stay in the base version's folder
  (V3.2 was based on V3.1, so its verdict is in L1_v31/)
- The .bak files in live/ (e.g. L1_TrendLong.pla.bak_20260723) are legacy
  manual backups; this skill replaces that pattern with proper versioned archives
- Deploy only when flat (no open position in MC9)
