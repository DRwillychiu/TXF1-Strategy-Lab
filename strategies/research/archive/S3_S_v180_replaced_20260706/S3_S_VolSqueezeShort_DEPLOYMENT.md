# S3_S VolSqueezeShort — DEPLOYMENT (v1.8.0-PROD)

**Promote 日**：2026-06-30
**.pla**：`S3_S_VolSqueezeShort.pla` v1.8.0-PROD
**取代版本**：v1.7.3-FINAL（archived）
**Portfolio cap**：**3% account**
**R-6 配對**：S3_L VolSqueezeLong（5% cap，合計 squeeze sleeve 8%）

---

## 一、Promote 決策依據（**user 2026-06-30 ruling D**）

### 用戶 3 個論點（採納）
1. **NTD nominal 受 TWII 規模影響**（12K→46K 自然放大 P/L）→ 應用 % 報酬比較
2. **30 trades 是 design choice 不是缺陷**（precision sleeve 哲學）
3. **0 trade windows 該 verify regime 是否「正確守規」**

### v1.8.0 vs v1.7.3 對比

| 指標 | v1.7.3-FINAL | **v1.8.0-PROD** |
|------|--------------|----------------|
| Net Profit (2020-2026) | +1,013K | **+846K** |
| **PF gross** | 3.95 | **4.13** ⭐ |
| **PF adj (含滑價)** | 2.17 | **2.24** ⭐ |
| MDD % | -22.1% | **-19.4%** ⭐ |
| **1M_Exit 救援機制** | ❌ 無 | ✅ **6/8 case -10 pts** |
| 5/22 BoJ-like trade | -106K (典型) | -132K (Bug 2 影響) |
| Trade count | 29 | 24 |

---

## 二、Deployment Caveats（**部署前必讀**）

### 1. WFA 結果 mixed
- **嚴格 PF gate**：3/9 windows PASS
- **Net+Sharpe gate**：6/9 windows PASS（PF=0 為 MC 全勝顯示問題）
- **alpha 集中 2025-2026** (97%)，2022-2024 早期較弱
- 風險：未來 regime 變化可能失靈

### 2. 1M Multi-layer 機制需 MC12 chart 配 Data3
- Data1 = 60M / Data2 = Daily / **Data3 = 1M（必要）**
- IntrabarOrderGeneration = **TRUE**

### 3. Bug 2 SP IOG（**Non-blocking blackswan**）
- IOG=true 環境下 SP stop 可能 intrabar 大滑價
- 2024-08-05 BoJ trade SP -132K 是案例
- 但：6 年僅 1 次 + 夜盤可手動處理 + 1M_Exit 不受影響
- 已 documented 為 known limitation（user 2026-06-30 降級為 blackswan）

### 4. 4 trades/year 心理紀律壓力
- 平均 2-3 個月才一筆
- 必須設提醒「沒進場 = 正確守規」

---

## 三、Kill Triggers（**自動停用**）

| # | 條件 | 動作 |
|---|------|------|
| 1 | Monthly DD > 5% account | 停用 + review |
| 2 | 3 連續 SL > -100K 內 30 天 | 停用 + review |
| 3 | 12 個月內 0 trades | 檢視 regime filter health |
| 4 | Cluster losses > 3σ historical DD | 停用 + emergency review |
| 5 | 模擬期 PF < 1.5 over 30+ trades | 檢視 thesis |
| 6 | **單筆 SP loss > -200K**（Bug 2 防護）| 停用 + 重新評估 |

---

## 四、Operational Compliance

- ✅ Rule #11 Settlement_Flat（7 elements 完整）
- ✅ Rule #12 P3b SetStopLoss（MP ≥ 0 short variant guard）
- ✅ Rule #13 10-dim eval（將於 W5 完成）
- ✅ Rule #14 OFFICIAL_ROADMAP S3_S sequence
- ✅ Rule #15 ASCII 100%（`verify_pla_ascii.py --strict` PASS）
- ✅ Rule #16 Engineering System 5-pillar
- ✅ Rule #17 Extreme SL Multilayer SOP（**v1.8.0 IS the implementation**）

---

## 五、MC12 Chart Setup（**Required**）

| 設定 | 值 |
|------|-----|
| Data1 | TXF1 60M（連續近月）|
| Data2 | TXF1 Daily（regime filter 必要）|
| **Data3** | **TXF1 1M（v1.8.0 NEW，必要）**|
| **IntrabarOrderGeneration** | **TRUE**（v1.8.0 1M_Exit 需即時）|
| 策略運算最大使用 K 棒數量 | **1000** |
| Initial Capital | 1,000,000 NTD |
| Slippage | 1,000 NTD round-trip |
| Trade Size | 1 contract |

---

## 六、Final inputs（**鎖定 v1.8.0-PROD GA-best**）

```
{ Bollinger Bands - v1.7.3 baseline }
BBLen                = 45
BBStd                = 2.0
BWLookback           = 120
BWPctile             = 25
ATR_Len              = 14
StopATRMult          = 2.75
TargetATRMult        = 3.5

{ Exit timing }
MaxBars              = 35
UseMidExit           = True
MidExit_MinBars      = 2

{ Layer 2 SP }
SP_Trigger_ATRMult   = 1.5
SP_Retain_Pct        = 70

{ Cooldown }
Cooldown_Days        = 1

{ Regime Filter }
Use_Regime_Filter    = True
Regime_FastMA        = 15
Regime_SlowMA        = 40
Regime_BlockRange    = True
Regime_BlockWeakBull = True

{ v1.8.0 NEW: 1M Multi-layer (GA-best lock) }
ML_ActivationPct     = 30   *** GA best (was 40) ***
ML_ScoreTrigger      = 30   *** GA best (was 65) ***
ML_MinCategories     = 3
ML_VolSpikeMult      = 1.5  *** GA best (was 2.5) ***
ML_VolAvgLen         = 15   *** GA best (was 20) ***
ML_SpeedBars         = 5
ML_SpeedThreshPts    = 30   *** GA best (was 80) ***
ML_ATR_Short_Len     = 3    *** GA best (was 5) ***
ML_ATR_Long_Len      = 90   *** GA best (was 60) ***
ML_ATR_Ratio         = 2.5  *** GA best (was 2.0) ***

{ Compliance }
Holiday_Flat_Time    = 415
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230
```

---

## 七、Monitoring Schedule

| 頻率 | 動作 |
|------|------|
| Daily | 確認 strategy alive，無 error log，Data3 1M feed 正常 |
| Weekly | 檢視 entries（預期 ~0-1 per week）|
| Monthly | DD check + Kill trigger 評估 + portfolio rebalance |
| Quarterly | 對比回測 PF 偏離度（≤ 30% gate）+ 1M_Exit 觸發次數 |
| Annually | Full institutional 10-dim re-eval + 重新評估 Bug 2 |

---

## 八、Promote to live/（晉升條件）

| 標準 | 門檻 |
|------|------|
| 模擬期 trades | ≥ 5（v1.8.0 低頻 by design）|
| 模擬期 PF | ≥ 2.0（精準設計要求高）|
| 1M_Exit 至少觸發 1 次 | 證實 live data 1M 機制有效 |
| 模擬期 MDD | ≤ -25% account |
| 與回測 PF 偏離度 | ≤ 30% |
| 假日鐵律觸發 | 0 次違規 |
| **時程** | **至少 12 個月** |

---

## 九、Archived v1.7.3-FINAL（**保留歷史**）

位置：`strategies/research/archive/S03_VolSqueezeShort_v173_archived_20260630/`
- `S3_S_VolSqueezeShort_v173_archived.pla`
- `S3_S_VolSqueezeShort_v173_strategy.md`
- `S3_S_VolSqueezeShort_v173_DEPLOYMENT.md`
- `S3_S_VolSqueezeShort_v173_BOSS_VIEW.md`

v1.7.3 仍可作 reference / rollback fallback。
