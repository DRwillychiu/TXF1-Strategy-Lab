# S7 BullPullbackLong — 中文逐行註解

> 對應程式碼：`S7_BullPullbackLong.pla`（MC12 直接使用的全英文版）
> 策略描述：`S7_BullPullbackLong_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：E 類 — 多頭回檔抄底
- **方向**：★做多
- **週期**：15 分鐘 + 日線(Data2)
- **核心邏輯**：多頭趨勢中（日線收盤 > MA20），當 15M RSI(6) 跌破超賣門檻、連續下跌、且偏離均線超過 2.5 ATR，判定急跌過度，做多抄底

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `RSILen` | 6 | RSI 計算週期（短週期捕捉極端超賣）|
| `RSIOversold` | 15 | RSI 超賣門檻 |
| `ConsecDownBars` | 3 | 需連續下跌的K棒數 |
| `DevATRMult` | 2.5 | 價格偏離 MA 的 ATR 倍數門檻 |
| `ATRLen` | 14 | ATR 計算週期 |
| `MA_Len` | 20 | 均線長度（Data1 偏離計算 + Data2 趨勢過濾）|
| `StopATRMult` | 2.0 | 停損 = 進場價 - ATR × 2.0 |
| `TargetATRMult` | 3.0 | 停利 = 進場價 + ATR × 3.0 |
| `SessionStart` | 0845 | 交易時段開始 |
| `SessionEnd` | 1330 | 交易時段結束 |

---

## 逐段邏輯註解

### 1. 指標計算
```
v_RSI = RSI(Close, RSILen);
v_ATR = AvgTrueRange(ATRLen);
```
- RSI(6) 極短週期，能快速反應超賣狀態

### 2. 連續下跌計算
```
v_ConsecDown = 0;
If Close < Close[1] Then v_ConsecDown = v_ConsecDown + 1;
If Close[1] < Close[2] Then v_ConsecDown = v_ConsecDown + 1;
If Close[2] < Close[3] Then v_ConsecDown = v_ConsecDown + 1;
```
- 逐根回溯檢查，計算最近3根是否連續收黑

### 3. 偏離度計算
```
v_Deviation = (Average(Close, MA_Len) - Close) / v_ATR;
```
- 收盤價低於 MA20 的程度，以 ATR 為單位衡量
- 值越大代表偏離越嚴重（跌得越深）

### 4. Data2 趨勢過濾
```
v_TrendFilter = Close of Data2 > Average(Close of Data2, MA_Len)[1] of Data2;
```
- 日線收盤在 MA20 上方 = 多頭趨勢確認
- 使用 `[1]` 索引確保引用已收盤日線（MC12 Data2 當根不可靠）

### 5. 做多進場
```
Buy ("LE_BP_Long") Next Bar at Market;
```
- 條件：空手 + 時段內 + RSI<15 + 連跌≥3根 + 偏離≥2.5ATR + 日線多頭

### 6. 出場管理
```
Sell ("LX_BP_SL") Next Bar at v_StopPrice Stop;
Sell ("LX_BP_TP") Next Bar at v_TargetPrice Limit;
Sell ("LX_BP_EOD") Next Bar at Market;
```

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_BP_Long` | `Buy` | 做多 | 進場 | RSI<15 + 連跌3根 + 偏離>2.5ATR + 日線多頭 |
| `LX_BP_SL` | `Sell` | 做多 | 出場 | 停損 ATR×2.0 |
| `LX_BP_TP` | `Sell` | 做多 | 出場 | 停利 ATR×3.0 |
| `LX_BP_EOD` | `Sell` | 做多 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **15 分鐘** | 10M, 30M | 15M 平衡訊號頻率與超賣精確度 |
| **Data2** | TXF1 **日線** | — | 趨勢過濾用，不可省略 |

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
| `RSIOversold` | 15 | 10 | 25 | 5 | 4 | 超賣門檻 |
| `ConsecDownBars` | 3 | 2 | 5 | 1 | 4 | 連跌根數 |
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
