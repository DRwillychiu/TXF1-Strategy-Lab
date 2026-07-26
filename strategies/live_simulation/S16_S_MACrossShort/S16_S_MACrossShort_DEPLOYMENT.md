# S16_S MACrossShort — Deployment Guide (v1.5)

**Promote Date**: 2026-07-10 (v1.0-PROD) / **正式上架 (v1.4 official deployment): 2026-07-18**
**Current Version**: v1.5 + SetStopContract + SL_Pct (2026-07-26)
**Official Baseline (v1.5, 2026-07-26)**: **112T / Net +2,006,800 / PF 1.775 / MDD -456,000 (-18.3%) / WR 25.89%**
**Prior Baseline (v1.4, 718)**: 107T / +1,094,800 / PF 1.910 / MDD -228,000 / WR 27.1% (superseded)

---

## ✅ 正式上架宣告 (2026-07-18, Rule #19 CHECKLIST 全過)

| Check | 結果 |
|-------|------|
| 1 Placeholder scan | PASS（v_Holiday_Block reset+loop 覆寫為合法模式）|
| 2 Rule #11 有效性 | PASS（63 假日 registry 實測擋單證明有效）|
| 3 Rule #12 SetStopContract+SetStopLoss+SL_Pct | PASS（v1.5: SetStopContract per-contract, SL_Pct=1.00 converge, MP>=0 guard）|
| 4 Rule #15 ASCII | 27/27 PASS |
| 5 Rule #13/#18 | 5 件套通用 4/5 / 適性 5/5；WFA 轉化為參數凍結鐵則 |
| 6 Sniper 特殊條件 | 破產率 0.02% / 單筆最大虧 4.26% / EV +10,232 全過 |

**模擬時鐘自 2026-07-18 起算**（v1.4 為凍結版本，改 code = 30 筆重計時）。

### 上架操作（MC12 端）
1. `git pull` → 重新編譯 live_simulation 版 .pla（header 同步至 v1.4-BELATE）
2. 策略屬性恢復預設值 + 確認「策略運算最大使用K棒數量 = 200」
3. 滑價 1000/邊、初始資金 1,000,000、固定 1 口 — 與 718 對帳設定一致
4. 全期回測 sanity：應重現 107T / +1,094,800

### 模擬期監控（30 筆檢討前不動 code）
- 🚨 暫停：累計 MDD > 25% / 單月連虧 > 8 筆 / PF < 0.8 連 3 月
- ⚠️ Review：月 trade > 15 / 連續 3 筆大幅回吐型出場（BE_Late 監控條款）
- 升 live 門檻：模擬 ≥ 30 筆 + PF ≥ 1.2 + 回測偏離度 ≤ 30%
- ⛔ 參數凍結鐵則：任何定期重最佳化禁止；重評估僅限指數 >55K 或紅線觸發
- 📅 2026-12 前 refresh 2027-2028 假日 registry (F2)
**Signal Load Name**: `STRATEGY_GEN_S16_S_MACrossShort`
**Portfolio Cap**: **3%**
**Account Sleeve**: 100 萬 NTD / 1 口大台

---

## 🔴 Post-Promote Compliance Patch (2026-07-16) — 已驗證 (2026-07-18)

**Version bump**: v1.0-PROD → v1.0.1-HOLIDAY
**Reason**: v1.0-PROD 帶著 W2 draft placeholder `v_Holiday_Block = False;` 通過 PROMOTE，違反 Rule #11
**Impact 實測（2026-07-17/18 用戶 MC12 重跑，逐筆 diff 驗證）**:
- 唯一差異 = 移除 1 筆跨清明連假持倉（2025-04-03 04:45 進場，+370,200 彩券單）
- 該筆為連假收盤前 15 分鐘進場裸空、跨關稅崩盤週末——gap 面前所有停損失效，
  屬運氣而非 alpha；反向跳空即為單筆 -360K+
- **MDD / 毛損完全不變** — 拿掉的是運氣，不是 alpha
- 用戶 ruling (2026-07-18)：**接受合規 baseline**
**Full details**: [S16_S_HOLIDAY_PATCH_20260716.md](../research/S16_MACrossShort/S16_S_HOLIDAY_PATCH_20260716.md) + [S16_S_HOLIDAY_IMPACT_20260717.md](../research/S16_MACrossShort/S16_S_HOLIDAY_IMPACT_20260717.md)
**Enforcement doc**: [PROMOTE_CHECKLIST.md](../../docs/policies/PROMOTE_CHECKLIST.md)

---

## 一、Strategy Identity

**5M TXF1 極短動能 burst 狙擊手（Sniper Style）**

- **主場**：Bear + Volatile regime
- **保險成本**：Bull regime（可接受）
- **交易頻率**：~16 trades/year
- **持倉時間**：2 小時內為主
- **哲學**：進場精挑細選，出場迅速果斷

---

## 二、Key Parameters (LOCKED)

| Input | Value | 用途 |
|-------|-------|------|
| ZLEMA_Fast | **25** | 5M 短期基準（125 分鐘）|
| ZLEMA_Slow | **70** | 5M 中期基準（350 分鐘）|
| MinSlope | **28** | Fast ZLEMA 每 K 下跌 ≥ 28 pts（純點數）|
| QuickStop_MaxLoss_Pts | 60 | 快速止血 |
| MaxHoldingBars | **24** | 2hr 強制平倉（G2 雙向實證最優：12/36/48 全劣）|
| StopATRMult | 4.0 | 最後防線 SL 距離 |
| **SL_Pct (v1.5)** | **1.00** | ATR 停損趴數上限（MC sweep 0-5.0 收斂點）|
| **BE_Trigger_ATR (v1.4)** | **2.5** | 保本延後啟動（高原 2.0-3.0 平坦，勿低於 2.0）|
| **BE_Tier2_ATR (v1.4)** | **3.5** | 二層保本 |
| **BE_Buffer_Pts (v1.4)** | **15 / 20** | Tier 1/2 緩衝（脫離雜訊帶）|
| Tail_LastEntry / ForceExit (v1.3) | 430 / 440 | 時間護欄，絕不跨休市 |

---

## 三、Backtest Evidence（MC12 實測）

| Metric | **v1.5 (現行, 2026-07-26)** | v1.4-BELATE | v1.3-TIMEGUARD | v1.0-PROD (superseded) |
|--------|---------------------------|-------------|----------------|------------------------|
| Net Profit | **+2,006,800 NTD** | +1,073,200 | +888,400 | +1,028,600（含彩券單）|
| PF | **1.775** | 1.876 | 1.736 | 1.885 |
| MDD | **-456,000 (-18.31%)** | -228,000 (-18.6%) | -249,600 (-21.25%) | -271,600 |
| Trades | **112** | 109 | 109 | 106 |
| WR | **25.89%** | 26.6% | 23.85% | 22.64% |
| Win:Loss | **5.08 : 1** | 5.2 : 1 | 5.54 : 1 | ~6.8 : 1 |
| Sharpe (年化) | **+0.718** | +0.57 | +0.530 | +0.463 |
| Sortino | **1.216** | 0.979 | 0.529 | 0.66 |
| Max Single Win | **602,800** | — | — | — |
| Max Single Loss | **-85,200** | — | — | — |
| 最大連虧 | **10 次 / -322,800** | 10 次 | 10 次 / -159,600 | 13 次 |

**v1.5 vs v1.4 變化原因**：engine stop 從「上一筆交易的凍結 ATR」改為「每根 K 棒即時 ATR」，
消除跨 regime 使用過時波動率的結構性缺陷。MDD% 持平（18.6%→18.3%），非風險放大。

### v1.3 vs v1.0.1 逐筆 diff（109/110 完全一致）
- 擋掉 `2025-03-05 05:00` 進場（-32,800，該筆持倉跨 05:00-08:45 早盤空窗吃 gap 虧損）
- `2026-03-07` 出場 04:50 BE_Trail2 (-600) → 04:45 TailFlat (+21,400)
- 總變動 +54,800，對帳一分不差

### 出場分佈（v1.5 Excel 交叉驗證）

| Exit | Trades | Net | WR | Avg P/L |
|------|--------|-----|-----|---------|
| TimeStop | 23 | **+4,375,200** | 100% | +190,226 |
| GoldenCross | 3 | +175,200 | 100% | +58,400 |
| TailFlat (v1.3) | 1 | +42,800 | 100% | +42,800 |
| BE_Trail2 | 1 | +1,600 | 100% | +1,600 |
| BE_Trail1 | 2 | -400 | 50% | -200 |
| ML_Exit | 1 | -28,000 | 0% | -28,000 |
| QuickStop_Time | 31 | -418,800 | 0% | -13,510 |
| QuickStop_Loss | 50 | **-2,140,800** | 0% | -42,816 |

### Regime 表現（W5-era 數據，含已移除彩券單，待 regime 重跑）

| Regime | Net | PF |
|--------|-----|-----|
| Bear | +590K | 3.79 |
| Volatile | +591K（含 +370K 彩券單）| 2.13 |
| Bull | -106K | 0.70 |

### 2026-07 實戰級對沖證據（模擬）

台股 7 月 DD 危機（L1-L5 live 帳戶 -21.3%）期間，S16_S 單月 14 筆 **+264,000**。
空方 sniper sleeve 在組合最需要對沖時發揮本職。

---

## 四、W4 Walk-Forward Evidence（**通過傳統嚴格 gate**）

- **WFE = 77.4%** ✅（gate > 50%）
- 9 windows / 416 OOS trades / +1,737,800 aggregate
- **7/9 windows PASS**（Bear + Volatile 100% 獲利）
- 2/9 LOSS（W5 小虧、W6 -347K bull whipsaw）
- **不需要 Path A 豁免**（S3_S 曾需，S16_S 無需）

### W6 警訊必要 disclosure

**Window 6（2024 H2 OOS）**：
- Regime: AI 主升段 + BoJ shock
- Net: -347,000
- MDD: **-43.4%**
- 這是**空頭策略在強多頭 whipsaw regime 的自然弱點**
- 已由 2026-07-08 Option A ruling 接受為保險成本

---

## 五、W5 Sniper-Adapted Validation（**8/8 PASS**）

- Ruin probability 0.03% < 1%
- Single trade max loss 4.26% < 5%
- Kelly criterion 11.2% > 0
- Expected value +10,547/trade > 0
- Bear PF 3.79 > 2.0
- Volatile PF 2.13 > 1.0
- Max consec loss 16.2% < 20%
- Robustness 5/7

**Memory reference**: `feedback_validation_precheck`

---

## 六、Chart Setup

```
Symbol:                 TXF1
Timeframe:              5 Minutes (Data1)
Session:                Day + Night (08:45-05:00)
IntrabarOrderGeneration: FALSE (locked in code)
MaxBarsBack:            >= 200
History:                From 2020-01-01 (or as available)
```

---

## 七、Trading Costs

| 項目 | 值 |
|------|---|
| 滑價 | 2,000 NTD / 趟（實測 110 筆共 220,000，逐筆驗證）|
| 手續費 | 已含在滑價 |
| 每點值 | 200 NTD (大台) |
| 帳戶乘數 | 固定 1 口 |

---

## 八、監控紅線（Portfolio Manager 必看）

### 🚨 立即暫停 trigger（任一觸發）
- 累計 MDD > 25% 帳戶
- 單月連虧 > 8 筆
- 連續 3 個月 PF < 0.8

### ⚠️ Review trigger（需檢討但不停）
- 單月 trade 數 > 15（進場過度活躍）
- 12 個月 0 trade（regime 全變）
- W6 型 bull whipsaw 重現（連 2 個月 -10% 損失）

### 🔍 定期審查
- 每季 review 一次
- 半年 backtest 比對 vs 模擬帳戶偏離度
- 每年 GA re-optimize 檢查

---

## 九、Bull Regime Insurance Cost（重要 disclosure）

策略在**強多頭 + 短暫 shock 恢復**的 regime 中會虧損。

**根據 W4 WFA W6 evidence**：
- 2024 H2 (AI 主升段) 虧損 -34.7% MDD
- 這是**單一方向做空 sniper 的結構性弱點**
- **不是 bug，是設計**（Option A ruling 已接受）
- **必須靠 portfolio 補位**（如 S3_L VolSqueezeLong）

**若 portfolio 未搭配多頭策略**：建議提高 cap 至 5-10%，或考慮**單獨提高 QuickStop 敏感度**。

---

## 十、模擬期升 live 條件

依 CLAUDE.md 三層晉升流程：

```
live_simulation → live：
- 模擬 ≥ 30 筆
- 模擬 PF ≥ 1.2
- 回測偏離度 ≤ 30%
```

**預估模擬期**：**約 21 個月**（每年 ~17 trades，需累積 30 筆；高波動年更快）

---

## 十一、Rule Compliance

| Rule | 狀態 |
|------|------|
| #11 Settlement_Flat | ✅ 落實 P0 |
| #12 SetStopContract+SetStopLoss+SL_Pct | ✅ Section 7 (v1.5: per-contract, SL_Pct=1.00) |
| #13 10-dim eval | ✅ 8/10 PASS |
| #14 OFFICIAL_ROADMAP | ✅ Batch 04 S16_S |
| #15 ASCII 100% | ✅ verify PASS |
| #16 五支柱工程 | ✅ |
| #17 Multi-Layer SL | ✅ M6 Rule #17 |
| #18 Non-WFA 5-piece | ✅ Sniper 8/8 |

---

## 十二、Related Files

- Strategy PLA: `S16_S_MACrossShort.pla` (**v1.5**)
- Strategy Text: `../research/S16_MACrossShort/S16_S_STRATEGY_TEXT_20260718.md`（現行版）
- Holiday impact: `../research/S16_MACrossShort/S16_S_HOLIDAY_IMPACT_20260717.md`
- Risk Register: `../research/S16_MACrossShort/S16_S_OPEN_ISSUES_20260713.md`（A-G 全議題）
- W4 WFA report: `../research/S16_MACrossShort/W4_WFA_analysis_20260710.md`
- W5 5-piece: `../research/S16_MACrossShort/W5_fivepack_validation_20260709.md`
- Final Summary: `../research/S16_MACrossShort/S16_S_FINAL_SUMMARY_20260710.md`
- BOSS_VIEW: `S16_S_MACrossShort_BOSS_VIEW.md`

---

**Deployment Ready — 2026-07-10 / Compliance-verified — 2026-07-18 / v1.5 Stop Hardening — 2026-07-26** 🎯
