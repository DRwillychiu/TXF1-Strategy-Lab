# S9 NightFadeShort — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（SOP v2 daily proxy ~10 分鐘 KILL）
**狀態**：💀 **KILLED — RECENT-BIAS ALPHA**（最近 11 年才出現的 alpha = 高過擬合風險）
**用戶決策**：2026-06-21 ultracode session（**第 7 個 KILL，roadmap 100% closed**）
**最後版本**：N/A（W0 proxy preverify killed before W1）

---

## 一、為什麼 KILL — 一句話總結

> **S9 「US 弱夜 + TXF1 跟跌 short」策略的 alpha 是 2015+ 新興現象（recent 6.4y Sharpe +3.16），
> 完全沒有 1997-2014 長期歷史證據（GFC -1.49, Dot-com -0.77）：L18 recent/long ratio 
> 高達 6.56× → 嚴重 recent-bias，部署有 alpha 反向風險（類 S8 sign flip）。
> 28y PF 1.20 + 6/3 regime fail 也驗證 alpha 不夠 robust。**

---

## 二、KILL 觸發證據（SOP v2 4 gates）

### Gate A: 28-year — **mixed**

| 維度 | 數字 | 標準 | 結果 |
|------|------|------|------|
| 28y Sharpe | +0.481 | > 0.4 | ✓ PASS |
| 28y PF | **1.202** | > 1.3 | ❌ FAIL |
| 28y Cum | +126.16% | > 0 | ✓ |

PF 不到 1.3 = alpha 不夠強。

### Gate B: 6 regime — **FAIL (3/6)**

| Regime | Sharpe | 狀態 |
|--------|--------|------|
| 1997-2002 Dot-com | **-0.772** | ❌ |
| 2003-2007 China bull | -0.044 | ❌ |
| 2008-2009 GFC | **-1.491** | ❌ |
| 2010-2014 Post-GFC | +0.697 | ✓ |
| 2015-2019 Sideways | +1.854 | ✓ |
| **2020-2026 COVID+AI** | **+3.019** | ✓ |

→ **1997-2009 連續 3 regime 大虧** (12 年負 alpha)
→ Alpha 是 **2010 後新興**的 phenomenon

### Gate C: L18 + L23 — **FAIL** ❌

- 28-year Sharpe: +0.481
- Recent 6.4y Sharpe: **+3.157**
- Ratio: **6.56×**（超過 2.5× threshold 2.6 倍）

→ AUTO-KILL: ratio > 2.5×

### Gate D: Anti-correlation with S1 — **deferred**

無法在 daily proxy 下精確計算，需 MC12 actual。但因 Gate A/B/C 已 FAIL，moot。

---

## 三、為什麼這是危險的 alpha

**S9 vs S8 對比**（兩個都是 recent bias 但方向相反）：

| 維度 | **S8 FOMC Fade** | **S9 NightFadeShort** |
|------|------------------|----------------------|
| 28y Sharpe | +0.686 (高) | +0.481 (邊際) |
| 1997-2014 表現 | Sharpe 0.32 to 3.35 (**強**) | Sharpe -0.77 to -1.49 (**全負**) |
| 2015-2026 表現 | Sharpe -1.24 to -1.96 (**完全反向**) | Sharpe +1.85 to +3.02 (**alpha 出現**) |
| 失效模式 | Sign flip (L23) | Recent bias (L18) |
| 部署風險 | 立刻虧 | 可能短期賺，但本質不穩 |

**S9 是「相反的 trap」**：
- S8 trap = 28y 看起來好但 recent 反向
- S9 trap = 28y 邊際但 recent 太強 → 「**未來會回歸 mean**」風險

**機制懷疑**：
- S9 在 2010 後出現 alpha 跟全球 quant easing + 中美貿易戰相關
- 這個 regime 可能是 anomaly 而非新常態
- Fed 政策轉向 / 兩岸關係變化 → S9 alpha 可能立刻死

---

## 四、KILL 速度 (S9 完成 roadmap 7/7)

| 策略 | KILL 速度 | KILL 觸發 |
|------|---------|----------|
| S2 InsideBarBreak | 5 版本 + 多週 | 多次迭代 |
| S4 TurnOfMonth | 1 天 | W1 同日 |
| S5 SPX_Overnight | 0.5 天 | W0 pre-verify |
| S6 ForeignPositionFade | 0.1 天 | pre-W0 user gate |
| S7 PreSettlementHarvest | 10 分 | SOP v2 |
| S8 FOMC_OvernightFade | 10 分 | SOP v2 + L23 |
| **S9 NightFadeShort** | **10 分** | **SOP v2 + L18 + proxy** |

**SOP v2 平均 10 分鐘 KILL 速度**（vs S2 多週）

---

## 五、Roadmap 100% CLOSED — **7/7 KILLED 終極確認**

| # | 策略 | 狀態 | KILL 主因 |
|---|------|------|----------|
| 1 | ~~S2 InsideBarBreak~~ | 💀 | L5 textbook decay |
| 2 | ~~S4 TurnOfMonth~~ | 💀 | L16, L18 cyclical decay |
| 3 | ~~S5 SPX_Overnight~~ | 💀 | L19, L20 cross-asset follow 錯 |
| 4 | ~~S6 ForeignPositionFade~~ | 💀 | L21 MC12 not executable |
| 5 | ~~S7 PreSettlementHarvest~~ | 💀 | L22 calendar dead |
| 6 | ~~S8 FOMC_OvernightFade~~ | 💀 | L23 sign flip |
| 7 | ~~**S9 NightFadeShort**~~ | 💀 | **L18 recent bias** |

**100% kill rate = 7/7 = 終極證明 portfolio saturation**

---

## 六、累積 lessons 維持 L1-L23（S9 無新 lesson）

S9 KILL 是 **L18 + L20 + L23** 既有 lessons 的綜合應用，不需新 lesson。  
這證明 **23 lessons 已足夠 catch 大多數失效模式**。

---

## 七、KILL 規範

```
若你看到本檔（S9_FINAL_VERDICT.md）：
  ❌ 不要寫 S9 spec / .pla
  ❌ 不要嘗試「夜盤 fade short」變種
  ❌ 不要再嘗試 mirror S1 strategy
  ✅ 可以讀本檔 + L18 + L20 + L23
  
重啟條件（極嚴）：
  1. 1997-2014 期間 S9-like 邏輯重新 backtest 顯示正 alpha
  2. 全球宏觀環境恢復類 1997-2014 (Fed 加息 + 中國淡出)
  3. 用戶明確要求
```

---

## 八、相關文件

- **SOP v2**：[../../../docs/STRATEGY_RD_SOP_v2.md](../../../docs/STRATEGY_RD_SOP_v2.md)
- **預檢腳本**：[../../../scripts/analyze_s9_nightfadeshort_preverify.py](../../../scripts/analyze_s9_nightfadeshort_preverify.py)
- **S1 NightMomentum (本應 mirror)**：strategies/live_simulation/S1_NightMomentum.pla
- **S8 (相反的 trap)**：[../S08_FOMC_OvernightFade/S8_FINAL_VERDICT.md](../S08_FOMC_OvernightFade/S8_FINAL_VERDICT.md)
- **Saturation acceptance (本 commit)**：[../../../docs/portfolio_saturation_acceptance_20260621.md](../../../docs/portfolio_saturation_acceptance_20260621.md)

---

## 九、用戶聲明

> 「A，然後繼續推進 S9」  
> — 2026-06-21 ultracode session

第 7 個 KILL，**roadmap 7/7 終極 closure**。

---

## 十、Final stamp

```
S9 NightFadeShort
Status: KILLED
Date:   2026-06-21 (7th KILL, roadmap 100% closed)
Reason: 
  1. Alpha is 2015+ recent phenomenon, no 1997-2014 evidence
  2. 1997-2009 (12 years) consistently negative Sharpe
  3. Recent/long Sharpe ratio 6.56x = severe over-fit risk
  4. PF 1.20 below 1.3 threshold
Effort: ~10 minutes (SOP v2 daily proxy)
Lessons: NONE NEW — confirms L18 + L20 + L23 sufficient
KILL speed: 1000x+ faster than S2
Roadmap status: 100% CLOSED (7/7 KILLED)
```

---

**Seven strikes. Roadmap fully closed. Portfolio definitively saturated.**
