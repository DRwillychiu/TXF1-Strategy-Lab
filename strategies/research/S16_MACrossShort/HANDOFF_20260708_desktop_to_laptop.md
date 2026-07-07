# S16_S Handoff: Desktop 2026-07-08 → Laptop

**接手時請先讀本檔**，接續 S16_S W3 進度。

---

## 一、今日進度總覽（2026-07-08 桌機）

### ✅ 完成事項（6 milestones）

1. **Layer 2 出場端 4 機制深度設計 lock**
2. **Layer 3 Regime Filter LOCK = 選項 A**（純規則簡單，不加 filter）
3. **W0 Alpha Pre-Verify STRONG PASS**（daily proxy 40/216 combos 4/4 gates）
4. **主 README / research README / OFFICIAL_ROADMAP** 全部同步反映進度
5. **W1 策略正式文件**（14 章機構級規格）
6. **W2 .pla v0.1-DRAFT 實作 + W3 MC12 backtest SOP**

### 📊 Git 時間軸（今日 6 commits）

```
c7f52df  feat(S16_S): W2 .pla + W3 backtest SOP     ← 最新
3a2b7d6  docs(S16_S): W1 strategy definition (14 章)
50260f6  docs: update main + research + ROADMAP READMEs
fd29db2  feat(S16_S): W0 STRONG PASS (40/216 combos)
2188e5a  docs(S16_S): Layer 3 Regime Filter LOCK = A
8c56f08  docs(S16_S): Layer 1+2 entry+exit spec
```

Repo：https://github.com/DRwillychiu/TXF1-Strategy-Lab.git

---

## 二、當前策略狀態

### S16_S MACrossShort — W2 完成

| 項目 | 狀態 |
|------|------|
| 版本 | **v0.1-DRAFT** |
| 檔案 | `strategies/research/S16_MACrossShort/S16_S_MACrossShort.pla` |
| 行數 | 453 LOC |
| ASCII | ✅ 26/26 PASS |
| Rule 合規 | #11 / #12 / #15 / #17 / #14 全過 |
| 下一步 | **W3 MC12 backtest**（用戶手動跑）|

### S3_S 部署狀態（截至今日）

- ✅ v1.9.6-OPT-PROD 已 live_simulation 部署（2026-07-06）
- ⚠️ Entry-gate audit 15 findings 中：F1 Registry 2027-01-01 過期需 Q4 rebuild（無立即影響）

---

## 三、明天筆電端可能要做的事

用戶 wrap-up 語意 = **今晚 wrap，明天筆電端可能繼續 W3**。

### Option A — 用戶已在 MC12 跑 W3 backtest
- 用戶會提供 xlsx 路徑
- 讀 `W3_MC12_backtest_SOP.md` 第七章「給 Claude 回報格式」
- 立即進 W3 分析：
  1. 驗證 configuration 對齊
  2. Trade 分布統計（依 exit 標籤）
  3. 年度 breakdown（stability）
  4. 與 W0 daily proxy 對比
  5. Rule #18 5 件套 pre-check（初步 MC + Bootstrap）
  6. 產出 `W3_baseline_backtest_analysis_20260709.md`

### Option B — 用戶還沒跑 W3
- 讀 `W3_MC12_backtest_SOP.md` 提醒用戶部署步驟
- 或討論其他事項（如 S3_S entry-gate audit F1 rebuild）

### Option C — 用戶想改 W2 code
- 檢視當前 v0.1-DRAFT 有無漏洞
- 加入額外 factor 或調整 gate

---

## 四、W2 .pla v0.1-DRAFT 完整規格摘要

### Entry (Section 9)
```pla
Entry Signal:
  Death Cross at Data1 5M close (ZLEMA_Fast(8) crosses BELOW ZLEMA_Slow(25))
  AND AbsValue(Slow_slope) > MinSlope (1.0)         // M1
  AND v_Settlement_Day     = False                   // Rule #11
  AND v_Holiday_Block      = False                   // Rule #11 (placeholder)
  AND v_Registry_Expired   = False                   // Rule #11 (1280101)
  AND Manual_Kill_Switch   = False                   // Rule #11 P0

Order: sell short next bar at market
```

### Exit Priority Chain (Section 10)
```
P0 : Compliance (Kill / Registry / Holiday / Settlement)
P1 : M5 Quick Stop
     - P1a: v_Loss > 15 pts -> SX_MA_QuickStop_Loss
     - P1b: v_BarsSince >= 6 AND Close >= EntryPrice -> SX_MA_QuickStop_Time
P2 : M6 Multi-Layer (5 categories, activation at loss > 20% SL dist)
     - 1F: bullish engulfing
     - 2F: volume spike (> avg * 2)
     - 3F: RSI reversal from oversold
     - 4F: higher low + close > MA(10)
     - 5F: ATR expansion (ATR_short / ATR_long > 2.5)
     - Trigger: score % >= 65% AND cat count >= 3
P3 : M7 Breakeven Trail
     - Tier 1: profit >= 1 ATR -> lock at Entry - 5 pts
     - Tier 2: profit >= 1.5 ATR -> tighter lock at Entry - 10 pts
P4 : Golden Cross main exit
P5 : M8 Time Stop (BarsSince >= 48)
P6 : ATR Frozen SL (v_SL_Level as Stop order)
P7 : SetStopLoss engine guard (Section 7, Rule #12)
```

---

## 五、22 個 Input 完整清單（v0.1-DRAFT defaults）

| Group | Input | Default |
|-------|-------|---------|
| A Entry | ZLEMA_Fast | 8 |
| A Entry | ZLEMA_Slow | 25 |
| A Entry | MinSlope | 1.0 |
| B M5 | QuickStop_On | True |
| B M5 | QuickStop_MaxBars | 6 |
| B M5 | QuickStop_MaxLoss_Pts | 15 |
| C M6 | ML_On | True |
| C M6 | ML_ActivationPct | 20 |
| C M6 | ML_ScoreTrigger | 65 |
| C M6 | ML_MinCategories | 3 |
| C M6 | ML_VolAvgLen | 15 |
| C M6 | ML_VolSpikeMult | 2.0 |
| C M6 | ML_MA_ShortLen | 10 |
| C M6 | ML_ATR_ShortLen | 3 |
| C M6 | ML_ATR_LongLen | 90 |
| C M6 | ML_ATR_Ratio | 2.5 |
| D M7 | BE_On | True |
| D M7 | BE_Trigger_ATR | 1.0 |
| D M7 | BE_Buffer_Pts | 5 |
| D M7 | BE_Tier2_ATR | 1.5 |
| D M7 | BE_Tier2_Buffer_Pts | 10 |
| E M8 | M8_On | True |
| E M8 | MaxHoldingBars | 48 |
| F SL | ATR_Len | 14 |
| F SL | StopATRMult | 2.0 |
| H Rule#11 | Holiday_Flat_Time | 415 |
| H Rule#11 | Registry_Valid_Until | 1280101 |
| H Rule#11 | Manual_Kill_Switch | False |
| H Rule#11 | Settlement_Flat_Time | 1230 |

---

## 六、關鍵檔案清單

### S16_S 完整資料夾
```
strategies/research/S16_MACrossShort/
├── S16_S_MACrossShort.pla                       (453 LOC, W2 v0.1-DRAFT)
├── S16_S_strategy.md                            (W1, 14 章)
├── S16_S_entry_exit_spec_20260708.md            (Layer 1+2+3 完整 spec)
├── W0_alpha_preverify_result_20260708.md        (STRONG PASS 40/216)
├── W3_MC12_backtest_SOP.md                      (deployment SOP)
├── MA_deep_research_20260707.md                 (學術+市場全景)
├── _w0_alpha_preverify.py                       (可重跑)
├── S16_stage1_spec.md                           (原初 Stage-1)
├── HANDOFF_20260706_desktop_to_laptop.md        (歷史)
├── HANDOFF_20260707_laptop_to_desktop.md        (歷史)
└── HANDOFF_20260708_desktop_to_laptop.md        (本檔)
```

### S3_S 相關（明天可能延續 audit follow-up）
- `docs/research/S3_S_v196_entry_gate_audit_20260707.md` (15 findings)
- `docs/handoffs/handoff_20260707_s3s_entry_gate_audit.md`

---

## 七、規則遵守總結

- ✅ Rule #11 Settlement/Holiday/Kill/Registry
- ✅ Rule #12 SetStopLoss short guard
- ✅ Rule #13 10-dim (W5 待驗)
- ✅ Rule #14 OFFICIAL_ROADMAP（S16_S 已寫入）
- ✅ Rule #15 ASCII 100%（verify_pla_ascii.py 26/26 PASS）
- ✅ Rule #16 五支柱
- ✅ Rule #17 Multi-Layer 5 categories 已落實 M6
- ⏳ Rule #18 5 件套（W5 待跑）

---

## 八、S16_S W0-W6 進度

1. ✅ Stage -1 策略討論（2026-06-28 ~ 07-07）
2. ✅ Layer 1 進場設計（2026-07-07）
3. ✅ Layer 2 出場設計（2026-07-08）
4. ✅ Layer 3 Regime Filter Option A（2026-07-08）
5. ✅ W0 Alpha Pre-Verify STRONG PASS（2026-07-08）
6. ✅ W1 Strategy Definition（2026-07-08）
7. ✅ **W2 .pla v0.1-DRAFT + W3 SOP（2026-07-08）**
8. ⏳ **W3 MC12 baseline backtest（用戶手動跑，明天 or 之後）**
9. ⏳ W4 GA Phase 2 optimization
10. ⏳ W5 Rule #18 Non-WFA 5 件套
11. ⏳ W6 Promote 決策

---

**Handoff Complete — 2026-07-08 桌機端**
**明天筆電端見** 🌙

回筆電端第一步：讀本檔 → 若用戶已跑 backtest，立即進 W3 分析；若未跑，讀 W3 SOP 提醒 deployment。
