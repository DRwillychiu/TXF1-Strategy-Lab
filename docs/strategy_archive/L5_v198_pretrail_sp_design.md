# L5 v19.8 — Pre-Trail StopProfit 設計（L1 SP 哲學 + L4 教訓）

> 建立日期：2026-06-13
> 用戶概念：L5 = L1 獲利延伸 + L3 進場策略；解決「曾經獲利但全部吐回」
> 對應 PLA：L5_BreakoutLong.pla（v19.8 input-switched A/B engine）
> 預設配置：**所有 SP 開關 OFF = v19.7 行為（迴歸安全）**

---

## 一、設計動機

### 用戶觀察
> 「我希望做到的就是綜合 L1 以及 L3 的優點，因為現階段很明顯就是 L5 的策略就是綜合體。
>  獲利在出現需要延伸時，最擔心的就是獲利回吐。」

### 實證證據（舊版 BREAKOUT Excel，per contract normalized）
- **58 筆「曾經獲利但 ≤ 0」案例**
- **總浪費 MFE：+1,826,000 NTD**（per contract，4.8 年）
- **最慘案例**：2024-05-03 MFE +244 pts → BL_BE_Mid_Wait -10 pts → 吐回 254 pts

### v19.7 為何不解決這個問題？
v19.7 只做結構性安全（HolidayFlat + FrozenSL + DOW dead code 移除），**沒動 BL_BE 機制**。
v19.7 BL_BE Floor = EntryPrice（鎖 0 獲利）。
**L1 V2.6 SP Floor = Entry + Peak × 45%（鎖 peak 的 55%）**。

L5 v19.7 缺的就是這個「按峰值守護」哲學。

---

## 二、v19.8 機制設計

### 核心邏輯（從 L1 V2.6 移植）

```powerlanguage
{ Close-based MFE tracking (matches L1 pattern) }
if Close - EntryPrice > v_Peak_Profit then
    v_Peak_Profit = Close - EntryPrice;

{ Arm SP once threshold reached (never disarms until flat) }
if SP_Trigger_Pts > 0 and v_Peak_Profit >= SP_Trigger_Pts then
    v_SP_Armed = true;

{ Compute floor scaling with peak }
if v_SP_Armed then
    v_SP_Floor = EntryPrice + v_Peak_Profit * (1 - SP_Retain_Pct / 100);
```

### 跟 L1 V2.6 SP 的對比

| 維度 | L1 V2.6 | L5 v19.8 |
|------|---------|----------|
| 觸發門檻 | 250 pts | A/B 測（60/80/100） |
| 保留率 | 55% | A/B 測（40/50） |
| 計算基準 | close-based peak | close-based peak（同 L1）|
| 永不解除 | ✅ | ✅ |
| Floor 公式 | Entry + Peak × 0.45 | Entry + Peak × (1 - Retain/100) |
| 觸發後地板上升 | ✅ peak 增加則 floor 上升 | ✅ 同上 |

### Stop 訂單互斥優先序

**Stage 1（全倉，scale-out 前）**：
```
if v_SP_Armed and v_SP_Floor > v_Bot_Base_Stop:
    BL_SP_Bot at v_SP_Floor Stop   ← SP 緊於初始 SL
else:
    BL_SL_Bot at v_Bot_Base_Stop Stop
```

**Stage 2/3（scale-out 後，runner 60%）**：
```
if Trail_Active:
    if Dynamic_Stop > max(Entry, SP_Floor):
        BL_Trail_Bot   ← Trail 最緊
    elif SP_Armed and SP_Floor > Entry:
        BL_SP_Bot      ← SP 比 BE 緊
    else:
        BL_BE_Bot      ← 進場價保本
else:
    if SP_Armed and SP_Floor > Entry:
        BL_SP_Bot      ← SP 已 arm，用 SP
    else:
        BL_BE_Bot      ← 等 SP arm 或 trail 啟動
```

**優先序總結**：Trail > SP > BE > 初始 SL（LONG 取最高地板 = 最緊保護）。

每根 K 棒每條 leg 只發出 **一個** Stop 單，互斥避免衝突。

---

## 三、L4 v14.2 失敗教訓 vs L5 v19.8 規避

### 為什麼 L4 SP 變體（D/F/G）失敗？

| 失敗點 | L4 v14.2 D |
|--------|-----------|
| CS_SP 自身 100% 勝率 | ✅ 22 筆全賺 |
| 但截斷 CS_SL 大尾巴 | ❌ 從 45/+1,019K → 36/+619K（-401K）|
| 總淨利 | ❌ -212K |
| 機制原因 | 進場後直接接 SP，無 scale-out 緩衝，多階段獲利被截斷 |

### L5 v19.8 的關鍵差異

| 緩衝機制 | L4 v14.2 | L5 v19.8 |
|----------|----------|----------|
| Scale-out 部分停利 | ❌ 無 | ✅ 40% 在 TP 自動落袋 |
| Trail 接管 | 跌破 box_btm 才啟動 | 突破 box_top + ATR×2.5 啟動 |
| SP 影響範圍 | 全倉 | runner 60%（40% 已鎖） |
| 多階段截斷風險 | 高（整單被截）| 中（runner 截斷）|

**L5 因為有 Scale-Out 緩衝，SP 截斷的傷害理論上比 L4 小**。但仍可能傷及「強趨勢延續」案例 → 需 A/B 驗證。

---

## 四、變體矩陣（建議 MC9 測試）

| 變體 | SP_Trigger | SP_Retain | 假設 | 預期 |
|------|-----------|-----------|------|------|
| **A** baseline | 0 | — | v19.7 對照（迴歸檢查）| 必須與 v19.7 完全一致 |
| **B** Aggressive | **60** | 50 | 早期保護（門檻低）| 救回最多但 Top-10 風險最高 |
| **C** Mid | **80** | 50 | 中等門檻 | 平衡點 |
| **D** Conservative | **100** | 50 | 高門檻 | 只保護真大波段 |
| **E** LessRetain | 80 | **40** | 給更多回吐空間 | 留更多趨勢空間 |
| **F** L1-Like | 100 | **55** | 完全鏡像 L1 SP | L1 風格參考組 |

---

## 五、接受/否決條件（每個變體）

### 通過 PASS
- ✅ 淨利 > v19.7 baseline
- ✅ BL_SP 自身勝率 ≥ 50%（不能 0% 勝率，否則是 L3/L4 詛咒重演）
- ✅ Top-10 贏家保留 ≥ 80%（不能截斷大尾巴）
- ✅ MDD 不惡化超過 10%
- ✅ Scale-out（BL_TP）筆數不大幅減少（SP 不應替代 TP）

### 否決 FAIL
- ❌ BL_SP 勝率 < 30%（L3/L4 詛咒重演）
- ❌ Top-10 保留 < 70%（截斷大尾巴）
- ❌ 淨利低於 v19.7（整體淨損）
- ❌ MDD 惡化 > 10%

---

## 六、MC9 部署步驟（用戶端）

### 變體 A（迴歸驗證）— 必須先做
1. 載入 v19.8 PLA
2. 確認 inputs：`SP_Trigger_Pts = 0`、`SP_Retain_Pct = 50`
3. 跑回測 → 必須與 v19.7 結果完全一致
4. Export Excel → 提供驗證

### 變體 B-F 依序測試
1. 在 Inputs 修改 `SP_Trigger_Pts` 和 `SP_Retain_Pct` 對應變體值
2. Apply → 重跑回測
3. Export Excel 並命名（如 `..._v198_B.xlsx`）
4. 全部 6 個 export 完成後傳回給我做完整對比分析

### 我這邊的工作
- 接收 6 個 Excel
- 分析 BL_SP 勝率、Top-10 保留、淨利對比
- 套用接受/否決條件
- 推薦生產配置（可能是 B-F 其中之一，或維持 A baseline = v19.7）

---

## 七、預期結果情境

### 情境 1：某個變體通過所有條件
- 鎖該變體為 v19.8B 生產
- 修改 PLA 預設 SP_Trigger_Pts 為對應值
- 更新 annotated.md 和 verify_all_live.py
- 預期淨利提升 + MDD 改善

### 情境 2：全部變體都被否決（同 L4 命運）
- 維持 v19.7 為生產
- v19.8 程式碼保留但 input 永久 = 0
- 學到「L5 跟 L4 一樣不適合 SP」的新教訓
- 寫入記憶

### 情境 3：部分變體通過但效益小
- 列為「可選」配置
- v19.7 仍是預設

無論結果如何，**v19.7 是迴歸安全的 fallback**。

---

## 八、下一步

立即實作完成後：
1. ✅ v19.8 程式碼上 git
2. ⏭️ 用戶 MC9 跑 6 個變體（A baseline 必須優先驗證）
3. ⏭️ 用戶傳回 Excel
4. ⏭️ 我分析 + 裁定生產配置
5. ⏭️ 寫 `docs/L5_v198_variant_results.md`（同 L4 v14.2 模式）
