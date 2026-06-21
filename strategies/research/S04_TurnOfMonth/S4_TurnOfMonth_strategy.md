# S4 TurnOfMonth_Long — Strategy Specification (KILLED)

> 💀 **2026-06-21 KILLED — DO NOT IMPLEMENT**
> 詳見：[S4_FINAL_VERDICT.md](S4_FINAL_VERDICT.md)
>
> 本 spec v0.2 基於 6.4-year empirics 看起來通過，但 28-year robustness test
> 揭露這是 cyclical alpha decay：2010-2018 連 8 年負 Sharpe，28y overall
> Sharpe 0.33（recent 6.4y Sharpe 0.87 是 over-optimistic snapshot）。
>
> 本檔保留作 audit trail + 5 個新 lessons (L14-L18) 教材，**不可作為 .pla 實作依據**。

---

**版本**：v0.2 (TXF1-empirics-corrected) → **KILLED 2026-06-21**
**建立日**：2026-06-21（v0.1 → v0.2 → KILLED 同日）
**狀態**：💀 KILLED — DO NOT IMPLEMENT
**作者**：Claude

---

## ⚠️ v0.1 → v0.2 重大變更（學自 S2 lesson #2「設計超前實證」）

v0.1 使用美股學術 baseline（T-4 entry / T+3 exit, 7-day hold）。  
**用戶 2026-06-21 質疑**：「學術不等於 TXF1 實證」。

跑 [`analyze_s4_turn_of_month_empirics.py`](../../../scripts/analyze_s4_turn_of_month_empirics.py) +
[`analyze_s4_yearly_stability.py`](../../../scripts/analyze_s4_yearly_stability.py)
（TWII 2020-2026 1558 個交易日）發現：

| 維度 | v0.1 學術 | **v0.2 實證** | 改善 |
|------|----------|--------------|------|
| Entry day | T-4 | **T-1**（月底最後一天）| 大改 |
| Hold period | 5-7 days | **4 days**（≈ T-1 → T+3）| 縮短 |
| Sharpe (年化) | 0.395 (guess) | **0.869** (實證) | **+120%** |
| PF | 1.380 (guess) | **1.97** (實證) | **+43%** |
| WR | 62.3% (guess) | **67.5%** (實證) | +5pp |

→ **v0.2 是基於 6.4 年 TXF1 實證的校正版**。

---

## 1. Strategy Identity

| 欄位 | 值 |
|------|-----|
| Name | **S4 TurnOfMonth_Long** |
| MC Load Name | `STRATEGY_GEN_S4_TurnOfMonth_Long`（待定）|
| Class | **Calendar Effect Positional Long**（純日曆效應、無動量、無 regime） |
| Direction | **Long-only** |
| Timeframe | **Data1 = Daily**（純 day-session, 1D bar） |
| Data feeds | Data1 Daily（**單一 feed，無需 multi-TF**）|
| **Hold period** | **4 trading days**（實證 best）|
| Trades/year | ~12（每月 1 次） |
| Portfolio role | Sharpe-additive diversifier（**ρ ≈ 0** with all existing）|

---

## 2. Alpha Thesis

### 2.1 國際學術文獻（**僅作為 motivation，不作為設計依據**）

| 文獻 | 結論摘要 |
|------|---------|
| Ariel (1987) | S&P 500 月報酬 90%+ 集中在 T-4 to T+3 |
| Lakonishok & Smidt (1988) | DJIA 100 年資料確認 effect 在 T-1 to T+4 |
| Kunkel & Compton (1998) | 全球 17 個國家股市 effect 普遍存在 |
| McConnell & Xu (2008) | 1987-2005 美股 effect 仍存在（無 decay）|
| Liu (2013) | 亞洲市場（含 TWSE）effect 偏弱但統計顯著 |

### 2.2 機制（為什麼會有）

- **退休金月底自動投入** → 月底前最後幾天 buy pressure
- **Mutual fund window dressing** → 月底結算前持倉調整為「好看」標的
- **薪資 inflow** → 月初前幾天個人投資金流入
- **Quarterly rebalancing intensification at fiscal month-end**

### 2.3 ⭐ TXF1 實證證據（**v0.2 核心 — 取代學術假設**）

**Single-day anomaly (per-day mean return, basis points, t-test)**：

| Slot | N | Mean (bps) | WR% | t-stat | 顯著 |
|------|---|-----------|------|--------|------|
| T-7 | 77 | +20.66 | 57.1% | 1.41 | ns |
| T-6 | 77 | -4.55 | 45.5% | -0.34 | ns |
| **T-5** ⭐ | 78 | **+47.96** | **67.9%** | **3.42** | **\*\*\* (p<0.01)** |
| T-4 | 78 | +8.44 | 59.0% | 0.77 | ns |
| T-3 | 78 | +12.25 | 64.1% | 1.04 | ns |
| T-2 | 78 | -8.89 | 50.0% | -0.61 | ns |
| **T-1** | 78 | **-18.84** | 46.2% | -1.47 | **單日負，但作為 entry day 表現最佳** |
| T+1 | 76 | +18.34 | 55.3% | 1.12 | ns |
| T+2 | 77 | +20.83 | 59.7% | 1.53 | ns |
| T+3 | 77 | +6.74 | 71.4% | 0.31 | ns |
| **T+4** | 77 | +27.56 | 61.0% | 1.91 | **\* (p<0.10)** |
| middle | 480 | +3.32 | 52.1% | 0.58 | 基線（無 alpha）|

### 2.4 ⭐ Multi-day Hold 實證（找 best config）

| Entry | Hold (days) | N | Mean% | WR% | PF | **Sharpe(年化)** |
|-------|------------|---|-------|-----|-----|----------|
| **T-1** | **4** ⭐ | 77 | **0.791** | **67.5%** | **1.970** | **0.869** |
| T-1 | 3 | 77 | 0.526 | 72.7% | 1.665 | 0.652 |
| T-2 | 5 | 77 | 0.618 | 66.2% | 1.677 | 0.633 |
| T-3 | 6 | 77 | 0.543 | 70.1% | 1.549 | 0.550 |
| T-4 | 7 | 77 | 0.644 | 66.2% | 1.660 | 0.618 |
| T-4 | 6 (v0.1) | 77 | 0.379 | 62.3% | 1.380 | 0.395 |
| T-5 | 7 | 77 | 0.463 | 61.0% | 1.450 | 0.446 |

**結論**：**T-1 enter, 4-day hold** 是 TXF1 真實 best（不是學術 T-4/T+3）。

### 2.5 ⭐ 跨期穩定性（Sub-period split）

| Period | N | Sharpe(年化) | PF | WR% | Cum% |
|--------|---|------------|------|------|------|
| Early (2020-01 → 2024-10, 4.76y) | 58 | **0.927** | 1.940 | 70.7% | +39.51% |
| Late (2024-11 → 2026-06, 1.50y) | 19 | **0.885** | 2.032 | 57.9% | +21.37% |
| **Ratio late/early** | — | **0.95×** | — | — | — |

**Sharpe ratio = 0.95×** → ✅ **跨期一致，非 regime over-fit**。  
（對比 S3 v1.1：54% trades 集中 2026 H1 = regime concentration）

### 2.6 ⭐ Yearly Breakdown（**alpha 是否每年都在**）

| Year | N | Cum% | WR% | PF | 狀態 |
|------|---|------|------|-----|------|
| 2020 | 12 | **+30.16%** | 91.7% | 23.22 | 牛市，極強 |
| 2021 | 12 | +5.54% | 75.0% | 1.78 | 正常 |
| **2022** | 12 | **-6.63%** | 41.7% | 0.60 | **空頭年虧損** ⚠️ |
| 2023 | 12 | +4.99% | 66.7% | 2.11 | 正常 |
| 2024 | 12 | +12.63% | 83.3% | 2.01 | 正常 |
| 2025 | 12 | +0.50% | 50.0% | 1.03 | 平淡 |
| 2026 (5m) | 5 | +13.68% | 60.0% | 3.38 | 強 |

**6/7 年正報酬**，只 2022 年虧損 6.63%。

### 2.7 與 L1-L5 + S1 + S3 完全不衝突

- L1/L5 是**動量 / 趨勢**驅動 → calendar 中性
- L2 是**趨勢空** → 方向不同
- L3/L4 是**區間突破** → calendar 中性
- S1 是**夜盤動量** → timeframe 不同
- S3 v2.0.4 是**短週期 multi-path short** → 方向不同
- **S4 是 portfolio 中唯一 calendar-driven** → 真正缺口

---

## 3. Trading Mechanics（**v0.2 修正版**）

### 3.1 進場規則

```
Trigger date: T-1 (月底最後一個交易日)
  T-1 計算: 該月份的最後一個交易日（month_groups[year, month][-1]）
  範例: 2026-06 月底最後交易日 = 6/30 (Tue)
        進場日 = 6/30 day-session close

Trigger time: 日盤 close (13:25-13:45 之間)
Direction: Long (LE_TOM_Entry)
Order type: buy next bar at Market
  (T-1 close 觸發 → 下一交易日 = T+1 (新月份的第 1 個交易日) open 成交)

Entry filter:
  - v_Settlement_Day = False (進場日不能是 settlement Wed)
  - v_Holiday_Block = False (不能在假日 tail bar)
  - MP = 0 (必須空倉)
  - 距上次出場 ≥ 8 個交易日 (防止月內多次進場)
```

### 3.2 出場規則

```
Primary exit: 進場後 4 個交易日的 close
  Order: sell next bar at Market on 4th day close
  Label: LX_TOM_TPTime
  範例: T-1 = 6/30 進場 → T+1, T+2, T+3, T+4 持倉 → T+4 close 出場
       = 月初前 4 個交易日 close 出場 (~7/6 if no holidays)

Trailing stop: -2 × ATR(14, Daily) from EntryPrice
  Triggered intra-day when Close < EntryPrice - 2 × ATR
  Label: LX_TOM_TrailStop

Settlement override: 持倉中遇到 Settlement Wed
  Exit at 12:30 (Settlement_Flat_Time) per Rule #11
  Label: LX_TOM_Settlement
  注意: T-1 進場後最多持倉 4 個交易日，跨 settlement Wed 機率約 30%

Holiday override: 持倉中遇到 holiday eve
  Exit at 02:45 (Holiday_Flat_Time) per Rule #11
  Label: LX_TOM_HolFlat

Force flat: 持倉 > 7 trading days (安全網)
  Label: LX_TOM_MaxHold
```

### 3.3 Priority 0 Chain（Rule #11 強制）

```
Order (highest to lowest):
  P0-1 LX_TOM_Kill          (Manual_Kill_Switch)
  P0-2 LX_TOM_RegistryEnd   (registry expired)
  P0-3 LX_TOM_HolFlat       (holiday eve flat at 02:45)
  P0-4 LX_TOM_Settlement    (settlement Wed flat at 12:30)
  ────────────────────────
  S-1  LX_TOM_TPTime        (4th day close primary exit)
  S-2  LX_TOM_TrailStop     (-2 ATR trail)
  S-3  LX_TOM_MaxHold       (7-day safety net)
```

### 3.4 SetStopLoss (Rule #12)

```
v_Stop_Distance = 2 * AvgTrueRange(14) of Data1  { in price units }
v_Stop_Amount   = v_Stop_Distance * BigPointValue { in NTD }

if MarketPosition <= 0 then
    SetStopLoss(v_Stop_Amount);
```

---

## 4. Parameter List (~10 inputs)

### 進場日期參數
```
Entry_Day_FromMonthEnd      ( 1    )   { default T-1, opt 1..3 step 1 (was T-4) }
Hold_Days                   ( 4    )   { default 4, opt 3..6 step 1 (was 7) }
```

### 風險參數
```
ATR_Trail_Mult              ( 2.0  )   { default 2.0, opt 1.5..3.0 step 0.5 }
ATR_Length                  ( 14   )   { default 14, opt 10..21 step 7 }
Max_Hold_Days               ( 7    )   { safety net, opt 5..10 (was 10) }
Min_Days_Between_Trades     ( 8    )   { 防月內多次進場 }
```

### Settlement / Holiday 沿用 portfolio 共用
```
Holiday_Flat_Time           ( 245    )
Registry_Valid_Until        ( 1270101 )
Manual_Kill_Switch          ( False  )
Settlement_Flat_Time        ( 1230   )
```

### 可選 filter（v1.1 才加，v1.0 default OFF）
```
Trend_Filter_On             ( False  )   { 加 Daily MA200 trend filter }
MA200_Length                ( 200    )
```

**v0.2 共 ~10 個 inputs**，比 S3 (29 個) 簡潔。

---

## 5. Expected Performance（**v0.2 實證數字**，非 guess）

### 5.1 預期（基於 TWII 2020-2026 實證）

| 指標 | 實證 (TWII) | 預估 TXF1 (含滑價) | 標準 |
|------|------------|-------------------|------|
| Trades/年 | 12 | 12 | calendar |
| **WR** | **67.5%** | 60-65% (略折扣)| 學術 ≈ 60% |
| **PF (毛)** | **1.97** | ~1.6 (含 12 × $2K 滑價)| ≥ 1.5 ✓ |
| **PF (含滑價)** | — | **1.5-1.7** | ≥ 1.3 ✓ |
| Sharpe (年化) | **0.869** | 0.6-0.8 | ≥ 0.5 ✓ |
| Max DD | ~10% | < 12% | < 15% ✓ |
| 持倉週期 | 4 days | 4 days | — |
| 跨年穩定性 | **HIGH** (6/7 年正)| HIGH | — |

### 5.2 對比 Buy & Hold（**S2 lesson #11 現實檢驗**）

| 指標 | S4 best | TWII B&H |
|------|---------|---------|
| 總報酬 6.4y | +60.88% | +272.47% |
| 年化 | 9.5% | 22.72% |
| Sharpe | 0.869 | 1.113 |
| Time in market | 23% | 100% |

**S4 落後 B&H 4.5×**，但因 ρ≈0 仍是 portfolio Sharpe-additive sleeve。

### 5.3 Portfolio 角色預估

- 建議配置：**3-5%**（不可多，因為 standalone alpha 比 B&H 弱）
- 預期 portfolio Sharpe 貢獻：**+0.10 - +0.15**
- 預期年化貢獻：**+0.3-0.5%** to total portfolio return

---

## 6. Risk Management

### 6.1 風險清單

| 風險 | 嚴重度 | 緩解 |
|------|--------|------|
| **空頭年虧損 (2022 PF 0.60)** | 🔴 **HIGH** | **必須在 spec 中 disclose；用戶決策是否加 trend filter v1.1** |
| Settlement Wed 衝突 (持倉跨) | 🟠 MED | 強制 12:30 平倉，Priority 0 chain |
| 持倉跨假日連續長假 (CNY) | 🟠 MED | Holiday_Flat 強制 02:45 平倉 |
| 月內多次進場 | 🟡 LOW | Min_Days_Between_Trades ≥ 8 guard |
| ATR-2 stop 在低 vol 月被打 | 🟡 LOW | Trail 用 14-day ATR 平滑 |
| 滑價成本 25% 毛利 | 🟠 MED | 12 trades × $2K = $24K/年 vs ~$95K 毛利 |
| 樣本邊際 (78 trades) | 🟡 LOW | Sample-gate 從 100 放寬到 50 (W5 文件化) |

### 6.2 ⚠️ 必須對用戶 Disclose 的 1 件事

**2022 空頭年 cum -6.63% / WR 41.7% / PF 0.60**：
- S4 在 bear market year **預期虧損**
- 這是 calendar effect 的本質：資金流入也救不回大盤跌勢
- v1.0 純 calendar 不加 trend filter → 接受空頭年虧損
- v1.1 可考慮加 Daily MA200 trend filter（只在 Close > MA200 時 enable）

### 6.3 Failure Modes（學自 S2/S3 v1.1）

```
Mode 1: 跑出來 PF 1.0-1.5 → 「不好不壞」陷阱
  → v0.2 已實證 1.97 → 若 MC12 跑 < 1.5 即為 implementation bug
    (因為 W1 已驗證 alpha 真實存在)

Mode 2: 完全沒交易（filter 過嚴）
  → v0.2 設計極簡（10 個 inputs，calendar-only），預期不會發生

Mode 3: Best 集中某幾年（regime over-fit）
  → v0.2 已用 sub-period split 確認跨期一致 (late/early Sharpe 0.95×)
    
Mode 4: 含滑價虧損
  → 12 trades × $2K = $24K/年 滑價成本
    Mean return 0.791%/trade × 12 = 9.5% × 1.5M 帳戶 = ~$143K
    扣完 $24K 仍 +$119K = 8% annual
    → 滑價可承受
```

---

## 7. Mandatory Compliance（Rule #11/#12/#13）

### Rule #11 Settlement_Flat
- ✓ 7 元素：v_Settlement_Day / DayOfWeek check / DayOfMonth bounds / Settlement_Flat_Time / Settlement label / Priority 0 / entry gate
- ✓ Priority 0 順序：Kill > Registry > Holiday > Settlement > strategy exits
- ✓ Entry gate 含 `v_Settlement_Day = False`

### Rule #12 P3b SetStopLoss
- ✓ 單一 SetStopLoss call
- ✓ Guard `if MarketPosition <= 0`（Long 變體）
- ✓ Distance = ATR_Trail_Mult × ATR × BigPointValue
- ✓ 進場前呼叫，進場後自動 freeze

### Rule #13 10-dim eval
- Pre-deploy: W6 跑完整 10-dim evaluation
- 任一 fail → 不可進 live_simulation
- 即使 1-line input 改也須重評

---

## 8. 跟 S2 lesson 的對應（**v0.2 已 active 應用**）

| S2 lesson | v0.2 應用狀態 |
|----------|--------------|
| #2 設計超前實證 | ✅ **已修正** — v0.1→v0.2 用實證取代學術 baseline |
| #4 突破類 Long-only | ✅ S4 本來就 Long-only |
| #5 教科書 alpha 衰減 | ✅ W1 已實證 TXF1 effect 仍存在（PF 1.97 6.4 年） |
| #10 同日多進場 cooldown | ✅ Min_Days_Between_Trades = 8 |
| #11 Buy & Hold 是現實檢驗 | ✅ Spec 5.2 含 B&H 對比（誠實落後 4.5×） |
| #12 4 次迭代 + 0 實證 = 警訊 | ✅ v0.2 = 實證後 1 次校正，不會再迭代 v0.3+ 除非新證據 |
| #13 Filter 重疊度檢查 | ✅ v0.2 只 10 個 inputs，redundancy 風險低 |

---

## 9. W1-W7 開發路線

```
W1: ✅ README + strategy.md v0.2 (TXF1-empirics-corrected, 2026-06-21)
W2: ⏳ 寫 .pla (~150 LOC, 純 calendar 邏輯)
W3: ⏳ verify_s4 + 完整 baseline 回測 → ★ 第一個決策點
    PF > 1.5 → continue W4 (門檻提高，因為 W1 已實證 1.97)
    PF < 1.5 → implementation bug，回頭追查
W4: ⏳ Phase 1 sensitivity (T-N entry day / N-day hold 邊界)
W5: ⏳ Phase 2 Walk-Forward
W6: ⏳ Phase 3 MC + 10-dim eval ← ★ 第二個決策點
W7: ⏳ promote to live_simulation
```

---

## 10. 用戶決策點（**v0.2 修正版**）

### Q1 - 進場日 T-N
- ~~v0.1: T-4 (學術 baseline)~~
- **v0.2 推薦：T-1**（**實證 best**，Sharpe 高 2.2 倍）
- 備選：T-2 (Sharpe 0.633), T-3 (Sharpe 0.550)

### Q2 - 持倉天數
- ~~v0.1: T+3 (= 7-day hold)~~
- **v0.2 推薦：4 days**（**實證 best**, Sharpe 0.869）
- 備選：3 days (Sharpe 0.652), 5 days (Sharpe 0.633)

### Q3 - Settlement Wed 衝突處理
- **v0.2 推薦：Skip 該月 entry**（最安全，符合 Rule #11 精神）
- 備選：強制 12:30 平倉跨 Settlement / 改用 T-2 entry 避開

### Q4 - Trend filter
- **v0.2 推薦：v1.0 純 calendar**（baseline，符合 Q5 嚴格門檻）
- 備選：v1.0 就加 Daily MA200 filter（會降低 2022 空頭年虧損但減少 trades）

### Q5 - W3 結果如果 PF < 1.5（**門檻從 1.2 提高到 1.5**）
- **v0.2 推薦：立即追查 implementation bug**
- W1 已實證 PF 1.97，若 W3 < 1.5 = 程式碼有錯，不是 alpha 死
- 若追查後仍 < 1.5 → 結案

**我的推薦：A/A/A/A/A**（基於實證的 baseline）

---

## 11. 文件版本

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.2 (本檔) | 2026-06-21 | **TXF1-empirics-corrected**：用實證取代學術 baseline |
| v0.1 | 2026-06-21 | W1 學術 baseline 草稿（已棄用，保留供 audit）|

---

**等用戶確認 Q1-Q5（v0.2 推薦 A/A/A/A/A）→ 進 W2 寫 `.pla` (~150 LOC)**。
