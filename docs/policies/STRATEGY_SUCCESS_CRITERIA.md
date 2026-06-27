# STRATEGY SUCCESS CRITERIA — 集中編碼 Success Gates

**建立日**：2026-06-28
**目的**：把散落各處的 success gates 集中編碼，供 Loop framework 引用
**狀態**：🔒 LOCKED（不可降低標準，可加嚴）
**來源整合**：CLAUDE.md Rule #13 + institutional_risk_framework + Phase 2 spec + live_simulation/README

---

## 一、5 階段 Success Gates 速查

```
Stage -1 (Discussion)  → user GO/NO-GO (人工)
W0 (Alpha Pre-verify)  → 量化最低 alpha threshold
W3 (MC12 Baseline)     → 樣本 + 結構合規
W4 (WFA)               → OOS robustness
W5 (10-dim Institutional) → 全面風險評估
Promote to live_simulation → 模擬轉實盤前最後關
```

---

## 二、各階段 Gates 詳表

### Stage -1：策略設計討論（**不可 Loop**）

| Gate | 標準 | 驗證 |
|------|------|------|
| 4 段討論完整 | 內容 / 優點 / 缺點 / 為什麼合適 | User explicit GO |
| OFFICIAL_ROADMAP 對齊 | 不發明新名稱、不跳號 | Rule #14 |
| 不違反既有 lessons | L1-L24 全 check | docs/policies/ |

**HARD LIMIT**: 無（不是 Loop）

---

### W0：Alpha Pre-verify（Python 真實資料）

| Gate | 標準 | 驗證 |
|------|------|------|
| Trigger 發生頻率 | ≥ 5 instances/year（避免 sample 不足）| Python script |
| 後續 N bar 的方向 hit rate | ≥ 40%（vs 0% baseline）| Python script |
| Risk-reward ratio | ≥ 1.5（TP/SL ratio）| Python script |
| Alpha 跨年穩定 | 至少 50% 年份有正 PnL | Python script |

**FAIL → KILL（不寫 .pla）**
**HARD LIMIT**: 1 iteration（pre-verify 是 binary gate）

---

### W3：MC12 Baseline Backtest

| Gate | 標準 | 驗證 |
|------|------|------|
| 樣本數 | ≥ 100 trades / 6.4 yr | xlsx |
| PF gross | ≥ 1.1 | xlsx |
| Adj PF (含滑價) | ≥ 0.9 | xlsx |
| Sharpe (年化) | ≥ 0.15 | xlsx |
| Max DD | < 25% account | xlsx |
| Operational 5/5 | Settlement + SetStopLoss + Holiday + Kill + IOG | scripts/verify_*.py |
| Rule #15 ASCII | 100% ASCII | scripts/verify_pla_ascii.py |

**HARD LIMIT**: 2 iterations（baseline 不該反覆，過 2 次仍 fail = 設計問題）

---

### W4：Walk-Forward Analysis（**Loop 化首選**）

| Gate | 標準 | 驗證 |
|------|------|------|
| Windows | 9 (IS 2y / OOS 6m / step 6m) | xlsx 數量 |
| **≥ 5/9 windows pass 3 gates** | per window: WFE>50% AND OOS PF>1.0 AND OOS Sharpe>0 | 對 9 windows 統計 |
| Median WFE | > 50% | 計算 |
| Mean OOS PF | > 1.0 | 計算 |
| Total OOS Net | > 0 | 計算 |
| Mean OOS MDD | > -30% | 計算 |

**HARD LIMIT**: **5 iterations**（每輪 = 1 個 input 改 + 18 個 backtest）
**Per-iteration constraint**: 只改 1 個 input（防 over-fit）

---

### W5：10-dim Institutional Eval（Rule #13）

| # | Gate | 標準 |
|---|------|------|
| 1 | Sharpe / Sortino / Calmar | ≥ 0.15 |
| 2 | Max DD | < 25% account |
| 3 | 跨策略相關性 | < 0.7 vs 既有 7 sleeves |
| 4 | DD Clustering | < 3σ OR event-level Max/Mean < 1.5x |
| 5 | Sample | ≥ 100 trades |
| 6 | WFE | > 50%（W4 已驗）|
| 7 | Three-regime PF | bull/bear/range 各別 > 1.0 |
| 8 | Cost (adj PF) | > 1.3 |
| 9 | Operational risk | 5/5（Settlement/SetStopLoss/Holiday/Kill/IOG）|
| 10 | Regulatory | TXF1 1 contract / no leverage |

**HARD LIMIT**: **3 iterations**（fix → re-eval → final decide）
**FAIL → KILL or Accept with caveats (user ruling)**

---

### Promote to live_simulation/

| Gate | 標準 | 驗證 |
|------|------|------|
| W4 PASS | ≥ 5/9 OOS pass | W4 report |
| W5 PASS | 10/10 dimensions | W5 report |
| .pla ASCII | 100% | verify_pla_ascii.py |
| Deployment manifest | DEPLOYMENT.md 含 caveats / kill triggers | docs review |
| README / annotated.md | 完整 | docs review |
| OFFICIAL_ROADMAP update | promotion 標記 | OFFICIAL_ROADMAP.md |

**Manual**: User explicit ruling（不可 Loop）

---

## 三、HARD LIMITS 速查

| Loop 類型 | 上限 | 一次迭代 = |
|----------|-----|----------|
| W0 alpha pre-verify | **1** | 1 Python script run |
| W3 baseline backtest | **2** | 1 MC12 backtest + analysis |
| Bug fix (.pla) | **3** | 1 fix + 1 verify backtest |
| Phase 2 GA | **2 rounds** | 1 broad + 1 refined |
| **W4 WFA** | **5** | 1 input change + 18 backtests |
| W5 institutional eval | **3** | 1 dim fix + re-evaluate |

→ 超過上限 → 寫 `FINAL_VERDICT.md` per `feedback_strategy_kill_must_document`

---

## 四、FAIL 後動作 SOP

```
1. Loop ABORT (達 HARD LIMIT)
2. Reviewer (Opus) 寫 root cause analysis
3. 3 條路（user pick）:
   A. KILL → 寫 FINAL_VERDICT.md → archive 策略 → 進下一個
   B. Accept with caveats → portfolio cap + monitor
   C. Re-design (Stage -1) → 重新 4 段討論
4. 若 KILL → codify new lesson (L25+)
5. Update OFFICIAL_ROADMAP
```

---

## 五、跟既有 SOP 整合

| 既有 SOP | 跟 Success Criteria 關係 |
|---------|----------------------|
| `CLAUDE.md` Rule #13 | W5 10-dim 來源 |
| `institutional_risk_framework_20260619.md` | W5 詳細 spec |
| `STRATEGY_RD_SOP_v2.md` | W0-W6 phase 流程 |
| `lesson_L24_*.md` | FAIL 時不可加 event filter |
| `OFFICIAL_ROADMAP.md` | 順序 + 命名規範 |
| `LOOP_FRAMEWORK.md` | 引用本檔 gates 為 SUCCESS CRITERIA |
| `feedback_strategy_kill_must_document.md` | FAIL 必出 FINAL_VERDICT |

---

## 六、修訂歷史

| 日期 | 修訂 |
|------|------|
| 2026-06-28 | 初版（從 散落 SOP 整合）|

---

## 七、引用方式（在 Loop Spec 中）

```
LOOP SPEC: [策略] WFA Validation
SUCCESS CRITERIA: 引用 docs/policies/STRATEGY_SUCCESS_CRITERIA.md W4 section
HARD LIMIT: 5 iterations (per STRATEGY_SUCCESS_CRITERIA.md)
```

不再重抄 criteria，**集中於本檔**。
