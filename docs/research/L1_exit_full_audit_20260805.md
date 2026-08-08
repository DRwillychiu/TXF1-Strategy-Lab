---
title: L1_TrendLong 出場邏輯完整逐路徑稽核
strategy: L1_TrendLong (V3.1)
created: 2026-08-05
author: Claude Code (subagent, read-only audit)
source_of_truth: strategies/live/L1_TrendLong/L1_TrendLong.pla (706 lines, full read)
method: 靜態原始碼閱讀（static .pla reading）
verification_status: 未經 MC12 編譯驗證、未經回測驗證、未經 MC9 runtime log 驗證
scope: 出場邏輯（含影響出場的進場/指標/狀態變數）
excluded: .bak_* 檔案未讀；未執行任何編譯或回測
motivation: 使用者實盤 MC9 / 真實資金 / 固定 2 口，回報「急拉時移動停利跟不上」
---

# L1_TrendLong 出場邏輯完整稽核

## 0. 稽核基礎與免責

- 目標檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L1_TrendLong\L1_TrendLong.pla`
- 全檔 706 行**已完整讀完**（1-706）。
- 本報告**所有行號皆為實際讀到**，未推估。
- 本報告**全部為靜態閱讀結論**。沒有跑編譯、沒有跑回測、沒有看 MC9 runtime log。
  任何涉及 MC 引擎執行期仲裁行為的判斷一律標 `[不確定]`。
- 數值範例（如「約 120 點」）皆為**依現行 input 與假設指數位階推導的示意值**，
  非回測產生，標示為「示意估算，未驗證」。

### 已採用的既有物理驗證事實（來自主對話，本次複核一致）

| 事實 | 行號 | 本次複核 |
|---|---|---|
| `[IntrabarOrderGeneration = true]` | `:220` | 一致 |
| `maTrail = Average(Close, Length20)` 包在 `if BarStatus(1) = 2` 內 | `:424` `:426` | 一致 |
| 出場區塊外層只有 `if MP > 0 then begin`，無 BarStatus 守衛 | `:551` | 一致 |
| `if BarStatus(1) = 2 and v_SL_Locked = False` 只守初始停損凍結 | `:561` | 一致 |
| P7 StopProfit 無 BarStatus 守衛，用 `Close - Entry_P` | `:578-583` | 一致 |
| `v_Trail_High = MaxList(...)` 單向棘輪 | `:588` | 一致 |
| `Final_Exit_Price = MaxList(...)` 三腿取最高 | `:590-591` | 一致 |
| Gap 分支 `BarStatus(1) = 2 and Close < Final_Exit_Price` 改發 Market | `:596-600` | 一致 |
| Kill 為 else-if 鏈外的獨立 `if` | `:646` | 一致 |
| 進場端沒有 `Manual_Kill_Switch` gate | `:538-542` | 一致 |

### 全檔訂單語句清點（grep 物理核對）

以 `next bar at` 為 pattern 掃描全檔，命中 **11 筆**：`Buy` 1 筆（`:543`）+ `Sell` 10 筆。
另以 `\bSell\b` 單獨掃描，同樣得 **10 筆**：`:598 :600 :603 :606 :608 :610 :637 :640 :643 :647`。
另掃 `SetProfitTarget` / `SetExitOnClose` / `SetPercentTrailing` / `SetDollarTrailing` /
`BuyToCover` / `SellShort` / `ExitLong`：**全部 0 命中**。
唯一的引擎層級出場是 `SetStopLoss`（`:527` / `:531`，if/else 兩個呼叫點）。

> **自我核對聲明：全檔共 10 個 `Sell` 語句，下方 A 表列了 10 個，無遺漏。**
> 另加 1 個引擎層級出場（`SetStopLoss`）獨立列為 A-11。

---

## A. 出場路徑總表

出場價變數的定義位置先行說明（供表中「更新頻率」欄佐證）：

- `v_Frozen_SL` → `:568`，寫入條件 `:561`（`BarStatus(1) = 2 and v_SL_Locked = False`）→ **一筆交易只寫一次**
- `Exit_Price_SL = v_Frozen_SL` → `:572`（每 tick 賦值，但來源已凍結）
- `stopProfitPrice_L` → `:581-582`，條件 `:578`（**無 BarStatus 守衛**）→ **每 tick**
- `v_Trail_High` → `:588`（每 tick 執行，但輸入 `maTrail` 只在 `:424-426` 每根 K 更新）→ **實質每根 45M K**
- `Final_Exit_Price` → `:590-591`（每 tick 重算）

| # | 行號 | 標籤 | 觸發條件（可讀邏輯式） | 單型 | 所屬優先層 | 值的更新頻率 | 互斥保護 |
|---|---|---|---|---|---|---|---|
| A-1 | `:598` | `TL_SP_Gap` | `MP>0` AND `BarStatus(1)=2` AND `Close < Final_Exit_Price` AND `Final_Exit_Price >= Entry_P` | **Market** | P0-5 原邏輯（Gap 分支） | 觸發判定**每根 45M K 一次**；`Final_Exit_Price` 內含每 tick 的 SP 腿 | 與 A-2 為 if/else 互斥；與 A-3~A-6 為 if/else 互斥（`:596`/`:601`）。**與 A-7~A-10 無互斥** |
| A-2 | `:600` | `TL_SL_Gap` | 同上，但 `Final_Exit_Price < Entry_P` | **Market** | P0-5 原邏輯（Gap 分支） | 同上 | 同上 |
| A-3 | `:603` | `TL_SL` | `MP>0` AND NOT Gap 分支 AND `\|Final_Exit_Price - Exit_Price_SL\| < 0.001` | **Stop** | P0-5 原邏輯 | **進場後第一根 K 收盤凍結，之後靜態**（`:561` `:568`）；掛單**每 tick 重發** | else-if 鏈內互斥（`:602-610`）。**無 ExitFired 旗標** |
| A-4 | `:606` | `TL_SP` | NOT Gap AND NOT A-3 AND `stopProfitPrice_L > 0` AND `\|Final_Exit_Price - stopProfitPrice_L\| < 0.001` | **Stop** | P0-5 原邏輯 | **每 tick**（`:578-583` 無 BarStatus 守衛，單向上調）；掛單每 tick 重發 | 同上 |
| A-5 | `:608` | `TL_TP` | NOT Gap AND NOT A-3/A-4 AND `Exit_Price_Trail >= Entry_P` | **Stop** | P0-5 原邏輯 | **每根 45M K**（`maTrail` 受 `:424` 守衛，單向上調）；掛單每 tick 重發 | 同上 |
| A-6 | `:610` | `TL_TSL` | NOT Gap AND NOT A-3/A-4 AND `Exit_Price_Trail < Entry_P`（else 兜底） | **Stop** | P0-5 原邏輯 | 同 A-5 | 同上 |
| A-7 | `:637` | `TL_RegistryEnd` | `MP>0` AND `v_Registry_Expired` | **Market** | **P0-2** Registry | `v_Registry_Expired` 每根 45M K 更新（`:460` `:475-480`） | Section 4 else-if 鏈內與 A-8/A-9 互斥（`:636-644`）。**與 A-10 不互斥**，**與 A-1~A-6 完全不互斥** |
| A-8 | `:640` | `TL_Holiday` | `MP>0` AND NOT A-7 AND `v_Holiday_Block` AND `Time >= Holiday_Flat_Time(345)` | **Market** | **P0-3** Holiday | `v_Holiday_Block` 每根 45M K 更新（`:460-468`）；`Time` 每根 K | 同 A-7 |
| A-9 | `:643` | `TL_Settlement` | `MP>0` AND NOT A-7/A-8 AND `v_Settlement_Day` AND `Time >= Settlement_Flat_Time(1230)` | **Market** | **P0-4** Settlement | `v_Settlement_Day` **每 tick** 更新（`:490-492` 無守衛，但實質為日期，一根 K 內不變） | 同 A-7 |
| A-10 | `:647` | `TL_Kill` | `MP>0` AND `Manual_Kill_Switch = True` | **Market** | **P0-1** Kill（但**寫在鏈外、鏈後**） | input，靜態（使用者手動改才變，下一 tick 生效） | **獨立 `if`（`:646`），與 A-7~A-9 皆不互斥，與 A-1~A-6 亦不互斥** |
| A-11 | `:527` `:531` | （MC 引擎，無標籤；報表顯示為 `Stop Loss`） | `MP <= 0` 時設定金額；部位建立後停止呼叫 | **引擎 Stop**（`SetStopLoss`，`SetStopContract` 基礎 `:524`） | P3b Immediate Stop Guard | **進場前最後一次 flat 的 bar 收盤凍結**（見 B-3 說明） | 與所有自訂單並存，無互斥 |

**全檔無任何 `ExitFired` / `v_Exit_*` 類互斥旗標。**（Variables 宣告區 `:262-309` 已逐行讀完，不存在此類變數。）

---

## B. 三腿選擇函數方向稽核（附錄 C 陷阱逐點檢查）

程式碼中（排除註解）的 `MaxList` / `MinList` 呼叫共 **8 處**，全部逐一判定如下。

### B-1 `:527` 外層 `MinList(Current_ATR * SL_Multiplier, MinList(...))`

- 運算元：**距離**（點數，皆為正）
- 多單語義：距離取小 = 停損靠近進場價 = **取緊**
- 設計意圖（`:518-521` 註解）：「MinList of DISTANCES is the TIGHTER leg = exactly what P3 freezes below」→ 明示要取緊
- **判定：一致 ✅**

### B-2 `:528` 內層 `MinList(Daily_ATR * Daily_Cap_Multiplier, Close * SL_Pct / 100)`

- 運算元：**距離**
- 多單語義：**取緊**
- 設計意圖（`:186`「P3b mirror updated: MinList adds Pct distance when > 0」）→ 取緊
- **判定：一致 ✅**
- 補充：此分支只在 `SL_Pct > 0` 時執行（`:526`）。若 `SL_Pct = 0` 走 `:531` else 分支，
  **不把 0 當哨兵值丟進 MinList**——這是正確的，因為 `MinList(距離, 0) = 0` 會產生零距離停損＝進場即出場。
  作者用獨立分支迴避了這個陷阱。**這正是附錄 C 陷阱的鏡像面，此處處理正確。**

### B-3 `:531` `MinList(Current_ATR * SL_Multiplier, Daily_ATR * Daily_Cap_Multiplier)`（SL_Pct = 0 分支）

- 運算元：**距離** → **取緊**；意圖同 B-1
- **判定：一致 ✅**

### B-4 `:568` 外層 `MaxList(Exit_Price_ATR, MaxList(...))`

- 運算元：**價格**（`Entry_P - 距離`）
- 多單語義：價格取高 = 停損靠近進場價 = **取緊**
- 設計意圖（`:559`「MaxList picks the TIGHTEST (highest price for long)」、`:195`「MaxList = TIGHTEST leg」）→ 取緊
- **判定：一致 ✅**

### B-5 `:568` 內層 `MaxList(Exit_Price_Cap, Exit_Price_Pct)`

- 運算元：**價格**；多單語義 **取緊**；意圖同 B-4
- **判定：一致 ✅**
- 哨兵安全性：`SL_Pct = 0` 時 `Exit_Price_Pct = 0`（`:567`）。價格空間下 `MaxList(正數, 0) = 正數`，
  0 必定落敗 → 停用語義正確。**與 B-2 的距離空間處理方向相反但兩者皆正確**，
  這正是附錄 C 所指「同名函數兩處語義相反」的情境，L1 現行版本**兩處都對**。

### B-6 `:588` `MaxList(v_Trail_High, maTrail - TrailOffset)`

- 運算元：**價格 vs 價格**
- 多單語義：取高 = **取緊**（單向棘輪，只上不下）
- 設計意圖（`:585-586`「uni-directional ratchet. v_Trail_High only moves up」、`:163-165`）→ 取緊
- **判定：一致 ✅**
- **但需標註的設計後果（非方向錯誤）**：MA 本質會回落，加上棘輪後，
  這條腿從「呼吸式均線移動停損」變成「均線歷史高水位停損」。
  在震盪型趨勢中，均線回落 N 點時停損位比「活的 MA55」高 N 點，
  出場會比 MA55 原始設計更早。這與 memory rule `feedback_trend_let_profits_run`
  「出場端保護三次陣亡」屬同一類風險。
  **[推論，非實測]** 需回測 diff 才能量化。

### B-7 `:590` 外層 `MaxList(Exit_Price_Trail, MaxList(...))`

- 運算元：**價格**；多單語義 **取緊**（三腿取最高＝最靠近現價的地板）
- 設計意圖（`:207`「Exit : single stop at Max(P4 trail, P3 frozen, P7 lock)」）→ 取緊
- **判定：一致 ✅**

### B-8 `:591` 內層 `MaxList(Exit_Price_SL, stopProfitPrice_L)`

- 運算元：**價格**；多單語義 **取緊**；意圖同 B-7
- **判定：一致 ✅**
- 哨兵安全性：`stopProfitPrice_L` 未武裝時 = 0（`:618` flat 時重設），
  價格空間下 0 落敗 → 未武裝的 SP 腿不影響選擇。**正確。**

### B 節結論

**8 處全部方向正確，未發現「P3b vs P3 反向取腿」型的真 bug。**
2026-07-22 V2.9 修的那個 bug 在現行 V3.1 檔案中確實已修復（`:527` `:531` 皆為 `MinList`）。

### B 節額外發現：兩處**鏡像保真度落差**（不是方向錯，但值得裁示）

`:199-200` 與 `:518-519` 宣稱 P3b 是 P3 的「true mirror」。逐項比對後，這個宣稱**只成立到近似程度**：

**落差 1：Pct 腿的參考價不同**
- P3b `:529`：`Close * SL_Pct / 100`
- P3  `:565`：`Entry_P - (Entry_P * SL_Pct / 100)` → 距離 = `Entry_P * SL_Pct / 100`
- `Close`（訊號 K 收盤價）≠ `Entry_P`（次根 K 開盤成交價）。
- 技術上無法避免（發 `SetStopLoss` 時尚未成交，`EntryPrice` 不存在），
  但**這違反 CLAUDE.md Rule #12「距離公式必須與該策略的 Frozen SL 使用相同變數和乘數」的字面要求**。
  見 F 節。

**落差 2：ATR 快照差一根 K（影響較大）**
逐行推導執行順序（`:424` 指標 → `:513` MP → `:524-533` SetStop → `:535` 進場 → `:551` 出場）：

| 時點 | `Current_ATR` 內容 | 事件 |
|---|---|---|
| Bar N 收盤（MP=0） | 含 Bar N | `:527/:531` SetStopLoss 用 **Bar N 的 ATR**；`:543` 送出 Buy |
| Bar N+1 開盤 | 未更新 | 成交，MP=1 |
| Bar N+1 盤中每 tick | 仍是 Bar N | `:561` 因 `BarStatus(1)<>2` **不執行** → `v_Frozen_SL` 仍為 0 |
| Bar N+1 收盤 | 更新為含 Bar N+1 | `:561-569` 觸發，`v_Frozen_SL` 用 **Bar N+1 的 ATR** 凍結 |

→ **P3b 用訊號 K 的 ATR，P3 用成交後第一根 K 的 ATR。兩者不是同一個快照。**
突破進場的 Bar N+1 通常波動放大，ATR(20) 上升 → **P3 凍結的停損比 P3b 的引擎停損更寬**。

**後果（依賴一個 `[不確定]`）**：若 MC9 的 `SetStopLoss` 在停止呼叫後仍持續生效
（`:90-92` 註解如此宣稱），則引擎停損可能在**整筆交易期間都比自訂 Frozen SL 更緊**，
亦即 `:93-95` 所稱「SetStopLoss becomes dormant backup」在多數交易中**恰好相反**——
真正在保護的是 P3b，而使用者以為在保護的 P3 從未生效。
`[不確定]` 見 G 節第 1 項。

---

## C. 各腿時間行為分析（含「急拉 / 急殺」兩情境）

> 「急拉」定義：45M 圖上 1-3 根 K 內指數上漲數百點。
> 「急殺」定義：同尺度下跌。

### C-1 P3 初始停損（三層，`:561-572`）

- **值多久變一次**：一筆交易**只變一次**。`:561` 的 `BarStatus(1)=2 and v_SL_Locked = False`
  在成交後第一根 45M K 收盤時執行一次，寫入 `v_SL_Locked = True`（`:569`），此後永不再算。
  `:572` 每 tick 把凍結值賦給 `Exit_Price_SL`，但來源不變。
- **掛單多久重發**：`:603` 在 `if MP > 0`（`:551`，無 BarStatus 守衛）內 → **每 tick 重發**，但價格恆定。
- **急拉**：完全不動。價格漲得越多，這條腿離現價越遠，越早退出「三腿取最高」的競爭。
  在急拉中它幾乎立刻變成無效腿。
- **急殺**：這是唯一會真正被打到的初始防線。單型是 Stop，急殺穿價時以 Stop 成交，
  **滑價全額承受**（CLAUDE.md 技術規格：1,000 NTD/口/邊 = 單邊 5 點）。
  若急殺發生在收盤瞬間或跨盤，見 C-4 Gap 分支。

### C-2 P7 StopProfit 鎖利地板（`:578-583`）

- **值多久變一次**：**每 tick**。`:578` 無 BarStatus 守衛，IOG=true 下 `Close` = 當前 tick 價。
  `posbleProfit_Long` 單向上調（`:579-580`），`stopProfitPrice_L = Entry_P + peak * 0.45`（`:581-582`）。
- **掛單多久重發**：`:606` 每 tick 重發，價格隨 tick 上移。
- **急拉**：**這條腿在更新頻率上完全跟得上**（每 tick 追峰）。
  但地板公式是**比例式**：`Entry + peak x 45%`，容許回吐 = `peak x 55%`。
  峰值越大，絕對回吐點數越大，且**沒有任何上限**。
  示意估算（未驗證）：進場 24000、急拉到 25000（peak = 1000），地板 = 24450，
  允許回吐 550 點 = 110,000 NTD/口 x 2 口 = **220,000 NTD**。
- **急殺**：若已武裝，地板是最緊的一腿，Stop 單每 tick 掛在 `Entry + 0.45 x peak`。
  急殺穿價時以 Stop 成交。若急殺快到在同一根 K 內從峰值直落穿地板，
  Stop 單本身有效（IOG 下已掛出），但**成交價取決於 MC 對「同 tick 內生成的單能否在同 tick 成交」的處理**，見 G 節第 2 項 `[不確定]`。
- **關鍵限制**：`:578` 的門檻 `(Close - Entry_P) >= 200` 是**硬門檻**。獲利未達 200 點前，
  這條腿的值恆為 0（`:618` flat 時重設），完全不參與保護。見 E-2。
- **回測 vs 實盤落差**：`:174` 註明回測需 Bar Magnifier（1 min）。
  1 分鐘 magnifier 下「tick」只有 1M OHLC 四點，而實盤是真 tick。
  **回測的 peak 追蹤精度低於實盤 → P7 的回測績效不能直接外推到實盤。** `[推論，未驗證]`

### C-3 P4 均線移動停利（`:585-589`）

- **值多久變一次**：**每根 45M K 一次**。`:588` 雖每 tick 執行，
  但輸入 `maTrail` 只在 `:424` 的 `BarStatus(1)=2` 內更新（`:426`），
  盤中 `MaxList(v_Trail_High, 同一個舊值)` = 不變。
- **掛單多久重發**：`:608` / `:610` 每 tick 重發，價格每 45 分鐘才可能上移一次。
- **急拉（★ 使用者原始提問的直接答案）**：
  1. `Length20 = 55`（變數名叫 Length20 但值是 55，見 `:234`；header `:201` 稱 MA55）。
     45M x 55 根 ≈ 2,475 分鐘。TXF1 日盤 5h + 夜盤 14h = 19h/日 ≈ 25.3 根/日
     → **MA55 ≈ 2.2 個交易日的均線**。
  2. 再減固定 `TrailOffset = 50` 點（`:234`）。
  3. 一根 45M K 才更新一次。
  → 三重遲滯疊加。急拉時 MA55 完全跟不上現價，這條腿**在急拉中結構性失效**。
  **這不是 bug，是設計必然。**
- **急殺**：棘輪值停在歷史高水位不下降（`:588`）。若急殺前 MA55 曾拉高，
  這條腿反而可能比 P3 凍結停損更緊，先被打到。急殺穿價以 Stop 成交。
- **與 P7 的競爭關係（重要）**：`:590-591` 三腿取最高。
  - 慢速趨勢（MA 有時間爬上來）→ **P4 綁定**。
  - 急拉（peak 快速累積，MA 落後）→ `Entry + 0.45 x peak` 幾乎必然高於 `maTrail - 50` → **P7 綁定**。
  → **急拉行情中，真正在保護部位的是 P7，不是 P4。**

### C-4 Gap 分支（`:596-600`）

- **值多久變一次**：觸發判定 **每根 45M K 一次**（`:596` 的 `BarStatus(1)=2`）。
  `Final_Exit_Price` 本身每 tick 重算，但這個分支只在收盤 tick 被檢查。
- **掛單多久重發**：條件成立時每根 K 收盤發一次 Market 單。
- **設計用途**（`:168-170`）：收盤指標重算可能把停損價推到 `Close` 之上
  （例如 `maTrail` 跳升使 `maTrail - 50 > Close`），此時 Stop 單掛在現價之上是無效狀態，改發市價單。
- **急拉**：幾乎不會觸發（`Close` 遠高於三腿）。
- **急殺**：**這是急殺情境下最關鍵、也最危險的一條**。
  - 若價格在一根 K 內直接摜穿三腿，且 Stop 單因故未成交（跳空、流動性斷層），
    收盤時 `Close < Final_Exit_Price` 成立 → 改發 `next bar at Market`。
  - `next bar at Market` 在 45M 圖上 = **下一根 K 的開盤價**。盤中約幾秒後成交；
    但若這根 K 是 13:45 日盤收盤 → 下一根是 15:00（**間隔 75 分鐘**），
    或 05:00 夜盤收盤 → 下一根是 08:45（**間隔 3 小時 45 分**）。
  - **此期間完全無保護，且市價單無法取消。**
  - 補充：進入 Gap 分支時走的是 `:596` 的 if，`:601` 的 else **不執行**
    → **這一輪不發 Stop 單**。原本的 Stop 單在該次評估中未被重新宣告。
    `[不確定]`：MC9 對「上一 tick 宣告、本 tick 未宣告」的 `next bar` 單是否自動撤銷，見 G 節第 3 項。

### C-5 Priority-0 四件套（`:634-650`）

| 腿 | 條件更新頻率 | 掛單頻率 | 急拉 | 急殺 |
|---|---|---|---|---|
| `TL_RegistryEnd` `:637` | `v_Registry_Expired` 每根 K（`:460` `:477`） | 條件成立則每 tick 發 Market | 無視價格，照樣平倉 | 無視價格，照樣平倉 |
| `TL_Holiday` `:640` | `v_Holiday_Block` 每根 K（`:460-468`） | 同上 | 同上 | 同上 |
| `TL_Settlement` `:643` | `v_Settlement_Day` 每 tick（`:490`，但實質日期不變） | 同上 | 同上 | 同上 |
| `TL_Kill` `:647` | input，靜態 | 同上 | 同上 | 同上 |

- **四者全部是 `next bar at Market`**，因此**在急拉與急殺中行為相同**：
  無視價格、無視損益、在下一根 K 開盤成交。
- **急拉時的具體傷害**：正在急拉的部位若碰上結算日 12:30 或假日 03:45，
  會在下一根 45M K 開盤被市價平掉，**不論當時獲利多少、不論趨勢是否完好**。
  這是憲法明文接受的 trade-off（憲法 §1.3 理由 4）。
- **急殺時的具體傷害**：同樣是下一根 K 開盤市價，急殺中的開盤價可能比觸發時差數百點。
- **重試預算不對稱**：
  - Settlement：12:30 觸發 → 12:45 / 13:00 / 13:15 三次成交機會（憲法第三章）。
  - Holiday：`Holiday_Flat_Time = 345`（`:244`）+ `Time <= 500` 守衛（`:463`）
    → 夜盤 45M 網格上只剩 03:45 收盤 → 04:30 開盤成交、04:30 收盤 → 05:00 開盤成交，
    **只有 2 次機會**，比 Settlement 少 1 次。`:626-627` 的註解寫「fill at 03:45」，
    但 `next bar at Market` 實際是在**下一根 K 開盤**成交，註解描述與 MC 語義不符（**文件與程式碼不一致，無 P&L 影響**）。

---

## D. 同根 K 多單並存分析

### D-1 單次腳本評估最多同時宣告幾張單？

| 來源 | 結構 | 最多幾張 |
|---|---|---|
| Section 3（`:551-611`） | `:596` if / `:601` else，內部再 else-if 鏈 | **恰好 1 張**（必發，只要 `MP > 0`） |
| Section 4 鏈（`:636-644`） | `if / else if / else if` | 0 或 1 張 |
| Section 4 Kill（`:646-648`） | **獨立 `if`** | 0 或 1 張 |

→ **單次評估最多同時宣告 3 張出場單。**

### D-2 Gap 分支 Market 單 與 Section 3 Stop 單 會不會同時發出？

**不會。** `:596` 與 `:601` 是嚴格 if/else，同一次評估只走一邊。
但要注意**跨評估**的殘留：前一 tick 發的 Stop 單，在 Gap 分支觸發的那次評估中未被重新宣告
（見 C-4 末段的 `[不確定]`）。

### D-3 Priority-0 Market 單 與 Section 3 Stop 單 會不會同時存在？

**會，而且是常態。**
- `:551` 的 `if MP > 0` 與 `:634` 的 `if MP > 0` 是**兩個獨立區塊**，中間沒有任何互斥旗標。
- 只要有部位，Section 3 **一定**發一張單（`:602-610` 的 else-if 鏈有 else 兜底 `:610`）。
- 因此在結算日 12:30 之後、假日 03:45 之後、Registry 過期、或 Kill 開啟時，
  **`TL_*` Stop 單與 `TL_Settlement/Holiday/RegistryEnd/Kill` Market 單同時掛在市場上，且各自都是全倉出場單。**

### D-4 `TL_Kill` 與 Priority-0 鏈的其他成員會不會同時發出？

**會。** `:646` 是鏈外的獨立 `if`。若 `Manual_Kill_Switch = True` 且同時 `v_Registry_Expired = True`，
`:637` 與 `:647` **兩張全倉 Market 單同時送出**。

### D-5 引擎停損（`SetStopLoss`）與自訂 Stop 單

**必然並存**（這是 P3b 的設計意圖，`:93-95`）。進場當根同時存在：
引擎 Stop（約 `Entry - MinList(距離)`）+ 自訂 Stop（`TL_TSL`，掛在 `maTrail - 50`，見 E-1）。

### D-6 `[不確定]` — MC 引擎仲裁行為

以下**無法從程式碼判定**，必須用 MC9 實測或 MC12 回測 trade list 驗證：

1. **多張全倉出場單在同一根 K 都被觸發時，MC9 會不會超額出場？**
   PowerLanguage 的 `Sell` 是「平多」指令，理論上不能開空倉，所以最壞情況應為
   「第一張成交後其餘變成無效單」。但 EasyLanguage 家族有「多個未指定 `total` 的出場單
   可能各自平掉完整部位」的已知警告。**實盤 2 口，若真有超額出場會變成反向 2 口空單。**
   → **這是本報告認為最需要優先做物理驗證的一項。**
2. Market 單與 Stop 單在同一根 K 都可成交時，**成交順序與最終記錄在哪個標籤下**。
3. 「上一 tick 宣告、本 tick 未宣告」的 `next bar` 單是否自動撤銷（影響 C-4 的空窗判定）。
4. IOG=true 下，同一 tick 內生成的 `next bar at ... Stop` 單能否在**同一 tick** 成交，
   還是最快要等下一 tick。這決定急殺時 P7 地板的實際滑價。

---

## E. 保護真空區系統性掃描

以下共檢查 **10 種狀態組合**。每一項標明「是真空 / 非真空 / 曝險窗」。

### E-1 【真空 — 自訂層完全缺席】成交瞬間 → 第一根 K 收盤（最長 45 分鐘）

- `v_Frozen_SL` 在 flat 時被重設為 0（`:616`）。
- `:561` 需要 `BarStatus(1) = 2`，成交發生在 K 棒開盤 → **整根 K 的盤中，`v_Frozen_SL` 恆為 0**。
- `stopProfitPrice_L` 亦為 0（`:618` 重設，且獲利未達 200）。
- 因此 `:590-591` → `Final_Exit_Price = MaxList(maTrail - 50, MaxList(0, 0)) = maTrail - 50`。
- 標籤路由（`:602` 不成立、`:604` 不成立、`:607` 通常不成立）→ 落到 `:610` **`TL_TSL`**。
- **這根 K 上唯一的自訂停損掛在 `maTrail - TrailOffset`。**
  進場價 ≈ `maBase + 2 x ATR`，而 `maBase`(MA61) 與 `maTrail`(MA55) 數值接近
  → 自訂停損距進場價約 `2 x ATR + 50` 點。
  示意估算（未驗證）：ATR45 = 100 時約 **250 點**，
  而設計中的 Frozen SL 約 `min(150, 0.5 x DailyATR, 0.5% x 24000 = 120)` ≈ **120 點**。
  **自訂層在這 45 分鐘內比設計值寬約 2 倍。**
- **唯一有效保護 = P3b 引擎停損（`:527/:531`）。** 這正是 P3b 的設計目的（`:83-86`），架構成立。
- **但風險是**：整根進場 K 的防線**單點依賴**一個無法從程式碼確認持續性的引擎函數（G 節第 1 項）。
  若 P3b 因任何原因失效，曝險立刻從 120 點跳到 250 點，且**沒有第二道防線會發現**。

### E-2 【真空 — 已知，本次確認】獲利 0 ~ +200 點區間

- `:578` 硬門檻 `(Close - Entry_P) >= stopProfitPoints_Long(200)`。未達標時 P7 完全不參與。
- `maTrail - 50` 在進場初期位於進場價**下方**約 `2 x ATR + 50` 點（見 E-1），
  且 MA55 需上漲約 `2 x ATR + 50` 點才追平進場價 → 這條腿在此區間**幾乎必然是無效腿**。
- 唯一保護 = 凍結初始停損（約 `Entry - 120`，示意估算）。
- **最壞往返**：峰值 +199 → 回落至 `Entry - 120` = **319 點**
  = 63,800 NTD/口 x 2 口 ≈ **127,600 NTD**（示意估算，未驗證）。
- **確認為真空。**

### E-3 【非真空】P7 武裝後價格跌回 +200 以下

- `:578` 條件不成立時，整個 block 不執行，但 `stopProfitPrice_L` 是 `IntraBarPersist` 變數（`:306-309`），
  **只在 flat 時被重設**（`:618`）→ **不會解除武裝**。
- 與 `:576-577` 註解「never disarms until flat」一致。
- **非真空。設計正確。**

### E-4 【曝險窗，非真空】Gap 分支觸發 → 下一根 K 開盤

- 見 C-4。市價單無法取消，跨盤時最長 3 小時 45 分無成交機會。
- 這是 Market 單的固有性質，非程式碼缺陷，但**必須列入實盤風險認知**。

### E-5 【曝險窗，非真空】盤中休市（13:45→15:00 / 05:00→08:45）

- 所有腿的值在休市期間都不更新（`maTrail` 需 K 棒、P7 需 tick）。
- Stop 單在重新開盤時若開盤價已穿價，以開盤價成交 → **滑價不受 `TrailOffset` 或 `SL_Pct` 約束**。
- 全策略共通，非 L1 特有。

### E-6 【真空 — 制度層】`Manual_Kill_Switch` 開啟後仍可建立新倉

- 出場端：`:646-648` 每 tick 發 `TL_Kill` 市價單 ✅
- 進場端：`:538-542` 的 gate 為 `MP = 0` / `Cond_Breakout` / `v_Weekly_Filter` /
  `v_Holiday_Block = false` / `v_Settlement_Day = false` → **完全沒有 `Manual_Kill_Switch` 檢查**。
- **後果**：Kill 開啟後策略變成「持續平倉 + 仍會在下次 `Crosses Over` 時重新買進」。
  使用者按下緊急停市鈕，得到的是**平倉，不是停止交易**。
- `Crosses Over`（`:536`）需要新的穿越，所以不會每根 K 無限churn，但**新倉確實會建立**。
- **這是安全架構的真空，且直接違反憲法條款 3 對 P0-1 的定位。** 見 F 節。

### E-7 【真空 — 潛在，觸發條件不確定】`Entry_P = 0` 時凍結出垃圾停損

- `:553` `Entry_P = EntryPrice`，**沒有任何 `Entry_P > 0` 的健全性檢查**。
- 若在某個 `BarStatus(1) = 2` 的 tick 上 `MarketPosition > 0` 但 `EntryPrice` 回傳 0，
  則 `:568` 會把 `v_Frozen_SL` 凍結成負值或 0，並且 `:569` 把 `v_SL_Locked = True`
  → **整筆交易的初始停損永久失效，且不會有任何訊號。**
  同時 `:578` 的 `(Close - 0) >= 200` 恆成立 → `stopProfitPrice_L = 0.45 x Close`（遠低於現價）→ 亦無保護。
- `[不確定]`：MC9 是否可能出現 `MarketPosition > 0` 但 `EntryPrice = 0` 的狀態
  （例如策略重載、Force Flat 後狀態不同步、手動 Roll Over 後——憲法補充規則 4 明列此場景）。
- **無論觸發機率高低，「缺少健全性守衛」本身是可確認的事實。**

### E-8 【真空 — 實盤特有】MC 重啟 / 策略重載後的 P7 地板下修

- `posbleProfit_Long` / `stopProfitPrice_L` / `v_Trail_High` 是 `IntraBarPersist` 狀態變數（`:306-309`），
  重載時由 MC 從圖表歷史**重新計算**。
- `v_Trail_High` 來自 MA55，可完整重現 ✅。
- `posbleProfit_Long` 來自**逐 tick 的 `Close` 峰值**（`:579-580`）。
  重載時 MC 只能用 Bar Magnifier 資料（1 分鐘）重建，
  **重建出的 peak 必然 ≤ 真實 tick peak** → `stopProfitPrice_L` 在重載後**變低**。
- **後果**：實盤 MC 重啟一次，鎖利地板就無聲下修一次，且圖表不會顯示這件事。
- 檔案自己的 header 已警告同類問題：`:44-46`「recalculated chart may disagree with a
  live open position. Deploy ONLY WHEN FLAT」——但那是講**部署**，**重啟**沒有對應警告。
- `[部分不確定]`：實際下修幅度取決於 MC9 的重建行為，需實測。

### E-9 【非真空，但「無此機制」本身是發現】濾網 / 箱型狀態變化

- 任務要求檢查「箱型/濾網狀態變化時」。**L1 沒有箱型模組。**
- 唯一的濾網 `v_Weekly_Filter`（`:441-450`）**只出現在進場 gate（`:540`）**，
  全檔出場邏輯中**零引用**（已 grep 確認）。
- `Cond_Breakout`（`:536`）同樣只用於進場。
- → **週線趨勢反轉不會平倉；突破結構被破壞不會平倉。**
  L1 沒有任何「進場理由消失就出場」的機制，只有價格型停損。
- 非程式碼 bug，但這是 Rule #17「ATR 停損 = 最後防線，不是主要出場機制」要求的
  「主動防線」在 L1 中**完全不存在**的直接證據。見 F 節。

### E-10 【非真空】`posbleProfit_Long` 跨交易殘留

- 出場成交後 `MP <= 0` → `:613-620` else 分支執行，五個狀態變數全部重設。
- 新倉最快只能在下一根 K 收盤下單（`:535` 受 `BarStatus(1)=2` 守衛）、下下根開盤成交，
  中間必然經過至少一次 `MP <= 0` 的評估 → **重設一定會發生。無殘留。**

---

## F. 與規範的合規落差

### F-1 CLAUDE.md Rule #11 / 憲法條款 1（Settlement_Flat 7 元素）

| 元素 | 要求 | L1 現況 | 判定 |
|---|---|---|---|
| 1 | `Settlement_Flat_Time(1230)` input | `:256` 值 1230 | ✅ |
| 2 | `v_Settlement_Day` 變數 | `:288` | ✅ |
| 3 | 偵測邏輯在 entry/exit 之前 | `:490-492`，早於 `:535` 與 `:551` | ✅ |
| 4 | Entry gate 含 `v_Settlement_Day = false` | `:542` | ✅ |
| 5 | P0 出場 `else if v_Settlement_Day and Time >= Settlement_Flat_Time` | `:642-644`，寫法完全相符 | ✅（憲法條款 9 已豁免無上界寫法） |
| 6 | 標籤前綴 `TL_` | `TL_Settlement`（`:643`） | ✅ |
| 7 | `scripts/verify_settlement_flat.py` 通過 | **本次唯讀稽核未執行任何腳本** | **未驗證** |

### F-2 憲法條款 3（Priority-0 出場鏈順序）— **兩處明確偏差**

憲法要求（`SETTLEMENT_DAY_DESIGN_CONSTITUTION.md:93-104`）：
`Kill > Registry > Holiday > Settlement > 原邏輯`，且「順序不可更動」「任何違反順序的策略 = 不可上架」。

**偏差 F-2a：Kill 不在鏈首，而在鏈外鏈後。**
- `:636` Registry → `:639` Holiday → `:642` Settlement 為 else-if 鏈；
  `:646` Kill 是**鏈外獨立 `if`**，位置在最後。
- 實務後果：Kill 與鏈上任一分支可同時發單（D-4）。
- 由於四者皆為 `next bar at Market` 全倉單，最終「平倉」的結果多半相同，
  但**成交記錄的標籤可能不是 `TL_Kill`**，事後歸因會失真。
  且若 D-6 第 1 項的超額出場風險成立，兩張單同時觸發的後果不可忽視。

**偏差 F-2b：「原邏輯」不在鏈上，而是在 Priority-0 之前的獨立區塊。**
- 憲法把「原策略邏輯（SP / Trail / Daily Exit）」定為 P0-5，是互斥鏈的**最後一位**。
- L1 的 Section 3（`:551-611`）是**獨立的 `if MP > 0` 區塊，位置在 Section 4（`:634`）之前**，
  且**必定發單**（`:610` 有 else 兜底）。
- → L1 的出場架構**根本不是憲法要求的互斥優先鏈**，而是「原邏輯永遠先發一張，Priority-0 再疊加」。
- 這是 D-3 所述「Stop 單與 Market 單常態並存」的根因。

### F-3 CLAUDE.md Rule #12（P3b Immediate Stop Guard）

| 要求 | L1 現況 | 判定 |
|---|---|---|
| `SetStopContract` 必須在 `SetStopLoss` 前呼叫 | `:524` 在 `:527/:531` 之前 | ✅ |
| `SetStopLoss` 存在 | `:527` / `:531` | ✅ |
| `SL_Pct` input 存在 | `:230`，預設 0.5 | ✅ |
| Long 策略 guard `if MP <= 0` | `:525` | ✅ |
| 必須在進場區塊之前、指標計算之後 | 指標 `:424-432` → SetStop `:524-533` → 進場 `:535` | ✅ |
| **距離公式必須與 Frozen SL 使用相同變數和乘數** | ATR/Cap 乘數相同；**但 Pct 腿用 `Close`（`:529`）而 Frozen SL 用 `Entry_P`（`:565`）；且 ATR 快照差一根 K（B 節落差 2）** | **⚠ 偏差** |
| **每隻策略僅限 1 組 `SetStopContract` + `SetStopLoss` 呼叫（不可重複）** | `SetStopContract` 1 處（`:524`）；**`SetStopLoss` 有 2 個呼叫點**（`:527` / `:531`） | **⚠ 字面偏差** |
| 金額 = 點數 x `BigPointValue` | `:529` / `:532` 皆有 `* BigPointValue` | ✅ |

- 「2 個 `SetStopLoss`」是 `if SL_Pct > 0 / else` 的分支，**單次執行只會呼叫一個**，
  語義上不構成「兩個競爭停損」。列為**字面偏差**，建議由使用者裁示是否需要改寫成單一呼叫。
- 「相同變數」那一項是**實質偏差**，且產生 B 節落差 2 的行為後果，建議優先處理。

### F-4 CLAUDE.md Rule #17（極端行情多層停損 SOP）

SOP 適用範圍（`extreme_sl_multilayer_sop_20260629.md:213-218`）四條件：
極端波動環境 / 用 ATR 初始停損 / 持倉跨越可能 500-1000 點波動 / 易受程式單停損串連影響。
L1 符合第 2、3、4 條；第 1 條「極端波動環境」是否涵蓋 L1 這種趨勢多單，
SOP §9 的 current candidates 只列 S3_S / S6 / S9，**未列 L1**。
→ **適用性本身 `[不確定]`，需使用者裁示。** 若判定適用，以下為落差：

| SOP 要求 | L1 現況 | 判定 |
|---|---|---|
| ATR 停損 = 最後防線，不是主要出場機制（§1 原則 1） | L1 虧損側**唯一**機制就是 `v_Frozen_SL`（ATR/DailyATR/Pct 三選一取緊）。前面沒有任何主動防線。 | **⚠ 落差** |
| 1M 五層即時監控（§3 1F-5F） | **完全不存在**。L1 只有 Data1=45M / Data2=Daily / Data3=Weekly（`:8`），**沒有 1M 資料流**。 | **⚠ 落差（結構性）** |
| 觸發機制：加權積分 ≥ 65% + 跨類別 ≥ 3 層 | 不存在 | **⚠ 落差** |
| 禁止固定點數 cap（§1 原則 3） | 初始停損的 cap 是 `Daily_ATR x 0.5`（vol-adaptive）與 `Entry x 0.5%`（價格比例），**皆非固定點數** ✅；但出場架構中有兩個固定點數常數：`TrailOffset(50)`（`:234`）與 `stopProfitPoints_Long(200)`（`:237`） | **部分符合**。SOP 字面只禁初始停損的固定點數 cap，L1 的初始停損合規；TrailOffset / SP 門檻是否在禁令範圍內 `[不確定]`，需裁示 |
| 所有新策略停損 spec 必須引用本 SOP 並檢查合規 | `.pla` header（`:13-187`）**未引用** Rule #17 或本 SOP | **⚠ 落差（文件面）** |

### F-5 CLAUDE.md 技術規格（成本門檻）

- 規範：「任何保本／成本門檻常數必須 >= 10 點」（來回滑價 2,000 NTD = 10 點）。
- `TrailOffset = 50` ≥ 10 ✅
- `stopProfitPoints_Long = 200` ≥ 10 ✅
- P7 最小武裝時的地板 = `Entry + 200 x 0.45 = Entry + 90` 點 ≥ 10 ✅
- **無違反。**

### F-6 CLAUDE.md 程式碼規範第 10 條「每隻策略 < 150 行」

- L1 全檔 706 行（含 ~205 行 header 註解 + ~85 行假日登錄表 + ~50 行 MDD 視覺化模組）。
- 純邏輯行數仍明顯超過 150。**偏差，但屬既有 live 策略的歷史狀態**，非本次出場稽核的處理範圍，僅記錄。

### F-7 憲法第四章 checklist「任何 `Time >=` 條件是否同時有 `Time <=` 閉區間」

| 位置 | 條件 | 判定 |
|---|---|---|
| `:642` Settlement | `Time >= 1230`，無上界 | ✅ **條款 9 明文豁免**（憲法 `:176-218`） |
| `:639` Holiday | `Time >= 345`，無上界 | ✅ **實質閉區間**：`v_Holiday_Block` 只在 `Time <= 500` 的掃描中被設為 True（`:463-468`）；Registry 過期路徑（`:479`）雖會在任意時間設 True，但 `:636` 的 Registry 分支排在其前先攔截。與憲法 `:213-215` 描述的機制**完全吻合**，非漏寫 |

---

## G. `[不確定]` 清單（全部需物理驗證，禁止當事實使用）

| # | 不確定項 | 歧義在哪 | 影響 | 建議驗證方式 |
|---|---|---|---|---|
| 1 | **MC9 的 `SetStopLoss` 在停止呼叫後是否持續生效？** | `:90-92` 註解宣稱「Called only when flat -> freezes automatically」。EasyLanguage 家族有兩種可能語義：(a) 設定值黏著，持續產生停損單；(b) 需每根 K 呼叫，否則不再產生。程式碼無法區分。 | 決定 P3b 是「僅進場當根的保險」還是「整筆交易都在生效、且可能比 P3 更緊的實際主停損」（B 節落差 2）。也決定 E-1 真空的嚴重性。 | MC9 策略績效報表看是否出現 `Stop Loss` 標籤的出場，且發生在非進場當根 |
| 2 | **IOG=true 下，同一 tick 生成的 `next bar at ... Stop` 單能否在同一 tick 成交？** | MC 對 IOG 訂單生效時點的文件語義。 | 決定急殺穿越 P7 地板時的實際成交價與滑價。 | MC12 回測 trade list 逐筆檢視 `TL_SP` 的成交價 vs 當時 `stopProfitPrice_L` |
| 3 | **上一 tick 宣告、本 tick 未宣告的 `next bar` 單是否自動撤銷？** | Gap 分支（`:596`）觸發時 `:601` else 不執行，該次評估沒有重新宣告 Stop 單。 | 決定 C-4 描述的「Gap 分支期間 Stop 單消失」是否為真。 | MC12 逐 tick log 或 MC9 委託簿觀察 |
| 4 | **多張全倉 `Sell` 單在同一根 K 都被觸發時，MC9 是否超額出場？** | `Sell` 理論上只能平多不能開空，但 EasyLanguage 有「多個未指定 `total` 的出場單各自平全倉」的已知警告。 | **實盤 2 口。若超額出場，會變成反向空單。這是本清單風險最高的一項。** | MC9 上刻意讓 Settlement 與 Trail 同根觸發，看實際成交口數 |
| 5 | **`MarketPosition > 0` 但 `EntryPrice = 0` 的狀態在 MC9 是否可能出現？** | 憲法補充規則 4 明列「手動 Roll Over 後 MC 狀態脫鉤」場景，但未說明 `EntryPrice` 的回傳值。 | 決定 E-7 真空的觸發機率（「缺少守衛」本身已是確定事實）。 | MC9 Force Flat / 手動 Roll 後觀察策略內部值 |
| 6 | **策略重載後 `posbleProfit_Long` 的重建幅度** | Bar Magnifier 只有 1M OHLC，重建的 peak 必然 ≤ 真實 tick peak，但差多少無法從程式碼推導。 | 決定 E-8 的實際嚴重性。 | 實盤持倉中重載策略，前後比對 `stopProfitPrice_L` |
| 7 | **Rule #17 是否適用於 L1** | SOP §9 條件 1「極端波動環境」定義模糊，且 current candidates 未列 L1。 | 決定 F-4 是否算違規。 | 使用者裁示 |
| 8 | **`TrailOffset(50)` / `stopProfitPoints_Long(200)` 是否落在 Rule #17「禁止固定點數 cap」的射程內** | SOP §1 原則 3 的字面對象是初始停損的 cap。 | 決定 F-4 最後一列。 | 使用者裁示 |
| 9 | **所有點數示意估算（120 / 250 / 319 / 550 點等）** | 皆為依現行 input 與假設 ATR、假設指數位階 24000 推導，**未經回測**。 | 影響 E-2 / E-1 / C-2 的量級判斷，不影響方向性結論。 | MC12 回測 MFE/MAE 分佈 |

---

## H. 直接回答使用者的原始提問：「急拉時移動停利跟不上」

**結論（依 `:424-426` / `:578-583` / `:588` / `:590-591` 靜態推導）：**

「跟不上」的感受**不是來自更新頻率不足，而是來自兩條腿的分工與 P7 的比例式公式。**

1. **P4 均線移動停利（MA55 - 50）在急拉中結構性失效，且無法靠調參救。**
   三重遲滯：MA55 ≈ 2.2 個交易日均線 + 固定 -50 點 offset + 一根 45M K 才更新一次（`:424` `:426`）。
   急拉時它離現價可能數百點以上，早就退出「三腿取最高」的競爭（`:590-591`）。

2. **急拉時真正在保護部位的是 P7，不是 P4。**
   `Entry + 0.45 x peak` 隨急拉線性上移，必然超過落後的 `maTrail - 50`。

3. **P7 的更新頻率完全跟得上（每 tick，`:578` 無 BarStatus 守衛），
   但它容許的回吐 = 峰值的 55%，且沒有絕對點數上限。**
   急拉越猛、峰值越大，絕對回吐點數就越大。
   示意估算（未驗證）：peak +1000 點 → 允許回吐 550 點 → 2 口約 220,000 NTD。

4. **L1 目前沒有任何「貼著現價」的移動停利機制。**
   全檔只有三條腿（`:590-591`）：凍結初始停損、MA55 高水位棘輪、P7 比例地板。
   沒有 ATR trail、沒有 Chandelier、沒有固定點數 trail、沒有保本停損（breakeven）。
   （已 grep 確認無 `SetPercentTrailing` / `SetDollarTrailing` / `SetBreakEven`。）

**因此若要改善急拉場景，槓桿點在 P7 的 `profitReturnPrcnt_Long(55)` 與其公式形態
（比例式 vs 帶絕對上限的混合式），而不是 P4 的 `Length20` / `TrailOffset`。**
→ **此為靜態推導，任何實際改動前必須先跑 MC12 回測驗證，並依 memory rule
`feedback_trend_let_profits_run` 檢查「出場端保護」是否會重蹈三次陣亡覆轍。**

---

## 附錄：驗收條件自我檢核

| 驗收條件 | 達成情況 |
|---|---|
| 1. A 表窮舉所有 `Sell` 且有自我核對聲明 | ✅ grep 得 10 筆，A 表列 10 筆 + 1 筆引擎出場，聲明見「全檔訂單語句清點」 |
| 2. B 對每一處 MaxList/MinList 逐一判定 | ✅ 8 處程式碼呼叫點全數判定（B-1~B-8） |
| 3. C 對每條腿回答「快速上漲」與「快速下跌」 | ✅ C-1~C-5 五組，每組皆含兩情境 |
| 4. E 至少系統性檢查 5 種狀態組合 | ✅ 檢查 10 種（E-1~E-10） |
| 5. 每個結論附 `檔案:行號`，行號實際讀到 | ✅ 全檔 1-706 完整讀取後標註 |
| 6. 歧義處標 `[不確定]` | ✅ G 節 9 項 + 內文行內標註 |
| 唯讀限制 | ✅ 未修改 repo 任何既有檔案；未讀 `.bak_*`；未跑編譯/回測 |
