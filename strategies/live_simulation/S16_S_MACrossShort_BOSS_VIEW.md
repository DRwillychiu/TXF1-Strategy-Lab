# S16_S MACrossShort — BOSS VIEW

**Version**: v1.0-PROD | **Cap**: 3% | **Deployed**: 2026-07-10

---

## 一句話定位

**5M 台指期極短動能爆發空頭狙擊手（Sniper）**：只做主場，其他不做或小虧。

---

## Core Metrics（6.5 年 backtest）

| 指標 | 值 |
|------|---|
| Net | **+1,028,600 NTD** |
| PF | **1.885** |
| MDD | **-17.97%** (帳戶) |
| WR | 22.6% |
| Win:Loss | **6.8 : 1** |
| Sharpe | +0.46 |
| Trades | 106 (16/年) |

---

## Regime Identity

| Regime | Net | PF | 定位 |
|--------|-----|-----|------|
| **Bear** | +590K | **3.79** | 🎯 主場 |
| **Volatile / Crash** | +591K | 2.13 | 🎯 主場 |
| Bull | -106K | 0.70 | 🛡️ 保險成本 |

---

## W4 WFA 通過（**強於 S3_S**）

- **WFE 77.4%** (gate > 50%) ✅
- 9 windows / 416 OOS trades / +1.74M
- 7/9 windows PASS
- **無需 Path A 豁免**（S3_S 需要）

---

## W5 Sniper 5 件套 8/8 PASS

- 破產率 0.03% / Kelly 11.2% / Bear PF 3.79 / Volatile PF 2.13

---

## 部署 Caveats

1. **3% portfolio cap**（新策略保守）
2. **Bull whipsaw 保險成本可能 -30% MDD**（W6 evidence）
3. **建議搭配 S3_L 多頭 sleeve 補位**
4. **模擬期預估 24 個月**（累積 30 筆才升 live）

---

## 監控紅線

🚨 立即暫停：MDD > 25% / 連虧 8 筆/月 / PF < 0.8 連 3 月
⚠️ Review：月 trade > 15 / 12 月 0 trade / 連 2 月 -10%

---

## Portfolio 唯一動能 sleeve

台指期 5M 短期動能捕捉，與其他策略（S3_S 波動率、L1-L5 趨勢/盤整）**低相關**。
在 crash 事件時提供集中獲利（2025-04 Trump / 2026-06 Jun），bull 期間承擔保險成本。

---

**Reviewed & Approved for Simulation** ✅
