# 資料部

> 負責：回測與實戰資料的來源、格式、口徑換算

## 重點
- 回測報告：MC 匯出 Excel，必含「設定／策略分析／交易明細」，交易明細必須有**日期＋時間**欄
- 實戰紀錄：`台指_量化策略_260617開始_實戰策略.xlsx`；2 口同時進出算 1 筆
- 口徑換算：大台 1 點 200 元、微台 1 點 10 元，同口數時金額 ÷ 20；回測成本每口每邊 1,000 元（＝5 點），高於微台實際
- 帳戶口徑：以 30 萬為分母；MC 口徑（每支 200 萬）僅作輔助
- 日線資料：`txf_daily.json`（台指期日 OHLC），供波動與行情分段分析
- 未核對事項：券商對帳單 vs 實戰工作表（Phase 4 Task 4.5）

## 常用指令
```
python backtest/fetch_data.py                  # 抓資料
python backtest/optimize/walk_forward.py       # Walk-Forward
python backtest/optimize/monte_carlo.py        # Monte Carlo
python scripts/strategy_comparison.py          # 組合分析
python tools/make_baseline.py 報告.xlsx tools/baselines/Lx.json
```

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| 回測設定規格 | `docs/policies/BACKTEST_COST_SPEC.md` |
| 報告讀取器 | `tools/mc_report.py` |
| 資料格式 | `docs/specs/DATA_FORMAT.md` |
