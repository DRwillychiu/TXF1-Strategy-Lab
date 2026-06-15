# S15 BBReversion — 中文逐行註解

> 對應程式碼：`S15_BBReversion.pla`（MC12 直接使用的全英文版）
> 策略描述：`S15_BBReversion_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：B 類 — 價格結構型
- **方向**：★雙向
- **週期**：60 分鐘
- **核心邏輯**：當價格觸及布林帶極端位置（上軌超買或下軌超賣），搭配 RSI 確認超買超賣，並以 SMA60 趨勢方向過濾，進行均值回歸交易，目標為布林中軌

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `BBLen` | 20 | 布林帶計算週期 |
| `BBMult` | 2.0 | 布林帶標準差倍數 |
| `RSILen` | 14 | RSI計算週期 |
| `RSI_OB` | 70 | RSI超買門檻 |
| `RSI_OS` | 30 | RSI超賣門檻 |
| `SMATrendLen` | 60 | 趨勢均線週期 |
| `TrendLookback` | 5 | 趨勢比較回溯期 |
| `StopATRMult` | 1.5 | 停損 = 進場價 ± ATR × 1.5 |
| `ATRLen` | 14 | ATR計算週期 |
| `MaxBars` | 5 | 最大持倉5根K棒後強制出場 |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態

### 2. 指標計算
```
v_BBMid = BollingerBand(Close, BBLen, 0);
v_BBUpper = BollingerBand(Close, BBLen, BBMult);
v_BBLower = BollingerBand(Close, BBLen, -BBMult);
v_RSI = RSI(Close, RSILen);
v_SMATrend = Average(Close, SMATrendLen);
v_SMATrendPrev = Average(Close, SMATrendLen)[TrendLookback];
v_ATR = AvgTrueRange(ATRLen);
```
- 布林帶三軌（上、中、下），用於判定價格極端位置
- RSI 確認超買超賣狀態
- SMA60 當前值與5根前比較，判定趨勢方向

### 3. 做多進場（下軌超賣+上升趨勢）
```
If v_Prev_MP = 0 And
   Close[1] < v_BBLower[1] And
   v_RSI[1] < RSI_OS And
   v_SMATrend > v_SMATrendPrev Then Begin
    Buy ("LE_BR_Long") Next Bar at Market;
    v_BarsSinceEntry = 0;
End;
```
- 空手狀態
- 前根收盤低於布林下軌（極端超賣）
- RSI < 30（超賣確認）
- SMA60 上升中（大趨勢向上，回歸機率高）

### 4. 做空進場（上軌超買+下降趨勢）
```
If v_Prev_MP = 0 And
   Close[1] > v_BBUpper[1] And
   v_RSI[1] > RSI_OB And
   v_SMATrend < v_SMATrendPrev Then Begin
    SellShort ("SE_BR_Short") Next Bar at Market;
    v_BarsSinceEntry = 0;
End;
```
- 空手狀態
- 前根收盤高於布林上軌（極端超買）
- RSI > 70（超買確認）
- SMA60 下降中（大趨勢向下，回歸機率高）

### 5. 多單出場
```
Sell ("LX_BR_SL") Next Bar at v_StopPrice Stop;
Sell ("LX_BR_TP") Next Bar at v_BBMid Limit;
Sell ("LX_BR_Time") Next Bar at Market;
Sell ("LX_BR_EOD") Next Bar at Market;
```
- 停損：進場價下方 1.5 ATR
- 停利：布林中軌（均值回歸目標）
- 時間出場：持倉≥5根K棒
- 盤末出場：13:40 強制平倉

### 6. 空單出場
```
BuyToCover ("SX_BR_SL") Next Bar at v_StopPrice Stop;
BuyToCover ("SX_BR_TP") Next Bar at v_BBMid Limit;
BuyToCover ("SX_BR_Time") Next Bar at Market;
BuyToCover ("SX_BR_EOD") Next Bar at Market;
```
- 停損：進場價上方 1.5 ATR
- 停利：布林中軌（均值回歸目標）
- 時間出場與盤末出場同多單邏輯

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_BR_Long` | `Buy` | 做多 | 進場 | 布林下軌超賣+RSI<30+上升趨勢 |
| `SE_BR_Short` | `SellShort` | 做空 | 進場 | 布林上軌超買+RSI>70+下降趨勢 |
| `LX_BR_SL` | `Sell` | 做多 | 出場 | 停損 ATR×1.5 |
| `LX_BR_TP` | `Sell` | 做多 | 出場 | 停利 布林中軌 |
| `LX_BR_Time` | `Sell` | 做多 | 出場 | 持倉≥5根K棒 |
| `LX_BR_EOD` | `Sell` | 做多 | 出場 | 13:40盤末平倉 |
| `SX_BR_SL` | `BuyToCover` | 做空 | 出場 | 停損 ATR×1.5 |
| `SX_BR_TP` | `BuyToCover` | 做空 | 出場 | 停利 布林中軌 |
| `SX_BR_Time` | `BuyToCover` | 做空 | 出場 | 持倉≥5根K棒 |
| `SX_BR_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **60 分鐘** | 45M, 120M | 60M 適合布林帶均值回歸週期 |
| **Data2** | 不需要 | — | 單週期策略 |

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
| `BBMult` | 2.0 | 1.50 | 2.50 | 0.25 | 5 | 布林帶標準差倍數 |
| `RSI_OS` | 30 | 25 | 35 | 5 | 3 | RSI超賣門檻 |
| `RSI_OB` | 70 | 65 | 75 | 5 | 3 | RSI超買門檻 |
| `StopATRMult` | 1.5 | 1.00 | 2.50 | 0.25 | 7 | 停損ATR倍數 |
| `MaxBars` | 5 | 3 | 8 | 1 | 6 | 最大持倉K棒 |

**全參數組合數**：5 × 3 × 3 × 7 × 6 = **1,890**（暴力窮舉）

### 四、暴力窮舉設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 最佳化方式 | 暴力窮舉（Exhaustive Search）|
| 預估評估次數 | 1,890 |
| 最佳化依據 | 最大的 Net Profit |
