# S4 TurnOfMonth_Long — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（**研發 2 天 + 1 個版本即 KILL**）
**狀態**：💀 **KILLED — NOT FEASIBLE**（不可行，正式結案）
**用戶決策**：2026-06-21 ultracode session（28-year robustness test 後）
**最後版本**：v0.2 (TXF1-empirics-corrected, 從未進 W2 寫 .pla)

---

## 一、為什麼 KILL — 一句話總結

> **學術經典 turn-of-month effect 在 TWII 28 年 (1997-2026) 是 cyclical decay alpha：
> 6 個 macro regime 中只有 3 個有正 Sharpe，2010-2018 連續 8 年負 Sharpe，
> 28-year overall Sharpe 僅 0.33 / Max DD -32% 超過機構警戒 30%。
> 我先前看到的 Sharpe 0.87 是 cyclical revival 期的 over-optimistic snapshot，
> 不是真實長期 alpha。**

---

## 二、KILL 觸發證據（**28 年實證打臉 6.4 年結論**）

### 證據 #1: 6 個 macro regime 表現極不一致

| Regime | 期間 | N | Sharpe | PF | Cum% | 評估 |
|--------|------|---|--------|------|------|------|
| Dot-com 泡沫+崩盤 | 1997-2002 | 66 | **0.096** | 1.08 | +8.51% | ⚠️ marginal |
| 中國牛市 | 2003-2007 | 60 | **0.806** | 1.78 | +39.25% | ✅ 強 |
| GFC | 2008-2009 | 24 | 0.456 | 1.41 | +12.54% | ✓ OK |
| **後 GFC + 歐債** | 2010-2014 | 60 | **-0.063** | 0.95 | -2.22% | ❌ **失效** |
| **横盤+貿易戰** | 2015-2019 | 60 | **-0.404** | **0.73** | **-13.71%** | ❌❌ **負 alpha** |
| COVID+AI | 2020-2026 | 77 | **0.880** | 1.97 | +60.88% | ✅ 強（**我之前看到的**）|

→ **只 3/6 regime 有正 Sharpe**，alpha 是 cyclical 不是持久

### 證據 #2: 2010-2018 連續 8 年負 Sharpe（**institutional dealbreaker**）

| 4-year window | Sharpe | 評估 |
|--------------|--------|------|
| 2010-2014 | -0.063 | ❌ |
| 2011-2015 | -0.659 | ❌ |
| 2012-2016 | -0.519 | ❌ |
| 2013-2017 | -0.201 | ❌ |
| 2014-2018 | -0.502 | ❌ |
| 2015-2019 | -0.448 | ❌ |

**任何 portfolio manager 在 2014 deploy S4 → 連虧 5 年才轉正**  
→ **沒有機構會接受這種策略**

### 證據 #3: 28-year overall 數字遠低於 6.4-year

| 維度 | 我之前說 (6.4y) | **28-year 真相** | 落差 |
|------|---------------|-----------------|------|
| **Sharpe (年化)** | **0.876** | **0.331** | **-62%** |
| PF | 1.970 | 1.296 | -34% |
| WR | 67.5% | 57.9% | -10pp |
| Max DD | ~10% | **-32.07%** | **超過 30% 警戒** |

**Recent / Long-term Sharpe ratio = 2.64×** → **嚴重 recent bias**

### 證據 #4: 含滑價後 28 年版本 break-even

```
Mean per trade: 0.303%
Trades/年: 12.2
Gross annual: 3.7% × 1.5M 帳戶 = $55.5K
滑價: 12 × $2000 = $24K/年
含滑價 net: $31.5K/年 = 2.1% annual

→ 比通膨低，比定存差，比 B&H 22.7% 落後 11×
```

### 證據 #5: 學術文獻其實已預示衰減

- **McConnell & Xu (2008)**：美股 1987-2005 effect 仍存在 → 但已減弱
- **Liu (2013)**：亞洲市場（含 TWSE）effect **「偏弱但統計顯著」** ⚠️ 已是 warning
- **2013 之後沒看到強更新研究確認 TWSE 仍有 effect**

→ 我之前引用學術文獻是錯誤的 anchor — 學術本身就警告過 effect 在 TWSE 偏弱

---

## 三、我（Claude）的失誤檢討

### 失誤 #1: 只用 6.4 年數據判 GO
- 應該至少 15+ 年才能驗證 calendar effect 跨 regime
- 6 年無法涵蓋多個 macro cycle
- **教訓**：calendar / behavioral effect 必須跨 ≥ 2 個 macro cycle 驗證

### 失誤 #2: 「跨期一致」分析只在 backtest 內部 split
- 我把 2020-2024 vs 2024-2026 比 → 都是同個牛市時段
- 沒比 backtest 外的時段（2010-2019）
- **教訓**：sub-period 必須跨 backtest 邊界

### 失誤 #3: 沒主動 fetch 更長歷史
- 1997-2019 TWII data 在 yfinance 一直可用
- 我只用 local twii_daily.csv (2020-2026)
- 直到用戶 prompt 才去抓
- **教訓**：robustness 驗證的第一步是 maximize history window

### 失誤 #4: 重蹈 S2 教訓 #5 覆轍
- S2 lesson #5: 「教科書公開策略 alpha 已大幅衰減」
- TurnOfMonth 是 39 年公開效應（Ariel 1987）
- 應該預設衰減，不是預設仍存在
- **教訓**：教科書策略默認 alpha 已衰減，需要更高證據門檻

### 失誤 #5: 沒及時抓到 Liu (2013) 警告
- 我引用了 Liu 2013，但忽略「effect 偏弱」這個 keyword
- 應該重視亞洲市場學術文獻的 cautionary tone
- **教訓**：學術 quote 必須 read 整段，不是只 cherry-pick title

---

## 四、學自 S4 的 **5 個新 lessons**（永久保留）

1. **L14: Calendar / behavioral effect 必須 ≥ 28 年驗證**
   - 6.4 年絕對不夠
   - 必須跨多個 macro cycle (bull + bear + range + crisis)

2. **L15: 「跨期一致」必須跨 backtest 外的時段**
   - Within-backtest sub-period split 不算驗證
   - 必須有 out-of-sample period (時間上完全沒看過的)

3. **L16: 教科書策略 default alpha 已衰減**
   - 任何公開 ≥ 20 年的 anomaly default 視為已被套利
   - 證據門檻：必須證明在最近 5 年 still active
   - 不夠：必須證明跨 cyclical decay 仍存在

4. **L17: 學術 quote 必須 read 整段不是 cherry-pick**
   - "globally exists" 不等於 "in TWSE strong"
   - "statistically significant" 不等於 "tradable"
   - 重視 cautionary qualifier

5. **L18: Recent-bias check 必須在初步 GO 之前**
   - 算 recent Sharpe / long-term Sharpe ratio
   - > 1.5× → recent bias 警告
   - > 2× → 強烈警告
   - > 2.5× → KILL signal
   - S4 ratio = 2.64× → 明確 KILL

---

## 五、與 S2 對比（**KILL 標準的演進**）

| 維度 | S2 InsideBarBreak | **S4 TurnOfMonth_Long** |
|------|------------------|------------------------|
| 結案理由 | alpha 已死 (PF 1.057 跨 timeframe 一致) | **alpha cyclical decay** (28y Sharpe 0.33, 8 年連虧) |
| 證據 | 6 個迭代 + 2 個 timeframe | **6 個 macro regime + 26 個 rolling window** |
| KILL 速度 | 5 個版本 + 多週迭代 | **2 個版本 + 1 天**（更快 KILL）|
| 教訓貢獻 | 13 個 lessons | **5 個新 lessons (L14-L18)** |
| 開發資源耗用 | 高 | **低**（W1 just 完成即 KILL，沒進 W2 寫 .pla）|

→ **學習效率：S4 KILL 比 S2 快 6 倍**（lessons compound 起作用）

---

## 六、KILL 規範（**永久 archive 規則**）

```
若你看到本檔（S4_FINAL_VERDICT.md）：
  ❌ 不要修改 S4 任何代碼（沒寫 .pla，這條 trivial）
  ❌ 不要寫 S4 .pla（已決定不寫）
  ❌ 不要把 S4 加進 portfolio
  ✅ 可以讀文件參考設計思路
  ✅ 可以引用 5 個新 lessons (L14-L18)
  
重啟條件（極嚴）:
  以下 4 個同時滿足才可考慮:
  1. 學術新研究證明 TWSE turn-of-month effect 復活
  2. 至少 10 年新 OOS data 顯示 Sharpe > 0.5
  3. Trend filter (e.g., MA200) 證明可救 2010-2019 表現
  4. 用戶明確要求重啟
```

---

## 七、資源轉向

S4 KILL 釋出資源 → 直接跳 **S5 SPX_Overnight_DayOpen**（Q2 #3）

但 S5 需要 Phase 0 infra（SPX data feed），可能需要先：
1. 評估是否所有 Q2-Q4 策略都 face S4 類問題（教科書 alpha 衰減）
2. 重新審視 roadmap，可能優先做 portfolio 已 lock 的維護工作
3. 或者直接 cleanup tasks → handoff 下一對話

---

## 八、相關文件交叉參考

- **完整 28-year robustness analysis**：[../../../scripts/analyze_s4_28yr_robustness.py](../../../scripts/analyze_s4_28yr_robustness.py)
- **6.4 年初步分析**：[../../../scripts/analyze_s4_turn_of_month_empirics.py](../../../scripts/analyze_s4_turn_of_month_empirics.py)
- **跨年穩定性分析**：[../../../scripts/analyze_s4_yearly_stability.py](../../../scripts/analyze_s4_yearly_stability.py)
- **歷史 v0.2 spec（已 KILLED）**：[S4_TurnOfMonth_strategy.md](S4_TurnOfMonth_strategy.md)
- **歷史 README**：[README.md](README.md)
- **前置 S2 結案**：[../S02_InsideBarBreak/S2_FINAL_VERDICT.md](../S02_InsideBarBreak/S2_FINAL_VERDICT.md)
- **12 月 roadmap**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)

---

## 九、用戶聲明

> 「A。然後刪除掉的策略絕對要說明為甚麼刪除!」  
> — 2026-06-21 ultracode session

S4 在進 W2 寫 .pla **之前**就被 KILL — 這是**正確的 institutional 紀律**：寧可在 W1 KILL，不要在 W6 投入 6 週後才 KILL。

對比 S2 走完 5 個版本才 KILL，S4 **省下了 6 個 W (≥ 6 週) 的開發資源**。**這是 S2 13 lessons 真正開始發揮作用的證據**。

---

## 十、Final stamp

```
S4 TurnOfMonth_Long
Status: KILLED
Date:   2026-06-21
Reason: Cyclical alpha decay (28y Sharpe 0.33, 8-year continuous losses 2010-2018)
Effort: 1 day W1 (no .pla written)
Lessons: L14-L18 contributed to memory
Replaced by: TBD (TBD after roadmap re-evaluation per S4 lessons)
```

---

**Death is the start of new wisdom. S4's 5 lessons will outlive its source code.**
