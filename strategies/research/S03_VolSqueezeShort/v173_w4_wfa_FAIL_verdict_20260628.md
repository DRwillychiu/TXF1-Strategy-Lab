# S3_S v1.7.3 Band-Reject — W4 WFA FINAL VERDICT (FAIL)

**日期**：2026-06-28
**版本**：v1.7.3 + Stage 1 GA best (FastMA=15 / SlowMA=80 / BWPctile=30)
**狀態**：❌ **W4 WFA FAIL (2/9 windows pass) → KILL**
**動作**：回 v1.7.1 Round 1 promote

---

## 一、Headline

| 對照 | v1.7.1 Round 1 | **v1.7.3 band-reject** |
|------|---------------|----------------------|
| W4 WFA Windows PASS | **8/9** | **2/9** ❌ |
| Median WFE | +103.7% | **+37.9%** ❌ |
| Mean OOS PF | 1.72 | **0.79** ❌ |
| Total OOS Net | +2.13M | +1.15M |
| Total OOS Trades | 275 | **76** (-72%) |
| Avg trades/window | 30.6 | **8.4** (sample 不足) |

→ **v1.7.3 institutional W4 gate FAIL（3/4 aggregate gates fail）**

---

## 二、Per-Window Detail

| W | IS N | IS PF | OOS N | OOS PF | OOS Net | WFE | Status |
|---|------|------|-------|--------|---------|-----|--------|
| W1 | 23 | 2.77 | 11 | +1.69 | +72,200 | +61.1% | ✅ PASS |
| W2 | 36 | 2.64 | 22 | +2.38 | +175,400 | +90.0% | ✅ PASS |
| W3 | 32 | 2.41 | 5 | -0.87 | -4,800 | -36.2% | ❌ FAIL (WPS) |
| W4 | 28 | 3.27 | **2** | 0 | +61,000 | 0% | ❌ FAIL (WPS) |
| W5 | 20 | **6.93** ⚠️ | **2** | 0 | +60,400 | 0% | ❌ FAIL (WPS) |
| W6 | 27 | 3.65 | 8 | +1.39 | +48,000 | +37.9% | ❌ FAIL (W) |
| W7 | 13 | 2.25 | 12 | +1.11 | +50,800 | +49.3% | ❌ FAIL (W) |
| W8 | 8 | 2.90 | 9 | +1.39 | +148,000 | +47.9% | ❌ FAIL (W) |
| W9 | 10 | 2.11 | 5 | 0 | +536,800 | 0% | ❌ FAIL (WP) |

**Pass codes**: W=WFE>50 fail, P=OOS PF>1 fail, S=OOS Sharpe>0 fail

---

## 三、Side-by-Side vs v1.7.1 Round 1

| W | Round 1 OOS Net | v1.7.3 OOS Net | Winner |
|---|---------------|---------------|--------|
| W1 | +220,000 | +72,200 | Round 1 |
| W2 | +554,000 | +175,400 | Round 1 |
| W3 | +252,400 | -4,800 | Round 1 |
| W4 | +329,000 | +61,000 | Round 1 |
| W5 | +80,800 | +60,400 | Round 1 |
| W6 | +109,000 | +48,000 | Round 1 |
| W7 | -63,600 | +50,800 | **v1.7.3** ⭐ |
| W8 | +320,000 | +148,000 | Round 1 |
| W9 | +331,800 | +536,800 | **v1.7.3** ⭐ |
| **Total** | **+2,133,400** | **+1,147,800** | **Round 1 (+86%)** |

→ Round 1 在 **7/9 windows 勝**，僅 W7 (Trump alpha gap) + W9 (2026 H1) v1.7.3 勝

---

## 四、Root Cause Analysis — 4 個失敗因素

### 因素 1: BlockRange + BlockWeakBull 共同削掉 72% sample
- Round 1: 275 OOS trades
- v1.7.3: **76 OOS trades**
- Avg trades/window: 30.6 → **8.4**
- 6 個 OOS windows 樣本 ≤ 9 → WFE 計算 noise dominate

### 因素 2: IS PF 異常偏高 = over-fit warning
- W5 IS PF **6.93** = alpha cluster 過擬合警示
- Mean IS PF ≈ 3.20 但 IS sample 只 8-36 → fragile

### 因素 3: 4 windows (W4/W5/W9) OOS PF = 0 anomaly
- OOS 2-5 trades 全賺但 MC PF 無法計算
- PF undefined → automatic gate fail
- 統計上不顯著

### 因素 4: L24 教訓直接驗證
- Lesson L24: 「regime sub-filter 削 alpha source」
- v1.7.3 = Range + Weak Bull 雙重 block
- **OOS 76 / Round 1 275 = 28%** = 殘酷 sample loss
- 跟 v1.5 過擬合 pattern 一致：漂亮 IS 但 OOS sample 不足 → WFA fail

---

## 五、Lesson 學習（codify 為 L25 候選）

### Lesson L25 候選：**「Regime band-reject filter 在小 sample 策略上死亡」**

**Why**:
- Band-reject (Block specific zones) 看似 surgical filter
- 實際在 sample < 100 的策略 (S3_S 31 trades) 等於 50%+ trades drop
- WFA 9 windows 每窗 6 月 OOS 只剩 1-5 trades = statistical noise
- IS-OOS divergence 必然發生

**How to apply**:
- 若策略 full-period sample < 100，不可加 regime sub-filter
- 若一定要 filter，先確認 sample drop < 30%
- 替代方案：portfolio cap 風控（v1.7.1 Round 1 的選擇）

### 整合到 lessons archive
- `docs/policies/lessons/lesson_L25_regime_filter_kills_small_sample.md`

---

## 六、Final Decision

### KILL v1.7.3, 回 v1.7.1 Round 1
1. **v1.7.1 Round 1 已通過 8/8 + 8/9 WFA + 9/10 W5**
2. **v1.7.3 削掉真實 alpha** (2024 +435K → +78K, sample 78% loss)
3. **Round 1 Range -259K** 可用 portfolio cap 5% 吸收
4. **L24 + L25 雙重教訓**

### 動作
- v1.7.3 .pla 保留 archive（學習用）
- **生產用 v1.7.1 Round 1**
- 進 promote SOP

---

## 七、相關文件

- `S3_VolSqueezeShort_v17.pla` (v1.7.3 archive，後續 promote 使用 v1.7.1 Round 1 inputs)
- `v17_round1_evaluation_20260627.md`
- `v17_round1_w4_wfa_20260627.md`（8/9 PASS）
- `v17_round1_w5_institutional_20260627.md`（9/10 PASS）
- `lesson_L24_no_event_filter.md`（band-reject 違反此）
- 候選 `lesson_L25_regime_filter_kills_small_sample.md`（本案產出）
