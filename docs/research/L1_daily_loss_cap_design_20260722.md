# L1 Daily Loss Cap Design Spec — P8 Module (V2.8)

- **Date**: 2026-07-22
- **Strategy**: L1_TrendLong V2.7 -> V2.8
- **Problem**: P3 (structural audit) — no per-strategy daily loss limit
- **Prerequisite**: `L1-L5_structural_audit_20260721.md`, `L1-L5_optimization_user_review_20260722.md`
- **Status**: **REJECTED by backtest** — V2.8 net harmful (-167K NTD, MDD +100K worse). See `L1_v2.8_backtest_verdict_20260722.md`. Pending points-based redesign discussion.

---

## 1. Objective

Add a dual-trigger daily loss cap to L1 that blocks new entries after excessive losses within a single trading day window. This is the per-strategy implementation of audit P3, scoped to L1 as the first strategy.

**Target behavior**: After 3 closed losing trades OR net closed loss exceeding 100,000 NTD in one window, block all new entries until the next window opens.

---

## 2. Window Definition

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Start | 15:00 (night session open) | User-confirmed window (7/22 review) |
| End | 13:45 (next day close) | Covers one complete night+day cycle |
| Reset | First bar of each night session | Detected by `Time >= 1500 AND Time <= 1600 AND Time[1] <= 1400` |

The window spans two MC calendar dates (night bars after midnight carry the next day's date). Reset detection uses the time gap between day session close (~13:15) and night session open (~15:45) — robust to holidays and market closures.

---

## 3. Dual Trigger Design

### Trigger 1: Count-Based (Primary)
- **Input**: `DailyLoss_MaxCount(3)` — max closed losing trades per window
- **Mechanism**: Increment counter when `v_Prev_MP > 0 AND MP = 0 AND PositionProfit(1) < 0`
- **Rationale**: L1 trades 73/year (0.29/day). 3 losses in one window = extreme tail event.

### Trigger 2: NTD-Based (Secondary)
- **Input**: `DailyLoss_MaxNTD(100000)` — max cumulative closed loss per window (NTD, positive number)
- **Mechanism**: `(NetProfit - v_DayLoss_NetProfit_Snap) <= -DailyLoss_MaxNTD`
- **Rationale**: Provides high-vol protection. In normal vol, count trigger fires first (3 x 17.5K avg = 52.5K < 100K). In high vol, 2 large losses (2 x 90K = 180K > 100K) trigger NTD cap before count reaches 3.

### Trigger Interaction

| Scenario | Count | NTD Loss | Which Fires |
|----------|------:|--------:|------------|
| 3 avg losses (normal vol) | 3 | -52K | Count |
| 2 high-vol losses | 2 | -180K | NTD |
| 2 avg losses + 1 high-vol | 3 | -125K | Both |
| 1 avg loss + 1 big win + 1 avg loss | 2 | +45K net | Neither |

### Master Switch
- **Input**: `DailyLoss_Enable(True)` — allows disabling without removing code

---

## 4. Trade Detection Logic

Uses `v_Prev_MP` pattern (CLAUDE.md Rule #8):
```
if v_Prev_MP > 0 and MP = 0 then begin
    if PositionProfit(1) < 0 then
        v_DayLoss_Count = v_DayLoss_Count + 1;
end;
```

`v_Prev_MP` is updated at the end of each bar evaluation (`v_Prev_MP = MP;`).

NTD tracking uses MC's `NetProfit` reserved word, which includes all closed trades regardless of IOG setting. This is more reliable than `PositionProfit(1)` for cumulative tracking.

---

## 5. Entry Gate Integration

Added as the 6th condition in the entry gate:
```
if MP = 0 and
   Cond_Breakout and
   (v_Weekly_Filter = true) and
   (v_Holiday_Block = false) and
   (v_Settlement_Day = false) and
   (v_DailyLoss_Block = false) then begin
    Buy ("TL_Entry") next bar at Market;
end;
```

**Only blocks entries.** Existing positions continue normal exit logic (P3 frozen SL, P4 trail, P7 SP, priority exits). The P3b SetStopLoss guard also remains active (engine-level, independent of entry gate).

---

## 6. Code Placement

Module inserted between Settlement detection (end of section 1b) and Entry logic (section 2). `MP = MarketPosition` and `Cond_Breakout` moved into the P8 section header so the module can evaluate position state before the entry gate.

```
[Indicators] -> [Weekly Filter] -> [Holiday/Settlement] ->
[P8 Daily Loss Cap] -> [Entry Gate] -> [Exit Management] ->
[Priority Exits] -> [MDD Visual] -> [v_Prev_MP update]
```

---

## 7. New Inputs

```
{ P8: Daily Loss Cap (V2.8) }
DailyLoss_Enable(True),
DailyLoss_MaxCount(3),
DailyLoss_MaxNTD(100000),
```

## 8. New Variables

```
{ P8: Daily Loss Cap Variables }
v_DayLoss_Count(0),
v_DayLoss_NetProfit_Snap(0),
v_DailyLoss_Block(False),
v_Prev_MP(0),
```

---

## 9. Known Limitations

1. **Same-bar entry+exit (SetStopLoss)**: If P3b triggers within the entry bar, the count trigger misses it (v_Prev_MP never saw MP > 0). The NTD trigger still catches it via NetProfit. Rare event — requires ATR x 1.5 move within 45 minutes.

2. **Cross-day trade attribution**: A trade that enters in window N but exits in window N+1 counts against window N+1 (exit time). This is by design — the loss is realized in the exit window.

3. **Net vs gross NTD**: The NTD trigger uses NetProfit (net of all closed trades in window). A big win between losses reduces the NTD count. Example: -40K, +100K, -40K = +20K net -> NTD trigger NOT fired (count trigger fires at 2 losses if applicable). This is intended — net positive days don't need capping.

4. **Backtest vs live divergence**: In live MC9, bar timing and fill prices may differ slightly from backtest. The 100K NTD threshold has margin for this.

---

## 10. Expected Backtest Impact

- L1 trades 73/year (0.29/day). The 3-loss count trigger fires on days with 3+ entries that all stop out — historically very rare.
- From review Section 9.4: consecutive loss breaker (>=10 -> pause 1 week) saved 66,600 NTD over 6.5 years. The daily loss cap is a similar but per-day mechanism; expected impact is small positive (tail risk reduction) at the cost of occasional missed recovery entries.
- **Critical**: Review Section 9.5 showed <6h re-entry has the highest win rate (34.7%). The 3-loss cap preserves the first 2 re-entries and only blocks the 3rd+, minimizing conflict with this finding.
- **MC12 backtest required** before MC9 deployment to confirm exact impact on net profit, PF, and MDD.

---

## 11. Tradeoff Analysis

| Metric | Expected Direction | Reasoning |
|--------|-------------------|-----------|
| Net Profit | Slightly negative | Blocks some positive-EV entries after 3 losses |
| MDD | Improved | Prevents 4+ loss cascades in single day |
| Worst Day | Improved | Hard cap on daily damage |
| Trade Count | Slightly reduced | Blocked entries (~1-3/year estimate) |
| Win Rate | Neutral | Blocked entries are random WR (31.3%) |

The daily loss cap trades small expected profit for significant tail risk reduction. This aligns with the "small win + big win + small loss" target profile.

---

## 12. Cross-Strategy Applicability

This design is directly portable to L2-L5 with strategy-specific parameter tuning:

| Strategy | Suggested MaxCount | Suggested MaxNTD | Notes |
|----------|------------------:|----------------:|-------|
| L1 | 3 | 100,000 | Current design |
| L2 | 2 | 80,000 | Very low frequency (83 trades/6.5yr) |
| L3 | 3 | 100,000 | Similar frequency to L1 |
| L4 | 3 | 80,000 | Already has cooldown, smaller stops |
| L5 | 3 | 120,000 | Larger ATR multiplier (4.5x) |

---

## 13. Engineering System Checklist (Rule 16)

### Rules
- [x] Rule 11: Settlement module unchanged
- [x] Rule 12: P3b SetStopLoss unchanged (still fires when MP <= 0)
- [x] Rule 15: ASCII only (no Chinese in .pla)
- [x] Rule 17: No exit-side changes; P8 is entry-gate only

### Context
- [x] Prerequisite audit doc referenced
- [x] User review decisions incorporated (7/22 daily loss cap confirmed)
- [x] Cooldown research (review 9.5) accounted for: cap preserves first 2 re-entries

### Verification
- [ ] MC12 backtest: compare V2.7 vs V2.8 (net profit, PF, MDD, trade count)
- [ ] MC9 compile verification
- [ ] MC9 live chart: confirm v_DailyLoss_Block variable visible
- [ ] ASCII verification: `python scripts/verify_pla_ascii.py --strict`

### Memory
- No new memory entries needed (decisions documented in this spec)

### Format
- [x] Design spec follows 13-section structure
- [x] Code changes documented with exact insertion points
