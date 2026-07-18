# S16_S MACrossShort — BOSS VIEW

**Version**: v1.3-TIMEGUARD | **Cap**: 3% | **Deployed**: 2026-07-10 (合規 patch 07-16 / 時間護欄 07-18)

---

## 一句話定位

**5M 台指期極短動能爆發空頭狙擊手（Sniper）**：只做主場，其他不做或小虧。
**只賺紀律內的錢**：時間護欄（04:30 最晚進場 / 04:40 強制平倉）+ 63 假日封鎖 —
任何部位**結構上不可能**跨休市。

---

## Core Metrics（6.3 年 backtest，數據至 2026-07-18，v1.3 FINAL baseline）

| 指標 | 值 | vs v1.0.1 |
|------|---|-----------|
| Net | **+888,400 NTD** | +54,800 |
| PF | **1.74** | +0.06 |
| MDD | **-249,600 (-21.3%)** | 改善 22,000 |
| WR | 23.9% | +1.1pp |
| Win:Loss | **5.5 : 1** | — |
| Sharpe (年化) | +0.53 | +0.05 |
| 恢復因子 | 3.56 | +0.49 |
| 最大連虧 | **10 次** | 從 13 次改善 |
| Trades | 109 (17/年) | -1 |

> 演進：v1.0-PROD (+1,028K，含跨連假彩券單) → v1.0.1 合規 (+833.6K) →
> **v1.3 時間護欄 (+888.4K，全指標同步改善)**。
> 護欄擋掉 1 筆跨早盤空窗 gap 虧損 (-32,800)、提早 1 筆尾端出場 (+22,000)。
> 詳見 [`S16_S_HOLIDAY_IMPACT_20260717.md`](../research/S16_MACrossShort/S16_S_HOLIDAY_IMPACT_20260717.md)

---

## Alpha 結構（全數值與 MC 淨利交叉驗證一分不差）

| 出場機制 | 筆數 | Net | 角色 |
|---------|-----|-----|------|
| TimeStop (2hr) | 21 | **+1,986,200** (100% WR) | 🎯 全部 alpha |
| GoldenCross | 3 | +87,600 (100% WR) | 輔助 |
| TailFlat (v1.3) | 1 | +21,400 (100% WR) | 收盤前護欄 |
| QuickStop ×2 | 74 | -1,153,400 | 🛡️ 控損成本 |
| BE_Trail ×2 | 10 | -53,400 | ⚠️ 檢驗中 (G3) |

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
| G6 | 時間護欄（最晚進場+強制平倉）| ✅ **DONE 07-18 (v1.3, +54.8K)** |
| G1 | Debug print 漏單統計 | 待實作 (next) |
| G2 | TimeStop 12/24/36/48 對比 | 待實作（G6 已為前置）|
| G3 | BE_Trail A/B/C（-53.4K 疑似 alpha 洩漏）| 待實作 |
| G4 | 雙 gate 抓取（突然高斜率 + 連續型斜率）| 待實作 |

KPI 錨定 v1.3 FINAL baseline：Net ≥ +950K / PF ≥ 1.60 / MDD ≤ -275K / TimeStop ≥ 19 筆。

---

**Reviewed & Approved for Simulation** ✅
