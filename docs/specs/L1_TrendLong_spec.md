# L1 TrendLong 規格

| | |
|---|---|
| 來源 | `WILLY_ATR_LONG_45M_V32_RESEARCH` (V3.2) |
| 行為等同 | V3.1（V3.2 的 re-entry 腿以 `ReEntry_On = 0` 出貨，完全惰性） |
| 週期 | Data1 **45M** · Data2 **Daily** · Data3 **Weekly** |
| IOG | **`true`** — 五支裡唯一 |
| 方向 | 純多 |
| 出場控制 | **無 ExitFired**。一根最多三張市價單（J-3，標頭自承未修） |
| SHA-256 | ⬜ |

> 策略名稱寫 60M，**實際圖表是 45M**。標頭自承：「name kept for live continuity」。

---

## 一 做什麼

價格向上穿越 MA61 加 2 倍 ATR 時進場做多。停損在進場當根凍結，取
**三條腿裡最緊的一條**。持倉中用 MA55 移動停損（單向棘輪）與峰值回吐保護，
三者取最高者為唯一出場價。

**單一停損架構**——與 L2/L4 的優先級鏈不同，L1 把所有保護合成一個價位。

---

## 二 進場

`Buy next bar at Market`，五個條件全成立（**在 `BarStatus(1) = 2` 守衛內**）。

| # | 條件 | 公式 |
|---|---|---|
| G1 | 空手 | `MP = 0` |
| G2 | 突破 | `Close Crosses Over (MA61 + ATR45 × 2.0)` |
| G3 | 週線濾網 | `Close of D3 > MA20` **或** `> MA60` |
| G4 | 非假日尾盤 | `v_Holiday_Block = false` |
| G5 | 非結算日 | `v_Settlement_Day = false` |

### 2.1 指標

```
maBase         = Average(Close, 61)
maTrail        = Average(Close, 55)
Current_ATR    = AvgTrueRange(20) of Data1
Daily_ATR      = AvgTrueRange(20)[1] of Data2        ← 有 [1]，V3.0 修正
Breakout_Level = maBase + Current_ATR × 2.0
Cond_Breakout  = Close Crosses Over Breakout_Level
```

> `Crosses Over` 是五支裡唯一使用穿越運算子的地方。它需要前一根的狀態，
> 在 IOG 下語意特別微妙——標頭註明「evaluated once per bar either way」，
> 因為整段包在 `BarStatus(1) = 2` 內。

### 2.2 週線濾網用 OR

```
v_Weekly_Filter = (Close of D3 > MA20) 或 (Close of D3 > MA60)
```

> **L5 用 AND，L1 用 OR。** 標頭理由：趨勢策略需要在趨勢起點就進場，
> AND 會錯過早期多頭階段。

### 2.3 Re-entry 模組（出貨即關閉）

`ReEntry_On = 0`，`v_IsReEntry` 永不為真，停損繼承分支永不執行，
不會下任何 re-entry 單。

**所有開關刻意宣告為數值 0/1 而非 TrueFalse**——MC12 的最佳化器完全不列出
TrueFalse 型別的 input，凡是需要被掃描或 A/B 的東西都必須是數字。

> 本模組的順序是承重的。註解明載：
> 「Main entry and re-entry are mutually exclusive **ONLY because** the new-cycle
> reset here clears the arm before the entry blocks execute. There is no explicit
> exclusion flag. Move this block below them and one bar can place two entry orders.」

---

## 三 IOG 語意 — L1 獨有

### 3.1 `BarStatus(1) = 2` 守衛

**在守衛內（每根 K 棒收盤執行一次）**：

- 核心指標（`maBase` `maTrail` `Current_ATR` `Daily_ATR` `Breakout_Level` `Cond_Breakout`）
- 週線濾網
- 假日 / 註冊表偵測
- 進場邏輯（含 re-entry 狀態機）
- P3 凍結停損的鎖定
- 跳空偵測分支
- MDD 視覺化

**不在守衛內（每個 tick 執行）**：

- `MP = MarketPosition`
- `SetStopContract` / `SetStopLoss`
- 結算日偵測
- **Section 3 出場管理的其餘部分**（P7 峰值追蹤、P4 棘輪、出場下單）
- Section 4 強制平倉
- `v_Prev_MP` 更新

### 3.2 `IntraBarPersist`

```
Variables: IntraBarPersist
    posbleProfit_Long, stopProfitPrice_L, v_Trail_High
```

沒有這個宣告，三個變數會在**每個 tick 重置回 bar-open 值**。
Python 版必須實作等價的 tick 間持久化語意。

### 3.3 P7 逐 tick 追蹤

```
若 (Close − Entry_P) >= 200：                       ← Close 是當下成交價
   若 (Close − Entry_P) > posbleProfit_Long：
      posbleProfit_Long = Close − Entry_P
   stopProfitPrice_L = Entry_P + posbleProfit_Long × (1 − 55/100)
```

V3.0 把門檻從 500 降到 200，**因為 IOG 讓更低的門檻變得可行**。

### 3.4 P4 單向棘輪

```
v_Trail_High = MaxList(v_Trail_High, maTrail − 50)
```

每 tick 執行，但 `maTrail` 只在收盤更新。V3.0 之前是雙向「呼吸」，
在回撤中會讓有效停損下沉。

> **回測需要 Bar Magnifier（至少 1 分鐘）。**

---

## 四 停損三層

### 4.1 P3 凍結初始停損 — 三條腿取最緊

```
在 BarStatus(1) = 2 且 v_SL_Locked = false 時計算一次：

Exit_Price_ATR = Entry_P − ATR45 × 1.5
Exit_Price_Cap = Entry_P − Daily_ATR × 0.5
Exit_Price_Pct = Entry_P − Entry_P × 0.5 / 100          （SL_Pct = 0 時為 0）

v_Frozen_SL = MaxList(ATR, MaxList(Cap, Pct))            ← 多單取最高價 = 最緊
v_SL_Locked = true
```

### 4.2 P3b 引擎停損 — 三條腿取最緊距離

```
SetStopContract;                                          ← 頂層無條件
若 MP <= 0：
   SetStopLoss(MinList(ATR45 × 1.5,
               MinList(Daily_ATR × 0.5,
                       Close × SL_Pct / 100)) × BigPointValue)
```

**MinList 的距離 == MaxList 的價位**，兩者是同一條腿。

> **V2.9 的取證是本專案最重要的一次除錯，值得完整記錄：**
>
> 舊標頭把 P3 錯誤地改述成「Entry − MaxList(distances)」，V2.6+ 的 P3b
> 照著那個公式形狀寫，於是引擎停損取了**較鬆的一條腿**，比設計意圖寬
> 1.6–2.8 倍，**橫跨整個 V2.6+ 世代未被發現**。
>
> 取證方法：重建 100 萬根 K 棒的 ATR45 與 DailyATR、456 筆交易、
> 凍結距離預測誤差 p90 = 1 點。結論：緊腿在 99–100% 的進場是 ATR 腿；
> 12 筆同根死亡填在寬腿（超額 −460 點）；2 筆歷史贏家因寬腿才活過進場那根。
>
> **驗證器也一起錯了**：舊的 `verify_l1_immediate_stop.py` 的 V-4 斷言的是
> 那個有 bug 的 MaxList 形狀——**bug 通過驗證，因為驗證器把 bug 編碼進去了。**

### 4.3 單一出場價

```
Exit_Price_SL    = v_Frozen_SL
Exit_Price_Trail = v_Trail_High
Final_Exit_Price = MaxList(Trail, MaxList(SL, stopProfitPrice_L))
```

三者取最高 = 最緊。**L2/L4 用優先級鏈，L1 用單一價位——效果相同，結構不同。**

---

## 五 出場標籤路由

V2.9.1 的裁決：**虧損側標籤只能標虧損出場，獲利了結必須用不同標籤。**

舊路由破壞這條兩次：`TL_TP`（追蹤）曾在進場價下方觸發（#452，−444 點）；
`TL_SL_Gap` 曾在進場價上方觸發（SP 鎖定後跳空）。

```
若 BarStatus(1) = 2 且 Close < Final_Exit_Price：       ← 跳空分支，收盤才判
   若 Final_Exit_Price >= Entry_P → Sell ("TL_SP_Gap") Market
   否則                          → Sell ("TL_SL_Gap") Market
否則：
   若 |Final − Exit_Price_SL| < 0.001            → TL_SL
   否則若 stopProfitPrice_L > 0 且
        |Final − stopProfitPrice_L| < 0.001      → TL_SP
   否則若 Exit_Price_Trail >= Entry_P            → TL_TP
   否則                                          → TL_TSL
```

| 側 | 標籤 |
|---|---|
| 虧損 | `Stop Loss`（P3b 引擎，僅進場根）· `TL_SL` · `TL_SL_Gap` · `TL_TSL` |
| 獲利 | `TL_TP` · `TL_SP` · `TL_SP_Gap` |

> 標籤在**下單時**指派。跳空穿過進場價仍可能讓獲利標籤成交在小虧——
> 標頭記錄為「documented edge, not an overlap」。
>
> 浮點比較用 `< 0.001` 容差，不是等號。移植必須照抄容差值。

---

## 六 強制平倉 — J-3 缺陷所在

```
若 MP > 0：
   若 v_Registry_Expired                     → Sell ("TL_RegistryEnd") Market
   否則若 假日 且 Time >= 345                 → Sell ("TL_Holiday")     Market
   否則若 結算日 且 Time >= 1230              → Sell ("TL_Settlement")  Market

   若 Manual_Kill_Switch = True              → Sell ("TL_Kill")        Market
                                                ↑ 獨立 if，不在 else 鏈上
```

標頭自承：

> L1 can emit **two full-size market orders on one bar** today: Manual_Kill_Switch
> sits outside the else-if chain and last. Adding a mutual-exclusion flag would
> change behaviour and break the anchor. **That is fix J-3** and carries its own
> separate anchor.

實際上最多三張：Section 3 必發一張 + Section 4 鏈上一張 + Kill 一張。

`Holiday_Flat_Time = 345`（03:45）是五支裡最早的——45M 網格上 03:45 觸發、
03:45 成交、04:30 重試、05:00 前必平。

---

## 七 狀態

| 變數 | 類別 | 重置 |
|---|---|---|
| `v_SL_Locked` `v_Frozen_SL` | per-trade | 空手 |
| **`posbleProfit_Long` `stopProfitPrice_L` `v_Trail_High`** | per-trade，**IntraBarPersist** | 空手 |
| `Entry_P` `Exit_Price_*` `Final_Exit_Price` | per-bar | 每根重算 |
| `v_Frozen_Gap` `v_Frozen_MABase` `v_Frozen_SL_Orig` | 跨交易（re-entry 用） | **平倉後仍需存活** |
| `v_Wk_Entry_Fast` `v_Wk_Entry_Slow` | 跨交易 | 同上 |
| `v_ReEntry_Armed` `v_ReEntry_Price` `v_IsReEntry` `v_Last_EntryPrice` | 跨交易 | 新訊號時清除 |
| `WkCloses` 等 | — | L1 用 Data3，不自行合成週線 |
| `MyEquity` `Year_*` `txtID` | MDD 視覺化 | **不移植** |
| `v_Prev_MP` | 跨交易 | 腳本最末行 |

> **[D-1]** `v_Prev_MP` 在最末行更新且**不在 `BarStatus` 守衛內**，
> 所以在 IOG 下它記錄的是**每個 tick** 的部位，不是每根 K 棒。
> 註解宣稱「records the position of every bar without exception」——語意不符。
>
> re-entry 的 arm 判斷 `v_Prev_MP = 1 and MP = 0` 在守衛內，讀到的是
> 前一個 tick 的部位而非前一根的部位。**因 `ReEntry_On = 0` 目前惰性，
> 但啟用時會是問題。**

---

## 八 承諾與斷言

| # | 承諾 | 斷言 | 驗證 |
|---|---|---|---|
| 1 | P3「computed once on the entry bar close and **locked**」 | `v_SL_Locked` 為真後 `v_Frozen_SL` 不變 | ✓ |
| 2 | P3「MaxList picks the **TIGHTEST**」 | `v_Frozen_SL == Entry − MinList(三距離)` | ✓ V2.9 修正後 |
| 3 | P3b「Distance = same as P3 frozen SL」 | 引擎距離 == 凍結距離 | ✓ V2.9 修正後 |
| 4 | P4「**uni-directional** ratchet」 | `v_Trail_High[t] >= v_Trail_High[t−1]` | ✓ MaxList |
| 5 | P7「an armed runner can **never** round-trip into a loss」 | `stopProfitPrice_L > 0` 蘊含 `> Entry_P` | ✓ |
| 6 | P7「giveback from peak **capped at 55 pct**」 | 出場 >= `Entry + peak × 0.45` | ✓ |
| 7 | P5「**Iron Rule**: flat before the 05:00 close」 | `Time >= 345` 必平 | ✓ |
| 8 | P5「beyond the verified registry: **no entries, flatten all**」 | 過期即封鎖 + 平倉 | ✓ |
| 9 | P6「flat-time 12:30 before 13:30 settlement」 | `Time >= 1230` 不持倉 | ✓ |
| 10 | P3b「active on the **ENTRY BAR itself**」 | 進場那根保護已生效 | ✓ |
| 11 | 單一部位 | `MarketPosition ∈ {0, 1}` | ✓ |
| 12 | V2.9.1「loss side and profit side **never share a label**」 | 標籤與側別一致 | ✓ 下單時判定 |
| 13 | `AvgTrueRange(20)[1] of Data2` 的 `[1]` | 決策時可計算性 | ✓ |

> **13 條全數成立。** 這正是 `.md` 那 13 條不變量的來源——它們是從 L1 的註解推導的，
> **因此只對 L1 完全適用**（L2 的驗證已顯示其中三條在 L2 不成立）。

---

## 九 觸發頻率

| 版本 | 筆數 | 淨利 | PF | 勝率 | MDD |
|---|---|---|---|---|---|
| V2.7（SP 500） | **476** | 3,018,400 | 1.496 | 31.3% | −547,800 (−21.2%) |
| V2.7 backtest | — | +3,938K | 1.484 | — | −461K（451 筆） |

> **[D-2]** 標頭同時列出兩組 V2.7 數字（476 筆 / 3,018,400 與 451 筆 / 3,938K），
> 未說明差異來源。且 V3.2 明載：
>
> 「Trade counts in the older documents were taken on an earlier bar set and are
> **NOT a valid baseline**. TWO runs are required.」

V2.7 的 Plan C（被動出場後 re-entry）已被 A/B 否決：假設 +2.1M，
實測 A+C 組合 3,018K vs Plan A 單獨 3,938K，**拖累 −920K**。
69 筆 re-entry 淨負，「re-entry 部位的停損價比原始突破進場更差」。

---

## 十 模式差異

| # | 項目 | mc12 | live | v2 |
|---|---|---|---|---|
| 1 | 下單時機 | 次根開盤 | 立即 | 同 live |
| 2 | 收盤前兩根 | 允許 | 禁止 | 同 live |
| 3 | J-3 一根多張市價單 | **照抄** | 照抄 | 可加互斥旗標 |
| 4 | MDD 視覺化 | 不移植 | 不移植 | 不移植 |
| 5 | Re-entry 模組 | `ReEntry_On = 0` | 同 | 可啟用 |
| 6 | IOG tick 粒度 | 需 tick 資料 | 凱基 tick | 同 |

---

## 十一 已知落差

**[D-1] `v_Prev_MP` 在 IOG 下記錄 tick 而非 bar** `中，目前惰性`
不在 BarStatus 守衛內。註解宣稱記錄每根，實際記錄每 tick。
`ReEntry_On = 0` 時無影響，啟用時會是問題。

**[D-2] 兩組 V2.7 績效數字未調和** `高，擋住對帳基準`
476 筆 / 3,018,400 與 451 筆 / 3,938K。V3.2 明載舊文件的筆數
「NOT a valid baseline」，需要**兩次執行**才能建立 anchor。

**[D-3] J-3：一根最多三張市價單** `高，刻意保留`
Manual_Kill_Switch 在 else 鏈外。標頭明載修它會破壞 anchor。

**[D-4] IOG 行為未在 MC 上實測** `高，無法驗證`
`.md` §10.6 記載：「L1 的 P7 逐 tick 執行」由「該區塊無 BarStatus 護欄
+ IOG=true + 註解自述」推得，**未在 MC12 上驗證**。
且 MC 匯不出 tick 級狀態，**歷史無法驗證**。

> **替代方案：平行前向驗證。** Python 只發訊號不下單、MC 續實盤、
> 每日比對，連續 N 天一致才算通過。用的是真實 tick，比任何歷史回放都準。

**[D-5] 策略名稱與實際週期不符** `低`
名稱 `..._60M_...`，實際 45M。標頭自承為 live 連續性而保留。

**[D-6] 浮點標籤路由用 0.001 容差** `低`
`AbsValue(Final − Exit_Price_SL) < 0.001`。移植必須照抄容差值，
改成等號比較會讓標籤分佈不同。

**[D-7] 結算日遇休市會標錯** `低`　五支共通。

---

## 十二 移植評估

| 特性 | 值 | 影響 |
|---|---|---|
| IOG | **`true`** | **需 tick 生命週期 + BarStatus 守衛 + IntraBarPersist** |
| 資料流 | 三條（45M / Daily / Weekly） | 45M 週期只有 L1 用 |
| 單型 | Market + Stop | 不需 Limit |
| 部位 | 單一 | 不需多腿 |
| 出場控制 | **無 ExitFired，最多三張** | 需並存訂單管理 |
| 變數歷史 | 需 `v_Trail_High` 的棘輪語意 | 需 `types/stateful.py` |
| 未來函數 | 無 | `Daily_ATR` 已帶 `[1]` |
| 特殊運算子 | `Crosses Over` | 已實作 |

> **移植順位 5（最後）。** L1 是唯一需要 tick 級生命週期的策略，
> 而 `engine/context.py` 的資料模型必須從第一天就以 tick 為原生、
> bar close 為特例——否則做到這裡要回頭重構，前四支已通過的對帳全部重跑。

---

## 十三 待決

| # | 項目 |
|---|---|
| 1 | `.pla` 的 SHA-256 |
| 2 | D-2：以**兩次執行**重建 V3.1 anchor，舊筆數不採用 |
| 3 | D-4：IOG 行為改採平行前向驗證，需決定連續一致的天數 N |
| 4 | D-3：J-3 是否在 `v2` 模式修正 |
| 5 | Re-entry 模組（`ReEntry_On = 0`）是否移植死碼 |
| 6 | `SL_Pct = 0` 的雙腿模式（V3.0 相容）是否移植 |
| 7 | MDD 視覺化確認不移植（Section 5，40 行） |
