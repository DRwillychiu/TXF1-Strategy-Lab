# L4 v17 退化錨點 —— 執行卡（2026-08-24）

> **錨點的定義**：新版本在「所有新功能關閉」時，必須與舊版本**逐筆完全相同**。
> 一格不同就是有 bug，不是「差不多」。

---

## 0. 執行前的靜態驗證（已完成，2026-08-24）

跑在 `strategies/research/L4_ConsolidationShort/L4_v17/L4_ConsolidationShort_v17.pla`。

| 檢查 | 方法 | 結果 |
|---|---|---|
| ASCII 100%（Rule #15） | `scripts/verify_pla_ascii.py --strict` | **67/67 PASS** |
| 識別字重複宣告 | 解析 `inputs:` / `variables:` | **76 個，0 重複** |
| `begin` / `end` 平衡 | 去註解後計數 | **34 / 34** |
| 六個新變數皆已宣告 | 交叉比對 | **6/6** |
| 四個開關預設值 | 讀 `.pla` | `Buffer_Form=1` `Stop_Form=1` `Trail_Form=1` `Max_Entry_Risk_Pct=0` |
| 插入位置的作用域 | 對照 live 檔行號 | 與原 `v_Trigger_Price` **同一個 `begin...end`**（L576-647） |

### 0.1 退化路徑的逐條證明

| 開關 | 預設 | 走到的分支 | 與 live v14.6 |
|---|---|---|---|
| `Buffer_Form = 1` | `v_Buffer_Form_Pct = false` | `v_Trigger_Price = v_Box_Top - ATR*i_Buffer_ATR_Mult` | **同一行** |
| `Stop_Form = 1` | `v_Stop_Form_Pct = false` | 引擎 guard 與 frozen stop 皆走 ATR 分支 | **同一行** |
| `Trail_Form = 1` | `v_Trail_Form_Pct = false` | `v_Lowest_Low + Trail_ATR_Mult*ATR` | **同一行** |
| `Max_Entry_Risk_Pct = 0` | `v_Risk_OK = ( 0 <= 0 or ... )` | **恆為 true** | 進場 gate 等同未加 |

**`v_Planned_*` 只寫入新變數，無副作用。**
**`v_Risk_OK` 無陳舊讀取路徑**——賦值（L629）與使用（L639）在同一個區塊、同一根 K 棒、賦值在前。

> **靜態結論：這份檔案「必須」逐筆重現 live L4。**
> 若實測不重現，就是我的靜態分析錯了，見 §4。

---

## 1. MC12 設定（照抄基準線，一格都不要改）

基準線來源：`TXF1  L4_ConsolidationShort 策略回測績效報告.xlsx`（2026-08-23 20:58 匯出）

| 項目 | 值 |
|---|---|
| 商品 | TXF1 |
| 壓縮 | **15 Minutes** |
| 原始資本 | **2,000,000** |
| 口數 | **2 口** |
| 滑價 | **1,000 每口每邊** |
| 佣金 | 無手續費 |
| **細部資料** | **已停用** |
| 利率 / 最低可接受報酬率 | 2 / 2 |
| 回測模式 | 傳統模式 |
| 開始日期 | 2020-02-21 11:00 |
| 結束日期 | 2026-08-22 05:00 |

**⚠ 載入名稱必須是 `STRATEGY_WILLY_SHORT_V17_RESEARCH`，不可存回 `STRATEGY_WILLY_SHORT_CTEST2`（那是 live 訊號）。**

### 1.1 Inputs：舊的 23 個必須與基準線一致

`Daily_FastMA_Len 20` / `Daily_SlowMA_Len 60` / `Lookback_Bars 15` / `Range_Shrink_Rate 0.7` /
`Weekly_MA_Len 48` / `ATR_Length 60` / `ATR_Stop_Mult 2` / `i_Buffer_ATR_Mult 0.4` /
`Time_Limit_Bars 6` / `Cooldown_Bars 8` / `Time_Stop_Bars 60` / `Trail_ATR_Mult 1` /
`Freeze_SL_On True` / `Holiday_Flat_Time 415` / `Registry_Valid_Until 1270101` /
`Manual_Kill_Switch False` / `Settlement_Flat_Time 1230` / `Night_Block_On True` /
`BE_Trigger_Pts 0` / `BE_Offset_Pts 5` / `SP_Trigger_Pts 0` / `SP_Retain_Pct 50` / `SL_Pct 1.5`

### 1.2 Inputs：v17 新增的 7 個，**全部留預設**

| Input | 錨點值 |
|---|---|
| `Buffer_Form` | **1** |
| `i_Buffer_Pct` | 0.30（Form 2 才生效，此輪不參與） |
| `Stop_Form` | **1** |
| `Stop_Pct` | 0.60（同上） |
| `Trail_Form` | **1** |
| `Trail_Pct` | 0.50（同上） |
| `Max_Entry_Risk_Pct` | **0** |

---

## 2. 通過標準（四個數字全中才算過）

| 指標 | 必須等於 |
|---|---|
| 交易筆數 | **79** |
| 淨利 | **877,200** |
| 獲利因子 | **1.4902** |
| 最大策略虧損 | **−789,200** |

**加碼條件**：最後一筆平倉出場時間必須是 **2026-08-20 20:30**。

---

## 3. 驗證指令（不要用肉眼比對）

```bash
python scripts/compare_mc12_reports.py "C:/Users/User/Downloads/TXF1  L4_ConsolidationShort 策略回測績效報告.xlsx" "<v17 匯出的檔案>"
```

| 退出碼 | 意義 | 動作 |
|---|---|---|
| **0** | 可比且逐筆相同 | **錨點通過**，直接進 Run C |
| **1** | 可比但交易分歧 | **真的有 bug**，看它印的第一個分歧點，見 §4 |
| **2** | 不可比 | 先修這個，見 §3.1 |

### 3.1 ⚠ EXIT=2 的處理（B-1 教訓）

基準線的設定表寫 `結束日期 2026-08-22 05:00`，
但**實際跑到的最後一根 K 棒只到 2026-08-20 20:30**。

**設定表的結束日期是「你要求的範圍」，不是「MC 實際拿到的資料」。**

若你在 08-23 之後又更新過 K 棒，v17 會比基準線多看到資料，可能多出交易 →
腳本會判 EXIT=2 並印出「多出的尾端交易」。

**這種情況下的正解不是猜，是：把 live L4 在同一個 session 立刻重跑一次**，
然後拿「今天的 live」對「今天的 v17」比。資料變數就此消失。

（先跑 v17、EXIT=0 就收工，是最省事的路徑。只有 EXIT=2 才需要補跑 live。）

---

## 4. 若錨點沒過，候選成因（依機率排序）

| # | 假設 | 怎麼分辨 |
|---|---|---|
| 1 | **資料窗不同**（非 bug） | 腳本 gate [2]；差異只在尾端且金額等於尾端交易 |
| 2 | 舊的 23 個 input 有一個被 MC 重設成別的值 | 腳本 gate [1] 會逐欄印出來 |
| 3 | MaxBarsBack 自動偵測跑掉 | 檢查 MC 策略屬性，應為 **100** |
| 4 | 我的靜態分析錯了（某條分支沒退化乾淨） | 分歧點若在**中段**且與尾端無關 → 就是這個，回頭讀 §0.1 |

**第 4 項若成立，責任在我，不在 MC。**

---

## 5. 誠實聲明

1. 本檔的靜態驗證是**文字層級**的，**v17 從未經 MC12 編譯**。編譯錯誤仍有可能。
2. 基準線的 79 筆 / 877,200 為單一份報告，**細部資料停用**，成交價為 bar-level 推定。
3. 錨點只證明「新版在關閉時等同舊版」，**不證明任何新形式是好的**。那是 Run A~D 的事。
