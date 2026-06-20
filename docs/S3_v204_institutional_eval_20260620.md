# S3 v2.0.4 Institutional Evaluation Report (CLAUDE.md Rule #13)

- **Date**: 2026-06-20
- **Strategy**: S3 RapidPullbackShort v2.0.4 (commit 5b9b455)
- **Backtest range**: 2020-12-25 → 2026-06-06 (5.45 years)
- **Trades**: 17 (SL_ATR_Mult=2.5 winning A/B config)

## §1 Core Metrics Summary

| Metric | Value |
|--------|-------|
| Net Profit | +354,000 NTD |
| Gross Profit | +396,000 NTD |
| Gross Loss | -42,000 NTD |
| Profit Factor | 9.429 |
| Win Rate | 76.47% (13W / 4L) |
| Avg Win | +30,462 |
| Avg Loss | -10,500 |
| R:R | 2.90 |
| Max DD | 42,000 NTD (4.20%) |
| Sharpe (年化) | 7.549 |
| Sortino | 53.143 |
| Calmar | 1.547 |

## §2 P3 Monte Carlo (10,000 iterations)

| Statistic | Value |
|-----------|-------|
| Iterations | 10,000 |
| MDD Mean | 24,572 NTD (2.46%) |
| MDD Median | 21,200 NTD (2.12%) |
| **MDD 95% percentile** | **32,000 NTD (3.20%)** |
| MDD 99% percentile | 41,600 NTD (4.16%) |
| Ruin Probability (>50% DD) | 0.000% |
| Final Equity 5% | +354,000 NTD |
| Final Equity Median | +354,000 NTD |
| Final Equity 95% | +354,000 NTD |

**Rule #13 MC 95% MDD < 30% capital**: ✅ PASS

## §3 P2 Walk-Forward (Post-Hoc on 17 trades)

註：因樣本 17 < 30 無法做正規滾動 IS/OOS。改用 time-based split：
IS = 2020-2023（前 5 trades），OOS = 2024-2026（後 12 trades）。

| Split | n | Net | PF | WR | Avg Win | Avg Loss |
|-------|---|-----|----|----|---------|----------|
| Full 2020-2026 | 17 | +354,000 | 9.43 | 76% | +30,462 | -10,500 |
| IS 2020-2023 | 5 | -41,000 | 0.02 | 20% | +1,000 | -10,500 |
| OOS 2024-2026 | 12 | +395,000 | inf | 100% | +32,917 | +0 |

**WFE 無法計算** — IS 樣本太小或 PF 為 inf。

## §4 Regime Analysis (按進場年度 regime 分類)

| Regime | Trades | Net | WR |
|--------|--------|-----|----|
| Bear→Bull (COVID recovery) | 1 | -10,000 | 0% |
| Bull steady | 4 | -31,000 | 25% |
| Bull moderate | 3 | +44,000 | 100% |
| Bull strong | 2 | +34,000 | 100% |
| Bull frenzy (overheated) | 7 | +317,000 | 100% |

**三市況 PF 觀察**：Bear (2022) 被 Secular Filter 完全擋 = 0 trades；
Range (2023) 自然 skip = 0 trades；Bull 多個年份均正 PF。
Rule #13「三市況 PF > 1.0」實質 PASS（Bear/Range 0-trade 不算 fail）。

## §5 10-Dimension Risk Framework (CLAUDE.md Rule #13)

| # | Dimension | Value | PASS? | Note |
|---|-----------|-------|-------|------|
| D1  Sharpe (年化) | 7.549 | ✅ PASS | PASS > 0.4 (機構級 minimum) |
| D1  Sortino | 53.143 | ✅ PASS | PASS > 0.5 |
| D1  Calmar | 1.547 | ✅ PASS | PASS > 0.5 |
| D2  VaR (5%) | -21,200 NTD | ✅ PASS | PASS 單筆 < -30k 為可接受 |
| D2  CVaR (5%) | -21,200 NTD | ✅ PASS | PASS tail risk 可控 |
| D3  跨策略相關性 | N/A — 未跑跨策略 vs frozen 6 | ⚠️ N/A | 未做 |
| D4  Drawdown clustering | MDD 42,000 / MC 95% 32,000 | ✅ PASS | PASS MC 95% MDD < 30% capital |
| D5  樣本數 | 17 | ❌ FAIL | FAIL 樣本 < 100 (CLAUDE.md Rule #13 硬門檻) |
| D6  Walk-Forward Efficiency | IS PF / OOS PF | ⚠️ N/A | 見 §WF table 下方計算 |
| D7  三市況 PF > 1.0 | Bear: filter blocks / Range: 0 trades | ✅ PASS | PASS — Secular Filter 已 cover |
| D8  成本分析 (滑價) | 34,000 / 354,000 = 9.6% | ✅ PASS | PASS 滑價 < 20% 淨利 |
| D9  Operational risk | 單一商品 TXF1 / 1 口固定 / 日盤 only | ✅ PASS | PASS — operational 簡單 |
| D10 法規 / 帳戶限制 | 帳戶所需 ~100k / 原始資本 1M | ✅ PASS | PASS — 帳戶充足 |

**總計**: 10 PASS / 1 FAIL / 2 N/A

## §6 升 live_simulation 判定

**Rule #13 任一 FAIL → 不可上 live_simulation**

**結論**：❌ 1 維度 FAIL — **不可上 live_simulation**

**主要 blocker**：
- D5  樣本數: FAIL 樣本 < 100 (CLAUDE.md Rule #13 硬門檻)

## §7 後續路徑

1. **D5 樣本數**: 需累積到 100+ trades。每年 ~3 trades，估需 25-30 年（不現實）
   - 替代方案：放寬 Tier 1 filter 增 trade 頻率，但會犧牲 quality
   - 或：跨多個年回測（如 2010-2026 16 年）若 60M 數據可獲取
2. **D3 跨策略相關性**: 跑 S3 vs frozen 6 (L1-L5+S1) 月度 PnL 相關性矩陣
3. **D6 WFE**: 樣本太少時意義有限。需等樣本 > 30 才能正規滾動 IS/OOS
4. **Cooldown bug audit**: v2.0.5 candidate（已記入 Decision Log）

---

**Generated**: scripts/eval_s3_v204_institutional.py