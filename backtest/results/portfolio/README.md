# backtest/results/portfolio/ — 6-sleeve portfolio raw analytics

**來源**：2026-06-21 off-roadmap session 產出（後 session KILLED 但 data 有 reuse 價值）
**移入此位**：2026-06-23 strategies cleanup（從 `strategies/research/archive/_temp_offRoadmap_2026Q2/` 移出）

## 檔案

### `portfolio_pnl_6sleeves_2019-2026.json`
**內容**：L1 / L2 / L3 / L4 / L5 / S1 六隻 sleeve 的 daily PnL series（2019-12-18 ~ 2026-06-XX）

格式：
```json
{
  "L1": {"2019-12-18": 32400.0, "2019-12-19": -6200.0, ...},
  "L2": {...},
  "L3": {...},
  "L4": {...},
  "L5": {...},
  "S1": {...}
}
```

**用途**：
- 跨策略 correlation 計算（W5 Dim 3）
- Portfolio equity curve 模擬
- Sharpe / Sortino / Calmar 重算

⚠️ 不含 S3_RPS (2026-06-20 deploy 後) 與 S3_L (2026-06-23 deploy)。如需 7-8 sleeve 完整 data，需從各策略 xlsx 重新提取 daily PnL append。

### `rolling_corr_raw_6sleeves.json`
**內容**：6 sleeve 間 rolling correlation matrix raw data

**用途**：穩定性檢驗（correlation 隨時間漂移程度）

### `rolling_sharpe_6sleeves.json`
**內容**：6 sleeve 各自 rolling Sharpe（trade_days array + rolling window stats）

**用途**：alpha decay 偵測（rolling Sharpe 下降 = alpha 弱化警報）

## 重建 / 更新

若需把 S3_RPS + S3_L 加入：
1. 用 `scripts/_temp_analyze_s3l_w5_10dim.py` pattern 從 MC12 xlsx 提取 daily PnL
2. Merge 到 `portfolio_pnl_6sleeves_2019-2026.json` （變成 8 sleeves）
3. 重算 rolling_corr / rolling_sharpe

---

**Note**：本資料夾以前不存在 — 2026-06-23 cleanup 時為了給有 reuse 價值的 portfolio data 一個永久位置而建立。
