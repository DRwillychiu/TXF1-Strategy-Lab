# S16_S MACrossShort — Deployment Guide (v1.0.1-HOLIDAY)

**Promote Date**: 2026-07-10 (v1.0-PROD)
**Current Version**: v1.0.1-HOLIDAY (2026-07-16 compliance patch)
**Signal Load Name**: `STRATEGY_GEN_S16_S_MACrossShort`
**Portfolio Cap**: **3%**
**Account Sleeve**: 100 萬 NTD / 1 口大台

---

## 🔴 Post-Promote Compliance Patch (2026-07-16)

**Version bump**: v1.0-PROD → v1.0.1-HOLIDAY
**Reason**: v1.0-PROD 帶著 W2 draft placeholder `v_Holiday_Block = False;` 通過 PROMOTE，違反 Rule #11
**Impact**: Alpha 邏輯完全不變，僅補足假日合規（63 個 TAIFEX 假日）
**Full details**: [S16_S_HOLIDAY_PATCH_20260716.md](../research/S16_MACrossShort/S16_S_HOLIDAY_PATCH_20260716.md)
**Enforcement doc**: [PROMOTE_CHECKLIST.md](../../docs/policies/PROMOTE_CHECKLIST.md)
**Action required**: 用戶 MC12 需重新載入 .pla 並重跑回測確認績效影響 < 1%

---

## 一、Strategy Identity

**5M TXF1 極短動能 burst 狙擊手（Sniper Style）**

- **主場**：Bear + Volatile regime
- **保險成本**：Bull regime（可接受）
- **交易頻率**：~16 trades/year
- **持倉時間**：2 小時內為主
- **哲學**：進場精挑細選，出場迅速果斷

---

## 二、Key Parameters (v1.0-PROD, LOCKED)

| Input | Value | 用途 |
|-------|-------|------|
| ZLEMA_Fast | **25** | 5M 短期基準（125 分鐘）|
| ZLEMA_Slow | **70** | 5M 中期基準（350 分鐘）|
| MinSlope | **28** | Fast ZLEMA 每 K 下跌 ≥ 28 pts（純點數）|
| QuickStop_MaxLoss_Pts | 60 | 快速止血 |
| MaxHoldingBars | 24 | 2 小時強制平倉 |
| StopATRMult | 4.0 | 最後防線 SL 距離 |

---

## 三、Backtest Evidence

| Metric | v1.0-PROD |
|--------|-----------|
| Net Profit | +1,028,600 NTD |
| PF | 1.885 |
| MDD | -271,600 (17.97%) |
| Trades | 106 (2020-2026) |
| WR | 22.64% |
| Avg Win : Avg Loss | ~6.8 : 1 |
| Sharpe | +0.463 |

### Regime 表現

| Regime | Net | PF |
|--------|-----|-----|
| Bear | +590K | 3.79 |
| Volatile | +591K | 2.13 |
| Bull | -106K | 0.70 |

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
| 滑價 | 1,000 NTD round-trip |
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

**預估模擬期**：**約 24 個月**（每年 16 trades，需累積 30 筆）

---

## 十一、Rule Compliance

| Rule | 狀態 |
|------|------|
| #11 Settlement_Flat | ✅ 落實 P0 |
| #12 SetStopLoss guard | ✅ Section 7 |
| #13 10-dim eval | ✅ 8/10 PASS |
| #14 OFFICIAL_ROADMAP | ✅ Batch 04 S16_S |
| #15 ASCII 100% | ✅ verify PASS |
| #16 五支柱工程 | ✅ |
| #17 Multi-Layer SL | ✅ M6 Rule #17 |
| #18 Non-WFA 5-piece | ✅ Sniper 8/8 |

---

## 十二、Related Files

- Strategy PLA: `S16_S_MACrossShort.pla` (v1.0-PROD)
- Strategy Definition: `../research/S16_MACrossShort/S16_S_strategy.md`
- W4 WFA report: `../research/S16_MACrossShort/W4_WFA_analysis_20260710.md`
- W5 5-piece: `../research/S16_MACrossShort/W5_fivepack_validation_20260709.md`
- Final Summary: `../research/S16_MACrossShort/S16_S_FINAL_SUMMARY_20260710.md`
- BOSS_VIEW: `S16_S_MACrossShort_BOSS_VIEW.md`

---

**Deployment Ready — 2026-07-10** 🎯
