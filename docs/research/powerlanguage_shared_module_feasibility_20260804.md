---
title: PowerLanguage 共用假日模組 - 技術可行性研究
查證日期: 2026-08-04
研究對象: MultiCharts PowerLanguage（非 .NET 版）
本機環境: MultiCharts64 ProductVersion 9.0.11581.400（實測，見 §0.2）
來源類型:
  - A_官方隨機文件: PowerLanguage.chm / MultiCharts64.chm（MC 9.0 build 11581 隨附，最權威且版本精確）
  - B_官方Wiki: multicharts.com/trading-software（WebFetch 被 403 擋，僅能透過搜尋引擎摘要取得）
  - C_官方論壇: multicharts.com/discussion（同樣 403，僅能透過搜尋引擎摘要取得）
  - D_本機物理證據: C:\ProgramData\TS Support\MultiCharts64\ 實際檔案內容
  - E_第三方: TradeStation 官方 EL 文件、georgepruitt.com、tradingcode.net
證據等級標記: 【物理】= 本機實測 /【官方】= 官方文件明說 /【搜尋摘要】= 官方網頁但只拿到搜尋引擎摘要 /【推論】= 我的推理，未經證實 /【未知】= 查不到
禁止事項: 本文件為研究輸出，未修改 repo 內任何檔案
---

# PowerLanguage 共用假日模組 - 技術可行性研究

## §0 結論先行

### 0.1 一句話推薦

**做得到，而且該做：把假日表包成一支 User Function（.pln / Function study），函式內部自己宣告 `arrays:` 並在 `if CurrentBar = 1` 時填值，回傳 True/False；10 支策略各自只留一行呼叫。**
但**必須配套一條鐵律**：每次改這支 function 之後，在**每一台機器**上都要跑 `Compile → Recompile All`（Ctrl+F7），否則已掛在圖上的策略會繼續用舊版函式（見 §4.2，這是本案最大風險）。

### 0.2 本機物理證據（先講證據，再講結論）

| 事實 | 證據 |
|---|---|
| 本機 MC 版本 = 9.0.11581.400 | `(Get-Item 'C:\Program Files\TS Support\MultiCharts64\MultiCharts64.exe').VersionInfo.ProductVersion` |
| PowerLanguage 原始碼**在磁碟上是純文字檔** | `C:\ProgramData\TS Support\MultiCharts64\StudyServer\Studies\SrcEl\{Functions,Indicators,Strategies}\`，副檔名 `.elf`（function）/ `.el`（indicator/strategy），CRLF 純文字，可直接 `cat` |
| Function **可以**在內部宣告 array 並跨 bar 累積狀態 | MultiCharts 自家出貨的 `SrcEl\Functions\f_SharpeRatio.elf` 內有 `array: periods_returns[](0);` + `var: intrabarpersist last_idx(0);` + `last_idx += new_periods;`，且 `Dlls\Functions\f_SharpeRatio.dll` 存在（= 已編譯成功） |
| `once` 關鍵字在 MC 9.0 **可用但未文件化** | 同一支 `f_SharpeRatio.elf` 用了 3 次 `once`；但 `PowerLanguage.chm` 的 A-Z 關鍵字索引（`files/01_about/about03.htm`）裡 O 段只有 Of / On / OnCreate / OnDestroy / Open…，**沒有 `once`** |
| Function 的「Return Type / Function Storage / MaxBarsBack」**不存在原始碼文字裡**，是另存的 metadata | `StudyServer\Studies\graph_backup.xml`（UTF-16）每個 `<GraphNode>` 有 `<signature ObligatoryParamCount RetType StorageType/>` 與 `<StudyProperties BarRefMode BarRefValue .../>`，而 `.elf` 檔內完全沒有這些欄位 |
| 使用者現況：29 個策略檔內嵌 `Holiday_Tail` | `grep -l "Holiday_Tail" SrcEl\Strategies\*.el` → 29 檔（17 支 `s_` + 12 支 `sb_` 批次變體） |
| 現有寫法 | `arrays: Holiday_Tail[80](0);` + `if CurrentBar = 1 then begin Holiday_Tail[1] = 1190913; … Holiday_Tail[63] = 1270101; end;` + 每根 bar `for hidx = 1 to 80` 線性掃描 |

> 註：使用者說「10 支在役」，本機掃到 29 檔含同一份表。實際維護面比原估更嚴重（多出的多半是 `sb_` 批次回測變體與舊版本）。

---

## §1 子問題 1：User Function 能否持有靜態資料表？

### 1.1 Function 內可否宣告 array 並在首次呼叫時填值？

**可以。**

- 【物理】MultiCharts 出貨的 `f_SharpeRatio.elf` 就是這樣寫的：
  ```
  array: periods_returns[](0), periods_return_percent[](0);
  var: intrabarpersist last_idx(0);
  var: recalcpersist int_rate_per_period(12);
  once begin
      switch (Period) begin
          case 0 : int_rate_per_period = IntRate / 12 / 100;
      end;
  end;
  ```
  且對應的 `f_SharpeRatio.dll` 存在於 `Dlls\Functions\` → 這段語法在 MC 9.0 編得過。
- 【官方】`Array` 關鍵字文件（PowerLanguage.chm `03_words/Declaration/array.htm`）對「可用位置」沒有任何「僅限 indicator/signal」的限制字眼，語法為
  `Array: [IntraBarPersist] ArrayName[D1,D2,...](InitialValue [, DataN]), ...`，最多 9 維，索引從 0 起。
- 【官方】動態陣列以 `[]` 宣告，用 `Array_SetMaxIndex(ArrayName, MaxIndex)` 改大小（`03_words/Dynamic_Arrays/array_setmaxindex.htm`）。
- 【官方】`Fill_Array(ArrayName, Value)` 可一次填滿一維陣列（`03_words/Dynamic_Arrays/fill_array.htm`）。

### 1.2 Function 的 array 是每次呼叫重新初始化，還是跨 bar 保持狀態？

**跨 bar 保持狀態。這是 EasyLanguage/PowerLanguage 與 C/Python 最大的差異之一。**

- 【搜尋摘要 / 官方論壇】MultiCharts 論壇主題標題本身就是結論：**"Values of variables in function will be kept"**（<https://www.multicharts.com/discussion/viewtopic.php?t=52638>）。摘要內容：「Values of variables in a function will be kept no matter the function is type of simple or series.」，並附有「function 內 local variable `index` 每次 +1，畫出來的 plot 持續遞增」的範例。
- 【搜尋摘要 / 官方論壇】第二串 <https://www.multicharts.com/discussion/viewtopic.php?t=5823>（persistence scope of variables within a study）給出同方向結論。
  - ⚠ **誠實標註**：這兩筆我只拿到搜尋引擎摘要（multicharts.com 全站對 WebFetch 回 403），無法逐字驗證原文。兩串是不同 thread，但摘要有可能被搜尋引擎混寫。
- 【第三方，可獨立驗證】George Pruitt（TradeStation EL 圈的知名作者）〈Function Variable Data Survives Between Calls〉<https://georgepruitt.com/function-variable-data-survives-between-calls/>：
  - 「once you define a variable or an array in a function and start dumping stuff in them, the stuff will be remembered throughout the life of the simulation.」
  - 「When you come back into the function from the next bar of data tradeCnt and tradesArray are still there for you and most importantly still intact.」
  - 範例即 function 內 `array: tradesArray[500](0);`
- 【第三方 / TradeStation 官方】<https://help.tradestation.com/10_00/eng/tsdevhelp/elword/el_definitions/about_functions.htm>：「A series function automatically stores its own previous values and executes on every bar (even if used within a conditional statement).」
- 【物理】`f_SharpeRatio.elf` 的 `last_idx += new_periods;` 依賴跨 bar 累積才有意義。

**⚠ 未解衝突（誠實標註）**：函式的狀態是「每個呼叫點（call site）各一份」還是「整支 function 全域一份」，兩個第三方來源說法相反：
- 搜尋摘要引 markplex/Pruitt：「Each unique call to a function is calling a separate instance of that function.」
- WebFetch 對 Pruitt 那篇的摘要卻寫成「creating a single persistent instance rather than separate instances per call site」。
**我無法在本輪確定哪個對。**
→ **對本案無影響**：假日表是唯讀查表，就算每個呼叫點各存一份 63 筆 double（約 0.5 KB），也毫無成本；也不依賴跨策略共享狀態。但**如果未來想用 function 做跨策略共享的可寫狀態，必須先實測**。

### 1.3 `once` / `if CurrentBar = 1` 在 function 內的行為與 strategy 內是否相同？

- `if CurrentBar = 1`：【物理 + 官方】可用。出貨函式 `f_AB_NextColor.elf` / `f_AB_NextLabel.elf` 內含 `condition1 = ( CurrentBar of Data1 = 1 and var0 = 2 ) or var0[1] = 2;`。`CurrentBar` 在 MC 9.0 關鍵字索引中存在。
- `once`：【物理】在 MC 9.0 可編譯（`f_SharpeRatio.elf` 使用且已產出 DLL），支援 `once begin … end;` 與 `once <expr>;` 兩種形式。但**未列在 MC 9.0 的 PowerLanguage.chm 關鍵字索引**。
  → 【推論，未證實】`once` 屬「相容 TradeStation EL 但 MC 官方文件漏寫」的關鍵字。**對真金交易碼，建議用 `if CurrentBar = 1 then begin … end;`（有官方關鍵字文件背書）而不是 `once`**，避免依賴未文件化行為。
- **重要陷阱（官方明說）**：`CurrentBar = 1` 不是圖上第一根 K，而是「MaxBarsBack 之後的第一根」。官方 MultiCharts64.chm `04_PL/41-0002_Scripts.html`：「If signal script contains references to previous bars' values, signal can begin generating orders starting with the first bar that follows the Maximum number of bars a study will reference.」
- **第二個陷阱（官方明說）**：MaxBarsBack 自動偵測時，「The process of automatic MaxBarsBack detection **may cause some functions to be executed repeatedly for the first few bars** of a chart when a study is first applied」（同上）。
  → 對「純賦值、冪等」的假日表填值**無害**（重跑幾次結果一樣）。但**若把「計數器 / 累加」放進 function 的初始化區塊，就會被重複執行而算錯**。本案務必保持初始化區塊 100% 冪等。

---

## §2 子問題 2：Function 型別與回傳限制

### 2.1 Simple / Series 的差別

- 【官方】建立 function 時要選 **Return Type** 與 **Function Storage**（MultiCharts64.chm `03_PLE/31-0101_OperatingStudies.html`：「Select the Return Type. Select the Function Storage.」）。
- 【官方】Input 型別：`NumericSimple` = 「The value of an input defined as Simple is constant from bar to bar and thus **has no history**」；`NumericSeries` = 「The value of an input defined as a Series **may vary from bar to bar and can be referenced historically**」（PowerLanguage.chm `03_words/Declaration/numericsimple.htm` / `numericseries.htm`；`TrueFalseSimple` / `TrueFalseSeries` 同理）。
- 【第三方 / TradeStation 官方】Series function「automatically stores its own previous values and **executes on every bar (even if used within a conditional statement)**」。
  → 這是 Series 的關鍵語意：**即使你把它包在 `if` 裡，它每根 bar 還是會被算一次**（保證歷史連續）；Simple 則不會。

### 2.2 哪種適合「給定日期回傳是否為假日」？

**Simple（或 Auto-detect 讓它落在 Simple）。**理由：
1. 假日判定是純查表，**不需要引用自己的歷史值**（`IsHoliday(Date)[1]` 沒有意義）。
2. Series function 保證每根 bar 執行 → 額外開銷且無必要。
3. 【官方】Simple input 明說「has no history」，正好符合「只吃當根的 Date」。

**⚠ 但有一個必須注意的矛盾**：函式內部要保有「已初始化」的 array 狀態（跨 bar）。這與「Simple」的宣告是**兩回事**——Simple/Series 描述的是**回傳值與 input 的歷史語意**，不是內部變數的生命週期。
【搜尋摘要】論壇 t=52638 明說「no matter the function is type of simple or series」變數值都會保留 → 兩者可並存。
【誠實標註】此點只有單一來源直接支持（t=52638），加上 Pruitt 的間接支持。**建議實測驗證**（見 §6.3 驗收清單）。

### 2.3 能否回傳陣列？

**不能直接回傳陣列，但可以用「陣列 by reference」把資料寫回呼叫端。**

- 【官方】關鍵字索引存在 `NumericArray`、`NumericArrayRef`、`NumericRef`、`StringArrayRef`、`TrueFalseArrayRef`（PowerLanguage.chm `01_about/about.htm`、`about02.htm`、`about03.htm`、`about04.htm`）。
- 【物理】出貨函式 `f_RemoveLastZeros.elf` 就是這個用法：
  ```
  inputs:
      Array_[MaxSize]( numericarrayref ), NewLast(NumericRef);
  for value1 = MaxSize downto 1 begin
      if 0 <> Array_[value1] then break;
  end;
  NewLast = value1;
  array_setmaxindex(Array_, NewLast);
  ```
- 【物理】`f_emulate_dictionary__set_size.elf` 同樣接兩個 `NumericArrayRef`。
- 【官方 Wiki，搜尋摘要】專頁〈Passing values to and from a function〉<https://www.multicharts.com/trading-software/index.php?title=Passing_values_to_and_from_a_function>。
- 【官方】function 必須回傳單一值（TradeStation 官方：「All EasyLanguage functions must return a value」），做法是在函式內對「與函式同名的變數」賦值。

→ 本案有兩種可行架構（§6 會選一種）：
- **A. 自足查表函式**：`IsTaifexHoliday(TheDate) : TrueFalse`，表存在函式內部。策略端 1 行。
- **B. 填表函式**：`TaifexHolidayFill(HolidayArray : NumericArrayRef) : Numeric`，把表寫進策略自己宣告的陣列。策略端 2 行（宣告 + 呼叫）。

### 2.4 宣告型別對效能與 MaxBarsBack 的影響？

- 效能：【推論】Series function 每根 bar 強制執行，Simple 只在被呼叫時執行。假日表是 O(63) 線性掃描，兩者差異對 60 分鐘 K 線可忽略。**未查到官方效能數據**。
- MaxBarsBack：見 §3。

---

## §3 子問題 3：MaxBarsBack 交互作用

### 3.1 官方規則（MultiCharts64.chm `04_PL/41-0002_Scripts.html`，逐字重點）

- 「The number of previous bars that must be available for a script in order to start performing calculations is called Maximum number of bars a study will reference, or MaxBarsBack.」
- 「When detected automatically, MaxBarsBack will initially be set to **the value of the largest data offset in the study**; however, if a **variable data offset** is used in the script, the initial MaxBarsBack value may prove to be too small. In such a case, the MaxBarsBack value will **automatically be increased by 5 or by a factor of 1.618**, whichever yields a higher value, and the study recalculated.」
- 「The process of automatic MaxBarsBack detection may cause some functions to be executed repeatedly for the first few bars of a chart when a study is first applied; this can be avoided by **setting the MaxBarsBack value manually**.」

### 3.2 邏輯移進 function 後，會不會額外墊高策略的 MaxBarsBack？

- **【推論，中信心】會，但只在「function 內部有歷史引用」時才會。**
  官方說 auto-detect 取「the largest data offset **in the study**」。EasyLanguage/PowerLanguage 的 function 在編譯時是被連結進 study 的（本機證據：`SrcCpp` 有 transcode、`Dlls\Functions\*.dll` 有獨立 DLL，兩者並存），**推論**其 offset 需求會併入呼叫端的 study。
  **⚠ 我沒有找到官方直接明說「function 的 offset 會計入呼叫者 MaxBarsBack」的句子。這是推論。**
- **對本案的實際影響：零。**
  假日查表函式**沒有任何 `[n]` 歷史引用**（只吃當根的 `Date`，內部陣列是 index-based 不是 bar-offset），所以 largest data offset = 0。
  → **推論**：把現行內嵌邏輯搬進 function，不會改變任何策略的 MaxBarsBack 需求；專案的 MaxBarsBack = 100 可維持。

### 3.3 已知的「function 導致 MaxBarsBack 意外膨脹」陷阱

- 【官方】上引「variable data offset」條款：如果 function 內出現 `Close[SomeVariable]` 這種**變動 offset**，auto-detect 會低估 → 平台自動 ×1.618 或 +5 並重算，造成啟動變慢與「首幾根 bar 重複執行」。
- 【官方，本案專屬】本案的假日表**必須**確保初始化區塊冪等，否則上述「重複執行」會出錯。
- 【官方】MaxBarsBack 是**每支 study 各自的屬性**，不是全域的。本機物理證據：`graph_backup.xml` 每個 `<GraphNode>` 都有自己的 `<StudyProperties BarRefMode="…" BarRefValue="…"/>`（實測分布：`BarRefMode="1" BarRefValue="50"` 316 筆、`BarRefMode="0" BarRefValue="50"` 104 筆…）。
  【推論】`BarRefMode` 0/1 應對應「User specified / Auto-detect」，但**我沒有官方對照表，不要當事實用**。
- **⚠ 重要**：**Function 本身也有自己的 MaxBarsBack 屬性**（`f_SharpeRatio` 的節點是 `BarRefMode="0" BarRefValue="10"`）。這代表建立新 function 時，其 MaxBarsBack 設定會被存進 study database，而**這個設定不會跟著 `.el` 純文字檔走**（見 §4.3）。

---

## §4 子問題 4：部署與版本管理

### 4.1 .pln function 如何被多支策略引用？全域命名空間嗎？

- 【官方】「A Function is an independent procedure (subroutine) that **can be called from another script** to carry out a specific task.」（MultiCharts64.chm `03_PLE/31-0101_OperatingStudies.html`）
- 【物理】**是全域單一命名空間**：所有 function 平放在 `SrcEl\Functions\`（本機 232 支），`graph_backup.xml` 是**單層 431 個 `<GraphNode>` 的平坦清單，沒有任何 edge / namespace / folder 結構**（實測：XML 元素只有 `Graph` / `GraphNode` / `data` / `signature` / `StudyProperties` / `PasswordState` / `NodeText` / `PlotInfo`）。
  → **後果：函式命名衝突是真實風險**（例如取名 `IsHoliday` 可能與第三方套件撞名）。命名務必加專屬前綴，如 `TXF_IsTaifexHoliday`。
- 【官方】呼叫方式就是直接寫函式名稱，無 import / include 語句。**PowerLanguage 沒有 `#include`**（間接證據：官方關鍵字 A-Z 全索引中無任何 include/import/require 類關鍵字；只有 `External`、`DefineDLLFunc` 用於呼叫 DLL）。

### 4.2 ⚠⚠ 修改 function 後，引用它的策略需要重新編譯嗎？

**要，而且不會自動連動。這是本案最大的營運風險。**

- 【搜尋摘要 / 官方 Wiki】〈Using Studies (PowerLanguage Editor)〉<https://www.multicharts.com/trading-software/index.php?title=Using_Studies_%28PowerLanguage_Editor%29>：
  「When you change the code of a function which is used in several indicators or signals, **it is required to use the "Recompile all" option**, so that the references to this function will be renewed in all studies. … If you don't use the "Recompile all" option, **the new reference will only be applied to the studies that are not added to charts.**」
  → 白話：**已經掛在圖上的策略，若沒有 Recompile All，會繼續跑舊版假日表。** 對 live 交易 = 假日照常進場。
- 【官方】MC 9.0 隨機文件（`03_PLE/31-0103_WorkingStudies.html`）列出的編譯選項：
  - Compile（F3，只編當前視窗）
  - All Opened（Ctrl+Shift+F2）
  - All Uncompiled
  - **All Studies**（編譯電腦上所有 study）
  - All Indicators and Signals Only
  【誠實標註】MC 9.0 文件用的字是 "All Studies"，較新版 Wiki/論壇說的是 "Recompile All (Ctrl+F7)"。**MC9 的快捷鍵與選單字樣可能與 MC12 不同，請以實機選單為準。**
- 【搜尋摘要 / 官方論壇】t=50927（Primary purpose of "Compile" and "Recompile All"）補充：partial recompile 會造成「改過的 study 在新 assembly、沒改的在舊 assembly」的混用狀態。

### 4.3 跨機器同步：原始碼在磁碟是文字檔還是資料庫？

**兩者都是——這正是同步的陷阱所在。**

| 項目 | 位置 | 型態 | 能否進 git |
|---|---|---|---|
| 原始碼文字 | `C:\ProgramData\TS Support\MultiCharts64\StudyServer\Studies\SrcEl\{Functions,Indicators,Strategies}\*.elf/*.el` | **純文字（CRLF）** | ✅ 可以 |
| Transcode 中繼 | 同層 `SrcCpp\` | C++ | ❌ 不必 |
| 編譯產物 | 同層 `Dlls\`（本機 100 MB） | DLL | ❌ 不該 |
| **Study 註冊表 + 屬性**（名稱、type、RetType、StorageType、MaxBarsBack、密碼保護、是否已編譯） | `C:\ProgramData\TS Support\MultiCharts64\Databases\TSSTORAGE.GDB`（約 111 MB，二進位；另有 `FBPORTFOLIO.GDB`、`TSCACHE.GDB`） | **二進位資料庫** | ❌ 不可 |
| 上述屬性的鏡像備份 | `StudyServer\Studies\graph_backup.xml`（UTF-16，含 base64 編碼原始碼） | XML | 理論可以，但非官方介面 |

- 【搜尋摘要 / 官方論壇】社群做法一致：「MultiCharts stores plain text content of custom PowerLanguage scripts in `SrcEl`… they are simply plain text files」；有人用 git／SVN 追蹤 `SrcEl`（<https://www.multicharts.com/discussion/viewtopic.php?t=11386>、<https://www.multicharts.com/discussion/viewtopic.php?t=48239>、<https://www.multicharts.com/discussion/viewtopic.php?t=52858>）；官方 issue tracker 有 MC-1690「core powerlanguage files should be on github」為 OPEN 狀態。
- 【搜尋摘要 / 官方論壇，關鍵陷阱】t=52480（Mass Compile Strategies From Text Files）：**直接覆蓋 `SrcEl` 的檔案，PowerLanguage Editor 不會知道原始碼變了，資料庫不會被標記為 uncompiled，編譯器會拿舊的 cpp transcode 去編**。
  → **絕對不要把「直接寫 `SrcEl` 檔案」當成部署手段。** git 只能當**真相來源與 diff 工具**，實際進機器仍須走 Import / 貼進 Editor / 編譯。
- 【物理佐證】`.elf` 檔內完全沒有 Return Type / Storage / MaxBarsBack 欄位；這些只存在 `graph_backup.xml` 的 `<signature>` / `<StudyProperties>` 與 `TSSTORAGE.GDB`。
  → **git 裡的 `.elf` 純文字不足以完整重建一支 function**，新機器上第一次建立時必須「手動選對 Return Type / Function Storage」，或改用 PLA 匯入。

### 4.4 MC9 與 MC12 的 function 相容嗎？

| 格式 | 跨版本相容 | 來源 |
|---|---|---|
| **PLA**（PowerLanguage Archive，MC 原生匯出/匯入格式） | ✅ **相容**。【搜尋摘要 / 官方 KB】「after installing a new version of MultiCharts you can import desired studies from this file, and **these files work correctly with all MultiCharts versions**」（<https://www.multicharts.com/support/base/how-can-i-back-up-multicharts/>） | B |
| **XML** | ✅ MC 9.0 官方文件明列可匯入/匯出 XML | A |
| **SEF**（source-compiled 唯讀） | ❌ **鎖 build**。MC 9.0 隨機文件逐字：「**Only SEF studies created with the same version number (build) of MultiCharts can be imported!**」「Exported SEF studies can only be imported by the same version number (build) of MultiCharts!」 | A |
| **編譯後的 DLL**（`Dlls\`） | ❌【推論】絕不可跨版本複製 | — |

- **語法層**：【推論，高信心】本案要用的語法（`arrays:`、`if CurrentBar = 1`、`for … begin … end`、`inputs: (NumericSimple)`）是 MC 9.0 就有的最基本子集，MC12 必然向下相容。MC 12.0 release notes 提到的 PowerLanguage 變更只有「MidStr keyword output matches TS now」等零星項目（<https://www.multicharts.com/traders-blog/multicharts-12-0-release-2/>），沒有破壞性語言變更。
- **⚠ 一個真實已知風險**：`MidStr` 的行為在 MC12 被改成對齊 TradeStation。本案不使用 `MidStr`，但這證明「MC 版本間的 keyword 語意確實可能改變」→ **不要假設「MC9 跑得對，MC12 就一定跑得一樣」，必須在兩台機器各自跑一次驗證。**
- **⚠ 匯出/匯入操作陷阱**：【官方】匯出視窗有「**Select dependant function(s)**」勾選框——匯出策略時**務必勾選**，否則對方機器會缺少假日 function。【搜尋摘要 / 論壇 t=47311】反映 PLA 檔匯入時該勾選框會被 grey out（ELD 則不會），造成「相依 function 沒帶到」的實務問題。

---

## §5 子問題 5：四個替代方案比較

### 方案 1：外部檔案 + PowerLanguage 檔案讀取函式

| 項目 | 評估 |
|---|---|
| 可行性 | ❌ **PowerLanguage 沒有內建讀檔功能** |
| 證據 | 【官方】MC 9.0 關鍵字全索引只有 `FileAppend`（寫入/附加）、`FileDelete`（刪除）、`Print`（可導向檔案），**完全沒有任何讀檔關鍵字**。【搜尋摘要 / 論壇】「PowerLanguage Editor has the PRINT keyword to write on a file, but an instruction to read from a file is missing」「Reading from a file in PowerLanguage requires an external dll」；官方論壇還有一串投票請願〈Please VOTE: Read from File〉(t=51022) → 反證它至今不是內建功能 |
| 若硬做 | 需 `DefineDLLFunc` + 第三方 DLL（如 IOData.dll、ELCollections）。已知限制：IOData.dll 遇到超過 254 字元的行會停止讀取 |
| 維護成本 | 高：DLL 需 32/64 bit 對應、需在兩台機器各自部署、MC 升級時可能失效 |
| 失效模式 | **災難級**：live 機器上檔案路徑不存在／權限不足／DLL 沒載入 → 假日判定靜默失敗，策略在假日照常下單 |
| 適合本案？ | ❌ **不適合**。為了 63 筆一年改一次的資料，引入 DLL 依賴，風險報酬比極差 |

### 方案 2：MultiCharts Global Variables（GV）跨腳本共享

| 項目 | 評估 |
|---|---|
| 可行性 | ❌ **技術上能跑，但語意上不能用於回測** |
| 證據 | 【搜尋摘要 / 官方 Wiki】〈Global Variables〉：「Global Variables is an **external .dll file** designed to transfer values between strategies on different charts…information is stored in a shared memory space」；**「Global Variables can only work in realtime, because there's no bar linking and synchronization between studies on different charts, and it's not possible to establish this synchronization through PowerLanguage.」**【物理】MC 9.0 的 PowerLanguage.chm 關鍵字索引**沒有任何 `GV*` 關鍵字** → 確認 GV 不是內建語言功能，是外掛 DLL |
| 失效模式 | 回測歷史 bar 上 GV 沒有值 → 假日判定在回測中全部失效 → **回測與實盤結果不一致**，這對量化研究是最毒的失效模式（會污染所有績效統計） |
| 適合本案？ | ❌ **完全不適合**。假日判定必須在歷史回測中也正確 |

### 方案 3：演算法化（期交所規則 + 農曆推算）

| 項目 | 評估 |
|---|---|
| 可行性 | ⚠ 技術上做得到，但**不該做** |
| 理由 | 台股休市日 = 國定假日 + 行政院人事總處「調整放假」+ 補班日 + 颱風假 + 期交所特別公告。**其中「調整放假」與「補班」是每年由行政院公告的行政決定，沒有封閉演算法**；颱風假更是當日決定 |
| 農曆推算 | 春節可推，但「春節前後彈性放假幾天」不可推 |
| 已存在的紀律 | 使用者的 auto-memory `feedback_settlement_holiday_rule` 已記錄：**推算台指結算日永遠要驗國定假日，不可假設第三個週三即結算日** → 此方案與既有紀律直接衝突 |
| 失效模式 | 演算法自信地算出錯誤答案，且**不會報錯**。比查表缺資料更危險（查表至少可以用 `Registry_Valid_Until` 過期警示，使用者現行程式碼已經有這個機制） |
| 適合本案？ | ❌ **不適合**。且現行程式碼的「registry 過期紅字警告 + 到期後強制 Holiday_Block」設計已經是正確答案，不該退化成演算法 |

### 方案 4：維持各自內嵌，用 Python 自動產生／同步該段程式碼（code generation）

| 項目 | 評估 |
|---|---|
| 可行性 | ✅ 可行，且是**方案 A 的最佳備援 / 互補** |
| 做法 | git repo 內放 `holidays_taifex.csv`（單一真相）→ Python 產生 `HOLIDAY_BLOCK` 程式碼片段 → 以標記註解（`{ BEGIN AUTOGEN HOLIDAY }` / `{ END AUTOGEN HOLIDAY }`）在 repo 的 10 份 `.pla`/`.el` 原始碼中做區塊替換 |
| 優點 | 1. **零平台風險**：不新增 function、不改 MaxBarsBack、不需 Recompile All 連動；2. 每支策略仍 100% 自足，可單獨匯出給別人；3. git diff 看得見實際變更；4. **不需要在兩台機器同步 function metadata** |
| 缺點 | 1. 產生後**仍要人工把 10 支貼回 Editor 並編譯**（不能直接寫 `SrcEl`，見 §4.3 陷阱）；2. 每支策略檔仍多 63 行雜訊；3. 若有人手改了策略檔內的表，下次產生會被覆蓋（這其實是優點：強制單一真相） |
| 失效模式 | 產生腳本沒跑 / 只跑了一半 → 部分策略舊表。**但這是「靜默不一致」，比方案 A 的「全體用舊表」更難察覺** → 需配套：在產生的區塊內嵌入 `Registry_Valid_Until` 與版本雜湊，讓策略自己在圖上喊 |
| 適合本案？ | ✅ **適合，作為 Plan B / 過渡方案** |

---

## §6 明確推薦

### 6.1 推薦：方案 A（單一 User Function 自足查表）+ 方案 4 的 CSV 單一真相

**具體形狀：**

```
git repo (單一真相)
└── data/taifex_holidays.csv          <- 63 筆日期，人維護這一份
        │
        │  Python: gen_pl_function.py
        ▼
└── src/pl/f_TXF_IsTaifexHoliday.txt  <- 產生的 PowerLanguage function 全文（純 ASCII）
        │
        │  人工：貼進 PowerLanguage Editor -> Compile -> Recompile All
        ▼
MC9 桌機 / MC12 筆電
```

Function 骨架（示意，英文 ASCII，實作時再定案）：

```
{ f_TXF_IsTaifexHoliday - Return Type: TrueFalse, Function Storage: Simple }
{ AUTOGENERATED from data/taifex_holidays.csv - DO NOT EDIT BY HAND }
{ REGISTRY_VALID_UNTIL = 1270101 }

inputs: TheDate( NumericSimple );

arrays: HolidayTail[80]( 0 );
vars: hidx( 0 ), Found( False );

if CurrentBar = 1 then begin
    HolidayTail[1]  = 1190913;
    { ... 63 entries ... }
    HolidayTail[63] = 1270101;
end;

Found = False;
for hidx = 1 to 63 begin
    if TheDate = HolidayTail[hidx] then Found = True;
end;

TXF_IsTaifexHoliday = Found;
```

策略端 10 支各自從 63+ 行縮成 1 行：
```
v_Holiday_Block = ( Time < 500 ) and TXF_IsTaifexHoliday( Date );
```

### 6.2 推薦理由

1. **平台真的做得到**，且有 MultiCharts 自家出貨程式碼（`f_SharpeRatio.elf`）作為存在性證明，不是我推測出來的用法。
2. **不影響 MaxBarsBack = 100**：函式無 bar-offset 歷史引用（§3.2）。
3. **維護點從 10（實際 29）個降到 1 個 CSV**。
4. **保留現行的過期警示設計**：`REGISTRY_VALID_UNTIL` 可由 Python 一併寫進 function 註解與一個 `TXF_HolidayRegistryValidUntil()` 姊妹函式，策略端的紅字警告邏輯可原樣保留。
5. **跨機同步用 PLA**（官方 KB 明說跨版本相容），不用 SEF（鎖 build）。

### 6.3 最大風險（必須寫進 SOP）

| # | 風險 | 嚴重度 | 對策 |
|---|---|---|---|
| **R1** | **改 function 後沒有 Recompile All → 已掛圖的 live 策略繼續用舊表** | 🔴 **災難**（假日照常下單） | 改表後強制流程：Editor → Compile → **All Studies / Recompile All** → 到圖上確認策略被重建 → **物理驗證：拿一個已知假日日期，看策略是否 block** |
| R2 | 兩台機器（MC9 live / MC12 dev）的 function 版本不一致 | 🔴 高 | function 內嵌 `REGISTRY_VALID_UNTIL` 與 build 標記，策略在 `LastBarOnChart` 時 print 出來；每次同步後兩台都要對這個值 |
| R3 | 全域命名空間撞名 | 🟡 中 | 函式名一律加 `TXF_` 前綴 |
| R4 | 新機器建立 function 時選錯 Return Type / Function Storage（這兩個值不在 `.elf` 文字裡） | 🟡 中 | **改用 PLA 匯入而非手動新建**；PLA 帶 metadata。若手動建，SOP 明寫「Return Type = TrueFalse，Function Storage = Simple」 |
| R5 | 匯出策略時沒勾「Select dependant function(s)」→ 對方缺 function | 🟡 中 | 匯出 SOP 加檢查項 |
| R6 | 初始化區塊非冪等 → 被 MaxBarsBack auto-detect 重複執行而算錯 | 🟡 中 | 初始化區塊只准「常數賦值」，禁止任何 `+=` / 計數器 |
| R7 | 我沒能 100% 證實「Simple function 內部的 array 跨 bar 保持狀態」（§2.2 單一直接來源） | 🟠 中 | **上線前必做物理驗證**（見下） |

### 6.4 上線前必做的物理驗證（不可跳過）

1. 建一支測試 indicator，呼叫 `TXF_IsTaifexHoliday(Date)`，`Plot1`。掛上 TXF1 日線，**肉眼比對 63 個假日是否全中、非假日是否全 False**。
2. **反向測試**：故意把 function 的 `if CurrentBar = 1` 拿掉一次，確認結果會壞 → 證明初始化區塊真的有作用（避免「其實根本沒填到值，只是剛好都 False」的假通過）。
3. 在 **MC9 桌機**與 **MC12 筆電**各跑一次，比對輸出**逐筆相同**。
4. 改一筆假日日期 → 只按 Compile（不按 Recompile All）→ 確認已掛圖策略**沒有**變化（親眼確認 R1 是真的）→ 再按 Recompile All → 確認變化生效。這一步是為了讓 SOP 有物理依據。

### 6.5 如果 6.4 第 1 或 3 步失敗

退回**方案 4（Python code generation + 各自內嵌）**。方案 4 對平台的假設最少，唯一依賴是「PowerLanguage 能宣告陣列並用 `if CurrentBar = 1` 填值」——這一點使用者現有的 29 個檔案已經跑了很久，是既成事實。

---

## §7 查不到 / 未確認事項（誠實清單）

| # | 問題 | 狀態 | 試過的關鍵字 |
|---|---|---|---|
| U1 | 官方是否明說「function 內部的 bar offset 會計入呼叫端 study 的 MaxBarsBack」 | **未找到直接陳述** | `MultiCharts PowerLanguage function increases MaxBarsBack`、`function history reference MaxBarsBack auto-detect`、`maxbarsback function offset calling study` |
| U2 | 「function 狀態是 per-call-site 還是 per-function」 | **兩個第三方來源互相矛盾，未解** | `EasyLanguage function each call separate instance`、`function variable data survives between calls`、`multiple calls same function different state` |
| U3 | `once` 在 MC12 是否仍可用、是否已補進官方文件 | **未查證**（本機只有 MC9 的 chm） | `MultiCharts once keyword PowerLanguage`（未針對 MC12 專查） |
| U4 | MC9 的 `StorageType` 數值 0 / 16 / 32 與 `BarRefMode` 0 / 1 的官方對照表 | **未找到**，§3.3 的解讀是推論 | 僅本機 `graph_backup.xml` 逆推，未做外部查證 |
| U5 | MC12 的編譯選單是否仍叫 "All Studies" 或已改為 "Recompile All (Ctrl+F7)" | **未確認**（MC9 chm 寫 "All Studies"，Wiki/論壇寫 "Recompile All"） | `MultiCharts Recompile All vs Compile`、`compile all studies PowerLanguage` |
| U6 | 是否有官方支援的 CLI / 自動化編譯介面（供 CI 用） | **未找到官方介面**，論壇 t=52480 的手法官方未背書且有已知缺陷 | `Mass Compile Strategies From Text Files`、`MultiCharts automate compile script` |

### 7.1 研究方法的重大限制（必須讓使用者知道）

**`multicharts.com` 全站對本 session 的 WebFetch 回 HTTP 403**（Wiki、論壇、KB 皆然），`web.archive.org` 亦被封鎖。
因此所有標記【搜尋摘要】的內容，**是搜尋引擎對官方頁面的摘要，不是我逐字讀到的原文**。我已盡量以下列方式補強：
1. **優先採用本機隨機官方文件**（PowerLanguage.chm / MultiCharts64.chm，MC 9.0 build 11581）——這是最高等級證據，且版本與 live 機器完全一致；
2. **優先採用本機物理檔案**（出貨函式原始碼、graph_backup.xml、Databases）；
3. 官方網頁摘要僅用於「本機文件涵蓋不到」的題目（主要是 §4.2 Recompile All 與 §4.4 PLA 跨版本）。

**§4.2 的 Recompile All 規則是本案最關鍵的營運事實，卻只有【搜尋摘要】等級的證據。** → 已在 §6.4 第 4 步設計了物理驗證來補這個洞。請務必執行。

---

## §8 來源清單

### A 級：官方隨機文件（本機，MC 9.0 build 11581）
- `C:\Program Files\TS Support\MultiCharts64\PowerLanguage.chm` → 解壓於 scratchpad `plhelp\`
  - `files/01_about/about.htm`｜`about02.htm`｜`about03.htm`｜`about04.htm` — 完整 A-Z 關鍵字索引
  - `files/03_words/Declaration/array.htm`｜`variable.htm`｜`intrabarpersist.htm`｜`recalcpersist.htm`｜`numericsimple.htm`｜`numericseries.htm`｜`truefalsesimple.htm`｜`truefalseseries.htm`
  - `files/03_words/Dynamic_Arrays/array_setmaxindex.htm`｜`fill_array.htm`
  - `files/03_words/Output/fileappend.htm`｜`filedelete.htm`
- `C:\Program Files\TS Support\MultiCharts64\MultiCharts64.chm` → 解壓於 scratchpad `mchelp\`
  - `files/04_PL/41-0002_Scripts.html` — How Scripts Work / MaxBarsBack 規則
  - `files/03_PLE/31-0101_OperatingStudies.html` — Function 定義、建立流程（Return Type / Function Storage）
  - `files/03_PLE/31-0102_Imp-ExpStudies.html` — PLA/XML/SEF 匯入匯出、SEF 鎖 build、Select dependant function(s)
  - `files/03_PLE/31-0103_WorkingStudies.html` — 編譯選項清單
  - `files/03_PLE/31-0105_Default_Properties.html` — 預設 MaxBarsBack 設定

### D 級：本機物理證據
- `C:\ProgramData\TS Support\MultiCharts64\StudyServer\Studies\SrcEl\Functions\f_SharpeRatio.elf`（function 內 array + once + recalcpersist + 跨 bar 累積）
- `…\SrcEl\Functions\f_RemoveLastZeros.elf`｜`f_emulate_dictionary__set_size.elf`（NumericArrayRef by-reference）
- `…\SrcEl\Functions\f_AB_NextColor.elf`｜`f_AB_NextLabel.elf`（function 內 CurrentBar）
- `…\StudyServer\Studies\Dlls\Functions\f_SharpeRatio.dll`（編譯成功佐證）
- `…\StudyServer\Studies\graph_backup.xml`（study metadata：signature / StudyProperties）
- `…\Databases\TSSTORAGE.GDB`｜`FBPORTFOLIO.GDB`｜`TSCACHE.GDB`
- `…\SrcEl\Strategies\s_S3_S_VolSqueezeShort.el` 等 29 檔（使用者現行 Holiday_Tail 實作）

### B/C 級：官方 Wiki / 論壇 / KB（僅取得搜尋引擎摘要，WebFetch 403）
- <https://www.multicharts.com/trading-software/index.php?title=Using_Studies_%28PowerLanguage_Editor%29> — **Recompile All 規則（§4.2 關鍵）**
- <https://www.multicharts.com/trading-software/index.php?title=4.5_Functions_and_Special_Variables>
- <https://www.multicharts.com/trading-software/index.php/How_Scripts_Work>
- <https://www.multicharts.com/trading-software/index.php?title=Array>
- <https://www.multicharts.com/trading-software/index.php?title=Passing_values_to_and_from_a_function>
- <https://www.multicharts.com/trading-software/index.php?title=Global_Variables> — GV 僅限 realtime
- <https://www.multicharts.com/trading-software/index.php?title=Importing_and_Exporting_Studies>
- <https://www.multicharts.com/trading-software/index.php/SetMaxBarsBack>
- <https://www.multicharts.com/support/base/how-can-i-back-up-multicharts/> — PLA 跨版本相容
- <https://www.multicharts.com/discussion/viewtopic.php?t=52638> — Values of variables in function will be kept
- <https://www.multicharts.com/discussion/viewtopic.php?t=5823> — persistence scope of variables within a study
- <https://www.multicharts.com/discussion/viewtopic.php?t=50927> — Primary purpose of "Compile" and "Recompile All"
- <https://www.multicharts.com/discussion/viewtopic.php?t=51022> — Please VOTE: Read from File（反證無內建讀檔）
- <https://www.multicharts.com/discussion/viewtopic.php?t=49864> — Reading a txt file in power language?
- <https://www.multicharts.com/discussion/viewtopic.php?t=52480> — Mass Compile Strategies From Text Files（直改 SrcEl 的陷阱）
- <https://www.multicharts.com/discussion/viewtopic.php?t=47311> — Importing Function Dependencies From ELD/PLA-Files
- <https://www.multicharts.com/discussion/viewtopic.php?t=11386> — Putting Power Language in code repository?
- <https://www.multicharts.com/discussion/viewtopic.php?t=48239> — keep EasyLanguage files in sync between different computers
- <https://www.multicharts.com/discussion/viewtopic.php?t=52858> — from mc export xml file to git
- <https://www.multicharts.com/pm/public/multicharts/issues/MC-1690> — core powerlanguage files should be on github（OPEN）
- <https://www.multicharts.com/traders-blog/multicharts-12-0-release-2/> — MC12 release notes（MidStr 語意變更）

### E 級：第三方（可 WebFetch 驗證者已標註）
- <https://help.tradestation.com/10_00/eng/tsdevhelp/elword/el_definitions/about_functions.htm> — TradeStation 官方：series function 每根 bar 執行（✅ 已 WebFetch 逐字取得）
- <https://georgepruitt.com/function-variable-data-survives-between-calls/> — function 內變數/陣列跨呼叫存活（✅ 已 WebFetch 逐字取得）
- <https://codereindeer.com/en/multicharts-and-powerlanguage-function-en/> — ❌ WebFetch 403，未取得
