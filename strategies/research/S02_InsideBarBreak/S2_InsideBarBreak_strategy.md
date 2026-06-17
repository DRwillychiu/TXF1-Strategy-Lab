# S2 InsideBarBreak — 策略完整說明

**MC Load Name**：`STRATEGY_GEN_InsideBarBreak`
**版本**：v0.2 (Phase 1)
**檔案**：[`S2_InsideBarBreak.pla`](S2_InsideBarBreak.pla)
**寫於**：2026-06-17（reactivation 當天）

---

## 1. 策略概述

### 一行版本
**等日線母子線（Inside Bar）形成壓縮後，跟隨日線 MA 方向買 / 賣突破。**

| 屬性 | 內容 |
|------|------|
| 類別 | **Category B**（Pattern Breakout，型態突破型）|
| 操作方向 | **雙向**（Long when Daily MA up, Short when Daily MA down）|
| 主交易週期 | **30 分鐘**（Data1）|
| 確認週期 | **日線**（Data2）|
| 預期交易頻率 | ~5-7 筆 / 年（樣本稀少策略）|
| 預期分類（憲法條款 6）| **Swing-Trend**（與 L1 同類，跨日持倉是設計本意）|
| 平均持倉 | 1-3 天（最長 15 小時 = MaxBarsHeld 30 根 30M）|

### 在策略組合中的角色

> **「低頻 / 高品質 / 雙向」的 Pattern Trader**，補足現有 6 隻策略中**沒有「型態識別」alpha 來源**的缺口。

| 現有策略 alpha 來源 | S2 alpha 來源 |
|------------------|------------|
| L1 L2: ATR breakout 趨勢延續 | **Pattern Compression** + 突破 |
| L3 L4: 60M consolidation 盤整 | (不同維度) |
| L5: 突破多 | (相近但不同訊號)|
| S1: 夜盤 gap 套利 | (不同時段) |

---

## 2. Alpha 來源論證 — 為什麼能 work

### 2.1 理論依據

**Inside Bar（內包母子線）= 市場決策真空**：

```
母棒 (Mother Bar)  ┌────────┐
範圍較大           │        │  ← Mother High
                   │   ┌─┐  │
                   │   │ │  │  ← Inside Bar 完全被母棒包覆
                   │   └─┘  │
                   │        │  ← Mother Low
                   └────────┘
```

- 母棒範圍大 = 前一日有強烈方向選擇
- 隔日 Inside Bar = **多空雙方僵持**（波動率壓縮）
- 突破方向 = **新一輪方向選擇的開始**

### 2.2 三個 Edge 來源

**Edge 1：波動率壓縮後的爆發效應**
- 經典「Volatility Compression → Volatility Expansion」原理
- Inside Bar 是「壓縮中」的視覺確認
- 突破時通常伴隨成交量放大 → trend follower 集體進場

**Edge 2：母棒範圍提供天然 SL/TP 比例**
- SL = MotherRange × 50%（半個母棒）
- TP = MotherRange × 1.5（一倍半母棒）
- 自適應停損 = **不同波動率時段，停損點數自動調整**
- 避免固定停損在大波動日被甩出，或在小波動日設太遠

**Edge 3：日線 MA 過濾消除逆勢交易**
- 只在 Daily MA(20) 之上做多
- 只在 Daily MA(20) 之下做空
- 過濾掉「逆大方向」的低勝率突破
- 用日線級訊號控制「賺什麼錢」

### 2.3 為什麼 30M Chart + Daily 訊號

**訊號來自日線**（Inside Bar 是日線型態），**進場在 30M**（突破即刻確認）：
- 日線訊號 = 高品質、低頻
- 30M 進場 = 精準度高、滑價低
- 比「等日線收盤確認」少跨 1 天 = 進場更早

### 2.4 為什麼樣本少（34 筆 / 6.4 年）是好事

**Inside Bar 是相對罕見的型態**：
- 一年只發生 5-8 次「乾淨」Inside Bar
- 加上母棒範圍過濾（50-400 點）+ MA 方向過濾後更少
- **樣本少 ≠ 過擬合**，是 alpha 本來就稀少
- 反之，如果一隻策略一年 200 筆 → 大概率在賺噪訊

---

## 3. 進場邏輯詳解

### 3.1 進場條件（4 個 AND 條件）

#### Long（做多）

```powerlanguage
v_IsInsideBar = TRUE              AND   { 1. 樣態確認 }
MotherRange ∈ [50, 400]          AND   { 2. 母棒範圍合理 }
v_MA_Up = TRUE                   AND   { 3. 日線方向過濾 }
Close > MotherHigh + BreakOffset  THEN  { 4. 突破觸發 }
    buy ("LE_IB_Entry") next bar at market
```

#### Short（做空）

```powerlanguage
v_IsInsideBar = TRUE              AND
MotherRange ∈ [50, 400]          AND
v_MA_Down = TRUE                 AND
Close < MotherLow - BreakOffset   THEN
    sell short ("SE_IB_Entry") next bar at market
```

### 3.2 額外 Priority 0 Entry Gate

```powerlanguage
{ 必須通過憲法強制的三道 Gate }
AND v_Holiday_Block = false       { 不在假日前夕進場 }
AND v_Settlement_Day = false      { 不在結算日進場 }
AND v_Registry_Expired = false    { 不在登錄表過期後進場 }
```

### 3.3 進場細節

| Step | 動作 |
|------|------|
| 1 | 每根 30M K 棒檢測 Data2 (Daily) 是否形成 Inside Bar |
| 2 | 若是，記錄 MotherHigh / MotherLow / MotherRange |
| 3 | 過濾母棒範圍（< 50 = 訊號太弱；> 400 = 異常波動）|
| 4 | 檢查 Daily MA(20) 方向 |
| 5 | 等待 30M Close 突破 MotherHigh + 5 點（或跌破 MotherLow - 5 點）|
| 6 | next bar at market 進場 |

---

## 4. 出場邏輯詳解

### 4.1 出場優先序（Priority 0 鏈）

```
P0-1  Manual_Kill_Switch       → IB_Kill           (緊急停市)
P0-2  v_Registry_Expired       → IB_RegistryEnd    (登錄表過期)
P0-3  v_Holiday_Block + 04:15  → IB_HolFlat        (假日前夕)
P0-4  v_Settlement_Day + 12:30 → IB_Settlement     (月結算日)
P0-5  策略原邏輯出場           → IB_SL / IB_TP / IB_Time
```

### 4.2 策略原邏輯出場（P0-5）

| 出場類型 | 觸發條件 | 標籤（多/空）|
|---------|---------|------------|
| **停損** | 跌破 EntryPrice - MotherRange × 50%（最少 40 點）| `LX_IB_SL` / `SX_IB_SL` |
| **停利** | 觸及 EntryPrice ± MotherRange × 1.5 | `LX_IB_TP` / `SX_IB_TP` |
| **時間停損** | 持倉 ≥ 30 根 30M K（15 小時）| `LX_IB_Time` / `SX_IB_Time` |

### 4.3 出場設計哲學

- **單腿出場 + 三種觸發**：不用 Trail，純 Fixed SL + Fixed TP + Time Stop
- **盈虧比 3:1**（TP 1.5 × MotherRange vs SL 0.5 × MotherRange）
- **MinStopPts(40)**：避免母棒太小導致停損過近被噪訊掃出

---

## 5. 適用市況 vs 不適用市況

### 5.1 ✅ 適用市況

| 市況 | 為什麼適用 |
|------|----------|
| **趨勢中波動率壓縮** | Inside Bar 在強勢趨勢中是「短暫整理 → 續勢」訊號 |
| **重大事件後等待方向** | 例如 Fed FOMC、台積電法說後，市場暫時觀望 |
| **盤整末期突破** | 連續多日 Inside Bar 後的方向選擇通常很強勁 |

### 5.2 ❌ 不適用市況

| 市況 | 為什麼不適用 |
|------|------------|
| **極端高波動** | 母棒範圍 > 400 點被過濾（避免假突破撕裂）|
| **無方向盤整** | Daily MA 方向不明 → 無法通過 MA Filter |
| **新聞驅動 gap** | gap up/down 通常不在 Inside Bar 框架內 |
| **結算日當天** | Entry gate 主動阻擋（憲法條款 1）|

### 5.3 預期表現分布

| 市況比例 | 表現 |
|---------|------|
| 適用市況 ~20% | **賺主要利潤**（PF 4.61 來源）|
| 不適用市況 ~60% | **空手**（不開單）|
| 混合市況 ~20% | **小賠或打平**（30M Time Exit 兜底）|

---

## 6. 參數完整說明

### 6.1 策略核心參數（8 個）

| Input | 預設 | 範圍 | 說明 |
|-------|------|------|------|
| `BreakOffset` | 5 | 0-20 | 突破閥值（避免母棒高/低點剛好觸及就觸發）|
| `StopPct` | 50 | 30-70 | 停損 = MotherRange × X% |
| `TargetMult` | 1.5 | 1.0-3.0 | 停利 = MotherRange × X |
| `MinMotherRange` | 50 | 30-80 | 母棒下界（過濾過小波動）|
| `MaxMotherRange` | 400 | 300-600 | 母棒上界（過濾異常波動）|
| `MALen` | 20 | 10-50 | 日線 MA 過濾長度 |
| `MaxBarsHeld` | 30 | 20-50 | 持倉上限（30 × 30M = 15h）|
| `MinStopPts` | 40 | 20-80 | 停損最少點數（避免過近）|

### 6.2 憲法強制防護參數（4 個）

| Input | 預設 | 說明 |
|-------|------|------|
| `Holiday_Flat_Time` | 415 | 04:15 假日前平倉 |
| `Registry_Valid_Until` | 1270101 | 登錄表有效到 2027/01/01 |
| `Manual_Kill_Switch` | false | 緊急停市開關 |
| `Settlement_Flat_Time` | 1230 | 12:30 結算平倉 |

**共 12 個 input，全有 production 預設值**。

### 6.3 參數敏感度預判（待 Phase 3 驗證）

| 參數 | 敏感度預判 | 理由 |
|------|---------|------|
| `BreakOffset` | 🟡 中 | 太小 = 假突破多，太大 = 錯失早期進場 |
| `StopPct` | 🔴 高 | 直接影響單筆風險 / 盈虧比 |
| `TargetMult` | 🟡 中 | 影響 TP 觸及率 |
| `MinMotherRange` | 🟢 低 | 主要篩掉噪訊 |
| `MaxMotherRange` | 🟢 低 | 主要篩掉異常 |
| `MALen` | 🔴 高 | 直接決定「對方向」與否 |
| `MaxBarsHeld` | 🟢 低 | 大多單在到達前已 SL/TP |

---

## 7. 與現有 6 隻策略對比 / 互補關係

### 7.1 對比矩陣

| 策略 | Alpha 來源 | 週期 | 方向 | 持倉 | 相關性預判 |
|------|---------|------|------|------|---------|
| L1 TrendLong | ATR 趨勢突破 | 45M / Daily / Weekly | 多 | 跨日 | 中（同類趨勢但訊號不同）|
| L2 TrendShort | ATR 趨勢突破 | 同上 | 空 | 跨日 | 中（同類趨勢但訊號不同）|
| L3 ConsolidationLong | 區間多 | 15M | 多 | 短 | 低（不同邏輯）|
| L4 ConsolidationShort | 區間空 | 15M | 空 | 短 | 低（不同邏輯）|
| L5 BreakoutLong | 突破多 | 多週期 | 多 | 跨日 | **中高**（相近邏輯！需驗證）|
| S1 NightMomentum | 夜盤 gap | 15M | 多 | 短 | 低（不同時段）|
| **S2 InsideBarBreak** | **Pattern + MA filter** | **30M / Daily** | **雙向** | **跨日** | — |

### 7.2 與 L5 BreakoutLong 的潛在衝突

⚠️ **L5 也是突破多，S2 多單也是突破** —— 可能在同一突破事件雙重進場 → 1 口策略變 2 口曝險。

**Phase 3 必驗證**：
- 計算 L5 vs S2 多單訊號重疊率
- 若重疊 > 30% → 考慮把 S2 改為「只做空」（避免與 L5 雙重曝險，且補足「空頭 pattern alpha」缺口）

### 7.3 戰略價值定位

**S2 在策略組合中的獨特價值**：
- 唯一的「Pattern Trader」（型態驅動 alpha）
- 唯一的「Long + Short 對稱」設計（其他都是單向）
- 低頻 + 高 PF → **降低整體組合相關性，提升 Sharpe**

---

## 8. 風險清單

### 8.1 統計風險

| 風險 | 嚴重性 | 緩解 |
|------|------|------|
| **樣本僅 34 筆** | 🔴 高 | 必須 MC 30M 重跑 + Walk-Forward |
| **PF 4.61 異常高** | 🟡 中 | 可能過擬合，OOS 必須降至少 30% |
| **Python ^TWII 代理 ≠ MC 真實** | 🔴 高 | Phase 2 強制 MC 30M 真實回測 |
| **6.4 年回測涵蓋 COVID + 2024 牛市** | 🟡 中 | 順風期，需驗證 2022 熊市 OOS |

### 8.2 結構性風險

| 風險 | 嚴重性 | 緩解 |
|------|------|------|
| **雙向 alpha 可能不對稱** | 🟡 中 | Phase 3 拆分 Long-only / Short-only 各跑回測 |
| **MA 過濾在橫盤時頻繁切換方向** | 🟢 低 | Inside Bar 本身罕見，已隱含過濾 |
| **與 L5 訊號重疊** | 🟡 中 | Phase 3 計算相關性 |
| **MaxBarsHeld 設定主觀** | 🟢 低 | 統計上應 < 5% 觸發此 exit |

### 8.3 部署風險

| 風險 | 嚴重性 | 緩解 |
|------|------|------|
| **跨日 + 結算日衝突** | ✅ 已解 | 憲法 Settlement_Flat 模組接管 |
| **跨日 + 假日衝突** | ✅ 已解 | HolidayFlat_v3 模組接管 |
| **MC9 vs MC12 差異** | 🟡 中 | Phase 4 上 live_simulation 前測試兩平台 |

---

## 9. Phase 路線圖（從 research 到 live）

### Phase 1 ✅（2026-06-17 完成）
**目標**：符合憲法 v1.2 基本要求

- [x] 從 archive 拉出獨立資料夾
- [x] 加入 Settlement_Flat 7 元素
- [x] 加入 HolidayFlat_v3（63 筆 TAIFEX 登錄表）
- [x] 加入 Manual_Kill_Switch + Registry
- [x] 統一標籤前綴 IB_
- [x] 寫 strategy.md / annotated.md / README.md

### Phase 2 ⏳ — MC 真實回測

**目標**：確認 Python 日線代理 ≈ MC 30M 真實

- [ ] MC12 載入新版 .pla（30M chart + Daily Data2）
- [ ] 跑 2020/01/01 ~ 2026/06/17 完整回測
- [ ] 對比 Python 日線代理 vs MC 30M：
  - PF 是否仍 > 2.0？
  - WR 是否仍 > 50%？
  - 樣本數是否 > 30？
- [ ] 跑 `verify_strategy_holding_classification.py` 確認 Swing-Trend
- [ ] 跑 `analyze_settlement_backtest.py` 看 IB_Settlement 觸發狀況

**通過標準**：MC PF > 2.0 AND 樣本 > 30 → 進 Phase 3；否則回頭重新評估

### Phase 3 ⏳ — P1-P3 標準驗證

**目標**：證明 alpha 真實穩定

- [ ] **Phase 3.1 參數敏感度**：8 個策略參數各掃描，確認都有「高原」非「尖峰」
- [ ] **Phase 3.2 Walk-Forward**：滾動 IS 2 年 / OOS 6 個月，WFE > 50%
- [ ] **Phase 3.3 Monte Carlo**：10,000 次序列重排，95% MDD < 帳戶 30%
- [ ] **Phase 3.4 與 L5 相關性**：訊號重疊率 < 30%
- [ ] **Phase 3.5 雙向對稱性**：Long 子集 PF > 1.5 AND Short 子集 PF > 1.5

**通過標準**：5/5 → 進 Phase 4；任何 fail → 回頭優化

### Phase 4 ⏳ — 晉升 live_simulation

**目標**：模擬實盤至少 30 筆交易

- [ ] 移到 `strategies/live_simulation/S2_InsideBarBreak.pla`
- [ ] 加入 `verify_settlement_flat.py` 與 `verify_all_live.py` 測試清單
- [ ] MC12 模擬帳戶實盤 ≥ 3 個月
- [ ] 模擬 PF ≥ 1.2 AND 回測偏離度 ≤ 30%

**通過標準** → 進 Phase 5（晉升 live）

### Phase 5 ⏳ — 晉升 live

**目標**：真金白銀上架

- [ ] 移到 `strategies/live/S2_InsideBarBreak.pla`
- [ ] 帳戶配置：建議 500K~1M（樣本少 → 起始小額）
- [ ] 加入 master verify 腳本
- [ ] 第一個月密切監控偏離

---

## 10. 績效預期（基於 v0.1 Python 代理）

### 10.1 v0.1 回測數字（Python ^TWII 代理）

| 指標 | 數值 |
|------|------|
| 回測期間 | 2020/01/02 ~ 2026/06/05（6.4 年）|
| 總交易 | 34 |
| 勝率 | 64.7% |
| Profit Factor | **4.61** |
| 淨利 | +791,754 NTD |
| MDD | -63,879 NTD |
| 平均獲利 | +45,957 NTD |
| 平均虧損 | -18,275 NTD |
| 盈虧比 | 2.51 |
| CAGR | 27.0% |

### 10.2 Phase 2 後的預期（MC 30M 真實回測）

**保守預期（基於以往 Python → MC 差距經驗）**：
- 樣本可能增加到 50-80 筆（因為 30M 比日線觸發點更多）
- PF 預期降至 1.5 - 2.5（從 4.61）
- WR 預期降至 45 - 55%
- 但**淨利可能上升**（樣本變多）
- MDD 可能上升到 -150,000 ~ -250,000

**通過標準**：PF > 2.0 + 樣本 > 30 → 維持研究路線

### 10.3 最終 live 預期（如通過所有 Phase）

| 指標 | 預期區間 |
|------|--------|
| 年化交易筆數 | 15-25 筆 |
| 年化淨利 | +100k ~ +250k |
| 年化 MDD | 帳戶 8-15% |
| Profit Factor | 1.6 - 2.2 |
| 與組合相關性 | < 0.4 |

**戰略價值**：補足「Pattern Trader」缺口，提升整體 Sharpe ratio。

---

## 11. 相關文件

- [中文逐段註解](S2_InsideBarBreak_annotated.md)
- [README reactivation 緣由](README.md)
- [原 v0.1 archive 版本](../archive/batch01_S2-S5/S2_InsideBarBreak.pla)
- [batch01 績效總覽](../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md)
- [憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [策略分類決策矩陣](../../../docs/strategy_classification_decision_matrix.svg)
