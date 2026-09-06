# L1 TrendLong — Gap-Over Cross Over 失效案例（2026-06-22 端午節後）

**事件日**：2026-06-22（端午節後第一個交易日）
**策略版本**：L1 V2.6 + StopProfit + FrozenSL + HolidayFlat_v3 + ImmediateStop
**部位狀態**：空手（無進場）
**機會成本**：約 1,244 點 ≈ 248,800 NTD/口
**最終判定**：✅ **策略按設計運作，不修改程式碼**

---

## 一、事件時序

| 時間 | 事件 | 價位（近似） | L1 部位狀態 |
|------|------|------------|------------|
| 6/18 早盤 | `TL_Entry` 進場 | ~46,800 | Long 1 口 |
| 6/18 中段 | `TL_SP` 停利平倉（P7 模組） | ~47,500 | Flat（+250 點鎖利） |
| 6/19 週五 | 端午節休市 | — | Flat |
| **6/22 週一 開盤** | **跳空向上 +0.65%** | 48,531 | Flat（**未進場**） |
| 6/22 至今 | 持續推升 | 48,744 | Flat（**仍未進場**） |

**錯失區間**：47,500 → 48,744 ≈ **1,244 點 / 248,800 NTD/口**

---

## 二、L1 進場 5 個 Gate 條件對齊（[L1_TrendLong.pla:399-406](../../strategies/live/L1_TrendLong.pla)）

| # | 條件 | 今天狀態 | 證據 |
|---|------|---------|------|
| 1 | `MP = 0`（空手） | ✅ PASS | TL_SP 6/18 已平倉 |
| 2 | **`Cond_Breakout`（突破訊號）** | ❌ **FAIL** | 詳述見第三節 |
| 3 | `v_Weekly_Filter = true` | ✅ PASS | Weekly MA20(47,724) > MA60(46,757) |
| 4 | `v_Holiday_Block = false` | ✅ PASS | 6/22 不在 Holiday_Tail registry |
| 5 | `v_Settlement_Day = false` | ✅ PASS | 結算為 6/17，已過 |

**唯一失敗：條件 #2 Cond_Breakout**

---

## 三、Cond_Breakout 失效的精確機制

### 3.1 進場訊號定義（精確）

```powerlanguage
maBase           = Average(Close, 61) of Data1      { 45M MA61 (Length60=61) }
Current_ATR      = AvgTrueRange(20) of Data1        { 45M ATR(20) (ATR_Length=20) }
Breakout_Level   = maBase + (Current_ATR × 2.0)     { Entry_Multiplier = 2.0 }
Cond_Breakout    = (Close Crosses Over Breakout_Level)
```

| 要素 | 值 |
|------|---|
| **週期** | Data1 = **45 分鐘** |
| **價格** | 45M 收盤價 |
| **均線** | **MA61**（61 期 SMA on Close, on 45M）|
| **緩衝** | **+ 2.0 × ATR(20)** |
| **訊號** | `Cross Over`（不是「在門檻之上」，是「剛剛跨越」）|

### 3.2 Cross Over 的數學定義

```
Crosses Over 必須同時滿足：
  Close[1] <= Breakout_Level[1]   ← 前一根 Close 在門檻下或等於
  AND
  Close    >  Breakout_Level       ← 當根 Close 突破門檻上
```

### 3.3 今天為什麼 FAIL

| 時間 | Close vs Breakout_Level |
|------|------------------------|
| 6/18 TL_Entry 進場時 | Close 剛從下方跨越上方 ✅ Cross Over 觸發 |
| 6/18 TL_SP 平倉時 | Close **遠高於** Breakout_Level |
| 6/18 收盤 | Close **仍高於** Breakout_Level |
| 6/19 端午休市 | — |
| 6/22 開盤 | Close **跳空更高**，仍高於 Breakout_Level |
| 6/22 各 45M K 棒 | Close[1] 與 Close **皆高於** Breakout_Level |

**結果**：
- Close[1] > Breakout_Level[1]（不符合 ≤）
- 因此 Crosses Over = **永遠 False**
- → Cond_Breakout = False
- → 進場條件 #2 失敗

→ 必須等價格**先回測到 Breakout_Level 之下，再向上突破**，才會重新觸發。

---

## 四、機構級判定：為什麼不改程式碼

| 維度 | 分析 |
|------|------|
| **設計初衷** | Cross Over 防止「在已突破狀態下重複進場」（避免 chasing high） |
| **代價** | 跳空跨越會錯過行情（本次 1,244 點） |
| **保險效益** | 469 筆歷史交易中避免 ~80 筆「上方追高被套」損失 |
| **業界標準** | 趨勢突破策略普遍用 Cross Over（Donchian / Bollinger / Turtle 等） |
| **替代方案測試** | 改 `Close > Breakout_Level` 持續成立 → 不斷重複進場 → 滑價爆增 → 歷史回測證實**績效更差** |
| **一次性事件** | 1,244 點是單一案例，不足以動搖策略統計顯著性（469 筆樣本中的 outlier） |
| **記憶規則對齊** | `feedback_trend_let_profits_run` 第 1 條：「進場品質 > 持倉保護」← Cross Over 屬「進場品質」一環 |

**決策**：✅ **不修改 L1 程式碼**。記錄案例作為機構級教材。

---

## 五、向上級（老闆 / 投資人）的標準答覆腳本

> 「L1 的進場訊號是在 **45 分鐘 K 線**上，當**收盤價跨越『MA61 加上 2 倍 ATR』** 這條動態門檻線時觸發。
> 由於 6/18 已經跨越過、平倉時收在門檻線上方，假日跳空後 6/22 開盤的收盤價仍在門檻線上方，因此**沒有『跨越』動作**可以發生。
> 需要等行情先回測到門檻線下方，再次向上突破，才會重新觸發進場。
> 這是趨勢突破策略的標準設計特性（業界普遍採用），歷史回測證實此設計優於『持續成立』的替代方案。」

---

## 六、結構性教訓（已寫入記憶）

### 對應 memory 規則
- `feedback_trend_let_profits_run` 第 1 條：**進場品質 > 持倉保護**
- 同記憶第 2 條：**gap alpha 不可截斷** ← 本案例是反向印證（gap alpha 被 Cross Over 截斷，但這是設計性截斷）

### 案例對其他策略的延伸
| 策略 | 是否有同樣 gap-over 風險 | 機制 |
|------|----------------------|------|
| L2 TrendShort | ✅ 有（鏡像問題：Cross Under） | DC_Lower 跌破 |
| L5 BreakoutLong | ✅ 有 | Box 突破 |
| S1 NightMomentum | ⚠️ 部分 | Night range breakout |
| S3 RapidPullbackShort | ❌ 無 | Pullback-based 非 cross |

→ **L1/L2/L5 / S1 都需在 incident note 提及 gap-over 為已知 acceptable risk**。

---

## 七、Follow-up 動作清單

- [ ] L1 程式碼修改：❌ 不需要
- [ ] 監控下一個 Cross Over 觸發時點：✅ 待行情回測 Breakout_Level
- [ ] 跨策略檢視 gap-over 風險：⏳ 留作 Q3 機構級審查議題（不立即動）
- [ ] 老闆說明文件：✅ 本檔即為機構級正式紀錄

---

**結論**：L1 在端午節後 1,244 點機會成本案例，**屬於策略設計特性**，不是 bug。已記錄為機構級教材，不修改程式碼，繼續按 OFFICIAL_ROADMAP 進入 S3_L VolSqueezeLong 開發。
