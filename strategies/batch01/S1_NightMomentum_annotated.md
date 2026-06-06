# S1 NightMomentum — 中文逐行註解

> 對應程式碼：`S1_NightMomentum.pla`（MC12 直接使用的全英文版）
> 最後更新：2026-06-07
> 參數來源：Walk-Forward 優化結果

---

## 策略概述
- **類別**：A 類（時段型）
- **方向**：雙向（做多 + 做空）
- **週期**：15 分鐘
- **核心邏輯**：夜盤開盤前 N 根 K 棒形成「開盤區間」，突破高點做多、跌破低點做空

---

## 參數說明

| 參數 | WF 最佳值 | 原始值 | 說明 |
|------|----------|--------|------|
| `LookbackBars` | **6** | 4 | 夜盤開盤後幾根 K 棒形成區間（6×15M = 90分鐘） |
| `EntryOffset` | **6** | 10 | 突破區間高/低後加幾點才進場（過濾假突破） |
| `MinRange` | 30 | 30 | 區間寬度最低門檻（太窄 = 無方向性） |
| `MaxRange` | 200 | 200 | 區間寬度最高門檻（太寬 = 已走完行情） |
| `StopLossPts` | **80** | 60 | 固定停損點數 |
| `TakeProfitPts` | **160** | 120 | 固定停利點數 |
| `TrailActivate` | 50 | 50 | 獲利超過幾點啟動追蹤停損 |
| `TrailOffset` | 30 | 30 | 追蹤停損回撤幾點平倉 |
| `NightOpen` | 1500 | 1500 | 夜盤開盤時間（15:00） |
| `ExitTime` | 0430 | 0430 | 強制平倉時間（04:30） |

---

## 逐段邏輯註解

### 1. 偵測夜盤時段
```
v_IsNightSession = (Time >= NightOpen) or (Time < ExitTime);
```
- 15:00 以後 **或** 04:30 以前 → 判定為夜盤

### 2. 夜盤開盤重置
```
if Time >= NightOpen and Time[1] < NightOpen then begin
    v_NightHigh = 0;
    v_NightLow = 999999;
    v_NightBarCount = 0;
    v_RangeReady = false;
end;
```
- 當時間跨過 15:00 → 重置所有變數
- `Time[1] < NightOpen`：前一根 K 棒還不是夜盤 → 確定是剛開盤

### 3. 建構開盤區間
```
if v_IsNightSession and v_RangeReady = false then begin
    v_NightBarCount = v_NightBarCount + 1;
    if High > v_NightHigh then v_NightHigh = High;
    if Low < v_NightLow then v_NightLow = Low;
    if v_NightBarCount >= LookbackBars then begin
        v_RangeWidth = v_NightHigh - v_NightLow;
        if v_RangeWidth >= MinRange and v_RangeWidth <= MaxRange then
            v_RangeReady = true;
    end;
end;
```
- 逐根累計最高/最低價
- 滿 6 根後計算區間寬度
- 區間寬度在 30~200 點之間才啟動 → 過濾過窄（無方向）或過寬（行情已走完）的情況

### 4. 進場：區間突破
```
if v_RangeReady and v_IsNightSession and Time < ExitTime then begin
    if v_Prev_MP <= 0 then
        buy ("LE_NM_Long") next bar at v_NightHigh + EntryOffset stop;
    if v_Prev_MP >= 0 then
        sell short ("SE_NM_Short") next bar at v_NightLow - EntryOffset stop;
end;
```
- **做多**：價格觸及「區間高點 + 6 點」→ Stop 單進場
- **做空**：價格觸及「區間低點 - 6 點」→ Stop 單進場
- `v_Prev_MP` 避免同方向重複進場

### 5. 出場：停損/停利（MC12 內建函數）
```
SetStopLoss(StopLossPts * 200);      // 80 × 200 = 16,000 NTD
SetProfitTarget(TakeProfitPts * 200); // 160 × 200 = 32,000 NTD
```
- MC12 全域停損/停利函數，單位是金額（點數 × 合約乘數 200）

### 6. 出場：追蹤停損
```
if MarketPosition = 1 and MaxContractProfit / 200 >= TrailActivate then
    sell ("LX_NM_Trail") next bar at EntryPrice + TrailActivate - TrailOffset stop;
```
- 做多：獲利達 50 點後，在「進場價 + 50 - 30 = 進場價 + 20」設停損
- 做空：同理，鎖住至少 20 點利潤

### 7. 出場：時間平倉
```
if Time >= ExitTime and Time < NightOpen then begin
    if MarketPosition = 1 then
        sell ("LX_NM_Time") next bar at market;
    if MarketPosition = -1 then
        buy to cover ("SX_NM_Time") next bar at market;
end;
```
- 04:30 後強制平倉，避免留倉到日盤

---

## 進出場標籤對照表

| 標籤 | 指令 | 方向 | 類型 | 觸發條件 |
|------|------|------|------|---------|
| `LE_NM_Long` | `buy` | 做多 | 進場 | 突破區間高點 |
| `SE_NM_Short` | `sell short` | 做空 | 進場 | 跌破區間低點 |
| `LX_NM_Trail` | `sell` | 做多 | 出場 | 追蹤停損觸發 |
| `SX_NM_Trail` | `buy to cover` | 做空 | 出場 | 追蹤停損觸發 |
| `LX_NM_Time` | `sell` | 做多 | 出場 | 04:30 時間平倉 |
| `SX_NM_Time` | `buy to cover` | 做空 | 出場 | 04:30 時間平倉 |
| *(SetStopLoss)* | — | 多/空 | 出場 | 固定 80 點停損 |
| *(SetProfitTarget)* | — | 多/空 | 出場 | 固定 160 點停利 |

> **規則**：`LE_` = Long Entry、`LX_` = Long eXit、`SE_` = Short Entry、`SX_` = Short eXit
> 每個標籤唯一，多空絕不共用。

---

## MC12 設定

| 項目 | 設定 |
|------|------|
| Data1 | TXF1，15 分鐘 |
| Data2 | 不需要 |
| 回測區間 | 2020/01/01 ~ 今天 |
| 合約乘數 | 200 NTD/點 |
| 滑價 | 單邊 500 NTD |
| 口數 | 1 口 |

## MC12 參數優化建議範圍

| 參數 | 掃描範圍 | 步長 | Python 高原區 |
|------|---------|------|--------------|
| LookbackBars | 4 ~ 8 | 1 | 6-10 (plateau 44%) |
| EntryOffset | 2 ~ 12 | 2 | 0-18 (plateau 69%) |
| StopLossPts | 60 ~ 100 | 10 | 70-120 (plateau 50%) |
| TakeProfitPts | 120 ~ 200 | 10 | 110-200 (plateau 60%) |
| TrailActivate | 30 ~ 80 | 10 | 日線無法驗證 |
