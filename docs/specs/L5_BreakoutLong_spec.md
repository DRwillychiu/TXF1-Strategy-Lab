# L5 BreakoutLong 規格

| | |
|---|---|
| 來源 | `_Research_L5_v19_9_R1_BreakoutLong` |
| 行為等同 | v19.9（R1 只加 Print 與三個計數器，不發任何單） |
| 週期 | Data1 **15M** · Data2 **Daily** · Data3 **Weekly** |
| IOG | `false`（未宣告，取預設） |
| 方向 | 純多 |
| 部位模型 | **雙腿 + 40% 分批出場 + `from Entry` 綁定** |
| SHA-256 | ⬜ |

> **五支裡部位模型最複雜的一支。** L1 難在時間粒度，L5 難在部位結構。

---

## 一 做什麼

在**日線**箱體中掛兩張 Buy Stop：一張在箱底、一張在中線。價格突破時進場，
達到目標先出 40%，剩下 60% 交給 MFE 三階動態追蹤停損去跑趨勢。

L1 + L3 的混合體：L3 的箱體進場，L1 的獲利保護哲學。

---

## 二 進場

**兩條腿，可各自成交。**

```
若 Close < v_Box_Btm  且 Close > v_Box_Btm − v_ATR_Buffer：
   Buy ("BL_Entry_Bot") next bar at v_Box_Btm  Stop;

若 Close < v_Mid_Line 且 Close > v_Mid_Line − v_ATR_Buffer：
   Buy ("BL_Entry_Mid") next bar at v_Mid_Line Stop;
```

三個共同閘門：

| # | 條件 | 公式 |
|---|---|---|
| G1 | 日線多方 | `Close of D2 > Average(Close,60) of D2` |
| G2 | 週線濾網 | `Close of D3 > MA20` **且** `> MA60` |
| G3 | 報酬風險比 | `v_Current_RR >= 1.1` |

再加 `MarketPosition = 0` 與 `v_Allow_Entry`。

### 2.1 箱體 — 建立在日線

```
v_Ref_High = Highest(High, 4)[1] of Data2       ← 四日箱
v_Ref_Low  = Lowest(Low,  4)[1] of Data2
成立：High of D2 <= Ref_High 且 Low of D2 >= Ref_Low
      且 Curr_Range / Ref_Range <= 0.6
失效：High of D2 > Box_Top 或 Low of D2 < Box_Btm     ← 用 High/Low
```

> **[D-1]** **L5 用 High/Low 判定失效，L3/L4 用 Close。**
> L5 的箱體因此脆弱得多——任何影線碰到就終止。同一份程式碼形狀，語意完全不同。

`Lookback_Bars = 4` 是**四個日線 K 棒**，不是四小時。L3/L4 是 16/15 根 60M。

### 2.2 幾何

```
v_Mid_Line        = (Box_Top + Box_Btm) / 2
v_Expected_Reward = (Box_Top − Box_Btm) / 2
v_Expected_Risk   = v_ATR_Buffer = ATR(35) × 4.5
v_Current_RR      = Reward / Risk

v_Target_Bot = v_Mid_Line − FrontRun_Ticks × TickSize      ← 需 MinMove/PriceScale
v_Target_Mid = v_Box_Top  − FrontRun_Ticks × TickSize
```

> `v_TickSize = MinMove / PriceScale` 是**商品屬性**。五支裡只有 L5 用到。

### 2.3 時間濾網

```
v_Allow_Entry = true
若 400 <= Time <= 500                → false     （深夜低流動性）
若 DayOfWeek = 6 且 Time >= 1330     → false     （週六）
若 v_Holiday_Block                   → false
若 v_Settlement_Day                  → false
```

v19.7 移除了三處 `DayOfWeek(Date) = 7` 死碼——PowerLanguage 的 DayOfWeek 回傳
0–6（Sun=0），**7 永遠不成立**。實測 4.8 年 152 筆，`BL_SatClose_*` 零觸發。

> L5 的深夜封鎖 400–500，L4 是 200–500。**L5 的夜盤資料顯示 02–04 進場淨 +87,800，
> 與 L4 的 −120,800 相反**，所以不套用 L4 的封鎖區間。

---

## 三 持倉管理

### 3.1 P3b 引擎停損

```
SetStopContract;                                   ← 頂層，註解寫「must be outside conditional」

若 MarketPosition <= 0：
   v_Guard_Distance = |Close − (v_Box_Btm − v_ATR_Buffer)|
   若 SL_Pct > 0：min(v_Guard_Distance, v_Box_Btm × 1.0 / 100)     ← 錨在箱底
   SetStopLoss(v_Guard_Distance × BigPointValue)
```

> **[D-2]** **SL_Pct 上限錨在 `v_Box_Btm`，其餘四支錨在 `Close`。** 未見註解說明理由。

兩條腿共用同一個 guard，用的是**較寬的 Bot 腿停損**——Mid 腿因此拿到多於必要的緩衝。
標頭註明這是刻意的保守做法。

### 3.2 凍結

```
若 Freeze_SL_On 且 v_SL_Locked = false：
   v_Frozen_ATR        = v_Current_ATR
   v_Frozen_ATR_Buffer = v_Frozen_ATR × 4.5
   v_SL_Locked         = true
```

凍結**中間變數**（同 L4），非最終價位（L1/L2/L3）。

### 3.3 Stage 1 — 全倉

```
v_ScaleOut_Size = Round(MaxContracts × 0.4, 0)
若 MaxContracts > 1 且 v_ScaleOut_Size = 0：v_ScaleOut_Size = 1

Sell ("BL_TP_Bot") v_ScaleOut_Size contracts
    from Entry ("BL_Entry_Bot") next bar at v_Target_Bot Limit;
Sell ("BL_TP_Mid") v_ScaleOut_Size contracts
    from Entry ("BL_Entry_Mid") next bar at v_Target_Mid Limit;

基礎停損：
v_Bot_Base_Stop = v_Box_Btm  − v_Frozen_ATR_Buffer
v_Mid_Base_Stop = v_Mid_Line − v_Frozen_ATR_Buffer
若 SL_Pct > 0：
   v_SL_Pct_Floor = EntryPrice × (1 − 1.0/100)
   兩者各自 MaxList(base, v_SL_Pct_Floor)                ← 多單取高 = 緊

Sell ("BL_SL_Bot") CurrentContracts contracts from Entry ("BL_Entry_Bot") ... Stop
Sell ("BL_SL_Mid") CurrentContracts contracts from Entry ("BL_Entry_Mid") ... Stop

若 BarsSinceEntry >= 31：
   Sell ("BL_TimeExit_Bot" / "_Mid") from Entry (...) next bar at Market
```

### 3.4 Stage 2/3 — 分批後的跑單

判定：`CurrentContracts < MaxContracts`

```
若 v_Trail_Active：
   MFE 三階：
      > ATR × 10.0  → 追蹤倍數 0.8
      > ATR ×  6.0  → 1.5
      > ATR ×  3.0  → 2.0
      否則          → 3.0
   v_Dynamic_Stop = v_Highest_Since_Entry − ATR × 倍數

   優先級：Trail > SP > BE
      若 v_Dynamic_Stop > MaxList(EntryPrice, v_SP_Floor) → BL_Trail_*
      否則若 SP 武裝 且 SP_Floor > EntryPrice             → BL_SP_*
      否則                                                → BL_BE_* at EntryPrice Stop

否則（追蹤未啟動）：
   SP > BE 兩選一
```

追蹤啟動：`High > v_Box_Top + ATR × 2.5`——**必須突破箱頂**才啟動。

### 3.5 SP 模組（永久關閉）

`SP_Trigger_Pts = 0`。五個變體 B/C/D/E/F 全數失敗：

> 三筆超級贏家（+376K、+177K、+131K）被砍到 +7K～+38K。

---

## 四 出場

**無 ExitFired。每腿各一張，兩腿並行。**

### 4.1 Priority 0 — 安全出場

```
若 Manual_Kill_Switch          → BL_Kill_Bot        + BL_Kill_Mid
否則若 v_Registry_Expired      → BL_RegistryEnd_*
否則若 假日 且 Time >= 415      → BL_Holiday_*
否則若 結算日 且 Time >= 1230   → BL_Settlement_*
```

Kill **在 else 鏈上**（與 L1/L3 不同），但**每次發兩張**（兩腿各一）。

### 4.2 箱體失效

```
Sell ("BL_BreakExit_Bot") from Entry ("BL_Entry_Bot") next bar at Market;
Sell ("BL_BreakExit_Mid") from Entry ("BL_Entry_Mid") next bar at Market;
```

同 L3：箱體失效後，Stage 1/2/3 的所有停損停利單都不再掛出。

### 4.3 單根訂單數上限

```
Stage 1 盤整中：TP × 2 + SL × 2 + 安全出場 × 2 + TimeExit × 2  = 最多 8 張
```

> **執行層必須支援每腿獨立的訂單集合，且腿與腿之間互不干擾。**

---

## 五 `from Entry` 綁定 — L5 獨有

全案 **28 處** `from Entry(...)`，只有 L5 使用。

標頭說明了為什麼 L5 沒有 re-entry 標籤：

> Renaming an entry **orphans every exit bound to it and the position loses all stops.**
> L2 / L3 / L4 有零個 `from Entry` 綁定，所以它們可以在進場側加 re-entry 標籤，L5 不行。

因此 L5 改用 **Print 日誌**觀測 re-entry：

```
L5_ENTRY, Date, Time, EntryPrice, EpisodeID, EntryNo, BoxTop, BoxBtm
EntryNo = 1   → 該箱體第一次進場
EntryNo >= 2  → re-entry
```

---

## 六 狀態

| 變數 | 類別 | 重置 |
|---|---|---|
| `v_Highest_Since_Entry` `v_Trail_Active` `v_Dynamic_Trail_Mult` | per-trade | 空手 |
| `v_SL_Locked` `v_Frozen_ATR` `v_Frozen_ATR_Buffer` | per-trade | 空手 |
| `v_Peak_Profit` `v_SP_Armed` `v_SP_Floor` | per-trade | 空手 |
| `v_Bot_Base_Stop` `v_Mid_Base_Stop` `v_SL_Pct_Floor` | per-trade | 空手 |
| `v_is_in_consolidation` `v_Box_Top` `v_Box_Btm` | per-session，**需 `[1]`** | 永不 |
| `v_Episode_ID` `v_Episode_Entries` | 跨交易 | 新箱體時 Entries 歸 0 |
| `v_Prev_MP` | 跨交易 | 腳本最末行 |
| **`CurrentContracts` / `MaxContracts`** | 引擎提供 | — |

> `CurrentContracts` 與 `MaxContracts` **不是策略變數，是引擎狀態**。
> Stage 判定完全靠它們，所以 `engine/position.py` 必須提供。

---

## 七 承諾與斷言

| # | 承諾 | 斷言 | 驗證 |
|---|---|---|---|
| 1 | 凍結 ATR 不漂移 | 持倉期間 `v_Frozen_ATR` 不變 | ✓ |
| 2 | SL_Pct 封頂初始停損 | `base_stop >= Entry × (1 − 1.0%)` | ✓ |
| 3 | SL_Pct 不套用 Stage 2/3 | 標頭明載「NOT applied to runner」 | ✓ 刻意 |
| 4 | 追蹤只在突破箱頂後啟動 | `High > Box_Top + ATR × 2.5` | ✓ |
| 5 | 分批 40% | `Round(MaxContracts × 0.4)` | ✓ |
| 6 | R1「no order change」 | 只加 Print 與計數器 | ✓ |
| 7 | DayOfWeek 0–6 | 無 `= 7` 的比較 | ✓ v19.7 已移除 |
| 8 | Iron Rule | `Time >= 415` 必平 | ✓ |
| 9 | 決策時可計算性 | 每條件只讀已存在資料 | ✓ 無未來函數 |
| 10 | 單一部位 | — | **✗ 雙腿，可同時持有** |
| 11 | 「每次平倉都有對應出場單」 | — | **✗ 見 D-3** |

---

## 八 觸發頻率

| 版本 | 筆數 | 淨利 | PF | MDD |
|---|---|---|---|---|
| v19.6 基線 | 162 | 1,713,000 | 2.136 | −193,200 (−16.61%) |

標頭註明：**待 v19.7 部署後以新 Excel 重新驗證。**

MC12 於 2026-08-26 的一次執行：**171 筆進場**。

---

## 九 模式差異

| # | 項目 | mc12 | live | v2 |
|---|---|---|---|---|
| 1 | 下單時機 | 次根開盤 | 立即 | 同 live |
| 2 | 收盤前兩根 | 允許 | 禁止 | 同 live |
| 3 | Debug_Entry_Log | `true` | **關閉** | 關閉 |
| 4 | SP 模組 | 關閉 | 關閉 | 可重新設計 |
| 5 | 箱體失效用 High/Low | 照抄 | 照抄 | 待裁決 |

`Debug_Entry_Log` 在最佳化掃描前必須設 False——一萬次迭代中的 Print 極慢。

---

## 十 已知落差

**[D-1] 箱體失效用 High/Low** `中`
L3/L4 用 Close。L5 的箱體因此脆弱得多，任何影線碰到就終止。
形狀相同語意不同，移植時極易照抄成 Close。

**[D-2] SL_Pct 錨在 `v_Box_Btm`** `中`
其餘四支錨在 `Close`。未見理由說明。

**[D-3] 引擎停損可在無出場單的情況下平倉** `高`
標頭實測：`SL_Pct = 1.0` 使 MC 引擎 `SetStopLoss` 直接平倉，
**171 筆中有 1 筆被報為 "Stop Loss" 而無對應的 Sell 標籤**。

> 出場側標籤永遠標不到這條路徑。
> **Python 必須把引擎停損記成一種獨立的出場類型**，否則對帳會出現
> 「有平倉但找不到對應出場單」。這是 L5 加 Print 日誌的直接原因。

**[D-4] 兩腿共用較寬的 Bot 腿 guard** `低`　標頭自承刻意保守。

**[D-5] 績效基線待重測** `中`　v19.6 的數字，v19.7 之後未重新驗證。

**[D-6] 結算日遇休市會標錯** `低`　五支共通。

---

## 十一 移植評估

| 特性 | 值 | 影響 |
|---|---|---|
| IOG | `false`（未宣告） | 預設值本身未經驗證 |
| 資料流 | 三條（15M / **Daily** / Weekly） | Data2 是日線，與 L3/L4 的 60M 不同 |
| 單型 | Market + Stop + **Limit** | 需 Limit + OCO |
| 部位 | **雙腿 + 分批 + 綁定** | **需完整 OMS** |
| 出場控制 | 無 ExitFired，最多 8 張 | 每腿獨立訂單集合 |
| 商品屬性 | 需 `MinMove` / `PriceScale` | 需 `instruments/` |
| 變數歷史 | 需 `v_is_in_consolidation[1]` | 需 `types/stateful.py` |
| 未來函數 | 無 | — |

> **移植順位 4。** 執行層做到 L5 才第一次被迫支援：
> 多腿部位、部分口數出場、`from Entry` 綁定、`CurrentContracts` 追蹤、
> 以及「引擎停損作為獨立出場類型」。

---

## 十二 待決

| # | 項目 |
|---|---|
| 1 | `.pla` 的 SHA-256 |
| 2 | D-5：重跑 v19.9 的 MC 報告作為對帳基準 |
| 3 | D-1：箱體失效用 High/Low 是否刻意（與 L3/L4 不一致） |
| 4 | D-2：SL_Pct 錨在箱底是否刻意 |
| 5 | SP 死碼（`SP_Trigger_Pts = 0`）是否移植 |
| 6 | `Freeze_SL_On = false` 的非凍結路徑是否移植 |
| 7 | Bot 與 Mid 兩腿同時成交時的口數分配（`MaxContracts` 如何決定） |
