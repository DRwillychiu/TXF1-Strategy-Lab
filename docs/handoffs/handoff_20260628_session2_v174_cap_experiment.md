# Handoff 2026-06-28 Session 2 — v1.7.4 Hard SL Cap 實驗 + Roadmap Override

**Session 結束時間**：2026-06-28 晚（user 累了，明日筆電端繼續）
**主要進度**：8 commits, 7 新策略 + ROADMAP override + v1.7.4 EXPERIMENTAL cap 100 backtest
**待 user 明日決定**：cap sweet spot (150/200/250) 找 final value

---

## 一、今日重大里程碑（8 commits chronological）

| # | Commit | 內容 |
|---|--------|------|
| 1 | `0b752c6` | v1.7.3 isolated WFA FAIL verdict（KILL → 回 Round 1）|
| 2 | `2a1c210` | v1.7.3-PROD initial promote → live_simulation/ |
| 3 | `dae9da6` | v1.7.3-FINAL refine（BWPctile 25, SlowMA 40）+ S3_S BOSS_VIEW 首份 + template |
| 4 | `f18b742` | 補 7 份 BOSS_VIEW（L1-L5 + S1 + S3 + S3_L），9/9 全策略覆蓋 |
| 5 | `a12cfb7` | OFFICIAL_ROADMAP override（加 S16_MACrossShort + S4_S 跳 S4_L）|
| 6 | `0e3da9d` | S4_S MACDDivergenceShort W0 + W1（MARGINAL 3/4 PASS）|
| 7 | `1e05307` | v1.7.4 EXPERIMENTAL Hard SL Cap 設計 + .pla |
| 8 | (本檔) | v1.7.4 cap 100 首次 backtest 結果 + handoff |

---

## 二、S3_S 全進度 timeline

```
v1.7.1 Round 1     ✅ 8/8 stage-2 / 8/9 WFA / 9/10 W5 PASS
                       但 Range PF 0.73 (sub-optimal)

v1.7.3-FINAL       ✅ PROMOTED to live_simulation/
                       band-reject 0.98-1.05 規避 Range/WeakBull
                       29 trades / +1,013K / PF 3.95 / WR 82.8% / MDD -22.1%

v1.7.4 EXPERIMENTAL ⚠️ cap 100 太緊
                       32 trades / +750K (-26%) / PF 3.26 / WR 56.3% / MDD -13.1%
                       SP→SL 切換 8 筆 → 2026 H1 -432K 損失
                       MDD 改善 9pp 達成「控制賠」哲學
                       但 cap 過緊截斷 alpha
                       
明日 todo:           跑 cap 150/200/250 找 sweet spot (預期 cap 200)
```

---

## 三、v1.7.4 cap 100 honest 結論

### ✅ 達成
- MDD 改善 9pp（-22.1% → -13.1%）
- 單筆最大虧 -45K（vs -106K）
- Sortino +28%

### ❌ 代價
- Net -26%（-1.01M → +750K）
- WR 大跌 -27pp（83% → 56%）
- SL trades 暴增 4.3 倍（3 → 13）

### Root Cause
- Cap 100 點 < SP arm 距離（1.5 ATR ~ 290 點）
- → SP 還沒 arm 就先觸 cap SL
- → 8 筆原本 SP 鎖利 → 變成 SL 出場
- 跟 2026 H1 落差 -432K 完全吻合

### 結論
- cap 100 過緊，**不 promote**
- 需要 cap >= SP arm threshold（>= 290 點 才不傷 SP）
- 推測 sweet spot 在 200-250 點範圍

---

## 四、明日筆電端 todo（user resume 入口）

### Step 1: Pull git
```bash
cd C:/tmp/TXF1-Strategy-Lab
git pull origin main
```

### Step 2: 讀今日 final files
```
strategies/research/S03_VolSqueezeShort/v174_HardSLCap_spec.md
strategies/research/S03_VolSqueezeShort/v174_cap100_result_20260628.md
strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v174_EXPERIMENTAL.pla
docs/handoffs/handoff_20260628_session2_v174_cap_experiment.md (本檔)
```

### Step 3: MC12 backtest 3 組對照
**Chart setup**：Data1=60M / Data2=Daily / IOG=false / MaxBarsBack=1000

| 組別 | SL_Hard_Cap_Pts | 其他 22 個 inputs |
|------|----------------|-----------------|
| **D** | **150** | 同 v1.7.3-FINAL |
| **E** ⭐ | **200** | 同 v1.7.3-FINAL |
| **F** | **250** | 同 v1.7.3-FINAL |

### Step 4: 命名輸出
```
TXF1  VolSqueezeShort_v17 v174_D_cap150.xlsx
TXF1  VolSqueezeShort_v17 v174_E_cap200.xlsx
TXF1  VolSqueezeShort_v17 v174_F_cap250.xlsx
```

### Step 5: 傳 3 個 xlsx 給 Claude
→ 我做 5 組完整對比（含 v1.7.3 baseline + cap 100 + 150/200/250）
→ 推薦 final cap 值
→ 若 sweet spot 找到 → 進 W4 WFA verify → promote v1.7.4

---

## 五、其他待處理項目（順位低）

### Task #136 S16_MACrossShort
- 等 S4_S 完成才啟動（Rule R-3 不可平行開發）
- Stage-1 spec 已寫，待 W0 alpha pre-verify

### Task #135 S4_S MACDDivergenceShort
- W0 MARGINAL 3/4 PASS
- W1 strategy.md 已寫
- 待 W2 .pla 實作（暫緩，先 focus S3_S v1.7.4）

### 全 portfolio SL audit (long-term)
- L2/L4/S3 是否有同樣 SL 過遠問題
- 等 v1.7.4 sweet spot 確認後 rollout

---

## 六、Status snapshot

| 項目 | 狀態 |
|------|------|
| live/ 5 隻策略 | ✅ 全有 BOSS_VIEW + 實盤運行 |
| live_simulation/ 4 隻策略 | ✅ S1 / S3 / S3_L / **S3_S v1.7.3-FINAL** 全有 BOSS_VIEW |
| research/ S4_S | 🔵 W0 + W1 done, W2 待 (priority 暫降) |
| research/ S16 | 🟡 Stage-1 done, 等 S4_S |
| research/ S03 v1.7.4 | 🟡 cap 100 = sub-optimal, cap 200 待 user 跑 |
| OFFICIAL_ROADMAP | ✅ 更新含 S16 + S4_S 跳號 override |
| Git sync | ✅ 100% pushed |

---

## 七、Token & 時間使用

- 今日 session: ~ 8 hr+
- 8 commits / 1500+ insertions
- 3 並行 Explore agents（research L1-L5 + S1/S3/S3_L）
- 1 Python script (S4_S W0)
- Major: S3_S v1.7.3 promote + 9 BOSS_VIEW + ROADMAP override + v1.7.4 探索

---

## 八、好好休息

今日完成 8 commits，全策略 BOSS_VIEW 100% 覆蓋，新增 S4_S + S16 排程，v1.7.4 探索完成。

**v1.7.3-FINAL 仍是穩定生產版本**（live_simulation 未動），v1.7.4 是 EXPERIMENTAL 不影響部署。

明日筆電端拿到 3 個 xlsx 後 ~10 分鐘可決定 final cap 值。

晚安。
