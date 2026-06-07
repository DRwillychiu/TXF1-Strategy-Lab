# S12 WeekdayMomentum — 中文逐行註解

> 對應程式碼：`S12_WeekdayMomentum.pla`（MC12 直接使用的全英文版）
> 策略描述：`S12_WeekdayMomentum_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：E 類 — 統計型
- **方向**：★雙向
- **週期**：日線
- **核心邏輯**：觀察週一、週二連續同方向動量（漲幅或跌幅超過門檻），於週三進場延續動量方向，捕捉週間趨勢慣性

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `MinDayReturnPct` | 0.3 | 單日最低報酬率門檻（%），週一二漲/跌幅需超過此值 |
| `SMA_Len` | 20 | 均線週期，確認趨勢方向 |
| `ATRLen` | 14 | ATR計算週期 |
| `StopATRMult` | 1.5 | 停損 = 進場價 ± ATR × 1.5 |
| `TargetATRMult` | 2.0 | 停利 = 進場價 ± ATR × 2.0 |

---

## 逐段邏輯註解

### 1. 部位狀態追蹤
```
v_Prev_MP = MarketPosition[1];
```
- 取前一根K棒的部位狀態

### 2. 指標計算
```
v_SMA = Average(Close, SMA_Len);
v_ATR = AvgTrueRange(ATRLen);
```
- SMA20 用於趨勢過濾
- ATR14 用於停損停利計算

### 3. 週間報酬計算
```
If DayOfWeek(Date) = 3 Then Begin
    If Open[2] > 0 Then v_MonReturn = (Close[2] - Open[2]) / Open[2] * 100;
    If Open[1] > 0 Then v_TueReturn = (Close[1] - Open[1]) / Open[1] * 100;
End;
```
- 僅在週三計算週一與週二的日內報酬率
- `DayOfWeek(Date) = 3` 對應週三

### 4. 做多進場
```
If v_Prev_MP = 0 And DayOfWeek(Date) = 3 And
   v_MonReturn > MinDayReturnPct And
   v_TueReturn > MinDayReturnPct And
   Close[1] > v_SMA[1] Then Begin
    Buy ("LE_WM_Long") Next Bar at Market;
End;
```
- 空手 + 週三
- 週一漲幅 > 0.3% + 週二漲幅 > 0.3%（連續多頭動量）
- 前根收盤 > SMA20（確認多頭趨勢）

### 5. 做空進場
```
If v_Prev_MP = 0 And DayOfWeek(Date) = 3 And
   v_MonReturn < -MinDayReturnPct And
   v_TueReturn < -MinDayReturnPct And
   Close[1] < v_SMA[1] Then Begin
    SellShort ("SE_WM_Short") Next Bar at Market;
End;
```
- 空手 + 週三
- 週一跌幅 > 0.3% + 週二跌幅 > 0.3%（連續空頭動量）
- 前根收盤 < SMA20（確認空頭趨勢）

### 6. 多單出場
```
Sell ("LX_WM_SL") Next Bar at v_StopPrice Stop;
Sell ("LX_WM_TP") Next Bar at v_TargetPrice Limit;
Sell ("LX_WM_EOD") Next Bar at Market;
```
- 停損：進場價下方 1.5 ATR
- 停利：進場價上方 2.0 ATR（R:R = 1.33:1）
- 盤末出場：13:25 強制平倉

### 7. 空單出場
```
BuyToCover ("SX_WM_SL") Next Bar at v_StopPrice Stop;
BuyToCover ("SX_WM_TP") Next Bar at v_TargetPrice Limit;
BuyToCover ("SX_WM_EOD") Next Bar at Market;
```
- 停損：進場價上方 1.5 ATR
- 停利：進場價下方 2.0 ATR
- 盤末出場：13:25 強制平倉

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_WM_Long` | `Buy` | 做多 | 進場 | 週一二連漲+多頭趨勢 |
| `SE_WM_Short` | `SellShort` | 做空 | 進場 | 週一二連跌+空頭趨勢 |
| `LX_WM_SL` | `Sell` | 做多 | 出場 | 停損 ATR×1.5 |
| `LX_WM_TP` | `Sell` | 做多 | 出場 | 停利 ATR×2.0 |
| `LX_WM_EOD` | `Sell` | 做多 | 出場 | 13:25盤末平倉 |
| `SX_WM_SL` | `BuyToCover` | 做空 | 出場 | 停損 ATR×1.5 |
| `SX_WM_TP` | `BuyToCover` | 做空 | 出場 | 停利 ATR×2.0 |
| `SX_WM_EOD` | `BuyToCover` | 做空 | 出場 | 13:25盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **日線** | — | 日線級別統計策略 |
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
| `MinDayReturnPct` | 0.3 | 0.20 | 0.60 | 0.05 | 9 | 單日報酬率門檻% |
| `StopATRMult` | 1.5 | 1.00 | 2.50 | 0.25 | 7 | 停損ATR倍數 |
| `TargetATRMult` | 2.0 | 1.50 | 3.50 | 0.25 | 9 | 停利ATR倍數 |

**全參數組合數**：9 × 7 × 9 = **567**（暴力窮舉）

### 四、暴力窮舉設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 最佳化方式 | 暴力窮舉（Exhaustive Search）|
| 預估評估次數 | 567 |
| 最佳化依據 | 最大的 Net Profit |
