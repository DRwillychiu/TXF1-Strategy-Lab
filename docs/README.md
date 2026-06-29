# docs/ — 機構級文件分類索引

> 比照機構量化研究團隊的 data analyst 文件管理規範分類。
> 每個子資料夾代表不同的 governance 層級與用途。

---

## 一、五大資料夾

| 資料夾 | 用途 | 變更頻率 | 引用對象 |
|--------|------|---------|---------|
| **`policies/`** | 強制規範、憲法、排程鎖定 | 罕（重大決策後） | CLAUDE.md / 所有新策略 |
| **`methodology/`** | 流程 SOP、工作方法論 | 偶（流程改進後） | 每次策略開發 |
| **`research/`** | 主題研究、theses、機會分析 | 中（新發現後） | 策略設計階段 |
| **`strategy_archive/`** | 已部署策略的歷史演進、決策紀錄 | 偶（版本升級後） | 既有策略維護 |
| **`archive/`** | 失效 / off-roadmap / 舊 handoffs | 罕（清理時） | 歷史追溯 |

---

## 二、`policies/` — 強制規範（合規層）

| 文件 | 對應規則 | 強制等級 |
|------|---------|---------|
| [`OFFICIAL_ROADMAP.md`](policies/OFFICIAL_ROADMAP.md) | Rule #14 排程鎖定 | 🔒 LOCKED |
| [`SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`](policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) | Rule #11 結算日 7 元素 | 🔒 LOCKED |
| [`P3b_immediate_stop_guard_design_20260618.md`](policies/P3b_immediate_stop_guard_design_20260618.md) | Rule #12 SetStopLoss | 🔒 LOCKED |
| [`institutional_risk_framework_20260619.md`](policies/institutional_risk_framework_20260619.md) | Rule #13 10 維度評估 | 🔒 LOCKED |
| [`settlement_flat_module_20260617.md`](policies/settlement_flat_module_20260617.md) | Settlement_Flat 模組詳細設計 | 參考 |
| [`settlement_flat_flow_diagram.svg`](policies/settlement_flat_flow_diagram.svg) | 結算日決策流程圖 | 參考 |
| [`settlement_flat_backtest_validation_20260617.md`](policies/settlement_flat_backtest_validation_20260617.md) | 6 隻策略結算回測驗證 | 證據 |
| [`strategy_classification_decision_matrix.svg`](policies/strategy_classification_decision_matrix.svg) | 策略分類 × Settlement 角色矩陣 | 參考 |
| [`STRATEGY_SUCCESS_CRITERIA.md`](policies/STRATEGY_SUCCESS_CRITERIA.md) | 機構級策略成功標準 | 參考 |
| [`lesson_L24_risk_overlay_alpha_preservation.md`](policies/lesson_L24_risk_overlay_alpha_preservation.md) | Lesson L24: Risk overlay 不可削 alpha source | 參考 |

---

## 三、`methodology/` — 流程方法論

| 文件 | 內容 |
|------|------|
| [`entry_exit_sop.md`](methodology/entry_exit_sop.md) | 9 層出場架構標準（Priority 0-8 完整鏈） |
| [`claude_code_workflow.md`](methodology/claude_code_workflow.md) | Claude Code 與此 repo 的協作流程 |
| [`cowork_sync_prompt.md`](methodology/cowork_sync_prompt.md) | Cowork ↔ Claude Code 同步規範 |
| [`position_sizing_and_capacity.md`](methodology/position_sizing_and_capacity.md) | 口數配置 + 胃納量框架 |
| [`LOOP_FRAMEWORK.md`](methodology/LOOP_FRAMEWORK.md) | Loop 開發迭代框架 |
| [`ENGINEERING_SYSTEM.md`](methodology/ENGINEERING_SYSTEM.md) | **五支柱工程規範**（Rule #16，2026-06-29 建立） |

---

## 四、`research/` — 主題研究 / Theses

| 文件 | 主題 |
|------|------|
| [`index_level_thesis.md`](research/index_level_thesis.md) | 指數位階論基礎 thesis |
| [`structural_issues_review_20260618.md`](research/structural_issues_review_20260618.md) | 跨策略 5 個結構性議題審查（A-E） |
| [`optimization_opportunities_2026Q2.md`](research/optimization_opportunities_2026Q2.md) | 2026 Q2 全策略優化機會清單 |

---

## 五、`strategy_archive/` — 既有策略歷史演進

每隻 live / live_simulation 策略的版本演化紀錄、A/B 測試結果、決策路徑。

### L 系列（live）
| 文件 | 對應策略 / 版本 |
|------|---------------|
| `L1_v26_20260622_gap_miss_case.md` | L1 v2.6 Gap miss 案例分析 |
| `L4_v142_pathA_entry_diagnostic.md` | L4 v14.2 Path A 進場品質診斷 |
| `L4_v142_pathB_variant_matrix.md` | L4 v14.2 Path B 變體矩陣 |
| `L4_v142_variant_results.md` | L4 v14.2 A-G 七變體實證結果 |
| `L5_v198_pretrail_sp_design.md` | L5 v19.8 SP 模組設計 |
| `L5_v198_variant_results.md` | L5 v19.8 A/B 六變體實證 |
| `L5_v199_1contract_removed_code.md` | L5 v19.9 移除多口邏輯碼 |
| `range_force_exit_deployment_20260617.md` | L3/L4 RangeForceExit 部署紀錄 |
| `range_force_exit_rollback_20260617.md` | L3/L4 RangeForceExit 回滾原因 |

### S 系列（live_simulation）
| 文件 | 對應策略 / 版本 |
|------|---------------|
| `S1_v23_daily_flat_redesign.md` | S1 v2.3 日盤平倉重設計 |
| `S1_v24_overnight_gap_revelation.md` | S1 v2.4 隔夜 gap 啟發 |

---

## 六、`archive/` — 歸檔（off-roadmap、舊 handoffs）

| 子資料夾 | 內容 |
|---------|------|
| [`archive/handoffs/`](archive/handoffs/) | 過時 session handoffs（2026-06-07、2026-06-13） |
| [`archive/offRoadmap_2026Q2/`](archive/offRoadmap_2026Q2/) | 2026-06-19/20/21 偏離排程產物（L4 退役、portfolio v2/v3、STRATEGY_RD_SOP、saturation acceptance 等 22 個檔案） |

---

## 七、文件變更紀律

### 新增 policies/ 文件
- 必須有強制等級標註
- 必須在 CLAUDE.md 對應更新 Rule
- 必須在所有現存策略檢查相容性

### 新增 methodology/ 文件
- 必須有適用範圍說明
- 必須有「成功 / 失敗」案例

### 新增 research/ 文件
- 必須有資料來源與 reproducibility
- 必須在結論段明確標註 actionable / for-record-only

### 新增 strategy_archive/ 文件
- 命名格式：`<策略代號>_<版本>_<主題>_<日期>.md`
- 必須引用對應 .pla 行號

### 歸檔到 archive/
- 必須在原資料夾留 ARCHIVE_NOTE.md 或 redirect
- 必須在本 README 移除索引
