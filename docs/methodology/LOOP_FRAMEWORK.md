# LOOP FRAMEWORK — Prompt-to-Loop 完整轉換手冊

> **適用範圍**：TXF1-Strategy-Lab 所有策略開發 / 優化 / WFA 驗證 / 文件產出任務
> **整合日期**：2026-06-28
> **位置**：`docs/methodology/LOOP_FRAMEWORK.md`（專案級 SOP）

---

## 0. 核心原則

- **Prompt** = 單次指令，人驅動，人停它停
- **Loop** = 目標 + 完成標準 + 放棄規則，AI 自己跑完整個循環
- **先手動跑通一次 → 固化成 Skill → 套上 Loop → 最後才自動化**
- 跳過前面直接自動化 = Loop 在你睡覺時爆炸

---

## 1. Loop 適用性檢查（四條全滿足才做）

| # | 條件 | 不滿足時的替代方案 |
|---|------|--------------------|
| 1 | 任務至少每週重複一次 | 用單次高品質 prompt |
| 2 | 壞結果可以被自動拒絕（測試失敗、lint 報錯、數值不達標等硬性判定）| 人工審核，不套 loop |
| 3 | Agent 能從頭到尾完成，不需要中途大量丟回給人 | 拆成更小的子任務再評估 |
| 4 |「完成」必須客觀可判定，不是靠審美 | 設計 rubric 評分，但降低自動化期望 |

---

## 2. TXF1-Strategy-Lab 適用任務矩陣

| 任務類型 | Loop 適用? | 推薦模板 | 備註 |
|---------|-----------|---------|------|
| **策略 WFA 驗證**（9 windows IS/OOS）| ✅ 完美適用 | 模板 D | 已有 institutional gates (≥5/9, WFE>50%) |
| **Phase 2 GA 參數優化** | ✅ 適用 | 模板 D 變體 | GA 內建迭代，但 over-fit 檢測需 Loop 包裝 |
| **.pla bug fix 循環**（v1.2→v1.3 那種）| ✅ 適用 | 模板 A | A/B test 結果可硬判定 |
| **W5 10-dim institutional eval** | ✅ 適用 | 模板 D | 10 維度全 pass 為硬標準 |
| **Strategy KILL 決策** | ❌ 不適用 | — | 需 user explicit ruling |
| **Stage -1 策略設計討論** | ❌ 不適用 | — | 創意 + judgement, 不可 loop |
| **Lesson codify** | ❌ 不適用 | — | 一次性 documentation |

---

## 3. Prompt → Loop 轉換流程（六步）

### Step 1：從原始 Prompt 提取三要素
- **GOAL**：你到底要什麼產物？
- **SUCCESS CRITERIA**：怎樣算完成？（必須可測量）
- **ABORT RULE**：什麼情況下放棄？

### Step 2：設計五步循環結構
```
DISCOVER  → 讀取現有狀態
PLAN      → 決定這一輪只做什麼（一次只修一件）
EXECUTE   → 執行修改
VERIFY    → 對照每條 SUCCESS CRITERIA
ITERATE   → 沒達標 → 記錄 → 回 DISCOVER
```

### Step 3：設計 Verify 機制
| 驗證類型 | TXF1 適用場景 |
|----------|--------------|
| **硬測試** | `python scripts/verify_pla_ascii.py` / `scripts/verify_all_live.py` |
| **可測量條件** | WFA windows pass count, PF, Sharpe, MDD 數值門檻 |
| **Rubric 評分** | Annotated.md 完整度、Strategy review.md 深度 |
| **比對基準** | v1.2 vs v1.6 WFA 結果 diff |

**關鍵原則：做事的 agent 和檢查的 agent 分開**
- Writer：Sonnet/Haiku 快速產出
- Reviewer：Opus 嚴格驗證

### Step 4：設計 State 記錄
存於 `loop_state_<task>.md` in 對應 strategy folder

### Step 5：設計 Stop Condition
- **SUCCESS EXIT**：所有 SUCCESS CRITERIA 通過
- **HARD LIMIT EXIT**：達迭代上限（TXF1 推薦 5-8）

### Step 6：組裝成完整 Loop Spec

---

## 4. TXF1-Strategy-Lab 標準 Loop 模板

### 模板 D-1：策略 Walk-Forward 驗證 Loop（**最常用**）

```
LOOP SPEC: [S3_S / S4_L / Sx] Walk-Forward Validation

GOAL:
對 [策略] 執行 9 windows WFA，確認 OOS 表現穩定可 promote 到 live_simulation。

SUCCESS CRITERIA:
- [ ] IS 2y / OOS 6m / step 6m = 9 windows
- [ ] ≥ 5/9 windows 3 gates 全 pass (WFE>50% AND OOS PF>1.0 AND OOS Sharpe>0)
- [ ] Median WFE > 50%
- [ ] Mean OOS PF > 1.0
- [ ] Mean OOS MDD < -30%
- [ ] Total OOS Net > 0

VERIFY METHOD:
可測量條件 — 每輪跑：
  1. python scripts/_temp_analyze_s3s_wfa_w4.py (或對應策略 script)
  2. 讀取每個 window 的 IS/OOS metrics
  3. 計算 WFE，逐 gate 檢查
  4. 統計 pass/fail 比率

EACH ITERATION:
1. DISCOVER: 讀取上輪 state log，看哪些 windows fail
2. PLAN: 選擇一個 input 調整（基於 fail pattern）
3. EXECUTE: 改 .pla input default，commit
4. USER ACTION: 跑 MC12 18 次 backtest，傳 xlsx
5. VERIFY: Claude 跑 analysis script，輸出對照表
6. UPDATE STATE: 寫入 loop_state.md
7. DECIDE: 達標 → SUCCESS / 未達 → 迭代 / 上限 → ABORT

STOP CONDITIONS:
- SUCCESS: 5/9 + WFE > 50% + OOS gates pass
- HARD LIMIT: 5 iterations (每輪 = 1 個 input 改 + 18 次 backtest)

ON STOP:
- 總結所有改動
- 若 ABORT: 寫 FINAL_VERDICT.md (per 用戶 規範)，進 next strategy

CONSTRAINTS:
- 一次只改一個 input（防 over-fit）
- 不可逆向 fit IS 為了通過 OOS
- 不可加 strategy-level event filter (per Lesson L24)
- 不可發明新策略名稱 (per Rule #14)
```

### 模板 A-1：.pla bug fix Loop（v1.2→v1.3 那種）

```
LOOP SPEC: [策略] [bug 描述] BugFix Loop

GOAL:
修正 [bug 現象]，A/B test 證實 bug 已解。

SUCCESS CRITERIA:
- [ ] A/B 兩 config 結果不再 identical（如 Cooldown bug）
- [ ] 目標 case 被正確處理（e.g., 2025-04-07 SL 被擋）
- [ ] 整體 Net 不降低 > 10%
- [ ] WFA pass 率不降低

VERIFY METHOD:
硬測試 — 每輪跑：
  1. python scripts/verify_pla_ascii.py --strict
  2. ASCII compliance + 5 operational items
  3. 用戶 MC12 backtest A/B
  4. Claude 跑 comparison script

EACH ITERATION:
1. Read state log，看上次失敗原因
2. 設計 1 個 fix（不超過 30 lines diff）
3. Edit .pla
4. Verify ASCII + structural
5. 等用戶 backtest
6. Claude 對比 → fix 是否生效

STOP: fix 生效 OR 3 iterations (bug fix 應該快)
```

### 模板 D-2：W5 10-dim institutional eval Loop

```
LOOP SPEC: [策略] W5 10-dim Institutional Eval

GOAL:
通過 CLAUDE.md Rule #13 所有 10 個 dimensions, 才可 promote 到 live_simulation。

SUCCESS CRITERIA:
- [ ] Sharpe / Sortino / Calmar ≥ 0.15
- [ ] Max DD < 25% account
- [ ] 跨策略相關性 < 0.7 vs 既有 7 sleeves
- [ ] DD Clustering < 3σ (or event-level < 1.5x mean acceptable)
- [ ] Sample ≥ 100
- [ ] WFE > 50%
- [ ] Three-regime PF > 1.0 各別
- [ ] Adj PF (含滑價) > 1.3
- [ ] Operational 5/5 (Settlement/SetStopLoss/Holiday/Kill/IOG)
- [ ] Regulatory 標準

VERIFY METHOD:
混合 — 8 個可測量 + 2 個 review pass
EACH ITERATION: 一次只解 1 個 dim fail，最多 5 iterations
STOP: 10/10 PASS OR ABORT (轉 KILL or accept caveats)
```

---

## 5. Sub-Agent 分離設計（推薦）

```
┌─────────────────────────────┐
│ WRITER (Sonnet / Haiku)     │
│ - 寫 .pla / 改 input        │
│ - 產出 backtest setup       │
└─────────┬───────────────────┘
          ↓ 產物
┌─────────────────────────────┐
│ REVIEWER (Opus 4.7/4.8 high) │
│ - 跑 analysis script        │
│ - 對照 SUCCESS CRITERIA     │
│ - 嚴格找 over-fit signal    │
└─────────┬───────────────────┘
          ↓ verdict
┌─────────────────────────────┐
│ LOOP CONTROLLER (User)      │
│ - Read reviewer verdict     │
│ - All PASS → FINAL          │
│ - FAIL → 反饋 Writer 修     │
│ - 達上限 → STOP             │
└─────────────────────────────┘
```

---

## 6. State Log 範本

存放位置：`strategies/research/<策略>/loop_state_<task>.md`

```markdown
# Loop State: S3_S WFA Validation
# Started: 2026-06-26
# Status: ABORTED (3/9 pass, 5 iterations exhausted)

## Iteration 1 (v1.2 baseline)
- Action: 9 windows IS/OOS, no GA, default inputs
- Result: FAIL — 3/9 pass, median WFE -19%
- Failed Criteria: 4/5 gates fail
- Root Cause: event-driven alpha, W1-W4 全 fail
- Next Priority: 嘗試 reduced GA (4 params)

## Iteration 2 (v1.6 4-param GA)
- Action: GA on BWPctile / TargetATR / MaxBars / SP_Trigger
- Result: FAIL — 3/9 pass, median WFE -19%
- 跟 v1.2 完全相同 → GA 沒幫助
- Next Priority: 試 regime filter

## Iteration 3 (v1.7 regime filter)
- Action: 加 Daily MA50/200 ratio filter
- Result: TBD
- ...
```

---

## 7. 常見失敗模式 + 防護

| 失敗模式 | 症狀 | 防護 |
|----------|------|------|
| Ralph Wiggum Loop | 過早宣告完成 | Verify 必須外部，不自我判定 |
| 無限空轉 | 改但不收斂 | 硬性 5-8 iterations 上限 |
| 重複犯錯 | 每輪同 error | State log 強制記錄失敗原因 |
| 過度擬合 | IS 暴衝 OOS 慘 | WFA 包進 verify, 不只看 IS |
| Context 爆炸 | Token 用太多 | 每輪只傳必要 state |
| Reviewer 太鬆 | 什麼都 PASS | Opus + 嚴格 instruction |

---

## 8. 快速 Cheat Sheet（TXF1 專用）

```
1. 最終產物?              → GOAL
2. 怎樣算做好?            → SUCCESS CRITERIA (用 CLAUDE.md Rule #13 10 dim or WFA gates)
3. 怎麼驗證?              → VERIFY METHOD (scripts/ 或 user MC12 backtest)
4. 最多跑幾輪?            → HARD LIMIT (3-8)
5. 失敗了怎麼辦?           → FINAL_VERDICT.md (per 用戶 規範)
6. 絕對不能碰?            → Lesson L24 / Rule #14 / R-6 鐵則
7. 組裝 → 完成
```

---

## 9. 引用方式

```
請參考 docs/methodology/LOOP_FRAMEWORK.md，把以下任務轉成 Loop Spec：
[貼上任務描述]
```

或直接點名模板：
```
請用 LOOP_FRAMEWORK.md 模板 D-1 幫我建 S4_L 的 WFA Loop
```

---

## 10. 跟既有 SOP 整合

| 既有 SOP | 跟 Loop 關係 |
|---------|-----------|
| `OFFICIAL_ROADMAP.md` (Rule #14) | Loop 不可違反排程順序 |
| `STRATEGY_RD_SOP_v2.md` (W0-W6) | W4 WFA / W5 eval 用 Loop 包裝 |
| `lesson_L24_*.md` | Loop 不可建議違反 lessons 的 fix |
| `feedback_strategy_kill_must_document.md` | Loop ABORT 必出 FINAL_VERDICT |
| Stage -1 enforcement | Loop **不可**取代 Stage -1 創意設計 |
