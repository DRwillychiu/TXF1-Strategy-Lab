# Handoff 2026-06-27 (Session 2) — S3_S v1.7.3 Band-Reject Regime Filter Backtest

**From**: Laptop (筆電端)
**To**: Desktop (桌機端 MC12)
**Status**: v1.7.3 code ready, awaiting MC12 backtest
**Priority**: Run backtest with BlockRange=True to verify Bear alpha recovery

---

## What Changed (v1.7.2 → v1.7.3)

### Bug Found in v1.7.2
v1.7.2 used `Regime_MinRatio >= 0.98` (lower-bound filter), which **kills Bear alpha**:
- Strong Bear (<0.95): PF 99, **blocked by MinRatio**
- Weak Bear (0.95~0.98): PF 11.0, +492K, **blocked by MinRatio**
- Range (0.98~1.02): PF 0.73, -259K (correctly blocked)
- Weak Bull (1.02~1.05): PF 1.61 (correctly blocked)
- Strong Bull (>1.05): PF 4.49 (only survivor)

### v1.7.3 Fix: Band-Reject Design
Changed to `v_Regime_OK = True` then **block specific zones**:
- Removed `Regime_MinRatio` input entirely
- Added `Regime_BlockRange (True)` — blocks 0.98 <= ratio <= 1.02
- Kept `Regime_BlockWeakBull (True)` — blocks 1.02 < ratio < 1.05

**Result**: Bear (<0.98) and Strong Bull (>1.05) both PASS, only Range + WeakBull blocked.

---

## MC12 Backtest Instructions

### File to Load
```
strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v17.pla
```

### Required Inputs (confirm these in MC12)
| Input | Value | Note |
|-------|-------|------|
| Use_Regime_Filter | True | Master switch |
| Regime_FastMA | 20 | Daily fast MA (or try Round 1 best: 15) |
| Regime_SlowMA | 50 | Daily slow MA (or try Round 1 best: 40) |
| Regime_BlockRange | **True** | v1.7.3 new — blocks PF 0.73 zone |
| Regime_BlockWeakBull | True | v1.7.1 — blocks PF 1.61 zone |

### Data Requirement
- Data1: TXF1 intraday (15M or whatever S3_S uses)
- Data2: **Daily chart** (regime MA calculated from Daily close)

### What to Compare
1. **v1.7.3 (BlockRange=True)** vs **v1.7.1 baseline (BlockRange=False)**
2. Key metrics: Net Profit, PF adj (with slippage), MDD%, Sharpe
3. Verify Bear trades are NOT filtered out (should see Strong Bear + Weak Bear trades)
4. Verify Range trades ARE filtered out (0.98~1.02 zone should be empty)

### Expected Outcome
If band-reject works correctly:
- Net Profit should improve ~+259K (Range zone P&L was -259K)
- Bear alpha (+492K from Weak Bear) should be preserved
- Trade count drops by Range-zone trades only

---

## Repo Audit Completed (This Session)

7-item cleanup pushed as `560f41f`:
- CLAUDE.md directory tree: complete rewrite with full expansion
- S3_L archived to `archive/S03_VolSqueezeLong_promoted_20260620/`
- 9 temp scripts relocated to proper `_analyze_scripts/` folders
- Duplicate Batch01 summary removed
- All 5 READMEs updated (docs, live, research, archive)
- 282 files tracked, structure verified clean

---

## Git State
```
560f41f repo audit: fix directory tree, archive S3_L, dedup, move temp scripts
9142d47 docs: sync S3_S v1.7.3 progress to TRACKER, B01 log, annotated.md
521a9a1 S3_S v1.7.3: fix regime filter to band-reject (recover Bear alpha)
```

All pushed to remote. Desktop should `git pull` before starting.
