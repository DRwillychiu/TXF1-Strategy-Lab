# S10 AdaptiveBreakout — 中文逐行註解

> 對應程式碼：`S10_AdaptiveBreakout.pla`（MC12 直接使用的全英文版）
> 策略描述：`S10_AdaptiveBreakout_strategy.md`（完整策略說明）
> 最後更新：2026-06-07
> 參數來源：初始設定（待優化）

---

## 策略概述
- **類別**：A 類 — 突破（位階自適應）
- **方向**：★雙向
- **週期**：30 分鐘
- **核心邏輯**：經典 N 根 K 棒高低點突破，核心創新在停損機制：`MinList(ATR*mult, Close*pct%)`，取 ATR 與百分比停損較小值，確保任何指數位階都有合理停損

---

## 參數說明
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `BreakoutBars` | 20 | 突破回溯 N 根K棒（30M × 20 ≈ 10 交易日）|
| `ATRLen` | 14 | ATR 計算週期 |
| `StopATRMult` | 2.0 | ATR 停損倍數 |
| `StopPctCap` | 0.015 | 百分比停損上限（1.5%）|
| `TargetATRMult` | 3.0 | 停利 ATR 倍數 |
| `MinVolRatio` | 1.0 | 最低成交量倍率（≥均量才進場）|
| `SessionStart` | 0845 | 交易時段開始 |
| `SessionEnd` | 1330 | 交易時段結束 |

---

## 逐段邏輯註解

### 1. 自適應停損計算（核心創新）
```
v_StopATR = v_ATR * StopATRMult;
v_StopPct = Close * StopPctCap;
v_AdaptiveStop = MinList(v_StopATR, v_StopPct);
```
- **低位階（10000）**：ATR ≈ 100 → ATR停損 200 vs 百分比停損 150 → 用 150
- **高位階（45000）**：ATR ≈ 400 → ATR停損 800 vs 百分比停損 675 → 用 675
- 自動在兩種停損機制間選擇較保守的

### 2. 通道計算
```
v_HH = Highest(High, BreakoutBars);
v_LL = Lowest(Low, BreakoutBars);
```
- N 根 K 棒最高價/最低價構成突破通道

### 3. 成交量過濾
```
v_VolOK = Volume >= Average(Volume, 20) * MinVolRatio;
```
- 確保突破時有足夠量能支撐（非假突破）

### 4. 雙向進場
```
Buy ("LE_AB_Long") Next Bar at Market;      // 向上突破
SellShort ("SE_AB_Short") Next Bar at Market; // 向下突破
```
- 收盤突破前 N 根最高/最低價 + 量能確認

### 5. 出場管理
```
Sell ("LX_AB_SL") Next Bar at v_StopPrice Stop;     // 自適應停損
Sell ("LX_AB_TP") Next Bar at v_TargetPrice Limit;   // ATR停利
Sell ("LX_AB_EOD") Next Bar at Market;                // 盤末
```
- 停損使用自適應機制，停利仍使用 ATR 倍數

---

## 進出場標籤對照表
| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_AB_Long` | `Buy` | 做多 | 進場 | 收盤 > N根最高價 + 量能確認 |
| `SE_AB_Short` | `SellShort` | 做空 | 進場 | 收盤 < N根最低價 + 量能確認 |
| `LX_AB_SL` | `Sell` | 做多 | 出場 | 自適應停損 MinList(ATR,Pct) |
| `LX_AB_TP` | `Sell` | 做多 | 出場 | 停利 ATR×3.0 |
| `LX_AB_EOD` | `Sell` | 做多 | 出場 | 13:40盤末平倉 |
| `SX_AB_SL` | `BuyToCover` | 做空 | 出場 | 自適應停損 MinList(ATR,Pct) |
| `SX_AB_TP` | `BuyToCover` | 做空 | 出場 | 停利 ATR×3.0 |
| `SX_AB_EOD` | `BuyToCover` | 做空 | 出場 | 13:40盤末平倉 |

---

## MC12 優化設定卡

### 一、交易操作週期
| 項目 | 主要設定 | 替代測試範圍 | 說明 |
|------|---------|-------------|------|
| **Data1** | TXF1 **30 分鐘** | 15M, 60M | 30M 平衡突破有效性與交易頻率 |
| **Data2** | 不需要 | 日線（可選趨勢確認）| 單週期已有效 |

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
| `BreakoutBars` | 20 | 10 | 40 | 5 | 7 | 突破回溯期 |
| `StopATRMult` | 2.0 | 1.0 | 3.0 | 0.5 | 5 | ATR停損倍數 |
| `StopPctCap` | 0.015 | 0.008 | 0.025 | 0.002 | 9 | 百分比停損 |
| `TargetATRMult` | 3.0 | 2.0 | 5.0 | 0.5 | 7 | 停利倍數 |
| `MinVolRatio` | 1.0 | 0.5 | 2.0 | 0.5 | 4 | 量能倍率 |

**全參數組合數**：7 × 5 × 9 × 7 × 4 = **8,820**（可直接暴力掃描）

### 四、基因演算法（GA）設定
| 項目 | 設定 |
|------|------|
| 組合數範圍 | < 10,000 |
| 方式 | **直接暴力掃描**（全掃 8,820 組合）|
| 最佳化依據 | 最大的 Net Profit |
