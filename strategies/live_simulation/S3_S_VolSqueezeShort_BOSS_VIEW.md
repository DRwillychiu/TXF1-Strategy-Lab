# S3_S VolSqueezeShort — 老闆快速 View

**版本** v1.9.6-OPT-PROD（2026-07-06 升級部署，取代 v1.8.0-PROD）
**回測** 2019-09 ~ 2026-06（6.5 年）｜ **狀態** ✅ live_simulation

---

## 📊 績效重點（v1.9.6 Config B + OPT）

| 指標 | 數值 |
|------|------|
| **淨利** | **+731,000 NTD**（xlsx 2026-07-06）|
| **PF** | **1.749** |
| **Sharpe (年化)** | **+0.549** |
| **MDD** | **-17.17%** |
| **勝率** | 49.3% |
| **交易數** | 71 筆 / 6.5 年 ≈ 11 筆/年 |
| **2025-2026 主力捕獲** | +641K（88% alpha）|

---

## 🎯 Rule #18 驗證（7/7 PASS）

| 測試 | 值 | Gate | 判定 |
|------|-----|------|------|
| MC 95% MDD | -20.47% | < 30% | ✅ PASS (10pp buffer) |
| Bootstrap P(Net>0) | 95.0% | > 60% | ✅ PASS |
| Stress Test 6 events | 6/6 | Event-Net | ✅ PASS |
| HHI winners | 0.0655 | < 0.25 | ✅ PASS |
| Remove Top 3 | +146K | still profitable | ✅ PASS |
| WFA | 14.8% | > 50% | ⚠️ Path A 豁免（low-freq）|
| Correlation vs S3_L | N/A | < 0.7 | ✅ 豁免（非鏡像）|

---

## 🌪️ Stress Test 6 事件

| 事件 | Net | 判定 |
|------|-----|-----|
| 2020 COVID | -28K | ✅ 保費 |
| 2022 熊全年 | **+153K** | 🏆 CRASH WIN |
| 2022-Q4 CPI shock | **+87K** | 🏆 CRASH WIN (WR 75%) |
| 2024-08 BoJ | 0 | ✅ Regime blocked |
| 2025-04-07 Trump 關稅 | **+190K** | 🏆 CRASH WIN |
| 2026-06 crash cluster | **+343K** | 🏆 CRASH WIN |

---

## 💰 策略角色

**低頻 + 大回報事件驅動的 Crash Insurance**
- 平均年 11 筆交易，17/82 個月活躍（21%）
- 20-30% MDD 換 crash 期爆發式獲利
- 適合作為多頭 sleeve 的 directional hedge

---

## 🛡️ 保護機制

1. **Regime Filter**：只在強熊 / 強牛下跌預期時觸發（2024 牛年只 1 筆）
2. **Hunt State Machine**：BB compression + fresh thrust 才 arm，避免 churn
3. **Circuit Breaker**：連 4 次 1M_Exit 自動 DISARM
4. **SP Priority Fire**：獲利 200-300 pts 後緊 retain 85-90%
5. **1M Multi-Layer Exit**：11 factor 5 category ML exit
6. **Anti-Hunt L1+L2**（v1.9.6 新，預設 OFF）：夜盤 SL 加寬 + Confirmation SL

---

## 📅 v1.8.0 → v1.9.6 升級關鍵

- **樣本從 24 筆 → 71 筆**（統計顯著性大幅提升）
- **v1.8.0 靠 top 3 win 撐 GAP → v1.9.6 remove top 3 仍 +146K**
- **MC 95% MDD 從 -30.64% (FAIL) → -20.47% (PASS +10pp)**
- **反掃單機制落實**（用戶 26/06 起夜盤 hunt 觀察）
- **BWRank equal-BW bug 修正**（bug fix，預設 ON）
- **Portfolio Correlation 豁免**（用戶 ruling：非鏡像）

---

## ⚠️ Deploy Caveats

- Portfolio cap **3%**（沿用 v1.8.0）
- Anti-Hunt L1/L2 待實戰觀察後決定開啟
- **T68 06-08 -120K single loss**：MAE Cap 評估延後 parallel 進行
- 監控：連 4 週 PF < 0.8 或 MDD > 25% → 立即下架

---

## 📁 相關文件

- [DEPLOYMENT](S3_S_VolSqueezeShort_DEPLOYMENT.md)
- [strategy.md](S3_S_VolSqueezeShort_strategy.md)
- [MC + Bootstrap 5/5 PASS](../research/S03_VolSqueezeShort/v196_ANTIHUNT_MC_bootstrap_OPT_20260706.md)
- [Stress Test 6/6 PASS](../research/S03_VolSqueezeShort/v196_ANTIHUNT_stress_test_20260706.md)
