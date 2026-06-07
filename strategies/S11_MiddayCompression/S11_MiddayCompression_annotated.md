# S11 MiddayCompression — 中文逐行註解

> 對應程式碼：`S11_MiddayCompression.pla`（MC12 直接使用的全英文版）
> 策略描述：`S11_MiddayCompression_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：A 類 — 時段型
- **方向**：★做多
- **週期**：45 分鐘
- **核心邏輯**：偵測 ATR 壓縮（短期 ATR < 長期 ATR 的 75%）加上窄幅 K 棒，在午盤時段突破前高做多，捕捉壓縮後的爆發行情

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `ATR_Fast` | 5 | 短期 ATR 計算週期 |
| `ATR_Slow` | 14 | 長期 ATR 計算週期 |
| `ATR_Ratio` | 0.75 | 壓縮門檻，短期ATR需低於長期ATR的75% |
| `SMA_Len` | 20 | 均線週期，確認多頭趨勢 |
| `RangeThreshPct` | 1.2 | 窄幅門檻，K棒振幅佔收盤價百分比需低於此值 |
| `StopATRMult` | 1.8 | 停損 = 進場價 - ATR_Slow × 1.8 |
| `TargetATRMult` | 3.0 | 停利 = 進場價 + ATR_Slow × 3.0 |
| `MaxBars` | 5 | 最大持倉5根K棒後強制出場 |
| `SessionStart` | 1200 | 交易時段開始（午盤） |
| `SessionEnd` | 1330 | 交易時段結束 |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態，避免 MC12 當根 MarketPosition 不穩定的問題

### 2. 指標計算
```
v_ATRFast = AvgTrueRange(ATR_Fast);
v_ATRSlow = AvgTrueRange(ATR_Slow);
v_SMA = Average(Close, SMA_Len);
If Close > 0 Then
    v_RangePct = (High - Low) / Close * 100;
```
- `v_ATRFast`：短期 ATR（5根），反映近期波動率
- `v_ATRSlow`：長期 ATR（14根），作為波動率基準
- `v_RangePct`：K棒振幅佔收盤價的百分比，用來判定窄幅

### 3. 做多進場
```
If v_Prev_MP = 0 And
   Time >= SessionStart And Time <= SessionEnd And
   v_ATRFast < v_ATRSlow * ATR_Ratio And
   Close[1] > v_SMA[1] And
   v_RangePct[1] < RangeThreshPct And
   Close > High[1] Then Begin
    Buy ("LE_MC_Long") Next Bar at Market;
    v_BarsSinceEntry = 0;
End;
```
- 空手狀態 + 午盤時段內（12:00~13:30）
- 短期 ATR < 長期 ATR × 0.75（波動率壓縮中）
- 前根收盤 > SMA20（多頭趨勢確認）
- 前根 K 棒為窄幅（振幅% < 1.2%）
- 當根收盤突破前根最高價（突破訊號）

### 4. 出場管理
```
Sell ("LX_MC_SL") Next Bar at v_StopPrice Stop;
Sell ("LX_MC_TP") Next Bar at v_TargetPrice Limit;
Sell ("LX_MC_Time") Next Bar at Market;
Sell ("LX_MC_EOD") Next Bar at Market;
```
- 停損：進場價下方 1.8 ATR
- 停利：進場價上方 3.0 ATR（R:R = 1.67:1）
- 時間出場：持倉超過5根K棒
- 盤末出場：13:40 強制平倉

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_MC_Long` | `Buy` | 做多 | 進場 | ATR壓縮+窄幅+午盤突破 |
| `LX_MC_SL` | `Sell` | 做多 | 出場 | 停損 ATR×1.8 |
| `LX_MC_TP` | `Sell` | 做多 | 出場 | 停利 ATR×3.0 |
| `LX_MC_Time` | `Sell` | 做多 | 出場 | 持倉≥5根K棒 |
| `LX_MC_EOD` | `Sell` | 做多 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **45 分鐘** | 30M, 60M | 45M 平衡午盤壓縮偵測與突破確認 |
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
| `ATR_Ratio` | 0.75 | 0.60 | 0.85 | 0.05 | 6 | ATR壓縮門檻比率 |
| `StopATRMult` | 1.8 | 1.2 | 2.5 | 0.2 | 7 | 停損ATR倍數 |
| `RangeThreshPct` | 1.2 | 0.8 | 1.8 | 0.2 | 6 | 窄幅K棒振幅門檻% |
| `TargetATRMult` | 3.0 | 2.0 | 4.0 | 0.5 | 5 | 停利ATR倍數 |

**全參數組合數**：6 × 7 × 6 × 5 = **1,260**（暴力窮舉）

### 四、暴力窮舉設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 最佳化方式 | 暴力窮舉（Exhaustive Search）|
| 預估評估次數 | 1,260 |
| 最佳化依據 | 最大的 Net Profit |
