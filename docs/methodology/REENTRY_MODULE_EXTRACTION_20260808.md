---
title: Re-Entry Module Extraction and Spec Reconciliation
created: 2026-08-08
source: S16_S v1.17.0 static read + REENTRY_MODULE_SPEC_20260730.md reconciliation
authority: strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.17.0.pla.bak_20260808
verification_status: NOT verified by MC12 compile or backtest (static code read only)
scope: read-only extraction; no repo file was modified
---

> **POINTER CORRECTION (2026-08-08 evening).** This document was written
> against the ORIGINAL v1.17.0 (the MinSlope-percentage draft). That
> version number was later reused: `S16_S_MACrossShort_v1.17.0.pla` now
> holds the Session Boundary Fill Guard, rebased on v1.16.0. The file
> this document actually read is preserved as
> `S16_S_MACrossShort_v1.17.0.pla.bak_20260808`, and the `authority`
> field above has been repointed there.
>
> Effect on this document's content: the re-entry block it extracts was
> byte-identical to v1.16.0's, so the extraction stays accurate. The
> current v1.17.0 adds two protective gates to that block
> (`v_Tail_Entry_OK`, `v_Sess_LastBar_Block`), which this document does
> not describe.

# Re-Entry 模組抽取與規格對帳（2026-08-08）

## 0. 一句話結論

`REENTRY_MODULE_SPEC_20260730.md` 是一份**忠實描述了一個「已被否決、且檔案已被覆寫」的 v1.9.0 版本**的規格書：它所寫的 `ReEntry_On`、`MaxReEntries`、`v_ReEntry_Count`、P7 guard 對齊、flat-state `v_IsReEntry` 重設 **五項，在今天磁碟上的任何 S16_S 版本中都不存在**（含現行 `S16_S_MACrossShort_v1.9.0.pla`）。照它套用到其他策略，等於實作一個 **S16_S 自己驗證過並拒絕採用**的模組。

**而在做這件事之前，還有一個更根本的問題**：二次進場在 S16_S 上的實證優勢**接近於零**（扣掉單一異常值後每筆期望值 **低於**主進場），且 L1_TrendLong 曾實作過 re-entry 並在 MC9 A/B 測試中被證偽移除（拖累 −920K）。詳見第 2 節。**建議在推廣之前先回答「這個機制真的有 alpha 嗎」，而不是先解決「怎麼移植」。**

---

## 0b. ★ 推廣前必須先看的三個實證數字

| # | 事實 | 出處 |
|---|---|---|
| **1** | S16_S 的 11 筆 re-entry 合計 +648,000，但扣掉 2026-06-09 那筆 +565,600 之後，**每筆期望值僅 +8,240，低於主進場的 +12,913**。v1.6.1 的斜率閘門與 v1.6.2 的方向閘門**從未單獨驗證過** | `docs/research/S16S_entry_side_gap_analysis_20260808.md:128-139, :372` |
| **2** | v1.6.2 研究階段的 10 筆 re-entry 中，**1 筆佔 81.5% 的獲利**（Issue 1, CRITICAL）；且 **10 筆全部落在 2026 年的 5 個月內，2020-2025 零筆**（Issue 2, CRITICAL）。兩項至今列為「待討論」 | `strategies/live_simulation/S16_S_MACrossShort/S16_S_ReEntry_Research_v1.6.2.md:76-105` |
| **3** | **L1_TrendLong 曾實作 re-entry（Plan C），被 MC9 A/B 測試證偽而移除**：假說預期 +2.1M，實測 A+C 合併 Net 3,018K vs Plan A 單獨 3,938K = **−920K 拖累**，69 筆 re-entry 淨值為負。原文歸因：「Re-entry positions hit SL at worse prices than original breakout entries」 | `strategies/live/L1_TrendLong/L1_TrendLong.pla:72-79`（註解）；commit `dc7e7dc` |

> ⚠ **第 3 列的適用範圍限制**：L1 的那次 A/B 是在 **SP500** 上跑的（原文 `L1_TrendLong.pla:74-75`「MC9 path-level backtest (A+C combined, SP500)」），**不是 TXF1**。所以它不能直接當成「re-entry 在台指上無效」的證據。但它的**歸因機制**——二次進場的停損價位比原始突破進場更差——是與商品無關的結構性論點，且 L1 是本 repo 唯一一支有 re-entry 實戰 A/B 數據的策略。**建議把它當成必須被反駁的先驗，而不是已定讞的判決。**

另有一個反向設計事實：**S3_VolSqueezeLong / S3_S_VolSqueezeShort / S3_RapidPullbackShort 三支都刻意用 cooldown 去「阻止」re-entry**（各檔註解，如 `S3_RapidPullbackShort.pla:634, :737, :987`）。也就是說，repo 內對「平倉後再進場」這件事的既有結論，**兩次是負面的（L1 實測、S3 系列設計選擇），一次是統計上未證實的（S16_S）**。

---

## 1. 事實基準（所有結論的證據來源）

| 檔案 | 版本 | 行數 | 角色 |
|---|---|---|---|
| `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.17.0.pla` | v1.17.0 | 2091 | **權威來源**（research head） |
| `strategies/live_simulation/S16_S_MACrossShort/S16_S_MACrossShort.pla` | **v1.6.2** | 771 | 已部署版（`:5` 版本行） |
| `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.9.0.pla` | v1.9.0 | — | 規格書自稱的抽取來源 |
| `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.8.4.pla` | v1.8.4 | — | **已否決**變體，但規格書多項內容實際源自此檔 |
| `docs/methodology/REENTRY_MODULE_SPEC_20260730.md` | v1.0 | 257 | 待對帳的規格書 |

**部署落差（先講最危險的一件事）**：`live_simulation` 上跑的是 **v1.6.2**，只有 `v_ReEntry_Armed` / `v_ReEntry_Price` 兩個變數（`S16_S_MACrossShort.pla:477,483`），**沒有** `v_IsReEntry`、**沒有** `v_Original_Frozen_ATR`、**沒有** ATR 繼承（`S16_S_MACrossShort.pla:504-506` 直接 `v_Frozen_ATR = v_ATR`）。也就是說 v1.8.0 那個「re-entry 繼承 original frozen ATR」的核心修正，**至今未進入模擬部署**。研究 head 與部署版之間隔了 11 個版本。

---

## 2. A 表：規格書 vs v1.17.0 實作逐項對帳

### A-1 §3 Inputs（規格宣稱「Module adds 2」）

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| `ReEntry_On` (True) 主開關 | **不存在** | ✗ | 全 repo 任何 S16_S 版本皆無此 input。模組無法關閉，也無法做 On/Off A-B 對照回測 | 搜遍 `v1.17.0.pla` 0 筆；`v1.7.1`~`v1.17.0` 逐檔 grep 皆 0（唯 `v1.8.4` 有 4 筆，見 A-1a） |
| `MaxReEntries` (1) 鏈上限 | **不存在** | ✗ | 見 D-1。實作無任何計數器 | 同上 |

**A-1a 規格書來源的真相（git 考證）**：規格書並非憑空杜撰，而是**忠實抽取自一個真實存在過、但隨即被否決並覆寫的 v1.9.0**。

- commit `0b037a7`（2026-07-30）一次做了三件事：把 **v1.8.1 從「Cap SL Distance」整個改寫為「P7 Engine Guard Alignment」**、建立 **v1.9.0 module hardening**（含 `v_IsReEntry` 平倉重置、`MaxReEntries` cap、`v_Last_EntryPrice` 移入 lock block、`ReEntry_On` 總開關 + 成交後 disarm）、並新增本規格書。**規格書 §3/§4/§5.3/§5.4/§5.6 的內容，就是那個 v1.9.0 與那個改寫版 v1.8.1。**
- 該 v1.9.0 被判定為 **`MaxReEntries=1` 偏離 2026-07-29 的「B1 = OPEN」裁定**而不採用（`S16_S_EXIT_AUDIT_20260729.md:192`；`S16_S_V180_V190_COMPARISON_20260730.md:23-24, :99-101`）；改寫版 v1.8.1 被判定為「unauthorized, no performance data」（`S16_S_EXIT_AUDIT_20260729.md:191`）。
- 隨後 commit `c3f6479` **用另一個完全不同的 v1.9.0（MinSlope 百分比實驗，base v1.8.0）覆蓋了同名檔案**。所以今天磁碟上的 `S16_S_MACrossShort_v1.9.0.pla` 已經不是規格書的來源，規格書描述的那個版本**只存在於 git 歷史**。

**結論修正**：規格書不是「寫錯」，而是**描述了一條被走過、被評估、被拒絕的路**。任何拿它去套其他策略的動作，等於在重走一條 S16_S 已經否決過的路——而且是在沒有績效數據支持的情況下（v1.8.1 改寫版與 v1.9.0 都沒有 MC12 數據）。

另有一個更早、獨立的實作：v1.8.4 的 **`ReEntry_MaxCount`（預設 1）**（`S16_S_MACrossShort_v1.8.4.pla:295`），配合 `v_ReEntry_Count`（`:383`）、arming gate（`:505`）、death cross 歸零（`:521`）、進場時 +1（`:546`）。v1.8.4 有 MC12 數據，結果是 **−227K**（見 D-2）。

實際 v1.17.0 的 input 區（`v1.17.0.pla:932-1216`）中，**沒有任何一個 input 屬於 re-entry 模組**。

### A-2 §4 Variables（規格宣稱「Module adds 6」）

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| `v_ReEntry_Armed` (False) | 存在 | ✓ | — | `v1.17.0.pla:1295` |
| `v_ReEntry_Price` (0) | 存在 | ✓ | — | `:1296` |
| `v_ReEntry_Count` (0) | **不存在** | ✗ | 無計數器 | — |
| `v_Last_EntryPrice` (0) | 存在 | ✓ | 但賦值位置與規格不同，見 A-4 | `:1297` |
| `v_IsReEntry` (False) | 存在 | ✓ | 但重設點與規格不同，見 A-7 | `:1298` |
| `v_Original_Frozen_ATR` (0) | 存在 | ✓ | 但宣告在 Frozen SL 群組而非 Re-Entry 群組 | `:1246` |

**實際 = 5 個，不是 6 個。** 且 `v_Prev_MP`（`:1239`）是模組運作的必要前提但規格書把它列在 §7 checklist 而非 §4，容易漏。

### A-3 §2 狀態機（狀態數與轉移）

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 |
|---|---|---|---|
| `Armed -> Entry -> In-Position -> Exit -> (Re-Armed or Disarmed)` | 大致成立 | 部分 | 規格圖有 `[Counter < Max?]` 分支節點，實作**沒有這個節點**（`:1782-1795` 進場條件無計數器） |
| 進場後 `v_ReEntry_Armed = False`（§5.4） | **未實作** | ✗ | 進場區塊只設 `v_IsReEntry = True`（`:1793`），**不解除 armed**。後果：armed 在持倉期間維持 True，且 stop 單每根 K 重新掛（見 C 節） |
| Disarm 條件 | 實作有 2 組 | 部分 | `:1658-1663`（golden cross **或** 結構失效）+ `:1665-1668`（death cross）。規格 §5.1 的 pseudo-code 形狀一致 |

### A-4 §5.1 Arming

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| `if v_Prev_MP <> 0 and MarketPosition = 0 and ReEntry_On = True` | `if v_Prev_MP = -1 and MarketPosition = 0` | ✗ | 兩處差異：(a) 硬寫 `-1`，**不是規格宣稱的方向中性**；(b) 無 `ReEntry_On` | `:1653` |
| `v_ReEntry_Price = v_Last_EntryPrice` | 同 | ✓ | — | `:1655` |
| 「NOTE on direction: 方向中性」 | **錯誤** | ✗ | 規格 §5.1 的 NOTE 明講 `v_Prev_MP <> 0` 是 direction-neutral，實作是 `= -1`。做多策略照抄會永遠不 arm | `:1653` |
| Disarm on counter-signal | 同形狀 | ✓ | 實作的 counter-signal = `v_Golden_Cross = True or v_ZLEMA_Fast >= v_ZLEMA_Slow`（**兩個條件的 OR**，規格只寫一個 `[COUNTER_SIGNAL]` 佔位） | `:1658-1663` |
| New primary signal 重設含 `v_ReEntry_Count = 0` | 只重設 armed + price | 部分 | 無計數器可歸零 | `:1665-1668` |

### A-5 §5.2 Frozen ATR Setup

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| `v_Last_EntryPrice = EntryPrice` 放在 `v_SL_Locked = False` 區塊**內** | 放在區塊**外**（`if MarketPosition = -1` 的第一行） | ✗ | §7 checklist 甚至特別寫「Move v_Last_EntryPrice inside」。實作沒照做。S16_S 不加碼，`EntryPrice` 持倉期間恆定，**目前無害**；但對會加碼／分批的策略，`EntryPrice` 是均價會變動，照抄會出錯 | `:1684` vs `:1685` |
| ATR 繼承 if/else | 完全一致 | ✓ | `if v_IsReEntry = True and v_Original_Frozen_ATR > 0 then v_Frozen_ATR = v_Original_Frozen_ATR else begin ... end` | `:1686-1692` |
| 「v_Original_Frozen_ATR 不在 flat block 重設」 | 一致 | ✓ | flat else 區塊 `:1713-1727` 確實沒有它 | `:1713-1727` |

### A-6 §5.3 P7 Engine Guard Alignment

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| `if v_ReEntry_Armed = True and v_Original_Frozen_ATR > 0 then v_Guard_Distance = MinList(v_Guard_Distance, v_Original_Frozen_ATR * StopATRMult)` | **完全不存在** | ✗ | v1.17.0 的 P7 只有 `v_Guard_Distance = v_ATR * StopATRMult`（`:1734`）+ `MinList(v_Guard_Distance, Close * SL_Pct / 100)`（`:1736`）。**沒有任何 re-entry 相關項** | `:1734-1741` |

**追加查證**：這段在現行磁碟的 **v1.9.0 也不存在**（`v1.9.0.pla:577-583`，內容與 v1.17.0 相同，無 re-entry cap）。它的真實出處是 commit `0b037a7` **改寫後的 v1.8.1**（P7 Engine Guard Alignment，base v1.8.0），該版本被判定為「unauthorized, no performance data」而不採用（`S16_S_EXIT_AUDIT_20260729.md:191`），其對應的原始問題是 Issue 4「引擎 SL 對 re-entry 的衝擊，單筆 −152,000」（`S16_S_ReEntry_Research_v1.6.2.md:119-127`）。

**所以 §5.3 是一段有真實動機、但從未取得績效驗證、且已被否決的修正。** 它描述的問題（P7 引擎停損與 P6/ML/BE 用不同 ATR，彼此不對齊）**在 v1.17.0 仍然存在且未修**。

### A-7 §5.4 / §5.6 進場區塊與 Flat 清理

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| 進場 gate 含 `v_ReEntry_Count < MaxReEntries` | 無 | ✗ | 見 D-1 | `:1782-1792` |
| 進場區塊 `v_ReEntry_Count = v_ReEntry_Count + 1` | 無 | ✗ | — | `:1793-1794` |
| 進場區塊 `v_ReEntry_Armed = False` | **無** | ✗ | 這是行為差異，不只是缺欄位。實作讓 stop 單**每根 K 重掛**，且 armed 在持倉中維持 True | `:1793-1794` |
| §5.6 flat else 區塊 `v_IsReEntry = False` | **無** | ✗ | flat 區塊 `:1713-1727` 重設 13 個變數，**沒有 `v_IsReEntry`**。`v_IsReEntry` 全檔只在主進場（`:1771`）設 False、re-entry 進場（`:1793`）設 True | `:1713-1727` |

**追加查證**：v1.9.0 的 flat else 區塊（`v1.9.0.pla:561-570`）同樣沒有 `v_IsReEntry = False`。§5.6 也是從未實作。

### A-8 §6 Exit Integration

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| 「S16_S (Short, 10 layers): QS_Loss -> QS_Time -> ML -> BE -> GoldenCross -> TimeStop -> FrozenSL -> SetStopLoss」 | 實際 **13 個出場標籤**，且列舉漏掉整個 P0 與 P0.5 | ✗ | 實際鏈：Kill(`:1811`) → Registry(`:1816`) → Holiday(`:1821`) → Settlement(`:1827`) → TailFlat(`:1839`) → QS_Loss(`:1850`) → QS_Time(`:1857`) → ML(`:1913`) → **Struct(`:2058`) / Trail(`:2060`) / BE(`:2062`)** → GoldenCross(`:2066`) → TimeStop(`:2072`) → FrozenSL(`:2080`) → SetStopLoss(`:1740`) | `:1810-2083` |
| 「v_Original_Frozen_ATR ... 用於 SL distance, ML activation, BE trigger」 | **BE 已完全不用 ATR** | ✗ | v1.11.0 F6「Removed all ATR dependency from BE module」（`:693`）。v1.17.0 的 BE 觸發是 `v_Profit >= EntryPrice * BE_Trigger_Pct / 100`（`:1948-1950`），Trail/Struct 同為百分比制（`:1952-1958`）。ATR 繼承現在**只影響 2 處**：`v_SL_Level`（`:1693-1694`）與 ML activation（`:1870`） | `:1870, 1693-1694, 1948-1958` |
| 「模組不定義任何出場」 | 成立 | ✓ | 出場鏈確實完全由策略擁有；模組不掛任何出場單 | — |

**A-8 引申結論（重要）**：ATR 繼承這件事的**價值在 v1.8.0 之後被稀釋了**。v1.8.0 的理由是「同時撐寬 SL/BE/ML」（`:700`），但 v1.11.0 把 BE 改成百分比、v1.12.0/v1.13.0 的 Trail/Struct 也是百分比。**如果一支目標策略的出場層已經全是百分比制，ATR 繼承對它幾乎沒有作用**——不要把它當成模組的必備品照搬。

### A-9 §8 Known Constraints

| 規格書宣稱 | v1.17.0 實際 | 一致？ | 差異說明 | 行號 |
|---|---|---|---|---|
| 1. IOG=False assumed | 一致 | ✓ | `[IntrabarOrderGeneration = False]` | `:926` |
| 2. Single re-entry price（只用 last EntryPrice） | 一致 | ✓ | — | `:1655` |
| 3. No re-entry-specific exits | 一致 | ✓ | v1.17.0 出場鏈不讀 `v_IsReEntry`（全檔僅 `:1687` 讀取，在 SL 設定處） | `:1687` |
| 4. P7 cap direction「MinList 對多空皆可」 | **不適用** | ✗ | P7 根本沒有 re-entry cap（A-6）。且此段推論本身有錯：`SL_Pct` 的 cap 在 §7 是 `MinList(v_SL_Level, ceiling)`（`:1697`），做多必須改成 `MaxList(v_SL_Level, floor)`，**不是方向無關** | `:1697, 1734-1736` |

### A-10 明確回答：規格書哪幾節已過時？

| 節 | 判定 | 理由 |
|---|---|---|
| §1 Module Scope | **過時** | 列的 7 項 Module Provides 中，「Counter + MaxReEntries」「P7 guard 對齊」「ReEntry_On 主開關」**3 項不存在** |
| §2 State Machine | **過時** | `[Counter < Max?]` 節點不存在；缺「進場不解除 armed」這個實際行為 |
| §3 Inputs | **完全錯誤** | 宣稱 2 個 input，v1.17.0 實際 **0 個**。兩者只存在於 `0b037a7` 那個被否決並被覆寫的 v1.9.0 |
| §4 Variables | **部分過時** | 宣稱 6 個，實際 5 個（缺 `v_ReEntry_Count`）；`v_Prev_MP` 這個真正的必要前提被放在 §7 checklist 而非 §4，容易漏 |
| §5.1 Arming | **過時且危險** | `v_Prev_MP <> 0` 方向中性的說法與實作 `= -1` 相反；`ReEntry_On` 不存在 |
| §5.2 Frozen ATR | **大致正確** | 唯 `v_Last_EntryPrice` 位置與規格不符 |
| §5.3 P7 Alignment | **未實作於任何存活版本** | 出處是 `0b037a7` 改寫版 v1.8.1，被判「unauthorized, no performance data」而否決；它要處理的問題（P7 與 P6/ML/BE 用不同 ATR）在 v1.17.0 仍存在 |
| §5.4 Entry Block | **過時** | 3 行中有 2 行（counter、disarm）不存在 |
| §5.5 Long vs Short | **嚴重低估** | 宣稱 3 處，實際至少 7 處，見 B-3 |
| §5.6 Flat Cleanup | **未實作** | `v_IsReEntry = False` 不在 flat 區塊 |
| §6 Exit Integration | **過時** | 出場鏈已從 8 層變 13 個標籤；BE 已不用 ATR |
| §7 Checklist | **過時** | 14 項中至少 5 項描述不存在的東西 |
| §8 Known Constraints | **1-3 正確，4 錯誤** | 見 A-9 |

**未過時的只有 §5.2（ATR 繼承本體）與 §8.1-8.3。** 其餘全部需要重寫。

---

## 3. B-1：通用層元素（strategy-independent，可原樣搬）

以下元素**確實不依賴 S16_S 的任何特性**，可原樣移植（行號皆指 `v1.17.0.pla`）。

| 元素 | 型別 | 內容 | 為什麼是通用的 | 行號 |
|---|---|---|---|---|
| `v_ReEntry_Armed` | variable (False) | 是否處於等待二次進場狀態 | 純布林狀態，語意與方向、商品、週期無關 | `:1295` |
| `v_ReEntry_Price` | variable (0) | 二次進場的掛單價位 | 純數值容器 | `:1296` |
| `v_Last_EntryPrice` | variable (0) | 最近一次的實際成交進場價 | 由 `EntryPrice` 內建函數取得，方向無關 | `:1297` |
| `v_IsReEntry` | variable (False) | 本筆交易是否為二次進場 | 純旗標，供下游分歧用 | `:1298` |
| `v_Original_Frozen_ATR` | variable (0) | 主進場當下凍結的 ATR，供 re-entry 繼承 | ATR 本身方向無關（波動度量） | `:1246` |
| **Arming 觸發形狀** | 邏輯區塊 | 「前一根有部位、這一根平倉 → arm，並記下 `v_ReEntry_Price = v_Last_EntryPrice`」 | 「剛出場」這個事件本身是通用的；但**判斷式要改**，見 B-3 | `:1653-1656` |
| **Disarm 形狀（雙條件）** | 邏輯區塊 | armed 期間持續檢查「反向訊號 OR 結構失效」→ 解除並清價位 | 兩段式解除（事件 + 狀態）的結構通用 | `:1658-1663` |
| **新週期重設** | 邏輯區塊 | 主訊號再次出現 → 強制解除 armed、清價位 | 「新週期覆蓋舊週期」的優先權規則通用；也是主進場/二次進場互斥的機制 | `:1665-1668` |
| **ATR 繼承 if/else** | 邏輯區塊 | `if v_IsReEntry and v_Original_Frozen_ATR > 0 → 沿用；else → 重新凍結並存檔` | 完全方向無關，是本模組唯一經過採用驗證的核心邏輯 | `:1686-1692` |
| **「`v_Original_Frozen_ATR` 不在 flat 區塊重設」** | 約束 | 必須跨越出場-再進場的空窗期存活 | 通用不變量 | `:1713-1727`（以「不出現」的方式成立） |
| **執行順序約束** | 約束 | Arming/Disarm 區塊必須排在訊號偵測之後、進場區塊之前 | 保證主訊號能在同一根 K 覆蓋 armed 狀態 | Section 5(`:1633`) → 5.5(`:1646`) → 9(`:1757`) |
| **零回看** | 特性 | 模組本體不使用任何 `[N]` bar offset | 對 MaxBarsBack 零壓力（見 E-4） | `:1653-1668`、`:1782-1795` 實測 0 個 `[` |

**注意：以上「通用」清單裡沒有 `ReEntry_On` 與 `MaxReEntries`——因為它們不存在。若要推廣，這兩者必須當成「新功能」重新設計並回測，不能當成「既有模組的一部分」直接抄。**

---

## 4. B-2：策略專屬掛鉤點（每支必須自己接）

| 掛鉤點 | 需要策略提供什麼 | S16_S 目前怎麼接 | 換一支策略要怎麼改 | 行號 |
|---|---|---|---|---|
| **H1 前一根部位狀態** | 一個在腳本最末行更新的 `v_Prev_MP` | `v_Prev_MP = MarketPosition;`（最後一行） | **必須先加**。L1-L5 全部沒有（見 E-1） | `:2091` |
| **H2 Arming 的方向判斷式** | 「剛從本策略方向的部位出場」的判斷 | `v_Prev_MP = -1` | 做多改 `= 1`；或改成方向中性 `<> 0`（但雙向策略要另外處理方向記憶） | `:1653` |
| **H3 PRIMARY_SIGNAL（新週期）** | 觸發新交易週期的主訊號 | `v_Death_Cross`（ZLEMA 快線下穿慢線） | S3_S 用 squeeze breakout；L5 用 breakout。必須是**離散事件**（該根為 True），不是持續狀態 | `:1665` |
| **H4 COUNTER_SIGNAL（解除）** | 讓二次進場失效的反向訊號 | `v_Golden_Cross`（離散事件） | 對應 H3 的反向 | `:1659` 前半 |
| **H5 STRUCTURE_LOST（解除）** | 結構已不支持該方向的持續狀態 | `v_ZLEMA_Fast >= v_ZLEMA_Slow` | 做多為 `<=`；squeeze 類策略可能是「squeeze 結束」 | `:1659` 後半 |
| **H6 STRUCTURE_INTACT（進場 gate）** | H5 的補集 | `v_ZLEMA_Fast < v_ZLEMA_Slow` | 必須與 H5 嚴格互補，否則會出現「armed 但永不進場」或「已失效仍進場」 | `:1784` |
| **H7 動能 gate** | 與主進場相同的動能門檻 | `v_Slope > v_MinSlope_Eff`（v1.6.1 加入，理由：要求「主動空方動能」而非僅結構） | 各策略自定；**設計原則是「與主進場同一把尺」** | `:1785`、主進場對照 `:1764` |
| **H8 PRICE_GATE 方向** | 掛單方向正確性保護 | `Close >= v_ReEntry_Price`（v1.6.2 加入，確保下一根必須「跌到」該價位） | 做多為 `Close <= v_ReEntry_Price` | `:1786` |
| **H9 進場單型態** | 方向正確的 stop 單 | `sell short ("SE_MA_ReEntry") next bar at v_ReEntry_Price stop` | 做多為 `buy (...) next bar at v_ReEntry_Price stop` | `:1794` |
| **H10 合規 gate 群** | Rule #11 / Kill / Registry / 時段 / 其他濾網 | 6 條：`Time`、`v_Settlement_Day`、`v_Holiday_Block`、`v_Registry_Expired`、`Manual_Kill_Switch`、`v_Gap_Block` | **必須與該策略主進場的 gate 完全一致**（S16_S 是逐條複製的，`:1765-1770` vs `:1787-1792`） | `:1787-1792` |
| **H11 持倉方向判斷** | Frozen SL 區塊的 `MarketPosition` 比較 | `if MarketPosition = -1` | 做多改 `= 1` | `:1683` |
| **H12 SL 方向與 cap** | 停損價位方向 + 百分比 cap 方向 | `v_SL_Level = EntryPrice + dist`；cap 用 `MinList(..., ceiling)` | 做多：`EntryPrice - dist`；cap 用 `MaxList(..., floor)` | `:1694, 1695-1698` |
| **H13 ATR 來源** | `v_ATR` 的計算方式 | `AvgTrueRange(ATR_Len)`，`ATR_Len=14` | 各策略自定；若策略無 frozen ATR 概念，整個 ATR 繼承邏輯不適用（見 E-3） | `:1675, 1140` |
| **H14 出場標籤命名** | 進出場標籤字串 | `SE_MA_ReEntry` | 建議沿用 `<策略前綴>_ReEntry` 慣例 | `:918, 1794` |

---

## 5. B-3：方向相依處驗證（規格 §5.5 宣稱「only 3 places」）

**驗證結果：不成立。v1.17.0 的 re-entry 路徑上，模組自有的方向相依處至少 7 處**（不含 B-2 中本來就標為 hook 的訊號定義）。

| # | 位置 | Short（現況） | Long 需改成 | 規格書有列？ | 行號 |
|---|---|---|---|---|---|
| 1 | Arming 的前部位判斷 | `v_Prev_MP = -1` | `v_Prev_MP = 1` | **✗ 漏列，且規格宣稱此處方向中性** | `:1653` |
| 2 | Frozen SL 區塊的持倉判斷 | `MarketPosition = -1` | `MarketPosition = 1` | **✗ 漏列** | `:1683` |
| 3 | SL 價位方向 | `EntryPrice + v_Frozen_SL_Dist` | `EntryPrice - dist` | ✓ 有列 | `:1694` |
| 4 | SL_Pct cap 方向 | `v_SL_Pct_Ceil = Entry + Entry*SL_Pct/100`；`MinList` | floor + `MaxList` | **✗ 漏列，且 §8.4 誤稱方向無關** | `:1696-1697` |
| 5 | P7 engine guard 的持倉判斷 | `if MarketPosition >= 0` | `if MarketPosition <= 0` | **✗ 漏列** | `:1738` |
| 6 | Price gate | `Close >= v_ReEntry_Price` | `Close <= v_ReEntry_Price` | ✓ 有列 | `:1786` |
| 7 | 進場單 | `sell short ... stop` | `buy ... stop` | ✓ 有列 | `:1794` |

**另有 4 處是 hook 內部的方向相依**（規格把它們歸為策略層，形式上不算模組的，但移植時同樣會出錯）：
- `:1659` disarm 結構條件 `v_ZLEMA_Fast >= v_ZLEMA_Slow`
- `:1784` 進場結構條件 `v_ZLEMA_Fast < v_ZLEMA_Slow`
- `:1785` 斜率符號慣例（`v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast`，**正值代表下跌**，`:1427`）— 做多策略若沿用同一個符號慣例會方向相反
- `:1807-1808` `v_Loss` / `v_Profit` 的符號定義

**合計 11 處。規格書的「3 處」低估了近 4 倍，這是本次對帳中最容易造成真金損失的一項。**

---

## 6. C：狀態機完整定義

### C-1 狀態表示

模組沒有單一 state 變數，狀態由 3 個布林/數值的**組合**表示：

| 狀態 | `v_ReEntry_Armed` | `MarketPosition` | `v_IsReEntry` | 說明 |
|---|---|---|---|---|
| **S0 IDLE** | False | 0 | 任意 | 無部位、未武裝。等待主訊號 |
| **S1 MAIN_POS** | False（通常） | -1 | False | 主進場持倉中 |
| **S2 ARMED** | True | 0 | 沿用上一筆 | 已出場、結構仍在，等待價格回到 `v_ReEntry_Price` |
| **S3 RE_POS** | **True（未被解除）** | -1 | True | 二次進場持倉中 |
| **S4 DISARMED** | False | 0 | 沿用 | 結構失效或反向訊號，週期結束 |

**S3 的 `v_ReEntry_Armed` 維持 True 是實作事實**（進場區塊 `:1793-1794` 不解除），與規格 §5.4 不符。目前無害是因為 P7 沒有讀 `v_ReEntry_Armed`（A-6）；但若照規格補上 P7 cap，這個殘留就會讓 cap 在持倉期間永遠生效——**這是「照規格補程式反而製造 bug」的具體案例**。

### C-2 轉移表

| # | From → To | 觸發條件 | 行號 |
|---|---|---|---|
| T1 | S0 → S1 | 主訊號 + 斜率 + 時段 + 5 條合規 gate 全過 → `sell short next bar at market`；`v_IsReEntry = False` | `:1762-1773` |
| T2 | S1 → S2 | `v_Prev_MP = -1 and MarketPosition = 0`（出場後第一根）→ `v_ReEntry_Armed = True`；`v_ReEntry_Price = v_Last_EntryPrice` | `:1653-1656` |
| T3 | S2 → S4 | `v_Golden_Cross = True` **或** `v_ZLEMA_Fast >= v_ZLEMA_Slow` → armed=False；price=0 | `:1658-1663` |
| T4 | S2 → S0 | `v_Death_Cross = True` → armed=False；price=0（隨即由 T1 進主進場） | `:1665-1668` |
| T5 | S2 → S3 | armed + 結構完好 + 斜率 + `Close >= v_ReEntry_Price` + 5 條合規 gate → `v_IsReEntry = True`；掛 stop 單 | `:1782-1795` |
| T6 | S3 → S2 | 同 T2（出場後再次 arm）→ **可無限循環，見 D-1** | `:1653-1656` |
| T7 | S3/S1 → 出場 | 13 層出場鏈任一觸發 | `:1810-2083` |
| T8 | 任意 → S1 | 任何時候出現 `v_Death_Cross` 且 MP=0，主進場優先 | `:1665` 先於 `:1762` |

### C-3 重設點（哪些事件把狀態歸零）

| 事件 | 歸零什麼 | **不**歸零什麼 | 行號 |
|---|---|---|---|
| **反向訊號 / 結構失效** | `v_ReEntry_Armed`、`v_ReEntry_Price` | `v_IsReEntry`、`v_Original_Frozen_ATR`、`v_Last_EntryPrice` | `:1658-1663` |
| **新主訊號（death cross）** | `v_ReEntry_Armed`、`v_ReEntry_Price` | 同上 | `:1665-1668` |
| **主進場成立** | `v_IsReEntry = False` | — | `:1771` |
| **主進場 fill（進 SL lock）** | `v_Frozen_ATR`、`v_Original_Frozen_ATR` 一起刷新 | — | `:1689-1692` |
| **變成 flat（MP≠-1）** | 13 個交易狀態變數（SL_Locked / Frozen_ATR / SL_Dist / SL_Level / EntryBar / QuickStop / BE / MaxProfit / Trail×2 / Struct×3） | **`v_IsReEntry`（規格要求但未實作）**、`v_Original_Frozen_ATR`（刻意）、`v_ReEntry_Armed`（刻意）、`v_ReEntry_Count`（不存在）、`v_Last_EntryPrice` | `:1713-1727` |
| **新交易日 / 新 session** | **無**。模組完全不感知交易日邊界 | 全部 | — |
| **Priority-0 出場（Kill/Registry/Holiday/Settlement/TailFlat）** | **不特別歸零**。走一般 flat 路徑，所以**仍會 T2 re-arm** | armed 狀態 | `:1811-1843` → `:1653` |

**⚠ 最需要注意的重設缺口**：Priority-0 出場（例如 Settlement 強制平倉、Holiday 強制平倉、TailFlat 收盤前強制平倉）**不會阻止 re-arm**。下一根 K 只要 `v_Prev_MP = -1 and MP = 0` 成立就會武裝。實務上因為進場端有相同的合規 gate（`:1787-1792`），停用期間不會真的進場；但 `v_ReEntry_Armed = True` 會**跨過整個假日/結算日存活**，等禁令解除後在完全不同的市況下用一個舊價位進場。這是靜態讀碼可見的行為，`[不確定]` 的是它在歷史上是否真的觸發過（需 MC12 逐筆檢視才能證實）。

### C-4 邊界情況

**BC-1：同一根 K 同時是「出場根」與「death cross 根」**
執行順序：`:1653` 先 arm → `:1658` 檢查（death cross 根上 fast 剛下穿，`fast >= slow` 為 False，不解除）→ `:1665` death cross 解除 armed → `:1762` 主進場成立、`v_IsReEntry = False` → `:1782` 因 armed=False 跳過。
**結果：主進場勝出，二次進場不會同根重複下單。** 這個互斥完全靠「Section 5.5 排在 Section 9 之前」這一個順序約束，**沒有任何顯式的互斥旗標保護**。移植時若把 arming 區塊放到進場區塊之後，會立刻出現同根雙下單。

**BC-2：同一根 K 同時是「出場根」與「golden cross 根」**
`:1653` 先無條件 arm → `:1658` golden cross 立即解除。
**結果：淨效果為不武裝。** 這是「先無條件 arm、再立刻用結構條件複驗」的設計，順序反過來就會漏掉。

**BC-3：re-entry stop 單掛出但未成交**
`:1793-1794` 不設 `v_ReEntry_Armed = False`，所以下一根若條件仍成立會**重新掛單**（PowerLanguage 的 `next bar` 單只對下一根有效）。若價格跳空穿過 `v_ReEntry_Price` 而未觸發、且收盤跌破該價位，`Close >= v_ReEntry_Price`（`:1786`）失效 → 不再掛單，但 **armed 仍為 True**，等價格漲回該價位之上又會重新掛。這是「掛單漂移」行為，規格書完全沒有描述。

**BC-4：`v_IsReEntry` 在 flat 期間殘留 True**
因為 `:1713-1727` 不重設它。目前無害，理由是：`:1687` 只在 `MarketPosition = -1` 時被讀取，而任何進場路徑都會先寫這個旗標（主進場 `:1771` 寫 False、二次進場 `:1793` 寫 True）。**但這是靠「只有兩個進場入口」這個巧合成立的**，一旦目標策略有第三個進場路徑（例如加碼、反手），就會用到殘留值。

**BC-5：無限鏈中的 ATR 老化**
每次 re-entry 都繼承 `v_Original_Frozen_ATR`（`:1687-1688`），而它只在主進場時刷新（`:1691`）。一條長鏈裡第 N 次 re-entry 用的仍是第 1 次主進場當下的 ATR。鏈越長，凍結 ATR 越陳舊，`v_SL_Level`（`:1694`）與 ML activation（`:1870`）就越偏離當前波動度。**這是 D-1「無上限」問題的實際傷害管道，不只是交易次數多寡的問題。**

**BC-6：`v_ReEntry_Price` 的來源在鏈中會漂移**
`v_Last_EntryPrice = EntryPrice`（`:1684`）取的是**實際成交價**，不是掛單價。所以第 2 次 re-entry 的目標價 = 第 1 次 re-entry 的實際成交價（含滑價/跳空），與主進場價不同。鏈越長，`v_ReEntry_Price` 離原始主進場價越遠。規格 §8.2 說「Single re-entry price: Uses last EntryPrice only」，字面正確但沒點出這個漂移。

---

## 7. D：已知缺陷與已修紀錄

### D-1 ★ 重點查證：re-entry 鏈無上限，v1.17.0 修了沒？

**答案：沒有修。v1.17.0 仍然完全沒有鏈上限。**

證據（逐檔 grep `MaxReEntries|ReEntry_On|v_ReEntry_Count`，排除 `.bak_*`）：

| 版本 | 命中數 |
|---|---|
| v1.7.1 / v1.8.0 / v1.8.1 / v1.8.2 / v1.8.3 | 0 |
| **v1.8.4** | **4** |
| v1.9.0 / v1.10.0 / v1.11.0 / v1.12.0 / v1.13.0 / v1.14.0 / v1.15.0 / v1.16.0 / **v1.17.0** | **0** |

- v1.17.0 的進場 gate（`:1782-1792`）有 10 個條件，**沒有一個是計數器**。
- 唯一存在過的實作是 **v1.8.4 的 `ReEntry_MaxCount`（預設 1）**：宣告 `v1.8.4.pla:295`、變數 `v_ReEntry_Count` `:383`、arming gate `if v_ReEntry_Count < ReEntry_MaxCount` `:505`、death cross 歸零 `:521`、進場時 `+1` `:546`。**v1.8.4 未被採用**。
- v1.17.0 自己的版本註解白紙黑字承認：v1.8.0「**Solves: A1 + A2 + A3. Does NOT solve: B1 (chain limit)**」（`v1.17.0.pla:705`）。而 v1.8.4 的註解寫「Solves: A1 + A2 + A3 + B1 (all four issues)」（`v1.8.4.pla:18`）。
- 也就是說：**被採用的方案是四個問題裡只解三個的那一個，B1 被明知而放棄，之後九個版本沒有人回頭補。**

**B1 的原始稽核記載**（`strategies/research/S16_MACrossShort/S16_S_EXIT_AUDIT_20260729.md`）：
- `:34-41` 問題定義：Group B / **B1 Unbounded Re-Entry Chain / MEDIUM RISK / Status: OPEN**。出場後在 re-entry 自己的 `EntryPrice` 重新 arm；無次數上限，唯一控制是空頭結構閘門（ZLEMA + MinSlope）；持續空頭趨勢反覆洗盤時，多次 re-entry 會在逐次膨脹的 ATR 下累積虧損。
- `:71-76` Resolution Priority：**`2. B1 (chain limit) — must fix before live_simulation`**，排在 A1 之後、A2+A3（should fix）之前。
- `:223`「**B1 chain limit: NOT resolved by v1.8.0** — remains open issue」；`:234`「B1: OPEN — deferred to future version」。
- `:198-200`（2026-08-01 定案）：「Open items deferred to future: B1 chain limit（`MaxReEntries` concept valid but needs separate discussion）」。

**盤點文件的記載與本次更正**：
- `docs/research/strategy_logic_inventory_20260804.md:386`（F-18）：「S16_S re-entry 鏈無次數上限（稽核標 B1 must fix before live_simulation），**至 research v1.12.0 仍未修**」，證據指向 `S16_S_MACrossShort_v1.12.0.pla:464-468`。
- 同檔 `:444`（U27）列為未決事項：「**是刻意暫緩還是漏掉**」，解法欄寫「**使用者 ruling**」。
- **本次更正：F-18 的「至 v1.12.0」低估了。實測至 v1.17.0（2026-08-08 head）仍未修。**
- `docs/handoffs/HANDOFF_S16S_V1160_ADOPTED_20260808_EOD.md:166` 把它排入 Next 清單第 3 順位（「二次進場四個開關 + 失效測試」，排程 v1.17.0、4 次回測），但 **v1.17.0 實際做的是 MinSlope 百分比化，這一項沒做**。

**repo 內出現過的三種修法，全部沒有存活**：

| 方案 | 內容 | 出處 | 結局 |
|---|---|---|---|
| v1.8.4 Option 5 | 「max 1 re-entry per death cross」，與獨立出場框架綁在一起 | `S16_S_EXIT_AUDIT_20260729.md:119` | **否決（MC12 −227K，見 D-2）** |
| v1.9.0 FIX 2 | `MaxReEntries = 1` input + `v_ReEntry_Count`，每個 death-cross 週期重置 | commit `0b037a7` | **否決（偏離 B1=OPEN 裁定），檔案已被 `c3f6479` 覆寫** |
| 早期 Issue 1 方案 B | `MaxReEntryPerCycle = 1` | `S16_S_ReEntry_Research_v1.6.2.md:90` | 未實作 |

**沒有 input 可用、沒有預設值可報。** 若要推廣，鏈上限必須從頭設計，並重跑回測——因為加上限**會改變交易母體**，v1.16.0/v1.17.0 的所有績效數字都不再適用。**且必須先取得使用者 ruling**：U27 已把這件事定性為需要 ruling，而非工程判斷。

### D-2 v1.8.0~v1.8.4 五個變體：採用哪一個？

**採用 v1.8.0（Option 1: Inherit Frozen ATR）。** 證據：v1.8.0 的 fix 是唯一被帶進後續版本的——`v1.9.0.pla:542-546`、`v1.12.0.pla:622-626`、`v1.16.0.pla:1607-1611`、`v1.17.0.pla:1686-1692` 都保留 `{ v1.8.0: re-entry inherits original frozen ATR }` 這段程式碼與註解；v1.8.1/8.2/8.3/8.4 的特有元素在 v1.9.0 之後全部消失。

五個變體由 commit `77f9050`（2026-07-29）一次建立，目的是隔離 A/B 回測，對照組為 v1.6.2 baseline 與 v1.7.1（`QS_MaxLoss_Pct=0.25`）。方案與結局如下（主要證據：`S16_S_EXIT_AUDIT_20260729.md:82-132, :145-253`）：

| 版本 | 方案 | 解決的問題 | 新參數數 | MC12 結果 | 結局 |
|---|---|---|---|---|---|
| **v1.8.0** | Option 1: Inherit Original Frozen ATR | A1+A2+A3 | **0** | 與 v1.7.1 逐筆相同 | **採用**（2026-08-01 使用者定案為 definitive version，commit `53bd108`） |
| v1.8.1 | Option 2: Cap Re-Entry SL at Main Entry SL Distance（`MinList` 封頂） | A1 | 0 | 與 v1.7.1 逐筆相同 | 否決 |
| v1.8.2 | Option 3: Separate Multiplier `ReEntry_StopATRMult = 2.0`（主 4.0） | A1 | 1 | 與 v1.7.1 逐筆相同 | 否決 |
| v1.8.3 | Option 4: Pure Percentage SL `ReEntry_SL_Pct = 0.50%`，完全不用 ATR | A1 | 1 | 與 v1.7.1 逐筆相同 | 否決 |
| v1.8.4 | Option 5: Full Redesign（固定 % SL／ML 停用／固定 % BE／`ReEntry_MaxHold=12`／chain limit 1） | A1+A2+A3+**B1** | 3-4 | **Net +2,413K → +2,186K（−227K）、PF 1.773 → 1.700** | 否決 |

**否決理由（皆有數據，非推測）**：

| 變體 | 理由 | 出處 |
|---|---|---|
| v1.8.1 / v1.8.2 / v1.8.3 | MC12 實測**與 v1.7.1 在 7.5 年內逐筆完全相同**（零差異），但只修 A1。v1.8.0 同樣零成本卻一次修掉 A1+A2+A3，且**新增 0 個參數**（v1.8.2/v1.8.3 各需 1 個待最佳化參數）。**在效果相同時，選參數最少的那個** | `S16_S_EXIT_AUDIT_20260729.md:147-154, :226-228` |
| v1.8.4 | **唯一有差異、且是負的**。根因是 `ReEntry_MaxHold = 12` 太激進，把 3 筆本可續抱到 24 根的 re-entry 提早砍掉（`SX_MA_TimeStop 26→24`、`SX_MA_RE_TimeStop 0→3`、`SX_MA_GoldenCross 4→3`）。決定性的一點：**Gross Loss 完全沒改善（−3,122K 不動）**，代表新增的防禦機制一筆虧損都沒救到，純粹只砍掉獲利 | `S16_S_EXIT_AUDIT_20260729.md:155-176` |
| （`0b037a7` 改寫版 v1.8.1，P7 guard alignment） | 「unauthorized, no performance data」 | `S16_S_EXIT_AUDIT_20260729.md:191` |
| （`0b037a7` 的 v1.9.0 module hardening） | `MaxReEntries=1` 偏離 2026-07-29 的 B1=OPEN 裁定 | `S16_S_EXIT_AUDIT_20260729.md:192`；`S16_S_V180_V190_COMPARISON_20260730.md:23-24, :99-101` |

**v1.8.4 的設計論點**（`v1.8.4.pla:8-18`）：「Re-entry = verification trade（洗盤結束、趨勢回復）。對了就快速獲利，錯了就快速出場」，因此用 `v_IsReEntry` 分岔整個出場框架。**這個論點被 MC12 否證了**——這對推廣有直接意義：**「二次進場需要更緊的出場」這個直覺，在 S16_S 上已經被實測推翻過一次。**

**v1.8.0 為何零差異**（`S16_S_V162_V171_V180_COMPARISON_20260729.md:109-125`）：8 筆 re-entry 全部經由百分比制 QuickStop 或 K 棒數制 TimeStop/GoldenCross 出場，ATR 相關機制（SL/BE/ML）**根本沒被觸發到**。所以 v1.8.0 的定位是「**結構保險**」，不是績效改善。**這一點必須帶進推廣決策：ATR 繼承在 S16_S 的實測貢獻是 0 元。**

### D-3 出場標籤 `SX_MA_RE_*` 的設計理由與現況

**現況：已不存在於任何在役或 head 版本。**

全 repo grep（排除 `.bak_*`、`archive/`）只有 5 筆命中：
- `S16_S_MACrossShort_v1.8.4.pla:232`（`SX_MA_RE_BE` 標籤說明）
- `S16_S_MACrossShort_v1.8.4.pla:233`（`SX_MA_RE_TimeStop` 標籤說明）
- `S16_S_MACrossShort_v1.8.4.pla:770`（`buy to cover ("SX_MA_RE_BE")`）
- `S16_S_MACrossShort_v1.8.4.pla:814`（`buy to cover ("SX_MA_RE_TimeStop")`）
- `S16_S_EXIT_AUDIT_20260729.md:170`（「SX_MA_RE_TimeStop: 0 -> 3 (NEW: re-entry 12-bar exit)」）

**設計理由（白紙黑字寫在 commit `df173c7` 訊息中，2026-07-29 15:12）**：「MC12 can now distinguish re-entry vs main exits in trade report」。該 commit 只動 1 個檔、4 增 2 刪，做了兩組改名——`SX_MA_BE_Trail1 → SX_MA_RE_BE`、`SX_MA_TimeStop → SX_MA_RE_TimeStop`，**主進場路徑保留原標籤**。也就是說標籤分岔的動機是**回測歸因能力**，而不是交易邏輯本身。

之所以需要它，是因為 v1.8.4 讓 re-entry 走一套獨立的出場參數（BE 用固定 0.25%、TimeStop 用 12 bars 而非 24）。**v1.8.4 被否決後（−227K），這組標籤隨之死亡**——`df173c7` 是它唯一的一次生命。

**v1.17.0 的現況**：re-entry 與主進場**共用同一組出場標籤**（`:1810-2083` 沒有任何 `RE_` 變體），所以在 MC12 交易清單裡**無法從出場標籤區分一筆交易是不是二次進場**——只能從進場標籤 `SE_MA_ReEntry`（`:1794`）辨識。這與規格 §8.3「No re-entry-specific exits」一致，但代價是**歸因能力受限**。

### D-4 其他 re-entry 相關問題盤點

**先講一個反直覺的結果**：任務指定的三份稽核/交接文件，**各自只有 1 處提到 re-entry，且沒有一處是缺陷**。

| 文件 | re-entry 相關內容 | 性質 | 檔案:行號 |
|---|---|---|---|
| `docs/research/S16S_v1140_code_architecture_audit_20260806.md`（443 行） | 確認「二次進場（`v_IsReEntry = True`）走同一段狀態重置程式碼，因此也會完整歸零」，符合 v1.12.0 F5 設計要求 | **PASS（非缺陷）** | `:83-84` |
| `docs/research/S16S_v1150_deep_audit_20260806.md`（400 行） | 標籤表列出 `SE_MA_ReEntry`（`sell short` / stop 單 / ExitFired 欄位為「—（進場）」），列入「14 個標籤全部合規」 | **PASS（非缺陷）** | `:175` |
| `docs/handoffs/HANDOFF_S16S_V1160_ADOPTED_20260808_EOD.md`（237 行） | Next 清單第 3 順位：「二次進場四個開關（`ReEntry_On` / 三道閘門 / `ReEntry_Max_Chain`）+ 失效測試」，排程 v1.17.0、4 次回測 | **待辦，未修** | `:166` |

兩份稽核文件各自的真發現（v1.14.0 的 A-1~A-8、v1.15.0 的 B-1~B-6）**沒有任何一項與 re-entry 有關**。

> ⚠ **文件用詞問題**：Handoff `:166` 把 `ReEntry_Max_Chain` 寫成「已存在、待失效測試的開關」，但該識別字在全 repo 的 .pla 中**零命中**（規格書用的名字是 `MaxReEntries`，v1.8.4 用的是 `ReEntry_MaxCount`）。實際情況是「這四個開關要**新增**」，不是「要**測**」。`[不確定]` — 這是撰寫用詞不精確，還是撰寫者誤以為已存在，文件本身沒有說明。

**「re-entry 鏈無上限」的記載不在那三份文件裡**，而在 `docs/research/strategy_logic_inventory_20260804.md:386`（F-18）與 `:444`（U27）——已完整引用於 D-1。

### D-4a 其他文件中的 re-entry 問題（完整盤點）

| 問題 | 嚴重度 | 稽核版本 | 已修/未修 | 檔案:行號 |
|---|---|---|---|---|
| A1 Initial SL Widened（re-entry 繼承膨脹 ATR，最大虧損達主進場 178%） | must fix | v1.7.1 | **已修（v1.8.0）** | `S16_S_EXIT_AUDIT_20260729.md:16-21, :231` |
| A2 BE Trailing Activation Delayed（2.14x） | should fix | v1.7.1 | **已修（v1.8.0）** | `S16_S_EXIT_AUDIT_20260729.md:22-27, :232` |
| A3 Multi-Layer Activation Delayed（2.14x） | should fix | v1.7.1 | **已修（v1.8.0）** | `S16_S_EXIT_AUDIT_20260729.md:28-32, :233` |
| **B1 Unbounded Re-Entry Chain** | **must fix before live_simulation** | v1.7.1 | **未修（至 v1.17.0）** | `S16_S_EXIT_AUDIT_20260729.md:34-41, :71-76, :223, :234` |
| D2 `v_ReEntry_Armed` 成交後未重置（語意不潔，功能安全） | LOW | v1.7.1 | **未修**（v1.9.0 FIX 4 曾修，版本被棄） | `S16_S_EXIT_AUDIT_20260729.md:59-61, :235` |
| Issue 1 統計脆弱：10 筆 re-entry 中 1 筆佔 81.5% 獲利 | **CRITICAL** | v1.6.2 | **待討論** | `S16_S_ReEntry_Research_v1.6.2.md:76-91` |
| Issue 2 樣本集中：10 筆全在 2026 年 5 個月內，2020-2025 零筆 | **CRITICAL** | v1.6.2 | **待討論** | `S16_S_ReEntry_Research_v1.6.2.md:93-105` |
| Issue 3 Order-Fill Condition Gap：Bar N 判斷、Bar N+1 成交 | MEDIUM | v1.6.2 | 待討論 | `S16_S_ReEntry_Research_v1.6.2.md:107-117` |
| Issue 4 引擎 SL 對 re-entry 的衝擊（單筆 −152,000） | MEDIUM | v1.6.2 | **未修**（v1.8.1 P7 對齊被否決） | `S16_S_ReEntry_Research_v1.6.2.md:119-127` |
| Issue 5 無時效衰減（`v_ReEntry_Armed` 可跨 100+ 根存活） | LOW | v1.6.2 | 待討論 | `S16_S_ReEntry_Research_v1.6.2.md:129-137` |
| E-5 二次進場優勢只有一筆（見 §0b 表格第 1 列）；v1.6.1/v1.6.2 兩道閘門從未單獨驗證 | 待辦（3 次失效測試可結案） | v1.15.0 | **未修** | `docs/research/S16S_entry_side_gap_analysis_20260808.md:128-139, :372` |
| D-2「二次進場可能用陳舊價格跨時段觸發」 | — | v1.15.0 | **查證後排除**（11 筆間隔全在 0.1~1.1 小時內） | `docs/research/S16S_entry_side_gap_analysis_20260808.md:146` |
| 結構限制：緩跌趨勢中 24 根 TimeStop 出場後，`Close >= v_ReEntry_Price` 恆假 → 無法武裝，且不會有新死叉 → 完全無法再進場 | 角色邊界，非缺陷 | v1.14.0 | 不修（洗盤回補 vs 續勢加碼數學上互斥） | `docs/research/S16S_time_stop_investigation_20260806.md:149-188` |

> 注意 `S16S_entry_side_gap_analysis_20260808.md:146` 的 D-2 條目與 §C-3 中我判定的 N5（Priority-0 出場後 armed 跨假日存活）**不是同一件事**：該文查證的是「正常出場後的時間間隔」（11 筆全在 1.1 小時內），未涵蓋「被 Settlement/Holiday/TailFlat 強制平倉後」的情況。N5 仍為未查證。

從 v1.17.0 程式碼本身可直接讀到的稽核殘留：
- **A-1 finding**（`:1991-2030`）：Struct leg 實際是「lowest-profit-since-entry trail」而非 swing-high trail。與 re-entry 無直接關聯，但 re-entry 交易同樣受其管轄。
- **A-5 finding**（`:1928-1941`）：P3 不設 `ExitFired`，程式順序 ≠ 成交順序。**這對 re-entry 的意義**：re-entry 交易的保護停損與 P4/P5 市價單可能同根同時存在，實際成交由單型決定（市價單走下根開盤，先成交）。

以下為**本次靜態讀碼自行發現、未見於規格書**的問題（皆為 v1.17.0 現況）：

| # | 問題 | 嚴重度（本文件判定） | 狀態 | 行號 |
|---|---|---|---|---|
| N1 | re-entry 鏈無上限 | **must fix**（真金） | **未修**（= 稽核 B1，見 D-1） | `:1782-1795` |
| N2 | 無 `ReEntry_On` 主開關，無法做 On/Off 對照回測 | should fix | 未修（Handoff `:166` 已排程但 v1.17.0 未做） | inputs `:932-1216` |
| N3 | 進場後不解除 `v_ReEntry_Armed` | should fix（目前無害，補 P7 cap 後會致命） | 未修（= 稽核 **D2**，`S16_S_EXIT_AUDIT_20260729.md:59-61`） | `:1793-1794` |
| N4 | `v_IsReEntry` 不在 flat 區塊重設 | should fix（可移植性） | 未修（v1.9.0 FIX 1 曾修，版本被棄） | `:1713-1727` |
| N5 | Priority-0 強制平倉後仍會 re-arm，狀態跨假日/結算日存活 | should fix | **未查證**（既有分析未涵蓋此情境） | `:1653` |
| N6 | 已部署版（v1.6.2）缺 v1.8.0 的 ATR 繼承修正 | **must fix**（部署落差） | 未修 | `live_simulation/.../S16_S_MACrossShort.pla:504-506` |
| N7 | ATR 繼承的收益面在 v1.11.0 之後大幅縮水（BE 已改百分比），且 v1.8.0 當初的實測貢獻本來就是 0 元 | nice to have（需重新評估是否值得移植） | 未評估 | `:693, 1948-1958`；`S16_S_V162_V171_V180_COMPARISON_20260729.md:109-125` |

### D-5 狀態機的版本穩定性（推廣的好消息）

**`SECTION 5.5 - RE-ENTRY STATE MANAGEMENT` 這段狀態機程式碼，從 v1.11.0 到 v1.17.0 逐字元完全相同**（`diff` 零輸出）。v1.9.0 之後所有改動都落在「re-entry 與主進場共用的閘門」，沒有一次動到 arming/disarming 本體：

```
v1.9.0            : v_Slope > v_MinSlope_Threshold
v1.10.0           : ( MinSlope <= 0 or v_Slope > MinSlope )      <- NoSlope 實驗，已 KILL
v1.11.0 ~ v1.15.0 : v_Slope > MinSlope
v1.16.0           : v_Slope > MinSlope        + v_Gap_Block = False
v1.17.0           : v_Slope > v_MinSlope_Eff  + v_Gap_Block = False
```

**推廣意義**：狀態機本體（B-1 的邏輯區塊）是**穩定的、七個版本沒動過的**，抽出來當通用層是安全的。**不穩定的是掛鉤點（B-2 的 H7 動能閘門、H10 合規閘門）**——那才是每次版本推進真正在動的地方，也正是移植時必須逐支重寫的部分。這個觀察支持「通用層／策略層」這個切法本身是對的，只是切線要畫在規格書畫的位置之外。

---

## 8. E：套用到其他策略的前置條件

### E-1 硬前置條件（缺一不可）

| 前置條件 | 為什麼必要 | 誰滿足 | 誰不滿足 |
|---|---|---|---|
| **P1. `v_Prev_MP` 且在腳本最末行更新** | Arming 唯一觸發源（`:1653`）。無此變數整個模組無法運作 | S16_S、S1_NightMomentum、S3_RapidPullbackShort、S3_S_VolSqueezeShort、S3_VolSqueezeLong | **L1 / L2 / L3 / L4 / L5 全部沒有（0 筆）** |
| **P2. `ExitFired` 互斥鏈** | re-entry 增加交易密度，多層出場同根競爭的機率上升。無互斥旗標時多個出場單同根併發 | L2、L4、S16_S、S3_RapidPullbackShort、S3_S_VolSqueezeShort、S3_VolSqueezeLong | **L1 / L3 / L5 / S1_NightMomentum 全部沒有（0 筆）** |
| **P3. Frozen ATR 機制（`v_Frozen_ATR` + `v_SL_Locked` 進場鎖定區塊）** | ATR 繼承（`:1686-1692`）沒有可掛載的位置 | L4、L5、S16_S、S3_RapidPullbackShort、S3_S_VolSqueezeShort、S3_VolSqueezeLong | **L1 / L2 / L3 / S1_NightMomentum 全部沒有（0 筆）** |
| **P4. 離散的主訊號與反向訊號** | H3/H4 掛鉤點。趨勢跟隨型策略若進場條件是「持續狀態」而非「穿越事件」，`:1665` 的新週期重設會每根都觸發，模組永遠不會武裝 | S16_S（death/golden cross）、S3 系列（squeeze 事件）`[不確定]` | `[不確定]`，需逐支確認 |
| **P5. 單一 Data1 或明確的訊號 stream** | `v_ReEntry_Price` 是 Data1 的價格。多 data stream 策略若在 Data2 產生訊號、Data1 執行，價格語意會錯 | L2、S16_S、S3_VolSqueezeLong（Data2 引用 0 筆） | L1(2)、L3(12)、L4(12)、L5(10)、S1(7)、S3_RapidPullbackShort(57)、S3_S_VolSqueezeShort(24) |
| **P6. IOG = False** | 規格 §8.1。武裝/解除一根一次、收盤評估 | S16_S（`:926`） | `[不確定]`，需逐支確認 |

### E-2 ★ 明確回答：哪些前置條件目前「只有 S16_S 滿足」？

以本次實測（`find strategies/live strategies/live_simulation -name "*.pla"`，排除 `.bak_*`、`archive/`、`IND_*`，共 10 支）：

**單一條件層級**：沒有任何一條是 S16_S 獨佔的（P1 有 5 支、P2 有 6 支、P3 有 6 支、P5 有 3 支）。

**組合層級**：
- **P1 + P2 + P3（`v_Prev_MP` + `ExitFired` + Frozen ATR）同時滿足 = 4 支**：S16_S、S3_RapidPullbackShort、S3_S_VolSqueezeShort、S3_VolSqueezeLong
- **P1 + P2 + P3 + P5（再加單一 data stream）同時滿足 = 1 支，只有 S16_S**

**逐支現況表**：

| 策略 | 路徑 | `v_Prev_MP` | `ExitFired` | Frozen ATR | Data2 引用 | 有 re-entry |
|---|---|---|---|---|---|---|
| L1_TrendLong | `strategies/live/L1_TrendLong/L1_TrendLong.pla` | **0** | **0** | **0** | 2 | 0 |
| L2_TrendShort | `strategies/live/L2_TrendShort/L2_TrendShort.pla` | **0** | 20 | **0** | 0 | 0 |
| L3_ConsolidationLong | `strategies/live/L3_ConsolidationLong/L3_ConsolidationLong.pla` | **0** | **0** | **0** | 12 | 0 |
| L4_ConsolidationShort | `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort.pla` | **0** | 14 | 4 | 12 | 0 |
| L5_BreakoutLong | `strategies/live/L5_BreakoutLong/L5_BreakoutLong.pla` | **0** | **0** | 11 | 10 | 0 |
| S1_NightMomentum | `strategies/live_simulation/S1_NightMomentum/S1_NightMomentum.pla` | 4 | **0** | **0** | 7 | 0 |
| S3_VolSqueezeLong | `strategies/live_simulation/S3_VolSqueezeLong/S3_VolSqueezeLong.pla` | 3 | 15 | 4 | 0 | 0 |
| S3_S_VolSqueezeShort | `strategies/live_simulation/S3_S_VolSqueezeShort/S3_S_VolSqueezeShort.pla` | 3 | 25 | 4 | 24 | 0 |
| S3_RapidPullbackShort | `strategies/live_simulation/S3_RapidPullbackShort/S3_RapidPullbackShort.pla` | 6 | 18 | 4 | 57 | 0 |
| **S16_S_MACrossShort** | `strategies/live_simulation/S16_S_MACrossShort/S16_S_MACrossShort.pla` | 4 | 28 | 4 | 0 | **14** |

（數字為 grep 命中筆數；「0」代表該機制不存在。**確認：全 repo 只有 S16_S 一支有 re-entry。**）

**最貴的一件事：L1-L5 五支 live 策略全部沒有 `v_Prev_MP`。** 這是模組的第一塊地基，五支正在實盤跑的策略都得先動刀才談得上裝模組——而動 live 策略的程式碼是最高風險的操作。

**`ExitFired` 缺口的完整範圍**（含 research 版本，排除 `.bak_*` / `archive/`，共 53 檔中 11 檔沒有）：
```
strategies/live/L1_TrendLong/L1_TrendLong.pla
strategies/live/L3_ConsolidationLong/L3_ConsolidationLong.pla
strategies/live/L5_BreakoutLong/L5_BreakoutLong.pla
strategies/live_simulation/S1_NightMomentum/S1_NightMomentum.pla
strategies/research/L1_TrendLong/L1_v30/L1_TrendLong_v30.pla
strategies/research/L1_TrendLong/L1_v31/L1_TrendLong_v31.pla
strategies/research/L3_ConsolidationLong/L3_v141/L3_ConsolidationLong_v141.pla
strategies/research/L3_ConsolidationLong/L3_v15/L3_ConsolidationLong_v15.pla
strategies/research/L5_BreakoutLong/L5_v198/L5_BreakoutLong_v198.pla
strategies/research/L5_BreakoutLong/L5_v199/L5_BreakoutLong_v199.pla
strategies/live_simulation/S16_S_MACrossShort/IND_S16_S_Monitor.pla   <- 指標非策略
```
也就是說 **L1 / L3 / L5 / S1 這四族連 research 版都沒有 `ExitFired`**，不是「live 版落後」而是「這個機制從未被引入該策略族」。

另有兩筆既有的 `ExitFired` 紀律缺陷（本模組會放大其風險，因為 re-entry 提高交易密度）：
- F-07：L2 Priority 5 區塊未設 `ExitFired`（`L2_TrendShort.pla:721-728`），因 `IsDay`/`IsNight` 互斥故實務影響為零（`docs/research/strategy_logic_inventory_20260804.md:375`）
- F-08：L4 Priority 3 停損區塊未檢查 `if ExitFired = 0`（`L4_ConsolidationShort.pla:705-717`）（同檔 `:376`）

`docs/research/strategy_logic_inventory_20260804.md:277-278` 把「Re-Entry 狀態機」與「完整 first-hit-wins `ExitFired` 鏈」**兩者都列為 S16_S 獨有機制**。

### E-3 對 Priority-0 出場鏈的要求

- re-entry 的進場 gate **必須逐條複製主進場的 Priority-0 gate**。S16_S 是 6 條逐字複製（`:1787-1792` vs `:1765-1770`）。**這是手工同步，沒有任何機制保證兩邊一致**——加一條新 gate 而漏了 re-entry 那邊，就會出現「主進場被擋、二次進場照進」的合規破口。
- Priority-0 出場**不會**阻止 re-arm（見 C-3）。目標策略若有更長的停用窗口（例如整個結算週），要自行加上清除邏輯。

### E-4 MaxBarsBack 影響

**模組本體零影響。** 實測 `:1653-1668` 與 `:1782-1795` 兩個區塊**沒有任何 `[N]` bar offset**，全部靠 latched 變數。所以裝上模組不會推高 MaxBarsBack 需求。

（附註：`v1.17.0.pla:923` 註明 `MaxBarsBack >= 200`，與專案 CLAUDE.md 的「MaxBarsBack：100」不一致。這是 S16_S 自身的既有落差，與 re-entry 無關，但移植時若參考該行會被誤導。`[不確定]` — 未查證哪一個才是 MC12 實際設定。）

### E-5 與既有出場層的衝突點

| 衝突 | 說明 |
|---|---|
| **每根重掛的 stop 單** | re-entry 進場單是 `next bar at price stop`（`:1794`），若目標策略的出場層也用 stop 單，MC 的「同名單覆蓋」規則可能造成互相干擾。`[不確定]` — 需 MC12 實測 |
| **共用出場參數** | re-entry 交易與主交易共用 `MaxHoldingBars`、`QS_MaxLoss_Pct`、`BE_Trigger_Pct` 等全部參數（v1.17.0 現況）。v1.8.4 認為這是錯的並做了分岔，但那個版本未被採用。目標策略若持倉時間分布與 S16_S 差異大，這個假設要重新檢驗 |
| **Frozen ATR 的下游依賴數** | S16_S 的 `v_Frozen_ATR` 只餵 2 個下游（SL level `:1693-1694`、ML activation `:1870`）。目標策略若有更多 ATR 依賴的出場層，ATR 繼承的影響面會放大，必須重新回測而非假設「照抄即可」 |
| **加碼 / 分批策略** | `v_Last_EntryPrice = EntryPrice`（`:1684`）在加碼情境下會取到均價並逐根變動，`v_ReEntry_Price` 會漂移。S16_S 固定 2 口不加碼所以無害 |

---

## 9. F：不應該被通用化的部分

| # | 不該通用化的元素 | 理由 |
|---|---|---|
| **F1** | **「回到原進場價再進一次」這個 alpha 假設本身** | 這是 S16_S 特有的「washout recovery」論點（`:1647-1648`、`:1775`）：MA 死亡交叉後被洗出場，結構未破就用原價再進。它假設**原進場價是一個有意義的支撐/壓力**。對均值回歸型、突破型、隔夜動能型策略，原進場價沒有這個語意，模組會退化成一個沒有理論根據的加倉器 |
| **F2** | **`v_ReEntry_Price = v_Last_EntryPrice` 這個價位選擇** | 規格 §8.2 自己承認「No support for multiple price levels or adaptive re-entry prices」。這不是通用設計，是 S16_S 的單點選擇。且鏈中會漂移（BC-6） |
| **F3** | **`v_Slope > v_MinSlope_Eff` 這個動能 gate 的數值與符號慣例** | `v_Slope` 的正負定義（`:1427`，正值 = 下跌）綁死做空語意。且 `MinSlope` 本身在 v1.16.0/v1.17.0 被證實有嚴重的尺度問題（28 點在 2019 是 0.28%、今天是 0.062%，`:936-943`）——**這是一個公開承認有瑕疵的參數，不該被複製到 9 支策略上** |
| **F4** | **ATR 繼承作為「必備品」** | 見 A-8/N7。v1.8.0 的價值論證建立在「同時撐寬 SL/BE/ML」，但 v1.11.0 之後 BE/Trail/Struct 全改百分比制。**對出場層已全百分比化的策略，ATR 繼承幾乎不做事**，強行加入只是增加狀態複雜度 |
| **F5** | **「無鏈上限」這個現況** | 絕對不可以當作模組行為推廣。它是一個 must-fix 缺陷被明知放棄（`:705`）的結果，不是設計選擇。推廣前必須先補上限並重跑回測 |
| **F6** | **`ExitFired` 之外的隱式互斥（靠程式順序）** | BC-1 的主進場/二次進場互斥**完全靠 Section 5.5 排在 Section 9 之前**，沒有旗標保護。這種靠排版維持的正確性不該被當成模組契約——移植時必須改寫成顯式互斥 |
| **F7** | **S16_S 的 6 條合規 gate 清單** | `v_Gap_Block`（`:1770/1792`）是 v1.16.0 針對 S16_S 的 session opening gap 缺陷專門加的，其存在理由是 `v_Slope` 在 session 首根會把隔夜跳空誤讀為一根 K 的動能（`:169-174`）。這是 S16_S 特有的指標缺陷補丁，不是通用 gate |
| **F8** | **「二次進場需要更緊/更短的出場」這個直覺** | v1.8.4 照這個直覺做了完整分岔（固定 % SL、ML 停用、`ReEntry_MaxHold=12`），MC12 結果 **−227K**，且 Gross Loss 一毛沒改善。**這個方向在 S16_S 上已被實測推翻過一次**，不要把它當成模組的可選擴充推薦給其他策略 |
| **F9** | **把「S16_S 已在 live_simulation」當成 re-entry 已驗證的證據** | 部署版是 **v1.6.2**，且 v1.6.2 的 re-entry 樣本本身有兩個 CRITICAL 未決（1 筆佔 81.5% 獲利、10 筆全在 2026 年 5 個月內）。**在役 ≠ 已驗證** |

---

## 10. 建議的下一步（不在本次授權範圍內，僅供決策）

**順序刻意如此排列——第 1 項沒有答案之前，後面幾項都是白工。**

1. **先回答「這個機制有 alpha 嗎」，再談移植。** §0b 的三個數字（S16_S 扣除異常值後期望值低於主進場、樣本全在 2026 年 5 個月內、L1 實測 −920K 被移除）指向同一個方向：**二次進場在本 repo 尚未取得任何一次正面的統計證據**。`S16S_entry_side_gap_analysis_20260808.md:372` 已經提出「3 次失效測試可結案」的具體路徑（v1.6.1 斜率閘門、v1.6.2 方向閘門、整體 On/Off）。**建議先跑這三次，再決定要不要推廣到 9 支策略。**
2. **先修規格書，再談推廣。** 現行 `REENTRY_MODULE_SPEC_20260730.md` 12 節中 11 節需要修訂（A-10）。它描述的是一個**被否決、檔案已被覆寫**的 v1.9.0。拿它去套 9 支策略，等於把一條 S16_S 已經走過並拒絕的路重走 9 次。
3. **D-1 的鏈上限需要使用者 ruling，不是工程決定。** `strategy_logic_inventory_20260804.md:444`（U27）已把它定性為需要 ruling；兩次實作嘗試（v1.8.4、v1.9.0）都被否決，一次因績效（−227K）、一次因偏離裁定。
4. **部署落差 N6 優先於推廣。** live_simulation 上跑的是 v1.6.2，連 v1.8.0 的核心修正都沒有——research head 與部署版之間隔了 11 個版本。
5. **L1-L5 的 `v_Prev_MP` 缺口是最大的工程量。** 五支 live 策略要動刀，建議先在 research 分支驗證。同時 L1 是**唯一一支有 re-entry 實戰數據的策略，而那個數據是負的**——L1 應該排在推廣名單的最後，不是最前。
6. 補齊本文件的 `[不確定]` 項（見下）。

---

## 11. `[不確定]` 清單

| # | 項目 | 已查什麼 | 還缺什麼 |
|---|---|---|---|
| U1 | `ReEntry_Max_Chain` 這個識別字的定義來源 | 全 repo .pla grep 零命中；規格書用 `MaxReEntries`、v1.8.4 用 `ReEntry_MaxCount` | `HANDOFF_S16S_V1160_ADOPTED_20260808_EOD.md:166` 寫它是「已存在待測的開關」，但找不到任何定義。是用詞不精確還是誤認，文件沒說明 |
| U2 | `S16S_entry_side_gap_analysis_20260808.md:28` 稱 `v_IsReEntry` 為「v1.12.0 為出場端加入」 | 實測 `v_IsReEntry` 早在 `S16_S_MACrossShort_v1.8.0.pla:371, :526, :597, :618` 就存在 | 該句版本歸屬應為 v1.8.0（v1.12.0 只新增 F5 per-entry reset 語意），但文件無更正紀錄 |
| U3 | v1.8.0~v1.8.3 是否**真的**程式路徑等價，還是只是 re-entry 交易從未觸及 SL 門檻 | `S16_S_EXIT_AUDIT_20260729.md:181-182` 明確留下這條未結案的驗證要求；`S16_S_V162_V171_V180_COMPARISON_20260729.md:111-115` 給了機制解釋（8 筆全走 QS/TimeStop/GoldenCross） | 那是分析不是實測。後續驗證紀錄在 `docs/`、`strategies/research/S16_MACrossShort/*.md`、全部 handoff 中都找不到 |
| U4 | B1 從「must fix before live_simulation」降級為「deferred / OPEN」的**具體理由** | 只找到結果（`S16_S_EXIT_AUDIT_20260729.md:198-200, :223, :234`） | 論證本身。`strategy_logic_inventory_20260804.md:444` 自己也說「是刻意暫緩還是漏掉」不明 |
| U5 | 其他策略是否滿足 P4（離散主訊號）與 P6（IOG=False） | 僅 S16_S 確認（`v1.17.0.pla:926`） | 逐支讀碼 |
| U6 | Priority-0 強制平倉後 armed 跨假日/結算日存活，歷史上是否真的造成過壞交易（N5） | 靜態行為已確認；`S16S_entry_side_gap_analysis_20260808.md:146` 的 D-2 只查證了正常出場（11 筆間隔 0.1~1.1 小時），未涵蓋強制平倉情境 | MC12 逐筆交易檢視 |
| U7 | MaxBarsBack 到底是 100 還是 200 | `v1.17.0.pla:923` 寫 `>= 200`、專案 CLAUDE.md 寫 100 | MC12 實際設定截圖 |
| U8 | re-entry stop 單與出場 stop 單在 MC 的同根交互行為 | 程式碼順序已確認；`v1.17.0.pla:1928-1941`（A-5）說明市價單/停損單的成交先後 | MC12 實測 |

---

**驗證聲明**：本文件所有行號皆為 2026-08-08 實際讀取所得。**未執行 MC12 編譯、未執行任何回測**。所有績效數字均引自檔案既有註解，非本次產生。標 `[不確定]` 之處禁止當作事實引用。
