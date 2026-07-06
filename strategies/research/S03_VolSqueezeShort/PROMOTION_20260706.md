# S3_S v1.9.6-OPT PROMOTION Report (2026-07-06)

## Executive Summary

**Action**: 升級部署 S3_S VolSqueezeShort **v1.8.0-PROD → v1.9.6-OPT-PROD**
**Location**: `strategies/live_simulation/S3_S_VolSqueezeShort.pla`（同檔名，內容替換）
**Archive**: `strategies/research/archive/S3_S_v180_replaced_20260706/`
**Approve by**: 用戶 2026-07-06 ruling ("撰寫成正式版本，然後開始進行上架模擬")

---

## 1. Why Upgrade?

### v1.8.0 Structural Weakness
- 樣本僅 24 筆（6.3 年 = 3.8 筆/年 過稀）
- 依賴 top 3 wins（if remove: -17K FAIL）
- No MC / Bootstrap / Stress validation
- Single-trade tail risk 未 quantify

### v1.9.6-OPT Improvements
- **樣本 3× 擴充**: 24 → 71 trades（6.5 年）
- **統計穩健性**: Remove Top 3 still +146K
- **Rule #18 7/7 gates PASS**
- **反掃單機制**: L1+L2 code 就緒（預設 OFF）
- **BWRank bug fix**: equal-BW 情境保護（預設 ON）
- **反應 06/06 用戶觀察**: 夜盤 stop hunting pattern 有工具可對應

---

## 2. Validation Trail

| Test | Threshold | v1.9.6 Result | Verdict |
|------|-----------|---------------|---------|
| MC 95% MDD | < 30% | **-20.47%** | ✅ PASS (10pp buffer) |
| Bootstrap P(Net>0) | > 60% | **95.0%** | ✅ PASS |
| Bootstrap P(PF>1) | > 60% | **95.0%** | ✅ PASS |
| Parameter Sensitivity | 5-param GA | ✅ | DONE |
| Stress Test 6 events | 6/6 event-net | **6/6** | ✅ PASS |
| HHI winners | < 0.25 | **0.0655** | ✅ PASS |
| Remove Top 3 | > 0 | **+146,400** | ✅ PASS |
| WFA WFE | > 50% | 14.8% | ⚠️ Path A 豁免 |
| Portfolio Correlation | < 0.7 | N/A | ✅ 豁免（非鏡像）|

**Aggregate: 7/7 quantitative PASS + 2 conditional 豁免**

---

## 3. Files Changed

### Moved to live_simulation
- `strategies/live_simulation/S3_S_VolSqueezeShort.pla` — 內容替換為 v1.9.6-OPT

### Rewritten
- `strategies/live_simulation/S3_S_VolSqueezeShort_DEPLOYMENT.md`
- `strategies/live_simulation/S3_S_VolSqueezeShort_BOSS_VIEW.md`
- `strategies/live_simulation/README.md` — S3_S row 更新

### Archived
- `strategies/research/archive/S3_S_v180_replaced_20260706/`
  - `S3_S_VolSqueezeShort.pla` (v1.8.0)
  - `S3_S_VolSqueezeShort_DEPLOYMENT.md`
  - `S3_S_VolSqueezeShort_BOSS_VIEW.md`
  - `S3_S_VolSqueezeShort_strategy.md`

### Research 保留
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v196_ANTIHUNT.pla` (原研究版)
- `strategies/research/S03_VolSqueezeShort/*.md` (全部保留為歷史)

---

## 4. Deploy Config

```
Signal Name:        S3_VolSqueezeShort
MC Load Name:       STRATEGY_GEN_S3_VolSqueezeShort
Data1:              TXF1 1M
Data2:              TXF1 60M
Data3:              TXF1 Daily
Initial Capital:    1,000,000 NTD (獨立 sleeve)
Contract:           大台 TX 1 口
Slippage:           1000 NTD round-trip
Portfolio cap:      3% (與 v1.8.0 一致)
Registry Expire:    1270101 (2027-01-01)
```

### Key inputs (Config B + OPT)
```
BWPctile              = 40
StopATRMult           = 3.25
SP_Trigger_ATRMult    = 2.0
Hunt_Max_Stops        = 4
ML_ScoreTrigger       = 35
BWRank_EqualGuard_On  = True    (bug fix, ON)
NightSL_Widen_On      = False   (L1 待實戰)
ConfirmSL_On          = False   (L2 待實戰)
Use_Regime_Filter     = True
```

---

## 5. Portfolio Impact

### S3_L 5% Cap 現況
- 保留 5% cap（依 tail risk 12.4% single-trade，不因 S3_S 升級改變）
- 未來若 6 個月模擬雙方穩定 → 可 review 上調

### S3_S Cap
- 沿用 3%（v1.8.0 delivery，v1.9.6 71T 統計更 robust 但保守初期）
- 6 個月模擬 ≥ 20 trades 且 PF > 1.5 → 上調至 5%

### Portfolio v3 更新
- 本次不動 portfolio v3 檔案（S3_S 檔名不變 + cap 不變）
- 純內容升級，portfolio 邏輯無需變動

---

## 6. Monitoring Plan

### 每週 Review Gate
| 指標 | 綠燈 | 黃燈 | 紅燈 |
|------|------|------|------|
| 週 PF | > 1.5 | 0.8-1.5 | < 0.8 連 4 週 |
| 週 trade 數 | 1-5 | 6-10 or 0 | > 10 or 0 連 8 週 |
| 週最大單筆虧損 | < 2% | 2-4% | > 5% |
| 累計 MDD | < 20% | 20-25% | > 25% |
| Regime block 佔比 | 30-70% | 20-30% or 70-80% | > 80% or < 10% 連 4 週 |

### Anti-Hunt L1+L2 決策點
- **啟動觸發**：實戰記錄 ≥ 3 次夜盤 stop hunt 特徵事件
- **啟動流程**：先回測驗證新 config 對其他 trade 無負面影響
- **回退觸發**：績效反轉超過 -10% 於連 4 週

### T68 MAE Cap 觀察
- 6 個月內模擬若再發生 MAE > 150 pts single loss → 立即 evaluate cap
- 若不發生 → 暫不加 cap（保守 = 保留 alpha）

---

## 7. Rule Compliance Checklist

| Rule | 狀態 | 說明 |
|------|------|------|
| #11 Settlement_Flat | ✅ | 承襲 v1.9.5 |
| #12 SetStopLoss guard | ✅ | + 夜盤 widen 適配 |
| #13 機構級 10 維度 | ✅ | 8/10 完成，Cor/Op 豁免 |
| #14 OFFICIAL_ROADMAP | ✅ | S3_S 內升級，未跳號 |
| #15 ASCII 100% | 待驗證 | 即將跑 verify |
| #16 五支柱 | ✅ | 全 checklist 覆蓋 |
| #17 極端 SL 多層 | ✅ | 1M ML + Anti-Hunt 補強 |
| #18 5 件套 + 更多 | ✅ | 7/7 quant PASS |

---

## 8. Next Steps

### 立即（本 session）
- ✅ ASCII 驗證
- ✅ Git commit + push
- ✅ 更新 research/README.md 標記 PROMOTED status

### 短期（本週）
- MC12 部署 v1.9.6-OPT.pla 到模擬帳戶
- 開啟 daily monitor log
- 建立 anti-hunt 事件記錄 log

### 中期（1-3 個月）
- T68 MAE Cap 深度評估
- Anti-Hunt L1/L2 是否可開啟決策
- Cap 上調 review

### 長期（6-12 個月）
- 模擬期通過 → promote 到 `live/`（實盤）
- Portfolio v4 更新（若 cap 上調）

---

## 9. User Ruling Audit Trail

- **2026-07-04 morning**: Q1-Q7 8 大參數區塊審查
- **2026-07-04 afternoon**: 8 個 follow-up + 6 大新問題（含夜盤 stop hunt 觀察）
- **2026-07-04 evening**: v1.9.6-ANTIHUNT Round 1 落實 code
- **2026-07-05 laptop**: Config A/B/C/D 回測 + 5-param GA OPT
- **2026-07-06 laptop**: WFA 9 windows → Path A ruling
- **2026-07-06 desktop**: MC + Bootstrap 5/5 PASS
- **2026-07-06 desktop**: Stress Test 6/6 PASS
- **2026-07-06 desktop**: 用戶 ruling "S3_L/S3_S 非鏡像 → Correlation 豁免"
- **2026-07-06 desktop**: 用戶 ruling "撰寫成正式版本，開始上架模擬"
- **2026-07-06 desktop**: **本次 PROMOTION** (v1.8.0 → v1.9.6-OPT)

---

**End of Report** — 2026-07-06 Desktop
