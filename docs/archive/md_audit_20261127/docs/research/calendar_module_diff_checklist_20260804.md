---
建立日期: 2026-08-04
SOP: adversarial-engineering-sop 第 1 步（差異清單）
規則手冊: calendar_module_rules_20260804.md
資料來源: 兩個獨立 subagent 對 10 支在役策略的 .pla 靜態閱讀
驗證狀態: 未經 MC12 編譯與回測驗證；63 筆日期尚未與 TAIFEX PDF 核對
---

# 行事曆風控模組化 — 差異清單

> 本文為原始差異記錄，判定與決策見 [規則手冊](calendar_module_rules_20260804.md)。
> 兩份報告由兩個獨立 agent 產出（live 5 支 / live_simulation 5 支），
> 兩者**獨立確認 63 筆假日日期完全相同**（md5 一致）。


---

# Part A — live (L1-L5)

# Live 5 支策略 — Priority-0 行事曆風控出場鏈 + Holiday Registry 抽取比對

- 產出時間：2026-08-04
- 讀取對象（唯讀，未修改任何 repo 檔案；`.bak_*` 未讀）：
  - `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L1_TrendLong\L1_TrendLong.pla` (706 行)
  - `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L2_TrendShort\L2_TrendShort.pla` (741 行)
  - `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L3_ConsolidationLong\L3_ConsolidationLong.pla` (474 行)
  - `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla` (719 行)
  - `C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L5_BreakoutLong\L5_BreakoutLong.pla` (729 行)
- 未執行編譯、未執行回測。所有行號皆為實際讀到的行號。

---

## L1_TrendLong

檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L1_TrendLong\L1_TrendLong.pla`

### 基本資料
- 版本 V3.1；`[IntrabarOrderGeneration = true]` @ L1:220
- **K 棒週期**：檔頭 L1:8-11 寫 `Data1 = 45M / Data2 = Daily / Data3 = Weekly`，並明確註記「strategy name says 60M but Excel report confirms compression = 45 Minutes」→ **實際 45M**
- 標籤前綴：`TL_`

### A. Holiday registry 資料表
- 陣列宣告：`Array: Holiday_Tail[80](0);` @ L1:311-312 → **大小 80**
- 實際填入筆數：**63**（index 1..63），index 64..80 保持 0
- 日期格式：**民國年 YYYMMDD**（例 `1190913` = 民國 119 年 9 月 13 日 = 2019-09-13）
- 填表方式：**`if Init_Done = False then begin ... Init_Done = True; end;`** @ L1:333 / L1:416-418
  - 不是 `once`、也不是 `if CurrentBar = 1`。`Init_Done` 宣告於 L1:281（一般 Variables，非 IntraBarPersist）
  - 位置在指標計算（L1:420 起）之前
- `Registry_Valid_Until` = **1270101** @ L1:245（input，附 3 行註解說明每年 Q4 要 bump）
- 語意定義 @ L1:317-323：`Holiday_Tail` = 最後交易日 + 1 個日曆日 = 該夜盤 00:00-05:00 尾段 K 棒的日期戳記

#### 完整日期清單（L1:336-412，逐筆）
| idx | 值 | 註解 | idx | 值 | 註解 |
|---|---|---|---|---|---|
| 1 | 1190913 | (2019) | 33 | 1231007 | National Day |
| 2 | 1191010 | (2019) | 34 | 1231230 | 2024 New Year |
| 3 | 1200101 | 2020 New Year | 35 | 1240206 | CNY |
| 4 | 1200121 | CNY | 36 | 1240228 | 228 |
| 5 | 1200228 | 228 | 37 | 1240404 | Tomb Sweeping |
| 6 | 1200402 | Tomb Sweeping | 38 | 1240501 | * Labor Day |
| 7 | 1200501 | * Labor Day | 39 | 1240608 | Dragon Boat |
| 8 | 1200625 | Dragon Boat | 40 | 1240917 | Mid-Autumn |
| 9 | 1201001 | Mid-Autumn | 41 | 1241010 | National Day |
| 10 | 1201009 | National Day | 42 | 1250101 | 2025 New Year |
| 11 | 1210101 | 2021 New Year | 43 | 1250123 | CNY |
| 12 | 1210206 | CNY | 44 | 1250228 | 228 |
| 13 | 1210227 | 228 | 45 | 1250403 | Tomb Sweeping |
| 14 | 1210402 | Tomb Sweeping | 46 | 1250501 | * Labor Day |
| 15 | 1210612 | Dragon Boat | 47 | 1250530 | Dragon Boat (5/30 make-up) |
| 16 | 1210918 | Mid-Autumn | 48 | 1250927 | * Teachers Day (9/29 make-up) |
| 17 | 1211009 | National Day | 49 | 1251004 | Mid-Autumn |
| 18 | 1211231 | 2022 New Year | 50 | 1251010 | * National Day |
| 19 | 1220127 | CNY | 51 | 1251024 | * Retrocession Day |
| 20 | 1220226 | 228 | 52 | 1251225 | * Constitution Day |
| 21 | 1220402 | Tomb Sweeping | 53 | 1260101 | 2026 New Year |
| 22 | 1220430 | * Labor Day (5/2 make-up) | 54 | 1260212 | CNY (最後交易日 2/11) |
| 23 | 1220603 | Dragon Boat | 55 | 1260227 | 228 (2/27 make-up, eve 2/26) |
| 24 | 1220909 | Mid-Autumn | 56 | 1260403 | Children/Tomb 4/3-4/6, eve 4/2 |
| 25 | 1221008 | National Day | 57 | 1260501 | Labor Day 5/1-5/3, eve 4/30 |
| 26 | 1221231 | 2023 New Year | 58 | 1260619 | Dragon Boat 6/19-6/21, eve 6/18 |
| 27 | 1230118 | CNY | 59 | 1260925 | Mid-Autumn+Teachers 9/25-9/28 |
| 28 | 1230225 | 228 | 60 | 1261009 | National Day 10/9-10/11 |
| 29 | 1230401 | Tomb Sweeping | 61 | 1261024 | Retrocession (Saturday tail) |
| 30 | 1230429 | * Labor Day | 62 | 1261225 | Constitution 12/25-12/27 |
| 31 | 1230622 | Dragon Boat | 63 | 1270101 | 2027 New Year 1/1-1/3 |
| 32 | 1230929 | Mid-Autumn | | | |

> `*` 標記者為檔頭 L1:327-330 註明「舊 eve-based 清單漏掉、屬重建」的日期，原始碼要求「verify vs archived TAIFEX PDFs before trusting re-backtest stats」。

### B. Holiday 判定與出場
- 掃描區塊 @ L1:460-481，整段包在 **`if BarStatus(1) = 2 then begin`**（僅 bar close 執行）
- 旗標重置 `v_Holiday_Block = False;` @ L1:461 —— **在時間 guard 之外**
- **掃描時間條件：`if Time <= 500 then begin` @ L1:463（閉區間 `<=`）**
- 掃描迴圈：`for idx = 1 to 80` @ L1:464 → **掃滿 80 格**（含 17 個為 0 的空格，無 early break）
- Registry fail-safe @ L1:475-480：`if Date > Registry_Valid_Until then` → `v_Registry_Expired = True; v_Holiday_Block = True;`（此處設 True **不受 `Time <= 500` 限制**）
- `Holiday_Flat_Time` 預設 = **345**（03:45）@ L1:244，註解「fill 03:45, retry 04:30, flat before 05:00 close」
- 出場標籤：`TL_RegistryEnd` / `TL_Holiday` / `TL_Settlement` / `TL_Kill`（各 1 個，單腿）
- 進場封鎖：@ L1:538-544，`if MP = 0 and Cond_Breakout and (v_Weekly_Filter = true) and (v_Holiday_Block = false) and (v_Settlement_Day = false) then Buy ("TL_Entry") next bar at Market;`
- **出場時間上界：無顯式 `Time <=`**。實質上界靠 `v_Holiday_Block` 只在 `Time <= 500` 才會被設 True（見「重點查證 3」）

### C. Priority-0 鏈結構
位置：`4. P5 v3: Pre-Holiday Forced Flat (Iron Rule)` @ L1:622-650，包在 `if MP > 0 then begin` @ L1:634。**此區塊未包 `BarStatus(1) = 2`**（IOG=true 下每 tick 都跑）。

實際順序（L1:636-648）：
1. `if v_Registry_Expired then Sell ("TL_RegistryEnd") next bar at Market;`
2. `else if v_Holiday_Block and Time >= Holiday_Flat_Time then Sell ("TL_Holiday") ...`
3. `else if v_Settlement_Day and Time >= Settlement_Flat_Time then Sell ("TL_Settlement") ...`
4. **獨立 `if`（鏈外）**：`if Manual_Kill_Switch = True then Sell ("TL_Kill") next bar at Market;` @ L1:646-648

- 型態：**Registry → Holiday → Settlement 是單一 `if / else if` 鏈；Kill 在鏈外、且排在最後**
- **`ExitFired` 旗標：L1 完全沒有此變數**（grep 全檔 0 命中）。優先權靠 `else if` + 後續區段自行判斷
- 與 CLAUDE.md Rule #11 規定的「Kill > Registry > Holiday > Settlement」順序相比：**L1 的 Kill 寫在最後且獨立**，程式碼順序 = Registry → Holiday → Settlement → Kill
- 出場單型別：4 個分支全部 `Sell (...) next bar at Market`
- Settlement 判定 @ L1:490-492（**不在 `BarStatus` 內，每 tick 重算**）：
  `v_Settlement_Day = (DayOfWeek(Date) = 3) and (DayOfMonth(Date) >= 15) and (DayOfMonth(Date) <= 21);`

### D. 相依性
- 專屬變數：`Init_Done`(L1:281)、`idx`(L1:285)、`Registry_Warn_ID`(L1:284)
- 迴圈計數器名稱 **`idx`**（L2 用 `hidx`、L3/L4/L5 用 `hidx`）
- **跨 data stream**：整個 Holiday/Settlement 區段被 `if BarStatus(1) = 2` 包住（L1:460），即依賴 Data1 bar close；Data2/Data3 只在指標與 weekly filter 用到，Priority-0 鏈本身不引用 Data2/Data3
- 區段位置：registry 填表 L1:311-418（檔案前段，指標之前）；偵測 L1:452-507；進場 gate L1:509-545；Priority-0 出場 L1:622-650（在 P3/P4/P7 出場管理 L1:547-620 **之後**）
- 警示：`LastBarOnChart` + 30 天到期紅字 @ L1:496-507

---

## L2_TrendShort

檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L2_TrendShort\L2_TrendShort.pla`

### 基本資料
- 版本 5.3；**全檔無 `[IntrabarOrderGeneration]` 宣告**（grep 全 live 目錄只有 L1=true、L4=false）→ 走 MC 預設
- **K 棒週期**：檔頭 L2:8-10 `Timeframe : 60-Minute (Day + Night Sessions, grid verified vs Excel timestamps: day 09:45-13:45, night 16:00-05:00 hourly close stamps)` → **60M**
- 標籤前綴：`TS_`
- Session 判定 @ L2:224-232：`If (Time >= 845) And (Time <= 1245) Then IsDay = True Else IsDay = False;`（此處 `>=` 有配對 `<=`）

### A. Holiday registry 資料表
- 陣列宣告：`Array: WkCloses[ 21 ] ( 0 ), Holiday_Tail[ 80 ] ( 0 );` @ L2:215 → **大小 80**（與 WkCloses 共宣告一行）
- 實際填入筆數：**63**（index 1..63）
- 日期格式：**民國年 YYYMMDD**
- 填表方式：**`If CurrentBar = 1 Then Begin ... End;`** @ L2:253 / L2:336 —— **與 L1 的 `Init_Done` 旗標寫法不同**
- `Registry_Valid_Until` = **1270101** @ L2:122
- 位置：SECTION 4B，L2:235-336

#### 完整日期清單（L2:256-332）
數值 **與 L1 完全相同**（1..63 逐筆比對過，無任何一筆差異）。差異只在註解文字：
- L2:314 `Holiday_Tail[47] = 1250530; { Dragon Boat (5/30 make-up) }` — L1 同一筆的註解多了一句 `old list had 1250530 as eve = the holiday itself, could never fire`
- L2:323 `Holiday_Tail[54]` 註解缺 L1 的 `2/12-2/13 closed` 後半句
- L2:331 `Holiday_Tail[61]` 註解缺 L1 的 `(Saturday tail)`

### B. Holiday 判定與出場
- 掃描區塊 @ L2:338-352，**沒有任何 `BarStatus` 包覆**（與 L1 不同）
- 旗標重置 `v_Holiday_Block = False;` @ L2:338 —— 在時間 guard 之外
- **掃描時間條件：`If Time <= 500 Then Begin` @ L2:340（閉區間 `<=`）**
- 掃描迴圈：`For hidx = 1 To 80` @ L2:341 → 掃滿 80 格，無 early break
- Registry fail-safe @ L2:347-352，語意與 L1 相同
- `Holiday_Flat_Time` 預設 = **300**（03:00）@ L2:121，註解「03:00 trigger on 60M grid -> fill 03:00, retry 04:00」
- 出場標籤：`TS_Kill` / `TS_RegistryEnd` / `TS_Holiday` / `TS_Settlement`（各 1 個，單腿）
- 進場封鎖：@ L2:473-480，5 個 AND 條件含 `( v_Holiday_Block = False ) And ( v_Settlement_Day = False )`，動作 `SellShort( "TS_Entry" ) Next Bar at Market`
- **出場時間上界：無顯式 `Time <=`**

### C. Priority-0 鏈結構
位置：SECTION 13 @ L2:635-741，主體包在 `If MarketPosition = -1 Then Begin` @ L2:664。`ExitFired = 0;` 在 L2:662（**在 `If MarketPosition = -1` 之外**）。

實際順序（L2:666-687）—— **4 個各自獨立的 `If`，全部以 `(ExitFired = 0)` 開頭，無 `else if`**：
1. L2:667-670 `Manual_Kill_Switch = True` → `BuyToCover("TS_Kill") Next Bar at Market` → `ExitFired = 1`
2. L2:672-675 `v_Registry_Expired = True` → `BuyToCover("TS_RegistryEnd")` → `ExitFired = 1`
3. L2:677-681 `v_Holiday_Block = True And Time >= Holiday_Flat_Time` → `BuyToCover("TS_Holiday")` → `ExitFired = 1`
4. L2:683-687 `v_Settlement_Day = True And Time >= Settlement_Flat_Time` → `BuyToCover("TS_Settlement")` → `ExitFired = 1`

- **Kill 在鏈內且排第一**（與 L1/L3 的「Kill 在鏈外、排最後」相反），順序 = Kill → Registry → Holiday → Settlement，**符合 CLAUDE.md Rule #11**
- `ExitFired` 旗標：**Priority 0 四個分支全部設；Priority 1-4 也設；Priority 5（L2:721-728）與 Priority 6（L2:731-739）判斷 `ExitFired = 0` 但內部 NOT 設 `ExitFired = 1`**（讀到的程式碼確實沒有）
- 出場單型別：Priority-0 四個分支全部 `Next Bar at Market`
- Settlement 判定 @ L2:355-357：與 L1 同式（`DayOfWeek=3` + `DayOfMonth` 15..21）

### D. 相依性
- 專屬變數：`ExitFired`(L2:193)、`hidx`(L2:199)、`LoopIdx`(L2:192)、`IsDay`/`IsNight`(L2:141-142)
- 無 `Init_Done`（改用 `CurrentBar = 1`）
- **跨 data stream**：Priority-0 區段本身不引用其他 data stream；L2 的 weekly filter 是自建 `WkCloses` 陣列（非 Data3）
- 區段位置：registry + 偵測 SECTION 4B @ L2:235-370（在 weekly filter SECTION 5 之前）；進場 gate @ L2:473-480；Priority-0 出場在檔案最末的 SECTION 13 @ L2:662-687
- 警示：`LastBarOnChart` + 30 天到期紅字 @ L2:359-370（訊息字串為 `"HOLIDAY REGISTRY EXPIRES "`，L1 是 `"P5 HOLIDAY REGISTRY EXPIRES "`）

---

## L3_ConsolidationLong

檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L3_ConsolidationLong\L3_ConsolidationLong.pla`

### 基本資料
- 版本 v15.0（v14.1 base + SetStopContract + SL_Pct 0.55% + Opening Block + Min R:R）@ L3:5
- **無 `[IntrabarOrderGeneration]` 宣告**
- **K 棒週期**：檔頭 L3:8 `Timeframe : Data1 = 15M / Data2 = 60M / Data3 = Daily` → **執行 K 棒 15M**
- 標籤前綴：`CL_`
- 檔頭 L3:36-37 明講「KEPT: All safety modules (Holiday v3, Settlement, ImmediateStop, FrozenSL, BreakExit, Registry fail-safe, Manual Kill)」

### A. Holiday registry 資料表
- 陣列宣告：`arrays: Holiday_Tail[80](0);` @ L3:184-185 → **大小 80**（關鍵字為小寫 `arrays:`，L1/L2 是 `Array:`）
- 實際填入筆數：**63**
- 日期格式：**民國年 YYYMMDD**
- 填表方式：**`if CurrentBar = 1 then begin ... end;`** @ L3:191 / L3:226
- 排版：**每行兩筆**的緊湊寫法（L1/L2 是每行一筆），年份用行首註解 `{ 2020 }` 標示
- `Registry_Valid_Until` = **1270101** @ L3:121（**無 inline 註解**，L1/L2/L4/L5 都有）
- 區段標題 L3:188 寫 `(TAIFEX-verified, shared with L1/L2)`

#### 完整日期清單（L3:192-225）
數值 **與 L1/L2 完全相同**（1..63 逐筆比對過，零差異）。註解密度最低：只有年份分組註解 `{ 2020 } { 2021 } ... { 2026 (verified: TAIFEX official 115-yr calendar) }`，**沒有逐筆的節日名稱、也沒有 `*` 重建標記**。

### B. Holiday 判定與出場
- 掃描區塊 @ L3:228-242，**無 `BarStatus` 包覆**
- 旗標重置 `v_Holiday_Block = false;` @ L3:228 —— 在時間 guard 之外
- **掃描時間條件：`if Time <= 500 then begin` @ L3:230（閉區間 `<=`）**
- 掃描迴圈：`for hidx = 1 to 80` @ L3:231 → 掃滿 80 格，無 early break
- Registry fail-safe @ L3:237-242，語意與 L1/L2 相同
- `Holiday_Flat_Time` 預設 = **415**（04:15）@ L3:120，**無 inline 註解說明 grid**（L4/L5 有 `{ 15M grid: 04:15 trigger, retries 04:30/04:45 }`）
- 出場標籤：`CL_RegistryEnd` / `CL_Holiday` / `CL_Settlement` / `CL_Kill`（各 1 個，單腿）
- 進場封鎖：@ L3:360-373，外層 `if v_Box_Qualified and MarketPosition = 0 then begin`，內含 6 條 AND 條件（`v_Trend_Dir=1` / `v_Daily_Filter` / **`v_Holiday_Block = false`** / **`v_Settlement_Day = false`** / `v_Opening_Block = false` / `v_RR_Qualified = true`），動作 `Buy ("CL_Entry") next bar at v_Box_Btm Stop`
- **出場時間上界：無顯式 `Time <=`**

### C. Priority-0 鏈結構
位置：`6. Safety Exits (Priority 0, always active)` @ L3:445-461，包在 `if MarketPosition = 1 then begin` @ L3:449。

**關鍵結構事實**：L3 的進場邏輯與一般出場（CL_TP / CL_SL / CL_BE / CL_BreakExit）全部包在 `if v_is_in_consolidation and v_Box_Top > v_Box_Btm then begin` @ L3:331 ... `end else begin ... end;` @ L3:437-443。**Priority-0 區塊在這個 box-state 判斷之外**，因此箱型消失後仍會執行（區段標題自稱 "always active"）。

實際順序（L3:451-459）：
1. `if v_Registry_Expired then Sell ("CL_RegistryEnd") next bar at Market`
2. `else if v_Holiday_Block and Time >= Holiday_Flat_Time then Sell ("CL_Holiday") next bar at Market`
3. `else if v_Settlement_Day and Time >= Settlement_Flat_Time then Sell ("CL_Settlement") next bar at Market;`
4. **獨立 `if`（鏈外）**：`if Manual_Kill_Switch then Sell ("CL_Kill") next bar at Market;` @ L3:458-459

- 型態：**與 L1 完全同構** —— Registry/Holiday/Settlement 為 `if / else if` 鏈，Kill 獨立且在最後
- 語法差異：L3 的三個分支**沒有 `begin/end`**（單語句形式），L1 有
- `ExitFired`：**L3 全檔無此變數**（grep 0 命中）
- 出場單型別：4 個分支全部 `next bar at Market`
- Settlement 判定 @ L3:244-246：與 L1/L2 同式

### D. 相依性
- 專屬變數：`hidx`(L3:171)、`v_Opening_Block`(L3:164)、`v_RR_Qualified`(L3:165)、`v_is_in_consolidation`/`v_Box_Top`/`v_Box_Btm`（箱型狀態，但 Priority-0 不引用）
- 無 `Init_Done`、無 `ExitFired`
- **跨 data stream**：Priority-0 區段本身**不引用** Data2/Data3；但同檔的 box 邏輯用 Data2（60M）、daily filter 用 Data3
- 區段位置：registry L3:184-226；偵測 L3:228-259；進場 gate L3:360-373；Priority-0 出場 L3:445-461（檔案倒數第 2 個區塊，後面只剩 `7. State Reset` L3:463-474）
- 警示：`LastBarOnChart` + 30 天到期紅字 @ L3:248-259
- 另有 V15 Opening Block @ L3:345-350，含 `if Time = 500` 與 `if Time >= 900 and Time < Open_Block_End`（後者 `>=` 有配對上界 `< 945`）

---

## L4_ConsolidationShort

檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla`

### 基本資料
- 版本 v14.6 + SetStopContract + SL_Pct（PRODUCTION）@ L4:5
- **`[IntrabarOrderGeneration = false]` @ L4:237**（5 支中唯一明文設 false）
- **K 棒週期**：檔頭 L4:10 `Timeframe : Data1 = 15M / Data2 = 60M / Data3 = Daily` → **執行 K 棒 15M**
- 標籤前綴：`CS_`
- 檔頭 L4:6-7 註明 v14.3/v14.3.1 的 RangeForceExit 已於 2026-06-17 rollback

### A. Holiday registry 資料表
- 陣列宣告：`arrays: Holiday_Tail[80](0);` @ L4:356-357 → **大小 80**
- 實際填入筆數：**63**
- 日期格式：**民國年 YYYMMDD**
- 填表方式：**`if CurrentBar = 1 then begin ... end;`** @ L4:366 / L4:403
- 排版：每行兩筆（與 L3/L5 同）
- `Registry_Valid_Until` = **1270101** @ L4:267（inline 註解 `verified holiday-registry horizon; bump each Q4`）
- 區段標題 L4:359-363 寫 `shared with L1/L2/L3`，並註 `* = reconstructed`（但清單本身**沒有任何 `*` 標記**，是遺留的說明）

#### 完整日期清單（L4:367-401）
數值 **與 L1/L2/L3 完全相同**（1..63 逐筆比對，零差異）。年份分組註解為 `{ 2020 } ... { 2025 } { 2026 ... }`，無逐筆節日名稱。

### B. Holiday 判定與出場
- 掃描區塊 @ L4:405-419，**無 `BarStatus` 包覆**
- 旗標重置 `v_Holiday_Block = false;` @ L4:405 —— 在時間 guard 之外
- **掃描時間條件：`if Time <= 500 then begin` @ L4:407（閉區間 `<=`）**
- 掃描迴圈：`for hidx = 1 to 80` @ L4:408 → 掃滿 80 格，無 early break
- Registry fail-safe @ L4:414-419
- `Holiday_Flat_Time` 預設 = **415**（04:15）@ L4:266，註解 `{ 15M grid: 04:15 trigger, retries 04:30/04:45 }`
- 出場標籤：`CS_Kill` / `CS_RegistryEnd` / `CS_Holiday` / `CS_Settlement`（各 1 個，單腿）
- 進場封鎖：@ L4:547-560，9 條 AND 條件，含 `v_Holiday_Block = false` / `v_Night_Block = false` / `v_Settlement_Day = false`，動作 `SellShort ("CS_Entry") next bar at Market`
- **出場時間上界：無顯式 `Time <=`**
- 另有 Night Block @ L4:446-448：`if Night_Block_On = true and Time >= 200 and Time < 500 then v_Night_Block = true;`（`>=` 有配對上界 `< 500`）

### C. Priority-0 鏈結構
位置：`6. Exit Chain with Priority Gates` @ L4:655-682，包在 **`if MarketPosition = -1 then begin` @ L4:587**，該 block 一路延伸到檔尾 `end;` @ L4:719。`ExitFired = 0;` 在 L4:656（**在 `MarketPosition = -1` block 之內** —— 與 L2 的「在 block 之外」不同）。

實際順序（L4:658-682）—— **4 個各自獨立的 `if`，全部以 `(ExitFired = 0)` 開頭，無 `else if`**：
1. L4:659-662 `Manual_Kill_Switch` → `BuyToCover ("CS_Kill") next bar at Market` → `ExitFired = 1`
2. L4:665-668 `v_Registry_Expired` → `BuyToCover ("CS_RegistryEnd")` → `ExitFired = 1`
3. L4:671-675 `v_Holiday_Block and (Time >= Holiday_Flat_Time)` → `BuyToCover ("CS_Holiday")` → `ExitFired = 1`
4. L4:678-682 `v_Settlement_Day and (Time >= Settlement_Flat_Time)` → `BuyToCover ("CS_Settlement")` → `ExitFired = 1`

- 型態：**與 L2 同構**，Kill 在鏈內且排第一，順序 = Kill → Registry → Holiday → Settlement，符合 CLAUDE.md Rule #11
- `ExitFired`：Priority 0 四支全設；Priority 1（L4:685-690）、Priority 2（L4:693-698）也設
- **注意（差異點）**：Priority 3 的停損掛單區塊 @ L4:700-717 **完全沒有 `(ExitFired = 0)` 檢查**，`CS_SP`/`CS_BE`/`CS_SL` 三選一必定會掛出。即 Priority-0 觸發的同一根 K 棒，仍會同時掛出停損單。L2 的 Priority 5/6 至少有檢查 `(ExitFired = 0)`（雖然也不設定它）
- 出場單型別：Priority-0 四個分支全部 `next bar at Market`
- Settlement 判定 @ L4:422-424：與 L1/L2/L3 同式

### D. 相依性
- 專屬變數：`ExitFired`(L4:354)、`hidx`(L4:336)、`v_Night_Block`（Night Block，L4:446）、`v_Locked_Top`/`v_Locked_Btm`（Priority-0 不引用）
- 無 `Init_Done`
- **跨 data stream**：Priority-0 四支本身不引用其他 data stream；但同一個 exit chain 的 **Priority 1 引用 `Close of Data2`** @ L4:687。這代表整個 exit chain 區塊（含 Priority-0）在 Data2 尚未備妥時的行為與 Data2 綁定；抽模組時 Priority-0 本身可獨立，但不能把整段 chain 一起搬
- 區段位置：registry Phase -1 @ L4:356-403；偵測 L4:405-437；Night Block L4:439-448；進場 gate L4:547-560；Priority-0 出場 L4:655-682（檔案最末 block 內）
- 警示：`LastBarOnChart` + 30 天到期紅字 @ L4:426-437

---

## L5_BreakoutLong

檔案：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live\L5_BreakoutLong\L5_BreakoutLong.pla`

### 基本資料
- 版本 v19.9 + SetStopContract + SL_Pct + HolidayFlat_v3 + FrozenSL + ImmediateStop @ L5:5
- **無 `[IntrabarOrderGeneration]` 宣告**
- **K 棒週期**：檔頭 L5:8 `Timeframe : Data1 = 15M / Data2 = Daily / Data3 = Weekly` → **執行 K 棒 15M**
- 標籤前綴：`BL_`
- **雙進場腿**：`BL_Entry_Bot` @ L5:528、`BL_Entry_Mid` @ L5:532
- 檔頭 L5:118-135（FIX 2）自述本模組與 L1/L2/L3/L4 **"byte-identical" 的共享 registry**

### A. Holiday registry 資料表
- 陣列宣告：`arrays: Holiday_Tail[80](0);` @ L5:325-326 → **大小 80**
- 實際填入筆數：**63**
- 日期格式：**民國年 YYYMMDD**
- 填表方式：**`if CurrentBar = 1 then begin ... end;`** @ L5:335 / L5:372
- 排版：每行兩筆（與 L3/L4 同）
- `Registry_Valid_Until` = **1270101** @ L5:237
- 區段標題 `[SEC--1]` @ L5:328-333（注意標題字串是 `[SEC--1]`，兩個連字號）

#### 完整日期清單（L5:336-370）
數值 **與 L1/L2/L3/L4 完全相同**（1..63 逐筆比對，零差異）。

### B. Holiday 判定與出場
- 掃描區塊 @ L5:374-388，**無 `BarStatus` 包覆**
- 旗標重置 `v_Holiday_Block = false;` @ L5:374 —— 在時間 guard 之外
- **掃描時間條件：`if Time <= 500 then begin` @ L5:376（閉區間 `<=`）**
- 掃描迴圈：`for hidx = 1 to 80` @ L5:377 → 掃滿 80 格，無 early break
- Registry fail-safe @ L5:383-388
- `Holiday_Flat_Time` 預設 = **415**（04:15）@ L5:236，註解 `{ 15M grid: 04:15 trigger, retries 04:30/04:45 }`
- **出場標籤：每個分支各 2 個（雙腿）**，共 8 個 —— `BL_Kill_Bot`/`BL_Kill_Mid`、`BL_RegistryEnd_Bot`/`_Mid`、`BL_Holiday_Bot`/`_Mid`、`BL_Settlement_Bot`/`_Mid`
- 進場封鎖：**不是寫在進場條件裡，而是透過 `v_Allow_Entry` 旗標**（[SEC-0] TIME FILTER @ L5:408-429）：
  - `v_Allow_Entry = true;` @ L5:417
  - `if (Time >= 400) and (Time <= 500) then v_Allow_Entry = false;` @ L5:419-420
  - `if DayOfWeek(Date) = 6 and Time >= 1330 then v_Allow_Entry = false;` @ L5:422-423
  - `if v_Holiday_Block then v_Allow_Entry = false;` @ L5:425-426
  - `if v_Settlement_Day then v_Allow_Entry = false;` @ L5:428-429
  - 使用點：`if MarketPosition = 0 and v_Allow_Entry then begin` @ L5:521
  - **這是 5 支中唯一把封鎖抽成獨立旗標的寫法**；其餘 4 支都是把 `v_Holiday_Block = false` / `v_Settlement_Day = false` 直接串進進場的 AND 條件
- **出場時間上界：無顯式 `Time <=`**

### C. Priority-0 鏈結構
位置：`{ Priority 0: Holiday Iron Rule / Registry / Kill }` @ L5:574-588。

**巢狀層級（高風險發現）**：
```
if v_is_in_consolidation and v_Box_Top > v_Box_Btm then begin   { L5:499 }
    ...
    if MarketPosition = 1 then begin                            { L5:541 }
        ...
        { Priority 0 chain }                                    { L5:574-588 }
```
→ **L5 的 Priority-0 出場被 `v_is_in_consolidation` 箱型狀態 gate 住**。箱型消失時走 `end else begin` @ L5:705-710，該分支只有 `BL_BreakExit_Bot` / `BL_BreakExit_Mid`，**沒有 Holiday / Settlement / Registry / Kill**。
> 對照：L3 的同名安全出場區塊刻意放在箱型判斷**之外**（L3:445-461，標題自稱 "always active"）。**這是 L3 與 L5 之間最實質的行為差異。**
> 緩解（推測、未驗證）：箱型消失當根就會發出 `BL_BreakExit_*` at Market，理論上不會長期持倉無 box。但這條路徑不受 `Holiday_Flat_Time` 時間控制，也不受 Kill switch 控制。

實際順序（L5:576-588）—— **單一 `if / else if` 鏈，Kill 在鏈內且排第一**：
1. L5:576-578 `if Manual_Kill_Switch then` → `Sell ("BL_Kill_Bot") from Entry ("BL_Entry_Bot") next bar at Market;` + `Sell ("BL_Kill_Mid") from Entry ("BL_Entry_Mid") next bar at Market;`
2. L5:579-581 `else if v_Registry_Expired then` → `BL_RegistryEnd_Bot` + `BL_RegistryEnd_Mid`
3. L5:582-584 `else if v_Holiday_Block and Time >= Holiday_Flat_Time then` → `BL_Holiday_Bot` + `BL_Holiday_Mid`
4. L5:585-587 `else if v_Settlement_Day and Time >= Settlement_Flat_Time then` → `BL_Settlement_Bot` + `BL_Settlement_Mid`

- 型態：**第三種模式** —— 與 L1/L3（Kill 在鏈外、排最後）不同，也與 L2/L4（4 個獨立 if + ExitFired）不同
- `ExitFired`：**L5 全檔無此變數**
- 出場單型別：8 張單全部 `from Entry (...) next bar at Market`，**未指定口數**（其他 Stage 1/2/3 的出場單多數有 `CurrentContracts contracts` 或 `v_ScaleOut_Size contracts` 限定）
- Settlement 判定 @ L5:391-393：與 L1/L2/L3/L4 同式

### D. 相依性
- 專屬變數：`v_Allow_Entry`（時間/假日/DOW 綜合旗標）、`hidx`(L5:311)、`v_is_in_consolidation`/`v_Box_Top`/`v_Box_Btm`（**Priority-0 透過巢狀 gate 間接相依**）、`v_ScaleOut_Size`、`CurrentContracts`/`MaxContracts`（Stage 判斷，Priority-0 不用）
- 無 `Init_Done`、無 `ExitFired`
- **跨 data stream**：Priority-0 四支本身不引用其他 data stream；但其外層 gate `v_is_in_consolidation` 由 **Data2（Daily）** 計算（L5:435-457）→ **L5 的 Priority-0 間接相依 Data2**。這是 5 支中唯一的跨 data stream 相依
- 區段位置：registry `[SEC--1]` @ L5:325-372；偵測 L5:374-406；`[SEC-0]` TIME FILTER L5:408-429；進場 L5:521-535；Priority-0 出場 L5:574-588（在 `[SEC-4] EXIT LOGIC` 開頭、Stage 1/2/3 之前）
- 警示：`LastBarOnChart` + 30 天到期紅字 @ L5:395-406

---

# 跨策略比對總表

| 項目 | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| K 棒週期 (Data1) | **45M** | **60M** | 15M | 15M | 15M |
| Data2 / Data3 | Daily / Weekly | 無（自建 WkCloses） | 60M / Daily | 60M / Daily | Daily / Weekly |
| IOG 宣告 | `true` (L1:220) | 無宣告 | 無宣告 | `false` (L4:237) | 無宣告 |
| 標籤前綴 | TL_ | TS_ | CL_ | CS_ | BL_ |
| 陣列大小 | 80 | 80 | 80 | 80 | 80 |
| 實際筆數 | 63 | 63 | 63 | 63 | 63 |
| 日期格式 | 民國 YYYMMDD | 同 | 同 | 同 | 同 |
| 填表守衛 | **`Init_Done` 旗標** (L1:333) | `CurrentBar = 1` (L2:253) | `CurrentBar = 1` (L3:191) | `CurrentBar = 1` (L4:366) | `CurrentBar = 1` (L5:335) |
| 陣列宣告關鍵字 | `Array:` | `Array:`（與 WkCloses 同行） | `arrays:` | `arrays:` | `arrays:` |
| 排版 | 每行 1 筆 + 逐筆節日註解 | 每行 1 筆 + 逐筆註解 | 每行 2 筆，僅年份註解 | 每行 2 筆 | 每行 2 筆 |
| `Registry_Valid_Until` | 1270101 | 1270101 | 1270101 | 1270101 | 1270101 |
| 掃描時間條件 | `Time <= 500` (L1:463) | `Time <= 500` (L2:340) | `Time <= 500` (L3:230) | `Time <= 500` (L4:407) | `Time <= 500` (L5:376) |
| 掃描迴圈 | `for idx = 1 to 80` | `For hidx = 1 To 80` | `for hidx = 1 to 80` | `for hidx = 1 to 80` | `for hidx = 1 to 80` |
| 迴圈變數名 | **`idx`** | `hidx` | `hidx` | `hidx` | `hidx` |
| 偵測是否包 BarStatus | **是**（`BarStatus(1)=2`, L1:460） | 否 | 否 | 否 | 否 |
| `Holiday_Flat_Time` | **345** | **300** | 415 | 415 | 415 |
| `Settlement_Flat_Time` | 1230 | 1230 | 1230 | 1230 | 1230 |
| `Manual_Kill_Switch` 預設 | False | False | false | false | false |
| P0 鏈型態 | if/else-if（Kill 在鏈外、最後） | 4 個獨立 if + ExitFired | if/else-if（Kill 在鏈外、最後） | 4 個獨立 if + ExitFired | **單一 if/else-if（Kill 在鏈內、第一）** |
| P0 實際順序 | Registry→Holiday→Settlement→**Kill** | Kill→Registry→Holiday→Settlement | Registry→Holiday→Settlement→**Kill** | Kill→Registry→Holiday→Settlement | Kill→Registry→Holiday→Settlement |
| 符合憲法條款 3 順序 | **否**（Kill 排最後） | 是 | **否**（Kill 排最後） | 是 | 是 |
| `ExitFired` 變數 | 無 | 有 (L2:193) | 無 | 有 (L4:354) | 無 |
| P0 外層 gate | `if MP > 0` (L1:634) | `If MarketPosition = -1` (L2:664) | `if MarketPosition = 1` (L3:449) | `if MarketPosition = -1` (L4:587) | **`v_is_in_consolidation` (L5:499) 內再 `MarketPosition = 1` (L5:541)** |
| P0 標籤數 / 分支 | 1 | 1 | 1 | 1 | **2（Bot + Mid）** |
| 進場封鎖寫法 | 直接串 AND (L1:541-542) | 直接串 AND (L2:477-478) | 直接串 AND (L3:363-364) | 直接串 AND (L4:553-555) | **獨立 `v_Allow_Entry` 旗標 (L5:417-429)** |
| 警示訊息字串 | `"P5 HOLIDAY REGISTRY EXPIRES "` | `"HOLIDAY REGISTRY EXPIRES "` | 同 L2 | 同 L2 | 同 L2 |
| Settlement 偵測式 | 完全相同（`DayOfWeek=3` + `DayOfMonth` 15..21） | 同 | 同 | 同 | 同 |

參考基準：`docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` v1.2
- 條款 1（7 元素）@ 該檔:53-83；條款 3（P0 順序 Kill > Registry > Holiday > Settlement）@ 該檔:92-103；條款 4（scale-out 必須成對標籤）@ 該檔:105-114
- 條款 7/8 已於 2026-06-17 撤回（@ 該檔:140-173），撤回原因正是 `Time >= 1200` / `Time >= 1330` 在 MC 24 小時制下夜盤全為 true
- **但檢查表項目「任何 `Time >=` 條件是否同時有 `Time <=` 閉區間？（防夜盤誤觸）」仍有效** @ 該檔:234

---

# 重點查證 1：多標籤（雙腿）情況

| 策略 | 進場腿數 | P0 各分支標籤數 | 明細 |
|---|---|---|---|
| L1 | 1（`TL_Entry`） | 1 | `TL_RegistryEnd` / `TL_Holiday` / `TL_Settlement` / `TL_Kill` |
| L2 | 1（`TS_Entry`） | 1 | `TS_Kill` / `TS_RegistryEnd` / `TS_Holiday` / `TS_Settlement` |
| L3 | 1（`CL_Entry`） | 1 | `CL_RegistryEnd` / `CL_Holiday` / `CL_Settlement` / `CL_Kill` |
| L4 | 1（`CS_Entry`） | 1 | `CS_Kill` / `CS_RegistryEnd` / `CS_Holiday` / `CS_Settlement` |
| L5 | **2**（`BL_Entry_Bot` L5:528 / `BL_Entry_Mid` L5:532） | **2** | Kill/Registry/Holiday/Settlement **四個分支全部各有 `_Bot` + `_Mid` 兩個標籤**，共 8 個（L5:576-587） |

**結論**：問題中提到的 `BL_Settlement_Bot` + `BL_Settlement_Mid` 不是特例 —— L5 的 **Kill / Registry / Holiday 也各有兩個標籤**（`BL_Kill_Bot`/`BL_Kill_Mid` L5:577-578、`BL_RegistryEnd_Bot`/`_Mid` L5:580-581、`BL_Holiday_Bot`/`_Mid` L5:583-584）。其餘 4 支**沒有任何多標籤情況**，全部單腿。

補充：L3 曾有雙腿但已移除 —— 檔頭 L3:28-30 明記 `REMOVED: CL_Entry_Bot / CL_Entry_Mid dual-leg split`。抽模組時若把 L3 當「單腿」硬編碼，之後若 L3 回頭做 scale-out 會再撞一次。

L5 的 8 張 P0 出場單全部寫 `from Entry ("BL_Entry_XXX") next bar at Market` 且**未指定口數**；同檔其他出場單（Stage 1/2/3）多數有 `CurrentContracts contracts` / `v_ScaleOut_Size contracts` 限定 —— 抽模組時這個「不指定口數」的寫法必須原樣保留。

---

# 重點查證 2：時間值 vs K 棒週期相容性

前提（推算基礎）：TXF1 日盤 08:45-13:45、夜盤 15:00-05:00（來源：專案 CLAUDE.md「交易時段」段）。K 棒格點由 session 起點對齊推算。

| 策略 | 週期 | `Holiday_Flat_Time` | 該時點是否有對應收盤 | `Settlement_Flat_Time` | 該時點是否有對應收盤 |
|---|---|---|---|---|---|
| L1 | 45M | 345 (03:45) | **有** — 15:00 + 45m×17 = 03:45；程式碼註解 L1:626-627 自述「trigger on the 03:45 bar, fill at 03:45; retry on the 04:30 bar」 | 1230 (12:30) | **有** — 08:45 + 45m×5 = 12:30 |
| L2 | 60M | 300 (03:00) | **有** — 檔頭 L2:9-10 自述夜盤「16:00-05:00 hourly close stamps」，03:00 在其上；input 註解 L2:121 亦寫「fill 03:00, retry 04:00」 | 1230 (12:30) | **無** — 檔頭 L2:9 自述日盤收盤戳記為 09:45/10:45/11:45/12:45/13:45，**12:30 不是格點** |
| L3 | 15M | 415 (04:15) | **有** — 15M 格點含 04:15 / 04:30 / 04:45 | 1230 (12:30) | **有** |
| L4 | 15M | 415 (04:15) | **有** — input 註解 L4:266 自述「15M grid: 04:15 trigger, retries 04:30/04:45」 | 1230 (12:30) | **有** |
| L5 | 15M | 415 (04:15) | **有** — input 註解 L5:236 同 L4 | 1230 (12:30) | **有** |

**唯一不相容項：L2 的 `Settlement_Flat_Time = 1230` 在 60M grid 上沒有對應收盤時點。**

但這**不是**「永遠不會觸發」，因為條件是 `Time >= Settlement_Flat_Time`（L2:684）而非 `Time =`：
- 日盤第一根滿足 `Time >= 1230` 的棒是 **12:45** → 該棒收盤發出 `BuyToCover("TS_Settlement") Next Bar at Market` → 於 12:45-13:45 那根的開盤（12:45）成交
- 仍落在 13:30 結算之前 → **實質保護未失效**，但比 input 註解宣稱的「12:30 trigger」晚 15 分鐘

**抽模組風險**：若共用模組把條件改成 `Time = Settlement_Flat_Time`（看似更精確），**L2 會直接失去結算日保護**。這是本次抽取最容易踩到的單點失誤之一。

**沒有任何一支出現「該時間點永遠不會觸發」的高風險組合。**

---

# 重點查證 3：閉區間紀律 —— 所有 `Time >=` 條件配對檢查

以下為 5 支全部 `Time` 比較式的完整清單（來源：全 live 目錄 ripgrep，已逐條回讀原始碼確認）。

## ✅ 有配對上界者
| 位置 | 條件 |
|---|---|
| L2:224 | `If ( Time >= 845 ) And ( Time <= 1245 )` （IsDay 判定） |
| L3:349 | `if Time >= 900 and Time < Open_Block_End`（上界 = 945，半開區間但有界） |
| L4:447 | `if Night_Block_On = true and Time >= 200 and Time < 500` |
| L5:419 | `if (Time >= 400) and (Time <= 500)` |

## ❌ 沒有配對上界者（共 11 處）

### (a) Holiday 出場 —— 5 處，**有「間接上界」**
| 位置 | 條件 |
|---|---|
| L1:639 | `else if v_Holiday_Block and Time >= Holiday_Flat_Time` |
| L2:678 | `( v_Holiday_Block = True ) And ( Time >= Holiday_Flat_Time )` |
| L3:453 | `else if v_Holiday_Block and Time >= Holiday_Flat_Time` |
| L4:672 | `v_Holiday_Block and (Time >= Holiday_Flat_Time)` |
| L5:582 | `else if v_Holiday_Block and Time >= Holiday_Flat_Time` |

**判定：實質安全，但靠「旗標」而非「閉區間」**。理由：5 支的 `v_Holiday_Block` 都先被無條件重設為 false（L1:461 / L2:338 / L3:228 / L4:405 / L5:374），只有在 `Time <= 500` 的 guard 內才可能被設 true。因此 `Time > 500` 的棒上 `v_Holiday_Block` 恆為 false → 實際生效窗口 = `[Holiday_Flat_Time, 500]`。

**唯一漏洞已被優先序封死**：`v_Registry_Expired` 為 true 時會**不受時間限制**地把 `v_Holiday_Block` 設 true（L1:477-480 / L2:349-352 / L3:239-242 / L4:416-419 / L5:385-388）。但 5 支的 Registry 分支都排在 Holiday 分支之前（L1/L3/L5 靠 `else if`，L2/L4 靠 `ExitFired`），所以該狀態下 Holiday 分支不可達。**抽模組時若把 Registry 與 Holiday 的順序調換、或把 `else if` 拆成獨立 `if`，這個保護會立刻消失。**

### (b) Settlement 出場 —— 5 處，**沒有任何上界，且旗標本身也沒有時間界**
| 位置 | 條件 |
|---|---|
| L1:642 | `else if v_Settlement_Day and Time >= Settlement_Flat_Time` |
| L2:684 | `( v_Settlement_Day = True ) And ( Time >= Settlement_Flat_Time )` |
| L3:455 | `else if v_Settlement_Day and Time >= Settlement_Flat_Time` |
| L4:679 | `v_Settlement_Day and (Time >= Settlement_Flat_Time)` |
| L5:585 | `else if v_Settlement_Day and Time >= Settlement_Flat_Time` |

**判定：這 5 處是真正未配對的條件，與憲法檢查表項目（該檔:234）直接衝突。**

`v_Settlement_Day` 只由日期決定（`DayOfWeek(Date) = 3` + `DayOfMonth` 15..21），**完全沒有時間界**。因此結算日當天任何 `Time >= 1230` 的棒都會觸發，包含夜盤 15:00 之後的所有棒 —— 這正是憲法條款 7/8 撤回文件描述的「MC 24-hour 制下夜盤 15:00-23:59 全部為 true」情境（該檔:146-147）。

**是否真的誤觸，取決於 MC session template 如何為夜盤棒蓋日期戳記** → 見下方 `[不確定]` 清單第 1 條。
補充事實：憲法條款 1 的「元素 5」參考實作（該檔:75）本身就寫成無上界的 `else if v_Settlement_Day and Time >= Settlement_Flat_Time`，**憲法內部（元素 5 vs 檢查表第 234 行）互相矛盾**。

### (c) 其他 —— 1 處
| 位置 | 條件 | 判定 |
|---|---|---|
| L5:422 | `if DayOfWeek(Date) = 6 and Time >= 1330 then v_Allow_Entry = false;` | 未配對上界。僅為**進場**過濾（不影響出場），且 DOW=6（週六）只可能出現夜盤尾段 00:00-05:00 的棒 → `Time >= 1330` 在週六大概率永遠不成立，實質為 no-op。檔頭 L5:112-114 稱這段「IS correct Saturday」而刻意保留。**[不確定]**：實際是否有週六 13:30 後的棒需 MC 資料驗證 |

---

# `[不確定]` 清單

1. **`v_Settlement_Day` 在夜盤是否為 true（決定 5 支 Settlement 分支是否夜盤誤觸）**
   取決於 MC session template 對夜盤 15:00-23:59 棒的日期戳記：若戳記為當日（結算週三）→ `Time >= 1230` 全為 true → 該夜盤整段被強制平倉／無法持倉；若戳記為次一交易日（週四）→ `DayOfWeek = 4`，不觸發。憲法撤回文件（`SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`:146-147）明講「MC PowerLanguage 24-hour 制下，夜盤 15:00-23:59 全部為 true」，暗示戳記為當日。**但那段講的是日盤持倉延續到夜盤的情境，不能直接等同於「`Date` 也是週三」**。未跑 MC，無法確認。這是抽模組前必須用實機或 print log 驗證的第一順位項目。

2. **各策略的 K 棒格點對齊起點**
   本報告的「時間點是否存在」是由「session 起點 + 壓縮週期」推算，不是從檔案讀到的。L1/L2/L4/L5 的 input 註解與檔頭自述格點與我的推算一致（L1:626-627、L2:9-10 + L2:121、L4:266、L5:236），可信度較高；**L3 完全沒有格點註解**（L3:120 是 5 支中唯一無 inline 註解的 `Holiday_Flat_Time`），其 04:15 屬 15M 格點的推論未被檔案文字佐證。

3. **L1 的 `BarStatus(1) = 2` 對 Priority-0 的實際影響**
   L1 是唯一 `IOG = true` 的策略，其 Holiday 偵測包在 `BarStatus(1) = 2` 內（L1:460）而 Priority-0 出場區塊（L1:634-650）**沒有** BarStatus 包覆 → 出場條件每 tick 評估、但 `v_Holiday_Block` 只在 bar close 更新。`v_Settlement_Day`（L1:490-492）則是每 tick 更新。這個混合語意在 IOG=true 下是否會產生跨 tick 的狀態不一致，需實機驗證，本報告不做結論。

4. **L5 的 Priority-0 被 `v_is_in_consolidation` gate 住的實際後果**
   `end else begin` 分支（L5:705-710）只有 `BL_BreakExit_Bot/Mid` at Market，理論上箱型消失當根就會平倉，所以「持倉 + 無箱型 + 遇到假日」的視窗應該只有 1 根 K 棒。但這是我讀碼後的推論，**未經回測或 log 佐證**。若 `BL_BreakExit` 因任何原因未成交（例如 next bar 無成交量），Holiday/Settlement/Kill 全部不會補位。

5. **L2 的 `Time` 語意（收盤戳記 vs 開盤時刻）**
   L2:220-221 的註解寫「IsDay : bar open time 08:45 to 12:45 (Time 845 to 1245)」，但檔頭 L2:9-10 寫日盤收盤戳記是 09:45-13:45。兩者用不同基準描述同一件事。我採用「`Time` = 收盤戳記」的 MC 標準語意做重點查證 2 的推算；若實際為開盤時刻，L2 的 12:30 相容性結論需重算。

6. **`Holiday_Tail` 日期本身是否與期交所行事曆一致**
   本報告只做「5 支之間的一致性比對」，**沒有**與期交所官方行事曆核對。原始碼自己標記 `*` 的共 **9 筆**（index 7, 22, 30, 38, 46, 48, 50, 51, 52 = 1200501 / 1220430 / 1230429 / 1240501 / 1250501 / 1250927 / 1251010 / 1251024 / 1251225），位置 L1:344, 363, 373, 383, 393, 395, 397, 398, 399；L2 亦保留同樣 9 個標記（L2:264, 283, 293, 303, 313, 315, 317, 318, 319）。L1:327-330 註明這些是「重建、未經 TAIFEX PDF 驗證，verify vs archived TAIFEX PDFs before trusting re-backtest stats」。
   **L3 / L4 / L5 的清單完全沒有保留這些 `*` 標記**（L4:363 的區段註解還寫著 `* = reconstructed`，但下方清單裡一個 `*` 都沒有）。抽模組時若以 L3/L4/L5 為母本，「哪些日期尚未驗證」的資訊會永久遺失。
   另注意 index 47（1250530，2025 端午）：L1:394 特別註明「old list had 1250530 as eve = the holiday itself, could never fire」，這是一筆歷史修正紀錄，只有 L1 保留完整說明。

---

# 抽模組時最可能改變行為的差異點（風險排序）

1. **L5 的雙腿標籤**（8 個 vs 其他 4 支的 4 個）—— 模組必須支援「每個 Entry 標籤對應一組出場標籤」，憲法條款 4（該檔:105-114）已明文要求
2. **L5 的 Priority-0 被箱型 gate 住** —— 若抽出後改成 always-active（如 L3），L5 的歷史行為會改變（多出「無箱型 + 假日」的出場路徑）；若維持 gate，則模組必須容許呼叫端決定巢狀位置
3. **P0 鏈的三種型態** —— Pattern A (L1/L3: Kill 鏈外最後)、Pattern B (L2/L4: 獨立 if + ExitFired)、Pattern C (L5: 單鏈 Kill 第一)。統一成任一種都會改變另外兩組的語意（尤其 L1/L3 的 Kill 目前**排在最後且與其他三支互不排斥**，統一後 Kill 會提前）
4. **`ExitFired` 的有無** —— L2/L4 有、L1/L3/L5 無。若模組要求 `ExitFired`，L1/L3/L5 需新增變數並改動其下游出場區塊；若模組不用，L2/L4 的下游 Priority 1-6 會失去互斥保護
5. **L2 的 `Settlement_Flat_Time = 1230` 不在 60M 格點上** —— 任何把 `>=` 改成 `=` 的「精確化」都會讓 L2 失去結算保護
6. **L1 的 `Init_Done` vs 其餘 4 支的 `CurrentBar = 1`** —— 語意上 `Init_Done` 對 MC 重新載入/重算的行為與 `CurrentBar = 1` 不同（`Init_Done` 只在變數被重設時才會再填一次）。**[不確定]** 兩者在 MC 12 的實際差異未驗證
7. **L1 的 `BarStatus(1) = 2` 包覆** —— 5 支中唯一，也是唯一 IOG=true。模組化後若移除或加上此 guard，L1 的 tick 級行為會改變
8. **L5 的 `v_Allow_Entry` 旗標寫法** —— 其餘 4 支是直接串 AND。模組若只提供旗標、不提供 gate helper，L5 的 `[SEC-0]` 區段需重寫
9. **迴圈變數名 `idx`(L1) vs `hidx`(其餘 4 支)** —— 純命名，但抽模組時若沿用 `hidx`，L1 的 `idx` 變數宣告（L1:285）會變成 dead variable（MC 不報錯，但 verify 腳本可能誤判）
10. **警示訊息字串 `"P5 HOLIDAY REGISTRY EXPIRES "`(L1) vs `"HOLIDAY REGISTRY EXPIRES "`(其餘)** —— 純顯示差異，統一無風險

---

# 驗收自查

- [x] 5 支全涵蓋，A~D 四類皆有內容
- [x] A 的完整日期清單逐筆列出（L1 表格為母本，其餘 4 支已逐筆比對確認數值相同）
- [x] 每個差異點附 `檔案:行號`，行號皆為實際 Read 讀到
- [x] 重點查證 1/2/3 對 5 支逐一判定
- [x] 歧義處標 `[不確定]`（共 6 條 + 內文散見 3 處）
- [x] 唯讀：本次僅寫入本報告檔，未修改 repo 內任何檔案；未讀 `.bak_*`；未跑編譯／回測


---

# Part B — live_simulation (S1 / S3_L / S3_S / S3_RPS / S16_S)

# Priority-0 行事曆風控出場鏈 + Holiday Registry 跨策略差異清單

- 產出日期：2026-08-04
- 範圍：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\live_simulation\` 下 5 支策略
- 方法：唯讀，逐檔實際讀取行號；未跑編譯、未跑回測；未讀任何 `.bak_*`
- 目的：抽出跨策略共用「行事曆風控模組」前的完整行為基線（零遺漏比精簡重要）

---

## 0. 總覽對照表（先看這張）

| 項目 | S1_NightMomentum | S3_VolSqueezeLong | S3_S_VolSqueezeShort | S3_RapidPullbackShort | S16_S_MACrossShort |
|---|---|---|---|---|---|
| 檔案總行數 | 484 | 542 | 1142 | 995 | 771 |
| Data1 K 棒 | **15M** | **60M** | **1M** | **5M** | **5M** |
| 多 data stream | data2=Daily / data3=Weekly（僅 TrendFilterMode>=2 用） | 無（60M 單一 feed） | Data2=60M, Data3=Daily | Data2=60M, Data3=Daily | 無（5M 單一 feed） |
| Registry 陣列 | `Holiday_Tail[80](0)` | `Holiday_Tail[80](0)` | `Holiday_Tail[80](0)` | `Holiday_Tail[80](0)` | `Holiday_Tail[80](0)` |
| 實際筆數 | 63 | 63 | 63 | 63 | 63 |
| 日期清單 | 完全相同（md5 驗證） | 同左 | 同左 | 同左 | 同左 |
| 填表方式 | `if CurrentBar = 1` | `if CurrentBar = 1` | `if CurrentBar = 1` | `if CurrentBar = 1` | `if CurrentBar = 1` |
| `Registry_Valid_Until` | 1270101 | 1270101 | 1270101 | 1270101 | 1270101 |
| 掃描時間條件 | `Time <= 500`（含） | `Time < 500`（strict） | `Time < 500`（strict） | `Time < 500`（strict） | `Time <= 500`（含） |
| 掃描迴圈 | `for hidx = 1 to 80` | 同 | 同 | 同 | 同 |
| `Holiday_Flat_Time` | 415 | 415 | 415 | **245** | 415 |
| `Settlement_Flat_Time` | 1230 | 1230 | 1230 | 1230 | 1230 |
| 出場上界 `Time <= 455` | **無** | **有** | **有** | **有** | **無** |
| P0 鏈型式 | `if / else if`（無旗標） | 獨立 `if` + `ExitFired` | 獨立 `if` + `ExitFired` | 獨立 `if` + `ExitFired` | 獨立 `if` + `ExitFired` |
| `ExitFired` 變數 | **不存在** | 有 | 有 | 有 | 有 |
| Registry 過期→強制 block | 有（同一 if 內） | 有 | 有 | 有（獨立 if，順序在掃描之後） | 有（獨立 if，順序在掃描之後） |
| Registry 到期紅字警告 | 有 | 有 | 有 | 有 | **無** |
| 進場 gate 含 `Manual_Kill_Switch = False` | **無** | **無** | **無** | 有 | 有 |
| 進場 gate 含 `v_Registry_Expired = False` | **無**（靠 Holiday_Block 傳遞） | 有 | 有 | 有 | 有 |
| 出場單型別（全 P0 分支） | market | Market | Market | Market | market |
| Settlement 判定邏輯 | 5 支完全相同（DayOfWeek=3 且 DayOfMonth 15~21） | 同 | 同 | 同 | 同 |

---

## A. Holiday registry 資料表（5 支完全相同）

### A-1. 完整日期清單（63 筆，民國曆 YYYMMDD，YYY = 西元年 - 1911 之 EL 表示法 Year-1900）

> 格式說明：EL 標準 `Date` = YYYMMDD 且 YYY = 西元年 - 1900。
> 例：`1190913` = 119 + 1900 = 2019 年 09 月 13 日。
> S16_S 檔內明文註記此格式：`S16_S_MACrossShort.pla:267`、`:408`。

| # | 值 | 西元日期 | 節日註記（取自 S3_L / S3_RPS 註解） |
|---|---|---|---|
| 1 | 1190913 | 2019-09-13 | （2019 中秋，無註解） |
| 2 | 1191010 | 2019-10-10 | （2019 國慶，無註解） |
| 3 | 1200101 | 2020-01-01 | （2020 元旦，無註解） |
| 4 | 1200121 | 2020-01-21 | CNY |
| 5 | 1200228 | 2020-02-28 | 228 |
| 6 | 1200402 | 2020-04-02 | Tomb Sweeping |
| 7 | 1200501 | 2020-05-01 | Labor Day |
| 8 | 1200625 | 2020-06-25 | Dragon Boat |
| 9 | 1201001 | 2020-10-01 | Mid-Autumn |
| 10 | 1201009 | 2020-10-09 | National Day |
| 11 | 1210101 | 2021-01-01 | 2021 New Year |
| 12 | 1210206 | 2021-02-06 | CNY |
| 13 | 1210227 | 2021-02-27 | 228 |
| 14 | 1210402 | 2021-04-02 | Tomb Sweeping |
| 15 | 1210612 | 2021-06-12 | Dragon Boat |
| 16 | 1210918 | 2021-09-18 | Mid-Autumn |
| 17 | 1211009 | 2021-10-09 | National Day |
| 18 | 1211231 | 2021-12-31 | 2022 New Year |
| 19 | 1220127 | 2022-01-27 | CNY |
| 20 | 1220226 | 2022-02-26 | 228 |
| 21 | 1220402 | 2022-04-02 | Tomb Sweeping |
| 22 | 1220430 | 2022-04-30 | Labor Day（5/2 make-up） |
| 23 | 1220603 | 2022-06-03 | Dragon Boat |
| 24 | 1220909 | 2022-09-09 | Mid-Autumn |
| 25 | 1221008 | 2022-10-08 | National Day |
| 26 | 1221231 | 2022-12-31 | 2023 New Year |
| 27 | 1230118 | 2023-01-18 | CNY |
| 28 | 1230225 | 2023-02-25 | 228 |
| 29 | 1230401 | 2023-04-01 | Tomb Sweeping |
| 30 | 1230429 | 2023-04-29 | Labor Day |
| 31 | 1230622 | 2023-06-22 | Dragon Boat |
| 32 | 1230929 | 2023-09-29 | Mid-Autumn |
| 33 | 1231007 | 2023-10-07 | National Day |
| 34 | 1231230 | 2023-12-30 | 2024 New Year |
| 35 | 1240206 | 2024-02-06 | CNY |
| 36 | 1240228 | 2024-02-28 | 228 |
| 37 | 1240404 | 2024-04-04 | Tomb Sweeping |
| 38 | 1240501 | 2024-05-01 | Labor Day |
| 39 | 1240608 | 2024-06-08 | Dragon Boat |
| 40 | 1240917 | 2024-09-17 | Mid-Autumn |
| 41 | 1241010 | 2024-10-10 | National Day |
| 42 | 1250101 | 2025-01-01 | 2025 New Year |
| 43 | 1250123 | 2025-01-23 | CNY |
| 44 | 1250228 | 2025-02-28 | 228 |
| 45 | 1250403 | 2025-04-03 | Tomb Sweeping |
| 46 | 1250501 | 2025-05-01 | Labor Day |
| 47 | 1250530 | 2025-05-30 | Dragon Boat（5/30 make-up） |
| 48 | 1250927 | 2025-09-27 | Teachers Day（9/29 make-up） |
| 49 | 1251004 | 2025-10-04 | Mid-Autumn |
| 50 | 1251010 | 2025-10-10 | National Day |
| 51 | 1251024 | 2025-10-24 | Retrocession Day |
| 52 | 1251225 | 2025-12-25 | Constitution Day |
| 53 | 1260101 | 2026-01-01 | 2026 New Year |
| 54 | 1260212 | 2026-02-12 | CNY：final trading day 2/11 |
| 55 | 1260227 | 2026-02-27 | 228：2/27 make-up, eve 2/26 |
| 56 | 1260403 | 2026-04-03 | Children/Tomb 4/3-4/6, eve 4/2 |
| 57 | 1260501 | 2026-05-01 | Labor Day 5/1-5/3, eve 4/30 |
| 58 | 1260619 | 2026-06-19 | Dragon Boat 6/19-6/21, eve 6/18 |
| 59 | 1260925 | 2026-09-25 | Mid-Autumn + Teachers 9/25-9/28, eve 9/24 |
| 60 | 1261009 | 2026-10-09 | National Day 10/9-10/11, eve 10/8 |
| 61 | 1261024 | 2026-10-24 | Retrocession 10/24-10/26, eve 10/23 |
| 62 | 1261225 | 2026-12-25 | Constitution 12/25-12/27, eve 12/24 |
| 63 | 1270101 | 2027-01-01 | 2027 New Year 1/1-1/3, eve 12/31 |

**語意**（引自 `S3_VolSqueezeLong.pla:181-182`）：
`Holiday_Tail` = 最後交易日 + 1 個日曆日 = 該夜盤段所蓋的日期戳記。
亦即這是「休市前最後一段夜盤（00:00-05:00 那半段）」的日期，不是節日本身第一天。

### A-2. 一致性物理驗證

以 script 抽出 5 支全部 `Holiday_Tail[n] = value` 賦值、正規化排序後比對：

```
S1_NightMomentum:      63 entries, md5=664638980cb2
S3_VolSqueezeLong:     63 entries, md5=664638980cb2
S3_S_VolSqueezeShort:  63 entries, md5=664638980cb2
S3_RapidPullbackShort: 63 entries, md5=664638980cb2
S16_S_MACrossShort:    63 entries, md5=664638980cb2
```
5 支兩兩 `diff` 全部無差異。**索引與值 100% 相同。**
（差異僅在排版：S1/S16_S 一行兩筆且無節日註解；S3_L/S3_S/S3_RPS 一行一筆，S3_L/S3_RPS 有節日註解，S3_S 無註解。）

### A-3. 陣列宣告與填表位置

| 策略 | `arrays:` 宣告 | 填表區塊 | 備註 |
|---|---|---|---|
| S1 | `S1_NightMomentum.pla:240-241` | `:247-281` | 陣列區只有 Holiday_Tail 一個 |
| S3_L | `S3_VolSqueezeLong.pla:174-175` | `:185-267`（SECTION 4） | 同上 |
| S3_S | `S3_S_VolSqueezeShort.pla:403-405` | `:413-495`（SECTION 4） | 陣列區另含 `BW_History[150](0)` |
| S3_RPS | `S3_RapidPullbackShort.pla:251-252` | `:261-342`（SECTION 0） | 同上 |
| S16_S | `S16_S_MACrossShort.pla:359-360` | `:372-406`（SECTION 3） | 同上 |

5 支全部用 `if CurrentBar = 1 then begin ... end;`，**沒有任何一支用 `once`**。
陣列宣告大小一律 80，實際只填 1~63，索引 64~80 保持初值 0。

---

## B. Holiday 判定與出場（逐檔差異）

### B-1. 掃描時間條件（重點：兩派）

| 策略 | 程式碼 | 行號 |
|---|---|---|
| S1 | `if Time <= 500 then begin` | `S1_NightMomentum.pla:285` |
| S3_L | `if Time < 500 then begin` | `S3_VolSqueezeLong.pla:279` |
| S3_S | `if Time < 500 then begin` | `S3_S_VolSqueezeShort.pla:505` |
| S3_RPS | `if Time < 500 then begin` | `S3_RapidPullbackShort.pla:352` |
| S16_S | `if Time <= 500 then begin` | `S16_S_MACrossShort.pla:415` |

**與任務前提一致**：S3_L / S3_S / S3_RPS 用 strict `<`；S1 / S16_S 用 `<=`。

S3_L 檔內對 strict `<` 有明確設計理由（`S3_VolSqueezeLong.pla:272-273`）：
「avoid Time=500 cross-holiday fill」，並註明是承襲 S1 v2.3 的架構規則。
但 **S1 現行程式碼實際是 `<=`**（`:285`），與 S3_L 註解引述的「S1 規則」相反 → 註解已過時或 S1 後續被改回。標為 `[不確定]`（見 §E）。

S3_L 檔頭 `:58` 寫「holiday tail detection at Time<=500」，與其實際程式碼 `Time < 500`（`:279`）不一致 —— **檔頭註解與程式碼矛盾**。

### B-2. 掃描迴圈邊界

5 支完全相同：`for hidx = 1 to 80 begin  if Date = Holiday_Tail[hidx] then v_Holiday_Block = True; end;`
- 迴圈跑滿 80，不是 63 → 索引 64~80 比對 `Date = 0`，永不成立，無害但每根 K 棒多跑 17 次無效比對。
- 5 支都沒有 early-break。
- 比對用 `=` 精確相等，不是區間。
- `hidx` 在 5 支全部宣告於 `variables:`（S1 `:218`、S3_L 見 variables 區、S3_S `:355`、S3_RPS `:228`、S16_S `:356`）。

### B-3. Registry 過期升級為 Holiday block

| 策略 | 寫法 | 行號 |
|---|---|---|
| S1 | `if Date > Registry_Valid_Until then begin v_Registry_Expired = true; v_Holiday_Block = true; end;` | `:294-297` |
| S3_L | 同上（大寫 True） | `:288-291` |
| S3_S | 同上 | `:514-517` |
| S3_RPS | 同上 | `:361-364` |
| S16_S | **拆成兩段**：`:409-411` 先算 `v_Registry_Expired`（在掃描之前），`:423-424` 再 `if v_Registry_Expired = True then v_Holiday_Block = True;`（在掃描之後） | `:409-411`, `:423-424` |

S16_S 的**執行順序不同**：先算 Registry → 再掃 Holiday（`v_Holiday_Block = False` 重設在 `:414`）→ 再把 Registry 過期升級為 block。
其餘 4 支：先掃 Holiday → 再算 Registry 並升級。
**淨效果相同**（因為 S16_S 的 `v_Holiday_Block = False` 重設在 Registry 計算之後、升級之前），但抽模組時順序不可隨意合併。

### B-4. 出場條件與時間上界

| 策略 | P0-3 出場條件（原文精簡） | 行號 | 有效時間窗 |
|---|---|---|---|
| S1 | `else if v_Holiday_Block and Time >= Holiday_Flat_Time then sell ("LX_NM_Holiday") next bar at market` | `:431-432` | [415, 500]（上界由 `v_Holiday_Block` 的 `Time<=500` 傳遞） |
| S3_L | `( v_Holiday_Block = True ) and ( Time >= Holiday_Flat_Time ) and ( Time <= 455 )` | `:480-486` | [415, 455] |
| S3_S | 同結構 | `:967-974` | [415, 455] |
| S3_RPS | 同結構 | `:755-762` | [245, 455] |
| S16_S | `ExitFired = 0 and v_Holiday_Block = True and Time >= Holiday_Flat_Time` | `:617-621` | [415, 500] 閉區間（上界由掃描的 `Time<=500` 傳遞） |

**出場標籤名稱（5 支全不同）**：
- S1：`LX_NM_Kill` / `LX_NM_RegistryEnd` / `LX_NM_Holiday` / `LX_NM_Settlement`（`:428,430,432,434`）
- S3_L：`LX_VS_Kill` / `LX_VS_RegistryEnd` / `LX_VS_HolFlat` / `LX_VS_Settlement`（`:469,475,484,492`）
- S3_S：`SX_VS_Kill` / `SX_VS_RegistryEnd` / `SX_VS_HolFlat` / `SX_VS_Settlement`（`:957,963,972,980`）
- S3_RPS：`SX_RPS_v2_Kill` / `SX_RPS_v2_RegistryEnd` / `SX_RPS_v2_HolFlat` / `SX_RPS_v2_Settlement`（`:745,751,760,768`）
- S16_S：`SX_MA_Kill` / `SX_MA_Registry` / `SX_MA_Holiday` / `SX_MA_Settlement`（`:608,613,619,625`）
  註：S16_S 的 registry 標籤是 `SX_MA_Registry`（**沒有 `End` 字尾**），與其餘 4 支的命名慣例不同。

### B-5. 進場封鎖寫在哪

| 策略 | 位置 | 條件內容 |
|---|---|---|
| S1 | `S1_NightMomentum.pla:406-408` | `v_Holiday_Block = false and v_Settlement_Day = false`（**缺 `v_Registry_Expired`、缺 `Manual_Kill_Switch`**） |
| S3_L | `S3_VolSqueezeLong.pla:431-437` | `v_Holiday_Block` / `v_Settlement_Day` / `v_Registry_Expired`（**缺 `Manual_Kill_Switch`**） |
| S3_S | `S3_S_VolSqueezeShort.pla:909-922` | 同 S3_L（**缺 `Manual_Kill_Switch`**）；整段包在 `if BarStatus(2) = 2 then` 內 |
| S3_RPS | `S3_RapidPullbackShort.pla:698-710` | 四項齊全，含 `( Manual_Kill_Switch = False )`（`:708`，v2.0.6 CB-1 修補） |
| S16_S | `S16_S_MACrossShort.pla:562-569`（主進場）、`:580-591`（Re-Entry） | 四項齊全，兩處都含 `Manual_Kill_Switch = False` |

**S1 的特別之處**：進場 gate 沒有 `v_Registry_Expired = false`，但因為 `:296` 把 registry 過期升級成 `v_Holiday_Block = true`，實際上被傳遞封鎖。抽模組時若拆開這個耦合，S1 進場行為會改變。

**Kill Switch 進場漏洞**：S1 / S3_L / S3_S 三支的進場 gate 都**沒有** `Manual_Kill_Switch = False`。
S3_RPS 檔內 `:980-983` 明確記載這是已知 bug（CB-1）：
Kill Switch 開啟 → P0-1 平倉 → MP=0 → 下一根進場條件成立 → 又進場 → 無限循環。
S3_RPS 與 S16_S 已修，S1 / S3_L / S3_S **未修**。

### B-6. `Holiday_Flat_Time` 預設值 vs K 棒週期

| 策略 | `Holiday_Flat_Time` | Data1 週期 | 有效時間窗 | 窗內是否存在 K 棒收盤點 |
|---|---|---|---|---|
| S1 | 415（`:181`） | **15M**（檔頭 `:5` `{Timeframe: 15-min on TXF1}`） | [415,500] | **是**（15M 網格必含 04:15/04:30/04:45/05:00） |
| S3_L | 415（`:120`） | **60M**（檔頭 `:8` `Data1 = 60M (sole feed)`） | [415,455] | **高風險：很可能否** — 見 §D-3 |
| S3_S | 415（`:237`） | **1M**（檔頭 `:85,:90`） | [415,455] | 是（41 根 1M 收盤） |
| S3_RPS | **245**（`:132`） | **5M**（檔頭 `:8`） | [245,455] | 是（機械上成立；但設計上不可達，見 §D-2） |
| S16_S | 415（`:269`） | **5M**（檔頭 `:166,:211`） | [415,500] | 是 |

---

## C. Priority-0 鏈結構

### C-1. S1_NightMomentum — `if / else if` 鏈，無 `ExitFired`

位置：`S1_NightMomentum.pla:425-435`（全檔 484 行，位於進場之後、SL/TP 之前）

```
if MarketPosition = 1 then begin
    if Manual_Kill_Switch then                        sell ("LX_NM_Kill")
    else if v_Registry_Expired then                   sell ("LX_NM_RegistryEnd")
    else if v_Holiday_Block and Time >= Holiday_Flat_Time then  sell ("LX_NM_Holiday")
    else if v_Settlement_Day and Time >= Settlement_Flat_Time then sell ("LX_NM_Settlement");
end;
```
- 順序：Kill → Registry → Holiday → Settlement ✓（符合 Rule #11）
- **互斥由 `else if` 語法保證，沒有 `ExitFired` 旗標**（S1 全檔無此變數）
- 沒有 `end;` 包住各分支 → 每個分支只有單一 statement
- 出場單型別：全部 `next bar at market`
- **與其餘 4 支結構完全不同**，抽模組時 S1 必須改寫成旗標式，或模組須支援兩種型式

### C-2. S3_VolSqueezeLong — 獨立 `if` + `ExitFired`

位置：`S3_VolSqueezeLong.pla:443-523`（SECTION 11，全檔 542 行，接近檔尾）

```
ExitFired = 0;                                  { :463 - 在 if MarketPosition 之外 }
if MarketPosition = 1 then begin
    P0-1  if (ExitFired = 0) and (Manual_Kill_Switch = True)          -> ExitFired = 1  { :468-471 }
    P0-2  if (ExitFired = 0) and (v_Registry_Expired = True)          -> ExitFired = 1  { :474-477 }
    P0-3  if (ExitFired = 0) and (v_Holiday_Block = True)
             and (Time >= Holiday_Flat_Time) and (Time <= 455)        -> ExitFired = 1  { :480-486 }
    P0-4  if (ExitFired = 0) and (v_Settlement_Day = True)
             and (Time >= Settlement_Flat_Time)                       -> ExitFired = 1  { :489-494 }
    if ExitFired = 0 then begin  ... S-1 TP / S-2 Mid / S-3 TimeStop / S-4 Frozen SL ... end;
end;
```
- 4 個分支全部設 `ExitFired = 1`
- `ExitFired = 0` 重設在 `if MarketPosition` **之外**（`:463`）→ 每根 K 棒都重設
- 出場單型別：4 個 P0 分支全部 `sell(...) next bar at Market`
- 注意 S-1 TP（`:500`）位於 `if ExitFired = 0 then begin` 內但**不設** `ExitFired = 1` → limit 單每根都重掛，是刻意設計

### C-3. S3_S_VolSqueezeShort — 獨立 `if` + `ExitFired`（+ P0.5 額外層）

位置：`S3_S_VolSqueezeShort.pla:938-1100+`（SECTION 11，全檔 1142 行）

```
ExitFired = 0;                                  { :951 }
if MarketPosition = -1 then begin
    P0-1  Manual_Kill_Switch          -> buy to cover ("SX_VS_Kill")         { :956-959 }
    P0-2  v_Registry_Expired          -> buy to cover ("SX_VS_RegistryEnd")  { :962-965 }
    P0-3  v_Holiday_Block + [415,455] -> buy to cover ("SX_VS_HolFlat")      { :968-974 }
    P0-4  v_Settlement_Day + >=1230   -> buy to cover ("SX_VS_Settlement")   { :977-982 }
    ---- Layer 2 SP tracking（peak/arm/tiered floor）  { :984-1008 }
    P0.5  SP Armed Priority Fire      -> "SX_VS_SP_Armed"                    { :1025-1032 }
    S-0   1M_Exit                     -> "SX_VS_1M_Exit"                     { :1035-1040 }
    S-1..S-4                                                                  { :1043+ }
end;
```
- P0-1~P0-4 與 S3_L **結構與時間窗完全相同**，只差 `buy to cover` vs `sell` 與標籤前綴
- **獨有**：P0-4 與 S-0 之間插入 SP 追蹤與 P0.5 分支；抽模組時 P0 區塊與 SP 區塊之間不能有耦合假設
- 另有 `v_1M_ExitFired` 旗標（`:360`, `:737`, `:891`, `:1037`），與 `ExitFired` 是**兩個不同變數**

### C-4. S3_RapidPullbackShort — 獨立 `if` + `ExitFired`（+ P0a 日盤強平）

位置：`S3_RapidPullbackShort.pla:713-818`（SECTION 7，全檔 995 行）

```
ExitFired = 0;                                  { :733 }
{ CB-2: 引擎停損偵測，v_Prev_MP = -1 且 MP = 0 -> v_DailyCooldown_Active = True }  { :738-739 }
if MarketPosition = -1 then begin
    P0-1  Manual_Kill_Switch                 -> "SX_RPS_v2_Kill"         { :744-747 }
    P0-2  v_Registry_Expired                 -> "SX_RPS_v2_RegistryEnd"  { :750-753 }
    P0-3  v_Holiday_Block + [245,455]        -> "SX_RPS_v2_HolFlat"      { :756-762 }
    P0-4  v_Settlement_Day + >=1230          -> "SX_RPS_v2_Settlement"   { :765-770 }
    P0a   Time >= 1325 and Time <= 1340      -> "SX_RPS_v2_DayClose"     { :773-778 }
    S-1..S-3                                                              { :781-816 }
end;
if ExitFired > 0 then v_DailyCooldown_Active = True;   { :827-829 }
```
- **獨有 P0a 分支**（日盤 13:25 強制平倉，`Daily_Flat_Time` = 1325，配對上界 1340）
- **獨有**：`ExitFired > 0` 會觸發當日冷卻（`:827-829`）→ 抽模組後若 P0 出場不再寫同一個 `ExitFired`，冷卻機制會失效
- 出場單型別：全部 `BuyToCover(...) next bar at Market`

### C-5. S16_S_MACrossShort — 獨立 `if` + `ExitFired`（+ P0.5 Tail Force Exit）

位置：`S16_S_MACrossShort.pla:594-770+`（SECTION 10，全檔 771 行）

```
if MarketPosition = -1 then begin
    ExitFired = 0;                          { :601 - 在 if MarketPosition 之內！}
    v_BarsSince / v_Loss / v_Profit         { :602-604 }
    P0    if Manual_Kill_Switch = True                   -> "SX_MA_Kill"        { :607-610 }
          if ExitFired = 0 and v_Registry_Expired        -> "SX_MA_Registry"    { :612-615 }
          if ExitFired = 0 and v_Holiday_Block
             and Time >= Holiday_Flat_Time               -> "SX_MA_Holiday"     { :617-621 }
          if ExitFired = 0 and v_Settlement_Day
             and Time >= Settlement_Flat_Time            -> "SX_MA_Settlement"  { :623-627 }
    P0.5  if ExitFired = 0 and Time >= Tail_ForceExit_Time and Time <= 500
                                                          -> "SX_MA_TailFlat"   { :635-639 }
    P1..P7 ...                                                                  { :642-770 }
end;
```
- **`ExitFired = 0` 重設在 `if MarketPosition = -1` 之內**（`:601`），與 S3_L/S3_S/S3_RPS（在外面）不同。無部位時 `ExitFired` 保留上一根的值 → 其餘程式若在無部位時讀 `ExitFired` 會拿到殘值。本檔未見此類讀取，但抽模組時是行為差異點。
- **P0-1 沒有 `ExitFired = 0` 前置條件**（`:607`，因為是第一個分支）；其餘三個有。
- **獨有 P0.5 Tail Force Exit**（`Tail_ForceExit_Time` = 440，`:280`），註解 `:629-634` 明說「Holiday flat at 0415 fires earlier as backstop」。
- P0-3 **沒有** `Time <= 455`，上界完全依賴 `v_Holiday_Block` 的 `Time <= 500` 傳遞。
- 出場單型別：全部 `buy to cover(...) next bar at market`

### C-6. Settlement 判定邏輯 — 5 支逐字相同

```
v_Settlement_Day = ( DayOfWeek( Date ) = 3 ) and ( DayOfMonth( Date ) >= 15 ) and ( DayOfMonth( Date ) <= 21 );
```
| 策略 | 行號 |
|---|---|
| S1 | `:300-302` |
| S3_L | `:294-296` |
| S3_S | `:520-522` |
| S3_RPS | `:367-369` |
| S16_S | `:427-429` |

差異僅為空白排版。5 支全部用**日曆推算**（當月第 3 個週三），**沒有任何一支查國定假日修正表**。
→ 這與 memory rule `feedback_settlement_holiday_rule`（推算結算日永遠要驗國定假日）有結構性衝突：
若第 3 個週三適逢國定假日，期交所結算日會提前/順延，5 支全部會抓錯日期。列為抽模組時必須決策的項目（**本次唯讀，未修改**）。

---

## D. 相依性 + 重點查證 1~5

### D-1. 查證 1：S1 是純夜盤策略，是否「天然豁免」？

**結論：S1 有完整實作，不是簡化版，不是沒有。**
- Registry 陣列存在且 63 筆完整（`:240-281`）
- Holiday / Registry / Settlement 判定完整（`:283-315`）
- P0 出場鏈完整 4 分支（`:425-435`）
- 唯一結構差異：用 `if/else if` 而非 `ExitFired` 旗標

**但「天然豁免」的說法在行為上大致成立**，理由：
- S1 有 `LX_NM_Time` 強制出場：`if Time >= ExitTime and Time < NightOpen then sell("LX_NM_Time") next bar at market`（`:472-475`，`ExitTime` = 500）→ 每日 05:00 必平倉，永遠不留倉過夜/過假日。
- 因此 `LX_NM_Holiday`（[415,500]）只比 `LX_NM_Time`（>=500）早 45 分鐘觸發，是「提早 45 分鐘平倉」而非「防止跨假日留倉」。
- 實務價值仍在：假日尾盤流動性極差，提早 45 分鐘出場可避開最後一段掃單。

**抽模組風險**：若模組統一改成「只在 [415,455] 觸發」，S1 會失去 [455,500] 這段窗口 —— 但因 `LX_NM_Time` 在 500 接手，淨影響僅為「45 分鐘窗口縮成 40 分鐘」，不會造成留倉。

### D-2. 查證 2：S3_RPS 是純日盤，`Holiday_Flat_Time = 245` 有意義嗎？

**結論：機械上可觸發，設計上永遠不可達 —— 是死碼，但為無害死碼。**

證據鏈：
- 進場時間窗：`Time >= Entry_Open_Time (850)` and `Time <= Entry_Cutoff_Time (1230)`（`:702-703`；input 值 `:127-128`）
- 日盤強平：`Time >= Daily_Flat_Time (1325)` and `Time <= 1340` → `SX_RPS_v2_DayClose`（`:773-778`；input 值 `:129`）
- 時間停損：`Max_Bars_TimeStop = 27` × 5M = 135 分鐘（`:126`）→ 最晚進場 12:30 + 135 分 = 14:45，但 13:25 的 P0a 先觸發
- 引擎停損 `SetStopLoss`（SECTION 5）獨立生效

→ 部位最晚在 13:25~13:40 之間必平，**絕不可能存活到隔日 02:45**。
`Holiday_Flat_Time = 245` 與 `Time <= 455` 這條 P0-3 分支對 S3_RPS 而言是**不可達分支**。

**為何值是 245 而非 415**：檔內註解 `:132` 寫「02:45 holiday tail flat retry start」，看起來是從某個留倉策略沿用而來的「retry 起點」語意（比 415 更早開始重試平倉），非日盤策略需求。標為 `[不確定]` — 未找到說明此數值選擇的設計文件（本次未查 docs/）。

**抽模組風險**：若模組統一 `Holiday_Flat_Time = 415`，S3_RPS 行為不變（兩者都不可達）。這是唯一可以安全統一的一支。

### D-3. 查證 3：時間值 vs K 棒週期相容性（逐支判定）

| 策略 | 週期 | 窗 | 判定 |
|---|---|---|---|
| **S1** | 15M | [415, 500] | **相容**。15M 網格無論錨在 15:00 還是 08:45，都會產生 04:15 / 04:30 / 04:45 / 05:00 收盤點。 |
| **S3_L** | **60M** | [415, 455] | **高風險 — 很可能永不觸發（死碼）** |
| **S3_S** | 1M | [415, 455] | **相容**。41 根 1M 收盤全落在窗內。 |
| **S3_RPS** | 5M | [245, 455] | **網格相容**（02:45、02:50…04:55 皆為 5M 收盤點），但設計上不可達（見 D-2）。 |
| **S16_S** | 5M | [415, 500] | **相容**。04:15…05:00 共 18 根 5M 收盤點。 |

**S3_L 詳細推導（本清單最重要的單一發現）**：
- S3_L Data1 = 60M 單一 feed（檔頭 `:8`）→ 出場鏈每小時只評估一次
- 有效窗 [415, 455] 寬度 41 分鐘 < 60 分鐘 → 窗內**最多**只能有一個 60M 收盤點，而且必須恰好落在 04:15–04:55
- TXF1 夜盤 15:00 開盤，MC 的 session-aligned 60M 網格收盤點為 16:00, 17:00, …, 04:00, 05:00 → **04:15–04:55 之間無任何收盤點**
- 佐證：S3_RPS 檔頭 `:592-598` 明文說明 MC12 的 TXF1 60M 是 **session-aligned**（日盤 08:45 開 → 收在 09:45/10:45/…），亦即網格錨在 session 開盤時刻。夜盤 15:00 開 → 收在整點。
- → 若夜盤 60M 錨在 15:00，**`LX_VS_HolFlat` 永不觸發**

**後果嚴重性**：S3_L 是本次 5 支中**唯一沒有任何每日強制平倉機制**的策略（S1 有 05:00 `LX_NM_Time`；S3_RPS 有 13:25 `DayClose`；S16_S 有 04:40 `TailFlat`；S3_S 有 1M 五層 + SP）。S3_L 只有 `MaxBars` 時間停損（70 根 60M ≈ 5 個交易日）。假日尾盤 P0-3 若死碼，S3_L 就會**帶著部位穿越整個連假**，正是任務描述的災難模式。

`[不確定]` 保留：實際 60M 收盤時間戳取決於使用者 MC12 的 session template 設定。若 template 讓夜盤 60M 收在 04:45（例如全 24h 連續、錨在 08:45），則窗內有 1 個收盤點、P0-3 可觸發。**建議物理驗證**：在 MC12 開 S3_L 的 60M 圖，用 Print 或觀察 K 棒，確認 04:xx 那根的 `Time` 值。

**同樣邏輯下的次要觀察**：S3_L 的掃描條件 `Time < 500` 在 60M 網格上只有 Time = 100/200/300/400（及 2400 若存在）會落入，`Time = 500`（04:00–05:00 那根）被 strict `<` 排除。若改成 `<=`，S3_L 在 Time=500 那根就能同時滿足 block 與（`Time <= 455` 移除後的）出場。這是抽模組時最直接的修正方向，但**本次唯讀，未修改**。

### D-4. 查證 4：閉區間紀律 —— 所有 `Time >=` 條件配對稽核

依 `docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` 條款 7/8 精神，逐一列出。
分類：**已配對**（有明確 `Time <=`）／**狀態守衛**（靠 flag 傳遞上界）／**未配對**（無上界，需人工判定）

#### S1_NightMomentum
| 行號 | 條件 | 判定 |
|---|---|---|
| `:367` | `v_IsNightSession = (Time >= NightOpen) or (Time < ExitTime)` | 跨午夜 OR 定義，本身即完整區間 → **安全** |
| `:370` | `if Time >= NightOpen and Time[1] < NightOpen` | 邊緣偵測，由 `Time[1]` 條件收斂 → **安全** |
| `:431` | `Time >= Holiday_Flat_Time` | **狀態守衛**（`v_Holiday_Block` 需 `Time<=500`）→ 有效上界 500 |
| `:433` | `Time >= Settlement_Flat_Time` (1230) | **未配對** ⚠ 見下 |
| `:472` | `Time >= ExitTime and Time < NightOpen` | **已配對** [500, 1500) |

#### S3_VolSqueezeLong
| 行號 | 條件 | 判定 |
|---|---|---|
| `:482-483` | `Time >= Holiday_Flat_Time and Time <= 455` | **已配對** |
| `:491` | `Time >= Settlement_Flat_Time` (1230) | **未配對** ⚠ |

#### S3_S_VolSqueezeShort
| 行號 | 條件 | 判定 |
|---|---|---|
| `:653` | `Time >= NightSL_Start_Time or Time < NightSL_End_Time` | 跨午夜 OR → **安全** |
| `:970-971` | `Time >= Holiday_Flat_Time and Time <= 455` | **已配對** |
| `:979` | `Time >= Settlement_Flat_Time` (1230) | **未配對** ⚠ |

#### S3_RapidPullbackShort
| 行號 | 條件 | 判定 |
|---|---|---|
| `:556` | `( Date <> v_DaySess_HighDate ) and ( Time >= Entry_Open_Time )` | **未配對** ⚠ 但由 `Date <>` 收斂為「每日第一根 >= 08:50 的棒」；夜盤 15:00 起 Date 已換日 → 夜盤第一根（15:05）會重設 `v_DaySess_High` = 該根 High。**行為疑點，非直接爆炸**（見下） |
| `:561` | `Time >= Entry_Open_Time and Time <= 1345` | **已配對** |
| `:637` | `if Time >= Entry_Open_Time`（在 `if Date <> v_LastSeenDate` 內） | **未配對** ⚠ 同上，夜盤 Time>=850 亦成立（如 15:05、22:30）→ 冷卻可能在夜盤被提早解除。檔內 `:633-635` 註解宣稱此 gate 是「防止同交易日深夜再進場繞過 gate」，但 `Time >= 850` 在夜盤同樣為真。**與註解意圖不符** ⚠ |
| `:758-759` | `Time >= Holiday_Flat_Time and Time <= 455` | **已配對** |
| `:767` | `Time >= Settlement_Flat_Time` (1230) | **未配對** ⚠ |
| `:774-775` | `Time >= Daily_Flat_Time and Time <= 1340` | **已配對** |

註：S3_RPS `:855-867` 有一段自我稽核註解，宣稱「No bare Time>=X without a pair or a state-guard」，但該註解**沒有列入** `:556` 與 `:637` 這兩處。**檔內自稽清單不完整。**

#### S16_S_MACrossShort
| 行號 | 條件 | 判定 |
|---|---|---|
| `:565`, `:585` | `( Time <= Tail_LastEntry_Time or Time > 500 )` | 跨午夜 OR → **安全** |
| `:618` | `Time >= Holiday_Flat_Time` | **狀態守衛**（`v_Holiday_Block` 需 `Time<=500`）→ 有效上界 500 |
| `:624` | `Time >= Settlement_Flat_Time` (1230) | **未配對** ⚠ |
| `:636` | `Time >= Tail_ForceExit_Time and Time <= 500` | **已配對** |

#### ⚠ 未配對總結（共 7 處，跨 5 支）

**共通型 —— Settlement（5 支全中，5 處）**：
`S1:433` / `S3_L:491` / `S3_S:979` / `S3_RPS:767` / `S16_S:624`
`Time >= 1230` 只由 `v_Settlement_Day`（純日期判定，與時間無關）守衛，**沒有時間上界**。
在 MC 24 小時制下，結算日當天 12:30 ~ 23:59 全部為 true，**包含夜盤 15:00-23:59**。
這正是憲章條款 7/8 記載的失效型態（`Time >= 1200` 夜盤全 true）。

實務衝擊評估（逐支）：
- S1：結算日夜盤不會有部位（進場 gate 有 `v_Settlement_Day = false`），且前一夜留倉在 05:00 已平 → **實務無害，結構違規**
- S3_L：進場 gate 有 `v_Settlement_Day = false`，但 S3_L **可留倉數日**。結算日「之前」進場的部位，在結算日 12:30 被平掉 —— 這是預期行為。夜盤 15:00 之後 `v_Settlement_Day` 仍為 true（Date 仍是結算日）→ 若 12:30~13:45 未成交（60M 網格只有 12:45? / 13:45 收盤），15:00 之後才成交 → 平倉時點漂移。**中度風險** `[不確定]`
- S3_S：同 S3_L 但 Data1=1M，12:30 那根即觸發 → **實務無害**
- S3_RPS：13:25 P0a 必平 → **實務無害**
- S16_S：Data1=5M，12:30 即觸發 → **實務無害**

**S3_RPS 專屬（2 處）**：`:556`、`:637` —— `Time >= Entry_Open_Time (850)` 在夜盤同樣成立。
`:637` 的冷卻解除邏輯與其註解意圖（`:633-635`）不一致。**這不屬於行事曆模組範圍，但在同一稽核清單內發現，一併記錄。**

### D-5. 查證 5：多 data stream 的日期陷阱

| 策略 | Registry 判定用哪個 stream 的 Date | 出場單掛在哪個節奏 | 判定 |
|---|---|---|---|
| S1 | `Date`（裸寫 = **Data1 = 15M**），`:287,294,300` | Data1（15M） | **一致**。data2/data3 僅在 `TrendFilterMode >= 2` 時用於 MA，與行事曆無關。 |
| S3_L | `Date`（裸寫 = **Data1 = 60M**），`:281,288,294` | Data1（60M） | **一致**（單一 feed，無跨 stream 問題） |
| S3_S | `Date`（裸寫 = **Data1 = 1M**），`:507,514,520` | **Data1（1M）** —— 出場鏈 `:953` `if MarketPosition = -1` 無 `BarStatus(2)` 包裹 | **一致（判定與出場同為 Data1）**，但**與進場不一致**：進場包在 `if BarStatus(2) = 2`（`:909`，Data2 60M 收盤）內，卻用 Data1 的 `v_Holiday_Block`。在 60M 收盤瞬間，Data1 的 `Time` 與 `Date` 應等於該 60M 收盤時刻 → 實務上同值。**低風險，但抽模組時必須明確記錄「registry 一律用 Data1 日期」** |
| S3_RPS | `Date`（裸寫 = **Data1 = 5M**），`:354,361,367` | Data1（5M） | **一致**。Data2 的日期另存於 `v_LastSeenData2Date`（`:613,629`），**僅用於 60M RSI 快照，未參與行事曆判定** |
| S16_S | `Date`（裸寫 = **Data1 = 5M**），`:410,417,427` | Data1（5M） | **一致**（單一 feed） |

**結論：5 支的 Holiday / Registry / Settlement 判定全部使用 Data1 的 `Date` 與 `Time`，沒有任何一支用 `Date of Data2`。** 出場單也全部掛在 Data1 節奏上。→ **無跨 stream 時序落差**。
唯一需注意：S3_S 的進場在 Data2 節奏、出場在 Data1 節奏，行事曆 flag 在兩邊都是 Data1 值。

### D-6. 各策略專屬相依變數（抽模組時的耦合點）

| 策略 | P0 區段用到的專屬變數 | 說明 |
|---|---|---|
| S1 | 無額外；但 P0 區塊本身依賴 `MarketPosition = 1`，且**無 `ExitFired`** | 抽模組必須為 S1 新增 `ExitFired` 或保留 `else if` 型式 |
| S3_L | `ExitFired`（`:166` 宣告） | 與下游 S-1~S-4 共用 |
| S3_S | `ExitFired`（`:357`）、`v_1M_ExitFired`（`:360`）、`v_Was_1M_Stop`、`v_SP_Armed`、`v_Peak_Profit_Pts`、`v_SP_Floor_Price`、`v_SP_Retain_Dynamic`、`v_Night_Session` | P0 之後緊接 SP 追蹤，`ExitFired` 被 P0.5/S-0 連鎖使用 |
| S3_RPS | `ExitFired`（`:229`）、`v_Prev_MP`、`v_DailyCooldown_Active` | **關鍵耦合**：`if ExitFired > 0 then v_DailyCooldown_Active = True`（`:827-829`）—— P0 出場也會觸發當日冷卻 |
| S16_S | `ExitFired`（`:357`）、`v_BarsSince`、`v_Loss`、`v_Profit`（`:602-604`，在 P0 之前計算） | `ExitFired = 0` 重設位置在 `if MarketPosition` **內** |

### D-7. 各檔區段位置（供抽模組定位）

| 策略 | inputs | variables | arrays | Registry 填表 | 判定區 | 進場 gate | P0 出場 | 總行數 |
|---|---|---|---|---|---|---|---|---|
| S1 | `:180-183`, `:195` | `:214-221` | `:240-241` | `:243-281` | `:283-315` | `:406-408` | `:425-435` | 484 |
| S3_L | `:119-123` | `:159-166` | `:174-175` | `:179-267`（SEC 4） | `:270-310`（SEC 5） | `:431-437`（SEC 10） | `:443-523`（SEC 11） | 542 |
| S3_S | `:236-240` | `:350-360` | `:403-405` | `:409-495`（SEC 4） | `:498-536`（SEC 5） | `:909-922`（SEC 10） | `:938-1040+`（SEC 11） | 1142 |
| S3_RPS | `:131-135` | `:223-229` | `:251-252` | `:256-342`（SEC 0） | `:345-383`（SEC 1B） | `:698-710`（SEC 6） | `:713-818`（SEC 7） | 995 |
| S16_S | `:267-272`, `:279-280` | `:352-357` | `:359-360` | `:372-406`（SEC 3） | `:408-429`（SEC 3） | `:562-591`（SEC 9） | `:594-639`（SEC 10） | 771 |

**注意**：S16_S 把 Registry 填表與判定放在**同一個 SECTION 3**（`:364-429`），其餘 4 支拆成兩段。

### D-8. Registry 到期紅字警告（S16_S 獨缺）

4 支有：
```
if LastBarOnChart and DateToJulian(Date) >= DateToJulian(Registry_Valid_Until) - 30 then begin
    if Registry_Warn_ID < 0 then begin ... Text_New(...) ... end;
end;
```
| 策略 | 行號 | 變數宣告 |
|---|---|---|
| S1 | `:304-315` | `Registry_Warn_ID(-1)` @ `:217` |
| S3_L | `:298-310` | `Registry_Warn_ID(-1)` @ `:163` |
| S3_S | `:524-536` | `Registry_Warn_ID(-1)` @ `:354` |
| S3_RPS | `:371-383` | `Registry_Warn_ID(-1)` @ `:227` |
| **S16_S** | **無** | **無 `Registry_Warn_ID` 變數** |

→ 2027-01-01 registry 到期前 30 天，S16_S **不會顯示任何警告**。抽模組時若統一加上，S16_S 是行為新增（安全方向）。

---

## E. `[不確定]` 清單

1. **`[不確定]` S3_L 的 60M K 棒實際收盤時間戳**
   推論 04:15–04:55 之間無 60M 收盤點（因此 `LX_VS_HolFlat` 為死碼），依據是 `S3_RapidPullbackShort.pla:592-598` 對 MC12 TXF1 60M session-aligned 行為的描述 + 夜盤 15:00 開盤 → 整點收盤。
   **但實際收盤時間戳取決於使用者 MC12 的 session template**，本次唯讀無法驗證。需在 MC12 實機確認 04:xx 那根的 `Time` 值。這是本清單最高優先的待驗項。

2. **`[不確定]` S3_L 註解與 S1 程式碼矛盾**
   `S3_VolSqueezeLong.pla:272-273` 宣稱 strict `Time < 500` 是「per S1 v2.3 architectural rule」，但 S1 現行程式碼 `:285` 是 `Time <= 500`。無法判定是：(a) S1 v2.3 之後被改回 `<=`、(b) S3_L 註解一開始就寫錯、(c) 兩者指涉不同的 500。未查 S1 版本歷史（`.bak_*` 依指示未讀）。

3. **`[不確定]` S3_L 檔頭自述與程式碼不符**
   `S3_VolSqueezeLong.pla:58` 檔頭寫「holiday tail detection at Time<=500」，程式碼 `:279` 是 `Time < 500`。可能只是檔頭未同步，但也可能反映曾經的改動。

4. **`[不確定]` S3_RPS `Holiday_Flat_Time = 245` 的來源**
   註解 `:132` 只寫「02:45 holiday tail flat retry start」，未說明為何是 245 而非 415。本次未查 `docs/` 內設計文件。

5. **`[不確定]` S1 兩處「無註解」的 registry 條目語意**
   索引 1~3（1190913 / 1191010 / 1200101）在 S3_L/S3_RPS 也沒有節日註解，僅索引 4 起才有。推測為 2019 中秋 / 國慶 / 2020 元旦，但**檔內無明文**，本表已標「（無註解）」。

6. **`[不確定]` S3_L 結算日 12:30 出場的實際成交時點**
   S3_L 是 60M，`Time >= 1230` 在日盤網格上最早落在哪根（12:45？13:45？）取決於 session 錨點。若日盤 08:45 開 → 收盤點 09:45/10:45/11:45/12:45/13:45，則 12:45 那根首次滿足。與 60M 網格假設同源，一併待驗。

7. **`[不確定]` `v_Settlement_Day` 純日曆推算是否為刻意決策**
   5 支全部用「第 3 個週三」而不查國定假日。與 memory rule `feedback_settlement_holiday_rule` 衝突。本次未查 `docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` 內文，無法判定是已知取捨還是遺漏。

---

## F. 抽模組時「不可自動統一」的行為差異（風險清單）

按「統一後會改變行為」的嚴重度排序：

| # | 差異 | 涉及策略 | 統一後果 |
|---|---|---|---|
| 1 | 出場上界 `Time <= 455` 有/無 | 有：S3_L/S3_S/S3_RPS；無：S1/S16_S | 若統一加上 455，S1 失去 [455,500]（有 `LX_NM_Time` 兜底，安全）；S16_S 失去 [455,500]（有 `SX_MA_TailFlat` @ 440 兜底，安全）。**若統一移除 455，S3_L 反而被修好**（見 D-3） |
| 2 | `Holiday_Flat_Time` 415 vs 245 | S3_RPS = 245 | 統一為 415 對 S3_RPS 無影響（分支本就不可達） |
| 3 | 掃描 `<` vs `<=` | strict：S3_L/S3_S/S3_RPS；含：S1/S16_S | 統一為 `<` → S1/S16_S 在 Time=500 那根不再 block。S1 有 `LX_NM_Time`@500 兜底；S16_S 有 `TailFlat`@440 兜底 → 安全但需確認。統一為 `<=` → S3_L 在 Time=500 那根新增 block（可能是修復，見 D-3） |
| 4 | `if/else if` vs `ExitFired` 旗標 | S1 為 else-if | S1 必須改寫；改寫時若動到 `LX_NM_Time`（`:472-475`，位於 P0 之外且**不受 `ExitFired` 保護**）會產生重複下單 |
| 5 | `ExitFired = 0` 重設位置 | S16_S 在 `if MarketPosition` 內；其餘在外 | 統一移到外面，S16_S 無部位時 `ExitFired` 行為改變（本檔未見依賴，但需複檢 P1~P7） |
| 6 | `ExitFired` 觸發當日冷卻 | 僅 S3_RPS（`:827-829`） | 模組若改用自己的旗標而不寫 `ExitFired`，S3_RPS **冷卻機制會靜默失效** → 同日重複進場 |
| 7 | 進場 gate 缺 `Manual_Kill_Switch` | S1/S3_L/S3_S 缺 | 統一補上 = 修復 CB-1 bug（行為改變但方向正確） |
| 8 | 進場 gate 缺 `v_Registry_Expired` | 僅 S1 | S1 靠 `:296` 的 `v_Holiday_Block = true` 傳遞。模組若拆開此耦合，S1 進場封鎖會失效 |
| 9 | Registry 紅字警告 | S16_S 缺 | 統一補上 = 純新增（安全） |
| 10 | Registry / Holiday 計算順序 | S16_S 先 Registry 後 Holiday；其餘相反 | 淨效果相同，但 S16_S 的 `v_Holiday_Block = False` 重設位置（`:414`）必須跟著搬 |
| 11 | 出場標籤前綴 | 5 支全不同（`LX_NM_` / `LX_VS_` / `SX_VS_` / `SX_RPS_v2_` / `SX_MA_`） | 模組必須參數化標籤前綴，否則 MC 訂單追蹤與績效歸因全部斷 |
| 12 | 多做/多空方向 | S1/S3_L = long (`sell`)；S3_S/S3_RPS/S16_S = short (`buy to cover`) | 模組必須參數化方向或分兩份 |
| 13 | S3_S P0.5 / S3_RPS P0a / S16_S P0.5 | 各自獨有的額外分支 | 模組只能涵蓋 P0-1~P0-4，額外分支必須留在各策略檔內，且插入點必須在模組之後 |
