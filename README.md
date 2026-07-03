# TXF1-Strategy-Lab

台灣加權指數期貨（TXF1）量化策略研究與部署庫。

---

## 一、專案規格

| 項目 | 值 |
|------|---|
| **商品** | TXF1（台指期近月連續） |
| **合約乘數** | 1 點 = 200 NTD |
| **平台** | MultiCharts 9.0（live）/ MultiCharts 12（研究 / 模擬） |
| **滑價** | 1,000 NTD round-trip（單邊 500） |
| **固定口數** | 1 口 |
| **回測區間** | 2020/01/01 ~ 今天 |
| **交易時段** | 日盤 08:45-13:45 / 夜盤 15:00-05:00 |

---

## 二、三層策略升級制度

```
research/         ──[W0-W6 通過]──►   live_simulation/   ──[模擬實證]──►   live/
（開發中）                              （MC12 模擬帳戶）                     （MC9 實盤）
S3 VolSqueeze                          S1, S3 RapidPullback                  L1-L5
```

### 升級門檻
- research → live_simulation：WFE > 50%、MC 95% MDD < 帳戶 30%、OOS PF > 1.0、樣本 ≥ 100
- live_simulation → live：模擬 ≥ 30 筆、模擬 PF ≥ 1.2、回測偏離度 ≤ 30%

---

## 三、當前部署狀態

### Live（MC9 實盤上架）
| 策略 | 類別 | 方向 | 主週期 |
|------|------|------|--------|
| **L1 TrendLong** | 趨勢追蹤 | Long | 45M |
| **L2 TrendShort** | 趨勢追蹤 | Short | 60M |
| **L3 ConsolidationLong** | 盤整區間 | Long | 15M |
| **L4 ConsolidationShort** | 盤整反轉 | Short | 15M |
| **L5 BreakoutLong** | 盤整突破 | Long | 15M |

### Live Simulation（MC12 模擬中）
| 策略 | 類別 | 方向 | 主週期 | 部署日 |
|------|------|------|--------|--------|
| **S1 NightMomentum** | 時段型 | Long | 15M | 2026-06-07 |
| **S3 RapidPullbackShort** | 多頭過熱拉回 | Short | 5M | 2026-06-20 |

### Research（開發中）
| 策略 | 類別 | 進度 |
|------|------|------|
| **S3_S VolSqueezeShort** | C 類波動率（空） | v1.9.5 GA 完成 (+513.4K/PF1.574)，待蒙地卡羅/WFA 驗證 |

---

## 四、開發排程（強制鎖定）

詳見 [`docs/policies/OFFICIAL_ROADMAP.md`](docs/policies/OFFICIAL_ROADMAP.md)。

```
S2 InsideBarBreak     ⚰️ KILLED (alpha 已死)
S3_S VolSqueezeShort  🟠 v1.9.5 GA done, pending validation
S4 MACDDivergence     ⏳ S3 後
S5 SettlementWeek     ⏳
S6 FlashCrashMomentum ⏳
S7 BullPullbackLong   ⏳
S8 BearBounceSell     ⏳
S9 VolExplosion       ⏳
S10 AdaptiveBreakout  ⏳
S11-S15               ⏳
S16+                  ⏳ 每週由 Cowork 自動生成（2026-W24 起）
```

**規則**：依 CLAUDE.md Rule #14，不發明新策略名稱、不跳號、不平行開發。

---

## 五、目錄結構

```
TXF1-Strategy-Lab/
├── README.md                       ← 本檔
├── CLAUDE.md                       ← Claude Code 專案指引 (14 條強制規範)
│
├── strategies/                     策略原始碼層
│   ├── live/                       L1-L5 (MC9 實盤)
│   ├── live_simulation/            S1, S3 RapidPullback (MC12 模擬)
│   └── research/                   研究中
│       ├── S03_VolSqueezeShort/     ← 當前開發 (v1.9.5 GA done)
│       ├── 2026-W24/               ← 每週批次 (Cowork 自動更新)
│       └── archive/                 歷史批次
│           ├── batch01_S2-S5/      原始排程基線
│           ├── batch02_S6-S10/
│           ├── batch03_S11-S15/
│           ├── S02_InsideBarBreak_killed_20260622/
│           ├── S03_RapidPullbackShort_archived_20260622/
│           └── offRoadmap_2026Q2_killed/
│
├── docs/                           機構級文件分類
│   ├── policies/                   ★ 強制規範 (Rules, Constitution, Roadmap)
│   ├── methodology/                ★ 流程 SOP
│   ├── research/                   ★ 主題研究 / Theses
│   ├── strategy_archive/           ★ 策略歷史 (L1-L5 / S1 演進)
│   └── archive/                    歸檔（off-roadmap、舊 handoffs）
│
├── backtest/                       Python 日線代理回測 (DEPRECATED, 歷史紀錄)
│   ├── fetch_data.py
│   ├── run_backtest.py             ⚠️ DEPRECATED
│   ├── optimize/                   Walk-Forward / Monte Carlo 框架
│   └── results/
│
├── optimization/                   原始 ROADMAP 追蹤系統
│   ├── TRACKER.md                  ← S1-S15 master 進度表
│   └── logs/                       每隻策略的 Phase 1-4 詳細紀錄
│       ├── B01_S1_NightMomentum.md
│       ├── B01_S3_VolSqueeze.md    ← S3 當前開發必須更新此檔
│       └── ... (16 個 log)
│
└── scripts/                        驗證 / 分析工具腳本 (對應 live 策略)
    ├── verify_all_live.py
    ├── verify_l1_immediate_stop.py
    └── ... (17 個 active 腳本)
```

---

## 六、開發紀律（從 13 條 CLAUDE.md 規則摘要）

1. 所有策略必含 **Settlement_Flat 7 元素**（Rule #11）
2. 所有策略必含 **P3b SetStopLoss**（Rule #12）
3. 所有策略必通過 **機構級 10 維度評估**（Rule #13）
4. 策略開發必照 **OFFICIAL_ROADMAP** 排程（Rule #14）
5. PowerLanguage 程式碼必對齊 Rule #1-#10

---

## 七、相關文件入口

- 開發排程：[`docs/policies/OFFICIAL_ROADMAP.md`](docs/policies/OFFICIAL_ROADMAP.md)
- 結算日憲法：[`docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`](docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- P3b 停損規範：[`docs/policies/P3b_immediate_stop_guard_design_20260618.md`](docs/policies/P3b_immediate_stop_guard_design_20260618.md)
- 機構級 10 維度：[`docs/policies/institutional_risk_framework_20260619.md`](docs/policies/institutional_risk_framework_20260619.md)
- 流程 SOP：[`docs/methodology/entry_exit_sop.md`](docs/methodology/entry_exit_sop.md)
- TRACKER（S1-S15 進度）：[`optimization/TRACKER.md`](optimization/TRACKER.md)
