# L4 盤整空 — STRATEGY_WILLY_SHORT_CTEST2

> 腳本名稱：_Live_Adaptive_Farmer_v14.2_SpringOnly
> MC 載入名稱：STRATEGY_WILLY_SHORT_CTEST2
> 版本：**v14.2 + HolidayFlat_v3 + FrozenSL + PathA/B A/B Engine**
> 平台：MultiCharts 9.0 PowerLanguage x64
> 狀態：🟢 已上架實盤運行 v14.1（待 A/B 測試完成後決定是否升級至 v14.2 任一變體）
> 口數：1 口
> Path A 診斷：[L4_v142_pathA_entry_diagnostic.md](../../docs/L4_v142_pathA_entry_diagnostic.md)
> Path B 設計：[L4_v142_pathB_variant_matrix.md](../../docs/L4_v142_pathB_variant_matrix.md)

## v14.2 A/B Engine（生產預設 = OFF，回歸安全）

v14.2 用 input 開關支援七個變體，**生產預設所有開關關閉 = 行為等同 v14.1**。
用戶在 MC9 切換 input 跑 A/B 回測，依數據決定最終生產配置。

| Input | 預設 | 用途 |
|-------|------|------|
| `Night_Block_On` | **false** | true = 封鎖 02:00-04:59 進場（Path A） |
| `BE_Trigger_Pts` | **0** | 0 = 關閉。設 60/80/100 啟動 BE 保護（Path B） |
| `BE_Offset_Pts` | 5 | BE floor = Entry - 5 pts（鎖 5 pts 獲利） |
| `SP_Trigger_Pts` | **0** | 0 = 關閉。設 60/80/100 啟動峰值守護（Path B） |
| `SP_Retain_Pct` | 50 | SP floor = Entry - Peak × (1 - Retain%) |

### 七個命名變體（建議 MC9 測試順序）

| 變體 | Night | BE | SP | Retain | 假設 |
|------|-------|-----|-----|--------|------|
| **A** baseline | false | 0 | 0 | — | 等同 v14.1（回歸對照） |
| **B** PathA only | **true** | 0 | 0 | — | 只剔除 02-04 夜盤（預估 +120,800） |
| **C** PathB BE | false | **60** | 0 | — | 簡單 BE +60/+5 |
| **D** PathB SP | false | 0 | **80** | **50** | 峰值守護 +80/50% |
| **E** A+C | **true** | **60** | 0 | — | Night + BE |
| **F** A+D | **true** | 0 | **80** | **50** | Night + SP（預估最佳）|
| **G** A+SP保守 | **true** | 0 | **100** | **50** | 最保守組合（最高門檻） |

### 預期結果（理想模擬，實際應折扣到 60-80%）

| 變體 | 預估淨利 | Δ vs v14.1 | 風險評等 |
|------|----------|------------|----------|
| A | 581,200 | 0 | — |
| B | ~702,000 | +20.8% | 極低 |
| C | ~778,000 | +33.9% | 中（BE 截斷風險） |
| D | ~831,000 | +43.0% | 低-中 |
| F | ~950,000 | **+63.5%** | 低-中 |
| G | ~852,000 | +46.6% | 極低 |

### 新出場標籤

| 標籤 | 觸發 | 優先級 |
|------|------|--------|
| CS_BE | BE_Floor 緊於 v_Stop_Level 而被觸發 | SP > **BE** > SL（互斥） |
| CS_SP | SP_Floor 緊於 v_Stop_Level 而被觸發 | **SP** > BE > SL（互斥） |
| CS_SL | 原 v_Stop_Level（無 BE/SP 覆蓋時） | SP > BE > **SL** |

每根 K 棒只發出 **一個** 帶標籤 Stop 單，互斥避免衝突。

### L3 變體 D 詛咒檢核

| 維度 | L3 變體 D（失敗） | L4 v14.2（規劃） |
|------|------------------|------------------|
| 門檻 | +50 pts（=箱寬 25%，太低） | **+60~+100 pts**（=多倍 ATR） |
| MFE≥門檻 後典型路徑 | 回測中線（區間反覆） | 趨勢延續（CS_SL 平均最終 +198 pts） |
| 對贏家的截斷 | 96 筆到價獲利被砍 | **模擬 0 筆**（贏家最終遠高於 floor） |
| 預設 | 已關（OK） | **關（生產安全）** |

### 接受/否決條件

**通過 PASS**：
- ✅ 淨利提升 ≥ 100,000
- ✅ MDD 不變或改善
- ✅ 勝率 ≥ 40%
- ✅ CS_BE / CS_SP 勝率 ≥ 50%
- ✅ Top-10 贏家保留率 ≥ 80%

**否決 FAIL**：
- ❌ CS_BE 或 CS_SP 勝率 < 30%（L3 詛咒重演）
- ❌ Top-10 贏家保留率 < 70%（截斷大贏家）
- ❌ MDD 惡化 > 10%

---

## v14.1 變更摘要（2026-06-13）

| 項目 | v14.0 | v14.1 |
|------|-------|-------|
| 假日鐵律 | 無 | ✅ 63 筆 TAIFEX 登錄表 + 04:15 強制歸零 + Registry fail-safe |
| 初始停損漂移 | ATR 每根重算 + LockedTop ratchet | ✅ Freeze_SL_On=true：進場根鎖 ATR + LockedTop |
| 出場優先序 | 隱含 | ✅ ExitFired gate：Kill > Registry > Holiday > BreakExit > TimeExit > SL |
| 新出場標籤 | CS_SL / CS_TimeExit / CS_BreakExit | + CS_Kill / CS_RegistryEnd / CS_Holiday |
| CS_BreakExit | 未動（下一輪處理） | 未動（下一輪處理） |

## v14.1 假日鐵律模組

| 項目 | 內容 |
|------|------|
| 強制歸零 | 尾段日 Time ≥ **04:15** 市價出場（15M 格線：04:15 成交、04:30/04:45 兩次重試、05:00 收盤前必歸零） |
| 進場封鎖 | 尾段日（00:00-05:00）SellShort 條件加上 `v_Holiday_Block = false` 門禁 |
| 視界 fail-safe | `Registry_Valid_Until = 1270101`，超過即封鎖+平倉（CS_RegistryEnd）+30 天圖表紅字 |
| 緊急開關 | `Manual_Kill_Switch` → CS_Kill |
| 歷史影響 | 0 筆跨假持倉 → 重算後歷史軌跡不變 |

## v14.1 初始停損凍結

| 機制 | 說明 |
|------|------|
| 觸發 | `Freeze_SL_On(true) AND v_SL_Locked = false`，僅在進場根執行一次 |
| 鎖定 | `v_Frozen_ATR = v_Current_ATR`、`v_Frozen_LockedTop = v_Locked_Top` |
| 套用 | 追蹤停損未啟動前：`v_Stop_Level = v_Frozen_LockedTop + ATR_Stop_Mult × v_Frozen_ATR` |
| 追蹤層 | 進入追蹤後仍用 `v_Current_ATR`（設計意圖：trail 跟隨當下波動） |
| 平倉重置 | `MarketPosition = 0` 時 `v_SL_Locked = false`，下一筆重新鎖定 |
| 切回舊版 | `Freeze_SL_On = false` 完整還原 v14.0 動態行為（baseline 對照用） |

---

## 策略概述

- **類別**：盤整假突破型（Wyckoff Spring Trap）
- **方向**：★純做空
- **週期**：Data1 = 15M / Data2 = 60M / Data3 = 日線（三時間框架）
- **核心邏輯**：60M 偵測盤整箱體 → 日線確認非多頭環境 → 價格假突破箱頂後回落 → 做空陷阱交易者 → 追蹤停損
- **市場曝險**：僅 1.62%（五隻策略中最低，絕大部分時間空倉等待陷阱）

---

## MC9 回測績效（v14.1 實測，部署日 2026-06-13）

| 指標 | v14.0 baseline | **v14.1 新 baseline** | 變化 |
|------|----------------|----------------------|------|
| 回測區間 | 2020/02/19 ~ 2026/06/06 | 2020/02/19 ~ 2026/06/06 | — |
| 總交易次數 | 88 | 88 | 不變 |
| 勝率 | 42.05% | 42.05% | 不變 |
| Profit Factor | 1.602 | **1.622** | +1.2% ✅ |
| 淨利 | +569,200 | **+581,200** | +12,000 ✅ |
| 毛利 | +1,515,400 | +1,515,400 | 不變 |
| 毛損 | -946,200 | **-934,200** | +12,000 ✅ |
| MDD | -334,600 (-23.39%) | **-328,000 (-22.84%)** | 改善 6,600 ✅ |
| 最大平倉交易虧損 | -300,800 | -294,200 | 改善 6,600 |
| 淨利/MDD | 1.70 | **1.77** | +4.1% ✅ |
| 帳戶報酬 | — | 197.55% | — |
| 滑價支付 | — | 176,000 | — |

### 出場標籤統計（v14.1 新 baseline）

| 標籤 | v14.0 | v14.1 | 變化 |
|------|-------|-------|------|
| CS_SL | 47 / 59.6% / +994,000 | **45 / 62.2% / +1,019,200** | -2 / **+2.6% WR** / +25,200 ✅ |
| CS_TimeExit | 12 / 75.0% / +145,000 | 15 / 60.0% / +107,200 | +3 / -15% / -37,800（重分配） |
| **CS_BreakExit** | **29 / 0% / -569,800** | **28 / 0% / -545,200** | **-1 / +24,600** ✅ |
| CS_Holiday | — | 0 | 預期（無歷史違規） |
| CS_RegistryEnd | — | 0 | 預期 |
| CS_Kill | — | 0 | 預期 |
| 合計 | 88 / 42.05% / +569,200 | **88 / 42.05% / +581,200** | +12,000 ✅ |

### 凍結 SL 核心修復驗證

| 指標 | v14.0 | v14.1 | 改善 |
|------|-------|-------|------|
| CS_SL 由盈轉虧筆數 | 15 | **12** | **-3 (-20%)** ✅ |
| 浪費 MFE 合計 | 445,400 | **341,800** | **-103,600 (-23%)** ✅ |

> **驗證：凍結 SL 確實減少了 3 筆原本被漂移停損掃出的盈利交易，浪費潛在獲利下降 23%。**

### 年度績效對比

| 年份 | v14.0 | v14.1 | 變化 |
|------|-------|-------|------|
| 2020 | +153,600 | +153,600 | 0 |
| 2021 | +34,600 | +34,600 | 0 |
| 2022 | +74,600 | +72,200 | -2,400 |
| **2023** | **-10,800** | **-3,000** | **+7,800** ✅ |
| 2024 | +17,000 | +19,400 | +2,400 |
| 2025 | +300,200 | +304,400 | +4,200 |

2023 年（最弱年）改善最明顯，從虧損年接近損平。

### 待處理痛點（v14.1 未動）

| 標籤 | 筆數 | 勝率 | 損益 | 處置 |
|------|------|------|------|------|
| **CS_BreakExit** | 28 | **0%** | **-545,200** | **下一輪 v14.2 核心議題** |

29 → 28 筆只是凍結 SL 間接攔下 1 筆，CS_BreakExit 本身的 0% 勝率結構未動。

### 交易分析

| 指標 | 數值 |
|------|------|
| 平均獲利交易 | +40,957 NTD |
| 平均虧損交易 | -18,553 NTD |
| 盈虧比 | 2.208 |
| 最大單筆獲利 | +273,000 NTD（2025/04/07） |
| 最大單筆虧損 | -69,600 NTD（2024/11/30） |
| 獲利交易平均持倉 | 34.7 根 K 棒（~8.7 小時） |
| 虧損交易平均持倉 | 22.9 根 K 棒（~5.7 小時） |
| 最長持平期間 | 1 年 3 個月 21 天 |

---

## 進場邏輯

### Phase 0：日線多頭封鎖（Master Kill Switch）
```
封鎖做空的條件（任一成立 → v_Macro_Block = true）：
條件 A：日線收盤 > 60MA 且 60MA 向上（強勢多頭）
條件 B：日線 20MA > 60MA（黃金交叉）
→ 多頭環境下完全禁止開空
```

### Phase 1：60M 盤整偵測（Commander）
```
① 當前 60M 高低點在前 15 根 60M K 棒的高低區間內
② 當前 60M 波幅 ≤ 前 15 根區間的 70%（Range_Shrink_Rate = 0.7）
③ 60M 趨勢：Close < MA(48) → 偏空（v_Trend_Dir = -1）
④ 若 60M 收盤突破箱體 → 盤整失效
```

### Phase 2：假突破陷阱偵測（Spring Trap）
```
步驟 1 - 陷阱偵測：
  15M 最高價 > Box_Top → 啟動陷阱區（v_In_Trap_Zone = true）
  陷阱區有效期：6 根 15M K 棒（1.5 小時）

步驟 2 - 做空觸發：
  全部滿足才進場：
  ① 目前無持倉
  ② 冷卻期已過（上次出場後 ≥ 8 根 K 棒）
  ③ 60M 趨勢偏空（v_Trend_Dir = -1）
  ④ 日線未封鎖（v_Macro_Block = false）
  ⑤ 在陷阱區內（v_In_Trap_Zone = true）
  ⑥ 收盤 < Box_Top - ATR(60) × 0.4
  ⑦ **v_Holiday_Block = false（v14.1 新增：尾段日封鎖）**
  → SellShort next bar at Market
```

---

## 出場邏輯（v14.1 ExitFired 優先序）

| 優先級 | 標籤 | 條件 | 方式 |
|--------|------|------|------|
| 0 | **CS_Kill** | Manual_Kill_Switch = true | Market |
| 0 | **CS_RegistryEnd** | 超出登錄表視界 | Market |
| 0 | **CS_Holiday** | 尾段日 Time ≥ 04:15 | Market |
| 1 | CS_BreakExit | 盤整失效 + 60M 收盤 > Locked_Top | Market |
| 2 | CS_TimeExit | 持倉 ≥ 60 bars 且追蹤未啟動 | Market |
| 3 | CS_SL | 反向觸及停損線 | Stop |

### 初始停損（v14.1 凍結）
```
Freeze_SL_On = true（生產）：
  進場根：v_Frozen_ATR = ATR(60), v_Frozen_LockedTop = Box_Top
  追蹤未啟動：v_Stop_Level = v_Frozen_LockedTop + 2.0 × v_Frozen_ATR
  → 整筆交易停損價固定，reload 不變

Freeze_SL_On = false（baseline 對照）：
  完整還原 v14.0：v_Stop_Level = v_Locked_Top + 2.0 × v_Current_ATR
  ATR 隨每根 K 棒重算，Locked_Top 若 Box_Top 下移會跟著下移
```

### 追蹤停損（保持 v14.0 設計）
```
啟動條件：價格低點觸及 Locked_Box_Btm（跌到箱底）
啟動後：v_Stop_Level = MinList(v_Stop_Level[1], Lowest_Low + 1.0 × v_Current_ATR)
→ 用「當下 ATR」是設計意圖：追蹤層希望跟隨現行波動率
方向：只往下修（MinList），不會往上放寬
```

### 冷卻期
```
出場後 8 根 K 棒（2 小時）內不得再進場
避免同一盤整箱連續虧損
```

---

## 參數一覽（v14.1）

| 參數 | 值 | 模組 | 說明 |
|------|-----|------|------|
| Daily_FastMA_Len | 20 | Kill Switch | 日線快速 MA |
| Daily_SlowMA_Len | 60 | Kill Switch | 日線慢速 MA |
| Lookback_Bars | 15 | Commander(60M) | 盤整參考期 |
| Range_Shrink_Rate | 0.7 | Commander(60M) | 波幅收縮門檻（70%） |
| Weekly_MA_Len | 48 | 趨勢過濾(60M) | 60M 趨勢 MA（≈ 2 週） |
| ATR_Length | 60 | 風控(15M) | ATR 計算長度 |
| ATR_Stop_Mult | 2.0 | 停損 | 初始停損 ATR 倍數 |
| i_Buffer_ATR_Mult | 0.4 | 進場 | 回落緩衝區 ATR 倍數 |
| Time_Limit_Bars | 6 | 陷阱偵測 | 陷阱有效期（15M K 棒） |
| Cooldown_Bars | 8 | 風控 | 出場後冷卻期 |
| Time_Stop_Bars | 60 | 時間停損 | 持倉上限 K 棒數 |
| Trail_ATR_Mult | 1.0 | 追蹤停損 | 追蹤 ATR 倍數 |
| **Freeze_SL_On** | **true** | **v14.1** | **進場根鎖 ATR + LockedTop** |
| **Holiday_Flat_Time** | **415** | **v14.1** | **15M 格線：04:15 強制歸零** |
| **Registry_Valid_Until** | **1270101** | **v14.1** | **登錄表視界（2027/1/1）** |
| **Manual_Kill_Switch** | **false** | **v14.1** | **緊急停市開關** |

---

## MC 設定

| 項目 | 設定 |
|------|------|
| Data1 | TXF1 15 分鐘 |
| Data2 | TXF1 60 分鐘 |
| Data3 | TXF1 日線 |
| 初始資金 | 1,000,000 NTD |
| 滑價 | 1,000 NTD/口 |
| 手續費 | 0 |
| IntrabarOrderGeneration | false |

---

## 部署檢查清單（v14.1）

- [ ] MC9 確認 L4 為空手狀態
- [ ] 載入新版 _Live_Adaptive_Farmer_v14.1_SpringOnly
- [ ] 確認 Inputs 預設值：Freeze_SL_On=true, Holiday_Flat_Time=415, Registry_Valid_Until=1270101, Manual_Kill_Switch=false
- [ ] 跑完整回測（2020/02/19 起），保存新 Excel 報告
- [ ] 比對 v14.0 vs v14.1 績效：CS_SL 平均盈虧、CS_BreakExit 應保持 29/0% 不變、總筆數應接近 88
- [ ] 確認 6/18 端午尾段不會新開空單
- [ ] 確認 04:15 後若有持倉會自動平倉

---

## 下一輪優化重點（v14.2 候選）

| 優先 | 議題 | 痛點 |
|------|------|------|
| **P1** | **CS_BreakExit 改造** | 29 筆 0% 勝率 -569,800（=全部淨利），10 筆 MFE>10K 卻全吐回 |
| P2 | CS_SL 由盈轉虧 | 47 筆 CS_SL 中 15 筆 MFE>0 但最終虧損，浪費 +445,400 |
| P2 | 00-05 夜盤進場 | 11 筆 WR 27.3%、−142,400（其他兩時段均賺） |
| P3 | StopProfit 評估 | 反轉類策略是否適用（≠ L1 趨勢、≠ L3 純區間） |

---

## 策略特色

1. **Wyckoff Spring Trap**：專抓假突破箱頂後的反轉，做空被困的多頭追漲者
2. **極低市場曝險**：僅 1.62%，98.4% 時間空倉
3. **高盈虧比**：2.208，低勝率靠大波段彌補
4. **日線雙重 Kill Switch**：多頭環境完全封鎖做空
5. **陷阱時間衰減**：假突破後僅 6 根 K 棒內有效
6. **冷卻期保護**：8 根 K 棒冷卻
7. **v14.1 凍結停損**：ATR + LockedTop 鎖在進場根，reload 不漂移
8. **v14.1 假日鐵律**：63 筆 TAIFEX 登錄表 + 04:15 強制歸零

---

## L4 vs L2 對比（兩隻做空策略）

| 面向 | L4 盤整空 | L2 趨勢空 |
|------|----------|----------|
| 賺什麼錢 | 假突破反轉（Spring Trap） | 趨勢延續下跌 |
| 進場方式 | 假突破箱頂後回落做空 | Donchian 新低突破做空 |
| 環境過濾 | 日線 Kill Switch + 60M MA48 | 週線 13SMA |
| 交易頻率 | ~14 筆/年 | ~13 筆/年 |
| PF | 1.602 | 2.595 |
| MDD | -334,600 (-23.39%) | -269,400 (-15.98%) |
| 盈虧比 | 2.208 | 4.354 |
| 曝險 | 1.62% | 4.88% |
| Holiday Flat_Time | 415（15M） | 300（60M） |

> L4 抓盤整假突破反轉，L2 追趨勢新低延續。兩者在不同行情階段互補。
