# S3_S VolSqueezeShort — DEPLOYMENT (v1.7.3-PROD)

**Promote 日**：2026-06-28
**.pla**：`S3_S_VolSqueezeShort.pla` v1.7.3-PROD
**Portfolio cap**：3% account
**R-6 配對**：S3_L VolSqueezeLong（5% cap, 合計 squeeze sleeve 8%）

---

## 一、Deployment Caveats（**部署前必讀**）

### 1. 4 trades/year = 心理紀律壓力極端
- 平均每 3 個月才一筆
- 容易產生「手癢加倉」、「提前止盈」、「乾脆關掉策略」心理偏差
- **必須 set 提醒：沒進場 = 正確守則**

### 2. 2024 Tier S 大魚被擋走是 evidence
- BoJ Aug +316K / AI sell-off +104K → v1.7.3 都沒抓
- 接受 trade-off：「精選 quality + portfolio cover loss frequency」
- 不可因「漏抓大魚」事後改 .pla（違反 L24）

### 3. L24 風險未完全消除
- BlockRange 是 hard-coded zone reject
- 未來 TWII 進入長期 range 可能 filter 失效
- Manual review trigger：12 個月內 0 trades

### 4. 統計顯著性弱
- 31 trades / 8 yr 樣本偏弱
- live_simulation 前 6 個月 paper trade 累積 ≥ 5 trades 才考慮 live

---

## 二、Kill Triggers（自動停用條件）

任一觸發 → 立即停用 + 寫 incident report：

| # | 條件 | 動作 |
|---|------|------|
| 1 | Monthly DD > 5% account（單月虧 > 5%）| 停用 + review |
| 2 | 3 連續 SL（每筆 > -100K）30 天內 | 停用 + review |
| 3 | 12 個月內 0 trades | review filter health |
| 4 | Cluster losses > 3σ outside historical DD | 停用 + emergency review |
| 5 | 模擬期 PF < 1.5 over 30+ trades | review thesis |

---

## 三、Operational Compliance（已驗證）

- ✅ Rule #11 Settlement_Flat（7 elements 完整）
- ✅ Rule #12 P3b SetStopLoss（MP ≥ 0 short variant guard）
- ✅ Rule #13 10-dim eval：v1.7.1 R1 9/10 PASS（band-reject 版本依 portfolio sleeve standard）
- ✅ Rule #14 OFFICIAL_ROADMAP S3_S sequence
- ✅ Rule #15 ASCII 100%（`verify_pla_ascii.py --strict` PASS）
- ✅ HolidayFlat_v3 63-entry registry
- ✅ Manual_Kill_Switch
- ✅ Registry_Valid_Until 1270101

---

## 四、MC12 Chart Setup（**必要**）

| 設定 | 值 |
|------|-----|
| Data1 | TXF1 60M（連續近月）|
| **Data2** | **TXF1 Daily（regime filter 必要）**|
| 策略運算最大使用 K 棒數量 | **1000**（cover MA80 × 19 ratio）|
| Intrabar Order Generation | **False**（.pla 內已 set）|
| Initial Capital | 1,000,000 NTD |
| Slippage | 1,000 NTD round-trip |
| Commission | TBD (按券商) |
| Trade Size | 1 contract |

---

## 五、Final inputs（鎖定）

```
BBLen                = 45
BBStd                = 2.0
BWLookback           = 120
BWPctile             = 25    *** v1.7.3-FINAL tightened ***
ATR_Len              = 14
StopATRMult          = 2.75
TargetATRMult        = 3.5
MaxBars              = 35
UseMidExit           = True
MidExit_MinBars      = 2
SP_Trigger_ATRMult   = 1.5
SP_Retain_Pct        = 70
Cooldown_Days        = 1
Use_Regime_Filter    = True
Regime_FastMA        = 15    *** v1.7.3-FINAL ***
Regime_SlowMA        = 40    *** v1.7.3-FINAL (revised from 80) ***
Regime_BlockRange    = True  *** v1.7.3-PROD band-reject ***
Regime_BlockWeakBull = True
Holiday_Flat_Time    = 415
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230
```

---

## 六、Monitoring Schedule

| 頻率 | 動作 |
|------|------|
| Daily | 確認 strategy alive，無 error log |
| Weekly | 檢視 entries（預期 ~0-1 per week）|
| Monthly | DD check + Kill trigger 評估 + portfolio rebalance |
| Quarterly | 對比回測 PF 偏離度（≤ 30% gate）|
| Annually | Full institutional 10-dim re-eval |

---

## 七、Promote to live/（晉升條件）

| 標準 | 門檻 |
|------|------|
| 模擬期 trades | ≥ 5（v1.7.3 低頻 by design，5 trades = 1 年樣本）|
| 模擬期 PF | ≥ 2.0（high precision design 要求高）|
| 模擬期 MDD | ≤ -25% account |
| 與回測 PF 偏離度 | ≤ 30% |
| 假日鐵律觸發 | 0 次違規 |
| 滑價成本符合預估 | 單邊 ≤ 500 NTD |
| **時程** | **至少 12 個月**（因頻率低）|
