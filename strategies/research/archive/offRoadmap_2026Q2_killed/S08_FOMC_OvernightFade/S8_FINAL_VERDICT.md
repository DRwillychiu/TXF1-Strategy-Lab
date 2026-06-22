# S8 FOMC_OvernightFade — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（SOP v2 自動化 ~10 分鐘 KILL，但**KILL 原因最複雜**）
**狀態**：💀 **KILLED — ALPHA REVERSED**（alpha 倒轉，正式結案）
**用戶決策**：2026-06-21 ultracode session（5/6 KILL 後最後測試）
**最後版本**：N/A（pre-verification killed before W1）

---

## Stage -1: 策略內容說明（**2026-06-21 retroactively added per user instruction**）

> 用戶 2026-06-21 sharp 反饋：「我都不知道策略在幹嘛，你就否決」
> SOP v2 已加入 Stage -1 必走規則。本 verdict 補上 Stage -1。

### 策略內容（roadmap §9.3 S8）
```
類型: Event-driven cross-asset fade

前置:
  - 建立 FOMC + ECB + BoJ 公布日曆 CSV (每年 ~24 events)

進場規則:
  - FOMC 公布日 (台灣時間 02:00 ET = 02:00 TW)
  - 在 02:30 偵測 02:00-02:15 bar 變動
  - 若 |變動| > 0.5% → fade direction (反向進場)
    - bar 漲 → TXF1 夜盤 short
    - bar 跌 → TXF1 夜盤 long

出場規則:
  - 1×ATR target (profit)
  - 1.5×ATR stop (loss)
  - 05:00 強制平倉

樣本: 8 FOMC/yr × 28y = ~225 trades (邊際但充足)
```

### 優點
- Event-driven 邏輯清楚 (FOMC 大事件必有 over-reaction)
- Fade 方向 (修正 S5 follow microstructure 錯誤)
- 純 TXF1 夜盤 native, MC12 PASS
- Portfolio 缺口 (既有無 event-driven sleeve)
- 跟 S1 night session ρ 低 (S1 動量 long / S8 event fade)
- 1997-2014 alpha 真的存在 (Sharpe +0.32 to +3.35)

### 缺點
- 樣本邊際 (8/yr × 28y = 225)
- 跨資產 microstructure (TWII 開盤已吸收 FOMC)
- **2015 後 alpha 完全反向** (Sharpe -1.241, -1.962)
- FOMC 排程需手動維護 (operational layer)
- 夜盤流動性差，滑價可能 2-3× 日盤

### 為什麼不合適（**一段話**）
**S8 是今天 7 個 KILL 中最複雜也最危險的失效模式：alpha 在 1997-2014 期間真實存在且極強（Dot-com Sharpe +2.20 / China bull +1.23 / GFC +3.35 / Post-GFC +0.32），28-year aggregated Sharpe +0.686 / PF 1.368 看起來輕鬆通過 institutional gates；但 2015 後 alpha 完全 sign-flip 反向（2015-2019 Sharpe -1.241, 2020-2026 Sharpe -1.962），recent / long ratio = 負 2.99 倍，按 28y 數字部署將連虧 11 年並越虧越多。失效機制：HFT/algo 成熟後 fade trade 已被套利消化、TWII 機構化後反應 efficient、Fed 政策可預測性提高 → 散戶情緒化 over-reaction 消失。這個案例催生最重要的 L23：「Sign flip 比 magnitude decay 更危險」— 不能只看 28y aggregated number，必須 sub-period sign check，因為 aggregated 平均能掩蓋早期巨大 alpha 與近期完全反向的真相。**

---

## 一、為什麼 KILL — 一句話總結

> **S8 fade 邏輯在 1997-2014 是強 alpha（Sharpe 1.23-3.35），但 2015 之後**完全反向**
> （2015-2019 Sharpe -1.241 / 2020-2026 Sharpe -1.962）→ 28-year overall Sharpe +0.686 是
> over-aggregated 假象 → recent 6.4y Sharpe -2.051，按 28y 部署將連虧 11 年 → 必須 KILL。
> 這是「alpha reversal」而非「alpha decay」 — 比 S4/S5 更危險的失效模式。**

---

## 二、KILL 觸發證據（SOP v2 4 gates 結果）

### Gate A: 28-year Sharpe / PF — **PASS** ✓

| 維度 | 數字 | 標準 | 結果 |
|------|------|------|------|
| 28-year Sharpe | +0.686 | > 0.4 | ✓ PASS |
| 28-year PF | 1.368 | > 1.3 | ✓ PASS |
| 28-year Cum return | +170.63% | > 0 | ✓ |

**這是 trap**：28y aggregated 數字看起來 PASS，但隱藏 sub-period 反轉。

### Gate B: 6 macro regime — **PASS (4/6)** ✓

| Regime | Sharpe | 狀態 |
|--------|--------|------|
| 1997-2002 Dot-com | **+2.195** | ✅✅ |
| 2003-2007 China bull | +1.232 | ✅ |
| 2008-2009 GFC | **+3.350** | ✅✅✅ alpha 巔峰 |
| 2010-2014 Post-GFC | +0.318 | ✓ 邊際 |
| **2015-2019 Sideways** | **-1.241** | ❌ **alpha 翻轉** |
| **2020-2026 COVID+AI** | **-1.962** | ❌❌ **完全反向** |

**4/6 PASS Gate B**，但**最近 2 個 regime 嚴重負**。

### Gate C: L18 Recent-bias — **FAIL** ❌

- 28-year Sharpe: **+0.686**
- Recent 6.4y Sharpe: **-2.051**（!!）
- Ratio: **-2.99×**（**負值** = sign flip）

按原 L18 規則 ratio > 2.5× = AUTO-KILL。但這裡 ratio 是 **-2.99x**（負），更嚴重。

### Gate D: Direction symmetry — **FAIL** ❌

| 方向 | Sharpe |
|------|--------|
| Fade-long (SPX 跌 fade 做多) | 0.295（邊際）|
| Fade-short (SPX 漲 fade 做空) | 0.710（強）|
| Asymmetry | 0.415 |

Fade-long < 0.3 → 不 balanced。

### 結論

**Gate A + B PASS but Gate C + D FAIL** → **KILL**

關鍵：**Gate A 的「PASS」是假象**，因為它 average 了 2000s 的 +3 Sharpe 跟 2020s 的 -2 Sharpe。

---

## 三、Alpha Reversal 機制深度分析

### 為什麼 1997-2014 work？
- FOMC 公告造成 SPX 大波動 → TWII 開盤過度反應
- 散戶主導市場 → 開盤情緒化買賣
- HFT / quant 算法在 2010 前尚未成熟
- TWII fade 修正過度反應 = real alpha

### 為什麼 2015 後反向？
- **全球 HFT/algo 成熟**：fade trade 已被機構大量套利
- **TWII 機構化提升**：開盤反應更 efficient
- **Fed 政策可預測性提高**：FOMC 不再 surprise
- **趨勢延續取代均值回歸**：QE/AI 時代趨勢更強

→ **alpha mechanism 真實存在但 market structure 已變**

### 為什麼比 S4 更危險

| 比較 | S4 TurnOfMonth | **S8 FOMC Fade** |
|------|----------------|----------------|
| 28y Sharpe | 0.331 (低但正) | **+0.686**（看起來好）|
| Recent Sharpe | +0.876 (改善) | **-2.051**（反向）|
| 失效模式 | Cyclical decay (時好時壞) | **Sign flip** (完全反向) |
| 部署風險 | 連虧 8 年 | **連虧 11+ 年 + 越虧越多** |
| 判別難度 | 容易 (L18 ratio 2.64x) | **困難** (28y 數字 PASS Gate A)|

→ **Sign flip 是最危險的 alpha 失效模式**

---

## 四、新 Lesson **L23**

9. **L23: Sign Flip 比 Magnitude Decay 更危險 — L18 必須擴充偵測負 ratio**
   
   **原 L18 規則**：recent/long Sharpe ratio > 2.5× = AUTO-KILL
   
   **L23 擴充**：
   - ratio < 0 (sign flip) = **AUTO-KILL** (更嚴重)
   - ratio > 2.5× = AUTO-KILL (原規則)
   - 必須同時檢查 absolute Sharpe 是否 sign-consistent
   
   **判別流程**：
   ```
   IF 28y_Sharpe > 0 AND recent_Sharpe < 0:
       alpha 已反轉 → AUTO-KILL
   ELIF abs(recent / long) > 2.5:
       recent over-fit → AUTO-KILL  (原 L18)
   ELIF 0.4 < recent / long < 2.5:
       robust → PASS
   ```
   
   **教訓**：不能只看 28y aggregated number — 必須拆 sub-period 看 sign

**累積 lessons (S2-S8)**：
- S2: L1-L13 (13)
- S4: L14-L18 (5)
- S5: L19-L20 (2)
- S6: L21 (1)
- S7: L22 (1)
- **S8: L23 (1)** → 總計 **L1-L23 (23 lessons)**

---

## 五、KILL 速度全紀錄（6 個 KILL，今日 5 個）

| 策略 | KILL 速度 | KILL 觸發 |
|------|---------|----------|
| S2 InsideBarBreak | 5 版本 + 多週 | 5 次迭代後實證 (2026-06-20) |
| S4 TurnOfMonth | 1 天 | W1 同日 28y 驗證 |
| S5 SPX_Overnight | 0.5 天 | W0 pre-verify |
| S6 ForeignPositionFade | 0.1 天 | pre-W0 user gate (L21) |
| S7 PreSettlementHarvest | ~10 分鐘 | SOP v2 自動 4 gates |
| **S8 FOMC_OvernightFade** | **~10 分鐘** | **SOP v2 + L23 sign flip detection** |

---

## 六、Roadmap **100% 終局** — 6/6 候選全 KILLED

| 策略 | 狀態 | KILL 理由 |
|------|------|----------|
| ~~S2 InsideBarBreak~~ | 💀 ARCHIVED | 教科書 alpha 衰減 (L5)|
| ~~S4 TurnOfMonth~~ | 💀 KILLED | Cyclical decay (L16, L18)|
| ~~S5 SPX_Overnight~~ | 💀 KILLED | Cross-asset follow 邏輯錯 (L19, L20)|
| ~~S6 ForeignPositionFade~~ | 💀 KILLED | MC12 無法執行 (L21)|
| ~~S7 PreSettlementHarvest~~ | 💀 KILLED | Calendar 全死亡 (L22)|
| ~~**S8 FOMC_OvernightFade**~~ | 💀 **KILLED** | **Alpha sign flip (L23)** |

**100% kill rate 確認 portfolio 已 saturate**

---

## 七、Portfolio Final State — 7 sleeves 是最佳停止點

**Live + Live_Simulation (7 sleeves)**：
- L1 TrendLong 29% (frozen)
- L2 TrendShort 22% (frozen)
- L3 ConsolidationLong 10% (frozen)
- L4 ConsolidationShort 0%/3% (frozen, retired per v3 但可重啟)
- L5 BreakoutLong 16% (frozen)
- S1 NightMomentum 20% (frozen, live_sim)
- **S3 v2.0.4 RapidPullbackShort** (live_sim, 2026-06-20 deployed)

**6 KILLs 證明**：
- TWII/TXF1 真實可挖掘 alpha 已被既有 7 sleeves 覆蓋
- 教科書策略 (S2 / S4 / S7) 全死
- Cross-asset (S5 / S8) 全死或反轉
- Operational unfeasible (S6) 不可部署
- → **portfolio 結構性 saturate**

---

## 八、未來方向建議（給用戶）

### Option A: **接受 saturation，停 roadmap**
- 7 sleeves 已 cover TWII/TXF1 主要 alpha
- 把資源轉去 portfolio monitoring + S3 live_sim 觀察
- 寫 portfolio_saturation_acceptance.md 正式宣告

### Option B: **跳出 TXF1 範疇**
- 23 lessons 可應用到其他商品 (台指選擇權 / 元大 0050 / 個股期貨)
- 但 scope 跨越本專案 (TXF1-Strategy-Lab)

### Option C: **etc...等用戶決策**

---

## 九、KILL 規範

```
若你看到本檔（S8_FINAL_VERDICT.md）：
  ❌ 不要寫 S8 spec / .pla
  ❌ 不要嘗試 fade FOMC 變種
  ❌ 不要追任何已 sign-flipped 的 alpha
  ✅ 可以讀本檔 + L23
  ✅ 學習：28y aggregated 數字可能掩蓋 sub-period reversal
```

---

## 十、相關文件交叉參考

- **SOP v2** (本次套用)：[../../../docs/STRATEGY_RD_SOP_v2.md](../../../docs/STRATEGY_RD_SOP_v2.md)
- **預檢腳本**：[../../../scripts/analyze_s8_fomc_overnight_fade_preverify.py](../../../scripts/analyze_s8_fomc_overnight_fade_preverify.py)
- **S5 SPX_Overnight (cross-asset 前置)**：[../S05_SPX_Overnight/S5_FINAL_VERDICT.md](../S05_SPX_Overnight/S5_FINAL_VERDICT.md)
- **L23 更新建議**：應該擴充 [`feedback_strategy_kill_must_document`](../) memory

---

## 十一、用戶聲明

> 「A」  
> — 2026-06-21 ultracode session（接續 S7 KILL 後）

第 6 個 KILL，**roadmap 100% closed**。今天從早到晚連續 5 個 KILL (S4/S5/S6/S7/S8)。

---

## 十二、Final stamp

```
S8 FOMC_OvernightFade
Status: KILLED
Date:   2026-06-21 (6th KILL today, roadmap 100% closed)
Reason: 
  1. Alpha sign-flipped in 2015 (2015-2026 Sharpe -1.241/-1.962)
  2. 28y +0.686 is over-aggregated illusion
  3. Deploying based on 28y would mean 11+ years continuous loss
  4. Most dangerous failure mode discovered: sign reversal
Effort: ~10 minutes (SOP v2 + new L23 sign-flip detection)
Lessons: L23 contributed (extends L18 with sign-flip auto-kill)
KILL speed: 1000x+ faster than S2 (SOP automation final state)
Replaced by: PORTFOLIO SATURATION ACCEPTANCE
```

---

**Six strikes. Roadmap 100% closed. Portfolio is officially saturated at 7 sleeves.**

**The day's true achievement isn't 5 new strategies — it's 6 KILLs + 23 permanent lessons + SOP v2.**
