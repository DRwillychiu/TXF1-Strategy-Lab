# 移植稽核 2026-09-07

> **方法**：`tools/audit_port.py` 直接讀 `.pla`，逐項與 Python 模組機器比對。
> 不是我說有沒有漏，是機器比。輸出 `✗` 的都是**確定的落差**，不是推測。
>
> ```powershell
> python tools\audit_port.py
> ```

---

## 一 稽核抓到的（已修）

### ✗ L1：六個 input 與一個標籤整個缺失

| 缺的 | 預設 |
|---|---|
| `ReEntry_Close_Gate` | 1 |
| `ReEntry_Trend_Gate` | 1 |
| `ReEntry_Weekly_Gate` | 1 |
| `ReEntry_MABase_Gate` | 0 |
| `ReEntry_WeeklyTier_Gate` | 0 |
| `ReEntry_Trend_Ratio` | 0.20 |
| 標籤 `TL_ReEntry` | — |

我當初的理由是「`ReEntry_On = 0` 讓它惰性，不用移植」。

> **後果：有人把 `ReEntry_On` 設成 1 時，我的移植會靜默地什麼都不做，
> 而 MC 會發 `TL_ReEntry` 單。**
>
> **惰性 ≠ 不存在。** 這正是我一路在批評的那種缺陷——沒有斷言會失敗。

**已補齊**，包含：
- 六個閘門寫成 `(開關關閉 or 條件)`，全開時退化成單純條件式
- W3 週線層級檢查（`v_Wk_Entry_Fast` / `v_Wk_Entry_Slow`）
- **停損繼承**：`MaxList(繼承的, 重算的)` = 較緊者。
  那正是 Plan C 被診斷出來的失敗（「re-entry 部位的停損價比原始更差」）
- 獲利保護狀態**刻意不繼承**——建立它的那段行情已被吐回

**回歸驗證**：`ReEntry_On = 0` 時仍是 **496 筆、`TL_ReEntry` 0 筆**。

### ✗ L5：24 個標籤在 Python 裡一個都查不到

我用 f-string 組標籤：`f"BL_TP_{sfx}"`、`f"{kind}_{sfx}"`、`f"{safety}_{sfx}"`。

> **用 f-string 組標籤等於放棄可稽核性。打錯前綴不會有任何檢查抓得到。**

**已改為顯式常數表** `LABELS`，24 個標籤全部是字面值。

### ✗ L5：40% 分批出場從未生效

```
持倉 6008 根   Stage 1 = 6008   Stage 2/3 = 0   分批 0 組
```

根因是 2026-09-06 那個裁決的後果：

> 「口數由風險層決定」**只適用於進場**。
>
> 　進場口數 = 風險決策（要下多大）
> 　出場口數 = **策略決策**（要平掉部位的多少）

`FixedLotRiskGate` 把分批的 1 口覆寫成 2 口，每次分批變成全平，
`CurrentContracts < MaxContracts` 永不成立，**Stage 2/3 的 MFE 三階追蹤從未執行**。

**已修**：`OrderIntent.exit_quantity`，風險層必須遵守；進場單不得指定它。

### ✗ 綁到不存在的腿時中止整批

`BL_TimeExit_Bot` 綁在不存在的 Bot 腿上，處理完就 `break`，
**Mid 那筆永遠處理不到**。實測：L5 的部位掛了 3416 根，而 `Time_Stop_Bars` 是 31。

由 `tools/signals.py` 抓到。**已修**：該單作廢，不中止整批。

---

## 一之二 ★ 稽核工具本身也壞了

在你的機器上第一次跑完整稽核，結果是：

```
✓ L2   訂單標籤 0
✓ L4   訂單標籤 0
```

**L2 和 L4 明明有 `SellShort("TS_Entry")` 和 `BuyToCover(...)`。**

根因：正規式寫成 `\b(?:Buy|Sell)\s*\(`，而
**`SellShort (` 與 `BuyToCover (` 都不匹配**（`Sell` 後面接的是 `Short`
不是空白或括號）。PowerLanguage 有**四個**下單動詞，不是兩個。

> **後果：工具對兩支策略印了 ✓，而它連看都沒看。**
>
> 這正是「判官不判」的失敗模式——與 2026-08-25 那個對帳工具
> 不合併分批出場卻當場印「通過」是同一類。

**已修，並加了三道防線：**

| 防線 | 內容 |
|---|---|
| 四個動詞 | `BuyToCover` · `SellShort` · `Buy` · `Sell` |
| **標籤數 0 = 解析失敗** | 策略不可能不下單。0 一律報錯，不靜默通過 |
| 標頭 grep 數比對 | L5 標頭自報 `from Entry` 28 處，實測 30 處 → 警告 |

三道都寫成測試。

### ▲ L5 的 from Entry：標頭說 28，實測 30

標頭寫「**Measured, not assumed: grep count is 28**」，但剝除註解後實測 30 處。

**差 2。** 要嘛標頭的計數在 v19.9-R1 之後沒更新，要嘛我的註解剝除有誤。
工具現在會把這個不符報為警告，不會放過。

### 兩個誤報（已修）

| 誤報 | 原因 |
|---|---|
| L1「`of Data2` 找不到對應」 | 我的 Python 寫 `avg_true_range(d2, ...)`，沒有 `d2.` 屬性存取。提示字串太窄 |
| L4「`IntrabarOrderGeneration` 找不到對應」 | L4 是 `= false`，工具沒區分 true/false |

---

## 二 稽核結果：三支零落差

```
✓ L3   inputs 16   標籤 10   落差 0
✓ L5   inputs 19   標籤 24   落差 0
✓ L1   inputs 19   標籤 12   落差 0
```

L2 / L4 的 `.pla` 不在我的容器裡，**請在你的機器上跑 `audit_port.py` 補完那兩支**。

---

## 三 仍然存在的問題（未修，按嚴重度）

### ★★★ P-1　L1 是收盤評估，不是 IOG 逐 tick

L1 是五支裡唯一 `IntrabarOrderGeneration = true`。原始碼把指標 / 進場 /
P3 凍結包在 `BarStatus(1) = 2` 內，而 **P7 峰值追蹤 / P4 棘輪 / 出場下單**
在守衛外逐 tick 執行。

**`engine/context.py` 不存在，所以全部在收盤評估。**

```
P7 只看得到收盤峰值 -> posble_profit 偏低 -> stop_profit_price 偏低
-> TL_SP 觸發次數是**下限**，不是實際值
```

而 V3.0 把 SP 門檻從 500 降到 200 **正是因為 IOG 讓更低的門檻可行**，
所以用 200 跑收盤評估，**既不是 V2.7 也不是 V3.2 的行為**。

**優化方向**：`engine/context.py` 的資料模型必須**以 tick 為原生、
bar close 為特例**。若先做成 bar-only 再加 tick，五支已完成的對帳全部要重跑。

### ★★★ P-2　L5 差 +101 筆，箱體幾何未對上

```
263 筆 vs 162   淨 +28,916 vs +1,713,000   PF 1.004 vs 2.136
BL_TimeExit 138 筆（超過一半）   BL_TP 只有 8 筆
```

分批修好後 `BL_Trail` 開始觸發（4 筆），但**超過一半的部位在到達目標前
就被 31 根的時間停損砍掉**。

日線定義的實測：

| 定義 | L5 淨利 | L3 差 | L4 差 |
|---|---|---|---|
| **A 日盤 + 隨後夜盤**（現行） | +28,916 | **+3** | **+1** |
| B 前夜盤 + 日盤 | +1,462,591 | −19 | +2 |
| C 只有日盤 | −270,584 | — | — |

**三支的偏好不一致。** 要嘛 MC 各張圖的 session 設定不同，
要嘛 L5 還有別的問題。

**優化方向**：需要 **MC 匯出的日線 K 棒**逐根比對。
在那之前 L5 的數字不可用於任何決策。

### ★★ P-3　`v_Prev_MP` 在 IOG 下的語意

L1 的 `v_Prev_MP` 在最末行更新且**不在 `BarStatus` 守衛內**，
所以 IOG 下記錄的是**每個 tick** 的部位，不是每根 K 棒。

註解宣稱「records the position of every bar without exception」——**語意不符**。

re-entry 的 arm 判斷在守衛內，讀到的是前一個 tick 的部位而非前一根的。
**`ReEntry_On = 0` 時惰性，啟用時會是問題。**

**優化方向**：`engine/context.py` 做完後，`v_Prev_MP` 要有兩個版本
（per-tick / per-bar），並在 arm 判斷處明確選一個。

### ★★ P-4　`SetStopContract` 的位置三支不同

```
L1 · L4 · L5   頂層無條件
L2             在 if MarketPosition >= 0 之內
L3             在 if v_is_in_consolidation 之內
```

L5 的註解明白寫「must be outside conditional」。**若 L5 正確，L2 與 L3 的位置是錯的。**

**優化方向**：這是策略層的裁決，不是移植問題。需要你決定是否為 bug。
`mc12` 模式一律照抄；修正只能進 `v2`。

### ★★ P-5　`quotes/continuous.py` 只做標記，沒做接續

換月跳空實測中位 60.5 點、最大 511 點。五支結構上碰不到換月點
（`Settlement_Flat_Time = 1230` < 換月 1330），**所以目前無害**。

但 `v2` 模式若放寬結算日規則，或未來新增策略不遵守 Iron Rule，
**那個假象會直接進到損益裡**。

**優化方向**：實作 back-adjusted 連續合約作為可切換的資料來源，
與現行的未調整序列並存，兩者跑一次比對。

### ★ P-6　L2 差 +3 筆，分解為「3 筆多出來 + 1 筆標籤錯」

```
24 − 3 − 1 = 20      TS_ReEntry
56 + 1     = 57      TS_Entry
```

排除了邊界誤判（24 筆 re-entry 的餘裕是 4 到 416 點，**沒有一筆等於 0**）。

**優化方向**：需要 `TXF1  L2_TrendShort_v5.4 策略回測績效報告.xlsx` 做逐筆 diff。
anchor 文件記載它做過**逐筆 8 欄位比對**，所以那份 Excel 有完整明細。

---

## 四 分層與模組的完善程度

```
層 0    contracts ✓  types ✓  instruments ✓  costs ✓  metrics ✓  lineage ✓  timing ✓
        journal ○    state ○    obs ○
支撐    indicators ✓  tradecal ✓  engine ✓（context ○）
層 1    quotes ✓（continuous 只做標記）
層 2    strategies ✓✓✓✓✓  五支全部
層 3    risk ✓（protections）  reconcile ○
層 5    notify ○    broker ○
旁路    parity ✓（diff · golden · invariants · anchors）
組裝    runtime ✓（backtest · multi）  live ○
```

### 空套件的排序（按上線的必要性）

| 順位 | 套件 | 為什麼 |
|---|---|---|
| **1** | `engine/context` | **擋住 L1 的正確性**，且資料模型必須從一開始就對 |
| **2** | `runtime/live` | dry-run 是從 MC12 切換的唯一安全路徑 |
| **3** | `notify` | 專案終點的一半。`tools/signals.py` 已經產出內容，缺的是通道 |
| **4** | `state` | 崩潰復原。**沒有快照時預設停機，不是重建** |
| **5** | `obs` | 觸發次數監控。唯一能抓到 L2 停擺 443 天的東西 |
| **6** | `journal` | 重放的唯一輸入。實盤出事時要重現「那天系統看到的市場」 |
| **7** | `broker` | 自動下單。**必須在 dry-run 連續一致之後** |
| **8** | `risk/reconcile` | 券商部位對帳。不一致即停機，**不自動修正** |

### 三個已知的架構缺口

**一、`engine/reality.py` 不存在。** `fill_mc12` 是 MC 的樂觀假設
（觸價即成交、零滑價）。**沒有真實成交模型，就永遠不會問
「真實滑價下 MDD 是多少」。**

**二、`MeasuredLatency` 樣本數 = 0。** 型別寫好了，
`is_measured` 旗標也有了，但沒有任何實盤延遲被錄下來。

**三、五支同時跑的組合層不存在。** B-2（五支疊加的組合 MDD）仍是空白。
`risk/protections.py` 有 `ExposureLimit`，但沒有東西在呼叫它。

---

## 五 建議的下一步

**不要先做 `notify`。** `tools/signals.py` 已經證明訊號內容可以產出，
通道是最容易的部分。

**先做 `engine/context.py`。** 三個理由：

1. 它擋住 L1 的正確性（P-1），而 L1 是五支裡最大的一支（496 筆）
2. **它的資料模型必須從第一天就以 tick 為原生**——晚做要重構，
   前四支已通過的對帳全部重跑
3. 它同時解掉 P-3（`v_Prev_MP` 的 tick/bar 語意）

做完之後 `runtime/live.py` 的 dry-run 才有意義，
因為即時端本來就是 tick 驅動。
