# S16_S MACrossShort — 完整進出場規劃 Spec

**日期**：2026-07-08
**狀態**：Stage-1 進出場設計 lock（Layer 1 + Layer 2 完整定案）
**策略類別**：G 類動量交叉（純空）
**時框架構**：Data1 = 5M（執行 + 訊號）/ Data2 = Daily（Regime 待決）
**Alpha 來源**：動能異常（Momentum Anomaly）— 學術支撐 Jegadeesh & Titman (1993)
**指標選擇**：ZLEMA（Zero Lag EMA，相位延遲 ≈ 0）

---

## 一、策略哲學（用戶 2026-07-07 ruling）

> **「進場門戶大開，出場刀鋒銳利」**
> **「短線抓獲利，遇洗盤只做嚴格控管虧損」**
> **「Whipsaw 是可以接受的 — 只要每筆虧損嚴格控管」**

**核心矛盾**：ZLEMA 消除延遲 → 抓得更快，但也**更容易被雜訊觸發** → whipsaw 頻繁。
**解法**：進場條件簡單快速抓機會，**出場端 4 層防護嚴格控管每筆虧損**。

---

## 二、Layer 1 — 進場端設計（DONE 2026-07-07）

### 2.1 進場條件（**只有 5 個 gate**）

```pla
Entry Signal (S16_S MACrossShort):

  ZLEMA_Fast(N1) crosses BELOW ZLEMA_Slow(N2) at Data1 (5M) close
  AND AbsValue(ZLEMA_Slow - ZLEMA_Slow[1]) > MinSlope  // M1 斜率過濾
  AND v_Settlement_Day     = False                     // Rule #11
  AND v_Holiday_Block      = False                     // Rule #11
  AND v_Registry_Expired   = False                     // Rule #11
  AND Manual_Kill_Switch   = False                     // Rule #11 P0

Order:
  sell short next bar at market
```

### 2.2 Layer 1 機制決策（4 個機制的 ruling）

| 機制 | 決策 | 理由 |
|------|------|------|
| **M1 Slope confirmation** | ✅ **KEEP**（loose threshold）| Slow ZLEMA 斜率 ≠ 0 過濾盤整噪音，不擋 dominant 訊號 |
| M2 N-bar delay | ❌ DROP | 5M 承擔不起 10-15 分鐘延遲；exit-side 處理假交叉 |
| M3 ATR threshold | ❌ DROP from entry | ATR 屬出場邏輯範疇；保持進場純粹 |
| M4 Volume confirmation | ❌ DROP | 會擋掉夜盤訊號；日盤中分辨性也差 |

### 2.3 ZLEMA 參數建議範圍（W0 掃描）

| 參數 | 建議範圍 | 選定策略 |
|------|--------|--------|
| ZLEMA_Fast (N1) | 3, 5, 8, 10, 12, 15 | W0 掃描 |
| ZLEMA_Slow (N2) | 15, 20, 25, 30, 40, 50 | W0 掃描 |
| 約束 | Slow > Fast × 2 且 Slow ≤ 50 | 硬性 |
| MinSlope | 0.5, 1.0, 2.0（pts/bar）| W0 掃描 |

---

## 三、Layer 2 — 出場端 4 機制深度設計（2026-07-08 lock）

### 3.1 出場優先順序（**Priority Chain**）

```
P0:  Kill / Registry / Holiday / Settlement  (Rule #11/#12 硬性合規)
P1:  M5 Quick Stop                            (短線洗盤第一刀)
P2:  M6 Rule #17 多層 1M 監控                 (極端行情商辦大樓)
P3:  M7 Breakeven Trailing                    (進 profit 後保護)
P4:  黃金交叉出場                              (主要出場 - Golden Cross)
P5:  M8 Time Stop                             (最大持倉時間)
P6:  ATR-based SL                             (最後防線 - Frozen SL)
P7:  SetStopLoss engine guard                 (Rule #12 backup)

NO TP - trend running per feedback_trend_let_profits_run
```

**設計原則**：**先處理立即性 exit**（Kill/Quick Stop/Rule #17），**後處理正常 exit**（Golden Cross），**最後才用 SL 保命**。

---

### 3.2 M5 Quick Stop — 快速砍虧刀

#### 目的
短線策略最重要的第一道防線。**進場後短時間內沒賺錢或立即虧損 → 立即出場**，不給洗盤機會累積損失。

#### 設計哲學
5M 週期若進場後**幾根 K 就轉向** = 訊號錯 = **立即認錯**，不等 SL 距離觸發。

#### 觸發條件（**兩個條件擇一觸發**）

| 條件 | 說明 |
|------|------|
| **Time-based** | 進場後 `QuickStop_MaxBars` 根 K 都沒獲利（Close 沒低於 Entry）→ 出場 |
| **Loss-based** | 進場後 Loss > `QuickStop_MaxLoss_Pts` 點 → 立即出場 |

#### 參數建議

| 參數 | 建議值 | 範圍 | 理由 |
|------|-------|------|------|
| `QuickStop_MaxBars` | **6** | 3-10 | 5M × 6 = 30 分鐘，短線策略耐心上限 |
| `QuickStop_MaxLoss_Pts` | **15** | 10-25 | 3,000 NTD = 帳戶 0.3%，可接受單筆損失 |
| `QuickStop_On` | **True** | True/False | 開關 |

#### Code 範例

```pla
{ M5 Quick Stop (P1) }
if MarketPosition = -1 and QuickStop_On = True then begin
    v_BarsSince = BarsSinceEntry;
    v_Loss = Close - EntryPrice;   // 空單: Close > Entry = 虧損

    // Time-based
    if v_BarsSince >= QuickStop_MaxBars and Close >= EntryPrice then
        buy to cover ("SX_MA_QuickStop_Time") next bar at market;

    // Loss-based
    if v_Loss > QuickStop_MaxLoss_Pts then
        buy to cover ("SX_MA_QuickStop_Loss") next bar at market;
end;
```

#### Trade-off 分析

| 太短（激進）| 太長（保守）|
|-----------|-----------|
| 好交易 breakout 前被砍 | Whipsaw 損失累積 |
| WR ↓，PF ↓ | 單筆 max loss ↑ |
| 頻率 ↑，滑價成本 ↑ | 心理壓力 ↑ |

---

### 3.3 M6 Rule #17 多層 1M 監控 — 商辦大樓五層

#### 目的
借用 S3_S 已驗證的 1M Multi-Layer Exit 架構，**在極端反向行情（V 轉、突發利多）時提前逃生**。

#### Rule #17 五層架構

```
5F 波動率層  (ATR 突增 = 極端行情啟動)
4F 結構層    (Higher High / Lower Low = 趨勢反轉)
3F 動能層    (RSI 反轉 / MACD 轉正)
2F 量價層    (量爆增 + Close 上漲)
1F K 棒層    (吞噬、大反彈 K)
──────────────────────
0F ATR 停損  (地基 - 最後防線, 不在 Rule #17 範圍)
```

#### 觸發條件

**加權積分 ≥ 65%** AND **跨類別 ≥ 3 層亮起** AND **虧損啟動門檻已達**

#### 參數建議

| 參數 | 建議值 | 說明 |
|------|-------|------|
| `ML_On` | **True** | 開關 |
| `ML_ActivationPct` | **20** | Loss 達 SL 距離 20% 才啟動監控 |
| `ML_ScoreTrigger` | **65** | 加權積分 threshold（% of max）|
| `ML_MinCategories` | **3** | 至少 3 類別亮起（避免單一因子誤觸）|

#### 具體 factor 對應 5 層

**1F K 棒層**（3 factors）：
- A1: 吞噬 K（Close > Open of prev bar）
- A2: 大反彈 K（body > avg body × 2）
- A4: 上影線短、下影線長

**2F 量價層**（2 factors）：
- B1: Volume > Avg(Volume, 15) × 2
- B2: Close vs High of last N bars

**3F 動能層**（2 factors）：
- C1: RSI(14) < 30 → 轉 > 40（超賣反轉）
- C2: MACD histogram 轉正

**4F 結構層**（2 factors）：
- D2: 最新 low > 前一個 low
- D3: 最新 close > MA(10)

**5F 波動率層**（2 factors）：
- E3: ATR(3) / ATR(90) > 2.5

#### Code 骨架

```pla
{ M6 Rule #17 Multi-Layer 1M Monitor (P2) }
if MarketPosition = -1 and ML_On = True then begin
    // Activation gate: 已虧損到 SL 20% 才監控
    v_Loss = Close - EntryPrice;
    v_ActivationLevel = v_StopDist * ML_ActivationPct / 100;

    if v_Loss > v_ActivationLevel then begin
        // 計算各 factor score
        v_Score_A1 = <A1 detection>;  // K bar factor 1
        ... [11 factors total, per S3_S design]

        v_Total_Score = v_Score_A1 + v_Score_A2 + ... + v_Score_E3;
        v_Score_Pct = v_Total_Score / MAX_SCORE * 100;

        v_Category_Count = 0;
        if (v_Score_A1 + v_Score_A2 + v_Score_A4) > 0 then v_Category_Count += 1;
        ... [check each of 5 categories]

        if v_Score_Pct >= ML_ScoreTrigger and
           v_Category_Count >= ML_MinCategories then
            buy to cover ("SX_MA_ML_Exit") next bar at market;
    end;
end;
```

#### Trade-off 分析

| 高積分門檻（60-70%）| 低積分門檻（40-50%）|
|-------------------|-------------------|
| 只在真反轉時 exit | Whipsaw 頻繁誤觸 |
| 可能錯過反彈 exit | 保護早 |
| PF ↑ | WR ↑ 但 Avg Win ↓ |

---

### 3.4 M7 Breakeven Trailing — 進 profit 後保護

#### 目的
**當 profit 累積到一定程度時**，把 stop 拉到 breakeven（或 breakeven + buffer），確保**已賺的錢不倒退**。

#### 設計哲學
Golden Cross 是主要出場，但反轉時 Golden Cross **會延遲**。M7 提供**中間保護層**：進場後開始賺錢 → 移動 SL → 若行情反轉 → 至少不倒賠。

#### 觸發條件

**Profit ≥ `BE_Trigger_ATR × v_ATR`** → 移動 stop 到 `EntryPrice - BE_Buffer_Pts`

（空單：SL 在 Entry 上方，Breakeven trail 把它拉到 Entry 或 Entry + buffer）

#### 3 種進化模式

**模式 A：純 Breakeven**（簡單版）
```
Profit >= 1.0 ATR → SL 移到 EntryPrice
Profit >= 1.5 ATR → SL 移到 EntryPrice - 10 pts (小 buffer)
```

**模式 B：Trailing % of Peak**（進階）
```
Peak Profit tracked (like S3_S SP_Armed)
Profit reaches X% of Peak → exit
```

**模式 C：ATR Trail**（動態）
```
Every bar: v_Trail_Stop = Close + (v_ATR × Trail_Mult)
If Close > v_Trail_Stop → exit
```

#### 建議：**先用模式 A（簡單版）**，W0 後看數據升級

#### 參數建議

| 參數 | 建議值 | 說明 |
|------|-------|------|
| `BE_On` | **True** | 開關 |
| `BE_Trigger_ATR` | **1.0** | Profit 達 1 ATR 啟動 |
| `BE_Buffer_Pts` | **5** | 拉到 Entry - 5（讓一點空間）|
| `BE_Tier2_ATR` | **1.5** | 二階：Profit 達 1.5 ATR 收緊 |
| `BE_Tier2_Buffer_Pts` | **10** | 二階拉到 Entry - 10 |

#### Code 骨架

```pla
{ M7 Breakeven Trailing (P3) }
if MarketPosition = -1 and BE_On = True then begin
    v_Profit = EntryPrice - Close;   // 空單: Entry > Close = 賺

    // Tier 1: Profit >= 1 ATR
    if v_Profit >= BE_Trigger_ATR * v_ATR then begin
        v_BE_Stop = EntryPrice - BE_Buffer_Pts;   // 空: stop 在 Entry 稍下
        if Close <= v_BE_Stop then
            buy to cover ("SX_MA_BE_Trail1") next bar at market;
    end;

    // Tier 2: Profit >= 1.5 ATR (更緊)
    if v_Profit >= BE_Tier2_ATR * v_ATR then begin
        v_BE_Stop = EntryPrice - BE_Tier2_Buffer_Pts;
        if Close <= v_BE_Stop then
            buy to cover ("SX_MA_BE_Trail2") next bar at market;
    end;
end;
```

#### Trade-off 分析

| BE 太早設（0.5 ATR）| BE 太晚設（2.0 ATR）|
|-------------------|-------------------|
| Whipsaw 都出場 | 大浮盈變小虧 |
| 錯過 continuation | 保護遲 |
| 心理舒服但錯過大 win | 心理煎熬但抓大波段 |

---

### 3.5 M8 Time Stop — 最大持倉時間

#### 目的
避免持倉**過長**跨越風險時段（假日、結算日、夜盤到日盤過渡）。

#### 觸發條件

**Bars Held ≥ `MaxHoldingBars`** → 強制平倉

#### 參數建議

| 參數 | 建議值 | 說明 |
|------|-------|------|
| `M8_On` | **True** | 開關 |
| `MaxHoldingBars` | **48** | 5M × 48 = 4 小時（半個日盤）|

#### 特殊處理

- **接近 Settlement_Flat_Time (12:30)**：Rule #11 已 handle
- **接近夜盤結束 05:00**：Rule #11 已 handle
- **假日前**：Rule #11 已 handle
- **一般週間跨日**：M8 處理

#### Code

```pla
{ M8 Time Stop (P5) }
if MarketPosition = -1 and M8_On = True then begin
    if BarsSinceEntry >= MaxHoldingBars then
        buy to cover ("SX_MA_TimeStop") next bar at market;
end;
```

#### Trade-off

| 太短（36 = 3hr）| 太長（96 = 8hr = 全日盤）|
|---------------|------------------------|
| 好趨勢被砍 | 隔夜風險高 |
| 頻率 ↑ | 動能可能耗盡 |

---

### 3.6 出場優先順序完整 Code 架構

```pla
{ === 出場優先順序 P0 到 P7 === }

if MarketPosition = -1 then begin
    ExitFired = 0;

    { ---- P0: 硬性合規 (Rule #11 / #12) ---- }
    if v_Kill_Switch or v_Registry_Expired or v_Holiday_Block or v_Settlement_Day then begin
        buy to cover ("SX_MA_P0_Compliance") next bar at market;
        ExitFired = 1;
    end;

    { ---- P1: M5 Quick Stop ---- }
    if ExitFired = 0 and QuickStop_On then begin
        // Time or Loss based
        [M5 logic]
    end;

    { ---- P2: M6 Rule #17 Multi-Layer Monitor ---- }
    if ExitFired = 0 and ML_On then begin
        [M6 logic]
    end;

    { ---- P3: M7 Breakeven Trailing ---- }
    if ExitFired = 0 and BE_On then begin
        [M7 logic]
    end;

    { ---- P4: Golden Cross (主要出場) ---- }
    if ExitFired = 0 then begin
        if ZLEMA_Fast crosses above ZLEMA_Slow then
            buy to cover ("SX_MA_GoldenCross") next bar at market;
    end;

    { ---- P5: M8 Time Stop ---- }
    if ExitFired = 0 and M8_On then begin
        if BarsSinceEntry >= MaxHoldingBars then
            buy to cover ("SX_MA_TimeStop") next bar at market;
    end;

    { ---- P6: ATR SL (Frozen) ---- }
    if ExitFired = 0 then begin
        if Close >= v_SL_Level then
            buy to cover ("SX_MA_SL") next bar at v_SL_Level Stop;
    end;

    { ---- P7: SetStopLoss engine guard (backup) ---- }
    SetStopLoss(v_StopDist * BigPointValue);
end;
```

---

## 四、Layer 3 — Regime Filter 決策（**待用戶 ruling**）

### 4.1 選項對比

| 選項 | 說明 | 優點 | 缺點 |
|------|------|------|------|
| **A. 純規則簡單** | 不加 Daily MA regime filter | 簡單、規則清楚、透明 | 多頭年 whipsaw 損失大 |
| **B. Daily MA Filter** | Daily Close < MA50 才允許空 | 大幅減少多頭年損失 | 違反 L24 精神、規則變複雜 |
| **C. W0 決定** | 兩版本都跑 W0，讓數據說話 | 客觀 | 增加開發時間 |

### 4.2 我的建議：**C（W0 對比決定）**

**理由**：
- L24 教訓是「不要為救 alpha 疊 filter」，但 Regime filter 本質是**環境判斷**不是策略 sub-filter
- 5M 純空策略在強多頭年**結構性逆風** → 若不加 filter 可能 W0 直接 FAIL
- W0 對比讓數據說話，避免主觀判斷

**待用戶 ruling**：A / B / C 選一

---

## 五、完整參數清單（**MC12 部署用**）

### Group A — Entry (ZLEMA)

| Input | Default | 範圍 |
|-------|--------|------|
| ZLEMA_Fast | 5 | 3, 5, 8, 10, 12, 15 |
| ZLEMA_Slow | 20 | 15, 20, 25, 30, 40, 50 |
| MinSlope | 1.0 | 0.5, 1.0, 2.0 |

### Group B — M5 Quick Stop

| Input | Default | 範圍 |
|-------|--------|------|
| QuickStop_On | True | True / False |
| QuickStop_MaxBars | 6 | 3, 4, 6, 8, 10 |
| QuickStop_MaxLoss_Pts | 15 | 10, 12, 15, 20, 25 |

### Group C — M6 Multi-Layer

| Input | Default | 範圍 |
|-------|--------|------|
| ML_On | True | True / False |
| ML_ActivationPct | 20 | 10, 15, 20, 25 |
| ML_ScoreTrigger | 65 | 50, 60, 65, 70 |
| ML_MinCategories | 3 | 2, 3, 4 |

### Group D — M7 Breakeven Trail

| Input | Default | 範圍 |
|-------|--------|------|
| BE_On | True | True / False |
| BE_Trigger_ATR | 1.0 | 0.5, 1.0, 1.5, 2.0 |
| BE_Buffer_Pts | 5 | 0, 5, 10, 15 |
| BE_Tier2_ATR | 1.5 | 1.5, 2.0, 2.5 |
| BE_Tier2_Buffer_Pts | 10 | 5, 10, 15, 20 |

### Group E — M8 Time Stop

| Input | Default | 範圍 |
|-------|--------|------|
| M8_On | True | True / False |
| MaxHoldingBars | 48 | 24, 36, 48, 60, 96 |

### Group F — ATR SL (Frozen)

| Input | Default | 範圍 |
|-------|--------|------|
| ATR_Len | 14 | 10, 14, 20 |
| StopATRMult | 2.0 | 1.5, 2.0, 2.5, 3.0 |

### Group G — Regime Filter (**待 ruling**)

| Input | Default | 範圍 |
|-------|--------|------|
| Use_Regime_Filter | True/False | 待 ruling |
| Regime_MA_Period | 50 | 20, 40, 50, 100 |

### Group H — Rule #11 合規

| Input | Default |
|-------|--------|
| Holiday_Flat_Time | 415 |
| Registry_Valid_Until | 1280101 |
| Manual_Kill_Switch | False |
| Settlement_Flat_Time | 1230 |

---

## 六、預期表現框架

| 指標 | 樂觀 | 中性 | 悲觀 |
|------|------|------|------|
| 年 trade 數 | 100-150 | 50-80 | < 30 |
| Win Rate | 40-50% | 30-40% | < 30% |
| PF | 1.4-1.8 | 1.0-1.3 | < 0.9 |
| MDD % | -12% | -18% | -25%+ |
| Sharpe | 0.5-0.8 | 0.3-0.5 | < 0.2 |
| Avg Win / Avg Loss | 2.0+ | 1.5 | 1.2 |

**Base rate**：純 MA/ZLEMA cross 策略在**趨勢明顯**市場 PF 1.3-1.6，**盤整市場**需靠 Quick Stop + Multi-Layer 保命。

---

## 七、下一步

1. ✅ Layer 1 進場設計 lock（2026-07-07）
2. ✅ Layer 2 出場設計 lock（2026-07-08 本檔）
3. ⏳ **Layer 3 Regime Filter** 用戶 ruling A/B/C
4. ⏳ **W0 Alpha Pre-verify Python script**（ZLEMA cross on TXF1 5M 2020-2026）
5. ⏳ **W1 策略正式文件**（若 W0 PASS）
6. ⏳ **W2 .pla 實作**（含 P0-P7 完整出場鏈）

---

## 八、五支柱工程系統 checklist (Rule #16)

- **Rules**：符合 Rule #11 / #12 / #13 / #14 / #15 / #17 / #18
- **Context**：Fully documented in this spec + MA_deep_research_20260707.md
- **Verification**：待 W0 Python + W2 ASCII verify + W3 MC12 backtest
- **Memory**：對齊 `feedback_trend_let_profits_run` / `feedback_holiday_flatten_rule` / `feedback_mc_time_24hr_pitfall`
- **Format**：完整 spec md + 未來 handoff + annotated md

---

**End of Spec — 2026-07-08 Desktop**
