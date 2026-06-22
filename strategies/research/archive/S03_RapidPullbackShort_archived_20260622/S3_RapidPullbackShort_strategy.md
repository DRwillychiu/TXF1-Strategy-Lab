# S3 RapidPullbackShort — Alpha Thesis

- **Date**: 2026-06-20
- **Author**: Claude（ultracode session，使用者 D1-D8 全數 ACCEPT RECOMMENDED + 參數可 MC12 後續優化）
- **Document type**: Alpha thesis（策略本體論述，institutional voice）
- **Companion docs**:
  - 設計規格：[`S3_PullbackShort_design_spec_v2.md`](S3_PullbackShort_design_spec_v2.md)
  - 五份子研究：`scripts/_temp_s3_regime_gate.md`、`_temp_s3_momentum_trigger.md`、`_temp_s3_exit_mechanism.md`、`_temp_s3_portfolio_impact.md`、`_temp_s3_implementation_arch.md`
  - 統計實證：`scripts/_temp_s3_pullback_stats.json`（TWII 2020-2026，22 個歷史 overheating 事件）
- **Constitution compliance**: Rule #11（Settlement_Flat 七元素）、Rule #12（P3b SetStopLoss）、Rule #13（10 維機構級評估）— **MANDATORY**

---

## 1. Strategy Identity

| 欄位 | 內容 |
|------|------|
| **Code name** | `S3_RapidPullbackShort` |
| **MC Load name** | `STRATEGY_GEN_RapidPullbackShort` |
| **Label prefix** | `SE_RPS_*`（Short Entry），`SX_RPS_*`（Short eXit） |
| **One-line essence** | **強多頭過熱 + 5M 快速下跌啟動 → 做空 30 分-4 小時，吃 0.7%-1% 拉回** |
| **Direction** | Short-only（單向，不做多） |
| **Strategy class** | Counter-trend mean-reversion with momentum confirmation（趨勢反轉，但需動能確認） |
| **Execution timeframe** | 5M（執行）/ 60M（overheating overlay）/ Daily（regime gate） |
| **Holding horizon** | 30 分鐘 - 4 小時，日內強制平倉（13:25 force flat） |
| **Position** | 固定 1 口（與 frozen 6 一致） |

S3 不是「mean reversion 賭多頭轉空」的純做空策略。S3 是 **「多頭趨勢中段，當 5M 親自證明拉回已經啟動之後」才出手** 的條件式反向策略。Tier 1 定義機會背景（regime），Tier 2 證明拉回是真的（momentum confirmation）。兩層 gate 是核心架構，缺一不可。

---

## 2. Alpha Thesis — Why This Works

### 2.1 Market mechanism（市場機制）

TXF1 多頭過熱期間具有三項可被結構性利用的市場特徵：

1. **獲利了結節奏（profit-taking rhythm）**：當 Daily RSI(14) > 70 連續 2 根，代表市場連續上攻已使機構部位偏多失衡。任何雜訊都可能觸發 risk parity / vol-targeting 帳戶減碼，引發 1-3% 量級的拉回。歷史 22 次（2020-2026 TWII）顯示 median 2-day pullback = 0.57%，p75 = 1.15%，p90 = 1.64%。
2. **散戶 FOMO 高峰（retail capitulation buying peak）**：距 MA20 > 3% 是台灣散戶的進場高峰區。Z-score 概念下，此時邊際買盤已耗盡，下方支撐脆弱，賣壓觸發後容易連鎖。
3. **日內 momentum exhaustion**：當 5M 連續 3 根紅 K + EMA5 下彎 + ATR 急遽放大時，意味前段上攻動能已轉為下行動能。這個訊號在 overheating 背景下的訊噪比遠高於 baseline。

### 2.2 Why momentum-confirmed vs pure mean-reversion

純 mean reversion（RSI > 75 即放空）在台指期的長期實證是 **負期望值**。原因：

- RSI > 75 可以持續 2-6 週（2024-Q4、2025-Q2 都有先例）
- 在多頭主升段反向放空 = 與趨勢對作 + 與時間對作
- Frozen 6 中 L4 ConsolidationShort（原本的反轉派代表）即因此在 OVERFIT_RISK 狀態下被使用者選擇退役（D6）

S3 的解方：**「不預測拉回，等拉回發生才進場」**。Tier 2 的 4-AND 條件（M1 3 紅 K + M2 EMA5 下彎 + M3 ATR 放大 + M4 拉回幅度 [0.5%, 1.5%] 帶內）讓 S3 跳過「等待拉回」這個漫長的負期望期間，只在「拉回已開始但尚未走完」的窄窗口內進場。

Agent A 子研究進一步證實：**單一 overheating signal 預測 1-day pullback 的 hit rate 比 baseline 還差**。Tier 1 不是 trigger，是 filter；trigger 必須在 5M 上由 momentum confirmation 提供。這是 S3 與所有「賭頂」型策略的本質差異。

### 2.3 Academic support

- **Time-series momentum reversal**（Moskowitz, Ooi & Pedersen 2012，後續 De Bondt-Thaler 1985 series）：12-month momentum 後常見 1-3 month reversal，但 reversal 須有 confirmation 才具交易價值。
- **Intraday momentum exhaustion**（Bogousslavsky 2016；Heston, Korajczyk & Sadka 2010）：當日內 trending behaviour 達極端後，後段常出現 mean-reversion 區段，但僅在 volume + volatility 同步擴張時可被識別。
- **Counter-trend with confirmation outperforms pure contrarian**（Jegadeesh & Titman 1993 reverse-momentum；近代 high-frequency literature）：純反向策略的 Sharpe 通常 < 0.3，加入 confirmation filter（如動能轉向、波動率擴張）後 Sharpe 可提升至 0.5-0.8。

S3 的 Tier 1 + Tier 2 架構即落在這個學術光譜的「filter-confirmed mean reversion」位置。

### 2.4 TXF1 specifics

- **散戶比重高**：TXF1 散戶/法人比顯著高於 SPX，使「散戶 FOMO 高峰」這個機制信號相對強烈。
- **日盤強度集中**：08:45-13:45 五小時內完成 60-70% 日均成交量，5M 訊號密度足夠（不同於 SPX 23 小時稀釋）。
- **單一商品流動性**：1 口進出滑價 1,000 NTD（CLAUDE.md 規範），對 0.7% TP（≈150 點）約 6.7% 拖累，可接受。
- **無夜盤 carry**：S3 嚴格日內，避開夜盤跳空 gap 風險（風險 #6）。

---

## 3. Portfolio Role

### 3.1 Fills the bull-mid-pullback hedge gap

Frozen 6 的多空配置如下：

| 多頭 sleeves | 空頭 sleeves | 區間 |
|--------------|--------------|------|
| L1 TrendLong (29%) | L2 TrendShort (22%) | L3 ConsolidationLong (10%) |
| L5 BreakoutLong (16%) | L4 ConsolidationShort (3%) | S1 NightMomentum (20%, 多頭偏向) |

帳面上空頭占 25%，但 **S1 是夜盤多頭動能**，L4 需要「箱型整理 + 下緣突破」才會 fire。實證上 frozen 6 在 **多頭趨勢中段的 intraday pullback** 月份（2024-11、2025-06）並無任何 sleeve 提供結構性對沖 — L1/L5 同時吃損，L2 因規模太小且需 bear trend confirmation 而不 fire。

S3 直擊這個缺口：**Tier 1 強制 bull regime（MA20>MA60）+ overheating，正好是 L1/L5 開始吃 pullback 損失的時機**。S3 fire 的時候，L1/L5 大概率正在吐回獲利。S3 的損失場景（pullback 沒發生）反而是 L1/L5 賺錢的時候。這就是結構性負相關。

### 3.2 Why L2 and L4 cannot cover this gap

| 策略 | 開火條件 | 為何不能取代 S3 |
|------|----------|-----------------|
| **L2 TrendShort** | 需要 Daily 確認下行趨勢（MA 反轉 + ADX）才 fire | 多頭主升段 L2 完全沉睡。等 L2 fire 時拉回已走完 |
| **L4 ConsolidationShort** | 需要箱型整理 + 下緣突破 | 多頭趨勢 = 沒箱型；L4 在 trending 月份全月不 fire；且 L4 已因 OVERFIT_RISK 在 D6 退役 |
| **S1 NightMomentum** | 夜盤多頭動能 | 多頭，且夜盤限定，與日內 pullback 完全錯開 |

S3 唯一補上的時間窗口：**Bull regime（日線）+ Daily overheating 兩條件成立的日內**。Tier 1 預期一年約 55-65 個 WATCH 日（每月 ~5 天），Tier 2 在這些日子裡篩出 25-40 次 entry（一年）。

### 3.3 Predicted correlation matrix（monthly horizon）

| | L1 | L2 | L3 | L5 | S1 | S3 |
|---|---:|---:|---:|---:|---:|---:|
| **S3** | **−0.35** | +0.30 | +0.05 | **−0.30** | **−0.15** | 1.00 |

- 與 L1/L5/S1（三大多頭 sleeves）結構性負相關：S3 fire 的月份正是它們回吐的月份
- 與 L2 modest 正相關：兩者都在 down month 上 fire，但 S3 是 intraday，L2 是 multi-day swing — 不衝突
- 與 L3 近獨立：L3 需 range regime，S3 需 bull regime，兩者 mutually exclusive 觸發

所有預測 ρ 絕對值 < 0.40，遠低於 institutional |r| < 0.7 gate（Rule #13 dim 3）。最終實證須以 Phase 2 live_simulation 30+ 筆樣本驗證。

### 3.4 Replaces L4's slot in v3 allocation

使用者 D6 明確 OVERRIDE 先前「L4 不可砍光」承諾，原因如下：

1. L4 stability test 5 項僅通過 1 項，OVERFIT_RISK status
2. L4 一年僅 fire 3-6 次，且觸發場景（範圍整理 + 下緣突破）出現頻率遠低於 S3 觸發場景（bull pullback）
3. L4 的「downside capture」角色由 S3 以更頻繁、機制更可解釋的方式取代

**v3 Allocation**：

| Sleeve | v2 | **v3** | Δ |
|--------|---:|-------:|---:|
| L1 TrendLong | 29% | **29%** | 0 |
| L2 TrendShort | 22% | **22%** | 0 |
| L3 ConsolidationLong | 10% | **10%** | 0 |
| L4 ConsolidationShort | 3% | **0%** | **−3 (RETIRED)** |
| L5 BreakoutLong | 16% | **16%** | 0 |
| S1 NightMomentum | 20% | **20%** | 0 |
| **S3 RapidPullbackShort** | — | **3%** | **+3 (NEW)** |
| **TOTAL** | 100% | **100%** | 0 |

---

## 4. Trading Mechanics

### 4.1 Two-tier gating architecture

```
TIER 1 — REGIME GATE (Daily Data3)
  A: MA20 > MA60 (mandatory bull anchor)
  AND
  B OR C:
    B: RSI(14) > 70 sustained 2 bars
    C: (Close - MA20) / MA20 × 100 > 3.0%
  → v_S3_Watch = true (~5 days/month)

TIER 2 — MOMENTUM TRIGGER (5M Data1)
  Inside active WATCH window AND:
  M1: 3 consecutive 5M red candles
  M2: Close < EMA5 AND EMA5 declining
  M3: ATR(5) > ATR(20) × 1.3
  M4: (HighD(0) - Close) / HighD(0) × 100 ∈ [0.5%, 1.5%]
  → SellShort Next Bar at Market (SE_RPS_Entry)
```

所有 Tier 1 signals 用 Daily Data3 `[1]` 索引（CLAUDE.md rule #3，已收盤）。所有 Tier 2 signals 純 OHLC（避開 5M Volume 不確定性，§4.4）。

### 4.2 Exit cascade（Priority 0 → P3）

| Priority | Trigger | Label | Order type |
|---------:|---------|-------|------------|
| **P0** | Manual_Kill_Switch | `SX_RPS_Kill` | Market |
| P0 | Date > Registry_Valid_Until | `SX_RPS_RegistryEnd` | Market |
| P0 | Holiday_Block + Time≥0245 | `SX_RPS_HolFlat` | Market |
| P0 | Settlement_Day + Time≥1230 | `SX_RPS_Settlement` | Market |
| P0 | `SetStopLoss(...)` engine-level always-armed | (engine) | Stop |
| **P0a** | Time ≥ 1325 | `SX_RPS_DayClose` | Market |
| **P1** | Close ≤ TP_Price OR Close ≤ 5M_EMA20[1] | `SX_RPS_TP` | Market |
| **P2** | Close ≥ v_SL_Level (frozen) | `SX_RPS_SL` | Stop |
| **P3** | BarsSinceEntry ≥ 24 (=120 min) | `SX_RPS_TimeStop` | Market |

關鍵設計：

- **P0a (DayClose 13:25) 優先級高於 TP/SL**：日內限定是硬約束，不可違反
- **TP 雙觸發**：固定 0.7% OR 5M EMA20 觸碰（D4 ACCEPT）— 約 30% 拉回會在 0.7% 之前先觸碰 EMA20
- **SL frozen on entry bar**：進場當下凍結 `v_Frozen_ATR_5M × 4.0`，禁止 mid-trade 漂移（entry_exit_sop §3 principle #1）
- **同日 cooldown**：任一 SX_RPS_* 觸發後鎖定 `v_S3_LastExitDate = Date`，當日不再進場（S2 lesson）

### 4.3 Inputs（all parameterized for MC12 optimization）

依使用者明確要求：**所有數值門檻必須是 PowerLanguage inputs，禁止 hardcode**。提供 sensible defaults 與 suggested optimization ranges（供 v1.1 MC12 sweep）：

```powerlanguage
Inputs:
   /* Tier 1 — Regime Gate (Daily) */
   Regime_MA_Fast_Len      ( 20    ),   /* sweep: 15-25 */
   Regime_MA_Slow_Len      ( 60    ),   /* sweep: 40-80 */
   Regime_RSI_Len          ( 14    ),   /* sweep: 10-21 */
   Regime_RSI_Threshold    ( 70.0  ),   /* sweep: 65-78 */
   Regime_RSI_Sustained    ( 2     ),   /* sweep: 1-3 bars */
   Regime_Dist_MA_Pct      ( 3.0   ),   /* sweep: 2.0-5.0 */

   /* Tier 2 — Momentum Trigger (5M) */
   Trigger_ConsecRed_N     ( 3     ),   /* sweep: 2-4 */
   Trigger_EMA_Len         ( 5     ),   /* sweep: 3-8 */
   Trigger_ATR_Fast        ( 5     ),   /* sweep: 3-8 */
   Trigger_ATR_Slow        ( 20    ),   /* sweep: 15-30 */
   Trigger_ATR_Ratio       ( 1.3   ),   /* sweep: 1.1-1.6 */
   Trigger_Pullback_Min    ( 0.5   ),   /* sweep: 0.3-0.8 */
   Trigger_Pullback_Max    ( 1.5   ),   /* sweep: 1.2-2.5 */

   /* Exit Mechanics */
   TP_Pct                  ( 0.70  ),   /* sweep: 0.5-1.0 */
   TP_Use_MA20_Backup      ( true  ),   /* boolean */
   TP_MA_Len               ( 20    ),   /* sweep: 15-30 */
   SL_ATR_5M_Multiple      ( 4.0   ),   /* sweep: 3.0-5.5 */
   SL_ATR_Len              ( 14    ),   /* sweep: 10-21 */
   MaxBars_TimeStop        ( 24    ),   /* sweep: 18-36 = 90-180min */

   /* Time Windows */
   Entry_Open_Time         (  845  ),   /* D5 wider, ACCEPT */
   Entry_Cutoff_Time       ( 1230  ),   /* sweep: 1130-1300 */
   Daily_Flat_Time         ( 1325  ),   /* hard rule, do NOT sweep */

   /* Constitution (inherited from L2/L5) */
   Holiday_Flat_Time       (  245  ),
   Settlement_Flat_Time    ( 1230  ),
   Manual_Kill_Switch      ( false ),
   Registry_Valid_Until    ( 1270101 ),

   /* HighConviction Modifier (D8 — logging-only in v1.0) */
   HC_Dist_Threshold       ( 5.0   ),   /* dist_MA20 > 5%, logging only */

   /* Volume (D7 verification pending; OFF by default v1.0) */
   VolConfirm_On           ( false );   /* 5M volume reliability TBD */
```

---

## 5. Expected Performance Profile (PRE-BACKTEST)

下列為 **forecast only**，根據 Agent A-E 五份子研究與 22 個歷史事件統計外推；非 backtest 數據。Phase 1 須以 MC12 實證重新校準。

| 指標 | 目標 / 預測值 | 來源 |
|------|---------------|------|
| Trades / year | **25-40** | Agent B BALANCED 4-AND × ~55-65 WATCH days/yr |
| Win rate | **52-58%** | Counter-trend with confirmation typical range |
| Avg winner / Avg loser (R:R) | **1.21** | TP 0.7% / SL 0.58%（4×ATR）|
| Expected PF | **1.3-1.7** | WR 55% × R:R 1.21 ≈ 1.48 mid-case |
| Avg hold time | **60-90 min** | 中位數，受 P1 TP 與 P3 TimeStop 雙端拉扯 |
| Max hold | 120 min (24 × 5M bars) | P3 hard cap |
| Slippage drag | ~6-9% of gross | 1k/round × ~30 trades × 200k gross |
| Target MDD (sleeve-level) | **< 7% of allocated capital** | Counter-trend tail-risk budget |
| Sample over 6.5y backtest | **165-260 trades** | Rule #13 dim 5 threshold (≥100) PASS |
| Forecast Sharpe (sleeve alone) | 0.4-0.7 | Counter-trend strategies typical |
| Forecast portfolio Sharpe lift | **+1% to +10%** (1.41 → 1.42-1.55) | Agent D §3.5 |

最關鍵的預測：**S3 在 2024-11、2025-06 型 bull pullback 月份應將 portfolio worst-month MDD 從 -199k 降至 -140k ~ -170k（-15% ~ -30% improvement）**。這是 S3 加入的根本理由。

---

## 6. Risk Management & Constraints

### 6.1 Counter-trend = tight SL mandatory

逆勢交易最大的風險是 **「拉回沒發生而趨勢繼續延伸」**。S3 用三層防護：

1. **Tier 2 M4 ceiling 1.5%**：禁止在已下跌 > 1.5% 後追空（避免接刀）
2. **Frozen SL = 4×ATR(5M,14) ≈ 0.58%**：吸收典型 5M noise 但對趨勢延伸快速停損
3. **Time stop 120 min**：拉回若 2 小時內未達 TP，論點即視為失效

### 6.2 5M slippage proportionally larger

5M timeframe 的單筆獲利目標（0.7% ≈ 150 點 ≈ 30k NTD/口）相對於 1k 滑價的比例（~3.3%）顯著高於 15M/60M 策略。S3 的 R:R 1.21 設計已將此計入；若 Phase 1 backtest 顯示實際滑價拖累 > 10% gross，須擴大 TP 或降低 trade frequency。

### 6.3 Volume signal dropped (S2 v0.4 lesson)

**最重要的防禦性設計**：5M Volume confirmation **NOT** 進入 core combo。

- 背景：S2 v0.4 將 `VolFilter_On = true` 預設開啟，但 TXF1 30M Volume 在 MC12 中常為 0；當 `v_VolMA = 0` 時 VolFilter 永遠 false → S2 v0.4 在 6.5 年 backtest 中產生 0 筆 entry
- TXF1 5M Volume 可靠性未驗證，假設更不可靠
- **替代方案**：M3 ATR spike 作為 volume 的 OHLC-only 代理
- **v1.0 default**：`VolConfirm_On = false`，並提供 `v_VolMA20 > 0` guard 供使用者驗證後 opt-in
- **D7 procedural step**：`.pla` coding 前先用 5-line MC ShowMe study 量測 5M Volume = 0 的 bar 比例

### 6.4 Mandatory Settlement_Flat / Holiday / SetStopLoss

per CLAUDE.md Rule #11 / #12 與 SETTLEMENT_DAY_DESIGN_CONSTITUTION，S3 從 L2_TrendShort.pla / L5_BreakoutLong.pla 模板 byte-identical 繼承以下模組：

- 63 條 `Holiday_Tail` 陣列（含 sentinel 1270101 與當期 1260619）
- `v_Settlement_Day` 偵測（DayOfWeek=3 + DayOfMonth ∈ [15,21]）
- `SetStopLoss(SL_ATR_5M_Multiple × AvgTrueRange(SL_ATR_Len) × BigPointValue)`，guard `if MP >= 0`
- 進場 gate 必含 `v_Settlement_Day = false`

### 6.5 Daily flat 13:25 (no overnight risk for S3)

S3 嚴格日內，13:25 強制平倉（早於 13:45 day session close 20 min cushion）：

- 完全避開夜盤跳空 gap 風險
- 完全避開隔夜 news risk
- 完全避開 weekend gap
- 但代價：放棄 multi-day pullback 的尾段（接受，因為 multi-day 屬於 L2 領域）

### 6.6 Known unknowns（須 Phase 1 驗證）

| Risk | Phase 1 驗證方法 |
|------|------------------|
| 5M ATR magnitude（估 25-45 TXF pts） | Log `AvgTrueRange(14)` 分佈，median 須落在 25-45 pt |
| Watch state stuck（perpetual rearming） | `Watch_Stale_Bars = 8` (40 min) timeout + single-shot per fire |
| Correlations come in flat | 30-trade gate before live capital + Phase 2 WFE 量測實際 ρ |

---

## 7. Comparison vs L2 / L4

| Dimension | **S3 RapidPullbackShort** | L2 TrendShort | L4 ConsolidationShort (retired) |
|-----------|---------------------------|---------------|----------------------------------|
| Direction | Short | Short | Short |
| **Regime needed** | **Bull (MA20>MA60) + overheating** | **Bear trend (MA reversal + ADX)** | **Range (low ADX + boxed)** |
| Execution TF | 5M | 30M | 30M |
| Entry mechanism | 5M momentum confirmation 後逆勢空 | 趨勢確認轉空後順勢空 | 箱型下緣突破空 |
| Holding horizon | 30 min - 4 hr（intraday） | 1-5 days（swing） | 6-24 hr（intra-multi） |
| TP target | 0.7% / EMA20 觸碰 | 趨勢段尾端 / 移動停利 | 箱型寬度 |
| When does each fire? | Bull pullback intraday | Bear leg 主升段 | Sideways breakdown |
| **互斥性** | Tier 1 強制 bull，與 L2 regime 互斥 | Bear regime，與 S3 互斥 | Range regime，與 S3 互斥 |
| Frequency (forecast) | 25-40 / yr | ~12 / yr | ~3-6 / yr |
| Portfolio role | Bull-pullback hedge | Bear-trend capture | Range breakout（已退役） |
| Allocation v3 | **3%** | 22% | 0% |

關鍵觀察：**三者開火條件 mutually exclusive，因此可同時持有而 monthly correlation 接近獨立或負值**。

---

## 8. Versions Plan

| 版本 | 範圍 | 啟動條件 |
|------|------|----------|
| **v1.0** | BALANCED 預設值（D1-D5/D7 ACCEPT），HighConviction logging-only（D8），L4 retired（D6） | 本 thesis + design_spec_v2 + verify script + .pla 完成後 |
| **v1.1** | MC12 parameter sweep（all 22 inputs），找最佳 PF / Sharpe 高原區 | v1.0 通過 Phase 1-3，30+ sim trades，PF ≥ 1.2 |
| v1.2 | HighConviction modifier activate（A: relax M3 ATR ratio when dist>5%） | v1.1 確認 HC bin 樣本 ≥ 30 且 PF 顯著優於 base |
| v2.0 | 3-stage exit（partial TP at 0.4% → trail to EMA20 → time stop） | v1.2 通過 6 個月 live_simulation |
| v2.x | 引入 60M overheating overlay（RSI60 / BB60 作為 Tier 1.5） | v2.0 證實穩定後 |

**v1.0 不嘗試擊敗 L1/L2 的 Sharpe**。v1.0 的成功定義 = 「在 bull pullback 月份提供結構性負相關，且自身 PF > 1.2、樣本 ≥ 30」。

---

## 9. Mandatory Compliance

### 9.1 Rule #11 — Settlement_Flat 7 elements

從 `L2_TrendShort.pla` 模板繼承（design_spec_v2 §8.1 列出全部 7 元素），核心：

- 第 3rd Wednesday + DayOfMonth ∈ [15, 21] 偵測
- `SX_RPS_Settlement` 在 Priority 0 區塊
- 進場 gate 含 `v_Settlement_Day = false`
- Settlement_Flat_Time = 1230（強制當日 12:30 平倉）

### 9.2 Rule #12 — P3b SetStopLoss

```powerlanguage
/* MUST come BEFORE entry block, AFTER indicator computation */
if MarketPosition >= 0 then
   SetStopLoss( SL_ATR_5M_Multiple * AvgTrueRange(SL_ATR_Len) * BigPointValue );
```

Guard `MP >= 0`（short strategy 進場前），距離與 Frozen SL 使用相同變數與 multiple，金額 = 距離 × BigPointValue（TXF1 = 200），全策略僅 1 call。

### 9.3 Rule #13 — 10-dim institutional eval

`verify_s3_pullbackshort.py`（60 項檢查）涵蓋全部 10 維度：

| Dim | 預檢狀態 | live_simulation 通過門檻 |
|----:|----------|--------------------------|
| 1 Sharpe/Sortino/Calmar | Forecast 0.4-0.7 | Sharpe ≥ 0.5 |
| 2 VaR/CVaR | Pending Phase 1 | 95% VaR ≤ 2% account |
| 3 Correlation < 0.7 | Forecast all < 0.40 | 實證 < 0.7 daily, < 0.6 monthly |
| 4 Drawdown clustering | Pending | 12-mo 滾動內無 3+ 連續虧損月 |
| 5 Sample ≥ 100 | Forecast 165-260 over 6.5y | 30+ sim, 100+ live |
| 6 WFE > 50% | Pending Phase 2 | WFE > 0.5 |
| 7 三市況 PF > 1.0 | Bear=dormant 可接受（regime-specialist） | Bull PF ≥ 1.2 |
| 8 Cost analysis | Forecast 6-9% drag | Net > 5× cost |
| 9 Operational risk | 5M = high intraday attention | 須出 monitoring SOP |
| 10 法規/帳戶 | 1 口 intraday 全範圍 | OK |

**任一維度 fail → 禁止上 live_simulation**（Rule #13 強制位階）。

---

## 10. References

### 內部文件

- **設計規格**：[`S3_PullbackShort_design_spec_v2.md`](S3_PullbackShort_design_spec_v2.md)（v2 final, 2026-06-20）
- **子研究 A — Regime Gate**：`scripts/_temp_s3_regime_gate.md`（8 signals 分析，Option 3B MODERATE 推薦）
- **子研究 B — Momentum Trigger**：`scripts/_temp_s3_momentum_trigger.md`（8 signals 分析，BALANCED 4-AND 推薦）
- **子研究 C — Exit Mechanism**：`scripts/_temp_s3_exit_mechanism.md`（TP/SL/Time empirical derivation）
- **子研究 D — Portfolio Impact**：`scripts/_temp_s3_portfolio_impact.md`（allocation forecast 1.41→1.42-1.55 Sharpe）
- **子研究 E — Implementation Arch**：`scripts/_temp_s3_implementation_arch.md`（MC12 architecture, ~420 LOC）
- **統計實證**：`scripts/_temp_s3_pullback_stats.json` / `_temp_s3_pullback_stats.py`（22 episodes 2020-2026）

### Constitution & Framework

- `docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`（強制位階 v1.1）
- `docs/entry_exit_sop.md`（9 層出場架構）
- `docs/P3b_immediate_stop_guard_design_20260618.md`（SetStopLoss 強制規範）
- `docs/institutional_risk_framework_20260619.md`（10 維度 framework）

### Portfolio anchors（v3 to be written）

- `docs/portfolio_correlation_matrix_20260620.md`（v2 baseline，含 S3 預測 ρ）
- `docs/portfolio_walk_forward_20260620.md`（v2 baseline WFE）
- `docs/portfolio_allocation_v2_20260620.md`（frozen 6 weights，將由 portfolio_allocation_v3_20260620.md 取代）

### Code templates

- `strategies/live/L2_TrendShort.pla`（Settlement + Holiday + SetStopLoss 模板來源）
- `strategies/live/L5_BreakoutLong.pla`（3-data wiring 模板來源）

---

_Alpha thesis 撰寫於 2026-06-20，承接使用者 D1-D8 全數 ACCEPT RECOMMENDED 之決議。所有數值門檻已設為 PowerLanguage inputs 供 MC12 v1.1 sweep。Constitution Rule #11/#12/#13 之合規檢查為 live_simulation 前置 mandatory gate。Next concrete action：撰寫 `S3_RapidPullbackShort_annotated.md` per-line walkthrough，續寫 `.pla` 與 `verify_s3_pullbackshort.py`（60 項）。_
