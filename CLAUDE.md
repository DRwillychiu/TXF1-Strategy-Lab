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

## 目錄結構（三層分類，2026-06-13 重組）
```
CLAUDE.md                          # 本檔案 - Claude Code 的專案指引
strategies/
  live/                            # 實盤上架（真金白銀）— L1-L5
    README.md                      # 上架策略清單 + 共通保護模組
    L1_TrendLong.pla
    L2_TrendShort.pla
    L3_ConsolidationLong.pla
    L4_ConsolidationShort.pla
    L5_BreakoutLong.pla
    L*_annotated.md
    L*_review.md
  live_simulation/                 # 上架但模擬中（MC12 模擬帳戶）— S1
    README.md                      # 模擬中策略 + 晉升 live 條件
    S1_NightMomentum.pla
    S1_NightMomentum_annotated.md
  research/                        # 研究中（未通過 P1-P3）— S2-S15
    README.md                      # 研究流程 + 晉升模擬條件
    batch01/                       # 第一批：S2-S5
    S06_FlashCrashMomentum/        # 各自獨立資料夾
    ... (S07-S15)
    _batch_summaries/
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
  verify_all_live.py               # ★ Master 跨策略驗證（L1-L5）110 項
  verify_l4_v142.py                # L4 深度驗證 67 項
  verify_s1_v22.py                 # S1 模擬上架驗證 26 項
  analyze_l5_v198_variants.py      # L5 v19.8 A/B 分析
  export_to_mc.py                  # 匯出 PowerLanguage 原始碼供 MC 載入
  strategy_comparison.py           # 策略組合分析
docs/
  SETTLEMENT_DAY_DESIGN_CONSTITUTION.md  # ★ 結算日策略設計憲法 v1.1（強制位階）
  settlement_flat_module_20260617.md     # Settlement_Flat 模組詳細設計
  settlement_flat_flow_diagram.svg       # 結算日完整決策流程圖
  settlement_flat_backtest_validation_20260617.md  # 6 隻策略真實回測深度驗證
  strategy_classification_decision_matrix.svg      # ★ 策略分類×Settlement 角色決策矩陣
  entry_exit_sop.md                # 9 層出場架構標準
  position_sizing_and_capacity.md  # 口數配置框架
  L4_v142_pathA_entry_diagnostic.md   # L4 A/B Path A 完整診斷
  L4_v142_pathB_variant_matrix.md     # L4 A/B Path B 變體設計
  L4_v142_variant_results.md          # L4 A/B 七變體實證結果
  L5_v198_pretrail_sp_design.md       # L5 SP 模組設計
  L5_v198_variant_results.md          # L5 A/B 六變體實證結果
  optimization_opportunities_2026Q2.md  # 優化空間清單
  optimization_guide.md            # 優化方法論文件
```

## 三層晉升流程

```
research/  ──[Phase 1-3 通過]──►  live_simulation/  ──[模擬實證]──►  live/
（開發中）                       （MC12 模擬）                      （MC9 實盤）
```

**晉升條件**：
- research → live_simulation：通過 WFE > 50%、MC 95% MDD < 帳戶 30%、OOS PF > 1.0
- live_simulation → live：模擬 ≥ 30 筆交易、模擬 PF ≥ 1.2、回測偏離度 ≤ 30%

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
11. **★ 強制規範**：所有策略必須含 Settlement_Flat 模組（7 元素）
    - 詳見 [docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md](docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
    - Priority 0 出場順序：Kill > Registry > Holiday > **Settlement** > 原邏輯
    - 進場 gate 必含 `v_Settlement_Day = false`
    - 驗證腳本 `scripts/verify_settlement_flat.py` 必須通過
12. **★ 強制規範**：所有策略必須含 P3b Immediate Stop Guard（SetStopLoss）
    - 詳見 [docs/P3b_immediate_stop_guard_design_20260618.md](docs/P3b_immediate_stop_guard_design_20260618.md)
    - `SetStopLoss` 為 MC 引擎層級函數，進場成交瞬間即生效（無 IOG 依賴）
    - 必須在進場區塊之前、指標計算之後呼叫
    - Guard 條件：Long 策略 `if MP <= 0`、Short 策略 `if MP >= 0`（進場後自動凍結）
    - 距離公式必須與該策略的 Frozen SL 使用相同變數和乘數
    - 金額 = 點數距離 × `BigPointValue`（TXF1 = 200）
    - 每隻策略僅限 1 個 `SetStopLoss` 呼叫（不可重複）
    - 新策略開發時，此項與 Settlement_Flat 同為必備結構模組

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
