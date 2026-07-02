# L3 盤整多 — STRATEGY_WILLY_LONG_C

> 腳本名稱：_Backtest_Adaptive_Farmer_v14_PureLong
> MC 載入名稱：STRATEGY_WILLY_LONG_C
> 版本：**v14.0 Matrix Range Capture + FrozenSL + HolidayFlat_v3 + ImmediateStop**
> 平台：MultiCharts 9.0 PowerLanguage x64
> 狀態：**V14 PENDING MC9 VALIDATION**（程式碼已完成，等待 MC9 回測驗證）
> 口數：1 口
> 深度審查：`L3_ConsolidationLong_review.md`

---

## V14 架構升級（2026-07-03）

### 問題診斷

v13 半箱設計將盤整箱拆為 Bot→Mid 和 Mid→Top 兩腿，結構性鎖死 reward ratio ~1.1x：
- **CL_Entry_Bot**：26 筆 / 6.5 年，勝率 26.9%，淨損 -10.4K（死腿）
- **CL_Entry_Mid**：405 筆，勝率 51.9%，淨利 +707.6K（所有利潤來源）
- 94% 利潤來自中線進場，但目標只吃半箱 → 盈虧比 1.1x 不匹配盤整策略應有水準

### 設計方向

**用戶裁示**：不管箱多大、行情在哪處盤整，都要完整吃到盤整規律的獲利。採用多維度思維方式以及矩陣化建構程式碼。

### V14 矩陣四維度

| 維度 | 內容 | 對應邏輯 |
|------|------|---------|
| **Dim 1: Box Qualification** | 箱體大小過濾（Min_Box_ATR） | 避開磨耗吃掉 edge 的小箱 |
| **Dim 2: Support Zone** | 統一支撐區進場（Entry_Zone_Pct） | 箱底 30% 區域統一進場 |
| **Dim 3: Dynamic Target** | 動態 swing high（Swing_Lookback） | 15M 實際壓力位，capped at Box_Top |
| **Dim 4: Trend + Daily** | 環境過濾（不變） | 60M MA + Daily MA OR |

### Pre-Verify 結果（Python 28 年 TWII Daily）

| 指標 | A: 半箱（現行） | B: 全區間 | C: 過濾全區間 |
|------|:-----------:|:-------:|:----------:|
| PF | 0.806 | 1.021 | **1.086** |
| Reward Ratio | 0.90x | 1.92x | **1.85x** |
| Cum Return | -94% | +9% | **+33%** |
| Sharpe(ann) | -0.280 | 0.024 | **0.086** |

> Daily data 對 range 策略不利（15M 精確執行的 alpha 無法反映），但方向性確認全區間 > 半箱。
> 預估 intraday uplift 套用後：Filtered PF ~1.47（vs 現行 1.187）。

### V14 vs V13 差異總覽

| 項目 | V13.4 | V14.0 |
|------|-------|-------|
| 進場 | CL_Entry_Bot + CL_Entry_Mid 雙腿 | **CL_Entry** 統一支撐區 |
| 目標 | Bot→Mid / Mid→Top（半箱） | **動態 swing high → 全區間** |
| 腿分類 | v_Leg_IsBot 分流 | **已移除**（無需） |
| 箱體門檻 | 無 | **Min_Box_ATR = 3.0** |
| 進場區域 | 固定中線/箱底 | **Entry_Zone_Pct = 0.30** |
| Swing Target | 無 | **Swing_Lookback = 32** |
| 出場標籤 | CL_TP_Bot / CL_TP_Mid | **CL_TP** |
| 安全模組 | 全部 | **全部保留** |

---

## V13.2B 生產設定歷史（2026-06-13 用戶裁定）

| 開關 | 生產值 | 裁決依據 |
|------|------|---------|
| Freeze_SL_On | **true** | 進場當根鎖定停損+目標。淨利 +12%、MDD -21%、淨利/MDD 1.89→2.67 |
| BE_Trigger_Pts | **0（關閉）** | 變體 D 否決：100 筆 CL_BE 零勝率，BE 截斷 ~96 次到價獲利。**L1 保本邏輯不適用區間策略** |

## Cooldown-D 測試紀錄（2026-06-25，已移除）

4 種 Cooldown 變體全部 FAIL（-4.5% ~ -51.7%），L3 是區間策略，同箱重進場產生 TP 贏家。

---

## 策略概述

- **類別**：盤整區間型
- **方向**：純做多
- **週期**：Data1 = 15M / Data2 = 60M / Data3 = 日線
- **核心邏輯**：60M 偵測盤整箱體（收縮 ≤ 10%）→ 箱體大小過濾 → 日線多頭確認 → 15M 支撐區接球做多 → 動態 swing high 全區間停利

---

## MC9 回測績效

### V13.4 基準（Excel 2026/06/07，Variant B Production）

| 指標 | 數值 |
|------|------|
| 回測區間 | 2020/01/07 ~ 2026/06/06 |
| 總交易次數 | 431 |
| 勝率 | 50.35% |
| Profit Factor | 1.187 |
| 淨利 | +697,200 NTD |
| MDD | -368,800 NTD (-30.24%) |
| 盈虧比 | 1.165 |
| 市場曝險 | 8.35% |

### V14.0 MC9 回測 — **PENDING**

> 載入 V14 程式碼後，設定新 inputs 並跑回測。
> 比較重點：PF、盈虧比（預期 1.1x → 1.5x+）、交易筆數變化。

---

## 進場邏輯（V14）

### 第一層：60M 盤整偵測（Commander，不變）
```
① High ≤ Ref_High AND Low ≥ Ref_Low（完全在前 16 根區間內）
② 當前波幅 / 參考區間 ≤ 10%（極度收縮）
→ 箱體成立，記錄 Box_Top 和 Box_Btm
③ 60M 收盤突破箱體 → 盤整失效
```

### 第二層：V14 箱體資格矩陣（Dim 1, NEW）
```
Box_Range = Box_Top - Box_Btm
Box_Range / ATR(9) >= Min_Box_ATR (3.0)
→ 過濾磨耗型小箱
```

### 第三層：方向過濾（不變）
```
60M 趨勢：Close > MA(12) → v_Trend_Dir = 1
日線過濾：Close > 20MA OR Close > 60MA（OR 邏輯）
```

### 第四層：統一支撐區進場（Dim 2, NEW）
```
Support_Zone = Box_Btm + Box_Range × Entry_Zone_Pct (0.30)
條件：Close < Support_Zone AND Close > Box_Btm - ATR × 3.0
→ Buy ("CL_Entry") next bar at Box_Btm Stop

V13 雙腿 CL_Entry_Bot + CL_Entry_Mid 已合併為單一 CL_Entry。
Stop order at Box_Btm: below box = bounce fill; in zone = fills at open.
```

---

## 出場邏輯（V14）

### 動態 Swing High 目標（Dim 3, NEW）
```
進場當根計算一次，之後凍結（Freeze_SL_On）：
  Swing_High = Highest(High, 32)  [15M 過去 32 根 = ~8 小時]
  Frozen_Target = Min(Swing_High, Box_Top)  [不超過箱頂]
  若 Frozen_Target < Mid_Line + ATR → 降級為 Box_Top  [保證最低報酬]
→ Sell ("CL_TP") next bar at Frozen_Target Limit
```

### 凍結停損（不變）
```
Frozen_SL = Box_Btm - ATR(9) × 3.0（進場當根鎖定）
→ Sell ("CL_SL") next bar at Frozen_SL Stop
```

### 盤整失效出場（不變）
```
60M 收盤突破箱體 → Sell ("CL_BreakExit") next bar at Market
注意：V14 BreakExit 只在真正箱體破壞時觸發，
     箱體資格因 ATR 變化而改變不會觸發退出。
```

---

## 參數一覽

| 參數 | 值 | 模組 | 說明 |
|------|-----|------|------|
| Lookback_Bars | 16 | Commander(60M) | 盤整參考期 |
| Range_Shrink_Rate | 0.1 | Commander(60M) | 波幅收縮門檻（10%） |
| MA_Len | 12 | 趨勢過濾(60M) | 60M MA |
| **Entry_Zone_Pct** | **0.30** | **V14 Matrix** | **支撐區 = 箱底 30%** |
| **Min_Box_ATR** | **3.0** | **V14 Matrix** | **箱體最小 ATR 倍數** |
| **Swing_Lookback** | **32** | **V14 Matrix** | **15M swing high 回看根數** |
| ATR_Length | 9 | 風控(15M) | ATR 計算長度 |
| ATR_Stop_Mult | 3.0 | 停損(15M) | 停損 ATR 倍數 |
| Daily_MA_Fast | 20 | 日線過濾 | 日線快速 MA |
| Daily_MA_Slow | 60 | 日線過濾 | 日線慢速 MA |
| Freeze_SL_On | true | 凍結引擎 | V14 永遠 true |
| BE_Trigger_Pts | 0 | BE 層（關閉） | 區間策略不適用 BE |

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

---

## 出場標籤對照

| 標籤 | V14 觸發條件 |
|------|------------|
| CL_TP | Dynamic swing high / Box_Top limit（全區間目標） |
| CL_SL | Frozen SL at Box_Btm - ATR × 3.0 |
| CL_BE | BE floor（disabled, BE_Trigger_Pts = 0） |
| CL_BreakExit | 60M close 突破箱體（真正 box break） |
| CL_Holiday | 休市前夕夜盤尾段 ≥ 04:15 強制歸零 |
| CL_Settlement | 結算日 ≥ 12:30 歸零 |
| CL_RegistryEnd | 超出假日登錄驗證視界 |
| CL_Kill | 手動緊急出場 |
