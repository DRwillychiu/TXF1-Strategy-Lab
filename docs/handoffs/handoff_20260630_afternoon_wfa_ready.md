# Handoff 2026-06-30 Afternoon — WFA Spec Ready, Resume at Home

**Session**: 2026-06-30 afternoon (Laptop)
**Status**: WFA spec complete, ready to execute on MC12
**Next**: User resumes at home to run W1-W9

---

## 1. Status

| Item | Status |
|------|--------|
| Git working tree | Clean |
| Local = origin/main | Pending push (2 commits ahead) |
| v1.7.3-FINAL production | Unchanged (live_simulation) |
| v1.8.0-GA | Active development, WFA next |
| Bug 2 | Downgraded to non-blocking |

---

## 2. Today's Commits (2 commits)

| Commit | Content |
|--------|---------|
| `1ebc10b` | Bug 2 blackswan note: downgraded to non-blocking |
| `106c3e4` | W4 WFA spec (18-file plan) + Bug 2 update (night session trade confirmed) |

---

## 3. Today's Key Decisions

### D1: Continue v1.8.x (not v1.7.3-FINAL)
- User ruling: extreme market strategies NEED 1M judgment capability
- v1.7.3 ATR-only SL is passive, not the desired design
- v1.8.0-GA 1M_Exit already proven (6/8 case: -1,560 pts -> -10 pts)

### D2: Bug 2 downgraded to non-blocking
- MC12 trade list confirms: entry 2024/8/5 16:00 night session (not day session limit-down)
- Trade IS plausible in live trading (night session has liquidity)
- But: low frequency (1 in 6 years), user has manual override, eats profit not principal
- 1M_Exit (market order) completely unaffected by Bug 2
- Bug 2 only affects passive SP/SL stop order layers
- Non-blocking for development; still blocking for promote to live

### D3: WFA spec approved
- 9 windows, IS=24M, OOS=6M, Step=6M
- 10 ML params with defined sensitivity ranges
- 18 output files (9 IS optimization + 9 OOS verification)
- Pass criteria: >= 6/9 OOS positive, WFE > 50%

---

## 4. Resume SOP (Home)

### Step 1: Pull git
```bash
cd <TXF1-Strategy-Lab path>
git pull origin main
```

### Step 2: Read WFA spec
```
strategies/research/S03_VolSqueezeShort/v180GA_W4_WFA_spec_20260630.md
```

### Step 3: Open MC12, load v1.8.0 strategy
- Load `S3_VolSqueezeShort_v180_EXPERIMENTAL.pla`
- Data1: TXF1 60M, Data2: TXF1 Daily, Data3: TXF1 1M
- IOG = TRUE

### Step 4: Run W1 (first window)
- IS: 2020-01-01 to 2021-12-31
- Optimize 10 ML params (GA 256 pop x 30 gen)
- Export: `v180GA_WFA_W1_IS_2020Q1-2021Q4_optimization.xlsx`
- Apply IS-best to OOS: 2022-01-01 to 2022-06-30
- Export: `v180GA_WFA_W1_OOS_2022Q1-Q2_verify.xlsx`

### Step 5: Repeat W2-W9

---

## 5. Files Changed Today

| File | Action |
|------|--------|
| `strategies/research/S03_VolSqueezeShort/bug2_sp_iog_blackswan_note_20260630.md` | NEW — Bug 2 practical assessment |
| `strategies/research/S03_VolSqueezeShort/v180GA_W4_WFA_spec_20260630.md` | NEW — WFA 18-file execution spec |
| `docs/handoffs/handoff_20260630_afternoon_wfa_ready.md` | NEW — This handoff |

---

## 6. Pending Items

| Task | Priority | Blocker |
|------|----------|---------|
| W4 WFA 9-window execution | Now | MC12 time (~5-7 hr total) |
| Phase 1 param sensitivity (plateau check) | With WFA | Same MC12 runs |
| W5 Monte Carlo 10K sim | After WFA pass | WFA results |
| W5 institutional 10-dim assessment | After MC | WFA + MC results |
| Bug 2 fix (dual-strategy or other) | Later | Before promote to live |
| S4_S MACDDivergenceShort W2 | After S3_S closure | S3_S WFA verdict |

---

## 7. Evidence Chain Summary

6 versions tested, 5 lessons (L29-L33), Bug 2 documented:

| Version | Net | SP maxL | Lesson |
|---------|-----|---------|--------|
| v1.7.3-FINAL | +1,013K | -5K | Baseline |
| v1.7.4 cap 100 | +792K | -4.8K | L29: gap fail |
| v1.8.0-orig | +502K | -132K | L30: IOG risk |
| v1.8.0-GA | +846K | -132K | L31: GA partial |
| v1.8.1 BarStatus | +585K | -143K | L32: gate ineffective |
| v1.8.1-GA | +536K | -143K | L33: architecture limit |

Current path: v1.8.0-GA -> WFA verify -> if pass -> MC -> promote decision
