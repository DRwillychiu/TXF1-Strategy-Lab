# S5 SPX_Overnight_DayOpen — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（**W0 pre-verification 即 KILL，W1 spec 未寫**）
**狀態**：💀 **KILLED — NOT FEASIBLE**（不可行，正式結案）
**用戶決策**：2026-06-21 ultracode session（28-year pre-verify 後）
**最後版本**：N/A（pre-verification killed before W1）
**KILL 速度**：**0.5 天**（S4 1 day → S5 0.5 day → lessons compound）

---

## 一、為什麼 KILL — 一句話總結

> **「SPX overnight return > |0.7%| → TWII day-session in-line」這個 cross-asset spillover 邏輯
> 在 1997-2026 28 年實證上是大虧損策略：整體 Sharpe -0.445 / PF 0.884 / Cum -158%。
> Long 方向 (SPX 漲跟 TWII 多) Sharpe -0.885 = 追高殺低；
> 6 個 macro regime 中 4 個嚴重負 Sharpe；
> Recent / long-term ratio = ∞（28y 為負）= L18 auto-KILL。**

---

## 二、KILL 觸發證據

### 證據 #1: Long 方向是大虧損方向（**致命邏輯錯誤**）

| 方向 | N | WR% | PF | Sharpe | 28y Cum% |
|------|---|------|-----|--------|---------|
| **LONGS** (SPX 漲→TWII 多) | 1565 | 47.3% | **0.714** | **-0.885** | **-216.89%** |
| SHORTS (SPX 跌→TWII 空) | 1364 | 51.6% | 1.097 | +0.230 | +58.81% |
| ALL | 2929 | 49.3% | 0.884 | -0.445 | -158.07% |

**根因**：
- TWII 開盤 09:00 TW = 21:00 NY 前一晚
- 此時 NY market 已交易 5 小時（NY 開市 09:30 ET = 21:30 TW）
- TWII open price 已**完全吸收** SPX overnight 訊息
- **再 follow SPX move = 追高殺低**
- 應該 fade 而非 follow，但 fade 整體 Sharpe 也只 +0.23 不夠強

### 證據 #2: 28-year 整體數字慘烈

| 維度 | 數字 | 標準 | 結果 |
|------|------|------|------|
| 28-year Sharpe | -0.445 | > 0.4 | ❌ FAIL |
| 28-year PF | 0.884 | > 1.3 | ❌ FAIL |
| 28-year Cum return | **-158.07%** | > 0 | ❌ 完全虧損 |
| Max DD | (深度未計算，整體就虧 158%) | < 30% | ❌ FAIL |

### 證據 #3: 6 個 regime 表現極端化

| Regime | Sharpe | PF | Cum% |
|--------|--------|------|------|
| 1997-2002 Dot-com | **-2.103** | 0.61 | -225.91% |
| 2003-2007 China bull | **-1.892** | 0.58 | -85.71% |
| 2008-2009 GFC | **-2.520** | 0.57 | -96.78% |
| 2010-2014 Post-GFC | **-0.690** | 0.82 | -25.25% |
| 2015-2019 Sideways | +1.942 | 1.95 | +64.70% |
| 2020-2026 COVID+AI | +3.016 | 2.40 | +210.87% |

**只 2/6 regime 正**，且 1997-2014 連續 **18 年虧損**。

### 證據 #4: L18 Recent-bias 直接 AUTO-KILL

- 28-year Sharpe: **-0.445**（負！）
- Recent 6.4y Sharpe: **+3.154**
- Ratio: **∞**（因 28y 為負，數學上 ratio 無意義）

→ L18 規定 ratio > 2.5× = AUTO-KILL，這裡是 **infinity**

### 證據 #5: Threshold sensitivity 沒有 sweet spot

| Threshold |SPX| | N | Sharpe | Cum% |
|---------|------|---|--------|------|
| 0.3% | 4879 | -0.410 | -174.46% |
| 0.5% | 3797 | -0.371 | -145.15% |
| **0.7%** (roadmap) | 2929 | -0.445 | -158.07% |
| 1.0% | 1996 | -0.463 | -143.20% |
| 1.5% | 1045 | -0.686 | -170.63% |
| 2.0% | 556 | -0.553 | -108.15% |

**所有 threshold 全部負 Sharpe** — 不是 parameter tuning 能救的。

---

## 三、我（Claude）的失誤檢討

### 失誤 #1: 沒思考 microstructure 直接信 roadmap
- Roadmap §9.2 寫「TWII day-session open follow SPX overnight」
- 我沒先想：「TWII open 已經吸收 SPX 嗎？」
- 一個簡單 microstructure question 就能避免這次 KILL
- **教訓**：寫 spec 之前必須先 microstructure check

### 失誤 #2: 沒同時測 follow/fade 雙方向
- S5 roadmap 假設 "in-line"（follow）
- 但 cross-asset 可能是 mean-reversion 而非 momentum
- 如果一開始就拆 LONG/SHORT 看，會立刻發現 LONG -0.885
- **教訓**：任何 signal-following 策略必須測雙方向

### 失誤 #3: 對 cross-asset 過度樂觀
- S4 KILL 我以為是「教科書 calendar」問題（L16）
- 預期 cross-asset 不在 L16 範圍
- 但 cross-asset 也有 microstructure decay：HFT 套利 + 全球同步交易
- **教訓**：cross-asset 不等於免疫 alpha decay

---

## 四、學自 S5 的 **2 個新 lessons (L19-L20)**

5. **L19: Cross-asset spillover 必做 microstructure 預檢**
   - 不是看時區差就能 follow signal
   - TWII open 已吸收 NY 5h trading → 不能再 follow SPX overnight
   - 必須計算「TWII open 已 priced in 多少 SPX move」
   - 跨市場策略 default 視為「需要 fade 而非 follow」

6. **L20: Signal-following 策略必測雙方向**
   - LONG/SHORT 兩邊都要看 Sharpe + PF
   - 若一邊強一邊弱 → alpha 不對稱 → 設計需 redesign
   - 若兩邊都弱 → KILL
   - 若兩邊都強 → robust

**累積 lessons 演進**：
- S2: 13 lessons (L1-L13)
- S4: 5 new lessons (L14-L18)
- **S5: 2 new lessons (L19-L20)**
- 總共 **20 個 lessons** 永久保留

---

## 五、KILL 速度演進（lessons compound 證據）

| 策略 | KILL 速度 | 投入 | 累積 lessons 應用 |
|------|---------|------|------------------|
| S2 InsideBarBreak | 5 版本 + 多週 | 高 | L1-L13 生成 |
| S4 TurnOfMonth | 1 天 (W1 同日 KILL) | 中 | L1-L13 應用 → L14-L18 生成 |
| **S5 SPX_Overnight** | **0.5 天 (W0 pre-verify 即 KILL)** | **極低** | **L1-L18 應用 → L19-L20 生成** |

**S5 比 S2 快 10×+ KILL** → 18 個 lessons 真正發揮加速作用

---

## 六、對 roadmap 其他策略的 ripple effect 警告

S5 KILL 觸發了一個重要 question：**roadmap 6 個候選策略還有幾個 viable**？

| 策略 | 類型 | L14-L20 風險評估 |
|------|------|------------------|
| ~~S2 InsideBarBreak~~ | 母子線突破 | 💀 KILLED (L5) |
| ~~S4 TurnOfMonth~~ | Calendar | 💀 KILLED (L16, L18) |
| ~~**S5 SPX_Overnight**~~ | **Cross-asset spillover** | 💀 **KILLED (L19, L20)** |
| S6 ForeignPositionFade | 三大法人 z-score | 🟡 中等（z-score 機構化套利可能消化）|
| S7 PreSettlementHarvest | Calendar (3rd Wed) | 🔴 高風險（L16 calendar decay）|
| S8 FOMC_OvernightFade | Event-driven (FOMC) | 🟡 中等（fade 邏輯比 follow 更 robust）|
| S9-S15 | TBD | 待 evaluate |

**3/6 KILL rate 表示 roadmap design 需要 critical re-evaluation**。

---

## 七、KILL 規範

```
若你看到本檔（S5_FINAL_VERDICT.md）：
  ❌ 不要寫 S5 spec / .pla
  ❌ 不要再嘗試「SPX overnight follow」邏輯
  ❌ 不要修改 S5 任何代碼（沒有，這條 trivial）
  ✅ 可以讀本檔 + 2 個新 lessons (L19-L20)
  ✅ 可以參考 fade 方向的弱正 Sharpe 作未來研究線索
  
重啟條件（極嚴）：
  以下 3 個同時滿足才可考慮：
  1. 學術新研究證明 TWII 對 SPX overnight 是 fade pattern
  2. ≥10 年新 OOS data 顯示 fade 方向 Sharpe > 0.5
  3. 用戶明確要求重啟
```

---

## 八、資源轉向

S5 KILL 後 portfolio 戰略位置改變：

**剩餘 roadmap 6 個候選**（S6-S11）需要**全面重新 evaluation**，不能再按 roadmap 順序盲做。

建議下一步：
1. 用 L14-L20（總 20 個 lessons）對 S6-S11 做 **pre-verify rank**
2. 找最高 prior 通過機率的策略優先做
3. 或者：認知 portfolio 目前已 saturate（6 frozen + S3 v2.0.4），停加新策略

---

## 九、相關文件交叉參考

- **預檢分析腳本**：[../../../scripts/analyze_s5_spx_overnight_preverify.py](../../../scripts/analyze_s5_spx_overnight_preverify.py)
- **前置策略 KILL**：[../S04_TurnOfMonth/S4_FINAL_VERDICT.md](../S04_TurnOfMonth/S4_FINAL_VERDICT.md)
- **S2 結案**：[../S02_InsideBarBreak/S2_FINAL_VERDICT.md](../S02_InsideBarBreak/S2_FINAL_VERDICT.md)
- **Roadmap (需 update)**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **Memory feedback (KILL 必文件化)**：`feedback_strategy_kill_must_document.md`

---

## 十、用戶聲明

> 「A，請記得完整的流程。」  
> — 2026-06-21 ultracode session（接續 S4 KILL 後）

用戶的「完整流程」要求被執行得徹底：W0 pre-verification stage 直接 KILL，**保留了 Q2 整季 (W1-W13) 的開發資源**。這是 lessons compound 的明確證據。

---

## 十一、Final stamp

```
S5 SPX_Overnight_DayOpen
Status: KILLED
Date:   2026-06-21 (same day as S4)
Reason: Cross-asset spillover follow logic is structurally wrong
        (28y Sharpe -0.445, LONG side -0.885, microstructure backfire)
Effort: 0.5 day (no .pla, no W1 spec, just preverify)
Lessons: L19-L20 contributed to memory (total 20 累積)
KILL speed: 10x faster than S2 → lessons compound proven
Replaced by: TBD (roadmap re-evaluation required)
```

---

**Three strikes (S2, S4, S5) — time to question if roadmap itself needs redesign.**
