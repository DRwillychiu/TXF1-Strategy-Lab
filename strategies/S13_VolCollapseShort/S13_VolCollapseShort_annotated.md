# S13 VolCollapseShort — 中文逐行註解

> 對應程式碼：`S13_VolCollapseShort.pla`（MC12 直接使用的全英文版）
> 策略描述：`S13_VolCollapseShort_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：C 類 — 波動率型
- **方向**：★做空
- **週期**：30 分鐘
- **核心邏輯**：偵測 ATR 百分位處於極低水準（第20百分位以下），搭配空頭趨勢偏向（收盤 < SMA20 + MACD柱狀體為負），當價格跌破近期低點一定幅度後做空，捕捉低波動後的空頭爆發

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `ATRLen` | 14 | ATR計算週期 |
| `PctileLookback` | 60 | ATR百分位排名回溯期 |
| `PctileThresh` | 20 | ATR百分位門檻，需低於第20百分位 |
| `SMA_Len` | 20 | 均線週期，確認空頭趨勢 |
| `LowestLen` | 10 | 近期最低價回溯期 |
| `BreakATRMult` | 0.3 | 突破幅度，跌破低點需超過 ATR × 0.3 |
| `StopATRMult` | 2.0 | 停損 = 進場價 + ATR × 2.0 |
| `TargetATRMult` | 2.5 | 停利 = 進場價 - ATR × 2.5 |
| `MaxBars` | 7 | 最大持倉7根K棒後強制出場 |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態

### 2. 指標計算
```
v_ATR = AvgTrueRange(ATRLen);
v_SMA = Average(Close, SMA_Len);
v_LowestL = Lowest(Low, LowestLen);
v_MACD = MACD(Close, 12, 26);
v_Signal = XAverage(v_MACD, 9);
v_Hist = v_MACD - v_Signal;
```
- ATR14 用於波動率百分位計算
- SMA20 確認空頭趨勢
- 10根最低價作為突破參考
- MACD 柱狀體確認空頭動能

### 3. ATR 百分位排名
```
v_Count = 0;
For v_i = 1 To PctileLookback Begin
    If v_ATR <= v_ATR[v_i] Then
        v_Count = v_Count + 1;
End;
If PctileLookback > 0 Then
    v_ATRRank = v_Count / PctileLookback * 100;
```
- 計算當前 ATR 在過去60根中的百分位排名
- 排名越低代表波動率越低（壓縮越嚴重）

### 4. 做空進場
```
If v_Prev_MP = 0 And
   v_ATRRank <= PctileThresh And
   Close[1] < v_SMA[1] And
   Close < v_LowestL[1] - BreakATRMult * v_ATR And
   v_Hist[1] < 0 Then Begin
    SellShort ("SE_VC_Short") Next Bar at Market;
    v_BarsSinceEntry = 0;
End;
```
- 空手狀態
- ATR 百分位 ≤ 20（極低波動率）
- 前根收盤 < SMA20（空頭趨勢）
- 當根收盤跌破近期低點 - 0.3 ATR（確認突破）
- MACD 柱狀體 < 0（空頭動能）

### 5. 出場管理
```
BuyToCover ("SX_VC_SL") Next Bar at v_StopPrice Stop;
BuyToCover ("SX_VC_TP") Next Bar at v_TargetPrice Limit;
BuyToCover ("SX_VC_Time") Next Bar at Market;
BuyToCover ("SX_VC_EOD") Next Bar at Market;
```
- 停損：進場價上方 2.0 ATR
- 停利：進場價下方 2.5 ATR（R:R = 1.25:1）
- 時間出場：持倉超過7根K棒
- 盤末出場：13:40 強制平倉

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `SE_VC_Short` | `SellShort` | 做空 | 進場 | ATR極低百分位+空頭+突破 |
| `SX_VC_SL` | `BuyToCover` | 做空 | 出場 | 停損 ATR×2.0 |
| `SX_VC_TP` | `BuyToCover` | 做空 | 出場 | 停利 ATR×2.5 |
| `SX_VC_Time` | `BuyToCover` | 做空 | 出場 | 持倉≥7根K棒 |
| `SX_VC_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **30 分鐘** | 15M, 45M | 30M 平衡波動率偵測精度與雜訊 |
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
| `PctileThresh` | 20 | 10 | 30 | 5 | 5 | ATR百分位門檻 |
| `BreakATRMult` | 0.3 | 0.1 | 0.5 | 0.1 | 5 | 突破幅度ATR倍數 |
| `TargetATRMult` | 2.5 | 2.0 | 4.0 | 0.5 | 5 | 停利ATR倍數 |
| `StopATRMult` | 2.0 | 1.5 | 3.0 | 0.5 | 4 | 停損ATR倍數 |

**全參數組合數**：5 × 5 × 5 × 4 = **500**（暴力窮舉）

### 四、暴力窮舉設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 最佳化方式 | 暴力窮舉（Exhaustive Search）|
| 預估評估次數 | 500 |
| 最佳化依據 | 最大的 Net Profit |
