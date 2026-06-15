# TXF1 量化策略批次 01
> 生成日期：2026-06-07
> 類別組合：A + B + C + D + E
> 回測區間：2020/01/01 ~ 2026/06/06
> 資料來源：^TWII 日線代理（日內策略需在 MC 用分鐘數據驗證）

---

## 回測績效總覽

| # | 策略名稱 | 操作方向 | 操作週期 | 賺什麼錢？ | 交易數 | 勝率 | PF | 淨利(NTD) | MDD(NTD) | CAGR | 年化報酬(NTD) |
|---|---------|---------|---------|-----------|-------|------|-----|----------|----------|------|-------------|
| 1 | NightMomentum | 🟢★純做多(v2.1) | 15M | 夜盤開盤區間突破+波動率擴張 | 807 | 58.9% | 1.448 | +1,997,000 | -278,800 | 31.1% | ~310k | 
| 2 | InsideBarBreak | ★雙向（多+空） | 30M+日線 | 日線母子線壓縮後方向選擇的爆發 | 34 | 64.7% | 4.61 | +791,754 | -63,879 | 27.0% | +146,424 |
| 3 | VolSqueeze | ★雙向（多+空） | 60M | BB收縮後波動率擴張的方向突破 | 33 | 36.4% | 0.88 | -115,622 | -645,467 | — | -23,127 |
| 4 | MACDDivergence | ★雙向（逆勢） | 60M | 趨勢動能衰竭後的均值回歸反轉 | 2 | 100% | — | +38,000 | 0 | — | — |
| 5 | SettlementWeek | ★結算前空/後多 | 日線 | 結算日前壓低+後反彈的日曆效應 | 83 | 34.9% | 0.60 | -367,000 | -451,000 | — | -58,638 |

> ⚠️ **重要提醒**：以上為 Python 日線代理回測，精度不如 MC 分鐘回測。S1 使用窄幅日突破代理夜盤 ORB 邏輯，實際表現會有差異。S3/S5 在日線回測中表現不佳，但在分鐘級別可能不同——請務必在 MC12 用正確週期驗證。S4 樣本僅 2 筆，無統計意義。

---

## 策略 1：夜盤動量追蹤策略

### 1. 策略概述
- **類別**：A 類（時段型）
- **操作方向**：🟢 ★純做多（MC12 分析：空單 PF=0.93，淨利-618,600，已移除）
- **賺什麼錢**：夜盤前半段（15:00-17:45）觀察 11 根 15 分 K 棒形成價格區間，波動率擴張時突破高點做多；後半段（17:45-05:00）賺慣性延續。只做多、不做空。
- **版本**：v2.1 ATR-Based + 波動率擴張過濾器（VolFilter）
- **主交易週期**：15 分鐘
- **確認週期**：無（純時段內策略）
- **預期交易頻率**：每月 ~12.4 筆
- **與現有策略的差異**：TL/TS 以日盤為主且依賴日線/週線確認；本策略專注夜盤時段，用開盤區間突破進場，邏輯完全不同。
- **優化狀態**：🟢 **P1~P3 檢驗完成，核准上架實測（最低帳戶 1,000,000 NTD）**

### 2. MC12 v2.1 GA 回測績效（正式）
| 指標 | 數值 |
|------|------|
| 總交易次數 | 807 |
| 勝率 | 58.86% |
| Profit Factor | 1.448 |
| 淨利 | +1,997,000 NTD |
| 最大回撤 (MDD) | -278,800 NTD |
| MDD% | 27.2%（@1M 帳戶） |
| 年報酬率 | 31.1% |
| 初始資金 | 1,000,000 NTD |
| WFA WFE | 62.5%（5/8 窗口 OOS 獲利）|
| MC 95% MDD | ~270k（PASS@1M, FAIL@500k）|

> ⚠️ 以上為 MC12 15M 正式回測，非日線代理。完整分析見 `S1_NightMomentum_annotated.md` 及 `optimization/logs/B01_S1_NightMomentum.md`

### 3. 進場邏輯（v2.1）
- **做多進場**（純做多，空單已移除）：
  1. 當前時間在夜盤時段（15:00-05:00）
  2. 夜盤開盤後前 `LookbackBars`=11 根 K 棒形成開盤區間
  3. 區間寬度在 `RangeMinATR`~`RangeMaxATR` 倍 ATR 之間
  4. **波動率擴張**：快速 ATR / 慢速 ATR ≥ `VolRatioMin`=0.80（v2.1 核心）
  5. 價格突破開盤區間高點 + ATR × `EntryATRMult`=0.2
- **訊號確認**：Stop 單即時觸發

### 4. 出場邏輯（v2.1 ATR-Based）
- **停損**：EntryPrice - v_EntryATR × `StopATRMult`=2.75（ATR 凍結機制）
- **停利**：EntryPrice + v_EntryATR × `TargetATRMult`=2.0
- **追蹤停損**：獲利達 ATR × 2.75 後，在 ATR × 2.05 處設停損
- **時間出場**：05:00 強制平倉

### 5. 完整 PowerLanguage 程式碼（v2.1 GA 最佳化參數）

> 正式版原始碼：`S1_NightMomentum.pla` / `powerlanguage/STRATEGY_GEN_NightMomentum.txt`

```
{STRATEGY_GEN_NightMomentum}
{v2.1: ATR-Based + Volatility Expansion Filter}
{Category A: Night Session Opening Range Breakout}
{Direction: Long Only (Short removed: MC12 Short PF=0.93)}
{Timeframe: 15-min on TXF1}
{Parameters: MC12 v2.1 GA optimized (2020/01~2026/06, 1M capital)}

inputs:
    LookbackBars(11),
    ATRLen(11),
    EntryATRMult(0.2),
    RangeMinATR(0.9),
    RangeMaxATR(4.5),
    StopATRMult(2.75),
    TargetATRMult(2.0),
    TrailActATR(2.75),
    TrailOffATR(0.7),
    NightOpen(1500),
    ExitTime(0500),
    VolSlowLen(70),
    VolRatioMin(0.80);

variables:
    v_NightHigh(0), v_NightLow(999999), v_NightBarCount(0),
    v_RangeReady(false), v_IsNightSession(false),
    v_ATR(0), v_EntryATR(0), v_RangeWidth(0), v_Prev_MP(0),
    v_SlowATR(0), v_VolRatio(0), v_VolPass(false);

v_ATR = AvgTrueRange(ATRLen);
v_SlowATR = AvgTrueRange(VolSlowLen);
if v_SlowATR > 0 then v_VolRatio = v_ATR / v_SlowATR
else v_VolRatio = 1;
v_VolPass = (v_VolRatio >= VolRatioMin);

v_IsNightSession = (Time >= NightOpen) or (Time < ExitTime);

if Time >= NightOpen and Time[1] < NightOpen then begin
    v_NightHigh = 0; v_NightLow = 999999;
    v_NightBarCount = 0; v_RangeReady = false;
end;

if v_IsNightSession and v_RangeReady = false then begin
    v_NightBarCount = v_NightBarCount + 1;
    if High > v_NightHigh then v_NightHigh = High;
    if Low < v_NightLow then v_NightLow = Low;
    if v_NightBarCount >= LookbackBars then begin
        v_RangeWidth = v_NightHigh - v_NightLow;
        if v_ATR > 0 and
           v_RangeWidth >= v_ATR * RangeMinATR and
           v_RangeWidth <= v_ATR * RangeMaxATR then
            v_RangeReady = true;
    end;
end;

if v_RangeReady and v_IsNightSession and Time < ExitTime and v_VolPass then begin
    if v_Prev_MP <= 0 and v_ATR > 0 then
        buy ("LE_NM_Long") next bar at v_NightHigh + v_ATR * EntryATRMult stop;
end;

if MarketPosition = 1 and v_Prev_MP <= 0 then
    v_EntryATR = v_ATR;

if MarketPosition = 1 and v_EntryATR > 0 then begin
    sell ("LX_NM_SL") next bar at EntryPrice - v_EntryATR * StopATRMult stop;
    sell ("LX_NM_TP") next bar at EntryPrice + v_EntryATR * TargetATRMult limit;
    if MaxContractProfit / 200 >= v_EntryATR * TrailActATR then
        sell ("LX_NM_Trail") next bar at EntryPrice + v_EntryATR * (TrailActATR - TrailOffATR) stop;
end;

if Time >= ExitTime and Time < NightOpen then begin
    if MarketPosition = 1 then
        sell ("LX_NM_Time") next bar at market;
end;

v_Prev_MP = MarketPosition;
```

### 6. MC 設定建議
- **Data1**：TXF1，15 分鐘
- **Data2**：不需要

### 7. 優化方向（v2.1 已完成）
- 13 個參數全部 GA 最佳化完成（族群 500, 代數 400, 突變 0.08）
- 關鍵改動：RangeMinATR 0.2→0.9（嚴篩區間）、TargetATRMult 3.0→2.0（提前鎖利）
- **已解決的殺手問題**：v2.1 Vol Filter 解決低波動期假突破連虧

### 8. MC12 v2.1 GA 最佳化參數（2026-06-07 — 🟢上架實測）
```
LookbackBars=11, ATRLen=11, EntryATRMult=0.2,
RangeMinATR=0.9, RangeMaxATR=4.5,
StopATRMult=2.75, TargetATRMult=2.0,
TrailActATR=2.75, TrailOffATR=0.7,
NightOpen=1500, ExitTime=500,
VolSlowLen=70, VolRatioMin=0.80
```
- **Phase 1**：✅ PASS — 全參數高原 44~100%
- **Phase 2**：✅ PASS — WFE=62.5%（5/8 窗口），OOS 累計 +1,939,500
- **Phase 3**：✅ PASS@1M — MC 10k 次，95% MDD=27.2%，破產率 0.01%
- **最低帳戶**：1,000,000 NTD

---

## 策略 2：Inside Bar 日線突破策略

### 1. 策略概述
- **類別**：B 類（價格結構型）
- **操作方向**：★★★ 雙向 — 做多（MA↑）+ 做空（MA↓）★★★
- **賺什麼錢**：日線 Inside Bar = 市場猶豫/能量壓縮。隔日突破母線高低點時順勢進場，賺的是「壓縮後方向選擇的爆發行情」。
- **主交易週期**：30 分鐘
- **確認週期**：日線（Data2，偵測 Inside Bar + MA 方向）
- **預期交易頻率**：每月 3-6 筆
- **與現有策略的差異**：BL 是分鐘級盤整突破；本策略基於日線 K 棒型態，觸發頻率更低、持倉更長。

### 2. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 總交易次數 | 34 |
| 勝率 | 64.7% |
| Profit Factor | 4.61 |
| 淨利 | +791,754 NTD |
| 最大回撤 (MDD) | -63,879 NTD |
| CAGR | 27.0% |
| 年化報酬 | +146,424 NTD/年 |
| 盈虧比 | 2.51 |

### 3. 進場邏輯
- **做多**：昨日為 Inside Bar + 日線 20MA 向上 + 今日 30M 收盤突破昨高 + 5 點
- **做空**：昨日為 Inside Bar + 日線 20MA 向下 + 今日 30M 收盤跌破昨低 - 5 點
- **訊號確認**：30 分鐘收盤確認

### 4. 出場邏輯
- **停損**：母線區間 × 50%（最低 40 點）
- **停利**：母線區間 × 1.5 倍
- **時間出場**：持倉超過 30 根 K 棒

### 5. 完整 PowerLanguage 程式碼

```
{STRATEGY_GEN_InsideBarBreak - Inside Bar 日線突破策略}
{B類：日線 Inside Bar 隔日突破}
{操作方向：★雙向（做多+做空，MA方向過濾）}

inputs:
    BreakOffset(5),
    StopPct(50),
    TargetMult(1.5),
    MinMotherRange(50),
    MaxMotherRange(400),
    MALen(20),
    MaxBarsHeld(30),
    MinStopPts(40);

variables:
    v_IsInsideBar(false),
    v_MotherHigh(0),
    v_MotherLow(0),
    v_MotherRange(0),
    v_StopDist(0),
    v_TargetDist(0),
    v_MA_Up(false),
    v_MA_Down(false),
    v_EntryBar(0),
    v_Prev_MP(0);

v_IsInsideBar = (High of Data2[1] < High of Data2[2]) and
                (Low of Data2[1] > Low of Data2[2]);

v_MotherHigh = High of Data2[2];
v_MotherLow = Low of Data2[2];
v_MotherRange = v_MotherHigh - v_MotherLow;

v_MA_Up = Close of Data2[1] > Average(Close of Data2, MALen)[1];
v_MA_Down = Close of Data2[1] < Average(Close of Data2, MALen)[1];

v_StopDist = MaxList(v_MotherRange * StopPct / 100, MinStopPts);
v_TargetDist = v_MotherRange * TargetMult;

if v_IsInsideBar and
   v_MotherRange >= MinMotherRange and
   v_MotherRange <= MaxMotherRange then begin

    if v_Prev_MP <= 0 and v_MA_Up and
       Close > High of Data2[1] + BreakOffset then begin
        buy ("LE_IB_Long") next bar at market;
        v_EntryBar = BarNumber;
    end;

    if v_Prev_MP >= 0 and v_MA_Down and
       Close < Low of Data2[1] - BreakOffset then begin
        sell short ("SE_IB_Short") next bar at market;
        v_EntryBar = BarNumber;
    end;
end;

if MarketPosition = 1 then begin
    sell ("LX_IB_SL") next bar at EntryPrice - v_StopDist stop;
    sell ("LX_IB_TP") next bar at EntryPrice + v_TargetDist limit;
    if BarNumber - v_EntryBar >= MaxBarsHeld then
        sell ("LX_IB_Time") next bar at market;
end;

if MarketPosition = -1 then begin
    buy to cover ("SX_IB_SL") next bar at EntryPrice + v_StopDist stop;
    buy to cover ("SX_IB_TP") next bar at EntryPrice - v_TargetDist limit;
    if BarNumber - v_EntryBar >= MaxBarsHeld then
        buy to cover ("SX_IB_Time") next bar at market;
end;

v_Prev_MP = MarketPosition;
```

### 6. MC 設定建議
- **Data1**：TXF1，30 分鐘
- **Data2**：TXF1，日線

### 7. 優化方向
- `BreakOffset`（0-15）：假突破過濾強度
- `StopPct`（30-70）：停損佔母線區間比例
- `TargetMult`（1.0-2.5）：勝率型 vs 盈虧比型
- **殺手問題**：Inside Bar 出現頻率低（年均 <30 次），樣本不足，統計顯著性存疑。

---

## 策略 3：波動率收縮爆發策略

### 1. 策略概述
- **類別**：C 類（波動率型）
- **操作方向**：★★★ 雙向 — 做多 + 做空 ★★★
- **賺什麼錢**：BB BandWidth 降至歷史低位 = 波動率極度壓縮 → 即將爆發。賺的是「波動率週期從壓縮轉擴張時的方向性突破」。
- **主交易週期**：60 分鐘
- **確認週期**：無
- **預期交易頻率**：每月 4-8 筆
- **與現有策略的差異**：TL 用 ATR 通道 + 多時間框架確認；本策略用 BandWidth 百分位作「準備狀態」，純波動率週期理論。

### 2. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 總交易次數 | 33 |
| 勝率 | 36.4% |
| Profit Factor | 0.88 |
| 淨利 | -115,622 NTD |
| 最大回撤 (MDD) | -645,467 NTD |
| CAGR | — |
| 年化報酬 | -23,127 NTD/年 |
| 盈虧比 | 1.54 |

> ⚠️ **日線回測虧損**。此策略設計在 60M 週期運行，日線上 BB 收縮訊號特性不同。務必在 MC12 用 60M 數據重新回測。中軌出場可能在日線上過早觸發。

### 3. 進場邏輯
- **做多**：BandWidth ≤ 過去 120 期的 20 百分位 + 收盤 > 上軌
- **做空**：同上 BandWidth 條件 + 收盤 < 下軌
- **訊號確認**：60M 收盤確認

### 4. 出場邏輯
- **停損**：ATR(14) × 1.5 倍
- **停利**：ATR(14) × 3.0 倍
- **中軌出場**：進場後 ≥3 根 K 棒，收盤回穿 MA 平倉
- **時間出場**：持倉超過 40 根 K 棒

### 5. 完整 PowerLanguage 程式碼

```
{STRATEGY_GEN_VolSqueeze - 波動率收縮爆發策略}
{C類：Bollinger BandWidth 收縮後突破}
{操作方向：★雙向（做多+做空）}

inputs:
    BBLen(20),
    BBStd(2.0),
    BWLookback(120),
    BWPctile(20),
    ATRLen(14),
    StopATRMult(1.5),
    TargetATRMult(3.0),
    MaxBars(40),
    UseMidExit(true);

variables:
    v_UpperBand(0),
    v_LowerBand(0),
    v_MidBand(0),
    v_BandWidth(0),
    v_BWRank(0),
    v_BWCount(0),
    v_ATR(0),
    v_StopDist(0),
    v_TargetDist(0),
    v_Squeeze(false),
    v_EntryBar(0),
    v_Prev_MP(0),
    v_i(0);

v_MidBand = Average(Close, BBLen);
v_UpperBand = v_MidBand + BBStd * StandardDev(Close, BBLen, 1);
v_LowerBand = v_MidBand - BBStd * StandardDev(Close, BBLen, 1);

if v_MidBand > 0 then
    v_BandWidth = (v_UpperBand - v_LowerBand) / v_MidBand * 100
else
    v_BandWidth = 0;

v_BWCount = 0;
for v_i = 1 to BWLookback begin
    if v_BandWidth[v_i] < v_BandWidth then
        v_BWCount = v_BWCount + 1;
end;
v_BWRank = v_BWCount / BWLookback * 100;

v_Squeeze = (v_BWRank <= BWPctile);

v_ATR = AvgTrueRange(ATRLen);
v_StopDist = v_ATR * StopATRMult;
v_TargetDist = v_ATR * TargetATRMult;

if v_Squeeze then begin
    if v_Prev_MP <= 0 and Close > v_UpperBand then begin
        buy ("LE_VS_Long") next bar at market;
        v_EntryBar = BarNumber;
    end;
    if v_Prev_MP >= 0 and Close < v_LowerBand then begin
        sell short ("SE_VS_Short") next bar at market;
        v_EntryBar = BarNumber;
    end;
end;

if MarketPosition = 1 then begin
    sell ("LX_VS_SL") next bar at EntryPrice - v_StopDist stop;
    sell ("LX_VS_TP") next bar at EntryPrice + v_TargetDist limit;
    if UseMidExit and BarNumber - v_EntryBar >= 3 and Close < v_MidBand then
        sell ("LX_VS_Mid") next bar at market;
    if BarNumber - v_EntryBar >= MaxBars then
        sell ("LX_VS_Time") next bar at market;
end;

if MarketPosition = -1 then begin
    buy to cover ("SX_VS_SL") next bar at EntryPrice + v_StopDist stop;
    buy to cover ("SX_VS_TP") next bar at EntryPrice - v_TargetDist limit;
    if UseMidExit and BarNumber - v_EntryBar >= 3 and Close > v_MidBand then
        buy to cover ("SX_VS_Mid") next bar at market;
    if BarNumber - v_EntryBar >= MaxBars then
        buy to cover ("SX_VS_Time") next bar at market;
end;

v_Prev_MP = MarketPosition;
```

### 6. MC 設定建議
- **Data1**：TXF1，60 分鐘
- **Data2**：不需要
- 需至少 120 根 60M K 棒預熱期

### 7. 優化方向
- `BWPctile`（10-30）：收縮門檻嚴格度
- `StopATRMult`（1.0-2.5）：停損空間
- `BBLen`（15-30）：BB 靈敏度
- **殺手問題**：低波動可持續很久，Squeeze 突破可能連續假突破導致連停。建議加 ADX 或成交量確認。

---

## 策略 4：MACD 背離反轉策略

### 1. 策略概述
- **類別**：D 類（動量型，逆勢）
- **操作方向**：★★★ 雙向 — 底背離做多 + 頂背離做空（逆勢反轉）★★★
- **賺什麼錢**：趨勢動能衰竭的反轉。價格創新高/低但 MACD 柱狀體未跟隨 = 動能枯竭 → 反轉。賺的是「趨勢末端的均值回歸」。
- **主交易週期**：60 分鐘
- **確認週期**：無
- **預期交易頻率**：每月 3-7 筆
- **與現有策略的差異**：TL/TS 順勢；本策略完全逆勢，用 MACD 背離 + RSI 極值做反轉。

### 2. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 總交易次數 | 2 |
| 勝率 | 100% |
| Profit Factor | — |
| 淨利 | +38,000 NTD |
| 最大回撤 (MDD) | 0 NTD |
| CAGR | — |
| 年化報酬 | — |
| 盈虧比 | — |

> ⚠️ **僅 2 筆交易，無統計意義**。日線上同時滿足所有背離條件極為困難。此策略設計在 60M 週期，預期在 MC12 回測可產生每月 3-7 筆。務必用 60M 數據驗證。

### 3. 進場邏輯
- **底背離做多**：價格 50 期新低 + MACD Hist 低點墊高 + Hist 翻正 + RSI < 35
- **頂背離做空**：價格 50 期新高 + MACD Hist 高點降低 + Hist 翻負 + RSI > 65
- **訊號確認**：Histogram 翻轉確認（滯後 1 根）

### 4. 出場邏輯
- **停損**：近 `SwingLen` 根 K 棒極值 + 15 點緩衝
- **停利**：固定 100 點
- **時間出場**：持倉超過 20 根 K 棒

### 5. 完整 PowerLanguage 程式碼

```
{STRATEGY_GEN_MACDDivergence - MACD 背離反轉策略}
{D類：MACD 背離做反轉}
{操作方向：★雙向（做多+做空，逆勢反轉）}

inputs:
    FastLen(12),
    SlowLen(26),
    SignalLen(9),
    PriceLookback(50),
    SwingLen(10),
    HistLookback(30),
    RSILen(14),
    RSIOversold(35),
    RSIOverbought(65),
    StopBuffer(15),
    TargetPts(100),
    MaxBars(20);

variables:
    v_MACD(0),
    v_Signal(0),
    v_Hist(0),
    v_PriceNewLow(false),
    v_PriceNewHigh(false),
    v_HistPrevLow(0),
    v_HistCurrLow(0),
    v_HistPrevHigh(0),
    v_HistCurrHigh(0),
    v_BullDiv(false),
    v_BearDiv(false),
    v_RSI(0),
    v_SwingLow(0),
    v_SwingHigh(0),
    v_EntryBar(0),
    v_Prev_MP(0);

v_MACD = MACD(Close, FastLen, SlowLen);
v_Signal = XAverage(v_MACD, SignalLen);
v_Hist = v_MACD - v_Signal;
v_RSI = RSI(Close, RSILen);

v_PriceNewLow = Low = Lowest(Low, PriceLookback);
v_PriceNewHigh = High = Highest(High, PriceLookback);

v_SwingLow = Lowest(Low, SwingLen);
v_SwingHigh = Highest(High, SwingLen);

v_HistCurrLow = Lowest(v_Hist, SwingLen);
v_HistPrevLow = Lowest(v_Hist, HistLookback)[SwingLen];

v_HistCurrHigh = Highest(v_Hist, SwingLen);
v_HistPrevHigh = Highest(v_Hist, HistLookback)[SwingLen];

v_BullDiv = v_PriceNewLow and
            v_HistCurrLow > v_HistPrevLow and
            v_Hist > 0 and v_Hist[1] <= 0 and
            v_RSI < RSIOversold;

v_BearDiv = v_PriceNewHigh and
            v_HistCurrHigh < v_HistPrevHigh and
            v_Hist < 0 and v_Hist[1] >= 0 and
            v_RSI > RSIOverbought;

if v_Prev_MP <= 0 and v_BullDiv then begin
    buy ("LE_MD_Long") next bar at market;
    v_EntryBar = BarNumber;
end;

if v_Prev_MP >= 0 and v_BearDiv then begin
    sell short ("SE_MD_Short") next bar at market;
    v_EntryBar = BarNumber;
end;

if MarketPosition = 1 then begin
    sell ("LX_MD_SL") next bar at v_SwingLow - StopBuffer stop;
    sell ("LX_MD_TP") next bar at EntryPrice + TargetPts limit;
    if BarNumber - v_EntryBar >= MaxBars then
        sell ("LX_MD_Time") next bar at market;
end;

if MarketPosition = -1 then begin
    buy to cover ("SX_MD_SL") next bar at v_SwingHigh + StopBuffer stop;
    buy to cover ("SX_MD_TP") next bar at EntryPrice - TargetPts limit;
    if BarNumber - v_EntryBar >= MaxBars then
        buy to cover ("SX_MD_Time") next bar at market;
end;

v_Prev_MP = MarketPosition;
```

### 6. MC 設定建議
- **Data1**：TXF1，60 分鐘
- **Data2**：不需要

### 7. 優化方向
- `RSIOversold/RSIOverbought`（30-40 / 60-70）
- `TargetPts`（60-150）
- `PriceLookback`（30-80）
- **殺手問題**：「背離可以再背離」。強趨勢中連續觸發 5-8 次假訊號 → 嚴重連損。考慮加 ADX < 25 過濾。

---

## 策略 5：結算週效應策略

### 1. 策略概述
- **類別**：E 類（統計型）
- **操作方向**：★★★ 結算前 → 做空 / 結算後 → 做多 ★★★
- **賺什麼錢**：台指期每月第三個週三結算。統計上結算前 2 天偏空（法人壓低結算價），結算後偏多（壓力釋放反彈）。賺的是「結算日前後的結構性方向偏差」。
- **主交易週期**：日線
- **確認週期**：無
- **預期交易頻率**：每月 1-2 筆
- **與現有策略的差異**：純日曆效應，不依賴任何技術指標。

### 2. 模擬回測績效（日線）
| 指標 | 數值 |
|------|------|
| 總交易次數 | 83 |
| 勝率 | 34.9% |
| Profit Factor | 0.60 |
| 淨利 | -367,000 NTD |
| 最大回撤 (MDD) | -451,000 NTD |
| CAGR | — |
| 年化報酬 | -58,638 NTD/年 |
| 盈虧比 | 1.12 |

> ⚠️ **回測虧損**。結算週效應在 2020-2026 台指期統計上不顯著，或被其他因子覆蓋。此策略風險最高，建議僅作為研究參考，不建議直接實盤。可嘗試只做結算後做多（去掉結算前做空）或加更嚴格的濾網。

### 3. 進場邏輯
- **做空（結算前）**：結算日前 2 個交易日 + 當日收陰線
- **做多（結算後）**：結算日後 1 個交易日 + 收盤 > 5MA
- **訊號確認**：日線收盤確認

### 4. 出場邏輯
- **停損**：固定 80 點
- **停利**：固定 100 點
- **時間出場**：持倉超過 3 個交易日

### 5. 完整 PowerLanguage 程式碼

```
{STRATEGY_GEN_SettlementWeek - 結算週效應策略}
{E類：結算日前後的統計偏差}
{操作方向：★結算前做空 / 結算後做多}

inputs:
    DaysBefore(2),
    DaysAfter(1),
    StopPts(80),
    TargetPts(100),
    HoldDays(3),
    UseCloseFilter(true),
    MAFilterLen(5);

variables:
    v_DOM(0),
    v_DOW(0),
    v_IsSettleDay(false),
    v_DaysFromSettle(0),
    v_EntryBar(0),
    v_Prev_MP(0),
    v_i(0),
    v_Month(0);

v_DOW = DayOfWeek(Date);
v_DOM = DayOfMonth(Date);
v_Month = Month(Date);

// 第三個週三：DOM 15-21 且為週三
v_IsSettleDay = (v_DOW = 3) and (v_DOM >= 15) and (v_DOM <= 21);

// 結算後天數
v_DaysFromSettle = 0;
for v_i = 1 to 10 begin
    if DayOfWeek(Date[v_i]) = 3 and
       DayOfMonth(Date[v_i]) >= 15 and
       DayOfMonth(Date[v_i]) <= 21 and
       Month(Date[v_i]) = v_Month then begin
        v_DaysFromSettle = v_i;
        v_i = 11;
    end;
end;

// 結算前做空：結算週的週一或週二
condition1 = (v_DOM >= 13) and (v_DOM <= 21) and
             (v_DOW >= 1) and (v_DOW <= 2) and
             DaysBefore >= (3 - v_DOW);

// 結算後做多
condition2 = v_DaysFromSettle >= 1 and v_DaysFromSettle <= DaysAfter;

if v_Prev_MP >= 0 and condition1 then begin
    if UseCloseFilter = false or (UseCloseFilter and Close < Open) then begin
        sell short ("SE_SW_Short") next bar at market;
        v_EntryBar = BarNumber;
    end;
end;

if v_Prev_MP <= 0 and condition2 then begin
    if UseCloseFilter = false or (UseCloseFilter and Close > Average(Close, MAFilterLen)) then begin
        buy ("LE_SW_Long") next bar at market;
        v_EntryBar = BarNumber;
    end;
end;

if MarketPosition = 1 then begin
    sell ("LX_SW_SL") next bar at EntryPrice - StopPts stop;
    sell ("LX_SW_TP") next bar at EntryPrice + TargetPts limit;
    if BarNumber - v_EntryBar >= HoldDays then
        sell ("LX_SW_Time") next bar at market;
end;

if MarketPosition = -1 then begin
    buy to cover ("SX_SW_SL") next bar at EntryPrice + StopPts stop;
    buy to cover ("SX_SW_TP") next bar at EntryPrice - TargetPts limit;
    if BarNumber - v_EntryBar >= HoldDays then
        buy to cover ("SX_SW_Time") next bar at market;
end;

v_Prev_MP = MarketPosition;
```

### 6. MC 設定建議
- **Data1**：TXF1，日線
- **Data2**：不需要

### 7. 優化方向
- `DaysBefore`（1-3）
- `HoldDays`（2-5）
- `StopPts`（60-120）
- **殺手問題**：日曆效應可能是數據挖掘產物。結算制度/大戶行為改變即失效。建議考慮只保留結算後做多，或加上趨勢方向過濾。
