# S6 FlashCrashMomentum — 中文逐行註解

> 對應程式碼：`S6_FlashCrashMomentum.pla`（MC12 直接使用的全英文版）
> 策略描述：`S6_FlashCrashMomentum_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：D 類 — 閃崩動量捕捉
- **方向**：★做空
- **週期**：5 分鐘
- **核心邏輯**：偵測價格加速崩跌（N根K棒跌幅/ATR超過門檻）加上成交量爆發，做空捕捉崩跌延伸利潤

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `AccelBars` | 5 | 計算價格加速度的回溯K棒數 |
| `AccelThresh` | 3.0 | 加速度門檻，跌幅需達ATR的3倍才觸發 |
| `VolSpikeRatio` | 2.0 | 成交量需達20根均量的2倍 |
| `ATRLen` | 14 | ATR計算週期 |
| `StopATRMult` | 2.0 | 停損 = 進場價 + ATR × 2.0 |
| `TargetATRMult` | 3.0 | 停利 = 進場價 - ATR × 3.0 |
| `ExitBars` | 10 | 最大持倉10根K棒後強制出場 |
| `SessionStart` | 0845 | 交易時段開始 |
| `SessionEnd` | 1330 | 交易時段結束（提前避開收盤波動） |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態，避免 MC12 當根 MarketPosition 不穩定的問題

### 2. 指標計算
```
v_ATR = AvgTrueRange(ATRLen);
v_Accel = (Close[AccelBars] - Close) / v_ATR;
v_VolRatio = Volume / Average(Volume, 20);
```
- `v_Accel`：價格加速度，衡量N根K棒內的跌幅相對於ATR有多劇烈
- `v_VolRatio`：當根成交量與20根平均量的比值，偵測量能爆發

### 3. 做空進場
```
If v_Prev_MP = 0 And
   Time >= SessionStart And Time <= SessionEnd And
   v_Accel >= AccelThresh And
   v_VolRatio >= VolSpikeRatio And
   Close < Close[1] Then Begin
    SellShort ("SE_FC_Short") Next Bar at Market;
```
- 空手狀態 + 交易時段內
- 價格加速度 ≥ 3.0 ATR（急跌中）
- 成交量 ≥ 均量2倍（恐慌拋售）
- 當根收盤 < 前根收盤（確認下跌方向）

### 4. 出場管理
```
BuyToCover ("SX_FC_SL") Next Bar at v_StopPrice Stop;
BuyToCover ("SX_FC_TP") Next Bar at v_TargetPrice Limit;
BuyToCover ("SX_FC_Time") Next Bar at Market;
BuyToCover ("SX_FC_EOD") Next Bar at Market;
```
- 停損：進場價上方 2.0 ATR
- 停利：進場價下方 3.0 ATR（R:R = 1.5:1）
- 時間出場：持倉超過10根K棒
- 盤末出場：13:40 強制平倉

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `SE_FC_Short` | `SellShort` | 做空 | 進場 | 加速度≥3ATR + 量爆發 |
| `SX_FC_SL` | `BuyToCover` | 做空 | 出場 | 停損 ATR×2.0 |
| `SX_FC_TP` | `BuyToCover` | 做空 | 出場 | 停利 ATR×3.0 |
| `SX_FC_Time` | `BuyToCover` | 做空 | 出場 | 持倉≥10根K棒 |
| `SX_FC_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **5 分鐘** | 3M, 10M | 5M平衡閃崩捕捉速度與雜訊過濾 |
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
| `AccelBars` | 5 | 3 | 10 | 1 | 8 | 加速度回溯期 |
| `AccelThresh` | 3.0 | 2.0 | 5.0 | 0.5 | 7 | 加速度門檻 |
| `VolSpikeRatio` | 2.0 | 1.5 | 3.0 | 0.5 | 4 | 量爆發倍率 |
| `StopATRMult` | 2.0 | 1.0 | 3.0 | 0.5 | 5 | 停損ATR倍數 |
| `TargetATRMult` | 3.0 | 2.0 | 5.0 | 0.5 | 7 | 停利ATR倍數 |
| `ExitBars` | 10 | 5 | 20 | 5 | 4 | 最大持倉K棒 |

**全參數組合數**：8 × 7 × 4 × 5 × 7 × 4 = **31,360**（GA 優化）

### 四、基因演算法（GA）設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | 10,000 ~ 100,000 |
| 族群規模 | 200 |
| 最大代數 | 200 |
| 突變率 | 0.05 |
| 預估評估次數 | 40,000 |
| 最佳化依據 | 最大的 Net Profit |
| 交配機率 | 0.90 |
| 收斂型態 | 世代數量 |
| Crossover 個體數 | 20 |
| 演算法類型 | 增加的（Incremental）|
| 更換方案 | 最差 |
