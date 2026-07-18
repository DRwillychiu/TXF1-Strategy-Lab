# S16_S MACrossShort — BOSS VIEW

**Version**: v1.0.1-HOLIDAY | **Cap**: 3% | **Deployed**: 2026-07-10 (合規 patch 2026-07-16)

---

## 一句話定位

**5M 台指期極短動能爆發空頭狙擊手（Sniper）**：只做主場，其他不做或小虧。
**只賺紀律內的錢**：63 假日進場封鎖 + 絕不持倉跨休市。

---

## Core Metrics（6.3 年 backtest，數據至 2026-07-18，合規 baseline）

| 指標 | 值 |
|------|---|
| Net | **+833,600 NTD** |
| PF | **1.67** |
| MDD | **-271,600 (-23.8%)** |
| WR | 22.7% |
| Win:Loss | **5.7 : 1** |
| Sharpe (年化) | +0.48 |
| 恢復因子 | 3.07 |
| Trades | 110 (17/年) |

> 舊版 v1.0-PROD 數字 (+1,028K / PF 1.885) 含一筆違反假日鐵律的跨連假彩券單 (+370K)，
> 2026-07-16 合規 patch 後移除。**MDD / 毛損完全不變** — 拿掉的是運氣，不是 alpha。
> 詳見 [`S16_S_HOLIDAY_IMPACT_20260717.md`](../research/S16_MACrossShort/S16_S_HOLIDAY_IMPACT_20260717.md)

---

## Alpha 結構（全數值與 MC 淨利交叉驗證一分不差）

| 出場機制 | 筆數 | Net | 角色 |
|---------|-----|-----|------|
| TimeStop (2hr) | 21 | **+1,986,200** (100% WR) | 🎯 全部 alpha |
| GoldenCross | 3 | +87,600 (100% WR) | 輔助 |
| QuickStop ×2 | 75 | -1,186,200 | 🛡️ 控損成本 |
| BE_Trail ×2 | 11 | -54,000 | ⚠️ 檢驗中 (G3) |

---

## Regime Identity

| Regime | 定位 |
|--------|------|
| **Bear / Crash** | 🎯 主場（W5-era: Bear PF 3.79 / Volatile PF 2.13，含已移除彩券單，待重跑）|
| Bull | 🛡️ 保險成本（可控小虧）|

**2026-07 實戰級證據（模擬）**：台股 7 月 DD 危機（L1-L5 帳戶 -21.3%）期間，
S16_S 單月 14 筆 **+264,000** — 空方對沖本職到位。

---

## 驗證狀態

- **W4 WFA WFE 77.4%**（9 windows，v1.0-PROD 時代數據，一個 OOS window 含彩券單 → 數字偏樂觀，結構結論仍成立）
- **W5 Sniper 5 件套 8/8 PASS**（同上註記）
- **Rule #19 PROMOTE_CHECKLIST**：因本策略 placeholder 事件而生（2026-07-16）

---

## 部署 Caveats

1. **3% portfolio cap**（新策略保守）
2. **Bull whipsaw 保險成本**（W6 evidence -30% 級 MDD 可能）
3. **建議搭配 S3_L 多頭 sleeve 補位**
4. **模擬期預估 24 個月**（累積 30 筆才升 live）
5. **Registry 2026-12 前需 refresh 2027-2028 假日**（F2 議題）

---

## 監控紅線

🚨 立即暫停：MDD > 25% / 連虧 8 筆/月 / PF < 0.8 連 3 月
⚠️ Review：月 trade > 15（**2026-07 已達 14，逼近紅線，高頻月屬 crash regime 正常但需留意**）/ 12 月 0 trade / 連 2 月 -10%

---

## 進行中優化（G-tracks，2026-07-16 確立）

| Track | 內容 | 狀態 |
|-------|------|------|
| G1 | Debug print 漏單統計 | 待實作 |
| G2 | TimeStop 12/24/36/48 對比 | 待實作 |
| G3 | BE_Trail A/B/C（-54K 疑似 alpha 洩漏）| 待實作 |
| G4 | 雙 gate 抓取（突然高斜率 + 連續型斜率）| 待實作 |

KPI 錨定新 baseline +833,600 / PF 1.67 / TimeStop ≥ 19 筆。

---

**Reviewed & Approved for Simulation** ✅
