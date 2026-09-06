# L4 ConsolShort 規格

| | |
|---|---|
| 來源 | `_Research_L4_v14.7_SpringOnly` |
| 行為等同 | v14.6（v14.7 只改 label 字串） |
| 週期 | Data1 **15M** · Data2 **60M** · Data3 **Daily** |
| IOG | **`false`（明宣告）** |
| 方向 | 純空 |
| 出場控制 | ExitFired 短路，**保證單根單張** |
| SHA-256 | ⬜ |

> 凡註解與程式碼衝突，以程式碼為準，列於第十節。

---

## 一 做什麼

日線確認**非多頭環境**後，在 60M 箱體內等待**假突破**：價格衝出箱頂（進入誘多區），
六根 K 棒內若跌回箱頂減 0.4 ATR，即認定突破失敗，做空。

停損以箱頂為錨，跌破箱底後轉為追蹤停損。箱體向上真突破則市價認賠。

---

## 二 進場

`SellShort next bar at Market`，九個條件全成立。

| # | 條件 | 公式 | 資料 |
|---|---|---|---|
| G1 | 空手 | `MarketPosition = 0` | — |
| G2 | 冷卻期滿 | `v_BarsSinceExit >= 8` | 需 `MarketPosition[1]` |
| G3 | 60M 空方 | `Close of D2 < Average(Close,48) of D2` | Data2 |
| G4 | 非強多環境 | `v_Macro_Block = false` | Data3 |
| G5 | 誘多區有效 | `v_In_Trap_Zone = true` | Data1 |
| G6 | 跌回觸發價 | `Close < v_Box_Top − ATR × 0.4` | Data1 |
| G7 | 非假日尾盤 | `v_Holiday_Block = false` | — |
| G8 | 非深夜 | `v_Night_Block = false` | — |
| G9 | 非結算日 | `v_Settlement_Day = false` | — |

進場後立即 `v_In_Trap_Zone = false`，同一次誘多只做一次。

### 2.1 誘多區偵測

```
若 High > v_Box_Top：      v_In_Trap_Zone = true, v_Trap_Counter = 0
若 v_In_Trap_Zone：        v_Trap_Counter += 1
                           若 v_Trap_Counter > 6 → v_In_Trap_Zone = false
```

用 `High` 不是 `Close`——影線碰到箱頂就算誘多。

### 2.2 總體濾網

```
v_Macro_Block = (Close of D3 > SlowMA60  且  SlowMA60 >= SlowMA60[1])
                或 (FastMA20 > SlowMA60)
```

任一成立即封鎖做空。v14.5 曾加「日線 MA 乖離 > 1%」，A/B 測出**是本條的嚴格子集**，
100% 冗餘、零效果，已完全移除。

### 2.3 箱體

```
v_Ref_High = Highest(High, 15)[1] of Data2      ← 有 [1]
v_Ref_Low  = Lowest(Low,  15)[1] of Data2
成立：High of D2 <= Ref_High 且 Low of D2 >= Ref_Low
      且 Curr_Range / Ref_Range <= 0.7
失效：Close of D2 突破 Box_Top 或 Box_Btm       ← 用 Close
```

`Range_Shrink_Rate = 0.7` 遠寬於 L3 的 0.1。同一份程式碼形狀，鬆緊差七倍。

### 2.4 深夜封鎖

```
v_Night_Block = Night_Block_On 且 200 <= Time < 500
```

診斷依據：02:00–04:59 的 9 筆進場淨 −120,800、零 BreakExit，純雜訊。
移除後淨利 +106,000、MDD 改善 27%、前十大贏家 100% 保留。

---

## 三 持倉管理

### 3.1 P3b 引擎停損

```
若 MarketPosition >= 0：
   v_Guard_Distance = |(v_Box_Top + ATR × 2.0) − Close|
   若 SL_Pct > 0：min(v_Guard_Distance, Close × 1.50 / 100)
   SetStopLoss(v_Guard_Distance × BigPointValue)
```

`SetStopContract` 在**頂層無條件呼叫**，與 L1/L5 相同，與 L2/L3 不同（見橫向比對）。

> **[D-1]** 但 `SetStopLoss` 本身在 `if v_is_in_consolidation` 之內——非盤整期間不設定。

### 3.2 凍結

```
若 Freeze_SL_On 且 v_SL_Locked = false：
   v_Frozen_ATR       = v_Current_ATR
   v_Frozen_LockedTop = v_Locked_Top
   v_SL_Locked        = true
```

> **[D-2]** L4 凍結的是**中間變數**（ATR 與箱頂），不是最終停損價位。
> L1/L2/L3 凍結價位。當 `v_Locked_Top` 在持倉期間變動時兩者會分岔。

`v_Locked_Top` / `v_Locked_Btm` **只在空手時快照**：

```
若 MarketPosition = 0 且 v_is_in_consolidation：
   v_Locked_Top = v_Box_Top;  v_Locked_Btm = v_Box_Btm
```

### 3.3 停損價位

```
若 v_Trail_Active：
   v_Stop_Level = MinList(v_Stop_Level[1], v_Lowest_Low + 1.0 × ATR)   ← 需歷史值
否則若 Freeze_SL_On：
   v_Stop_Level = v_Frozen_LockedTop + 2.0 × v_Frozen_ATR
否則：
   v_Stop_Level = v_Locked_Top + 2.0 × ATR
   若 v_Box_Top < v_Locked_Top：v_Locked_Top = v_Box_Top

最後統一封頂：
   若 SL_Pct > 0：v_Stop_Level = MinList(v_Stop_Level, EntryPrice × (1 + 1.50/100))
```

> **`v_Stop_Level[1]` 是追蹤棘輪的全部**。歷史值取錯，整條追蹤停損失效且不報錯。
> 這是 `types/stateful.py` 存在的直接原因。

**與 L2 相反**：L4 的 SL_Pct **統一套用於全部路徑**（凍結 / 動態 / 追蹤），L2 只封頂初始停損。

### 3.4 追蹤啟動

```
若 Low < v_Lowest_Low：v_Lowest_Low = Low
若 v_Lowest_Low <= v_Locked_Btm：v_Trail_Active = true
```

跌破箱底即啟動。單一條件，無連續根數要求（L2 需連兩根 C1）。

### 3.5 BE / SP（production 關閉）

`BE_Trigger_Pts = 0`、`SP_Trigger_Pts = 0`。A/B 測試結論：

- **C（BE +60/+5）**：淨 −345K。CS_BE 25 筆 0% 勝率，砍掉前十大贏家中的 4 筆
- **D（SP +80/50%）**：CS_SP 22 筆 100% 勝率看似完美，但 CS_SL 從 45 筆/+1,019K 掉到 36 筆/+619K

> **核心教訓**：L4 的大贏家是**多階段獲利**（+60 → +30 → +200 → 追蹤在 +180 出場）。
> BE 與 SP 都攔第一次回撤，因此永遠吃不到後面那一段。

---

## 四 出場優先級

ExitFired 短路，**保證單根單張**。

| 優先 | 標籤 | 條件 | 單型 |
|---|---|---|---|
| 0a | `CS_Kill` | Manual_Kill_Switch | Market |
| 0b | `CS_RegistryEnd` | 註冊表過期 | Market |
| 0c | `CS_Holiday` | 假日尾盤 且 `Time >= 415` | Market |
| 0d | `CS_Settlement` | 結算日 且 `Time >= 1230` | Market |
| 1 | `CS_BreakExit` | 箱體失效 **且** `Close of D2 > v_Locked_Top` | Market |
| 2 | `CS_TimeExit` | 追蹤未啟動 且 `BarsSinceEntry >= 60` | Market |
| 3 | `CS_SP` / `CS_BE` / `CS_SL` | 三選一，最緊者得標 | Stop |

> **[D-3]** 優先級 1 只在**向上**突破時觸發。箱體向下失效（對空單有利）不出場，
> 但 Phase 2 整個區塊停止執行——誘多偵測與 P3b 都不再更新，停損單仍由 Phase 3 掛出。

優先級 3 的標籤路由：

```
v_Effective_Stop = v_Stop_Level
若 SP 已武裝 且 SP_Floor < v_Effective_Stop  → CS_SP
否則若 BE 已武裝 且 BE_Floor < v_Effective_Stop → CS_BE
否則 → CS_SL
```

空單「更低 = 更緊」，方向正確。

---

## 五 強制條件

| 項目 | 值 | 與其他四支比 |
|---|---|---|
| Holiday_Flat_Time | **415** | 同 L3 L5；L1=345、L2=300 |
| Settlement_Flat_Time | 1230 | 五支相同 |
| Registry_Valid_Until | 1270101 | 五支相同 |
| Holiday_Tail 陣列 | 63 筆 | **五支逐筆相同** |

假日尾盤與結算日皆**封鎖進場 + 強制平倉**。

---

## 六 狀態

| 變數 | 類別 | 重置 |
|---|---|---|
| `v_Lowest_Low` `v_Trail_Active` | per-trade | 空手 |
| `v_SL_Locked` `v_Frozen_ATR` `v_Frozen_LockedTop` | per-trade | 空手 |
| `v_Peak_Profit_Pts` `v_BE_Armed` `v_SP_Armed` `v_BE_Floor` `v_SP_Floor` `v_SL_Pct_Ceil` | per-trade | 空手 |
| **`v_Stop_Level`** | per-trade，**需歷史值 `[1]`** | 未顯式重置 |
| `v_Locked_Top` `v_Locked_Btm` | 跨交易 | 只在空手時更新 |
| `v_is_in_consolidation` `v_Box_Top` `v_Box_Btm` | per-session | 永不 |
| `v_In_Trap_Zone` `v_Trap_Counter` | per-session | 進場時 In_Trap_Zone = false |
| `v_BarsSinceExit` | 跨交易 | 持倉時歸 0 |
| `v_Episode_ID` `v_Episode_Entries` | 跨交易 | 新箱體時歸 0 |
| `v_Prev_MP` | 跨交易 | 腳本最末行 |

> **[D-4]** `v_Stop_Level` 不在空手重置清單裡。下一筆交易的第一根若 `v_Trail_Active`
> 為假則會被重算，所以實務上無害——但它是唯一沒被顯式清掉的 per-trade 變數。

---

## 七 承諾與斷言

| # | 註解承諾 | 斷言 | 驗證 |
|---|---|---|---|
| 1 | 追蹤停損只收緊 | `v_Stop_Level[t] <= v_Stop_Level[t-1]`（追蹤啟動後） | ✓ MinList 正確 |
| 2 | SL_Pct「Applied to BOTH engine and custom stop」 | 兩條路徑皆受封頂 | ✓ 且統一套用全路徑 |
| 3 | 凍結停損不隨 ATR 漂移 | 持倉期間 `v_Frozen_ATR` 不變 | ✓ |
| 4 | Iron Rule 假日前平倉 | `Time >= 415` 必平 | ✓ |
| 5 | 結算日 12:30 平倉 | `Time >= 1230` 不持倉 | ✓ |
| 6 | SetStopContract 使停損 per-contract | — | ✓ |
| 7 | 單一部位 | `MarketPosition ∈ {0, −1}` | ✓ |
| 8 | ExitFired 保證單根單張 | `len(orders) <= 1` | ✓ |
| 9 | 決策時可計算性 | 每條件只讀已存在資料 | ✓ 無未來函數 |
| 10 | 誘多區六根後失效 | `v_Trap_Counter > 6 → false` | ✓ |

**十條全數成立。L4 是五支裡承諾與程式碼最一致的一支。**

---

## 八 觸發頻率

| 期間 | 筆數 |
|---|---|
| 完整回測 | **79** |

標頭記載：v15/v15.1/v15.1_opt/v16.0 研究線全部失敗，結論是
**「L4 的 alpha 只存在於空頭/中性陷阱訊號。多頭市場零交易 = 正確行為。」**

> 移植驗收：`mc12` 模式必須產出 79 筆。多頭期間零觸發是預期，不是錯誤。

---

## 九 模式差異

| # | 項目 | mc12 | live | v2 |
|---|---|---|---|---|
| 1 | 下單時機 | 次根開盤 | 立即 | 同 live |
| 2 | 收盤前兩根 | 允許 | 禁止 | 同 live |
| 3 | BE / SP | 關閉（照抄） | 關閉 | 可重新設計 |
| 4 | 凍結中間變數而非價位 | 照抄 | 照抄 | 可改凍結價位 |
| 5 | 成本模型 | 手續費 + 稅分開算 | 同 | 同 |

---

## 十 已知落差

**[D-1] SetStopLoss 在盤整判斷內** `中`
`SetStopContract` 頂層無條件，但 `SetStopLoss` 在 `if v_is_in_consolidation` 內。
非盤整期間不設引擎停損。持倉且箱體已失效時，保護只剩 Phase 3 的自訂停損單。

**[D-2] 凍結對象與其他三支不同** `中`
L4/L5 凍結 ATR 與箱頂等中間變數，L1/L2/L3 凍結最終價位。
`v_Locked_Top` 在持倉期間若變動，兩種做法會分岔。Freeze 模式下不會變動，故實務上等價。

**[D-3] BreakExit 只認向上突破** `低`
向下失效不出場。這對空單有利，應為刻意設計，但註解未說明。

**[D-4] `v_Stop_Level` 未顯式重置** `低`
唯一沒被列入空手重置清單的 per-trade 變數。

**[D-5] 兩組績效無法調和** `高，擋住對帳基準`

| 來源 | 筆數 | 淨利 | PF | MDD |
|---|---|---|---|---|
| 2026-08-24 重測 | 79 | 877,200 | 1.4902 | −789,200 |
| 「sealed 2026-07-26」 | 79 | 894,400 | 1.54 | −525,600 |

標頭自承：「both claim 79 trades, so if no trade occurred between the two dates
the net profit must match, and 894,400 does not equal 877,200. **The provenance
of the older measurement could not be recovered.**」

**[D-6] 結算日遇休市會標錯** `低`　五支共通。

---

## 十一 移植評估

| 特性 | 值 | 影響 |
|---|---|---|
| IOG | `false` 明宣告 | bar close 評估，行為最確定 |
| 資料流 | 三條（15M / 60M / Daily） | 需 `quotes/align.py` |
| 單型 | Market + Stop | 不需 Limit |
| 部位 | 單一 | 不需多腿 |
| 出場控制 | ExitFired | 與 L2 同構 |
| 變數歷史 | **需 `v_Stop_Level[1]`** | 需 `types/stateful.py` |
| 未來函數 | 無 | — |

> **移植順位 2。** 與 L2 同構（ExitFired、單一部位），但多了三資料流與變數歷史。
> 拆完可驗證 `strategies/base.py` 的介面撐不撐得住第二支。

---

## 十二 待決

| # | 項目 |
|---|---|
| 1 | `.pla` 的 SHA-256 |
| 2 | D-5：重跑 MC 報告作為對帳基準，兩組舊數字皆不採用 |
| 3 | D-1：SetStopLoss 位置是否為 bug |
| 4 | BE / SP 死碼（`BE_Trigger_Pts = 0`、`SP_Trigger_Pts = 0`）是否移植 |
| 5 | v14.0 動態路徑（`Freeze_SL_On = false`）是否移植 |
