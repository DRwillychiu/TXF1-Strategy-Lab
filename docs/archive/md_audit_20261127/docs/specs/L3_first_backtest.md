# L3 首次回測結果（2026-09-07）

## 結果

視窗 **2020-05-12 ~ 2026-07-25**（v14.1 標頭明載）

| | Python | MC v15.0 |
|---|---|---|
| **筆數** | **379** | **376** |
| PF | 1.319 | 1.255 |
| 勝率 | 45.9% | 46.3% |
| `CL_ReEntry` | 50 | 區間 20–115 ✓ |

**差 +3 筆（+0.8%）——三支裡最接近的。**

## ★ 視窗的影響比我追了一整天的東西都大

同一份程式碼、同一份資料：

```
2019-12-16 ~ 2026-07-25   399 筆   與 MC 376 差 +23  (+6.1%)
2020-05-12 ~ 2026-07-25   379 筆   與 MC 376 差 +3   (+0.8%)
```

我先前對三支都用 2019-12-16——**那是 L1 的基準起點，不是 L3 的**。
L3 的標頭明載「Backtest: 2020/05/12 - 2026/07/04」。

> **視窗是第一級參數，而且每支不同。**
> 已編碼進 `parity/anchors.py` 的 `backtest_start` / `backtest_end`，
> 並提供 `window()` 統一套用。

## 三支的對帳狀態

| | Python | MC | 差 |
|---|---|---|---|
| **L3** | 379 | 376 | **+0.8%** |
| **L4** | 83 | 82 | **+1.2%** |
| **L2** | 80 | 77 | **+3.9%** |

## 從原始碼取得、規格表原本沒有的參數

| 參數 | 值 |
|---|---|
| `v_ATR_Buffer` | **`ATR_Stop_Mult × ATR(9)` = 3.0 × ATR** |
| `Entry_Zone_Pct` | 0.50（掃描 0.30 → 0.50，71% 分位） |
| `Min_Box_ATR` | 8.5（掃描 3.0 → 8.5，85% 分位，未貼邊界） |
| `Swing_Lookback` | 80（掃描 32 → 80，63% 分位） |

## ★ L3 的 re-entry 解除是結構性的，這正是 L4 v18 失敗的教訓

原始碼註解明載：

> Disarm when the box episode ends. This is the ONLY disarm, and it is
> structural rather than price based -- **L4 v18 fired zero times because
> its price disarm was implied by its own stop**, and that trap is avoided
> here by not testing a price at all.

**L4 v18 的價格解除條件（`Close of Data2 > 箱頂`）被它自己的停損蘊含**
（停損永遠在箱頂上方 2 個 ATR），所以旗標在設立的同一根就被清掉。

L3 完全不測價格——**episode 變了就解除**，零自由參數。

## 為什麼 L3 不能沿用 L2 的 re-entry 定義

原始碼註解：

> L2's definition does not transfer. On L3 it selects **134 of 360 trades,
> 37 pct of everything.** L3 enters at `v_Box_Btm` with a Buy Stop and the
> box bottom is a **MOVING structural level**, so "entry at or below the
> previous entry" mostly means "the box did not move up" — not a re-entry.

而且 L3 的比較在決策當下就成立：**訂單價就是 `v_Box_Btm`，下單時已知**。
L2 v5.4 揭露的陷阱（比一個還不存在的成交價）在 Buy Stop 上不存在。

## 執行層第一次用到 OCO

L3 常態同時掛 `CL_TP`（限價）+ `CL_SL`（停價）。實測 OCO 撤銷 **0 次**——
TP 在箱頂、SL 在箱底減 3 ATR，一根 15M K 棒同時觸及兩者極罕見。

**但機制必須存在**，L5 的每腿訂單集合會用到。

## 已知落差（照抄，未修）

**[D-1] `SetStopContract` 在盤整判斷內。** L5 的註解寫
「must be outside conditional」。若 L5 正確，這裡是錯的。

**[D-2] 箱體失效後 TP 與 SL 兩張都不再掛出。** 執行區塊在
`if v_is_in_consolidation` 之內，`else` 分支只發市價 `CL_BreakExit`。

**[D-3] `CL_Kill` 在 else-if 鏈外。** 與 L1 的 J-3 同型。
一根最多四張：TP + SL + 安全出場 + Kill。

## 待處理

- [ ] 標頭內部矛盾：`PERFORMANCE` 376/2,446,000 vs v15.1 `CHANGELOG` 360/1,389,600
- [ ] 淨利 3,005,415 vs 2,446,000（+23%），筆數只差 +0.8%——需逐筆才知道差在哪
