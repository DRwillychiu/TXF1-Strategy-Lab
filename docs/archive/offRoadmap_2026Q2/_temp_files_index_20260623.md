# _temp_offRoadmap_2026Q2/ 32 個 work files 索引（已刪除）

**Archive 日期**：2026-06-23 (strategies cleanup 時刪除原檔)
**原位置**：`strategies/research/archive/_temp_offRoadmap_2026Q2/`
**處理**：
- 3 個 valuable JSONs 移到 `backtest/results/portfolio/` 永久保存
- 32 個 `_temp_*.{py,md,json}` 因 work-only nature 直接刪除
- 本文件作為 audit trail，索引曾存在的 work files

## 為什麼刪除

`_temp_` 前綴本身已標示「短暫」性質，是 2026-06-19~21 off-roadmap session 階段性產出：
- 含 38 個 file × 平均 15KB ≈ 600KB 殘留 work content
- Session 已 KILLED（產出 L14-L23 lessons + portfolio_saturation_acceptance）
- 後續開發已不需要這些 scripts/docs

## 已保留為永久 data（移到 `backtest/results/portfolio/`）

| 檔名（新位置） | 原檔 | 用途 |
|---------|------|------|
| `portfolio_pnl_6sleeves_2019-2026.json` | `_temp_portfolio_pnl.json` | 6 sleeve daily PnL series |
| `rolling_corr_raw_6sleeves.json` | `_temp_rolling_corr_raw.json` | Rolling correlation matrix |
| `rolling_sharpe_6sleeves.json` | `_temp_rolling_sharpe.json` | Rolling Sharpe 序列 |

## 已刪除的 32 個 _temp 檔索引

### Analysis docs (12 files)
| File | Content summary |
|------|----------------|
| `_temp_alpha_taxonomy.md` (35KB) | Alpha 分類學初稿（後正規化進 institutional_risk_framework）|
| `_temp_candidate_pipeline.md` (25KB) | S4-S15 候選 pipeline（後正規化進 OFFICIAL_ROADMAP）|
| `_temp_coverage_gap.md` (28KB) | Portfolio 7 sleeve 覆蓋缺口分析 |
| `_temp_daily_corr.md` (8KB) | Daily correlation report |
| `_temp_institutional_lib.md` (24KB) | 機構級 institutional library 初稿（後 → docs/policies/）|
| `_temp_is_oos.md` (12KB) | IS/OOS 分析報告 |
| `_temp_monthly_corr.md` (10KB) | Monthly correlation report |
| `_temp_overfit_check.md` (7KB) | Overfit detection 邏輯設計 |
| `_temp_regime_corr.md` (10KB) | Regime-conditional correlation |
| `_temp_rolling_corr.md` (8KB) | Rolling correlation analysis |
| `_temp_rolling_stats.md` (10KB) | Rolling statistics report |
| `_temp_sharpe_analysis.md` (5KB) | Sharpe 計算說明 |
| `_temp_txf_anomalies.md` (14KB) | TXF1 anomaly catalog |
| `_temp_yearly_metrics.md` (8KB) | 年度指標摘要 |

### S3-specific docs (6 files, off-roadmap S3=RapidPullback context)
| File | Content summary |
|------|----------------|
| `_temp_s3_exit_mechanism.md` (26KB) | S3 RapidPullback 出場機制設計 (已被 S3_RPS_v2.0.4 production .pla 取代)|
| `_temp_s3_implementation_arch.md` (27KB) | S3 implementation architecture |
| `_temp_s3_momentum_trigger.md` (28KB) | S3 momentum trigger 設計 |
| `_temp_s3_portfolio_impact.md` (28KB) | S3 對 portfolio 影響分析 (後 → portfolio_v3) |
| `_temp_s3_regime_gate.md` (32KB) | S3 regime gate 設計 |
| `_temp_short_rip_design.md` (35KB) | Short Rip 策略設計初稿 |

### Python scripts (10 files)
| File | Purpose |
|------|---------|
| `_temp_compute_sharpe.py` (15KB) | Sharpe 計算腳本 |
| `_temp_corr_heatmap.py` (10KB) | Correlation heatmap generator |
| `_temp_daily_corr_analysis.py` (17KB) | Daily correlation analyzer |
| `_temp_is_oos_analysis.py` (15KB) | IS/OOS analyzer |
| `_temp_make_report.py` (12KB) | Report generator |
| `_temp_overfit_runner.py` (15KB) | Overfit detection runner |
| `_temp_rolling_calc.py` (7KB) | Rolling stats calc |
| `_temp_rolling_corr_analysis.py` (19KB) | Rolling correlation analyzer |
| `_temp_rolling_report.py` (11KB) | Rolling report writer |
| `_temp_s3_pullback_stats.py` (10KB) | S3 pullback stats (已用過, 結果固化到 S3_RPS .pla)|

### Data (2 files retained → backtest/results/portfolio/)
(see above)

### 其他 (2 files)
| File | Purpose |
|------|---------|
| `_temp_s3_pullback_stats.json` (4KB) | S3 pullback raw stats (已用過, 不需要保留) |
| `_temp_yearly_summary.json` (11KB) | 年度摘要 raw data |

---

## 復原方法

若未來需要某個 _temp file：
```bash
git log --all --pretty=format:"%H %s" -- "strategies/research/archive/_temp_offRoadmap_2026Q2/_temp_<name>.md"
git show <commit_hash>:strategies/research/archive/_temp_offRoadmap_2026Q2/_temp_<name>.md > recovered.md
```

git history 保存所有歷史內容，本目錄刪除只清 working tree。

---

**最後 commit before deletion**：`07d96e2` (2026-06-23 S3_L sync)
