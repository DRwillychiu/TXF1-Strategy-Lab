# L4 ConsolidationShort -- Research Summary

**策略名稱**: L4 ConsolidationShort (S_Spring 假突破反轉做空)
**研究期間**: 2026-06-13 ~ 2026-08-26
**結論**: v14.6 = PRODUCTION. 所有延伸研究 (v15.1, v16.0, v17.0, v18.0) 確認 alpha 邊界不可擴展。
**最新版本**: v14.7 (2026-08-26) -- 純標籤, 錨點通過, 未 promote。
**研究線狀態**: 邏輯線 CLOSED (2026-07-26)。可讀性線於 2026-08-24~26 重開並結案。

> **本檔 2026-09-06 補上 v17.0 / v18.0 / v14.7 三個版本** -- 先前停在 2026-07-26,
> 落後 42 天, 缺了整條 2026-08 的研究線。

---

## 版本演進總覽

| 版本 | 日期 | 內容 | 結果 |
|------|------|------|------|
| **v14.2B** | 2026-06-13 | Production baseline (Variant B sealed) | ✅ PRODUCTION |
| **v14.4** | 2026-06-18 | P3b Immediate Stop Guard 加入 | ✅ 安全升級 |
| **v14.5** | 2026-06-18 | Strong Long Block + Fast BreakExit 實驗 | ❌ A/B 兩配置皆失敗，完全回滾 |
| **v14.6** | 2026-07-26 | SetStopContract bug fix + SL_Pct=1.50% | ✅ **CURRENT PRODUCTION** |
| v15.0 | 2026-07-26 | Macro Block OR→AND 收緊 | ❌ 淨利 -41.8%，OR 是 load-bearing |
| v15.1 | 2026-07-26 | Pressure Zone 進場新增 | ❌ net negative，與 trap alpha 互斥 |
| v15.1 opt | 2026-07-26 | MC sweep 全參數空間搜索 | ❌ 無 sweet spot |
| v16.0 | 2026-07-26 | Regime-Adaptive 雙路徑架構 | ❌ 0 bull trades，結構不可行 |
| v17.0 | 2026-08-24 | 風險形態掃描錨點基準（7 個新 input） | ❌ 四條風險腿全部推翻 |
| v18.0 | 2026-08-24 | 二次進場狀態機 | ❌ **零觸發**，解除條件被自己的停損蘊含 |
| **v14.7** | **2026-08-26** | **二次進場標籤（純標籤，零行為變化）** | ✅ **錨點通過，最新版本** |

---

## 各版本詳述

### v14.2B: Production Baseline (2026-06-13)

Variant B sealed（Night_Block_On=true, BE=0, SP=0）。確立 L4 的核心交易邏輯：
盤整箱體假突破 → 做空反轉。Macro Block（ADX<25 OR Close<200MA）定義有效 regime。

### v14.4: P3b Immediate Stop Guard (2026-06-18)

加入 SetStopLoss（Rule #12）+ HolidayFlat_v3 + Settlement_Flat。
純安全性升級，不影響 alpha 結構。

### v14.5: Strong Long Block + Fast BreakExit (2026-06-18) -- TRIED AND REMOVED

兩個方向的嘗試：
- **Strong Long Block**: 多頭強勢時禁止做空 → 砍掉有效交易
- **Fast BreakExit**: 加速假突破認定出場 → 過早出場錯失利潤

A/B 兩配置四種組合全部實證無效，完全回滾至 v14.4。

### v14.6: SetStopContract + SL_Pct (2026-07-26) -- CURRENT PRODUCTION

修復 SetStopContract bug，統一 SL_Pct=1.50%。
這是最後一個成功的改動，確立為 production 版本。

### v15 系列: Macro Block 修改實驗 (2026-07-26) -- ALL FAILED

三個子實驗全部失敗：
1. **v15.0**: OR→AND 收緊 → 淨利 -41.8%（OR 覆蓋的兩個 regime 都有獨立 alpha）
2. **v15.1**: Pressure Zone 進場 → net negative（mean-reversion 與 trap alpha 互斥）
3. **v15.1 opt**: 全參數空間 sweep → 無 sweet spot（結構問題非參數問題）

詳見 [`L4_v15.1/L4_v15.1_FINAL_VERDICT.md`](L4_v15.1/L4_v15.1_FINAL_VERDICT.md)

### v16.0: Regime-Adaptive 雙路徑 (2026-07-26) -- FAILED

將 Macro Block 從 blocker 改為 router：
- Bear path: 原 trap 進場（不變）
- Bull path: Pressure Entry + Box Quality Gate（新增）

結果 122 trades 全走 bear path，bull path **0 trades**。
Bull market 盤整太短太窄，Quality Gate（60 bars + 2 touches）結構不可行。
17 bug fixes + dead variable (`v_Active_Cooldown`) 清理確認非 implementation 問題。

詳見 [`L4_v16.0/L4_v16.0_FINAL_VERDICT.md`](L4_v16.0/L4_v16.0_FINAL_VERDICT.md)

---

### v17.0: 風險形態掃描的錨點基準 (2026-08-24) -- 四腿全部推翻

**性質**: v14.6 PRODUCTION + 7 個風險形態 input (Stop_Form / Max_Entry_Risk_Pct / Trail form)。
每個新 input 停在預設值時, 逐筆重現 v14.6 的 79 筆交易。

| Run | 掃描對象 | 結果 |
|---|---|---|
| Anchor | 全部預設 | **79/79 逐筆相同, 24 指標 24/24 相同** |
| Run A | `Stop_Form` = 2 + `Stop_Pct` 掃描 | **推翻**。預測最佳 0.40-0.60, 實測 1.35 |
| Run D | `Max_Entry_Risk_Pct` 掃描 | **推翻**。23/24 格劣於不設限 |
| Trail | 移動停利形態 | **推翻**。crash 對 calm 差 4.5 倍, 無高原 |

**結構性發現**: L4 的獲利全部集中在「進場那一刻風險最大」的那些交易上。
任何在進場端限制風險、或收緊停損的機制, 拿掉的正好就是那些交易。
1.45 -> 1.50 的斷崖是 1,017,600, 分布在 11 筆被 `SL_Pct` 夾到剛好 1.50% 的交易上。

### v18.0: 二次進場狀態機 (2026-08-24) -- KILLED, 零觸發

**`ReEntry_On = 1` 一次都沒有觸發。**

根因: 解除條件測試「Data2 收盤 > 箱頂」, 而凍結停損掛在「箱頂 + 2 x ATR」。
**被停損出場這件事本身就已經蘊含了解除條件**, 所以旗標永遠在武裝前就被解除。

**這與兩天前在 L1 抓到的是同一族陷阱, 而我當時還寫過「L4 的幾何是乾淨的」。**

用戶裁示: 「假設原始 L4 本身就有二次進場, 那就是不需要進行優化。」
-> L4 維持基礎設定, 二次進場線結案。記錄為 Lesson L28。

### v14.7: 二次進場標籤 (2026-08-26) -- 最新, 純標籤

**性質**: v14.6 base + `CS_ReEntry` 標籤。零行為變化。

| | |
|---|---|
| 錨點 | 3,735 列, **4 處差異** = 3 筆改標 + 1 個策略名稱 |
| `CS_ReEntry` | **3 筆, +15,600, 佔淨利 1.9%** |
| MC Load Name | `STRATEGY_L4_V147_RESEARCH` |

**定義決定答案, 不是資料**: 同一份交易明細下, 「前次出場後 24 小時內」給 16 筆、
「7 天內」給 46 筆、而 v14.7 採用的結構定義「同箱型第 2 次以上」只給 3 筆。

---

## Production 版本最終績效

| 指標 | v14.6 (Production) |
|------|-------------------|
| 淨利 | **+894,400 NTD** |
| Profit Factor | **1.54** |
| Win Rate | **43.04%** |
| MDD | **-525,600 NTD** |
| 交易數 | **79** |
| 每年交易數 | ~13 |

---

## 核心洞見

### L4 Alpha 的本質

> **L4 alpha = bear/neutral market trap signal ONLY.**

1. **Alpha 來源**: 盤整箱體假突破 → 其他交易者被誘騙進場 → 停損出場推動價格反轉
2. **有效 regime**: 盤整市（ADX<25）或空頭市（Close<200MA），二者 OR 連接
3. **Bull market 零交易 = 正確行為**: 不是需要修復的 bug，是 alpha 不存在的正確反映

### 不可擴展的邊界

v15 + v16 的集體失敗證明了 L4 alpha 的嚴格邊界：

- ❌ 不能收緊 regime filter（OR 是 load-bearing）
- ❌ 不能新增 mean-reversion 進場（與 trap 機制互斥）
- ❌ 不能擴展到 bull regime（bull market 沒有結構性假突破機會）
- ❌ 不能修改進場條件（trap 進場是唯一有效路徑）

### Portfolio 角色

L4 在 portfolio 中扮演 **bear/neutral regime specialist**：
- L1 TrendLong: bull trend alpha
- L3 ConsolidationLong: bull consolidation alpha
- L5 BreakoutLong: bull breakout alpha
- **L4 ConsolidationShort: bear/neutral trap alpha** (互補)

Bull market 零交易 = portfolio 不需要 L4 在 bull market 出力，
因為 L1/L3/L5 已經覆蓋。這是正確的策略分工。

---

## 累計 Lessons (L28-L33)

| # | 來源 | 教訓 |
|---|------|------|
| L28 | v15.0 | Regime filter OR 條件不可輕易改 AND -- 可能切斷獨立 alpha 來源 |
| L29 | v15.1 | Trap-based alpha 與 mean-reversion alpha 互斥 |
| L30 | v15.1 opt | 全參數空間零 sweet spot = 結構問題，立即 KILL |
| L31 | v16.0 | Blocker→Router 架構假設目標 regime 有 alpha -- 必須先驗證 |
| L32 | v16.0 | Quality gate 在低頻事件 regime = impossible filter (quality-quantity tradeoff) |
| L33 | v16.0 | 0 trades in one path = 最強 KILL 信號 |

---

## 研究線狀態

```
L4 研究線：CLOSED (2026-07-26)
Production: v14.6 (SetStopContract + SL_Pct 1.50%)

未來方向：
  ✅ v14.6 持續在 MC9 live 運行
  ✅ 監控 forward performance（尤其 2026 年度表現是否回歸均值）
  ❌ 不再投入 L4 新版本開發資源
  ❌ 不嘗試擴展 bull regime 進場
  ❌ 不修改 Macro Block 結構
```

---

## 相關文件索引

| 文件 | 路徑 |
|------|------|
| Production .pla | `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort.pla` |
| Production 審查 | `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort_review.md` |
| Production 注解 | `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort_annotated.md` |
| v15 .pla | `strategies/research/L4_ConsolidationShort/L4_v15.1/L4_ConsolidationShort_v15.1.pla` |
| v15 FINAL_VERDICT | `strategies/research/L4_ConsolidationShort/L4_v15.1/L4_v15.1_FINAL_VERDICT.md` |
| v16 .pla | `strategies/research/L4_ConsolidationShort/L4_v16.0/L4_ConsolidationShort_v16.0.pla` |
| v16 FINAL_VERDICT | `strategies/research/L4_ConsolidationShort/L4_v16.0/L4_v16.0_FINAL_VERDICT.md` |
| v17.0 .pla | `strategies/research/L4_ConsolidationShort/L4_v17.0/L4_ConsolidationShort_v17.0.pla` |
| v18.0 .pla | `strategies/research/L4_ConsolidationShort/L4_v18.0/L4_ConsolidationShort_v18.0.pla` |
| v14.7 .pla | `strategies/research/L4_ConsolidationShort/L4_v14.7/L4_ConsolidationShort_v14.7.pla` |
| v17.0 錨點 | `docs/research/L4_v17.0_anchor_result_20260824.md` |
| v18.0 結案 | `docs/research/L4_REENTRY_FINAL_VERDICT_20260824.md` |
| v14.7 錨點 | `docs/research/L4_v14.7_anchor_result_20260826.md` |
| v14.2 variant 實證 | `docs/strategy_archive/L4_v14.2_*.md` |
| Boss View | `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort_BOSS_VIEW.md` |
