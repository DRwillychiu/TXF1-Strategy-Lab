# strategies/research/ — 研究中策略（雙軌系統）

> **2026-06-22 更新**：研究分為**兩條獨立軌道**並行。

---

## 一、雙軌系統概覽

```
                  ┌─────────────────────────────┐
                  │   research/ (此資料夾)      │
                  └──────────┬──────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                  │
            ▼                                  ▼
  軌道 A：原始 ROADMAP                軌道 B：每週新批次
  S1-S15 (batch01-03)                 S16+ (ISO 週號分組)
  ──────────────────────              ─────────────────────────
  - 依 OFFICIAL_ROADMAP 順序執行       - Cowork 每週日自動生成 5 隻
  - 一次一隻 (S3 → S4 → S5...)        - 按 ISO 週號歸檔 (2026-Www/)
  - 嚴守 CLAUDE.md Rule #14            - S16-S20 開始連續編號
  - **當前資料夾**：                    - **當前資料夾**：
    S03_VolSqueeze/                     2026-W24/ (S16-S20 待加入)
```

兩條軌道**互不衝突**：軌道 A 是已知排程的深度執行，軌道 B 是新概念探索。

---

## 二、軌道 A：原始 ROADMAP（S1-S15）

依 [`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md) 強制排程：

| 編號 | 策略 | 狀態 | 位置 |
|------|------|------|------|
| S1 | NightMomentum | 🟢 live_sim 已部署 | [`../live_simulation/S1_NightMomentum.pla`](../live_simulation/S1_NightMomentum.pla) |
| S2 | InsideBarBreak | ⛔ KILLED 2026-06-22 | [`archive/S02_InsideBarBreak_killed_20260622/`](archive/S02_InsideBarBreak_killed_20260622/) |
| **S3** | **VolSqueeze** | 🔵 **CURRENT** | [`S03_VolSqueeze/`](S03_VolSqueeze/) |
| S4 | MACDDivergence | ⏳ Queue | (S3 完成後建立) |
| S5 | SettlementWeek | ⏳ Queue | — |
| S6-S10 | batch02 | ⏳ Queue | — |
| S11-S15 | batch03 | ⏳ Queue | — |

每隻策略完整週期見 [`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md) §三 W0-W6 流程。

---

## 三、軌道 B：每週新批次（S16+，ISO 週號分組）

### 編號規則
- 從 **S16** 開始連續編號
- 不回收已用編號

### 資料夾結構
```
2026-Www/                       (Www = ISO 週號，如 W24)
├── README.md                    本週 5 組策略狀態摘要
├── Sxx_StrategyName/            (xx = S16+)
│   ├── Sxx_StrategyName.pla
│   ├── Sxx_StrategyName_strategy.md
│   └── Sxx_StrategyName_annotated.md
└── ... (共 5 組)
```

### ISO 週號對照
| 週號 | 日期 | 預定編號 |
|------|------|---------|
| 2026-W24 | 6/8-6/14 | S16-S20 |
| 2026-W25 | 6/15-6/21 | S21-S25 |
| 2026-W26 | 6/22-6/28 | S26-S30（本週） |
| 2026-W27 | 6/29-7/5 | S31-S35 |

### Cowork 自動化
每週日中午由 Cowork session 自動生成本週 5 隻策略並推上 git。詳見 [`../../docs/methodology/cowork_sync_prompt.md`](../../docs/methodology/cowork_sync_prompt.md)。

---

## 四、共同開發流程（軌道 A + B 都適用）

### W0 — Alpha Pre-verify（必做）
- Python 真實資料測 alpha 是否存在
- W0 fail → 立即 KILL，寫 FINAL_VERDICT.md

### W1 — 策略文件
- `Sxx_Name_strategy.md`（機構級規格）
- `Sxx_Name_annotated.md`（中文逐段註解）

### W2 — .pla 實作
- 必含 Rule #11 Settlement_Flat 7 元素
- 必含 Rule #12 P3b SetStopLoss
- 必含 HolidayFlat_v3 / IOG=false / Manual_Kill_Switch / Registry_Valid_Until

### W3 — MC12 baseline backtest
- 60M / 30M / 15M 等對應週期
- 用 design_spec 中位值，**不開 GA**

### W4 — Walk-Forward
- IS 2020-2024 / OOS 2025-2026
- WFE > 50%

### W5 — 10 維度評估（Rule #13）
- Sharpe / Sortino / Calmar / VaR / CVaR / 相關性 / DD clustering / 樣本 / WFE / 三市況 PF / 成本 / Operational risk / 法規

### W6 — 晉升 live_simulation OR KILL with FINAL_VERDICT.md

---

## 五、品質門檻

| 指標 | 門檻 | 來源 |
|------|------|------|
| Walk-Forward Efficiency | > 50% | CLAUDE.md |
| Monte Carlo 95% MDD | < 帳戶 30% | CLAUDE.md |
| 參數高原寬度 | > 範圍 20% | CLAUDE.md |
| OOS Profit Factor | > 1.0 | CLAUDE.md |
| 每月最少交易 | ≥ 2 筆 | CLAUDE.md |
| 樣本數（≥ 6.5 年） | ≥ 100 筆 | Rule #13 |
| 跨策略相關性 | < 0.7 | Rule #13 |
| 三市況 PF | > 1.0 各別 | Rule #13 |

---

## 六、晉升路徑

```
research/                          live_simulation/                  live/
   │                                       │                            │
   ├─[W0 Pre-verify 通過]──────►          ├─[模擬 ≥30 筆,]──►          │
   ├─[W1-W5 完成]                          │  [模擬 PF ≥ 1.2,]            │
   └─[W6 通過 Rule #13 10 維]             │  [假日鐵律 0 違規]           │
                                          └─────────────────────────►   實盤
```

---

## 七、archive/ 歷史檔案結構

| 子資料夾 | 內容 |
|---------|------|
| [`archive/batch01_S2-S5/`](archive/batch01_S2-S5/) | 原始排程 S2-S5 的雛形 .pla |
| [`archive/batch02_S6-S10/`](archive/batch02_S6-S10/) | 原始排程 S6-S10 的雛形 .pla |
| [`archive/batch03_S11-S15/`](archive/batch03_S11-S15/) | 原始排程 S11-S15 的雛形 .pla |
| [`archive/S02_InsideBarBreak_killed_20260622/`](archive/S02_InsideBarBreak_killed_20260622/) | S2 開發到 v0.6 後 KILLED |
| [`archive/S03_RapidPullbackShort_archived_20260622/`](archive/S03_RapidPullbackShort_archived_20260622/) | S3 off-roadmap 命名（生產版已部署 live_sim） |
| [`archive/offRoadmap_2026Q2_killed/`](archive/offRoadmap_2026Q2_killed/) | 2026-06-19~21 偏離排程的 6 隻策略全部 KILLED |
| [`archive/_temp_offRoadmap_2026Q2/`](archive/_temp_offRoadmap_2026Q2/) | 35 個 off-roadmap 研究殘留 |

---

## 八、相關文件

- 開發排程：[`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md)
- 規範清單：[`CLAUDE.md`](../../CLAUDE.md)
- 進度追蹤：[`optimization/TRACKER.md`](../../optimization/TRACKER.md)
- Cowork 同步：[`docs/methodology/cowork_sync_prompt.md`](../../docs/methodology/cowork_sync_prompt.md)
