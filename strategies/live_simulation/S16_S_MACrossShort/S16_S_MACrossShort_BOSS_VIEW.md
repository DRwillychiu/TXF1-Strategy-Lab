# S16_S MACrossShort — BOSS VIEW

**Version**: v1.4-BELATE | **Cap**: 3% | **Deployed**: 2026-07-10 (合規 07-16 / 護欄+保本延後 07-18)

---

## 一句話定位

**5M 台指期極短動能爆發空頭狙擊手（Sniper）**：只做主場，其他不做或小虧。
**只賺紀律內的錢**：時間護欄（04:30 最晚進場 / 04:40 強制平倉）+ 63 假日封鎖 —
任何部位**結構上不可能**跨休市。

---

## Core Metrics（6.3 年 backtest，數據至 2026-07-18，v1.4 FINAL baseline）

| 指標 | 值 | vs v1.0.1 合規版 |
|------|---|------------------|
| Net | **+1,073,200 NTD** | +239,600 (+28.7%) |
| PF | **1.88** | +0.20 |
| MDD | **-228,000 (-18.6%)** | 改善 43,600 |
| WR | 26.6% | +3.9pp |
| Win:Loss | **5.2 : 1** | — |
| Sharpe (年化) | +0.57 | +0.09 |
| Sortino | **0.98** | +0.57 |
| 恢復因子 | **4.71** | +1.64 |
| 最大連虧 | **10 次** | 從 13 次改善 |
| Trades | 109 (17/年) | -1 |

> 單日四段演進 (2026-07-18)：v1.0-PROD (+1,028K，含彩券單) → v1.0.1 合規 (+833.6K)
> → v1.3 時間護欄 (+888.4K) → **v1.4 保本延後 (+1,073.2K)**。
> v1.4 已超越含彩券單的 v1.0-PROD 原始數字，且合規、MDD 更低。
> G-tracks 全記錄見 [`S16_S_OPEN_ISSUES_20260713.md`](../research/S16_MACrossShort/S16_S_OPEN_ISSUES_20260713.md)

---

## Alpha 結構（全數值與 MC 淨利交叉驗證一分不差）

| 出場機制 | 筆數 | Net | 角色 |
|---------|-----|-----|------|
| TimeStop (2hr) | 23 | **+2,187,600** (100% WR) | 🎯 全部 alpha |
| GoldenCross | 3 | +87,600 (100% WR) | 輔助 |
| TailFlat (v1.3) | 1 | +21,400 (100% WR) | 收盤前護欄 |
| BE_Trail ×2 (v1.4 延後) | 3 | +600 | 晚期守門員 |
| ML_Exit (Rule #17) | 1 | -14,000 | 首次參戰 |
| QuickStop ×2 | 78 | -1,210,000 | 🛡️ 控損成本 |

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

- 原版 WFE 77.4% — INVALIDATED（窗口重疊+污染，見 [`S16_S_WFA_AUDIT_20260718.md`](../research/S16_MACrossShort/S16_S_WFA_AUDIT_20260718.md)）
- **乾淨版 W4 WFA (v1.4)：WFE 42.5%，FAIL** — 但 FAIL 的是「滾動重最佳化」流程：同 4.5 年 OOS，滾動 -172,800 vs **固定參數 +830,800（差 100 萬）**。W6 whipsaw：滾動 -440K vs 固定 +49K。詳見 [`W4_WFA_v14_analysis_20260718.md`](../research/S16_MACrossShort/W4_WFA_v14_analysis_20260718.md)
- **⛔ 參數凍結鐵則（2026-07-18）**：禁止定期 GA 重最佳化；重評估僅限結構性觸發（指數>55K / 紅線）
- **Rule #18 5 件套 (v1.4 官方數據集 718)：通用 4/5 PASS / 適性 5/5 PASS** — MC 適性重驗（月區塊 Bootstrap 保留贏虧共聚）95% MDD 26.7% 過 30% gate；冷啟動最壞開局實測 -169,800；IID 洗牌 38.1% 保留為壓力包絡。維持 1M sleeve + 3% cap + 25% 暫停紅線。詳見 [`S16_S_v14_fivepiece_20260718.md`](../research/S16_MACrossShort/S16_S_v14_fivepiece_20260718.md)
- **官方 baseline (MaxBarsBack=200)**：**107T / +1,094,800 / PF 1.910 / MDD -228,000 / WR 27.1%**
- **身分修正**：alpha 全在 Volatile regime (87T, PF 2.06)；Bear 僅 3 筆 —「崩盤/波動收割者」非「熊市策略」。風險告知：真實 95% DD 潛力 ≈ -380K（配置資本須承受）
- Forward OOS 初步：參數定案（07-10）後的 7/14-17 交易 +175,200（4 筆）
- **時框 robustness 已驗證（2026-07-18）**：10M 移植版獨立獲利（PF 1.61 / +615,600），架構非 5M 巧合；同時實證 5M 粒度全維度優勢（恢復因子 4.80 vs 1.32）。詳見 [`S16_S_10M_FINAL_SUMMARY_20260718.md`](../research/S16_MACrossShort_10M/S16_S_10M_FINAL_SUMMARY_20260718.md)
- **Rule #19 PROMOTE_CHECKLIST** + L-P6 WFA 跨度驗證鐵則

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
| G6 | 時間護欄（最晚進場+強制平倉）| ✅ DONE (v1.3, +54.8K) |
| G1 | 進場漏斗統計（7,746 死叉 98.5% 拒絕）| ✅ DONE (嚴選確認, G4 降級) |
| G2 | TimeStop 12/24/36/48 對比 | ✅ **CLOSED — 24 雙向實證最優** (36/48 MDD 爆 -575K) |
| G3 | BE_Trail 延後啟動 | ✅ **DONE (v1.4, +184.8K, 高原驗證通過)** |
| G4 | 雙 gate 抓取（連續型斜率）| ⏸️ MED-LOW（G1 量化天花板僅 20-60 筆候選）|

G4 驗收 KPI（若啟動，v1.4 基準）：Net ≥ +1,148K / PF ≥ 1.72 / MDD ≤ -251K / TimeStop ≥ 21 筆。

---

**Reviewed & Approved for Simulation** ✅
