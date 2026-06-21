# S4 TurnOfMonth_Long — Strategy Specification (W1 Draft)

**版本**：v0.1 (W1 draft, alpha thesis)
**建立日**：2026-06-21
**狀態**：📋 設計討論階段（pre-code）
**作者**：Claude（依 [roadmap](../../../docs/strategy_development_roadmap_v1_20260620.md) §9.1 #2 草擬）

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
| Hold period | 5-7 trading days |
| Trades/year | ~12（每月 1 次） |
| Portfolio role | Sharpe-additive diversifier（ρ ≈ 0 with all existing）|

---

## 2. Alpha Thesis（**核心 — 必須先 verify**）

### 2.1 國際學術文獻

**Turn-of-Month Effect** = 月末最後 4 個交易日 + 月初前 3 個交易日的**股市超額正報酬**現象：

| 文獻 | 結論摘要 |
|------|---------|
| Ariel (1987) | S&P 500 全月報酬 90%+ 集中在 T-4 to T+3 |
| Lakonishok & Smidt (1988) | DJIA 100 年資料確認 effect 在 T-1 to T+4 |
| Kunkel & Compton (1998) | 全球 17 個國家股市 effect 普遍存在 |
| McConnell & Xu (2008) | 1987-2005 美股 effect 仍存在（無 decay）|
| Liu (2013) | 亞洲市場（含 TWSE）effect 偏弱但統計顯著 |

### 2.2 機制（為什麼會有）

- **401(k) / 退休金月底自動投入** → 月底前最後幾天 buy pressure
- **Mutual fund window dressing** → 月底結算前持倉調整為「好看」標的
- **Salary inflow** → 月初前幾天個人投資金流入
- **Quarterly rebalancing intensification at fiscal month-end**

### 2.3 TXF1 specific 風險

**S2 教訓 #5「教科書公開策略 alpha 衰減」必須警惕**：
- TurnOfMonth 是經典公開效應 → algo / quant 早已套利
- TXF1 機構 vs 散戶結構不同於美股
- 台股退休金結構（勞保 / 勞退）效應強度未知
- **必須跑 2020-2026 完整回測驗證 effect 是否仍存在**

→ W3 回測結果若 PF < 1.2 → 考慮結案（不重蹈 S2 覆轍）

### 2.4 為什麼不會跟 L1-L5 衝突

- L1/L5 是**動量 / 趨勢**驅動（日內或日間動量），不看 calendar
- L2 是**趨勢空**，方向不同
- L3/L4 是**區間突破**，需要區間特徵，calendar 中性
- S1 是**夜盤動量**，timeframe 不同
- S3 v2.0.4 是**短週期 multi-path short**，方向不同
- **S4 是唯一 calendar-driven** → portfolio 真正缺口

---

## 3. Trading Mechanics

### 3.1 進場規則

```
Trigger date: T-4 (月底前第 4 個交易日)
  T-4 計算: 從月底最後一個交易日往前推 4 個交易日
  範例: 2026-06 月底最後交易日 = 6/30 (Tue)
        T-1 = 6/30, T-2 = 6/27 (Fri), T-3 = 6/26 (Thu), T-4 = 6/25 (Wed)
        進場日 = 6/25 day-session close

Trigger time: 日盤 close (13:25-13:45 之間)
Direction: SellLong (LE_TOM_Entry)
Order type: buy next bar at Market
  (T-4 close 觸發 → T-3 開盤成交)

Entry filter:
  - v_Settlement_Day = False (進場日不能是 settlement Wed)
  - v_Holiday_Block = False (不能在假日 tail bar)
  - MP = 0 (必須空倉)
  - Not already entered this month (防止月內多次進場)
```

### 3.2 出場規則

```
Primary exit: T+3 day-session close (月初第 3 個交易日 close)
  Order: sell next bar at Market on T+3 close
  Label: LX_TOM_TPTime

Trailing stop: -2 × ATR(14, Daily) from EntryPrice
  Triggered intra-day when Close < EntryPrice - 2 × ATR
  Label: LX_TOM_TrailStop

Settlement override: 持倉中遇到 Settlement Wed
  Exit at 12:30 (Settlement_Flat_Time) per Rule #11
  Label: LX_TOM_Settlement

Holiday override: 持倉中遇到 holiday eve
  Exit at 02:45 (Holiday_Flat_Time) per Rule #11
  Label: LX_TOM_HolFlat

Force flat: 持倉 > 10 trading days (安全網)
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
  S-1  LX_TOM_TPTime        (T+3 close primary exit)
  S-2  LX_TOM_TrailStop     (-2 ATR trail)
  S-3  LX_TOM_MaxHold       (10-day safety net)
```

### 3.4 SetStopLoss (Rule #12)

```
v_Stop_Distance = 2 * AvgTrueRange(14) of Data1  { in price units }
v_Stop_Amount   = v_Stop_Distance * BigPointValue { in NTD }

if MarketPosition <= 0 then
    SetStopLoss(v_Stop_Amount);

  { Frozen at signal-bar ATR on entry; SetStopLoss engine handles invocation }
```

---

## 4. Parameter List (estimated ~10 inputs)

### 進場日期參數
```
Entry_Day_Before_MonthEnd   ( 4    )   { default T-4, opt 3..5 step 1 }
Exit_Day_After_MonthEnd     ( 3    )   { default T+3, opt 2..4 step 1 }
```

### 風險參數
```
ATR_Trail_Mult              ( 2.0  )   { default 2.0, opt 1.5..3.0 step 0.5 }
ATR_Length                  ( 14   )   { default 14, opt 10..21 step 7 }
Max_Hold_Days               ( 10   )   { safety net, opt 7..14 }
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

**v1.0 共 ~10 個 inputs，比 v1.1 v2.0 的 S3 (29 個) 簡潔得多**。

---

## 5. Expected Performance（pre-backtest, **必須驗證**）

### 5.1 樂觀預估

| 指標 | 預估 | 出處 |
|------|------|------|
| Trades/年 | 12 | calendar (每月 1 次) |
| **WR** | **58-65%** | 學術文獻平均 |
| **PF (毛)** | **1.5-2.0** | 學術 effect strength |
| **PF (含滑價)** | **1.3-1.7** | 12 trades × $2000 slippage / year |
| Sharpe (年化) | **0.6-1.0** | calendar effect 通常 0.5-1.0 |
| Max DD | **< 8%** | 樣本散開，無 cluster |
| 持倉週期 | 5-7 days | T-4 to T+3 |
| 跨年穩定性 | **HIGH** | calendar 不受 regime 影響 |

### 5.2 悲觀情境

如果 TXF1 calendar effect 已被套利消化：
| 指標 | 悲觀值 |
|------|--------|
| WR | 50-52% |
| PF | 1.0-1.2 |
| 含滑價 PF | < 1.0 |
| Sharpe | < 0.3 |

→ 觸發 S2 lesson: 「教科書 alpha 衰減」→ 考慮結案

### 5.3 對比 Buy & Hold（必檢）

- TXF1 B&H 2020-2026 年化約 ~10-15%（多頭年代）
- S4 預期年化 6-10%（持倉 5-7 days × 12 次/年 = 60-84 days/年 = 30% time in market）
- S4 / B&H ratio = 0.6-0.7 → 配合 ρ≈0 仍 Sharpe-additive ✓

---

## 6. Risk Management

### 6.1 風險清單

| 風險 | 嚴重度 | 緩解 |
|------|--------|------|
| Calendar effect 在 TXF1 已死 | 🔴 HIGH | W3 完整回測驗證，PF < 1.2 → 結案 |
| Settlement Wed 衝突 | 🟠 MED | Skip 該月 entry (Option A) |
| 持倉跨假日連續長假 (CNY) | 🟠 MED | Holiday_Flat 強制 02:45 平倉 |
| 月內多次進場 | 🟡 LOW | One-entry-per-month guard |
| ATR-2 stop 在低 vol 月被打 | 🟡 LOW | Trail 用 14-day ATR 平滑 |
| 樣本不足（78 trades 6.5 年） | 🟡 LOW | Sample-gate 從 100 放寬到 50 (W5 文件化) |

### 6.2 Failure Modes（學自 S2/S3 v1.1）

```
Mode 1: 跑出來 PF 1.0-1.2 → 「不好不壞」陷阱
  → 不浪漫化：PF < 1.2 即結案，不開 v0.2/0.3...

Mode 2: 完全沒交易（filter 過嚴）
  → v1.0 設計就極簡（10 個 inputs），預期不會發生

Mode 3: Best 集中某幾年（regime over-fit）
  → calendar 不受 regime 影響，理論上不會。但 W4 跨年穩定性必查。

Mode 4: 含滑價虧損
  → 12 trades × $2000 = $24K/年 滑價成本
    Net Profit 必須 > $50K/年才有意義
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

## 8. 跟 S2 lesson 的對應

| S2 lesson | S4 應用 |
|----------|---------|
| #4 突破類 Long-only | S4 本來就 Long-only ✓ |
| #5 教科書 alpha 衰減 | **W3 必驗證 TXF1 effect 是否還在** ⚠️ |
| #10 同日多進場 cooldown | One-entry-per-month guard |
| #11 Buy & Hold 是現實檢驗 | strategy.md 必含 B&H 對比 |
| #12 4 次迭代 + 0 實證 = 警訊 | v1.0 baseline → 直接回測，不超過 2 次迭代 |
| #13 Filter 重疊度檢查 | v1.0 只 10 個 inputs，redundancy 風險低 |

---

## 9. W1-W7 開發路線（**詳見 [README](README.md)**）

```
W1: README + strategy.md      ← NOW
W2: .pla (~150 LOC)
W3: verify_s4 + 完整 baseline 回測 → ★ 第一個決策點
    PF > 1.2 → continue W4
    PF < 1.2 → 結案 (S2 lesson #5)
W4: Phase 1 sensitivity
W5: Phase 2 Walk-Forward
W6: Phase 3 MC + 10-dim eval ← ★ 第二個決策點
W7: promote to live_simulation
```

---

## 10. 用戶決策點（W1 → W2 transition 前必確認）

### Q1 - 進場日 T-N
- A: **T-4**（學術建議，baseline）
- B: T-5（更早進場）
- C: T-3（晚一天進場）

### Q2 - 出場日 T+N
- A: **T+3**（學術建議，baseline）
- B: T+2（早一天出場）
- C: T+4（晚一天出場）

### Q3 - Settlement Wed 衝突處理
- A: **Skip 該月 entry**（最安全，預期 12 → 11 trades/年）
- B: 改用 T-3 entry 避開
- C: 強制 12:30 平倉跨 Settlement

### Q4 - Trend filter
- A: **純 calendar v1.0**（baseline，pure alpha test）
- B: 加 Daily MA200 filter（v1.0 就加）

### Q5 - W3 結果如果 PF < 1.2
- A: **立即結案**（S2 lesson #5 應用）
- B: 進 W4 sensitivity sweep 看能否救
- C: 加 trend filter v0.2 再試

**我的推薦：A/A/A/A/A**（保守 baseline + 嚴格結案標準，避免 S2 spiral）。

---

## 11. 文件版本

| 版本 | 日期 | 變更 |
|------|------|------|
| v0.1 (本檔) | 2026-06-21 | W1 alpha thesis draft，待用戶 review 5 個 Q |

---

**等用戶確認 Q1-Q5 → 進 W2 寫 `.pla` (~150 LOC)**。
