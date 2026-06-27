# strategies/research/archive/ — 歸檔策略與歷史資料

> 包含原始批次排程雛形、已 KILL / 已升等策略開發歷史、off-roadmap 產物。
> 當前開發嚴守 OFFICIAL_ROADMAP 單軌順序（Rule #14）。

---

## 歷史批次清單

### batch01_S2-S5/（原始批次）
- **位置**：[`batch01_S2-S5/`](batch01_S2-S5/)
- **產出日期**：~2026-06-07 之前
- **內容**：
  - S2 InsideBarBreak
  - S3 VolSqueeze
  - S4 MACDDivergence
  - S5 SettlementWeek
- **歷史備註**：原批次也含 S1 NightMomentum，但 S1 已通過 P1-P3 升級至 `live_simulation/`

### batch02_S6-S10/（指數位階論系列）
- **位置**：[`batch02_S6-S10/`](batch02_S6-S10/)
- **產出日期**：2026-06-07
- **動機**：2026/06/05 夜盤台指期崩跌 3006 點（-6.2%），暴露現有策略組合三個結構性缺口
- **內容**：
  - S06 FlashCrashMomentum（閃崩動量做空）
  - S07 BullPullbackLong（多頭回檔抄底）
  - S08 BearBounceSell（空頭反彈放空）
  - S09 VolExplosion（波動爆發）
  - S10 AdaptiveBreakout（自適應突破）
- **共通設計**：ATR-based 或百分比自適應（指數位階從 10000→45000+，固定點數不適用）

### batch03_S11-S15/（多策略類型擴展）
- **位置**：[`batch03_S11-S15/`](batch03_S11-S15/)
- **產出日期**：2026-06-07
- **內容**：
  - S11 MiddayCompression（A 類時段型，45M 做多，PF 2.28 🥈）
  - S12 WeekdayMomentum（E 類統計型，日線雙向，PF 0.90 🥉）
  - S13 VolCollapseShort（C 類波動率型，30M 做空，PF 1.58 ⚠️低頻）
  - S14 TripleTFTrend（F 類多時間框架，15M 雙向，PF 1.86 🥇）
  - S15 BBReversion（B 類價格結構型，60M 雙向，PF 9.03 ⚠️異常）

### _batch_summaries/（跨批次摘要）
- **位置**：[`_batch_summaries/`](_batch_summaries/)
- **內容**：
  - TXF1_Strategies_Batch02.md
  - TXF1_Strategies_Batch03.md
- **備註**：Batch01 摘要在 `batch01_S2-S5/TXF1_Strategies_Batch01.md`（已移除重複）

### S03_VolSqueezeLong_promoted_20260620/（已升等）
- **位置**：[`S03_VolSqueezeLong_promoted_20260620/`](S03_VolSqueezeLong_promoted_20260620/)
- **內容**：S3_L W0-W5 開發歷史（.pla、W5 10-dim eval、handoff、分析腳本）
- **保留原因**：production .pla 在 `live_simulation/`，此處保留開發 audit trail

### S3_S_v2_killed_20260626/（KILLED）
- **位置**：[`S3_S_v2_killed_20260626/`](S3_S_v2_killed_20260626/)
- **內容**：v2.0 ride-to-end thesis disproved（PF 1.18 → 0.86）
- **保留原因**：KILL 決策紀錄

---

## 為什麼歸檔？

2026-06-13 用戶決議：
> 「每週會更新 5 組策略，因此絕對必須分門別類，用時間點去區分資料夾。」

歷史批次（S2-S15）保留於此供：
1. **參考**：未來研究可借鏡的設計（如 ATR-based 自適應、Wyckoff Spring、Donchian 突破）
2. **比較**：新週批次策略 vs 歷史方案
3. **資料完整性**：不刪除，git 完整保留

---

## 重新啟用歷史策略？

若想把某隻歷史策略提升到當前週批次研究，建議：
```bash
# 例：把 S14 TripleTFTrend 移到 W24 重新評估
git mv strategies/research/archive/batch03_S11-S15/S14_TripleTFTrend \
       strategies/research/2026-W24/S14_TripleTFTrend
```

但通常不建議——歷史檔已封存，新週批次採用新編號（S16 起）較清晰。

---

## 與 live/ 上架策略的對應

- **L1 TrendLong** 對應原 NightMomentum 早期版本（v1.0）的趨勢概念
- **L2 TrendShort** 對應 AdaptiveFarmer 趨勢空頭專案（不在 S 系列）
- **L3 ConsolidationLong** 對應 Adaptive Farmer 純做多版本
- **L4 ConsolidationShort** 對應 Adaptive Farmer 純做空版本（Wyckoff Spring）
- **L5 BreakoutLong** 對應 Adaptive Farmer God Mode 突破版本
- **S1 NightMomentum** → 已升級到 `live_simulation/`，原 batch01 位置已遷移

L1-L5 開發 **早於** S 系列研究編號系統，不屬於此 archive 範圍。
