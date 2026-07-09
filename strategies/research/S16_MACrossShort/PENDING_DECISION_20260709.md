# S16_S v0.5 — Pending Decision Node (2026-07-09)

**用途**：保留 2026-07-09 深度討論的結論與未定決策，供下次接續。
**當前狀態**：v0.5 LOCKED + W5 五件套完成。全部決策已解決。

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

## 二、已解決決策（RESOLVED 2026-07-09）

### D1. GA 執行方式 — RESOLVED: Genetic Algorithm
- 執行路線：先 90-combo neighborhood Exhaustive → 再 1024-combo broad Genetic (25,920 space)
- 結果：F25/S70/Slope28 Calmar 3.96 勝出，v0.5 鎖定

### D2. .pla defaults — RESOLVED: v0.5 locked
- F25/S70/Slope28 + QS(4,60) MH24 ATR4.0
- Git commit: a212da6

### D3. Entry filter — RESOLVED: pure parameter calibration
- 純參數校準，不加新 filter（用戶 ruling）
- MinSlope 從 26→28 = 精挑旋鈕收緊

### D4. Rule #14 naming — RESOLVED: keep MACrossShort
- v0.5 GoldenCross 仍只有 2 筆觸發，TimeStop 仍主導 (20 筆)
- 但 Rule #14 naming 來自 OFFICIAL_ROADMAP (S16 = MACross)，不可改名
- 策略哲學定位：5M momentum burst sniper，名稱保留不變

### D5. Success criteria — RESOLVED: sniper-adapted thresholds
- 原 SOP 門檻（Claude 自訂）對 low-WR sniper 結構性不適用
- 用戶 ruling：驗證門檻須依策略類型調整
- Sniper 門檻：破產率 < 1% + 單筆 < 5% + Kelly > 0 + 期望值 > 0
- v0.5 結果：8/8 PASS（見 W5_fivepack_validation_20260709.md）
- 用戶 feedback 已存入 memory: feedback_validation_precheck

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

**v0.5 W5 已完成。下一步：用戶 ruling on promote to live_simulation。**

---

## 六、Git 狀態

- HEAD: `a212da6` (v0.5 parameter lock)
- W5 report: `W5_fivepack_validation_20260709.md`

---

## 七、Files Index

### 今日新增/更新文件
- `S16_S_MACrossShort.pla` — v0.5 (F25/S70/Slope28/QS60)
- `W5_fivepack_validation_20260709.md` — 五件套完整報告
- `PENDING_DECISION_20260709.md` — 本檔（全部 D1-D5 RESOLVED）

### 歷史關鍵文件
- `W4_ReGA_Phase1_analysis_20260709.md`（Phase 1 全負分析）
- `v04_CANDIDATE_analysis_20260709.md`（v0.4 深度分析）
- `S16_S_strategy.md`（W1 14 章）
- `S16_S_entry_exit_spec_20260708.md`（Layer 1+2+3 spec）
- `W0_alpha_preverify_result_20260708.md`（W0 STRONG PASS）

---

**End of Pending Decision — 2026-07-09 (all decisions RESOLVED)**
