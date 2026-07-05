# S3_S Handoff: Desktop 2026-07-04 → Laptop 2026-07-05

**接手時請先讀本檔**，接續 v1.9.6-ANTIHUNT 進度。

---

## 一、今日進度摘要（2026-07-04 桌機）

### ✅ 完成事項

1. **v1.9.5 深度審查**（8 大參數區塊 Q&A）
2. **v1.9.6-ANTIHUNT Round 1 落實**（7 items code 完成 + ASCII PASS）
3. **反掃單 5 層設計**（L1+L2 落實，L3-L5 pending）
4. **完整文件 + Git 同步**（本地 = 雲端）

### 📊 Git 時間軸（今日 4 commits）

```
57d4b9f  feat(S3_S): v1.9.6-ANTIHUNT Round 1 - 7 items + BWRank bug fix
cc83988  docs(S3_S): plan v1.9.6-ANTIHUNT + anti-hunt 5-layer design
77c78c4  docs(S3_S): append 2026-07-04 Q&A on 8 parameter blocks
396ed12  L5: revert to v19.8 production
```

Repo：https://github.com/DRwillychiu/TXF1-Strategy-Lab.git

---

## 二、當前策略狀態

### Baseline: v1.9.5-EXPERIMENTAL
- 檔案：`S3_VolSqueezeShort_v195_EXPERIMENTAL.pla` (969 LOC)
- Backtest: 68T / +513.4K / PF 1.574 / MDD -19.05% / WR 50%
- Rule #18: 3/5 pass (MC/Bootstrap PASS, MDD 邊界 FAIL 0.64%)

### 實驗版: v1.9.6-ANTIHUNT
- 檔案：`S3_VolSqueezeShort_v196_ANTIHUNT.pla` (1107 LOC)
- Spec：`v196_ANTIHUNT_spec_20260704.md`
- 7 features 全 input 預設 OFF/0 = v1.9.5 baseline（除 BWRank guard 預設 ON）

---

## 三、v1.9.6-ANTIHUNT 7 個 Feature 對照表

| # | Item | Section | Input | Default |
|---|------|---------|-------|---------|
| 1 | 夜盤 SL 加寬 22:00-05:00 | 7, 9 | `NightSL_Widen_On` | **False** |
| 2 | Confirmation SL 連 N 根 | 11 S-4 | `ConfirmSL_On` / `ConfirmSL_Bars=2` | **False** |
| 3 | BWRank equal-BW guard | 6 | `BWRank_EqualGuard_On` | **True** (bug fix) |
| 4 | Mid Exit Confirm Bars | 11 S-2 | `MidExit_ConfirmBars` | 1 |
| 5 | Mid Exit Peak Min ATR | 11 S-2 | `MidExit_PeakMinATR` | 0 |
| 6 | SP Peak Min Pts | 11 P0.5 | `SP_Peak_Min_Pts` | 0 |
| 7 | 夜盤 SP Volume 確認 | 11 P0.5 | `SP_Night_VolConfirm_On` | **False** |

---

## 四、用戶 ruling 溯源（2026-07-04）

### Morning Q1-Q7（8 大參數區塊）
- Q1 BB Squeeze：BWStd=2.0 / BWLookback=120 (6.3 天)
- Q2 Exit 時序管理
- Q3 SP Trail 保護
- Q4 Cooldown 移除（Use_Cooldown=False）
- Q5 Hunt Quality Gates
- Q6 Regime Filter
- Q7 1M Multi-Layer Exit 3-gate

### Afternoon 8 個 follow-up
1. md 完整更新 ✅
2. BWLookback 6 太寬鬆 → **改 5 或 3 天**（Round 2 待實作）
3. 兩次壓縮 = **獨立事件**（Round 2 評估缺點後實作）
4. Exit 時間管理極致優化 ✅（Round 1 落實）
5. SP Arm 缺點 ✅（Round 1 落實 Peak Min + Night Vol）
6. Fire 用 1M K close ✅（確認）
7. Hunt Gates 過擬合（Round 2 sensitivity）
8. 1M Multi-Layer Exit 缺點（Round 2/3 補 MAE Cap + Multi-K confirm）

### Late Afternoon 6 大新問題
1. BWRank 週期 + bug 驗證（Round 2）
2. 每次 squeeze 獨立事件實戰缺點（Round 2）
3. Exit 極致優化優先順序 ✅（規劃 + Round 1 落實）
4. SP Arm 缺點優先順序 ✅（規劃 + Round 1 落實）
5. **🆕 26/06 夜盤 stop hunting 觀察 → 極端行情策略反掃單**
   → **落實 Anti-Hunt L1 + L2**（Round 1）
6. 優先處理 + 完整表格 + git 同步 ✅

---

## 五、反掃單 5 層進度

| 層 | 機制 | 進度 |
|----|------|------|
| **L1** | 夜盤 SL 加寬 22:00-05:00 × 1.3 | ✅ Round 1 落實 |
| **L2** | Confirmation SL 連 2 根 1M K close > SL | ✅ Round 1 落實 |
| **L3** | Hunt Detection Log（MAE 觸 SL 後 5min 回升）| ⏳ Round 2 |
| **L4** | Fake Break Re-entry（反利用 hunt）| ⏳ Round 3 |
| **L5** | 時段風險 Modifier（動態 SL）| ⏳ Round 3 |

---

## 六、明天筆電端建議下一步（等用戶 ruling）

### 選項 A：立刻回測 v1.9.6（推薦順序）
1. **Config A**（全關）→ 確認 = v1.9.5 baseline（sanity check）
2. **Config B**（只開 BWRank guard）→ 測 bug fix 影響
3. **Config D**（開 L1+L2 only）→ 測 anti-hunt 純效果
4. **Config C**（Round 1 全開）→ 完整版

### 選項 B：先跑 Round 2 Sensitivity
- BWLookback 敏感度 57/95/120 三組
- Hunt Gates plateau (Thrust_Margin / Hunt_Max_Stops)
- 獨立 episode 缺點測試

### 選項 C：直接 Round 3 進階實驗
- Fake Break Re-entry 邏輯設計
- 時段風險 Modifier

---

## 七、4 組 Backtest Config 對照

### Config A：純 v1.9.5 baseline reproduction（sanity）
```
NightSL_Widen_On       = False
ConfirmSL_On           = False
BWRank_EqualGuard_On   = False   ← 特別關掉才是純 baseline
MidExit_ConfirmBars    = 1
MidExit_PeakMinATR     = 0
SP_Peak_Min_Pts        = 0
SP_Night_VolConfirm_On = False
```
**預期**：68T / +513K / PF 1.574 / MDD -19.05%（與 v1.9.5 一致）

### Config B：Bug Fix 單獨測試
Config A + `BWRank_EqualGuard_On = True`
**目的**：驗證 BWRank bug 修正對交易數影響

### Config C：Round 1 完整開啟
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

### Config D：純 Anti-Hunt L1+L2（隔離測試）
Config A + `NightSL_Widen_On = True` + `ConfirmSL_On = True`

---

## 八、關鍵檔案清單

### 核心
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v195_EXPERIMENTAL.pla` — Baseline
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v196_ANTIHUNT.pla` — 實驗版
- `strategies/research/S03_VolSqueezeShort/v196_ANTIHUNT_spec_20260704.md` — Spec

### 文件
- `strategies/research/S03_VolSqueezeShort/v195_unresolved_and_realworld_20260703.md`
  - 附錄 A：8 大參數區塊逐項驗證
  - 附錄 B：v1.9.6-ANTIHUNT 規劃 + 反掃單 5 層 + Round 1/2/3
- `strategies/research/S03_VolSqueezeShort/v195_GA_validation_20260703.md` — Rule #18 驗證
- `strategies/research/S03_VolSqueezeShort/README.md` — 專案總覽（含 v1.9.6 行）

### 本 handoff
- `strategies/research/S03_VolSqueezeShort/HANDOFF_20260704_to_laptop.md`

---

## 九、規則遵守

- ✅ Rule #11 Settlement_Flat（承襲 v1.9.5）
- ✅ Rule #12 SetStopLoss guard（承襲 + widen 適配）
- ✅ Rule #13 機構級 10 維度（待 Config C 全套跑）
- ✅ Rule #14 OFFICIAL_ROADMAP（未跳號 / 未發明策略）
- ✅ Rule #15 ASCII 100%（`scripts/verify_pla_ascii.py --strict` PASS）
- ✅ Rule #16 五支柱工程系統
- ✅ Rule #17 極端 SL 多層 SOP（承襲 + anti-hunt 層）
- ⏳ Rule #18 5 件套（3/5 done: MC/Bootstrap/HHI，pending: Sensitivity/WFA/Stress）

---

## 十、注意事項

1. **v1.9.5 = production baseline** — 未推進；v1.9.6-ANTIHUNT = **實驗版**
2. **BWRank guard 是 bug fix** — 預設 ON，其他 6 個都是 optional gate
3. **backtest 前務必先跑 Config A** 確認 = v1.9.5 baseline，避免 code bug 誤判效果
4. **不要動 Entry logic / Hunt State Machine / 1M ML Exit factor** — v1.9.6 只在 exit + SL 側加 gate
5. **feedback_git_full_push**：更新 git 一律 commit + push（本次已遵守）
6. **feedback_language_chinese**：對話一律繁中，code 保持英文
7. **feedback_no_break_questions**：用戶自管節奏，主動推進

---

## 十一、Todo Follow-up

從桌機端未完成事項延續：
- Task #142：1M 還沒形成 fill SL 深度研究
- Task #145：v1.8.1 WFA GA 加速建議
- Task #150：v1.9.1 GA Phase 2 全範圍優化建議
- Task #151：5 件套 Python script templates
- Task #158：v1.9.7 W4 WFA 9 windows OOS verification
- Task #159：v1.9.8 5 件套 Non-WFA validation Rule #18（in_progress）

---

**Handoff Complete — 2026-07-04 桌機端**
