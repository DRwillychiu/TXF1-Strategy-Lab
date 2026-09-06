# L1–L5 完整分層規劃

> 產出 2026-09-06。**全部由五份原始碼反推**，不是設計偏好。
> 每一個模組後面都標了「哪幾支需要它」，沒有任何一支需要的模組不列入。

---

## 一、能力矩陣（五份原始碼實際用到的東西）

| 能力 | L1 | L2 | L3 | L4 | L5 | 現況 |
|---|:-:|:-:|:-:|:-:|:-:|---|
| 多資料流 `of Data2/Data3` | ● | · | ● | ● | ● | ✗ |
| **策略變數歷史 `v_X[1]`** | ● | ● | ● | ● | ● | ✓ 已補 |
| `MarketPosition[1]` 冷卻計數 | · | · | · | ● | · | ✗ |
| Limit 單 | · | · | ● | · | ● | ✗ |
| 部分口數 `N contracts` | · | · | · | · | ● | ✗ |
| `from Entry` 腿綁定 | · | · | · | · | ● | ✗ |
| `CurrentContracts/MaxContracts` | · | · | · | · | ● | ✗ |
| `MinMove / PriceScale` | · | · | · | · | ● | ✗ |
| IOG tick 生命週期 | ● | · | · | · | · | ✗ |
| `IntraBarPersist` | ● | · | · | · | · | ✗ |
| `BarStatus(1) = 2` 守衛 | ● | · | · | · | · | ✗ |
| `Crosses Over` | ● | · | · | · | · | ✓ |
| `SetStopLoss` / `SetStopContract` | ● | ● | ● | ● | ● | 型別有，引擎無 |
| Market / Stop 單 | ● | ● | ● | ● | ● | 型別有，引擎無 |
| 成交模型 | ● | ● | ● | ● | ● | ✗ |
| Fill → 權益曲線 | ● | ● | ● | ● | ● | ✗ |
| 換月 / 連續合約 | ● | ● | ● | ● | ● | ✗ |
| `BigPointValue` 商品屬性 | ● | ● | ● | ● | ● | 位置錯誤 |
| `EntryPrice` / `BarsSinceEntry` | ● | ● | ● | ● | ● | ✓ |
| `PositionProfit(1)` | · | ● | ● | · | · | ✓ |
| ATR / SMA / EMA / Highest / Lowest | ● | ● | ● | ● | ● | ✓ |
| 假日 / 結算 / 註冊表 | ● | ● | ● | ● | ● | ✓ |

**22 項中 16 項未完成。**

---

## 二、每支策略的資料流需求

| | Data1 | Data2 | Data3 | IOG | 單型 | 部位模型 |
|---|---|---|---|---|---|---|
| **L1** | 45M | Daily | Weekly | **true** | Market · Stop | 單一 |
| **L2** | 60M | — | — | false | Market · Stop | 單一 |
| **L3** | 15M | 60M | Daily | false | Market · Stop · **Limit** | 單一 |
| **L4** | 15M | 60M | Daily | false | Market · Stop | 單一 |
| **L5** | 15M | **Daily** | Weekly | false | Market · Stop · **Limit** | **雙腿 + 分批** |

報價層必須提供五種週期：**15M / 45M / 60M / Daily / Weekly**。

---

## 三、完整模組清單

標記：✓ 已完成　◐ 部分　○ 空　★ 新增（本次由原始碼反推出來）

### 層 0　基礎設施（不在流上，全層依賴）

| 模組 | 內容 | 誰需要 | 狀態 |
|---|---|---|---|
| `contracts/` | 三顆插頭 + 十個 port（Protocol） | 全部 | ✓ |
| `types/bar.py` | Bar · Series · BarSeries，負索引拋例外 | 全部 | ✓ |
| `types/orders.py` | 訂單意圖 schema + 冪等鍵 | 全部 | ✓ |
| `types/mctime.py` | MC 日期時間 + `trading_day()` | 全部 | ✓ |
| **`types/stateful.py`** ★ | **`Var` / `VarBook`，變數自帶歷史 `v_X[1]`** | **全部** | ✓ |
| **`instruments/`** ★ | 商品主檔：`BigPointValue` `TickSize` `MinMove` `PriceScale`、合約規格、到期與換月日曆 | 全部（L5 直接用 TickSize） | ○ |
| `costs/fees.py` | 手續費 + 期交稅（分開算） | 全部 | ✓ |
| `metrics/drawdown.py` | drawdown · max_drawdown · portfolio_mdd | 全部 | ✓ |
| `timing/` | `Clock` 實作（K 棒時鐘 / 系統時鐘）+ 三戳記 | 全部 | ○ |
| `journal/` | append-only 事件日誌 | 重放與對帳 | ○ |
| `state/` | 持久化 + `KillSwitch` | 上線前 | ○ |
| `lineage/` | 血緣雜湊 | 對帳 | ○ |
| `obs/` | 心跳 + 觸發次數監控 | 上線前 | ○ |

### 共用支撐（`.pla` 裡完全不存在，五支共用）

| 模組 | 內容 | 誰需要 | 狀態 |
|---|---|---|---|
| `indicators/core.py` | ATR · SMA · EMA · ZLEMA · Highest · Lowest · Crosses Over | 全部 | ✓ |
| `tradecal/` | 假日註冊表 + 結算 + 過期 fail-safe | 全部 | ✓ |
| `engine/context.py` | `BarStatus` · IOG · `IntraBarPersist` 生命週期 | **L1** | ○ |
| `engine/orders.py` | **訂單狀態機**：pending → acked → partial → filled / rejected | 全部（L5 必要） | ○ |
| `engine/position.py` | 部位帳。單一 + **雙腿 + 分批 + `from Entry` 綁定** | 全部（L5 必要） | ○ |
| `engine/protective.py` | `SetStopLoss` + `SetStopContract`，含「無出場單的平倉」路徑 | 全部 | ○ |
| `engine/fill_mc12.py` | MC 樂觀成交假設（觸價即成交、零滑價）—— 對帳專用 | 全部 | ○ |
| **`engine/accounting.py`** ★ | **Fill → 部位 → 含未平倉的權益曲線**（目前 Fill 與 drawdown 之間是斷的） | 全部 | ○ |
| `engine/reality.py` | 真實成交模型 —— 風險判斷專用，**與 fill_mc12 永不互相 import** | 上線前 | ○ |

### 層 1　報價

| 模組 | 內容 | 誰需要 | 狀態 |
|---|---|---|---|
| `quotes/session.py` | 日夜盤時段、各週期網格切點、殘棒處理 | 全部 | ○ |
| `quotes/bars.py` | 1 分 K → 15M / 45M / 60M / Daily / Weekly | 全部 | ○ |
| `quotes/align.py` | **`of Data2` / `of Data3` 對齊**——「當下已完成的那一根」 | L1 L3 L4 L5 | ○ |
| **`quotes/continuous.py`** ★ | **換月接續 / 連續近月合成**，換月日打標記 | 全部 | ○ |
| `quotes/history.py` | 讀 MC12 匯出的 1 分 K（回測 adapter） | 全部 | ○ |
| `quotes/quotecom.py` | 凱基 tick（即時 adapter） | 上線前 | ○ |

### 層 2　策略

| 模組 | 誰 | 狀態 |
|---|---|---|
| `strategies/base.py` | 五支共用骨架 + 介面契約 | ✓ |
| `strategies/l2_trendshort.py` | L2 | ✓ |
| `strategies/l4_consolshort.py` | L4 | ○ |
| `strategies/l3_consollong.py` | L3 | ○ |
| `strategies/l5_breakoutlong.py` | L5 | ○ |
| `strategies/l1_trendlong.py` | L1 | ○ |

### 層 3　風險

| 模組 | 內容 | 狀態 |
|---|---|---|
| `risk/limits.py` | 總口數 · 單筆風險 · 日內累計虧損 | ○ |
| `risk/reconcile.py` | 券商部位對帳迴路。不一致即停機，**不自動修正** | ○ |

### 層 5　通知與下單

| 模組 | 狀態 |
|---|---|
| `notify/` | message · channels · dedupe · heartbeat | ○ |
| `broker/` | 券商 adapter（終點已定為自動下單） | ○ |

### 旁路與組裝

| 模組 | 內容 | 狀態 |
|---|---|---|
| `parity/` | mc_report · replay · diff + **黃金測試集** | ○ |
| `runtime/backtest.py` | 歷史插頭組合 | ○ |
| `runtime/live.py` | 即時插頭組合 | ○ |

**合計 19 個套件、約 34 個模組。目前 8 個模組完成。**

---

## 四、三個由原始碼反推出來的新增模組

這三個在原規劃裡完全不存在，是這次比對五份原始碼才浮出來的。

### ★ `types/stateful.py` —— 變數歷史（已補）

PowerLanguage 的每個 `variables:` 宣告都自帶歷史，`v_X[1]` 對任何變數合法。
我的 dataclass 狀態沒有這個能力，在 L2 手刻了一個 `c1_bar_prev` 頂著。

**手刻是特例不是機制**，做到 L4 時 `v_Stop_Level[1]` 又要再刻一次。

而 L4 的 `v_Stop_Level = MinList(v_Stop_Level[1], ...)` 是追蹤停損的棘輪，
歷史值取錯就整條錯掉，**而且不會報錯**。

### ★ `instruments/` —— 商品主檔

`BigPointValue` 目前掛在 `StrategyConfig` 上。那是商品屬性不是策略屬性 ——
同一支策略跑大台或微台，點值不同但策略不變。

而且 L5 直接用了 `MinMove / PriceScale` 算 TickSize，那兩個值目前無處可放。

換月規則也沒有家。三份規格都點名「換月接續造成假跳空」，但沒有任何套件負責它。

### ★ `engine/accounting.py` —— Fill 到權益曲線

```
Fill  →  ???  →  metrics/drawdown.equity_curve()
```

中間是斷的。`equity_curve()` 吃一串數字，但沒有模組把成交轉成那串數字。
而「含未平倉損益」需要 mark-to-market，需要標記價來源 —— 也不存在。

---

## 五、實作順序（按「哪一支能因此跑起來」排）

| 階段 | 模組 | 完成後 |
|---|---|---|
| **A** | `instruments/` · `timing/` · `quotes/session` `bars` `history` | 能吃 MC12 匯出的 1 分 K，聚合成任何週期 |
| **B** | `engine/orders` `position` `protective` `fill_mc12` `accounting` | **L2 能跑完整回測，產出交易清單與權益曲線** |
| **C** | `quotes/align` · `quotes/continuous` | L4 能跑（三資料流 + 換月） |
| **D** | `engine/orders` 加 Limit 單 | L3 能跑 |
| **E** | `engine/position` 加雙腿 + 分批 + 腿綁定 | L5 能跑 |
| **F** | `engine/context`（IOG + IntraBarPersist + BarStatus） | L1 能跑 |
| **G** | `parity/` + 黃金測試集 | 五支可對帳 |
| **H** | `risk/` · `state/` · `obs/` · `journal/` | 具備上線前置條件 |
| **I** | `notify/` · `broker/` · `runtime/live` | 可上線 |

**階段 A + B 是最小可跑組合。** 做完之後 L2 不再是「寫好但跑不了」，
而是「能跑出交易清單，可以拿去跟 MC 對」。

---

## 六、仍待你裁決（三題，都會影響模組介面）

| # | 問題 | 影響哪個模組 |
|---|---|---|
| **1** | **口數在哪一層決定？** 策略輸出（風險層只能否決）or 風險層決定（策略只輸出方向） | `types/orders.py` 的 `OrderIntent.quantity`。目前是策略輸出，**這是我寫程式時默默選的，沒問過你** |
| **2** | 停機開關：`StrategyConfig.manual_kill_switch` 與 `contracts.KillSwitch` 目前是兩份真相 | `state/` 與 `strategies/base.py` |
| **3** | 回測期初資金：200 萬（CLAUDE.md）/ 30 萬（實戰）/ 100 萬（L1 L2 標頭） | `metrics/` 與所有 MDD 百分比 |

第 1 題在機構裡是 alpha 與 sizing 分層的核心問題，且它**已經被我默默定案了**，
所以列在最前面。
