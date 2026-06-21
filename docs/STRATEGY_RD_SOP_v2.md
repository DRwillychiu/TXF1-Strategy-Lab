# Strategy R&D SOP v2.0

**版本**：v2.0 (2026-06-21)
**狀態**：✅ Active — 強制位階（CLAUDE.md Rule 補充）
**版本歷史**：
- v1.0 (推測存在於 memory reference 但未實作)
- **v2.0 (本檔，2026-06-21)** — 整合 S2/S4/S5/S6 4 個 KILL 學到的 21 lessons + Pre-W0 gates

---

## 為什麼需要這份 SOP

2026-06-21 一天內連續 4 個策略 KILL：
- S2 InsideBarBreak (alpha 已死)
- S4 TurnOfMonth (cyclical decay)
- S5 SPX_Overnight (cross-asset follow 錯)
- S6 ForeignPositionFade (MC12 無法執行)

每個 KILL 都產出新 lessons，累積到 **L1-L21 (21 個)**。  
**不 codify SOP，下次 Claude 必重蹈覆轍**。

本 SOP 把 21 lessons + Pre-W0 gates 變成**可重複的 workflow**，把今天的「直覺判斷」變成「強制檢核」。

---

# 一、總流程圖

```
新策略 candidate
    ↓
Pre-W0 Gate 1: MC12 execution feasibility?  ← L21 (S6 KILL 學到)
    ├─ ❌ Non-MC12-native → AUTO KILL → write FINAL_VERDICT.md
    └─ ✓ PASS
    ↓
Pre-W0 Gate 2: Operational coherence?
    ├─ ❌ 引入新 layer → AUTO KILL
    └─ ✓ PASS
    ↓
W0: Alpha Pre-verification (Python)  ← L14-L18 (S4/S5 學到)
    ├─ ❌ Fail any of 4 gates → KILL → FINAL_VERDICT
    └─ ✓ PASS all 4
    ↓
W1: Design spec (alpha thesis + user 5 decisions)
    ↓
W2: .pla code (~150-650 LOC)
    ↓
W3: verify_<strategy>.py + baseline backtest
    ├─ PF << pre-verify estimate → implementation bug, fix
    └─ PF ≈ pre-verify estimate → continue
    ↓
W4: Phase 1 sensitivity sweep
    ↓
W5: Phase 2 Walk-Forward optimization
    ↓
W6: Phase 3 Monte Carlo + 10-dim institutional eval (Rule #13)
    ├─ Any FAIL → KILL or rework
    └─ All PASS → promote
    ↓
W7+: Live_simulation observation → eventually promote to live/
```

---

# 二、Pre-W0 Gates（**新增，本 SOP 核心貢獻**）

## Gate 1: MC12 Execution Feasibility（**L21**）

**問題**：策略的所有資料 source 是否 MC12 native auto-executable？

### ✓ PASS 條件

- 資料源是 MC12 native price feed (TXF1 / TWII / commodity / forex / index)
- 跨資產資料已有 ASCII Mapping 載入機制（如 SPX via yfinance → CSV → MC ASCII feed）
- 無人工每日 import 需求

### ❌ FAIL 條件（**AUTO KILL，不需 alpha 預檢**）

- 需要每日人工下載 CSV import（TAIFEX 三大法人 / 主力券商 / 自家爬蟲）
- 需要外部 HTTP API call（MC12 PowerLanguage 沒有 native HTTP）
- 需要 alert + 人工下單
- 跟既有 portfolio 7 sleeves 不同 operational architecture

### 案例

| 策略 | Gate 1 | 結果 |
|------|--------|------|
| S5 SPX_Overnight | ✓ (yfinance + CSV ASCII feed 可行) | PASS |
| **S6 ForeignPositionFade** | ❌ (TAIFEX 三大法人需人工 import) | **AUTO KILL** |
| S7 PreSettlementHarvest | ✓ (純 TXF1 calendar，MC native) | PASS |
| S8 FOMC_OvernightFade | ✓ (event 排程 + TXF1 native) | PASS |

## Gate 2: Operational Coherence

**問題**：跟既有 portfolio 7 sleeves (L1-L5 + S1 + S3 v2.0.4) operational architecture 一致嗎？

### ✓ PASS 條件

- 部署方式跟既有策略一致（MC12 chart + strategy 自動執行）
- Settlement_Flat / Holiday / SetStopLoss 模組相容
- Position sizing 跟既有 1-contract fixed 兼容
- 不需要額外監控人力

### ❌ FAIL 條件

- 需要新的 platform (Python + 券商 API)
- 需要額外人力（每日手動下單 / 監控）
- 需要修改既有 Constitution

---

# 三、W0 Alpha Pre-verification（**強制 4 gates**）

**位置**：Python script in `scripts/analyze_<strategy>_preverify.py`

**目的**：在寫 W1 spec **之前**，用實證證明 alpha 存在。

## ✓ 通過 4 gates 才能進 W1

### Gate A: 28-year robustness（**L14**）

- Fetch **≥ 28 年**歷史資料（yfinance ^TWII / ^GSPC / etc.）
- 6.4 年絕對不夠
- 必須涵蓋 ≥ 2 個 macro cycle

### Gate B: Cross-period stability（**L15**）

- 把資料切 ≥ 4 個 sub-period（不是只 early/late）
- 每個 sub-period 算 Sharpe / PF
- **≥ 4/6 sub-period Sharpe > 0.3** = PASS

### Gate C: Recent-bias check（**L18**）

- 計算 recent (last 6.4y) Sharpe / long-term (full 28y) Sharpe ratio
- **ratio < 2.5×** = PASS
- ratio > 2.5× = AUTO-KILL (S4/S5 都死於此)

### Gate D: Direction symmetry（**L20**, signal-following 策略）

- 對 LONG/SHORT 兩個方向分別算 Sharpe / PF
- 兩邊都 > 0.3 → balanced，PASS
- 一邊強一邊弱 → asymmetric，redesign or KILL
- 兩邊都 < 0.3 → KILL

## 標準 institutional 4-gate verdict

```python
print(f'  28y Sharpe > 0.4:           {"PASS" if s_all > 0.4 else "FAIL"}')
print(f'  28y PF > 1.3:               {"PASS" if pf > 1.3 else "FAIL"}')
print(f'  L18 recent/long < 2.5x:     {"PASS" if ratio < 2.5 else "FAIL"}')
print(f'  ≥4/6 regimes Sharpe > 0.3:  {"PASS" if regime_pass >= 4 else "FAIL"}')
```

**全 PASS → 進 W1**，**任一 FAIL → KILL 寫 FINAL_VERDICT.md**

---

# 四、W1 Spec（**alpha 已驗證後**才寫）

## 必含 sections

1. Strategy Identity (name, class, timeframe, data feeds)
2. Alpha Thesis（**含 W0 實證數據**，不是學術 guess）
3. Trading Mechanics (entry, exit, P0 chain, SetStopLoss)
4. Parameter List (~10-30 inputs, all MC-optimizable)
5. Expected Performance（基於 W0 實證，含 B&H 對比）
6. Risk Management (failure modes + disclosure)
7. Mandatory Compliance (Rule #11/#12/#13)
8. Lessons applied（L1-L21 哪些用到）
9. W1-W7 roadmap
10. User decisions (5 Q 推薦 + 備選)

## 用戶 5 Q 規範

```
Q1: Entry timing/condition (推薦 + 2 備選)
Q2: Exit timing/method (推薦 + 2 備選)
Q3: Settlement/Holiday conflict (推薦 + 1 備選)
Q4: 加 trend/regime filter? (推薦 v1.0 不加 + 2 備選)
Q5: W3 結果 PF < X 處理 (推薦 立即結案 + 備選 sweep)
```

---

# 五、W2 .pla 實作規範

## 必守

- Sec 1: Inputs (~10-30, all numeric MC-optimizable)
- Sec 2: Variables (v_ prefix)
- Sec 3: Arrays (Holiday_Tail 63 entries 沿用 L2 template)
- Sec 4: Section 0 Holiday Registry init
- Sec 5: Holiday / Registry / Settlement detection
- Sec 6: Indicator calculations
- Sec 7: Cooldown reset
- Sec 8: SetStopLoss (Rule #12, single call)
- Sec 9: Entry logic (≤ 5 conditions per Rule #10)
- Sec 10: Exit chain (P0-1 Kill > P0-2 Registry > P0-3 Holiday > P0-4 Settlement > strategy exits)
- Sec 11: Cooldown set on exit
- Sec 12+: Diagnostic logging

## 8 個從 S3 v1.1 + S4/S5/S6 學到的 anti-patterns（不可違反）

1. ❌ 不可用 `LastBarOnChart_Ex(0)` (不存在)
2. ❌ 不可用 `RSI(... of DataN)[N]` 不加 `of DataN` 後綴 (Data1-indexed)
3. ❌ 不可有 unmatched `Time >= X` (closed-interval 必須)
4. ❌ 不可重複 `XAverage(...)`，要 `v = XAverage(...); v_prev = v[1]`
5. ❌ 不可漏 SetStopLoss
6. ❌ 不可違反 P0 chain 順序
7. ❌ 不可漏 Volume 在 5M timeframe 上的可靠度檢查（S2 v0.4 lesson）
8. ❌ 不可硬編碼 numeric threshold (must be input)

---

# 六、W3 Verify Script 規範

寫 `scripts/verify_<strategy>.py`，必含 12 個 group：

```
A. Rule #11 Settlement_Flat 7 elements (5 checks)
B. Rule #12 P3b SetStopLoss (5 checks)
C. Rule #13 inputs / allocation / header (3 checks)
D. Entry logic correctness (~10 checks)
E. Exit logic correctness (~10 checks)
F. Time safety closed-interval audit (5 checks)
G. Volume safety (1 check, S2 lesson)
H. Filter redundancy check (3 checks)
I. Same-day cooldown (3 checks)
J. Label convention (5 checks)
K. Header / inits / feeds (10 checks)
L. PL function existence (8 checks) ← 學自 S3 v1.1 LastBarOnChart_Ex 慘案
```

**TOTAL ≥ 68 checks 必過**

---

# 七、KILL 規範（**永久強制位階**）

**任何 stage 觸發 KILL** → 必須產出 `S<N>_FINAL_VERDICT.md`

必含 sections（[`feedback_strategy_kill_must_document`](../) 規範）：

1. 一句話總結 KILL 理由
2. 量化證據（≥3 個獨立指標 fail）
3. 我（Claude）的失誤檢討
4. 新 lessons 提煉（永久保留 memory）
5. KILL 規範（不可重啟條件）
6. 資源轉向
7. 跨檔交叉參考

**KILL 速度演進證明 lessons compound**：
- S2: 5 版本 + 多週
- S4: 1 天 (W1 同日)
- S5: 0.5 天 (W0 pre-verify)
- S6: **0.1 天** (pre-W0 user gate)

---

# 八、累積 Lessons L1-L21（完整列表）

## S2 InsideBarBreak (L1-L13)
1. Python 日線代理 PF 不可信
2. 設計超前實證 = 紙上談兵
3. MC Time 24-hour 必須閉區間
4. **突破類策略 → Long-only 是常態** ⭐
5. **教科書公開策略 alpha 已大幅衰減** ⭐
6. MC12 input persistence 必須完全移除重載
7. MTF 設計前先驗證持倉天數
8. TP 倍率必從 MFE 統計推導
9. 過濾類 input 必須驗證歷史通過率
10. 同日多進場需 cooldown
11. **Buy and Hold 是現實檢驗** ⭐
12. 4 次設計迭代 + 0 實證 = 警訊
13. **新 filter 必須做重疊度 + 通過率雙重檢查** ⭐

## S4 TurnOfMonth (L14-L18)
14. **Calendar/behavioral effect 必須 ≥ 28 年驗證**
15. **「跨期一致」必須跨 backtest 外的時段**
16. **教科書策略 default 視為 alpha 已衰減**
17. **學術 quote 必須 read 整段不能 cherry-pick**
18. **Recent-bias check 強制 — recent/long Sharpe ratio > 2.5× = auto-KILL**

## S5 SPX_Overnight (L19-L20)
19. **Cross-asset spillover 必做 microstructure 預檢**
20. **Signal-following 策略必測雙方向 (LONG/SHORT)**

## S6 ForeignPositionFade (L21)
21. **MC12 Execution Feasibility = Pre-Everything Gate**

---

# 九、Roadmap 評估（用 SOP gates 重打分）

**4/6 KILLED 後剩餘 candidates**（用 L14-L21 預判）：

| Strategy | Gate 1 (MC12) | Gate 2 (Op) | L14 (28y) | L16 (textbook) | L18 (recent-bias) | L19 (cross-asset) | 綜合 |
|----------|--------|------|------|------|------|------|------|
| ~~S2~~ | ✓ | ✓ | N/A | 🔴 死 | N/A | N/A | 💀 KILLED |
| ~~S4~~ | ✓ | ✓ | 🔴 失敗 | 🔴 死 | 🔴 死 | N/A | 💀 KILLED |
| ~~S5~~ | ✓ | ✓ | 🔴 失敗 | ⚠️ | 🔴 死 | 🔴 死 | 💀 KILLED |
| ~~S6~~ | ❌ FAIL | ❌ FAIL | N/A | N/A | N/A | N/A | 💀 KILLED |
| **S7 PreSettlement** | ✓ | ✓ | 待驗 | 🔴 **L16 高風險** (calendar) | 待驗 | N/A | 🔴 預判 KILL 高機率 |
| **S8 FOMC_OvernightFade** | ✓ | ✓ | 待驗 (8/yr 樣本邊際) | 🟡 中 | 待驗 | 🟡 fade 比 follow 好 | 🟡 中 |
| S9-S15 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

---

# 十、本 SOP 的 audit trail

| 來源 | Lessons 貢獻 |
|------|------------|
| S2 結案 (2026-06-20 → 2026-06-21 30M evidence) | L1-L13 + KILL 必文件化規範 |
| S4 結案 (2026-06-21) | L14-L18 + W0 pre-verification SOP |
| S5 結案 (2026-06-21) | L19-L20 + dual-direction test |
| S6 結案 (2026-06-21) | L21 + Pre-W0 gates |

**S3 v2.0.4 (LIVE_SIMULATION) audit 也貢獻**：
- L21 預先 hint: 所有 portfolio 策略都是 MC12 native
- v1.1 → v2.0.4 redesign 過程證明 alpha verification 重要

---

# 十一、本 SOP 應用範例

立刻套用在 S7 PreSettlementHarvest：

```
Pre-W0 Gate 1: MC12 native? 
  → S7 用 TXF1 自身 calendar (3rd Wed detection) → ✓ PASS

Pre-W0 Gate 2: Operational coherence?
  → 純 MC12 chart + strategy → ✓ PASS
  → 但需要 Constitution amendment (EVENT_DRIVEN_EXEMPT flag)
  → 評估：amendment 一次性，過後 operational identical → ✓ PASS

W0 Alpha Pre-verification: 4 gates 套用
  → 跑 scripts/analyze_s7_presettlement_preverify.py
  → ★ 等結果決定 GO/KILL
```

---

**本 SOP 是今天 4 KILL 換來的鐵紀律。每次新策略必走，不可跳過 Gate。**
