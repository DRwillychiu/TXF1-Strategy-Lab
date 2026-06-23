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

## 目錄結構（2026-06-22 深度整理）
```
CLAUDE.md                          # 本檔（14 條強制規範）
README.md                          # 專案總覽
.gitignore

strategies/                        # 策略原始碼三層分類
├── live/                          # MC9 實盤（真金白銀）
│   ├── README.md
│   ├── L1_TrendLong.pla / _annotated.md / _review.md
│   ├── L2_TrendShort.pla / _annotated.md / _review.md
│   ├── L3_ConsolidationLong.pla / _annotated.md / _review.md
│   ├── L4_ConsolidationShort.pla / _annotated.md
│   └── L5_BreakoutLong.pla / _annotated.md / _review.md
├── live_simulation/               # MC12 模擬中
│   ├── README.md
│   ├── S1_NightMomentum.pla / _annotated.md
│   └── S3_RapidPullbackShort.pla / _annotated.md   # 2026-06-20 部署
└── research/                      # 研究中（雙軌）
    ├── README.md
    ├── S03_VolSqueeze/            # ★ CURRENT — 原始排程
    ├── 2026-W24/                  # 軌道 B：每週批次（Cowork 自動）
    └── archive/                   # 歷史與 off-roadmap
        ├── batch01_S2-S5/         # 原始排程雛形
        ├── batch02_S6-S10/
        ├── batch03_S11-S15/
        ├── S02_InsideBarBreak_killed_20260622/
        ├── S03_RapidPullbackShort_archived_20260622/
        ├── offRoadmap_2026Q2_killed/    # S4-S9 偏離排程
        └── _temp_offRoadmap_2026Q2/

docs/                              # 機構級文件分類（data-analyst 規範）
├── README.md                      # 文件索引
├── policies/                      # ★ 強制規範（合規層）
│   ├── OFFICIAL_ROADMAP.md        # Rule #14 排程鎖定
│   ├── SETTLEMENT_DAY_DESIGN_CONSTITUTION.md  # Rule #11
│   ├── P3b_immediate_stop_guard_design_20260618.md  # Rule #12
│   ├── institutional_risk_framework_20260619.md  # Rule #13
│   ├── settlement_flat_module_20260617.md
│   ├── settlement_flat_flow_diagram.svg
│   ├── settlement_flat_backtest_validation_20260617.md
│   └── strategy_classification_decision_matrix.svg
├── methodology/                   # 流程 SOP
│   ├── entry_exit_sop.md
│   ├── claude_code_workflow.md
│   ├── cowork_sync_prompt.md
│   └── position_sizing_and_capacity.md
├── research/                      # 主題研究 / theses
│   ├── index_level_thesis.md
│   ├── structural_issues_review_20260618.md
│   └── optimization_opportunities_2026Q2.md
├── strategy_archive/              # 既有策略歷史演進
│   ├── L4_v142_*.md
│   ├── L5_v198_*.md
│   ├── S1_v23_*.md / v24_*.md
│   └── range_force_exit_*.md
└── archive/                       # 歸檔（off-roadmap、舊 handoffs）
    ├── handoffs/
    └── offRoadmap_2026Q2/         # 22 個偏離排程文件

optimization/                      # 原始 ROADMAP 追蹤系統
├── README.md
├── TRACKER.md                     # S1-S15 master 進度表
└── logs/                          # 每隻策略 Phase 1-4 詳細紀錄
    ├── B01_S1_NightMomentum.md   # 🟢 已部署
    ├── B01_S3_VolSqueeze.md      # 🔵 CURRENT
    ├── B01_S4_MACDDivergence.md  # ⏳ next
    └── ... (共 16 個 log)

scripts/                           # 驗證 / 分析腳本
├── README.md
├── verify_all_live.py             # ★ Master 跨策略驗證 110 項
├── verify_l1-l5_immediate_stop.py # Rule #12 驗證
├── verify_settlement_*.py         # Rule #11 驗證
├── verify_s1_v22-v26.py
└── analyze_l5_v198_variants.py

backtest/                          # ⚠️ Python 日線代理（DEPRECATED）
├── README.md
├── run_backtest.py                # ⚠️ DEPRECATED
├── fetch_data.py
├── twii_daily.csv
├── results_batch01.json           # 原始基線證據
├── results_batch02.json
├── optimize/                      # Walk-Forward / Monte Carlo 框架
└── results/s1_optimization/       # S1 視覺化結果
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
13. **★ 強制規範**：所有新策略 / 既有策略優化必須通過機構級 10 維度評估
    - 詳見 [docs/institutional_risk_framework_20260619.md](docs/institutional_risk_framework_20260619.md)
    - 10 維度：Sharpe/Sortino/Calmar、VaR/CVaR、跨策略相關性 < 0.7、
      Drawdown clustering、樣本數 ≥ 100、WFE > 50%、三市況 PF > 1.0、
      成本分析、Operational risk、法規 / 帳戶限制
    - 任一維度 fail → 不可上 live_simulation
    - 即使是 1-line input 改動，也須評估這 10 維度的變化
14. **★ 強制規範**：策略開發必須嚴格按照 OFFICIAL_ROADMAP.md 排程，不可發明新策略名稱
    - 詳見 [docs/policies/OFFICIAL_ROADMAP.md](docs/policies/OFFICIAL_ROADMAP.md)
    - 完整排程（拆解後 21 隻）：
      `S3_L → S3_S → S4_L → S4_S → S5_L → S5_S → S6 → S7 → S8 → S9_L → S9_S`
      `→ S10_L → S10_S → S11 → S12_L → S12_S → S13 → S14_L → S14_S → S15_L → S15_S`
    - **不允許**：發明新策略名稱（RapidPullbackShort / TurnOfMonth / SPX_Overnight 等）
    - **不允許**：跳號（S3_L 完成必直接進 S3_S → S4_L）
    - **不允許**：平行開發（一次只開發一隻）
    - **拆解規則（Rule R-6）**：原始排程雙向策略**必拆**為 `Sx_L` (純多) + `Sx_S` (純空)
    - **順序鐵則**：一律先 L 後 S（TXF1 偏多 regime，Long 驗證較快）
    - 每隻策略必有 W0 Alpha Pre-verify (Python 真實資料) → 才寫 .pla
    - 違反本規則 = 違反用戶 2026-06-22 明確指示
15. **★ 強制規範**：所有 .pla 檔必須 100% ASCII（無中文、無 em dash、無 emoji、無全形標點）
    - MC PowerLanguage 對非 ASCII 字元行為 build-dependent，曾發生 v1.1 因 em dash + 勾號炸 line 0 編譯錯誤
    - 違規 = MC 編譯失敗（通常 line 0 col 0 通用錯誤，極難 debug）
    - 強制驗證腳本：`python scripts/verify_pla_ascii.py --strict`
    - Commit 前**必須跑驗證**通過才能 push
    - 適用範圍：`strategies/live/`、`strategies/live_simulation/`、`strategies/research/`（排除 archive/）
    - 違反本規則 = 違反 memory rule `feedback_mc_english_only` + 用戶 2026-06-22 明確指示

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
