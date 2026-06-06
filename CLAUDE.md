# TXF1-Strategy-Lab

## 專案概述
台指期貨（TXF1）量化策略研究庫。所有策略以 MultiCharts 12 PowerLanguage 撰寫，用 Python 做模擬回測驗證。

## 技術規格
- 商品：TXF1（台指期近月連續），1 點 = 200 NTD
- 平台：MultiCharts 12 / PowerLanguage（EasyLanguage 相容）
- 滑價：1,000 NTD round-trip（單邊 500）
- 固定口數：1 口
- 回測區間：2020/01/01 ~ 今天
- 交易時段：日盤 08:45-13:45 / 夜盤 15:00-05:00

## 目錄結構
```
CLAUDE.md                          # 本檔案 - Claude Code 的專案指引
strategies/
  batchNN/                         # 每批策略（Markdown + 回測 JSON）
backtest/
  fetch_data.py                    # 資料抓取（yfinance ^TWII）
  run_backtest.py                  # 批次回測腳本
  twii_daily.csv                   # TAIEX 日線資料快取
  optimize/                        # 參數優化腳本
    walk_forward.py                # Walk-Forward 優化框架
    monte_carlo.py                 # Monte Carlo 模擬
    param_sensitivity.py           # 參數敏感度分析
  results/                         # 優化結果
optimization/
  configs/                         # 各策略的優化設定 YAML
  reports/                         # 優化報告輸出
scripts/
  export_to_mc.py                  # 匯出 PowerLanguage 原始碼供 MC 載入
  strategy_comparison.py           # 策略組合分析
docs/
  optimization_guide.md            # 優化方法論文件
```

## PowerLanguage 程式碼規範
1. 所有參數用 `inputs:` 宣告，不可寫死
2. 變數用 `variables:` 宣告，`v_` 前綴
3. Data2 引用用 `[1]` 已收盤索引（Data2 當根不可靠）
4. 不使用未來函數（不可用 `highest(high, N)[0]` 前瞻引用）
5. 進場：`buy/sell short next bar at X stop/limit`
6. 出場：`sell/buy to cover next bar at X stop`
7. 不在同根 K 棒使用 `marketposition` 後立即引用
8. 用 `v_Prev_MP` 追蹤前根部位狀態，腳本最末行更新
9. 策略名稱 `STRATEGY_GEN_` 前綴
10. 每隻策略 < 150 行，進場條件 ≤ 5 個

## 優化工作流程（Claude Code 使用時遵守）

### Phase 1: 參數敏感度分析
對每個 input 參數，在合理範圍內掃描，繪製 3D 表面圖。
目標：確認參數有「高原」而非「尖峰」（尖峰 = 過度擬合）。

### Phase 2: Walk-Forward 優化
- In-Sample: 滾動 2 年
- Out-of-Sample: 滾動 6 個月
- 步長: 6 個月
- 合格標準: OOS PF > 1.0 且 OOS 淨利 > 0

### Phase 3: Monte Carlo 壓力測試
- 隨機打亂交易序列 10,000 次
- 計算 95% 信心水準下的 MDD
- 計算破產機率（帳戶虧損 > 50%）

### Phase 4: 策略組合分析
- 計算策略間相關性矩陣
- 模擬等權組合 equity curve
- 找最佳配置（Sharpe 最大化）

## 品質門檻
- Walk-Forward Efficiency > 50%
- Monte Carlo 95% MDD < 帳戶 30%
- 參數高原寬度 > 參數範圍的 20%
- OOS Profit Factor > 1.0
- 每月至少 2 筆交易

## 常用指令
```bash
# 抓取最新資料
python backtest/fetch_data.py

# 跑全策略回測
python backtest/run_backtest.py

# 單策略參數優化
python backtest/optimize/param_sensitivity.py --strategy NightMomentum --param LookbackBars --range 2,10

# Walk-Forward 驗證
python backtest/optimize/walk_forward.py --strategy NightMomentum

# Monte Carlo 壓力測試
python backtest/optimize/monte_carlo.py --strategy NightMomentum --iterations 10000

# 策略組合分析
python scripts/strategy_comparison.py
```
