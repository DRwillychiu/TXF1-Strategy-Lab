# S16_L MACrossLong — SUSPENDED (2026-07-10)

**狀態**：🟡 **SUSPENDED**（用戶 ruling 2026-07-10）
**暫停時點**：Stage -1 對話討論階段（未進入 W0）
**暫停理由**：**用戶決定優先做 S16_S 時框延伸實驗（S16_S_10M）**
**Roadmap 影響**：S16_L Queue → **SUSPENDED，等時框實驗完成再評估**

---

## 一、暫停決策脈絡

### 事件時序
1. **2026-07-10 21:30** — S16_S v1.0-PROD 完成 PROMOTE
2. **2026-07-10 22:10** — 依 OFFICIAL_ROADMAP R-6 順序啟動 S16_L
3. **2026-07-10 22:15** — Claude 寫了 Stage-1 spec md（**跳步：未對話討論**）
4. **2026-07-10 22:20** — 用戶指出 Claude 跳步，要求回歸 SOP v2 對話討論
5. **2026-07-10 22:30** — Claude 承認錯誤，列出 8 個前置討論 topics
6. **2026-07-10 22:35** — **用戶 ruling：暫停 S16_L，改做 S16_S 時框延伸實驗**

### 用戶原話（verbatim）
> **「我認為要先暫停 S16_L 的開發。先去記錄暫停。**
> **因為我想針對 S16_S 的策略進行週期的改變，去延伸不同週期下的策略。**
> **我想先改成以操作週期為 10M 為主。所以策略名稱要設定成 S16_S_10M」**

---

## 二、暫停原因分析

### 為什麼優先做 S16_S_10M 而非 S16_L？

| 面向 | S16_L | S16_S_10M |
|-----|-------|---------|
| 策略性質 | **新策略**（Long 方向）| **時框延伸**（Short 方向不變）|
| 開發成本 | 高（W0-W6 完整流程 + Long 邏輯調整）| 中（Fast/Slow 值 GA + W3-W5 重跑）|
| Alpha 假設 | 需驗證 Long momentum burst 存在性 | 已知 Short momentum burst 存在，測 10M 是否有效 |
| Portfolio 貢獻 | 補 5M Long sleeve（可能與 L1/L5 重疊）| 補 10M Short sleeve（差異化明確）|
| 風險 | Long 動能不對稱、樣本少、可能 KILL | 較低，已有 5M 版本作 baseline |
| 學習價值 | 標準 R-6 pair | **驗證時框對 sniper 型策略的影響** |

### 用戶洞察（推斷）
用戶想**先驗證 S16_S sniper 型策略在不同時框下的表現**，這是**更有學術與實戰價值**的實驗。若 10M 版本也 profitable，證明 sniper 型架構有時框 robustness。

---

## 三、Pre-W0 討論已完成的 8 個 topics（audit trail）

Claude 提出但**未逐一討論**（用戶跳過直接暫停）：

1. Long momentum 在 TXF1 5M 上是否存在
2. 與現有 5 個 Long sleeve 差異化定位
3. 是否照 R-6 硬鏡像 S16_S，還是允許結構調整
4. 時框選擇：5M vs 10M vs 15M
5. Portfolio saturation 檢查
6. Signal 命名 convention
7. 保險成本方向（Bear 急殺應該虧多少）
8. W0 alpha pre-verify 的 4 個 gates

**這 8 個 topic 保留為未來 S16_L 重啟時的討論起點**。

---

## 四、暫停期間 Rule #14 排程調整

### 原 roadmap
```
S3_L → S3_S → S4_L KILLED → S4_S KILLED → S16_S ✅ PROMOTED → S16_L → S5_L → ...
```

### 暫停後 roadmap
```
S3_L → S3_S → S16_S ✅ PROMOTED
→ S16_S_10M 🔵 CURRENT（時框延伸實驗，不算 roadmap 新項目）
→ S16_L 🟡 SUSPENDED（未來重啟）
→ S5_L → S5_S → ...
```

**Rule #14 合規性**：S16_S_10M 是 S16_S 家族擴展，不算新策略，不違反排程。

---

## 五、重啟 S16_L 的觸發條件

1. **S16_S_10M 實驗完成**（whether promote or KILL）
2. **Portfolio 需要新 Long sleeve**（若 L1/L5/S3_L 表現不足）
3. **明確 Long momentum 存在證據**（例如業界文獻或 TXF1 實測）

---

## 六、Files 保留

以下檔案**保留但標記 SUSPENDED**：
- `S16_L_stage1_spec.md`（Stage-1 討論初稿，可作為未來重啟起點）
- `S16_L_SUSPENDED_20260710.md`（本檔）

---

## 七、Rule #14 決策記錄

| 決策 | 依據 |
|------|-----|
| 暫停 S16_L | 用戶 2026-07-10 明確 ruling |
| 允許 S16_S_10M 開發 | S16_S 家族擴展，非新策略，不違反排程 |
| Rule R-6 純多拆分暫緩 | 用戶優先做時框實驗 |

---

**End of SUSPENDED Report — 2026-07-10 Desktop**

**S16_L 開發保留完整 Stage-1 討論資料，未來可直接重啟**。
