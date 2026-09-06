# L3 ConsolLong 規格

| | |
|---|---|
| 來源 | `_Backtest_Adaptive_Farmer_v14_PureLong` (v15.1) |
| 行為等同 | v15.0（v15.1 只改 label 字串） |
| 週期 | Data1 **15M** · Data2 **60M** · Data3 **Daily** |
| IOG | `false`（未宣告，取預設） |
| 方向 | 純多 |
| 出場控制 | **無 ExitFired**。常態同時掛 TP 限價 + SL 停價 |
| SHA-256 | ⬜ |

> 凡註解與程式碼衝突，以程式碼為準，列於第十節。

---

## 一 做什麼

在 60M 的**極窄箱體**（震幅收縮到參考區間的 10% 以內）中，等價格跌到箱體
下半部的支撐區，掛 Buy Stop 在**箱底**等突破反彈。目標是動態擺盪高點
（上限為箱頂），停損在箱底減 ATR 緩衝。

v14 的架構改版把 v13 的「半箱雙腿」改成**全箱單腿**——舊設計把箱體切成
下半段與上半段，結構上把報酬比封在 1.1 倍。

---

## 二 進場

`Buy next bar at v_Box_Btm Stop`，八個條件全成立。

| # | 條件 | 公式 |
|---|---|---|
| G1 | 空手 | `MarketPosition = 0` |
| G2 | 箱體合格 | `v_Box_Qualified = true`（見 2.2） |
| G3 | 60M 多方 | `Close of D2 > Average(Close,12) of D2` |
| G4 | 日線濾網 | `Close of D3 > MA20` **或** `> MA60` |
| G5 | 非假日尾盤 | `v_Holiday_Block = false` |
| G6 | 非結算日 | `v_Settlement_Day = false` |
| G7 | 非開盤波動區 | `v_Opening_Block = false` |
| G8 | 報酬風險比合格 | `v_RR_Qualified = true` |

再加兩條位置條件：

```
Close < v_Support_Zone                 ← 在支撐區內
Close > v_Box_Btm − v_ATR_Buffer       ← 還沒跌破停損位
```

### 2.1 箱體

```
v_Ref_High = Highest(High, 16)[1] of Data2
v_Ref_Low  = Lowest(Low,  16)[1] of Data2
成立：High of D2 <= Ref_High 且 Low of D2 >= Ref_Low
      且 Curr_Range / Ref_Range <= 0.1        ← 極窄，L4 是 0.7
失效：Close of D2 突破 Box_Top 或 Box_Btm     ← 用 Close，與 L5 不同
```

### 2.2 箱體合格（Dim 1）

```
v_Box_Range = Box_Top − Box_Btm
v_Box_Qualified = (v_Box_Range / ATR(9) >= 8.5)
v_Support_Zone  = Box_Btm + Box_Range × 0.50
```

`Min_Box_ATR = 8.5` 是兩輪 MC9 掃描收斂的內部解（85% 分位，未貼邊界）。

> **合格只擋進場，不擋出場**——註解明載。持倉中箱體變小仍照常管理。

### 2.3 開盤波動封鎖

```
若 Open_Block_End > 0：
   Time = 500              → 封鎖      （夜盤最後一根 → 09:00 成交）
   900 <= Time < 945       → 封鎖      （→ 09:15 / 09:30 / 09:45 成交）
```

**封鎖的是「成交會落在禁區」的訊號，不是訊號本身的時間。**

依據：日盤開盤進場對盤整策略結構性有毒——機構在開盤獵殺箱底，支撐邏輯失效。
OB930 第一版移除 08:45–09:30，但級聯效應把 19 筆推到 09:45（勝率 10.5%、−604K）。
OB945 消除級聯，10:xx 是第一個獲利時段（勝率 41%、+134K）。

### 2.4 報酬風險比閘門

```
若 Min_RR > 0 且 SL_Pct > 0 且 Box_Range > 0：
   若 Box_Range < 1.0 × Box_Btm × 0.55 / 100 → v_RR_Qualified = false
```

依據：27% 的 CL_TP 交易報酬小於風險。箱寬變動範圍 36–1188 點，
但 SL_Pct 上限近乎固定，所以窄箱結構上就是負期望值。

### 2.5 Re-entry 標籤

```
定義：同一 consolidation episode + 前一筆停損虧損 + 新單價 <= 前次進場價
```

標頭明確說明**不能沿用 L2 的定義**：

> L2 的定義在 L3 上會選中 360 筆中的 134 筆（37%）。L3 以 `v_Box_Btm` 掛
> Buy Stop，而箱底是**移動的結構位**，所以「進場價不高於前次」多半只代表
> 「箱子沒往上移」，根本不是 re-entry。

`v_MktExit_Ordered` 排除市價出場——L3 的 200 筆虧損出場中有 33 筆不是停損
（28 CL_BreakExit、4 CL_Holiday、1 CL_Settlement），只測「虧損」會過度計數。

---

## 三 持倉管理

### 3.1 P3b 引擎停損

```
SetStopContract;                                    ← 在 if v_is_in_consolidation 之內
若 v_Box_Qualified 且 MarketPosition <= 0：
   v_SL_Distance = |Close − (v_Box_Btm − v_ATR_Buffer)|
   若 SL_Pct > 0：min(v_SL_Distance, Close × 0.55 / 100)
   SetStopLoss(v_SL_Distance × BigPointValue)
```

> **[D-1]** `SetStopContract` 在 `if v_is_in_consolidation` 之內。
> L5 的註解明白寫「must be outside conditional」。若 L5 正確，L3 的位置是錯的。

註解自承 BUG-3：距離用 Close 是**保守近似**——進場是 Buy Stop 在 Box_Btm，
`Close > Box_Btm` 時實際成交價接近 Close。

### 3.2 凍結停損與目標

```
若 v_SL_Locked = false：
   v_Frozen_SL = v_Box_Btm − v_ATR_Buffer
   若 SL_Pct > 0：
      v_SL_Pct_Floor = EntryPrice × (1 − 0.55/100)
      v_Frozen_SL = MaxList(v_Frozen_SL, v_SL_Pct_Floor)    ← 多單取高 = 緊

   v_Swing_High    = Highest(High, 80)                       ← Data1 15M，約 20 小時
   v_Frozen_Target = MinList(v_Swing_High, v_Box_Top)
   若 v_Frozen_Target < v_Mid_Line + ATR：v_Frozen_Target = v_Box_Top

   v_SL_Locked = true
```

**凍結價位**（同 L1/L2），非凍結中間變數（L4/L5）。

目標的兜底條款：擺盪高點太靠近中線就直接用箱頂，避免目標過近。

### 3.3 BE 層（永久關閉）

`BE_Trigger_Pts = 0`。v13.2D 的失敗紀錄：BE +50 點**低於箱體正常震盪包絡**，
100 筆 CL_BE 全數 0% 勝率，其中 96 筆是被截斷的目標命中。

---

## 四 出場

**無 ExitFired。常態同時兩張單。**

### 4.1 盤整期間（`v_is_in_consolidation = true`）

```
Sell ("CL_TP") next bar at v_Work_Target Limit;      ← 限價
Sell ("CL_SL") next bar at v_Work_SL     Stop;      ← 停價
```

> **兩張單同時掛出**。執行層必須支援 **OCO 語意**：一張成交，另一張撤銷。
> 這是 L3 與 L2/L4 最大的結構差異。

### 4.2 箱體失效

```
Sell ("CL_BreakExit") next bar at Market;
v_MktExit_Ordered = true;
```

> **[D-2]** 箱體一失效，整個 4.1 區塊不再執行——**TP 與 SL 兩張單都不再掛出**。
> 只剩市價出場。這是行為，不是缺陷，但移植時容易漏。

### 4.3 安全出場（Priority 0，永遠執行）

```
若 v_Registry_Expired          → CL_RegistryEnd
否則若 假日尾盤 且 Time >= 415  → CL_Holiday
否則若 結算日 且 Time >= 1230   → CL_Settlement

若 Manual_Kill_Switch          → CL_Kill        ← 獨立 if，不在 else 鏈上
```

> **[D-3]** Kill 在 else-if 鏈外，與 L1 的 J-3 同型。
> 一根 K 棒可同時發出 4.1 的兩張 + 4.3 的一張 + Kill 一張 = **最多四張**。

---

## 五 強制條件

| 項目 | 值 |
|---|---|
| Holiday_Flat_Time | **415**（同 L4 L5） |
| Settlement_Flat_Time | 1230 |
| Registry_Valid_Until | 1270101 |
| Holiday_Tail | 63 筆，五支逐筆相同 |

---

## 六 狀態

| 變數 | 類別 | 重置 |
|---|---|---|
| `v_SL_Locked` `v_Frozen_SL` `v_Frozen_Target` `v_SL_Pct_Floor` | per-trade | 空手 |
| `v_BE_Armed` `v_BE_IsFloor` | per-trade | 空手 |
| `v_is_in_consolidation` `v_Box_Top` `v_Box_Btm` | per-session，**需 `[1]`** | 永不 |
| `v_Episode_ID` | 跨交易 | 永不（只增） |
| `v_MktExit_Ordered` | 跨交易 | **只在持倉時歸假** |
| `v_Last_EntryPrice` `v_ReEntry_Armed` `v_ReEntry_Price` `v_ReEntry_Episode` | 跨交易 | episode 變更時解除 |
| `v_Prev_MP` | 跨交易 | 腳本最末行 |

`v_MktExit_Ordered` 的重置慣用法值得注意：

```
if MarketPosition = 1 then v_MktExit_Ordered = false;
```

**只在持倉時重置**，所以在轉為空手那一根，它仍帶著最後一次在倉的值——
這正是 latch 需要讀到的東西。

---

## 七 承諾與斷言

| # | 承諾 | 斷言 | 驗證 |
|---|---|---|---|
| 1 | 凍結停損不隨 ATR 漂移 | 持倉期間 `v_Frozen_SL` 不變 | ✓ |
| 2 | SL_Pct 封頂 | `v_Frozen_SL >= EntryPrice × (1 − 0.55%)` | ✓ |
| 3 | MaxList 取最緊 | 多單較高價位 = 較緊 | ✓ |
| 4 | 目標不超過箱頂 | `v_Frozen_Target <= v_Box_Top` | ✓ |
| 5 | 合格只擋進場不擋出場 | 持倉時不檢查 `v_Box_Qualified` | ✓ |
| 6 | v15.1「zero behaviour change」 | 只有 label 不同 | ✓ |
| 7 | Iron Rule | `Time >= 415` 必平 | ✓ |
| 8 | 結算日 12:30 | `Time >= 1230` 不持倉 | ✓ |
| 9 | 決策時可計算性 | 每條件只讀已存在資料 | ✓ 無未來函數 |
| 10 | 單一部位 | `MarketPosition ∈ {0, 1}` | ✓ |
| 11 | 「一根一張停損單」 | — | **✗ 常態兩張（TP + SL）** |

第 11 條不是缺陷，是設計——但它讓 L3 無法沿用 L2/L4 的「單根單張」斷言。

---

## 八 觸發頻率

| 版本 | 筆數 | 淨利 |
|---|---|---|
| v15.0（含 OB945） | **376** | 2,446,000 |
| v15.1 anchor | **360** | 1,389,600 |
| v14.1 | 332 | 2,048,000 |

> **[D-4]** v15.0 與 v15.1 anchor 差 16 筆、超過 100 萬，但 v15.1 宣稱
> 「zero behaviour change」。**兩者測的不是同一段期間或同一組參數**，
> 標頭未說明。對帳前必須釐清。

Re-entry 次數**無法事前登記精確值**（「同一 episode」需要 K 棒資料，交易清單沒有），
改登記為區間：`20 <= CL_ReEntry <= 115`，預期靠近下限。**超過 115 代表 episode 閘門沒作用。**

---

## 九 模式差異

| # | 項目 | mc12 | live | v2 |
|---|---|---|---|---|
| 1 | 下單時機 | 次根開盤 | 立即 | 同 live |
| 2 | 收盤前兩根 | 允許 | 禁止 | 同 live |
| 3 | Kill 在鏈外 | 照抄 | 照抄 | 可加互斥旗標 |
| 4 | 箱體失效後撤單 | 照抄 | 照抄 | 待裁決 |
| 5 | BE 層 | 關閉 | 關閉 | 可重新設計 |

---

## 十 已知落差

**[D-1] SetStopContract 在盤整判斷內** `中`
L5 註解寫「must be outside conditional」。若正確，L3 與 L2 的位置皆錯。

**[D-2] 箱體失效後停損單消失** `中`
TP 與 SL 兩張單都不再掛出，只剩 BreakExit 市價。移植時極易漏。

**[D-3] Kill 在 else-if 鏈外** `中`
與 L1 的 J-3 同型。一根最多四張單。

**[D-4] v15.0 與 v15.1 anchor 差 16 筆** `高，擋住對帳基準`
360 vs 376 筆、1,389,600 vs 2,446,000，但宣稱零行為變更。需釐清測試條件。

**[D-5] 引擎停損距離用 Close 為近似** `低`
標頭自承 BUG-3，屬刻意的保守近似。

**[D-6] 結算日遇休市會標錯** `低`　五支共通。

---

## 十一 移植評估

| 特性 | 值 | 影響 |
|---|---|---|
| IOG | `false`（未宣告） | **預設值本身未經驗證** |
| 資料流 | 三條（15M / 60M / Daily） | 需 `quotes/align.py` |
| 單型 | Market + Stop + **Limit** | **需 Limit 單與 OCO** |
| 部位 | 單一 | 不需多腿 |
| 出場控制 | 無 ExitFired，常態兩張 | 需並存訂單管理 |
| 變數歷史 | 需 `v_is_in_consolidation[1]` | 需 `types/stateful.py` |
| 未來函數 | 無 | — |

> **移植順位 3。** L3 是第一支需要 **Limit 單與 OCO 撤銷語意**的策略。
> 執行層做到這裡才第一次被迫支援「多張單並存」。

---

## 十二 待決

| # | 項目 |
|---|---|
| 1 | `.pla` 的 SHA-256 |
| 2 | D-4：釐清 v15.0 與 v15.1 的測試條件，重跑作為對帳基準 |
| 3 | D-1：SetStopContract 位置是否為 bug |
| 4 | D-2：箱體失效後撤單是否為刻意 |
| 5 | BE 死碼（`BE_Trigger_Pts = 0`）是否移植 |
| 6 | `Freeze_SL_On = false` 的非凍結路徑是否移植 |
