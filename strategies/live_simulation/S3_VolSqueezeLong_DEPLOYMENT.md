# S3_L VolSqueezeLong — Live Simulation Deployment Manifest

**部署日**：2026-06-23
**版本**：v1.0 (529 LOC, MC12-ready)
**前置**：W0 (.pla 寫作) → W1-W3 (Baseline + GA + Refine) → W4 (Rolling WFA 9 windows) → **W5 10-dim institutional eval PASS**
**升等理由**：[W5_10dim_evaluation.md](../research/S03_VolSqueezeLong/W5_10dim_evaluation.md)

---

## ⚠️ Portfolio-level Caveats（必讀）

### 上限 1：配置不可超過帳戶 5%

**Why**：W5 揭露 single trade tail risk = 12.4% account（2026-04-02 川普關稅日 -124K NTD）。配置 5% 上限可隔離 single sleeve tail。

**How to apply**：portfolio rebalance 時 S3_L exposure 不可 > 5% 總 equity。

### 上限 2：等待 S3_S 上線後才完整 directional hedge

**Why**：S3_L 是 R-6 (L/S split) 的 Long 一半，single 部署有 directional exposure（vol expansion 向下時必虧）。真正 hedge 是 S3_S（VolSqueezeShort）並列部署，portfolio L+S 配對才能 capture 完整 vol expansion alpha。

**How to apply**：
- 當前狀態：S3_L 單 sleeve 模擬中，承擔 directional cost
- S3_S 完成後：portfolio 重平衡至 S3_L + S3_S 等權
- OFFICIAL_ROADMAP 次序：S3_L → S3_S → S4_L → ...

### 禁止 1：不可加 Pre-event Flat / event registry filter

**Why** (Lesson L24, 2026-06-23 用戶 ruling)：vol squeeze 策略 alpha source 就是 vol expansion events（FOMC/CPI/關稅/央行決議）。Filter 掉 events = self-defeat alpha + data mining overfit。

**How to apply**：任何 strategy-level event filter 提議都直接拒絕。所有 macro tail risk 在 portfolio level 解決（sizing / diversification）。

### 禁止 2：不可改 Long-only direction

**Why**：違反 R-6 split 設計。若需 short alpha 開 S3_S，不是改 S3_L。

---

## 模擬期觀察指標（Phase 5）

| 指標 | 門檻 | 目的 |
|------|------|------|
| 模擬實戰交易筆數 | ≥ 30 筆 | 樣本充足 |
| 模擬期 PF | ≥ 1.5 | 確認獲利穩定（高於 1.2 因 Phase 3 PF 2.55）|
| 模擬期 MDD | ≤ 帳戶 20% | 風險可承受（含 5% caveat buffer）|
| 與回測偏離度 | ≤ 30% | 模擬接近 backtest |
| 假日鐵律觸發 | 0 次違規 | 安全性 |
| 單筆滑價 | ≤ 500 NTD 單邊 | 執行品質 |
| **新指標** vol expansion 向下事件 single loss | ≤ 150K | tail risk monitor |

---

## Kill Triggers（觸發即降級或停用）

| Trigger | 動作 |
|---------|------|
| 模擬期 PF < 1.0 持續 10 筆 | 降回 research/ |
| 單筆虧損 > 250K NTD | 緊急 review（可能是 strategy 結構失效）|
| 連續 3 個 vol expansion event 虧損 > 150K | 結構 review，可能需 R-6 重審 |
| 模擬 MDD > 25% 帳戶 | 立即下架 |

---

## 載入 MC12 模擬帳戶設定

### Inputs（Phase 3 best params）
```pla
BBLen                = 45
BBStd                = 2.0
BWLookback           = 120
BWPctile             = 30
ATR_Len              = 14
StopATRMult          = 2.75
TargetATRMult        = 8.0
MaxBars              = 70
UseMidExit           = True
MidExit_MinBars      = 3
Cooldown_Days        = 1
Holiday_Flat_Time    = 415
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230
```

### Data Series
```
Data1 = TXF1 60M (主週期，breakout 偵測 + entry trigger)
Data2 = TXF1 Daily (regime filter, optional)
```

### Strategy Properties
```
Initial Capital:    1,000,000 NTD
Position Size:      1 contract (fixed)
Slippage:           500 NTD per side (1,000 round-trip)
Commission:         per IB / broker fee schedule
IOG (Intra-bar Order Gen): false
```

---

## 證據連結

| 文件 | 用途 |
|------|------|
| [W5_10dim_evaluation.md](../research/S03_VolSqueezeLong/W5_10dim_evaluation.md) | 10 維度完整評估 + L24 lesson |
| [progress_20260622_phase3_handoff.md](../research/S03_VolSqueezeLong/progress_20260622_phase3_handoff.md) | Baseline → P1 → P2 → P3 軌跡 |
| `scripts/_temp_analyze_s3l_wfa.py` | 9-window Rolling WFA |
| `scripts/_temp_analyze_s3l_w5_10dim.py` | 10 維度 auto eval |
| `scripts/_temp_analyze_s3l_dd_clustering.py` | DD source 深 dive |

---

## 晉升 live/ 條件

達到「模擬期觀察指標」全部 → 用戶 explicit promote → live/ 實盤帳戶（MC9）

預估時程：30+ 模擬 trades ≈ 3-6 個月（依市場頻率）

---

## 部署 changelog

- **2026-06-23**：W5 PASS，promote from research/ to live_simulation/。Caveats: 5% portfolio cap + 等待 S3_S 配對。

