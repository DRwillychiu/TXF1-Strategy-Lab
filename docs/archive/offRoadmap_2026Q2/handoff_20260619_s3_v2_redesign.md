# Handoff — S3 v2.0 Redesign (對話接續)

**寫於**：2026-06-19 ~23:30
**收件人**：新對話的 Claude
**原對話 token 已過量** → 用戶在新對話繼續 S3 work

---

## 一、當前狀態快照

### S3 v1.1 (已 deploy, commit `fe882a3`)
- 從 v1.0 660 LOC → v1.1 850 LOC
- **3 個 critical bug** 已修（LastBarOnChart_Ex + 2 RSI Data1-vs-Daily indexing）
- **13 audit-workflow patches** 已套用（4 HIGH + 6 MED + 3 LOW）
- 3 個 patches 跳過（#12 Data2 unused / #13 loop-80 / #14 section renumber）
- `verify_s3_pullbackshort.py`：**86/86 PASS**
- 路徑：`strategies/research/S03_PullbackShort/`

### Phase 1 GA Optimization 跑了 2 次（**失敗**）
- GA 設定：256 pop × **1 generation** = 不充分（用戶不知道世代 1 太少）
- 兩次 best 都 corner spike：
  - Daily_RSI_Threshold = 75
  - Daily_Dist_MA20_Pct = **5** (上邊角)
  - ATR_Spike_Mult = **1.1** (下邊角)
  - TP_Pct = **0.5** (下邊角)
  - SL_ATR_Mult = 4 / 3 (兩次不同, plateau)
- 績效：
  - PF gross 1.37 (低於 1.5 目標)
  - **PF 含滑價 = -0.92** ❌ 結構性虧損
  - 樣本 52 trades / 5.75 年 = **9 trades/year** (target 25-40)
  - **54% trades 集中 2026 H1** (regime over-fit)

### 用戶根因診斷（精準）
> **「觀察週期太長，導致實際有單機會降低」**

= Multi-TF 卡頓效應：最慢規則 (Daily Tier 1) 限制最快執行 (5M Tier 2)。Daily MA + RSI sustained 2 日 + 距 MA20 +3% 三 AND，年化只 ~30 個 WATCH-day。

### 用戶決策：**redesign 為 S3 v2.0**
不是 input 沒掃好，是 architecture 本質問題。

---

## 二、S3 v2.0 已 LOCKED 的 5 個設計決策

| Q | 決策 |
|---|------|
| **1** | 命名 **S3 v2.0**（v1.1 標 deprecated 但保留 .pla）|
| **2** | 操作時段：**Day (08:45-13:25 flat)** + **Night (15:00-04:30 flat)** ⚠️ 新增夜盤 |
| **3** | 持倉 hard cap **90 min** (18 × 5M bars) |
| **4** | 雙路徑進場 OR 邏輯（見下方 spec）|
| **5** | **Workflow 先 verify** alpha thesis（不再直接 implement 才發現結構錯）|

---

## 三、S3 v2.0 完整 Draft Spec

### Path C — Setup-Based Short (5-AND)
```
C1.1: Today Close > Today Open + C_RelStr_Min_Pct        (default 0.5%)
C1.2: Today High  > Today Open + C_DayHigh_Min_Pct       (default 0.8%)
C1.3: Distance from session high in [C_Pullback_Min, C_Pullback_Max]
                                                          (default 0.3-1.5%)
C2.1: Consec_Red_Bars 5M consecutive red K               (default 3)
C2.2: Close < 5M EMA(EMA_Fast_Len) AND EMA falling       (default 5)

Entry label: SE_RPS_PathC
```

### Path D — Event-Based Short (5-AND)
```
D1.1: Current 5M K drop > ATR(20) * D_BurstMult          (default 3.0)
D1.2: Close < Open (red confirm)
D2.1: Today Close > Today Open + D_MiniRegime_Pct        (default 0.3%)
D2.2: Distance from session high > D_MinFromHigh_Pct     (default 0.5%)
D3.1: No SE_RPS_PathD in last 5 bars (anti-noise)        (default 5 bars)

Entry label: SE_RPS_PathD
```

### OR Integration
- C 優先 D（C 是 higher-quality 5-AND vs D 的 burst event）
- 同 bar 雙觸發 → 只進 C
- 同日 cooldown（沿用 v1.1）

### Exit Tier
| Exit | v1.1 | **v2.0** |
|------|------|---------|
| TP % | 0.7% | **0.6%** |
| SL ATR | × 4 | **× 3** |
| Time stop | 24 bar (120 min) | **18 bar (90 min)** |
| Day flat | 13:25 | **13:25** (不變) |
| **Night flat** | (無) | **04:30** ⚠️ 新增 |
| Frozen SL backup | 有 | **有**（沿用 v1.1 fix）|
| Same-day cooldown | 有 | 有 |

### Sessions
- Day:   08:45 - 13:25 (entry window) → 13:25 force flat
- Night: 15:00 - 03:30 (entry window) → 04:30 force flat
- **跨段不持倉**（day 持倉不過 13:25, night 持倉不過 04:30）
- Holiday rules (02:45 flat) / Settlement (12:30 flat) 仍 apply

### Inputs 預估（~13 個 tunable）
**Path C** (4 個): C_RelStr_Min_Pct / C_DayHigh_Min_Pct / C_Pullback_Min_Pct / C_Pullback_Max_Pct
**Path D** (4 個): D_BurstMult / D_MiniRegime_Pct / D_MinFromHigh_Pct / D_AntiNoise_Bars
**Shared with v1.1** (5 個): Consec_Red_Bars / EMA_Fast_Len / TP_Pct / SL_ATR_Mult / Max_Bars_TimeStop

### Projected Performance (pre-backtest, to verify)
| 指標 | v1.1 實際 | v2.0 預估 |
|------|-----------|-----------|
| Trades/year | 9 | **80-150** |
| WR | 53.85% | 48-52% |
| PF gross | 1.37 | 1.25-1.40 |
| **PF 含滑價** | **-0.92** ❌ | **1.10-1.30** ✅ |
| Sharpe (年化) | 0.21 | 0.5-0.8 |

---

## 四、進行中 Workflow（**最重要**）

### Task ID: `w8btw7iog`

**狀態**：跑了 ~3 分鐘（啟動於 2026-06-19 ~23:25），預計 15-30 分總時長

**設計**：
- Phase 1: 5 平行 deep alpha verifier
  - A: Path C alpha 驗證（學術 + TXF1 統計 + condition 合理性）
  - B: Path D alpha 驗證（volatility burst literature + ATR×3 校準）
  - C: 夜盤 alpha + 風險（liquidity / S1 conflict / session boundary）
  - D: Portfolio interaction（correlation 預估 + Sharpe impact）
  - E: Adversarial brutal critic
- Phase 2: 3-vote refute per claim
- Phase 3: GO/NO-GO synthesis + verified design spec

**Verdict 範圍**：
- `GO` — 照 spec 進 implementation
- `GO_WITH_MODIFICATIONS` — 改某些後進
- `NO_GO_DAY_ONLY` — 砍夜盤先 ship day-only
- `NO_GO_REDESIGN` — 重大 flaw 回 drawing board

**輸出位置**：
```
C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Desktop\9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f\tasks\w8btw7iog.output
```

**Script 位置**（如需 resume 或 inspect）：
```
C:\Users\User\.claude\projects\C--Users-User-Desktop\9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f\workflows\scripts\s3-v2-alpha-verify-wf_f6964884-711.js
```

---

## 五、新對話 Claude 的接續 SOP

### Step 1：檢查 Workflow 是否完成
```python
# 方法 A: 看 output file 是否存在
ls "C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Desktop\9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f\tasks\w8btw7iog.output"

# 方法 B: 用 TaskOutput tool with block=false
# (需要 ToolSearch 載入 TaskOutput / TaskGet)
```

### Step 2：Read .output 看 verdict
```
Read the JSON result, look at:
  - go_no_go
  - confirmed_alpha_sources
  - critical_design_modifications
  - realistic_performance_projection
  - night_session_recommendation
  - top_risks_unresolved
  - user_decisions_needed
```

### Step 3：依 verdict 決定下一步
- **GO / GO_WITH_MODIFICATIONS** → 進 implementation:
  - 寫 `S3_v2_design_spec.md`
  - 寫 `S3_RapidPullbackShort_v2.pla` (~600 LOC, dual-path)
  - 寫 `verify_s3_v2.py` (~80 checks)
  - git commit + push (atomic)
- **NO_GO_DAY_ONLY** → 告訴用戶，等同意後 ship day-only 版本
- **NO_GO_REDESIGN** → 詳細解釋 flaw，等用戶決策

### Step 4：用戶優先原則
- **正確 > 快速**（這是 v1.1 慘案後的鐵律）
- 不跳過 verification
- 不直接 implement 沒驗證的 design

---

## 六、Key Files for Reference

### S3 v1.1 既有檔案
- `strategies/research/S03_PullbackShort/S3_RapidPullbackShort.pla` (v1.1)
- `strategies/research/S03_PullbackShort/S3_RapidPullbackShort_strategy.md`
- `strategies/research/S03_PullbackShort/S3_RapidPullbackShort_annotated.md`
- `strategies/research/S03_PullbackShort/S3_PullbackShort_design_spec_v2.md` (v1.1 spec, 改 v2.0 時參考)
- `strategies/research/S03_PullbackShort/S3_optimization_ranges_20260620.md`
- `scripts/verify_s3_pullbackshort.py` (86/86 PASS)
- `docs/portfolio_allocation_v3_20260620.md`
- `docs/L4_retirement_report_20260620.md`

### Phase 1 失敗證據（給新 Claude 看）
- `C:\Users\User\Desktop\MC9_20260108\回測報告\TXF1  PullbackShort 策略回測績效報告_phase1.xlsx`
  → 看「設定」分頁知道 best 用了 RSI=75/Dist=5/ATR=1.1/TP=0.5
  → 看「策略分析」分頁知道 PF=1.37 含滑價 -0.92
  → 看「交易明細」54% 集中 2026 H1

### Workflow 歷史（這個 session 的）
- Audit Workflow `w2zrqguup` (322 agents / 47 min / 15.5M tokens) — 找到 16 bugs
- Impl Workflow `wmt9c8kyq` (5 agents / 13 min / 325K tokens) — 13 patches
- **Alpha Verify Workflow `w8btw7iog`** (~20-36 agents / 15-30 min, **進行中**)

---

## 七、Git 狀態

- Latest commit: **`fe882a3`** "S3 RapidPullbackShort v1.0 → v1.1"
- Working tree: 應該 clean（無 v2.0 變動）
- Remote: 同步 origin/main

---

## 八、用戶 Profile 重要規則（從 memory）

| 規則 | 簡述 |
|------|------|
| 對話繁中 | Traditional Chinese 對話，code English |
| 不問休息 | User 自管休息節奏 |
| Git 一律 push | "更新 git" = commit + push 不可只本地 |
| MC Time 24hr | 跨日商品時段必須閉區間 |
| 假日鐵律 | TXF1 必須假日前平倉 + 封鎖前夕夜盤 |
| 趨勢讓利潤奔跑 | 不建議趨勢策略加 BE/SP |
| MC 進出場標籤 | LE_/LX_/SE_/SX_ 嚴格區分 |
| Filter 重疊度檢查 | 新 input 必 grep 既有 conditions 確認非 redundant |

---

## 九、新對話開機提示

```
1. 讀本檔: docs/handoff_20260619_s3_v2_redesign.md
2. 用 ls 或 Read 檢查 Workflow w8btw7iog.output 是否存在
   路徑: C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Desktop\9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f\tasks\w8btw7iog.output
3a. 如完成: Read JSON → 給用戶 verdict 摘要 + 下一步建議
3b. 如未完成: 告訴用戶在跑，等 task-notification
4. 用戶確認後進 implementation 或 redesign
```

---

**Workflow 結果是接續關鍵。Read .output file 第一**。
