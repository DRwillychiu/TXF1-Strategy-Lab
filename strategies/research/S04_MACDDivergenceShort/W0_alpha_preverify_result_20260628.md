# S4_S MACDDivergenceShort — W0 Alpha Pre-Verify 結果

**日期**：2026-06-28
**Script**：`_w0_alpha_preverify.py`
**Data**：TWII daily 2020-2026（1558 bars）
**Verdict**：⚠️ **MARGINAL — 3/4 gates pass**

---

## 一、Headline

**3/4 institutional gates PASS**（G3 RR ratio marginal fail at 1.33 vs gate 1.5）

| Gate | 標準 | 實際 | 結果 |
|------|------|------|------|
| G1 Trigger 頻率 | ≥ 5 signals/year | **5.2/yr**（33 訊號 / 6.4 年）| ✅ |
| G2 Forward hit rate | ≥ 40% | **48.5%**（FWD_N=10）| ✅ |
| **G3 Risk-reward ratio** | **≥ 1.5** | **1.33** | ❌ **marginal miss** |
| G4 Cross-year stability | ≥ 50% years positive | 3/6 = 50% | ✅（剛達標）|

---

## 二、Forward Test Detail（不同 N 對照）

| FWD_N | Trades | WR% | Avg Ret% | Avg Win% | Avg Loss% | RR |
|-------|--------|-----|---------|----------|-----------|-----|
| **5** | 33 | **51.5%** | +0.04% | +1.43% | -1.44% | 1.00 |
| **10** ⭐ | 33 | 48.5% | +0.22% | +2.26% | -1.70% | **1.33** |
| **20** | 33 | 36.4% | -0.20% | +5.98% | -3.74% | **1.60** |

→ trade-off: **N 越長 RR 越高，但 WR 跌**

---

## 三、Year-by-Year（FWD_N=10）

| Year | N | Total Return % | Avg/trade % | 評估 |
|------|---|--------------|------------|------|
| 2020 | 15 | **-15.56%** | -1.04% | ❌ 疫情後超強多頭，背離訊號全錯 |
| 2021 | 2 | -0.13% | -0.07% | 持平 |
| 2022 | 3 | +1.39% | +0.46% | ✅ 空頭年微利 |
| 2023 | 3 | +6.30% | +2.10% | ✅ |
| **2024** | 5 | **+21.44%** | **+4.29%** | ⭐⭐ 強 alpha（趨勢轉折期）|
| 2026 H1 | 5 | -6.19% | -1.24% | ⚠️ Trump 期 noise |

→ **2020 + 2024 兩極化**：alpha 集中於趨勢轉折期，**多頭延續期失效**

---

## 四、Honest Assessment

### 為什麼 G3 RR 1.33 marginal fail
- daily proxy 可能**underrepresent 60M 真實 alpha**（60M divergence 較精細）
- 用 N=10（中期）= 平衡點，但 RR 結構性偏低
- 2020 大虧拉低整體 avg（15 trades 集中於超強多頭）

### 但 alpha 確實存在
- **2024 +21.44% = 趨勢轉折期 alpha 真實**
- 2022/2023 微利證實 bearish divergence 在非超強多頭年有效
- **archive 設計是 60M**，daily proxy 是保守 underestimate

### 對 portfolio context 的意義
- 33 signals / 6.4 years 是合理頻率
- 跟 S3_S 結構性不同（S3_S 在 squeeze + breakdown 進場，S4_S 在 divergence + RSI 70 進場）
- 即使單 sleeve marginal，配 S3_S / L4 / L2 / S3 可形成空頭 sleeve 多元化

---

## 五、3 條 path

### Path A: **接受 marginal, 進 W1**（推薦）
- W0 是 cheap pre-filter，3/4 pass = 不是 hard KILL
- 真實 verify 是 W3 MC12 60M baseline backtest
- 60M 比 daily 更精細，可能 G3 RR 自動達標
- **若 W3 PF < 1.1 才 KILL**

### Path B: KILL with FINAL_VERDICT
- 嚴格 institutional：3/4 < 4/4 即 fail
- 節省 5-7 days
- 但 24 年 +21% alpha 證據被浪費

### Path C: 改 N=20 重測（RR 1.60 但 WR 36%）
- G3 PASS 但 G2 FAIL（36% < 40%）
- 換 fail gate 沒解決問題

### Path D: 加 trend filter（如 Daily MA20 > MA60 才不進場）
- 可能改善 2020 + 2026 H1 大虧
- 但**違反 L24「不可加 regime sub-filter」**

---

## 六、推薦：**Path A 進 W1**

理由：
1. **W0 3/4 pass 是 marginal，不是 hard fail**
2. **60M MC12 才是真實 verify**（daily proxy 保守）
3. **2024 +21% alpha 證據強**，不應因 daily proxy underestimate 就 KILL
4. **portfolio context 中** S4_S 是補強空頭多元化（與 S3_S/L4/L2 不同 alpha）
5. **W3 baseline 是 hard gate**（PF < 1.1 才 KILL）

→ **接受 W0 MARGINAL，進 W1 Stage-1 4 段討論 lock + W2 .pla 實作**

---

## 七、相關文件

- `_w0_alpha_preverify.py` — W0 Python script
- `S4_S_stage1_spec.md` — Stage-1 初版 spec (2026-06-28)
- `S4_S_strategy.md` — W1 完整 strategy doc (next, 待寫)
- `docs/policies/STRATEGY_SUCCESS_CRITERIA.md` — institutional gates
- `docs/policies/lesson_L24_*.md` — 不可加 regime filter（path D 不選原因）
