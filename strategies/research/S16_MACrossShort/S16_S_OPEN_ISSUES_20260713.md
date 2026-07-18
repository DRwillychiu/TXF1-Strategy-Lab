# S16_S v1.0-PROD — Potential Issues & Risk Register

**Date**: 2026-07-13
**Status**: v1.0-PROD deployed in live_simulation
**Context**: User review session — comprehensive issue list for boss discussion
**Strategy Text Reference**: `S16_S_STRATEGY_TEXT_20260713.md`

---

## A. Parameter Issues

### A1. Slow line parameter exceeds pure 5M scope
- ZLEMA_Slow=70 = 350 min = 5.8 hours lookback, approaching 10M territory
- Original MA deep research recommended Slow <= 50 for pure 5M meaning
- **Impact**: Strategy may be "misplaced" on 5M; 10M may be more appropriate
- **Resolution**: Launch S16_S_10M experiment as comparison. Do not modify current 5M version.

### A2. Slow line parameter is a narrow peak
- ZLEMA_Slow=80: performance drops -33.5%
- **Impact**: Parameter stability weaker than plateau-type strategies. Market structure changes could invalidate parameter without warning.
- **Resolution**: Documented as known risk. Monitor during simulation period.

### A3. MinSlope is 2 steps from cliff
- MinSlope=30: performance drops -27.4%. Current value = 28.
- **Impact**: Safety margin is thin.
- **Resolution**: Same as A2. Monitor during simulation.

### A4. MinSlope fixed points does not scale with index level — CLOSED (2026-07-14)
- 28 pts at TXF 12,000 (2020) = 0.23%/bar (very strict)
- 28 pts at TXF 47,000 (2026) = 0.06%/bar (relatively loose)
- **Impact**: Trade count artificially low in earlier years, higher in recent years. Profit concentration biased toward high-index periods.
- **Attempted #1**: v0.6 ATR-based adaptive — REJECTED (ATR measures volatility range, not directional slope)
- **Attempted #2**: v1.1-PCT percentage-based MinSlope — REJECTED (O-1, 2026-07-14)
  - 23-combo Exhaustive GA (MinSlope_Pct 0.03%-0.25%, step 0.01%)
  - No single percentage value beats v1.0 across net profit + trade count + Calmar
  - Root cause: bearish momentum absolute magnitude does not scale proportionally with index level; same 1% = 200pts at 20K vs 400pts at 40K
  - Both percentage and fixed points share the same structural limitation: each value is optimal for specific years, no universal parameter exists
  - Fixed 28pts accidentally provides non-proportional filtering that matches alpha distribution
  - Full analysis: `S16_S_O1_CONCLUSION_20260714.md`
- **Resolution**: CLOSED — maintain v1.0 MinSlope=28pts. Monitor when index reaches 55,000+ (28pts effective < 0.051%), re-evaluate with fixed-point GA at that time.

---

## B. Performance Structure Issues

### B1. Alpha concentrated in 20 trades
- 20 TimeStop exits = +2,103K = ALL alpha. Remaining 86 trades = -1,075K.
- **Impact**: Missing 2-3 big wins (system downtime, manual intervention) turns strategy from profitable to breakeven or loss. System uptime is a survival requirement.
- **Resolution**: Ensure MC12 100% uptime. No manual intervention.

### B2. Profit concentrated in 2025-2026
- 94% of profit from the last 2 years.
- **Impact**: May be benefiting from high index level (see A4). Performance could decline during lower-index periods.
- **Resolution**: WFA 77.4% cross-validated OOS profitability across 9 windows, partially mitigating this concern.

### B3. Longest flat period: 1 year 10 months
- 2020/05 ~ 2022/03: equity curve made no new high.
- **Impact**: Operator must endure extended periods with no return on allocated capital.
- **Resolution**: Portfolio allocation capped at 3%. Does not impair overall capital utilization.

---

## C. Operational Risk Issues

### C1. Losing streak psychological pressure
- Max consecutive losses: 13 (total loss 162K = 16.2% of capital)
- Average consecutive losses: 4.1
- **Impact**: Operator may manually shut down strategy during streaks, missing subsequent large wins. Data shows post-streak wins average 43K to 370K.
- **Resolution**: Discipline issue, no code-level solution. Documented in risk disclosure.

### C2. Bull regime is structural insurance cost
- Bull regime: PF 0.70, 35 trades, net -106K
- **Impact**: During extended bull markets, strategy bleeds consistently. WFA W6 showed -43.4% MDD in AI bull + BoJ regime.
- **Resolution**: Pair with long-side strategies (e.g. S3_L) in portfolio for hedge.

### C3. Day vs Night session contribution unknown
- Backtest does not separate day session vs night session performance.
- **Impact**: Cannot assess whether night session is net alpha or net cost contributor.
- **Resolution**: Post-trade analysis with trade list (session time split). Low priority.

---

## D. Design Philosophy Issues

### D1. No explicit take-profit mechanism
- Profit exit relies entirely on TimeStop (2 hours) and GoldenCross (MA reversal).
- No fixed-amount or percentage-based TP.
- **Impact**: Per-trade profit varies widely (20K to 370K).
- **User ruling (2026-07-13)**: Current design ACCEPTED. Simplicity and repeatability > complexity.

### D2. Entry quality cannot be pre-screened
- Average 4.1 losing trades before 1 winner.
- 6 filter types tested and ALL failed (ATR/Volume/consecutive slope/daily regime/time-of-day/distance).
- **Impact**: Equity curve has visible sawtooth pattern. Psychological cost is high.
- **Potential direction**: Optimize "post-entry judgment speed" rather than "pre-entry filtering" — make QuickStop faster/cheaper, not add more gates.
- **Constraint**: Any new approach must not delay entry (5M burst timing is critical) and must not filter out the 20 TimeStop alpha trades.

---

## F. Compliance / Operational Risk

### F1. Holiday_Block hardcoded to False — CLOSED (2026-07-16)
- v1.0-PROD / v1.1-PCT 的 `v_Holiday_Block = False;` 是 W2 draft placeholder
- Comment 明說「For W2 draft: hardcode Registry expiry only.」但一直未替換
- **Impact**: 假日期間策略可能誤進場/誤持倉（潛在風險，未實際發生虧損）
- **違反**: CLAUDE.md Rule #11 (Settlement_Flat 7 元素) + memory rule `feedback_holiday_flatten_rule`
- **Discovery**: 2026-07-16 例行 self-audit
- **Resolution 2026-07-16**:
  - research 版升 v1.2-HOLIDAY (包含 UsePercentSlope toggle + HolidayFlat_v3)
  - live_simulation 版升 v1.0.1-HOLIDAY (只加 HolidayFlat_v3，不含 UsePercentSlope)
  - Registry 同 L1-L5 / S1 / S3_S 的 63 個 TAIFEX 假日 (2019-2027)
  - Date arithmetic 改成 EL-standard (Year-1900) 格式
  - Registry_Valid_Until 從 1280101 (民國) → 1270101 (EL-std, 2027-01-01)
- **Prevention**: 建立 [`docs/policies/PROMOTE_CHECKLIST.md`](../../../docs/policies/PROMOTE_CHECKLIST.md) 6 項強制檢查
- Full patch details: [`S16_S_HOLIDAY_PATCH_20260716.md`](S16_S_HOLIDAY_PATCH_20260716.md)

### F2. Registry expiry hard limit — 2027-01-01
- Registry_Valid_Until = 1270101 (2027-01-01)
- 現在是 2026-07-16，Registry 剩 ~5.5 個月
- **Action Required**: 需在 2026-12 之前從 TAIFEX 官網撈 2027-2028 假日表更新 Registry
- **Owner**: 使用者 / Claude Code

### F1-b. Holiday patch 績效衝擊實測 — VERIFIED + 用戶 ACCEPTED (2026-07-18)
- 逐筆 diff vs v1.0-PROD：**唯一差異 = 移除 1 筆跨清明連假的 +370,200 彩券單**（2025-04-03 04:45 進場，連假收盤前 15 分鐘裸空，跨關稅崩盤週末）
- 該單違反假日鐵律，gap 可雙向 — 若反向跳空 = 單筆 -360K+，patch 行為 100% 正確
- 用戶 2026-07-18 ruling：**接受合規 baseline**
- **FINAL 合規 baseline（數據回補至 2026-07-18）: Net +833,600 / 110T / PF 1.672 / MDD -271,600 / TimeStop 21 筆 +1,986,200**
- 2026-07 單月 14 筆 +264,000（DD 危機對沖實證，模擬）
- 詳見 `S16_S_HOLIDAY_IMPACT_20260717.md`（含 KPI 重錨定）+ `S16_S_STRATEGY_TEXT_20260718.md`（現行策略文字說明）

### F4. 週六清晨進場 → 跨週末持倉 — CLOSED (2026-07-18, G6 v1.3-TIMEGUARD)
- 原 gap：Holiday registry 不涵蓋普通週末；尾端進場可能持倉跨休市
- **實測發現**：2025-03-05 05:00 進場那筆（-32,800）正是此類 — 04:55 成交後被迫扛過早盤空窗吃 gap 虧損
- **Resolution**：v1.3-TIMEGUARD（用戶設計 ruling）
  - `Tail_LastEntry_Time(430)`：最後進場訊號棒 04:30，成交 04:30 — 夜盤全程開放到此，未來凌晨 burst 頭段吃得到
  - `Tail_ForceExit_Time(440)`：04:40 訊號 → 04:40 成交平倉，距收盤 20 分鐘緩衝
  - 任何部位**結構上不可能**跨任何休市（早盤空窗/週末/假日）
- 對 110 筆 baseline 的預期影響：擋掉 -32,800 那筆（+32.8K）、2026-03-07 出場 04:50→04:40（微幅）、其餘 108 筆不變 → 預期 ~109T / ~+866K
- **MC12 實測驗證 (2026-07-18)**：109T / **+888,400** / PF 1.736 / MDD **-249,600**（改善 22K）/ 連虧 **13→10 次**。2026-03-07 出場實際 flip 為 +21,400（04:45 cover 價比 04:50 低 110 點）→ 實際比預期再好 +22K。逐筆對帳一分不差。**G6 CLOSED，全指標同步改善**

### F3-b. G6 上線後 F3 的重新定位 — CLOSED BY DESIGN (2026-07-18)
- F3 原訴求「封鎖假日前夕夜盤進場」的目的 = 避免跨假日持倉
- G6 之後：前夕夜盤進場**允許**，但任何部位最晚 04:40 平倉（假日尾端更提早到 04:15）
- 「絕不跨休市」由出場端結構保證，進場端不再需要一刀切封鎖 — 符合用戶 2026-07-18 設計哲學：「未來可能性多變，有對應停損停利就該讓策略進場」
- S16_S 專屬 CLOSED；其他策略（S1/L1-L5/S3_S）的 F3 類 gap 是否比照辦理，另案評估

### F3. 假日前夕夜盤未封鎖（系統性 gap）
- 現行 HolidayFlat_v3 只在假日**當天** (Time <= 500) 判 Block
- 缺「前夕夜盤 (15:00-23:59)」封鎖邏輯
- 實例：週三假日 → 週二 21:00 出現死叉+Slope>28 會照常進場，僅在週三 04:15 平倉
- **範圍**: 同時存在於 S1 / L1-L5 / S3_S / S16_S，系統性 gap，非 S16_S 特有
- **與 memory rule 對齊**: 違反 `feedback_holiday_flatten_rule`「封鎖前夕夜盤進場」
- **Action Required**: 未來 batch 處理，全策略一次升級
- **不阻擋**: v1.0.1-HOLIDAY 現行部署

---

## G. Alpha Optimization Tracks（2026-07-16 確定的 4 主線）

### G1. Debug Print 漏單統計 — CLOSED (2026-07-18, 實測完成)
- **實測結果（v1.3.1-G1DEBUG，MC12 全期回測）**:
```
DeathCross total : 7,746  (6.3 年，約 1,226 次/年)
Slope reject     : 7,628  (98.5%)
  slope <= 0     :   556  (7.2%，平/上彎叉 = 純雜訊)
  0 - 7          : 5,850  (75.5%，接近零斜率 = 雜訊主體)
  7 - 14         :   868  (11.2%)
  14 - 21        :   248  (3.2%)
  21 - 28        :   106  (1.4%，near-miss zone)
Compliance reject:     8 / Tail reject: 1 / WOULD ENTER: 109 ✓
```
- **Sanity PASS**: WOULD ENTER = 109 = 實際交易數，加總一分不差
- **核心結論**:
  1. **死叉本身幾乎零資訊量** — 83% 的死叉斜率 <= 7 點。策略的真實身分不是「均線交叉策略」，而是「陡峭斜率 burst 偵測器」，死叉只是 timing trigger。98.5% 拒絕率就是與大眾化 MA cross 的差異化本體
  2. **通過率 1.41%（109/7,746）**，per 判讀矩陣落在「reject >= 85% = 嚴選正確」區
  3. **G4 效益上限量化**: near-miss (21-28) 僅 106 個候選 ≈ 現有進場數；14-28 合計 354。加上 3 根連續性要求後，Type 2 gate 預估僅能新增 20-60 筆 — 且 v0.5 GA 已證明無腦降門檻為負（plateau 26-28，更低為 GA 淘汰區）
- **決策影響**: **G4 從 HIGH 降為 MED-LOW**，排到 G2/G3 之後，驗收從嚴（Type 2 子集必須獨立正期望 + 不拖 PF < 1.60）
- Debug_On 已改回 False（code 保留供未來重跑）

### G2. TimeStop 對比實驗（主線 D）
- MaxHoldingBars 12 / 24 / 36 / 48 四配置對比
- 目的：量化「超過 2hr 的 burst」是否存在
- **Status**: 待實作
- **Priority**: MED

### G3. BE_Trail A/B/C（主線 B，用戶洞察）
- 用戶洞察：BE 在初始停損階段就啟用 → 該賺的賺不到
- 3 配置：A baseline / B 全關 BE / C 延後啟動 (Trigger 2.5×ATR, Buffer 15pts)
- **Status**: 待實作
- **Priority**: HIGH (11 筆 BE 全虧是明確 alpha leak)

### G4. D-2 進化版 — 雙 gate 抓取（主線 A）
- 用戶洞察：空方策略在多頭環境要抓「突然高斜率」+「連續型斜率」兩類
- Type 1: `Slope > 28 AND 加速度 >= 0`
- Type 2: `3根均斜 > 15 AND 3根連續下彎`
- **Status**: 待實作
- **Priority**: HIGH (最大結構改進，但依賴 G1-G3 診斷)

### G5. D-5 Post-Entry N-bar Confirmation（待 ruling）
- 進場後 3 根若 slope 未續弱即退場（動能 based exit）
- 與現有 QuickStop 互補（loss/time based）
- **Status**: 待用戶 GO/NO ruling
- **Priority**: 待定

---

## 已排除方向（audit trail）

| Direction | 排除原因 | Rejection Date |
|-----------|--------|---------------|
| v0.6 ATR-scaled slope | 混淆方向與波動 | 2026-07-10 |
| v1.1-PCT MinSlope 百分比 | O-1 GA 全 REJECTED | 2026-07-14 |
| D-3 分年 GA + 折衷值 | 用未來預測過去 | 2026-07-16 |
| D-4 ATR-normalized slope | 極短周期不能延遲 | 2026-07-16 |
| D-6 單參數 GA 微調 | 過度擬合機率極高 | 2026-07-16 |

---

## E. Overall Assessment

### Strengths
- WFA 77.4% STRONG PASS (strongest in entire portfolio)
- Ruin probability 0.03%, max single loss only 4.26% of capital
- Reward/risk ratio 6.44, recovery factor 3.79
- QuickStop loss control effective (72 trades avg loss only -14K)

### Core Risks
- Alpha highly concentrated (20 trades carry all profit)
- Parameter stability is narrow (S70 narrow peak + Slope30 cliff)
- Requires extreme operator discipline (no intervention during streaks + patience during flat periods)

### Recommendation
- Maintain 3% cap allocation, no adjustment during live_simulation
- Launch S16_S_10M experiment to resolve A1/A4
- Comprehensive re-evaluation after 30+ simulation trades accumulated

---

## Resolution Roadmap

| Issue | Depends On | Earliest Resolution |
|-------|-----------|-------------------|
| A1 | S16_S_10M experiment | After 10M experiment completes |
| A2 | Live simulation data | Ongoing monitoring |
| A3 | Live simulation data | Ongoing monitoring |
| A4 | O-1 percentage GA | CLOSED — 28pts maintained (2026-07-14) |
| B1 | System uptime | Operational requirement |
| B2 | Time + more data | WFA partially addressed |
| B3 | Portfolio design | Managed by 3% cap |
| C1 | Operator discipline | Ongoing |
| C2 | Portfolio hedge | Pair with long strategies |
| C3 | Session-split analysis | Can be done anytime |
| D1 | User ruling | CLOSED — current design accepted |
| D2 | QuickStop optimization | Future optimization cycle |
| F1 | HolidayFlat_v3 patch | CLOSED 2026-07-16 (v1.0.1-HOLIDAY / v1.2-HOLIDAY) |
| F2 | TAIFEX 2027 calendar refresh | Required before 2026-12-31 |
| F3 | 假日前夕夜盤封鎖 (系統性 gap) | Future cross-strategy batch |
| G1 | Debug print 漏單統計 | 主線 C，待明天實作 |
| G2 | TimeStop 對比實驗 | 主線 D，待明天實作 |
| G3 | BE_Trail A/B/C 對比 | 主線 B，待明天實作 |
| G4 | D-2 進化版雙 gate | 主線 A，待明天實作 |
| G5 | D-5 Post-Entry Confirmation | 待用戶 ruling |
