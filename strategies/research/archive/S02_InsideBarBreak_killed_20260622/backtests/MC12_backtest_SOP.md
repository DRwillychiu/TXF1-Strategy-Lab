# S2 v0.4 MC12 回測操作 SOP

**用途**：用同一份 `S2_InsideBarBreak.pla`，跑 4 個 input 配置版本
**預估時間**：總共 60-90 分鐘
**重要警告**：MC12 input 持久化陷阱 — 改 input 後**必須重跑回測**，否則用舊值
**結果**：4 份 xlsx 匯出到 `backtests/` 子資料夾

---

## 一、總覽：4 個版本要做什麼

| 順序 | 版本 | input 改動 | 預期樣本 | 目的 |
|------|------|----------|--------|------|
| 1 | **v0.4 完整** | 不動（用 .pla 預設）| 12-24 | 最新最完整 |
| 2 | **v0.3 復刻** | A 系列 3 個 false | 30-50 | 分離 A 系列效果 |
| 3 | **v0.2 復刻** | A+B+C 全 false | 40-70 | 分離 B+C 系列效果 |
| 4 | **Naive** | + BreakOffset_Mode=0 | 50-90 | baseline (教科書版) |

---

## 二、Phase 1：MC12 首次載入策略

### 步驟 1.1：清掉舊版（若有）

如果 MC12 之前已載過 S2_InsideBarBreak（或 STRATEGY_GEN_InsideBarBreak）：

```
1. Charts → PowerLanguage Editor (F8)
2. File → Open... → 找到 STRATEGY_GEN_InsideBarBreak
3. 右鍵 → Delete  （完全移除舊版本，避免 inputs 殘留）
4. 確認 PowerLanguage Editor 樹狀清單裡沒有 STRATEGY_GEN_InsideBarBreak
```

### 步驟 1.2：從 .pla 載入新版

```
1. PowerLanguage Editor → File → Import...
2. 選擇 .pla 檔：
   C:\Users\User\Desktop\TXF1-Strategy-Lab\strategies\research\
   S02_InsideBarBreak\S2_InsideBarBreak.pla
3. Import → 確認 STRATEGY_GEN_InsideBarBreak 出現在 Signals 樹下
4. 雙擊打開 → File → Verify (F3) → 確認綠色 "Verify Successful"
```

### 步驟 1.3：建立 30M 圖表

```
1. MC12 主畫面 → New Chart Window
2. Symbol: TXF1
3. Settings:
   - Resolution: 30 Min
   - Bars Back: 至少 8 年（涵蓋 2018 ~ 今）
   - Session: Use Custom Session (含夜盤 15:00-05:00)
4. OK → 30M chart 出現
```

### 步驟 1.4：添加 Data2 = TXF1 Daily

```
1. 右鍵 chart → Format Data...
2. Add Data → TXF1
3. Settings:
   - Resolution: Daily
   - Use this data: only as Data2 (不顯示 in chart)
4. OK → chart 內部多了 Daily data feed
```

### 步驟 1.5：套用策略

```
1. 右鍵 chart → Insert Strategy...
2. 從 Signals 清單找 STRATEGY_GEN_InsideBarBreak
3. Add → OK
4. Inputs 視窗自動彈出 → 應該看到 32 個 input
   （若沒看到 Settlement_Flat_Time / Compression_On 等，
    代表載到舊版了，回 1.1 重來）
```

---

## 三、Phase 2：依序跑 4 個版本

### 版本 1：v0.4 完整版（最先跑）

#### Input 設定（**全部用 .pla 預設值**，不用改）

| Input | 值 |
|-------|---|
| BreakOffset | 5 |
| StopPct | 50 |
| TargetMult | 1.5 |
| MinMotherRange | 50 |
| MaxMotherRange | 400 |
| MALen | 20 |
| MaxBarsHeld | 30 |
| MinStopPts | 40 |
| Holiday_Flat_Time | 415 |
| Registry_Valid_Until | 1270101 |
| Manual_Kill_Switch | False |
| Settlement_Flat_Time | 1230 |
| **BreakOffset_Mode** | **1** |
| BreakOffset_Pct | 5 |
| MinBreakOffset | 5 |
| **Confirm_On** | **True** |
| ConfirmBars | 2 |
| **VolFilter_On** | **True** |
| VolMALen | 20 |
| VolMultiplier | 1.2 |
| **BE_On** | **True** |
| BE_Trigger_Pct | 75 |
| **Trail_On** | **True** |
| Trail_Trigger_Pct | 70 |
| Trail_Offset_Pct | 30 |
| **SP_On** | **True** |
| SP_Trigger_Mult | 1.0 |
| SP_GiveBack_Pct | 45 |
| **Compression_On** | **True** |
| MaxCompressionRatio | 0.6 |
| **BB_Filter_On** | **True** |
| BB_Length | 20 |
| BB_StdDev_Mult | 2 |
| BB_AvgLen | 60 |
| BB_Width_Threshold | 0.8 |
| **ATR_Filter_On** | **True** |
| ATR_Short_Len | 5 |
| ATR_Long_Len | 20 |
| ATR_Compression_Threshold | 0.8 |

#### 跑回測 + 匯出

```
1. Format Strategy → Properties → 確認 inputs（上表）
2. 設定:
   - Initial Capital: 1,000,000
   - Slippage: 1000 per round-trip (500 each side)
   - Commission: 30 per trade
   - Pyramiding: false
   - Use One Contract: true (1 口固定)
3. OK → 自動重新計算
4. View → Strategy Performance Report
5. File → Export Report → Excel...
6. 存檔: C:\Users\User\Desktop\TXF1-Strategy-Lab\
        strategies\research\S02_InsideBarBreak\backtests\
        S2_v04_full_20260617.xlsx
```

---

### 版本 2：v0.3 復刻（A 系列關閉）

#### Input 改動（**只改 3 個 _On 開關**）

```
從 v0.4 設定改：
  Compression_On    : True → False
  BB_Filter_On      : True → False
  ATR_Filter_On     : True → False
其他 input 全部保持 v0.4 預設
```

#### 跑回測 + 匯出

```
1. Format Strategy → Properties → 改上面 3 個 _On 為 False
2. OK → 自動重新計算（樣本數應該變多，因為過濾減少了）
3. View → Strategy Performance Report → Export → Excel
4. 存檔: backtests\S2_v03_replica_20260617.xlsx
```

---

### 版本 3：v0.2 復刻（A+B+C 全關，動態 offset 仍開）

#### Input 改動（**所有功能 _On 設 False**）

```
從 v0.3 復刻設定再改：
  Confirm_On        : True → False
  VolFilter_On      : True → False
  BE_On             : True → False
  Trail_On          : True → False
  SP_On             : True → False

  Compression_On    : False (保持)
  BB_Filter_On      : False (保持)
  ATR_Filter_On     : False (保持)

  BreakOffset_Mode  : 1 (保持動態)
```

#### 跑回測 + 匯出

```
1. Format Strategy → 改上面 5 個 _On 為 False
2. OK → 自動重新計算
3. Export → backtests\S2_v02_replica_20260617.xlsx
```

---

### 版本 4：Naive 教科書版（全關 + 固定 offset）

#### Input 改動（**只改 BreakOffset_Mode**）

```
從 v0.2 復刻設定再改：
  BreakOffset_Mode  : 1 → 0 (改為固定 5pt)

其他保持 v0.2 復刻設定（A+B+C 都 false）
```

#### 跑回測 + 匯出

```
1. Format Strategy → 改 BreakOffset_Mode 為 0
2. OK → 自動重新計算
3. Export → backtests\S2_naive_20260617.xlsx
```

---

## 四、完成後檢查清單

```
[ ] 4 份 xlsx 都已匯出
[ ] 檔案命名符合規則: S2_<version>_<YYYYMMDD>.xlsx
[ ] 全部放在 backtests/ 子資料夾
[ ] 每份 xlsx 都有「策略分析」「交易明細」兩個 sheet
[ ] 每份 xlsx 的「交易明細」第一筆與最後一筆日期合理
   (應接近 2020-01-01 ~ 2026-06-17)
[ ] 樣本數順序合理: Naive > v0.2 > v0.3 > v0.4
   (因為 v0.4 過濾最嚴格，樣本應該最少)
```

---

## 五、常見問題

### Q1: input 改了但回測沒重跑

A: MC12 改 input 後通常會自動重算，但若沒有：
```
右鍵 chart → Recalculate
或 Insert Strategy 後 Apply
```

### Q2: 樣本只有個位數，太少了

A: 可能設定問題：
- 確認 Data2 是 Daily（不是 30M）
- 確認 Bars Back 至少 8 年
- 確認 BreakOffset_Mode 設定對

### Q3: PowerLanguage Verify 失敗

A: 可能 MC12 不支援某些函數，或語法錯誤：
```
1. 截圖錯誤訊息
2. 回報給我
3. 我修 .pla
```

### Q4: 樣本數 v0.4 > v0.3 (反邏輯)

A: 表示 A 系列過濾沒生效，可能：
- input 沒改成 false
- 確認 Format Strategy → Properties 看到的就是回測用的值

### Q5: 交易明細 xlsx 為空

A: 沒有任何進場，可能：
- v0.4 過濾太嚴格（這也是發現！）
- Volume data 不可用（VolFilter_On 直接 false 試試）

---

## 六、跑完後通知我

匯出 4 份 xlsx 完成後，告訴我：

```
「S2 v0.4 4 份回測完成，xlsx 已放 backtests/ 」
```

我接著做的事：
1. 讀 4 份 xlsx
2. 寫 `analyze_s2_phase2.py` 分析腳本
3. 跑分析產出對比表：
   - 樣本 / WR / PF / 淨利 / MDD 4 版對比
   - v0.2-Naive / v0.3-v0.2 / v0.4-v0.3 增量 alpha
   - MFE/MAE / 持倉天數 / Long-Short 分布
   - Settlement / Holiday / Kill 觸發次數
4. 寫 `S2_phase2_results_YYYYMMDD.md` 完整分析報告
5. 更新 issue tracker D / F / G / H / I 系列
6. 一起決定 Phase 3 或 archive
7. commit + push

---

## 七、預估時程

| 步驟 | 時間 |
|------|------|
| Phase 1 載入（步驟 1.1-1.5）| 15 分鐘 |
| 版本 1 v0.4 完整 | 15 分鐘 |
| 版本 2 v0.3 復刻 | 10 分鐘（只改 inputs，比較快）|
| 版本 3 v0.2 復刻 | 10 分鐘 |
| 版本 4 Naive | 10 分鐘 |
| **總計** | **60 分鐘左右** |

---

## 八、相關文件

- [v0.4 設計規格](../S2_v04_design_spec.md)
- [Backtests README](README.md)
- [策略 .pla 檔](../S2_InsideBarBreak.pla)
- [Backtest Journal](../S2_backtest_journal.md)
