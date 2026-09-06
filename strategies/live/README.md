# strategies/live/ — 實盤上架策略（真金白銀）

> **版本以 [`docs/LIVE_VERSIONS.md`](../../docs/LIVE_VERSIONS.md) 為單一真相來源。**
> 本檔版本欄若與該檔不符，以該檔為準。

> 這裡的策略都已部署到 MultiCharts 9.0 實盤帳戶，每天真金白銀運作。
> 任何變更必須 **空手時部署**，並通過 `scripts/verify_all_live.py` 全 110 項驗證。

---

## 上架策略清單（截至 2026-07-26）

| 策略 | 類別 | 方向 | 版本 | 標籤前綴 | 最新基準淨利 | BOSS_VIEW |
|------|------|------|------|----------|--------------|----------|
| **L1** TrendLong | 趨勢追蹤 | 純多 | V2.6 + StopProfit + FrozenSL + HolidayFlat_v3 | `TL_` | **+3,216,200** | [📋](L1_TrendLong/L1_TrendLong_BOSS_VIEW.md) |
| **L2** TrendShort | 趨勢追蹤 | 純空 | **v5.3 + SetStopContract + SL_Pct=1.25** | `TS_` | **+2,882,400** | [📋](L2_TrendShort/L2_TrendShort_BOSS_VIEW.md) |
| **L3** ConsolidationLong | 盤整區間 | 純多 | v13.4（Variant B：Freeze 開、BE 關） | `CL_` | +697,200 | [📋](L3_ConsolidationLong/L3_ConsolidationLong_BOSS_VIEW.md) |
| **L4** ConsolidationShort | 盤整反轉 | 純空 | **v14.6 + SetStopContract + SL_Pct=1.50** | `CS_` | **+894,400** | [📋](L4_ConsolidationShort/L4_ConsolidationShort_BOSS_VIEW.md) |
| **L5** BreakoutLong | 盤整突破 | 純多 | **v19.9 + SetStopContract + SL_Pct=1.0** | `BL_` | +1,361,400 | [📋](L5_BreakoutLong/L5_BreakoutLong_BOSS_VIEW.md) |

📋 = **BOSS_VIEW**（老闆快速 view，每隻策略強制附，規範見 [`docs/methodology/BOSS_VIEW_TEMPLATE.md`](../../docs/methodology/BOSS_VIEW_TEMPLATE.md)）

---

## 全策略共通保護模組

| 模組 | 用途 | L1 | L2 | L3 | L4 | L5 |
|------|------|----|----|----|----|----|
| Holiday_Tail[80] 63 筆 TAIFEX 登錄表 | 假日尾段日強制歸零 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Registry_Valid_Until = 1270101 | 視界 fail-safe | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manual_Kill_Switch | 緊急停市 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Frozen Initial SL | 進場根鎖 ATR（防 reload 漂移） | ✅ | ✅ | ✅ | ✅ | ✅ |
| **SetStopContract** | 引擎停損 per-contract（非 total） | ✅ | ✅ | ✅ | ✅ | ✅ |
| **SL_Pct** | ATR 停損距離趴數上限（極端保護） | — | 1.25% | — | 1.50% | 1.0% |
| 30 天紅字警告 | 登錄表過期前通知 | ✅ | ✅ | ✅ | ✅ | ✅ |

**Holiday_Flat_Time 依 K 棒網格分配**：L1=345（45M）/ L2=300（60M）/ L3=L4=L5=415（15M）

---

## 各策略特有特色

### L1 — V2.6 StopProfit 模組（趨勢延續保護）
- close-based peak tracking，達 +250 pts 後啟動
- Floor = Entry + Peak × 45%（55% 保留）
- **L1 SP 哲學不可移植到 L4/L5**（已實證）

### L2 — 雙會話 Donchian 突破
- Day session: 08:45-13:45（Time 845-1245）
- Night session: 15:00-05:00
- 週線 13SMA 過濾（一個季度）

### L3 — Variant B 生產（A/B 實證後封裝）
- Freeze_SL_On(true)：鎖腿分類 + 停損 + 目標
- BE_Trigger_Pts(0)：BE 駁回（變體 D 慘案：100 筆 0 勝率）
- 教訓：盤整區間策略不適合 BE

### L4 — v14.6 生產（A/B 實證後封裝 + SetStopContract + SL_Pct=1.50）
- Night_Block_On(true)：02:00-04:59 進場封鎖
- BE/SP 駁回（A/B 實證 -345K ~ -82K 全敗）
- v15/v16 研究全 KILLED（alpha = bear/neutral trap only）
- 教訓：100% 勝率機制可以是淨損

### L5 — SP 駁回（A/B 實證後封裝 + SetStopContract + SL_Pct=1.0）
- v19.9 行為 = 生產配置
- SP_Trigger_Pts(0) 永久 0
- 教訓：L1 SP 完全鏡像也失敗（策略尾巴集中度 > 70% = SP 禁區）

---

## 部署/變更工作流

1. **空手確認**：MC9 該策略無持倉
2. **載入新版 PLA**：覆蓋舊版檔案
3. **確認 Inputs 預設值**：與 .pla 檔案一致
4. **跑完整回測**：與前版對比 PF / MDD / 淨利 / Top-10 保留
5. **Export Excel**：交給我做完整 acceptance 驗證
6. **若 PASS**：自動進入生產
7. **若 FAIL**：rollback 到前版

---

## 驗證腳本

```bash
# 全策略 master verification（必跑）
python scripts/verify_all_live.py     # 110/110 項

# L4 深度驗證（針對 v14.2B）
python scripts/verify_l4_v142.py      # 67/67 項
```

---

## 跨策略已驗證的鐵律

寫入記憶 `feedback_trend_let_profits_run.md`：

1. **趨勢策略可用 SP**（L1 V2.6 高門檻 + 寬保留有效）
2. **盤整區間策略不可用 BE**（L3 變體 D 100 筆 0 勝率慘案）
3. **盤整反轉策略不可用 BE/SP**（L4 v14.2 全失敗）
4. **盤整突破策略不可用 SP**（L5 v19.8 全失敗 — 連完全鏡像 L1 的 F 變體也失敗）
5. **策略尾巴集中度 > 70% = SP 禁區**（L5 Top-10 88% 集中 → SP 必自殺）
6. **100% 勝率的保護機制可以是淨損**（CS_SP、BL_SP 自身 100% 勝率但截斷大尾巴）
7. **進場品質過濾 > 持倉中段保護**（L4 Path A 夜盤封鎖 +106K 完勝 BE/SP）

---

## 參考文件

- [docs/methodology/entry_exit_sop.md](../../docs/methodology/entry_exit_sop.md) — 9 層出場架構標準
- [docs/methodology/position_sizing_and_capacity.md](../../docs/methodology/position_sizing_and_capacity.md) — 口數配置
- [docs/strategy_archive/L4_v14.2_variant_results.md](../../docs/strategy_archive/L4_v14.2_variant_results.md) — L4 A/B 完整實證
- [docs/strategy_archive/L5_v19.8_variant_results.md](../../docs/strategy_archive/L5_v19.8_variant_results.md) — L5 A/B 完整實證
- [docs/research/optimization_opportunities_2026Q2.md](../../docs/research/optimization_opportunities_2026Q2.md) — 優化空間清單
