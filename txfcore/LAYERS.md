# 分層與依賴規則

本檔是 `txfcore/` 的權威分層定義。`tests/test_layer_boundaries.py` 機械檢查，
違反即測試失敗 —— 規劃書層 0 的「層間依賴 CI 檢查」就是它。

## 架構型態：ports and adapters

**層 0 定義所有跨層介面（Protocol），各層提供實作（adapter）。**

先有介面再有模組。介面定完，每個模組都是照著介面填，
而不是寫完再回頭想它屬於哪一層。

三顆插頭就是三個 Protocol：`QuoteSource` / `OrderSink` / `Clock`。
回測與即時是**兩組 adapter**，中間三層一個字都不動。
鐵則因此不是紀律，是型別。

## 分層

| 層 | 套件 | 在資料流上 | 對應介面 | 狀態 |
|---|---|---|---|---|
| **0 基礎設施** | `contracts` | 否 | — 它就是介面本身 | ✓ |
| | `types` | 否 | — | ✓ |
| | `costs` `metrics` | 否 | — 純函數 | ✓ |
| | `journal` | 否 | `Journal` | ○ |
| | `timing` | 否 | `Clock` | ○ |
| | `state` | 否 | `StateStore` `KillSwitch` | ○ |
| | `lineage` | 否 | `Lineage` | ○ |
| | `obs` | 否 | `Observer` `TriggerMonitor` | ○ |
| **共用支撐** | `indicators` `tradecal` | 否 | — 純函數 | ✓ |
| | `engine` | 否 | `FillModel` `PositionBook` | ○ |
| **1 報價** | `quotes` | 是（入口） | `QuoteSource` | ○ |
| **2 策略** | `strategies` | 是 | `Strategy` | L2 完成 |
| **3 風險** | `risk` | 是 | `RiskGate` | ○ |
| **5 通知下單** | `notify` `broker` | 是（出口） | `OrderSink` | ○ |
| **旁路** | `parity` | 否 | `ParityChecker` | ○ |
| **組裝根** | `runtime` | — | — | ○ |

## 一個歸類修正

**「回測層」不是一層，是一種組裝。**

原規劃把 backtest 列為層 6，但它不在資料流上、也不被任何層呼叫。
它做的事是：把三顆插頭換成歷史版本，然後跑同一個迴圈。

所以正確的位置是 `runtime/`，與 `runtime/live.py` 並列：

```
runtime/backtest.py   歷史 K 棒 + 交易記錄器 + K 棒時鐘
runtime/live.py       凱基 tick   + 券商/通知   + 系統時鐘
```

**`runtime/` 是唯一允許 import 全部層的地方**（組裝根的定義）。
把它獨立出來，其他每一層才能維持嚴格的單向依賴。

## 依賴規則

```
0  contracts types costs metrics journal timing state lineage obs
      ↑ 不得依賴任何其他 txfcore 套件（contracts 除外可依賴 types）

S  indicators tradecal engine     可依賴 0
1  quotes                         可依賴 0
2  strategies                     可依賴 0 S      ← 不得碰 quotes notify broker
3  risk                           可依賴 0 S      ← 不得碰 quotes notify broker
5  notify broker                  可依賴 0
旁  parity                        可依賴 0 S 2
根  runtime                       可依賴全部
```

## 兩條最重要的禁令

**一、`strategies/` 與 `risk/` 不得 import `quotes/` `notify/` `broker/`。**

策略層若能直接抓報價或直接下單，那份程式碼就綁死在某一端，
換插頭就不再是換插頭。沒有這道機械檢查，六個月後一定會有人
為了 debug 方便在策略層印個東西。

**二、層 0 不得依賴其他套件。**

地基一旦有向上的依賴，依賴圖就出現環。

## 層 0 的內部次序（2026-09-06 由依賴檢查抓出）

原規則寫成「層 0 不得依賴任何其他套件」，但 `timing/clock.py` 需要
`types/mctime` 的日期轉換。這不是違規，是**規則寫得太嚴**。

層 0 內部有次序：

```
types            最內圈。純資料型別，誰都不依賴
  ↑
instruments  costs  metrics  journal  timing  state  lineage  obs  contracts
                 只准依賴 types，不得橫向依賴彼此
                 （例外：costs 依賴 instruments，成本計算需要商品規格）
```

**這不是環，是正確的地基分層。** 修規則不是修程式碼。

## quotes -> tradecal（2026-09-06 由依賴檢查抓出）

網格切分需要知道結算日——**結算日的日盤在 13:30 收，只有 285 分鐘**
（208 萬列 1 分 K 實測，92 天零例外）。所以 `quotes/session.py`
必須讀 `tradecal/settlement.py`。

這是**具體的一條邊**，不是放寬整層：

```
quotes → tradecal        ✓ 允許。結算行事曆是市場參考資料，且 tradecal 不依賴 quotes，無環
quotes → engine          ✗ 仍禁止。報價層不該知道執行層
strategies → quotes      ✗ 仍禁止。這條是鐵則的核心
```

**檢查器兩次抓到的都是規則本身的問題，不是程式碼的問題。**
第一次是層 0 內部次序（types 是最內圈），第二次是這條。
這比抓到程式碼問題更有價值——它讓規則跟著真實依賴修正，而不是反過來。

## 鐵則的誠實聲明（2026-09-06 補，來源：NautilusTrader）

原鐵則寫「回測與即時只有三顆插頭不同」。**那不是全部的真相。**

NautilusTrader 的文件在宣告「同一份程式碼跑兩端」之後，緊接著明列了
模擬未必能重現的東西：**場所、傳輸、時序、持久化、外部活動、對帳**。

我們的對應：

| 模擬不能重現的 | 我們的處置 |
|---|---|
| 場所行為（拒單、部分成交、改單） | `engine/orders.py` 的狀態機有型別，但 `mc12` 模式下永遠用不到 |
| 傳輸延遲 | `timing/latency.py`。**未量測前 `is_measured = False`** |
| 時序（NTP 漂移、時區） | `timing/clock.py` 的 `SystemClock.drift_ok()` |
| 持久化（重啟後狀態） | `state/` 尚未實作 |
| 外部活動（手動下單、其他系統） | 只能靠券商部位對帳迴路發現 |
| 對帳 | `risk/reconcile.py` 尚未實作。**只有 live 需要** |

> **鐵則仍然成立，但它保證的是「策略邏輯一致」，不是「行為一致」。**
> 逐筆對帳通過，證明的是前者。


## 具體放行的邊（2026-09-08 更新）

三條，全部是「支撐層提供事實」而非「上層洩漏到下層」，且都無環：

```
quotes  -> tradecal    結算日的日盤只有 285 分鐘
engine  -> tradecal    每日結算的時刻（一般日 1345 · 結算日 1330）
metrics -> instruments 損益指標要把點數換算成金額
metrics -> costs       手續費總額與期交稅總額要分開算，需要費率表
costs   -> instruments 成本要商品規格
```

**每一條都是被 `test_layer_boundaries.py` 抓出來後才放行的**，
不是事先開的洞。
