# 目錄結構

> **五支 live 與 research 的現行版本，見 [`LIVE_VERSIONS.md`](LIVE_VERSIONS.md)。**
> 本檔只畫目錄結構，不記版本號。

> **本檔來源**：2026-08-04 自 `CLAUDE.md` 拆出。CLAUDE.md 觸及 300 行硬上限
> （MAINTENANCE_PROTOCOL §2），此段為純參考資訊、非強制規範，故移出。
> CLAUDE.md 保留一行指標指向本檔。
>
> **內容為原文剪貼，未改寫**（依 MAINTENANCE_PROTOCOL §2「原文剪貼，不改寫」）。
>
> ⚠️ **已知過時處（2026-08-04 發現，尚未修正）**：
>
> 1. 下方樹狀圖將 live 策略列為 `live/L5_BreakoutLong.pla`，但實際路徑為
>    `live/L5_BreakoutLong/L5_BreakoutLong.pla`（各策略有自己的子目錄）。L1~L4 同樣情形。
>    已實查 `strategies/live/` 確認為五個子目錄。
> 2. 樹狀圖第一行 `CLAUDE.md  # 本檔（19 條強制規範）` 的「本檔」是搬移前的語境，
>    在本檔中已不再指向自己。因遵守「原文剪貼不改寫」故照抄。
>
> 上述兩點需一次完整重新審計，屆時一併更新。

## 目錄結構（2026-06-27 審計更新）
```
CLAUDE.md                          # 本檔（19 條強制規範）
README.md                          # 專案總覽
.gitignore

strategies/                        # 策略原始碼三層分類
├── live/                          # MC9 實盤（真金白銀）
│   ├── README.md
│   ├── L1_TrendLong.pla / _annotated.md / _review.md
│   ├── L2_TrendShort.pla / _annotated.md / _review.md
│   ├── L3_ConsolidationLong.pla / _annotated.md / _review.md
│   ├── L4_ConsolidationShort.pla / _annotated.md / _review.md
│   └── L5_BreakoutLong.pla / _annotated.md / _review.md
├── live_simulation/               # MC12 模擬中
│   ├── README.md
│   ├── S1_NightMomentum/          # S1 純多夜盤
│   ├── S3_RapidPullbackShort/     # S3 多頭拉回空
│   ├── S3_VolSqueezeLong/         # S3_L 波動率純多
│   ├── S3_S_VolSqueezeShort/      # S3_S 波動率純空
│   └── S16_S_MACrossShort/        # S16_S 動量交叉空 v1.5
└── research/                      # 研究中（單軌 OFFICIAL_ROADMAP）
    ├── README.md
    ├── L1_TrendLong/              # L1 研究版本
    │   ├── L1_v3.0/                        # V3.0 IOG + StopProfit + FrozenSL
    │   ├── L1_v3.1/                        # V3.1 = 現行 live
    │   └── L1_v3.2/                        # V3.2 二次進場模組 (ratio 0.20 已採用)
    ├── L2_TrendShort/             # L2 研究版本
    │   └── L2_v5.4/                        # v5.4 二次進場標籤 (純標籤, 錨點 24/24)
    ├── L3_ConsolidationLong/      # L3 研究版本
    │   ├── L3_v14.1/
    │   ├── L3_v15.0/                       # v15.0 = 現行 live
    │   └── L3_v15.1/                       # v15.1 二次進場標籤 (純標籤, 錨點 24/24)
    ├── L4_ConsolidationShort/     # L4 研究版本
    │   ├── L4_RESEARCH_SUMMARY.md
    │   ├── L4_v14.7/                       # ** 最新 ** 二次進場標籤 (純標籤)
    │   ├── L4_v15.1/                       # KILLED 2026-07-26
    │   ├── L4_v16.0/                       # KILLED
    │   ├── L4_v17.0/                       # 風險形態掃描錨點基準 (四腿全推翻)
    │   └── L4_v18.0/                       # KILLED 2026-08-24 二次進場零觸發
    ├── L5_BreakoutLong/           # L5 研究版本
    │   ├── L5_v19.8/
    │   └── L5_v19.9_R1/                    # v19.9-R1 二次進場 log (錨點 0 差異)
    ├── S03_VolSqueezeShort/       # S3_S 完整研發史
    ├── S04_MACDDivergenceShort/   # S4 W0 pre-verify (KILLED)
    ├── S16_MACrossLong/           # S16_L (SUSPENDED)
    ├── S16_MACrossShort/          # S16_S 完整研發史 + 10M 延伸
    │   └── S16_MACrossShort_10M/  # 10M 時框實驗 (正面收案)
    ├── S17_SwingShort60M/         # S17 Stage 1
    └── archive/                   # 歷史與 off-roadmap
        ├── README.md
        ├── _batch_summaries/              # Batch02/03 摘要（Batch01 在 batch01_S2-S5/ 內）
        ├── batch01_S2-S5/                 # 原始排程雛形 + powerlanguage/
        ├── batch02_S6-S10/                # S06-S10 各自子資料夾
        │   ├── S06_FlashCrashMomentum/
        │   ├── S07_BullPullbackLong/
        │   ├── S08_BearBounceSell/
        │   ├── S09_VolExplosion/
        │   └── S10_AdaptiveBreakout/
        ├── batch03_S11-S15/               # S11-S15 各自子資料夾
        │   ├── S11_MiddayCompression/
        │   ├── S12_WeekdayMomentum/
        │   ├── S13_VolCollapseShort/
        │   ├── S14_TripleTFTrend/
        │   └── S15_BBReversion/
        ├── S02_InsideBarBreak_killed_20260622/
        ├── S03_RapidPullbackShort_archived_20260622/
        ├── S03_VolSqueezeLong_promoted_20260620/   # S3_L 升等後 W0-W5 歷史
        ├── S3_S_v2_killed_20260626/
        └── offRoadmap_2026Q2_killed/      # S4-S9 偏離排程 KILL

docs/                              # 機構級文件分類（data-analyst 規範）
├── README.md                      # 文件索引
├── handoffs/                      # 當前 session handoffs
├── policies/                      # ★ 強制規範（合規層）
│   ├── OFFICIAL_ROADMAP.md                    # Rule #14 排程鎖定
│   ├── SETTLEMENT_DAY_DESIGN_CONSTITUTION.md  # Rule #11
│   ├── P3b_immediate_stop_guard_design_20260618.md  # Rule #12
│   ├── institutional_risk_framework_20260619.md     # Rule #13
│   ├── STRATEGY_SUCCESS_CRITERIA.md           # 機構級成功標準
│   ├── lesson_L24_risk_overlay_alpha_preservation.md  # Lesson L24
│   ├── settlement_flat_module_20260617.md
│   ├── settlement_flat_flow_diagram.svg
│   ├── settlement_flat_backtest_validation_20260617.md
│   └── strategy_classification_decision_matrix.svg
├── methodology/                   # 流程 SOP
│   ├── entry_exit_sop.md
│   ├── claude_code_workflow.md
│   ├── cowork_sync_prompt.md
│   ├── position_sizing_and_capacity.md
│   └── LOOP_FRAMEWORK.md
├── research/                      # 主題研究 / theses
│   ├── index_level_thesis.md
│   ├── structural_issues_review_20260618.md
│   └── optimization_opportunities_2026Q2.md
├── strategy_archive/              # 既有策略歷史演進
│   ├── L1_v2.6_20260622_gap_miss_case.md
│   ├── L4_v14.2_*.md               # pathA / pathB / variant_results
│   ├── L5_v19.8_*.md / L5_v19.9_*.md
│   ├── S1_v23_*.md / S1_v24_*.md
│   └── range_force_exit_*.md      # deployment + rollback
└── archive/                       # 歸檔（off-roadmap、舊 handoffs）
    ├── handoffs/                   # 過期 handoffs（2026-06-07、06-13）
    └── offRoadmap_2026Q2/         # 24 個偏離排程產物

optimization/                      # 原始 ROADMAP 追蹤系統
├── README.md
├── TRACKER.md                     # S1-S15 master 進度表
└── logs/                          # 每隻策略 Phase 1-4 詳細紀錄
    ├── B01_S1_NightMomentum.md    # 🟢 已部署 live_simulation
    ├── B01_S3_VolSqueeze.md       # 🟡 v1.7.3 regime filter 實驗中
    ├── B01_S4_MACDDivergence.md   # ⏳ next
    ├── B02_S6~S10 / B03_S11~S15  # ⏳ Queue
    └── TEMPLATE_optimization_log.md

scripts/                           # 驗證 / 分析腳本
├── README.md
├── verify_all_live.py             # ★ Master 跨策略驗證 110 項
├── verify_pla_ascii.py            # Rule #15 ASCII 驗證
├── verify_l{1..5}_immediate_stop.py  # Rule #12 驗證
├── verify_settlement_*.py         # Rule #11 驗證
├── verify_s1_v22~v26.py           # S1 各版本驗證
├── analyze_*.py                   # 分析腳本
├── wfa_loop_runner.py             # WFA 自動化
└── results/                       # WFA JSON 輸出

backtest/                          # ⚠️ Python 日線代理（DEPRECATED）
├── README.md
├── run_backtest.py                # ⚠️ DEPRECATED
├── fetch_data.py
├── twii_daily.csv
├── results_batch01.json           # 原始基線證據
├── results_batch02.json
├── optimize/                      # Walk-Forward / Monte Carlo 框架
└── results/                       # S1 視覺化 + portfolio 分析
    ├── s1_optimization/           # Phase 1-3 PNG + JSON
    └── portfolio/                 # 組合分析 JSON
```
