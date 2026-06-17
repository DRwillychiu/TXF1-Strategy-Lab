# S2 v0.3 設計規格 — B 系列 + C 系列整合方案

**版本**：v0.2 (Phase 1 完成) → **v0.3** (B + C 整合)
**設計日**：2026-06-17
**目標**：解決 [`S2_known_issues.md`](S2_known_issues.md) 中 P1 優先級 8 個問題
**設計哲學**：所有改進用 **input switch 控制**，預設可關閉以**完整保留 v0.2 行為**

---

## 一、設計總則（避免重蹈 RangeForceExit 覆轍）

### 鐵律 1：所有新機制 input-switched
每個改進都有獨立開關，預設可設為「**等於 v0.2 行為**」。
這樣 MC 上可以做 A/B 對比：原版 vs 改進版績效。

### 鐵律 2：時段條件絕對閉區間
B/C 系列**不涉及時段條件**，所以無 MC Time 24-hour 陷阱風險。
但作為原則：任何 `Time >= X` 都必須伴隨 `Time <= Y` 或日期/狀態隔離。

### 鐵律 3：先解決設計，不急著回測
> 「糟糕的設計，不管回測多少次都是糟糕的東西」— 用戶 2026-06-17

v0.3 完成後才有資格做 Phase 2 真實回測。

### 鐵律 4：保留與 L1 V2.6 的設計一致性
S2 是 Swing-Trend 類（與 L1 同類），保護機制應參考 L1 經過實戰驗證的設計。

---

## 二、B 系列：假突破過濾完整化

### B-1: 動態 BreakOffset

**現況**：固定 5 點偏移
**問題**：小波動日（MotherRange=50）和大波動日（MotherRange=400）用相同過濾 → 大波動日過濾過弱

**設計**：
```powerlanguage
{ B-1: 動態 BreakOffset = MotherRange × X%, 最少 MinBreakOffset 點 }
v_DynBreakOffset = MaxList(v_MotherRange * BreakOffset_Pct / 100,
                            MinBreakOffset);

{ 使用方式 }
Close > High of Data2[1] + v_DynBreakOffset   { 多 }
Close < Low  of Data2[1] - v_DynBreakOffset   { 空 }
```

**新 inputs**：
- `BreakOffset_Pct(5)` — 突破偏移占 MotherRange 的百分比
- `MinBreakOffset(5)` — 下限，防止小波動日偏移過小
- `BreakOffset_Mode(1)` — 0=固定 (v0.2)，1=動態 (v0.3 預設)

**預期效果**：
- MotherRange = 50 → DynBreakOffset = 5（MinBreakOffset 兜底）
- MotherRange = 100 → DynBreakOffset = 5（5% 計算 = 5）
- MotherRange = 200 → DynBreakOffset = 10
- MotherRange = 400 → DynBreakOffset = 20

### B-2: 連續 N 根 K 站穩確認

**現況**：突破當根 next bar at Market 立刻進
**問題**：被「突破後立刻收回」的 trap 抓住

**設計**：兩階段進場
```powerlanguage
{ Stage 1: 突破發生, 標記「準備中」狀態 }
if v_IsInsideBar and Close > High of Data2[1] + v_DynBreakOffset then begin
    v_PendingLong_Bars = 1;
    v_PendingLong = true;
end;

{ Stage 2: 後續 K 棒持續站穩 }
if v_PendingLong then begin
    if Close > High of Data2[1] then begin   { 仍站穩 }
        v_PendingLong_Bars = v_PendingLong_Bars + 1;
        if v_PendingLong_Bars >= ConfirmBars then begin
            buy ("LE_IB_Entry") next bar at market;
            v_PendingLong = false;
            v_PendingLong_Bars = 0;
        end;
    end else begin   { 跌回 → cancel }
        v_PendingLong = false;
        v_PendingLong_Bars = 0;
    end;
end;
```

**新 inputs**：
- `ConfirmBars(2)` — 需要連續站穩的 K 棒數
- `Confirm_On(true)` — 開關（false 時行為與 v0.2 相同）

**Trade-off**：
- ✅ 過濾掉 false breakout
- ❌ 進場延後 1 根 K（30 分鐘）→ 進場價可能差 5-15 點
- 預期：過濾掉的 false breakout 損失 > 進場差價的成本

### B-3: 量能放大確認

**現況**：無
**問題**：真突破伴隨量能放大；假突破量能平淡

**設計**：
```powerlanguage
{ 30M 級別量能比較 }
v_VolMA = Average(Volume, VolMALen);
v_VolPass = (Volume > v_VolMA * VolMultiplier);

{ 加入進場條件 }
if (v_VolPass or VolFilter_On = false) and ... then ...
```

**新 inputs**：
- `VolFilter_On(true)` — 開關
- `VolMALen(20)` — 量能平均長度
- `VolMultiplier(1.2)` — 量能放大倍數要求

**風險檢查**：
- ⚠️ MC PowerLanguage 中 TXF1 30M Volume = 該 K 棒成交口數，**確認 data feed 有 Volume**
- 若 Volume 全為 0 → VolFilter_On 必須關掉

### B-4: 快速回測過濾

**現況**：無
**問題**：突破後快速回測 = 假突破特徵

**設計**：**已被 B-2 涵蓋**
- B-2 要求 ConfirmBars 根都站穩 → 自動排除快速回測
- 不需要額外實作

---

## 三、C 系列：停損 SOP 完整化（4 層保護）

### 設計哲學：4 層遞進保護

```
Layer 0: Initial SL (Frozen at entry)           ← v0.2 已有
Layer 1: Break Even (BE)  ←★ 新增 C-1
Layer 2: Stop Profit (SP) ←★ 新增 C-3
Layer 3: Trailing Stop    ←★ 新增 C-2
```

**Final SL = Max(Initial, BE, SP, Trail)**（取最高 = 最保護）

### C-1: Break Even (保本停損)

**設計**：盈利達到 MotherRange × X% 時，SL 上移到 EntryPrice
```powerlanguage
{ Long: 追蹤峰值 close (而非 high, 避免 wick 干擾) }
if Close > v_HighestClose then v_HighestClose = Close;
v_Peak_Profit_L = v_HighestClose - EntryPrice;

{ BE 啟用條件 }
if BE_On and v_Peak_Profit_L >= v_MotherRange * BE_Trigger_Pct / 100 then
    v_BE_Armed_L = true;

{ BE Level }
v_BE_Level_L = IIff(v_BE_Armed_L, EntryPrice, 0);
```

**新 inputs**：
- `BE_On(true)` — 開關
- `BE_Trigger_Pct(75)` — 盈利 75% MotherRange 時啟動

**理由**：
- v0.2 TP = MotherRange × 1.5
- BE 啟動點 = MotherRange × 0.75 = TP 的 50%
- 賺到一半時，先保本 → 避免 round-trip

**注意（重要）**：
- L1/L2 的 BE 已被撤回（趨勢策略不要 BE）
- 但 S2 是「**早期突破**」而非「成熟趨勢延續」
- S2 的假突破風險 > 趨勢被切斷風險
- 所以 BE 對 S2 應該有效（待 Phase 2 驗證）

### C-2: Trailing Stop（移動停損）

**設計**：TP 觸及 70% 後啟動，跟隨峰值 close
```powerlanguage
{ Trail 啟用條件 }
if Trail_On and v_Peak_Profit_L >= v_TargetDist * Trail_Trigger_Pct / 100 then
    v_Trail_Armed_L = true;

{ Trail Level: 跟蹤峰值, 留 X% MotherRange 緩衝 }
if v_Trail_Armed_L then
    v_Trail_Level_L = v_HighestClose - v_MotherRange * Trail_Offset_Pct / 100;
```

**新 inputs**：
- `Trail_On(true)` — 開關
- `Trail_Trigger_Pct(70)` — TP 達 70% 時啟動
- `Trail_Offset_Pct(30)` — Trail 距離峰值 = MotherRange × 30%

**理由**：
- TP = MotherRange × 1.5
- Trail 啟動 = TP × 70% = MotherRange × 1.05
- 啟動後讓利潤奔跑超越 TP
- 滿足「**趨勢策略讓利潤奔跑**」鐵律

### C-3: Stop Profit（從 L1 V2.6 移植）

**設計**：盈利達 MotherRange × X 倍時啟動，鎖 (1 - GiveBack%) 利潤
```powerlanguage
{ SP 啟用條件 }
if SP_On and v_Peak_Profit_L >= v_MotherRange * SP_Trigger_Mult then
    v_SP_Armed_L = true;

{ SP Level: 鎖住 (100 - GiveBack)% 的峰值利潤 }
if v_SP_Armed_L then
    v_SP_Level_L = EntryPrice + v_Peak_Profit_L *
                   (1 - SP_GiveBack_Pct / 100);
```

**新 inputs**：
- `SP_On(true)` — 開關
- `SP_Trigger_Mult(1.0)` — 盈利達 MotherRange × 1 倍時啟動
- `SP_GiveBack_Pct(45)` — 容許從峰值回撤 45%（鎖 55%）

**理由**：
- 與 L1 V2.6 SP 相同哲學（peak ratchets up only）
- 但 S2 用 MotherRange 為單位（適應每筆交易的波動率）
- 對比 L1：用固定 250 點啟動

### C-4: 4 層整合 Final SL 計算

**設計**：取 4 層中最高的（最保護的）
```powerlanguage
v_Final_SL_L = MaxList(v_Frozen_SL_L,    { Layer 0 }
                  MaxList(v_BE_Level_L,    { Layer 1 }
                  MaxList(v_SP_Level_L,    { Layer 2 }
                          v_Trail_Level_L))); { Layer 3 }

{ 識別 source (用於 label 區分) }
if Close < v_Final_SL_L then
    sell ("LX_IB_SL_Gap") next bar at market
else begin
    if AbsValue(v_Final_SL_L - v_Frozen_SL_L) < 0.001 then
        sell ("LX_IB_SL") next bar at v_Final_SL_L stop
    else if v_SP_Armed_L and
            AbsValue(v_Final_SL_L - v_SP_Level_L) < 0.001 then
        sell ("LX_IB_SP") next bar at v_Final_SL_L stop
    else if v_Trail_Armed_L and
            AbsValue(v_Final_SL_L - v_Trail_Level_L) < 0.001 then
        sell ("LX_IB_Trail") next bar at v_Final_SL_L stop
    else
        sell ("LX_IB_BE") next bar at v_Final_SL_L stop;
end;

{ TP / Time Stop 仍保留 }
sell ("LX_IB_TP") next bar at EntryPrice + v_TargetDist limit;
if BarNumber - v_EntryBar >= MaxBarsHeld then
    sell ("LX_IB_Time") next bar at market;
```

**新出場標籤**：
- `LX_IB_SL_Gap` — 跳空跌穿 Final SL
- `LX_IB_BE` — 觸發保本停損
- `LX_IB_Trail` — 觸發移動停損
- `LX_IB_SP` — 觸發 Stop Profit
- `LX_IB_SL` / `LX_IB_TP` / `LX_IB_Time` 保留 v0.2

**Short 側鏡像**：對應 SX_ 前綴標籤。

---

## 四、Input 完整清單對比

### v0.2 Inputs (12 個)
```
BreakOffset(5)
StopPct(50)
TargetMult(1.5)
MinMotherRange(50)
MaxMotherRange(400)
MALen(20)
MaxBarsHeld(30)
MinStopPts(40)
Holiday_Flat_Time(415)
Registry_Valid_Until(1270101)
Manual_Kill_Switch(false)
Settlement_Flat_Time(1230)
```

### v0.3 Inputs (12 + 11 = 23 個)
```
{ v0.2 全部保留 (12 個) }
...

{ v0.3 新增 B 系列 (5 個) }
BreakOffset_Mode(1)       { 0=固定(v0.2), 1=動態(v0.3 預設) }
BreakOffset_Pct(5)        { 動態偏移百分比 }
MinBreakOffset(5)         { 偏移下限 }
ConfirmBars(2)            { 連續站穩根數 }
Confirm_On(true)          { 站穩確認開關 }
VolFilter_On(true)        { 量能過濾開關 }
VolMALen(20)              { 量能平均長度 }
VolMultiplier(1.2)        { 量能放大倍數 }

{ v0.3 新增 C 系列 (8 個) }
BE_On(true)               { BE 開關 }
BE_Trigger_Pct(75)        { BE 觸發 = MotherRange × X% }
Trail_On(true)            { Trail 開關 }
Trail_Trigger_Pct(70)     { Trail 觸發 = TP × X% }
Trail_Offset_Pct(30)      { Trail 偏移 = MotherRange × X% }
SP_On(true)               { SP 開關 }
SP_Trigger_Mult(1.0)      { SP 觸發 = MotherRange × X }
SP_GiveBack_Pct(45)       { SP 允許回撤百分比 }
```

**A/B 測試組合**：
- **v0.2 純原版**：所有 _On = false, BreakOffset_Mode = 0
- **v0.3 完整版**：所有 _On = true, BreakOffset_Mode = 1（預設）
- **半激進版**：只開 C 系列（保留 v0.2 進場 + 加強出場）
- **半保守版**：只開 B 系列（強化進場過濾 + v0.2 出場）

---

## 五、Variables 新增清單

```
{ v0.3 B 系列 }
v_DynBreakOffset(0)        { B-1 動態 BreakOffset }
v_VolMA(0)                 { B-3 量能平均 }
v_VolPass(false)           { B-3 量能通過 }
v_PendingLong(false)       { B-2 Long 等待站穩中 }
v_PendingShort(false)      { B-2 Short 等待站穩中 }
v_PendingLong_Bars(0)      { B-2 Long 已站穩根數 }
v_PendingShort_Bars(0)     { B-2 Short 已站穩根數 }

{ v0.3 C 系列 - Long }
v_HighestClose(0)          { Long 峰值 close }
v_Peak_Profit_L(0)         { Long 峰值利潤點數 }
v_Frozen_SL_L(0)           { Long Initial SL frozen }
v_BE_Armed_L(false)        { Long BE 已啟用 }
v_BE_Level_L(0)            { Long BE 位置 }
v_Trail_Armed_L(false)     { Long Trail 已啟用 }
v_Trail_Level_L(0)         { Long Trail 位置 }
v_SP_Armed_L(false)        { Long SP 已啟用 }
v_SP_Level_L(0)            { Long SP 位置 }
v_Final_SL_L(0)            { Long 最終 SL }

{ v0.3 C 系列 - Short }
v_LowestClose(0)
v_Peak_Profit_S(0)
v_Frozen_SL_S(0)
v_BE_Armed_S(false)
v_BE_Level_S(0)
v_Trail_Armed_S(false)
v_Trail_Level_S(0)
v_SP_Armed_S(false)
v_SP_Level_S(0)
v_Final_SL_S(0)
```

---

## 六、Flat 狀態 reset 邏輯

```powerlanguage
if MarketPosition = 0 then begin
    { v0.3 Long state reset }
    v_HighestClose     = 0;
    v_Peak_Profit_L    = 0;
    v_Frozen_SL_L      = 0;
    v_BE_Armed_L       = false;
    v_BE_Level_L       = 0;
    v_Trail_Armed_L    = false;
    v_Trail_Level_L    = 0;
    v_SP_Armed_L       = false;
    v_SP_Level_L       = 0;

    { Short state reset }
    v_LowestClose      = 999999;
    v_Peak_Profit_S    = 0;
    v_Frozen_SL_S      = 0;
    v_BE_Armed_S       = false;
    v_BE_Level_S       = 0;
    v_Trail_Armed_S    = false;
    v_Trail_Level_S    = 0;
    v_SP_Armed_S       = false;
    v_SP_Level_S       = 0;
end;
```

---

## 七、預期影響與待驗證假設

### 預期改進
| 維度 | v0.2 預期 | v0.3 預期 |
|------|---------|---------|
| 進場樣本 | 一年 5-8 筆 | **5-8 筆**（B-2 + B-3 過濾，可能略減）|
| WR | 64.7%（v0.1 Python）| **65-75%**（過濾品質提升）|
| 單筆均利 | +45k | **+30-60k**（Trail 拉長 + BE 防虧）|
| 單筆均虧 | -18k | **-12-15k**（BE 防 round-trip）|
| **PF** | 4.61（v0.1 樂觀）| **2.5-4.0（MC 真實預期）** |
| MDD | -64k（v0.1） | **-50-100k** |

### 待 Phase 2 驗證的假設
1. ✅ B-2 站穩確認真能過濾 false breakout（要看實際 cancel 率）
2. ❓ B-3 量能過濾是否 TXF1 30M 有效（需確認 Volume data 可用）
3. ❓ BE 對「早期突破」策略是否真有效（vs L1 BE 撤回經驗）
4. ❓ Trail 30% Offset 是否最佳（vs L1 用 MA55 Trail）
5. ❓ SP 45% GiveBack 是否最佳（vs L1 用 55%）

---

## 八、解決的 issue tracker 項目

完成後將 `S2_known_issues.md` 中以下標記為 ✅：

| Issue | 解決方案 |
|-------|--------|
| **B-1** | 動態 BreakOffset (BreakOffset_Pct × MotherRange) |
| **B-2** | ConfirmBars 連續站穩確認 |
| **B-3** | Volume > MA × VolMultiplier 過濾 |
| **B-4** | 已被 B-2 涵蓋（連續站穩 = 排除快速回測）|
| **C-1** | BE 機制（盈利 75% MotherRange 啟動）|
| **C-2** | Trailing Stop（TP 70% 後啟動，30% Offset）|
| **C-3** | Stop Profit（盈利 1.0 MotherRange 啟動，55% lock）|
| **C-4** | 4 層 Final SL 整合（Frozen + BE + SP + Trail）|

**29 題剩餘 21 題未解**（D 5 題 + A 3 題 + E 3 題 + F 3 題 + G 3 題 + H 2 題 + I 3 題）。

---

## 九、相關文件

- [策略完整說明](S2_InsideBarBreak_strategy.md) — v0.3 後將更新
- [Issue tracker](S2_known_issues.md) — B/C 解決後更新追蹤表
- [中文逐段註解](S2_InsideBarBreak_annotated.md) — v0.3 後將更新
- [憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [L1 V2.6 SP 設計參考](../../live/L1_TrendLong.pla)
