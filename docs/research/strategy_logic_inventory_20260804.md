---
建立日期: 2026-08-04
資料來源: 4 份抽取檔（.pla 靜態閱讀）+ 主對話與驗收 agent 的原檔實讀校正
驗證狀態: 未經 MC12 編譯與回測驗證；已通過一次獨立 fresh-context 驗收
修訂版次: rev.1 (2026-08-04 驗收後修正)
---

# 全庫策略條件邏輯歸納（模組化停利／停損重構輸入）

## 修訂履歷

| 版次 | 日期 | 說明 |
|---|---|---|
| rev.0 | 2026-08-04 | 初版，由 4 份抽取檔合成 |
| **rev.2** | **2026-08-04** | **使用者裁決後的修補落地**（見下方「rev.2 狀態變更」）。本表所述的 3 項合規缺口已修，2 支驗證腳本已升級。**注意：本文其餘章節描述的是修補前狀態，凡與 rev.2 衝突者以 rev.2 為準** |
| **rev.1** | **2026-08-04** | **獨立 fresh-context 驗收判定 FAIL 後修正**（驗收 agent 未獲初版製作過程，避免 anchoring）。修正 3 項九層歸類誤判 + 5 處行號錯誤，並將 2 項 `[來源衝突]` 開原檔定案。詳見下表 |

**rev.1 修正清單**

| # | 類別 | 原稿 | 修正後 | 依據 |
|---|---|---|---|---|
| 1 | 九層歸類 | S3_S 的 Layer 2 SP **同時**填層 2 與層 3 | 僅層 2；層 3 改判 ❌ | `entry_exit_sop.md:58` 明訂層 3 錨「價格絕對位置」、層 2 錨「帳面利潤%」。S3_S:988-989 的 floor = `EntryPrice − peak × retain/100` 為純利潤%制 |
| 2 | 九層歸類 | L4 / L5 層 7 填 ✅ | 改 ❌（並保留「僅進場端」說明） | 本層定義為**出場**向；L4 出場鏈 :659-717 無夜盤分支；`entry_exit_sop.md:158-159` 審計快照對此二格亦為 ❌ |
| 3 | 合規語意 | Rule #17 欄對 L1–L5 / S1 / S3_L / S3_RPS 填 ❌ | 改「—不適用」 | CLAUDE.md Rule #17 適用範圍限「極端行情策略（S3_S、S6、S9 等）」。填 ❌ 會與 L4 的 Rule #15 真違規視覺等價 |
| 4 | 行號 | `S16_S:863`（越界，該檔僅 771 行） | `S16_S:631`（設計意圖註解） | 原檔實讀 |
| 5 | 行號 | `S16_S:906`（越界） | `S16_S:758-760`（P6 停單區塊） | 原檔實讀 |
| 6 | 行號 | `S16_S:157`（2 處） | `S16_S:156` | 原檔實讀：`NO TP` 在 :156 |
| 7 | 行號 | `S3_S:261`（2 處） | `S3_S:260` | 原檔實讀：:260 = `ConfirmSL_On`，:261 = `ConfirmSL_Bars` |
| 8 | 來源衝突定案 | U29 L3 三個 input 行號待校核 | 定案 `:109 / :110 / :111` | 原檔實讀 :108-112 |
| 9 | 來源衝突定案 | U30 L1 `Registry_Valid_Until` 行號待校核 | 定案 `L1:245` | 原檔實讀 :242-247，:246 為續行註解 |

> rev.1 的教訓：初版自陳「`entry_exit_sop.md` 本身未被讀取，第 3 節分類需重新對齊」——**這個自陳的風險確實發生了**。第 1、2 項誤判即源於此。凡以他人整理的二手摘要建表，務必回頭核對一次原始規範文件。

---

## rev.2 狀態變更（2026-08-04 使用者裁決後執行）

### A. 已修補的合規缺口

| # | 項目 | 修補內容 | 物理證據 |
|---|---|---|---|
| A1 | **S3_L Rule #12 由 1/3 → 3/3** | 新增 `SL_Pct(0)` input；新增 `SetStopContract`（置於 `SetStopLoss` 之前）；新增 `MinList` 百分比上限邏輯，錨點用 `Close`（與 L1/L2/L3/L4/S16_S 同慣例）。原單行 `if` 改為 `begin/end` 區塊 | 剝除註解後計數：`SetStopContract`=1、`SetStopLoss()`=1，符合 Rule #12「僅限 1 組」 |
| A2 | **S3_S Rule #12 由 1/3 → 3/3** | 同上。百分比上限套用於**夜盤加寬乘數之後**，使 cap 同時約束加寬後的距離。原 `S3_S:709-710` 的單行 `if` 無 `begin/end`，已補上 | 同上 |
| A3 | **L4 Rule #15 非 ASCII 違規已清除** | `:507` 與 `:622` 的 `U+00D7`（`×`）改為 ASCII `x`。**僅動 `{ }` 註解內文字，零行為影響** | 修補後 non-ASCII bytes = 0；檔案行數 719 前後一致；`git diff --stat` = 2 insertions / 2 deletions |

> **A1 / A2 的重要但書**：`SL_Pct` 預設為 **0（停用）**。Rule #12 要求「MC sweep 0.00-5.00 step 0.25 找收斂點後寫回預設」，該 sweep **尚未執行**。目前狀態是「結構合規、數值待掃描」，不是完整合規。
>
> **A1 / A2 會改變回測結果**：補上 `SetStopContract` 使引擎停損金額由 TOTAL POSITION 改為 PER-CONTRACT。固定 2 口下，這等於**把引擎停損距離放寬一倍到設計值**。這是修正而非退化，但**必然改變逐筆結果**，promote 前須重跑回測。
>
> **三檔皆未經 MC12 編譯驗證**。依鐵律 4，需使用者執行編譯 + runtime + log 三層物理驗證。

### B. 驗證腳本升級（Rule #11 / #15 的執行機制）

**升級前的四個確診根因**

| # | 根因 | 證據 |
|---|---|---|
| B1 | `verify_pla_ascii.py` 的 `live/*.pla` 與 `live_simulation/*.pla` glob **缺 `**` 遞迴**，2026-07-26 資料夾重構後匹配不到任何檔 | 掃描數 36，實際應 47；漏掉的 11 檔正好是全部在役策略 |
| B2 | `verify_settlement_flat.py` 硬編碼 6 個舊路徑，且直接 `open()` → **crash 而非回報 FAIL** | 實跑於第一個檔 L1 拋 `FileNotFoundError`、exit 1 |
| B3 | 該腳本的 `FILES` 字典**完全沒有 S3_L / S3_S / S3_RPS / S16_S** | 僅涵蓋 L1-L5 + S1 |
| B4 | repo **無 active git hook、無 CI 設定** | `.git/hooks` 只有 `.sample`；無 `.github/` |

**最危險的不是 B2（crash 很吵），是 B1（靜默）**：腳本回報「36/36 PASS、exit 0」，看起來完全健康，實際上一隻在役策略都沒掃到，而漏掃區裡正躺著 A3 那個違規。

**升級後**

| 檔案 | 變更 |
|---|---|
| `scripts/strategy_discovery.py`（新增） | 單一事實來源。遞迴發現，排除 `archive/` 與 `.bak`；區分 strategy / indicator（檔名前綴 **與** 檔內下單語句雙重判定，不一致時發 warning 而非靜默歸類） |
| `scripts/verify_pla_ascii.py`（改寫） | 改用 discovery；新增**覆蓋率斷言**（發現數 ≠ 掃描數即 FAIL）；新增 **tier 下限守門**（live 或 live_simulation 掃到 0 檔即 structural failure） |
| `scripts/verify_settlement_flat.py`（改寫） | 改用 discovery，零硬編碼路徑；**fail-closed**（讀不到檔 = 該檔 FAIL 並繼續，絕不 crash）；出場標籤改由檔案推導；涵蓋全部 10 隻 |

**關鍵設計決定**：structural failure（discovery 掃到 0 檔、覆蓋率有缺口）**無條件 exit 1，不需 `--strict`**。理由：守門員看不到自己該看的範圍時，絕不允許回報成功。內容違規才沿用 `--strict` 慣例。

**升級後實跑結果（主對話獨立複跑，非轉述）**

```
verify_pla_ascii.py --strict
  live 5 / live_simulation 6 / research 36 -> DISCOVERED 47 files
  COVERAGE: discovered 47 / scanned 47  ->  OK
  RESULT:   47/47 PASS, 0/47 FAIL          EXIT = 0

verify_settlement_flat.py --strict
  DISCOVERED 10 strategies under Rule #11
  COVERAGE: discovered 10 / checked 10  ->  OK
  ELEMENTS: 70/70 OK (100%)   STRATEGIES: 10/10 fully compliant   EXIT = 0
```

修補 A3 之前，ASCII 腳本確實抓到 `L4:507 C30 U+00D7` 與 `L4:622 C67 U+00D7` 並 exit 1 —— 這是升級有效的直接證據（舊版對同一個檔回報 PASS）。

### C. 升級後仍未解決的弱點

| # | 弱點 | 說明 |
|---|---|---|
| C1 | **B4 完全未解 —— 目前最大的洞** | 仍無 git hook、無 CI。腳本再嚴謹，沒有東西強迫它被執行。本次事故的真正教訓不是「glob 寫錯」，是「守門員 9 天沒上工也沒人發現」 |
| C2 | 忘記加 `--strict` 仍會放行**內容**違規 | 僅 structural failure 無條件 exit 1 |
| C3 | 元素 5/6/7 是**存在性**檢查非**語意**檢查 | 腳本確認有 settlement 出場單、有 time gate、有進場 gate，但未驗證 time gate 真的包住那張出場單，也未驗證 Priority 0 順序正確。把 gate 寫在不相干位置仍會 PASS。（本文 6.1 節記載的 L1/L3 Kill 鏈外偏差，腳本至今抓不到） |
| C4 | 只驗 tier 非空，未驗**預期檔數** | live/ 若從 5 隻掉到 1 隻，守門不會叫。需一份與 `OFFICIAL_ROADMAP.md` 對帳的 manifest |
| C5 | 突變測試未固化為 regression test | 已驗證 8 種破壞皆會被抓到，但該測試是一次性腳本，未留在 repo。下次有人改壞 regex 不會有人發現 |

## 0. 文件目的與證據等級聲明

### 0.1 目的

本文件把 TXF1-Strategy-Lab 全庫在役策略的**進場條件、停損結構、停利／鎖利結構、強制模組合規狀態**收斂成一組可逐格比對的表格，作為「模組化停利／停損」重構的唯一設計輸入。表格的每一格都會被用來判斷「這個機制能不能抽成共用模組」，因此本文的編寫原則是**只搬運，不發明**。

### 0.2 證據等級（必讀）

- 本文所有內容來自 4 份 `.pla` **靜態閱讀**抽取檔（見第 9 節）。
- **無任何 MC12 編譯驗證、無任何回測驗證、無任何 runtime log**。
- 凡涉及「MC 引擎在同一根 K 棒上如何仲裁 Market / Stop / Limit 單」的敘述，一律為未驗證項，已集中列於第 8 節。
- 少數已由主對話**實跑指令**確認的事實（檔案雜湊、腳本 exit code、非 ASCII byte 計數、git 狀態），在文中以「主對話實測」標示，屬本文中證據等級最高的一類。
- 本文**未**執行任何腳本、**未**讀取任何 `.pla` 原始碼、**未**修改 repo 內任何既有檔案。

### 0.3 兩種標記的意思

| 標記 | 意思 | 處理原則 |
|---|---|---|
| `[不確定]` | 抽取檔已判定「無法從程式碼本身判定」的項目（多半需 MC12 實測、需查 MC 官方文件，或需使用者 ruling）。 | 承接原標記，**不得**在本文中被改寫成肯定句。全部彙整於第 8a 表。 |
| `[來源衝突]` | 4 份抽取檔之間對**同一事實**（行號／預設值／機制有無／定義）給出不同答案。 | **兩邊都列出**並標明各自出處檔名，不自行選一個。 |
| `[抽取檔未涵蓋]` | 4 份抽取檔皆未載明該欄位。 | 直接寫此標記，**禁止推測後當事實寫**。 |

---

## 1. 策略母體盤點

### 1.1 在役策略（10 隻）

repo root：`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\`

| 策略 ID | 層級 | 檔案路徑（相對 repo root） | 實測行數 | 方向 | 主週期 | 版本 | 備註 |
|---|---|---|---|---|---|---|---|
| L1_TrendLong | live | `strategies\live\L1_TrendLong\L1_TrendLong.pla` | 706 | Long | 45M（Data1）+ Daily + Weekly | V3.1 | 全庫唯一 `[IntrabarOrderGeneration = true]`（L1:220）；Priority 0 順序偏差 |
| L2_TrendShort | live | `strategies\live\L2_TrendShort\L2_TrendShort.pla` | 741 | Short | 60M（單一 feed） | 5.3 + SetStopContract + SL_Pct | 4 份抽取檔**無** L2 research 線資料 `[抽取檔未涵蓋]` |
| L3_ConsolidationLong | live | `strategies\live\L3_ConsolidationLong\L3_ConsolidationLong.pla` | 474 | Long | 15M + 60M + Daily | v15.0 | 全庫最短；唯一完全無 trailing；Priority 0 順序偏差 |
| L4_ConsolidationShort | live | `strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla` | 719 | Short | 15M + 60M + Daily | v14.6 + SetStopContract + SL_Pct | **Rule #15 違規**：非 ASCII 位於 `:507` / `:622`（主對話實測 4 bytes，字元 U+00D7 `×`，皆在註解內） |
| L5_BreakoutLong | live | `strategies\live\L5_BreakoutLong\L5_BreakoutLong.pla` | 729 | Long | 15M + Daily + Weekly | v19.9 | 全庫唯一分批出場（40%）+ 唯一雙進場腿 + 唯一 MFE 四階 trail |
| S1_NightMomentum | live_simulation | `strategies\live_simulation\S1_NightMomentum\S1_NightMomentum.pla` | 484 | Long | 15M（Data2/3 僅 `TrendFilterMode>=2/3` 才引用，預設 0） | v2.7+StopHarden | 全 6 檔 live_sim 中唯一未宣告 IOG |
| S3_VolSqueezeLong（S3_L） | live_simulation | `strategies\live_simulation\S3_VolSqueezeLong\S3_VolSqueezeLong.pla` | 526 | Long | 60M（單一 feed） | v1.1 | **Rule #12 三件套 1/3**（缺 SetStopContract、缺 SL_Pct） |
| S3_S_VolSqueezeShort（S3_S） | live_simulation | `strategies\live_simulation\S3_S_VolSqueezeShort\S3_S_VolSqueezeShort.pla` | 1123 | Short | 1M 執行 / 60M 決策 / Daily regime | v1.9.6-OPT-PROD | **Rule #12 三件套 1/3**；與 research head 可執行碼零差異（差 13 行檔頭） |
| S3_RapidPullbackShort（S3_RPS） | live_simulation | `strategies\live_simulation\S3_RapidPullbackShort\S3_RapidPullbackShort.pla` | 995 | Short | 5M 執行 / 60M regime / Daily | v2.0.6 | 檔頭自承 `NO BACKTEST YET. v2.0 is research-tier only`（S3_RPS:82）卻位於 live_simulation |
| S16_S_MACrossShort | live_simulation | `strategies\live_simulation\S16_S_MACrossShort\S16_S_MACrossShort.pla` | 771 | Short | 5M（單一 feed） | v1.6.2 | 落後 research head（v1.12.0）六個版本，落後內容全在停損停利 |

> 同目錄另有 `IND_S16_S_Monitor.pla`（104 行，indicator，不下單）— 純視覺診斷，不計入策略母體。

### 1.2 research 版本（快照／變體／已否決）

| 策略 ID | 層級 | 檔案路徑（相對 repo root） | 實測行數 | 方向 | 主週期 | 版本 | 備註 |
|---|---|---|---|---|---|---|---|
| L1_TrendLong_v3.1 | research-head | `strategies\research\L1_TrendLong\L1_v3.1\L1_TrendLong_v3.1.pla` | 706 | Long | 同 L1 | V3.1 | **與 live byte-identical（主對話 Get-FileHash 完全相同）→ 非獨立策略，是 live 的快照** |
| L3_ConsolidationLong_v15.0 | research-head | `strategies\research\L3_ConsolidationLong\L3_v15.0\L3_ConsolidationLong_v15.0.pla` | 474 | Long | 同 L3 | v15.0 | **與 live byte-identical（主對話 Get-FileHash 完全相同）→ 非獨立策略** |
| L5_BreakoutLong_v19.9 | research-head | `strategies\research\L5_BreakoutLong\L5_v19.9\L5_BreakoutLong_v19.9.pla` | 729 | Long | 同 L5 | v19.9 | **與 live byte-identical（主對話 Get-FileHash 完全相同）→ 非獨立策略** |
| L4_ConsolidationShort_v16.0 | research-head | `strategies\research\L4_ConsolidationShort\L4_v16.0\L4_ConsolidationShort_v16.0.pla` | 657 | Short | 15M + 60M + Daily | v16.0 | **KILLED**（`L4_v16.0_FINAL_VERDICT.md:3`，2026-07-26）；**與 live 不同（主對話 Get-FileHash 不同）**；bull path 6 年 0 筆；Rule #12 **0/3**；研究線 CLOSED |
| S3_VolSqueezeShort_v196_ANTIHUNT | research-head | `strategies\research\S03_VolSqueezeShort\S3_VolSqueezeShort_v196_ANTIHUNT.pla` | 1110 | Short | 同 S3_S | v1.9.6-ANTIHUNT | 與 live_sim S3_S **可執行碼零差異**，僅檔頭 13 行 PROMOTE 區塊；行號 = live_sim 行號 − 13 |
| S16_S_MACrossShort_v1.12.0 | research-head | `strategies\research\S16_MACrossShort\S16_S_MACrossShort_v1.12.0.pla` | 918 | Short | 5M | v1.12.0 | 領先 live_sim 六版；含 true BE（`BE_Cost_Pts=10`）+ P3b Profit Trail（1.20/80） |
| S16_S_10M_MACrossShort | research-variant | `strategies\research\S16_MACrossShort\S16_MACrossShort_10M\S16_S_10M_MACrossShort.pla` | 497 | Short | 10M | v0.1-PORT | **封存變體**（檔頭 `:7-12` 明示為 timeframe robustness 佐證，`NOT a replacement`）；Rule #12 **1/3**；回測基準 1 lot / 1,000,000（與全庫 2 lot / 2,000,000 不同） |

被取代版本（抽取檔有提及、非 head）：`L1_v3.0`（680 行）、`L3_v14.1`（394 行）、`L4_v15.1`（594 行）、`L5_v19.8`（695 行）、`S3_VolSqueezeShort_v196_EXPERIMENTAL`、目錄內未帶版號的 `S3_VolSqueezeShort.pla`（v1.5 殘留）與 `S16_S_MACrossShort.pla`（v1.4-BELATE 殘留）、S16_S v1.9.0 / v1.10.0（KILLED）/ v1.11.0。

### 1.3 母體結論（4 行）

1. **真正獨立的在役策略 = 10 隻**（live 5 隻：L1–L5；live_simulation 5 隻：S1 / S3_L / S3_S / S3_RPS / S16_S）。
2. `L1_v3.1` / `L3_v15.0` / `L5_v19.9` 三檔經主對話 Get-FileHash 實測與 live 完全相同，是 **live 的 byte-identical 快照**，不得計為獨立策略或「下一代設計」；`S3_S` 的 research head 與 live_sim 亦為可執行碼零差異。
3. **開發中版本線只有 1 條有實質前進**：S16_S 5M（research v1.12.0 領先 live_sim v1.6.2 六版，落後內容 100% 落在停損停利）。L1 / L3 / L5 三條已 promote 完畢無前進；L4 一條已 KILLED / CLOSED（且 v16 相對 live v14.6 在 Rule #12 上是退步）；S16_S_10M 為封存變體。
4. L2 在 4 份抽取檔中完全沒有 research 線資料 `[抽取檔未涵蓋]`；模組化時 L2 只有 live 一份實作可參考。

---

## 2. 進場邏輯歸納

> 邏輯式一律用可讀符號改寫，非原始碼。`∧` = AND，`∨` = OR。

| 策略 | 核心進場條件（邏輯式，精簡） | 主要 input 與預設值 | 進場 gate（阻擋條件） | 資料流 |
|---|---|---|---|---|
| **L1** | `MP=0 ∧ (Close 上穿 MA61 + ATR20×2.0) ∧ (Close_W > MA20_W ∨ Close_W > MA60_W) ∧ ¬Holiday ∧ ¬Settlement` → `Buy` next bar **Market**（L1:535-543） | `Length60=61`(L1:224)、`Entry_Multiplier=2.0`(L1:225)、`ATR_Length=20`(L1:240)、`Weekly_MA_Fast=20`(L1:259)、`Weekly_MA_Slow=60`(L1:260) | Settlement ✅(L1:490-492,542)｜Holiday tail `Time<=500` ✅(L1:463-468,541)｜Registry ✅(L1:477-480)｜**Kill ❌僅出場端**(L1:646)｜Session ❌無｜regime = 週線 **OR**(L1:441-450)｜bar-close guard `BarStatus(1)=2`(L1:535) | Data1=45M / Data2=Daily（ATR 用 `[1]`，L1:429）/ Data3=Weekly（`Close of Data3` **未用 `[1]`**，L1:445-446）；**IOG=true**(L1:220) |
| **L2** | `FilterOK(週線熊) ∧ C0(Close < DC_Lower − ATR×0.45) ∧ C_A(ZLEMA 下彎) ∧ C_B(ZLEMA < EMA20) ∧ ¬Holiday ∧ ¬Settlement ∧ MP=0` → `SellShort` next bar **Market**（L2:473-480） | `WkSMA_Len=13`(L2:81)、`DC_Len=30`(L2:85)、`ZLEMA_Len=20`(L2:87)、`ZLEMA_Lag=9`(L2:88)、`C0_ATR_Filter=0.45`(L2:94)、`ATR_Len=21`(L2:95) | Settlement ✅(L2:355-357,478)｜Holiday ✅(L2:338-345,477)｜Registry ✅(L2:349-352)｜**Kill ❌僅出場端**(L2:667)｜Session ❌無進場濾網（`IsDay`/`IsNight` 僅出場端 L2:722/732）｜regime = **手動陣列重建** 13 週 SMA(L2:388-427) | **單一 Data1=60M**；全檔無 `of Data2` / `of Data3`；IOG 無宣告（預設 false） |
| **L3** | `箱型成立 ∧ Box_Qualified(Range/ATR≥8.5) ∧ MP=0 ∧ Trend60M=1 ∧ Daily-OR ∧ ¬Holiday ∧ ¬Settlement ∧ ¬OpeningBlock ∧ RR_Qualified ∧ (Close < 支撐區) ∧ (Close > Box_Btm − ATR_Buffer)` → `Buy` next bar @ `v_Box_Btm` **Stop**（L3:331,360-370） | `Lookback_Bars=16`(L3:99)、`Range_Shrink_Rate=0.1`(L3:100)、`MA_Len=12`(L3:101)、`Entry_Zone_Pct=0.50`(L3:104)、`Min_Box_ATR=8.5`(L3:105)、`Swing_Lookback=80`(L3:106)、`ATR_Length=9` **[來源衝突]**ᴬ、`ATR_Stop_Mult=3.0` **[來源衝突]**ᴬ、`Open_Block_End=945`(L3:112)、`Min_RR=1.0`(L3:113) | Settlement ✅(L3:244-246,364)｜Holiday ✅(L3:230-235,363)｜Registry ✅(L3:239-242)｜**Kill ❌僅出場端**(L3:458)｜**Session ✅開盤禁區** `Time=500` 或 `900≤Time<945`(L3:346-350)｜regime = Daily **OR**(L3:319-323) + 60M 趨勢(L3:272-275)｜**Min R:R gate**(L3:353-356) | Data1=15M / Data2=60M（箱型用 `[1]`，L3:265-266；`v_Curr_Range` 用當根 L3:267）/ Data3=Daily（`Close of Data3` **未用 `[1]`**，L3:319-320）；IOG 無宣告 |
| **L4** | `MP=0 ∧ BarsSinceExit≥8 ∧ Trend60M=−1 ∧ ¬MacroBlock ∧ InTrapZone ∧ (Close < Trigger_Price) ∧ ¬Holiday ∧ ¬NightBlock ∧ ¬Settlement` → `SellShort` next bar **Market**（L4:518,547-557） | `Daily_FastMA_Len=20`(L4:241)、`Daily_SlowMA_Len=60`(L4:242)、`Lookback_Bars=15`(L4:245)、`Range_Shrink_Rate=0.7`(L4:246)、`Weekly_MA_Len=48`(L4:247，**實為 Data2 60M 的 48 根均線**)、`ATR_Length=60`(L4:250)、`i_Buffer_ATR_Mult=0.4`(L4:254)、`Time_Limit_Bars=6`(L4:255)、`Cooldown_Bars=8`(L4:258) | Settlement ✅(L4:422-424,555)｜Holiday ✅(L4:407-412,553)｜Registry ✅(L4:416-419)｜**Kill ❌僅出場端**(L4:659)｜**Session ✅夜盤封鎖** `Night_Block_On=true ∧ 200≤Time<500`(L4:446-448,554)｜regime = Macro 多頭封鎖（Data3 日線，L4:460-466,550）｜**Cooldown 8 根**(L4:548) | Data1=15M / Data2=60M（`[1]`，L4:472-473）/ Data3=Daily(L4:457-460)；**IOG=false**(L4:237) |
| **L5** | 共用 gate `MP=0 ∧ v_Allow_Entry ∧ TrendDaily=1 ∧ 週線 **AND** 濾網 ∧ RR≥1.1`；再各腿獨立 `(Close < 錨) ∧ (Close > 錨 − ATR_Buffer)` → `Buy` next bar @ `v_Box_Btm` / `v_Mid_Line` **Stop**（L5:499,521-532） | `Lookback_Bars=4`(L5:205)、`Range_Shrink_Rate=0.6`(L5:206)、`Daily_MA_Len=60`(L5:207)、`Min_RR_Bull=1.1`(L5:210)、`ATR_Length=35`(L5:213)、`ATR_Stop_Mult=4.5`(L5:214)、`FrontRun_Ticks=5`(L5:215)、`Weekly_MA_Fast=20`(L5:229)、`Weekly_MA_Slow=60`(L5:230) | **Settlement ✅間接**（經 `v_Allow_Entry`，L5:391-393,428-429）｜Holiday ✅間接(L5:425-426)｜Registry ✅(L5:385-388)｜**Kill ❌僅出場端**(L5:576)｜**Session ✅深夜** `400≤Time≤500`(L5:419-420) **+ 週六** `DOW=6 ∧ Time≥1330`(L5:422-423)｜regime = Daily 趨勢 + 週線 **AND**(L5:480-484)｜**R:R gate**(L5:524) | Data1=15M / Data2=**Daily**（`[1]`，L5:435-436）/ Data3=Weekly（**未用 `[1]`**，L5:480-481）；箱型解除用 **High/Low**（L5:454-457，L3/L4 用 Close）；IOG 無宣告 |
| **S1** | `RangeReady ∧ IsNightSession ∧ Time<500 ∧ VolPass ∧ TrendPass ∧ ¬Holiday ∧ ¬Settlement ∧ Prev_MP≤0 ∧ ATR>0` → `Buy` next bar @ `NightHigh + ATR×0.2` **Stop**（S1:406-411） | `LookbackBars=11`(S1:162)、`ATRLen=11`(S1:163)、`EntryATRMult=0.2`(S1:164)、`RangeMinATR=0.9`(S1:165)、`RangeMaxATR=4.5`(S1:166)、`NightOpen=1500`(S1:175)、`ExitTime=500`(S1:176)、`VolSlowLen=70`(S1:177)、`VolRatioMin=0.80`(S1:178)、`TrendFilterMode=0`(S1:186) | Settlement ✅(S1:300-302,408)｜Holiday `Time<=500` 掃描 ✅(S1:283-290,407)｜Registry ✅(S1:292-297)｜**Kill ❌僅出場端**(S1:427)｜**Session ✅實際窗口僅 `Time<500`**（布林代數必然結果；檔頭 S1:192-194 敘述與程式碼不一致，**程式碼為準**）｜regime = VolPass(S1:334-339) + `TrendFilterMode`（**預設 0 = 恆 true = 關閉**，S1:346-347） | Data1=15M；Data2/Data3 **僅在 `TrendFilterMode>=2/3` 時才引用**（預設 0 → 等同單一 15M feed）；跨週期一律 `[1]`(S1:352-353,358-359)；**IOG 未宣告** |
| **S3_L** | `MP=0 ∧ Squeeze(BWRank≤30) ∧ (Close > 上軌) ∧ ¬Cooldown ∧ ¬Holiday ∧ ¬Settlement ∧ ¬RegistryExpired` → `Buy` next bar **Market**（S3_L:415-424） | `BBLen=45`(S3_L:99)、`BBStd=2.0`(S3_L:100)、`BWLookback=120`(S3_L:101)、`BWPctile=30`(S3_L:102)、`ATR_Len=14`(S3_L:105)、`StopATRMult=2.75`(S3_L:106)、`TargetATRMult=8.0`(S3_L:107)、`MaxBars=70`(S3_L:110)、`Cooldown_Days=1`(S3_L:115) | Settlement ✅(S3_L:292-294,420)｜Holiday **strict `Time<500`** ✅(S3_L:275-282,419)｜Registry ✅(S3_L:284-289,421)｜**Kill ❌僅出場端**(S3_L:452)｜**Session ❌無時段限制**(S3_L:411-412)｜**regime ❌無**（S3_L 無 regime 模組）｜方向濾網 ❌無｜Cooldown 1 日 ✅(S3_L:418) | **單一 Data1=60M**；全檔無 `of Data2` / `of Data3`；**IOG=false**(S3_L:88) |
| **S3_S** | `BarStatus(2)=2 ∧ MP=0 ∧ Hunt_Active ∧ (Close_60M < 下軌) ∧ (Close_60M < Hunt_Low − 0.15×ATR) ∧ (¬Use_Cooldown ∨ ¬Cooldown) ∧ ¬Holiday ∧ ¬Settlement ∧ ¬RegistryExpired ∧ Regime_OK` → `SellShort` next bar **Market**（S3_S:890-903） | `BBLen=45`(S3_S:194)、`BBStd=2.0`(S3_S:195)、`BWLookback=120`(S3_S:196)、`BWPctile=40`(S3_S:197)、`ATR_Len=14`(S3_S:200)、`StopATRMult=3.25`(S3_S:201)、`TargetATRMult=2`(S3_S:202)、`MaxBars=35`(S3_S:205)、`Use_Cooldown=False`(S3_S:221)、`Thrust_Margin_ATR=0.15`(S3_S:224)、`Hunt_Max_Stops=4`(S3_S:225)、`Use_Regime_Filter=True`(S3_S:228)、`Regime_FastMA=15`(S3_S:229)、`Regime_SlowMA=40`(S3_S:230) | Settlement ✅(S3_S:518-520,897)｜Holiday strict `Time<500` ✅(S3_S:501-508,896)｜Registry ✅(S3_S:510-515,898)｜**Kill ❌僅出場端**(S3_S:937)｜**Session ❌無時段限制**｜**regime ✅Daily MA 比值 band-reject**（門檻 0.98 / 1.02 / 1.05 **硬編碼**，S3_S:542-563,899）｜**Hunt 熔斷 Gate B** ✅(S3_S:1104-1113) | Data1=1M（執行 + 1M 監控）/ Data2=60M（決策，`BarStatus(2)=2` 閘）/ Data3=Daily（regime，用 `[1]`，S3_S:543-544）；MaxBarsBack≥1000(S3_S:93)；**IOG=False**(S3_S:181) |
| **S3_RPS** | `MP=0 ∧ Regime_Watch(60M: A ∧ (B ∨ C)) ∧ Trigger_Fired(5M: M1∧M2∧M3∧M4) ∧ Secular_Bull_OK(Daily 3 條件 AND) ∧ 850≤Time≤1230 ∧ ¬DailyCooldown ∧ ¬Holiday ∧ ¬Settlement ∧ ¬RegistryExpired ∧ ¬Kill` → `SellShort` next bar **Market**（S3_RPS:698-710） | `H60_FastMA_Len=20`(S3_RPS:100)、`H60_SlowMA_Len=60`(S3_RPS:101)、`H60_RSI_Len=14`(S3_RPS:102)、`H60_RSI_Threshold=70`(S3_RPS:103)、`H60_RSI_Sustained_Bars=2`(S3_RPS:104)、`H60_Dist_MA20_Pct=1.5`(S3_RPS:105)、`Consec_Red_Bars=3`(S3_RPS:111)、`EMA_Fast_Len=5`(S3_RPS:112)、`ATR_Spike_Mult=1.0`(S3_RPS:115)、`Pullback_Min_Pct=0.5`(S3_RPS:116)、`Pullback_Max_Pct=1.5`(S3_RPS:117)、`Entry_Open_Time=850`(S3_RPS:127)、`Entry_Cutoff_Time=1230`(S3_RPS:128)、`Daily_SecularMA_Fast=60`(S3_RPS:150)、`Daily_SecularMA_Slow=200`(S3_RPS:151) | Settlement ✅(S3_RPS:367-369,706)｜Holiday strict `Time<500` ✅(S3_RPS:350-357,705)｜Registry ✅(S3_RPS:359-364,707)｜**Kill ✅在進場端**(S3_RPS:708)｜**Session ✅封閉區間 08:50–12:30**(S3_RPS:702-703)｜regime = Tier1 60M(S3_RPS:454-458) + Tier3 Daily Secular Bull(S3_RPS:504-511)｜**每日一單 cooldown** ✅(S3_RPS:704,636-641) | Data1=5M / Data2=60M（全部用 `[1]` 且顯式括號綁定）/ Data3=Daily（`[1]`）；Data2 前進偵測用 `(Date of Data2, Time of Data2)` tuple(S3_RPS:613-631)；MaxBars Strategy Reference 需 300(S3_RPS:932)；**IOG=false**(S3_RPS:85) |
| **S16_S** | 主進場 `MP=0 ∧ Death_Cross ∧ Slope>28 ∧ (Time≤430 ∨ Time>500) ∧ ¬Settlement ∧ ¬Holiday ∧ ¬RegistryExpired ∧ ¬Kill` → `SellShort` next bar **Market**（S16_S:562-571）<br>Re-Entry `MP=0 ∧ ReEntry_Armed ∧ (Fast<Slow) ∧ Slope>28 ∧ (Close≥ReEntry_Price) ∧ [同五道 gate]` → `SellShort` next bar @ `v_ReEntry_Price` **Stop**（S16_S:580-591） | `ZLEMA_Fast=25`(S16_S:224)、`ZLEMA_Slow=70`(S16_S:225)、`MinSlope=28`（**純點數，非 ATR 倍數**，S16_S:226）、`ATR_Len=14`(S16_S:262)、`StopATRMult=4.0`(S16_S:263)、`SL_Pct=1.00`(S16_S:264)、`Tail_LastEntry_Time=430`(S16_S:279) | Settlement ✅(S16_S:427-429,566/586)｜Holiday `Time<=500`（**非 strict**）✅(S16_S:414-420,567/587)｜Registry ✅(S16_S:409-411,568/588)｜**Kill ✅在進場端**(S16_S:569/589)｜**Session ✅封鎖 04:31–05:00**(S16_S:565/585)｜**regime ❌刻意不做**（S16_S:156，user 2026-07-08 ruling Option A: pure simple）｜方向濾網 = `MinSlope` 純點數斜率｜Cooldown ❌無 | **單一 Data1=5M**；全檔無 `of Data2` / `of Data3`；MaxBarsBack≥200(S16_S:213)；**IOG=False**(S16_S:216) |

**腳註 ᴬ（L3 input 行號）— 原為 `[來源衝突]`，2026-08-04 已開原檔定案**

| 參數 | `extract_live.md` | `extract_research_L.md` | **定案（原檔實讀）** |
|---|---|---|---|
| `ATR_Length = 9` | `L3:110` ✗ | `:109` ✓ | **`L3:109`** |
| `ATR_Stop_Mult = 3.0` | `L3:111` ✗ | `:110` ✓ | **`L3:110`** |
| `SL_Pct = 0.55` | `L3:111` ✓ | `:111` ✓ | **`L3:111`** |

定案依據（`L3_ConsolidationLong.pla` 原檔 :108-112 實讀）：

```
109: ATR_Length(9),
110: ATR_Stop_Mult(3.0),
111: SL_Pct(0.55),
```

→ `extract_research_L.md` 全對；`extract_live.md` 前兩筆 off-by-one。**本文其他引用 `extract_live.md` L3 input 行號之處，應一律 −1 校正後採用。**

**進場條件複雜度速查（僅 L1–L5，出處 `extract_live.md`）**

| 策略 | 進場 AND 條件數 | 訂單型態 | 進場腿數 |
|---|---|---|---|
| L1 | 5（L1:538-542） | Market | 1 |
| L2 | 7（L2:473-479） | Market | 1 |
| L3 | 10（L3:331 + L3:360-369） | **Stop @ `v_Box_Btm`** | 1 |
| L4 | 10（L4:518 + L4:547-555） | Market | 1 |
| L5 | 6 + 4 個 `v_Allow_Entry` 子條件（L5:499,521-527/531） | **Stop @ `v_Box_Btm` / `v_Mid_Line`** | **2** |

---

## 3. 出場九層矩陣（本文件核心）

九層定義依 `docs/methodology/entry_exit_sop.md`：
`1` 初始停損 ／ `2` 獲利回檔保護 ／ `3` 追蹤停損 ／ `4` 目標停利 ／ `5` 時間停損 ／ `6` 結構失效 ／ `7` 跳空夜盤保護 ／ `8` 行事曆風控 ／ `9` 緊急開關

符號：`✅機制名` = 有且**預設生效**｜`⚠️留碼停用` = 程式碼存在但參數 = 0 / False 使其不執行｜`❌無` = 程式碼完全沒有｜`—類別免除` = 策略結構上不可能暴露於該風險

| 策略 | 1 初始停損 | 2 獲利回檔保護 | 3 追蹤停損 | 4 目標停利 | 5 時間停損 | 6 結構失效 | 7 跳空夜盤保護 | 8 行事曆風控 | 9 緊急開關 |
|---|---|---|---|---|---|---|---|---|---|
| **L1** | ✅三腿 Frozen SL（`MaxList` 價，L1:561-572）+ 引擎 3/3（L1:524-532） | ✅P7 StopProfit 單級保留 45%（門檻 200 pts，L1:578-583） | ✅P4 MA55 − 50 單向棘輪（L1:588） | ❌無固定／ATR／Limit 目標（L1 G 節） | ❌無（L1 I 節「無時間出場」） | ❌無結構性出場 | ✅Gap 分支：`Close < Final_Exit_Price` 時 Stop 轉 **Market**（`TL_SP_Gap`/`TL_SL_Gap`，L1:596-600）；無夜盤專屬機制 | ✅Registry→Holiday→Settlement（L1:636-644） | ✅`TL_Kill`（L1:646-648）ᵃ |
| **L2** | ✅Frozen `DC_Lower + ATR×1.1`，`MinList` Pct（L2:487-496）+ 引擎 3/3（L2:465-470） | ✅`TS_StopProfit` 單級保留 45%（門檻 250 pts，L2:620-632,714-718） | ✅TSL `Lowest(Close[1],9) + ATR×1.0` 單向；需 **2 根連續 C1_Bar** 才 arm（L2:528-532,546-577） | ❌無固定目標 | ❌無固定 N 根上限（L2 I 節） | ✅`TS_StructureTP`（`Close > Highest(Close[1],30)`，L2:700-704）+ `TS_WeeklyExit`（週五 12:45 週線轉多，L2:690-697） | ✅夜盤收盤確認出場：`IsNight ∧ Close > Active_SL` → **Market**（非 Stop，L2:731-739） | ✅Kill→Registry→Holiday→Settlement（L2:667-687） | ✅`TS_Kill`（L2:667-670，P0 第一位） |
| **L3** | ✅Frozen `Box_Btm − ATR_Buffer`，`MaxList` Pct floor（L3:378-398）+ 引擎 3/3（L3:337-342） | ⚠️留碼停用 BE（`BE_Trigger_Pts=0`，L3:131；邏輯 L3:416-425）；**無 SP 模組** | ❌無（全庫唯一完全無 trailing，L3 G 節） | ✅`CL_TP` **Limit** @ `MinList(Swing_High, Box_Top)`，保底改 `Box_Top`（L3:389-392,428） | ❌無（無 `Time_Stop_Bars`） | ✅`CL_BreakExit`（箱型消失 else 分支 → Market，L3:437-443） | ❌無（進場端有開盤禁區，出場端無任何跳空／夜盤保護） | ✅Registry→Holiday→Settlement（L3:451-456） | ✅`CL_Kill`（L3:458-459）ᵃ |
| **L4** | ✅Frozen ATR + 凍箱頂（L4:598-612）+ **SL_Pct cap 套用全路徑含 trail**（L4:624-627）+ 引擎 3/3（L4:508,537-541） | ⚠️留碼停用 BE（`BE_Trigger_Pts=0`，L4:279）+ ⚠️留碼停用 SP（`SP_Trigger_Pts=0`，L4:286） | ✅Trail `MinList(prev, Lowest_Low + ATR×1.0)` 單向；啟動 = MFE 觸及箱底（L4:594-608） | ❌無固定／Limit 目標 | ✅`CS_TimeExit`：`¬Trail_Active ∧ BarsSinceEntry≥60`（L4:693-698） | ✅`CS_BreakExit`（箱型消失 ∧ `Close of Data2 > Locked_Top`，L4:685-690） | ❌**出場端無**（出場鏈 L4:659-717 無任何夜盤分支）；僅**進場端**封鎖 `Night_Block_On=true ∧ 200≤Time<500`（L4:446-448,554）。本層定義為出場向，故判 ❌ | ✅Kill→Registry→Holiday→Settlement（L4:659-682） | ✅`CS_Kill`（L4:659-662，P0 第一位） |
| **L5** | ✅Frozen ATR（價每根重算）→ Stage 1 base stop，`MaxList` Pct floor **僅 Stage 1**（L5:554-613）+ 引擎 3/3（L5:487,514-518） | ✅BE **以部位狀態啟動**（Stage 2/3 掛 `EntryPrice` Stop，L5:676-681,694-697）；⚠️SP 永久停用（`SP_Trigger_Pts=0`，L5:249） | ✅MFE **四階**動態 trail `Highest − 當下ATR × {0.8/1.5/2.0/3.0}`（L5:646-658） | ✅`BL_TP_Bot/Mid` **Limit 分批 40%** @ `Mid`/`Box_Top` − 5 ticks（L5:570-572,594-597） | ✅`BL_TimeExit`：`BarsSinceEntry≥31`，**僅 Stage 1**（L5:636-639） | ✅`BL_BreakExit_Bot/Mid`（箱型消失，用 High/Low 判定，L5:454-457,705-710） | ❌**出場端無**；僅**進場端**深夜 `400≤Time≤500` + 週六 `DOW=6 ∧ Time≥1330`（L5:419-423）。本層定義為出場向，故判 ❌ | ✅Kill→Registry→Holiday→Settlement（L5:576-587） | ✅`BL_Kill_Bot/Mid`（L5:576-578，P0 第一位） |
| **S1** | ✅Frozen `v_EntryATR × 2.75`，`MaxList` SL_Pct floor（S1:414-415,438-444）+ 引擎 3/3（S1:398-400） | ⚠️留碼停用 Trail A（固定鎖利，`Trail_Mode=0`，S1:173；邏輯 S1:459-462）；**無 BE 模組** | ⚠️留碼停用 Trail B（真 ratcheting，`Trail_Mode=0`，S1:463-466）；關閉原因：v2.5 實測 −385K（S1:103-108） | ✅`LX_NM_TP` **Limit** @ `EntryPrice + v_EntryATR×2.0`（**凍結 ATR**，S1:448-449） | ✅`LX_NM_Time`：`500≤Time<1500` → Market（S1:472-475） | ❌無（無反向訊號、無中軌、無結構失效出場） | ❌無（策略設計為**捕捉**隔夜跳空 `Overnight Gap Capture`，S1:3，非防禦） | ✅Kill→Registry→Holiday→Settlement（S1:426-435） | ✅`LX_NM_Kill`（S1:427-428，P0 第一位） |
| **S3_L** | ✅Frozen `EntryPrice − v_Frozen_ATR×2.75`（S3_L:376-382）+ **引擎僅 1/3**（缺 SetStopContract、缺 SL_Pct，S3_L:396） | ❌無（無 BE、無 SP、無 peak retain） | ❌無 trailing | ✅`LX_VS_TP` **Limit** @ `EntryPrice + v_ATR×8.0`（**當下 ATR，非凍結**，S3_L:349,484） | ✅`LX_VS_TimeStop`：`BarNumber − v_EntryBar ≥ 70`（60M → 70 小時，S3_L:495-499） | ✅`LX_VS_Mid` 中軌反向出場（`Close < v_MidBand`，S3_L:487-492） | ❌無 | ✅Kill→Registry→Holiday(`≤455`)→Settlement（S3_L:452-478） | ✅`LX_VS_Kill`（S3_L:452-455，P0-1） |
| **S3_S** | ✅Frozen `EntryPrice + v_Frozen_ATR×3.25`（S3_S:681-686）+ **引擎僅 1/3**（缺 SetStopContract、缺 SL_Pct，S3_S:710，且為單行 if 無 begin/end） | ✅Layer 2 SP **四階 retain 70/80/85/90%**（門檻 0/100/200/300 點**硬編碼**，S3_S:978-989）；出場口 P0.5 市價(S3_S:1006-1013) + S-4 停單(S3_S:1063-1064)；**無傳統 BE** | ❌無獨立追蹤停損模組。Layer 2 SP 的 floor = `EntryPrice − peak × retain/100`（S3_S:988-989）錨定**已實現利潤%**，依 `entry_exit_sop.md:58` 判準（層 3 錨「價格絕對位置」、層 2 錨「帳面利潤%」）**屬層 2 不屬層 3** | ✅`SX_VS_TP` **Limit** @ `EntryPrice − v_ATR×2`（**當下 ATR，非凍結**，S3_S:646,1027）`[不確定]` 與 SP 觸發門檻同值，見 8a-U1 | ✅`SX_VS_TimeStop`：`BarNumber of Data2 − v_EntryBar ≥ 35`（S3_S:1050-1056） | ✅`SX_VS_Mid` 中軌 + 確認棒 + 峰值下限（S3_S:1032-1047） | ⚠️留碼停用（ANTIHUNT L1 夜盤 SL 加寬 `NightSL_Widen_On=False`，S3_S:254；L2 確認式 SL `ConfirmSL_On=False`，S3_S:260；SP 夜盤量能確認 `SP_Night_VolConfirm_On=False`，S3_S:277）— **全庫唯一有夜盤專屬模組，但預設全關** | ✅Kill→Registry→Holiday(`≤455`)→Settlement（S3_S:937-963） | ✅`SX_VS_Kill`（S3_S:937-940，P0-1） |
| **S3_RPS** | ✅Frozen `EntryPrice + v_Frozen_ATR_5M×2.5`（S3_RPS:654-660）+ 引擎結構 3/3（S3_RPS:676-678）；**`SL_Pct=0` cap 未啟用**（S3_RPS:138） | ❌無（無 BE、無 SP） | ❌無（檔頭明載 `Engine SetStopLoss + Frozen SL (no trailing)`，S3_RPS:912） | ✅`SX_RPS_v2_TP`：`TP_Pct=1.0%` 固定 % 目標 **∨** EMA20 結構備援，**Market 單非 Limit**（S3_RPS:792-800） | ✅`SX_RPS_v2_TimeStop` 27 根 5M（S3_RPS:801-804）+ `SX_RPS_v2_DayClose` `Time≥1325`（S3_RPS:773-778） | ❌無獨立結構失效出場（EMA20 備援併入層 4 的 TP 標籤；反向訊號出場：無） | —類別免除（純日盤：進場窗 08:50–12:30、13:25–13:40 強制平倉，結構上不留倉過夜，S3_RPS:702-703,773-778） | ✅Kill→Registry→Holiday(`≤455`)→Settlement（S3_RPS:744-770） | ✅`SX_RPS_v2_Kill`（S3_RPS:744-747，P0-1）**+ 進場端 gate**（S3_RPS:708） |
| **S16_S** | ✅Frozen `EntryPrice + v_Frozen_ATR×4.0`，`MinList` SL_Pct ceiling（S16_S:503-511）+ 引擎 3/3（S16_S:534-541） | ✅BE Trail **兩階閂鎖**：Tier1 鎖 15 點 @2.5ATR、Tier2 鎖 20 點 @3.5ATR，用**當下 ATR**（S16_S:714-743） | ❌無真移動停利（BE 兩階為固定點數鎖利階梯，不隨 peak 移動）；research v1.12.0 才有 Profit Trail | ❌無 TP（檔頭明載 `NO TP (feedback_trend_let_profits_run)`，S16_S:156） | ✅`SX_MA_TimeStop` 24 根 5M（S16_S:752-756）+ P0.5 `SX_MA_TailFlat` 04:40（S16_S:635-639）+ P1b QuickStop_Time 4 根（S16_S:653-659） | ✅`SX_MA_GoldenCross` 反向訊號出場（S16_S:746-749） | ✅`SX_MA_TailFlat`：`440≤Time≤500` → Market，「保證絕不跨盤中休息／週末／假日」（S16_S:635-639；設計意圖註解於 S16_S:631） | ✅Kill→Registry→Holiday→Settlement（S16_S:607-627） | ✅`SX_MA_Kill`（S16_S:607-610，P0-1）**+ 進場端 gate**（S16_S:569/589） |

**腳註 ᵃ**：L1 的 `TL_Kill`（L1:646）與 L3 的 `CL_Kill`（L3:458）機制存在且生效，但寫成 **else-if 鏈外的獨立 `if`**，實際 code 順序為 `Registry → Holiday → Settlement`，Kill 另掛，不符 Rule #11 規定的 `Kill > Registry > Holiday > Settlement`。詳見第 6 節。

### 3(a) 全庫共同缺口

| # | 缺口 | 具體分佈 |
|---|---|---|
| G1 | **層 7 跳空／夜盤保護沒有任何一隻有「已啟用且經實證」的出場端機制** | 出場端真正生效的只有 L1 Gap 市價分支（L1:596-600）、L2 夜盤市價轉換（L2:731-739）、S16_S TailFlat（S16_S:635-639）三種形態且互不相同；L4/L5 只在**進場端**封鎖夜盤（出場鏈無夜盤分支，本層判 ❌）；S3_S 是全庫唯一有夜盤專屬 SL 模組但**預設全關**；L3 / S1 / S3_L **完全無**；S3_RPS 類別免除。→ **無可直接抽取的共用範式** |
| G2 | **層 2 獲利回檔保護只有一半策略生效** | 生效 5（L1 SP 45%、L2 SP 45%、L5 BE、S3_S SP 四階、S16_S BE 兩階）；留碼停用 3（L3 BE=0、L4 BE=0 且 SP=0、S1 Trail A）；完全無 2（S3_L、S3_RPS）。且 5 隻生效者分屬 3 種完全不同型態（峰值 retain% / 移到成本價 / 固定點數鎖利） |
| G3 | **層 3 追蹤停損的錨點三分五裂** | 均線（L1:588）／通道（L2:550）／MFE 極值（L4:607、L5:657）三種錨點，皆錨定「價格絕對位置」符合 `entry_exit_sop.md:58` 對層 3 的定義；完全無 **5**（L3、S3_L、S3_RPS、S16_S、**S3_S**）；留碼停用 1（S1）。**S3_S 的 Layer 2 SP 錨定「已實現利潤%」，依 SOP:58 歸層 2，不計入本層** |
| G4 | **層 5 時間停損：L1 / L2 / L3 三隻完全沒有** | 其餘 7 隻皆有，但計數基準三種（`BarsSinceEntry` / `BarNumber` 差 / `CurrentBar − v_EntryBar`），且 L4 只在 trail 未啟動時生效、L5 只在 Stage 1 生效 |
| G5 | **層 4 目標停利：L1 / L2 / L4 / S16_S 四隻無 TP** | 有 TP 的 6 隻中，ATR 來源分裂：S1 凍結、S3_L / S3_S 當下（S3_L:349、S3_S:646）；S3_RPS 用 %；L3 / L5 用結構價位 |
| G6 | **出場互斥語意（`ExitFired`）四分裂** | 完整 first-hit-wins 1（S16_S）／有 1（S3_RPS）／部分 4（L2 P5-P6 未設、L4 P3 未檢查、S3_L TP 不設、S3_S TP 不設）／**完全無 4**（L1、L3、L5、S1）。同棒 Market + Stop + Limit 並存的實際成交順序**全庫皆為 `[不確定]`** |
| G7 | **層 1 品質不齊：Rule #12 三件套** | 完整 3/3 共 8 隻；**S3_L、S3_S 僅 1/3**（缺 `SetStopContract`）；S3_RPS 結構 3/3 但 `SL_Pct=0` 未啟用。依 Rule #12，缺 `SetStopContract` 在固定 2 口下引擎停損實際窄一半 |
| G8 | **層 8 / 層 9 是唯二 10/10 全有的層**，但參數不一致：`Holiday_Flat_Time` 四種預設（245 / 300 / 345 / 415）、Holiday 掃描 `<` vs `<=`、Holiday 出場上界 `≤455` 有無、Kill 在鏈內 vs 鏈外 | 見第 6 節與第 7 節候選 #1 |

### 3(b) 只有單一策略有的孤例機制

| 孤例機制 | 唯一持有者 | 位置 |
|---|---|---|
| 分批出場（scale-out 40%） | L5 | L5:570-572, 593-598 |
| MFE 多階動態 trail（4 階） | L5 | L5:646-658 |
| 雙進場腿 + `from Entry` 配對出場 | L5 | L5:526-532, 594-597 |
| 三腿初始停損（含 Daily ATR cap leg） | L1 | L1:562-568 |
| 單一停損合併架構（`MaxList` 三 floor） | L1 | L1:590-591 |
| Gap 分支（Stop 單改掛 Market） | L1 | L1:596-600 |
| `[IntrabarOrderGeneration = true]` | L1 | L1:220 |
| Trailing 需 **2 根連續**訊號棒才 arm | L2 | L2:528-532 |
| 夜盤收盤確認出場（Market 而非 Stop） | L2 | L2:731-739 |
| 手動陣列重建週線 SMA（非 data stream） | L2 | L2:388-427 |
| 唐奇安通道錨定初始停損 | L2 | L2:491-492 |
| 開盤波動禁區（09:00–09:45 + `Time=500`） | L3 | L3:346-350 |
| 棒數 cooldown（`Cooldown_Bars=8`） | L4 | L4:258, 548 |
| SL_Pct cap 套用於 **trail 之後**（universal safety net） | L4 | L4:624-627 |
| Trail_Mode 開關（A 固定鎖利 / B 真移動兩型可切） | S1 | S1:452-469 |
| TP 使用**凍結** ATR | S1 | S1:448-449 |
| 固定 % 目標（`TP_Pct`，非 ATR 制） | S3_RPS | S3_RPS:792 |
| 每日最多一單 cooldown | S3_RPS | S3_RPS:636-641, 827-829 |
| 峰值 retain **階梯**（4 級 70/80/85/90%） | S3_S | S3_S:978-985 |
| Hunt 狀態機（ARM / DISARM）+ Gate B 熔斷 | S3_S | S3_S:616-626, 1104-1113 |
| ANTIHUNT 反獵殺三件（夜盤加寬 / 確認式 SL / BWRank guard） | S3_S | S3_S:651-660, 1066-1077, 610-613 |
| Daily MA 比值 band-reject regime filter | S3_S | S3_S:542-563 |
| Re-Entry 狀態機（平倉後同價再掛 stop 單） | S16_S | S16_S:462-485, 580-591 |
| 完整 first-hit-wins `ExitFired` 鏈 | S16_S | S16_S:601-761 |
| 兩階閂鎖式 BE（Tier2 先檢查） | S16_S | S16_S:714-743 |

雙持有機制（不是孤例但也不是共識）：Rule #17 多層 1M 監控（S3_S + S16_S）、進場端 Kill gate（S3_RPS + S16_S）、Min R:R 進場 gate（L3 + L5）。

---

## 4. 停損結構詳表

| 策略 | 初始 SL 公式 | 凍結對象 | `SL_Pct` 值 | `SL_Pct` 基準價（custom / P3b） | `SetStopContract` | `SetStopLoss` | P3b guard | 三件套完整度 |
|---|---|---|---|---|---|---|---|---|
| **L1** | `MaxList(Entry_P − ATR45×1.5, Entry_P − DailyATR×0.5, Entry_P − Entry_P×SL_Pct/100)`（L1:562-568） | **凍價**（`v_Frozen_SL` 存價，L1:568-569） | `0.5`（L1:230） | `Entry_P`（L1:565）／ **`Close`**（L1:529） | 有，**頂層無條件**（L1:524） | 有，兩分支（L1:527-529 / 531-532） | `if MP <= 0`（L1:525，Long ✓） | **3/3** |
| **L2** | `MinList(DC_Lower + ATR×1.1, EntryPrice + EntryPrice×SL_Pct/100)`（L2:491-495） | **凍價**（`SL_Locked` + `BarsSinceEntry=0`，L2:489-496） | `1.25`（L2:132） | `EntryPrice`（L2:495）／ **`Close`**（L2:468） | 有，**在 guard 區塊內**（L2:469）`[不確定]` | 有（L2:470） | `if MarketPosition >= 0`（L2:465，Short ✓） | **3/3**（位置存疑） |
| **L3** | `MaxList(v_Box_Btm − ATR_Buffer, EntryPrice − EntryPrice×SL_Pct/100)`（L3:380-386） | **凍價**（`Freeze_SL_On=true`，L3:128,379-394） | `0.55`（L3:111） | `EntryPrice`（L3:385）／ **`Close`**（L3:341） | 有，**在 `if v_is_in_consolidation` 區塊內**（L3:337）`[不確定]` | 有（L3:342） | `if v_Box_Qualified and MarketPosition <= 0`（L3:338，Long ✓ 但**多一條件**） | **3/3**（guard 多條件 + 位置存疑） |
| **L4** | `MinList(v_Frozen_LockedTop + ATR_Stop_Mult×v_Frozen_ATR, EntryPrice + EntryPrice×SL_Pct/100)`（L4:612, 625-626） | **凍 ATR + 凍箱頂**（價每根重算，L4:599-600） | `1.50`（L4:293） | `EntryPrice`（L4:625）／ **`Close`**（L4:540） | 有，**頂層無條件**（L4:508） | 有（L4:541，但整段在 L4:518 條件內）`[不確定]` | `if MarketPosition >= 0`（L4:537，Short ✓） | **3/3** |
| **L5** | `MaxList(v_Box_Btm − v_Frozen_ATR_Buffer, EntryPrice×(1 − SL_Pct/100))`（Bot 腿）／ Mid 腿同形（L5:602-613） | **凍 ATR**（價每根重算，L5:555-556） | `1.0`（L5:217），**僅套用 Stage 1，runner 不套**（L5:196-197） | `EntryPrice`（L5:611）／ **`v_Box_Btm`（全庫唯一，L5:517）** | 有，**頂層無條件**，註解 `must be outside conditional`（L5:486-487） | 有（L5:518，但整段在 L5:499 條件內）`[不確定]` | `if MarketPosition <= 0`（L5:514，Long ✓） | **3/3** |
| **S1** | `MaxList(EntryPrice − v_EntryATR×2.75, EntryPrice − EntryPrice×SL_Pct/100)`（S1:438-444） | **凍 ATR**（`v_EntryATR`，S1:414-415） | `1.50`（S1:198） | `EntryPrice`（S1:440）／ **`Close`**（S1:396） | 有（S1:399） | 有（S1:400，同一 begin/end） | `if MarketPosition <= 0`（S1:398，Long ✓） | **3/3** |
| **S3_L** | `EntryPrice − v_Frozen_ATR×2.75`（S3_L:378-380） | **凍 ATR**（`v_Frozen_ATR`，S3_L:376-382） | **無此 input**（全檔 grep 0 命中） | — ／ — | **缺** | 有（S3_L:396） | `if MarketPosition <= 0`（S3_L:395，Long ✓） | **1/3** |
| **S3_S** | `EntryPrice + v_Frozen_ATR×3.25`；夜盤乘數後 `v_SL_Level_Effective = EntryPrice + v_Frozen_SL_Dist × v_SL_Mult_Effective`（S3_S:682-688） | **凍 ATR**（ATR 來源 = Data2 60M，S3_S:644,681-686） | **無此 input** | — ／ — | **缺** | 有（S3_S:710，**單行 if 無 begin/end**，S3_S:709-710） | `if MarketPosition >= 0`（S3_S:709，Short ✓） | **1/3** |
| **S3_RPS** | `MinList(EntryPrice + v_Frozen_ATR_5M×2.5, EntryPrice + EntryPrice×SL_Pct/100)`（S3_RPS:656-658, 807-812） | **凍 ATR**（`v_Frozen_ATR_5M`，5M Data1，S3_RPS:654-660） | **`0` = cap 關閉**（S3_RPS:138，註解 `0=off. MC sweep to find convergence` → 尚未 sweep） | `EntryPrice`（S3_RPS:810）／ `[抽取檔未涵蓋]`（engine 端 cap 存在於 S3_RPS:673-674，但基準價未載明） | 有（S3_RPS:677） | 有（S3_RPS:678，同一 begin/end） | `if MarketPosition >= 0`（S3_RPS:676，Short ✓） | **3/3 結構，cap 未啟用** |
| **S16_S** | `MinList(EntryPrice + v_Frozen_ATR×4.0, EntryPrice + EntryPrice×SL_Pct/100)`（S16_S:504-510） | **凍 ATR**（S16_S:503-511） | `1.00`（S16_S:264，有 MC sweep 收斂記錄 S16_S:19-21,142） | `EntryPrice`（S16_S:507）／ **`Close`**（S16_S:536） | 有（S16_S:539） | 有（S16_S:540，同一 begin/end） | `if MarketPosition >= 0`（S16_S:538，Short ✓） | **3/3** |

### 4.1 三件套不完整者逐一列出

| 策略 | 缺項 | 檔案:行號 | 出處抽取檔 |
|---|---|---|---|
| **S3_L** | 缺 `SetStopContract`（全檔 grep 0 命中）；缺 `SL_Pct` input | `strategies\live_simulation\S3_VolSqueezeLong\S3_VolSqueezeLong.pla:396`（僅存 `SetStopLoss`）；guard 於 `:395` | `extract_livesim.md` F 節 + 附錄 2 |
| **S3_S** | 缺 `SetStopContract`（全檔 grep 0 命中）；缺 `SL_Pct` input；且 `SetStopLoss` 為單行 `if` 無 `begin/end`，補 `SetStopContract` 時必須同步補 | `strategies\live_simulation\S3_S_VolSqueezeShort\S3_S_VolSqueezeShort.pla:709-710` | `extract_livesim.md` F 節 + 附錄 2 + 附錄 4 #6；`extract_research_S.md` A-F 節（research 對應行號 `:696-697`） |
| **S3_RPS** | 結構齊全但 `SL_Pct = 0` → `if SL_Pct > 0` 兩處皆不執行，cap 功能未啟用 | `strategies\live_simulation\S3_RapidPullbackShort\S3_RapidPullbackShort.pla:138`；受影響處 `:673`、`:809` | `extract_livesim.md` E / F 節 |
| L4_v16.0（research，非在役） | **0/3**：缺 `SetStopContract`、缺 `SL_Pct` | `strategies\research\L4_ConsolidationShort\L4_v16.0\L4_ConsolidationShort_v16.0.pla:450-451`（僅 `SetStopLoss`） | `extract_research_L.md` 3-F 節 |
| S16_S_10M（封存變體，非在役） | **1/3**：缺 `SetStopContract`、缺 `SL_Pct` | `strategies\research\S16_MACrossShort\S16_MACrossShort_10M\S16_S_10M_MACrossShort.pla:306-307` | `extract_research_S.md` C-F 節 |

依 CLAUDE.md Rule #12 原文：缺 `SetStopContract` → `SetStopLoss` 金額為 TOTAL POSITION 而非 per-contract，固定 2 口下引擎停損實際窄一半。此為規範文字推論，**非本次實測**。

> **重要**：CLAUDE.md Rule #12 括號註記「2026-07-26 發現 L2/L4/L5/S16_S 全部缺漏，已修復」**未含 S3_L / S3_S**。抽取檔在唯讀範圍內查無 S3_S 豁免 ruling → 列入第 8b 表待裁決。

---

## 5. 停利／鎖利結構詳表

| 策略 | TP 型態 | TP 的 ATR 來源 | 追蹤停損機制 | 保本 BE | 階梯 retain% | 時間出場 | 出場互斥機制 |
|---|---|---|---|---|---|---|---|
| **L1** | **無固定 TP**；採「單一停損合併」架構 `Final_Exit_Price = MaxList(Trail, MaxList(SL, SP))`（L1:590-591） | —（無 ATR 目標） | MA55 − `TrailOffset(50)` 單向棘輪（L1:426,588；`Length20=55` L1:233） | **無獨立 BE 模組**（P7 SP armed 後 floor = `Entry + peak×0.45 > Entry`，結構上等效保本，L1:51-55 註解） | **單級 45%**（`stopProfitPoints_Long=200` L1:237、`profitReturnPrcnt_Long=55` L1:238） | **無** | **無**（Section 3 Stop 單與 Section 4 Market 單同棒並存）`[不確定]` |
| **L2** | **無固定 TP**；鏈式出場架構（無 single-stop 合併） | — | TSL `Lowest(Close[1],9) + ATR×1.0`，`MinList` 單向；arm 需 2 根連續 `C1_Bar` + `BarsSinceEntry≥3`（L2:528-532,546-577） | **無** | **單級 45%**（`stopProfitPoints_Shrt=250` L2:117、`profitReturnPrcnt_Shrt=55` L2:118） | **無固定 N 根**（有條件式 `TS_WeeklyExit` 週五 12:45） | **部分**（P0–P4 皆設 `ExitFired`；**P5 / P6 未設**，L2:721-728 / 731-739；因 `IsDay`/`IsNight` 互斥故實務影響為零） |
| **L3** | **固定 Limit** @ `MinList(Swing_High, Box_Top)`，保底條件 `< Mid + ATR` 時改用 `Box_Top`（L3:389-392,428） | —（非 ATR 目標；保底條件用**當下** `v_Current_ATR`，L3:391） | **無**（全庫唯一） | ⚠️留碼停用（`BE_Trigger_Pts=0` L3:131、`BE_Offset_Pts=5` L3:132；邏輯 L3:416-425） | 無 | **無** | **無**（`CL_TP` Limit 與 `CL_SL`/`CL_BE` Stop 同棒並存，L3:428 vs 431/433）`[不確定]` |
| **L4** | **無固定 TP、無 Limit 單** | — | `MinList(v_Stop_Level[1], v_Lowest_Low + Trail_ATR_Mult(1.0)×當下ATR)`，啟動 = MFE 觸及箱底（L4:594-608） | ⚠️留碼停用（`BE_Trigger_Pts=0` L4:279；A/B 實證失敗：`CS_BE` 25 筆 0% WR、殺掉 Top-10 中 4 筆、−435,800，L4:279-282） | ⚠️留碼停用（`SP_Trigger_Pts=0` L4:286；`SP_Retain_Pct=50` inert L4:290） | `Time_Stop_Bars=60`，**僅 trail 未啟動時**（L4:259,693-698） | **部分**（P0–P2 設 `ExitFired`；**P3 停損區塊未檢查旗標**，L4:705-717 → 同棒 Market + Stop 並存）`[不確定]` |
| **L5** | **Limit 分批 40%** @ `v_Mid_Line − 5 ticks`（Bot 腿）／ `v_Box_Top − 5 ticks`（Mid 腿）（L5:510-511,594-597） | —（非 ATR 目標） | **MFE 四階動態** `v_Highest_Since_Entry − 當下ATR × {0.8 / 1.5 / 2.0 / 3.0}`（門檻 `MFE_ATR_Tier_1/2/3 = 3.0/6.0/10.0`，L5:224-226,646-658）；啟動 `High > Box_Top + ATR×2.5`（L5:550-551） | **生效，以部位狀態啟動**：Stage 2/3 自動掛 `EntryPrice` Stop，**無點數／ATR 門檻**（L5:676-681,694-697） | ⚠️SP **永久停用**（`SP_Trigger_Pts=0` L5:249，5 個 A/B 變體全失敗 L5:243-252；`SP_Retain_Pct=50` inert） | `Time_Stop_Bars=31`，**僅 Stage 1**（L5:216,636-639） | **無**（Priority 0 Market 單與 Stage 1/2/3 的 Stop/Limit 單同棒並存；註解 L5:574-575 宣稱 Market 先行但程式碼無法佐證）`[不確定]` |
| **S1** | **ATR 固定目標 Limit** @ `EntryPrice + v_EntryATR × TargetATRMult(2.0)`（S1:448-449,168） | **凍結**（`v_EntryATR`，S1:414-415）— **全庫唯一** | Trail A（固定鎖利，不移動，S1:459-462）+ Trail B（真 ratcheting `v_HighestClose − v_EntryATR×0.7`，S1:463-466）；**`Trail_Mode=0` 兩者預設全關**（S1:173） | **無獨立 BE 模組** | 無 retain% 制（Trail A 為固定鎖利 `Entry + v_EntryATR×(TrailActATR − TrailOffATR)`） | `LX_NM_Time`：`500≤Time<1500` → Market（S1:472-475） | **無**（Priority 0 / SL / TP / Trail / Time 五段各自獨立掛單）`[不確定]` |
| **S3_L** | **ATR 固定目標 Limit** @ `EntryPrice + v_ATR × TargetATRMult(8.0)`（S3_L:484,107） | **當下**（`v_TargetDist = v_ATR × TargetATRMult` 每根重算，S3_L:349）→ TP 價位隨 ATR 漂移 | **無** | **無** | 無 | `MaxBars=70`（60M → 70 小時，S3_L:110,495-499） | **部分**（P0-1~P0-4 + S-2 + S-3 設 `ExitFired`；**S-1 TP 不設**，S3_L:484；S-4 SL 僅在 `ExitFired=0` 時才掛，S3_L:502） |
| **S3_S** | **ATR 固定目標 Limit** @ `EntryPrice − v_ATR × TargetATRMult(2)`（S3_S:1027,202） | **當下**（S3_S:646）`[不確定]` 與 `SP_Trigger_ATRMult=2.0`（S3_S:210）同值同乘數，SP 是否為死碼需 MC12 實測 | Layer 2 SP 峰值回吐地板 `EntryPrice − peak × retain/100`；出場口 P0.5 市價（S3_S:1006-1013）+ S-4 停單（S3_S:1063-1064） | **無傳統 BE**（SP 是「保留 peak X%」型，武裝前完全無保護） | **四階 70 / 80 / 85 / 90%**（`SP_Retain_Pct=70` S3_S:211、Tier1/2/3 = 80/85/90 S3_S:215-217；**門檻 100/200/300 點硬編碼** S3_S:978-985） | `MaxBars=35`（60M，S3_S:205,1050-1056） | **部分**（P0-1~P0-4 + P0.5 + S-0 + S-2 + S-3 設 `ExitFired`；**S-1 TP 不設**，S3_S:1027；S-4 停單不設） |
| **S3_RPS** | **固定 %**：`EntryPrice × (1 − TP_Pct/100)`，`TP_Pct=1.0`（S3_RPS:120,792）**∨** EMA20 結構備援（S3_RPS:793-797）；**Market 單非 Limit**（S3_RPS:798） | **不適用（% 制）** | **無**（檔頭明載 no trailing，S3_RPS:912） | **無** | 無 | `Max_Bars_TimeStop=27`（5M = 135 分，S3_RPS:126,801-804）+ `Daily_Flat_Time=1325` 日盤強制平倉（S3_RPS:129,773-778） | **有**（TP 與 TimeStop 為 `if / else if` 互斥，S3_RPS:800-801；SL 僅在 `ExitFired=0` 時才掛，S3_RPS:807；且有引擎停損墊底） |
| **S16_S** | **無 TP**（檔頭明載 `NO TP (feedback_trend_let_profits_run)`，S16_S:156；全檔無 limit 出場單） | — | **無真移動停利**（BE 兩階為固定點數鎖利階梯，不隨 peak 移動） | **生效，兩階閂鎖**：Tier1 `Entry − 15 pts` @ `v_Profit ≥ 2.5×ATR`；Tier2 `Entry − 20 pts` @ `v_Profit ≥ 3.5×ATR`；Tier2 先檢查且觸發時同時把 Tier1 設 True（S16_S:250-254,714-743）。**使用當下 `v_ATR`，非凍結**（S16_S:718,722） | 無 retain% 制（固定點數 15 / 20，皆 ≥ 10 點滑價門檻） | `MaxHoldingBars=24`（5M = 2 小時，S16_S:259,752-756）+ `Tail_ForceExit_Time=440`（S16_S:280,635-639）+ QuickStop_Time 4 根（S16_S:230,653-659） | **完整 first-hit-wins**（全庫唯一：P0→P6 每層皆設 `ExitFired`，僅 P6 掛停單不設旗標，S16_S:601-761） |

> **參考（非在役）**：research head `S16_S v1.12.0` 已把 BE 改為固定 % 門檻（`BE_Trigger_Pct=0.80`）+ 真保本 `BE_Cost_Pts=10` 停單 + 單層，並新增 P3b Profit Trail（`Trail_Trigger_Pct=1.20` / `Trail_Giveback_Pct=80`），兩條保護腿統一換算成鎖利點數取 max、只發一張停單（v1.12.0:846-851, 865-889）。live_simulation 的 v1.6.2 **不含**這些。

---

## 6. 強制模組合規矩陣

| 策略 | Rule #11 Settlement 7 元素 | Priority 0 順序正確 | Rule #12 三件套 | Rule #15 ASCII | Rule #17 多層監控 | 被驗證腳本覆蓋 |
|---|---|---|---|---|---|---|
| **L1** | **5/7**ᴮ（元素 5 順序偏差 L1:642；元素 7 腳本無法執行） | ✗ **偏差**：Kill 為鏈外獨立 `if`（L1:646），鏈序 = Registry→Holiday→Settlement（L1:636/639/642） | **3/3**（L1:524 / 527-532 / SL_Pct L1:230） | ✅ 100% ASCII | —**不適用**ᶜ | **否**（ASCII 腳本 36/36 PASS 但覆蓋不含 live/；Settlement 腳本 exit 1） |
| **L2** | **6/7**ᴮ（元素 7 腳本無法執行） | ✓ `Kill(L2:667) > Registry(672) > Holiday(677) > Settlement(683)` | **3/3**（L2:469 / 470 / SL_Pct L2:132）— `SetStopContract` 位置存疑 `[不確定]` | ✅ 100% ASCII | —**不適用**ᶜ | **否**（同上） |
| **L3** | **5/7**ᴮ（元素 5 順序偏差 L3:455；元素 7 腳本無法執行） | ✗ **偏差**：Kill 為鏈外獨立 `if`（L3:458） | **3/3**（L3:337 / 342 / SL_Pct L3:111）— guard 多 `v_Box_Qualified`；`SetStopContract` 在條件塊內 `[不確定]` | ✅ 100% ASCII | —**不適用**ᶜ | **否**（同上） |
| **L4** | **6/7**ᴮ（元素 7 腳本無法執行） | ✓ `Kill(L4:659) > Registry(665) > Holiday(671) > Settlement(678)` | **3/3**（L4:508 / 541 / SL_Pct L4:293） | ❌ **違規**：非 ASCII 於 `:507` 與 `:622`，字元 U+00D7（`×`），皆在 `{ }` 註解內。主對話實測 **4 bytes**；`extract_live.md` 記為「2 處」（同一事實的兩種計數：2 個字元 × 2 bytes/字元） | —**不適用**ᶜ | **否**（同上；且 ASCII 腳本 36/36 PASS **並未掃到本檔**，故腳本 PASS 與本檔違規並不矛盾） |
| **L5** | **6/7**ᴮ（元素 4 為間接實作但通過；元素 7 腳本無法執行） | ✓ `Kill(L5:576) > Registry(579) > Holiday(582) > Settlement(585)` | **3/3**（L5:487 / 518 / SL_Pct L5:217）— P3b 基準價用 `v_Box_Btm`（全庫唯一） | ✅ 100% ASCII | —**不適用**ᶜ | **否**（同上） |
| **S1** | **7/7**ᴰ（人工逐行比對，非腳本輸出） | ✓ `Kill(S1:427) > Registry(429) > Holiday(431) > Settlement(433)`（if/else-if 鏈） | **3/3**（S1:399 / 400 / SL_Pct S1:198） | ✅ 0 非 ASCII byte | —**不適用**ᶜ（`extract_livesim.md` I 節明述「無 Rule #17 的 1M 五層 / ANTIHUNT」） | **否**（ASCII 腳本覆蓋不含 live_simulation/；Settlement 腳本 exit 1） |
| **S3_L** | **7/7**ᴰ（人工逐行比對） | ✓ `Kill(S3_L:452) > Registry(458) > Holiday(464) > Settlement(473)` | **1/3** — 缺 `SetStopContract`、缺 `SL_Pct` | ✅ 0 非 ASCII byte | —**不適用**ᶜ | **否**（同上） |
| **S3_S** | **7/7**ᴰ（人工逐行比對） | ✓ `Kill(S3_S:937) > Registry(943) > Holiday(949) > Settlement(958)` | **1/3** — 缺 `SetStopContract`、缺 `SL_Pct`；`SetStopLoss` 單行 if 無 begin/end（S3_S:709-710） | ✅ 0 非 ASCII byte | ✅**有**：1M 五層 11 因子 / 5 類 / 滿分 30 / 3 道 gate（S3_S:718-872） | **否**（同上） |
| **S3_RPS** | **7/7**ᴰ（人工逐行比對） | ✓ `Kill(S3_RPS:744) > Registry(750) > Holiday(756) > Settlement(765)` | **3/3 結構**，但 `SL_Pct=0` 未啟用（S3_RPS:138） | ✅ 0 非 ASCII byte | —**不適用**ᶜ | **否**（同上） |
| **S16_S** | **7/7**ᴰ（人工逐行比對） | ✓ `Kill(S16_S:607) > Registry(612) > Holiday(617) > Settlement(623)` | **3/3**（S16_S:539 / 540 / SL_Pct S16_S:264） | ✅ 0 非 ASCII byte | ✅**有**：1M 五層 5 因子 / 5 類 / 滿分 5 / 2 道 gate（S16_S:662-712）；自承兩 gate 實質等價（S16_S:702） | **否**（同上） |

**腳註 ᴮ / ᴰ — [來源衝突]：兩份抽取檔用了「7 元素」的兩套不同定義**

| 出處 | 定義來源 | 7 個元素 |
|---|---|---|
| `extract_live.md` 檢查 1（用於 L1–L5，標 ᴮ） | `docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md:55-83` | ①`Settlement_Flat_Time(1230)` input ②`v_Settlement_Day` 變數 ③偵測邏輯 ④Entry gate ⑤**Priority 0 出場（第 4 位）** ⑥標籤前綴 ⑦**驗證腳本通過** |
| `extract_livesim.md` 附錄 1（用於 S1/S3_L/S3_S/S3_RPS/S16_S，標 ᴰ） | `scripts/verify_settlement_flat.py:1-10, 46-92` | ①input ②變數宣告 ③`DayOfWeek(Date)=3` ④`DayOfMonth` in [15,21] ⑤策略專屬 label ⑥進場 gate ⑦出場以 `Time >= Settlement_Flat_Time` 閘控 |

兩套定義**不含相同元素**（前者含「Priority 0 順序」與「腳本通過」，後者含 `DayOfWeek`/`DayOfMonth` 細節但不含腳本通過）。因此 **L1–L5 的 5–6/7 與 S 系列的 7/7 不可直接比較**。未自行選邊；模組化前需先確認以哪一份為準。

**腳註 ᶜ — 為何填「不適用」而非「❌」**：CLAUDE.md Rule #17 的適用範圍明訂為「**所有操作於極端波動環境的策略（S3_S、S6、S9 等）**」，並非全庫強制。L1–L5 / S1 / S3_L / S3_RPS 不屬該範圍，因此「沒有 1M 五層監控」是**設計上不適用**，不是合規失敗。

事實層已獨立驗證：以 `ML_` 前綴全庫掃描，L1–L5 / S1 / S3_L / S3_RPS **皆 0 命中**，S3_S = 26 命中、S16_S = 78 命中。

原稿此欄填 ❌，在「合規矩陣」語境下會與 L4 的 Rule #15 真違規視覺等價；且第 6.1 節的 FAIL 清單本來就未收錄任何 Rule #17 項，自相矛盾。已於 2026-08-04 驗收後改為「—不適用」。

### 6.1 FAIL / 偏差項逐項清單

| # | 項目 | 檔案:行號 | 出處抽取檔 |
|---|---|---|---|
| F-01 | L1 Priority 0 順序偏差（Kill 為鏈外獨立 `if`，不符 Rule #11 `Kill > Registry > Holiday > Settlement`） | `strategies\live\L1_TrendLong\L1_TrendLong.pla:646` | `extract_live.md` L1-J / 檢查 1 |
| F-02 | L3 Priority 0 順序偏差（同型） | `strategies\live\L3_ConsolidationLong\L3_ConsolidationLong.pla:458` | `extract_live.md` L3-J / 檢查 1 |
| F-03 | **L4 Rule #15 違規**：U+00D7（`×`）2 處 / 4 bytes，皆在註解 | `strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla:507`、`:622` | `extract_live.md` 檢查 3 + **主對話實測** |
| F-04 | S3_L Rule #12 僅 1/3（缺 `SetStopContract` + `SL_Pct`） | `strategies\live_simulation\S3_VolSqueezeLong\S3_VolSqueezeLong.pla:396` | `extract_livesim.md` 附錄 2 |
| F-05 | S3_S Rule #12 僅 1/3（同上）+ `SetStopLoss` 單行 if 無 begin/end | `strategies\live_simulation\S3_S_VolSqueezeShort\S3_S_VolSqueezeShort.pla:709-710` | `extract_livesim.md` 附錄 2 / 附錄 4 #6；`extract_research_S.md` A-F |
| F-06 | S3_RPS `SL_Pct=0`，百分比 cap 結構存在但未啟用；註解自承尚未做 MC sweep | `strategies\live_simulation\S3_RapidPullbackShort\S3_RapidPullbackShort.pla:138` | `extract_livesim.md` E / F |
| F-07 | L2 Priority 5 區塊未設 `ExitFired`，與 P0–P4 pattern 不一致（因 `IsDay`/`IsNight` 互斥故實務影響為零） | `strategies\live\L2_TrendShort\L2_TrendShort.pla:721-728` | `extract_live.md` L2-J |
| F-08 | L4 Priority 3 停損區塊未檢查 `if ExitFired = 0`，同棒 Market + Stop 並存 | `strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla:705-717` | `extract_live.md` L4-J（同型 pattern 亦見於 L4_v16.0:642-655） |
| F-09 | L3 P3b guard 多一個 `v_Box_Qualified` 條件：箱型存在但不合格時不刷新引擎停損 | `strategies\live\L3_ConsolidationLong\L3_ConsolidationLong.pla:338` | `extract_live.md` L3-F |
| F-10 | L5 P3b `SL_Pct` 基準價用 `v_Box_Btm`，其餘四檔用 `Close`（全庫唯一不一致） | `strategies\live\L5_BreakoutLong\L5_BreakoutLong.pla:517` | `extract_live.md` L5-F；`extract_research_L.md` 6-5 |
| F-11 | `SetStopContract` 放在條件塊內（L2 在 guard 內、L3 在 `if v_is_in_consolidation` 內），與 L5:486 註解 `must be outside conditional` 相反 | `L2_TrendShort.pla:469`、`L3_ConsolidationLong.pla:337` | `extract_live.md` L2-F / L3-F；`extract_research_L.md` 6-4 |
| F-12 | L3 / L4 / L5 的 `SetStopLoss` 位於 `if v_is_in_consolidation` 區塊內，箱型消失時不被呼叫 | `L3:342`（區塊 `L3:331`）、`L4:541`（區塊 `L4:518`）、`L5:518`（區塊 `L5:499`） | `extract_live.md` L3-F / L4-F / L5-F |
| F-13 | **驗證腳本覆蓋斷裂（治理層 FAIL）**：`verify_settlement_flat.py` 實跑在第一個檔 L1 就 `FileNotFoundError`、exit 1（腳本最後修改 2026-06-17 `ee8e14c`，資料夾重構發生在 2026-07-26 `78a8812` / `7e95cb5`）；`verify_pla_ascii.py --strict` 實跑 36/36 PASS exit 0 但覆蓋**不含** live/ 5 檔與 live_simulation/ 6 檔，共 **11 檔漏掃** | `scripts\verify_settlement_flat.py:14-21`（路徑字典過時） | **主對話實測** + `extract_live.md` 檢查 1 + `extract_livesim.md` 附錄 1 |
| F-14 | S3_RPS 治理層：檔頭自承 `PERFORMANCE: NO BACKTEST YET. v2.0 is research-tier only.` 卻位於 `live_simulation/`；CLAUDE.md Rule #14 亦列 `RapidPullbackShort` 為不允許發明的策略名 | `S3_RapidPullbackShort.pla:82` | `extract_livesim.md` 附錄 4 #8 |
| F-15 | S16_S live_simulation（v1.6.2）落後 research head（v1.12.0）六個版本，落後內容 **100% 落在停損停利**（v1.7.1 QS 百分比化、v1.8.0 ATR 通膨串聯防護、v1.11.0 真保本重寫、v1.12.0 成本算術修正 + Profit Trail） | 見第 1.2 節路徑 | `extract_research_S.md` D-3 |
| F-16 | S16_S 版本標示不一致：檔頭 v1.6.2，但 PERFORMANCE 與 Rule 合規區塊仍記 v1.5 數據，v1.6.x 三次改動無對應 CHANGELOG | `S16_S_MACrossShort.pla:5` vs `:7-27, :123-147, :185` | `extract_livesim.md` A 節 + 附錄 4 #7 |
| F-17 | S3_L 註解與程式碼不符（Section 11 表頭寫 `ATR x 3 target` 但 `TargetATRMult=8.0`；寫 `40 bars max hold` 但 `MaxBars=70`；寫 `BuyToCover` 但這是 Long 策略） | `S3_VolSqueezeLong.pla:435-438` vs `:107, :110, :503` | `extract_livesim.md` 附錄 4 #2 |
| F-18 | S16_S re-entry 鏈無次數上限（稽核標 B1「MEDIUM RISK / Status: OPEN / must fix before live_simulation」，至 research v1.12.0 仍未修） | `S16_S_MACrossShort_v1.12.0.pla:464-468`（狀態變數無計數器）；稽核 `S16_S_EXIT_AUDIT_20260729.md:36-41, :74` | `extract_research_S.md` B-K / F-9 |

---

## 7. 模組化候選清單

> **[來源衝突 / 派工前提修正]**：本節原定「以 `extract_research_S.md` 給的 10 項優先序為基礎」，但實際讀完該檔 983 行後，**該檔並無「10 項優先序」章節**（最接近者為 E 節 22 面向的三檔橫向對照表、F 節 9 項 `[不確定]` 清單）。唯一存在的 10 項編號清單是 `extract_livesim.md` 附錄 4「其他發現（記錄不修）」#1–#10。本節改以**跨 4 份抽取檔的實際事實**建構，並在「抽取障礙」欄逐項引用 `extract_livesim.md` 附錄 4 對應編號。

| # | 候選模組 | 現有最佳範式（策略:行號） | 目前有幾隻策略各自實作 | 抽取障礙 | 優先序 |
|---|---|---|---|---|---|
| 1 | **行事曆風控出場鏈**（Holiday / Settlement / Registry） | `S16_S_MACrossShort.pla:607-627`（`extract_livesim.md` 稱其為「5 隻中唯一的完整 first-hit-wins 鏈」） | **10 / 10**（全庫皆有，但無兩隻完全相同） | Holiday 掃描條件 strict `Time<500`（S3_L:277 / S3_S:503 / S3_RPS:352）vs `Time<=500`（S1:285 / S16_S:415 / L1:463）不一致（附錄 4 #3）；Holiday 出場上界 `Time<=455` 有無不一致（附錄 4 #4）；`Holiday_Flat_Time` **四種預設值** 245(S3_RPS:132) / 300(L2:121) / 345(L1:244) / 415（其餘）（附錄 4 #5）；Kill 在鏈內 vs 鏈外（L1:646 / L3:458） | **P0** |
| 2 | **Holiday registry 資料表**（63 筆 TAIFEX 日期 + `Registry_Valid_Until` fail-safe） | `L1_TrendLong.pla:336-412`（`extract_research_L.md` 5.3 明述四個 L head 內容**一致**） | **10 / 10**（每隻各自內嵌一份 80 格陣列 / 63 筆有效日期） | `Registry_Valid_Until = 1270101` 全庫一致（唯一無爭議的常數）；L1 該 input 行號**已定案為 `L1:245`**（原檔實讀，`:246` 是續行註解；見 8a-U30）；陣列本身無 include 機制，PowerLanguage 需以何種方式共用 `[抽取檔未涵蓋]` | **P0** |
| 3 | **Rule #12 P3b 引擎停損三件套**（`SetStopContract` + `SetStopLoss` + `SL_Pct` cap） | `S16_S_MACrossShort.pla:534-541`（`SetStopContract` 在 `SetStopLoss` 之前、guard 方向正確、距離每根重算 + `MinList` SL_Pct） | 完整 **8 / 10**（S3_L、S3_S 僅 1/3；S3_RPS 結構完整但 cap=0） | `SetStopContract` 位置分裂：頂層無條件（L1:524 / L4:508 / L5:487）vs 條件塊內（L2:469 / L3:337）`[不確定]`；`SetStopLoss` 在 `if v_is_in_consolidation` 內（L3:342 / L4:541 / L5:518）`[不確定]`；S3_S 為單行 if 無 begin/end（附錄 4 #6）；**補齊 S3_L / S3_S 等同改變引擎停損寬度 → 須使用者裁決（見 8b-1）** | **P0** |
| 4 | **Frozen 初始停損**（ATR 凍結 + 百分比 cap + flat 解鎖） | `S16_S_MACrossShort.pla:503-511`（凍 ATR + `MinList` SL_Pct ceiling + 進場同步初始化 4 個狀態旗標，S16_S:512-515） | **10 / 10**（形式各異） | **凍結對象不一**：凍價 3（L1:568 / L2:492 / L3:380）vs 凍 ATR 6（L5:555 / S1:414 / S3_L:376 / S3_S:681 / S3_RPS:654 / S16_S:503）vs 凍 ATR + 凍箱頂 1（L4:599-600）（附錄 4 #10）；**SL_Pct 基準價不一**：custom 端全用 `EntryPrice`/`Entry_P`，P3b 端 4 隻用 `Close`、**L5 用 `v_Box_Btm`**（L5:517）；S3_L / S3_S **無 SL_Pct**；SL_Pct 適用範圍不一（L4 含 trail 全路徑 L4:624-627 vs L5 僅 Stage 1 L5:610-614） | **P0** |
| 5 | **出場互斥旗標（`ExitFired` first-hit-wins 鏈）** | `S16_S_MACrossShort.pla:601-761`（全庫唯一完整鏈；僅 P6 掛停單刻意不設旗標） | 完整 1（S16_S）／有 1（S3_RPS）／**部分 4**（L2、L4、S3_L、S3_S）／**完全無 4**（L1、L3、L5、S1） | L1 用「單一停損合併 `MaxList` 三 floor」架構（L1:590-591），與鏈式**不可直接互換**；「停單是否設旗標」語意不同（S16_S:758-760 的 P6 停單刻意不設旗標；S3_L:502 反而只在 `ExitFired=0` 時才掛）；同棒 Market + Stop + Limit 的實際成交順序**全庫皆 `[不確定]`**（8a-U3/U4/U6/U7/U8） | **P1** |
| 6 | **跳空／夜盤保護** | `S3_S_VolSqueezeShort.pla:651-660` + `:688` + `:1066-1077`（ANTIHUNT L1 夜盤 SL 加寬 + L2 確認式 SL）—— **但預設全關**（`NightSL_Widen_On=False` S3_S:254、`ConfirmSL_On=False` S3_S:260） | 出場端生效 3（L1 Gap 分支、L2 夜盤市價轉換、S16_S TailFlat）／僅進場端 2（L4、L5）／**留碼停用 1**（S3_S）／完全無 3（L3、S1、S3_L）／類別免除 1（S3_RPS） | **全庫沒有任何一隻有「已啟用且經回測實證」的夜盤出場保護**，唯一設計完整者（S3_S）預設關閉且無實測數據；L1 的 Gap 分支綁死在其「單一停損合併」架構上；L2 的夜盤定義 `IsDay=(845≤Time≤1245)`（L2:224-232）與其他策略的時段常數不通用 | **P1**（全庫最大缺口，但缺可抽取的範式） |
| 7 | **時間出場**（TimeStop / 收盤與尾段強制平倉） | `S16_S_MACrossShort.pla:635-639` + `:752-756`（TailFlat 時間護欄 + MaxHoldingBars 雙層） | 有 **7 / 10**（L4、L5、S1、S3_L、S3_S、S3_RPS、S16_S）；無 3（L1、L2、L3） | 計數基準三種：`BarsSinceEntry`（L4:694 / L5:637 / S3_RPS:783）、`BarNumber − v_EntryBar`（S3_L:495 / S3_S:1050）、`CurrentBar − v_EntryBar`（S16_S:602）；生效條件不一（L4 僅 trail 未啟動、L5 僅 Stage 1）；**紅線**：S16_S 的 TimeStop 是 alpha 主體（`31 trades exit here with 100% WR / avg +72K`，S16_S:257），任何模組不得截斷 | **P1** |
| 8 | **Kill Switch** | `S3_RapidPullbackShort.pla:708`（進場端 gate）+ `:744-747`（出場端 P0-1） | 出場端 **10 / 10**；**進場端僅 2**（S3_RPS:708、S16_S:569/589）；鏈外獨立 `if` 2（L1:646、L3:458） | Rule #11 要求 Kill 位於 Priority 0 第一位，L1 / L3 不符；把 Kill 加入 8 隻的進場端 = 改動 8 個檔的進場條件 → 須裁決（見 8b-7）；低成本高一致性，但仍會改變同棒下單張數 | **P1** |
| 9 | **結構失效出場**（箱型消失 / 中軌反向 / 反向交叉） | `S3_S_VolSqueezeShort.pla:1032-1047`（中軌 + `MidExit_ConfirmBars` 確認棒 + `MidExit_PeakMinATR` 峰值下限，條件最完整） | 有 **7 / 10**（L2、L3、L4、L5、S3_L、S3_S、S16_S）；無 3（L1、S1、S3_RPS） | 判定資料源不一：L3 / L4 用 `Close of Data2` 解除箱型（L3:285-288 / L4:493-497）、**L5 用 `High/Low of Data2`**（L5:454-457）（`extract_research_L.md` 5.3 明列）；S3_L 的中軌出場**無**確認棒與峰值下限（S3_L:487-492），S3_S 有；S16_S 的 Golden Cross 是指標交叉，與箱型／中軌不同族 | **P2** |
| 10 | **獲利回檔保護（峰值 retain%）** | `S3_S_VolSqueezeShort.pla:965-989`（四階 retain 70/80/85/90 + 兩個出場口：P0.5 市價 / S-4 停單） | 生效 3（L1、L2、S3_S）／留碼停用 2（L4、L5）／無 5（L3、S1、S3_L、S3_RPS、S16_S） | 階梯門檻 100/200/300 點**硬編碼**（S3_S:978-985，附錄 4 #9）；L1 / L2 為單級 45%（`profitReturnPrcnt_*=55`），與四階制不同代數；**L4 / L5 的 SP 是 A/B 實證失敗後永久關閉**（L4:286-289、L5:243-252）→ 模組必須支援「留碼停用」而非強制啟用；S3_S 的 SP 觸發門檻與 TP 目標同值，是否為死碼 `[不確定]`（8a-U1） | **P2** |
| 11 | **保本（Breakeven）** | `L5_BreakoutLong.pla:676-681`（以**部位狀態**啟動，無點數／ATR 門檻）；點數鎖利型另見 `S16_S_MACrossShort.pla:714-743` | 生效 2（L5、S16_S）／留碼停用 2（L3、L4）／無 6 | **啟動基準三種**：部位狀態（L5）／當下 ATR 倍數（S16_S:718,722）／點數門檻（L3:131、L4:279）；S16_S 用**未凍結** ATR → ATR 通膨時保本門檻被推高（稽核 A2，`extract_research_S.md` C-H）；**L3 / L4 的 BE 是實證失敗**（L4:279-282 `CS_BE` 25 筆 0% WR、−435,800；L3 git `a96bf3e revert L3 V15.1 BE` + Lesson L27）→ 模組**不得預設開啟**；research v1.12.0 已把成本常數定為 `BE_Cost_Pts=10`（滑價 1000×2 邊 ÷ 200） | **P2** |
| 12 | **追蹤停損（trailing）** | `L5_BreakoutLong.pla:646-658`（MFE 四階動態，全庫唯一多階；倍數與 MFE 反向 = MFE 越大停損越緊） | 生效 4（L1、L2、L4、L5）＋ S3_S 由 SP floor 兼任／留碼停用 1（S1）／無 4（L3、S3_L、S3_RPS、S16_S） | **錨點三種**：均線（L1:588）／通道 `Lowest(Close[1],K)`（L2:550）／MFE 極值（L4:607、L5:657）—— 三者皆錨「價格絕對位置」，符合 `entry_exit_sop.md:58` 對層 3 的定義。**S3_S 的峰值利潤 floor（S3_S:988）錨「已實現利潤%」，依同一判準屬層 2，不是本模組的候選來源**；ATR 凍結與否不一（L5:657 用**當下** ATR，附錄 4 #10）；arm 條件差異極大（L2 需 2 根連續訊號棒、L4 需 MFE 觸及箱底、L5 需 `High > Box_Top + ATR×2.5`）；**S1 Trail_B 實測 −385K 已永久關閉**（S1:103-108）→ 模組須可整體停用 | **P2** |
| 13 | **Rule #17 多層即時監控**（1M 多因子計分先發制人出場） | `S3_S_VolSqueezeShort.pla:718-872`（11 因子 / 5 類 / 滿分 30 / 3 道 gate） | **2 / 10**（S3_S、S16_S）；無 8 | 分母硬編碼（S3_S:843 分母 30；S16_S:701 分母 5，附錄 4 #9）；S16_S 因「1 類 1 因子」使兩道 gate 實質等價（S16_S:702 自承）；啟動基準不一（S3_S:735-737 用**凍結** SL 距離；S16_S live_sim 用當下 ATR 算的 `v_StopDist`，S16_S:493,878 → 稽核 A3 標 OPEN）；**需 1M feed**（S3_S 有 Data1=1M；其餘 8 隻無 1M feed，導入等於改資料流架構） | **P3** |

---

## 8. 未驗證事項與待使用者裁決

### 8a `[不確定]` 項（承接自 4 份抽取檔，同類已合併，無一消失）

| # | 事項 | 為什麼無法從程式碼判定 | 需要什麼證據才能定案 | 出處 |
|---|---|---|---|---|
| U1 **（rev.2 深化，結論已修正）** | **S3_S 的 Layer 2 SP 是否為死碼** | **主路徑確實被堵，但次路徑仍開，故「死碼」的說法不成立**。詳見下方 U1 補述 | 見下方三個可證偽假設 H-A / H-B / H-C | `extract_livesim.md` 附錄 6 U1；`extract_research_S.md` A-G；rev.2 原檔複讀 S3_S:968-1015, :1027 |
| U2 | **S3_S 的 `1M_Exit` 是否會重複下單** | `v_1M_Trigger` 在 `v_1M_ExitFired = True` 後不再被重置（Section 9.5 整段被 S3_S:718 條件擋掉），而 S-0（S3_S:1016）只檢查 `v_1M_Trigger = True`。訊號棒到成交棒之間若仍持倉，S-0 條件仍成立 | MC12 對同名 `buy to cover next bar at Market` 重複下單的處理行為（實測或官方文件） | `extract_livesim.md` 附錄 6 U2 |
| U3 | **S3_L / S3_S 的 TP limit 單與後續層並存的實際成交順序** | TP 掛單（S3_L:484 / S3_S:1027）不設 `ExitFired`，同一根 K 上可與 Mid/TimeStop 的 market 單、S-4 的 stop 單同時存在。MC12 的單型優先解析規則無法從程式碼確認 | MC12 回測交易明細（同棒多單的成交序） | `extract_livesim.md` 附錄 6 U3；`extract_research_S.md` A-J |
| U4 | **S1 無 `ExitFired` 時多單並存的實際行為** | S1 的 Priority 0 / SL / TP / Trail / Time 五段各自獨立掛單（S1:426-475），同棒可同時存在 market + stop + limit 單 | MC12 實測 | `extract_livesim.md` 附錄 6 U4 |
| U5 | **S1 的 `Time` 在午夜（00:00）棒的實際值** | 進場窗 `Time < 500` 是否包含午夜棒，取決於 MC12 在 24 小時 session 下把午夜棒標成 `0` 還是 `2400`（各檔頭反覆提及的 `MC_Time_24hr` 陷阱，S3_L:57-59） | MC12 圖表上午夜棒的 `Time` 值 | `extract_livesim.md` 附錄 6 U5 |
| U6 | **L1 的 Section 4 安全出場（Market）與 Section 3（Stop）同棒並存的優先序** | Section 4 在程式碼中位於 Section 3 **之後**，兩區塊**無互斥旗標**（不同於 L2/L4 的 `ExitFired`）。同棒可同時掛 Stop 單與 Market 單，實際成交序取決於 MC 引擎的 order-type 排序 | MC12 實測 | `extract_live.md` L1-J |
| U7 | **L3 無 `ExitFired` 時 `CL_TP`（Limit）與 `CL_SL`/`CL_BE`（Stop）同棒並存的成交序** | L3 無互斥旗標；L3:428 與 L3:431/433 同棒掛出，Section 6 的 Market 單亦同棒並存 | MC12 實測 | `extract_live.md` L3-J |
| U8 | **L5 無 `ExitFired` 時 Priority 0 Market 與 Stage 1/2/3 Stop/Limit 並存的成交序** | 註解（L5:574-575）宣稱 Market-type「runs before stop/limit logic in PL engine」，但這是**註解的主張**，程式碼本身無法佐證 | MC12 實測或 PowerLanguage 官方文件 | `extract_live.md` L5-J；`extract_research_L.md` 6-7 |
| U9 | **L4 / L4_v16.0 的 P3 停損區塊缺 `ExitFired` 保護是否為 bug** | P0–P2 都有 `if ExitFired = 0`，P3（L4:705-717 / v16:642-655）沒有，每根都會掛一張 Stop 單。live v14.6 與 research v16 **寫法相同**，故至少不是 v16 新引入 | 設計意圖確認（使用者 ruling）+ MC12 同棒 Market/Stop 仲裁實測 | `extract_live.md` L4-J；`extract_research_L.md` 6-8 |
| U10 | **`SetStopContract` 放在條件塊內是否等價於頂層無條件呼叫** | L2:469（guard 內）與 L3:337（`if v_is_in_consolidation` 內）vs L1:524 / L4:508 / L5:487（頂層），且 L5:486 註解明寫 `must be outside conditional` | MC PowerLanguage 官方文件對 `SetStopContract` 作用域的定義 | `extract_live.md` L2-F / L3-F；`extract_research_L.md` 6-4 |
| U11 | **某根 K 棒未呼叫 `SetStopLoss` 時 MC 引擎的行為（沿用前值 vs 失效）** | L3:342 / L4:541 / L5:518 皆位於 `if v_is_in_consolidation and v_Box_Top > v_Box_Btm` 內，箱型消失時該區塊不執行 → `SetStopLoss` 不被呼叫 | MC PowerLanguage 官方文件 | `extract_live.md` L3-F / L4-F / L5-F |
| U12 | **L3 的 P3b guard 多 `v_Box_Qualified` 的實際風險** | 箱型存在但不合格（`Box_Range/ATR < 8.5`）時不設引擎停損。因該情況也不會進場，理論上無風險，但若**已持倉且箱型變為不合格**，引擎停損不會刷新 | MC12 回測中是否出現該狀態序列 | `extract_live.md` L3-F |
| U13 | **L5 兩條進場腿是否可能同根雙成交形成兩倍部位** | `BL_Entry_Bot`（L5:528）與 `BL_Entry_Mid`（L5:532）同根可同時送出 Stop 單，gate 只檢查 `MarketPosition = 0`（L5:521）。檔內無 pyramiding 宣告 | MC 策略屬性截圖（pyramiding 設定）+ 回測交易明細 | `extract_live.md` L5-K；`extract_research_L.md` 6-2 |
| U14 | **L5 的 P3b 百分比基準用 `v_Box_Btm` 是刻意設計還是筆誤** | L5:517 用 `v_Box_Btm * SL_Pct / 100`，L1:529 / L3:341 / L4:540 皆用 `Close`。檔頭 L5:191-198 未說明此差異 | **使用者 ruling**（另列 8b-2） | `extract_research_L.md` 6-5；`extract_live.md` L5-F |
| U15 | **各策略的實際口數** | 10 隻 `.pla` 內**皆無**口數指定語法（無 `SetPositionSize`、無 `Buy N contracts`；唯一命中是 `SetStopContract` 字串）。「固定 2 口」來自專案 CLAUDE.md，屬 MC 策略屬性設定，**非程式碼證據**。L5 用 `MaxContracts` / `CurrentContracts` 讀取，其分批邏輯完全依賴外部口數設定 | MC12 策略屬性截圖 | `extract_research_L.md` 6-3；`extract_live.md` 各檔 K 節；`extract_livesim.md` 各檔 K 節 |
| U16 | **`Close of Data3` 未用 `[1]` 是否構成規範問題** | L1:445-446 / L3:319-320 / L5:480-481 直接引用當根 `Close of Data3`。專案 CLAUDE.md PowerLanguage 規範第 3 條只點名「Data2 引用用 `[1]`」，未明述 Data3 | 規範文字釐清（使用者 ruling） | `extract_research_L.md` 6-6 |
| U17 | **Priority 0 市價出場相對主出場邏輯的實際優先序** | 四個 L head 的安全出場在程式碼順序上位置不一（L1/L3/L5 在主出場之後，L4 在 `ExitFired` 鏈最前）。實際成交序依賴 MC 引擎「市價單優先於停損單」的行為 | MC12 實測 | `extract_research_L.md` 6-7；`extract_live.md` 檢查 1（該節亦自承「這是推測」） |
| U18 | **L4 的「research head」定義** | `L4_v16.0` 是目錄最新且 git 最後 commit，但 `L4_v16.0_FINAL_VERDICT.md:3` = `KILLED`、`L4_RESEARCH_SUMMARY.md:6` = 研究線 `CLOSED`，live 走 v14.6。若 head = 「當前開發中的下一代」則 **L4 沒有 head** | 使用者對「head」定義的 ruling | `extract_research_L.md` 6-1 |
| U19 | **S3_S 缺 `SetStopContract` / `SL_Pct` 是遺漏還是豁免** | CLAUDE.md Rule #12 列為強制三件套，註記「2026-07-26 已修 L2/L4/L5/S16_S」**未提 S3_S**；檔內 S3_S:661 自稱 `(Rule #12, SHORT variant)` 卻只實作三件之一。唯讀範圍內查無豁免 ruling | 使用者 ruling（另列 8b-1） | `extract_research_S.md` F-1；`extract_livesim.md` 附錄 2 |
| U20 | **S3_S 的 `v_TargetDist` 未凍結是設計還是疏漏** | `v_TargetDist = v_ATR * TargetATRMult` 每根重算（S3_S:646），而 SL 明確凍結（S3_S:681-686）。檔內註解未說明此不對稱 | 使用者 ruling / 設計意圖確認 | `extract_research_S.md` F-2 |
| U21 | **S16_S v1.12.0 的 P3 停單與 P1b 市價單的實際競爭順序** | 檔內 `:42-43` / `:852-853` 宣稱停單能搶在 QuickStop_Time 市價單之前，但 code 順序上 P1b（`:783`）先於 P3（`:884`）且 P1b 會設 `ExitFired`。機制生效須依賴「P3 停單在前一根已掛出」 | MC12 回測 / 訂單生命週期 log | `extract_research_S.md` F-3 / B-J |
| U22 | **S16_S 的 MaxBarsBack 要求（檔頭 200）與 CLAUDE.md（100）衝突** | 5M v1.12.0:300 與 10M:55 都要求 ≥200；CLAUDE.md 技術規格寫 MaxBarsBack = 100 且「回看不得 > 99」。`ZLEMA_Slow=70` 的 XAverage 加 lag 34 合計回看較深 | 使用者 ruling / 規範更新 | `extract_research_S.md` F-4 / B-B |
| U23 | **TXF1 60M ATR 的實際點數未量測** | S3_S 的 SP 武裝門檻（2.0×ATR）、`MidExit_PeakMinATR`、ML 啟動門檻皆為 ATR 倍數制；「換算成點數後是否 ≥ 10 點」的結論是**代數推論**，非實測 | TXF1 60M ATR 的實際統計量 | `extract_research_S.md` F-5 / A-H |
| U24 | **S16_S_10M 變體的回測基準（1 lot / 1,000,000）與全庫（2 lot / 2,000,000）不同** | 檔頭 10M:56 自述。跨檔比較績效必須換算，抽取檔未做該換算 | 換算後的績效重算 | `extract_research_S.md` F-6 / C-A |
| U25 | **`S03 README.md:11` 自述 1107 LOC vs 實測 1110 行** | 3 行落差，可能是 README 未同步或計數方式不同 | 重新計數（不影響邏輯抽取） | `extract_research_S.md` F-7 / 行數校正段 |
| U26 | **`S16_S_10M` 的 `MinSlope = 44` 為 PROVISIONAL** | 檔內 10M:72-74 標明「唯一待 GA 的參數，scan 32-64 step 4，之後 FREEZE」。抽取檔未查到 W3 掃描是否已執行 | W3 掃描結果（目錄內有 `S16_S_10M_W3_SCAN1_20260718.md` 但未讀） | `extract_research_S.md` F-8 |
| U27 | **S16_S re-entry 鏈無上限（稽核 B1）是刻意暫緩還是漏掉** | `S16_S_EXIT_AUDIT_20260729.md:74` 標為「must fix before live_simulation」，但至 v1.12.0 仍未修；commit `a0e778f` 顯示曾嘗試加上限但偏離 ruling 而未採用 | 使用者 ruling | `extract_research_S.md` F-9 / B-K |
| U28 | **S16_S v1.12.0 changelog 記載 `QS_MaxLoss_Pct` 為 0.15% 但 input 預設為 0.25** | `extract_research_S.md` D-2 第 5 項寫 v1.7.1 改為 `QS_MaxLoss_Pct (0.15%)`，而 B-I 節 input 表寫 `QS_MaxLoss_Pct = 0.25`（`:318`）。同一份抽取檔內兩處不一致，無法判定是後續調參還是抄錄錯誤 | `.pla` 原檔 `:318` 重新核對 | `extract_research_S.md` D-2 vs B-I |
| ~~U29~~ **已定案 2026-08-04** | ~~L3 三個 input 的行號~~ | — | 已開 `.pla` 原檔實讀 :108-112 | **定案：`ATR_Length`=L3:109、`ATR_Stop_Mult`=L3:110、`SL_Pct`=L3:111。`extract_research_L.md` 全對；`extract_live.md` 前兩筆 off-by-one。詳見腳註 ᴬ** |
| ~~U30~~ **已定案 2026-08-04** | ~~L1 `Registry_Valid_Until` 的行號~~ | — | 已開 `.pla` 原檔實讀 :242-247 | **定案：`Registry_Valid_Until` = `L1:245`（`:246` 是該 input 的續行註解）。`extract_research_L.md` 正確；`extract_live.md` 的 `L1:246` 錯誤** |
| U31 | **Rule #11「Settlement 7 元素」的定義**`[來源衝突]` | `extract_live.md` 用 `SETTLEMENT_DAY_DESIGN_CONSTITUTION.md:55-83`（含「Priority 0 第 4 位」與「腳本通過」）；`extract_livesim.md` 用 `verify_settlement_flat.py:1-10,46-92`（含 `DayOfWeek`/`DayOfMonth` 細節、不含腳本通過）。兩套不含相同元素 → L1–L5 的 5–6/7 與 S 系列的 7/7 **不可直接比較** | 使用者確認以哪份規範為準 | `extract_live.md` 檢查 1；`extract_livesim.md` 附錄 1 |
| U32 | **L4 非 ASCII 的計數表述**（2 處 vs 4 bytes） | `extract_live.md` 檢查 3 記為「2 處非 ASCII」（`od -c` 驗證 `303 227` = UTF-8 的 U+00D7）；主對話實測記為 **4 bytes**。兩者為同一事實的兩種計數（2 個字元 × 2 bytes/字元），**非矛盾**，但文件用語需統一 | 統一計數單位即可，無需額外證據 | `extract_live.md` 檢查 3 + 主對話實測 |

#### U1 補述（rev.2，原檔複讀後修正）

**SP 不是「武裝即出場」，是兩步機制：**

```
S3_S:972   武裝：v_Peak_Profit_Pts >= v_ATR * SP_Trigger_ATRMult
S3_S:1008  地板：v_SP_Floor_Price = EntryPrice - ( peak * retain / 100 )
S3_S:1010  P0.5：武裝後，還要等 Close 反彈回到 Floor 之上，才發市價單
```

**主路徑被堵（成立）**：TP limit 掛在 `EntryPrice − v_ATR×2`（S3_S:1027），SP 武裝門檻是 `v_ATR×2.0` —— 同價位、同 ATR、同乘數。價格觸及該價位時，掛在那裡的 limit 單即成交；SP 才剛武裝、尚未等到回檔，部位已平。

**歷史佐證**：檔頭記載 GA 把 `SP_Trigger` 由 **1.4 → 2.0**。1.4 時武裝門檻在 TP 之前，SP 是活的；2.0 剛好撞上 TP。這是典型最佳化器產物 —— GA 發現「關掉 SP」分數較好，而在參數範圍內表達「關掉」的唯一方式就是把它推到 ≥ `TargetATRMult`。與 `S16S_exit_module_design_20260804.md` §0 記載的「曲面單調、越鬆越好」為同一病理。

**但次路徑仍開（這是 rev.2 修正的重點）**：`v_ATR` 每根重算，`v_Peak_Profit_Pts` 是**點數**的歷史最大值，兩者脫鉤 ——

1. ATR=100 時價格達 150 點獲利 → 門檻 200 未達，未武裝；TP 在 200 點，未成交
2. ATR 收縮至 70 → 門檻降為 140 → 已入袋的 150 點回頭跨過門檻 → **SP 武裝**
3. 此時價格已回撤至 60 點獲利，TP limit（同樣移到 140）在下方未被觸及
4. Floor = `Entry − 150×0.7 = Entry − 105`，現價 `Entry − 60` 在 Floor 之上 → **P0.5 觸發**

→ 正確表述是「**主路徑被堵、次路徑仍開、發生頻率未知**」，**不是死碼**。

**三個可證偽假設（需 MC12，本文無法自行驗證）**

| # | 假設 | 測法 | 成立代表 |
|---|---|---|---|
| H-A | 現行 2.0 下 `SX_VS_SP` 成交筆數 = 0 | baseline 回測的出場標籤統計 | 主路徑被堵，且次路徑在此樣本內未發生 |
| H-B | `SP_Trigger` = 2.0 / 3.0 / 99 三組**逐筆位元相同** | 退化錨點測試（設計文件鐵則三） | 2.0 已等同關閉，形成高原 |
| H-C | `SP_Trigger` = 1.4 時 `SX_VS_SP` > 0 且結果不同 | 對照組 | 機制本身有效，只是被參數關掉 |

A+B+C 全成立 → 現行參數下實質失效但機制健全；A 成立 B 不成立 → 次路徑有發生但未觸發出場，需細查；A 不成立 → 本補述整段分析錯誤。

**處理建議：不刪碼。** (1) 死的是參數值不是程式碼，1.4 時整條機制是活的，改數字可逆、刪碼不可逆；(2) 次路徑真實存在，而 ATR 收縮往往正是趨勢衰竭訊號，那時鎖利最有價值；(3) GA 的目標函數不等於使用者的目標（`feedback_target_profile_small_win_big_win` 要的是小賺+大賺+小賠，非最大化 PF）。

**結構性修法（若 A+B+C 成立）**：不是刪碼，而是讓最佳化器不能靠碰撞偷偷關掉它 —— 把 `SP_Trigger_ATRMult` 的掃描上界綁在 `TargetATRMult` 之下（如上界 = `TargetATRMult × 0.9`）。要關就明著關。

---

### 8b 待裁決項

| # | 事項 | 兩種可能的處理方式 | 影響範圍 |
|---|---|---|---|
| ~~D1~~ **已裁決並執行 2026-08-04** | ~~S3_L / S3_S 是否補 `SetStopContract` + `SL_Pct`~~ | **使用者裁決：(a) 立即補上。已執行，見 rev.2 §A1/A2。** `SL_Pct` 預設 0（停用）待 MC sweep；`SetStopContract` 已生效 → 引擎停損距離回到設計值（固定 2 口下等於放寬一倍） | S3_L + S3_S。**S3_S 於 2026-07-06 PROMOTE 時的 7/7 gates 是在舊行為下取得的，本次改動後該驗證需重跑** |
| D2 | **L5 的 P3b `SL_Pct` 基準價 `v_Box_Btm`**（承 U14） | **(a) 統一為 `Close`**（與 L1/L2/L3/L4/S1/S16_S 一致）→ 改變 L5 的引擎停損距離。**(b) 認定為刻意設計** → 模組介面須開放「基準價」為策略級參數 | L5 live 檔（與 research head byte-identical，改一邊等於兩邊都要動） |
| D3 | **`SL_Pct` cap 的適用範圍** | **(a) 統一**（全路徑含 trail，比照 L4:624-627 的 universal safety net）或（僅初始停損，比照 L1/L2/L3）。**(b) 模組提供 `scope` 參數**，由各策略自選 | L4（含 trail 全路徑）與 L5（僅 Stage 1，runner 不套）兩隻設計**互為相反**；L1/L2/L3 僅初始停損 |
| D4 | **TP 的 ATR 來源：凍結 vs 當下** | **(a) 統一凍結**（比照 S1:448-449）→ TP 價位不再隨 ATR 漂移，但會改變 S3_L / S3_S 的實際出場價分佈。**(b) 保留為策略級選項** | S1（凍結）／ S3_L:349、S3_S:646（當下）三隻；S3_S 另涉 U1 的 SP 死碼疑慮 |
| D5 | **Priority 0 中 Kill 的位置** | **(a) 移入 else-if 鏈首位**（符合 Rule #11）→ 改變同棒下單張數（原本 Kill 與其他安全出場可能各下一張 Market 單）。**(b) 維持現狀並修訂 Rule #11 文字** | L1:646、L3:458 兩隻 live |
| D6 | **是否全庫導入 `ExitFired` first-hit-wins 語意** | **(a) 全庫導入** → L1 的「單一停損合併 `MaxList` 三 floor」架構（L1:590-591）須整段重寫。**(b) 只在已是鏈式架構的策略導入**，保留 L1 的合併架構為獨立分支 | 完全無旗標 4 隻（L1、L3、L5、S1）＋ 部分 4 隻（L2、L4、S3_L、S3_S）＝ 8 隻 |
| D7 | **是否全庫導入進場端 Kill gate** | **(a) 全部加**（比照 S3_RPS:708 / S16_S:569）→ 8 個檔的進場條件都要改。**(b) 維持只有 2 隻有** | L1、L2、L3、L4、L5、S1、S3_L、S3_S 共 8 隻 |
| D8 | **驗證腳本修復**（承 F-13） | **(a) 修 `verify_settlement_flat.py` 的路徑字典 + 補上 S3_L/S3_S/S3_RPS/S16_S；修 `verify_pla_ascii.py` 的覆蓋清單補上 11 檔**。**(b) 另寫新腳本取代** | 全庫合規稽核的可信度。目前狀態：Settlement 腳本 **exit 1（完全失效）**，ASCII 腳本 36/36 PASS 但**漏掃 11 個最關鍵的檔** |
| D9 | **L4 Rule #15 違規修復**（承 F-03 / U32） | **(a) 把 `×` 改成 `x` 或 `*`** → 純註解改動不影響邏輯，但**會改變 live 檔 hash**，且 L4 live 與 research v16 本就不同版本線。**(b) 暫不動**，僅在模組化新檔中避免 | `strategies\live\L4_ConsolidationShort\L4_ConsolidationShort.pla:507`、`:622` |
| D10 | **S16_S 模組化以哪個版本為基準**（承 F-15） | **(a) 以 research v1.12.0 為準** → 採用「真保本 `BE_Cost_Pts=10` 停單 + Profit Trail 1.20/80 + 兩條保護腿合併成單張停單」的設計。**(b) 以 live_simulation v1.6.2 為準** → 採用「ATR 型兩階 BE 市價單」設計 | 直接決定第 7 節候選 #11（保本）與 #12（追蹤停損）的範式選擇。註：research v1.12.0 的後續設計文件（`docs/research/S16S_exit_module_design_20260804.md`）已**否決 A1 (ATR/Chandelier)** 與 **C2（兩段式收緊）**，並規格化 **A2（結構型移動停利）** |

---

## 9. 附錄：4 份抽取檔的路徑與涵蓋範圍

抽取檔目錄：`C:\Users\WILLYC~1\AppData\Local\Temp\claude\C--Users-WILLY-CHIU\6339f9da-faaf-4075-a0cc-8cc8752b5e23\scratchpad\`

| 檔名 | 派工單宣稱行數 | **實測行數** | 涵蓋範圍 | 抽取方法（檔內自述） |
|---|---|---|---|---|
| `extract_live.md` | 1020 | **1390** | `strategies/live/` 的 L1–L5（5 檔）＋ 跨策略橫向檢查 3 項（Rule #11 Settlement 7 元素、Placeholder 殘留、Rule #15 非 ASCII）＋ 5 隻停損停利對照總表 | 5 個 `.pla` 全文逐行讀取（非抽樣），行號為 Read 工具實際行號 |
| `extract_livesim.md` | 704 | **1061** | `strategies/live_simulation/` 的 S1 / S3_L / S3_S / S3_RPS / S16_S（5 個策略）＋ `IND_S16_S_Monitor`（indicator）＋ 附錄 1–6（Settlement 稽核、Rule #12 稽核、Placeholder/ASCII 掃描、10 項其他發現、5 隻結構對照、5 項 `[不確定]`） | 6 個檔案全文逐行讀取（無抽樣、無推估） |
| `extract_research_L.md` | 626 | **925** | `strategies/research/` 的 L1（v31/v30）／L3（v15/v141）／L4（v16/v15，**v16 KILLED**）／L5（v199/v198）＋ head 判定＋ research vs live 差異對照＋ 跨家族速查表＋ 8 項 `[不確定]` | 唯讀；未編譯、未回測、未修改 repo；`.bak_*` 一律未讀 |
| `extract_research_S.md` | 614 | **983** | `strategies/research/` 的 S03_VolSqueezeShort（v196_ANTIHUNT，head）／S16_MACrossShort（v1.12.0，head）／S16_S_10M（v0.1-PORT，變體）＋ head 判定＋ 版本演進脈絡（D-1/D-2）＋ live_sim 新舊比對（D-3）＋ 三檔橫向對照＋ 9 項 `[不確定]` | 唯讀；所有 `檔案:行號` 為實際 Read 讀到的行號 |

### 9.1 涵蓋缺口（本文件無法回答的範圍）

1. **L2 沒有 research 線資料** —— 4 份抽取檔皆未涵蓋 `strategies/research/L2_*`（若存在）。L2 只有 live 一份實作可供模組化參考。
2. **S16_S live_simulation 與 research 之間的中間版本**（v1.7.1 / v1.8.x / v1.9.0 / v1.10.0 / v1.11.0）僅有 changelog 摘要，無逐行抽取。
3. **`docs/methodology/entry_exit_sop.md` 本身未被讀取** —— 第 3 節的九層欄位名稱來自派工指令，本文未核對 SOP 原文對每一層的精確定義。若 SOP 對某層的定義與本文的歸類不同，第 3 節的分類需重新對齊。
4. **所有 `.pla` 原始碼未被本文件作者讀取** —— 本文 100% 轉載自上述 4 份抽取檔，行號正確性繼承自抽取檔。已知有 2 組行號 `[來源衝突]`（U29 / U30），實際可能還有未被交叉比對到的行號誤差。
5. **無任何績效數字被引用為結論** —— 文中出現的績效數（如 `CS_BE 25 筆 0% WR −435,800`、`TimeStop 31 筆 100% WR avg +72K`、`Trail_B −385K`）皆為抽取檔轉載的**檔內註解／稽核文件記載**，本文未驗證其正確性，僅作為「該機制曾被實證失敗／成功」的來源標記。
