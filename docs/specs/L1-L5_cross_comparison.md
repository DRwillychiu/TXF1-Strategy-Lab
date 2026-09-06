# 五支策略橫向比對

> 產出日期 2026-09-06　·　來源為五份 PowerLanguage 研究版原始碼
> 本文只放**並排才看得出來的東西**。單支細節見各自規格表。

---

## 一、資料流與執行模型

| 策略 | Data1 | Data2 | Data3 | IOG | 方向 | Flat 時間 | 出場控制 |
|---|---|---|---|---|---|---|---|
| **L1** TrendLong | **45M** | Daily | Weekly | **true** | 多 | 345 | **無** ExitFired |
| **L2** TrendShort | **60M** | — | — | false（未宣告） | 空 | 300 | ExitFired 短路 |
| **L3** ConsolLong | 15M | **60M** | Daily | false（未宣告） | 多 | 415 | else-if + 獨立 Kill |
| **L4** ConsolShort | 15M | **60M** | Daily | false（**明宣告**） | 空 | 415 | ExitFired 短路 |
| **L5** BreakoutLong | 15M | **Daily** | Weekly | false（未宣告） | 多 | 415 | else-if，**雙 leg** |

**報價層必須提供五種週期**：15M、45M、60M、Daily、Weekly。

**L2 是唯一單資料流的策略**，其週線濾網在 60M 流內自行合成，不用 Data3。

**L5 的 Data2 是 Daily，不是 60M** —— 它與 L3/L4 的箱體程式碼形狀幾乎相同，但箱體建立在**日線**上（`Lookback_Bars = 4` = 四日箱），而 L3/L4 是 60M 箱（16 / 15 根）。**形狀相同、語意完全不同。**

---

## 二、「五支共用」的真實範圍

原規劃假設 1c 假日偵測 / 1d 結算偵測 / 強制平倉區為五支共用。逐份比對結果：

| 元件 | 是否共用 | 說明 |
|---|---|---|
| `Holiday_Tail[1..63]` 陣列值 | ✅ **完全相同** | 63 筆民國年日期，五份逐筆一致 |
| 初始化守衛 | ❌ | **L1 用 `Init_Done` 旗標，其餘四支用 `CurrentBar = 1`** |
| 假日偵測區塊 | ❌ | **L1 包在 `BarStatus(1) = 2` 內，其餘四支在頂層無守衛** |
| `Time <= 500` 掃描迴圈 | ✅ | 邏輯一致 |
| `Registry_Valid_Until` | ✅ | 五支皆 1270101 |
| 註冊表過期 fail-safe | ✅ | 邏輯一致 |
| 結算日偵測 | ✅ **完全相同** | `DayOfWeek=3 and DayOfMonth in [15,21]` |
| `Settlement_Flat_Time` | ✅ | 五支皆 1230 |
| **`Holiday_Flat_Time`** | ❌ | **345 / 300 / 415 / 415 / 415** —— 隨 K 棒網格而異 |
| **強制平倉區塊結構** | ❌ | 四種不同寫法（見第三節） |

### 結論

> **共用的是「資料」與「偵測」，不共用的是「時間常數」與「執行結構」。**

`tradecal/` 可以抽出：Holiday_Tail 註冊表、假日偵測函數、結算日偵測函數、註冊表過期判定。

**不可抽出**：`Holiday_Flat_Time`（每支不同，屬 config）、強制平倉的下單區塊（四種結構）。

**若照原規劃把整個區塊抽成共用模組，會改變其中至少三支的行為。**

---

## 三、出場下單模型 —— 五種不同

這是執行層設計的核心約束。

### L1：無互斥旗標，一根 K 棒最多三張單

```
Section 3（持倉時必定執行）
    Sell (TL_SL / TL_SP / TL_TP / TL_TSL / TL_SL_Gap / TL_SP_Gap)

Section 4
    if v_Registry_Expired      → Sell(TL_RegistryEnd)
    else if v_Holiday_Block    → Sell(TL_Holiday)
    else if v_Settlement_Day   → Sell(TL_Settlement)

    if Manual_Kill_Switch      → Sell(TL_Kill)      ← 獨立 if，不在鏈上
```

標頭自承：

> L1 can emit **two full-size market orders on one bar** today: Manual_Kill_Switch sits outside the else-if chain and last. Adding a mutual-exclusion flag would change behaviour and break the anchor. **That is fix J-3.**

實際上最多三張：Section 3 一張 + Section 4 鏈上一張 + Kill 一張。**這是已知未修的缺陷，且刻意保留以維持 anchor。**

### L2：ExitFired 短路，嚴格一張

七個優先級依序檢查，任一成立即 `ExitFired = 1`，其後全部跳過。**保證單根單張。**

### L3：bracket 結構，常態同時兩張

```
Sell ("CL_TP") next bar at v_Work_Target Limit;      ← 停利限價
Sell ("CL_SL") next bar at v_Work_SL     Stop;      ← 停損停價
```

**TP 與 SL 同時掛出**，加上 Section 6 的安全出場（else-if 鏈 + 獨立 Kill），一根最多四張。

**執行層必須支援 OCO 語意**：兩張單其中一張成交，另一張要撤銷。

### L4：ExitFired 短路，嚴格一張

與 L2 相同機制。`CS_SP > CS_BE > CS_SL` 三選一，用 `else if` 互斥。

### L5：雙 leg + 分批出場 + leg 綁定，最複雜

```
Buy ("BL_Entry_Bot") next bar at v_Box_Btm  Stop;
Buy ("BL_Entry_Mid") next bar at v_Mid_Line Stop;    ← 兩張進場單可同時存在

Sell ("BL_TP_Bot") v_ScaleOut_Size contracts from Entry ("BL_Entry_Bot") ...
Sell ("BL_SL_Bot") CurrentContracts contracts from Entry ("BL_Entry_Bot") ...
```

- **兩條進場腿**（Bot / Mid），可各自成交
- **`from Entry (...)` 綁定**：出場單綁定到特定進場腿，全案只有 L5 使用（28 處）
- **分批出場**：`v_ScaleOut_Size = Round(MaxContracts × 0.4)`
- **階段判定**：`CurrentContracts = MaxContracts` → Stage 1；`<` → Stage 2/3
- 每階段每腿各掛一張，加安全出場，一根可達 6 張以上

L5 標頭說明了為什麼它沒有 re-entry 標籤：

> All 28 exit orders bind `from Entry(...)`. Renaming an entry **orphans every exit bound to it and the position loses all stops.**

### 對執行層的要求

| 能力 | 需要它的策略 |
|---|---|
| 市價單 | 全部 |
| 停價單（Stop） | 全部 |
| 限價單（Limit） | **L3、L5** |
| 引擎停損 SetStopLoss + SetStopContract | 全部 |
| 單根多張單並存 | L1、L3、L5 |
| OCO 撤銷語意 | L3、L5 |
| **部分口數出場** | **L5** |
| **進場腿綁定** | **L5** |
| **`CurrentContracts` / `MaxContracts` 追蹤** | **L5** |
| 逐 tick 評估 | **L1** |

> **L5 與 L1 是兩個不同方向的最高難度。**
> L1 難在時間粒度（IOG），L5 難在部位模型（多腿 + 分批 + 綁定）。
> **L2 與 L4 是唯二單純的**（ExitFired 保證單根單張、單一部位）。

---

## 四、看起來一樣、其實不一樣的地方

這些是移植最容易踩的坑——程式碼形狀幾乎相同，語意不同。

### 4.1 箱體失效判定

```
L3:  if (Close of Data2 > v_Box_Top) or (Close of Data2 < v_Box_Btm)  → 失效
L4:  if (Close of Data2 > v_Box_Top) or (Close of Data2 < v_Box_Btm)  → 失效
L5:  if (High  of Data2 > v_Box_Top) or (Low   of Data2 < v_Box_Btm)  → 失效
```

**L5 用 High/Low（碰到就破），L3/L4 用 Close（收盤才破）。**
L5 的箱體因此脆弱得多——任何影線都會終止箱體。

### 4.2 SL_Pct 上限的參考價

```
L1:  Close × SL_Pct / 100        （引擎）／ Entry_P × SL_Pct / 100（自訂）
L2:  Close × SL_Pct / 100        （引擎）／ EntryPrice × ...（自訂）
L3:  Close × SL_Pct / 100        （引擎）／ EntryPrice × ...（自訂）
L4:  Close × SL_Pct / 100        （引擎）／ EntryPrice × ...（自訂）
L5:  v_Box_Btm × SL_Pct / 100    （引擎）  ← 唯一不用 Close 的
     EntryPrice × (1 − SL_Pct/100)（自訂）
```

**L5 的引擎停損上限錨在箱底，其餘四支錨在收盤價。** 未見註解說明理由。

### 4.3 SetStopContract 的擺放位置

```
L1:  SetStopContract;  在 if MP <= 0 之外，無條件
L2:  if MarketPosition >= 0 then begin SetStopContract; SetStopLoss(...) end   ← 在條件內
L3:  SetStopContract;  在 if v_is_in_consolidation 之內、if v_Box_Qualified 之外
L4:  SetStopContract;  頂層，無條件
L5:  SetStopContract;  頂層，無條件，註解寫「must be outside conditional」
```

**三種擺法。** L5 的註解明白說必須放在條件外，而 **L2 放在條件內、L3 放在 `v_is_in_consolidation` 內**——非盤整期間完全不呼叫。

若 L5 的註解正確，L2 與 L3 的擺放是錯的。**待裁決。**

### 4.4 SL_Pct 收斂值

| | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| SL_Pct | 0.50 | 1.25 | 0.55 | **1.50** | 1.00 |

L4 標頭說明：`L4 SHORT wider than LONG strategies (L1=0.5%, L3=0.55%, L5=1.0%)`。
**兩支空頭（L2 1.25、L4 1.50）都比三支多頭寬。**

### 4.5 停損凍結的凍結對象不同

```
L1:  凍結「價位」  v_Frozen_SL = MaxList(三條腿的價位)
L2:  凍結「價位」  SL_Trig = DC_Lower + ATR×1.1，加 SL_Pct 上限
L3:  凍結「價位」  v_Frozen_SL = MaxList(Box_Btm − ATR緩衝, Pct底)
L4:  凍結「ATR 與 Locked_Top」，每根用凍結值重算價位
L5:  凍結「ATR 與 ATR_Buffer」，每根用凍結值重算價位
```

**L1/L2/L3 凍結最終價位，L4/L5 凍結中間變數。** 效果在多數情況相同，但當 `v_Locked_Top`（L4）或 `v_Box_Btm`（L5）在持倉期間變動時就會分岔。

---

## 五、Re-entry 機制的四種定義

四支有 re-entry 標籤，L5 只有日誌。**四個定義互不相同，不能共用實作。**

| 策略 | 定義 | 進場單型 | 狀態 |
|---|---|---|---|
| **L1** | 前倉為多 + 剛轉空手 + `v_Frozen_Gap > 0`；解除條件 `v_TrendRatio <= 0` 或週線失效；新訊號覆蓋 | **Stop** at `v_ReEntry_Price` | **`ReEntry_On = 0`，整條腿關閉** |
| **L2** | 前一筆虧損 且 本次 `Close <= 前次進場價` | Market | 標籤啟用，**無解除條件** |
| **L3** | 同一 consolidation episode + 前一筆停損虧損 + `v_Box_Btm <= 前次進場價`，且**排除市價出場** | Stop at `v_Box_Btm` | 標籤啟用，episode 變更時解除 |
| **L4** | 同一 episode 內第 2 次以上進場（**純結構，不看價格也不看盈虧**） | Market | 標籤啟用 |
| **L5** | 同左（episode 內第 N 次），但**只寫 Print 日誌不改標籤** | Stop | 僅觀測 |

L3 標頭解釋了為何不能沿用 L2 的定義：

> L2 的定義在 L3 上會選中 360 筆中的 134 筆（37%）。L3 以 `v_Box_Btm` 掛 Buy Stop，而箱底是**移動的結構位**，所以「進場價不高於前次」多半只代表「箱子沒往上移」，根本不是 re-entry。

**這是五支之間最重要的一條「不可共用」證據。**

---

## 六、L1 的三個獨有特徵

L1 是唯一 IOG = true 的策略，衍生出其他四支完全沒有的東西：

**1. `Variables: IntraBarPersist`**
```
IntraBarPersist posbleProfit_Long, stopProfitPrice_L, v_Trail_High
```
沒有這個宣告，這三個變數會在每個 tick 重置回 bar-open 值。**Python 必須實作等價的 tick 間持久化語意。**

**2. `BarStatus(1) = 2` 守衛**
指標、週線濾網、假日/結算偵測、進場（Crosses Over）、P3 凍結停損、MDD 視覺化全部包在守衛內，只在收盤執行。**未包守衛的部分逐 tick 執行**——P7 停利追蹤、P4 移動停損、出場下單。

**3. `Crosses Over`**
```
Cond_Breakout = (Close Crosses Over Breakout_Level)
```
唯一使用穿越運算子的策略，其餘四支都是純不等式比較。穿越需要「前一根的狀態」，在 IOG 下語意特別微妙——標頭註明「evaluated once per bar either way」。

---

## 七、移植順序（依實測複雜度）

| 順位 | 策略 | 理由 |
|---|---|---|
| **1** | **L2** | 單資料流、無 Data2/Data3、ExitFired 單張單、單一部位、無未來函數。**唯一能靠「零觸發」無歧義驗收的** |
| **2** | **L4** | 三資料流但 ExitFired 單張單、單一部位、IOG 明宣告 false |
| **3** | **L3** | 三資料流 + bracket（TP limit + SL stop 同時）→ 執行層要先支援 OCO |
| **4** | **L5** | 雙 leg + 分批出場 + `from Entry` 綁定 + `CurrentContracts` 追蹤 → 部位模型最複雜 |
| **5** | **L1** | IOG = true + IntraBarPersist + BarStatus 守衛 + Crosses Over + 三張單並存 |

**執行層的能力必須按這個順序疊加**，L2 通過時執行層只需最小集合，到 L5 才需要多腿部位，到 L1 才需要 tick 生命週期。

> 但 `engine/context.py` 的資料模型仍須從第一天就以 tick 為原生、bar close 為特例。
> 否則做到 L1 時要回頭重構，前四支已通過的對帳全部要重跑。

---

## 八、五支共通的已知風險

以下缺陷同時存在於全部或多數策略，Python 版會一併繼承。

| # | 風險 | 影響範圍 |
|---|---|---|
| 1 | **Holiday_Tail 為靜態陣列，僅覆蓋到 1270101** | 五支。過期後 fail-safe 會封鎖所有進場 |
| 2 | **註冊表中 `*` 標記的日期為重建值，未對 TAIFEX PDF 驗證** | 五支。勞動節每年、2025 新增國定假日 |
| 3 | **結算日靜態判定，遇休市會標錯** | 五支 |
| 4 | **臨時休市（颱風假）只能靠 `Manual_Kill_Switch`** | 五支 |
| 5 | **P3b 引擎停損錨在訊號棒 Close，自訂停損錨在 EntryPrice** | 五支。兩者必然不同 |
| 6 | **績效數字來源 Excel 不在版控，無法從 repo 重現** | L1、L2、L4 標頭明載 |

第 6 項最直接擋住對帳：**五支都需要重跑 MC 報告並存檔（帶時間戳 + SHA-256）**，標頭數字不可作為基準。

---

## 九、各支標頭自承的未解事項

| 策略 | 自承內容 |
|---|---|
| **L1** | J-3：Manual_Kill_Switch 在鏈外，一根可發兩張市價單。**未修，刻意保留** |
| **L1** | 策略名稱寫 60M 但實際圖表是 45M，「name kept for live continuity」 |
| **L2** | 標頭兩組績效互相矛盾（77/2.67M vs 78/2.88M），來源 Excel 不在 repo |
| **L2** | 自 2025-06-03 起 **443 天零交易**，Rule #13 嚴重違反 |
| **L3** | re-entry 次數無法事前登記，改登記為區間 `20 <= CL_ReEntry <= 115` |
| **L4** | 兩組績效無法調和（877,200 vs 894,400，同為 79 筆），舊測量出處已無法回溯 |
| **L4** | v15/v16 曾以 live 名稱上架過，「do not repeat it」 |
| **L5** | SL_Pct = 1.0 使引擎 SetStopLoss 可在**沒有任何 Sell 語句觸發**的情況下平倉；171 筆中有 1 筆如此 |

**L5 那一條特別重要**：出場側標籤永遠標不到引擎停損路徑。**Python 版必須把引擎停損也記成一種出場類型**，否則對帳時會出現「有平倉但找不到對應出場單」。

---

## 十、待裁決清單

| # | 事項 | 影響 |
|---|---|---|
| 1 | `SetStopContract` 三種擺法，L2/L3 是否為 bug | 引擎停損是否 per-contract |
| 2 | L5 的 SL_Pct 錨在 `v_Box_Btm` 而非 `Close`，是否刻意 | 引擎停損寬度 |
| 3 | L1 的 J-3（一根多張市價單）在 Python 是否照抄 | `mc12` 模式必須照抄；`v2` 可修 |
| 4 | L1 的 re-entry 模組 `ReEntry_On = 0`，是否移植這段死碼 | 工作量 |
| 5 | L5 的 SP 模組 `SP_Trigger_Pts = 0`（永久關閉），是否移植 | 工作量 |
| 6 | L4 的 BE/SP 模組（`BE_Trigger_Pts = 0`、`SP_Trigger_Pts = 0`）是否移植 | 工作量 |
| 7 | 五支重跑 MC 報告作為對帳基準 | 擋住全部對帳 |
| 8 | 五支的 SHA-256 | 防基準漂移 |

第 4、5、6 項合計是相當可觀的死碼量。**若不移植，`mc12` 模式的對帳仍成立**（因為開關為 0 時那些路徑本來就不執行），但 `v2` 模式將失去這些研究資產。
