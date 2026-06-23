# S3_S VolSqueezeShort — Progress Handoff (2026-06-23 桌機 → 筆電端)

**寫於**：2026-06-23 桌機端 session 結束
**收件人**：2026-06-24 (or after) 筆電端 Claude
**狀態**：✅ **W2 .pla v1.0 ready** — 等用戶 MC12 baseline backtest

---

## 一、今日 session 完成

### 1. S3_L 升等 (research → live_simulation)
- W4 Rolling WFA 9 windows 分析: 6/9 PASS, Mean WFE 82.5%
- W5 10-dim institutional eval: 7/10 PASS, 2 ⚠️ explainable, 1 DD clustering event-level acceptable
- Promoted to `strategies/live_simulation/S3_VolSqueezeLong.pla` + DEPLOYMENT.md
- annotated.md 補完 (13 sections, ~900 行)
- Caveats: portfolio 5% cap + 等 S3_S 配對

### 2. Lesson L24 codified
- **「Risk overlay 不可削 alpha source」**
- 起源: 用戶否決 Pre-event Flat 提議
- 文件: `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md`
- 累計 L1-L24

### 3. strategies/ 完整整理 (C plan)
- research/README.md 更新 (廢除雙軌, 反映 S3_L promoted, S3_S CURRENT)
- 刪 live/powerlanguage/ + 2026-W24/ 空資料夾
- _temp_offRoadmap_2026Q2/ 35 個 files 整理: 3 valuable JSONs → backtest/results/portfolio/, INDEX 寫到 docs/archive/, 32 files 刪
- L4_ConsolidationShort_review.md 補完 (institutional 9 層審查)

### 4. S3_S VolSqueezeShort 啟動
- Stage -1 完整 4 段討論 + 4 follow-up Q&A
- W2 .pla v1.0 寫好 (532 LOC, ASCII clean, R-6 short mirror)

---

## 二、S3_S .pla v1.0 設計核心（**筆電端必讀**）

**位置**: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort.pla`

### R-6 short mirror diffs vs S3_L

| Item | S3_L | S3_S |
|------|------|------|
| Direction | Long | **Short** |
| Entry trigger | `Close > Upper` | **`Close < Lower`** |
| Entry order | `buy` | **`sell short`** |
| Exit order | `sell` | **`buy to cover`** |
| TP price | `Entry + ATR x N` | **`Entry - ATR x N`** |
| SL price | `Entry - ATR x N` | **`Entry + ATR x N`** |
| Mid exit | `Close < Mid` | **`Close > Mid`** |
| MarketPosition | `= 1` | **`= -1`** |
| SetStopLoss guard | `MP <= 0` | **`MP >= 0`** (Rule #12 short) |
| Labels | `LE_VS_/LX_VS_` | **`SE_VS_/SX_VS_`** |

### 4 short-customized inputs（**NOT mirrored**, 用戶 Q3 ruling）

| Input | S3_L | S3_S | 原因 |
|-------|------|------|------|
| TargetATRMult | 8.0 | **3.5** | Short panic 快速下殺後盤整，遠 TP 反而回吐 |
| MaxBars | 70 | **35** | Short 持倉短（6h-2 days vs Long 多天）|
| MidExit_MinBars | 3 | **2** | 更積極反彈出場 |
| Cooldown_Days | 1 | **0** | 用戶 ruling: SL 控風險，無需日限；W3 A/B 驗證 |

### Mirrored inputs (S3_L Phase 3 best)
- BBLen=45, BBStd=2.0, BWLookback=120, BWPctile=30 (squeeze 偵測對稱)
- ATR_Len=14, StopATRMult=2.75 (SL 對稱)

---

## 三、用戶手動 MC12 回測（**待執行**）

### Step 1: Baseline backtest
- MC12 載入 `S3_VolSqueezeShort.pla`
- Data1 = TXF1 60M (sole feed)
- Strategy properties: 1M init / 1 contract / 1000 RT slippage
- 區間: 2020-01-20 ~ 2026-06-XX (同 S3_L)
- Inputs 全用 v1.0 default (預設已是 Phase 1 baseline)
- 匯出 xlsx

### Step 2: A/B Cooldown test
- Cooldown_Days 改 1 再跑一次
- 匯出第二份 xlsx
- 對比兩者 PF / Sharpe / DD / trade count

---

## 四、筆電端 Claude SOP（2026-06-24+）

```
1. git pull origin main 確認同步
2. 讀本檔 progress_20260623_handoff.md
3. 等用戶上傳 baseline xlsx (Cooldown=0)
4. 完整分析（同 S3_L Phase 1 風格）：
   - 績效指標表
   - 出場標籤分布 (TP/Mid/TimeStop/SL/SX_VS_*)
   - 跨年穩定性
   - 跟 S3_L 對比（hedge value）
   - 2026-04-02 那筆 (S3_L 虧 124K) S3_S 應抓到對應賺
   - 2022 bear regime / 2024 Q3-Q4 vol-down regime 表現
5. 等用戶上傳 A/B Cooldown=1 xlsx
6. A/B 對比 → final default decision
7. 進 W4 WFA 規劃 (IS 2y / OOS 6m / step 6m, 9 windows)
8. 不主動決定，等用戶 explicit instruction
```

---

## 五、預期 backtest profile（**先有 mental model**）

| 指標 | 預期範圍 | 健康判斷 |
|------|---------|---------|
| Trade count | 50-100 / 6 yr | < 30 警示 (TXF1 bear 少) |
| PF gross | 1.0-1.5 | < 1.0 = KILL gate |
| PF adj (含滑價) | 0.9-1.3 | < 0.9 警示 |
| Sharpe (年化) | 0-0.5 | < 0 = KILL gate |
| Max DD % | 10-25% | > 25% 警示 |
| WR | 35-50% | (short bias 較低正常) |
| **vs S3_L correlation** | **< 0.3** | > 0.5 = hedge 效果差 |

**關鍵 acceptance gate**：portfolio S3_L + S3_S Sharpe **>** S3_L 單獨 Sharpe → 證明 R-6 配對價值

---

## 六、Stage -1 用戶 ruling 摘要（**避免重新討論**）

### 用戶今日 4 個 ruling (2026-06-23)
1. **操作週期 60M**（不改 3M; 短週期版本走 S13 VolCollapseShort, batch03 已排程）
2. **Cooldown_Days=0** 預設, W3 A/B vs Cool=1 驗證
3. **TargetATR/MaxBars/MidExit_MinBars 不 mirror S3_L** (因 short panic 結構不同)
4. **不加 strategy-level event filter** (per Lesson L24, 用戶否決 Pre-event Flat)

### 不要再提的選項
- ❌ Pre-event Flat (L24 violation)
- ❌ 跳 OFFICIAL_ROADMAP 開 S13 (Rule #14)
- ❌ 改週期 (R-6 對稱性破壞)
- ❌ 改 Long-only direction (R-6 violation)
- ❌ 加 GA optimize 全部 inputs (先 baseline 看再決定)

---

## 七、相關文件連結

### S3_S 本身
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort.pla` (v1.0)
- `strategies/research/S03_VolSqueezeShort/README.md` (Stage -1 完整 4 段)

### S3_L 參考（R-6 對手）
- `strategies/live_simulation/S3_VolSqueezeLong.pla` (v1.1)
- `strategies/live_simulation/S3_VolSqueezeLong_annotated.md`
- `strategies/live_simulation/S3_VolSqueezeLong_DEPLOYMENT.md`
- `strategies/research/S03_VolSqueezeLong/W5_10dim_evaluation.md`
- `strategies/research/S03_VolSqueezeLong/progress_20260622_phase3_handoff.md`

### 規範
- `docs/policies/OFFICIAL_ROADMAP.md` (R-6 + Rule #14)
- `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md` (新)
- `CLAUDE.md` Rules #11-#15

### Portfolio data
- `backtest/results/portfolio/portfolio_pnl_6sleeves_2019-2026.json` (重算 correlation 用)

---

## 八、今日 commit 軌跡

```
05dab02 S3_S VolSqueezeShort v1.0 .pla
020af80 strategies/ 完整整理 (C plan) + S3_L annotated.md + L4 review.md
07d96e2 S3_L live_simulation copy: sync to latest v1.1 ASCII-clean
d1fe1e8 S3_L W5 PASS → promote to live_simulation + L24 codify + S3_S 啟動
```

git 狀態: clean, all pushed to origin/main

---

## 九、明日筆電端開機 SOP

```bash
# 1. 確認同步
cd ~/Desktop/TXF1-Strategy-Lab  (或筆電端 path)
git pull origin main

# 2. 讀 handoff
cat strategies/research/S03_VolSqueezeShort/progress_20260623_handoff.md

# 3. 等用戶 baseline xlsx → 分析
# 4. 等用戶 Cooldown A/B xlsx → 對比
# 5. 進 W4 WFA
```

**禁忌**：
- 不要自己 KILL/GO（用戶 explicit decision only）
- 不要跳過 W3 A/B (Cooldown 用戶要實證決定)
- 不要重新討論 Stage -1（已 sealed）
- 不要建議 Pre-event Filter (L24 violation)

---

**晚安。筆電端見。**
