# FOMC Night Session Risk Analysis

**Date**: 2026-07-25
**Scope**: Cross-strategy reference — applies to any TXF1 night session strategy
**Data**: 62 FOMC dates (2019-01 ~ 2026-07), 515 L1 TrendLong V3.1 trades, 2M+ 1-min bars
**Status**: Research complete, no code changes

---

## Executive Summary

FOMC 夜盤交易的風險低於直覺預期。L1 的結構（45M bar + ATR*2 門檻 + IOG）提供天然保護，X4 score filter 處理殘餘風險。不需要 FOMC-specific shutdown rule。但 FOMC 前夕波動有逐年升高趨勢（2026 已達 170pts），且 Fed 政治面（派系/主席風格）屬質化風險，需交易員 discretionary judgment 補充。

---

## 1. Core Finding: FOMC Nights Are Not the Death Trap Expected

| Metric | FOMC night | Normal night |
|--------|-----------|-------------|
| Avg range (pts) | 261 | 222 |
| Avg \|direction\| | 142 | 115 |
| L1 trigger rate | 21.4% | 13.4% |
| L1 avg PnL when triggered | +3,950 | +6,143 |

FOMC 夜盤波動大 17%，但**淨方向性移動更大 23%**。對趨勢策略是好事。

L1 在 FOMC 夜盤的 WR 54.5%（n=11），高於一般夜盤 34.0%。原因：73% 的 FOMC 夜盤進場發生在公布後 1-3h，搭的是 post-FOMC continuation，不是被洗。

---

## 2. Year-by-Year FOMC Night Results

| Year | FOMC dates | L1 night trigger | Avg range | Night PnL | WR |
|------|-----------|------------------|-----------|-----------|-----|
| 2019 | 7 | 0/7 | 86 | — | — |
| 2020 | 7 | 2/7 | 128 | -27,000 | 0% |
| 2021 | 8 | 2/8 | 173 | -31,600 | 0% |
| 2022 | 8 | 1/8 | 282 | +27,000 | 100% |
| 2023 | 8 | 3/8 | 167 | +135,600 | 100% |
| 2024 | 7 | 2/7 | 340 | +60,600 | 100% |
| 2025 | 7 | 1/7 | 351 | -16,600 | 0% |
| 2026 | 4 | 1/4 | 818 | -100,600 | 0% |

2025 觸發率極低（1/7），原因是 ATR 門檻隨波動自動拉高。2026 avg range 818 是 regime shift，非 FOMC 特有問題。

---

## 3. Pre-FOMC Open Positions: Do NOT Close

**9 trades were open when FOMC hit: WR 88.9%, avg PnL +68,089, total +612,800.**

| FOMC date | Hours before | Result | PnL |
|-----------|-------------|--------|-----|
| 2020-06-10 | 224h | WIN | +113,000 |
| 2021-04-28 | 130h | WIN | +42,000 |
| 2022-12-14 | 14h | SL | -16,800 |
| 2023-03-22 | 41h | WIN | +62,000 |
| 2023-06-14 | 120h | WIN | +44,400 |
| 2024-06-12 | 14h | WIN | +248,800 |
| 2024-07-31 | 10h | WIN | +25,800 |
| 2024-11-07 | 14h | WIN | +19,600 |
| 2026-01-28 | 50h | WIN | +74,000 |

FOMC 30-min spike 從未超過這些持倉的 SL 距離。趨勢已在車上，FOMC 只是加油。

**Rule: 已持有部位遇到 FOMC，絕對不提前平倉。**

---

## 4. Entry Proximity to FOMC

| Distance | n | SL% | WR% | Avg PnL |
|----------|---|-----|-----|---------|
| 0-3h BEFORE | **0** | — | — | — |
| 3-6h BEFORE | **0** | — | — | — |
| 6-12h before | 3 | 66.7% | 33.3% | +667 |
| 0-3h AFTER | 10 | 50.0% | 50.0% | +4,540 |
| >12h from FOMC | 494 | 57.5% | 34.6% | +4,225 |

**L1 從未在 FOMC 前 6 小時內開倉。** 市場在等公布，盤整不動，不產生突破信號。

---

## 5. Intra-Minute Whipsaw Analysis

### 5.1 FOMC 公布後 10 分鐘 whipsaw 分布

| Whipsaw range | Frequency | vs SL (avg 92pts) |
|--------------|-----------|-------------------|
| < 50 pts | 33/56 (59%) | SL safe |
| 50-100 pts | 15/56 (27%) | Borderline |
| 100-200 pts | 5/56 (9%) | May trigger SL |
| 200-500 pts | 2/56 (4%) | Will trigger SL |
| 500+ pts | 1/56 (2%) | Catastrophic (2026-06-17 only) |

Avg 10-min whipsaw: 70 pts. Max: 908 pts (2026-06-17).

### 5.2 Spike → Entry → Reversal → SL 場景

56 次 FOMC 中：
- 23 次 (41%) spike 碰到 L1 的 BO level
- 其中 4 次 (7.1%) 反轉幅度大到足以打掉 SL
- 實際 L1 進場且被打掉的：2 次
  - 2020-07-29: SL -13,600（正常損失）
  - 2026-06-17: SL -100,600（Score=1，X4 會殺掉）
- 另 2 次被 IOG/45M bar 條件擋住，L1 沒進場

### 5.3 2026-06-17 極端案例（分鐘級）

```
+0m: H+15 L+4     ← FOMC 公布瞬間
+1m: H+9  L-305   ← 第 1 分鐘暴跌 305 pts
+5m:       L-552   ← 5 分鐘跌 552 pts
+6m:       L-893   ← 6 分鐘跌 893 pts (max)
+10m:      反彈到 -423
```

L1 在 03:45（公布後 1h45m）才進場，Score=1。這不是 FOMC 洗刷問題，是品質差的進場。X4 的 score<=1 gate 可處理。

---

## 6. Pre-Announcement Jitters (00:00-02:00)

### 6.1 FOMC 前夕 vs 一般夜盤

| Metric | FOMC eve | Normal night | Ratio |
|--------|----------|-------------|-------|
| Avg range | 61 pts | 70 pts | 0.9x |
| Avg volume | 5,490 | 8,799 | 0.6x |
| Avg 1-min bar range | 4.6 | 5.5 | 0.8x |

歷史平均：FOMC 前夕**比一般夜盤更安靜**。

### 6.2 逐年趨勢（需持續觀察）

| Year | FOMC eve avg range | Avg 1m bar |
|------|-------------------|------------|
| 2019 | 17 | 1.1 |
| 2022 | 61 | 4.4 |
| 2024 | 72 | 5.4 |
| 2025 | 83 | 7.4 |
| **2026** | **170** | **14.9** |

FOMC 前夕波動逐年倍增。目前尚未大到觸發 L1，但趨勢明確。

---

## 7. FOMC-Specific Rule Simulation

| Approach | Trades skipped | PnL impact | Verdict |
|----------|---------------|------------|---------|
| Skip FOMC night entries | 13 | lose +47,400 | WORSE |
| Skip FOMC night + day-after | 21 | lose +58,400 | WORSE |
| Close pre-FOMC positions | 9 | lose +612,800 | DISASTER |
| X4 filter only (current) | 2 | save +86,600 | **BEST** |

---

## 8. Structural Protection Layers

L1 針對 FOMC 風險有四層保護，不需要額外規則：

1. **Market freeze** — FOMC 前 00:00-02:00 市場盤整（range 0.9x, vol 0.6x），不產生突破信號 → L1 不進場
2. **45M bar absorption** — FOMC spike 被壓進 45 分鐘的 OHLCV，High crossed BO 但 Close 沒有 → 信號被吸收
3. **ATR*2 adaptive threshold** — 高波動期 ATR 膨脹 → BO 門檻自動提高 → 只有真趨勢觸發
4. **X4 score filter** — score<=1 的低品質進場被殺掉（涵蓋 2026-06-17 災難）

---

## 9. Qualitative Risk: Fed Politics (Not Codeable)

FOMC 前夕的波動特性取決於：
- 主席風格（hawkish/dovish 傾向）
- 委員會派系消長（鷹派票數 vs 鴿派票數）
- 市場對決議的分歧程度（surprise factor）
- 利率路徑的不確定性（dot plot 分散度）

這些因素**無法寫進系統性規則**。2025-2026 FOMC 前夕波動升高可能與 Fed 政策轉向期的不確定性有關。

**處理方式**：交易員 discretionary judgment 補充系統規則。
- X4 處理可量化風險 → 自動
- Fed 政治面 → 交易員 monitor → 必要時手動暫停策略

---

## 10. Cross-Strategy Applicability

本研究的結論可推廣至其他 TXF1 夜盤策略，但需注意：

| Factor | L1-specific | Cross-strategy |
|--------|------------|----------------|
| 45M bar 吸收效應 | L1 用 45M | 其他 timeframe 保護程度不同 |
| ATR*2 門檻 | L1 特有 | 其他策略的進場條件不同 |
| IOG 行為 | L1 啟用 IOG | 依策略設定而異 |
| SL 0.5% | L1 設定 | SL 越緊 → FOMC whipsaw 風險越高 |
| X4 score filter | L1 research stage | 其他策略需自己的品質 filter |
| Pre-FOMC freeze | 通用 | 所有夜盤策略都受益 |
| Post-FOMC continuation | 通用 | 趨勢類策略共通特性 |
| Fed politics risk | 通用 | 所有策略共同面對 |

**對於 SL 更緊或 timeframe 更短的策略，FOMC whipsaw 風險更高。**
建議新策略上架前都跑一次 FOMC overlap test。

---

## 11. Action Items

- [x] 確認 X4 已涵蓋 FOMC 風險（不需額外規則）
- [x] 確認 pre-FOMC 持倉不應平倉
- [ ] Forward test 期間觀察 FOMC 前夕波動趨勢（2026 H2）
- [ ] 新策略上架時加入 FOMC overlap test（跑本文 Section 5.2 的 spike→entry→SL 檢查）
- [ ] S16_S 等做空策略需反向測試（FOMC spike 向上 → 做空被打）

---

## Data Files

- `scratchpad/fomc_night_analysis.py` — 初版 FOMC 夜盤分析
- `scratchpad/fomc_full_coverage.py` — 62 FOMC dates 全覆蓋掃描
- `scratchpad/fomc_proximity_risk.py` — 進場距離 vs 洗刷風險
- `scratchpad/fomc_intrabar_whipsaw.py` — 分鐘級 spike→entry→SL 模擬
