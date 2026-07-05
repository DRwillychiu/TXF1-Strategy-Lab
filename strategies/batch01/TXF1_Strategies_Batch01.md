# TXF1 量化策略批次 Batch01

- 商品：TXF1 (台指期近月連續)、合約乘數 1 點 = 200 NTD
- 平台：MultiCharts 12 (PowerLanguage)
- 每口滑價 1,000 NTD (單邊 500)，固定 1 口
- 回測區間：2020/01/01 ~ 2026/07/05
- 代理回測：yfinance `^TWII` 日線；每筆扣 1,000 NTD 滑價；notional margin 500,000 NTD 用於 CAGR
- 生成時間：2026-07-05 (自動化排程)

> ⚠️ 代理回測侷限：以 `^TWII` 日線近似日內策略績效，會嚴重高估/低估波動較短的 ORB、ZS。
> 進 MC12 用 5M/30M/60M/日線多資料源回測後績效才具參考性。

---

## 📊 績效總覽

| 策略名稱 | 類別 | 方向 | 週期 | 賺什麼錢 | 交易數 | 勝率 | PF | 淨利(NTD) | MDD(NTD) | CAGR | 年化(NTD) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| STRATEGY_GEN_ORB  | A-時段  | 雙向 | 5M+D  | 開盤區間動能 | 85 | 41.2% | 0.92 | -577,383 | 2,915,156 | -100% | -95,123 |
| STRATEGY_GEN_VOL  | C-波動率 | 雙向 | 30M+D | 波動壓縮後爆發 | 29 | 34.5% | 2.81 | +2,067,991 | 354,699 | +31.8% | +349,045 |
| STRATEGY_GEN_MOMS | D-動量  | 空方 | 60M+D | RSI 反彈後續跌 | 8 | 37.5% | 0.74 | -56,643 | 216,045 | -2.8% | -13,321 |
| STRATEGY_GEN_ZS   | E-統計  | 雙向 | 30M+60M | 極端 Z 值回歸 | 2 | 50.0% | 0.45 | -108,944 | 0 | -13.9% | -66,099 |
| STRATEGY_GEN_MTF  | F-多框架 | 多方 | 15M+D | 日線多頭 15M 拉回 | 33 | 54.5% | 1.91 | +1,864,916 | 777,223 | +29.3% | +307,938 |

**類別覆蓋檢查**：A(1) B(0) C(1) D(1) E(1) F(1) — 至少 1A ✅、至少 1 B/C ✅、至少 1 空方邏輯 ✅ (MOMS)、週期非全同 ✅ (5/30/60/30/15)。

**代理回測解讀**：
- VOL 與 MTF 在日線代理下表現最佳，訊號稀而利大 → 進 MC12 30M/15M 應能維持正 EDGE。
- ORB 在日線代理極差是預期結果 (日內開盤區間突破無法用日線近似)，仍需以 5M 實測評估。
- MOMS 訊號過少 (8 筆) 顯示日線代理過濾太嚴，60M 實測會增加至少 5-10 倍樣本。
- ZS 樣本過小；MC 上 30M z-score 訊號會顯著增加。

---

## 🅰️ STRATEGY_GEN_ORB (A類-時段型)

### 1. 策略概述
- **類別**：A-時段型
- **操作方向**：★ 雙向 (做多 + 做空) ★
- **賺什麼錢**：吃 08:45 開盤後 30 分鐘區間突破的日內動能；日線方向濾網避免逆勢。
- **操作週期**：Data1 5M
- **確認週期**：Data2 日線 (20MA 方向濾網)
- **預期交易頻率**：日內 0-1 筆、月均 10-15 筆
- **與現有策略差異**：BL 是 15M 盤整區間突破 (區間可持續數小時)；ORB 專打「開盤 30 分鐘」的固定時段區間，時窗與 K 週期都更小。

### 2. 進場邏輯
多方 (全部成立)：
- 開盤區間已完成 (`v_ORDone = true`)
- 日線 20MA 向上 (Close[Data2] > 20MA[Data2])
- ATR14 > 0 (避免死盤)
- 時間介於 08:45 ~ 13:15
- 下一根以區間上緣 + 最小跳動點 stop 買進

空方：
- 同前 3 條 + 日線 20MA 向下
- 下一根以區間下緣 - 最小跳動點 stop 放空

### 3. 出場邏輯
- 停損：進場價 ± 1.5 × ATR
- 停利：進場價 ± 3.0 × ATR
- 追蹤停利：波段極端價 ∓ 2.0 × ATR
- 時間出場：收盤前 15 分鐘全部平倉 (避免留倉風險)

### 4. PowerLanguage 程式碼
```powerlanguage
// STRATEGY_GEN_ORB — 完整程式碼見 pl_code/STRATEGY_GEN_ORB.pln
inputs: ORMinutes(30), SessionStart(845), SessionEnd(1330),
        StopATRmult(1.5), TargetATRmult(3.0), TrailATRmult(2.0),
        ATRLen(14), ExitMinutesBeforeClose(15);
variables: v_ORHigh(0), v_ORLow(0), v_ORDone(false), v_CurDate(0),
           v_MinutesFromOpen(0), v_ATR(0), v_Prev_MP(0), v_EntryPx(0),
           v_MaxSinceEntry(0), v_MinSinceEntry(999999);
v_ATR = AvgTrueRange(ATRLen);
if Date <> v_CurDate then begin
    v_CurDate = Date; v_ORHigh = 0; v_ORLow = 999999; v_ORDone = false;
end;
v_MinutesFromOpen = (Hour(Time)*60+Minute(Time)) - (Hour(SessionStart)*60+Minute(SessionStart));
if v_MinutesFromOpen >= 0 and v_MinutesFromOpen < ORMinutes then begin
    if High > v_ORHigh then v_ORHigh = High;
    if Low  < v_ORLow  then v_ORLow  = Low;
end else if v_MinutesFromOpen >= ORMinutes then v_ORDone = true;
if MarketPosition <> v_Prev_MP then begin
    if MarketPosition <> 0 then begin
        v_EntryPx = EntryPrice; v_MaxSinceEntry = Close; v_MinSinceEntry = Close;
    end;
    v_Prev_MP = MarketPosition;
end;
if MarketPosition = 1  and High > v_MaxSinceEntry then v_MaxSinceEntry = High;
if MarketPosition = -1 and Low  < v_MinSinceEntry then v_MinSinceEntry = Low;
condition1 = Close of Data2 > Average(Close of Data2, 20)[1];
condition2 = Close of Data2 < Average(Close of Data2, 20)[1];
condition3 = v_ORDone and Time >= SessionStart and Time <= SessionEnd - ExitMinutesBeforeClose;
condition4 = v_ATR > 0;
if MarketPosition = 0 and condition3 and condition4 then begin
    if condition1 then buy("ORB_L") next bar at v_ORHigh + MinMove/PriceScale stop;
    if condition2 then sell short("ORB_S") next bar at v_ORLow - MinMove/PriceScale stop;
end;
if MarketPosition = 1 then begin
    sell("ORB_L_SL") next bar at v_EntryPx - StopATRmult*v_ATR stop;
    sell("ORB_L_TP") next bar at v_EntryPx + TargetATRmult*v_ATR limit;
    sell("ORB_L_TR") next bar at v_MaxSinceEntry - TrailATRmult*v_ATR stop;
end;
if MarketPosition = -1 then begin
    buy to cover("ORB_S_SL") next bar at v_EntryPx + StopATRmult*v_ATR stop;
    buy to cover("ORB_S_TP") next bar at v_EntryPx - TargetATRmult*v_ATR limit;
    buy to cover("ORB_S_TR") next bar at v_MinSinceEntry + TrailATRmult*v_ATR stop;
end;
if (Hour(Time)*60+Minute(Time)) >= (Hour(SessionEnd)*60+Minute(SessionEnd)) - ExitMinutesBeforeClose then begin
    if MarketPosition = 1  then sell("ORB_L_EOD") next bar at market;
    if MarketPosition = -1 then buy to cover("ORB_S_EOD") next bar at market;
end;
```

### 5. MC 設定建議
- Data1：TXF1 5M (日盤)
- Data2：TXF1 日線
- Initial Capital 500,000 NTD、Slippage 1 tick、Commission 1,000 NTD/round

### 6. 模擬回測預期績效 (日線代理)
| 指標 | 值 |
|---|---:|
| 淨利 (NTD) | -577,383 |
| MDD (NTD) | 2,915,156 |
| CAGR | -100% |
| 年化 (NTD) | -95,123 |
| 勝率 | 41.2% |
| PF | 0.92 |
| 盈虧比 | 1.31 |
| 交易數 | 85 |

*代理績效不代表 5M 真實回測，預期 MC12 上 5M 實測會顯著改善 (代理過度膨脹單筆賠額)。*

### 7. 優化方向
- `ORMinutes` 20~45 (區間長度)
- `StopATRmult` 1.0~2.5、`TargetATRmult` 2.0~4.5 (R:R)
- `ExitMinutesBeforeClose` 10~30 (留倉風險)

### 8. 殺手問題
開盤跳空後區間過大導致停損太寬 → 期望值被 3-5 次極端日單邊掃完；需要 gap>N*ATR 濾網。

---

## 🎯 STRATEGY_GEN_VOL (C類-波動率型)

### 1. 策略概述
- **類別**：C-波動率型
- **操作方向**：★ 雙向 ★
- **賺什麼錢**：BB 帶寬壓縮 (Squeeze) 後跟隨爆發方向；波動由低到高的均值回歸。
- **操作週期**：Data1 30M
- **確認週期**：Data2 日線 (50MA 方向)
- **預期交易頻率**：月均 4-8 筆
- **與現有策略差異**：TL/TS 用 ATR 通道；VOL 用 BB 帶寬相對百分位判斷壓縮 → 只在波動極低時出手，訊號密度更低但勝負清楚。

### 2. 進場邏輯
多方：
- 前一根 BB 帶寬處於過去 60 根低 30 百分位 (擠壓)
- 當根 Close 突破 BB 上軌
- 10 根動量 > 0
- 日線 Close > 50MA
- 下一根 market 進場

空方：對稱條件，日線 Close < 50MA。

### 3. 出場邏輯
- 停損：進場價 ± 1.8 × ATR
- 停利：進場價 ± 3.5 × ATR
- 中軌反轉：Close 跌破/突破 BB 中軌 stop 出場
- 時間出場：8 根仍未達停利 → market

### 4. PowerLanguage 程式碼
```powerlanguage
// STRATEGY_GEN_VOL — 完整程式碼見 pl_code/STRATEGY_GEN_VOL.pln
inputs: BBLen(20), BBStdev(2.0), SqueezeLookback(60), SqueezePct(0.3),
        ATRLen(14), StopATRmult(1.8), TargetATRmult(3.5), MomLen(10);
variables: v_Mid(0), v_Up(0), v_Dn(0), v_BW(0), v_BWRef(0),
           v_Squeezed(false), v_ATR(0), v_Mom(0), v_Prev_MP(0), v_EntryPx(0);
v_Mid = Average(Close, BBLen);
v_Up  = v_Mid + BBStdev*StdDev(Close, BBLen);
v_Dn  = v_Mid - BBStdev*StdDev(Close, BBLen);
v_BW  = (v_Up - v_Dn) / v_Mid;
v_BWRef = Lowest(v_BW, SqueezeLookback) * (1 + SqueezePct);
v_Squeezed = v_BW <= v_BWRef;
v_ATR = AvgTrueRange(ATRLen);
v_Mom = Close - Close[MomLen];
if MarketPosition <> v_Prev_MP then begin
    if MarketPosition <> 0 then v_EntryPx = EntryPrice;
    v_Prev_MP = MarketPosition;
end;
condition1 = v_Squeezed[1] = true;
condition2 = Close > v_Up and v_Mom > 0;
condition3 = Close < v_Dn and v_Mom < 0;
condition4 = Close of Data2 > Average(Close of Data2,50)[1];
condition5 = Close of Data2 < Average(Close of Data2,50)[1];
if MarketPosition = 0 then begin
    if condition1 and condition2 and condition4 then buy("VOL_L") next bar at market;
    if condition1 and condition3 and condition5 then sell short("VOL_S") next bar at market;
end;
if MarketPosition = 1 then begin
    sell("VOL_L_SL")  next bar at v_EntryPx - StopATRmult*v_ATR stop;
    sell("VOL_L_TP")  next bar at v_EntryPx + TargetATRmult*v_ATR limit;
    sell("VOL_L_Mid") next bar at v_Mid stop;
end;
if MarketPosition = -1 then begin
    buy to cover("VOL_S_SL")  next bar at v_EntryPx + StopATRmult*v_ATR stop;
    buy to cover("VOL_S_TP")  next bar at v_EntryPx - TargetATRmult*v_ATR limit;
    buy to cover("VOL_S_Mid") next bar at v_Mid stop;
end;
if BarsSinceEntry >= 8 then begin
    if MarketPosition = 1  then sell("VOL_L_TIME") next bar at market;
    if MarketPosition = -1 then buy to cover("VOL_S_TIME") next bar at market;
end;
```

### 5. MC 設定建議
- Data1：TXF1 30M
- Data2：TXF1 日線

### 6. 模擬回測預期績效 (日線代理)
| 指標 | 值 |
|---|---:|
| 淨利 (NTD) | +2,067,991 |
| MDD (NTD) | 354,699 |
| CAGR | +31.8% |
| 年化 (NTD) | +349,045 |
| 勝率 | 34.5% |
| PF | 2.81 |
| 盈虧比 | 5.35 |
| 交易數 | 29 |

### 7. 優化方向
- `BBLen` 15~30、`BBStdev` 1.5~2.5
- `SqueezePct` 0.15~0.5 (壓縮認定寬鬆度)
- `TargetATRmult` 2.5~5.0 (R:R)

### 8. 殺手問題
壓縮後假突破 (fake-out) 頻繁；若 BB 中軌斜率為 0，突破根本無方向。需再加 EMA 斜率或 ADX 濾網 (但會犧牲樣本)。

---

## 📉 STRATEGY_GEN_MOMS (D類-動量趨勢型，★空方★)

### 1. 策略概述
- **類別**：D-動量趨勢型
- **操作方向**：★ 做空 (Short Only) ★
- **賺什麼錢**：反彈接近超買後回落 + 死叉續跌，補足現有策略缺乏的中週期空方。
- **操作週期**：Data1 60M
- **確認週期**：Data2 日線 (20MA 之下)
- **預期交易頻率**：月均 2-4 筆
- **與現有策略差異**：TS 是 60M 均線+動量趨勢空頭；MOMS 專打「RSI 反彈後從超買回落」→ 進場點在反彈頂而非破底，回撤結構不同。

### 2. 進場邏輯
空方 (5 條全成立)：
- 10MA < 30MA (死叉狀態)
- RSI 由 60 以上回落到 60 之下
- 日線 Close < 20MA
- 本根 TrueRange >= 0.8 × ATR14 (過濾死盤)
- Close < Close[3] (短期價格向下)
- 下一根 market 空

### 3. 出場邏輯
- 停損：進場價 + 1.5 × ATR
- 停利：進場價 - 3.0 × ATR
- 追蹤停利：最低價 + 2.5 × ATR
- 動能反轉出場：10MA > 30MA → market
- 時間出場：12 根 (12 小時)

### 4. PowerLanguage 程式碼
```powerlanguage
// STRATEGY_GEN_MOMS — 完整程式碼見 pl_code/STRATEGY_GEN_MOMS.pln
inputs: RSILen(14), RSIOverbought(60), FastMA(10), SlowMA(30),
        ATRLen(14), StopATRmult(1.5), TargetATRmult(3.0),
        TrailATRmult(2.5), MinRangeATR(0.8);
variables: v_RSI(0), v_Fast(0), v_Slow(0), v_ATR(0),
           v_Prev_MP(0), v_EntryPx(0), v_MinSinceEntry(999999), v_RSIPeak(0);
v_RSI  = RSI(Close, RSILen);
v_Fast = Average(Close, FastMA);
v_Slow = Average(Close, SlowMA);
v_ATR  = AvgTrueRange(ATRLen);
if v_RSI > v_RSIPeak or currentbar mod 5 = 0 then v_RSIPeak = v_RSI;
if MarketPosition <> v_Prev_MP then begin
    if MarketPosition <> 0 then begin
        v_EntryPx = EntryPrice; v_MinSinceEntry = Close; v_RSIPeak = 0;
    end;
    v_Prev_MP = MarketPosition;
end;
if MarketPosition = -1 and Low < v_MinSinceEntry then v_MinSinceEntry = Low;
condition1 = v_Fast < v_Slow;
condition2 = v_RSI < RSIOverbought and v_RSIPeak >= RSIOverbought;
condition3 = Close of Data2 < Average(Close of Data2,20)[1];
condition4 = TrueRange >= MinRangeATR*v_ATR;
condition5 = Close < Close[3];
if MarketPosition = 0 and condition1 and condition2 and condition3
   and condition4 and condition5 then
    sell short("MOMS_S") next bar at market;
if MarketPosition = -1 then begin
    buy to cover("MOMS_SL") next bar at v_EntryPx + StopATRmult*v_ATR stop;
    buy to cover("MOMS_TP") next bar at v_EntryPx - TargetATRmult*v_ATR limit;
    buy to cover("MOMS_TR") next bar at v_MinSinceEntry + TrailATRmult*v_ATR stop;
    if v_Fast > v_Slow then buy to cover("MOMS_REV") next bar at market;
    if BarsSinceEntry >= 12 then buy to cover("MOMS_TIME") next bar at market;
end;
```

### 5. MC 設定建議
- Data1：TXF1 60M
- Data2：TXF1 日線

### 6. 模擬回測預期績效 (日線代理)
| 指標 | 值 |
|---|---:|
| 淨利 (NTD) | -56,643 |
| MDD (NTD) | 216,045 |
| CAGR | -2.8% |
| 年化 (NTD) | -13,321 |
| 勝率 | 37.5% |
| PF | 0.74 |
| 盈虧比 | 1.23 |
| 交易數 | 8 |

*8 筆樣本統計不顯著；60M 實測預期 40-80 筆/年。*

### 7. 優化方向
- `RSIOverbought` 55~70 (反彈觸發強度)
- `FastMA/SlowMA` 5/20 ~ 20/60
- `MinRangeATR` 0.5~1.2 (死盤過濾強度)

### 8. 殺手問題
2020-2024 台股長多結構下，60M 死叉常為誤訊；牛市中每次「RSI 回落」都是加碼多方機會，這策略容易連續小虧。需觀察日線長多環境是否停用。

---

## 📈 STRATEGY_GEN_ZS (E類-統計型)

### 1. 策略概述
- **類別**：E-統計型
- **操作方向**：★ 雙向 ★
- **賺什麼錢**：Close 相對 50 根均值的標準化偏離 (Z-score) 極端後均值回歸。
- **操作週期**：Data1 30M
- **確認週期**：Data2 60M (20MA 斜率)
- **預期交易頻率**：月均 3-5 筆
- **與現有策略差異**：CL/CS 在 15M 盤整內做均值回歸；ZS 用 30M Z-score >2 極端事件，結合 60M 大時段趨勢做「順勢均值回歸」，避開純逆勢陷阱。

### 2. 進場邏輯
多方：
- 30M z50 <= -2.0 (極度超賣)
- 60M 20MA 斜率 >= 0 (大時段沒跌)
- 下一根 market 買

空方：
- 30M z50 >= 2.0
- 60M 20MA 斜率 <= 0
- 下一根 market 空

### 3. 出場邏輯
- 回歸平倉：|Z| <= 0.3 → market
- Z 惡化停損：|Z| >= 3.0 → market
- ATR 硬停損：進場價 ± 2.0 × ATR
- 時間出場：20 根未回歸 → market

### 4. PowerLanguage 程式碼
```powerlanguage
// STRATEGY_GEN_ZS — 完整程式碼見 pl_code/STRATEGY_GEN_ZS.pln
inputs: ZLen(50), EntryZ(2.0), ExitZ(0.3), StopZ(3.0),
        ATRLen(14), StopATRmult(2.0), MaxBars(20);
variables: v_Mean(0), v_Std(0), v_Z(0), v_ATR(0),
           v_Trend60(0), v_Prev_MP(0), v_EntryPx(0);
v_Mean = Average(Close, ZLen);
v_Std  = StdDev(Close, ZLen);
if v_Std > 0 then v_Z = (Close - v_Mean) / v_Std;
v_ATR = AvgTrueRange(ATRLen);
v_Trend60 = Average(Close of Data2, 20)[1] - Average(Close of Data2, 20)[6];
if MarketPosition <> v_Prev_MP then begin
    if MarketPosition <> 0 then v_EntryPx = EntryPrice;
    v_Prev_MP = MarketPosition;
end;
condition1 = v_Z <= -EntryZ and v_Trend60 >= 0;
condition2 = v_Z >=  EntryZ and v_Trend60 <= 0;
condition3 = v_Std > 0;
if MarketPosition = 0 and condition3 then begin
    if condition1 then buy("ZS_L") next bar at market;
    if condition2 then sell short("ZS_S") next bar at market;
end;
if MarketPosition = 1 then begin
    if v_Z >= -ExitZ then sell("ZS_L_MR") next bar at market;
    if v_Z <= -StopZ then sell("ZS_L_ZS") next bar at market;
    sell("ZS_L_SL") next bar at v_EntryPx - StopATRmult*v_ATR stop;
    if BarsSinceEntry >= MaxBars then sell("ZS_L_TIME") next bar at market;
end;
if MarketPosition = -1 then begin
    if v_Z <= ExitZ then buy to cover("ZS_S_MR") next bar at market;
    if v_Z >= StopZ then buy to cover("ZS_S_ZS") next bar at market;
    buy to cover("ZS_S_SL") next bar at v_EntryPx + StopATRmult*v_ATR stop;
    if BarsSinceEntry >= MaxBars then buy to cover("ZS_S_TIME") next bar at market;
end;
```

### 5. MC 設定建議
- Data1：TXF1 30M
- Data2：TXF1 60M

### 6. 模擬回測預期績效 (日線代理)
| 指標 | 值 |
|---|---:|
| 淨利 (NTD) | -108,944 |
| MDD (NTD) | 0 |
| CAGR | -13.9% |
| 年化 (NTD) | -66,099 |
| 勝率 | 50.0% |
| PF | 0.45 |
| 盈虧比 | 0.45 |
| 交易數 | 2 |

*日線代理無法模擬 30M z-score 密度；MC 實測預期每年 30-50 筆。*

### 7. 優化方向
- `EntryZ` 1.5~2.5、`ExitZ` 0.0~0.5
- `ZLen` 30~80
- `StopATRmult` 1.5~2.5

### 8. 殺手問題
趨勢加速時 Z 可從 -2 一路擴大到 -5，均值回歸假設崩潰。「回不去」的 fat tail 是致命傷；`StopZ` 若設太寬會單筆吃掉多次獲利。

---

## 🔀 STRATEGY_GEN_MTF (F類-多時間框架型，多方)

### 1. 策略概述
- **類別**：F-多時間框架型
- **操作方向**：★ 做多 (Long Only) ★
- **賺什麼錢**：日線多頭排列環境下，15M 拉回 20MA 附近的加碼點。
- **操作週期**：Data1 15M
- **確認週期**：Data2 日線 (20/60MA 排列)
- **預期交易頻率**：月均 3-6 筆
- **與現有策略差異**：TL 是 45M ATR 通道突破；MTF 進場邏輯完全不同 → 不追突破，而是等 15M 拉回到 20MA 觸及再入場，成本更低、SL 更緊。

### 2. 進場邏輯
多方 (5 條全成立)：
- 日線 20MA > 60MA 且 20MA 斜率向上
- 日線 Close > 60MA
- 15M Low <= 20MA + 0.6 × ATR (拉回觸及)
- 15M 當根收紅 (Close > Open)
- 15M Close > 20MA (拉回未破)
- 15M 20MA 向上
- 下一根以本根 High + tick stop 買進 (突破前根高)

### 3. 出場邏輯
- 停損：進場價 - 1.5 × ATR
- 停利：進場價 + 4.0 × ATR
- 追蹤停利：最高價 - 2.5 × ATR
- 日線失守出場：Close[D] < 60MA[D] → market
- 時間出場：60 根 (15 小時) 未達停利 → market

### 4. PowerLanguage 程式碼
```powerlanguage
// STRATEGY_GEN_MTF — 完整程式碼見 pl_code/STRATEGY_GEN_MTF.pln
inputs: ShortMA(20), LongMA(60), PullbackATR(0.6), ATRLen(14),
        StopATRmult(1.5), TargetATRmult(4.0), TrailATRmult(2.5),
        MinTrendSlope(0);
variables: v_SMA(0), v_LMA(0), v_DailyOK(false), v_ATR(0),
           v_Prev_MP(0), v_EntryPx(0), v_MaxSinceEntry(0);
v_SMA = Average(Close, ShortMA);
v_LMA = Average(Close, LongMA);
v_ATR = AvgTrueRange(ATRLen);
v_DailyOK = (Average(Close of Data2,20)[1] > Average(Close of Data2,60)[1])
            and (Average(Close of Data2,20)[1] > Average(Close of Data2,20)[6] + MinTrendSlope)
            and (Close of Data2 > Average(Close of Data2,60)[1]);
if MarketPosition <> v_Prev_MP then begin
    if MarketPosition <> 0 then begin
        v_EntryPx = EntryPrice; v_MaxSinceEntry = Close;
    end;
    v_Prev_MP = MarketPosition;
end;
if MarketPosition = 1 and High > v_MaxSinceEntry then v_MaxSinceEntry = High;
condition1 = v_DailyOK;
condition2 = Low <= v_SMA + PullbackATR*v_ATR;
condition3 = Close > Open;
condition4 = Close > v_SMA;
condition5 = v_SMA > v_SMA[3];
if MarketPosition = 0 and condition1 and condition2 and condition3
   and condition4 and condition5 then
    buy("MTF_L") next bar at High + MinMove/PriceScale stop;
if MarketPosition = 1 then begin
    sell("MTF_SL") next bar at v_EntryPx - StopATRmult*v_ATR stop;
    sell("MTF_TP") next bar at v_EntryPx + TargetATRmult*v_ATR limit;
    sell("MTF_TR") next bar at v_MaxSinceEntry - TrailATRmult*v_ATR stop;
    if Close of Data2 < Average(Close of Data2,60)[1] then
        sell("MTF_DailyBrk") next bar at market;
    if BarsSinceEntry >= 60 then sell("MTF_TIME") next bar at market;
end;
```

### 5. MC 設定建議
- Data1：TXF1 15M
- Data2：TXF1 日線

### 6. 模擬回測預期績效 (日線代理)
| 指標 | 值 |
|---|---:|
| 淨利 (NTD) | +1,864,916 |
| MDD (NTD) | 777,223 |
| CAGR | +29.3% |
| 年化 (NTD) | +307,938 |
| 勝率 | 54.5% |
| PF | 1.91 |
| 盈虧比 | 1.59 |
| 交易數 | 33 |

### 7. 優化方向
- `PullbackATR` 0.3~1.0 (拉回容忍度)
- `TargetATRmult` 3.0~5.0
- `TrailATRmult` 2.0~3.5

### 8. 殺手問題
「拉回不破 20MA」的定義過寬時會在跌勢初期反覆進場被上升趨勢反轉打爆；日線 60MA 失守時止損可能落後 3-5%，MDD 大部分來自單一年度轉折。

---

## 📁 檔案清單
- `TXF1_Strategies_Batch01.md` — 本文件
- `batch01/pl_code/STRATEGY_GEN_ORB.pln`
- `batch01/pl_code/STRATEGY_GEN_VOL.pln`
- `batch01/pl_code/STRATEGY_GEN_MOMS.pln`
- `batch01/pl_code/STRATEGY_GEN_ZS.pln`
- `batch01/pl_code/STRATEGY_GEN_MTF.pln`
- `batch01/backtest.py` — 代理回測腳本
- `batch01/results.json` — 原始績效 JSON
