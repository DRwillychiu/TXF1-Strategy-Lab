# S3_S Progress Handoff (2026-06-25 桌機 → 筆電端)

**狀態**：✅ **v2.0 EXPERIMENTAL .pla ready**，等明天筆電端跑 baseline backtest
**收件人**：2026-06-26+ 筆電端 Claude
**最新 commit**：`923d025`

---

## 一、今日完成

### v2.0 EXPERIMENTAL .pla 寫作（新檔，v1.2 FROZEN 不動）

**Driver**：用戶今早跟老闆討論後 ruling：
> 「60M 一波抱到底 + 反彈 33% 移動止損」
> 「一波抱到底 = 長下引線 OR 長紅實體 K 就出場」

**v2.0 設計變動 (vs v1.2 FROZEN)**：
1. TargetATRMult: 3.5 → **10**（TP 放遠，trail 主導）
2. SP_Retain_Pct: 70 → **67**（老闆 33% giveback）
3. **新 Layer: K-pattern Reversal Exit**（`SX_VS_Reversal`）
   - 長下引線（hammer）: wick > body × 2 AND wick > range × 50%
   - 長紅實體: Close > Open AND body > range × 70%
   - Arm 條件: 已賺 >= 1 ATR AND 持倉 >= 2 根 K
4. 新 priority: P0 → SL → **[Reversal]** → SP → Mid → TP(far) → TimeStop

**Thesis 對比**：
- v1.2: 「快進快出」short panic = V-bottom，TP 3.5 ATR 落袋
- v2.0: 「一波抱到底」short panic = 多日下跌，等 K 型態反轉確認結束

---

## 二、檔案結構

```
strategies/research/S03_VolSqueezeShort/
├── S3_VolSqueezeShort.pla          v1.2 FROZEN (不動)
├── S3_VolSqueezeShort_v2.pla       ★ v2.0 EXPERIMENTAL (今天新增, 719 LOC)
├── S3_VolSqueezeShort_annotated.md
├── README.md
├── extreme_event_coverage_20260624.md  (v1.2 分析)
├── progress_20260623_handoff.md
├── progress_20260624_handoff.md
└── progress_20260625_handoff.md    ★ 本檔
```

---

## 三、明天 (2026-06-26+) 筆電端 SOP

### Step 1: 同步雲端
```bash
cd ~/Desktop/TXF1-Strategy-Lab
git pull origin main
```

### Step 2: MC12 載入 v2.0 跑 baseline
- 開新 chart: **TXF1 60M** (不要替換 v1.2 chart, 並存對比)
- Load PowerLanguage: **`STRATEGY_GEN_S3_VolSqueezeShort_v2`**（注意 _v2 結尾）
- Strategy Properties:
  - Initial Capital: 1,000,000 NTD
  - Position Size: 1 contract
  - Slippage: 500 NTD per side (1000 RT)
  - 區間: 2020-01-20 ~ 2026-06-XX (同 v1.2)
- **Inputs 全用 default**（v2.0 already encoded TargetATR=10, SP_Retain=67, Use_Reversal=True 等）

### Step 3: 匯出 xlsx → 給筆電端 Claude 分析

### Step 4: 筆電端 Claude 任務
1. 讀本檔
2. 讀 v1.2 baseline data: `extreme_event_coverage_20260624.md`
3. 等用戶上傳 v2.0 xlsx
4. 跑對比腳本：reuse `scripts/_temp_analyze_s3s_cool_ab.py` pattern
5. 出對比 report:
   - Net / PF / Sharpe / MDD 對比
   - 6-layer exit 分布（新增 SX_VS_Reversal 看占比）
   - 28 個 macro events 兩版本 PnL 對照
   - 2024-08-02 / 2025-04-07 / 2026-06 月初 case 細節

---

## 四、v2.0 預設 inputs（**參考**）

```
BBLen                    = 45
BBStd                    = 2.0
BWLookback               = 120
BWPctile                 = 30
ATR_Len                  = 14
StopATRMult              = 2.75
TargetATRMult            = 10.0       ⭐ v2.0 (was 3.5)
MaxBars                  = 35
UseMidExit               = True
MidExit_MinBars          = 2
Cooldown_Days            = 1
SP_Trigger_ATRMult       = 1.5
SP_Retain_Pct            = 67         ⭐ v2.0 (was 70)
Use_Reversal_Exit        = True       ⭐ v2.0 NEW
Reversal_LowerWick_Mult  = 2.0        ⭐ v2.0 NEW
Reversal_BullBody_Pct    = 0.7        ⭐ v2.0 NEW
Holiday_Flat_Time        = 415
Registry_Valid_Until     = 1270101
Manual_Kill_Switch       = False
Settlement_Flat_Time     = 1230
```

---

## 五、v1.2 baseline 數據（**對比基準**）

```
Cool=1 Net:    +552,200
PF gross:      1.18
Sharpe:        0.30
MDD:           -52%
Trades:        185
5-layer exit:
  TP   21  +1,479,400  100%
  SP  112  +1,979,800   86%
  SL   43  -2,495,800    0%
  Mid   7    -380,400    0%
  Settlement 1  0
```

---

## 六、預期觀察重點

| 維度 | v1.2 | v2.0 預期 |
|------|------|---------|
| Net | +552K | ? (預期持平或略高) |
| PF | 1.18 | ? |
| MDD | -52% | ? (希望改善) |
| **新 SX_VS_Reversal** | (無) | ? 筆 / WR / PnL |
| TP 觸發頻率 | 21 筆 | 應 < 5 筆 (TP=10 太遠很少觸發) |
| SP 占比 | 112 筆 | 應 ↑ (TP 移除後 trail 接管) |
| 2024-08-02 BoJ | +254K | 預期 +250~+400K |
| 2025-04-07 | +278K TP + -206K SL | TP 不觸發, 看 Reversal/SP |
| 2026-06 月初 | (用戶提到的 case) | 預期被 Reversal 捕捉 |

---

## 七、禁忌（**避免再犯 v1.3 教訓**）

1. ❌ **不主動再改 v2.0 .pla**（先等用戶 backtest，看結果再討論）
2. ❌ **不 fix Section 12 cooldown**（v1.2 已 FROZEN 接受 limitation）
3. ❌ **不加更多 input** 除非用戶 explicit request
4. ❌ **不自動 GO/KILL**，等用戶 explicit instruction
5. ❌ **不發明新策略名稱** (Rule #14)
6. ❌ **不違反 Lesson L24** (不加 event filter)

---

## 八、今日 commit 軌跡

```
923d025  S3_S v2.0 EXPERIMENTAL: ride-to-end + K-pattern reversal exit
```

（其他 25+ commits 是筆電端昨晚 L3/L4/L5 cleanup，跟 S3_S 無關）

git 狀態: clean, all pushed to origin/main

---

## 九、相關文件

### v2.0 本身
- `.pla`: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v2.pla` (719 LOC)
- Header CHANGELOG 含完整 design rationale

### v1.2 對比基準
- `.pla`: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort.pla` (658 LOC, FROZEN)
- 分析: `extreme_event_coverage_20260624.md`
- 已 promote 到 `strategies/live_simulation/S3_VolSqueezeLong*` (S3_L sibling)

### 分析腳本（可 reuse for v2.0）
- `scripts/_temp_analyze_s3s_baseline.py` (single backtest analysis)
- `scripts/_temp_analyze_s3s_cool_ab.py` (A/B comparison framework)
- `scripts/_temp_analyze_s3s_extreme_coverage.py` (macro events coverage)
- `scripts/_temp_analyze_s3s_extreme_with_exits.py` (per-event exit details)

### 規範
- `CLAUDE.md` Rules #11-#15
- `docs/policies/OFFICIAL_ROADMAP.md`
- `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md`

---

## 十、明天 Action

```
筆電端 Claude:
  1. git pull
  2. 讀本檔
  3. 等用戶 v2.0 xlsx
  4. 跑 v1.2 vs v2.0 對比分析
  5. 出對比 report
  6. 不主動 GO/KILL，等用戶決定下一步
```

**晚安。明天筆電端見。**
