# S16_S v0.5 — Pending Decision Node (2026-07-09)

**用途**：保留 2026-07-09 深度討論的結論與未定決策，供下次接續。
**當前狀態**：Entry Layer 討論完成，執行方向未定。

---

## 一、已達成共識（LOCK）

### A1. 策略哲學修正 ✅
- 原本 W1 spec：「進場門戶大開，出場刀鋒銳利」
- **用戶 07-09 明確 ruling**：**「策略要清楚且熟悉他該賺的錢，碰到不適合的行情可以小虧或不做」**
- 策略性格從「捕手型」→ **「狙擊手型」**
- 定位：**5M 極短動能 burst 狙擊手**

### A2. v0.4-CANDIDATE 判定 ✅
- **不是錯，是暗示了對的方向**
- 績效結構符合用戶期待（+16.3% 年化 / MDD abs 259K < 300K）
- **但參數選擇違反 5M 意義**（Slow=90 已跨到 15M/hourly 領域）
- v0.4 教訓：**「burst-capture 是可能存在 alpha 的」+ 「TimeStop 短持倉可以是 feature」**
- **需要**在 5M 合理範圍內重新找 sweet spot

### A3. 「進場精挑細選」正確詮釋 ✅
- **不是**加更多 filter（ATR/Volume/連續下彎 → 實戰分析後全否決）
- **是**：**同樣 5 gate + 參數調嚴**
- **主要旋鈕**：**MinSlope**（從溫和 1.0 → 精挑 5-10）

### A4. Exit Layer 決策 ✅
- **不動**（用戶 07-09 明確 ruling）
- 8 層 priority chain 已足夠
- **鎖定 defaults**：ML_ScoreTrigger=60 / BE_Trigger_ATR=1.0 / etc.

### A5. GA 方向 ✅
- **純參數校準**（不加新機制）
- 用戶偏好 **Genetic Algorithm**
- 用戶會**設定範圍**

---

## 二、未定決策（PENDING）

### D1. GA 執行方式（3 選 1）

| 選項 | 說明 | 時間 | 推薦度 |
|-----|------|------|--------|
| **A** | Phase 1 Focused Exhaustive（Fast/Slow/MinSlope 3 params, 200 組合）| 90 min | ⭐⭐⭐ |
| B | 一次全跑 Genetic（6 params, 12,800 space, 100 pop × 40 gen = 4000 evals）| 3-5 hr | ⭐⭐ |
| C | 先改 code（MinSlope 計算方式改「累積 N 根 slope」）再跑 | 30 min code + 90 min BT | ⭐ |

**用戶尚未 ruling**。

### D2. .pla defaults 是否 revert？

**選項**：
- 選 X：**保留 v0.4-CANDIDATE defaults**（Fast=25/Slow=90/Slope=26）→ GA sweep 值全都不含這些 → 強制回到 5M 意義範圍
- 選 Y：Revert 為 v0.5-SANE-BASELINE（Fast=8/Slow=25/Slope=1）→ 明確策略回歸原設計

**我推薦選 X**（保留 v0.4，讓 GA 自動回歸），因為避免 code churn，且 sweep range 已強制不含 v0.4 值。

**用戶尚未 ruling**。

### D3. Entry 端「加新 filter」vs「純參數校準」最終定案

- 上一則討論已完整分析「加新 filter」的實戰劣勢
- 用戶方向明確：**純參數校準**
- **需保留此討論結果進 W1 strategy.md 修正 audit trail**（尚未做）

### D4. Rule #14 命名決策（v0.4 已質變後）

- v0.4 Golden Cross 0 觸發、ML_Exit 0 觸發、TimeStop 主導
- 已不是「MA Cross」策略本質
- 若 v0.5 找到 5M 合理範圍 sweet spot（讓 Golden Cross 有機會 fire）→ **可回到 MA Cross 命名**
- 若 v0.5 也是 burst 型 → 需 Rule #14 justify 或改名

**待 GA 結果後才能定案**。

### D5. 成功標準修正

原追求：4/8 → 6/8 Rule #13 gates PASS
用戶新標準（07-09 討論）：
- **核心 4 gates**：Net > 0, PF > 1.0, MDD abs < 300K, Sample ≥ 100
- **次要**：Sharpe > 0.5, WR > 30%
- **策略特性 gate**：與 S3_S 低相關（作 hedge sleeve）
- **不追求 8/8**，追求**策略純度 + 合理績效**

**建議**：待 GA 結果後正式寫入 strategy.md 修正版。

---

## 三、完整 GA sweep table（**推薦選項 A Phase 1**）

### Phase 1 — Entry Sweet Spot Focused Exhaustive

```
Optimization Type: Exhaustive

Sweep 3 inputs:
  ZLEMA_Fast:   [5, 8, 10, 12, 15]                (5 values)
  ZLEMA_Slow:   [20, 25, 30, 40, 50]              (5)
  MinSlope:     [0.5, 1, 2, 3, 5, 8, 12, 20]      (8) <- CORE

Lock all others (or use v0.4-CANDIDATE current values):
  QuickStop_MaxLoss_Pts = 30    (compromise 15 vs 60)
  MaxHoldingBars        = 72    (Golden Cross has chance)
  StopATRMult           = 3.0
  ML_ScoreTrigger       = 60
  ML_ActivationPct      = 20
  All other Group C/D at spec defaults
  All Rule #11 defaults

Total: 5 × 5 × 8 = 200 combos
Time: ~90 min
```

### Phase 2（Phase 1 sweet spot 找到後）— Safety Net Fine Tune

```
Lock Phase 1 best (Fast, Slow, MinSlope)

Sweep:
  QuickStop_MaxLoss_Pts:  [15, 25, 40, 60]        (4)
  MaxHoldingBars:         [48, 72, 96, 144]       (4)
  StopATRMult:            [2.0, 2.5, 3.0, 3.5]    (4)

Total: 4 × 4 × 4 = 64 combos
Time: ~30-45 min
```

---

## 四、實戰角度已否決的 filter 選項（audit trail）

上一則討論已完整分析並否決：

| Filter | 主要否決原因 |
|--------|-----------|
| A. ATR 環境 gate | ATR 是延遲指標，錯過 burst 起點 |
| B. Volume 確認 | 台指期夜盤 volume 低，擋掉 60% alpha 機會 |
| C. Fast MA 連續 N 根下彎 | 15min delay 錯過 25-50% 動能 |
| D. Higher timeframe Daily regime | 違反 Layer 3 Option A + Lesson L24 |
| E. 時段 filter | Overfit 風險大 |
| F. Distance filter | 篩掉太多，回到 v0.4 陷阱 |

**保留可能**：
- G. Anti-Hunt L1（夜盤 SL 加寬）— 未來可考慮，不緊急

---

## 五、下次接續 SOP

### 若用戶回覆「執行 Phase 1」

1. 修 .pla defaults？（D2 決策）— **建議保留 v0.4，直接 sweep**
2. 用戶跑 MC12 Exhaustive 200 combos
3. 貼 xlsx 給 Claude
4. Claude 分析 MinSlope sensitivity + Fast/Slow best
5. 進 Phase 2 or 直接進 W5

### 若用戶回覆「Full Genetic」

1. 用戶跑 4000 evals Genetic
2. 貼 xlsx
3. Claude 分析 + Candidate G 決策

### 若用戶回覆「先改 code」

1. Claude 修改 MinSlope 計算方式（3-bar cumulative slope）
2. ASCII verify + push
3. 再跑 Phase 1

---

## 六、Git 狀態（本檔 commit 前）

- HEAD: `64c62cd` (v0.4-CANDIDATE)
- Working tree: clean
- 待新增：**本 md**

---

## 七、Files Index

### 今日新增文件
- `W4_ReGA_Phase1_analysis_20260709.md`（Phase 1 全負分析）
- `v04_CANDIDATE_analysis_20260709.md`（v0.4 深度分析）
- `PENDING_DECISION_20260709.md`（**本檔**）

### 歷史關鍵文件
- `S16_S_MACrossShort.pla`（v0.4-CANDIDATE 現行）
- `S16_S_strategy.md`（W1 14 章，需更新哲學修正）
- `S16_S_entry_exit_spec_20260708.md`（Layer 1+2+3 spec）
- `MA_deep_research_20260707.md`（**Slow ≤ 50 硬限**依據）
- `W0_alpha_preverify_result_20260708.md`（W0 STRONG PASS 歷史）

---

**End of Pending Decision — 2026-07-09 Desktop**

**用戶下次來時，讀本檔即可完整接續。**
