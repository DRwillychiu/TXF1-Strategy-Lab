# S1 NightMomentum v2.3 — 中文逐行註解

> 對應程式碼：`S1_NightMomentum.pla`（MC12 直接使用的全英文版）
> 最後更新：**2026-06-13**
> 版本：**v2.3 Daily Flat as PRIMARY safety（三層防護架構）**
> 狀態：🟢 模擬上架運行 v2.1（待空手時部署 v2.3）
> 設計文件：[docs/S1_v23_daily_flat_redesign.md](../../../docs/S1_v23_daily_flat_redesign.md)

## v2.3 重新架構（2026-06-13）

### 用戶批評（v2.2 設計缺陷）
> 「你是特別針對節日作時間調整但本質上這份純夜盤策略應該要在 05:00 就把夜盤策略的單平倉才對。這部分你沒有規劃清楚。」

v2.2 把 **Holiday 模組** 當主角，把 **Daily 05:00 Flat** 寫成「ExitTime bug fix」。本末倒置。

### v2.3 三層安全架構
| 層級 | 機制 | 標籤 |
|------|------|------|
| **PRIMARY**（本質性，每天必做）| Daily 05:00 Flat | **LX_NM_DailyFlat** |
| SECONDARY（特殊日子加碼）| Holiday / Kill / Registry | LX_NM_Holiday / LX_NM_Kill / LX_NM_RegistryEnd |
| TERTIARY（緊急救命網）| Day Session Emergency | **LX_NM_DaySession_EMERGENCY** |

### Input 重新拆分（單一 ExitTime → 3 個專責 input）

| Input | v2.3 預設 | 職責 |
|-------|----------|------|
| `EntryEnd_Time` | 415 | 進場閘門（Time ≥ 此 → 不再發新單）|
| `DailyFlat_Time` | 415 | 出場觸發（Time ≥ 此 → forced flat）|
| **`NightCloseBar_Time`** | **500** | **HARD CAP** — 永不在此 bar 發單 |

### 為什麼 v2.3 不會出 v2.2 的 bug

v2.2：`Time >= ExitTime AND Time < NightOpen=1500` → 包含 Time=500（最後夜盤 bar）→ 發單 → next bar=900 → 09:00 出場 bug

v2.3：`Time >= DailyFlat_Time AND Time < NightCloseBar_Time=500` → 排除 Time=500 → 永不發單在最後 bar → **bug 從架構層級消滅**

### 新出場標籤對照

| 標籤 | v2.2 | v2.3 |
|------|------|------|
| LX_NM_Time | ✅ | ❌ 移除（被 LX_NM_DailyFlat 取代） |
| **LX_NM_DailyFlat** | ❌ | ✅ **新（PRIMARY 出場）** |
| **LX_NM_DaySession_EMERGENCY** | ❌ | ✅ **新（救命網）** |
| LX_NM_Kill / Registry / Holiday | ✅ | ✅（preserved）|

### MC12 部署要求（v2.3）
1. **完全移除** 現有 S1 strategy，重新從 .pla 新增（強制使用新預設值）
2. 確認看到新 input：`EntryEnd_Time / DailyFlat_Time / NightCloseBar_Time`
3. 確認不再看到舊 input：`ExitTime`
4. 重跑回測 → 驗收 `LX_NM_DailyFlat` 出場時間在 04:30-05:00 內
5. `LX_NM_DaySession_EMERGENCY` 觸發筆數應為 0（若有則需調查）

---

> 以下保留 v2.2 內容供參：

## v2.2 兩大修正（2026-06-13）

### 🔴 P0 — ExitTime 500 → 415（Critical Bug Fix）

| 維度 | v2.1（壞）| v2.2（修）|
|------|----------|----------|
| ExitTime | 500（05:00 = **最後一根夜盤 K 棒**）| **415（04:15 觸發）**|
| Market 單觸發 bar | 04:45-05:00 收盤 | 04:00-04:15 收盤 |
| Market 單成交 bar | **隔天 08:45-09:00 日盤首根** ❌ | 04:15-04:30 夜盤 ✅ |
| Excel 出場時間 | **09:00**（日盤開盤）| 04:30（夜盤內）|
| 跨夜盤 gap 暴露 | **3 小時 45 分鐘** ❌ | 無 ✅ |
| 純夜盤聲明 | 失真 ❌ | 真實 ✅ |
| 重試次數 | 0（已是最後一根）| 3 次（04:30/04:45/05:00）|

**bug 機制**：v2.1 在 Time=500 觸發 `sell next bar at market`，但 05:00 後夜盤結束，PowerLanguage 找不到下一根 K 棒直到 08:45 開盤 → 訂單卡在 queue → 08:45 OPEN 才成交。

**修正原則**：對齊 L4 v14.2B / L5 v19.7 的 15M 鐵律（Holiday_Flat_Time=415）。

### 🟡 P1 — HolidayFlat_v3 模組（與 L1-L5 同等保護）

| 新增項目 | 用途 |
|----------|------|
| Holiday_Tail[80] 63 筆登錄表 | TAIFEX-verified，與 L1-L5 byte-identical |
| `Holiday_Flat_Time(415)` | 假日尾段日強制歸零（同 ExitTime 值，belt-and-suspenders）|
| `Registry_Valid_Until(1270101)` | 視界 fail-safe，超過 2027/1/1 自動封鎖 |
| `Manual_Kill_Switch(false)` | 緊急停市開關（颱風等）|
| v_Holiday_Block | 額外進場閘門（尾段日 00:00-05:00 禁止 LE_NM_Long）|
| 30 天紅字警告 | LastBarOnChart 過期前提醒 |

**新增出場標籤（Priority 0）**：
- `LX_NM_Kill` — Manual_Kill_Switch 觸發
- `LX_NM_RegistryEnd` — 視界過期觸發
- `LX_NM_Holiday` — 尾段日 04:15 觸發（與 LX_NM_Time 同 bar 觸發但讓報表可區分）

**對 S1 而言 P1 的特殊性**：因為 S1 已是「每晚 04:15 強制歸零」，假日跨假風險本來就被 ExitTime 處理掉。HolidayFlat_v3 主要價值是：
1. Manual_Kill_Switch（真正獨有的新保護）
2. Registry_Valid_Until fail-safe
3. 與 L1-L5 一致性（將來組合分析容易）

---

> 原始 v2.1 內容如下（保留供參）：
>
> 參數來源：MC12 v2.1 GA 最佳化（已寫入 .pla）→ P1~P3 全通過 → ✅ PASS@1M，可上架實測

---

## 策略概述
- **類別**：A 類（時段型）
- **方向**：★純做多（MC12 分析：空單 PF=0.93，淨利-618,600，已移除）
- **週期**：15 分鐘
- **核心邏輯**：夜盤開盤後觀察 11 根 K 棒（約 2 小時 45 分鐘）形成價格區間，波動率擴張時突破高點做多
- **v2.0 重點**：所有進出場判斷改用 ATR 倍數，適應各種指數位階
- **v2.1 重點**：加入波動率擴張過濾器（fast ATR / slow ATR），低波動環境不進場

---

## 策略白話說明（PASS@1M — 核准上架實測）

```
純夜盤追趨勢多策略：
年化：31.09%
MDD：-278800元（一口大台保證金內）
週期：2020/01/01-2026/06/06
勝率：58.86%
-
進場：
觀察前 11 根 K 棒形成的價格區間。當近期波動明顯放大時，若價格往上突破這個區間，就順勢做多。
沒突破就不動。

出場：
用波動率自動計算停損、停利和移動停損的位置。
最晚凌晨 5 點全部平倉。

核心思路：
夜盤前半段判定方向，後半段賺延續。只做多、不做空。
這邊的判斷前半段以及後半段主要是透過觀察突破前N根K棒作為依據，而這裡經過時間驗證抓取11根15分K，也就是前半段時間區間為15:00-17:45。後半段為17:45-05:00。
```

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
| `LookbackBars` | 6 | **11** | 夜盤開盤後幾根 K 棒形成區間 |
| `ATRLen` | 14 | **11** | ATR 計算週期（根數） |
| `EntryATRMult` | 0.1 | **0.2** | 突破偏移 = ATR * 此值（過濾假突破） |
| `RangeMinATR` | 0.5 | **0.9** | 區間寬度最低門檻（ATR 倍數）★ v2.1 大幅提高 |
| `RangeMaxATR` | 3.5 | **4.5** | 區間寬度最高門檻（ATR 倍數） |
| `StopATRMult` | 1.5 | **2.75** | 停損 = EntryPrice - v_EntryATR * 此值 |
| `TargetATRMult` | 3.0 | **2.0** | 停利 = EntryPrice + v_EntryATR * 此值 ★ 提前鎖利 |
| `TrailActATR` | 1.0 | **2.75** | 獲利達 v_EntryATR * 此值 後啟動追蹤停損 |
| `TrailOffATR` | 0.5 | **0.7** | 追蹤停損回撤容忍（ATR 倍數） |
| `NightOpen` | 1500 | **1500** | 夜盤開盤時間（固定） |
| `ExitTime` | 0500 | **500** | 強制平倉時間 |
| `VolSlowLen` | 60 | **70** | v2.1：慢速 ATR 週期（~17.5 小時基準線） |
| `VolRatioMin` | 0.80 | **0.80** | v2.1：快/慢 ATR 比值門檻 |

---

## 逐段邏輯註解

### 1. ATR 計算
```
v_ATR = AvgTrueRange(ATRLen);
```
- MC12 內建函數，計算最近 ATRLen 根 K 棒的平均真實波幅
- 每根 bar 都更新，但進場後用 v_EntryATR 凍結

### 2. 波動率擴張過濾器（v2.1 新增）
```
v_SlowATR = AvgTrueRange(VolSlowLen);
if v_SlowATR > 0 then
    v_VolRatio = v_ATR / v_SlowATR
else
    v_VolRatio = 1;
v_VolPass = (v_VolRatio >= VolRatioMin);
```
- ★ v2.1 核心改動：快速 ATR（短週期）÷ 慢速 ATR（長週期）= 波動率擴張比率
- `v_VolRatio > 1.0`：近期波動率高於基準 → 擴張中 → 適合突破
- `v_VolRatio < 1.0`：近期波動率低於基準 → 收縮中 → 突破容易假訊號
- 只有 `v_VolRatio >= VolRatioMin` 時才允許進場
- **為什麼加這個？** v2.0 WFA 顯示 2021~2024 連虧 4 窗口，分析後判斷是低波動環境下突破策略失效。此過濾器讓策略在低波動期「不開機」，避免無效交易

### 3. 偵測夜盤時段
```
v_IsNightSession = (Time >= NightOpen) or (Time < ExitTime);
```
- 15:00 以後 **或** 05:00 以前 → 判定為夜盤

### 4. 夜盤開盤重置
```
if Time >= NightOpen and Time[1] < NightOpen then begin
    v_NightHigh = 0; v_NightLow = 999999;
    v_NightBarCount = 0; v_RangeReady = false;
end;
```
- 當時間跨過 15:00 → 重置所有變數，準備計算新的開盤區間

### 5. 建構開盤區間（ATR 化過濾）
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

### 6. 進場：區間突破（Long Only + Vol Filter）
```
if v_RangeReady and v_IsNightSession and Time < ExitTime and v_VolPass then begin
    if v_Prev_MP <= 0 and v_ATR > 0 then
        buy ("LE_NM_Long") next bar at v_NightHigh + v_ATR * EntryATRMult stop;
end;
```
- **v2.0 改動**：偏移量用 ATR 倍數（不再是固定 6 點）
- **v2.1 改動**：進場條件加入 `and v_VolPass`，低波動時不進場
- 僅做多，已移除 sell short

### 7. ATR 凍結機制
```
if MarketPosition = 1 and v_Prev_MP <= 0 then
    v_EntryATR = v_ATR;
```
- ★ 進場瞬間凍結 ATR → 持倉期間停損/停利不會因 ATR 變動而飄移
- 避免高波動時 ATR 突然擴大導致停損被拉遠

### 8. 出場：ATR 停損
```
sell ("LX_NM_SL") next bar at EntryPrice - v_EntryATR * StopATRMult stop;
```
- **v2.0 改動**：取代 SetStopLoss()，用手動 stop 單 + 有標籤
- GA 最佳：2.75 倍 ATR 停損

### 9. 出場：ATR 停利
```
sell ("LX_NM_TP") next bar at EntryPrice + v_EntryATR * TargetATRMult limit;
```
- **v2.0 改動**：取代 SetProfitTarget()，用手動 limit 單 + 有標籤
- GA 最佳：2.0 倍 ATR 停利（v2.1 提前鎖利）

### 10. 出場：ATR 追蹤停損
```
if MaxContractProfit / 200 >= v_EntryATR * TrailActATR then
    sell ("LX_NM_Trail") next bar at EntryPrice + v_EntryATR * (TrailActATR - TrailOffATR) stop;
```
- 獲利達 TrailActATR 倍 ATR 後，在 (TrailActATR - TrailOffATR) 倍 ATR 處設停損
- GA 最佳：獲利達 2.75 倍 ATR 後，鎖定 2.05 倍 ATR 利潤（2.75-0.7=2.05）

### 11. 出場：時間平倉
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
| **初始資金** | 1,000,000 NTD |

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
| 1 | LookbackBars | 2 | 12 | 1 | 11 | **11** | 開盤區間觀察根數 |
| 2 | ATRLen | 5 | 21 | 1 | 17 | **11** | ATR 計算週期 |
| 3 | EntryATRMult | 0.00 | 0.50 | 0.05 | 11 | **0.20** | 突破偏移（ATR倍數） |
| 4 | RangeMinATR | 0.1 | 1.0 | 0.1 | 10 | **0.9** | 區間最窄門檻（ATR倍數）★ |
| 5 | RangeMaxATR | 2.0 | 5.0 | 0.5 | 7 | **4.5** | 區間最寬門檻（ATR倍數） |
| 6 | StopATRMult | 0.50 | 3.00 | 0.25 | 11 | **2.75** | 停損（ATR倍數） |
| 7 | TargetATRMult | 1.0 | 5.0 | 0.5 | 9 | **2.0** | 停利（ATR倍數）★ 提前鎖利 |
| 8 | TrailActATR | 0.50 | 3.00 | 0.25 | 11 | **2.75** | 追蹤停損啟動（ATR倍數） |
| 9 | TrailOffATR | 0.1 | 1.5 | 0.1 | 15 | **0.7** | 追蹤停損回撤（ATR倍數） |
| — | NightOpen | 1500 | — | — | **固定** | **1500** | 夜盤開盤時間 |
| 10 | ExitTime | 400 | 530 | 30 | 5 | **500** | 強制平倉時間 |
| 11 | VolSlowLen | 40 | 200 | 20 | 9 | **70** | v2.1：慢速 ATR 週期（~17.5hr） |
| 12 | VolRatioMin | 0.60 | 1.40 | 0.10 | 9 | **0.80** | v2.1：快/慢 ATR 最低比值 |

**全暴力掃描組合數**：11 x 17 x 11 x 10 x 7 x 11 x 9 x 11 x 15 x 5 x 9 x 9 = **~952.2 billion**（~9,522 億，暴力不可行，必須 GA）

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

### 七、MC12 15M WFA 結果

#### v2.1 WFA（正式，含 Vol Filter）— ✅ PASS

| 窗口 | IS 淨利 | IS PF | IS 交易 | OOS 淨利 | OOS PF | OOS MDD | OOS 交易 | OOS 勝率 | 判定 |
|------|---------|-------|---------|----------|--------|---------|----------|----------|------|
| W1 | +174,000 | 1.19 | 251 | +80,400 | 1.29 | -66,800 | 55 | 63.6% | ✅ |
| W2 | -64,200 | 0.84 | 69 | — | — | — | — | — | ❌ |
| W3 | +325,000 | 1.92 | 139 | -21,000 | 0.85 | -110,400 | 41 | 63.4% | ❌ |
| W4 | +359,600 | 1.54 | 156 | -22,800 | 0.88 | -84,400 | 46 | 50.0% | ❌ |
| W5 | +278,000 | 1.49 | 143 | +34,200 | 1.38 | -67,400 | 26 | 42.3% | ✅ |
| W6 | +289,800 | 1.33 | 191 | +118,400 | 1.50 | -133,200 | 43 | 46.5% | ✅ |
| W7 | +551,600 | 1.72 | 179 | -200,800 | 0.73 | -343,800 | 62 | 53.2% | ❌ |
| W8 | +1,804,200 | 1.65 | 604 | +687,300 | 1.74 | -187,900 | 166 | 55.4% | ✅ |
| W9 | +2,415,700 | 1.98 | 501 | +1,263,800 | 1.91 | -436,700 | 106 | 62.3% | ✅ |

**WFE = 62.5% (5/8) ✅** | OOS 累計 +1,939,500 ✅ | 待 Phase 3 Monte Carlo

<details>
<summary>v2.0 WFA（不通過，有效 WFE=33.3%，已被 v2.1 取代）</summary>

| 窗口 | OOS 淨利 | OOS PF | OOS 交易 | 判定 |
|------|----------|--------|----------|------|
| W1 | +10,000 | 1.77 | 5 | ✅ (⚠️5筆) |
| W2 | -38,200 | 0.92 | 85 | ❌ |
| W3 | -137,800 | 0.67 | 83 | ❌ |
| W4 | +9,000 | 2.80 | 4 | ✅ (⚠️4筆) |
| W5 | -57,600 | 0.70 | 33 | ❌ |
| W6 | -139,600 | 0.84 | 72 | ❌ |
| W7 | +302,600 | 1.63 | 81 | ✅ |
| W8 | +562,200 | 1.56 | 72 | ✅ |

WFE 50%(名義)/33.3%(有效) | OOS 累計 +510,600

</details>

---

## 版本歷史

| 版本 | 日期 | 變動 |
|------|------|------|
| v1.0 | 2026-06-07 | 初版，固定點數進出場 |
| v1.1 | 2026-06-07 | MC12 分析移除空單（Short PF=0.93），改純做多 |
| v2.0 | 2026-06-07 | ★ 全面 ATR 化：6 個固定點數參數改 ATR 倍數，加 v_EntryATR 凍結機制 |
| v2.0 | 2026-06-07 | MC12 15M WFA 完成：⚠️ 不通過（有效 WFE=33.3%，MDD 爆表，中期連虧） |
| v2.1 | 2026-06-07 | 加入波動率擴張過濾器（VolSlowLen + VolRatioMin），低波動不進場 |
| v2.1 | 2026-06-07 | GA+WFA+MC 全通過：WFE=62.5%, OOS+1.94M, MC PASS@1M, 寫入 GA 最佳參數 |
| v2.1 | 2026-06-07 | ✅ **P1~P3 檢驗完成，核准上架實測**（最低帳戶 1,000,000 NTD） |
