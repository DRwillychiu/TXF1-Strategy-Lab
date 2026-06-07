# S1 NightMomentum v2.0 ATR — 中文逐行註解

> 對應程式碼：`S1_NightMomentum.pla`（MC12 直接使用的全英文版）
> 最後更新：2026-06-07
> 版本：v2.0 ATR-Based（全面移除固定點數）
> 參數來源：MC12 GA 最佳化 → 待 MC12 WFA 驗證

---

## 策略概述
- **類別**：A 類（時段型）
- **方向**：★純做多（MC12 分析：空單 PF=0.93，淨利-618,600，已移除）
- **週期**：15 分鐘
- **核心邏輯**：夜盤開盤前 N 根 K 棒形成「開盤區間」，突破高點做多
- **v2.0 重點**：所有進出場判斷改用 ATR 倍數，適應各種指數位階

---

## v1.0 vs v2.0 對照表

| v1.0 參數（固定點數） | v2.0 參數（ATR 倍數） | 轉換邏輯（ATR~60pt 時等效） |
|----------------------|---------------------|--------------------------|
| EntryOffset = 6 pts | EntryATRMult = 0.1 | 60 * 0.1 = 6 pts |
| MinRange = 30 pts | RangeMinATR = 0.5 | 60 * 0.5 = 30 pts |
| MaxRange = 200 pts | RangeMaxATR = 3.5 | 60 * 3.5 = 210 pts |
| StopLossPts = 80 pts | StopATRMult = 1.5 | 60 * 1.5 = 90 pts |
| TakeProfitPts = 160 pts | TargetATRMult = 3.0 | 60 * 3.0 = 180 pts |
| TrailActivate = 50 pts | TrailActATR = 1.0 | 60 * 1.0 = 60 pts |
| TrailOffset = 30 pts | TrailOffATR = 0.5 | 60 * 0.5 = 30 pts |
| SetStopLoss() | 手動 stop 單 (LX_NM_SL) | v_EntryATR 凍結機制 |
| SetProfitTarget() | 手動 limit 單 (LX_NM_TP) | v_EntryATR 凍結機制 |

**為什麼 ATR 化？** 加權指數 15,000 和 22,000 的 80 點停損分別是 0.53% 和 0.36%，風險完全不同。ATR 倍數自動適應波動率，確保每筆交易承擔相同比例的風險。

---

## 參數說明

| 參數 | 預設值 | GA 最佳 | 說明 |
|------|--------|--------|------|
| `LookbackBars` | 6 | 10 | 夜盤開盤後幾根 K 棒形成區間 |
| `ATRLen` | 14 | 13 | ATR 計算週期（根數） |
| `EntryATRMult` | 0.1 | 0.3 | 突破偏移 = ATR * 此值（過濾假突破） |
| `RangeMinATR` | 0.5 | 0.2 | 區間寬度最低門檻（ATR 倍數） |
| `RangeMaxATR` | 3.5 | 4.0 | 區間寬度最高門檻（ATR 倍數） |
| `StopATRMult` | 1.5 | 2.75 | 停損 = EntryPrice - v_EntryATR * 此值 |
| `TargetATRMult` | 3.0 | 3.0 | 停利 = EntryPrice + v_EntryATR * 此值 |
| `TrailActATR` | 1.0 | 2.5 | 獲利達 v_EntryATR * 此值 後啟動追蹤停損 |
| `TrailOffATR` | 0.5 | 0.5 | 追蹤停損回撤容忍（ATR 倍數） |
| `NightOpen` | 1500 | 1500 | 夜盤開盤時間（固定） |
| `ExitTime` | 0500 | 500 | 強制平倉時間（GA: 05:00） |

---

## 逐段邏輯註解

### 1. ATR 計算
```
v_ATR = AvgTrueRange(ATRLen);
```
- MC12 內建函數，計算最近 ATRLen 根 K 棒的平均真實波幅
- 每根 bar 都更新，但進場後用 v_EntryATR 凍結

### 2. 偵測夜盤時段
```
v_IsNightSession = (Time >= NightOpen) or (Time < ExitTime);
```
- 15:00 以後 **或** 05:00 以前 → 判定為夜盤

### 3. 夜盤開盤重置
```
if Time >= NightOpen and Time[1] < NightOpen then begin
    v_NightHigh = 0; v_NightLow = 999999;
    v_NightBarCount = 0; v_RangeReady = false;
end;
```
- 當時間跨過 15:00 → 重置所有變數，準備計算新的開盤區間

### 4. 建構開盤區間（ATR 化過濾）
```
if v_NightBarCount >= LookbackBars then begin
    v_RangeWidth = v_NightHigh - v_NightLow;
    if v_ATR > 0 and
       v_RangeWidth >= v_ATR * RangeMinATR and
       v_RangeWidth <= v_ATR * RangeMaxATR then
        v_RangeReady = true;
end;
```
- 逐根累計最高/最低價，滿 N 根後計算區間寬度
- **v2.0 改動**：區間過濾用 ATR 倍數（不再是固定 30/200 點）
- ATR=60 時：最窄 0.2*60=12pt，最寬 4.0*60=240pt

### 5. 進場：區間突破（Long Only）
```
buy ("LE_NM_Long") next bar at v_NightHigh + v_ATR * EntryATRMult stop;
```
- **v2.0 改動**：偏移量用 ATR 倍數（不再是固定 6 點）
- 僅做多，已移除 sell short

### 6. ATR 凍結機制
```
if MarketPosition = 1 and v_Prev_MP <= 0 then
    v_EntryATR = v_ATR;
```
- ★ 進場瞬間凍結 ATR → 持倉期間停損/停利不會因 ATR 變動而飄移
- 避免高波動時 ATR 突然擴大導致停損被拉遠

### 7. 出場：ATR 停損
```
sell ("LX_NM_SL") next bar at EntryPrice - v_EntryATR * StopATRMult stop;
```
- **v2.0 改動**：取代 SetStopLoss()，用手動 stop 單 + 有標籤
- GA 最佳：2.75 倍 ATR 停損

### 8. 出場：ATR 停利
```
sell ("LX_NM_TP") next bar at EntryPrice + v_EntryATR * TargetATRMult limit;
```
- **v2.0 改動**：取代 SetProfitTarget()，用手動 limit 單 + 有標籤
- GA 最佳：3.0 倍 ATR 停利

### 9. 出場：ATR 追蹤停損
```
if MaxContractProfit / 200 >= v_EntryATR * TrailActATR then
    sell ("LX_NM_Trail") next bar at EntryPrice + v_EntryATR * (TrailActATR - TrailOffATR) stop;
```
- 獲利達 TrailActATR 倍 ATR 後，在 (TrailActATR - TrailOffATR) 倍 ATR 處設停損
- GA 最佳：獲利達 2.5 倍 ATR 後，鎖定 2.0 倍 ATR 利潤（2.5-0.5=2.0）

### 10. 出場：時間平倉
```
if Time >= ExitTime and Time < NightOpen then begin
    if MarketPosition = 1 then sell ("LX_NM_Time") next bar at market;
end;
```
- GA 最佳 ExitTime=500（05:00），比預設 0430 晚 30 分鐘

---

## 進出場標籤對照表

| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_NM_Long` | `buy` | 做多 | 進場 | 突破區間高點 + ATR 偏移 |
| `LX_NM_SL` | `sell` | 做多 | 出場 | ATR 停損 |
| `LX_NM_TP` | `sell` | 做多 | 出場 | ATR 停利 |
| `LX_NM_Trail` | `sell` | 做多 | 出場 | ATR 追蹤停損 |
| `LX_NM_Time` | `sell` | 做多 | 出場 | 時間平倉 |

> **規則**：`LE_` = Long Entry、`LX_` = Long eXit
> v2.0 純做多，無 SE_/SX_ 標籤

---

## MC12 v2.0 GA 最佳化結果

| 指標 | v1.0 固定點數 | v2.0 ATR | 改善 |
|------|-------------|----------|------|
| 淨利 | +1,159,600 | +1,597,400 | +37.7% |
| PF | 1.171 | 1.292 | +10.3% |
| MDD | -634,600 | -318,000 | -49.8% |
| 勝率 | 54.97% | 54.27% | -0.7% |
| 交易次數 | 803 | 482 | -40.0% |

GA 最佳參數：
```
LookbackBars=10, ATRLen=13, EntryATRMult=0.3,
RangeMinATR=0.2, RangeMaxATR=4.0,
StopATRMult=2.75, TargetATRMult=3.0,
TrailActATR=2.5, TrailOffATR=0.5,
NightOpen=1500, ExitTime=500
```

---

## MC12 Walk-Forward Analysis 設定卡（★ 完整版 ★）

### 一、回測基本設定

| 項目 | 設定 |
|------|------|
| **商品** | TXF1（台指期近月連續） |
| **操作週期** | **15 分鐘**（★ 必須用操作週期） |
| **回測區間** | **2020/01/01 ~ 2026/06/07** |
| **合約乘數** | 200 NTD/點 |
| **滑價** | 單邊 500 NTD（來回 1,000 NTD） |
| **口數** | 1 口固定 |
| **初始資金** | 500,000 NTD |

### 二、WFA 窗口設定

| 項目 | 設定 |
|------|------|
| **IS（樣本內）** | 24 個月 |
| **OOS（樣本外）** | 6 個月 |
| **IS:OOS 比例** | **4:1**（IS 佔總窗口 80%） |
| **步長** | 6 個月（= OOS 長度） |
| **WF 類型** | Rolling（滾動） |
| **窗口數** | **9 個** |
| **最佳化目標** | Net Profit 最大化 |
| **合格標準** | OOS PF > 1.0 且 OOS 淨利 > 0 |

### 三、完整參數最佳化範圍（★ 全部列出 ★）

| # | 參數 | Start | End | Step | 組合數 | GA最佳 | 說明 |
|---|------|-------|-----|------|--------|--------|------|
| 1 | LookbackBars | 2 | 12 | 1 | 11 | 10 | 開盤區間觀察根數 |
| 2 | ATRLen | 5 | 21 | 1 | 17 | 13 | ATR 計算週期 |
| 3 | EntryATRMult | 0.00 | 0.50 | 0.05 | 11 | 0.30 | 突破偏移（ATR倍數） |
| 4 | RangeMinATR | 0.1 | 1.0 | 0.1 | 10 | 0.2 | 區間最窄門檻（ATR倍數） |
| 5 | RangeMaxATR | 2.0 | 5.0 | 0.5 | 7 | 4.0 | 區間最寬門檻（ATR倍數） |
| 6 | StopATRMult | 0.50 | 3.00 | 0.25 | 11 | 2.75 | 停損（ATR倍數） |
| 7 | TargetATRMult | 1.0 | 5.0 | 0.5 | 9 | 3.0 | 停利（ATR倍數） |
| 8 | TrailActATR | 0.50 | 3.00 | 0.25 | 11 | 2.50 | 追蹤停損啟動（ATR倍數） |
| 9 | TrailOffATR | 0.1 | 1.5 | 0.1 | 15 | 0.5 | 追蹤停損回撤（ATR倍數） |
| — | NightOpen | 1500 | — | — | **固定** | 1500 | 夜盤開盤時間 |
| 10 | ExitTime | 400 | 530 | 30 | 5 | 500 | 強制平倉時間 |

**全暴力掃描組合數**：11 x 17 x 11 x 10 x 7 x 11 x 9 x 11 x 15 x 5 = **~11,760,383,250**（~117.6 億，暴力不可行）

### 四、GA 設定（每個 WFA 窗口）

| 設定項目 | 值 | 說明 |
|---------|-----|------|
| **最佳化依據** | Net Profit | 淨利最大化 |
| **演算法** | 基因演算法（GA） | 117.6 億組合暴力不可行 |
| **族群規模** | 500 | 每窗口獨立 GA |
| **最大代數** | 400 | 每窗口 200,000 次評估 |
| **突變機率** | 0.08 | 10 個可變參數，偏高突變防局部最優 |
| **交配機率** | 0.90 | |
| **演算法類型** | Incremental（增加的） | |
| **更換方案** | 最差 | 淘汰最差個體 |

**預估總計**：200,000 次/窗口 x 9 窗口 = ~1,800,000 次回測

### 五、逐窗口 IS/OOS 日期配置表

| 窗口 | IS 起始 | IS 結束 | IS 期間 | OOS 起始 | OOS 結束 | OOS 期間 |
|------|---------|---------|---------|----------|----------|----------|
| **W1** | 2020/01/01 | 2021/12/31 | 24 個月 | 2022/01/01 | 2022/06/30 | 6 個月 |
| **W2** | 2020/07/01 | 2022/06/30 | 24 個月 | 2022/07/01 | 2022/12/31 | 6 個月 |
| **W3** | 2021/01/01 | 2022/12/31 | 24 個月 | 2023/01/01 | 2023/06/30 | 6 個月 |
| **W4** | 2021/07/01 | 2023/06/30 | 24 個月 | 2023/07/01 | 2023/12/31 | 6 個月 |
| **W5** | 2022/01/01 | 2023/12/31 | 24 個月 | 2024/01/01 | 2024/06/30 | 6 個月 |
| **W6** | 2022/07/01 | 2024/06/30 | 24 個月 | 2024/07/01 | 2024/12/31 | 6 個月 |
| **W7** | 2023/01/01 | 2024/12/31 | 24 個月 | 2025/01/01 | 2025/06/30 | 6 個月 |
| **W8** | 2023/07/01 | 2025/06/30 | 24 個月 | 2025/07/01 | 2025/12/31 | 6 個月 |
| **W9** | 2024/01/01 | 2025/12/31 | 24 個月 | 2026/01/01 | 2026/06/07 | ~5 個月 |

> W9 OOS 略短（~5 個月），因數據截止 2026/06/07。

### 六、WFA 判定標準

| 指標 | 門檻 | 說明 |
|------|------|------|
| **WFE** | >= 50% | OOS 獲利窗口佔比 |
| **每窗口 OOS PF** | > 1.0 | 樣本外必須獲利 |
| **累計 OOS 淨利** | > 0 | 所有窗口 OOS 合計正值 |
| **參數收斂** | 目視檢查 | 各窗口最佳參數應趨向穩定區域 |

---

## 版本歷史

| 版本 | 日期 | 變動 |
|------|------|------|
| v1.0 | 2026-06-07 | 初版，固定點數進出場 |
| v1.1 | 2026-06-07 | MC12 分析移除空單（Short PF=0.93），改純做多 |
| v2.0 | 2026-06-07 | ★ 全面 ATR 化：6 個固定點數參數改 ATR 倍數，加 v_EntryATR 凍結機制 |
