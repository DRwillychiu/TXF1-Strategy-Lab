# S3 RapidPullbackShort v1.1 — 中文逐段註解

**MC Load Name**：`STRATEGY_GEN_S3_RapidPullbackShort`（v1.1 #15 起補上 `S3_` infix）
**版本**：v1.1（13 項稽核 bug 修補，2026-06-19），承襲 v1.0.1 三項預發布封鎖修正
**檔案**：[`S3_RapidPullbackShort.pla`](S3_RapidPullbackShort.pla)
**設計規格**：[`S3_PullbackShort_design_spec_v2.md`](S3_PullbackShort_design_spec_v2.md)
**標籤前綴**：`SE_RPS_` (Short Entry)、`SX_RPS_` (Short Exit)
**配置額度**：3%（取代退役的 L4 名額；v3 配置 L1:29 L2:22 L3:10 L5:16 S1:20 **S3:3** = 100%）

---

## v1.1 修補總表（13 項）

承襲 v1.0.1（已修 LastBarOnChart_Ex 編譯封鎖、RSI[1] Data1/Data3 索引錯位、RSI[hidx] sustained 迴圈三項封鎖），本版再補：

| # | 嚴重度 | 一句話描述 | 對應 Section |
|---|--------|-----------|--------------|
| #1 | HIGH | EMA20 備援 TP 加 3 道守衛（MinBars + EMA20[1] + Close[1] 跨越），破解 fill-bar trap | 7 TP block |
| #2 | HIGH | 假日封鎖改 `Time < 500`（嚴格小於）+ P0-3 補 `Time <= 455` 顯式上界 | 1B + 7 P0-3 |
| #3 | HIGH | `Daily_Flat_Time` 上界改 1340（原 1345），避免成交跳到 15:00 夜盤開盤 | 7 P0a |
| #4 | HIGH | `HighD(0)` 夜盤污染改以 `v_DaySess_High` 自行累計（每新 Date + Entry_Open_Time 重置） | 3 M4 |
| #5 | MED | `v_Entry_Bar` 手動計數器移除，改用 `BarsSinceEntry` 內建，消除 +1 偏移 | 6 + 7 |
| #6 | MED | `Holiday_Flat_Time` 改 245（原 415），對齊 design_spec_v2 §5.2/§5.3 的 27 次重試窗 | 1 inputs |
| #7 | MED | `( Close of Data3 )[1]` 顯式括號，移除 Data1/Data3 綁定歧義 | 2 Data3 距離 |
| #8 | MED | Cooldown 重置與 RSI snapshot shift 切割：snapshot 走曆日轉換，cooldown 走日盤開 | 4 |
| #9 | MED | `XAverage` 去重：單次呼叫 + `v_5M_EMA[1]` 回看，取代兩條平行 function-series | 3 M2 |
| #10 | MED | 新增 Frozen SL 三件套（5a 凍結 + 5b SetStopLoss 共用凍結 ATR + 7 SX_RPS_SL 兜底） | 5a/5b + 7 |
| #11 | LOW | `v_S3_LastExitDate` dead-state 移除（從未被讀取） | 8 |
| #15 | LOW | MC Load Name 補 `S3_` infix → `STRATEGY_GEN_S3_RapidPullbackShort` | 檔頭 |
| #16 | LOW | `Entry_Open_Time` 改 850（原 845），MC 5M K 棒以收盤時間打 stamp，Time=845 不存在 | 1 inputs |

**未採用的修補**（刻意留存，已記於檔尾）：
- #12 Data2 未用：保留三 feed 圖表結構供 v1.1 MFE 模組使用。
- #13 迴圈 `1..80`：與 L1-L5 byte-identical invariant，不動。
- #14 Section 重編號：高擾動、零 runtime 效益。

---

## 〇、策略本質

### 0.1 賺什麼錢

**逆勢空單，獵殺過熱的多頭日內回檔**（counter-trend short on overheated bull pullback）。

```
多頭高估狀態（Daily Regime Watch）
 + 5M 動能急轉（4-AND momentum trigger）
 ──→ 沽空，賺 ~0.7% 回測幅度
```

**核心假設**：當日線結構偏多但出現過熱（RSI 高檔黏住 / 偏離 MA20 過大),盤中第一波明確失速（連 3 紅 + EMA 跌破 + ATR spike + 落點剛好的回檔）通常會延伸 60–120 分鐘的回測,足夠收 0.7% 利差。

### 0.2 為什麼會有 alpha

| 結構 | 反映的市場行為 |
|------|---------------|
| **Tier 1 Daily Regime（A AND (B OR C)）** | 只在「多頭已過熱」的環境出手,避開單純做空趨勢的死亡螺旋 |
| **Tier 2 5M 4-AND Trigger** | 4 個正交條件（連紅 / MA 結構 / 波動率 / 幾何位置）同時觸發,將胡亂空頭轉為「失速確認」 |
| **Pullback 落點 [0.5%, 1.5%]** | 太淺 = 噪音、太深 = 反彈空間有限。卡在「賣家剛要交棒、買家還沒接到位」的甜蜜區 |
| **0.7% TP / 0.58% SL / 120min 時間停損** | R:R 1.21、設計 WR 52–58%、避免過夜結算風險 |

### 0.3 為什麼這次設計把 Volume 拿掉

**S2 v0.4 教訓**：TXF1 5M 成交量序列尚未經 MC ShowMe 五行驗證,盲加 Volume filter 等於賭資料完整性。本版 v1.0 採 D7 程序保護:volume 條件留待 ShowMe 驗證後在 v1.1 重新評估。

---

## 一、Design Decisions 對照表（D1–D8）

| 編號 | 決策 | 採用版本 | 程式對應 |
|------|------|---------|----------|
| D1 | Regime Gate | **MODERATE**:A AND (B OR C) | Section 2 → `v_Regime_Watch` |
| D2 | Momentum Trigger | **BALANCED 4-AND**（無 Volume）| Section 3 → `v_Trigger_Fired` |
| D3 | Exit Tier | **BALANCED**:TP 0.7% / SL ATR×4 / Time 120min | Section 5a/5b (SL) + Section 7 |
| D4 | TP 結構備援 | INCLUDE **5M EMA20 觸及**（v1.1 加 3 道守衛）| `TP_Use_EMA20_Backup` + `TP_EMA20_MinBars` + Section 7 TP block |
| D5 | Entry Window | **08:50 – 12:30**（v1.1 #16 修正 stamp）| `Entry_Open_Time` / `Entry_Cutoff_Time` |
| D6 | L4 處置 | **退役 L4,S3 接 3% 額度** | （allocation 文件,非本檔程式碼）|
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

**做什麼**:在 `CurrentBar = 1` 一次性初始化 63 筆假日「尾巴」日期。`Holiday_Tail` 定義為「**最後交易日 +1 個曆日**」 = 連假前夕夜盤的 00:00–05:00 那段 tail bar 所掛上的日期。

**為什麼**:MC 把跨日夜盤 K 棒的 `Date` 印成「下一個交易日」,所以在偵測「假日前夕夜盤」時必須抓的不是 holiday 本身,而是 holiday tail 那組日期。此邏輯與 L1/L2/L3/L5 共用同一份 63 筆 byte-identical registry（feedback_holiday_flatten_rule.md「以期交所官方行事曆為唯一準據」）。

**對應決策**:CLAUDE.md Rule #11 Settlement_Flat 7 元素之一。

**Gotcha**:
- 帶 `*` 標記的列（如 `1240501` Labor Day）為待覆核項目,每 Q4 必須對照 TAIFEX 116 年行事曆重建。
- `Registry_Valid_Until = 1270101` 代表這份 registry 只到 2027 元旦前;超過會觸發 `v_Registry_Expired = True` 並 force-flat。

---

### Section 1B — Holiday / Registry / Settlement Detection（保護狀態旗標）

```powerlanguage
v_Holiday_Block = False;

{ BUG FIX v1.1 #2: strict < 500 }
if Time < 500 then begin
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

**做什麼**:每根 K 棒重置三個保護旗標:
1. `v_Holiday_Block`:當 `Time < 500`（嚴格小於 5 點 tail bar 時段）且 `Date` 命中 registry,則升旗。
2. `v_Registry_Expired`:超過 registry 截止日就升旗,並連帶把 `v_Holiday_Block` 也升起,達成「未知環境 = 全面 freeze」的兜底。
3. `v_Settlement_Day`:每月第三個禮拜三（DayOfWeek=3 且 DayOfMonth 落在 15–21 之間的唯一星期三）。

**v1.1 #2 修正細節（為什麼 `< 500` 而非 `<= 500`）**:
- 原 `Time <= 500` 在 `Time = 500`（最後一根夜盤 tail bar）仍會把 `v_Holiday_Block` 升起,觸發 P0-3 BuyToCover next bar at Market。但此後夜盤已收,下一根 K 棒就是 **連假後重新開盤**,中間可能跨 3+ 個曆日。
- 改成嚴格小於,讓最後一根 tail bar 不再升旗,符合 S1 v2.3 的架構鐵律:Priority 0 出場不允許跨 session gap 成交。
- 並於 Section 7 P0-3 補上 `Time <= 455` 作為 belt-and-suspenders,即使未來有人誤把 `< 500` 改回 `<= 500`,P0-3 自己也擋得住。

**為什麼**:
- `Time < 500` 是「**閉區間天然上界**」(`Time < 500` 本身就把區間封死),因此 24 小時制陷阱（feedback_mc_time_24hr_pitfall.md）在這裡不會發生。
- 把保護旗標統一在進場 / 出場前計算,可讓後續所有 `Time >= X` 條件都被 state-guard 抓住（避免「裸露 Time>=X」）。

**Gotcha**:迴圈跑 `for hidx = 1 to 80`,但 registry 只填到 63 ,剩下 17 格固定為 0;`Date = 0` 永遠 false 不會誤觸發,這是刻意預留擴充空間。

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

**做什麼**:在圖表上印出紅色警告字,提醒「registry 30 日內到期,請從 TAIFEX 行事曆重建」。`Registry_Warn_ID < 0` 守衛防止重複貼字。

**為什麼**:避免 registry 默默過期造成 v_Registry_Expired 連環觸發後策略全面停擺卻無人察覺。視覺警告 = 運維最後一道防線。

---

### Section 2 — Daily Tier 1 Calculations（日線環境閘）

```powerlanguage
v_Daily_FastMA = Average( Close, Daily_FastMA_Len )[1] of Data3;
v_Daily_SlowMA = Average( Close, Daily_SlowMA_Len )[1] of Data3;
{ BUG FIX v1.0.1: snapshot-based, no longer inline RSI(...)[1] }
v_Daily_RSI    = v_Daily_RSI_Snap0;
```

**做什麼**:從 Data3（日線）取已收盤 `[1]` 值計算 MA20、MA60;RSI 改採 Section 4 維護的 snapshot（v1.0.1 修正）。

**為什麼**:**CLAUDE.md Rule #3 強制**「Data3 當根可能為部分 bar,必須引用 `[1]` 已收盤值」。RSI 原本同樣用 `RSI(...)[1]` 但 `[1]` 在多 data 環境會被 parser 綁到 Data1 的 5M 偏移,造成同日內 `[1]..[N]` 全部塌成今日值,sustained 檢查失效;v1.0.1 改用 snapshot 是徹底解法。

```powerlanguage
{ BUG FIX v1.1 #7: explicit parentheses bind 'of Data3' first }
if v_Daily_FastMA > 0 then
    v_Daily_Dist_Pct = ( ( Close of Data3 )[1] - v_Daily_FastMA ) /
                       v_Daily_FastMA * 100
else
    v_Daily_Dist_Pct = 0;
```

**做什麼**:計算「昨日收盤距 MA20 的百分比距離」。正值 = 收盤在 MA20 之上。

**v1.1 #7 修正細節**:外層多一層括號 `( Close of Data3 )[1]`,強制 parser 先把 `of Data3` 與 `Close` 綁定,再把 `[1]` history 套到「Data3-bound 表達式」。原寫法 `Close of Data3[1]` 在不同 PowerLanguage parser 版本可能會把 `[1]` 綁到 Data1 的 5M 偏移,讓 dist 變成「日線 MA20 與 5M 前一根 5M Close 的差」,徹底是噪音。

**為什麼**:D1 condition C「距離 MA20 > +3%」之數值來源。除 0 防護（`> 0` guard）確保上市初期空資料不會炸 runtime error。

```powerlanguage
if v_Daily_FastMA > v_Daily_SlowMA then v_Trend_OK = True else v_Trend_OK = False;

{ Daily RSI sustained: snapshot-based (v1.0.1 fix) }
v_Daily_RSI_Sustained = True;
if Daily_RSI_Sustained_Bars >= 1 and v_Daily_RSI_Snap0 <= Daily_RSI_Threshold then
    v_Daily_RSI_Sustained = False;
if Daily_RSI_Sustained_Bars >= 2 and v_Daily_RSI_Snap1 <= Daily_RSI_Threshold then
    v_Daily_RSI_Sustained = False;
if Daily_RSI_Sustained_Bars >= 3 and v_Daily_RSI_Snap2 <= Daily_RSI_Threshold then
    v_Daily_RSI_Sustained = False;
if Daily_RSI_Sustained_Bars >= 4 and v_Daily_RSI_Snap3 <= Daily_RSI_Threshold then
    v_Daily_RSI_Sustained = False;
if v_Daily_RSI_Sustained then v_RSI_OK = True else v_RSI_OK = False;

if v_Daily_Dist_Pct > Daily_Dist_MA20_Pct then v_Dist_OK = True else v_Dist_OK = False;

if v_Trend_OK and ( v_RSI_OK or v_Dist_OK ) then v_Regime_Watch = True
else v_Regime_Watch = False;
```

**做什麼**:拼出 D1 的「**A AND (B OR C)**」邏輯:
- A `v_Trend_OK`:MA20 > MA60（日線多頭結構）
- B `v_RSI_OK`:最近 `Daily_RSI_Sustained_Bars` 根 RSI **snapshot** 全部 > 70（過熱黏住）
- C `v_Dist_OK`:距 MA20 > 3%（過度延伸）
- 合成 `v_Regime_Watch`

**為什麼**:D1 採 MODERATE 版（最終預期每月 ~5 個 WATCH 日）。AND-A 必要條件防止下跌趨勢中誤判 pullback;OR-(B,C) 給 RSI 黏滯型 vs 短時暴衝型兩種過熱模式同樣的入場資格。

**Gotcha**:Sustained 已展開為 1..4 的明文 if 串而非迴圈,因為 snapshot 上限 = 4(超過必須擴 Snap4..);若 optimization sweep 需要 > 4 根 sustained,須先擴 snapshot 變數與 Section 4 shift 邏輯。

```powerlanguage
if v_Daily_Dist_Pct > HighConv_Threshold_Pct then v_HighConv_Active = True
else v_HighConv_Active = False;
```

**做什麼**:D8 旗標:距 MA20 > +5% 視為 HighConviction 區。

**為什麼**:v1.0 只記不動。v1.1 將以此 flag 動態調整 TP_Pct(dist 越大、回測幅度越深,可放寬 TP)。

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

**做什麼**:迴圈檢查最近 `Consec_Red_Bars`（預設 3）根 5M K 棒**皆為紅**（Close < Open）。任一根綠就 break false。

**為什麼**:紅 K 連續是「賣壓持續、不是單一根噪音」的最基本訊號。3 根 (15 分鐘) 在 5M 時框是經典 momentum continuation 閘。

**Gotcha**:用 `>= Open` 判定非紅（含十字星）,避免十字星被當紅 K 帶入。

#### M2：跌破 EMA5 且 EMA5 向下（v1.1 #9 修正）

```powerlanguage
{ BUG FIX v1.1 #9: one XAverage call + variable[1] }
v_5M_EMA      = XAverage( Close, EMA_Fast_Len );
v_5M_EMA_Prev = v_5M_EMA[1];

if ( Close < v_5M_EMA ) and ( v_5M_EMA < v_5M_EMA_Prev ) then
    v_M2_BelowEMA = True
else
    v_M2_BelowEMA = False;
```

**做什麼**:兩個條件 AND——當前 Close 在 5M EMA5 下方、**且** EMA5 本根比前根低（slope < 0）。

**v1.1 #9 修正細節**:原 v1.0 寫 `v_5M_EMA_Prev = XAverage( Close, EMA_Fast_Len )[1]`,在 PowerLanguage 內等於「**第二條獨立的 EMA function-series instance**」,雖然數學上 `[1]` 取前根,但 MC 內部會維護兩條平行的 EMA 計算序列,佔額外記憶體並可能在 IOG/非 IOG 切換時出現微小數值漂移。標準 idiom 是「**single call + variable lookback**」:用第一條 EMA 變數的 `[1]` 直接抓上一根,語意一致、零冗餘 series。

**為什麼**:單純的「跌破 EMA」會被假突破騙;加上「EMA 本身在下彎」確認動能轉折已被均線吸收,是個典型 false-break filter。

**Gotcha**:`XAverage` 是 EMA 的 EasyLanguage 內建函數（非 SMA）。請勿改用 `Average` 否則 EMA5 變 SMA5,特性完全不同。

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

**做什麼**:ATR(5) > ATR(20) × 1.3 → 短期波動率比中期高 30%。

**為什麼**:純動能策略最大的死穴是「死水盤動兩根就空進去」。ATR spike 確保此刻是 **有量的失速**,而非 chop。

**Gotcha**:`v_5M_ATR_Long > 0` 守衛避免上市最初幾根 K 沒足夠歷史時除零崩潰。

#### M4：Pullback 幾何位置 [0.5%, 1.5%]（v1.1 #4 重寫）

```powerlanguage
{ BUG FIX v1.1 #4: day-session-only intraday high, no HighD(0) contamination }
if ( Date <> v_DaySess_HighDate ) and ( Time >= Entry_Open_Time ) then begin
    v_DaySess_High     = High;
    v_DaySess_HighDate = Date;
end
else if ( Date = v_DaySess_HighDate ) and
        ( Time >= Entry_Open_Time ) and ( Time <= 1345 ) then begin
    if High > v_DaySess_High then
        v_DaySess_High = High;
end;

if v_DaySess_High > 0 then
    v_Pullback_Pct = ( v_DaySess_High - Close ) / v_DaySess_High * 100
else
    v_Pullback_Pct = 0;

if ( v_Pullback_Pct >= Pullback_Min_Pct ) and
   ( v_Pullback_Pct <= Pullback_Max_Pct ) then
    v_M4_Pullback = True
else
    v_M4_Pullback = False;
```

**做什麼**:計算當前 Close 距「**當日盤中最高**」(`v_DaySess_High`) 的下跌百分比,必須落在 0.5% – 1.5% 之間。

**v1.1 #4 修正細節 — 為什麼丟掉 `HighD(0)`**:
- `HighD(0)` 是 EasyLanguage 內建,語意上「Data1 當前 Date 的最高」,但 MC 對 TXF1 5M 序列的 **Date 是 calendar-date-scoped**——夜盤 00:00–05:00 那段 tail bar 已經掛上「**下一個交易日的 Date**」。
- 結果是:當日盤 08:50 第一根 K 棒讀 `HighD(0)`,讀到的並非當日盤的最高,而是「**昨夜夜盤 00:00–05:00 那段 tail bar 的高 + 今日盤 08:45 開盤後到此刻的高**」混合值。
- 在強勢上漲日,夜盤 tail 高常常 > 日盤 08:50 開盤後幾根的高,導致 `v_Pullback_Pct` 被「假高」拉到 1.5% 之外,M4 永遠 false,4-AND 永遠不觸發。
- 修法:**自行維護 `v_DaySess_High`**,在「曆日改變且 Time 進入日盤開」的瞬間以當根 High 重置,之後每根 K 棒只在「日盤時段內」更新最大值;`v_DaySess_HighDate` 守住「每個 Date 只重置一次」。
- 副作用:讀數可信度提升,但要求 backtest 必須有 Section 4 之外的 day-session 進度資料(若 chart 只 load Daily 是不夠的)。

**為什麼**:
- 太淺 (< 0.5%):可能只是日內噪音,反彈失敗風險高、TP 空間擠在 SL 之內 = 不利 R:R。
- 太深 (> 1.5%):第一波下殺可能已結束,後續多頭反撲容易掃停損。
- 0.5–1.5% 區段是「賣方剛主導完三根紅 K、買方還沒組織反擊」的最佳逆勢空點。

**對應決策**:D2 M4。

#### 4-AND 合成

```powerlanguage
if v_M1_Consec and v_M2_BelowEMA and v_M3_ATR_Spike and v_M4_Pullback then
    v_Trigger_Fired = True
else
    v_Trigger_Fired = False;

v_5M_EMA20 = XAverage( Close, TP_MA_Len );
```

**做什麼**:四個條件全 AND,並算出 D4 用的 5M EMA20。

**為什麼**:4 條件正交(連紅 K = price action / EMA = trend / ATR = volatility / 落點 = geometry),符合 **feedback_filter_redundancy_check.md**「filter 必須非 redundant」。預期年觸發 25–40 次。

---

### Section 4 — Same-Day Cooldown Reset + RSI Snapshot Shift（v1.1 #8 切割雙節奏）

```powerlanguage
if Date <> v_LastSeenDate then begin
    { Snapshot shift: always on calendar-date rollover }
    v_Daily_RSI_Snap3 = v_Daily_RSI_Snap2;
    v_Daily_RSI_Snap2 = v_Daily_RSI_Snap1;
    v_Daily_RSI_Snap1 = v_Daily_RSI_Snap0;
    v_Daily_RSI_Snap0 = RSI( Close, Daily_RSI_Len ) of Data3;

    { Cooldown reset: gated by day-session open }
    if Time >= Entry_Open_Time then begin
        v_DailyCooldown_Active = False;
        v_LastSeenDate         = Date;
    end;
end;
```

**做什麼**:當 `Date` 與上一根 K 棒的 `v_LastSeenDate` 不同(=進入新交易日),分兩件事處理:
1. **RSI snapshot shift**:Snap3 ← Snap2 ← Snap1 ← Snap0,Snap0 重抓 Data3 最新 RSI。**無條件執行**,跟著 Daily bar close 的曆日節奏走。
2. **Cooldown 重置 + LastSeenDate 更新**:**僅在 `Time >= Entry_Open_Time` 時** 才執行。

**v1.1 #8 切割細節 — 為什麼兩件事節奏不同**:
- **RSI snapshot 的自然節奏 = Daily bar close = 曆日轉換**。Daily Data3 在 00:00 完成「昨日 bar 收盤」,任何 5M K 棒一旦看到 `Date` 改變(通常在夜盤 00:00 那根)就該立即拉新值,Tier 1 計算才有最新 RSI 可用。
- **Cooldown 重置的自然節奏 = 日盤開盤 (Entry_Open_Time)**。本策略 D5 進場視窗 08:50–12:30,夜盤完全不進場;若 cooldown 在 00:00 就解除,而 `Entry_Open_Time` 被優化器 sweep 下調(例如試 0500),會出現「夜盤偷溜進場」的破窗。
- 若兩件事擠在同一個 `if Date <> v_LastSeenDate` 分支裡共用一條 LastSeenDate 鎖,snapshot 會被「等到 Time >= Entry_Open_Time」延後 8 小時,讓 Tier 1 在夜盤算 RSI 用的是過時 Snap0;反過來把 LastSeenDate 提前在 00:00 更新,則 cooldown 也跟著提早,破窗風險回來。
- **解法**:snapshot shift 不用 LastSeenDate 鎖,純走 `Date <> v_LastSeenDate` 入口;cooldown 與 LastSeenDate 更新一起放在內層 `Time >= Entry_Open_Time` 守衛裡。兩個節奏各自運作,不互卡。

**為什麼本策略設計為一日至多一單**:
1. Counter-trend short 連續觸發通常是「**一波多殺**」,第二次進場是在反彈中位置已差,邊際勝率劇降。
2. 風險預算限制:日內第二次空單會把當日曝險翻倍,破壞 3% 配置的風控前提。

**Gotcha**:Snap0 取值用 `RSI( Close, Daily_RSI_Len ) of Data3`(無 `[1]`),因為「曆日已轉換」=「昨日 Daily bar 已收盤」=「Data3 當前 bar 就是已收盤值」,不需再 `[1]`。

---

### Section 5a + 5b — Frozen SL + SetStopLoss（v1.1 #10 belt-and-suspenders / CLAUDE.md Rule #12）

```powerlanguage
{ ---- 5a: Frozen SL setup (locks once per trade on entry bar) ---- }
if MarketPosition = -1 then begin
    if v_SL_Locked = False then begin
        v_Frozen_ATR_5M  = AvgTrueRange( SL_ATR_Len );
        v_Frozen_SL_Dist = v_Frozen_ATR_5M * SL_ATR_Mult;
        v_SL_Level       = EntryPrice + v_Frozen_SL_Dist;
        v_SL_Locked      = True;
    end;
end
else begin
    v_SL_Locked      = False;
    v_Frozen_ATR_5M  = 0;
    v_Frozen_SL_Dist = 0;
    v_SL_Level       = 0;
end;

{ ---- 5b: P3b SetStopLoss engine guard (shares frozen ATR once locked) ---- }
if v_SL_Locked = True then
    v_SL_ATR = v_Frozen_ATR_5M
else
    v_SL_ATR = AvgTrueRange( SL_ATR_Len );

if MarketPosition >= 0 then
    SetStopLoss( v_SL_ATR * SL_ATR_Mult * BigPointValue );
```

**做什麼(雙層架構)**:
- **5a Frozen SL**:成交瞬間(MP 從 0 變 -1 第一根)把 ATR、距離、停損價位三件事鎖死於 `v_Frozen_ATR_5M / v_Frozen_SL_Dist / v_SL_Level`。在 MP=0 或 MP=+1 時把它們全部清零並把 `v_SL_Locked` 設 False。
- **5b SetStopLoss**:呼叫 MC 引擎層級的 `SetStopLoss`,距離若已 lock 則用凍結 ATR,否則用即時 ATR;進場前後距離不會漂移。
- **配合 Section 7 SX_RPS_SL**:Section 7 用 `BuyToCover ... v_SL_Level Stop` 做 bar-level 兜底,組成 belt-and-suspenders。

**v1.1 #10 修正細節 — 為什麼三層**:
- 原 v1.0 只有 `SetStopLoss`,但 MC 對 `SetStopLoss` 在某些版本 / 某些 IOG 設定下會有 1 根 K 棒的延遲評估,L1-L5 實證有過「SL 在進場根後 1-2 根才生效」的個案。
- L1-L5 後來統一升級成「**Frozen ATR + SetStopLoss + SX_*_SL bar-level Stop**」三件套,S3 v1.1 跟進,確保 SL 在 fill bar 就有 bar-level Stop 可觸發。
- 短策略 anchor 公式:`v_SL_Level = EntryPrice + v_Frozen_SL_Dist`(空單停損在進場價**上方**)。

**為什麼**:
- **CLAUDE.md Rule #12 強制**:每隻策略必須含 P3b Immediate Stop Guard,原因是「進場成交瞬間 → 第一根自訂 stop 評估」之間的時間窗,若無 engine-level 兜底,IOG=false 設定下會出現「無保護視窗」。
- Short variant:`MarketPosition >= 0` 守衛(flat 或 long 時才設)。一旦空單成交,距離凍結於 signal-bar 的 ATR 值,不會隨後續 ATR 波動而漂移停損。
- **單一呼叫**:Rule #12 明文禁止重複 `SetStopLoss`,故全檔僅此一處。
- 距離公式必須與自訂 SL 共用同一個 anchor → 這裡 = `SL_ATR_Len` × `SL_ATR_Mult`,正是 D3 規格。

**Gotcha**:
- `BigPointValue` 對 TXF1 = 200(1 點 = 200 NTD)。若改商品需重設。
- Section 7 SX_RPS_SL 是 bar-level `BuyToCover at v_SL_Level Stop`,與 5b 的 `SetStopLoss` 共用同一條 frozen ATR 計算的 SL 距離,**故意冗餘**(belt-and-suspenders),不會雙重停損衝突(MC 引擎會擇先觸發者結算)。

---

### Section 6 — Entry Logic（v1.1 #5 移除 v_Entry_Bar)

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
    { BUG FIX v1.1 #5: manual entry-bar counter removed, BarsSinceEntry used in Section 7 }
    SellShort( "SE_RPS_Entry" ) next bar at Market;
end;
```

**做什麼**:8 條件 AND 成立 → 下根 K 棒以 Market 沽空。

**v1.1 #5 修正細節 — 為什麼移除 `v_Entry_Bar = BarNumber`**:
- 原 v1.0 在進場條件成立同根 K 棒記 `v_Entry_Bar = BarNumber`,然後 Section 7 用 `v_Bars_Held = BarNumber - v_Entry_Bar` 算持倉根數。
- 問題:**「進場條件成立」與「實際成交」差 1 根**(`next bar at Market`)。`v_Entry_Bar` 記的是條件根,實際成交在下一根,造成 `v_Bars_Held` 從 day 1 就比真實值多 1。
- 影響:`v_Bars_Held >= Max_Bars_TimeStop` 提前 1 根觸發,120 分鐘變 115 分鐘。
- **修法**:用 PowerLanguage 內建 `BarsSinceEntry`,它的語意精準等於「自上次成交以來的 K 棒數」,fill bar 當下 `BarsSinceEntry = 0`,第一根後續 = 1...自動處理 next bar 偏移。

**為什麼每一條都要在**:

| 條件 | 為什麼 |
|------|--------|
| `MarketPosition = 0` | 必須空手才進,避免加碼 |
| `v_Regime_Watch` | D1 環境閘(多頭過熱) |
| `v_Trigger_Fired` | D2 動能閘(4-AND 確認失速) |
| `Time >= Entry_Open_Time AND Time <= Entry_Cutoff_Time` | D5 進場視窗 08:50–12:30 |
| `v_DailyCooldown_Active = False` | 一日一單限制 |
| `v_Holiday_Block = False` | 假日前夕禁進場(feedback_holiday_flatten_rule.md) |
| `v_Settlement_Day = False` | CLAUDE.md Rule #11 結算日全策略禁進場 |
| `v_Registry_Expired = False` | Registry 過期 = 環境未知,全 freeze |

**對應決策**:D5。

**Gotcha**:
- `Time >= 850 AND Time <= 1230` 是**閉區間配對**寫法(feedback_mc_time_24hr_pitfall.md),未使用裸露 `Time >= X`,避免跨日夜盤誤觸發。
- `next bar at Market` 表示市價單下一根 K 棒開盤成交,避免 IOG 衝突。

---

### Section 7 — Exit Chain（Priority 0 + 策略出場）

#### Priority 順序

```
P0-1  SX_RPS_Kill          Manual_Kill_Switch
P0-2  SX_RPS_RegistryEnd   v_Registry_Expired
P0-3  SX_RPS_HolFlat       v_Holiday_Block + Time>=245 + Time<=455
P0-4  SX_RPS_Settlement    v_Settlement_Day + Settlement_Flat_Time
P0a   SX_RPS_DayClose      Time>=1325 + Time<=1340
S-1   SX_RPS_TP            0.7% TP OR EMA20 觸及（D4 + v1.1 #1 3 道守衛）
S-2   SX_RPS_TimeStop      24 根 5M K（120 分）
S-3   SX_RPS_SL            v_SL_Level Stop（v1.1 #10 belt-and-suspenders）
（SL engine call 由 Section 5b SetStopLoss 處理）
```

**為什麼用 ExitFired 互斥旗標**:MC 對同一根 K 棒、同一個 entry 標籤多次出場呼叫會產生未定義行為。`ExitFired = 0/1` 確保「**本根 K 一旦出場、後續所有出場條件全 short-circuit**」(SX_RPS_SL 是例外,見下方說明)。

#### P0-3 HolFlat（v1.1 #2 補 Time <= 455 顯式上界）

```powerlanguage
{ BUG FIX v1.1 #2: explicit Time <= 455 belt-and-suspenders }
if ( ExitFired = 0 ) and
   ( v_Holiday_Block = True ) and
   ( Time >= Holiday_Flat_Time ) and
   ( Time <= 455 ) then begin
    BuyToCover( "SX_RPS_HolFlat" ) next bar at Market;
    ExitFired = 1;
end;
```

**v1.1 #2 細節**:
- `v_Holiday_Block` 已被 Section 1B 的 `Time < 500` 守衛限定,理論上 P0-3 觸發時 Time 必 < 500;但 belt-and-suspenders 在 P0-3 自己加 `Time <= 455`,讓即使未來有人把 Section 1B 改回 `Time <= 500`,P0-3 也不會在 Time=500 那根開單(避免 next bar 跳到連假後重啟)。
- 245 (Holiday_Flat_Time 預設) → 455,**間隔 130 分鐘 = 約 26-27 次 5M 重試窗**,足以應付夜盤瞬斷或撮合延遲。

#### P0a DayClose（v1.1 #3 上界 1340 替代 1345）

```powerlanguage
{ BUG FIX v1.1 #3: upper bound MUST be 1340 (not 1345) }
if ( ExitFired = 0 ) and
   ( Time >= Daily_Flat_Time ) and
   ( Time <= 1340 ) then begin
    BuyToCover( "SX_RPS_DayClose" ) next bar at Market;
    ExitFired = 1;
end;
```

**v1.1 #3 細節 — 為什麼 1340 而非 1345**:
- TXF1 日盤 13:45 收盤,夜盤 15:00 開盤,中間 **1 小時 15 分 no-trading gap**。
- 若上界訂 `Time <= 1345`,在 13:45 那根 K 棒成交條件成立 → `next bar at Market` = 下一根可成交 K 棒 = **15:00 夜盤開盤那根**,跨 75 分鐘 gap 後成交,期間市況可能巨變,DayClose 的「保護」意義盡失。
- 改 `Time <= 1340`,最晚觸發根 = 13:40 → next bar = 13:45(仍在日盤內最後一根),DayClose 保證在日盤內完成平倉。
- 這是 L1-L5 後來統一的規則,S3 v1.1 跟進。

#### TP block（v1.1 #1 三道守衛破解 EMA20 fill-bar trap）

```powerlanguage
v_Bars_Held     = BarsSinceEntry;   { BUG FIX v1.1 #5 }
v_TP_Pct_Level  = EntryPrice * ( 1 - TP_Pct / 100 );
v_TP_EMA20      = v_5M_EMA20;

{ BUG FIX v1.1 #1: EMA20 backup requires THREE guards }
if ( Close <= v_TP_Pct_Level ) or
   ( ( TP_Use_EMA20_Backup = True ) and
     ( v_Bars_Held >= TP_EMA20_MinBars ) and
     ( v_5M_EMA20[1] < EntryPrice ) and
     ( Close[1] > v_TP_EMA20[1] ) and
     ( Close <= v_TP_EMA20 ) ) then begin
    BuyToCover( "SX_RPS_TP" ) next bar at Market;
    ExitFired = 1;
end
else if v_Bars_Held >= Max_Bars_TimeStop then begin
    BuyToCover( "SX_RPS_TimeStop" ) next bar at Market;
    ExitFired = 1;
end;

{ ---- S-3 Frozen SL backup ---- }
if ( ExitFired = 0 ) and ( v_SL_Locked = True ) then
    BuyToCover( "SX_RPS_SL" ) next bar at v_SL_Level Stop;
```

**v1.1 #1 細節 — 為什麼 EMA20 備援需要 3 道守衛**:

原 v1.0 寫法 `Close <= v_TP_EMA20` 在實戰會踩到 **fill-bar trap**:
- M2 條件成立的瞬間,Close 已在 EMA5 之下、EMA5 還在下彎;M4 要求 0.5-1.5% pullback。
- 在這幾何下,**EMA20(較長均線)幾乎永遠在 Close 之上**——也就是說 fill bar 本身 `Close <= v_TP_EMA20` 就已成立。
- 結果:進場後 5 分鐘(下一根 K 棒)就觸發 EMA20 備援 TP,獲利 = 一根 5M K 棒的小幅波動,完全踩死 0.7% TP 設計。

**三道守衛分別處理**:

| 守衛 | 程式 | 用意 |
|------|------|------|
| 1. Min bars 持倉 | `v_Bars_Held >= TP_EMA20_MinBars` (預設 3 根 = 15 分) | 跳過 fill-bar 視窗,確保 EMA20 是「持倉一陣子後動能耗盡」的訊號,不是 fill 瞬間的幾何巧合 |
| 2. EMA20 結構性低於進場 | `v_5M_EMA20[1] < EntryPrice` | 確認 EMA20 在「進場前一根」就已在進場價下方,代表這是「**真正從上方跌穿 EMA20**」的反彈進入結構區的成立式;若 EMA20 從一開始就高於 EntryPrice,則「Close <= EMA20」不是 from-above 訊號 |
| 3. 真實跨越 this bar | `Close[1] > v_TP_EMA20[1]` AND `Close <= v_TP_EMA20` | 前根 Close 在 EMA20 上方、本根 Close 在 EMA20 下方 = 真正的「**this bar 跨越**」,而非「Close 一直在 EMA20 下方苟著」的 stale 條件 |

#### SX_RPS_SL Frozen SL 兜底（v1.1 #10）

```powerlanguage
if ( ExitFired = 0 ) and ( v_SL_Locked = True ) then
    BuyToCover( "SX_RPS_SL" ) next bar at v_SL_Level Stop;
```

**做什麼**:Section 5a 鎖好的 `v_SL_Level` 在每根 K 棒掛 BuyToCover Stop 單。

**為什麼**:即使 Section 5b 的 `SetStopLoss` 因 MC 引擎延遲未在 fill bar 立即生效,本層 bar-level Stop 在下一根就有機會觸發。屬於 L1-L5 統一升級的 belt-and-suspenders 模式。

**Gotcha — 為什麼不需要 ExitFired guard 包死整段**:`BuyToCover ... Stop` 是條件單,只在 Low <= v_SL_Level 時才成交;若已有其他 ExitFired=1 的 Market 出場提前處理,Stop 單會被當根 ExitFired 後的下一個 next-bar 順序覆蓋而非「雙重平倉」。`ExitFired = 0` 守衛保留是為了「TP / TimeStop 都沒觸發時才掛 SL Stop 單」的優先序語意清晰。

#### 閉區間審計（feedback_mc_time_24hr_pitfall.md）

| Time>=X 出現位置 | 是否安全 | 為什麼 |
|------------------|---------|--------|
| `Time >= Holiday_Flat_Time AND Time <= 455` | OK | 顯式閉區間配對 + state-guard |
| `Time >= Settlement_Flat_Time` | OK | guarded by `v_Settlement_Day`(日期條件) |
| `Time >= Daily_Flat_Time AND Time <= 1340` | OK | 顯式閉區間配對 |

無裸露 `Time>=X`,符合 24 小時制陷阱規範。

---

### Section 8 — Cooldown Set on Exit

```powerlanguage
if ExitFired > 0 then begin
    v_DailyCooldown_Active = True;
    { BUG FIX v1.1 #11: v_S3_LastExitDate removed }
end;
```

**做什麼**:本根有任何出場觸發 → 設 cooldown active。

**v1.1 #11 細節**:`v_S3_LastExitDate` 原本只是寫不讀的 dead-state,v1.0 設計時預留給「最近 N 日出場後冷靜期」之類擴充,但 v1.0/v1.1 都沒有實作該擴充,反而徒增記憶體與認知負擔。dead-state 移除符合 simplify 原則。

**為什麼 cooldown 還在**:與 Section 4 配合形成「一日一單」閉環。出場後 cooldown 升起,當日剩餘時間內 Section 6 進場閘的 `v_DailyCooldown_Active = False` 條件就會擋住第二次進場;隔日 Section 4 偵測到 `Date` 改變且 `Time >= Entry_Open_Time` 後重置 cooldown(v1.1 #8 切割,見 Section 4)。

---

### Section 9 — Diagnostic Logging（D8 + v1.0.1 LastBarOnChart_Ex 修正歷史）

```powerlanguage
{ BUG FIX v1.0.1: LastBarOnChart_Ex( 0 ) does not exist in PowerLanguage }
if Log_HighConviction and v_HighConv_Active and ( Date <> Date[1] ) then
    Print( "S3 HighConv ", Date:8:0,
           " dist=", v_Daily_Dist_Pct:0:2, "%",
           " regime=",  v_Regime_Watch,
           " trigger=", v_Trigger_Fired,
           " RSI0=", v_Daily_RSI_Snap0:0:2,
           " RSI1=", v_Daily_RSI_Snap1:0:2 );
```

**做什麼**:當日線距 MA20 > +5% 且 `Log_HighConviction = True`,且 `Date` 與上一根不同(新交易日)時,在 MC Output Log 印一行診斷紀錄。

**v1.0.1 編譯封鎖修正歷史**:
- 原 v1.0 寫 `LastBarOnChart_Ex( 0 )`,但此函數在 PowerLanguage **不存在**,MC 編譯直接拋出 "Word LastBarOnChart_Ex not found in dictionary"。標準名稱是 `LastBarOnChart`(bool keyword、無括號)。
- 直接改 `LastBarOnChart` 雖然可編譯通過,但語意上「**只在整個資料集最後一根 K 棒** print 一次」——回測 5 年只會 print 1 行,完全失去診斷意義。
- **更好的選擇**:`Date <> Date[1]`(進入新曆日的第一根 K 棒)作為 print gate,每個有 v_HighConv_Active 的交易日恰好 print 一行(夜盤 00:00 那根 K 棒第一次見到新 Date 時觸發),5 年回測會有~50–80 行可分析 sample。
- 為何不用 `LastBarOnChart`:那是 live mode 才有意義(每秒鐘最末 K),回測時等於只 print 一次。

**為什麼**:D8 v1.0 採 **logging-only**(不改參數),目的為日後 v1.1 統計「HighConviction 區實際 trigger 率與勝率」是否值得擴大 TP_Pct。立刻動參數會混入未經實證的調整,所以分階段:v1.0 觀察、v1.1 sweep、v1.2 上線。

**Gotcha**:Print 新增了 `RSI0` 與 `RSI1` 兩個 snapshot 欄位,方便驗證 sustained 邏輯是否如預期(以前只 print 當日 RSI 就無從驗 snapshot shift)。

---

## 三、Time-Safety 驗證表（檔尾 audit）

| Section | 行為 | 安全性 |
|---------|------|--------|
| 1B | `if Time < 500`(v1.1 #2) | 自帶上界、OK |
| 6 | `Time >= Entry_Open_Time AND Time <= Entry_Cutoff_Time` | 閉區間配對、OK |
| 7 P0-3 | `Time >= Holiday_Flat_Time AND Time <= 455`(v1.1 #2) | 顯式閉區間配對 + state-guarded、OK |
| 7 P0-4 | `Time >= Settlement_Flat_Time` | guarded by `v_Settlement_Day` (date-scoped)、OK |
| 7 P0a | `Time >= Daily_Flat_Time AND Time <= 1340`(v1.1 #3) | 閉區間配對、OK |

**結論**:無裸露 `Time >= X`,**未觸發 MC 24 小時制跨日陷阱**。

---

## 四、Inputs 完整清單

### Tier 1：Regime Gate（Daily, Data3）

| Input | 預設 | 優化範圍 | 用途 |
|-------|------|---------|------|
| Daily_FastMA_Len | 20 | 10..30 step 5 | 日線快 MA |
| Daily_SlowMA_Len | 60 | 40..120 step 10 | 日線慢 MA |
| Daily_RSI_Len | 14 | 7..21 step 7 | RSI 期數 |
| Daily_RSI_Threshold | 70 | 60..80 step 5 | RSI 過熱閾值 |
| Daily_RSI_Sustained_Bars | 2 | 1..3 step 1（上限 4,Snap 數量限制） | RSI 連續黏住根數 |
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
| **TP_EMA20_MinBars**（v1.1 #1 新增） | **3** | **2..6 step 1** | **EMA20 備援啟用最少持倉根數(fill-bar trap 防護)** |
| SL_ATR_Len | 14 | 10..21 step 1 | SL ATR 期數 |
| SL_ATR_Mult | 4 | 3..6 step 0.5 | SL ATR 倍率 |
| Max_Bars_TimeStop | 24 | 18..36 | 時間停損 5M 根數 |
| Entry_Open_Time | **850**（v1.1 #16,原 845） | — | D5 進場視窗開。**MC 5M K 棒以「bar 收盤時間」打 stamp;TXF1 日盤 08:45 開盤後,第一根 5M bar 在 08:50 收盤、stamp = 850。Time = 845 的 stamp 不存在,設 845 等於把 cutoff 設在永遠不到的時點。若要跳過開盤第一根,須設 ≥ 855** |
| Entry_Cutoff_Time | 1230 | — | D5 進場視窗關 |
| Daily_Flat_Time | 1325 | — | 日盤強制平倉 |

### Priority 0 保護

| Input | 預設 | 用途 |
|-------|------|------|
| Holiday_Flat_Time | **245**（v1.1 #6,原 415） | **假日前夕 02:45 平倉,對齊 design_spec_v2 §5.2/§5.3 設計的「02:45 起每 5M 重試一次直到 04:55」共 ~27 次重試窗** |
| Registry_Valid_Until | 1270101 | Registry 有效到 2027/01/01 |
| Manual_Kill_Switch | False | 人工緊急停市開關 |
| Settlement_Flat_Time | 1230 | 結算日 12:30 平倉 |

### Diagnostic

| Input | 預設 | 用途 |
|-------|------|------|
| Log_HighConviction | True | D8 logging-only 開關 |
| HighConv_Threshold_Pct | 5.0 | D8 dist 閾值 (v1.1 sweep) |

**共 30 個 inputs**(v1.0 為 29 個,v1.1 #1 加 TP_EMA20_MinBars,全部 MC12 可優化)。

---

## 五、標籤完整清單

### 進場標籤
| 標籤 | 動作 | 觸發 |
|------|------|------|
| `SE_RPS_Entry` | SellShort | 8 條件 AND 全成立 |

### 出場標籤（8 個,v1.1 新增 SX_RPS_SL）
| 標籤 | 觸發 | Priority |
|------|------|----------|
| `SX_RPS_Kill` | Manual_Kill_Switch=true | P0-1 |
| `SX_RPS_RegistryEnd` | Date > Registry_Valid_Until | P0-2 |
| `SX_RPS_HolFlat` | Holiday tail + 02:45-04:55 | P0-3 |
| `SX_RPS_Settlement` | 結算日 + 12:30 | P0-4 |
| `SX_RPS_DayClose` | 13:25-13:40 force flat | P0a |
| `SX_RPS_TP` | 0.7% 或 EMA20(+3 守衛) 觸及 | S-1 |
| `SX_RPS_TimeStop` | 24 根 5M(BarsSinceEntry) | S-2 |
| **`SX_RPS_SL`**（v1.1 #10 新增） | **v_SL_Level Stop(Frozen SL 兜底)** | **S-3** |

**Engine SL 由 SetStopLoss 處理,MC 內部顯示為 "Stop"**(與 SX_RPS_SL 為 belt-and-suspenders 雙層保護)。

**總計：1 進場 + 8 出場 = 9 個標籤**(v1.0 為 1+7=8),全部符合 `SE_RPS_*` / `SX_RPS_*` 規範。

---

## 六、Constitution 合規檢查

| Rule | 內容 | 對應位置 | 通過 |
|------|------|---------|------|
| #3 | Data3 用 [1] 引用 | Section 2 Daily MA;Daily RSI 用 snapshot 替代 | OK |
| #11 | Settlement_Flat 7 元素 | Section 1B + Section 7 P0-3/P0-4 | OK |
| #12 | P3b SetStopLoss 單一呼叫 | Section 5b(僅此一處) | OK |
| #13 | 10-dim eval before live_simulation | 待 backtest 後 gate | 暫緩(research-tier) |
| Filter 重疊 | M1..M4 正交 | Section 3 4-AND | OK |
| 24 小時陷阱 | 閉區間 / state-guard | 檔尾 audit 表 | OK |
| 標籤前綴 | SE_/SX_ 嚴格區分 | Section 6 + Section 7 | OK |
| 假日鐵律 | 全 TXF1 策略休市前必平倉 | Section 0/1B/7-P0-3 | OK |
| 趨勢讓利潤奔跑 | 不適用(counter-trend) | — | N/A |

---

## 七、風險警告

1. **無回測**:v1.1 仍為研究稿,所有預期數字(WR 52–58%、R:R 1.21)為設計目標而非實證。v1.1 修補了 13 項邏輯 bug 後預期觸發頻率與實盤更接近,但仍待 backtest 驗證。
2. **5M Volume 已 drop**:M3 ATR spike 是唯一波動率代理,若 ATR 訊號失靈、可能流產率上升。需 ShowMe 驗證後在 v1.2 補回 volume confirmation。
3. **Counter-trend 結構性風險**:強趨勢日(gap up + 不回測)會觸發 4-AND 但被一路軋空。time stop + Frozen SL 是最後防線,但仍可能吃完 SL。
4. **L4 退役後曝險替代**:S3 接 3% 額度,但 S3 觸發頻率(年 25–40 次)vs L4 黑天鵝捕捉次數差異很大,組合風險特性會改變。
5. **HighConviction 區數據尚未蒐集**:dist > +5% 的回測樣本是否足夠統計顯著,需 v1.0/v1.1 跑完才知道。
6. **v1.1 #4 day-session High 副作用**:首次掛圖 / 重啟 MC 後第一個交易日的 `v_DaySess_High` 在 08:50 才有第一個值,該日 08:50 之前(本就不該進場)若有調試需求,M4 會回 false,屬預期行為非 bug。

---

## 八、後續 Phase 路線

### Phase 1（v1.0 已完成 2026-06-20,v1.1 patched 2026-06-19)
- [x] Agent D 五路 deep research 合成 design spec v2
- [x] 用戶確認 8 項決策 + parameterization override
- [x] 撰寫 .pla(29 inputs、Rule #11 / #12 合規)
- [x] 撰寫中文逐段註解
- [x] v1.0.1 修補 3 項預發布封鎖(LastBarOnChart_Ex / RSI[1] / RSI[hidx])
- [x] v1.1 修補 13 項稽核 bug(本版註解涵蓋)

### Phase 2（待執行）
- [ ] MC ShowMe 五行驗證 TXF1 5M 成交量(D7 procedural step)
- [ ] MC12 載入 .pla 跑 2020/01/01 ~ 今 backtest
- [ ] 樣本 ≥ 100 筆檢核
- [ ] 三市況(牛/熊/震盪)PF > 1.0 檢核

### Phase 3（P1-P3 標準驗證）
- [ ] 參數敏感度(每個 input scan,找高原;特別注意新增 TP_EMA20_MinBars)
- [ ] Walk-Forward Analysis WFE > 50%
- [ ] Monte Carlo 95% MDD < 帳戶 30%
- [ ] 跨策略相關性 < 0.7(vs L1/L2/L3/L5/S1)

### Phase 4（晉升 live_simulation）
- [ ] 10 維機構級評估 ALL PASS(Rule #13)
- [ ] 移到 `strategies/live_simulation/`
- [ ] 註冊到 master verify 腳本
- [ ] MC12 模擬帳戶上架收 ≥ 30 筆樣本

### Phase 5 / v1.2（HighConviction sweep + Volume 回補）
- [ ] D8 HighConv 區單獨統計勝率 / 平均回測幅度
- [ ] 若 HighConv 區回測幅度顯著 > 一般區 → TP_Pct 動態 modifier
- [ ] 補回 Volume 條件(若 ShowMe 驗證通過)

---

## 九、Glossary（變數名 → 中文對照）

### Inputs

| 變數 | 中文 |
|------|------|
| Daily_FastMA_Len | 日線快 MA 期數(預設 20) |
| Daily_SlowMA_Len | 日線慢 MA 期數(預設 60) |
| Daily_RSI_Len | 日線 RSI 期數(預設 14) |
| Daily_RSI_Threshold | RSI 過熱閾值(預設 70) |
| Daily_RSI_Sustained_Bars | RSI 連續超閾值根數(預設 2,上限 4) |
| Daily_Dist_MA20_Pct | 距 MA20 過漲百分比(預設 3.0%) |
| Consec_Red_Bars | M1 連續紅 K 根數(預設 3) |
| EMA_Fast_Len | M2 快 EMA 期數(預設 5) |
| ATR_Short_Len | M3 短 ATR 期數(預設 5) |
| ATR_Long_Len | M3 長 ATR 期數(預設 20) |
| ATR_Spike_Mult | M3 ATR spike 倍率(預設 1.3) |
| Pullback_Min_Pct | M4 回檔下界百分比(預設 0.5%) |
| Pullback_Max_Pct | M4 回檔上界百分比(預設 1.5%) |
| TP_Pct | TP 百分比(預設 0.7%) |
| TP_Use_EMA20_Backup | D4 結構備援 TP 開關(預設 True) |
| TP_MA_Len | 5M EMA20 期數(預設 20) |
| **TP_EMA20_MinBars** | **EMA20 備援啟用最少持倉根數(v1.1 新增,預設 3 = 15 分)** |
| SL_ATR_Len | SL ATR 期數(預設 14) |
| SL_ATR_Mult | SL ATR 倍率(預設 4) |
| Max_Bars_TimeStop | 時間停損 5M 根數(預設 24 = 120min) |
| Entry_Open_Time | 進場視窗開(v1.1 預設 850;MC 5M K 棒以收盤時間打 stamp) |
| Entry_Cutoff_Time | 進場視窗關(預設 1230) |
| Daily_Flat_Time | 日盤強制平倉時間(預設 1325) |
| Holiday_Flat_Time | 假日前夕平倉時間(v1.1 預設 245,對齊 design_spec_v2) |
| Registry_Valid_Until | 假日 registry 有效日(預設 1270101) |
| Manual_Kill_Switch | 人工緊急停市開關(預設 False) |
| Settlement_Flat_Time | 結算日平倉時間(預設 1230) |
| Log_HighConviction | D8 HighConv 日誌開關(預設 True) |
| HighConv_Threshold_Pct | D8 HighConv 距 MA20 閾值(預設 5.0%) |

### 狀態變數（v_ 前綴）

| 變數 | 中文 |
|------|------|
| v_Daily_FastMA | 日線快 MA 值(取 [1] 已收盤) |
| v_Daily_SlowMA | 日線慢 MA 值(取 [1] 已收盤) |
| v_Daily_RSI | 日線 RSI 值(取自 Snap0,v1.0.1 修正) |
| **v_Daily_RSI_Snap0..Snap3** | **日線 RSI snapshot(v1.0.1 新增,Section 4 於曆日轉換時 shift)** |
| v_Daily_RSI_Sustained | RSI 連續 N 根皆超閾值(True/False) |
| v_Daily_Dist_Pct | 收盤距 MA20 百分比(v1.1 #7 顯式括號) |
| v_Trend_OK | D1 條件 A:MA20 > MA60(多頭結構) |
| v_RSI_OK | D1 條件 B:RSI 持續過熱(snapshot-based) |
| v_Dist_OK | D1 條件 C:距 MA20 超漲 |
| v_Regime_Watch | D1 合成:A AND (B OR C) |
| v_M1_Consec | M1:連 N 根紅 K |
| v_M2_BelowEMA | M2:跌破 EMA5 且 EMA5 下彎 |
| v_M3_ATR_Spike | M3:ATR(5) > ATR(20)×1.3 |
| v_M4_Pullback | M4:回檔 0.5%–1.5% |
| v_5M_EMA | 5M EMA5 當前值(v1.1 #9 單次呼叫) |
| v_5M_EMA_Prev | 5M EMA5 前一根值(= v_5M_EMA[1],判斜率) |
| v_5M_ATR_Short | 5M ATR(5) |
| v_5M_ATR_Long | 5M ATR(20) |
| **v_DaySess_High** | **當日日盤時段自行累計的最高(v1.1 #4 新增,取代 HighD(0))** |
| **v_DaySess_HighDate** | **v_DaySess_High 對應的 Date(用於每新 Date 重置一次)** |
| v_Pullback_Pct | 當前 Close 距日內(日盤時段)高的百分比 |
| v_Trigger_Fired | D2 合成:M1 AND M2 AND M3 AND M4 |
| v_Red_Loop_OK | M1 迴圈暫存(紅 K 全部通過 = True) |
| v_red_idx | M1 迴圈索引 |
| v_TP_Pct_Level | TP 百分比目標價(EntryPrice × (1 − TP_Pct/100)) |
| v_TP_EMA20 | TP D4 結構備援價(= v_5M_EMA20) |
| v_5M_EMA20 | 5M EMA20 當前值 |
| **v_SL_Locked** | **Frozen SL 鎖定旗標(v1.1 #10 新增,True = 已於進場根鎖定 ATR/Dist/Level)** |
| **v_Frozen_ATR_5M** | **進場根凍結的 ATR 值(v1.1 #10 新增)** |
| **v_Frozen_SL_Dist** | **進場根凍結的 SL 點數距離(v1.1 #10 新增,= Frozen ATR × SL_ATR_Mult)** |
| **v_SL_Level** | **空單停損價位(v1.1 #10 新增,= EntryPrice + Frozen_SL_Dist,Section 7 SX_RPS_SL bar-level Stop 使用)** |
| v_SL_ATR | SL ATR 當前值(若 v_SL_Locked = True 則為 Frozen ATR;Section 5b SetStopLoss 距離計算用) |
| v_Bars_Held | 持倉根數(v1.1 #5 改用 BarsSinceEntry 內建,移除手動計數) |
| v_DailyCooldown_Active | 當日已出場、不再進場 |
| v_LastSeenDate | 上一根 K 的 Date(用於偵測新交易日;v1.1 #8 切割後仍由 cooldown 分支更新) |
| v_Holiday_Block | 假日 tail bar 旗標(v1.1 #2 嚴格 Time < 500) |
| v_Registry_Expired | Registry 過期旗標 |
| v_Settlement_Day | 結算日旗標(每月第三個禮拜三) |
| Registry_Warn_ID | Registry 過期紅字 Text ID |
| hidx | 通用迴圈索引(Section 1B 共用) |
| ExitFired | 本根 K 是否已有出場(互斥旗標) |
| v_HighConv_Active | D8 HighConviction 區旗標 |

**v1.1 移除的變數**(在 v1.0 註解中曾出現,本版已刪):
- `v_Entry_Bar`(v1.1 #5 移除,改用 `BarsSinceEntry` 內建)
- `v_S3_LastExitDate`(v1.1 #11 移除,dead-state)

### MC 內建函數 / 常數

| 名稱 | 中文 |
|------|------|
| `Average(price, len)` | SMA |
| `XAverage(price, len)` | EMA |
| `AvgTrueRange(len)` | ATR |
| `RSI(price, len)` | RSI |
| `HighD(0)` | 當日盤中最高(v1.1 #4 已被 v_DaySess_High 取代,僅作為對照存留) |
| `Date` | 當前 K 棒日期(YYYMMDD 民國年 + 月日,如 1260620) |
| `Time` | 當前 K 棒時間(HHMM,5M bar 以收盤時間 stamp) |
| `DayOfWeek(Date)` | 星期幾(0=Sun, 1=Mon, ..., 3=Wed) |
| `DayOfMonth(Date)` | 月內第幾日 |
| `DateToJulian(Date)` | 轉 Julian day(便於日期算術) |
| `BarNumber` | 當前 K 棒序號 |
| `MarketPosition` | 部位狀態(−1=Short, 0=Flat, +1=Long) |
| `EntryPrice` | 最近一次進場價 |
| `BigPointValue` | 每點價值(TXF1 = 200) |
| `LastBarOnChart` | 是否為圖表最右一根(v1.0.1 後僅出現於 Section 1B Registry 警告) |
| `BarsSinceEntry` | 自進場成交以來的 K 棒數(v1.1 #5 引入,取代手動 v_Entry_Bar 計數) |

---

## 十、相關文件

- [策略本身](S3_RapidPullbackShort.pla)
- [設計規格 v2](S3_PullbackShort_design_spec_v2.md)
- [策略總則](../README.md)
- [Settlement 憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [P3b Immediate Stop Guard 設計](../../../docs/P3b_immediate_stop_guard_design_20260618.md)
- [機構級 10 維風險框架](../../../docs/institutional_risk_framework_20260619.md)
- [S2 InsideBarBreak 註解(風格參照)](../S02_InsideBarBreak/S2_InsideBarBreak_annotated.md)
