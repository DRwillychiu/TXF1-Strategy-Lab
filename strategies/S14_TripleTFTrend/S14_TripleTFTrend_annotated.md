# S14 TripleTFTrend — 中文逐行註解

> 對應程式碼：`S14_TripleTFTrend.pla`（MC12 直接使用的全英文版）
> 策略描述：`S14_TripleTFTrend_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：F 類 — 多時間框架型
- **方向**：★雙向
- **週期**：15 分鐘
- **核心邏輯**：三條均線（SMA5 > SMA20 > SMA60）排列共振確認趨勢方向，RSI 處於中區（非超買超賣），價格回檔至短均線後突破前根高/低點進場，使用移動停利保護利潤

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `SMAFast` | 5 | 短期均線週期 |
| `SMAMid` | 20 | 中期均線週期 |
| `SMASlow` | 60 | 長期均線週期 |
| `RSILen` | 14 | RSI計算週期 |
| `RSIBullLo` | 40 | 多頭RSI下限 |
| `RSIBullHi` | 70 | 多頭RSI上限 |
| `RSIBearLo` | 30 | 空頭RSI下限 |
| `RSIBearHi` | 60 | 空頭RSI上限 |
| `PullbackPct` | 0.5 | 回檔容忍度（%），Low需接近SMAFast |
| `StopATRMult` | 2.0 | 初始停損 = 進場價 ± ATR × 2.0 |
| `TrailATRMult` | 2.5 | 移動停利距離 = Close ± ATR × 2.5 |
| `TrailAfterBars` | 2 | 啟動移動停利的最少持倉K棒 |
| `MaxBars` | 10 | 最大持倉10根K棒後強制出場 |
| `ATRLen` | 14 | ATR計算週期 |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態

### 2. 指標計算
```
v_SMAF = Average(Close, SMAFast);
v_SMAM = Average(Close, SMAMid);
v_SMAS = Average(Close, SMASlow);
v_RSI = RSI(Close, RSILen);
v_ATR = AvgTrueRange(ATRLen);
```
- 三條均線用於判定趨勢共振
- RSI 用於過濾超買超賣區域
- ATR 用於停損與移動停利計算

### 3. 做多進場
```
If v_Prev_MP = 0 And
   v_SMAF[1] > v_SMAM[1] And v_SMAM[1] > v_SMAS[1] And
   v_RSI[1] > RSIBullLo And v_RSI[1] < RSIBullHi And
   Low[1] <= v_SMAF[1] * (1 + PullbackPct / 100) And
   Close > High[1] Then Begin
    Buy ("LE_TT_Long") Next Bar at Market;
    v_TrailStop = EntryPrice - StopATRMult * v_ATR;
    v_BarsSinceEntry = 0;
End;
```
- 空手 + 三均線多頭排列（SMA5 > SMA20 > SMA60）
- RSI 在 40~70 中區（非超買，仍有上漲空間）
- 前根 Low 接近 SMA5（回檔至短均線）
- 當根收盤突破前根最高價（突破確認）

### 4. 做空進場
```
If v_Prev_MP = 0 And
   v_SMAF[1] < v_SMAM[1] And v_SMAM[1] < v_SMAS[1] And
   v_RSI[1] > RSIBearLo And v_RSI[1] < RSIBearHi And
   High[1] >= v_SMAF[1] * (1 - PullbackPct / 100) And
   Close < Low[1] Then Begin
    SellShort ("SE_TT_Short") Next Bar at Market;
    v_TrailStop = EntryPrice + StopATRMult * v_ATR;
    v_BarsSinceEntry = 0;
End;
```
- 空手 + 三均線空頭排列（SMA5 < SMA20 < SMA60）
- RSI 在 30~60 中區（非超賣，仍有下跌空間）
- 前根 High 接近 SMA5（反彈至短均線）
- 當根收盤跌破前根最低價（突破確認）

### 5. 多單出場（移動停利）
```
If v_BarsSinceEntry > TrailAfterBars Then
    v_TrailStop = MaxList(v_TrailStop, Close - TrailATRMult * v_ATR);
Sell ("LX_TT_Trail") Next Bar at v_TrailStop Stop;
Sell ("LX_TT_Time") Next Bar at Market;
Sell ("LX_TT_EOD") Next Bar at Market;
```
- 持倉超過2根K棒後啟動移動停利
- 移動停利只往上調整（MaxList），距離 = Close - 2.5 ATR
- 時間出場：持倉≥10根K棒
- 盤末出場：13:40 強制平倉

### 6. 空單出場（移動停利）
```
If v_BarsSinceEntry > TrailAfterBars Then
    v_TrailStop = MinList(v_TrailStop, Close + TrailATRMult * v_ATR);
BuyToCover ("SX_TT_Trail") Next Bar at v_TrailStop Stop;
BuyToCover ("SX_TT_Time") Next Bar at Market;
BuyToCover ("SX_TT_EOD") Next Bar at Market;
```
- 移動停利只往下調整（MinList），距離 = Close + 2.5 ATR
- 時間出場與盤末出場同多單邏輯

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_TT_Long` | `Buy` | 做多 | 進場 | 三均線多頭+RSI中區+回檔突破 |
| `SE_TT_Short` | `SellShort` | 做空 | 進場 | 三均線空頭+RSI中區+反彈突破 |
| `LX_TT_Trail` | `Sell` | 做多 | 出場 | 移動停利 ATR×2.5 |
| `LX_TT_Time` | `Sell` | 做多 | 出場 | 持倉≥10根K棒 |
| `LX_TT_EOD` | `Sell` | 做多 | 出場 | 13:40盤末平倉 |
| `SX_TT_Trail` | `BuyToCover` | 做空 | 出場 | 移動停利 ATR×2.5 |
| `SX_TT_Time` | `BuyToCover` | 做空 | 出場 | 持倉≥10根K棒 |
| `SX_TT_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **15 分鐘** | 10M, 30M | 15M 平衡均線共振偵測與回檔精度 |
| **Data2** | 不需要 | — | 單週期策略（三均線在同一時間框架） |

### 二、回測基本設定
| 項目 | 設定 |
|------|------|
| 商品 | TXF1（台指期近月連續）|
| 合約乘數 | 200 NTD/點 |
| 滑價 | 單邊 500 NTD（來回 1,000 NTD）|
| 口數 | 1 口固定 |
| 回測區間 | 2020/01/01 ~ 今天 |
| 初始資金 | 300,000 ~ 500,000 NTD |

### 三、所有參數最佳化範圍
| 參數 | 預設值 | 掃描起點 | 掃描終點 | 步長 | 組合數 | 說明 |
|------|--------|---------|---------|------|--------|------|
| `SMAFast` | 5 | 3 | 8 | 1 | 6 | 短期均線週期 |
| `SMAMid` | 20 | 10 | 30 | 5 | 5 | 中期均線週期 |
| `TrailATRMult` | 2.5 | 1.50 | 3.50 | 0.25 | 9 | 移動停利ATR倍數 |
| `MaxBars` | 10 | 5 | 15 | 1 | 11 | 最大持倉K棒 |

**全參數組合數**：6 × 5 × 9 × 11 = **2,970**（暴力窮舉）

### 四、暴力窮舉設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 最佳化方式 | 暴力窮舉（Exhaustive Search）|
| 預估評估次數 | 2,970 |
| 最佳化依據 | 最大的 Net Profit |
