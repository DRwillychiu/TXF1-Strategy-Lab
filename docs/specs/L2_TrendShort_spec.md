# L2 TrendShort — 移植規格表

| | |
|---|---|
| 來源 | `Trendbearish_V54_RESEARCH` (v5.4, 2026-08-25) |
| 行為等同 | v5.3（v5.4 只改 label 字串，CHANGELOG 明載 "untouched to the character"） |
| 商品 | TXF1 台指期近月連續 |
| 週期 | **60 分鐘**，單一資料流（無 Data2） |
| 方向 | **純空**（Short only） |
| IOG | 未宣告 → `false`，**bar close 評估即可** |
| 口數 | 2（CLAUDE.md 標準） |
| SHA-256 | ⬜ 待填 |

> 本規格由程式碼推導，非由註解推導。**凡註解與程式碼衝突處，以程式碼為準，並列於第十節。**

---

## 一、這支策略在做什麼

在**週線層級確認空頭環境**後，等待價格**跌破 30 根 Donchian 下軌**且**動能向下**，進場做空。持倉後用三層停損（引擎 / 初始 / 追蹤）與三層停利（結構反轉 / 回抽 / 峰值回吐）管理，並在假日、結算日、週線翻多時強制平倉。

四個進場條件全部是**狀態**，且**沒有任何 Cooldown**，所以一旦空手且狀態仍成立，下一根就再次進場。實測最短間隔 60 分鐘（一根 K 棒）。

---

## 二、進場條件

全部條件在同一根 K 棒收盤時評估，成立則 `SellShort Next Bar at Market`。

| # | 條件 | 公式 | 讀取資料 |
|---|---|---|---|
| **F** | 週線濾網 | `FilterOK = True` | 見 §2.1 |
| **C0** | 破底確認 | `Close < DC_Lower − ATR × 0.45` | `DC_Lower = Lowest(Low[1], 30)` ✓ 有 [1] |
| **C_A** | ZLEMA 下降 | `ZLEMA < ZLEMA[1]` | 當根 Close |
| **C_B** | ZLEMA 弱於 EMA20 | `ZLEMA < EMA20` | 當根 Close |
| **G1** | 非假日尾盤 | `v_Holiday_Block = False` | 見 §5 |
| **G2** | 非結算日 | `v_Settlement_Day = False` | 見 §5 |
| **G3** | 空手 | `MarketPosition = 0` | — |

指標定義：
```
ATR_Val   = AvgTrueRange(21)                    ← 當根，收盤評估
DC_Lower  = Lowest(Low[1], 30)                  ← 排除當根
CompPrice = 2 × Close − Close[9]
ZLEMA     = XAverage(CompPrice, 20)
EMA20     = XAverage(Close, 20)
```

### 2.1 週線濾網（L2 專屬，非標準週線）

**不使用 Data2 週線流，而是在 60M 流內自行合成。**

```
觸發：Time[1] = 1245  AND  DayOfWeek(Date[1]) = 5
      → 也就是「週五 12:45 那根的下一根」，即週五 13:45 那根

動作：陣列右移 → WkCloses[1] = Close[1] → 重算 SMA
      若 WkBarCount >= 13：FilterOK = (WkCloses[1] < WkSMASum / 13)
      否則 FilterOK = False（暖機保護）
```

> ⚠ **`Close[1]` 是週五 12:45 的收盤，不是 13:45 的日盤收盤。**
> 註解宣稱 "weekly period ... to Friday 13:45 close"，與程式碼不符。
> **Python 照程式碼寫 12:45。** 見第十節 D-4。

### 2.2 Re-entry 標籤（v5.4 新增，無行為影響）

```
持倉中：      v_Last_EntryPrice = EntryPrice          （每根更新）
轉為空手時：  v_ReEntry_Armed = (PositionProfit(1) <= 0)
              v_ReEntry_Price = v_Last_EntryPrice

進場時：      若 Armed 且 Price > 0 且 Close <= Price → label "TS_ReEntry"
              否則                                    → label "TS_Entry"
              進場後 v_ReEntry_Armed = False
```

`v_Prev_MP` 於**腳本最末行**更新（CLAUDE.md Rule #8），所以上述判斷讀到的是前一根的部位。

`<= 0` 而非 `< 0`：兩口的最小虧損正好是 −4,000 淨（毛 0），用 `<=` 讓判斷在毛/淨兩種口徑下一致。

---

## 三、持倉管理

### 3.1 P3b 引擎停損（進場前設定，進場當根即生效）

```
若 MarketPosition >= 0：
   v_Guard_Distance = |(DC_Lower + ATR × 1.1) − Close|
   若 SL_Pct > 0：v_Guard_Distance = MinList(v_Guard_Distance, Close × 1.25/100)
   SetStopContract            ← 使金額為 PER-CONTRACT
   SetStopLoss(v_Guard_Distance × BigPointValue)
```

`MarketPosition >= 0` 的守衛使其在建立空單後凍結。

> ⚠ 錨點是**訊號棒的 Close**，不是 EntryPrice。與 §3.2 不同棒、不同錨。見第十節 D-1。

### 3.2 初始停損（進場當根鎖定）

```
若 MarketPosition = -1 且 BarsSinceEntry = 0 且 SL_Locked = False：
   SL_Line = DC_Lower
   SL_Trig = SL_Line + ATR × 1.1
   若 SL_Pct > 0：SL_Trig = MinList(SL_Trig, EntryPrice + EntryPrice × 1.25/100)
   SL_Locked = True

空手時：SL_Line = 0, SL_Trig = 0, SL_Locked = False
```

`MinList` 對空單取較低天花板 = 較緊，方向正確。

### 3.3 追蹤停損啟動

```
若 MarketPosition = -1：
   Accel  = (Open − Close) > ATR × 0.5  AND  Close < Open
   NLow   = Close < Lowest(Close[1], 15)
   C1_Bar = Accel AND NLow

   若 TSL_Armed = False 且 C1_Bar 且 C1_Bar[1] 且 BarsSinceEntry >= 3：
      TSL_Armed = True

空手時：全部歸 False
```

需要**連續兩根** C1_Bar，且進場滿 3 根。

### 3.4 追蹤停損追蹤

```
若 TSL_Armed：
   New_TSL    = Lowest(Close[1], 9) + ATR × 1.0
   TSL_Line   = (首次) New_TSL  否則  MinList(TSL_Line, New_TSL)   ← 只降不升
   Active_TSL = TSL_Line + ATR × 1.1

   若 TSL_Line < SL_Trig：Active_SL = Active_TSL, v_SL_Src = 1
   否則                  Active_SL = SL_Trig,    v_SL_Src = 2

若未啟動：Active_SL = SL_Trig, v_SL_Src = 2
空手：    全部歸 0, v_SL_Src = 0
```

> ⚠ **比較的是 `TSL_Line`，使用的是 `Active_TSL`，兩者差 `ATR × 1.1`。**
> `Active_SL` 因此**不是單調收緊的**。見第十節 D-2。
> ⚠ **`SL_Pct` 未套用於 `Active_TSL`。** 見第十節 D-3。

### 3.5 回抽停利閘門（TTP）

```
若 MarketPosition = -1：
   LowestClose  = (進場當根) Close  否則  MinList(LowestClose, Close)
   WaveProfit   = EntryPrice − LowestClose
   MinProfitPts = ATR × 4.0                    ← 當根 ATR，會變動
   TTP_Line     = LowestClose × (1 + 1.5/100)
   TTP_Gate     = WaveProfit >= MinProfitPts   ← 未閂鎖，每根重算
   TTP_Fire     = TTP_Gate AND (Close > TTP_Line)
```

> ⚠ `TTP_Gate` 不閂鎖。ATR 上升會使 `MinProfitPts` 變大，已達標的交易可能退回未達標。

### 3.6 峰值回吐保護（StopProfit）

```
若 MarketPosition = 0：posbleProfit_Short = 0, stopProfitPrice = 0

若 MarketPosition = -1 且 (EntryPrice − Close) >= 250：
   posbleProfit_Short = MaxList(posbleProfit_Short, EntryPrice − Close)
   stopProfitPrice    = EntryPrice − posbleProfit_Short × (1 − 55/100)
                      = EntryPrice − posbleProfit_Short × 0.45
```

因 `posbleProfit >= 250`，故 `stopProfitPrice <= EntryPrice − 112.5`，**必定在獲利區**。

---

## 四、出場條件（優先級鏈）

`ExitFired` 為短路旗標。**任一優先級成立即設 1，其後全部跳過。**

| 優先級 | 標籤 | 條件 | 單型 |
|---|---|---|---|
| **0a** | `TS_Kill` | `Manual_Kill_Switch = True` | Next Bar at Market |
| **0b** | `TS_RegistryEnd` | `v_Registry_Expired = True` | Next Bar at Market |
| **0c** | `TS_Holiday` | `v_Holiday_Block` 且 `Time >= 300` | Next Bar at Market |
| **0d** | `TS_Settlement` | `v_Settlement_Day` 且 `Time >= 1230` | Next Bar at Market |
| **1** | `TS_WeeklyExit` | 週五 且 `Time = 1245` 且 `WkBarCount >= 13` 且 `Close > SMA13` | Next Bar at Market |
| **2** | `TS_StructureTP` | `Close > Highest(Close[1], 30)` | Next Bar at Market |
| **3** | `TS_TTP` | `TTP_Fire = True` | Next Bar at Market |
| **4** | `TS_StopProfit` | `stopProfitPrice > 0` | Next Bar at `stopProfitPrice` **Stop** |
| **5** | `TS_TSL_D` / `TS_InitSL_D` | `IsDay` 且 `Active_SL > 0` | Next Bar at `Active_SL` **Stop** |
| **6** | `TS_TSL_N` / `TS_InitSL_N` | `IsNight` 且 `Active_SL > 0` 且 `Close > Active_SL` | Next Bar at Market |

優先級 5、6 依 `v_SL_Src` 選標籤：`1 → TSL`、`2 → InitSL`。

> ⚠ **優先級 4 一旦成立，5 與 6 永不執行。** 見第十節 D-5。

### 4.1 時段判定（影響優先級 5 / 6）

```
IsDay   = (Time >= 845) AND (Time <= 1245)
IsNight = NOT IsDay
```

60M 收盤戳記：日盤 `09:45 / 10:45 / 11:45 / 12:45 / 13:45`，夜盤 `16:00 … 05:00`。

> ⚠ **`13:45` 那根落在 `IsNight`。** 下限 845 永不生效（無此戳記）。
> 後果：日盤收盤那根走優先級 6（收盤確認 + 次根市價），而次根開盤在 **15:00**。見第十節 D-6。

---

## 五、強制條件（優先於全部邏輯）

### 5.1 假日尾盤（Iron Rule）

```
Holiday_Tail[1..63]  靜態註冊表，民國年格式（如 1260212）
                     語意 = 最後交易日 + 1 曆日 = 該場休市前最後夜盤 00:00-05:00 的日期戳

v_Holiday_Block = False
若 Time <= 500：逐一比對 Date 是否等於 Holiday_Tail[hidx]，命中則 True
```

尾盤生效時：**封鎖進場**；`Time >= 300` 起強制 `BuyToCover`（03:00 觸發 → 03:00 成交，04:00 重試，05:00 前必平）。

### 5.2 註冊表過期

```
若 Date > Registry_Valid_Until (1270101)：
   v_Registry_Expired = True
   v_Holiday_Block    = True        ← 同時封鎖進場
```

到期前 30 天在圖表上顯示紅色警告文字。

### 5.3 結算日

```
v_Settlement_Day = (DayOfWeek = 3) AND (DayOfMonth >= 15) AND (DayOfMonth <= 21)
```

**整天封鎖進場**（不只 12:30 後）；`Time >= 1230` 強制平倉。

> ⚠ 夜盤 00:00–05:00 戳記為隔日，故結算日夜盤後半段不受封鎖。
> ⚠ 若第三個週三適逢休市，結算日會移動，此靜態規則會標錯。

---

## 六、狀態清單

| 變數 | 類別 | 寫入位置 | 重置時機 |
|---|---|---|---|
| `SL_Line` `SL_Trig` `SL_Locked` | per-trade | §3.2 | `MarketPosition ≠ -1` |
| `Accel` `NLow` `C1_Bar` `TSL_Armed` | per-trade | §3.3 | `MarketPosition ≠ -1` |
| `New_TSL` `TSL_Line` `Active_TSL` `Active_SL` `v_SL_Src` | per-trade | §3.4 | `MarketPosition ≠ -1` |
| `LowestClose` `WaveProfit` `MinProfitPts` `TTP_Line` `TTP_Gate` `TTP_Fire` | per-trade | §3.5 | `MarketPosition ≠ -1` |
| `posbleProfit_Short` `stopProfitPrice` | per-trade | §3.6 | **僅 `MarketPosition = 0`** |
| `WkCloses[1..13]` `WkBarCount` `WkSMASum` `FilterOK` | per-session | §2.1 | **永不重置** |
| `v_Prev_MP` | 跨交易 | 腳本最末行 | 永不 |
| `v_Last_EntryPrice` `v_ReEntry_Armed` `v_ReEntry_Price` | 跨交易 | §2.2 | Armed 於進場後清除 |
| `v_Holiday_Block` `v_Registry_Expired` `v_Settlement_Day` | per-bar | §5 | 每根重算 |
| `Holiday_Tail[1..63]` | 常數 | `CurrentBar = 1` | 永不 |
| `Registry_Warn_ID` `hidx` `LoopIdx` `ExitFired` | 暫存 | 各處 | — |

**Python 移植要求**：per-trade 與 per-session 在型別上分開；每筆交易結束時斷言 per-trade 已回初始值。

---

## 七、承諾清單 → 可執行斷言

| # | 註解承諾 | 斷言 | 驗證 |
|---|---|---|---|
| 1 | P3b「same anchor as Section 8 SL」 | 引擎停損距離 == 自訂停損距離 | **✕ 不成立**（D-1） |
| 2 | SL_Pct「Applied to BOTH engine and custom stop」 | 兩條停損路徑皆受 1.25% 上限 | **✕ 部分**（D-3） |
| 3 | TSL 為 trailing | `Active_SL` 對空單只降不升 | **✕ 不成立**（D-2） |
| 4 | v5.4「Zero behaviour change」 | 僅 label 字串不同 | ✓ |
| 5 | Iron Rule「flat before 05:00」 | 假日尾盤 `Time >= 300` 必平倉 | ✓ |
| 6 | Settlement「flat at 12:30」 | 結算日 `Time >= 1230` 不持倉 | ✓ |
| 7 | StopProfit「give back 55% of peak」 | 出場價 <= `Entry − 0.45 × peak` | ✓ |
| 8 | 單一部位 | `MarketPosition ∈ {0, -1}` | ✓ |
| 9 | 決策時可計算性 | 每條件只讀下單當下已存在的資料 | ✓ 無未來函數 |
| 10 | TSL_Line 單向 | `TSL_Line[t] <= TSL_Line[t-1]` | ✓ |
| 11 | SetStopContract 必在 SetStopLoss 前 | — | ✓ |
| 12 | 週線暖機保護 | `WkBarCount < 13` 時 `FilterOK = False` | ✓ |

**12 條中 3 條不成立。** L1 的 13 條不變量**不可直接套用於 L2**——每支需自建清單。

---

## 八、預期觸發頻率（事前登記）

| 期間 | 交易數 | 來源 |
|---|---|---|
| 完整回測 | 77–78 筆 | 標頭績效區（兩組數字不一致，見 D-8） |
| 2025-06-03 之後 | **0 筆** | 標頭 STATUS |
| 停擺長度 | **443 天（14.6 個月）** | 標頭 STATUS |
| 2026 YTD | 0 筆 | 標頭 STATUS |

**推定原因**（標頭註明為 INFERRED，未實測）：`FilterOK` 要求週收盤低於 SMA13，而指數自 21,000 走到 47,000。空方策略在多頭 regime 空轉屬預期行為。

> **移植驗收標準**：Python `mc12` 模式跑 2025-06-03 之後的資料，**也必須零觸發**。若有觸發，即為移植錯誤。
> 這是五支裡最乾淨的驗收案例——零是無歧義的。

---

## 九、模式差異點

| # | 項目 | `mc12` | `live` | `v2` |
|---|---|---|---|---|
| 1 | 下單時機 | 訊號棒收盤 → 次根開盤成交 | 訊號棒收盤 → 立即下單 | 同 live |
| 2 | 收盤前兩根 | 允許進場 | **禁止進場** | 同 live |
| 3 | 13:45 歸類 | 夜盤（照抄） | 照抄 | 待裁決 |
| 4 | 引擎/自訂停損錨點 | 不一致（照抄） | 照抄 | 可統一 |
| 5 | Active_TSL 的 SL_Pct | 無上限（照抄） | 照抄 | 可加上限 |
| 6 | 優先級 4 遮蔽 5/6 | 照抄 | 照抄 | 待裁決 |
| 7 | 週線取 12:45 | 照抄 | 照抄 | 待裁決 |
| 8 | 成本模型 | 手續費 12/邊 + 稅 0.00002×契約金額 | 同 | 同 |

**每加一項差異，`mc12` 與 `live` 的結果落差就更大，且必須能逐項解釋。**

---

## 十、已知落差（程式碼 vs 註解 vs 意圖）

### D-1　引擎停損與自訂停損錨點不同　`嚴重度：中`
```
引擎（訊號棒）  距離 = |(DC_Lower_sig + ATR_sig × 1.1) − Close_sig|,  上限 Close_sig × 1.25%
自訂（進場棒）  價位 =   DC_Lower_ent + ATR_ent × 1.1,                上限 Entry + Entry × 1.25%
```
不同 K 棒 → `DC_Lower` 與 `ATR` 值不同；不同錨點 → `Close_sig` vs `EntryPrice`。
註解明載理由（EntryPrice 在成交前不存在），屬**已知且刻意**。
**處置**：`mc12` 照抄；不變量 #1 對 L2 標記為 N/A。

### D-2　追蹤停損可能放鬆　`嚴重度：高`
比較 `TSL_Line`、使用 `Active_TSL`，兩者差 `ATR × 1.1`。

**機制一（啟動瞬間跳鬆）**：當 `DC_Lower < TSL_Line < DC_Lower + ATR×1.1` 時條件成立，但 `Active_TSL > SL_Trig`。
```
例：DC_Lower=20000, ATR=100 → SL_Trig=20110
    Lowest(Close[1],9)=19950 → TSL_Line=20050 < 20110 ✓ 進入分支
    Active_TSL = 20050 + 110 = 20160 > 20110   ← 停損放寬 50 點
```

**機制二（ATR 擴張）**：`Active_TSL = TSL_Line + ATR_當根 × 1.1`。`TSL_Line` 只降，但 `ATR_當根` 會升，故 `Active_SL` 可持續上移。

**處置**：`mc12` 照抄。**待你裁決是 bug 或設計**；若判為 bug，修正進 `v2`。

### D-3　SL_Pct 未套用於追蹤路徑　`嚴重度：中`
`SL_Pct` 封頂 `SL_Trig`（§3.2）與 `v_Guard_Distance`（§3.1），但**未封頂 `Active_TSL`**。
標頭宣稱 "Applied to BOTH engine stop and custom stop"——追蹤路徑不在其中。
SL_Pct 的設計目的正是防 ATR 飆升，而追蹤路徑恰好沒被保護。
**處置**：`mc12` 照抄；`v2` 可加上限。

### D-4　週線收盤取 12:45 而非 13:45　`嚴重度：中（移植必踩）`
程式碼在週五 13:45 那根執行 `WkCloses[1] = Close[1]`，取得的是 **12:45 收盤**。
註解宣稱 "Friday 13:45 close"。
偏移一致故 SMA 內部自洽，但**照註解寫 Python 會錯**。
**處置**：Python 照程式碼寫 12:45，規格表已註明。

### D-5　優先級 4 遮蔽優先級 5、6　`嚴重度：高`
`stopProfitPrice > 0` 後 `ExitFired = 1`，自訂停損單**永不掛出**。
此後保護僅剩 P3b 引擎停損（凍結於進場前）。
標頭統計 45 筆虧損出場中有 4 筆為 "engine Stop Loss"，應即此路徑。
**處置**：`mc12` 照抄；待裁決。

### D-6　13:45 歸類為夜盤　`嚴重度：中`
`IsDay` 上限 1245，故日盤最後一根走優先級 6（收盤確認 + 次根市價）。
次根為 16:00 戳記那根，**開盤在 15:00**，中間 1 小時 15 分無自訂停損。
**處置**：逐字照抄 `IsDay = (Time >= 845) And (Time <= 1245)`。

### D-7　TTP_Gate 未閂鎖　`嚴重度：低`
`MinProfitPts = ATR_當根 × 4.0`，ATR 上升可使已達標交易退回未達標。
**處置**：照抄。

### D-8　標頭兩組績效互相矛盾　`嚴重度：高（擋住對帳基準）`
| 來源 | 交易數 | 淨利 | PF | MDD |
|---|---|---|---|---|
| CHANGELOG 5.4 anchor（live v5.3） | 77 | 2,670,000 | 2.7456 | −484,400 |
| PERFORMANCE 區塊（2026/07/26） | 78 | 2,882,400 | 2.88 | −484,400 |

標頭自承：來源 Excel 不在 repo，無法從版控重現。
**處置**：對帳前必須重跑 MC 報告並存檔（帶時間戳 + SHA-256），不採用標頭數字。

### D-9　MDD −14.99% 的「矛盾」已解　`已結案`
標頭列為 UNRESOLVED：`−484,400 / 1,000,000 = −48.4%`，與印出的 −14.99% 不符。

反推：`484,400 ÷ 0.1499 = 3,231,488`。初始 1M + 淨利 2,882,400 → 期末 3,882,400，峰值 3,231,488 落在區間內。

**結論：−14.99% 使用滾動峰值當分母，與本專案採用的 `max_drawdown` 定義一致。三個數字皆無誤。**

### D-10　結算日遇休市時規則失效　`嚴重度：低`
`DayOfWeek = 3 AND DayOfMonth ∈ [15,21]` 為靜態判定。若第三個週三適逢休市，實際結算日會移動。
**處置**：照抄；列為已知風險。

---

## 十一、移植順序建議

L2 是五支裡技術上最單純的一支：

| 特性 | L2 | 影響 |
|---|---|---|
| IOG | `false` | bar close 評估即可，不需 tick 重放 |
| 資料流 | 單一 60M | **無 `of Data2`**，無跨週期對齊問題 |
| 未來函數 | 無 | 所有回看皆帶 `[1]` |
| 部位 | 單一、純空 | 狀態機最簡單 |
| 驗收 | 2025-06-03 後應零觸發 | 無歧義的驗收標準 |

**唯一的複雜點是週線濾網的自行合成**（§2.1），而那正好是 Python 最容易寫對、MC 最容易寫錯的部分。

---

## 十二、待填 / 待裁決

| # | 項目 | 類型 |
|---|---|---|
| 1 | 五支 `.pla` 的 SHA-256 | 待填 |
| 2 | D-2 追蹤停損放鬆：bug 或設計？ | 待裁決 |
| 3 | D-5 優先級 4 遮蔽：bug 或設計？ | 待裁決 |
| 4 | 重跑 MC 報告作為對帳基準（D-8） | 待執行 |
| 5 | `live` 模式的觸發/下單時機 | 待拍板 |
| 6 | 「收盤前兩根禁止進場」是否套用於 60M 週期 | 待拍板 |
