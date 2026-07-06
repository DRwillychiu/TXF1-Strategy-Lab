# S3_S v1.9.6-ANTIHUNT Spec (2026-07-04)

**Base**: v1.9.5-EXPERIMENTAL (GA-best 68 trades / Net +513K / PF 1.574 / MDD -19.05%)
**Motivation**: 用戶 2026-07-04 觀察 26/06 起夜盤 stop hunting + 8 大參數區塊審查
**Compatibility**: 全新 input 預設 OFF/0（除 BWRank guard 是 bug fix 預設 ON），設 default = v1.9.5 baseline

---

## Round 1 — 7 個 Features 完整表格

| # | Feature | Section | Input | Default | 開/關語意 |
|---|---------|---------|-------|---------|--------|
| 1 | **Night SL Widening** | 7, 9 | `NightSL_Widen_On` | **False** | ON = 夜盤 22:00-05:00 SL × 1.3 |
| 1a | Night SL Multiplier | 7 | `NightSL_Mult` | 1.3 | SL 距離放大倍數 |
| 1b | Night Start | 7 | `NightSL_Start_Time` | 2200 | HHMM |
| 1c | Night End | 7 | `NightSL_End_Time` | 500 | HHMM |
| 2 | **Confirmation SL** | 11 S-4 | `ConfirmSL_On` | **False** | ON = 連 N 根 1M K close > SL 才觸發 |
| 2a | Confirm Bars | 11 S-4 | `ConfirmSL_Bars` | 2 | 連續 K 數 |
| 3 | **BWRank Equal-BW Guard** | 6 | `BWRank_EqualGuard_On` | **True** | ON = 若 all BW 相等強制 Squeeze=False |
| 3a | Min Filled | 6 | `BWRank_MinFilled` | 5 | 至少填 N 根才啟動 guard |
| 4 | **Mid Exit Confirm Bars** | 11 S-2 | `MidExit_ConfirmBars` | 1 | 需連續 N 根 Close > MidBand |
| 5 | **Mid Exit Peak Min ATR** | 11 S-2 | `MidExit_PeakMinATR` | 0 | Peak_Profit >= v_ATR × X 才 exit |
| 6 | **SP Peak Min Pts** | 11 P0.5 | `SP_Peak_Min_Pts` | 0 | Peak_Profit_Pts >= X 才 fire SP |
| 7 | **SP Night Vol Confirm** | 11 P0.5 | `SP_Night_VolConfirm_On` | **False** | ON = 夜盤 P0.5 需 Volume > Avg |
| 7a | Vol Avg Len | 11 P0.5 | `SP_Night_VolAvgLen` | 15 | Average(Volume, N) |

---

## 完整 Anti-Hunt 5 層設計 (Round 1 落實 L1 + L2)

| 層 | 機制 | Round | Status |
|----|------|-------|--------|
| **L1** | 夜盤 SL 加寬 22:00-05:00 × 1.3 | Round 1 | ✅ 落實 |
| **L2** | Confirmation SL 連 2 根 1M K close > SL | Round 1 | ✅ 落實 |
| **L3** | Hunt Detection Log（MAE 觸 SL 後 5min 回升）| Round 2 | ⏳ 待實作 |
| **L4** | Fake Break Re-entry（反利用 hunt）| Round 3 | ⏳ 待實作 |
| **L5** | 時段風險 Modifier（動態 SL）| Round 3 | ⏳ 待實作 |

---

## 8 大參數區塊審查應對表

| 用戶點出的問題 | Round 1 應對 |
|-------------|------------|
| ① BB Squeeze BWLookback 6.3 天太寬鬆 | ⚠️ 未改預設值（120），等 Round 2 sensitivity 確認 5 或 3 天 |
| ① BWRank 震盪相等 bug | ✅ 加 `BWRank_EqualGuard_On`（default ON）|
| ② 兩次壓縮 = 獨立事件 | ⏳ Round 2（缺點還需評估）|
| ③ Exit 時間管理極致優化 | ✅ ConfirmBars + PeakMinATR gate |
| ④ SP Arm 5 缺點 | ✅ Peak Min Pts + Night Vol Confirm |
| ⑤ P0.5 用 1M K close | ℹ️ 已確認（不需改動）|
| ⑥ Hunt Gates 過擬合 | ⏳ Round 2 sensitivity |
| ⑦ 1M Multi-Layer Exit 缺點 | ⏳ Round 2/3（MAE Cap + Multi-K confirm）|
| ⑧ 夜盤 stop hunting | ✅ NightSL_Widen + ConfirmSL_On |

---

## Backtest 建議

### Config A：純 v1.9.5 baseline reproduction（sanity check）
```
所有 v1.9.6 新 input 全部關掉：
  NightSL_Widen_On       = False
  ConfirmSL_On           = False
  BWRank_EqualGuard_On   = False   ← 特別關掉 guard 才是純 baseline
  MidExit_ConfirmBars    = 1
  MidExit_PeakMinATR     = 0
  SP_Peak_Min_Pts        = 0
  SP_Night_VolConfirm_On = False
```
**預期**：68 trades / Net +513K / PF 1.574 / MDD -19.05%（與 v1.9.5 一模一樣）

### Config B：Bug Fix 單獨測試
```
Config A + BWRank_EqualGuard_On = True
```
**預期**：若 backtest 期間出現 equal-BW 情境 → 部分 trade 消失

### Config C：Round 1 完整開啟（Anti-Hunt 全部 ON）
```
NightSL_Widen_On       = True
ConfirmSL_On           = True
ConfirmSL_Bars         = 2
BWRank_EqualGuard_On   = True
MidExit_ConfirmBars    = 2
MidExit_PeakMinATR     = 0.5
SP_Peak_Min_Pts        = 100
SP_Night_VolConfirm_On = True
```
**預期**：Trade 數下降（gate 變嚴），MDD 改善（夜盤 hunt 保護），Net 待驗證

### Config D：Anti-Hunt 只開 L1 + L2（分離測試）
```
Config A + NightSL_Widen_On = True + ConfirmSL_On = True
```
**目的**：純測 anti-hunt 效果，隔離其他 gate 影響

---

## Rule #18 5-piece Validation Status

| # | Test | v1.9.5 | v1.9.6 |
|---|------|--------|--------|
| 1 | Monte Carlo (95% MDD) | 30.64% FAIL boundary | 待跑 |
| 2 | Bootstrap Resampling | 89.3% PASS | 待跑 |
| 3 | Parameter Sensitivity | ❌ 未跑 | OPT 完成 (5-param) |
| 4 | Walk-Forward Analysis | ❌ 未跑 | CONDITIONAL FAIL (WFE 14.8%, Path A exemption) |
| 5 | Stress Testing 6 events | ❌ 未跑 | 待跑 |

---

## Git History

- `396ed12` 2026-07-03: v1.9.5 GA validation 補強
- `77c78c4` 2026-07-04: 8 大參數 Q&A md 更新
- `cc83988` 2026-07-04: v1.9.6-ANTIHUNT 規劃 md
- `_next_` 2026-07-04: **v1.9.6-ANTIHUNT.pla + spec 落實**

---

## 用戶 ruling 溯源

- 2026-07-04 morning Q1-Q7：BB Squeeze / Exit / SP / Cooldown / Hunt Gates / Regime / 1M Multi-Layer
- 2026-07-04 afternoon 6 大新問題：
  1. 驗證 BWRank 週期 + bug（Round 2）
  2. 每次 squeeze 獨立事件的實戰缺點（Round 2）
  3. Exit 時間管理極致優化（Round 1 落實）
  4. SP Arm 缺點（Round 1 落實）
  5. 夜盤 stop hunting 極端行情策略（Round 1 落實 L1+L2）
  6. 優先順序處理 + 表格 + git 同步（本 spec）
