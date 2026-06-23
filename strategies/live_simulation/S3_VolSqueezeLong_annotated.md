# S3_VolSqueezeLong.pla — 中文逐段註解

> **本檔配對 .pla**：[S3_VolSqueezeLong.pla](S3_VolSqueezeLong.pla) (v1.1, 527 LOC)
> **部署狀態**：live_simulation/ since 2026-06-23
> **Deployment manifest**：[S3_VolSqueezeLong_DEPLOYMENT.md](S3_VolSqueezeLong_DEPLOYMENT.md) (caveats + kill triggers)
> **W5 評估**：[../research/S03_VolSqueezeLong/W5_10dim_evaluation.md](../research/S03_VolSqueezeLong/W5_10dim_evaluation.md)

---

## 索引

| Section | 行數 | 功能 | 註解位置 |
|---------|------|------|---------|
| Header | 1-86 | 識別 + thesis + perf summary | §0 |
| IOG declaration | 88 | `[IntrabarOrderGeneration = false]` | §0 |
| 1. INPUTS | 91-121 | 14 個可調 inputs（Phase 3 best 鎖入）| §1 |
| 2. VARIABLES | 124-164 | 內部狀態變數 | §2 |
| 3. ARRAYS | 167-173 | Holiday_Tail[80] | §3 |
| 4. HOLIDAY TAIL REGISTRY | 176-265 | 63 個 TAIFEX-verified 日期 | §4 |
| 5. HOLIDAY / REGISTRY / SETTLEMENT DETECTION | 268-308 | Priority 0 狀態旗 | §5 |
| 6. BB + SQUEEZE DETECTION | 311-340 | **核心 alpha 觸發** | §6 |
| 7. ATR + STOP/TARGET | 343-349 | ATR 距離 | §7 |
| 8. SAME-DAY COOLDOWN | 352-361 | 冷卻期 reset | §8 |
| 9. FROZEN SL + SetStopLoss | 364-396 | Rule #12 雙重保險 | §9 |
| 10. ENTRY LOGIC | 399-424 | 7-gate 進場 | §10 |
| 11. EXIT CHAIN | 427-507 | P0 + S 出場優先序 | §11 |
| 12. COOLDOWN SET ON EXIT | 510-519 | 觸發冷卻 | §12 |
| 13. PREV_MP TRACKING | 522-526 | Rule #8 末行 | §13 |

---

## §0. Header + IOG（line 1-88）

### 0.1 識別塊（line 1-19）

```pla
S3_L - VOLATILITY SQUEEZE LONG STRATEGY
Signal Name : S3_VolSqueezeLong
MC Load Name: STRATEGY_GEN_S3_VolSqueezeLong
Version     : v1.1  (2026-06-22 evening - Phase 3 best params locked in)
Timeframe   : Data1 = 60M (sole feed, no multi-TF)
Class       : Volatility Regime (C class) - Long only (Rule R-6 split)
Direction   : Long only
```

**重點**：
- **單 timeframe 60M** — 不像 L1/L5/S1 雙時間框架，這隻只用 Data1=60M
- **Long only** — R-6 split 強制：S3_S (VolSqueezeShort) 是 R-6 對手，獨立 .pla
- **C class** — 波動率型，alpha 來源 = vol expansion，不是 trend/range

### 0.2 R-6 split 標示（line 16-18）

```pla
R-6 split (2026-06-22): original bi-directional -> Sx_L pure long + Sx_S pure short
Order rule: L first, S second (TXF1 2020-2026 bullish regime)
This file is the L (long) version; S3_S VolSqueezeShort follows in next phase.
```

→ 違反 R-6（在這檔加入 short logic）= 違規 CLAUDE.md Rule #14。

### 0.3 v1.1 Changelog（line 20-38）

5 個 inputs 從 archive defaults 改到 Phase 3 GA 最佳：

| Input | v1.0 (archive) | v1.1 (Phase 3 best) |
|-------|---------------|-------------------|
| BBLen | 20 | **45** |
| BWPctile | 20 | **30** |
| StopATRMult | 1.5 | **2.75** |
| TargetATRMult | 3.0 | **8.0** ⚠️ upper edge |
| MaxBars | 40 | **70** |

**v1.1 Phase 3 績效**：
- Net 2,654,000 NTD / PF gross 2.55 / PF 含滑價 2.00
- Sharpe 1.02 / Sortino 0.84 / Max DD 13.1% / WR 53.0%
- 134 trades / vs B&H 1.07x（**overtake 機構級**）
- 7/7 institutional gates PASS

⚠️ **TargetATRMult=8.0 仍在上邊角** → 用戶選 W4 WFA 不再推 Phase 4，避免 overfit。

### 0.4 Alpha Thesis（line 40-48）

```pla
Bollinger BandWidth (BBW) compressed to 20-percentile of past 120 periods
= volatility squeeze, statistically anticipates expansion.
Long entry: Squeeze condition + Close > Upper Band (upward breakout).
Theory: vol cycle expansion -> directional follow-through.
```

**alpha 核心邏輯**：
1. BBW 量化「波動率壓縮程度」（百分位排名）
2. 壓縮 = 統計上接近 vol cycle 底
3. 突破上軌 = 向上 vol expansion 啟動訊號
4. 賺 expansion 的 directional follow-through

**重要 disclaimer**：
- Archive 雙向版日線回測 PF 0.88（虧錢）
- 但 archive 明說「60M 行為不同」
- MC12 60M 才是 truth gate（v1.1 證實 PF 2.55）

### 0.5 Lesson Check（line 56-62）

```pla
1. CLOSED TIME INTERVALS (Rule MC_Time_24hr):
   60M bars - holiday tail detection at Time<=500 within day boundary;
   all Time>=X conditions paired with state guards OR explicit Time<=Y.
2. FILTER REDUNDANCY CHECK (Rule Filter_Redundancy):
   BBW + Close>Upper = 2 conditions, orthogonal. Squeeze = state, Close = trigger.
3. VOLUME SIGNAL: not used (S2 v0.4 lesson; archive S3 also didn't use volume).
```

→ 3 條從歷史 lessons 學到的設計檢查（embedded reminders）。

### 0.6 Constitution Compliance（line 64-69）

對齊 CLAUDE.md 4 條強制規範：

| Rule | 內容 | 本檔位置 |
|------|------|---------|
| #11 | Settlement_Flat 7 元素 | §5 + §11 P0-4 |
| #12 | P3b SetStopLoss | §9 |
| #13 | 10-dim eval | W5 已完成 |
| #14 | OFFICIAL_ROADMAP 對齊 | S3_L 是排程下一個 |

### 0.7 Label Conventions（line 71-74）

```
LE_VS_*  long entry labels  (Long Entry, VolSqueeze)
LX_VS_*  long exit labels   (Long eXit, VolSqueeze)
No Short labels (R-6 split produced separate S3_S file).
```

→ **嚴格 LE_/LX_ 區分**（feedback_mc_entry_exit_labels）

### 0.8 IOG Declaration（line 88）

```pla
[IntrabarOrderGeneration = false]
```

**規範**：
- 必須在所有程式碼前明確宣告 `false`
- L1-L5/S1/S3_RPS 全部都 false（一致性）
- IOG=false → SetStopLoss 進入信號 bar 即生效（Rule #12 預設）

---

## §1. INPUTS（line 91-121, 14 inputs）

### 1.1 Bollinger Bands 核心 4 inputs（line 98-102）

```pla
BBLen                     ( 45    ),   { Phase 3 best; range 35..55 plateau confirmed }
BBStd                     ( 2.0   ),   { Locked; not optimized this run }
BWLookback                ( 120   ),   { Locked; not optimized this run }
BWPctile                  ( 30    ),   { Phase 3 best; range 20..35 plateau confirmed }
```

| Input | 用途 | v1.1 值 | 範圍 |
|-------|------|---------|------|
| BBLen | BB 計算期數（mid = SMA(Close, BBLen)）| 45 | 35-55 確認 plateau |
| BBStd | BB 標準差倍數 | 2.0 | 未掃 |
| BWLookback | BWRank 計算回看期 | 120 | 未掃 |
| BWPctile | Squeeze 觸發百分位（≤ 即進入 squeeze state）| 30 | 20-35 確認 plateau |

**設計邏輯**：
- BBLen=45 + BWLookback=120 → 至少需 120 根 60M bars 暖機 ≈ 7-10 trading days
- BWPctile=30 → 比 archive 20 寬鬆，捕捉更多 squeeze 訊號（樣本 +50%）
- 兩者都中間 plateau = 對單一 best params 不敏感（reduces overfit risk）

### 1.2 ATR 系列（line 104-107）

```pla
ATR_Len                   ( 14    ),   { Locked; not optimized this run }
StopATRMult               ( 2.75  ),   { Phase 2 best plateau (P2 confirmed) }
TargetATRMult             ( 8.0   ),   { Phase 3 best; UPPER EDGE (range 5.5..8.0), Mid exit 37% }
```

**用途**：
- `ATR_Len=14`：標準 ATR 期數
- `StopATRMult=2.75`：SL 距離 = ATR × 2.75 → Phase 2 plateau 中位確認
- `TargetATRMult=8.0`：TP 距離 = ATR × 8.0 → ⚠️ 仍 upper edge

**TargetATRMult=8 的 implication**：
- TP 距離 ATR × 8 ≈ 大多 trades 的 MFE 上限
- → Mid exit 占 37%（替代 TP 成主要出場）
- 用戶決定不再推 Phase 4 (TargetATR 9-12) 避免 overfit

### 1.3 Exit timing（line 109-112）

```pla
MaxBars                   ( 70    ),   { Phase 2 best plateau (P2 confirmed); 60M => 70hr cap }
UseMidExit                ( True  ),   { mid-band exit on/off, A/B test }
MidExit_MinBars           ( 3     ),   { min bars held before mid exit arms }
```

| Input | 用途 |
|-------|------|
| MaxBars=70 | 持倉超過 70 根 60M bar (≈ 70 小時) 強制 time stop |
| UseMidExit=True | Mid-band exit 開（A/B test 證實 ON 更佳）|
| MidExit_MinBars=3 | 進場後至少 3 根 K 才 arms mid exit（避免 entry bar 立即出）|

### 1.4 Cooldown（line 114-115）

```pla
Cooldown_Days             ( 1     ),   { cooldown days after exit, opt 0..3 }
```

- 出場後 1 個日曆日內不可再進場
- 防同日多次進場（intra-day churn）

### 1.5 Priority 0 Protection（line 117-121）

```pla
Holiday_Flat_Time         ( 415   ),   { 60M grid -> fire 04:15 holiday tail }
Registry_Valid_Until      ( 1270101 ), { TAIFEX-verified horizon; bump each Q4 }
Manual_Kill_Switch        ( False ),
Settlement_Flat_Time      ( 1230  );   { 1hr buffer before 13:30 settlement }
```

| Input | 用途 |
|-------|------|
| Holiday_Flat_Time=415 | 假日前夜盤 04:15 觸發強制平倉 |
| Registry_Valid_Until=1270101 | 假日登錄表有效至 2027-01-01 (Q4 2026 重建) |
| Manual_Kill_Switch=False | 手動緊急停用 (預設 OFF) |
| Settlement_Flat_Time=1230 | 結算日 12:30 強制平倉 (1 小時 buffer 防結算 vol) |

→ 全部對應 CLAUDE.md Rule #11 Settlement_Flat 7 元素。

---

## §2. VARIABLES（line 124-164）

### 2.1 Bollinger Bands 變數（line 129-136）

```pla
v_MidBand                ( 0     ),
v_UpperBand              ( 0     ),
v_LowerBand              ( 0     ),
v_BandWidth              ( 0     ),
v_BWRank                 ( 0     ),
v_BWCount                ( 0     ),
v_Squeeze                ( False ),
```

| 變數 | 用途 |
|------|------|
| v_MidBand | BB 中軌（SMA Close, BBLen）|
| v_UpperBand | BB 上軌 = Mid + Std × BBStd |
| v_LowerBand | BB 下軌 = Mid - Std × BBStd |
| v_BandWidth | BBW = (Upper - Lower) / Mid × 100 (%)|
| v_BWRank | 當前 BBW 在過去 BWLookback 期的百分位排名（低 = 壓縮）|
| v_BWCount | BWRank 計算用 counter |
| v_Squeeze | bool: BWRank ≤ BWPctile（壓縮狀態）|

### 2.2 ATR 變數（line 139-141）

```pla
v_ATR                    ( 0     ),
v_StopDist               ( 0     ),
v_TargetDist             ( 0     ),
```

| 變數 | 用途 |
|------|------|
| v_ATR | 當下 ATR(14) |
| v_StopDist | SL 距離 (= ATR × StopATRMult) |
| v_TargetDist | TP 距離 (= ATR × TargetATRMult) |

### 2.3 Trade state（line 144-145）

```pla
v_EntryBar               ( 0     ),
v_Prev_MP                ( 0     ),
```

- `v_EntryBar`：進場 bar number，用於計算持倉長度
- `v_Prev_MP`：上一根 K 的 MarketPosition，用於偵測 exit 事件（per Rule #8）

### 2.4 Frozen SL 變數（line 148-151）— **belt-and-suspenders Rule #12**

```pla
v_SL_Locked              ( False ),
v_Frozen_ATR             ( 0     ),
v_Frozen_SL_Dist         ( 0     ),
v_SL_Level               ( 0     ),
```

**Frozen SL 設計**：
- 進場後 ATR 會浮動（每根 K 重算），但 SL 距離應**鎖死**避免 drift
- `v_SL_Locked` = True 時，`v_Frozen_ATR / v_Frozen_SL_Dist / v_SL_Level` 鎖在進場 bar 值
- Section 9 詳細實作

### 2.5 Cooldown 變數（line 154-155）

```pla
v_LastExit_Date          ( 0     ),
v_Cooldown_Active        ( False ),
```

- `v_LastExit_Date`：最後出場日期（YYYMMDD 數字）
- `v_Cooldown_Active`：當前是否在冷卻

### 2.6 Priority 0 state（line 158-164）

```pla
v_Holiday_Block          ( False ),
v_Registry_Expired       ( False ),
v_Settlement_Day         ( False ),
Registry_Warn_ID         ( -1    ),
hidx                     ( 0     ),
v_i                      ( 0     ),
ExitFired                ( 0     );
```

| 變數 | 用途 |
|------|------|
| v_Holiday_Block | 假日尾段 bar 旗（True = 禁止進場 + 觸發 P0-3 出場）|
| v_Registry_Expired | 登錄表過期旗（True = 觸發 P0-2 出場）|
| v_Settlement_Day | 結算日旗（True = 禁進場 + 觸發 P0-4 出場）|
| Registry_Warn_ID | 過期警告文字 Text_New 物件 ID |
| hidx / v_i | for loop counters |
| ExitFired | 當下 bar 是否已觸發出場（防多重出場）|

---

## §3. ARRAYS（line 167-173）

```pla
arrays:
    Holiday_Tail[80]( 0 );
```

- 80 槽，63 用，預留 17（2027-2028 擴充）
- 跟 L1-L5 / S1 / S3_RPS byte-identical（同一份 TAIFEX 登錄表）

---

## §4. HOLIDAY TAIL REGISTRY（line 176-265）

### 4.1 結構

```pla
if CurrentBar = 1 then begin
    Holiday_Tail[1]  = 1190913;
    ...
    Holiday_Tail[63] = 1270101;
end;
```

- 只在 CurrentBar=1 載入（一次性 init）
- 日期格式 = YYYMMDD（TXF1 / TAIFEX 系統慣例，1190913 = 2019/09/13）

### 4.2 Holiday_Tail 定義

> **Holiday_Tail = 最後交易日 + 1 個日曆日**
> = 最後夜盤 00:00-05:00 那段尾段 bar 的日期 stamp

例子：2026 CNY 最後交易日 2/11，夜盤跨日 2/12 凌晨 → `Holiday_Tail[54] = 1260212`

### 4.3 63 個日期分布

| 年份 | 數量 | 範例 |
|------|------|------|
| 2019 | 3 | CNY/雙十/元旦 |
| 2020 | 8 | 完整年 |
| 2021 | 7 | |
| 2022 | 8 | |
| 2023 | 8 | |
| 2024 | 8 | |
| 2025 | 10 | 多了多個補假 |
| 2026 | 10 | TAIFEX 115 年完整月曆驗證 |

→ **2027 起需 Q4 2026 從 TAIFEX 116 年月曆重建**（line 264 註）

---

## §5. HOLIDAY / REGISTRY / SETTLEMENT DETECTION（line 268-308）

### 5.1 Holiday Block detection（line 275-282）

```pla
v_Holiday_Block = False;

if Time < 500 then begin
    for hidx = 1 to 80 begin
        if Date = Holiday_Tail[hidx] then
            v_Holiday_Block = True;
    end;
end;
```

**邏輯**：
- 每根 bar reset `v_Holiday_Block = False`
- 若當下 Time < 500（夜盤尾段，00:00-04:59）且 Date 命中 registry → `v_Holiday_Block = True`
- `Time < 500` **嚴格 <**（per S1 v2.3 架構規則，避免 Time=500 cross-holiday fill）

### 5.2 Registry Expired detection（line 284-289）

```pla
v_Registry_Expired = False;

if Date > Registry_Valid_Until then begin
    v_Registry_Expired = True;
    v_Holiday_Block    = True;
end;
```

- 若 Date 超過 `Registry_Valid_Until` (1270101) → 視為過期
- 同時 `v_Holiday_Block = True`（雙重保護）

### 5.3 Settlement Day detection（line 292-294）

```pla
v_Settlement_Day = ( DayOfWeek( Date ) = 3 ) and
                   ( DayOfMonth( Date ) >= 15 ) and
                   ( DayOfMonth( Date ) <= 21 );
```

**邏輯**：
- TXF1 月結算日 = 每月第 3 個週三
- DayOfWeek = 3 (Wed) AND DayOfMonth 在 15-21 之間 = 第 3 個 Wed

### 5.4 Registry 過期警告（line 297-308）

```pla
if LastBarOnChart and
   DateToJulian( Date ) >= DateToJulian( Registry_Valid_Until ) - 30 then begin
    if Registry_Warn_ID < 0 then begin
        Registry_Warn_ID = Text_New( Date, Time, High + 400,
            "HOLIDAY REGISTRY EXPIRES " +
            NumToStr( Registry_Valid_Until, 0 ) +
            " - REBUILD FROM TAIFEX CALENDAR" );
        Text_SetColor( Registry_Warn_ID, Red );
        Text_SetSize( Registry_Warn_ID, 14 );
        Text_SetAttribute( Registry_Warn_ID, 1, True );
    end;
end;
```

**邏輯**：
- 過期前 30 天起，在 chart 顯示紅色 14-point 警告文字
- `Registry_Warn_ID < 0` 確保只創一次（不重複）
- 提醒在 Q4 2026 重建 2027+ registry

---

## §6. BB + SQUEEZE DETECTION（line 311-340） — **核心 alpha**

### 6.1 Bollinger Bands 計算（line 320-322）

```pla
v_MidBand   = Average( Close, BBLen );
v_UpperBand = v_MidBand + BBStd * StandardDev( Close, BBLen, 1 );
v_LowerBand = v_MidBand - BBStd * StandardDev( Close, BBLen, 1 );
```

- Mid = SMA(Close, BBLen=45)
- Upper / Lower = Mid ± 2.0 × StdDev(Close, 45, 1)
- 標準 BB 設定（同 archive）

### 6.2 BandWidth 計算（line 324-327）

```pla
if v_MidBand > 0 then
    v_BandWidth = ( v_UpperBand - v_LowerBand ) / v_MidBand * 100
else
    v_BandWidth = 0;
```

- BBW = (Upper - Lower) / Mid × 100
- **百分比化** → 跨價格層級可比（不受指數絕對值影響）

### 6.3 BWRank 計算（line 330-338）— **squeeze 核心**

```pla
v_BWCount = 0;
for v_i = 1 to BWLookback begin
    if v_BandWidth[v_i] > v_BandWidth then
        v_BWCount = v_BWCount + 1;
end;
if BWLookback > 0 then
    v_BWRank = v_BWCount / BWLookback * 100
else
    v_BWRank = 100;
```

**邏輯**：
1. Loop 過去 `BWLookback=120` 根 bar
2. 累計「**過去 BBW > 當前 BBW**」次數
3. BWRank = 累計次數 / 120 × 100

**解讀**：
- BWRank 低 = 當前 BBW 在歷史是 **低位**（壓縮）
- BWRank 高 = 當前 BBW 在歷史是 **高位**（已擴張）

⚠️ **archive bug 修正**：
- Archive 寫 `if v_BandWidth[v_i] < v_BandWidth` (count narrower)
- 我們改 `>` (count wider) → 邏輯一致：低 rank = 當前比過去多數狹窄 = squeeze
- 這是 v1.0 寫作時主動 patch 的 archive bug

### 6.4 Squeeze 旗（line 340）

```pla
v_Squeeze = ( v_BWRank <= BWPctile );
```

- `v_Squeeze = True` 當 BWRank ≤ 30 → 壓縮狀態
- 進場 condition 之一

---

## §7. ATR + STOP / TARGET DISTANCES（line 343-349）

```pla
v_ATR        = AvgTrueRange( ATR_Len );
v_StopDist   = v_ATR * StopATRMult;
v_TargetDist = v_ATR * TargetATRMult;
```

- 純計算，每根 bar 更新（除非 Frozen SL 鎖定後 §9 會覆蓋 v_StopDist）
- TargetDist 永不 freeze（TP limit 可隨 ATR 微浮動 — 但 archive S3 也這設計）

---

## §8. SAME-DAY COOLDOWN RESET（line 352-361）

```pla
if Date <> v_LastExit_Date and
   v_LastExit_Date > 0 and
   DateToJulian( Date ) - DateToJulian( v_LastExit_Date ) >= Cooldown_Days then
    v_Cooldown_Active = False;
```

**邏輯**：
- 當下日期 ≠ 最後出場日期 + 距出場 ≥ Cooldown_Days → 解除冷卻
- 例：Cooldown_Days=1 → 出場後跨日即可再進場
- `v_Cooldown_Active=False` 後 Section 10 entry gate 才會通過

---

## §9. FROZEN SL + SetStopLoss（line 364-396） — **Rule #12 雙重保險**

### 9.1 Frozen SL setup（line 376-389）

```pla
if MarketPosition = 1 then begin
    if v_SL_Locked = False then begin
        v_Frozen_ATR     = v_ATR;
        v_Frozen_SL_Dist = v_Frozen_ATR * StopATRMult;
        v_SL_Level       = EntryPrice - v_Frozen_SL_Dist;
        v_SL_Locked      = True;
    end;
end
else begin
    v_SL_Locked      = False;
    v_Frozen_ATR     = 0;
    v_Frozen_SL_Dist = 0;
    v_SL_Level       = 0;
end;
```

**邏輯**：
- 進場後第一根 bar (`MP=1` 且 `v_SL_Locked=False`)：
  - 鎖死 ATR / SL 距離 / SL 價格
  - 設 `v_SL_Locked=True`
- 平倉時 reset 全部變數（給下次進場準備）

**避免的 bug**：
- 沒 Frozen → ATR 浮動 → SL 距離浮動 → 進場 1 hr 後 SL 可能比進場 bar 「更遠」（vol up）或「更近」（vol down）
- Frozen 後 → SL 固定 = 進場 bar 設定值

### 9.2 SetStopLoss engine guard（line 391-396）

```pla
if v_SL_Locked = True then
    v_StopDist = v_Frozen_SL_Dist;

if MarketPosition <= 0 then
    SetStopLoss( v_StopDist * BigPointValue );
```

**兩段邏輯**：
1. 進場後（v_SL_Locked=True）：v_StopDist 覆寫成 Frozen 版（保證 SetStopLoss 用同距離）
2. `if MP <= 0` 才呼叫 SetStopLoss → 進場 bar 即 arm engine SL（per Rule #12 R-6 Long 變體）

**Why 雙重？**：
- `SetStopLoss` = MC engine 層級，進場成交瞬間生效（無 IOG 依賴）
- `LX_VS_SL` (Section 11 S-4) = 程式邏輯層級，as backup
- 兩者用同 `v_Frozen_SL_Dist` → 距離一致，不衝突
- 任何一邊失效都還有對手承接

---

## §10. ENTRY LOGIC（line 399-424）

### 10.1 7-gate entry（line 415-424）

```pla
if ( MarketPosition = 0 ) and
   ( v_Squeeze = True ) and
   ( Close > v_UpperBand ) and
   ( v_Cooldown_Active = False ) and
   ( v_Holiday_Block = False ) and
   ( v_Settlement_Day = False ) and
   ( v_Registry_Expired = False ) then begin
    buy( "LE_VS_Entry" ) next bar at Market;
    v_EntryBar = BarNumber;
end;
```

**7 個 gates 全 AND**：

| # | Gate | 用途 |
|---|------|------|
| 1 | `MarketPosition = 0` | 必空手才進場 |
| 2 | `v_Squeeze = True` | **alpha 核心條件 1** — BWW 壓縮 |
| 3 | `Close > v_UpperBand` | **alpha 核心條件 2** — 向上突破 |
| 4 | `v_Cooldown_Active = False` | 不在冷卻期 |
| 5 | `v_Holiday_Block = False` | 不在假日尾段 bar |
| 6 | `v_Settlement_Day = False` | 不是結算日 |
| 7 | `v_Registry_Expired = False` | Registry 仍有效 |

**Order**：`buy next bar at Market` → 當前 bar 收盤觸發 → 下根 bar 開盤成交

**v_EntryBar 記錄**：用於 Section 11 的 MaxBars / MidExit_MinBars 計算

### 10.2 Closed-interval 安全性（line 411-412）

```pla
{ Closed-interval safety: no isolated Time>=X conditions in entry block.
  All time-related gates are state-flag based (v_Holiday_Block / v_Settlement_Day). }
```

→ **per feedback_mc_time_24hr_pitfall**：所有 Time>=X 條件必有 Time<=Y 或 state guard
→ 本檔 entry 不直接用 Time 條件，全部透過 state flags

---

## §11. EXIT CHAIN（line 427-507） — **Priority 0 鐵則**

### 11.1 出場優先序（per Rule #11）

```
P0-1  LX_VS_Kill          (Manual_Kill_Switch)
P0-2  LX_VS_RegistryEnd   (registry expired)
P0-3  LX_VS_HolFlat       (holiday tail + Holiday_Flat_Time)
P0-4  LX_VS_Settlement    (settlement day + Settlement_Flat_Time)
S-1   LX_VS_TP            (ATR x 8 target, limit)
S-2   LX_VS_Mid           (mid-band exit, >=3 bars after entry)
S-3   LX_VS_TimeStop      (70 bars max hold)
S-4   LX_VS_SL            (Frozen SL backup at v_SL_Level Stop)
```

→ Priority 0 (P0-1 ~ P0-4) **必先檢查**，任一觸發即跳過 strategy exits

### 11.2 ExitFired 互斥旗（line 447）

```pla
ExitFired = 0;
```

每根 bar reset → 確保每 bar 最多 1 個出場 signal

### 11.3 P0-1 Manual Kill Switch（line 452-455）

```pla
if ( ExitFired = 0 ) and ( Manual_Kill_Switch = True ) then begin
    sell( "LX_VS_Kill" ) next bar at Market;
    ExitFired = 1;
end;
```

- 手動緊急停用（input 改 True 立即觸發出場）
- 優先序最高（任何狀況都先平倉）

### 11.4 P0-2 Registry Expired（line 458-461）

```pla
if ( ExitFired = 0 ) and ( v_Registry_Expired = True ) then begin
    sell( "LX_VS_RegistryEnd" ) next bar at Market;
    ExitFired = 1;
end;
```

- Registry 過期 → 安全失效，立即平倉
- 強制用戶必更新 registry 才能繼續

### 11.5 P0-3 Holiday Iron Rule（line 464-470）

```pla
if ( ExitFired = 0 ) and
   ( v_Holiday_Block = True ) and
   ( Time >= Holiday_Flat_Time ) and
   ( Time <= 455 ) then begin
    sell( "LX_VS_HolFlat" ) next bar at Market;
    ExitFired = 1;
end;
```

**3-gate**：
1. `v_Holiday_Block = True` (state guard)
2. `Time >= 415` (Holiday_Flat_Time)
3. `Time <= 455` (**閉區間，per Rule MC_Time_24hr**)

→ 04:15 ~ 04:55 之間，假日尾段 bar 強制平倉
→ Time≤455 防夜盤跨日後誤觸（不會延伸到下個交易日 00:xx）

### 11.6 P0-4 Settlement Flat（line 473-478）

```pla
if ( ExitFired = 0 ) and
   ( v_Settlement_Day = True ) and
   ( Time >= Settlement_Flat_Time ) then begin
    sell( "LX_VS_Settlement" ) next bar at Market;
    ExitFired = 1;
end;
```

- 結算日 12:30 後強制平倉
- 不需 Time≤X 因為 v_Settlement_Day 本身只在結算日整天 = True，且日盤 13:30 收盤後夜盤新時段已 reset

### 11.7 S-1 TP（line 484）

```pla
sell( "LX_VS_TP" ) next bar at EntryPrice + v_TargetDist limit;
```

- Limit order 在 `EntryPrice + ATR×8` 平倉
- 永久 active（每 bar re-issue，MC 慣例）

### 11.8 S-2 Mid-band exit（line 487-492）

```pla
if UseMidExit = True and
   BarNumber - v_EntryBar >= MidExit_MinBars and
   Close < v_MidBand then begin
    sell( "LX_VS_Mid" ) next bar at Market;
    ExitFired = 1;
end;
```

**3 conditions AND**：
1. UseMidExit 開（input control）
2. 持倉 ≥ 3 根 K（防 entry bar 立即出）
3. 當前 Close < BB 中軌（vol breakout 失敗 / mean reversion 訊號）

→ 「不再 trending 就先收」的 mean reversion 出場

### 11.9 S-3 Time Stop（line 495-499）

```pla
if ExitFired = 0 and
   BarNumber - v_EntryBar >= MaxBars then begin
    sell( "LX_VS_TimeStop" ) next bar at Market;
    ExitFired = 1;
end;
```

- 持倉 ≥ 70 根 60M bar (= 70 hr ≈ 3 個交易日) → 強制平倉
- 防 vol expansion 沒到 TP 也沒回中軌的 stagnant 持倉

### 11.10 S-4 Frozen SL Backup（line 502-503）

```pla
if ExitFired = 0 and v_SL_Locked = True then
    sell( "LX_VS_SL" ) next bar at v_SL_Level Stop;
```

- Stop order 在 `v_SL_Level` (= EntryPrice - Frozen_SL_Dist) 平倉
- 跟 Section 9 SetStopLoss 同距離（雙重保險）
- 任一觸發即 cover（兩個 stops 在同一價）

---

## §12. COOLDOWN SET ON EXIT（line 510-519）

```pla
if v_Prev_MP = 1 and MarketPosition <> 1 then begin
    v_Cooldown_Active = True;
    v_LastExit_Date   = Date;
end;
```

**邏輯**：
- 偵測 transition: 上一根 MP=1 (有 long position) → 當下 MP≠1 (已平倉)
- → 觸發 cooldown：`v_Cooldown_Active = True`, 記錄 `v_LastExit_Date = 當下 Date`
- Section 8 會在跨日 + 滿 Cooldown_Days 後 reset 為 False

→ 這是 **Rule #8 v_Prev_MP 追蹤的標準用法**（exit 偵測必透過 transition）

---

## §13. PREV_MP TRACKING（line 522-526）— **Rule #8 最末行**

```pla
v_Prev_MP = MarketPosition;
```

**重要規範**：
- **必須在腳本最末行** (per CLAUDE.md Rule #8)
- 更新 v_Prev_MP 給下根 bar 用
- 不可在 Section 12 內或更早位置（會破壞 transition 偵測）

---

## 規範對齊驗證

| Rule | 內容 | 本檔位置 | 狀態 |
|------|------|---------|------|
| #1 | inputs: 宣告 | §1 (14 inputs) | ✅ |
| #2 | variables: 宣告 v_ 前綴 | §2 | ✅ |
| #3 | Data2 [1] 索引 | N/A (單 timeframe) | ✅ |
| #4 | 不用未來函數 | 全檔 | ✅ |
| #5 | buy/sell short next bar at | §10 entry | ✅ |
| #6 | sell/buy to cover next bar at | §11 exit | ✅ |
| #7 | 不同 K 用 marketposition | 全檔（透過 v_Prev_MP）| ✅ |
| #8 | v_Prev_MP 末行更新 | §13 (line 526) | ✅ |
| #9 | STRATEGY_GEN_ 前綴 | Header line 3 | ✅ |
| #10 | < 150 行 / 進場 ≤ 5 個條件 | ❌ 527 行 / 7 條件 | ⚠️ 超出 simple 規範但因合規模組必含 |
| #11 | Settlement_Flat 7 元素 | §4, §5, §11 P0 | ✅ |
| #12 | P3b SetStopLoss | §9 (line 395-396) | ✅ |
| #13 | 10-dim eval | W5_10dim_evaluation.md | ✅ |
| #14 | OFFICIAL_ROADMAP 對齊 | S3_L per roadmap | ✅ |

### Rule #10 例外說明

> CLAUDE.md #10：「每隻策略 < 150 行，進場條件 ≤ 5 個」

S3_L 527 行 + 7 個進場 gates 看似違反，但實際上：
- ~90 行 Header docs
- ~80 行 Holiday registry (63 entries，與 L1-L5 相同)
- ~50 行 Priority 0 detection + Frozen SL infrastructure
- **純策略邏輯** ≈ 60 行（squeeze + breakout + 4 exits）
- 進場 7 gates 中 4 個是合規 gates（Holiday/Settlement/Registry/Cooldown）

→ 跟 L1-L5 / S1 / S3_RPS 同等規模，**Rule #10 應理解為「核心策略邏輯」尺度**，合規模組為例外。

---

## v1.1 績效快照（Phase 3 best, 2020-01-20 ~ 2026-06-06, MC12 60M）

| 指標 | 值 |
|------|-----|
| Net Profit | **2,654,000 NTD** |
| PF gross | 2.55 |
| **PF 含滑價** | **2.00** |
| Sharpe (年化) | **1.02** |
| Sortino | 0.84 |
| Calmar | 3.18 |
| Max DD % | 13.1% |
| Win Rate | 53.0% |
| Trades | 134 |
| **vs B&H** | **1.07x (OVERTAKE)** |
| Annual return | 41.6% |
| Single max loss | -124,200 (2026-04-02 川普關稅 gap) |

**Status**: 7/7 institutional gates PASS + W4 WFA 6/9 pass + W5 10-dim 7/10 PASS → **promoted to live_simulation/ 2026-06-23**

---

## 部署 Caveats（**必讀**）

詳見 [S3_VolSqueezeLong_DEPLOYMENT.md](S3_VolSqueezeLong_DEPLOYMENT.md)：

1. **Portfolio allocation ≤ 5%**（single trade tail 隔離）
2. **不可加 Pre-event Flat / event filter**（違反 Lesson L24）
3. **不可改 Long-only direction**（違反 R-6）
4. **等 S3_S 上線後 L+S 配對** = 真實 directional hedge
5. **Kill triggers**: 單筆 > 250K / PF < 1.0 持續 10 筆 / MDD > 25%

---

## 相關文件

- [S3_VolSqueezeLong.pla](S3_VolSqueezeLong.pla) — 程式碼本體
- [S3_VolSqueezeLong_DEPLOYMENT.md](S3_VolSqueezeLong_DEPLOYMENT.md) — 部署 manifest + caveats
- [../research/S03_VolSqueezeLong/W5_10dim_evaluation.md](../research/S03_VolSqueezeLong/W5_10dim_evaluation.md) — W5 機構級評估
- [../research/S03_VolSqueezeLong/progress_20260622_phase3_handoff.md](../research/S03_VolSqueezeLong/progress_20260622_phase3_handoff.md) — Baseline → P3 軌跡
- [../research/S03_VolSqueezeShort/README.md](../research/S03_VolSqueezeShort/README.md) — R-6 對手 (S3_S CURRENT)
- [../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md](../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md) — L24 lesson
- [../../docs/policies/OFFICIAL_ROADMAP.md](../../docs/policies/OFFICIAL_ROADMAP.md) — 排程
