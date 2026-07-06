# S3_S VolSqueezeShort — DEPLOYMENT (v1.9.6-OPT-PROD)

**Promote 日**：2026-07-06
**.pla**：`S3_S_VolSqueezeShort.pla` v1.9.6-OPT-PROD (1110 LOC)
**取代版本**：v1.8.0-PROD（archived 至 `strategies/research/archive/S3_S_v180_replaced_20260706/`）
**Portfolio cap**：**3% account**（與 v1.8.0 一致，等待模擬期實證後再檢討）
**R-6 配對**：S3_L VolSqueezeLong（5% cap 依 tail risk 保留，非鏡像因此 correlation 豁免）

---

## 一、Promote 決策依據（**user 2026-07-06 ruling**）

### 用戶論點
1. **S3_L 與 S3_S 非鏡像關係** → Portfolio Correlation < 0.7 gate 結構性豁免
2. **v1.9.6 反掃單機制 + BWRank bug fix + 5-param GA OPT** 品質全面超越 v1.8.0
3. **Rule #18 7/7 gates PASS** = 立即可上架，T68 MAE Cap 評估 parallel 進行

### v1.8.0 vs v1.9.6-OPT 對比

| 指標 | v1.8.0-PROD | **v1.9.6-OPT-PROD** |
|------|-------------|-------------------|
| 交易數 | 24（2020-2026, 6.3y）| **71**（2019-09~2026-06）|
| 淨利 | +846K | **+731K** |
| PF | 4.13 | 1.749 |
| MDD | -19.4% | **-17.17%** |
| Sharpe | 0.56 | **+0.549** |
| WR | 75% | 49.3% |
| 平均每筆 | +35K | +10K |
| Bootstrap P(Net>0) | N/A | **95.0%** |
| MC 95% MDD | N/A | **-20.47%** |
| Stress 6 events | N/A | **6/6 Event-Net PASS** |

### 為什麼「Trade 更多、單筆更小」是進步

v1.8.0 依賴極少數大 win（PF 4.13 靠 24 筆），單筆 tail risk 大且 sample 太薄。
v1.9.6 分散為 71 筆，任意 3 筆移除仍獲利 +146K（v1.9.5 是 -17K FAIL）。
統計顯著性、regime 覆蓋、event coverage 均全面超越。

---

## 二、Rule #18 完整驗證表

| # | Test | Threshold | v1.9.6 Result | 判定 |
|---|------|-----------|---------------|------|
| 1 | MC 95% MDD | < 30% | **-20.47%** | ✅ PASS (10pp buffer) |
| 2 | Bootstrap P(Net>0) | > 60% | **95.0%** | ✅ PASS |
| 3 | Bootstrap P(PF>1) | > 60% | **95.0%** | ✅ PASS |
| 4 | Parameter Sensitivity | 5-param plateau | ✅ | GA OPT DONE |
| 5 | Stress Testing 6 events | 6/6 event-net | **6/6** | ✅ PASS |
| 6 | HHI winners | < 0.25 | **0.0655** | ✅ PASS |
| 7 | Remove Top 3 profitable | > 0 | **+146K** | ✅ PASS |
| 8 | WFA | WFE > 50% | 14.8% | ⚠️ Path A 豁免（low-freq） |
| 9 | Portfolio Correlation | < 0.7 | N/A | ✅ 豁免（非鏡像）|

**7/7 quantitative gates PASS + 2 conditional 豁免**

### Stress Test 6 事件明細
| Event | 期間 | N | Net | 判定 |
|-------|------|---|-----|-----|
| E1 2020 COVID | Feb-Apr 20 | 1 | -28K | ✅ SURVIVED |
| E2 2022 熊全年 | 全年 | 36 | **+153K** | 🏆 CRASH WIN |
| E3 2022-Q4 CPI | Sep-Oct 15 | 12 | **+87K** | 🏆 CRASH WIN (WR 75%) |
| E4 2024-08 BoJ | Aug 1-15 | 0 | 0 | ✅ Regime blocked |
| E5 2025-04-07 Trump | Apr 1-15 | 2 | **+190K** | 🏆 CRASH WIN |
| E6 2026-06 crash cluster | Jun 1-20 | 7 | **+343K** | 🏆 CRASH WIN |

---

## 三、關鍵 inputs（Config B + OPT 完整清單）

### 5-param GA OPT 結果
```
BWPctile              = 40      (v1.9.5: 35)
StopATRMult           = 3.25    (v1.9.5: 3.75)
SP_Trigger_ATRMult    = 2.0     (v1.9.5: 1.4)
Hunt_Max_Stops        = 4       (v1.9.5: 2)
ML_ScoreTrigger       = 35      (v1.9.5: 40)
```

### Anti-Hunt Gates (Round 1)
```
BWRank_EqualGuard_On   = True    Bug fix
NightSL_Widen_On       = False   L1 待實戰觀察
ConfirmSL_On           = False   L2 待實戰觀察
SP_Night_VolConfirm_On = False   待實戰觀察
```

### 其他保留 v1.9.5 值
```
BBLen 45, BBStd 2.0, BWLookback 120, ATR_Len 14, TargetATRMult 2
MaxBars 35, UseMidExit True, MidExit_MinBars 2
Thrust_Margin_ATR 0.15, Use_Regime_Filter True
Regime_FastMA 15, Regime_SlowMA 40
Holiday_Flat_Time 415, Settlement_Flat_Time 1230
ML_ActivationPct 20, ML_MinCategories 3
```

---

## 四、Portfolio 配置建議

### 現階段（v1.9.6 上架初期）
| Sleeve | Cap | Rationale |
|--------|-----|-----------|
| S3_L VolSqueezeLong | 5% | Tail risk 12.4% single-trade (2025-04-02 -124K)，保留至實戰驗證 |
| **S3_S VolSqueezeShort** | **3%** | 與 v1.8.0 一致，v1.9.6 樣本 71 vs 24 更 robust，但保留保守初期 |
| L1-L5 + S1 + S3_RPS | 依原 portfolio v3 | 不受本次影響 |

### 模擬期實證後可能調整
- **6 個月模擬 ≥ 20 trades 且 PF > 1.5**：S3_S cap 上調至 5%
- **12 個月模擬 tail 分佈符合預期**：S3_L cap 上調至 8%
- **兩者合計 squeeze sleeve**：初期 8%（3+5），未來目標 13-16%

---

## 五、監控指標（每週 review）

| 指標 | 綠燈 | 黃燈 | 紅燈（立即下架）|
|------|------|------|--------------|
| 週 PF | > 1.5 | 0.8-1.5 | < 0.8 連 4 週 |
| 週 trade 數 | 1-5 | 6-10 or 0 | > 10 or 0 連 8 週 |
| 週最大單筆虧損 | < 2% 帳戶 | 2-4% | > 5% |
| 累計 MDD | < 20% | 20-25% | > 25% |
| Regime block 佔比 | 30-70% | 20-30% or 70-80% | > 80% or < 10% 連 4 週 |

---

## 六、Live Simulation Config

```
Signal:             S3_VolSqueezeShort
MC Load Name:       STRATEGY_GEN_S3_VolSqueezeShort
Data1:              TXF1 1M
Data2:              TXF1 60M
Data3:              TXF1 Daily
Symbol:             TXF1 (front-month continuous)
Initial Capital:    1,000,000 NTD (獨立 sleeve, 用戶 2026-07-04 ruling)
Contract:           大台 TX 1 口
Cost:               1000 NTD round-trip
IOG:                False (strategy internal)
Max Bars Back:      >= 1000
Registry Expire:    1270101 (2027-01-01)
```

---

## 七、Kill 觸發條件

**Rule #14/17 legacy**：
- Manual_Kill_Switch = True → 立即 flat
- Registry_Valid_Until 到期 → 進場 gate 自動 block

**模擬期新增（Rule #16 五支柱）**：
- 模擬 MDD > 25% 帳戶 → 立即下架
- 連 4 週 PF < 0.8 → review + 潛在下架
- 連 8 週 0 trade → 檢視 Regime filter 是否誤 block
- Anti-Hunt L1/L2 開啟後績效反轉 → 立即回退預設 OFF

---

## 八、Anti-Hunt L1+L2 觀察計畫

Round 1 已落實 code，預設 OFF。

**Live simulation 觀察**：
- 若夜盤實際遇到 stop hunting → 記錄 log 並考慮開啟 L1 (NightSL_Widen_On)
- 若單根 spike SL 觸發 → 考慮開啟 L2 (ConfirmSL_On)
- 每次開啟前必回測對照，避免 overfit

---

## 九、決策時間軸

- **2026-06-30**: v1.7.3-FINAL → v1.8.0-PROD promote
- **2026-07-02**: v1.9.4 → v1.9.5 GA optimize（68T / +513K / PF 1.574）
- **2026-07-04**: v1.9.6-ANTIHUNT Round 1 落實（anti-hunt L1+L2 + BWRank bug + Exit/SP 強化）
- **2026-07-05**: 筆電端跑 Config A/B/C/D + 5-param GA OPT
- **2026-07-06**: 桌機 Rule #18 7/7 gates PASS + Stress 6/6 PASS
- **2026-07-06**: **PROMOTE v1.8.0-PROD → v1.9.6-OPT-PROD**（本次）

---

## 十、附件連結

- 完整 spec: [../research/S03_VolSqueezeShort/v196_ANTIHUNT_spec_20260704.md](../research/S03_VolSqueezeShort/v196_ANTIHUNT_spec_20260704.md)
- MC + Bootstrap: [../research/S03_VolSqueezeShort/v196_ANTIHUNT_MC_bootstrap_OPT_20260706.md](../research/S03_VolSqueezeShort/v196_ANTIHUNT_MC_bootstrap_OPT_20260706.md)
- Stress Test: [../research/S03_VolSqueezeShort/v196_ANTIHUNT_stress_test_20260706.md](../research/S03_VolSqueezeShort/v196_ANTIHUNT_stress_test_20260706.md)
- 未解決 + 實戰: [../research/S03_VolSqueezeShort/v195_unresolved_and_realworld_20260703.md](../research/S03_VolSqueezeShort/v195_unresolved_and_realworld_20260703.md)
- Archived v1.8.0: [../research/archive/S3_S_v180_replaced_20260706/](../research/archive/S3_S_v180_replaced_20260706/)

---

**Prepared by**: Claude Opus 4.7 + 用戶 DRwillychiu
**Approve by**: 用戶 2026-07-06 verbal ruling ("撰寫成正式版本，然後開始進行上架模擬")
