# S3_RapidPullbackShort_v2.pla — 中文逐行註解（focused on v2.0 diffs）

> **本檔策略**：v2.0 跟 v1.1 99% 結構相同，本檔聚焦註解「v2.0 變動 sections」。
> v1.1 未變動部分請見 [S3_RapidPullbackShort_annotated.md](S3_RapidPullbackShort_annotated.md)（935 行完整版）。
>
> **v2.0 對應檔**：[S3_RapidPullbackShort_v2.pla](S3_RapidPullbackShort_v2.pla)（745 行）

---

## 索引：v2.0 變動分布

| Section | 變動程度 | 註解位置 |
|---------|---------|---------|
| Header (line 1-80) | **大幅變動** | 本檔 §1 |
| Section 1 INPUTS (line 91-130) | **大幅變動** | 本檔 §2 |
| Section 2 VARIABLES (line 136-210) | **中度變動**（移除 Daily snap, 新增 hourly snap） | 本檔 §3 |
| Section 3 ARRAYS (line 220) | 不變 | reference v1.1 §3 |
| Section 0 HOLIDAY TAIL (line 232-314) | **byte-identical** | reference v1.1 §0 |
| Section 1B HOLIDAY/REGISTRY/SETTLEMENT (line 322-360) | 不變 | reference v1.1 §1B |
| Section 2 60M TIER 1 (line 363-443) | **大幅變動**（Daily → 60M） | 本檔 §4 |
| Section 3 5M TIER 2 (line 446-518) | 不變（M4 default 微調） | reference v1.1 §3 |
| Section 4 60M SNAP + COOLDOWN (line 530-580) | **大幅變動**（cadence 改，v2.0.1 MC12 patch） | 本檔 §5 |
| Section 5 SetStopLoss + Frozen SL (line 550-592) | 不變 | reference v1.1 §5 |
| Section 6 ENTRY (line 595-624) | 不變（label SE_RPS_v2_Entry） | reference v1.1 §6 |
| Section 7 EXIT (line 627-750) | 不變（label SX_RPS_v2_*） | reference v1.1 §7 |
| Section 8 COOLDOWN ON EXIT (line 753-762) | 不變 | reference v1.1 §8 |
| Section 9 DIAGNOSTIC (line 765-787) | 細微變動（HighConv threshold） | 本檔 §6 |

---

## 1. Header（line 1-80）

### 1.1 核心識別變動

```pla
Version     : v2.0  (2026-06-20)        // v1.1 → v2.0
Timeframe   : Data1 = 5M  (entry trigger / exit chain)
              Data2 = 60M (regime gate: MA20/MA60/RSI14/dist%)
                        ★ v2.0: previously reserved in v1.1, now ACTIVE
              Data3 = (removed in v2.0; was Daily regime gate)
```

**重點**：
- Data2 從 v1.1 的「reserved」變成 v2.0 的「active regime gate」
- Data3 (Daily) 完全移除，MC chart 只需掛 2 個 data series
- 載入時 MC12 chart 需要兩個 data feed：5M (Data1) + 60M (Data2)

### 1.2 v2.0 CHANGE LOG block

```pla
v2.0 CHANGE LOG vs v1.1 (USER OPTION B, 2026-06-20)
============================================================
Thesis: UNCHANGED - "Counter-trend short during overheated bull regime pullbacks"
Root cause of v1.1 underperformance: Daily Tier 1 too restrictive
  -> only 9 trades/yr (target 25-40), PF after slippage -0.92.
Fix path: Shorten regime time-frame Daily -> 60M (one tier shorter).
```

**設計意圖**：完整保留 thesis（過熱多頭回檔做空），只縮短 regime time-frame 從 Daily 到 60M。這是 User Option B 的核心。

---

## 2. Section 1 INPUTS（line 91-130）

### 2.1 Tier 1 改名 + 鬆綁

```pla
{ ===== Tier 1 : Regime Gate Parameters (60M, Data2) ===== }
H60_FastMA_Len            ( 20    ),   // v1.1: Daily_FastMA_Len = 20
H60_SlowMA_Len            ( 60    ),   // v1.1: Daily_SlowMA_Len = 60
H60_RSI_Len               ( 14    ),   // v1.1: Daily_RSI_Len = 14
H60_RSI_Threshold         ( 65    ),   // v1.1: Daily_RSI_Threshold = 70 ★ 鬆綁
H60_RSI_Sustained_Bars    ( 2     ),   // v1.1: 同（但 bars 意義 = 小時，非日）
H60_Dist_MA20_Pct         ( 1.5   ),   // v1.1: Daily_Dist_MA20_Pct = 3.0 ★ 鬆綁
```

**為什麼鬆綁**：
- 60M scale 下 RSI 更易上下波動，70 門檻會過嚴
- 60M 距 MA20 的數值天然比 Daily 距 MA20 小（時間框架短）
- 大致換算：Daily +3% ≈ 60M +1.5%, Daily RSI 70 ≈ 60M RSI 65

### 2.2 Tier 2 不變（僅 Pullback_Min_Pct 微調）

```pla
Pullback_Min_Pct          ( 0.3   ),   // v1.1: 0.5 ★ 鬆綁
Pullback_Max_Pct          ( 1.5   ),   // 不變
```

### 2.3 Exit Tier 收緊

```pla
TP_Pct                    ( 0.6   ),   // v1.1: 0.7 ★ 收緊
SL_ATR_Mult               ( 3     ),   // v1.1: 4 ★ 收緊
Max_Bars_TimeStop         ( 18    ),   // v1.1: 24 ★ 收緊（120min → 90min）
Entry_Cutoff_Time         ( 1325  ),   // v1.1: 1230 ★ 拓寬
```

**設計意圖**：90 min hold cap 對應較緊的 TP/SL 帶寬。原 v1.1 TP 0.7/SL 0.58 ≈ R:R 1.21；v2.0 0.6/0.44 ≈ R:R 1.36（略提升）。

### 2.4 Diagnostic 縮放

```pla
HighConv_Threshold_Pct    ( 2.5   ),   // v1.1: 5.0 ★ 60M scale
```

---

## 3. Section 2 VARIABLES（line 136-210）

### 3.1 移除（v1.1 有但 v2.0 無）

```pla
// 以下變數移除（v1.1 為 Daily 用，v2.0 已換 60M）
v_Daily_FastMA            ── 改名 v_H60_FastMA
v_Daily_SlowMA            ── 改名 v_H60_SlowMA
v_Daily_RSI               ── 改名 v_H60_RSI
v_Daily_RSI_Sustained     ── 改名 v_H60_RSI_Sustained
v_Daily_Dist_Pct          ── 改名 v_H60_Dist_Pct
v_Daily_RSI_Snap0..Snap3  ── 改名 v_H60_RSI_Snap0..Snap3
```

### 3.2 新增（v2.0.1 特有）

```pla
v_LastSeenData2Date      ( -1    ),
v_LastSeenData2Time      ( -1    ),
```

**用法**：Section 4 用 `(Date of Data2, Time of Data2)` tuple 偵測 Data2 60M bar advance；只在真正 advance 時 shift snapshot。預設 -1 確保第一根 bar 走 init branch（從歷史 `[1]..[4]` 直接 bootstrap 4 個 snap，避免 4 小時 warmup 全 zero）。

**為什麼不用 `v_LastSeenHour` + `Hour(Time)`**：原 v2.0 用這個做法，但 `Hour(Time)` 假設 60M align hour（09:00, 10:00, ...）對 TXF1 不成立 — session-aligned 60M 邊界在 09:45 / 10:45 / ...，hour-based 偵測會在錯誤時點 snap 到 partial bar RSI。v2.0.1 改用 Data2 自身時間戳。詳見 §5。

### 3.3 其他變數（不變）

5M Tier 2 變數、Exit state、Frozen SL、Cooldown、Holiday/Settlement、Diagnostic 全數 byte-identical with v1.1。詳見 v1.1 annotated §2。

---

## 4. Section 2 — 60M TIER 1 CALCULATIONS（line 363-443）★ v2.0 核心變動

### 4.1 60M MA（取代 Daily MA）— v2.0.1 explicit parens

```pla
v_H60_FastMA = ( Average( Close, H60_FastMA_Len ) of Data2 )[1];
v_H60_SlowMA = ( Average( Close, H60_SlowMA_Len ) of Data2 )[1];
```

**重點**：
- v2.0.1 加 explicit parens：`( ... of Data2 )[1]` 而非 `Average(...)[1] of Data2`
- 原寫法 `[1]` binding 在 Data1/Data2 之間 ambiguous across PowerLanguage parser versions（mirrors v1.1 BUG FIX #7 對 Close 的修正 idiom）
- `[1]` 確保使用「已收盤」的 60M bar（CLAUDE.md Rule #3）
- 同一個 thesis 但 reference 從 Data3 (Daily) 改為 Data2 (60M)
- 60M MA20 = 20 hours = 約 1 trading day 的 hourly 趨勢
- 60M MA60 = 60 hours = 約 3 trading days 的 hourly 趨勢

### 4.2 RSI 從 snapshot 取得（避免 stale）

```pla
v_H60_RSI = v_H60_RSI_Snap0;   // Section 4 維護 Snap0..Snap3
```

**為什麼用 snapshot 而不是直接 `RSI(...) of Data2`**：與 v1.1 同問題 — 5M 級別的 `RSI(...)[N] of Data2` 中 `[N]` 是 5M offset 而非 60M offset。直接讀同一個 60M bar 內所有 5M bar 會拿到相同值，sustained 邏輯失效。Snapshot 在 hour boundary shift 才能真正抓到「過去 N 個 60M bar 的 RSI」。

### 4.3 60M 距 MA20

```pla
if v_H60_FastMA > 0 then
    v_H60_Dist_Pct = ( ( Close of Data2 )[1] - v_H60_FastMA ) /
                     v_H60_FastMA * 100
else
    v_H60_Dist_Pct = 0;
```

**v1.1 BUG FIX #7 preserved**：明確 `( Close of Data2 )[1]` 強迫 parser 先 bind `of Data2` 再套 `[1]`，避免 Data1/Data2 binding 模糊。

### 4.4 Regime 結構（A AND (B OR C)）— 同 v1.1

```pla
// A: bullish 60M structure
if v_H60_FastMA > v_H60_SlowMA then v_Trend_OK = True else v_Trend_OK = False;

// B: RSI sustained loop (4 levels: Snap0..Snap3)
v_H60_RSI_Sustained = True;
if H60_RSI_Sustained_Bars >= 1 and v_H60_RSI_Snap0 <= H60_RSI_Threshold then
    v_H60_RSI_Sustained = False;
// ... (Snap1, Snap2, Snap3 依次檢查，最多 sustained 4 hr)

// C: 60M dist exceeds threshold
if v_H60_Dist_Pct > H60_Dist_MA20_Pct then v_Dist_OK = True else v_Dist_OK = False;

// Regime: A AND (B OR C)
if v_Trend_OK and ( v_RSI_OK or v_Dist_OK ) then
    v_Regime_Watch = True
else
    v_Regime_Watch = False;
```

**設計意圖**：結構與 v1.1 同形：A 必要、B/C 二選一。差異僅在 threshold 與 cadence。

---

## 5. Section 4 — 60M SNAP + COOLDOWN（line 530-580）★ v2.0 核心變動 + v2.0.1 MC12 patch

### 5.1 60M boundary 偵測 + snapshot shift（v2.0.1 MC12-safe）

```pla
if ( Date of Data2 <> v_LastSeenData2Date ) or
   ( Time of Data2 <> v_LastSeenData2Time ) then begin
    if v_LastSeenData2Date >= 0 then begin
        { Normal shift: Data2 just advanced to a new 60M bar }
        v_H60_RSI_Snap3 = v_H60_RSI_Snap2;
        v_H60_RSI_Snap2 = v_H60_RSI_Snap1;
        v_H60_RSI_Snap1 = v_H60_RSI_Snap0;
        v_H60_RSI_Snap0 = ( RSI( Close, H60_RSI_Len ) of Data2 )[1];
    end
    else begin
        { First-bar init: bootstrap from historical Data2 }
        v_H60_RSI_Snap0 = ( RSI( Close, H60_RSI_Len ) of Data2 )[1];
        v_H60_RSI_Snap1 = ( RSI( Close, H60_RSI_Len ) of Data2 )[2];
        v_H60_RSI_Snap2 = ( RSI( Close, H60_RSI_Len ) of Data2 )[3];
        v_H60_RSI_Snap3 = ( RSI( Close, H60_RSI_Len ) of Data2 )[4];
    end;
    v_LastSeenData2Date = Date of Data2;
    v_LastSeenData2Time = Time of Data2;
end;
```

**為什麼用 Data2 自身時間戳而不是 `Hour(Time)`**：

原 v2.0 用 `Hour(Time) <> v_LastSeenHour` 偵測 boundary。**這假設 60M bar 邊界在整點 (09:00, 10:00, ...)**。對 TXF1 不成立：
- TXF1 日盤 08:45-13:45，session-aligned 60M 邊界在 **09:45 / 10:45 / 11:45 / 12:45 / 13:45**
- 從 08:55 → 09:00（hour 從 8 變 9）會錯誤觸發 snap，但這時 60M (08:45-09:45) 還沒 close
- 跨夜盤 13:45 → 15:05 時 Hour 從 13 → 15，跳過 14，邏輯破洞

**正確 idiom**：
1. **Boundary detection**：用 `(Date of Data2, Time of Data2)` tuple — Data2 自身的時間戳。在 5M context 內，同一個 60M bar 內所有 5M bar 看到同樣的 `Time of Data2`，**只有當 Data2 真的 advance 到下一根時才會變更**。
2. **Snap0 讀值**：用 `( RSI(...) of Data2 )[1]` 而非 `RSI(...) of Data2`。當 boundary 剛切換時，current Data2 已經是「新開的 partial bar」；`[1]` 才是「剛 closed 的上一根」。
3. **Init branch**：第一根 bar (`v_LastSeenData2Date = -1`) 直接從歷史 `[1]..[4]` bootstrap 4 個 snap，避免 4 小時 warmup 全 zero。

**對比 v1.1**：v1.1 用 `Date <> v_LastSeenDate` 在 calendar-date 邊界 shift（一天 1 次 = Data3 Daily bar advance）。對應到 v2.0，正確類比是「Data2 advance」而非「clock hour change」。

### 5.2 Cooldown reset（不變）

```pla
if Date <> v_LastSeenDate then begin
    if Time >= Entry_Open_Time then begin
        v_DailyCooldown_Active = False;
        v_LastSeenDate         = Date;
    end;
end;
```

**v1.1 BUG FIX #8 preserved**：cooldown reset 仍 gated by `Time >= Entry_Open_Time`，避免夜盤誤觸發。

---

## 5.7 Section 2b — SECULAR BULL FILTER (v2.0.3 REVISED: Daily Data3) ★

### 5.7.1 完整 code

```pla
v_Daily_SecularMA_Fast = ( Average( Close, Daily_SecularMA_Fast ) of Data3 )[1];
v_Daily_SecularMA_Slow = ( Average( Close, Daily_SecularMA_Slow ) of Data3 )[1];

if Enable_Secular_Bull_Filter = False or (
   ( Close of Data3 )[1] > v_Daily_SecularMA_Fast and
   ( Close of Data3 )[1] > v_Daily_SecularMA_Slow and
   v_Daily_SecularMA_Fast    > v_Daily_SecularMA_Slow
) then
    v_Secular_Bull_OK = True
else
    v_Secular_Bull_OK = False;
```

**v2.0.3 從 60M Data2 (v2.0.2) 改成 Daily Data3**：
- Max Bars Strategy Reference: 5000 → **300**
- Input 數字: H60_SecularMA 1140/3800 → **Daily_SecularMA 60/200**（金融標準）
- 邏輯（3 條件 AND）+ 預期效果 完全不變

### 5.7.2 3 條件 AND

| # | 條件 | 含意 |
|---|------|------|
| 1 | Close > MA_Fast | 60M 收盤 > 季線（~60 day）|
| 2 | Close > MA_Slow | 60M 收盤 > 年線（~200 day）|
| 3 | MA_Fast > MA_Slow | **MA 結構多頭**（季線 > 年線）|

**3 條件全成立才 pass** — 確認「真多頭」（非短期反彈 / 弱多頭）。

### 5.7.3 為什麼用 AND 而非 L1 P6 的 OR

| 策略 | 思路 | OR/AND 選擇 |
|------|------|-----------|
| L1 (trend long) | 不要錯過 early bull → 用 OR | 寬鬆 |
| **S3 (counter-trend short)** | **不要在假反彈做空** | **AND（嚴格）** |

S3 跟 L1 需求**相反**：L1 寧可早進，S3 寧可少進。

### 5.7.4 為什麼用 1140 / 3800 (60M bars)

| Daily proxy | 60M bars 換算 | 意義 |
|------------|--------------|------|
| Daily MA60 (季線) | 60 × 19 ≈ **1140** | 中期格局 |
| Daily MA200 (年線) | 200 × 19 ≈ **3800** | 長期格局 |

19 = 一天 19 個 60M bars (TXF1 24hr 連續 session)。

### 5.7.5 進場 gate 加 v_Secular_Bull_OK = True

```pla
if ( MarketPosition = 0 ) and
   ( v_Regime_Watch = True ) and          // Tier 1 60M 過熱
   ( v_Trigger_Fired = True ) and         // Tier 2 5M 動能轉空
   ( v_Secular_Bull_OK = True ) and       // ⭐ NEW Secular Bull Filter
   ...
```

### 5.7.6 歷史 backtest 阻擋效果

| Trade | 日期 | 為何擋 | 救回 |
|-------|------|--------|------|
| #8 | 2022-07-28 | 大空頭中，3 條件都 fail | +400 (僥倖小贏，但 thesis 對) |
| #9 | 2022-10-05 | 弱空，close < MA | +9,000 |
| #10 | 2022-11-11 | 大空頭反彈，MA60 < MA200 | +13,200 |
| #12 | 2025-07-01 | 弱多但 MA60 < MA200（條件 3 fail）| +10,800 |

**合計救回 +32.6k 累積虧損**。2026 H1 三筆全 pass，0 影響。

---

## 6. Section 9 — DIAGNOSTIC LOGGING（line 765-787）

```pla
if Log_HighConviction and v_HighConv_Active and ( Date <> Date[1] ) then
    Print( "S3v2 HighConv ", Date:8:0,
           " dist60m=", v_H60_Dist_Pct:0:2, "%",
           " regime=",  v_Regime_Watch,
           " trigger=", v_Trigger_Fired,
           " RSI60m0=", v_H60_RSI_Snap0:0:2,
           " RSI60m1=", v_H60_RSI_Snap1:0:2 );
```

**變動點**：
- Prefix "S3v2"（vs v1.1 "S3"）便於 log 分流
- `dist60m=` / `RSI60m0=` / `RSI60m1=` 標示 60M 而非 Daily
- HighConv threshold 預設 2.5%（60M scale）vs v1.1 5%（Daily scale）

---

## 7. 未列出 sections（reference v1.1 annotated）

以下 sections 與 v1.1 byte-identical，除 label prefix `SE_/SX_RPS_*` 改為 `SE_/SX_RPS_v2_*` 外無變動：

| Section | v1.1 annotated 參考 |
|---------|--------------------|
| Section 3 Arrays | v1.1 §3 |
| Section 0 Holiday Tail (63 entries) | v1.1 §0 |
| Section 1B Holiday/Registry/Settlement Detection | v1.1 §1B |
| Section 3 5M Tier 2 (M1-M4 momentum) | v1.1 §3 |
| Section 5 SetStopLoss + Frozen SL | v1.1 §5 |
| Section 6 Entry Logic | v1.1 §6（label 改 SE_RPS_v2_Entry） |
| Section 7 Exit Chain (P0-1 ~ S-3) | v1.1 §7（labels 改 SX_RPS_v2_*） |
| Section 8 Cooldown on Exit | v1.1 §8 |

---

## 8. 驗證 + Time-safety audit

詳見 [scripts/verify_s3_v2.py](../../../scripts/verify_s3_v2.py) — 94 checks 全 PASS。

Time-safety 與 v1.1 相同 5 處 closed-interval check：
- Section 1B  `Time < 500` (上界自然有)
- Section 6   `Time >= Entry_Open_Time AND Time <= Entry_Cutoff_Time`
- Section 7   `Time >= Holiday_Flat_Time` (guarded by `v_Holiday_Block`) `AND Time <= 455`
- Section 7   `Time >= Settlement_Flat_Time` (guarded by `v_Settlement_Day`)
- Section 7   `Time >= Daily_Flat_Time AND Time <= 1340`

無裸 `Time >= X` 未配對者。跨日陷阱避免。

---

## 9. 後續工作

1. P0 pre-flight 8 項全勾 → MC12 GA Stage 1
2. Stage 1 best 找出 → Stage 2 refine
3. Walk-Forward (IS 2020-2022 / OOS 2023-2026-06)
4. v1.1 baseline 對照（必須 PF net > 0 才贏）
5. 10 維度 institutional eval（CLAUDE.md Rule #13）
6. PASS → 升 live_simulation；FAIL → v2.1（加夜盤）或 v2.2（thesis pivot）

詳見 [S3_v2_optimization_ranges.md](S3_v2_optimization_ranges.md)。
