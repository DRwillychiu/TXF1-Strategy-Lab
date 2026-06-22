# RangeForceExit 模組部署報告（憲法 v1.1 條款 7）

**部署日**：2026-06-17
**動機**：實證發現 L3/L4 跨商品交易日比例達 33-36%，存在漂移到 Q4 Swing-Range 禁區的風險

---

## 一、變更摘要

### 程式碼變更

| 策略 | 版本變更 | 變更內容 |
|------|---------|---------|
| L3 ConsolidationLong | v13.2B → **v13.3** | + `Range_ForceExit_Time(1200)` input + `CL_RangeForceExit` Priority 0 出場 |
| L4 ConsolidationShort | v14.2B → **v14.3** | + `Range_ForceExit_Time(1200)` input + `CS_RangeForceExit` Priority 0 出場 |
| L5 BreakoutLong | v19.8（不變）| **重新分類為 Swing-Trend**（突破策略本質跨日，與 L1 同類）|

### 驗證腳本

- 新增：[`scripts/verify_range_force_exit.py`](../scripts/verify_range_force_exit.py)（16 項檢查）
- 更新：[`scripts/verify_strategy_holding_classification.py`](../scripts/verify_strategy_holding_classification.py)（L5 expected 改為 Swing-Trend）

---

## 二、Priority 0 鏈完整順序（L3 / L4 部署後）

```
P0-1  Manual_Kill_Switch       → *_Kill           (緊急停市)
P0-2  v_Registry_Expired       → *_RegistryEnd    (假日登錄表過期)
P0-3  v_Holiday_Block          → *_Holiday        (假日 04:15)
P0-4  v_Settlement_Day + 12:30 → *_Settlement     (月結算)
P0-5  Time >= 1200             → *_RangeForceExit (盤整類強制日盤出場) ★ NEW
P0-6  原策略邏輯               → SP / Trail / Daily / Disaster
```

**時間關係**：
- RangeForceExit 觸發時段：**12:00 起**
- Settlement_Flat 觸發時段：**12:30 起**（僅結算日）
- RangeForceExit **早於 Settlement** 30 分鐘 = 結算日當天也是 RangeForceExit 先觸發

---

## 三、為什麼是 12:00（不是其他時間）

| 候選時間 | 缺點 | 評分 |
|---------|------|------|
| 11:30 | 犧牲半小時 mean-reversion 機會 | △ |
| **12:00** ✓ | 主動先於 Settlement 30 分鐘 + 充裕日盤獲利窗口 | ✅ |
| 12:15 | 與 Settlement 12:30 太接近，buffer 不足 | ❌ |
| 12:30 | 與 Settlement 重疊，失去獨立保護價值 | ❌ |
| 13:00 | 進入結算前噪訊區 | ❌ |

12:00 的設計哲學：**「在結算前噪訊區的入口前主動歸零」**。

---

## 四、驗證結果（部署後即時）

| 驗證腳本 | 結果 |
|---------|------|
| `verify_settlement_flat.py` | **42/42 PASS** ✅ |
| `verify_range_force_exit.py` | **16/16 PASS** ✅ |
| `verify_all_live.py` | **110/110 PASS** ✅ |
| `verify_strategy_holding_classification.py` | L1/L2/L5 PASS, L3/L4/S1 WARN（待 MC 重新回測 v13.3/v14.3）|

---

## 五、L5 重新分類的依據

| 維度 | 原分類「Intraday」| 新分類「Swing-Trend」|
|------|----------------|-------------------|
| 策略本質 | 假設日內突破 | **實質為趨勢突破**（突破成立後追隨）|
| 持倉跨商品交易日比例 | 設計意圖 < 5% | **實證 47.1%** |
| Settlement 觸發 | 預期 0 | 目前 0（但 alpha 來源不排斥跨結算）|
| 與 L1 的關係 | 不同類 | **同類（Swing-Trend 鎖利機制適用）**|

**結論**：L5 應與 L1 / L2 共享「Settlement_Flat = 核心鎖利」哲學，**不應加 RangeForceExit**（會切斷突破延續性）。

---

## 六、待用戶執行的部署步驟

### 必做
1. **MC12 上完全移除舊版 L3 / L4 策略**（避免 input 持久化覆蓋）
2. **重新從 v13.3 / v14.3 .pla 載入**
3. 確認 Inputs panel 出現新欄位：
   - `Range_ForceExit_Time` = 12:00 (1200)
4. **重跑回測**並另存為新檔（建議命名：`*_v143.xlsx`）
5. 把新 xlsx 拉到 Downloads 後，**重跑 `verify_strategy_holding_classification.py`**

### 預期效果（重跑後）

| 策略 | 跨日比例變化 | 自動分類預期 |
|------|------------|-------------|
| L3 | 36.3% → **≈ 0%**（12:00 強制平倉）| Swing-Mixed → **Intraday** |
| L4 | 33.3% → **≈ 0%** | Swing-Mixed → **Intraday** |
| L5 | 47.1%（不變，已重新分類為 Swing-Trend）| Swing-Trend |

### 績效影響預判（可在重跑後驗證）

| 影響面 | L3 預判 | L4 預判 |
|--------|---------|---------|
| 總筆數 | 減少 5-10%（剪掉 12:00 後新開倉 + 提早平倉部位）| 同 |
| WR | 可能略升或持平 | 同 |
| PF | 不確定（取決於剪掉的部位品質）| 同 |
| MDD | 應改善（避免 12:00-13:30 噪訊區放大虧損）| 同 |
| Settlement 觸發 | **必降到 0**（RangeForceExit 早於 Settlement）| 同 |

---

## 七、後續監控

### 下次結算日：2026-07-15
- 觀察 L3 / L4 v13.3 / v14.3 在實盤如何運作
- 確認 12:00 觸發 RangeForceExit 機制成功

### 永續監控
- **每次 input 調整**：強制重跑 `verify_strategy_holding_classification.py`
- **每次新策略開發**：強制三象限分類驗證

---

## 八、設計哲學總結

### 改變前（單一 Settlement_Flat）

```
日內策略 (L3/L4/L5/S1):
  完全依賴自然出場機制 → 撞運氣避開 12:30 Settlement
  風險：未來改 input 可能漂移到 Swing-Range 禁區
```

### 改變後（Settlement_Flat + RangeForceExit 雙模組）

```
盤整類策略 (L3/L4):
  12:00 主動 RangeForceExit → 結構性保證在 Q3 安全象限
  12:30 Settlement_Flat → 兜底（理論上 0 觸發）
  
趨勢/突破類策略 (L1/L2/L5):
  允許跨日 → 享受 Settlement_Flat 鎖利紅利
  不加 RangeForceExit → 不切斷趨勢 alpha
  
夜盤類策略 (S1):
  ExitTime 強制 04:15 → 不撞日盤結算
  Settlement_Flat 兜底
```

---

## 九、相關文件

- [`docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`](SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) v1.1 條款 7
- [`docs/strategy_classification_decision_matrix.svg`](strategy_classification_decision_matrix.svg) 決策矩陣
- [`docs/settlement_flat_backtest_validation_20260617.md`](settlement_flat_backtest_validation_20260617.md) 實證資料
- [`scripts/verify_range_force_exit.py`](../scripts/verify_range_force_exit.py) 驗證腳本
