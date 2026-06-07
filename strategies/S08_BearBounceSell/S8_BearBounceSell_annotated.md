# S8 BearBounceSell — 中文逐行註解

> 對應程式碼：`S8_BearBounceSell.pla`（MC12 直接使用的全英文版）
> 策略描述：`S8_BearBounceSell_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：F 類 — 空頭反彈放空
- **方向**：★做空
- **週期**：15 分鐘 + 日線(Data2)
- **核心邏輯**：空頭趨勢中（日線收盤 < MA20），當 15M RSI(6) 突破超買門檻、連續上漲、且偏離均線超過 2.5 ATR，判定反彈過度，放空

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `RSILen` | 6 | RSI 計算週期 |
| `RSIOverbought` | 85 | RSI 超買門檻 |
| `ConsecUpBars` | 3 | 需連續上漲的K棒數 |
| `DevATRMult` | 2.5 | 向上偏離 MA 的 ATR 倍數門檻 |
| `ATRLen` | 14 | ATR 計算週期 |
| `MA_Len` | 20 | 均線長度 |
| `StopATRMult` | 2.0 | 停損 = 進場價 + ATR × 2.0 |
| `TargetATRMult` | 3.0 | 停利 = 進場價 - ATR × 3.0 |
| `SessionStart` | 0845 | 交易時段開始 |
| `SessionEnd` | 1330 | 交易時段結束 |

---

## 逐段邏輯註解

### 1. 連續上漲計算
```
v_ConsecUp = 0;
If Close > Close[1] Then v_ConsecUp = v_ConsecUp + 1;
If Close[1] > Close[2] Then v_ConsecUp = v_ConsecUp + 1;
If Close[2] > Close[3] Then v_ConsecUp = v_ConsecUp + 1;
```
- S7 的鏡像邏輯，檢測連續收紅

### 2. 向上偏離度
```
v_Deviation = (Close - Average(Close, MA_Len)) / v_ATR;
```
- 收盤高於 MA20 的程度，ATR 單位

### 3. Data2 空頭過濾
```
v_TrendFilter = Close of Data2 < Average(Close of Data2, MA_Len)[1] of Data2;
```
- 日線收盤在 MA20 下方 = 空頭確認

### 4. 做空進場
```
SellShort ("SE_BB_Short") Next Bar at Market;
```
- 條件：空手 + 時段內 + RSI>85 + 連漲≥3根 + 偏離≥2.5ATR + 日線空頭

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `SE_BB_Short` | `SellShort` | 做空 | 進場 | RSI>85 + 連漲3根 + 偏離>2.5ATR + 日線空頭 |
| `SX_BB_SL` | `BuyToCover` | 做空 | 出場 | 停損 ATR×2.0 |
| `SX_BB_TP` | `BuyToCover` | 做空 | 出場 | 停利 ATR×3.0 |
| `SX_BB_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **15 分鐘** | 10M, 30M | 與 S7 對稱 |
| **Data2** | TXF1 **日線** | — | 趨勢過濾 |

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
| `RSILen` | 6 | 4 | 10 | 2 | 4 | RSI 週期 |
| `RSIOverbought` | 85 | 75 | 90 | 5 | 4 | 超買門檻 |
| `ConsecUpBars` | 3 | 2 | 5 | 1 | 4 | 連漲根數 |
| `DevATRMult` | 2.5 | 1.5 | 3.5 | 0.5 | 5 | 偏離門檻 |
| `StopATRMult` | 2.0 | 1.0 | 3.0 | 0.5 | 5 | 停損倍數 |
| `TargetATRMult` | 3.0 | 2.0 | 5.0 | 0.5 | 7 | 停利倍數 |

**全參數組合數**：4 × 4 × 4 × 5 × 5 × 7 = **11,200**（GA 優化）

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
