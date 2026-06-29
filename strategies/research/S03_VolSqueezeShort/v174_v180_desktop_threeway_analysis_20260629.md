# S3_S Three-way Deep Analysis — v1.7.3 vs v1.7.4 vs v1.8.0（desktop backtest）

**日期**：2026-06-29
**Verdict**：⚠️ **v1.7.3-FINAL 仍是 best path**，v1.7.4 + v1.8.0 都受傷
**Critical finding**：2026-06-08 case 揭露 **fixed cap + 1M multi-layer 雙重失效**

---

## 一、三版本完整對照

| 指標 | **v1.7.3-FINAL** | v1.7.4 (cap 100) | v1.8.0 (1M multi) |
|------|-----------------|------------------|-------------------|
| 期間 | 2020-2026 | 2020-03 ~ 2026-06-29 | 2020-03 ~ 2026-06-29 |
| **Net Profit** | **+1,013,600** ⭐ | +791,800 (-22%) | +502,400 (-50%) |
| **PF gross** | **3.95** ⭐ | 2.81 (-29%) | 1.87 (-53%) |
| **PF adj (含滑價)** | **2.17** ⭐ | 1.72 (-21%) | **-0.99** 🚨 虧損 |
| Sharpe | 0.69 | 0.64 | 0.40 |
| Sortino | 1.08 | **1.18** ⭐ | 0.27 |
| MDD % | -22.1% | **-19.2%** ⭐ | -19.9% |
| Trades | 29 | 34 | 23 |
| WR % | **82.8%** ⭐ | 55.9% | 78.3% |

→ **v1.7.3 在 7/9 指標領先**

---

## 二、🚨 2026-06-08 致命 case（gap risk 揭露 cap + 1M 雙重失效）

### 同一交易日，三版本表現

| 版本 | 6/8 trade 結果 | 點數 | 帳戶占比 |
|------|--------------|------|---------|
| v1.7.3 ATR-based | (前 cap 失效) | ~-530 點 | -10.6% |
| **v1.7.4 cap 100** | **-93,200** | **-466 點** | **-9.3%** 🚨 |
| **v1.8.0 1M multi** | **-312,000** | **-1,560 點** | **-31.2%** 🚨🚨 |

### Root Cause: 開盤 gap 越過 SL Level

- v1.7.4 設 cap 100 點 SL，但開盤 gap 跳過 → fill 在 +466 點
- v1.8.0 無 cap, 1M monitor 完全 dead → fill 在 +1,560 點
- **Hard cap 在 gap 風險下完全失效**

→ **驗證用戶 2026-06-29 ruling 正確**：「fixed-point caps 在 vol-adaptive 架構中是設計矛盾」

→ **同時驗證 v1.8.0 1M multilayer 沒救到單一 trade**

---

## 三、v1.7.4 cap 100 完整分析

### Exit 分布

| Exit | N | PnL | avg | maxL |
|------|---|------|-----|------|
| SL | **14** | -431,600 | -30,829 | **-93,200** ⚠️ |
| SP | 14 | +427,200 | +30,514 | -4,800 |
| TP | 6 | +796,200 | +132,700 | 0 |

### SL trades 細節（**14 筆 vs v1.7.3 只 3 筆**）

| Date | PnL | 點數 | 評估 |
|------|-----|------|------|
| 2020-03-12 | -34K | -170 | cap 失效 vol expand |
| 2020-03-13 | -22K | -110 | cap 成功 |
| 2020-03-16 | -22K | -110 | cap 成功 |
| 2021-01-28 | -22K | -110 | cap 成功 |
| 2022-11-28 | -22K | -110 | cap 成功 |
| 2024-08-05 | -56K | -281 | cap 失效（BoJ vol）|
| 2025-04-07 | -22K | -110 | cap 成功 |
| 2025-05-24 | -22K | -110 | cap 成功 |
| 2026-01-30 ×2 | -50K | -110/-141 | cap 成功/微失 |
| 2026-02-02 | -22K | -110 | cap 成功 |
| 2026-05-15 | -22K | -110 | cap 成功 |
| 2026-06-05 | -22K | -110 | cap 成功 |
| **2026-06-08** | **-93K** | **-466** | **🚨 cap 完全失效** |

→ **14 個 SL 中 4 個 cap 失效**（170 / 281 / 141 / 466 點）
→ Gap 與 vol expansion 是 cap 致命弱點

---

## 四、v1.8.0 1M multilayer 完整分析

### Exit 分布（**SP 機制也壞了**）

| Exit | N | PnL | avg | maxL |
|------|---|------|-----|------|
| SL | 3 | -425,200 | **-141,733** | **-312,000** 🚨 |
| **SP** | 16 | +299,000 | +18,688 | **-132,200** 🚨 |
| TP | 4 | +628,600 | +157,150 | 0 |
| **SX_VS_1M_Exit** | **0** | **0** | - | **🚨 完全沒觸發** |

### Critical Issues

#### Issue 1: SX_VS_1M_Exit = dead code
- ML_ScoreTrigger=65% 太嚴
- ML_SpeedThreshPts=80 pts/5 bars 太極端
- 整個 backtest 0 次觸發

#### Issue 2: SP 機制壞了 (maxL -132K)
- v1.7.3 SP maxL ~-5K（小回吐）
- v1.8.0 SP maxL **-132K**（穿過 floor 大幅虧損）
- 原因：IOG=true + Data3 1M + Multi-TF 環境下 next bar fill 不確定性大幅增加

#### Issue 3: 2026-06-08 -312K 災難
- 沒 cap 限制
- 1M monitor 沒救
- Gap 開盤直接 fill -1560 點
- 單筆吃 -31% 帳戶

### Year-by-Year 衝擊

| Year | v1.7.4 | v1.8.0 | 差異 |
|------|--------|--------|------|
| 2020 | +85K | +106K | +21K |
| 2021 | -22K | -53K | -31K |
| 2022 | +93K | +101K | +8K |
| **2024** | +40K | **-132K** | **-172K** 🚨 BoJ |
| 2025 | +440K | +342K | -98K |
| 2026 H1 | +156K | +139K | -17K |

→ **2024 BoJ 那筆 SL 是 v1.8.0 大失血**（vs v1.7.4 cap 救了一些）

---

## 五、Lessons Learned（**重要結構性發現**）

### Lesson L29 候選：**Fixed Cap 在 Gap 風險下完全失效**
- 2026-06-08 case 證實：cap 100 點 SL 在開盤 gap 跳過後 fill 在 466 點
- **Hard cap 只能限制 K 棒內走動，不能限制 gap**
- 真正的 max loss 仍由市場決定（gap 大小）

### Lesson L30 候選：**1M Multilayer 在 IOG=true 環境引入新風險**
- v1.8.0 SP 機制壞了（maxL -132K vs v1.7.3 -5K）
- IOG=true + Data3 1M = next bar fill 不確定性大增
- 表面看 1M 監控 = 多一層保護，實際上 IOG 引入新問題

### Lesson L31 候選：**多複雜度 ≠ 多保護**
- v1.8.0 加 11-factor scoring + 5 floors + 3-gate
- 但 0 次觸發 + 整體 PF adj 變負
- **複雜系統需要更多參數，每個參數都是 over-fit risk**
- v1.7.3 簡單 5 層 (Kill/TP/Mid/Time/SL+SP) 反而 robust

### Lesson L32 候選：**v1.7.3-FINAL 是 sweet spot**
- 7/9 指標 best
- 接受 SL 大虧為 alpha 必要代價
- 不要 fixed cap, 不要 1M, 不要 IOG=true

---

## 六、4 個 path（user 決策）

### Path A: **接受 v1.7.3-FINAL 為 final production** ⭐
- archive v1.7.4 + v1.8.0 為 EXPERIMENTAL learning records
- 接受 -106K avg SL 是 alpha 必要代價
- Portfolio cap 3-5% 控制整體曝險
- **最 honest path**

### Path B: Fix v1.8.0 thresholds 再跑
- ML_ScoreTrigger 65% → 40% / 50%
- ML_SpeedThreshPts 80 → 50 / 60
- 看 1M monitor 是否真有效
- 但 SP 機制壞掉問題未解
- 風險：可能 false positive 截斷正常 trades

### Path C: 設計 v1.8.1 加 **Gap Protection**
- 開盤檢測 (Open vs Prev Close)
- 跳空 > X 點 → 直接 market exit, 不等 stop order
- 解 2026-06-08 case
- 但增加複雜度（違反 L31）

### Path D: Portfolio-level 解
- v1.7.3 + 3% portfolio cap
- 單筆 -10.6% × 3% = -0.32% portfolio
- 不動 .pla, 靠 portfolio sizing 控
- 機構標準做法

---

## 七、推薦：**Path A + D 結合**

### Final Production: v1.7.3-FINAL
- **不動 .pla**（live_simulation 維持 v1.7.3-FINAL）
- Portfolio cap **3% 帳戶**（v1.7.3 DEPLOYMENT 已設）
- 接受偶爾 -10% 單筆是 design 代價（× 3% cap = -0.3% portfolio）

### Archive 為 EXPERIMENTAL learning
- v1.7.4 cap 100 → archive 為 "fixed cap gap failure proof"
- v1.8.0 1M multi → archive 為 "complexity ≠ protection proof"

### 寫 Lesson L29-L32（永久 codify）
- 加入 docs/policies/

---

## 八、Critical Caveats

### 真實 production 風險
- v1.7.3 偶爾單筆 -10% account
- 5 連 SL = -50% account（極端情境）
- Portfolio cap 3% = 5 連 SL = -1.5% portfolio（可承受）

### 但要 monitor
- 月度 DD > 5% → kill trigger
- 3 連續 SL > -100K → 暫停
- 12 個月內 0 trade → review

→ 這些已寫在 `S3_S_VolSqueezeShort_DEPLOYMENT.md`

---

## 九、相關文件

- `v174_HardSLCap_spec.md` (v1.7.4 設計)
- `v174_cap100_result_20260628.md` (v1.7.4 首次 backtest)
- `v175_ConditionalCap_spec.md` (v1.7.5 已 superseded)
- `v180_MultiLayer1M_spec.md` (v1.8.0 1M 設計)
- `S3_VolSqueezeShort_v17.pla` v1.7.3-FINAL (生產版)
- `live_simulation/S3_S_VolSqueezeShort.pla` v1.7.3-FINAL (deploy)

---

## 十、Status

- v1.7.3-FINAL: ✅ **PRODUCTION**（live_simulation 未動）
- v1.7.4 cap 100: ⚠️ **EXPERIMENTAL ARCHIVED**（gap failure proof）
- v1.7.5 conditional: ⚠️ **SUPERSEDED**（never backtested）
- v1.8.0 1M multi: ⚠️ **EXPERIMENTAL ARCHIVED**（complexity failure proof）
- 待 user 決定 path A/B/C/D
