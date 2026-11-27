# 外部借鑑

> 2026-09-06。四個開源專案，逐項對應到我們缺的東西。
> **記錄「沒採用的」與「採用的」同等重要**——否則六個月後會有人重問一次。

---

## 一、NautilusTrader

`github.com/nautechsystems/nautilus_trader`

### 驗證了我們的鐵則，但也修正了它

其文件說明<cite index="21-1">同一份策略與執行演算法程式碼可以同時跑在回測與實盤系統上，藉此降低部署時的分歧</cite>——這與我們的鐵則一致。

**但它接著加了一句我們原本沒有的誠實聲明**：<cite index="21-1">實盤執行仍會帶來場所、傳輸、時序、持久化、外部活動與對帳等模擬未必能重現的行為</cite>。

> **我們原本的鐵則寫「只有三顆插頭不同」，那不是全部的真相。**
> 已在 `LAYERS.md` 補上這條限制。

### 採用：訂單生命週期

其架構文件描述的順序是——RiskEngine 先做盤前檢查（部位上限、名目上限、
下單速率），<cite index="23-1">若檢查未通過，策略會收到 OrderDenied，訂單根本到不了交易所</cite>；
通過後 ExecutionEngine 路由給 ExecutionClient 送出，之後
<cite index="23-1">Accepted、Filled、Canceled、Rejected、Expired 等事件逐一回流，由 ExecutionEngine 更新 Cache 中的訂單狀態並交給策略的 handler</cite>。

**我們原本是 `OrderIntent → Fill`，中間什麼都沒有。** 三個後果：

| 缺口 | 後果 |
|---|---|
| 風險層攔截後策略不知道 | 它以為單送出去了，誤解會累積成錯誤的部位認知 |
| 部分成交表達不出來 | **L5 的 Stage 2/3 判定完全靠 `CurrentContracts`** |
| 拒單、逾時、重複回報 | 沒有型別可以承載 |

**已實作** `engine/orders.py`：`INITIALIZED → DENIED / SUBMITTED → ACCEPTED →
PARTIALLY_FILLED → FILLED / CANCELED / REJECTED / EXPIRED`，非法轉移拋例外。

**兩個關鍵區分**：

- `DENIED`（我們攔的）vs `REJECTED`（交易所拒的）—— 對帳時必須分得開
- `DENIED` **是一個回流給策略的事件**，不只是風險層的內部回傳值

### 採用：只有實盤需要對帳迴路

其文件明載<cite index="26-1">執行對帳把場所的實際訂單與部位狀態，與系統由事件建立的內部狀態對齊；只有 LiveExecutionEngine 會做對帳，因為回測兩邊都由自己控制</cite>。

這正好解釋了我們的 `risk/reconcile.py` 為什麼只在 live 模式有意義。

### 採用：單執行緒決定性

其架構說明<cite index="23-1">核心在單一執行緒上消化並分派訊息，提供決定性的事件順序，有助於維持回測與實盤的一致性</cite>。

這是我們規劃書 §7「同一根 K 棒同一組狀態，重跑一萬次都一樣」的**實作機制**。
我們目前的 runner 本來就是單執行緒迴圈，符合；但把理由寫下來，
避免日後有人為了加速而引入並行。

### 未採用：MessageBus、Cache、Actor 系統

**規模不符。** 那套是為多場所、多資產、多策略同時運行設計的。
我們是五支策略、一個帳戶、一個商品。引入訊息匯流排會增加一層間接性
而換不到對應的好處。

**但若日後五支要同時跑 + 組合層要仲裁**，這是該回頭看的地方。

---

## 二、hftbacktest

`github.com/nkaz001/hftbacktest`

### 採用：延遲分兩類分別建模

其說明寫著<cite index="15-1">此框架聚焦於同時計入行情延遲與訂單延遲，以及訂單在佇列中的位置</cite>，
而 roadmap 更進一步規劃<cite index="14-1">讓下單、改單、撤單以及訂單回應、成交、部位推送各自可以有不同的延遲</cite>。

**我們的三戳記（event / receipt / decision）型別上定義了，但沒有任何東西在填。**

**已實作** `timing/latency.py`：

```
ZeroLatency       mc12 對帳模式。必須是零——MC 沒有延遲概念，加了就對不上帳
FixedLatency      live 的粗略近似。標記 is_measured = False
MeasuredLatency   從實盤錄下，依時間重放。並提供 percentile()
```

### 最有價值的一點：從實盤錄，回測時重放

其範例中的 `intp_order_latency(['latency/live_order_latency_20220831.npz', ...])`
吃的就是**實盤錄下來的延遲檔**。

> **這件事我們現在就能做。**
> MC12 正在實盤自動下單，**下單時刻與成交回報時刻的差就是 order latency 樣本**。
> 錄一個月，回測就有真實的延遲分布可用。

而且 `MeasuredLatency.percentile()` 提醒了一件事：
**風險判斷要用 p99，不是平均**——延遲分布是長尾的，用平均會系統性低估最壞情況。

### 未採用：佇列位置模型

台指期貨的停損單與市價單不需要佇列位置——那是掛限價單做市才需要的。
L3 與 L5 有 Limit 單，但都是停利出場，不是掛在盤口等成交。

**但它背後的原則我們已經採用了**：成交是一個**模型**，不是事實。
這正是 `engine/fill_mc12.py` 把 intrabar 順序做成可切換 policy 的理由。

### 未採用：Numba JIT / Rust 核心

我們是 60M / 15M / 45M K 棒，全歷史 35,352 根，跑一次約三秒。**沒有效能問題。**

---

## 三、vectorbt

`github.com/polakowo/vectorbt`

### 未採用，但記錄一個未來的臨界點

它的核心是把回測寫成**向量化的陣列運算**，讓大規模參數掃描變快。

我們目前是逐根 Python 迴圈：

| 用途 | 執行次數 | 目前耗時 | 可接受 |
|---|---|---|---|
| 單次回測 | 1 | ~3 秒 | ✓ |
| MC 式參數掃描（SL_Pct 0–5 step 0.25） | 21 | ~1 分鐘 | ✓ |
| Walk-Forward（CLAUDE.md Phase 2） | ~30 | ~2 分鐘 | ✓ |
| **Monte Carlo 10,000 次（CLAUDE.md Phase 3）** | **10,000** | **~8 小時** | **✗** |

**臨界點在 Monte Carlo。** 但那一步的做法應該是「重排已完成回測的交易序列」，
不是重跑一萬次回測——所以真正需要向量化的可能只有 `metrics/`，不是整個引擎。

**現在不做。到了 Phase 3 再評估。**

---

## 四、kalshi-market-making

`github.com/nikhilnd/kalshi-market-making`

### 未採用

做市策略：雙邊報價、庫存管理、價差捕捉。
我們五支都是**單邊方向性策略**（三多兩空），沒有報價、沒有庫存中性化需求。

唯一相關的是訂單管理，而那部分 NautilusTrader 的模型更完整。

---

## 五、四個專案共同指向的一件事

| 專案 | 它們都在做同一件事 |
|---|---|
| NautilusTrader | 同一份程式碼跑回測與實盤，但**明說模擬不能重現什麼** |
| hftbacktest | 延遲與成交是**模型**，且模型可替換、可從實盤校準 |
| vectorbt | 研究用向量化，生產用事件驅動，**兩者是不同的東西** |

> **共同點：它們都不假裝模擬等於真實，而是把「哪裡不等於」明確標出來。**

我們的 `FillPolicy`、`LatencyModel.is_measured`、
以及對帳的三層（decision / fill / performance）走的是同一條路：
**把未知變成參數，而不是把猜測寫死。**

---

## 已落地的改動

| 檔案 | 來源 | 內容 |
|---|---|---|
| `engine/orders.py` | NautilusTrader | 訂單狀態機 + `DENIED` 回流事件 + OCO |
| `timing/latency.py` | hftbacktest | feed / order / response 三種延遲 + 實盤錄製重放 + percentile |
| `LAYERS.md` | NautilusTrader | 鐵則補上「模擬不能重現什麼」的誠實聲明 |

## 待辦

- [ ] **開始錄 MC12 實盤的下單→回報延遲**（現在就能做，錄一個月就有分布）
- [ ] `risk/` 實作盤前檢查並回傳 `OrderDenied` 事件
- [ ] `runtime/backtest.py` 改用 `OrderBook` 管理在途訂單（目前是簡化的 list）
- [ ] L3 / L5 動工時啟用 OCO 群組

---

# 第二批 2026-09-06

## 六、Kronos

`github.com/shiyu-coder/Kronos` · MIT · AAAI 2026

K 線的基礎模型：專用 tokenizer 把 OHLCV 量化成階層式離散 token，
再以 decoder-only Transformer 自迴歸預訓練，訓練資料涵蓋 45 個以上交易所。

### 最有價值的不是模型，是它 README 裡的一句話

其 README 註明：`finetune/` 目錄裡許多程式碼註解是由 AI 助理產生的，
可能包含不準確之處，**建議把程式碼本身當作邏輯的權威來源**。

> **這正是 V2.9 的機制。**
> 舊標頭把 P3 錯誤地改述成「Entry − MaxList(distances)」，
> P3b 照著錯的形狀寫，橫跨整個 V2.6+ 世代未被發現。
>
> 一個 23k star 的專案把「註解可能說謊、以程式碼為準」寫進 README。
> 我們規格表那句「凡註解與程式碼衝突，以程式碼為準」現在有外部佐證。

它另外註明，高保真的回測應該仔細建模交易成本、滑價與市場衝擊，
才能給出接近真實的績效估計——**同一種誠實聲明**。

### 不採用模型本身

**我們在做複述，不是預測。** 用 ML 預測會直接違反硬規則：

> Python 引擎在逐筆重現五支現行版本之前，不得用於任何新的參數掃描或邏輯評估。

### 但記錄一個未來選項：合成 K 棒

Kronos 明列**合成資料生成**為下游任務之一。

這正好補上我自己承認的缺口——黃金測試集的 12 個案例**全是我出的題我自己答**，
規格表要求用「構造案例」補上選擇偏誤，但那些案例目前是手寫的。

用合成 K 棒生成「進場後同根即穿破停損」這類罕見情境，比手寫真實。
**Phase 3 再評估，現在不做。**

---

## 七、freqtrade

`github.com/freqtrade/freqtrade`

### 採用：組合層斷路器

freqtrade 把「最近表現太差就暫停」做成可組合的 protections。
**MC 從來沒有這一層**——它一次只跑一支、一個帳戶、固定口數。

**已實作** `risk/protections.py`（原本是空目錄）：

| 保護器 | 擋什麼 | 為什麼策略層管不到 |
|---|---|---|
| `MaxDrawdownGuard` | 回撤超門檻 → **HALT_ALL** | 策略層停損只管單筆 |
| `StoplossGuard` | 窗口內停損 N 次 → 擋新進場 | L2 最大連續虧損 9 次，單筆停損管不到「連續九次」 |
| `CooldownPeriod` | 出場後冷卻 | L4 的 `Cooldown_Bars=8` 是策略層內建的，這是組合層 |
| `ExposureLimit` | 總口數上限 | 規劃書層 3 第一條不變量 |

`ProtectionStack` 依序檢查，**HALT_ALL 優先於 BLOCK_ENTRY**——
與策略層的優先級鏈同一個原則。

`CooldownPeriod` 預設 `per_strategy = True`，只擋該支，**與 MC 行為一致**；
改成擋全部才是新行為，屬 `v2` 模式。

### 待採用：dry-run

freqtrade 的 dry-run 是「跑實盤資料但不下單」。

**這正是 L1 平行前向驗證需要的東西，也是從 MC12 切換到 Python 的安全路徑：**

```
Python 上線但只發訊號、不下單    MC12 繼續實盤
每天比對「Python 說要下的單」vs「MC12 實際下的單」
連續 N 天一致 → 選一個空手時點切換
MC12 保持可隨時啟動作為回退
```

`runtime/live.py` 尚未實作。**這是層 5 動工時的第一個模式，不是最後一個。**

---

## 八、skfolio

`github.com/skfolio/skfolio` · BSD-3

建於 scikit-learn 之上的組合最佳化與風險管理，遵循 fit-predict-transform 範式。

### 採用：回撤家族的其餘度量

其風險度量清單包含 CVaR、CDaR、EDaR、Ulcer Index、平均回撤、
最大回撤、最壞實現值等等。

**我們的 `metrics/drawdown.py` 只回答「最壞的一次有多深」。那是單點統計。**

**已實作** `metrics/risk.py`：

| 度量 | 回答什麼 |
|---|---|
| `max_drawdown` | 最壞的一次（已有） |
| `average_drawdown` | 平常有多深 |
| `cdar_95` | 最壞 5% 的回撤平均。**比 MDD 穩定**，單一極端值不主導 |
| `ulcer_index` | 回撤的均方根。**同時懲罰深度與持續時間** |
| `cvar_95` | 最壞 5% 期間的平均損失 |
| `worst_realization` | 最壞的單期。**日內停損上限的直接依據** |

**Ulcer Index 的價值**：兩條曲線可以有相同的 `max_drawdown`，
但一條很快回復、一條拖兩年。**MDD 分不出來，Ulcer 分得出來。**
已寫成測試 `test_ulcer_distinguishes_curves_with_same_max_drawdown`。

### 實測結果

| | 筆數 | max_dd | avg_dd | CDaR95 | Ulcer | 最壞單期 | 水下比例 |
|---|---|---|---|---|---|---|---|
| L2 回測 | 92 | 9.26% | 2.45% | 8.20% | 3.51% | 2.77% | **73.6%** |
| L4 回測 | 95 | 14.65% | 2.60% | 10.60% | 3.80% | 5.12% | **77.9%** |
| **76 天實戰（五支）** | 59 | **31.53%** | — | — | — | — | **96.7%** |

**兩件事值得注意：**

一、**單支回測的 max_dd 都在 15% 以下，但五支實戰組合是 31.53%。**
這同時反映了「不可相加」與「回測用樂觀成交假設」兩件事。

二、**水下比例 73.6% / 77.9% / 96.7%。** 三分之二以上的時間在回撤中，
而 `max_drawdown` 這個數字完全看不出這件事。

### 待採用：CombinatorialPurgedCV

skfolio 的 `model_selection` 提供 `WalkForward` 與 `CombinatorialPurgedCV`。
其文件說明組合式交叉驗證會產生**多條路徑**而非單一路徑，
所以輸出是一個 Population 而不是單一組合。

**這直接對應 CLAUDE.md 的 Phase 2 Walk-Forward 與 Phase 3 Monte Carlo。**
單一 walk-forward 路徑只是一條樣本；CPCV 給出路徑的分布。

**Phase 2 再評估。現在做會違反「複述之前不得用於發現」。**

---

## 九、hummingbot

`github.com/hummingbot/hummingbot`

### 不採用

做市框架：雙邊報價、庫存中性化、跨交易所套利。
我們五支都是單邊方向性策略，沒有報價也沒有庫存中性化需求。

與 kalshi-market-making 同一類，訂單管理的部分 NautilusTrader 的模型更完整。

---

## 十、八個專案的共同結論

| 主題 | 來源 | 我們的落地 |
|---|---|---|
| 同程式碼跑兩端，**但明說模擬不能重現什麼** | NautilusTrader | `LAYERS.md` 的誠實聲明 |
| 訂單生命週期 + `OrderDenied` 回流 | NautilusTrader | `engine/orders.py` |
| 延遲分類建模 + **從實盤錄後重放** | hftbacktest | `timing/latency.py` |
| 成交是**模型**不是事實 | hftbacktest | `engine/fill_mc12.py` 的 `FillPolicy` |
| **註解可能說謊，以程式碼為準** | Kronos | 規格表的裁決規則獲外部佐證 |
| 組合層斷路器 | freqtrade | `risk/protections.py` |
| dry-run 是切換路徑 | freqtrade | `runtime/live.py` 待做 |
| 風險是一族度量不是單一數字 | skfolio | `metrics/risk.py` |
| 交叉驗證要給路徑分布 | skfolio | Phase 2 待評估 |

> **它們都不假裝模擬等於真實，而是把「哪裡不等於」明確標出來。**
