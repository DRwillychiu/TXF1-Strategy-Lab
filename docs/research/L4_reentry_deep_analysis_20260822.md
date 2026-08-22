---
建立日期: 2026-08-22
對象: `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort.pla`（v14.6，719 行）
狀態: **深度讀碼完成，尚未寫任何程式碼**
前置: `docs/policies/REENTRY_DESIGN_SPEC_20260822.md`
---

# L4 二次進場 深度探討

## 0. 一頁摘要

| # | 發現 | 影響 |
|---|---|---|
| **1** | **L4 的進場條件幾乎全部是「狀態」**，只有一個 latch 是事件衍生 | **不需要 L1 那種「事件→狀態」翻譯**，可直接重驗原條件 |
| **2** | **停損被打到時，trap zone 會自己重新武裝** | L4 **現在就會自然二次進場**，只是進場價不對 |
| **3** | `Cooldown_Bars = 8`（2 小時）是既有的節流閥 | 需裁決：二次進場繞過還是遵守 |
| **4** | **箱型能不能撐過停損，是這支的生死題** | 幾何複查未決，需實測 |
| **5** | 地基比 L1 好：已有 `ExitFired`、Frozen SL、SL_Pct | Step 1 比 L1 輕 |
| **6** | **L4 不需要 `v_TrendRatio`** | 少一個參數、少一次 sweep |

---

## 1. L4 的進場條件拆解

```powerlanguage
if v_is_in_consolidation and v_Box_Top > v_Box_Btm then begin
    if High > v_Box_Top then begin              { 假突破偵測 }
        v_In_Trap_Zone = true;
        v_Trap_Counter = 0;
    end;
    if v_In_Trap_Zone then begin                { 6 根後衰減 }
        v_Trap_Counter = v_Trap_Counter + 1;
        if v_Trap_Counter > Time_Limit_Bars then v_In_Trap_Zone = false;
    end;

    v_Trigger_Price = v_Box_Top - (v_Current_ATR * i_Buffer_ATR_Mult);

    if MarketPosition   = 0              and
       v_BarsSinceExit >= Cooldown_Bars  and     { 冷卻 8 根 = 2 小時 }
       v_Trend_Dir      = -1             and
       v_Macro_Block    = false          and
       v_In_Trap_Zone   = true           and
       Close            < v_Trigger_Price and
       v_Holiday_Block  = false          and
       v_Night_Block    = false          and
       v_Settlement_Day = false          then begin
        SellShort ("CS_Entry") next bar at Market;
        v_In_Trap_Zone = false;                  { latch 被消耗 }
    end;
end;
```

### 1.1 逐條型態判定

| # | 條件 | 型態 | 資料流 | 二次進場能否直接重驗 |
|---|---|---|---|---|
| A | `v_is_in_consolidation` + `Box_Top > Box_Btm` | **狀態** | Data2 60M | ✅ 直接 |
| B | `v_BarsSinceExit >= 8` | **狀態**（冷卻） | Data1 15M | ⚠️ 需裁決（E1） |
| C | `v_Trend_Dir = -1` | **狀態** | Data2 60M | ✅ 直接 |
| D | `v_Macro_Block = false` | **狀態** | Data3 Daily | ✅ 直接 |
| E | `v_In_Trap_Zone = true` | **latch，進場即清空** | Data1 15M | ⚠️ 需裁決（E2） |
| F | `Close < v_Trigger_Price` | **狀態** | Data1 + ATR | ✅ 直接 |
| G-I | Holiday / Night / Settlement | **狀態** | — | ✅ 直接 |

**⭐ 九個條件裡有七個可以原封不動重驗。**

**這是 L4 與 L1 最大的差別。** L1 的主進場是 `Close Crosses Over Breakout_Level`
——一個穿越事件，下一根就 false，所以必須翻譯成 `v_TrendRatio` 這個持續狀態版本。
**L4 沒有這個問題**，它的條件本來就都是狀態。

**推論：L4 不需要 `v_TrendRatio`，少一個參數、少一次 sweep。**

---

## 2. ⭐ 發現 2：L4 現在就會自然二次進場

trap 偵測每根都跑：

```powerlanguage
if High > v_Box_Top then begin
    v_In_Trap_Zone = true;
    v_Trap_Counter = 0;
end;
```

而停損掛在 `v_Frozen_LockedTop + ATR_Stop_Mult * v_Frozen_ATR` = **箱頂上方 2 個 ATR**。

**所以「被停損」這件事本身，必然伴隨 `High > v_Box_Top` → trap zone 自動重新武裝。**

冷卻 8 根過後，只要價格跌回 `Box_Top − 0.4 × ATR` 之下、其餘條件仍成立，
**L4 就會再進場一次**。

### 2.1 但它進的是「市價」，不是「原進場價」

| | L4 現況 | 規格要求 |
|---|---|---|
| 進場時機 | 條件重新對齊的那一根 | 價格**回到原進場價** |
| 進場價 | **市價**（下一根開盤） | **原成交價**（停損單） |
| 停損 | **重新凍結**（新的 ATR、新的 LockedTop） | **繼承**（取較緊者） |

**這就是 L4 缺的三件事**：價位錨定、停損繼承、可開關可量測。

**與 L3/L5 同型，但 L4 多了一個冷卻閥。**

---

## 3. ⚠ 發現 4：箱型能不能撐過停損 —— 這支的生死題

**這是 L1 幾何陷阱的 L4 版本。**

```
箱頂          v_Box_Top
停損          v_Box_Top + 2 x ATR          <- 停損在結構外側 2 個 ATR
進場          < v_Box_Top - 0.4 x ATR
```

**箱型失效條件**（`L4:494-497`）：

```powerlanguage
if (Close of Data2 > v_Box_Top) or (Close of Data2 < v_Box_Btm) then
    v_is_in_consolidation = false;
```

**破的是 Data2（60M）的收盤，不是 Data1 的高點。**

所以有兩種可能：

| 情境 | 60M 收盤 | 箱型 | 二次進場 |
|---|---|---|---|
| **假突破後拉回**（15M 插針到停損，60M 收在箱內） | 仍在箱內 | **存活** | ✅ 可行 |
| **真突破**（60M 收在箱頂之上） | 破箱 | **失效** | ❌ 條件 A 不成立 |

**⭐ 這正是 L4 的設計意圖**：它做的就是「假突破陷阱」（S_Spring）。
**理論上「假突破 → 停損 → 箱型仍在」正是它最想抓的情境。**

**但這是理論，不是實測。** 停損在箱頂外 2 個 ATR，那是一個相當深的穿刺，
60M 收盤跟著跑掉的機率不低。

### 3.1 這一題不能用推理解決，要用量的

**做法**：把結構閘門做成可開關的 input。跑 ON / OFF 兩格，
**觸發筆數的差額就是「箱型撐過停損」的次數**。

比 L1 幸運的是：L1 的幾何錯誤會讓機制**零觸發**且無聲；
L4 的結構閘門即使全擋，其餘條件仍可能放行，所以不會靜默失敗。

---

## 4. 地基盤點：比 L1 好

| 元件 | L1 改造前 | **L4 現況** |
|---|---|---|
| 「剛出場」偵測 | ❌ 無 | ⚠️ 有等效物：`MarketPosition = 0 and MarketPosition[1] <> 0`（`v_BarsSinceExit` 用） |
| `ExitFired` 互斥鏈 | ❌ 無 | ✅ **完整**（8 個出場全在鏈內） |
| Frozen SL | ✅ 凍結**價格** | ✅ 凍結 **ATR + LockedTop** |
| SL_Pct 上限 | ✅ 0.5 | ✅ **1.50**（已 sweep） |
| Priority-0 出場 | ⚠️ Kill 在鏈外 | ✅ **全在鏈內，順序正確** |

**⚠ 唯一要補的**：`v_Prev_MP`。L4 用的是 `MarketPosition[1]` 這個 bar offset，
**違反 CLAUDE.md PowerLanguage 規範第 8 條**（應用 `v_Prev_MP`，腳本最末行更新）。
語意驗證器會抓到。Step 1 一併補齊，但**必須保持 `v_BarsSinceExit` 行為完全不變**。

---

## 5. 方向鏡像清單（L4 = SHORT）

| 元素 | L1（多） | **L4（空）** |
|---|---|---|
| 武裝 | `v_Prev_MP = 1 and MP = 0` | `v_Prev_MP = -1 and MP = 0` |
| 價格閘門 | `Close <= v_ReEntry_Price` | **`Close >= v_ReEntry_Price`** |
| 下單 | `Buy ... stop` | **`SellShort ... next bar at v_ReEntry_Price stop`** |
| 持倉判斷 | `MP = 1` | `MP = -1` |
| 停損方向 | 停損在**下方**，取較緊用 `MaxList` | 停損在**上方**，取較緊用 **`MinList`** |
| SL_Pct | Floor = Entry x (1 − pct) | **Ceiling = Entry x (1 + pct)** |

**⚠ 停損繼承在 L4 要用 `MinList`。** L1 是 `MaxList`（多單取較高價 = 較緊），
L4 做空要取**較低價**才是較緊。方向寫反不會報錯，只會讓停損變鬆——正是 Plan C
的失敗機制。

---

## 6. 待裁決事項

| # | 事項 | 選項 | 建議 |
|---|---|---|---|
| **E1** | 二次進場是否遵守 `Cooldown_Bars = 8` | (a) 遵守 (b) 繞過 (c) 做成獨立的 `ReEntry_Cooldown` input | **(c)**，預設 = 8（等同遵守），可 sweep |
| **E2** | 二次進場是否仍要求 `v_In_Trap_Zone = true` | (a) 要求 (b) 不要求（武裝本身已蘊含出場，而出場必伴隨穿箱頂） | **(a) 做成開關預設 ON**，用失效測試量它值多少 |
| **E3** | 再進場價 = 原成交價 or `v_Trigger_Price` | (a) 原成交價（依規格定義） (b) `v_Trigger_Price`（結構價位） | **(a)**，規格定義如此；(b) 列為 P2 對照組 |
| **E4** | 是否需要 `v_TrendRatio` 閘門 | (a) 需要 (b) 不需要 | **(b)**，見 §1.1。L4 的條件本來就是狀態，直接重驗即可 |

---

## 7. 建議的 Step 1 內容（待 E1-E4 定案後動工）

**落點**：`strategies/research/L4_ConsolidationShort/L4_v15/`

**新增 inputs（數值 0/1，不可用 TrueFalse）**：

```
ReEntry_On              ( 0 )    { 錨點出貨值 }
ReEntry_Close_Gate      ( 1 )    { Close >= v_ReEntry_Price }
ReEntry_Structure_Gate  ( 1 )    { v_is_in_consolidation -- §3 的生死題 }
ReEntry_Trap_Gate       ( 1 )    { v_In_Trap_Zone -- E2 }
ReEntry_Cooldown        ( 8 )    { E1，預設等同現行 }
```

**新增 variables**：`v_Prev_MP` / `v_ReEntry_Armed` / `v_ReEntry_Price` /
`v_IsReEntry` / `v_Last_EntryPrice` / `v_Frozen_Stop_Orig` ＋ 5 個開關鏡射

**錨點驗收**：`ReEntry_On = 0` 時，與現行 live L4 **逐筆完全相同**。
**⚠ 特別檢查 `v_BarsSinceExit` 行為未變**（因為要補 `v_Prev_MP`）。

---

## 8. 誠實聲明

1. **本文全部來自靜態讀碼，零回測、零 MC12 編譯。**
2. §3 的「箱型能否撐過停損」**是推論，不是實測**。這是本支最大的未知數。
3. `Cooldown_Bars = 8` 的來源未查明（docs/ 未見 sweep 紀錄），
   與 `Entry_Multiplier = 2` 在 L1 的情形相同。
4. BE / SP 兩層在 PRODUCTION 皆為 0（停用），且檔內明文「DO NOT enable without
   redesign」。**二次進場不得順手啟用它們。**
5. 本文由 Claude 產出，**未經第二方審查**。
