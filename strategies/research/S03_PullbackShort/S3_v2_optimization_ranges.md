# S3_RapidPullbackShort_v2 — MC12 Optimization Parameter Sweep Guide

**Strategy**: `S3_RapidPullbackShort_v2`
**MC Load name**: `STRATEGY_GEN_S3_RapidPullbackShort_v2`
**Label prefix**: `SE_RPS_v2_` (entry short), `SX_RPS_v2_` (exit short)
**Document version**: 1.0
**Created**: 2026-06-20
**Author**: Strategy Lab
**Based on**: User Option B (2026-06-20) — preserve v1.1 thesis, shorten regime time-frame Daily → 60M.
**Status**: PRE-OPTIMIZATION — to be executed AFTER P0 pre-flight checklist passes

> **v2.0 變動**：Daily Tier 1 → 60M Tier 1 / TP 0.7→0.6 / SL ATR×4→×3 / TimeStop 24→18 bar / Entry cutoff 1230→1325
> **保留**：Tier 2 momentum (M1-M4)、Settlement_Flat、SetStopLoss、Holiday、Frozen SL、cooldown
> **延後**：夜盤（v2.1 加入）

---

## 0. Pre-flight Checklist (Block all optimization until DONE)

| 項 | 內容 | 狀態 |
|---|---|---|
| P0-1 | `verify_s3_v2.py` 結構驗證 100% PASS | ☐ |
| P0-2 | Rule #11 Settlement_Flat 已植入 `.pla` 並通過 verify | ☐ |
| P0-3 | Rule #12 P3b `SetStopLoss` 已植入並 verify | ☐ |
| P0-4 | 10-dim eval 對 baseline (default params) 已跑過，PF / Sharpe / MaxDD logged | ☐ |
| P0-5 | TXF1 5M Continuous data 2020-01-01 ~ 2026-06-20 已載入 MC12，bar count ≈ 120K 確認 | ☐ |
| P0-6 | TXF1 60M Continuous data 同期載入，bar count ≈ 30K 確認 | ☐ |
| P0-7 | MC12 Portfolio Trader「Auto-Trading OFF」確認（避免最佳化觸發實單） | ☐ |
| P0-8 | v1.1 baseline 結果記錄（PF gross 1.37、PF net -0.92、9 trades/yr）作對照組 | ☐ |

> 任一未勾，§3 以後流程一律不得啟動。

---

## 1. Optimization Philosophy

### 1.1 核心理念（沿用 v1.1）

1. **可被市場結構解釋的參數**（進場時間 850 / 平倉時間 1325）→ **永不掃描**
2. **訊號型參數**（MA 長度、RSI 門檻、ATR 倍數）→ **可掃描，分階段**
3. **出場型參數**（TP%、SL 倍數、Time Stop）→ **掃描目標 = 穩定 R:R，非極大化淨利**

### 1.2 v2.0 額外原則

4. **Tier 1 60M 尺度** ≠ **Tier 1 Daily 尺度**：threshold/distance 需重新校準，不能直接套 v1.1 範圍
5. **目標年交易次數 25-50**（v1.1 實測 9 太少）→ Coarse sweep 觀察 trade count，<10 視為過嚴
6. **基準對照 v1.1**：v2.0 Stage 2 結果必須 PF net > 0（v1.1 是 -0.92，超越就贏）

### 1.3 兩階段 GA 流程

```
Stage 1: Coarse Sweep
  ├── 範圍：寬區間（5-10 個離散值）
  ├── 目的：找 PF/Sharpe/trade-count 的「高原區」
  └── 警示：單一峰值 (spike) → 過擬合警報

Stage 2: Refine Sweep
  ├── 範圍：圍繞 Stage 1 最佳區域 ±1-2 step
  ├── 目的：在 plateau 內找穩健中心點
  └── 確認：plateau 寬度 ≥ 3 個連續 step
```

### 1.4 反過擬合三鐵則

1. **堅持 plateau 而非 spike**：最佳參數 ±1 step PF 掉 >15% → 過擬合，棄用
2. **單次最佳化最多 4 個參數同時掃**：>4 → 組合爆炸 + 過擬合風險倍增
3. **必過 Walk-Forward (WFE > 50%)**：純 IS 結果不得進 live_simulation

---

## 2. Per-Input Sweep Range Table

### 2.1 Tier 1 — Regime Gate (60M, Data2)  **★ v2.0 重點變動**

| Input | v1.1 (Daily) | v2.0 Default (60M) | Coarse Range | Refine Step | Sens | 備註 |
|-------|-------------|-------------------|--------------|-------------|------|------|
| `H60_FastMA_Len` | 20 | **20** | [10, 15, 20, 30] | ±5 around best | **HIGH** | 20 根 60M ≈ 20 hr ≈ 1 trading day |
| `H60_SlowMA_Len` | 60 | **60** | [40, 60, 80, 120] | ±10 around best | **HIGH** | 60 根 60M ≈ 60 hr ≈ 3 trading day；必須 > FastMA |
| `H60_RSI_Len` | 14 | **14** | [7, 14, 21] | ±2 around best | LOW | RSI 計算期；不建議大幅調 |
| `H60_RSI_Threshold` | 70 | **70** ⭐ | [55, 60, 65, 70, 75] | ±2 around best | **HIGH** | v2.0.2 LOCKED：27-trade opt 跟 v1.1 同回到 70 |
| `H60_RSI_Sustained_Bars` | 2 | **2** | [1, 2, 3, 4] | ±1 | **MED** | 每 bar = 1 hr，過大 → 觸發稀疏 |
| `H60_Dist_MA20_Pct` | 3.0 | **2.5** ⭐ | [1.0, 1.5, 2.0, 2.5, 3.0] | ±0.5 around best | **HIGH** | v2.0.2 LOCKED：27-trade opt 鎖 2.5（比 v1.1 3.0 略鬆）|

**Tier 1 約束**：`H60_FastMA_Len < H60_SlowMA_Len`（GA 須加 constraint）
**Tier 1 預期效果**：相較 v1.1 Daily Tier 1 (3.4/yr 觸發)，60M Tier 1 預估 30-60/yr regime watch 日（再經 Tier 2 5M momentum filter 後 25-50/yr 實際進場）

---

### 2.2 Tier 2 — Momentum Trigger (5M, Data1)  *（保留 v1.1，僅一個 default 微調）*

| Input | v1.1 Default | v2.0 Default | Coarse Range | Refine Step | Sens | 備註 |
|-------|-------------|--------------|--------------|-------------|------|------|
| `Consec_Red_Bars` | 3 | **3** | [2, 3, 4, 5] | ±1 | **HIGH** | 連續陰 K；越大訊號越少 |
| `EMA_Fast_Len` | 5 | **5** | [3, 5, 8, 10] | ±1 around best | **MED** | EMA 與斜率判動能反轉 |
| `ATR_Short_Len` | 5 | **5** | [3, 5, 8] | — | LOW | 不建議掃 |
| `ATR_Long_Len` | 20 | **20** | [14, 20, 30] | — | LOW | 不建議掃 |
| `ATR_Spike_Mult` | 1.3 | **1.1** ⭐ | [1.0, 1.1, 1.2, 1.3, 1.5] | ±0.1 around best | **HIGH** | v2.0.2 LOCKED：27-trade opt 鎖 1.1（比 v1.1 鬆，更易觸發）|
| `Pullback_Min_Pct` | 0.5 | **0.6** ⭐ | [0.2, 0.3, 0.4, 0.5, 0.6] | ±0.1 around best | **MED** | v2.0.2 LOCKED：27-trade opt 鎖 0.6（比 v1.1 略嚴）|
| `Pullback_Max_Pct` | 1.5 | **1.5** | [1.0, 1.5, 2.0, 2.5] | ±0.25 around best | **MED** | 距離 intraday high 上限 |

**Tier 2 約束**：`Pullback_Min_Pct < Pullback_Max_Pct`；`ATR_Short_Len < ATR_Long_Len`

---

### 2.3 Exit Tier  **★ v2.0.2 LOCKED defaults from 27-trade opt**

| Input | v1.1 Default | **v2.0.2 LOCKED** | Coarse Range | Refine Step | Sens | 備註 |
|-------|-------------|--------------------|--------------|-------------|------|------|
| `TP_Pct` | 0.7 | **1.0** ⭐ | [0.5, 0.6, 0.7, 0.8, 1.0, 1.2] | ±0.1 around best | **HIGH** | 27-trade opt 鎖定 1.0%（v2.0 試 0.6 過嚴）|
| `TP_MA_Len` | 20 | **20** | [10, 20, 30, 50] | ±5 around best | **MED** | EMA20 結構觸碰備援 TP |
| `TP_EMA20_MinBars` | 3 | **3** | [2, 3, 4, 6] | ±1 | **MED** | EMA20 backup 最少持倉 bar；防 fill-bar trap |
| `SL_ATR_Len` | 14 | **14** | [10, 14, 20] | — | LOW | ATR 計算基準 |
| `SL_ATR_Mult` | 4 | **3** ⭐ | [1.5, 2, 2.5, 3, 3.5] | ±0.5 around best | **HIGH** | 27-trade opt 鎖定 3，比 v1.1 的 4 收緊 |
| `Max_Bars_TimeStop` | 24 | **12** ⭐ | [12, 15, 18, 21, 24, 30] | ±3 around best | **MED** | 27-trade opt 鎖定 12 bar = **60 min**（大幅收緊）|

> ⚠️ v2.1 ATR Trailing SL layer **已 retired**（2026-06-20 backtest 證實不適合短週期反趨勢策略）。詳見 strategy.md §8 Decision Log。

**Exit Tier 配套邏輯**：
- TP 0.6% + SL ATR×3 (~0.44%) = R:R ≈ 1.36
- 比 v1.1 (TP 0.7% + SL ATR×4 ~0.58% = R:R 1.21) 略高
- Time stop 90 min 防止 90 min 內未到 TP/SL 的「猶豫部位」拖延

---

### 2.4 Entry Window (固定，不掃描)

| Input | v1.1 | v2.0 | 備註 |
|-------|------|------|------|
| `Entry_Open_Time` | 850 | **850** | 08:50 close bar (08:45 stamp 不存在) |
| `Entry_Cutoff_Time` | 1230 | **1325** ⚠️ | v2.0 widened to match Daily_Flat_Time |
| `Daily_Flat_Time` | 1325 | **1325** | 日盤強制平倉 |

---

### 2.5 Protection (Rule #11 / #12, 不掃描)

| Input | Default | 備註 |
|-------|---------|------|
| `Holiday_Flat_Time` | 245 | 02:45 holiday tail flat retry start |
| `Registry_Valid_Until` | 1270101 | TAIFEX-verified horizon |
| `Manual_Kill_Switch` | False | 緊急 kill switch |
| `Settlement_Flat_Time` | 1230 | 結算日 12:30 平倉 |

---

### 2.6 Diagnostic (logging-only, 不掃描)

| Input | v1.1 | v2.0 | 備註 |
|-------|------|------|------|
| `Log_HighConviction` | True | **True** | 印出 60M dist > threshold 日 |
| `HighConv_Threshold_Pct` | 5.0 | **2.5** ⚠️ | 60M scale (v1.1 Daily 5% ≈ 60M 2.5%) |

---

## 3. Recommended Stage 1 Coarse Sweep (Top 4 HIGH-sens params)

> 第一輪只掃 4 個 HIGH 敏感度參數，避免組合爆炸。

| 順序 | Input | Stage 1 Range | 組合數 |
|------|-------|---------------|-------|
| 1 | `H60_RSI_Threshold` | [55, 60, 65, 70, 75] | 5 |
| 2 | `H60_Dist_MA20_Pct` | [1.0, 1.5, 2.0, 2.5, 3.0] | 5 |
| 3 | `TP_Pct` | [0.4, 0.5, 0.6, 0.7, 0.9] | 5 |
| 4 | `SL_ATR_Mult` | [2.5, 3, 3.5, 4, 4.5] | 5 |

**Total combos**: 5 × 5 × 5 × 5 = **625** (GA pop=128, gen=5 約 30 min on i7)

**Stage 1 fitness function**：
```
Fitness = (PF_net × 0.5) + (Sharpe × 0.3) + (TradeCount / 30 × 0.2)
                                                ↑ 鼓勵 25-50/yr，過少或過多扣分
```

---

## 4. Recommended Stage 2 Refine Sweep

Stage 1 找到 best 後，圍繞 best ±1 step 跑：

| Input | Stage 2 Range example | 組合數 |
|-------|----------------------|-------|
| 4 個 Stage 1 best ±1 step | 3 × 3 × 3 × 3 | 81 |
| 加掃 `H60_RSI_Sustained_Bars` | [1, 2, 3] | × 3 |
| 加掃 `Pullback_Min_Pct` | [0.2, 0.3, 0.4] | × 3 |
| **Total** | | **729** |

---

## 5. Walk-Forward Validation (P2)

GA 找到 best 後，必過：
- IS: 2020-01-01 ~ 2022-12-31 (3 年)
- OOS: 2023-01-01 ~ 2026-06-20 (3.5 年)
- 步長: 6 個月
- **合格門檻**: WFE > 50% AND OOS PF > 1.0 AND 三市況皆 PF > 1.0

---

## 6. v1.1 vs v2.0 Baseline 對照

> Stage 2 完成後，必須將 v2.0 best params 跑出績效 vs v1.1 比較：

| 指標 | v1.1 baseline | v2.0 target | v2.0 actual (TBD) |
|------|--------------|-------------|-------------------|
| Trades/yr | 9 | 25-50 | ? |
| WR | 53.85% | 48-55% | ? |
| PF gross | 1.37 | 1.25-1.45 | ? |
| **PF net (含滑價)** | **-0.92 ❌** | **>1.0** ✅ | ? |
| Sharpe (年化) | 0.21 | 0.4-0.7 | ? |
| Max DD | 19.5% | <15% | ? |
| 2026 H1 集中度 | 54% | <35% | ? |

**v2.0 GO 條件**：PF net > 1.0 AND Sharpe > 0.4 AND 集中度 < 35%
**否則**：考慮 v2.1（加夜盤）或 v2.2（換 thesis）

---

## 7. Logging & Result Storage

```
optimization/
  reports/
    S3_v2_stage1_coarse_<YYYYMMDD>.csv
    S3_v2_stage1_summary_<YYYYMMDD>.md
    S3_v2_stage2_refine_<YYYYMMDD>.csv
    S3_v2_stage2_summary_<YYYYMMDD>.md
    S3_v2_walkforward_<YYYYMMDD>.json
    S3_v2_vs_v1.1_<YYYYMMDD>.md  ← 必填對照表
```

---

## 8. 參考

- [S3_RapidPullbackShort_v2.pla](S3_RapidPullbackShort_v2.pla) — v2.0 程式碼
- [S3_RapidPullbackShort.pla](S3_RapidPullbackShort.pla) — v1.1 baseline（保留供 A/B 對照）
- [S3_optimization_ranges_20260620.md](S3_optimization_ranges_20260620.md) — v1.1 ranges（參考格式）
- [docs/STRATEGY_RD_SOP.md](../../../docs/STRATEGY_RD_SOP.md) — 策略研發 SOP
- [docs/institutional_risk_framework_20260619.md](../../../docs/institutional_risk_framework_20260619.md) — 10 維度評估
