# L5 盤整多頭突破 — STRATEGY_WILLY_LONG_BREAKOUT_C

> 腳本名稱：_Live_Adaptive_Farmer_v19_8_BreakoutLong
> MC 載入名稱：STRATEGY_WILLY_LONG_BREAKOUT_C
> 版本：**v19.8 + Pre-Trail SP A/B Engine + HolidayFlat_v3 + FrozenSL**
> 平台：MultiCharts 9.0 PowerLanguage x64
> 狀態：🟢 已上架實盤運行 v19.6（待空手時部署 v19.8，預設 = v19.7 行為）
> 口數：1 口

## v19.8 Pre-Trail SP A/B Engine（2026-06-13）

**用戶概念**：L5 = L1 獲利延伸 + L3 進場策略；解決「曾經獲利但全部吐回」問題。

**機制**（從 L1 V2.6 SP 移植）：
- close-based MFE 追蹤（v_Peak_Profit = max(Close - Entry)）
- v_Peak_Profit >= SP_Trigger_Pts → v_SP_Armed = true
- v_SP_Floor = EntryPrice + Peak × (1 - SP_Retain_Pct/100)
- 永不解除（直到 flat）
- 優先序：Trail > SP > BE > 初始 SL

**Input 開關（生產預設 OFF，等同 v19.7 行為）**：
| Input | 預設 | 含義 |
|-------|------|------|
| `SP_Trigger_Pts` | **0**（off）| 0 = 關閉。A/B 測 60/80/100 |
| `SP_Retain_Pct` | 50 | 0-100。L1 用 55 |

**新標籤**：BL_SP_Bot / BL_SP_Mid（與 BL_BE / BL_SL / BL_Trail 互斥優先）

**完整變體設計**：[docs/L5_v198_pretrail_sp_design.md](../../docs/L5_v198_pretrail_sp_design.md)

**6 個建議測試變體**：
| 變體 | SP_Trigger | SP_Retain | 假設 |
|------|-----------|-----------|------|
| A baseline | 0 | — | v19.7 對照（迴歸）|
| B Aggressive | 60 | 50 | 早期保護 |
| C Mid | 80 | 50 | 中等門檻 |
| D Conservative | 100 | 50 | 高門檻 |
| E LessRetain | 80 | 40 | 更多回吐空間 |
| F L1-Like | 100 | 55 | 完全鏡像 L1 SP |

**接受條件**：淨利 > v19.7、BL_SP 勝率 ≥ 50%、Top-10 保留 ≥ 80%、MDD 不惡化 > 10%
**否決條件**：BL_SP 勝率 < 30%（L3/L4 詛咒）、Top-10 < 70%、淨利低於 v19.7

**L4 v14.2 失敗教訓已內化**：L5 因為有 Scale-Out 緩衝（40% 在 TP 落袋），SP 截斷風險理論上比 L4 小，但仍須 A/B 驗證。

---

## v19.7 三大修正（2026-06-13）

| 修正 | v19.6 狀況 | v19.7 改善 |
|------|-----------|-----------|
| **DayOfWeek=7 Dead Code** | 3 處引用 DOW=7，PowerLanguage Sat=6 → 永不成立 | 全移除；BL_SatClose 標籤刪除（4.8 年 0 觸發已實證） |
| **無假日鐵律** | 跨假持倉無保護 | 加入 HolidayFlat_v3：63 筆 TAIFEX 登錄表 + 04:15 強制歸零 + Registry fail-safe + Manual_Kill_Switch |
| **初始停損漂移** | v_ATR_Buffer 每根重算，reload 變動 | Freeze_SL_On(true)：進場根鎖 ATR，整筆交易固定 |

### v19.7 新出場標籤

| 標籤 | 觸發 |
|------|------|
| BL_Holiday_Bot / BL_Holiday_Mid | 尾段日 04:15 強制歸零 |
| BL_RegistryEnd_Bot / BL_RegistryEnd_Mid | 登錄表過期 fail-safe |
| BL_Kill_Bot / BL_Kill_Mid | Manual_Kill_Switch（颱風臨時停市）|

### 本輪刻意 **不**改變

| 議題 | 為什麼不動 |
|------|-----------|
| BL_BE 機制 | L4 v14.2 A/B 證明 BE 對多階段獲利策略有截斷副作用，但 L5 BE 是設計內建，未做 A/B；列為下一輪研究 |
| 夜盤封鎖（Path A）| L5 02-04 進場 12 筆 +87,800 淨利（不像 L4 -120,800），封鎖會傷害 L5 |
| Scale-Out / Trail 倍數 | 屬於 God Mode 核心引擎，非本輪 scope |

### MC9 部署（空手時）

新增 4 個 inputs 預設值：
- `Freeze_SL_On(true)`
- `Holiday_Flat_Time(415)`
- `Registry_Valid_Until(1270101)`
- `Manual_Kill_Switch(false)`

部署前提：MC9 空手狀態（v19.7 改變停損價計算，跨版會影響歷史軌跡）。

---

---

## 策略概述

- **類別**：盤整突破型
- **方向**：★純做多
- **週期**：Data1 = 15M / Data2 = 日線 / Data3 = 週線（三時間框架）
- **核心邏輯**：日線偵測盤整箱體（波動收縮） → 多頭環境確認 → 15M 突破箱體底部/中線進場做多 → MFE 三階追蹤停損
- **市場曝險**：僅 4.19%（大部分時間等待盤整形態出現）

---

## MC9 回測績效（Excel 報告 2026/06/07）

| 指標 | 數值 |
|------|------|
| 回測期間 | ~4 年 10 個月 |
| 初始資金 | 1,000,000 NTD |
| 滑價 | 1,000 NTD/口 RT |
| 總交易次數 | 162（全部多單） |
| 勝率 | 52.47% |
| Profit Factor | 2.136 |
| 淨利 | +1,713,000 NTD |
| 毛利 | +3,221,200 NTD |
| 毛損 | -1,508,200 NTD |
| 最大策略虧損 (MDD) | -193,200 NTD (-16.61%) |
| 最大平倉交易虧損 | -147,000 NTD (-14.48%) |
| 年報酬率 | 35.61% |
| 月報酬率 | 2.97% |
| 平均月報酬 | +29,534 NTD |
| 年度夏普比率 | 0.914 |
| 市場曝險時間 | 4.19% |

### 交易分析

| 指標 | 數值 |
|------|------|
| 平均獲利交易 | +37,896 NTD |
| 平均虧損交易 | -20,109 NTD |
| 盈虧比 | 1.885 |
| 最大單筆獲利 | +376,400 NTD（2026/04/08） |
| 最大單筆虧損 | -61,200 NTD |
| 獲利交易平均持倉 | 30.1 根 K 棒（~7.5 小時） |
| 虧損交易平均持倉 | 20.5 根 K 棒（~5.1 小時） |

---

## 進場邏輯

### 第一層：日線盤整偵測（Commander）
```
① 當日高低點在前 4 日的高低區間內（High ≤ Ref_High, Low ≥ Ref_Low）
② 當日波幅 ≤ 前 4 日區間的 60%（Range_Shrink_Rate = 0.6）
→ 盤整箱體成立，記錄 Box_Top 和 Box_Btm
③ 若價格突破箱體 → 盤整失效，退出
```

### 第二層：方向過濾
```
① 日線趨勢：Close > MA60 → 偏多（v_Trend_Dir = 1）
② 週線過濾：Close > 20MA AND Close > 60MA（AND 邏輯，比 L1 更嚴格）
③ 風報比：Expected_Reward / Expected_Risk ≥ 1.1
```

### 第三層：進場執行（15M）
```
兩個進場區域：
• BL_Entry_Bot：價格跌到箱底附近 → 反彈回箱底時 Stop 單做多
• BL_Entry_Mid：價格跌到中線附近 → 反彈回中線時 Stop 單做多
前搶 5 tick，Target 設在中線/箱頂
```

**設計思路：在盤整箱體的底部和中線「接球」做多，賺的是盤整突破後的多頭延續。**

---

## 出場邏輯（God Mode MFE 引擎）

### 全倉階段（Stage 1）
| 機制 | 條件 |
|------|------|
| 部分停利 | 40% 口數在目標價出場（Limit） |
| 初始停損 | Box_Btm/Mid - ATR(35) × 4.5（Stop） |
| 時間停損 | 持倉 ≥ 31 根 K 棒 → 市價出場 |

### 減倉後（Stage 2-3：MFE 三階追蹤）
```
啟動：價格突破 Box_Top + ATR × 2.5
追蹤停損倍數隨 MFE 距離動態調整：

MFE 距離          追蹤倍數    含義
< ATR × 3.0      3.0 ATR    寬鬆，讓利潤成長
≥ ATR × 3.0      2.0 ATR    收緊
≥ ATR × 6.0      1.5 ATR    更緊
≥ ATR × 10.0     0.8 ATR    極緊，鎖住大部分利潤

追蹤停損 = 最高點 - ATR × 動態倍數
若追蹤停損 < 進場價 → 改用打平停損（BE）
```

### 盤整失效出場
```
若盤整箱體被打破（日線突破 Box_Top 或 Box_Btm）且仍持倉
→ 市價出場（BL_BreakExit）
```

### 週末出場
```
週六 04:00 後強制平倉
```

---

## 參數一覽

| 參數 | 值 | 模組 | 說明 |
|------|-----|------|------|
| Lookback_Bars | 4 | Commander | 盤整參考期（日線） |
| Range_Shrink_Rate | 0.6 | Commander | 波幅收縮門檻（60%） |
| Daily_MA_Len | 60 | Commander | 日線趨勢 MA |
| Min_RR_Bull | 1.1 | 過濾 | 最低風報比 |
| ATR_Length | 35 | 共用 | ATR 計算長度 |
| ATR_Stop_Mult | 4.5 | 停損 | 初始停損 ATR 倍數 |
| FrontRun_Ticks | 5 | 進場 | 前搶 tick 數 |
| Time_Stop_Bars | 31 | 停損 | 時間停損 K 棒數 |
| ScaleOut_Percent | 0.4 | 減碼 | 部分停利比例（40%） |
| Trail_Start_Mult | 2.5 | MFE | 追蹤啟動 ATR 倍數 |
| MFE_ATR_Tier_1 | 3.0 | MFE | 第一階收緊門檻 |
| MFE_ATR_Tier_2 | 6.0 | MFE | 第二階收緊門檻 |
| MFE_ATR_Tier_3 | 10.0 | MFE | 第三階極緊門檻 |
| Weekly_MA_Fast | 20 | 週線 | 週線快速 MA |
| Weekly_MA_Slow | 60 | 週線 | 週線慢速 MA |

---

## MC 設定

| 項目 | 設定 |
|------|------|
| Data1 | TXF1 15 分鐘 |
| Data2 | TXF1 日線 |
| Data3 | TXF1 週線 |
| 初始資金 | 1,000,000 NTD |
| 滑價 | 1,000 NTD/口 |
| 手續費 | 0 |

---

## 策略特色

1. **盤整箱體偵測**：日線自動辨識波動收縮（≤ 60%），不依賴主觀判斷
2. **雙進場區域**：底部和中線兩個接球點，提高進場機會
3. **MFE 三階追蹤（God Mode）**：隨利潤增長自動收緊停損，從 3.0 ATR 收到 0.8 ATR
4. **部分停利 + 追蹤**：40% 先落袋，60% 讓利潤奔跑
5. **AND 週線過濾**：比 L1 的 OR 過濾更嚴格，確保多頭環境確立才進場
6. **時間過濾**：凌晨 4-5 點和週六不進場
7. **盤整失效保護**：箱體被打破時立即出場，不硬撐
