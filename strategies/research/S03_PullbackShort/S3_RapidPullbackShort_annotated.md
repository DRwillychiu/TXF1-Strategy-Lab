# S3 RapidPullbackShort v1.0 — 中文逐段註解

**MC Load Name**：`STRATEGY_GEN_RapidPullbackShort`
**版本**：v1.0（Agent D 五路 deep-research 合成終稿，2026-06-20）
**檔案**：[`S3_RapidPullbackShort.pla`](S3_RapidPullbackShort.pla)
**設計規格**：[`S3_PullbackShort_design_spec_v2.md`](S3_PullbackShort_design_spec_v2.md)
**標籤前綴**：`SE_RPS_` (Short Entry)、`SX_RPS_` (Short Exit)
**配置額度**：3%（取代退役的 L4 名額；v3 配置 L1:29 L2:22 L3:10 L5:16 S1:20 **S3:3** = 100%）

---

## 〇、策略本質

### 0.1 賺什麼錢

**逆勢空單，獵殺過熱的多頭日內回檔**（counter-trend short on overheated bull pullback）。

```
多頭高估狀態（Daily Regime Watch）
 + 5M 動能急轉（4-AND momentum trigger）
 ──→ 沽空，賺 ~0.7% 回測幅度
```

**核心假設**：當日線結構偏多但出現過熱（RSI 高檔黏住 / 偏離 MA20 過大），盤中第一波明確失速（連 3 紅 + EMA 跌破 + ATR spike + 落點剛好的回檔）通常會延伸 60–120 分鐘的回測，足夠收 0.7% 利差。

### 0.2 為什麼會有 alpha

| 結構 | 反映的市場行為 |
|------|---------------|
| **Tier 1 Daily Regime（A AND (B OR C)）** | 只在「多頭已過熱」的環境出手，避開單純做空趨勢的死亡螺旋 |
| **Tier 2 5M 4-AND Trigger** | 4 個正交條件（連紅 / MA 結構 / 波動率 / 幾何位置）同時觸發，將胡亂空頭轉為「失速確認」 |
| **Pullback 落點 [0.5%, 1.5%]** | 太淺 = 噪音、太深 = 反彈空間有限。卡在「賣家剛要交棒、買家還沒接到位」的甜蜜區 |
| **0.7% TP / 0.58% SL / 120min 時間停損** | R:R 1.21、設計 WR 52–58%、避免過夜結算風險 |

### 0.3 為什麼這次設計把 Volume 拿掉

**S2 v0.4 教訓**：TXF1 5M 成交量序列尚未經 MC ShowMe 五行驗證，盲加 Volume filter 等於賭資料完整性。本版 v1.0 採 D7 程序保護：volume 條件留待 ShowMe 驗證後在 v1.1 重新評估。

---

## 一、Design Decisions 對照表（D1–D8）

| 編號 | 決策 | 採用版本 | 程式對應 |
|------|------|---------|----------|
| D1 | Regime Gate | **MODERATE**：A AND (B OR C) | Section 2 → `v_Regime_Watch` |
| D2 | Momentum Trigger | **BALANCED 4-AND**（無 Volume）| Section 3 → `v_Trigger_Fired` |
| D3 | Exit Tier | **BALANCED**：TP 0.7% / SL ATR×4 / Time 120min | Section 5 (SL) + Section 7 |
| D4 | TP 結構備援 | INCLUDE **5M EMA20 觸及** | `TP_Use_EMA20_Backup` + Section 7 TP block |
| D5 | Entry Window | **08:45 – 12:30**（wider）| `Entry_Open_Time` / `Entry_Cutoff_Time` |
| D6 | L4 處置 | **退役 L4，S3 接 3% 額度** | （allocation 文件，非本檔程式碼）|
| D7 | Volume 驗證 | YES（ShowMe 五行外部驗證）| 留 Comment、v1.0 不入程式 |
| D8 | HighConviction modifier | **v1.0 logging-only**（dist > +5%）| Section 9 `Log_HighConviction` |

---

## 二、逐段註解

### Section 0 — Holiday Tail Registry（假日尾巴登錄表）

```powerlanguage
arrays:
    Holiday_Tail[80]( 0 );

if CurrentBar = 1 then begin
    { --- 2019 --- }
    Holiday_Tail[1]  = 1190913;
    ...
    { --- 2026 (verified: TAIFEX official 115-yr calendar) --- }
    Holiday_Tail[54] = 1260212;  { CNY: final trading day 2/11 }
    ...
    Holiday_Tail[63] = 1270101;  { 2027 New Year 1/1-1/3, eve 12/31 }
end;
```

**做什麼**：在 `CurrentBar = 1` 一次性初始化 63 筆假日「尾巴」日期。`Holiday_Tail` 定義為「**最後交易日 +1 個曆日**」 = 連假前夕夜盤的 00:00–05:00 那段 tail bar 所掛上的日期。

**為什麼**：MC 把跨日夜盤 K 棒的 `Date` 印成「下一個交易日」，所以在偵測「假日前夕夜盤」時必須抓的不是 holiday 本身，而是 holiday tail 那組日期。此邏輯與 L1/L2/L3/L5 共用同一份 63 筆 byte-identical registry（feedback_holiday_flatten_rule.md「以期交所官方行事曆為唯一準據」）。

**對應決策**：CLAUDE.md Rule #11 Settlement_Flat 7 元素之一。

**Gotcha**：
- 帶 `*` 標記的列（如 `1240501` Labor Day）為待覆核項目，每 Q4 必須對照 TAIFEX 116 年行事曆重建。
- `Registry_Valid_Until = 1270101` 代表這份 registry 只到 2027 元旦前；超過會觸發 `v_Registry_Expired = True` 並 force-flat。

---

### Section 1B — Holiday / Registry / Settlement Detection（保護狀態旗標）

```powerlanguage
v_Holiday_Block = False;

if Time <= 500 then begin
    for hidx = 1 to 80 begin
        if Date = Holiday_Tail[hidx] then
            v_Holiday_Block = True;
    end;
end;

v_Registry_Expired = False;
if Date > Registry_Valid_Until then begin
    v_Registry_Expired = True;
    v_Holiday_Block    = True;
end;

v_Settlement_Day = ( DayOfWeek( Date ) = 3 ) and
                   ( DayOfMonth( Date ) >= 15 ) and
                   ( DayOfMonth( Date ) <= 21 );
```

**做什麼**：每根 K 棒重置三個保護旗標：
1. `v_Holiday_Block`：當 `Time <= 500`（清晨 5 點以前 tail bar 時段）且 `Date` 命中 registry，則升旗。
2. `v_Registry_Expired`：超過 registry 截止日就升旗，並連帶把 `v_Holiday_Block` 也升起，達成「未知環境 = 全面 freeze」的兜底。
3. `v_Settlement_Day`：每月第三個禮拜三（DayOfWeek=3 且 DayOfMonth 落在 15–21 之間的唯一星期三）。

**為什麼**：
- `Time <= 500` 是「**閉區間天然上界**」(`Time <= 500` 本身就把區間封死)，因此 24 小時制陷阱（feedback_mc_time_24hr_pitfall.md）在這裡不會發生。
- 把保護旗標統一在進場 / 出場前計算，可讓後續所有 `Time >= X` 條件都被 state-guard 抓住（避免「裸露 Time>=X」）。

**Gotcha**：迴圈跑 `for hidx = 1 to 80`，但 registry 只填到 63 ，剩下 17 格固定為 0；`Date = 0` 永遠 false 不會誤觸發，這是刻意預留擴充空間。

```powerlanguage
if LastBarOnChart and
   DateToJulian( Date ) >= DateToJulian( Registry_Valid_Until ) - 30 then begin
    if Registry_Warn_ID < 0 then begin
        Registry_Warn_ID = Text_New( Date, Time, High + 400, ... );
        Text_SetColor( Registry_Warn_ID, Red );
        ...
    end;
end;
```

**做什麼**：在圖表上印出紅色警告字，提醒「registry 30 日內到期，請從 TAIFEX 行事曆重建」。`Registry_Warn_ID < 0` 守衛防止重複貼字。

**為什麼**：避免 registry 默默過期造成 v_Registry_Expired 連環觸發後策略全面停擺卻無人察覺。視覺警告 = 運維最後一道防線。

---

### Section 2 — Daily Tier 1 Calculations（日線環境閘）

```powerlanguage
v_Daily_FastMA = Average( Close, Daily_FastMA_Len )[1] of Data3;
v_Daily_SlowMA = Average( Close, Daily_SlowMA_Len )[1] of Data3;
v_Daily_RSI    = RSI( Close of Data3, Daily_RSI_Len )[1];
```

**做什麼**：從 Data3（日線）取已收盤 `[1]` 值計算 MA20、MA60、RSI14。

**為什麼**：**CLAUDE.md Rule #3 強制**「Data3 當根可能為部分 bar，必須引用 `[1]` 已收盤值」。若用 `[0]` 等於用未閉合的日 K 做決策，會產生回測 / 實盤行為不一致。

```powerlanguage
if v_Daily_FastMA > 0 then
    v_Daily_Dist_Pct = ( ( Close[1] of Data3 ) - v_Daily_FastMA ) /
                       v_Daily_FastMA * 100
else
    v_Daily_Dist_Pct = 0;
```

**做什麼**：計算「昨日收盤距 MA20 的百分比距離」。正值 = 收盤在 MA20 之上。

**為什麼**：D1 condition C「距離 MA20 > +3%」之數值來源。除 0 防護（`> 0` guard）確保上市初期空資料不會炸 runtime error。

```powerlanguage
if v_Daily_FastMA > v_Daily_SlowMA then v_Trend_OK = True else v_Trend_OK = False;

v_Daily_RSI_Sustained = True;
for hidx = 1 to Daily_RSI_Sustained_Bars begin
    if RSI( Close of Data3, Daily_RSI_Len )[hidx] <= Daily_RSI_Threshold then
        v_Daily_RSI_Sustained = False;
end;
if v_Daily_RSI_Sustained then v_RSI_OK = True else v_RSI_OK = False;

if v_Daily_Dist_Pct > Daily_Dist_MA20_Pct then v_Dist_OK = True else v_Dist_OK = False;

if v_Trend_OK and ( v_RSI_OK or v_Dist_OK ) then
    v_Regime_Watch = True
else
    v_Regime_Watch = False;
```

**做什麼**：拼出 D1 的「**A AND (B OR C)**」邏輯：
- A `v_Trend_OK`：MA20 > MA60（日線多頭結構）
- B `v_RSI_OK`：最近 `Daily_RSI_Sustained_Bars` 根 RSI 全部 > 70（過熱黏住）
- C `v_Dist_OK`：距 MA20 > 3%（過度延伸）
- 合成 `v_Regime_Watch`

**為什麼**：D1 採 MODERATE 版（最終預期每月 ~5 個 WATCH 日）。AND-A 必要條件防止下跌趨勢中誤判 pullback；OR-(B,C) 給 RSI 黏滯型 vs 短時暴衝型兩種過熱模式同樣的入場資格。

**Gotcha**：`for hidx = 1 to Daily_RSI_Sustained_Bars` 重用了 `hidx` 變數（Section 1B 同名變數）。PowerLanguage 允許 scope 重用，但需注意若未來新增「同根 K 棒先後使用 hidx」的邏輯，必須各自命名以免互相覆寫。

```powerlanguage
if v_Daily_Dist_Pct > HighConv_Threshold_Pct then
    v_HighConv_Active = True
else
    v_HighConv_Active = False;
```

**做什麼**：D8 旗標：距 MA20 > +5% 視為 HighConviction 區。

**為什麼**：v1.0 只記不動。v1.1 將以此 flag 動態調整 TP_Pct（dist 越大、回測幅度越深，可放寬 TP）。

---

### Section 3 — 5M Tier 2 Momentum Trigger（4-AND 動能觸發）

#### M1：連 N 根 5M 紅 K

```powerlanguage
v_Red_Loop_OK = True;
for v_red_idx = 0 to Consec_Red_Bars - 1 begin
    if Close[v_red_idx] >= Open[v_red_idx] then
        v_Red_Loop_OK = False;
end;
v_M1_Consec = v_Red_Loop_OK;
```

**做什麼**：迴圈檢查最近 `Consec_Red_Bars`（預設 3）根 5M K 棒**皆為紅**（Close < Open）。任一根綠就 break false。

**為什麼**：紅 K 連續是「賣壓持續、不是單一根噪音」的最基本訊號。3 根 (15 分鐘) 在 5M 時框是經典 momentum continuation 閘。

**Gotcha**：用 `>= Open` 判定非紅（含十字星），避免十字星被當紅 K 帶入。

#### M2：跌破 EMA5 且 EMA5 向下

```powerlanguage
v_5M_EMA      = XAverage( Close, EMA_Fast_Len );
v_5M_EMA_Prev = XAverage( Close, EMA_Fast_Len )[1];

if ( Close < v_5M_EMA ) and ( v_5M_EMA < v_5M_EMA_Prev ) then
    v_M2_BelowEMA = True
else
    v_M2_BelowEMA = False;
```

**做什麼**：兩個條件 AND——當前 Close 在 5M EMA5 下方、**且** EMA5 本根比前根低（slope < 0）。

**為什麼**：單純的「跌破 EMA」會被假突破騙；加上「EMA 本身在下彎」確認動能轉折已被均線吸收，是個典型 false-break filter。

**Gotcha**：`XAverage` 是 EMA 的 EasyLanguage 內建函數（非 SMA）。請勿改用 `Average` 否則 EMA5 變 SMA5，特性完全不同。

#### M3：ATR Spike（短期波動率突起）

```powerlanguage
v_5M_ATR_Short = AvgTrueRange( ATR_Short_Len );
v_5M_ATR_Long  = AvgTrueRange( ATR_Long_Len );

if ( v_5M_ATR_Long > 0 ) and
   ( v_5M_ATR_Short > v_5M_ATR_Long * ATR_Spike_Mult ) then
    v_M3_ATR_Spike = True
else
    v_M3_ATR_Spike = False;
```

**做什麼**：ATR(5) > ATR(20) × 1.3 → 短期波動率比中期高 30%。

**為什麼**：純動能策略最大的死穴是「死水盤動兩根就空進去」。ATR spike 確保此刻是 **有量的失速**，而非 chop。

**Gotcha**：`v_5M_ATR_Long > 0` 守衛避免上市最初幾根 K 沒足夠歷史時除零崩潰。

#### M4：Pullback 幾何位置 [0.5%, 1.5%]

```powerlanguage
if HighD(0) > 0 then
    v_Pullback_Pct = ( HighD(0) - Close ) / HighD(0) * 100
else
    v_Pullback_Pct = 0;

if ( v_Pullback_Pct >= Pullback_Min_Pct ) and
   ( v_Pullback_Pct <= Pullback_Max_Pct ) then
    v_M4_Pullback = True
else
    v_M4_Pullback = False;
```

**做什麼**：計算當前 Close 距「**當日盤中最高**」(`HighD(0)`) 的下跌百分比，必須落在 0.5% – 1.5% 之間。

**為什麼**：
- 太淺 (< 0.5%)：可能只是日內噪音，反彈失敗風險高、TP 空間擠在 SL 之內 = 不利 R:R。
- 太深 (> 1.5%)：第一波下殺可能已結束，後續多頭反撲容易掃停損。
- 0.5–1.5% 區段是「賣方剛主導完三根紅 K、買方還沒組織反擊」的最佳逆勢空點。

**對應決策**：D2 M4。

**Gotcha**：`HighD(0)` 是 EasyLanguage 內建函數，回傳「**當前 Data1 的當日最高**」。注意：跨夜後切到新交易日，`HighD(0)` 重置為新日盤中高點（與 Date 相關），所以 night session 期間的 HighD 是另一個值。

#### 4-AND 合成

```powerlanguage
if v_M1_Consec and v_M2_BelowEMA and v_M3_ATR_Spike and v_M4_Pullback then
    v_Trigger_Fired = True
else
    v_Trigger_Fired = False;

v_5M_EMA20 = XAverage( Close, TP_MA_Len );
```

**做什麼**：四個條件全 AND，並算出 D4 用的 5M EMA20。

**為什麼**：4 條件正交（連紅 K = price action / EMA = trend / ATR = volatility / 落點 = geometry），符合 **feedback_filter_redundancy_check.md**「filter 必須非 redundant」。預期年觸發 25–40 次。

---

### Section 4 — Same-Day Cooldown Reset（一日一單）

```powerlanguage
if Date <> v_LastSeenDate then begin
    v_DailyCooldown_Active = False;
    v_LastSeenDate         = Date;
end;
```

**做什麼**：當 `Date` 與上一根 K 棒的 `v_LastSeenDate` 不同（=進入新交易日），重置 cooldown。

**為什麼**：本策略設計為「**一日至多一單**」。原因有二：
1. Counter-trend short 連續觸發通常是「**一波多殺**」，第二次進場是在反彈中位置已差，邊際勝率劇降。
2. 風險預算限制：日內第二次空單會把當日曝險翻倍，破壞 3% 配置的風控前提。

**Gotcha**：MC 的「新 Date」對於跨日夜盤的判定要小心——夜盤 K 棒從 15:00 開始，但 MC 內部 Date 切換可能落在不同時點。對本策略影響低（cooldown 只是限制重複進場、不是核心風控），但若改為多日內多單版本需重新驗證 Date 切換時機。

---

### Section 5 — P3b Immediate Stop Guard / SetStopLoss（CLAUDE.md Rule #12）

```powerlanguage
v_SL_ATR = AvgTrueRange( SL_ATR_Len );

if MarketPosition >= 0 then
    SetStopLoss( v_SL_ATR * SL_ATR_Mult * BigPointValue );
```

**做什麼**：呼叫 MC 引擎層級的 `SetStopLoss`，距離 = ATR(14) × 4 × 200 (BigPointValue 點值)。

**為什麼**：
- **CLAUDE.md Rule #12 強制**：每隻策略必須含 P3b Immediate Stop Guard，原因是「進場成交瞬間 → 第一根自訂 stop 評估」之間的時間窗，若無 engine-level 兜底，IOG=false 設定下會出現「無保護視窗」。
- Short variant：`MarketPosition >= 0` 守衛（flat 或 long 時才設）。一旦空單成交，距離凍結於 signal-bar 的 ATR 值，不會隨後續 ATR 波動而漂移停損。
- **單一呼叫**：Rule #12 明文禁止重複 `SetStopLoss`，故全檔僅此一處。
- 距離公式必須與自訂 SL 共用同一個 anchor → 這裡 = `SL_ATR_Len` × `SL_ATR_Mult`，正是 D3 規格。

**Gotcha**：
- `BigPointValue` 對 TXF1 = 200（1 點 = 200 NTD）。若改商品需重設。
- 因為 Rule #12 規定「engine SL 已負責 SL」，Section 7 出場鏈中**故意沒有** `SellAtStop` / `BuyToCover ... stop` 的自訂 SL，以免雙重停損衝突。

---

### Section 6 — Entry Logic（多重 AND 進場閘）

```powerlanguage
if ( MarketPosition = 0 ) and
   ( v_Regime_Watch = True ) and
   ( v_Trigger_Fired = True ) and
   ( Time >= Entry_Open_Time ) and
   ( Time <= Entry_Cutoff_Time ) and
   ( v_DailyCooldown_Active = False ) and
   ( v_Holiday_Block = False ) and
   ( v_Settlement_Day = False ) and
   ( v_Registry_Expired = False ) then begin
    SellShort( "SE_RPS_Entry" ) next bar at Market;
    v_Entry_Bar = BarNumber;
end;
```

**做什麼**：8 條件 AND 成立 → 下根 K 棒以 Market 沽空，並記錄進場 BarNumber 供時間停損計算。

**為什麼每一條都要在**：

| 條件 | 為什麼 |
|------|--------|
| `MarketPosition = 0` | 必須空手才進，避免加碼 |
| `v_Regime_Watch` | D1 環境閘（多頭過熱）|
| `v_Trigger_Fired` | D2 動能閘（4-AND 確認失速）|
| `Time >= Entry_Open_Time AND Time <= Entry_Cutoff_Time` | D5 進場視窗 08:45–12:30 |
| `v_DailyCooldown_Active = False` | 一日一單限制 |
| `v_Holiday_Block = False` | 假日前夕禁進場（feedback_holiday_flatten_rule.md）|
| `v_Settlement_Day = False` | CLAUDE.md Rule #11 結算日全策略禁進場 |
| `v_Registry_Expired = False` | Registry 過期 = 環境未知，全 freeze |

**對應決策**：D5。

**Gotcha**：
- `Time >= 845 AND Time <= 1230` 是**閉區間配對**寫法（feedback_mc_time_24hr_pitfall.md），未使用裸露 `Time >= X`，避免跨日夜盤誤觸發。
- `next bar at Market` 表示市價單下一根 K 棒開盤成交，避免 IOG 衝突。
- `v_Entry_Bar = BarNumber` 是 **同一根 K 棒** 記錄（不等 next bar），供 Section 7 time stop 用作起點。注意此時實際成交尚未發生，但 BarNumber 紀錄已足夠估算「持倉根數」（誤差 1 根可接受）。

---

### Section 7 — Exit Chain（Priority 0 + 策略出場）

#### Priority 順序

```
P0-1  SX_RPS_Kill          Manual_Kill_Switch
P0-2  SX_RPS_RegistryEnd   v_Registry_Expired
P0-3  SX_RPS_HolFlat       v_Holiday_Block + Holiday_Flat_Time
P0-4  SX_RPS_Settlement    v_Settlement_Day + Settlement_Flat_Time
P0a   SX_RPS_DayClose      Daily_Flat_Time (13:25) ~ 1345
S-1   SX_RPS_TP            0.7% TP OR EMA20 觸及（D4）
S-2   SX_RPS_TimeStop      24 根 5M K（120 分）
（SL 由 Section 5 SetStopLoss 處理）
```

**為什麼用 ExitFired 互斥旗標**：MC 對同一根 K 棒、同一個 entry 標籤多次出場呼叫會產生未定義行為。`ExitFired = 0/1` 確保「**本根 K 一旦出場、後續所有出場條件全 short-circuit**」。

```powerlanguage
ExitFired = 0;

if MarketPosition = -1 then begin

    if ( ExitFired = 0 ) and ( Manual_Kill_Switch = True ) then begin
        BuyToCover( "SX_RPS_Kill" ) next bar at Market;
        ExitFired = 1;
    end;

    if ( ExitFired = 0 ) and ( v_Registry_Expired = True ) then begin
        BuyToCover( "SX_RPS_RegistryEnd" ) next bar at Market;
        ExitFired = 1;
    end;

    if ( ExitFired = 0 ) and
       ( v_Holiday_Block = True ) and
       ( Time >= Holiday_Flat_Time ) then begin
        BuyToCover( "SX_RPS_HolFlat" ) next bar at Market;
        ExitFired = 1;
    end;

    if ( ExitFired = 0 ) and
       ( v_Settlement_Day = True ) and
       ( Time >= Settlement_Flat_Time ) then begin
        BuyToCover( "SX_RPS_Settlement" ) next bar at Market;
        ExitFired = 1;
    end;

    if ( ExitFired = 0 ) and
       ( Time >= Daily_Flat_Time ) and
       ( Time <= 1345 ) then begin
        BuyToCover( "SX_RPS_DayClose" ) next bar at Market;
        ExitFired = 1;
    end;
```

**做什麼**：5 道 Priority 0 出場依序檢查，任一觸發即 BuyToCover 平倉並 set ExitFired=1。

**為什麼順序這樣排**：CLAUDE.md Rule #11 規定優先序為 **Kill > Registry > Holiday > Settlement > 原邏輯**：
- **Kill 最優先**：人工 override 一切（颱風臨停、ops 突發狀況）。
- **Registry 第二**：登錄表失效 = 未知環境，比 holiday 更嚴重。
- **Holiday 第三**：04:15 前必平倉，跨假持倉鐵律。
- **Settlement 第四**：12:30 (結算日 13:30 前 1 小時 buffer) 強制平倉。
- **DayClose 第五**：每個交易日 13:25 force flat，避免跨夜結算風險。

**閉區間審計**（feedback_mc_time_24hr_pitfall.md）：

| Time>=X 出現位置 | 是否安全 | 為什麼 |
|------------------|---------|--------|
| `Time >= Holiday_Flat_Time` | OK | guarded by `v_Holiday_Block`（僅 `Time<=500` 或 registry 過期時為真）|
| `Time >= Settlement_Flat_Time` | OK | guarded by `v_Settlement_Day`（日期條件）|
| `Time >= Daily_Flat_Time AND Time <= 1345` | OK | 顯式閉區間配對 |

無裸露 `Time>=X`，符合 24 小時制陷阱規範。

```powerlanguage
    if ExitFired = 0 then begin

        v_Bars_Held     = BarNumber - v_Entry_Bar;
        v_TP_Pct_Level  = EntryPrice * ( 1 - TP_Pct / 100 );
        v_TP_EMA20      = v_5M_EMA20;

        if ( Close <= v_TP_Pct_Level ) or
           ( ( TP_Use_EMA20_Backup = True ) and
             ( Close <= v_TP_EMA20 ) ) then begin
            BuyToCover( "SX_RPS_TP" ) next bar at Market;
            ExitFired = 1;
        end
        else if v_Bars_Held >= Max_Bars_TimeStop then begin
            BuyToCover( "SX_RPS_TimeStop" ) next bar at Market;
            ExitFired = 1;
        end;

    end;

end;
```

**做什麼**：策略級出場：
- `v_Bars_Held` = 持倉根數（BarNumber 相減）。
- `v_TP_Pct_Level` = EntryPrice × (1 − 0.7%)：空單 TP 在進場價下方。
- **TP 雙重觸發**：價格 ≤ 百分比 TP **OR**（D4 開關 ON 且 價格 ≤ 5M EMA20）→ 任一觸發即平倉。
- **Time Stop**：超過 24 根 5M（120 分鐘）→ 平倉。

**為什麼**：
- D3 BALANCED tier 的 TP 0.7% 設計 WR 52–58%，R:R 1.21。
- D4 EMA20 結構備援：若價格還沒達 0.7%、但已觸到 5M EMA20（中期均線），代表動能已被吸收，獲利出場勝過再等 → 「whichever fires first」原則。
- Time stop 120 分鐘：避免空單僵在原地、機會成本累積。24 根 = 5min × 24。

**Gotcha**：
- **沒有自訂 SL**：Rule #12 規定 SL 由 SetStopLoss 統一處理；這裡若加 `BuyToCover ... stop` 會雙重停損衝突。
- TP 條件用 `Close <= X`，是 5M K 棒收盤判定。實際成交在 next bar Market，會有 1 根 K 棒延遲（可能滑價）。
- EMA20 採當前根的 `v_5M_EMA20`（非 [1]），因為已是 5M 時框、bar 已收盤、可信。

---

### Section 8 — Cooldown Set on Exit

```powerlanguage
if ExitFired > 0 then begin
    v_DailyCooldown_Active = True;
    v_S3_LastExitDate      = Date;
end;
```

**做什麼**：本根有任何出場觸發 → 設 cooldown active、記錄出場日期。

**為什麼**：與 Section 4 配合形成「一日一單」閉環。出場後 cooldown 升起，當日剩餘時間內 Section 6 進場閘的 `v_DailyCooldown_Active = False` 條件就會擋住第二次進場；隔日 Section 4 偵測到 `Date` 改變後重置 cooldown。

**Gotcha**：`v_S3_LastExitDate` 在本版未被讀取（純診斷紀錄），但保留以便未來做「最近 N 日出場後冷靜期」之類擴充。

---

### Section 9 — Diagnostic Logging（D8 v1.0 logging-only）

```powerlanguage
if Log_HighConviction and v_HighConv_Active then begin
    if LastBarOnChart_Ex( 0 ) then
        Print( "S3 HighConv ", Date:8:0, " ", Time:4:0,
               " dist=", v_Daily_Dist_Pct:0:2, "%",
               " regime=", v_Regime_Watch,
               " trigger=", v_Trigger_Fired );
end;
```

**做什麼**：當日線距 MA20 > +5% 且 `Log_HighConviction = True`，在 MC Output Log 印一行診斷紀錄。

**為什麼**：D8 v1.0 採 **logging-only**（不改參數），目的為日後 v1.1 統計「HighConviction 區實際 trigger 率與勝率」是否值得擴大 TP_Pct。立刻動參數會混入未經實證的調整，所以分階段：v1.0 觀察、v1.1 sweep、v1.2 上線。

**Gotcha**：`LastBarOnChart_Ex(0)` 限制只在圖表最右一根才 print，避免回測時每根 K 棒灌爆 log。

---

## 三、Time-Safety 驗證表（檔尾 audit）

| Section | 行為 | 安全性 |
|---------|------|--------|
| 1B | `if Time <= 500` | 自帶上界、OK |
| 6 | `Time >= Entry_Open_Time AND Time <= Entry_Cutoff_Time` | 閉區間配對、OK |
| 7 P0-3 | `Time >= Holiday_Flat_Time` | guarded by `v_Holiday_Block` (Time<=500 或 registry expired)、OK |
| 7 P0-4 | `Time >= Settlement_Flat_Time` | guarded by `v_Settlement_Day` (date-scoped)、OK |
| 7 P0a | `Time >= Daily_Flat_Time AND Time <= 1345` | 閉區間配對、OK |

**結論**：無裸露 `Time >= X`，**未觸發 MC 24 小時制跨日陷阱**。

---

## 四、Inputs 完整清單

### Tier 1：Regime Gate（Daily, Data3）

| Input | 預設 | 優化範圍 | 用途 |
|-------|------|---------|------|
| Daily_FastMA_Len | 20 | 10..30 step 5 | 日線快 MA |
| Daily_SlowMA_Len | 60 | 40..120 step 10 | 日線慢 MA |
| Daily_RSI_Len | 14 | 7..21 step 7 | RSI 期數 |
| Daily_RSI_Threshold | 70 | 60..80 step 5 | RSI 過熱閾值 |
| Daily_RSI_Sustained_Bars | 2 | 1..3 step 1 | RSI 連續黏住根數 |
| Daily_Dist_MA20_Pct | 3.0 | 2..5 step 0.5 | 距 MA20 超漲閾值 (%) |

### Tier 2：Momentum Trigger（5M, Data1）

| Input | 預設 | 優化範圍 | 用途 |
|-------|------|---------|------|
| Consec_Red_Bars | 3 | 2..5 step 1 | M1 連紅根數 |
| EMA_Fast_Len | 5 | 5..10 step 1 | M2 快 EMA 期數 |
| ATR_Short_Len | 5 | 3..7 step 1 | M3 短 ATR |
| ATR_Long_Len | 20 | 15..30 step 5 | M3 長 ATR |
| ATR_Spike_Mult | 1.3 | 1.1..1.6 step 0.1 | M3 spike 倍率 |
| Pullback_Min_Pct | 0.5 | 0.3..0.7 step 0.1 | M4 回檔下界 (%) |
| Pullback_Max_Pct | 1.5 | 1.0..2.0 step 0.25 | M4 回檔上界 (%) |

### Exit 參數

| Input | 預設 | 優化範圍 | 用途 |
|-------|------|---------|------|
| TP_Pct | 0.7 | 0.5..1.0 step 0.1 | TP 百分比 |
| TP_Use_EMA20_Backup | True | — | D4 結構備援開關 |
| TP_MA_Len | 20 | 15..30 step 5 | 5M EMA20 期數 |
| SL_ATR_Len | 14 | 10..21 step 1 | SL ATR 期數 |
| SL_ATR_Mult | 4 | 3..6 step 0.5 | SL ATR 倍率 |
| Max_Bars_TimeStop | 24 | 18..36 | 時間停損 5M 根數 |
| Entry_Open_Time | 845 | — | D5 進場視窗開 |
| Entry_Cutoff_Time | 1230 | — | D5 進場視窗關 |
| Daily_Flat_Time | 1325 | — | 日盤強制平倉 |

### Priority 0 保護

| Input | 預設 | 用途 |
|-------|------|------|
| Holiday_Flat_Time | 415 | 假日前夕 04:15 平倉 |
| Registry_Valid_Until | 1270101 | Registry 有效到 2027/01/01 |
| Manual_Kill_Switch | False | 人工緊急停市開關 |
| Settlement_Flat_Time | 1230 | 結算日 12:30 平倉 |

### Diagnostic

| Input | 預設 | 用途 |
|-------|------|------|
| Log_HighConviction | True | D8 logging-only 開關 |
| HighConv_Threshold_Pct | 5.0 | D8 dist 閾值 (v1.1 sweep) |

**共 29 個 inputs**（全部 MC12 可優化）。

---

## 五、標籤完整清單

### 進場標籤
| 標籤 | 動作 | 觸發 |
|------|------|------|
| `SE_RPS_Entry` | SellShort | 8 條件 AND 全成立 |

### 出場標籤（7 個）
| 標籤 | 觸發 | Priority |
|------|------|----------|
| `SX_RPS_Kill` | Manual_Kill_Switch=true | P0-1 |
| `SX_RPS_RegistryEnd` | Date > Registry_Valid_Until | P0-2 |
| `SX_RPS_HolFlat` | Holiday tail + 04:15 | P0-3 |
| `SX_RPS_Settlement` | 結算日 + 12:30 | P0-4 |
| `SX_RPS_DayClose` | 13:25 force flat | P0a |
| `SX_RPS_TP` | 0.7% 或 EMA20 觸及 | S-1 |
| `SX_RPS_TimeStop` | 24 根 5M | S-2 |

**SL 由 SetStopLoss engine 處理，無顯式標籤**（MC 內部顯示為 "Stop"）。

**總計：1 進場 + 7 出場 = 8 個標籤**，全部符合 `SE_RPS_*` / `SX_RPS_*` 規範。

---

## 六、Constitution 合規檢查

| Rule | 內容 | 對應位置 | 通過 |
|------|------|---------|------|
| #3 | Data3 用 [1] 引用 | Section 2 全部 Data3 引用 | OK |
| #11 | Settlement_Flat 7 元素 | Section 1B + Section 7 P0-3/P0-4 | OK |
| #12 | P3b SetStopLoss 單一呼叫 | Section 5 | OK |
| #13 | 10-dim eval before live_simulation | 待 backtest 後 gate | 暫緩（research-tier） |
| Filter 重疊 | M1..M4 正交 | Section 3 4-AND | OK |
| 24 小時陷阱 | 閉區間 / state-guard | 檔尾 audit 表 | OK |
| 標籤前綴 | SE_/SX_ 嚴格區分 | Section 6 + Section 7 | OK |
| 假日鐵律 | 全 TXF1 策略休市前必平倉 | Section 0/1B/7-P0-3 | OK |
| 趨勢讓利潤奔跑 | 不適用（counter-trend） | — | N/A |

---

## 七、風險警告

1. **無回測**：v1.0 純研究稿，所有預期數字（WR 52–58%、R:R 1.21）為設計目標而非實證。
2. **5M Volume 已 drop**：M3 ATR spike 是唯一波動率代理，若 ATR 訊號失靈、可能流產率上升。需 ShowMe 驗證後在 v1.1 補回 volume confirmation。
3. **Counter-trend 結構性風險**：強趨勢日（gap up + 不回測）會觸發 4-AND 但被一路軋空。time stop 是最後防線、但仍可能吃完 SL。
4. **L4 退役後曝險替代**：S3 接 3% 額度，但 S3 觸發頻率（年 25–40 次）vs L4 黑天鵝捕捉次數差異很大，組合風險特性會改變。
5. **HighConviction 區數據尚未蒐集**：dist > +5% 的回測樣本是否足夠統計顯著，需 v1.0 跑完才知道。

---

## 八、後續 Phase 路線

### Phase 1（v1.0 已完成 2026-06-20）
- [x] Agent D 五路 deep research 合成 design spec v2
- [x] 用戶確認 8 項決策 + parameterization override
- [x] 撰寫 .pla（29 inputs、Rule #11 / #12 合規）
- [x] 撰寫本中文逐段註解

### Phase 2（待執行）
- [ ] MC ShowMe 五行驗證 TXF1 5M 成交量（D7 procedural step）
- [ ] MC12 載入 .pla 跑 2020/01/01 ~ 今 backtest
- [ ] 樣本 ≥ 100 筆檢核
- [ ] 三市況（牛/熊/震盪）PF > 1.0 檢核

### Phase 3（P1-P3 標準驗證）
- [ ] 參數敏感度（每個 input scan，找高原）
- [ ] Walk-Forward Analysis WFE > 50%
- [ ] Monte Carlo 95% MDD < 帳戶 30%
- [ ] 跨策略相關性 < 0.7（vs L1/L2/L3/L5/S1）

### Phase 4（晉升 live_simulation）
- [ ] 10 維機構級評估 ALL PASS（Rule #13）
- [ ] 移到 `strategies/live_simulation/`
- [ ] 註冊到 master verify 腳本
- [ ] MC12 模擬帳戶上架收 ≥ 30 筆樣本

### Phase 5 / v1.1（HighConviction sweep）
- [ ] D8 HighConv 區單獨統計勝率 / 平均回測幅度
- [ ] 若 HighConv 區回測幅度顯著 > 一般區 → TP_Pct 動態 modifier
- [ ] 補回 Volume 條件（若 ShowMe 驗證通過）

---

## 九、Glossary（變數名 → 中文對照）

### Inputs

| 變數 | 中文 |
|------|------|
| Daily_FastMA_Len | 日線快 MA 期數（預設 20） |
| Daily_SlowMA_Len | 日線慢 MA 期數（預設 60） |
| Daily_RSI_Len | 日線 RSI 期數（預設 14） |
| Daily_RSI_Threshold | RSI 過熱閾值（預設 70） |
| Daily_RSI_Sustained_Bars | RSI 連續超閾值根數（預設 2） |
| Daily_Dist_MA20_Pct | 距 MA20 過漲百分比（預設 3.0%） |
| Consec_Red_Bars | M1 連續紅 K 根數（預設 3） |
| EMA_Fast_Len | M2 快 EMA 期數（預設 5） |
| ATR_Short_Len | M3 短 ATR 期數（預設 5） |
| ATR_Long_Len | M3 長 ATR 期數（預設 20） |
| ATR_Spike_Mult | M3 ATR spike 倍率（預設 1.3） |
| Pullback_Min_Pct | M4 回檔下界百分比（預設 0.5%） |
| Pullback_Max_Pct | M4 回檔上界百分比（預設 1.5%） |
| TP_Pct | TP 百分比（預設 0.7%） |
| TP_Use_EMA20_Backup | D4 結構備援 TP 開關（預設 True） |
| TP_MA_Len | 5M EMA20 期數（預設 20） |
| SL_ATR_Len | SL ATR 期數（預設 14） |
| SL_ATR_Mult | SL ATR 倍率（預設 4） |
| Max_Bars_TimeStop | 時間停損 5M 根數（預設 24 = 120min） |
| Entry_Open_Time | 進場視窗開（預設 0845） |
| Entry_Cutoff_Time | 進場視窗關（預設 1230） |
| Daily_Flat_Time | 日盤強制平倉時間（預設 1325） |
| Holiday_Flat_Time | 假日前夕平倉時間（預設 0415） |
| Registry_Valid_Until | 假日 registry 有效日（預設 1270101） |
| Manual_Kill_Switch | 人工緊急停市開關（預設 False） |
| Settlement_Flat_Time | 結算日平倉時間（預設 1230） |
| Log_HighConviction | D8 HighConv 日誌開關（預設 True） |
| HighConv_Threshold_Pct | D8 HighConv 距 MA20 閾值（預設 5.0%） |

### 狀態變數（v_ 前綴）

| 變數 | 中文 |
|------|------|
| v_Daily_FastMA | 日線快 MA 值（取 [1] 已收盤） |
| v_Daily_SlowMA | 日線慢 MA 值（取 [1] 已收盤） |
| v_Daily_RSI | 日線 RSI 值（取 [1] 已收盤） |
| v_Daily_RSI_Sustained | RSI 連續 N 根皆超閾值（True/False） |
| v_Daily_Dist_Pct | 收盤距 MA20 百分比 |
| v_Trend_OK | D1 條件 A：MA20 > MA60（多頭結構） |
| v_RSI_OK | D1 條件 B：RSI 持續過熱 |
| v_Dist_OK | D1 條件 C：距 MA20 超漲 |
| v_Regime_Watch | D1 合成：A AND (B OR C) |
| v_M1_Consec | M1：連 N 根紅 K |
| v_M2_BelowEMA | M2：跌破 EMA5 且 EMA5 下彎 |
| v_M3_ATR_Spike | M3：ATR(5) > ATR(20)×1.3 |
| v_M4_Pullback | M4：回檔 0.5%–1.5% |
| v_5M_EMA | 5M EMA5 當前值 |
| v_5M_EMA_Prev | 5M EMA5 前一根值（判斜率） |
| v_5M_ATR_Short | 5M ATR(5) |
| v_5M_ATR_Long | 5M ATR(20) |
| v_Pullback_Pct | 當前 Close 距日內高的百分比 |
| v_Trigger_Fired | D2 合成：M1 AND M2 AND M3 AND M4 |
| v_Red_Loop_OK | M1 迴圈暫存（紅 K 全部通過 = True） |
| v_red_idx | M1 迴圈索引 |
| v_TP_Pct_Level | TP 百分比目標價（EntryPrice × (1 − TP_Pct/100)） |
| v_TP_EMA20 | TP D4 結構備援價（= v_5M_EMA20） |
| v_5M_EMA20 | 5M EMA20 當前值 |
| v_SL_ATR | SL ATR 當前值（用於 SetStopLoss 距離） |
| v_Bars_Held | 持倉根數（BarNumber − v_Entry_Bar） |
| v_Entry_Bar | 進場 BarNumber 紀錄 |
| v_S3_LastExitDate | 最近出場日期（診斷用） |
| v_DailyCooldown_Active | 當日已出場、不再進場 |
| v_LastSeenDate | 上一根 K 的 Date（用於偵測新交易日） |
| v_Holiday_Block | 假日 tail bar 旗標 |
| v_Registry_Expired | Registry 過期旗標 |
| v_Settlement_Day | 結算日旗標（每月第三個禮拜三） |
| Registry_Warn_ID | Registry 過期紅字 Text ID |
| hidx | 通用迴圈索引（Section 1B / Section 2 共用） |
| ExitFired | 本根 K 是否已有出場（互斥旗標） |
| v_HighConv_Active | D8 HighConviction 區旗標 |

### MC 內建函數 / 常數

| 名稱 | 中文 |
|------|------|
| `Average(price, len)` | SMA |
| `XAverage(price, len)` | EMA |
| `AvgTrueRange(len)` | ATR |
| `RSI(price, len)` | RSI |
| `HighD(0)` | 當日盤中最高 |
| `Date` | 當前 K 棒日期（YYYMMDD 民國年 + 月日，如 1260620）|
| `Time` | 當前 K 棒時間（HHMM）|
| `DayOfWeek(Date)` | 星期幾（0=Sun, 1=Mon, ..., 3=Wed）|
| `DayOfMonth(Date)` | 月內第幾日 |
| `DateToJulian(Date)` | 轉 Julian day（便於日期算術）|
| `BarNumber` | 當前 K 棒序號 |
| `MarketPosition` | 部位狀態（−1=Short, 0=Flat, +1=Long）|
| `EntryPrice` | 最近一次進場價 |
| `BigPointValue` | 每點價值（TXF1 = 200）|
| `LastBarOnChart` | 是否為圖表最右一根 |
| `LastBarOnChart_Ex(0)` | 進階版 LastBarOnChart |

---

## 十、相關文件

- [策略本身](S3_RapidPullbackShort.pla)
- [設計規格 v2](S3_PullbackShort_design_spec_v2.md)
- [策略總則](../README.md)
- [Settlement 憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [P3b Immediate Stop Guard 設計](../../../docs/P3b_immediate_stop_guard_design_20260618.md)
- [機構級 10 維風險框架](../../../docs/institutional_risk_framework_20260619.md)
- [S2 InsideBarBreak 註解（風格參照）](../S02_InsideBarBreak/S2_InsideBarBreak_annotated.md)
