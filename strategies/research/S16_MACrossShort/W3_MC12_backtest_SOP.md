# S16_S W3 MC12 Backtest SOP (2026-07-08)

**目的**：用真實 TXF1 5M 資料執行 baseline backtest，取得 xlsx 給 Claude 做 W3 分析。

**前置**：`S16_S_MACrossShort.pla` v0.1-DRAFT（W2）已 ASCII PASS。

---

## 一、部署 6 步驟

### Step 1 — Load .pla 到 MC12
1. 開啟 MultiCharts 12
2. `File → Import → PowerLanguage Script`
3. 選 `strategies/research/S16_MACrossShort/S16_S_MACrossShort.pla`
4. Signal Name 確認：`S16_S_MACrossShort`

### Step 2 — 建立圖表
1. `File → New → Chart Window`
2. Symbol: **TXF1**（近月連續）
3. Resolution: **5 Minutes**
4. Session: **含日盤 + 夜盤**（08:45-05:00 全時段）
5. History 至少 6 個月（建議 2020-01 開始拉全 backtest 期間）
6. Bars back requirement: **≥ 200**

### Step 3 — Apply Strategy
1. 右鍵圖表 → `Insert Study → Signal`
2. 選 `S16_S_MACrossShort`
3. **IntrabarOrderGeneration 已在 code 內鎖 False**

### Step 4 — Format Signal 檢查 Inputs
確認以下數值（**W2 default，不要動**）：

**Group A - Entry (ZLEMA)**
```
ZLEMA_Fast              = 8
ZLEMA_Slow              = 25
MinSlope                = 1.0
```

**Group B - M5 Quick Stop**
```
QuickStop_On            = True
QuickStop_MaxBars       = 6
QuickStop_MaxLoss_Pts   = 15
```

**Group C - M6 Multi-Layer**
```
ML_On                   = True
ML_ActivationPct        = 20
ML_ScoreTrigger         = 65
ML_MinCategories        = 3
ML_VolAvgLen            = 15
ML_VolSpikeMult         = 2.0
ML_MA_ShortLen          = 10
ML_ATR_ShortLen         = 3
ML_ATR_LongLen          = 90
ML_ATR_Ratio            = 2.5
```

**Group D - M7 Breakeven Trail**
```
BE_On                   = True
BE_Trigger_ATR          = 1.0
BE_Buffer_Pts           = 5
BE_Tier2_ATR            = 1.5
BE_Tier2_Buffer_Pts     = 10
```

**Group E - M8 Time Stop**
```
M8_On                   = True
MaxHoldingBars          = 48
```

**Group F - ATR SL**
```
ATR_Len                 = 14
StopATRMult             = 2.0
```

**Group H - Rule #11**
```
Holiday_Flat_Time       = 415
Registry_Valid_Until    = 1280101
Manual_Kill_Switch      = False
Settlement_Flat_Time    = 1230
```

### Step 5 — Format Signal 設定 Properties
1. `Properties` tab
   - Initial Capital: **1,000,000**
   - Currency: **NTD**
2. `Costs` tab
   - Commission: **500 NTD per side**（round-trip 1000）
3. `Backtesting` tab
   - Order Fill: **Realistic**
   - Bouncing Ticks: **True**

### Step 6 — 執行 Backtest
1. Format Symbol → 設定 Range：**2020-01-01 to 今天**
2. `Calculate` 按鈕
3. 等 backtest 完成
4. `View → Strategy Performance Report`

---

## 二、輸出 xlsx（給 Claude 分析）

### 匯出流程
1. Strategy Performance Report 開啟後
2. `File → Export → Excel`
3. **檔名建議**：`TXF1  S16_S_MACrossShort_baseline_backtest_20260709.xlsx`
4. 存放位置：`C:/Users/User/Downloads/`

### xlsx 必含 3 個 sheet（MC12 自動輸出）
| Sheet | 內容 |
|-------|------|
| **策略分析** | Net / PF / MDD / Sharpe / Trades / WR / Avg trade |
| **設定** | 20+ input 值 |
| **交易明細** | 每筆 SE_/SX_ + Date + Time + PnL + MFE + MAE |

---

## 三、快速健檢（部署後你自己看）

跑完後檢查以下 3 件事：

### ✅ Sanity Check A：Trade 數合理性
- 6.5 年應有 **300-800 trades**（5M 短週期 + 洗盤頻繁）
- 若 < 100 → 進場條件太緊（Slope 過高）
- 若 > 2000 → 進場條件太鬆或 whipsaw 極端

### ✅ Sanity Check B：Exit 分布
從交易明細看 SX_MA_* 標籤分布，應該：
- SX_MA_QuickStop_Loss / QuickStop_Time 占比 **30-50%**（洗盤消化）
- SX_MA_GoldenCross 占比 **20-40%**（趨勢跑完主要出場）
- SX_MA_BE_Trail1/2 占比 **10-20%**（保護獲利）
- SX_MA_ML_Exit 占比 **5-15%**（極端反轉）
- SX_MA_TimeStop / SL 占比 **少數個位數 %**（backup）
- SX_MA_Kill / Registry / Holiday / Settlement 應 **接近 0**（正常運作）

### ✅ Sanity Check C：PnL 合理性
- 這是 draft 版，不期待 4/4 gates，但期待：
  - **Net > 0** 或 slight negative（在多頭年 base）
  - **PF ≥ 0.9**（若 < 0.8 → 邏輯有 bug）
  - **MDD < 30%**（若 > 40% → M5/M6 沒守住）
  - **年 trade 數 30-100**（過度或過稀都要 review）

---

## 四、若有 compile error（不太可能，已 ASCII PASS）

| Error | 可能原因 | 檢查 |
|-------|--------|------|
| Line 0 col 0 | 非 ASCII 字元 | 已跑 verify_pla_ascii.py PASS |
| `Undefined function XAverage` | MC 版本問題 | 用 EMA function 替代 |
| `Undefined function RSI` | RSI 名稱 | 改 `RSI(Close, N)` 或 `RSIndex(Close, N)` |
| `Cannot resolve v_ML_RSI_Prior` | Lowest 用法 | 改用 History reference |

---

## 五、給 Claude 回報格式

跑完後 paste 給我以下 3 段：

### 1. xlsx 路徑
```
C:/Users/User/Downloads/TXF1  S16_S_MACrossShort_baseline_backtest_20260709.xlsx
```

### 2. Headline metrics（從策略分析 sheet 抄）
```
Trades:  ?
Net:     ?
PF:      ?
MDD %:   ?
Sharpe:  ?
WR %:    ?
```

### 3. 有沒有異常
- Compile error 或 warning 訊息？
- Trade 數是否合理（依 Sanity Check）？
- 你觀察到任何奇怪 pattern？

---

## 六、Claude W3 分析會做的事

拿到 xlsx 後我會：

1. **驗證 configuration 對齊**（20+ inputs 對照 W2 spec）
2. **Trade 分布統計**（依 exit 標籤）
3. **年度 breakdown**（stability check）
4. **Regime 分析**（若可辨識）
5. **與 W0 daily proxy 對比**（daily 45.8% WR，5M 是否 similar）
6. **Rule #18 5 件套 pre-check**（初步 MC + Bootstrap）
7. **問題發現**（whipsaw hot zones, param tuning hints）
8. **輸出 W3 分析報告**：`W3_baseline_backtest_analysis_20260709.md`
9. **W4 GA optimization 建議**（下一步 5-param sweep 方向）

---

## 七、下一步 (預計)

- W3 baseline analysis → 若 3/4 gates PASS 直接 GA
- W4 GA Phase 2 optimization（Fast/Slow/QuickStop/BE 4-5 params）
- W5 Rule #18 5 件套（MC + Bootstrap + Stress + Sensitivity + Robustness）
- W6 Promote 決策

---

**End of SOP — 2026-07-08 Desktop**
