# S3_S v1.9.6-OPT-PROD 進場閘門審計報告（2026-07-07）

- **審計對象**：`strategies/live_simulation/S3_S_VolSqueezeShort.pla`（1,124 行，commit `e81c26b` 之後的 v1.9.6-OPT-PROD）
- **審計範圍**：進場條件失效模式（entry-condition failure modes）——找出可能讓進場「永不觸發或異常稀少」的路徑
- **審計方式**：subagent 全檔逐行讀取，10 項檢查清單（gate 鏈 / 死鎖組合 / warm-up / 跨午夜時間邏輯 / registry 到期 / cooldown 永久封鎖 / 掛單機制 / ML gating / 部位旗標 / Data2/Data3 索引）
- **性質**：純診斷，本報告未修改任何程式碼

---

## 總體判定

**當前 Config B + OPT 參數組下，沒有發現「立即」使進場永久失效的邏輯 bug。**
所有狀態鎖（熔斷、cooldown、hunt DISARM）均有已驗證的 reset 路徑；4 處時間比較無跨午夜錯誤；進場市價單無成交機制風險。

真正的結構性風險按時序：
1. **Finding 1（BLOCKER）**：2027-01-01 registry 到期是有明確日期的全面進場死線，警告可見性依賴 LastBarOnChart。Q4 2026 重建 registry 是硬性待辦。
2. 低進場頻率（71 筆 / 6.5 年 ≈ 11 筆/年）主要由 Finding 2 / 3 / 13 三個設計性壓縮共同造成。
3. Finding 12（kill switch）與 Finding 14（參數與文件不一致）建議在下一次維護窗口處理。

---

## 完整進場 AND 鏈

進場邏輯唯一入口在 Section 10（`:890-903`）：

```
if BarStatus(2) = 2 then begin
    if ( MarketPosition = 0 ) and
       ( v_Hunt_Active = True ) and
       ( Close of Data2 < v_LowerBand ) and
       ( Close of Data2 < v_Hunt_Low - Thrust_Margin_ATR * v_ATR ) and
       ( Use_Cooldown = False or v_Cooldown_Active = False ) and
       ( v_Holiday_Block = False ) and
       ( v_Settlement_Day = False ) and
       ( v_Registry_Expired = False ) and
       ( v_Regime_OK = True ) then begin
        sell short ( "SE_VS_Entry" ) next bar at Market;
```

| # | 閘門 | 上游依賴 |
|---|------|---------|
| G0 | `BarStatus(2) = 2`（僅在 60M 收盤的那根 1M 棒評估） | Data2 資料流 |
| G1 | `MarketPosition = 0` | — |
| G2 | `v_Hunt_Active = True` | v_Squeeze（← v_BWRank ← BW_History 環形緩衝 ← v_BW_Filled）+ EqualGuard + 熔斷器 DISARM（Section 12） |
| G3 | `Close of Data2 < v_LowerBand` | BB(45, 2.0) of Data2 |
| G4 | `Close of Data2 < v_Hunt_Low - 0.15 * v_ATR` | v_Hunt_Low（Section 6 ARM + Section 10.5 ratchet）、v_ATR of Data2 |
| G5 | `Use_Cooldown = False or v_Cooldown_Active = False`（預設恆真） | Section 8 / 12 |
| G6 | `v_Holiday_Block = False` | Section 5 registry 掃描（僅 Time < 500）+ registry 過期強制 True |
| G7 | `v_Settlement_Day = False` | 週三 + 15≤日≤21（`:518-520`） |
| G8 | `v_Registry_Expired = False` | `Date > Registry_Valid_Until`（`:512`） |
| G9 | `v_Regime_OK = True` | Data3 日線 MA15/MA40 ratio 區間（`:542-563`） |

注意：**`Manual_Kill_Switch` 不在進場閘門中**（見 Finding 12）。

---

## 逐項 Findings

### Finding 1 — Registry 到期日 = 全策略進場死線（定時炸彈）
**SEVERITY: BLOCKER（結構性、有日期的必然阻斷）**
位置：`:236`、`:510-515`、`:896-898`

```
Registry_Valid_Until      ( 1270101 ),
...
if Date > Registry_Valid_Until then begin
    v_Registry_Expired = True;
    v_Holiday_Block    = True;
end;
```

`Date > 1270101` 之後，G6 與 G8 兩個閘門同時永久失效，進場完全停止（且 P0-2 會把持倉強制平倉）。這是 Rule #11 的 fail-safe 設計，但屬於「靜默失效」：審計日 2026-07-07，剩餘 runway 約 178 天，2027-01-02 起（1/1 為假日）第一個交易日進場全滅。紅字警告（`:523-534`）只在 `LastBarOnChart` 且距到期 30 天內（2026-12-02 起）才繪製。註解 `:492` 已標記「2027 CNY onward: rebuild from TAIFEX 116-yr calendar in Q4 2026」。

### Finding 2 — BWRank EqualGuard 會封鎖「歷史最窄帶寬」的正牌 squeeze 棒
**SEVERITY: MODERATE（特定 regime 下可長時間阻斷 ARM）**
位置：`:593-613`

```
v_BWCount = 0;
for v_i = 1 to v_BW_Filled begin
    if BW_History[v_i] < v_BandWidth then
        v_BWCount = v_BWCount + 1;
end;
...
if BWRank_EqualGuard_On = True and
   v_BWCount = 0 and
   v_BW_Filled >= BWRank_MinFilled then
    v_Squeeze = False;
```

Guard 本意是修「全部歷史 BW 相等 → count=0 → rank=0 → 假訊號」的退化案例，但 `v_BWCount = 0` 同時涵蓋「當前 BW 是 lookback 120 根內的新低」這個合法且最強的 squeeze 情境（嚴格 `<` 比較，新低棒必然 count=0）。失效情境：波動率單調收縮 regime 中每根 60M 棒都創 BW 新低 → 每根 count=0 → Config B 下 `v_Squeeze` 整段收縮期恆為 False → hunt 遲遲不 ARM。多數情況只延遲數棒，且 ARM 棒本身可同棒進場（Section 6 先於 Section 10 執行），但在「深度單調壓縮後直接崩跌」劇本裡，ARM 可能延遲到崩跌棒才發生，進場門檻變成 `Close < LowerBand - 0.15*ATR`，比正常 ARM 序列更嚴。Config B 相對 baseline 的已知代價，但「封鎖的正好是最深壓縮棒」這個副作用記錄在案。

### Finding 3 — Regime Filter 與 squeeze 本質上的統計衝突（半死閘組合）
**SEVERITY: MODERATE（結構性頻率壓縮）**
位置：`:551-560`、`:899`

```
v_In_WeakBull_Zone = ( v_Regime_Ratio > 1.02 ) and ( v_Regime_Ratio < 1.05 );
v_In_Range_Zone = ( v_Regime_Ratio >= 0.98 ) and ( v_Regime_Ratio <= 1.02 );
```

G2（60M squeeze）與 G9（日線 MA15/MA40 ratio 必須 < 0.98 或 > 1.05）統計負相關：60M 帶寬收縮的盤整期，日線快慢均線通常也在收斂（ratio → 1），恰好落入被封鎖的 [0.98, 1.02]。等於策略只能在「日線已明確走空或強多」時吃 squeeze breakdown——回測過的設計（71 筆），但橫盤年份裡這兩個閘門可以連續數月互斥，進場數趨近零不是 bug，是天性。暖機期副作用：Data3 MA 尚未成形時若 `v_MA_Slow_D = 0`，`:546-549` 令 ratio = 1 → 落入 Range Zone → 封鎖進場（fail-closed，方向安全）。

### Finding 4 — 圖表歷史長度不足 / 中途重載 = 靜默零進場
**SEVERITY: MODERATE（營運面，實務最常見的「怎麼都不進場」原因）**
位置：`:599-602`、`:629-634`、`:543-544`、`:93`

三層暖機需求疊加：(a) BWRank 需要 BW_History 填滿至 BWLookback=120 根 60M 棒（約 6-7 個交易日）才有統計意義，`v_BW_Filled = 0` 時 rank=100 → 永不 squeeze（fail-closed）；(b) Regime 需要 Data3 至少 41 根日線；(c) `v_Hunt_Active` 是從圖表第一根棒重放建立的狀態機——中途重載圖表且資料範圍未涵蓋當前 episode 的 ARM 棒時，hunt 處於未武裝狀態，直到下一次 squeeze 才恢復進場能力。所有狀態變數皆非 IntraBarPersist、由歷史重放重建，重載不會「永久卡死」，但「重放結果 ≠ 重載前狀態」（BW 緩衝內容隨圖表起點改變）會造成訊號漂移。**營運建議：固定圖表資料範圍下限 ≥ 60 個交易日**（覆蓋 120 根 60M + 41 根日線 + 當前 episode）。

### Finding 5 — v_BW_Filled 在 1~4 根時 EqualGuard 不生效，可能暖機期假 ARM
**SEVERITY: INFO**
位置：`:265`、`:610-612`

`BWRank_MinFilled = 5`：`v_BW_Filled` 在 1..4 且當根 BW 最窄時，count=0 → rank=0 → `v_Squeeze = True` 且 Guard 因 filled < 5 不生效 → 暖機頭 4 根 60M 棒可能假 ARM。方向是「多進場」而非阻斷，僅存在於全新圖表頭幾根，風險極低。

### Finding 6 — Hunt 熔斷器（Hunt_Max_Stops=4）：驗證無永久鎖死路徑
**SEVERITY: INFO（驗證通過）**
位置：`:616-626`、`:1099-1116`

reset 路徑三條全數確認：(a) 非 1M 出場歸零（`:1112-1113`）；(b) 熔斷觸發時歸零並 DISARM（`:1107-1109`）；(c) 新 episode ARM 時歸零（`:617-618`）。熔斷後 DISARM 非永久——下一根 `v_Squeeze = True` 即重新武裝並清零。頻率影響：熔斷後到下一次 squeeze 之間的所有 breakdown 都不進場（設計意圖，殺 churn）。`v_Was_1M_Stop` 橋接旗標在 Section 12 消費後清 False（`:1115`），回測/模擬中市價單必然成交，無卡死路徑；僅實盤委託被拒絕的極端情況可能殘留（v1.9.5 已知設計）。

### Finding 7 — Cooldown：預設短路，無風險；啟用時邏輯正確
**SEVERITY: INFO（驗證通過）**
位置：`:221`、`:668-670`、`:895`、`:1099-1101`

`Use_Cooldown ( False )` 使 G5 恆真（EL 中 `=` 優先於 `or`，括號語義正確）。若日後 GA 重新啟用：`v_LastExit_Date` 初始 0 有 `> 0` 保護（`:668`）；跨午夜後 Date 進位使 Julian 差 ≥ 1 天即解鎖，無永久鎖死。

### Finding 8 — 結算日偵測：純日期規則，封鎖整個日曆週三（含換月後夜盤），且假日順延時錯位
**SEVERITY: MODERATE（頻率壓縮 + 錯位風險）**
位置：`:517-520`、`:897`

```
v_Settlement_Day = ( DayOfWeek( Date ) = 3 ) and
                   ( DayOfMonth( Date ) >= 15 ) and
                   ( DayOfMonth( Date ) <= 21 );
```

兩個後果：(a) 結算週三 15:00-23:59 的夜盤（已是新月合約、結算風險已消失）進場一併被封——每月犧牲一個夜盤 alpha 時段（跨午夜後 Date 進位為週四即解封）；(b) 結算因國定假日順延（週三放假 → 週四結算）時封錯天：封了放假的週三（無害）、放行真正結算的週四（進場閘門漏洞 + 出場端 Settlement flat 也不觸發）。正是 auto-memory `feedback_settlement_holiday_rule` 警示的模式。**2026 下半年需逐月核對 TAIFEX 行事曆確認無順延結算日（未驗證）。**

### Finding 9 — 時間比較全面檢查：無午夜跨越 bug
**SEVERITY: INFO（驗證通過）**
位置：`:503`、`:651-654`、`:949-952`、`:958-960`

全檔 4 處時間窗比較逐一驗證：

```
if Time < 500 then begin                                  { :503  單邊比較，無 wrap }
if Time >= NightSL_Start_Time or Time < NightSL_End_Time  { :651  2200/500 用 OR，正確處理跨午夜 }
( Time >= Holiday_Flat_Time ) and ( Time <= 455 )         { :949-952  415-455 同側窗，無 wrap }
( Time >= Settlement_Flat_Time )                          { :960  1230 單邊，無 wrap }
```

進場本身沒有任何時段過濾——任何 60M 收盤（含 05:00 收盤棒）都可觸發；05:00 訊號的市價單將於 08:45 開盤成交（3h45m 跳空風險，屬滑價非阻斷）。微小邊角：假日 registry 封鎖只作用於 `Time < 500`，05:00 整點收盤棒不被 G6 封鎖，理論上可在假日尾端訊號後於假日後首日開盤進場——非阻斷型，備查。

### Finding 10 — ML_ScoreTrigger 與進場無關（釐清）
**SEVERITY: INFO**
位置：`:242`、`:718-868`、`:843-846`

`ML_ScoreTrigger ( 35 )` 只作用於出場端 1M 多層監控（Section 9.5 整段被 `if MarketPosition = -1 and v_1M_ExitFired = False` 包住）。計分上限 30 分，35% 門檻 = 需 ≥ 11 分 + 跨 ≥ 3 類 + 浮虧 > 凍結 SL 距離的 20%。不在進場 AND 鏈中；間接影響進場的唯一途徑是 1M 出場 → `v_Hunt_StopCount` → 熔斷器。OPT 把門檻 40→35 = 1M 出場更敏感 = 熔斷更快累積 = churn episode 更早停止進場——OPT 參數組的刻意取捨。

### Finding 11 — 進場單機制：市價單、單棒有效，無殘價/翻悔問題
**SEVERITY: INFO（驗證通過）**
位置：`:900`

`sell short ... next bar at Market` 不涉及價格變數，無 stale price / 掛遠不成交問題。IOG=False + `BarStatus(2)=2` 閘門 = 條件每 60M 評估一次，委託只存活到下一根 1M 棒即成交，無「條件閃爍撤單」窗口。G3/G4 用 `Close of Data2` 當根索引 `[0]`，但受 `BarStatus(2)=2` 保護，讀到的是剛完結的 60M 收盤（專案規範第 3 條要求 `[1]`，此處為守門式 `[0]`，功能正確但與規範字面不同，備查）。機制性依賴：若 Data2 收盤事件因 feed 異常未觸發 `BarStatus(2)=2`，該次 60M 評估直接消失——live 環境已知 MC 特性，建議模擬期比對 60M 棒數與評估次數（未驗證實際 feed 行為）。

### Finding 12 — Manual_Kill_Switch 不在進場閘門：開啟後會「出場-再進場」震盪
**SEVERITY: MODERATE（反向閘門缺失：該擋沒擋）**
位置：`:891-899`（缺席）、`:937-940`（僅出場）

進場 AND 鏈中沒有 `Manual_Kill_Switch = False`。持倉時打開 kill switch：P0-1 平倉 → 下一個 60M 收盤若條件仍成立 → 重新放空 → 又被 P0-1 平掉 → 循環（每輪付滑價）。與 Rule #11 Priority 0 精神（Kill > 原邏輯）不一致——Kill 目前只覆蓋出場側。

### Finding 13 — v_Hunt_Low 棘輪 + squeeze 刷新的雙向行為
**SEVERITY: INFO（設計如此，需理解頻率效應）**
位置：`:616-621`、`:913-916`、`:894`

Episode 內 `v_Hunt_Low` 經 Section 10.5 單向下修，G4 要求每次進場都要收破「episode 迄今所有低點再減 0.15×ATR」——連續進場門檻棘輪式墊高，緩跌/打底 regime 中第二筆之後的進場系統性稀少（v1.9.5 設計意圖，殺 T73 型邊際突破）。反向細節：episode 進行中若再現 squeeze 棒，`:620` 把 v_Hunt_Low 無條件重置回當根 LowerBand（通常高於已跌出的實際低點），等於放寬 G4——hunt 不會因棘輪永久自鎖，代價是部分弱化 fresh-thrust 保護。已驗證：不存在 `v_Hunt_Active = True` 而 `v_Hunt_Low = 0` 的狀態組合（會使 G4 永假）——所有設 0 路徑（`:624`、`:1108`）都同步設 Active=False。

### Finding 14 — 檔頭文件與實際 input 值不一致：Thrust_Margin_ATR
**SEVERITY: INFO（文件漂移，需人工確認 OPT 定案值）**
位置：`:68`、`:224`、`:884`

```
:68   Default 0.25 x ATR (~37-50 pts). A 1-point break cannot qualify.
:224  Thrust_Margin_ATR         ( 0.15  ),
:884  0.25 x ATR (~37-50 pts). Marginal
```

檔頭與 Section 10 註解都寫 0.25，實際 input 為 0.15。0.15 不在 PROMOTE 記錄的 5 參數 OPT 清單（BWPctile/StopATRMult/SP_Trigger/Hunt_Max_Stops/ML_Score）中。**未驗證**：0.15 是 GA 定案值還是誤植——若回測 xlsx 用的是 0.25，live_simulation 的進場會比已驗證組態更寬鬆（非阻斷方向，但偏離已驗證組態）。**待辦：對照 2026-07-06 回測參數表確認。**

### Finding 15 — 假日 registry 掃描迴圈：空槽安全
**SEVERITY: INFO（驗證通過）**
位置：`:402`、`:504-507`

`Holiday_Tail[80]` 只填到 index 63，64-80 為 0；`Date = 0` 永不成立，空槽無誤觸。`BW_History[150]` 對 BWLookback=120 界內安全（若 GA 日後掃 >150 會越界，界值備查）。

---

## 總表

| # | Finding | 嚴重度 | 位置 | 性質 |
|---|---------|--------|------|------|
| 1 | Registry 2027-01-01 到期 → 進場永久歸零（審計日剩 178 天） | **BLOCKER** | :236, :510-515, :896-898 | 設計內定時炸彈 |
| 2 | EqualGuard 封鎖歷史最窄 BW 棒；單調壓縮 regime 下延遲/阻斷 ARM | MODERATE | :593-613 | Config B 副作用 |
| 3 | Squeeze × Regime filter 統計互斥；Data3 暖機 fail-closed | MODERATE | :551-560, :899 | 結構性頻率壓縮 |
| 4 | 圖表歷史不足 / 重載 → BW 緩衝、Regime MA、Hunt 狀態機重建漂移 | MODERATE | :599-634, :543 | 營運風險 |
| 5 | v_BW_Filled 1-4 根時 Guard 未生效可能假 ARM | INFO | :610-612 | 暖機邊角 |
| 6 | 熔斷器無永久鎖死路徑（三條 reset 已驗證） | INFO | :616-626, :1099-1116 | 驗證通過 |
| 7 | Cooldown 預設短路，啟用時邏輯正確 | INFO | :668-670, :895 | 驗證通過 |
| 8 | 結算偵測封整個日曆週三（含新約夜盤）；假日順延結算錯位 | MODERATE | :517-520, :897 | 頻率成本+錯位 |
| 9 | 全部 4 處時間比較無午夜 wrap bug；進場無時段過濾 | INFO | :503, :651, :949, :960 | 驗證通過 |
| 10 | ML_ScoreTrigger 僅出場端；經熔斷器間接影響進場頻率 | INFO | :718-868 | 釐清 |
| 11 | 進場為市價單、單棒有效；無 stale price / 閃爍撤單 | INFO | :900 | 驗證通過 |
| 12 | Kill Switch 缺席進場閘門 → 開啟後出場-再進場震盪 | MODERATE | :891-899, :937-940 | 反向閘門缺失 |
| 13 | v_Hunt_Low 棘輪墊高 G4 門檻；squeeze 刷新防自鎖但弱化保護 | INFO | :616-621, :913-916 | 設計取捨 |
| 14 | Thrust_Margin_ATR 檔頭 0.25 vs 實值 0.15 不一致 | INFO | :68, :224, :884 | 文件漂移，需核對 |
| 15 | Registry 空槽 / 陣列界值安全 | INFO | :402, :504-507 | 驗證通過 |

---

## Live_simulation「長期零進場」除錯順序

1. Regime ratio 是否卡在 [0.98, 1.05]（F3）
2. BW 是否單調創低使 Guard 壓制 squeeze（F2）
3. Hunt 是否被熔斷且尚無新 squeeze（F6，非永久）
4. 圖表歷史是否足夠——建議資料範圍 ≥ 60 個交易日（F4）

## 後續動作（優先序）

1. **Q4 2026 registry 重建**列入 TRACKER 待辦（F1，硬死線 2027-01-01）
2. 核對 `Thrust_Margin_ATR = 0.15` 是否為 2026-07-06 GA 定案值（F14）
3. 下次維護窗口：Kill Switch 進場閘門（F12）+ 結算日假日順延規則（F8）
4. 逐月核對 2026 H2 TAIFEX 行事曆是否有順延結算日（F8）
