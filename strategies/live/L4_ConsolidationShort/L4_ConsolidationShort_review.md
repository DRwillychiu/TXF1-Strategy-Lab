# L4 盤整空（S_Spring 假突破反轉）出場機制深度審查

> 📌 **終態（2026-06-23 codified）**：v14.2B Path A 為 PRODUCTION（Night_Block_On=true, BE=0, SP=0），v14.4 = v14.2B + ImmediateStop + HolidayFlat_v3 + Settlement_Flat。
> v14.5 (Strong Long Block + Fast BreakExit) **完全回滾**（A/B 4 配置實證無效）。
> L4 仍處 portfolio 風險最高 sleeve；用戶 ruling 2026-06-20 為「暫不退役，等 short 替代 sleeve 成熟」。

> 審查日期：2026-06-23（基於 2026-06-18 v14.4 deep analysis + 2026-06-13 v14.2 A-G variants 完整實證）
> 依據：`docs/methodology/entry_exit_sop.md` 九層架構 + 假日平倉鐵律 + Rule #11/#12/#13/#14
> 數據來源：MC12 真實 60M 回測（81 筆，2020-02-21 ~ 2026-06-06）
> 對應 .pla：[L4_ConsolidationShort.pla](L4_ConsolidationShort.pla) (v14.4)
> 相關 audit：[docs/archive/offRoadmap_2026Q2/L4_v144_deep_analysis_20260618.md](../../docs/archive/offRoadmap_2026Q2/L4_v144_deep_analysis_20260618.md)

---

## 一、結論摘要

| # | 嚴重度 | 發現 | 行動 |
|---|:---:|------|------|
| 1 | 🔴 體質 | **Sharpe 0.058 — 全 portfolio 最低**。年化僅 +3.71%（B&H 27%），月報酬 std 41K = 高波動低 alpha | 用戶 2026-06-20 ruling: 不退役，等 short 替代 sleeve |
| 2 | 🔴 結構 | **2022 熊市反賠 -51K**（31 筆）= L4 本應「黃金年」但慘敗。**真相**：熊市中假突破多數**繼續跌**（真趨勢），CS_SL trail 鎖利成功率 < 平時 | 結構性弱點，已 disclose（無法 fix）|
| 3 | 🔴 結構 | **CS_BreakExit 20 筆 / 0% WR / -377,800** = 假突破論被打臉的真實虧損（淨利的 1.58x！）| v14.5 A/B 試圖 fix 但**完全失敗**，回滾 v14.4 |
| 4 | 🟡 集中 | **2025 一年 +294K（80% WR）佔淨利 123%** = 高度年度集中 | 監控 2026 是否回歸均值 |
| 5 | 🟡 樣本 | **13 筆/年偏少**，6 年 81 筆 prefer ≥ 100 機構樣本門檻 | 接受小樣本，靠 EW portfolio 攤平 |
| 6 | 🟢 風控 | MDD -12.87% 極佳，最大單筆 -111K 可控 | 不行動 |
| 7 | 🟢 規範 | Settlement_Flat (Rule #11) ✅ + SetStopLoss (Rule #12) ✅ + HolidayFlat_v3 ✅ + IOG=false ✅ | 規範對齊 5/5 PASS |

---

## 二、出場標籤統計（81 筆全解析）

| 出場標籤 | 筆數 | 淨利 | WR | 平均 | 說明 |
|---------|----:|-----:|----:|-----:|------|
| **CS_SL** | 26 | **+500,000** ⭐ | **65%** | +19,231 | **SL trail 鎖利**（不是傳統停損！）|
| **CS_SP** | 29 | +178,800 | **100%** | +6,166 | StopProfit trail 退場（v14.2B 加入後 active）|
| CS_TimeExit | 4 | -22,400 | 25% | -5,600 | 時間出場 |
| CS_Holiday | 1 | -22,600 | 0% | -22,600 | 假日鐵律觸發（少見）|
| **CS_BreakExit** | 20 | **-377,800** ❌ | **0%** | -18,890 | 「真突破成功」= 策略 thesis 失敗 |
| Stop Loss (engine) | 1 | -17,400 | 0% | -17,400 | MC engine SetStopLoss 觸發 |

### 2.1 關鍵 insight: CS_SL 賺錢的真相

> **CS_SL 不是「停損」，是「Trail 跟上來的鎖利出場」**

- 進場 SL = `Locked_Top + ATR × ATR_Stop_Mult`（反方向）
- 持倉啟動 Trail 後 SL 跟著價格下移
- 65% 觸發時：價格已大幅下跌，Trail 帶 SL 到賺錢區，反彈到 SL = **鎖利**

### 2.2 真實 alpha vs 真實 risk

```
賺錢來源：CS_SL Trail + CS_SP   = +679K (55 筆)
虧錢來源：CS_BreakExit (真突破)  = -378K (20 筆)
─────────────────────────────────────
淨利                              = +239K
```

**結構性結論**：L4 是「**多數時候假突破論成立，少數時候大虧**」的 asymmetric 策略。對沖價值 > 絕對報酬。

---

## 三、年度分布（極不穩定）

| 年份 | 筆數 | 淨利 | WR | 評估 |
|------|----:|-----:|----:|------|
| 2020 | 8 | +27,200 | 62.5% | 🟢 |
| 2021 | 7 | -17,600 | 57.1% | 🔴 |
| **2022** | **31** | **-51,200** | 61.3% | 🔴🔴 **熊市反賠** |
| 2023 | 17 | +26,800 | 47.1% | 🟢 |
| 2024 | 8 | -40,600 | 37.5% | 🔴 |
| **2025** | **10** | **+294,000** | **80%** | 🟢🟢 **單年救命** |
| 2026 H1 | — | — | — | (回測截止 2026-06-06) |

**6 年累積 +239K，但 2025 一年就佔 123%**（不含 2025 為 -55K 累積虧損）。

### 3.1 2022 熊市反賠的真實原因（重要結構發現）

- 2022 TWII 從 18,000 跌到 13,000 = -28%（典型 bear regime）
- L4 應該是「做空黃金年」
- 但 31 筆只賠 -51K
- **真相**：熊市中「向上假突破」次數**增加**但**多數繼續跌**（真趨勢）
- → CS_BreakExit trigger 比平時頻繁 → L4 thesis 在 strong trend 時失效

→ **L4 適合 range/choppy regime，不適合 strong trend (上或下都不行)**

---

## 四、九層檢核

| 層 | 現狀 | 判定 |
|---|------|------|
| 1 初始停損 | `Locked_Top + ATR × 2.0`，進場時隨單錨定 + Frozen | ✅ |
| 2 獲利回檔保護 | v14.2 A-G 全試 → **C (BE) + D (SP) 全 fail** → 移除 (L3 詛咒重現) | 🔴 已試過，無解 |
| 3 追蹤停損 | Trail 啟動條件: `Lowest_Low ≤ Locked_Btm` → Stop = `Lowest_Low + Trail_ATR × ATR` | ✅ 核心 alpha |
| 4 目標停利 | 無 fixed TP，靠 trailing 自然鎖利（CS_SL 65% WR 證明有效）| ✅ |
| 5 時間停損 | Time_Limit_Bars (Trap zone 過期) + 整體 MaxBars | ✅ |
| 6 結構失效出場 | **CS_BreakExit** (Box 真向上突破) — 20 筆 0% WR -378K | 🔴 **alpha 結構成本** |
| 7 夜盤保護 | **v14.2 Path A: Night_Block 02:00-04:59 全禁進場** | ✅ +120,800 net contribution |
| 8 行事曆風控 | HolidayFlat_v3 (63 entries) + Registry_Valid_Until | ✅ |
| 9 緊急開關 | Manual_Kill_Switch (input) + Settlement_Flat | ✅ |

---

## 五、v14.2 A-G 變體完整 audit（**已 sealed，不可重做**）

7 個 variants MC9 4 配置 A/B test 2026-06-13:

| Variant | Night | BE | SP | Net | PF | MDD | Top-10 retention | Status |
|---------|:-----:|:--:|:--:|----:|----:|----:|----------------:|--------|
| A baseline (v14.1) | off | 0 | 0 | 581,200 | 1.62 | -328K | — | baseline |
| **B Path A only** | **on** | 0 | 0 | **687,200** | **1.83** | **-239K** | **100%** | ✅ **PRODUCTION** |
| C Path B BE | off | 60 | 0 | -345K | < 1 | worse | 60% (4 winners killed) | ❌ L3 詛咒重現 |
| D Path B SP | off | 0 | 80/50 | -212K | < 1 | worse | — | ❌ 截斷大贏家 |
| E A+C | on | 60 | 0 | < A | — | — | — | ❌ |
| F A+D | on | 0 | 80/50 | < A | — | — | — | ❌ |
| G A+SP-conv | on | 0 | 100/50 | < A | — | — | — | ❌ |

### 5.1 為什麼 BE/SP 全失敗（L3 詛咒重現）

| L3 v13.2D 失敗 | L4 v14.2 C/D 失敗 |
|---------------|------------------|
| BE +50 pts < 箱體 oscillation 振幅 | BE/SP 任何 threshold 切第一個 retrace |
| 100 CL_BE 0% WR | C: 25 CS_BE 0% WR / 4 of Top-10 killed |
| 96 amputated target hits | L4 大贏家是 multi-stage（+60→+30→+200→trail 接 +180）|

### 5.2 永久 lesson（codified）

> **BE/SP 在「mean reversion/range」與「multi-stage trend follow」策略上都會 self-defeat。**
> Strategy-level 持倉中段保護模組 = 結構性截斷大贏家。
> 真正 risk 應在 portfolio level 解決（per [Lesson L24](../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md))。

---

## 六、v14.5 完全回滾（2026-06-18 audit）

v14.5 試圖 fix CS_BreakExit -378K leak，加 2 個 filter：
- A. Strong Long Block (Daily MA gap% > 1.0 不做空)
- B. Fast BreakExit (15M Close > Locked_Top + 0.5 ATR)

### 4 配置 MC12 同日測試結果

| Config | Trades | Net | PF |
|--------|-------:|----:|----:|
| 1: v14.4 replica | 81 | +238,600 | 1.414 |
| 2: A only | 81 | +238,600 | 1.414 |
| 3: B only | 85 | +220,600 | 1.372 |
| 4: v14.5 full | 85 | +220,600 | 1.372 |

→ **A filter 完全沒擋到任何 trade**（Daily MA gap 條件設計失敗）
→ **B filter 提早出場 +4 trades 但 Net 反而 -18K**（截斷未來大贏家）
→ **v14.5 完全 revert 回 v14.4**（2026-06-18 commit）

**Lesson**：CS_BreakExit -378K 是 L4 thesis 的**結構性成本**，不是 patchable bug。

---

## 七、Portfolio 角色（per L4_portfolio_role_20260618.md）

### 7.1 對沖價值（非絕對報酬）

L4 vs L1-L5 對照：
- L1 (TrendLong): 多頭 trending → 賺
- L2 (TrendShort): 空頭 trending → 賺
- L3 (ConsolidationLong): 多頭 range → 賺
- **L4 (ConsolidationShort): 空頭 range / chop → 賺**（filling gap）
- L5 (BreakoutLong): 多頭 breakout → 賺

→ **L4 是唯一專注 short-side range 的 sleeve，covers regime 空缺**

### 7.2 Frozen 配置（2026-06-20 user ruling）

- 配置：3% portfolio sleeve（最小，因 Sharpe 最低）
- 不退役理由：唯一 short-side range sleeve，移除 = portfolio regime 空缺
- 退役條件：**S3_RPS + S3_S 完整覆蓋 short side range 後**才考慮 L4 退休

### 7.3 跟 S3_RPS / S3_S 的角色區隔

| Sleeve | Alpha source | Regime |
|--------|-------------|--------|
| L4 | 盤整箱體假突破反轉 | short-side range |
| S3_RPS | 多頭過熱拉回 | bull pullback |
| S3_S (CURRENT 開發) | Vol squeeze 向下 breakout | short-side vol expansion |

→ 3 隻 short sleeve 互補，無重疊

---

## 八、規範對齊（Rule #11/#12/#13/#14）

| Rule | 內容 | L4 v14.4 狀態 |
|------|------|--------------|
| #11 | Settlement_Flat 7 元素 | ✅ Priority 0 CS_Settlement label |
| #12 | P3b SetStopLoss | ✅ MP >= 0 guard (Short 變體), single call |
| #13 | 10-dim eval | ⚠️ Sharpe 0.058 fail，但 frozen sleeve 例外處理 |
| #14 | OFFICIAL_ROADMAP 對齊 | ✅ L4 是 live frozen，不在新策略 roadmap |

### 8.1 Rule #13 為何允許 fail

L4 frozen 2026-06-20 之前已 deploy 在 live/，Rule #13 適用「**新策略 / 既有優化**」。L4 進入 frozen 狀態（不再優化），不適用新策略 gate。退役條件由 portfolio v3 文件管理，不由 Rule #13 自動觸發。

---

## 九、後續計畫

### 9.1 不行動（current state）

L4 v14.4 = production，不需任何修改。

### 9.2 觸發退役評估的條件

| Trigger | 動作 |
|---------|------|
| 2026 全年 PF < 1.0 | 評估退役 |
| S3_S promote 後 portfolio 重平衡 | 評估 L4 → 0% allocation |
| 連續 2 年 Sharpe < 0 | 退役 with FINAL_VERDICT.md |
| 單年 MDD > -20% | 結構失效 review |

### 9.3 不該做

- ❌ 加 BE/SP 任何形式（L3 詛咒 + v14.2 C/D fail 雙重證據）
- ❌ 加 event filter（Lesson L24）
- ❌ Cherry-pick CS_BreakExit 的 macro 特徵 fix（data mining）
- ❌ 改 Long-only direction（L4 是 Short-only by design）

---

## 十、結論

L4 v14.4 = **portfolio 風險最高 sleeve, 但 short-side range 唯一覆蓋者**。

| 維度 | 結論 |
|------|------|
| 絕對 alpha | 弱（Sharpe 0.058）|
| Regime fit | 限 short-side range（強 trend 時失效）|
| Portfolio 對沖價值 | 高（無替代）|
| 規範對齊 | 5/5 PASS |
| v14.2 / v14.5 audit | A-G 7 variant + 4 config v14.5 = **沒人能比 v14.2B 強** |
| 結構性成本 | CS_BreakExit -378K = 不可 patch 的 thesis cost |

**Status**: 🟡 Frozen，等 S3_S + 更多 short sleeves 成熟後評估退役。**禁止任何 strategy-level patch**。
