# S2 v0.4 設計規格 — A 系列波動率壓縮量化過濾

**版本**：v0.3 → **v0.4**（A 系列加入）
**設計日**：2026-06-17
**目標**：解決 [`S2_known_issues.md`](S2_known_issues.md) A-1 / A-2 / A-3
**設計哲學**：所有過濾器 input-switched 可關閉復刻 v0.3 行為

---

## 一、為什麼需要 A 系列

v0.3 的進場條件只有「**樣態識別**」+「**範圍過濾**」：

```
Inside Bar 樣態 ✓
MotherRange 50-400 ✓
MA 方向 ✓
動態 BreakOffset + ConfirmBars + Volume（v0.3 新增）✓
```

**但這只確認「**有 Inside Bar**」，沒確認「**真的壓縮**」。

實際狀況：
- 一個 50 點母棒 + 40 點 Inside Bar = **壓縮比 80% = 弱壓縮**
- 一個 200 點母棒 + 50 點 Inside Bar = **壓縮比 25% = 強壓縮**

**A 系列就是把「壓縮強度」量化過濾掉前者**。

---

## 二、A-1: Inside / Mother 範圍比過濾

### 設計

```powerlanguage
{ Inside Bar range / Mother Bar range }
v_InsideRange = High of Data2[1] - Low of Data2[1];
v_CompressionRatio = v_InsideRange / v_MotherRange;

{ 過濾：壓縮比 < threshold 才通過 }
if Compression_On = false then
    v_Compression_Pass = true
else
    v_Compression_Pass = (v_CompressionRatio <= MaxCompressionRatio);
```

### 新 inputs
- `Compression_On(true)` — 開關
- `MaxCompressionRatio(0.6)` — Inside / Mother ≤ 60% 才通過

### 預期效果

| MotherRange | InsideRange | Ratio | 通過？ |
|------------|------------|-------|------|
| 100 | 30 | 0.30 | ✅ 強壓縮 |
| 100 | 50 | 0.50 | ✅ 中壓縮 |
| 100 | 60 | 0.60 | ✅ 臨界 |
| 100 | 70 | 0.70 | ❌ 弱壓縮 |
| 100 | 90 | 0.90 | ❌ 微壓縮 |

**過濾掉「樣態上是 Inside Bar 但實質沒壓縮」的訊號**。

---

## 三、A-2: BB Width 收縮確認

### 設計理念

Bollinger Band Width = 2 × StdDev / 中線 → 衡量價格波動範圍。
- BB Width 變窄 = 波動率收縮（與 Inside Bar 邏輯一致）
- 當前 BB Width < 歷史平均 × X → **獨立的波動率訊號交叉確認**

### 設計

```powerlanguage
{ Data2 (Daily) BB Width 比例 }
v_BB_StdDev = StdDev(Close of Data2, BB_Length);
v_BB_Mid    = Average(Close of Data2, BB_Length);
if v_BB_Mid > 0 then
    v_BB_Width = (v_BB_StdDev * 2 * BB_StdDev_Mult) / v_BB_Mid
else
    v_BB_Width = 999999;

{ 歷史平均 BB Width }
v_BB_Width_Avg = Average(v_BB_Width, BB_AvgLen);

{ 過濾：當前 BB Width < 歷史平均 × threshold }
if BB_Filter_On = false then
    v_BB_Pass = true
else if v_BB_Width_Avg > 0 then
    v_BB_Pass = (v_BB_Width < v_BB_Width_Avg * BB_Width_Threshold)
else
    v_BB_Pass = true;
```

### 新 inputs
- `BB_Filter_On(true)` — 開關
- `BB_Length(20)` — BB 計算長度（日線）
- `BB_StdDev_Mult(2)` — 標準差倍數
- `BB_AvgLen(60)` — 歷史平均長度（過去 60 日 BB Width）
- `BB_Width_Threshold(0.8)` — 當前 BB Width 必須 < 平均 × 80%

### 預期效果

| 情境 | BB Width | Avg | 通過？ |
|------|---------|-----|------|
| 持續高波動 | 5.0% | 4.0% | ❌（5.0 > 4.0 × 0.8 = 3.2）|
| 進入收縮期 | 3.0% | 4.0% | ✅（3.0 < 3.2）|
| 深度收縮 | 2.0% | 4.0% | ✅（2.0 < 3.2）|
| 常態低波動 | 3.5% | 3.5% | ❌（3.5 > 3.5 × 0.8 = 2.8）|

**注意 4 號情境**：常態低波動 ≠ 真壓縮。要求「**比平常更壓縮**」才算真壓縮。

---

## 四、A-3: ATR_Short / ATR_Long 比例

### 設計理念

短期 ATR < 長期 ATR × X → 短期波動收縮 → 進入「**準爆發狀態**」。

### 設計

```powerlanguage
{ Data2 (Daily) ATR }
v_ATR_Short = AvgTrueRange(ATR_Short_Len) of Data2;
v_ATR_Long  = AvgTrueRange(ATR_Long_Len) of Data2;

{ 過濾：短期 ATR < 長期 ATR × threshold }
if ATR_Filter_On = false then
    v_ATR_Pass = true
else if v_ATR_Long > 0 then
    v_ATR_Pass = (v_ATR_Short < v_ATR_Long * ATR_Compression_Threshold)
else
    v_ATR_Pass = true;
```

### 新 inputs
- `ATR_Filter_On(true)` — 開關
- `ATR_Short_Len(5)` — 短期 ATR
- `ATR_Long_Len(20)` — 長期 ATR
- `ATR_Compression_Threshold(0.8)` — Short < Long × 80%

### 預期效果

| 情境 | ATR(5) | ATR(20) | Ratio | 通過？ |
|------|--------|---------|-------|------|
| 趨勢加速 | 150 | 100 | 1.50 | ❌ |
| 趨勢延續 | 100 | 100 | 1.00 | ❌ |
| 開始收縮 | 80 | 100 | 0.80 | ❌（臨界）|
| 中度收縮 | 70 | 100 | 0.70 | ✅ |
| 深度收縮 | 50 | 100 | 0.50 | ✅ |

---

## 五、三個過濾器的關係

### 邏輯關係
```
A-1 Inside/Mother 比  → 看「當前 K 棒」壓縮（樣態強度）
A-2 BB Width 收縮     → 看「過去 20 日」波動率（中期收縮）
A-3 ATR 短長比        → 看「過去 5 日 vs 20 日」收縮（近期加速壓縮）
```

**三個指標都通過 = 三維度交叉確認的真壓縮**：
- A-1 確認「**形態壓縮**」
- A-2 確認「**整體價格範圍收縮**」
- A-3 確認「**收縮的加速性**」

### 預期過濾率

| 過濾器 | 預估通過率 |
|-------|---------|
| 基礎 Inside Bar | ~ 1.5%（355 天的 5 次）|
| + A-1 過濾後 | ~ 60% |
| + A-2 過濾後 | ~ 50% |
| + A-3 過濾後 | ~ 70% |
| **三個全通過** | **~ 21%** |

預期年化進場樣本：5-8 → **2-4 筆**（更少但更精）

**這是 v0.4 哲學的極致**：「**少而精**」到極致。

---

## 六、Input 完整清單對比

### v0.3 inputs (23 個) → v0.4 (32 個)

```
{ v0.3 全部保留 (23 個) - 不重述 }

{ v0.4 新增 A 系列 (9 個) }
Compression_On(true),         { A-1 開關 }
MaxCompressionRatio(0.6),     { A-1 Inside/Mother ≤ 60% }

BB_Filter_On(true),           { A-2 開關 }
BB_Length(20),                { A-2 BB 長度 }
BB_StdDev_Mult(2),            { A-2 BB 標準差倍數 }
BB_AvgLen(60),                { A-2 歷史平均長度 }
BB_Width_Threshold(0.8),      { A-2 必須 < 平均 × 80% }

ATR_Filter_On(true),          { A-3 開關 }
ATR_Short_Len(5),             { A-3 短期 ATR }
ATR_Long_Len(20),             { A-3 長期 ATR }
ATR_Compression_Threshold(0.8){ A-3 必須 < 長 × 80% }
```

實際是 11 個 input 但 BB_Length 與 BB_StdDev_Mult 共用 BB 計算，數法不同；9 個新邏輯參數 + 開關。

### A/B 測試組合擴展

| 配置名 | v0.4 設定 |
|--------|---------|
| **v0.4 最嚴格** | 全部 _On = true（預設）|
| **v0.4 中度** | 只開 A-1（最廉價過濾）|
| **v0.4 寬鬆** | 只開 A-2 + A-3（量化指標）|
| **v0.3 復刻** | A 全 false + B/C 全 true |
| **v0.2 復刻** | A/B/C 全 false |

---

## 七、Variables 新增

```
{ A-1 }
v_InsideRange(0),
v_CompressionRatio(0),
v_Compression_Pass(false),

{ A-2 }
v_BB_StdDev(0),
v_BB_Mid(0),
v_BB_Width(0),
v_BB_Width_Avg(0),
v_BB_Pass(false),

{ A-3 }
v_ATR_Short(0),
v_ATR_Long(0),
v_ATR_Pass(false)
```

11 個新變數。

---

## 八、整合到進場邏輯

```powerlanguage
{ 進場條件鏈 — v0.4 完整版 }
if v_PendingLong = false and v_PendingShort = false and
   v_Prev_MP <= 0 and
   v_IsInsideBar and                                     { 樣態 }
   v_MotherRange >= MinMotherRange and                   { 範圍下界 }
   v_MotherRange <= MaxMotherRange and                   { 範圍上界 }
   v_Compression_Pass and                                { A-1 ★ }
   v_BB_Pass and                                         { A-2 ★ }
   v_ATR_Pass and                                        { A-3 ★ }
   v_MA_Up and                                           { 方向過濾 }
   v_Holiday_Block = false and                           { P0 gate }
   v_Settlement_Day = false and
   v_Registry_Expired = false and
   v_VolPass and                                         { B-3 }
   Close > v_MotherHigh + v_DynBreakOffset then begin    { B-1 + 突破 }
    ...
end;
```

**11 個 AND 條件**全部通過才進場。

---

## 九、解決的 issue tracker 項目

| Issue | v0.4 解決方案 |
|-------|------------|
| **A-1** | Inside / Mother 範圍比 ≤ 0.6 過濾 |
| **A-2** | BB Width < 歷史 60 日平均 × 80% |
| **A-3** | ATR(5) < ATR(20) × 80% |

**29 題：v0.3 已解 8 題 + v0.4 解 3 題 = ✅ 11 題完成 / ❌ 18 題未解**

---

## 十、與既有 6 隻策略的設計傳承

| 策略 | 波動率壓縮應用 |
|------|------------|
| L1 | ATR breakout（用 ATR 但不過濾壓縮）|
| L2 | 類似 L1 |
| L3 | Box detection（用範圍但不用 BB）|
| **S2 v0.4** | **三維度交叉確認壓縮（最嚴格）**|

S2 v0.4 = **portfolio 中第一隻完整實作「波動率壓縮過濾」的策略**。
其他策略可借鑑此設計加入類似機制。

---

## 十一、待 Phase 2 驗證

1. ✅ A-1 邏輯正確（自動 verify）
2. ❓ MaxCompressionRatio = 0.6 是否最佳（vs 0.5 / 0.7 sensitivity）
3. ❓ BB Width 60 日平均是否合理（vs 30/120 日）
4. ❓ BB_Width_Threshold = 0.8 是否最佳
5. ❓ ATR(5) vs ATR(20) 比例 80% 是否最佳
6. ❓ **三個過濾器是否互相獨立**（如果高度相關 = 不必要 redundancy）

Phase 3.1 應做：
- 每個閾值的 sensitivity test（找「高原」非「尖峰」）
- 三個過濾器相關性分析（如果 > 0.7 → 移除其中一個）

---

## 十二、設計風險

### 風險 1：過度過濾導致樣本歸零
- v0.1 一年 5-8 筆
- v0.3 預期 5-8 筆（B 系列不大改進場頻率）
- **v0.4 預期 2-4 筆**

若 Phase 2 顯示樣本 < 30（六年回測），**統計信心不足，需調寬閾值**。

### 風險 2：BB Width 與 ATR 過濾相關性過高
兩者都衡量「過去 N 日波動率」，可能 redundant。
Phase 3 必須測：
- 只開 A-2（BB）
- 只開 A-3（ATR）
- 同時開 A-2 + A-3
- 若三者效果相近 → 只保留一個

### 風險 3：常態低波動股票 vs TXF1
TXF1 是高流動性指數期貨，BB Width / ATR 通常有「中位水準」。
我們的 threshold 是「相對於歷史平均」，所以 TXF1 應該適合。
但若某段時期（如 2025 整年低波動），可能整段時期都沒有信號 → **要警惕「時段集中性」**。

---

## 十三、相關文件

- [v0.3 設計規格](S2_v03_design_spec.md)
- [Issue tracker](S2_known_issues.md)
- [策略完整說明](S2_InsideBarBreak_strategy.md)
- [憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
