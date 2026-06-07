# TXF1 量化策略批次 03
> 生成日期：2026-06-07
> 類別組合：A + E + C + F + B
> 回測區間：2020/04/08 ~ 2026/06/05（日線代理回測）
> 資料來源：^TWII 日線代理（日內策略需在 MC 用分鐘數據驗證）

---

## 回測績效總覽

| # | 策略名稱 | 操作方向 | 操作週期 | 賺什麼錢？ | 交易數 | 勝率 | PF | 淨利(NTD) | MDD(NTD) | CAGR | 年化報酬(NTD) |
|---|---------|---------|---------|-----------|-------|------|-----|----------|----------|------|-------------|
| S11 | MiddayCompression | ★做多 | 45M | 盤中窄幅壓縮後突破的方向慣性 | 22 | 54.5% | 2.28 | +639,782 | -195,541 | 14.3% | +103,904 |
| S12 | WeekdayMomentum | ★雙向 | 日線 | 週一二連續動量在週三的延續慣性 | 60 | 46.7% | 0.90 | -115,128 | -381,827 | -4.2% | -18,697 |
| S13 | VolCollapseShort | ★做空 | 30M | 極低波動後向下爆發的動能 | 7 | 42.9% | 1.58 | +65,070 | -86,798 | 2.0% | +10,568 |
| S14 | TripleTFTrend | ★雙向 | 15M+60M+日線 | 多時框均線共振後回檔進場的趨勢延續 | 66 | 51.5% | 1.86 | +2,457,619 | -820,336 | 33.5% | +399,131 |
| S15 | BBReversion | ★雙向 | 60M | 布林極端後回歸中軌的均值回歸利潤 | 13 | 76.9% | 9.03 | +934,134 | -67,642 | 18.7% | +151,708 |

> ⚠️ **重要提醒**：以上為 Python 日線代理回測。S11 壓縮突破在 45M 級別樣本量會增加。S12 日線回測為負但在分鐘級別可能改善。S13 交易極少(7筆)，統計顯著性不足。S15 高勝率/高PF 可能存在日線粒度偏差，須 MC 驗證。

---

## 策略 S11：午盤壓縮突破策略

### 1. 策略概述
- **類別**：A 類（時段型）
- **操作方向**：★★★ 做多 ★★★
- **賺什麼錢**：台指期盤中經常出現上午震盪收斂、午盤（12:00-13:30）突破的節奏。本策略捕捉 ATR 壓縮（短期波動率 < 長期 75%）後向上突破的方向慣性。本質上賺的是「壓縮後爆發的多方延續」。
- **主交易週期**：45 分鐘
- **確認週期**：無（純日內壓縮突破）
- **預期交易頻率**：每月 3-5 筆
- **與現有策略差異**：BL 為盤整區間突破，依賴固定區間；本策略依賴 ATR 壓縮比率動態偵測壓縮，且限定午盤時段。

### 2. 進場邏輯
**多方條件（全部滿足）：**
1. ATR(5) < ATR(14) × 0.75（短期波動率壓縮）
2. Close > SMA(20)（趨勢偏多）
3. 前一根 K 棒振幅 < 1.2%（窄幅日）
4. 當前 K 棒收盤 > 前一根最高價（突破確認）

### 3. 出場邏輯
- **停損**：進場價 − 1.8 × ATR(14)
- **停利**：進場價 + 3.0 × ATR(14)
- **時間出場**：持倉滿 5 根 K 棒強制平倉
- **追蹤停損**：無（固定停損停利 + 時間出場）

### 4. PowerLanguage 程式碼

```
// ===== STRATEGY_GEN_S11_MiddayCompression =====
// A類-時段型 | 做多 | 45M | ATR壓縮午盤突破

inputs:
    ATR_Fast(5),
    ATR_Slow(14),
    ATR_Ratio(0.75),
    SMA_Len(20),
    Range_Thresh(1.2),
    SL_Mult(1.8),
    TP_Mult(3.0),
    MaxBars(5);

variables:
    v_ATR_Fast(0),
    v_ATR_Slow(0),
    v_SMA(0),
    v_RangePct(0),
    v_EntryPrice(0),
    v_StopLoss(0),
    v_TakeProfit(0),
    v_BarsSinceEntry(0),
    v_Prev_MP(0);

v_ATR_Fast = AvgTrueRange(ATR_Fast);
v_ATR_Slow = AvgTrueRange(ATR_Slow);
v_SMA = Average(Close, SMA_Len);
v_RangePct = (High - Low) / Close * 100;

v_Prev_MP = MarketPosition[1];

// 進場：午盤壓縮突破做多
if MarketPosition = 0 then begin
    if v_ATR_Fast < v_ATR_Slow * ATR_Ratio
       and Close[1] > v_SMA[1]
       and v_RangePct[1] < Range_Thresh
       and Time >= 1200 and Time <= 1330 then begin
        buy ("S11_L") next bar at High stop;
    end;
end;

// 追蹤進場價和停損停利
if MarketPosition = 1 and v_Prev_MP <> 1 then begin
    v_EntryPrice = EntryPrice;
    v_StopLoss = v_EntryPrice - SL_Mult * v_ATR_Slow;
    v_TakeProfit = v_EntryPrice + TP_Mult * v_ATR_Slow;
    v_BarsSinceEntry = 0;
end;

if MarketPosition = 1 then begin
    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    // 停損
    sell ("S11_SL") next bar at v_StopLoss stop;

    // 停利
    sell ("S11_TP") next bar at v_TakeProfit limit;

    // 時間出場
    if v_BarsSinceEntry >= MaxBars then
        sell ("S11_TimeExit") next bar at market;
end;
```

### 5. MC 設定建議
- **Data1**：TXF1 45 分鐘
- **Data2**：不需要
- **注意**：時段過濾 1200-1330，確保交易所時段正確

### 6. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 交易數 | 22 |
| 勝率 | 54.5% |
| Profit Factor | 2.28 |
| 淨利 | +639,782 NTD |
| MDD | -195,541 NTD |
| CAGR | 14.3% |
| 年化報酬 | +103,904 NTD |
| 盈虧比 | 1.90 |

### 7. 優化方向
1. **ATR_Ratio**：0.60 ~ 0.85，步進 0.05（壓縮程度門檻）
2. **SL_Mult**：1.2 ~ 2.5，步進 0.2（停損寬度）
3. **Range_Thresh**：0.8 ~ 1.8，步進 0.2（窄幅判定）

### 8. 殺手問題
午盤突破在趨勢盤有效，但橫盤震盪市場容易被假突破洗出。45M 壓縮週期較長，可能在急漲急跌盤錯過快速突破窗口。日線代理僅 22 筆，統計意義有限。

---

## 策略 S12：週內動量延續策略

### 1. 策略概述
- **類別**：E 類（統計型）
- **操作方向**：★★★ 雙向（多+空）★★★
- **賺什麼錢**：週一、週二若連續同向收漲/收跌超過 0.3%，週三有較高機率延續動量方向。本質上賺的是「機構資金佈局在週初形成的慣性延續」。
- **主交易週期**：日線
- **確認週期**：無
- **預期交易頻率**：每月 3-5 筆
- **與現有策略差異**：S5 為結算週效應（月週期），本策略為週一二動量→週三延續（週內統計模式），邏輯完全不同。

### 2. 進場邏輯
**多方條件（全部滿足）：**
1. 當日為週三
2. 週一收盤漲幅 > 0.3%（(Close-Open)/Open）
3. 週二收盤漲幅 > 0.3%
4. 週二收盤 > SMA(20)（趨勢偏多確認）

**空方條件（全部滿足）：**
1. 當日為週三
2. 週一收盤跌幅 > 0.3%
3. 週二收盤跌幅 > 0.3%
4. 週二收盤 < SMA(20)（趨勢偏空確認）

### 3. 出場邏輯
- **停損**：1.5 × ATR(14)
- **停利**：2.0 × ATR(14)
- **時間出場**：當日收盤強制平倉（日內交易）
- **追蹤停損**：無

### 4. PowerLanguage 程式碼

```
// ===== STRATEGY_GEN_S12_WeekdayMomentum =====
// E類-統計型 | 雙向 | 日線 | 週一二動量→週三延續

inputs:
    MinDayReturn(0.3),
    SMA_Len(20),
    SL_Mult(1.5),
    TP_Mult(2.0);

variables:
    v_MonReturn(0),
    v_TueReturn(0),
    v_SMA(0),
    v_ATR(0),
    v_EntryPrice(0),
    v_StopLoss(0),
    v_TakeProfit(0),
    v_Prev_MP(0);

v_SMA = Average(Close, SMA_Len);
v_ATR = AvgTrueRange(14);

// 計算週一、週二漲跌幅
if DayOfWeek(Date) = 3 then begin  // Wednesday = 3
    v_MonReturn = (Close[2] - Open[2]) / Open[2] * 100;
    v_TueReturn = (Close[1] - Open[1]) / Open[1] * 100;
end;

v_Prev_MP = MarketPosition[1];

// 進場
if MarketPosition = 0 and DayOfWeek(Date) = 3 then begin
    // 多方：週一二連漲 + 趨勢偏多
    if v_MonReturn > MinDayReturn
       and v_TueReturn > MinDayReturn
       and Close[1] > v_SMA[1] then begin
        buy ("S12_L") next bar at market;
    end;

    // 空方：週一二連跌 + 趨勢偏空
    if v_MonReturn < -MinDayReturn
       and v_TueReturn < -MinDayReturn
       and Close[1] < v_SMA[1] then begin
        sell short ("S12_S") next bar at market;
    end;
end;

// 多方出場
if MarketPosition = 1 then begin
    if v_Prev_MP <> 1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice - SL_Mult * v_ATR;
        v_TakeProfit = v_EntryPrice + TP_Mult * v_ATR;
    end;
    sell ("S12_L_SL") next bar at v_StopLoss stop;
    sell ("S12_L_TP") next bar at v_TakeProfit limit;
    // 收盤出場
    if Time >= 1325 then
        sell ("S12_L_EOD") next bar at market;
end;

// 空方出場
if MarketPosition = -1 then begin
    if v_Prev_MP <> -1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice + SL_Mult * v_ATR;
        v_TakeProfit = v_EntryPrice - TP_Mult * v_ATR;
    end;
    buy to cover ("S12_S_SL") next bar at v_StopLoss stop;
    buy to cover ("S12_S_TP") next bar at v_TakeProfit limit;
    if Time >= 1325 then
        buy to cover ("S12_S_EOD") next bar at market;
end;
```

### 5. MC 設定建議
- **Data1**：TXF1 日線
- **Data2**：不需要
- **注意**：DayOfWeek 在 MC 中：1=Mon, 2=Tue, 3=Wed

### 6. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 交易數 | 60 |
| 勝率 | 46.7% |
| Profit Factor | 0.90 |
| 淨利 | -115,128 NTD |
| MDD | -381,827 NTD |
| CAGR | -4.2% |
| 年化報酬 | -18,697 NTD |
| 盈虧比 | 1.02 |

> ⚠️ 日線代理為負，但統計型策略在日內分鐘級別的進出場精度會顯著改善。建議在 MC 用 15M 或 30M 驗證。

### 7. 優化方向
1. **MinDayReturn**：0.2 ~ 0.6，步進 0.05（動量門檻）
2. **SL_Mult**：1.0 ~ 2.5，步進 0.25（停損倍數）
3. **TP_Mult**：1.5 ~ 3.5，步進 0.25（停利倍數）

### 8. 殺手問題
週三不一定延續動量，尤其在重大事件（央行決策、美股暴跌）衝擊下動量可能反轉。台指期受國際盤影響大，純依賴週內統計模式容易在事件驅動市場失效。

---

## 策略 S13：波動率極低爆發空方策略

### 1. 策略概述
- **類別**：C 類（波動率型）
- **操作方向**：★★★ 做空 ★★★
- **賺什麼錢**：當 ATR 降至近 60 日最低 20%，市場處於「暴風雨前的寧靜」。若此時價格在 SMA20 之下且 MACD 偏空，向下突破往往引發恐慌性賣壓。賺的是「低波動壓縮後空方爆發的動能利潤」。
- **主交易週期**：30 分鐘
- **確認週期**：日線（SMA20 + MACD）
- **預期交易頻率**：每月 1-2 筆（低頻精選）
- **與現有策略差異**：TS 用均線+動量確認做空，屬趨勢跟隨；本策略依賴波動率百分位極低值做觸發，屬於波動率爆發策略，進場邏輯不同。

### 2. 進場邏輯
**空方條件（全部滿足）：**
1. ATR(14) 位於過去 60 日的 20% 百分位以下（極低波動）
2. 收盤價 < SMA(20)（趨勢偏空）
3. 收盤跌破 10 日最低點 − 0.3 × ATR(14)（帶力度的突破）
4. MACD 柱狀體 < 0（空方動能確認）

### 3. 出場邏輯
- **停損**：進場價 + 2.0 × ATR(14)
- **停利**：進場價 − 2.5 × ATR(14)
- **時間出場**：持倉滿 7 根 K 棒強制平倉
- **追蹤停損**：無

### 4. PowerLanguage 程式碼

```
// ===== STRATEGY_GEN_S13_VolCollapseShort =====
// C類-波動率型 | 做空 | 30M | ATR極低百分位空方爆發

inputs:
    ATR_Len(14),
    Pctile_Lookback(60),
    Pctile_Thresh(20),
    SMA_Len(20),
    Lowest_Len(10),
    Break_Mult(0.3),
    SL_Mult(2.0),
    TP_Mult(2.5),
    MaxBars(7);

variables:
    v_ATR(0),
    v_SMA(0),
    v_LowestL(0),
    v_MACD(0),
    v_Signal(0),
    v_Hist(0),
    v_ATR_Rank(0),
    v_Count(0),
    v_EntryPrice(0),
    v_StopLoss(0),
    v_TakeProfit(0),
    v_BarsSinceEntry(0),
    v_Prev_MP(0),
    v_i(0);

v_ATR = AvgTrueRange(ATR_Len);
v_SMA = Average(Close, SMA_Len);
v_LowestL = Lowest(Low, Lowest_Len);
v_MACD = MACD(Close, 12, 26);
v_Signal = XAverage(v_MACD, 9);
v_Hist = v_MACD - v_Signal;

// 計算 ATR 百分位排名
v_Count = 0;
for v_i = 1 to Pctile_Lookback begin
    if v_ATR <= v_ATR[v_i] then
        v_Count = v_Count + 1;
end;
v_ATR_Rank = v_Count / Pctile_Lookback * 100;

v_Prev_MP = MarketPosition[1];

// 進場：ATR極低 + 趨勢偏空 + 跌破支撐 + MACD空
if MarketPosition = 0 then begin
    if v_ATR_Rank <= Pctile_Thresh
       and Close[1] < v_SMA[1]
       and Close < v_LowestL[1] - Break_Mult * v_ATR
       and v_Hist[1] < 0 then begin
        sell short ("S13_S") next bar at Low stop;
    end;
end;

// 出場
if MarketPosition = -1 then begin
    if v_Prev_MP <> -1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice + SL_Mult * v_ATR;
        v_TakeProfit = v_EntryPrice - TP_Mult * v_ATR;
        v_BarsSinceEntry = 0;
    end;

    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    buy to cover ("S13_SL") next bar at v_StopLoss stop;
    buy to cover ("S13_TP") next bar at v_TakeProfit limit;

    if v_BarsSinceEntry >= MaxBars then
        buy to cover ("S13_TimeExit") next bar at market;
end;
```

### 5. MC 設定建議
- **Data1**：TXF1 30 分鐘
- **Data2**：TXF1 日線（可選，用於確認 SMA20）
- **MaxBarsBack**：至少 80（60 日百分位 + ATR）

### 6. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 交易數 | 7 |
| 勝率 | 42.9% |
| Profit Factor | 1.58 |
| 淨利 | +65,070 NTD |
| MDD | -86,798 NTD |
| CAGR | 2.0% |
| 年化報酬 | +10,568 NTD |
| 盈虧比 | 2.11 |

> ⚠️ 僅 7 筆交易，統計顯著性極低。30M 級別交易數會增加。此策略定位為「低頻精選空方」，用盈虧比 > 2 彌補低勝率。

### 7. 優化方向
1. **Pctile_Thresh**：10 ~ 30，步進 5（波動率門檻嚴/鬆）
2. **Break_Mult**：0.1 ~ 0.5，步進 0.1（突破力度要求）
3. **TP_Mult**：2.0 ~ 4.0，步進 0.5（停利目標）

### 8. 殺手問題
ATR 極低 + 趨勢偏空的組合極少觸發（6年僅7筆），在 30M 可能增加至 30-50 筆但仍屬低頻。最大風險是低波動期反而向上爆發（V轉），空方被停損出場。

---

## 策略 S14：三時框共振趨勢策略

### 1. 策略概述
- **類別**：F 類（多時間框架型）
- **操作方向**：★★★ 雙向（多+空）★★★
- **賺什麼錢**：當 SMA(5) > SMA(20) > SMA(60) 三條均線完美排列時，趨勢確立。等待價格回檔至 SMA(5) 附近再進場，搭順風車。賺的是「多時框共振確認後，回檔進場的趨勢延續利潤」。
- **主交易週期**：15 分鐘
- **確認週期**：60 分鐘 + 日線（三時框對齊）
- **預期交易頻率**：每月 5-10 筆
- **與現有策略差異**：TL 用 ATR 通道突破進場，BL 用盤整區間突破；本策略用三時框均線排列 + 回檔到短均線作為進場觸發，邏輯為「趨勢確認後等回檔」而非「突破追價」。

### 2. 進場邏輯
**多方條件（全部滿足）：**
1. SMA(5) > SMA(20) > SMA(60)（多方完美排列）
2. RSI(14) 介於 40-70（非超買區）
3. 前一根 Low 接近 SMA(5)（回檔至短均線，允許 0.5% 容差）
4. 當前 K 棒收盤 > 前一根最高價（反彈確認）

**空方條件（全部滿足）：**
1. SMA(5) < SMA(20) < SMA(60)（空方完美排列）
2. RSI(14) 介於 30-60（非超賣區）
3. 前一根 High 接近 SMA(5)（反彈至短均線，允許 0.5% 容差）
4. 當前 K 棒收盤 < 前一根最低價（再度轉弱確認）

### 3. 出場邏輯
- **停損**：2.0 × ATR(14)
- **追蹤停損**：持倉 > 2 根 K 棒後啟動，距離 = 2.5 × ATR(14)
- **時間出場**：持倉滿 10 根 K 棒強制平倉
- **停利**：無固定停利，由追蹤停損或時間出場決定

### 4. PowerLanguage 程式碼

```
// ===== STRATEGY_GEN_S14_TripleTFTrend =====
// F類-多時間框架型 | 雙向 | 15M+60M+日線 | 三時框共振回檔進場

inputs:
    SMA_Fast(5),
    SMA_Mid(20),
    SMA_Slow(60),
    RSI_Len(14),
    RSI_Bull_Lo(40),
    RSI_Bull_Hi(70),
    RSI_Bear_Lo(30),
    RSI_Bear_Hi(60),
    Pullback_Pct(0.5),
    SL_Mult(2.0),
    Trail_Mult(2.5),
    Trail_After(2),
    MaxBars(10);

variables:
    v_SMA_F(0),
    v_SMA_M(0),
    v_SMA_S(0),
    v_RSI(0),
    v_ATR(0),
    v_EntryPrice(0),
    v_StopLoss(0),
    v_TrailStop(0),
    v_BarsSinceEntry(0),
    v_Prev_MP(0),
    v_Direction(0);

v_SMA_F = Average(Close, SMA_Fast);
v_SMA_M = Average(Close, SMA_Mid);
v_SMA_S = Average(Close, SMA_Slow);
v_RSI = RSI(Close, RSI_Len);
v_ATR = AvgTrueRange(14);

v_Prev_MP = MarketPosition[1];

// 多方進場
if MarketPosition = 0 then begin
    if v_SMA_F[1] > v_SMA_M[1] and v_SMA_M[1] > v_SMA_S[1]
       and v_RSI[1] > RSI_Bull_Lo and v_RSI[1] < RSI_Bull_Hi
       and Low[1] <= v_SMA_F[1] * (1 + Pullback_Pct / 100)
       and Close > High[1] then begin
        buy ("S14_L") next bar at High stop;
        v_Direction = 1;
    end;

    // 空方進場
    if v_SMA_F[1] < v_SMA_M[1] and v_SMA_M[1] < v_SMA_S[1]
       and v_RSI[1] > RSI_Bear_Lo and v_RSI[1] < RSI_Bear_Hi
       and High[1] >= v_SMA_F[1] * (1 - Pullback_Pct / 100)
       and Close < Low[1] then begin
        sell short ("S14_S") next bar at Low stop;
        v_Direction = -1;
    end;
end;

// 多方出場
if MarketPosition = 1 then begin
    if v_Prev_MP <> 1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice - SL_Mult * v_ATR;
        v_TrailStop = v_StopLoss;
        v_BarsSinceEntry = 0;
    end;

    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    // 追蹤停損（持倉 > Trail_After 根後啟動）
    if v_BarsSinceEntry > Trail_After then begin
        v_TrailStop = MaxList(v_TrailStop, Close - Trail_Mult * v_ATR);
    end;

    sell ("S14_L_SL") next bar at v_TrailStop stop;

    if v_BarsSinceEntry >= MaxBars then
        sell ("S14_L_Time") next bar at market;
end;

// 空方出場
if MarketPosition = -1 then begin
    if v_Prev_MP <> -1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice + SL_Mult * v_ATR;
        v_TrailStop = v_StopLoss;
        v_BarsSinceEntry = 0;
    end;

    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    if v_BarsSinceEntry > Trail_After then begin
        v_TrailStop = MinList(v_TrailStop, Close + Trail_Mult * v_ATR);
    end;

    buy to cover ("S14_S_SL") next bar at v_TrailStop stop;

    if v_BarsSinceEntry >= MaxBars then
        buy to cover ("S14_S_Time") next bar at market;
end;
```

### 5. MC 設定建議
- **Data1**：TXF1 15 分鐘
- **Data2**：TXF1 日線（用 SMA60 日線確認長期趨勢）
- **MaxBarsBack**：至少 80

### 6. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 交易數 | 66 |
| 勝率 | 51.5% |
| Profit Factor | 1.86 |
| 淨利 | +2,457,619 NTD |
| MDD | -820,336 NTD |
| CAGR | 33.5% |
| 年化報酬 | +399,131 NTD |
| 盈虧比 | 1.75 |

### 7. 優化方向
1. **SMA_Fast / SMA_Mid**：(3,10) ~ (8,30)（均線組合敏感度）
2. **Trail_Mult**：1.5 ~ 3.5，步進 0.25（追蹤停損寬度）
3. **MaxBars**：5 ~ 15，步進 1（最大持倉時間）

### 8. 殺手問題
三時框共振需要強趨勢市場，震盪盤中均線交叉頻繁導致假信號。MDD 82 萬偏大，若趨勢突然反轉（如 6/5 崩跌），回檔進場可能直接觸停損。15M 級別可能有更多雜訊。

---

## 策略 S15：布林極端均值回歸策略

### 1. 策略概述
- **類別**：B 類（價格結構型）
- **操作方向**：★★★ 雙向（多+空）★★★
- **賺什麼錢**：當價格觸及布林通道極端位置（跌破下軌或突破上軌），且 RSI 確認超賣/超買，價格傾向回歸中軌。本策略結合長期趨勢過濾（SMA60 方向），只做與大趨勢一致的均值回歸。賺的是「超跌/超漲後回歸中軌的均值回歸利潤」。
- **主交易週期**：60 分鐘
- **確認週期**：日線（SMA60 方向過濾）
- **預期交易頻率**：每月 2-3 筆
- **與現有策略差異**：CL/CS 為 15M 均值回歸，用不同指標組合；本策略用布林通道極端 + RSI 極值 + SMA60 趨勢方向三重過濾，時框更大(60M)，進場條件更嚴格。

### 2. 進場邏輯
**多方條件（全部滿足）：**
1. 前一根收盤 < 布林下軌(20,2)（跌破下軌）
2. RSI(14) < 30（超賣確認）
3. SMA(60) 上升中（5日前 SMA60 < 當前 SMA60）
4. 於次根 K 棒開盤進場

**空方條件（全部滿足）：**
1. 前一根收盤 > 布林上軌(20,2)（突破上軌）
2. RSI(14) > 70（超買確認）
3. SMA(60) 下降中（5日前 SMA60 > 當前 SMA60）
4. 於次根 K 棒開盤進場

### 3. 出場邏輯
- **停損**：1.5 × ATR(14)
- **停利**：價格回到布林中軌（SMA20）
- **時間出場**：持倉滿 5 根 K 棒強制平倉
- **追蹤停損**：無

### 4. PowerLanguage 程式碼

```
// ===== STRATEGY_GEN_S15_BBReversion =====
// B類-價格結構型 | 雙向 | 60M | 布林極端均值回歸

inputs:
    BB_Len(20),
    BB_Mult(2.0),
    RSI_Len(14),
    RSI_OB(70),
    RSI_OS(30),
    SMA_Trend_Len(60),
    Trend_Lookback(5),
    SL_Mult(1.5),
    MaxBars(5);

variables:
    v_BB_Mid(0),
    v_BB_Upper(0),
    v_BB_Lower(0),
    v_RSI(0),
    v_SMA_Trend(0),
    v_SMA_Trend_Prev(0),
    v_ATR(0),
    v_EntryPrice(0),
    v_StopLoss(0),
    v_BarsSinceEntry(0),
    v_Prev_MP(0),
    v_Direction(0);

v_BB_Mid = BollingerBand(Close, BB_Len, 0);
v_BB_Upper = BollingerBand(Close, BB_Len, BB_Mult);
v_BB_Lower = BollingerBand(Close, BB_Len, -BB_Mult);
v_RSI = RSI(Close, RSI_Len);
v_SMA_Trend = Average(Close, SMA_Trend_Len);
v_SMA_Trend_Prev = Average(Close, SMA_Trend_Len)[Trend_Lookback];
v_ATR = AvgTrueRange(14);

v_Prev_MP = MarketPosition[1];

// 多方進場：跌破下軌 + 超賣 + 長趨勢上升
if MarketPosition = 0 then begin
    if Close[1] < v_BB_Lower[1]
       and v_RSI[1] < RSI_OS
       and v_SMA_Trend > v_SMA_Trend_Prev then begin
        buy ("S15_L") next bar at market;
        v_Direction = 1;
    end;

    // 空方進場：突破上軌 + 超買 + 長趨勢下降
    if Close[1] > v_BB_Upper[1]
       and v_RSI[1] > RSI_OB
       and v_SMA_Trend < v_SMA_Trend_Prev then begin
        sell short ("S15_S") next bar at market;
        v_Direction = -1;
    end;
end;

// 多方出場
if MarketPosition = 1 then begin
    if v_Prev_MP <> 1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice - SL_Mult * v_ATR;
        v_BarsSinceEntry = 0;
    end;

    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    sell ("S15_L_SL") next bar at v_StopLoss stop;

    // 停利：回到中軌
    sell ("S15_L_TP") next bar at v_BB_Mid limit;

    if v_BarsSinceEntry >= MaxBars then
        sell ("S15_L_Time") next bar at market;
end;

// 空方出場
if MarketPosition = -1 then begin
    if v_Prev_MP <> -1 then begin
        v_EntryPrice = EntryPrice;
        v_StopLoss = v_EntryPrice + SL_Mult * v_ATR;
        v_BarsSinceEntry = 0;
    end;

    v_BarsSinceEntry = v_BarsSinceEntry + 1;

    buy to cover ("S15_S_SL") next bar at v_StopLoss stop;

    // 停利：回到中軌
    buy to cover ("S15_S_TP") next bar at v_BB_Mid limit;

    if v_BarsSinceEntry >= MaxBars then
        buy to cover ("S15_S_Time") next bar at market;
end;
```

### 5. MC 設定建議
- **Data1**：TXF1 60 分鐘
- **Data2**：TXF1 日線（SMA60 趨勢方向）
- **MaxBarsBack**：至少 80

### 6. 模擬回測績效（日線代理）
| 指標 | 數值 |
|------|------|
| 交易數 | 13 |
| 勝率 | 76.9% |
| Profit Factor | 9.03 |
| 淨利 | +934,134 NTD |
| MDD | -67,642 NTD |
| CAGR | 18.7% |
| 年化報酬 | +151,708 NTD |
| 盈虧比 | 2.71 |

> ⚠️ PF 9.03 異常高，源自日線粒度下條件嚴格（6年僅13筆）。60M 級別交易數會增加，PF 預期降至 1.5-3.0 區間。須 MC 驗證。

### 7. 優化方向
1. **BB_Mult**：1.5 ~ 2.5，步進 0.25（通道寬度）
2. **RSI_OS / RSI_OB**：(25,75) ~ (35,65)（超買超賣門檻）
3. **SL_Mult**：1.0 ~ 2.5，步進 0.25（停損寬度）

### 8. 殺手問題
布林下軌 + RSI < 30 在趨勢性崩跌中會連續觸發假信號（如 2020/03、2022/07、2026/06），SMA60 方向過濾能擋一部分但非萬能。高勝率可能在少數極端虧損中被摧毀（肥尾風險）。

---

## 批次設計備註

**類別分配**：A(S11) + E(S12) + C(S13) + F(S14) + B(S15) — 與 Batch01(A+B+C+D+E)、Batch02(D+D+D+C+F) 完全不同

**週期分配**：45M(S11)、日線(S12)、30M(S13)、15M(S14)、60M(S15) — 5 種不同週期

**空方覆蓋**：S13 純空、S12/S14/S15 含空方邏輯

**MC 驗證優先順序**：
1. **S14 TripleTFTrend** — 日線 PF 1.86，交易數充足(66)，15M 可能更優
2. **S15 BBReversion** — PF 異常高需驗證，60M 交易數應增加
3. **S11 MiddayCompression** — 45M 需驗證壓縮邏輯有效性
4. **S13 VolCollapseShort** — 低頻但概念清晰，30M 增加樣本量
5. **S12 WeekdayMomentum** — 日線為負，建議 30M 重新驗證或調參
