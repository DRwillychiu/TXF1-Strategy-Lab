# S3_RapidPullbackShort — MC12 Optimization Parameter Sweep Guide

**Strategy**: `S3_RapidPullbackShort`
**MC Load name**: `STRATEGY_GEN_RapidPullbackShort`
**Label prefix**: `SE_RPS_` (entry short), `SX_RPS_` (exit short)
**Document version**: 1.0
**Created**: 2026-06-20
**Author**: Strategy Lab (Auto + Ultracode)
**Status**: PRE-OPTIMIZATION — to be executed AFTER D7 volume verification

> 用戶指示 (2026-06-20)：「參數可經過 MultiCharts 最佳化找適合的參數」
> 此文件為 MC12 GA / WFO 最佳化的正式作戰手冊。所有 25–30 個 input 皆設計為可掃描，
> 但必須遵守反過擬合守則與分階段流程，禁止一次性 brute-force 全掃。

---

## 0. Pre-flight Checklist (Block all optimization until DONE)

| 項 | 內容 | 狀態 |
|---|---|---|
| P0-1 | D7 Volume Pre-Build Verification 完成（5 行 ShowMe 確認 TXF1 5M 成交量欄位真實可用） | ☐ |
| P0-2 | Rule #11 Settlement_Flat 7 elements 已植入 `.pla` 並通過 verify | ☐ |
| P0-3 | Rule #12 P3b `SetStopLoss` 已植入 | ☐ |
| P0-4 | 10-dim eval 已對 baseline (default params) 跑過，PF / Sharpe / MaxDD 已 logged | ☐ |
| P0-5 | TXF1 5M Continuous data 2020-01-01 至 2026-06-19 已載入 MC12，bar count ≈ 120K 已確認 | ☐ |
| P0-6 | MC12 Portfolio Trader「Auto-Trading OFF」確認（避免最佳化觸發實單） | ☐ |

> 若任一項未勾，本文件 §3 以後流程一律不得啟動。

---

## 1. Optimization Philosophy

### 1.1 核心理念
S3 的 25–30 個 input 是「為最佳化而設計」，並非為了上線時隨意調整。**所有 input 在程式碼中皆已 expose**，但這不代表每一個都該被無腦掃描。原則：

1. **可被市場結構解釋的參數**（如進場時間 845 / 結算日平倉時間 1325）→ **永不掃描**
2. **訊號型參數**（MA 長度、RSI 門檻、ATR 倍數）→ **可掃描，但須分階段**
3. **出場型參數**（TP%、SL 倍數、Time Stop）→ **可掃描，但目標為穩定 R:R 而非極大化淨利**

### 1.2 兩階段 GA (Genetic Algorithm) 流程

```
Stage 1: Coarse Sweep
  ├── 範圍：寬區間（5–10 個離散值）
  ├── 目的：找出 PF / Sharpe 的「高原區」(plateau)
  └── 警示：若某參數有單一峰值 (spike) 而周圍迅速塌陷 → 過擬合警報

Stage 2: Refine Sweep
  ├── 範圍：圍繞 Stage 1 最佳區域 ±1–2 step
  ├── 目的：在 plateau 內找穩健中心點
  └── 確認：plateau 寬度 ≥ 3 個連續 step 才算通過
```

### 1.3 反過擬合三鐵則

> 1. **堅持 "plateau" 而非 "spike"**：若最佳參數移動 ±1 step 後 PF 掉超過 15%，視為過擬合，棄用。
> 2. **單次最佳化最多 4 個參數同時掃**：超過 4 → 組合爆炸 + 過擬合風險倍增。
> 3. **必過 Walk-Forward (WFE > 50%)**：純 In-Sample 最佳化結果一律不得進入 live_simulation。

---

## 2. Per-Input Sweep Range Table

### 2.1 Tier 1 — Regime Gate (Daily TF)

| Input | Default | Coarse Range | Refine Step | Sensitivity | 備註 |
|---|---|---|---|---|---|
| `Daily_FastMA_Len` | 20 | [10, 15, 20, 30, 50] | ±5 around best | **HIGH** | 與 SlowMA 形成均線多頭結構的關鍵 |
| `Daily_SlowMA_Len` | 60 | [40, 60, 80, 100, 120] | ±10 around best | **HIGH** | 必須 > FastMA，否則 Regime Gate 失效 |
| `Daily_RSI_Threshold` | 70 | [65, 70, 75, 80] | ±2 around best | **MED** | RSI 越高 → WATCH 日越少但勝率可能上升 |
| `Daily_RSI_Sustained_Bars` | 2 | [1, 2, 3, 5] | ±1 | **MED** | 連續達標日數，避免一日噪訊 |
| `Daily_Dist_MA20_Pct` | 3.0 | [1.5, 2.0, 3.0, 4.0, 5.0] | ±0.5 around best | **HIGH** | 過熱距離；越大 → 觸發越少但極端偏多 |

**Tier 1 約束**：`Daily_FastMA_Len < Daily_SlowMA_Len`（GA 須加 constraint，否則大量無效組合）。

### 2.2 Tier 2 — Momentum Trigger (5M TF)

| Input | Default | Coarse Range | Refine Step | Sensitivity | 備註 |
|---|---|---|---|---|---|
| `Consec_Red_Bars` | 3 | [2, 3, 4, 5] | ±1 | **HIGH** | 連續陰 K 棒數；越大 → 訊號越少 |
| `EMA_Fast_Len` | 5 | [3, 5, 8, 10] | ±1 around best | **MED** | 與斜率判斷一同決定動能反轉 |
| `ATR_Short_Len` | 5 | [3, 5, 8] | — | **LOW** | 短期波動度基準；不建議掃 |
| `ATR_Long_Len` | 20 | [14, 20, 30] | — | **LOW** | 長期波動度基準；不建議掃 |
| `ATR_Spike_Mult` | 1.3 | [1.1, 1.2, 1.3, 1.5, 2.0] | ±0.1 around best | **HIGH** | 波動度噴出倍數；過大則錯失訊號 |
| `Pullback_Min_Pct` | 0.5 | [0.3, 0.5, 0.7] | ±0.1 around best | **MED** | 距離 intraday high 下限 |
| `Pullback_Max_Pct` | 1.5 | [1.0, 1.5, 2.0, 2.5] | ±0.25 around best | **MED** | 距離 intraday high 上限；不可 < Pullback_Min_Pct |

**Tier 2 約束**：`Pullback_Min_Pct < Pullback_Max_Pct`；`ATR_Short_Len < ATR_Long_Len`。

### 2.3 Exit Tier

| Input | Default | Coarse Range | Refine Step | Sensitivity | 備註 |
|---|---|---|---|---|---|
| `TP_Pct` | 0.7 | [0.4, 0.6, 0.7, 0.9, 1.2, 1.5] | ±0.1 around best | **HIGH** | 主 TP；R:R 平衡關鍵 |
| `TP_MA_Len` | 20 | [10, 20, 30, 50] | ±5 around best | **MED** | EMA20 結構觸碰備援出場 |
| `SL_ATR_Len` | 14 | [10, 14, 20] | — | **LOW** | ATR 計算基準 |
| `SL_ATR_Mult` | 4 | [2, 3, 4, 5, 6] | ±0.5 around best | **HIGH** | 停損距離；越大越能承受噪訊但單筆風險越高 |
| `Max_Bars_TimeStop` | 24 | [12, 18, 24, 36, 48] | ±3 around best | **MED** | 5M bar 數；24 = 120 min |

**Exit 約束**：`TP_Pct / (SL_ATR_Mult × ATR/Close)` 即 R:R，目標保持 ≥ 1.0；GA 須能讀取此衍生值並作為次目標。

### 2.4 Time Window — **DO NOT OPTIMIZE**

| Input | Default | 鎖定原因 |
|---|---|---|
| `Entry_Open_Time` | 845 | 開盤 15 分鐘後讓開盤亂流結束；market microstructure rationale |
| `Entry_Cutoff_Time` | 1230 | 留 55 分鐘給 120-min time stop 在 1325 平倉前完成 |
| `Daily_Flat_Time` | 1325 | 日盤收盤前 20 分鐘強制平倉；與 Rule #11 Settlement_Flat 對齊 |

> **嚴格規定**：任何 GA / WFO 任務的 Optimization Inputs 列表中**禁止勾選**以上三項。
> 若未來有調整需求，必須先提 market-structure 變化證據（如期交所收盤時間異動）並重審。

### 2.5 HighConviction Modifier — v1.0 **LOG ONLY**

| Input | Default | v1.0 行為 |
|---|---|---|
| `HighConv_Dist_Pct` | 5.0 | 僅寫入 strategy log（`Print` 或 commentary），不影響 sizing |
| `HighConv_Size_Mult` | 1.0 | v1.0 固定 1.0；v1.1 才可掃 [1.0, 1.5, 2.0] |

> v1.1 升級條件：v1.0 30 個交易日 PF ≥ 1.3 且 plateau 證實。

---

## 3. Optimization Targets / Objectives

### 3.1 主次目標排序

| 排序 | 指標 | 目標值 | 用途 |
|---|---|---|---|
| **Primary** | Profit Factor (PF) | **> 1.5** | GA fitness function 主軸 |
| **Secondary** | Annualized Sharpe Ratio | **> 0.8** | 用於 plateau 篩選 |
| **Tertiary** | Max Consecutive Losses | **< 5** | 排除「平均賺但會連續爆雷」的組合 |
| **Excluded** | Net Profit alone | — | **禁止單看淨利**；會引導高風險組合 |
| **Excluded** | Win Rate alone | — | 易誘發剪刀策略 (small win / huge loss) |

### 3.2 MC12 GA 設定建議

```
Optimization Type:       Genetic
Population Size:         50–100
Generations:             20–30
Crossover Rate:          0.7
Mutation Rate:           0.05
Fitness Function:        Custom = PF × min(Sharpe, 1.5)
                         (PF 為主，Sharpe 在 1.5 以上不再加分，避免追求極端)
Elitism:                 Top 5
Convergence:             20 generations no improvement → stop
```

---

## 4. Anti-Overfit Guards

### 4.1 Walk-Forward Optimization (WFO) — **必跑**

| 段 | 期間 | 用途 |
|---|---|---|
| In-Sample (IS) | 2020-01-01 — 2024-12-31 (5 年) | GA 找最佳參數 |
| Out-of-Sample (OOS) | 2025-01-01 — 2026-06-19 (~1.5 年) | 驗證 plateau 是否穩定 |
| Walk-Forward Efficiency (WFE) | OOS PF / IS PF | **必須 > 50%** |

> WFE < 50% → 過擬合，最佳化結果作廢，回到 design_spec 階段修訂訊號邏輯。

### 4.2 Parameter Plateau Test (手動 + 自動)

對每一個進入 final 候選的參數組合，**對所有 HIGH-sensitivity input 做 ±1 step 鄰域檢查**：

```
For each HIGH-sensitivity input in [Daily_FastMA_Len, Daily_SlowMA_Len,
                                     Daily_Dist_MA20_Pct, Consec_Red_Bars,
                                     ATR_Spike_Mult, TP_Pct, SL_ATR_Mult]:
    Run 3 backtests at [best-1step, best, best+1step]
    Plateau pass if: max(PF) - min(PF) < 15% × best_PF
    
If 任一 input 未過 plateau → REJECT 該組合
```

### 4.3 IS / OOS Split 額外規則

- **不允許 peeking**：OOS 時段在 IS GA 完成前**禁止 visualize**
- **不允許 OOS-driven re-optimization**：若 OOS 失敗，必須回到 design_spec 改邏輯，不可改參數重試（避免「OOS 變相 IS」）
- **OOS 跑超過 2 次即視為汙染**：必須等待新資料（至少 +3 個月）才能再驗證

---

## 5. Recommended Optimization Schedule

### Phase 0 — Preparation (1 day)
- [ ] 完成 §0 Pre-flight Checklist 全部 6 項
- [ ] baseline (default params) 完整 backtest，PF / Sharpe / MaxDD / Trade count 入 `scripts/_temp_s3_opt_log_baseline.csv`

### Phase 1 — Sensitivity Screening (1 day)
- 單變數掃描（One-At-A-Time, OAT），每次只動一個 input
- 對 §2 標記 **HIGH** 的 7 個 input 各跑一次 OAT
- 輸出：每個 input 的 PF 對該值的曲線圖
- 目的：確認哪些 input 真的「HIGH」、哪些可以下放到 MED/LOW

### Phase 2 — Coarse GA (1–2 days)
- 同時掃描的 input 數：**≤ 4 個**（從 Phase 1 確認最 sensitive 的前 4 個）
- GA 設定如 §3.2
- 候選組合保留 Top 10
- 結果存 `scripts/_temp_s3_opt_log_coarse_20260620.csv`

### Phase 3 — Refine (1 day)
- 圍繞 Top 10 coarse 結果各做 ±1 step 鄰域微掃（grid，不再 GA）
- 套用 §4.2 Plateau Test
- 通過者保留 Top 5
- 結果存 `scripts/_temp_s3_opt_log_refine_20260620.csv`

### Phase 4 — WFO (1 day)
- 對 Top 5 各跑 WFO（IS 2020-2024 / OOS 2025-2026）
- 排除 WFE < 50%
- 通過者送 10-dim eval

### Phase 5 — Final Selection (0.5 day)
- 10-dim eval 全部通過者送 live_simulation 候選
- 若 0 個通過：回到 design_spec 階段，**禁止降低 WFE 門檻硬上**

**總時程預估**：5–7 個工作日。

---

## 6. Caveats / Known Pitfalls

| # | 風險 | 緩解 |
|---|---|---|
| C1 | MC12 GA 可能找到 spurious optima（看似好但 OOS 崩潰） | 強制 WFO + Plateau Test |
| C2 | 5M 6 年 ≈ 120K bars，每次 backtest 數十秒；GA 50×20 = 1000 次 → 數小時 | 用 dedicated optimization 機台；筆電風扇全開 |
| C3 | 結算日 Settlement_Flat 邏輯若 buggy 會在最佳化中被「獎勵」（誤把不該開的單關掉） | Pre-flight P0-2 必過 |
| C4 | 時間窗口被誤勾入 GA → GA 會找到「只交易某 15 分鐘」的 cherry-pick 解 | §2.4 嚴格鎖定，code review 時三審 |
| C5 | Volume input 雖未啟用，但若未來啟用必須先過 D7 → 否則 S2 教訓重演 | §0 P0-1 強制 |
| C6 | Optimization log CSV 散落各處 → 半年後無法追溯哪一版參數哪一次跑的 | 統一存放 `scripts/_temp_s3_opt_log_<phase>_<YYYYMMDD>.csv`，retention 6 個月 |
| C7 | GA 多次重跑可能因 random seed 結果不同 | 固定 seed 並記錄；至少跑 3 次 seed 確認結果穩定 |
| C8 | MC12 Portfolio Trader 啟用 Auto-Trading 時誤觸發實單 | §0 P0-6 強制；最佳化期間 MC12 物理斷網 OK |

---

## 7. Output Artifacts

每次最佳化階段結束後，必須產出：

1. **`scripts/_temp_s3_opt_log_<phase>_<YYYYMMDD>.csv`**
   欄位：`run_id, phase, timestamp, <all inputs>, num_trades, net_profit, pf, sharpe, max_dd, max_consec_loss, win_rate, avg_win, avg_loss, expectancy, wfe_pct, plateau_pass`

2. **`S3_optimization_results_<YYYYMMDD>.md`** （Phase 4 / 5 結束時）
   - 最終 5 個候選的完整參數表
   - WFO 圖 + Plateau 圖
   - 10-dim eval 通過/否
   - 推薦上 live_simulation 的版本與理由

3. **Constitution 對齊聲明**
   - Rule #11 通過：是 / 否（附 verify 截圖）
   - Rule #12 通過：是 / 否
   - Rule #13 10-dim eval 通過：是 / 否

---

## 8. Version History

| 版本 | 日期 | 變更 | 作者 |
|---|---|---|---|
| 1.0 | 2026-06-20 | 初稿；對齊 D1–D8 用戶決策，反映 L4 退役、S3 取得 3% slot | Strategy Lab |

---

**END OF GUIDE**

> 提醒：本文件僅為「如何最佳化」的方法論。實際最佳化前**必須**先完成 D7 volume verification + Constitution Rule #11/#12 植入 + baseline 10-dim eval。任何跳過 §0 Pre-flight 即啟動 GA 的行為，視為違反 Constitution Rule #13。
