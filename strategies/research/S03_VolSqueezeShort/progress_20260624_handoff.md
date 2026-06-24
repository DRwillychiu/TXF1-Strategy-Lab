# S3_S Progress Handoff (2026-06-24 桌機 → 筆電端)

**狀態**：✅ **v1.2 FROZEN，極端事件覆蓋率分析完成**，等明天筆電端進 Phase 2 GA
**收件人**：2026-06-25+ 筆電端 Claude
**最新 commit**：`ac1096a`

---

## 一、今日完成

### 1. v1.0 → v1.1 加入 Layer 2 SP（保本層）
- 用戶筆電端先寫 annotated.md 升級到 5-layer exit
- .pla 加 SP_Trigger_ATRMult / SP_Retain_Pct inputs + v_SP_Armed/Peak/Floor variables
- commit `d094280`

### 2. v1.1 → v1.2 BUGFIX (Section 8)
- 用戶跑 baseline + Cool=1 → 100% 相同！
- 發現 Section 8 cooldown reset 邏輯有 contradiction (`Date <> v_LastExit_Date` 多餘條件)
- 移除多餘條件 → Cool=0 vs Cool=1 真實有差
- commit `78a9208`

### 3. v1.2 → v1.3 BUGFIX2 (Section 12) → REVERTED
- 用戶 v1.2 A/B 重跑：Cool=1 (+552K) 比 Cool=0 (-44K) 好很多
- 但 2025-04-07 case (same-bar entry+exit) 仍漏
- 嘗試 v1.3 用 EntriesToday() fix → **失敗** (Net 跌 -181K，MDD -7%，trades +10)
- 用戶要求 freeze → revert v1.3 回 v1.2
- commit `295ff2f` (v1.3 attempt) + `1c4b0e4` (revert to v1.2 FROZEN)

### 4. v1.2 FROZEN 極端事件覆蓋率分析
- 對 41 個 macro events + 65 個 TWII -2% 大跌日做 coverage check
- 28/41 = 68% macro 覆蓋 / 44/65 = 67.7% -2% 覆蓋
- 每個抓到 event 對應 trade 的 exit signal 標出
- 識別 3 個關鍵 alpha gap（2025-04-09 / **2026-04-02** / 2020-03-19）
- 寫 `extreme_event_coverage_20260624.md`
- commit `ac1096a`

---

## 二、v1.2 FROZEN 正式版基準（**Phase 2 GA baseline**）

### 績效（Cool=1）
```
Net Profit:  +552,200 NTD
PF gross:    1.177
PF adj:      -0.952 (滑價吃光 risk-adj alpha) ⚠️
Sharpe:      0.299
MDD:         -52% ⚠️ (超出 25% institutional gate)
Trade count: 185
Win Rate:    63.2%
```

### 5-Layer Exit 分布
```
SX_VS_TP   21  +1,479,400  100%
SX_VS_SP  112  +1,979,800   86% ← 主力 alpha
SX_VS_SL   43  -2,495,800    0%
SX_VS_Mid   7    -380,400    0%
SX_VS_Settlement  1  0
```

### 28 個抓到 macro events 的 trade-level exit 分布
```
TP   5  +566,400  100%  (一氣呵成下殺事件)
SP  30  +924,000   97%  (主力, 鎖峰值 70%)
SL   8  -546,400    0%  (進場錯)
Mid  2   -74,800    0%  (論點失效)
```

### 接受的 limitation
- **Section 12 cooldown imperfect**: same-bar entry+exit 不擋 (2025-04-07 case)
- **v1.4 改善方案** (v_TradedDate flag in Section 10) 列入 backlog
- **2026-04-02 完全漏抓**（R-6 hedge 失敗，需 Phase 2 GA 試解）

---

## 三、明天 (2026-06-25+) 筆電端入口

```bash
cd ~/Desktop/TXF1-Strategy-Lab    # 筆電端路徑
git pull origin main              # 同步雲端
cat strategies/research/S03_VolSqueezeShort/progress_20260624_handoff.md
cat strategies/research/S03_VolSqueezeShort/extreme_event_coverage_20260624.md
```

### 預計動作：進 Phase 2 GA

用戶最新 ruling：**接受 v1.2 FROZEN，進 Phase 2 GA**

筆電端 Claude SOP：
1. 確認用戶 ready 進 Phase 2
2. 給完整 GA 參數範圍（鏡像 S3_L Phase 1 流程）
3. 排除已凍結 inputs (Cooldown_Days)
4. GA pop 50 × gen 30-40，預估 5000-8000 組合
5. 等用戶 MC12 跑完 xlsx → 分析最佳組合

### Phase 2 GA 範圍 preview

| Input | Range | Step | 備註 |
|-------|-------|------|------|
| BBLen | 30-60 | 5 | 鏡像 S3_L Phase 1 範圍 |
| BWPctile | 20-40 | 5 | 加 35-40 試「半壓縮」抓 follow-through |
| StopATRMult | 2.0-3.5 | 0.25 | |
| TargetATRMult | 2.5-5.0 | 0.5 | 短 panic 結構 |
| MaxBars | 25-50 | 5 | |
| MidExit_MinBars | 1-4 | 1 | |
| SP_Trigger_ATRMult | 1.0-2.5 | 0.25 | Layer 2 新 input 優化 |
| SP_Retain_Pct | 50-80 | 10 | 鬆/緊 tradeoff |
| **排除** | Cooldown_Days, BBStd, BWLookback, ATR_Len, UseMidExit, all Priority 0 | — | 已凍結 |

詳細範圍 + GA 配置等用戶 confirm 進 Phase 2 後再給。

---

## 四、禁忌（**避免再犯**）

| 禁忌 | 來源 |
|------|------|
| ❌ 不再嘗試 fix Section 12 cooldown（v1.3 失敗教訓）| v1.2 FROZEN |
| ❌ 不加 Pre-event Flat / event filter | Lesson L24 |
| ❌ 不改 R-6 short-only direction | OFFICIAL_ROADMAP |
| ❌ 不發明新策略名稱 | Rule #14 |
| ❌ 自己 commit 不該由 fix 引發的改動（v1.4 v_TradedDate proposal 列 backlog 不主動做）|  |
| ❌ 不主動 KILL/GO，等用戶 explicit | discipline |

---

## 五、Backlog（未來再評估）

| 項目 | 觸發條件 |
|------|---------|
| v1.4 cooldown 重寫（v_TradedDate flag）| 若 Phase 2 GA 結果仍邊際，再評估 |
| 2026-04-02 R-6 hedge gap | Phase 2 GA 期間特別觀察 |
| Adj PF < 1 改善 | Phase 2 GA 後若仍 < 1 → KILL or 退役 |
| MDD -52% 縮減 | Phase 2 GA + position sizing 評估 |

---

## 六、今日 commit 軌跡

```
ac1096a  S3_S extreme event coverage (3 tables + exit details)
1c4b0e4  S3_S v1.3 REVERTED -> v1.2 FROZEN
295ff2f  S3_S v1.2 -> v1.3 BUGFIX2 (失敗實驗)
78a9208  S3_S v1.1 -> v1.2 BUGFIX Section 8
d094280  S3_S v1.0 -> v1.1 Layer 2 SP
fb38dae  S3_S annotated.md 全面補充 (筆電端前一日完成)
```

git 狀態：clean, all pushed to origin/main

---

## 七、相關檔案連結

### S3_S 本身
- `.pla` v1.2 FROZEN: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort.pla` (658 LOC, ASCII clean)
- annotated.md: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_annotated.md`
- README.md: `strategies/research/S03_VolSqueezeShort/README.md`
- **extreme coverage**: `strategies/research/S03_VolSqueezeShort/extreme_event_coverage_20260624.md` ⭐
- 本檔 (handoff): `strategies/research/S03_VolSqueezeShort/progress_20260624_handoff.md`

### 分析腳本
- `scripts/_temp_analyze_s3s_baseline.py` (baseline 績效 / 出場分布)
- `scripts/_temp_analyze_s3s_cool_ab.py` (A/B Cool 對比)
- `scripts/_temp_analyze_s3s_extreme_coverage.py` (macro events coverage)
- `scripts/_temp_analyze_s3s_extreme_with_exits.py` (per-event exit details)

### 規範
- `CLAUDE.md` Rules #11-#15
- `docs/policies/OFFICIAL_ROADMAP.md` (S3_S CURRENT)
- `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md`

---

**晚安。明天筆電端見。**
