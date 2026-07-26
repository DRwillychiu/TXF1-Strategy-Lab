# S1 NightMomentum — Deployment Guide (v2.7)

**Promote Date**: 2026-06-07 (v2.1 initial) / **Current Version**: v2.7+StopHarden (2026-07-26)
**Official Baseline (v2.7, 200 萬 / 2 口)**: **790T / Net +3,066,000 / PF 1.319 / MDD -1,012,800 (-22.3%) / WR 57.59%**
**Prior Baseline (v2.6)**: 807T / +2,782,400 / PF 1.258 / MDD -1,092,800 / WR 55.51% (superseded)

---

## 一、Strategy Identity

**15M TXF1 夜盤突破 + 跨夜 Gap Up 捕手（高頻 Momentum）**

- **主場**：夜盤多頭結構成立 + 隔日 gap up
- **交易頻率**：~120 trades/year
- **持倉時間**：夜盤進場 → 隔日 09:00 強制出場
- **哲學**：捕捉夜盤突破動能 + 跨夜系統性正向 gap
- **方向**：純多

---

## 二、Key Parameters (LOCKED)

| Input | Value | 用途 |
|-------|-------|------|
| LookbackBars | **11** | 夜盤 high 回顧長度 |
| ATRLen | **11** | ATR 計算週期 |
| EntryATRMult | **0.2** | 突破門檻 = NightHigh + 0.2 ATR |
| RangeMinATR | **0.9** | 夜盤振幅最低門檻（ATR 倍數）|
| RangeMaxATR | **4.5** | 夜盤振幅最高門檻（排除極端波動）|
| StopATRMult | **2.75** | 停損距離 = 2.75 ATR |
| TargetATRMult | **2.0** | 停利距離 = 2.0 ATR |
| Trail_Mode | **0** | OFF（v2.6 裁示：Trail_B -385K 證實對短週期無效）|
| ExitTime | **500** | 09:00 強制出場（gap 捕捉）|
| NightOpen | **1500** | 夜盤開始 15:00 |
| TrendFilterMode | **0** | OFF（v2.6 option，目前 baseline 不啟用）|
| Holiday_Flat_Time | **415** | 假日前 04:15 強制平倉 |
| Registry_Valid_Until | **1270101** | 假日登錄表有效期 |
| Settlement_Flat_Time | **1230** | 結算日 12:30 前平倉 |
| **SL_Pct (v2.7)** | **1.50** | ATR 停損趴數上限（MC sweep 0-5.0 收斂最佳值）|

---

## 三、v2.7 Stop Hardening 變更摘要

### SetStopContract Bug Fix
v2.6 以下：2 口倉位的 engine SetStopLoss 以 TOTAL 計算 → 實際停損距離 = 設計值一半（1.375 ATR vs 2.75 ATR）。
v2.7：加 `SetStopContract` 修正為 PER-CONTRACT。

### SL_Pct=1.50 Cap
極端波動時 ATR 暴漲導致停損距離過大。SL_Pct 在 entry price 的 1.50% 處設上限。
MC sweep 0.75-5.00 step 0.25 收斂分析：
- 收斂點 = 2.50（baseline 不降）
- 最佳點 = **1.50**（Net +3,066,000，比 baseline +50K）
- < 1.00 開始 degrade

### Engine Stop Architecture
v_Guard_Distance 每根 K 棒重算（current ATR, not frozen），確保不因 stale ATR 產生 SetStopLoss(0) 即停 bug。
修正前 33 筆 engine stop → 修正後 5 筆（27 筆轉換出場，16 筆轉正）。

---

## 四、Backtest Evidence (MC12 200 萬 / 2 口)

| Metric | **v2.7 (現行)** | v2.6 (prior) | 變化 |
|--------|---------------|-------------|------|
| Net Profit | **+3,066,000** | +2,782,400 | **+283,600 (+10.2%)** |
| PF | **1.319** | 1.258 | +0.061 |
| MDD | **-1,012,800 (-22.3%)** | -1,092,800 (-24.0%) | 改善 |
| Trades | **790** | 807 | -17 |
| WR | **57.59%** | 55.51% | +2.08pp |
| Sharpe | **0.770** | 0.685 | +0.085 |
| Sortino | **0.508** | 0.432 | +0.076 |
| Avg Trade | **+3,881** | +3,448 | +433 |
| Gross Profit | +12,685,600 | — | — |
| Gross Loss | -9,619,600 | — | — |

### 出場分佈 (v2.7)

| Exit | Trades | % | Net | WR | Avg P/L | 角色 |
|------|--------|---|-----|-----|---------|------|
| LX_NM_Time | 474 | 60.0% | +1,872,000 | 52.7% | +3,949 | 主體（時間出場 + gap capture）|
| LX_NM_TP | 205 | 25.9% | +6,189,200 | 100% | +30,191 | Alpha 引擎（佔淨利 202%）|
| LX_NM_SL | 106 | 13.4% | -4,777,600 | 0% | -45,072 | 控損成本 |
| Stop Loss | 5 | 0.6% | -217,600 | 0% | -43,520 | Engine 極端保護 |

### TP=2.0 ATR 驗證結論

- MFE capture: **99.9%**（205 筆中僅 2 筆有 MFE 超過 TP 水位）
- 調低 1.5 ATR → 估算 -2.88M（不可行）
- 調高 2.5 ATR → 估算 -1.33M（不可行）
- 結論：**TP=2.0 ATR 為 sweet spot，不調整**

### 年度分佈

| Year | Total | TP | Time | SL | Eng | Net |
|------|-------|-----|------|-----|-----|-----|
| 2020 | 94 | 23 | 50 | 20 | 1 | -333,200 |
| 2021 | 91 | 23 | 59 | 9 | 0 | +235,200 |
| 2022 | 135 | 36 | 79 | 20 | 0 | +1,200 |
| 2023 | 140 | 44 | 72 | 21 | 3 | -139,600 |
| 2024 | 120 | 30 | 77 | 13 | 0 | +483,600 |
| 2025 | 135 | 33 | 89 | 13 | 0 | +1,443,600 |
| 2026 | 75 | 16 | 48 | 10 | 1 | +1,375,200 |

### MDD 結構

MDD -1,012,800 發生在 **2026/06/13 ~ 07/23**（40 天 / 13 筆 / 雙波段 DD）：
- Wave 1 (06/16-06/30): 6 連敗，DD -685,200（含 2 筆 SL -159K/-240K）
- Wave 2 (07/07-07/23): DD 加深至 -955,200 closed + intra-trade 至 -1,012,800
- 與 L1-L5 帳戶同期 DD 同步（市場 regime 不利夜盤做多）

---

## 五、Label Inventory (11 labels)

| Label | Type | Line | Backtest | Status |
|-------|------|------|----------|--------|
| LE_NM_Long | Entry | 410 | 790T | Active |
| LX_NM_Time | Exit | 474 | 474T | Active |
| LX_NM_TP | Exit | 449 | 205T | Active |
| LX_NM_SL | Exit | 444 | 106T | Active |
| Stop Loss | Engine | 399 | 5T | Active |
| LX_NM_Kill | Exit | 428 | 0T | Manual kill switch |
| LX_NM_RegistryEnd | Exit | 430 | 0T | Registry warning |
| LX_NM_Holiday | Exit | 432 | 0T | Holiday safety |
| LX_NM_Settlement | Exit | 434 | 0T | Settlement safety |
| LX_NM_Trail_A | Exit | 461 | 0T | Disabled (Trail_Mode=0) |
| LX_NM_Trail_B | Exit | 465 | 0T | Disabled (Trail_Mode=0) |

---

## 六、Chart Setup

```
Symbol:                 TXF1
Timeframe:              15 Minutes (Data1)
Session:                Day + Night (08:45-05:00)
IntrabarOrderGeneration: FALSE
MaxBarsBack:            >= 200
History:                From 2020-01-01
Initial Capital:        2,000,000 NTD
Contracts:              2
```

---

## 七、Trading Costs

| 項目 | 值 |
|------|---|
| 滑價 | 2,000 NTD / 趟（含手續費）|
| 每點值 | 200 NTD (大台) |
| 帳戶乘數 | 固定 2 口 |

---

## 八、監控紅線

### 立即暫停（任一觸發）
- 累計 MDD > 30% 帳戶
- 連續 10 筆虧損
- 連續 3 個月 PF < 0.8

### Review（需檢討但不停）
- 單月 trade 數 > 30（進場過度活躍）
- TP hit rate 連續 3 個月 < 15%
- 6 個月滾動 Sharpe < 0

---

## 九、Rule Compliance

| Rule | 狀態 |
|------|------|
| #11 Holiday_Flat | P0 (63 筆 registry + HolidayFlat_v3) |
| #12 SetStopContract+SetStopLoss+SL_Pct | v2.7 三件套完備 |
| #15 ASCII 100% | verify PASS |

---

## 十、Related Files

- Strategy PLA: `S1_NightMomentum.pla` (**v2.7**)
- BOSS_VIEW: `S1_NightMomentum_BOSS_VIEW.md`
- Annotated: `S1_NightMomentum_annotated.md`

---

**v2.7 Stop Hardening deployed — 2026-07-26**
