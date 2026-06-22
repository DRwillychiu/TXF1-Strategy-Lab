# optimization/ — 原始 ROADMAP 追蹤系統 + 每策略 Phase 1-4 詳細紀錄

> 此資料夾與 [`docs/policies/OFFICIAL_ROADMAP.md`](../docs/policies/OFFICIAL_ROADMAP.md) **互補**：
> - OFFICIAL_ROADMAP 鎖定策略**名稱與順序**
> - 本資料夾追蹤每隻策略的**績效進度與決策路徑**

---

## 一、TRACKER.md — Master 進度表

[`TRACKER.md`](TRACKER.md) 包含 S1-S15 全部 16 隻策略的：
- 基線淨利 / PF / MDD / 月均交易
- 優化狀態（🔴 未開始 / 🟡 進行中 / 🟢 PASS / ⛔ FAIL / ⏸️ 暫停）
- Phase 1-4 進度
- 最終判定與決策日期
- FAIL 策略墓地

**每次有意義變更必須更新此檔**（commit message 標註 "Update TRACKER"）。

---

## 二、logs/ — 每隻策略 Phase 1-4 詳細紀錄

| Batch | 策略 | log 檔 | 狀態 |
|-------|------|--------|------|
| B01 | S1 NightMomentum | [`logs/B01_S1_NightMomentum.md`](logs/B01_S1_NightMomentum.md) | 🟢 PASS@1M（已部署 live_simulation） |
| B01 | S2 InsideBarBreak | [`logs/B01_S2_InsideBarBreak.md`](logs/B01_S2_InsideBarBreak.md) | ⛔ KILLED 2026-06-22（alpha 已死） |
| B01 | **S3 VolSqueeze** | [`logs/B01_S3_VolSqueeze.md`](logs/B01_S3_VolSqueeze.md) | 🔵 **CURRENT — W0 Pre-verify 待開始** |
| B01 | S4 MACDDivergence | [`logs/B01_S4_MACDDivergence.md`](logs/B01_S4_MACDDivergence.md) | ⏳ Queue（S3 後） |
| B01 | S5 SettlementWeek | [`logs/B01_S5_SettlementWeek.md`](logs/B01_S5_SettlementWeek.md) | ⏳ Queue |
| B02 | S6 FlashCrashMomentum | [`logs/B02_S6_FlashCrashMomentum.md`](logs/B02_S6_FlashCrashMomentum.md) | ⏳ Queue |
| B02 | S7 BullPullbackLong | [`logs/B02_S7_BullPullbackLong.md`](logs/B02_S7_BullPullbackLong.md) | ⏳ Queue |
| B02 | S8 BearBounceSell | [`logs/B02_S8_BearBounceSell.md`](logs/B02_S8_BearBounceSell.md) | ⏳ Queue |
| B02 | S9 VolExplosion | [`logs/B02_S9_VolExplosion.md`](logs/B02_S9_VolExplosion.md) | ⏳ Queue |
| B02 | S10 AdaptiveBreakout | [`logs/B02_S10_AdaptiveBreakout.md`](logs/B02_S10_AdaptiveBreakout.md) | ⏳ Queue |
| B03 | S11 MiddayCompression | [`logs/B03_S11_MiddayCompression.md`](logs/B03_S11_MiddayCompression.md) | ⏳ Queue |
| B03 | S12 WeekdayMomentum | [`logs/B03_S12_WeekdayMomentum.md`](logs/B03_S12_WeekdayMomentum.md) | ⏳ Queue |
| B03 | S13 VolCollapseShort | [`logs/B03_S13_VolCollapseShort.md`](logs/B03_S13_VolCollapseShort.md) | ⏳ Queue |
| B03 | S14 TripleTFTrend | [`logs/B03_S14_TripleTFTrend.md`](logs/B03_S14_TripleTFTrend.md) | ⏳ Queue |
| B03 | S15 BBReversion | [`logs/B03_S15_BBReversion.md`](logs/B03_S15_BBReversion.md) | ⏳ Queue |

---

## 三、Log 檔的標準結構（必須維護）

每個 `BXX_SY_<Name>.md` 必須含 7 個 section：

1. **基本資料** — 代號、類別、方向、週期、原始參數
2. **日線代理回測基線** — 從 archive batch01-03 原始數據
3. **Phase 1: 參數敏感度分析** — 每個參數的高原範圍 + 判定
4. **Phase 2: Walk-Forward** — IS/OOS 滾動結果 + WFE%
5. **Phase 3: Monte Carlo 壓力測試** — 95% MDD / 99% MDD / 破產率
6. **Phase 4: 策略組合分析** — 與既有 portfolio 的相關性 + Sharpe
7. **最終判定** — 7 項門檻檢核 + 決策日期

---

## 四、與 OFFICIAL_ROADMAP 的關係

```
OFFICIAL_ROADMAP.md (docs/policies/)
       │ 鎖定名稱與順序
       ▼
TRACKER.md (本資料夾)
       │ 追蹤每隻策略當前狀態
       ▼
logs/BXX_SY_<Name>.md (本資料夾)
       │ 每隻策略 Phase 1-4 詳細執行紀錄
       ▼
strategies/research/SXX_<Name>/ (策略開發資料夾)
       │ .pla + design_spec + annotated
       ▼
strategies/live_simulation/ (晉升)
       │ 部署 MC12 模擬
       ▼
strategies/live/ (最終上架)
```

---

## 五、Template

當為新策略建立 log 檔時，從 [`logs/TEMPLATE_optimization_log.md`](logs/TEMPLATE_optimization_log.md) 複製。

---

## 六、紀律

1. 每次策略 Phase 完成必更新對應 log + TRACKER
2. KILL 決策必標註於 log 「最終判定」section + TRACKER 「FAIL 策略墓地」
3. 跳號或偏離排程 = 違反 CLAUDE.md Rule #14
