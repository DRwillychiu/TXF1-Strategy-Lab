# S16_S MACrossShort — 能力邊界分析 + 程式碼自我審計

**日期**：2026-07-23
**觸發事件**：7/23 夜盤殺盤（44800 → 44200）策略未開單，用戶反思策略能力邊界
**版本**：v1.4-BELATE（參數凍結期，改 code = 30 筆重計時）

---

## 一、S16_S 能做到的行情

策略的 alpha 來源是「**急轉彎的瞬間**」——ZLEMA 死叉 + 高斜率 = 動能爆發型空方進場。

| 行情型態 | 機制 | 回測實證 |
|----------|------|---------|
| **V 頂急反轉** | 漲→跌轉折猛烈，死叉瞬間 Slope >> 28 | 7/2 15:05 S=93.7 |
| **崩盤第一波** | 恐慌拋售造成 ZLEMA 急墜 | 7/17 08:45 S=92.6 |
| **跳空開低** | 缺口直接拉開均線距離，開盤即死叉+高斜率 | 7/16 08:45 S=55.7 |
| **反彈失敗二次下殺** | 先反彈（黃金交叉），再殺時產生新的死叉 | 7/8 連續 3 筆 (10:10, 12:10, 16:25) |
| **Bear/Volatile regime 動能 burst** | 核心獵場，2hr 內動能釋放完畢 | PF 3.79 (Bear) / PF 2.13 (Volatile) |

**共同特徵**：
- 轉折力道夠猛（Slope > 28 pts / 5M bar）
- 動能在 2 小時內集中釋放（TimeStop 24 根 = alpha 窗口）
- 22.6% 勝率 × 6.8 倍盈虧比 = sniper profile

---

## 二、S16_S 結構性做不到的行情

以下均為**架構天花板**，非參數可解：

### 2.1 慢跌→加速崩（今晚 7/23 案例）

**現象**：死叉在 18:20 發生但 Slope=7.5（溫吞滑落），被 MinSlope 擋掉。20:37 之後暴跌 500+ 點，但 ZLEMA_Fast 已在 Slow 下方，不會產生新交叉。

**根本原因**：Cross-based 進場只認「穿越的瞬間」，不認「穿越之後的延續」。

**歸屬判斷**：→ **S17_S SwingShort60M 的獵場**（中速空方 swing，60M+日線，Stage-1 進行中）

### 2.2 趨勢延續段（已在路上的下跌）

**現象**：市場已處於下跌趨勢，ZLEMA_Fast 持續在 Slow 下方，無新死叉。

**根本原因**：均線交叉是一次性事件，不會在趨勢中重複觸發。

**歸屬判斷**：→ **L2 TrendShort 的領域**（但 L2 使用 13 週 SMA，2026 全年 0 筆——S17_S 被立案的部分原因）

### 2.3 磨底陰跌（每天跌一點）

**現象**：慢慢下跌，每根 5M 的 Slope 都只有個位數，永遠過不了 28。

**根本原因**：MinSlope=28 的設計代價。降低門檻會引入大量假信號（GA 實證：Slope30 cliff -27%，暗示反方向也有邊界）。

**歸屬判斷**：→ **需要獨立策略**。磨底是不同的 alpha 結構，適合用 threshold-based（F-S 差距閾值）或 regime filter 方式捕捉，不適合嫁接在 cross-based 架構上。

### 2.4 閃崩（< 5 分鐘完成）

**現象**：一根 5M K 棒內崩完，ZLEMA 平滑延遲導致死叉可能在暴跌結束後才出現。

**根本原因**：所有均線天生有平滑延遲，5M 時框的 ZLEMA(25) 反應窗口 ~125 分鐘，無法捕捉秒級事件。

**歸屬判斷**：→ **S6 FlashCrashMomentum（Queue，5M 時框）**，專為閃崩設計。

### 2.5 尾盤行情（04:30 之後）

**現象**：04:30 後進場被 Tail_LastEntry_Time 封鎖（v1.3 時間護欄）。

**根本原因**：合規設計——不允許部位跨越早盤空窗 05:00-08:45。

**歸屬判斷**：→ **不可解也不應解**。這是風控規範，不是 alpha 問題。

### 2.6 Bull regime whipsaw

**現象**：多頭+短暫 shock 恢復 regime 中，死叉頻繁但方向錯，被 QuickStop 止血。

**根本原因**：單向做空策略在強多頭中的結構性弱點。W4 WFA W6 窗口 -347K MDD -43.4%。

**歸屬判斷**：→ **已接受為保險成本**（2026-07-08 Option A ruling）。portfolio 層級由多頭策略（L1/L3/L5/S3_L）補位。

---

## 三、覆蓋缺口歸屬判斷總表

| 缺口 | 歸屬 | 可否整合進 S16_S | 理由 |
|------|------|-----------------|------|
| 慢跌→加速 | **S17_S** | 不可 | 需要 60M+日線不同時框 + K 棒型態觸發（非 cross） |
| 趨勢延續 | **L2 / S17_S** | 不可 | 需要 continuation entry，本質不同 |
| 磨底陰跌 | **獨立新策略** | 不可 | 需要 threshold-based 架構，寫在 cross-based 裡是設計矛盾 |
| 閃崩 | **S6** | 不可 | 閃崩邏輯（價格異常偏移）vs 均線交叉是不同 alpha |
| 尾盤 | **不可解** | N/A | 合規規範，非 alpha 缺口 |
| Bull whipsaw | **組合補位** | N/A | 已接受為保險成本 |

**結論：S16_S 的 6 個覆蓋缺口中，0 個適合整合進本策略。** 每個缺口都需要不同的進場架構或時框，強行塞進 cross-based 5M 框架會稀釋現有 alpha（PF 1.91 / +109 萬）。

---

## 四、程式碼自我審計報告

### 4.1 標籤規範審計 — 全部通過

| 標籤 | 動作 | 前綴 | 合規 |
|------|------|------|------|
| SE_MA_DeathCross | sell short | SE_ | PASS |
| SX_MA_GoldenCross | buy to cover | SX_ | PASS |
| SX_MA_QuickStop_Time | buy to cover | SX_ | PASS |
| SX_MA_QuickStop_Loss | buy to cover | SX_ | PASS |
| SX_MA_ML_Exit | buy to cover | SX_ | PASS |
| SX_MA_BE_Trail1 | buy to cover | SX_ | PASS |
| SX_MA_BE_Trail2 | buy to cover | SX_ | PASS |
| SX_MA_TimeStop | buy to cover | SX_ | PASS |
| SX_MA_SL | buy to cover (Stop) | SX_ | PASS |
| SX_MA_Kill | buy to cover | SX_ | PASS |
| SX_MA_Registry | buy to cover | SX_ | PASS |
| SX_MA_Holiday | buy to cover | SX_ | PASS |
| SX_MA_Settlement | buy to cover | SX_ | PASS |
| SX_MA_TailFlat | buy to cover | SX_ | PASS |

**14/14 PASS**。所有 sell short 用 SE_，所有 buy to cover 用 SX_，無混用。

### 4.2 函數使用規範審計 — 全部通過

| 函數 | 用途 | 合規 |
|------|------|------|
| XAverage | ZLEMA 內核 EMA 計算 | PASS |
| AvgTrueRange | ATR 計算（14/3/90 三組） | PASS |
| IntPortion | ZLEMA lag 整數部分 | PASS |
| RSI | M6 動能層 | PASS |
| Average | M6 量均線 + 短 MA | PASS |
| Lowest | M6 RSI 5 期最低 | PASS |
| SetStopLoss | Rule #12 引擎級停損（MP>=0 guard） | PASS |
| DayOfWeek / DayOfMonth | 結算日判定 | PASS |
| EntryPrice | 盈虧計算 | PASS |
| BigPointValue | SetStopLoss 金額換算 | PASS |

### 4.3 邏輯衝突審計 — 無衝突

| 檢查項 | 結果 | 說明 |
|--------|------|------|
| ExitFired 優先權鏈 | PASS | P0→P0.5→P1→P2→P3→P4→P5→P6 嚴格順序 |
| SetStopLoss 與 Frozen SL 一致性 | PASS | MP>=0 時 SetStopLoss 預載，MP=-1 時 P6 接手 |
| BE 方向性 | PASS | short: v_Profit = Entry-Close，Close >= BE_Stop = 回吐觸發 |
| QuickStop 方向性 | PASS | short: v_Loss = Close-Entry，Close >= Entry = 未獲利 |
| Holiday loop vs array 範圍 | PASS | array[80] vs 63 entries，多餘 17 比對 0 值，不影響結果 |
| 進場時間護欄 | PASS | `Time<=430 or Time>500` 正確使用 MC 24hr 閉區間 |
| Tail 出場時間護欄 | PASS | `Time>=440 and Time<=500` 正確閉區間 |

### 4.4 發現：死碼（Dead Code）

| 變數 | 行號 | 狀態 | 風險 |
|------|------|------|------|
| **v_ML_Loss** | 270 | 宣告但**從未賦值、從未讀取** | 無影響，純多餘 |
| **v_Prev_MP** | 256, 655 | 賦值但**從未被任何條件讀取** | 無影響（IOG=False 下直接用 MarketPosition 安全） |

**影響評估**：兩者都不影響策略行為，但違反「無無效內容」原則。

**處置建議**：**不動**。策略處於參數凍結期，任何 code 修改 = 30 筆模擬重計時。死碼不影響邏輯或效能，記錄在案即可。待凍結期結束或觸發紅線時一併清理。

### 4.5 發現：效能低項（非 Bug）

| 項目 | 說明 | 影響 |
|------|------|------|
| Holiday loop 80 vs 63 | 每根 K 棒多比對 17 個 0 值 | 可忽略 |
| RSI 重複計算 | Section 8 v_ML_RSI + Section 10 Lowest(RSI()) | 可忽略（5M 頻率極低） |
| Input Group G 缺失 | A/B/C/D/E/F/H/I，跳過 G | 純命名問題 |

---

## 五、BUG 排查 SOP（假設未來出現 BUG）

### 第一層：部署檢查（排除設定錯誤，90% 問題在此層解決）

1. 圖表時間週期 = **5 分鐘**（非 1M/15M/60M）
2. MaxBarsBack >= **200**
3. 策略狀態 = **On**
4. IntrabarOrderGeneration = **False**
5. Data feed 正常（看圖上 K 棒有沒有在跑）
6. 策略成功編譯（無紅色錯誤）

### 第二層：信號驗證（指標 + Python 雙重交叉驗證）

1. **掛 IND_S16_S_Monitor** — 看死叉標記 + Slope 數值是否與策略進出場位置吻合
2. **跑 Python 1M→5M 模擬** — 獨立計算 ZLEMA + 進場條件
3. **匯出 MC12 交易清單** — 與 Python 結果逐筆 diff

### 第三層：邏輯深查（信號不一致時啟動）

| 懷疑點 | 排查方式 |
|--------|---------|
| ZLEMA 計算偏差 | Print 輸出策略內部 v_ZLEMA_Fast/Slow，比對指標 Plot 值 |
| Holiday 誤擋 | 檢查 Holiday_Tail 日期 vs 實際期交所行事曆 |
| Settlement 誤判 | 確認 DayOfWeek(Date)=3 + DayOfMonth 15-21 |
| Registry 過期 | 確認 Registry_Valid_Until = 1270101（2027-01-01） |
| SetStopLoss 提前平倉 | 檢查 P7 是否在 P1-P6 之前觸發（用 Print 追蹤 ExitFired） |
| ExitFired 漏判 | 確認每個 P 層 begin/end 配對正確 |

### 第四層：回測對帳（終極驗證）

MC12 全期回測結果必須重現官方 718 baseline：
- **107T / Net +1,094,800 / PF 1.910 / MDD -228,000 / WR 27.1%**
- 數字不符 → `git diff` 找出 code 差異

---

## 六、與 S17_S 的角色互補關係

| 維度 | S16_S MACrossShort | S17_S SwingShort60M（設計中） |
|------|-------------------|------------------------------|
| 時框 | 5M | 60M + 日線 |
| 進場類型 | Cross-based（穿越瞬間） | K 棒型態觸發（反彈失敗） |
| 獵場 | 暴力急轉折 | 中速慢跌 |
| 持倉時間 | 2 小時內 | 數日（swing） |
| 弱點 | 慢啟動加速行情 | 閃崩型行情（速度太快） |
| 2022 慢熊 | 僅 3 筆 | 設計目標覆蓋 |
| 組合角色 | 閃電收割者 | 持久戰選手 |

**S16_S 吃「猛轉彎」，S17_S 吃「慢漂移」——兩者互補，不重疊。**

---

## 附件：7/23 夜盤殺盤實例分析

### 時序還原（Python 1M→5M 模擬驗證）

| 時間 | 事件 | ZLEMA F-S | Slope | 結果 |
|------|------|-----------|-------|------|
| 18:20 | Death Cross 發生 | -8.8 | **7.5** | **BLOCKED**（Slope 7.5 < 28） |
| 19:05 | F 已在 S 下方 | -16.6 | -2.5 | 無交叉可觸發 |
| 19:35 | 差距擴大 | -75.1 | 32.7 | Slope 高但無新交叉 |
| 20:37 | 暴跌開始 | ~-160 | ~45 | 殺盤加速，但已無穿越事件 |
| 20:42 | 收盤 44,223 | -202.5 | 50.0 | F-S 差距持續擴大中 |

### 結論

策略未開單 = **正確行為**。死叉在 18:20 就發生了，但初始力道不夠（S=7.5），被 MinSlope 正確過濾。之後的殺盤是「死叉延續段」，cross-based 架構無法也不應捕捉——這屬於 S17_S 的獵場。
