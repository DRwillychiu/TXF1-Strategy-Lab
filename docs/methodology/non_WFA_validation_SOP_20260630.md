# Non-WFA 驗證 5 件套 SOP（**所有未來策略強制執行**）

**建立日期**：2026-06-30
**驅動 ruling**：user 2026-06-30：「在接下來的所有策略除了 WFA 之外，全部都要跑 Monte Carlo + Bootstrap + Stress Testing + Regime Analysis + Robustness Testing」
**規範 level**：CLAUDE.md Rule #18（強制）
**例外**：Paper Trading 不列入（本來就會在 live_simulation 期間執行）

---

## 一、5 件套執行 Order（**從快到慢**）

| # | 驗證方法 | 工具 | 時間 | 優先級 |
|---|---------|------|------|--------|
| 1 | **Monte Carlo Simulation** | Python | 10-15 min | ⭐⭐⭐⭐⭐ |
| 2 | **Bootstrap Resampling** | Python | 5-10 min | ⭐⭐⭐⭐⭐ |
| 3 | **Stress Testing** | Python + MC12 | 15-30 min | ⭐⭐⭐⭐ |
| 4 | **Regime Analysis** | Python | 10-15 min | ⭐⭐⭐⭐ |
| 5 | **Robustness Testing** | MC12 ±10% | 30-60 min | ⭐⭐⭐⭐ |

→ **總時間 ~70-130 分鐘**（vs WFA 1 個策略 1-15 hr，更 efficient）

---

## 二、每件套詳細 SOP

### 1️⃣ Monte Carlo Simulation（**最 robust**）

**目的**：用 trade list 重新洗牌 10,000 次，算 worst-case scenario 機率

**邏輯**：
```python
import random
trades = [...]  # original PnL list
N_SIMS = 10000

mdds, finals, ruins = [], [], []
for _ in range(N_SIMS):
    shuffled = random.sample(trades, len(trades))
    equity = [INITIAL_CAPITAL]
    for pnl in shuffled:
        equity.append(equity[-1] + pnl)
    
    peak = INITIAL_CAPITAL
    mdd = 0
    for e in equity:
        if e > peak: peak = e
        mdd = min(mdd, e - peak)
    
    mdds.append(mdd)
    finals.append(equity[-1])
    ruins.append(min(equity) < INITIAL_CAPITAL * 0.5)

# 95% confidence
mdd_p95 = sorted(mdds)[int(N_SIMS * 0.05)]
ruin_pct = sum(ruins) / N_SIMS * 100
```

**Pass criteria**：
- 95% confidence MDD < 帳戶 30%
- 破產機率 < 1%
- Final equity 5%-95% 區間都 > initial

**Output**：`MC_simulation_<strategy>_<date>.json` + equity curve PNG

---

### 2️⃣ Bootstrap Resampling（**統計顯著性**）

**目的**：用 trade list with replacement 抽樣，算 confidence intervals

**邏輯**：
```python
import random
N_BOOTSTRAPS = 10000

pf_list, sharpe_list, net_list = [], [], []
for _ in range(N_BOOTSTRAPS):
    sample = random.choices(trades, k=len(trades))
    # compute PF, Sharpe, Net for each resample
    ...
    pf_list.append(pf)
    sharpe_list.append(sharpe)
    net_list.append(net)

# 95% CI
pf_ci = (sorted(pf_list)[250], sorted(pf_list)[9750])
sharpe_ci = (sorted(sharpe_list)[250], sorted(sharpe_list)[9750])
```

**Pass criteria**：
- PF 95% CI 下界 > 1.0
- Sharpe 95% CI 下界 > 0
- Net 95% CI 下界 > 0

**Output**：`bootstrap_<strategy>_<date>.json` + histogram PNG

---

### 3️⃣ Stress Testing（**極端情境**）

**目的**：用歷史最壞 events 重壓 strategy

**Standard 6 個 stress scenarios**：
| Event | 期間 | 重壓 |
|-------|------|------|
| 1987 Black Monday | 1987-10-19 | 單日 -22.6% |
| 2008 雷曼 | 2008-09-15 起 | 月度 -30% |
| 2010 Flash Crash | 2010-05-06 | 分鐘級 -9% |
| 2015 中國股災 | 2015-06 起 | 季度 -40% |
| 2020 COVID | 2020-02-19 起 | 月度 -34% |
| 2024-08-05 BoJ | 2024-08-05 | 單日 -12% |

**對 TXF1 specific**：
- 加 2026-04-02 Trump 關稅（已有 data）
- 加 2025-04-09 Trump 主跌

**做法**：
- 把這些期間數據 isolate 跑 backtest
- 看 max single trade loss
- 看 cluster losses
- 看 1M_Exit / SP / SL 表現

**Pass criteria**：
- 任何 stress event 單筆 loss < 帳戶 5%
- 任何 stress event cluster loss < 帳戶 15%
- 策略 survival (不爆倉)

**Output**：`stress_test_<strategy>_<date>.md` + per-event trade detail

---

### 4️⃣ Regime Analysis（**三市況**）

**目的**：bull/bear/range 三 regime 分別 evaluate PF

**Regime classifier**：
- 用 Daily MA20/MA50 ratio
  - Bull: ratio > 1.05
  - Range: 0.98 ≤ ratio ≤ 1.05
  - Bear: ratio < 0.98
- 或 vol regime: ATR_short / ATR_long
- 或 trend regime: ADX(14) > 25

**做法**：
```python
for trade in trades:
    regime = classify_regime(trade['entry_date'])
    regime_groups[regime].append(trade)

for regime, ts in regime_groups.items():
    pf, sharpe, net = compute_metrics(ts)
    print(f'{regime}: PF={pf} Sharpe={sharpe} Net={net}')
```

**Pass criteria**：
- 三 regime 至少 2 個 PF > 1.0
- 主要 alpha regime PF > 2.0
- 沒有 regime 完全災難（Net 損失 > 帳戶 10%）

**Output**：`regime_analysis_<strategy>_<date>.md`

---

### 5️⃣ Robustness Testing（**參數敏感度**）

**目的**：核心 inputs ±10% / ±20% 看 PF 是否穩定（plateau test）

**做法**：
- 鎖其他 inputs，逐 input 改 ±10%, ±20%
- 跑 MC12 backtest
- 看 PF / Net / MDD 變化幅度

**Pass criteria**：
- 核心 input ±10% → PF 變化 < 20%
- 核心 input ±20% → PF 變化 < 40%
- PF 不應對單一 input 「尖峰敏感」

**Output**：sensitivity 3D surface PNG + `robustness_<strategy>_<date>.md`

---

## 三、Combined Pass/Fail Verdict

| 5 件套 | PASS | MARGINAL | FAIL |
|--------|------|----------|------|
| **5/5 PASS** | ✅ promote-eligible | - | - |
| **4/5 PASS** | - | ⭐ 接受 with caveats | - |
| **3/5 PASS** | - | ⚠️ user ruling | - |
| **≤ 2/5 PASS** | - | - | ❌ archive |

---

## 四、與 WFA 的整合

| 流程 | 順序 |
|------|------|
| W0 Alpha Pre-verify | 必先做 |
| W1 Strategy doc | 必先做 |
| W2 .pla 實作 | 必先做 |
| W3 Baseline backtest | 必先做 |
| W4 WFA | 對 low-freq strategy 可考慮 long-window WFA |
| **W4.5 Non-WFA 5 件套** ⭐ NEW | **本 SOP，強制執行** |
| W5 Institutional 10-dim eval | 必先做 |
| W6 Promote | user ruling |

---

## 五、模板腳本（**重用 across 策略**）

### 位置
```
scripts/
├── monte_carlo_simulation.py
├── bootstrap_resampling.py
├── stress_testing.py
├── regime_analysis.py
└── robustness_testing.py
```

### 使用
```bash
# 對 S3_S v1.8.0 跑 5 件套
python scripts/monte_carlo_simulation.py --strategy S3_S --trades v180_trades.json
python scripts/bootstrap_resampling.py --strategy S3_S --trades v180_trades.json
python scripts/stress_testing.py --strategy S3_S --pla v180_EXPERIMENTAL.pla
python scripts/regime_analysis.py --strategy S3_S --trades v180_trades.json
# Robustness 需 MC12 跑, 結果 export 後 Python analyze
```

---

## 六、規範範圍

### 強制執行
- 所有 future strategies（S4_S 以後）promote 前必跑 5 件套
- 已 promote strategies 在 quarterly review 時跑 5 件套
- 任何 .pla 重大改動（>10% 邏輯變動）必跑 5 件套

### 不強制
- Hot fix（單行 bug fix）
- 文件改動
- Cosmetic changes

---

## 七、Engineering System Checklist（Rule #16）

| Pillar | 狀態 |
|--------|------|
| Rules | Rule #18 強制 5 件套 |
| Context | 對 WFA 不適合 low-freq strategy 提供替代 |
| Verification | 每件套有明確 pass/fail criteria |
| Memory | 加入 docs/methodology/ 永久查閱 |
| Format | SOP 七節結構 + 模板腳本路徑 |

---

## 八、修訂歷史

| 日期 | 修訂 |
|------|------|
| 2026-06-30 | 初版（user 2026-06-30 ruling）|

---

## 九、相關文件

- `docs/policies/STRATEGY_SUCCESS_CRITERIA.md`（W0-W6 gates）
- `docs/policies/institutional_risk_framework_20260619.md`（10-dim）
- `docs/methodology/extreme_sl_multilayer_sop_20260629.md`（Rule #17 多層 SL）
- `docs/methodology/BOSS_VIEW_TEMPLATE.md`（老闆 view 規範）
- 未來：`scripts/monte_carlo_simulation.py` 等 5 個模板腳本
