# backtest/ — Python 日線代理回測（DEPRECATED 歷史紀錄）

> ⚠️ **本資料夾全部為 2026-06-07 之前的 Python 日線代理回測，使用 ^TWII 而非真實 TXF1 數據。**
> ⚠️ **所有真實回測現以 MultiCharts 12 進行**，本資料夾僅保留作為**歷史基線證據**與**原始 S1-S15 概念驗證**用途。

---

## 一、為什麼歸類為 DEPRECATED

| 問題 | 影響 |
|------|------|
| 用 ^TWII 日線而非 TXF1 真實期貨 tick | 缺夜盤、缺真實 OHLC 形成 |
| 跳過 MC 引擎邏輯（IOG / SetStopLoss 等） | 無法重現實盤行為 |
| `run_backtest.py` 內含硬編路徑 `/tmp/...` | Windows 環境跑不起來 |
| 與 MC12 真實回測差距可達 30-50% | 不能作為 alpha 證據 |

---

## 二、檔案清單

### Python 腳本（歷史用途）

| 檔案 | 用途 | 狀態 |
|------|------|------|
| [`fetch_data.py`](fetch_data.py) | 用 yfinance 抓 ^TWII 日線 | 可運行（但結果不可信） |
| [`run_backtest.py`](run_backtest.py) | 跑 S1-S5 日線代理回測 | ⚠️ **DEPRECATED**（硬編路徑） |
| [`twii_daily.csv`](twii_daily.csv) | ^TWII 日線資料快取 | 歷史資料 |
| [`results_batch01.json`](results_batch01.json) | Batch01 (S1-S5) 日線回測結果 | 原始基線 |
| [`results_batch02.json`](results_batch02.json) | Batch02 (S6-S10) 日線回測結果 | 原始基線 |

### Walk-Forward / Monte Carlo 框架（`optimize/`）

| 檔案 | 用途 | 狀態 |
|------|------|------|
| [`optimize/walk_forward.py`](optimize/walk_forward.py) | Walk-Forward 框架（IS/OOS 滾動） | 仍可參考 |
| [`optimize/monte_carlo.py`](optimize/monte_carlo.py) | Monte Carlo 模擬 10k 次 | 仍可參考 |
| [`optimize/param_sensitivity.py`](optimize/param_sensitivity.py) | 參數敏感度分析 + 3D 表面圖 | 仍可參考 |
| [`optimize/s1_optimize.py`](optimize/s1_optimize.py) | S1 專屬優化腳本 | 歷史紀錄 |
| [`optimize/s1_mc_optimized.py`](optimize/s1_mc_optimized.py) | S1 MC 最佳化結果 | 歷史紀錄 |

### 視覺化結果（`results/`）

| 檔案 | 內容 |
|------|------|
| [`results/s1_optimization/`](results/s1_optimization/) | S1 Phase 1-3 視覺化圖表（heatmap / WFA / MC） |

---

## 三、原始基線回測結果（**僅供參考**）

`results_batch01.json`、`results_batch02.json` 為 S1-S10 在日線代理上的 Profit Factor / MDD / 淨利。
此為 2026-06-07 原始排程基線，**已被 MC12 真實回測超越**：
- S1：日線代理 PF 1.448 → MC12 15M v2.1 = +1,997K NTD, WFE 62.5%
- S3：日線代理 PF 0.88（虧）→ MC12 60M 未測（即將開始 W0 Pre-verify）

詳細真實基線見：[`optimization/TRACKER.md`](../optimization/TRACKER.md)

---

## 四、未來使用方式

### 不要做的事
- ❌ 不要用 `run_backtest.py` 作為策略決策依據
- ❌ 不要用 `results_batch01.json` 作為 alpha 證據（已過時）

### 可以做的事
- ✅ 用 `fetch_data.py` 抓 ^TWII 補充資料（如指數位階長期 thesis）
- ✅ 用 `optimize/walk_forward.py` 框架移植到 MC12 流程
- ✅ 引用本資料夾作為「S1-S10 原始概念基線」歷史紀錄

---

## 五、相關文件

- 當前 MC12 真實回測流程：[`docs/methodology/entry_exit_sop.md`](../docs/methodology/entry_exit_sop.md)
- S3 即將開始的 W0 Pre-verify：[`docs/policies/OFFICIAL_ROADMAP.md`](../docs/policies/OFFICIAL_ROADMAP.md)
