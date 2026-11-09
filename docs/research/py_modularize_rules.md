# Python 模組化重構：規則手冊（對抗式工程 SOP 第 0～1 步，2026-10-07）

> 範圍：把 `l2_trendshort_v5_11.py`、`l4_consolshort_v14_10.py` 拆成共用模組，之後 L3、L5、L1 直接用模組組裝。
> 設計：`docs/specs/python_module_design_20261007.md`。避坑來源：`docs/methodology/retro_TXF1_20261007.md`（T 編號）、system-dev-method §九、本 SOP 附錄 C。

## 第 0 步：假設整套有 BUG

| # | 問題 | 答案 |
|---|---|---|
| Q1 | 最壞後果 | 重構改到交易行為卻沒發現，L3、L5、L1 都建在錯的模組上，日後 Python 實盤下錯單 |
| Q2 | 反證 | ① L2 96／96 或 L4 135／135 任一列改變；② 模組單元測試輸出與原策略檔不同；③ 同一規則搜得到兩份實作 |
| Q3 | 回滾 | 舊的兩支整檔保留到新組裝版通過為止（兩版並存、輸出逐筆相同才刪）；工作區快照 `repo_delta_1007.zip` |

## 規則（每條附來源坑）

| # | 規則 | 為什麼（來源） |
|---|---|---|
| R1 | 重構只搬位置、不改邏輯；每抽一個模組就跑 L2、L4 考題 | T30 語意落差到最後才發現；SOP 第 5 步回測逐筆 diff |
| R2 | 每條規則只有一份實作，抽完搜尋舊碼確認已刪 | 同一規則兩份實作（今天 L2 假日表） |
| R3 | 名稱相同、語意不同的規則拆成兩個函式，不用參數硬湊 | SOP 附錄 C「MinList 用在價格 vs 距離方向相反」；L2 最低收盤 vs L4 最低低點 |
| R4 | MC 引擎行為（7 項）集中在一個相容設定，呼叫端不各自傳 | T12、T23、T29 平台語意 |
| R5 | 模組是純函式：輸入 K 棒、參數、狀態，輸出結果；不讀全域、不碰報價與下單 | `txfcore/LAYERS.md` 禁令一 |
| R6 | 參數只從設定檔讀，載入時比對 .pla 預設值，不一致即紅燈 | T09 版本設定、T12 輸入值保留 |
| R7 | 每個模組附單元測試，含邊界輸入 | SOP 第 6 步偽陽性 |
| R8 | 新測試接進一鍵驗證；需要 1 分 K 的慢測用環境變數跑並記錄結果 | 回顧第五節第 6 條：手動工具不算擋 |
| R9 | 每完成一步就寫進 PROJECT.md（10/31 前是 PROGRESS 與計畫檔） | 確認過的東西當下寫進 repo |
| R10 | 不新增功能、不順手優化，只搬 | 「只做負責人要的」 |
| R11 | 開工前報時間與 token，超過就先停下回報 | T36 |
| R12 | 執行者不審自己的產出：全部完成後，由一個獨立審查者只看差異清單與考題 | SOP 鐵律 |
| R13 | 不改 .pla、不改 MC 答案檔（`tests/fixtures/`） | 答案卷唯讀 |

## 依賴圖（工作順序；每一步的關卡都是 L2 96／96 ＋ L4 135／135 ＋ 全部測試綠燈）

```
D0 快照（舊兩支保留）
 → D1 MC 相容設定（profiles/mc_compat）
 → D2 行事曆單一化（刪掉 L2 檔內假日表，改用 calendar）
 → D3 資料（bars、日 K、對齊歸位到 data/）
 → D4 閘門（gates）
 → D5 停損（stops）
 → D6 出場（exits、出場鏈）
 → D7 訊號（signals）
 → D8 設定檔取代程式內參數
 → D9 獨立審查
 → D10 L3、L5、L1 用模組組裝
```

## 差異清單（預期行為變更：0）

| 規則 | 現在位置 | 搬到 |
|---|---|---|
| 假日尾盤／登錄表／靜態結算日 | L2 `HOLIDAY_TAIL`、L4 引用 L2 | `calendar` ＋ `gates/calendar_gate` |
| tick 進位、引擎停損只活進場根、同根停損、限價不計滑價、成本 1,000、日 K 收盤日歸屬 | 呼叫端各自傳 | `profiles/mc_compat` |
| 週線 13 週濾網 | L2 `_weekly` | `gates/trend_filter.weekly_sma` |
| 日線 MA20／MA60 封鎖＋F6 | L4 on_bar | `gates/trend_filter.daily_ma_block` |
| 方案 B 跳過、R1 跳過 | L2、L4 on_bar | `gates/loss_streak`（兩種模式，各一函式） |
| 冷卻、深夜封鎖、Kill | L4、L2 | `gates/cooldown`、`gates/session_block`、`gates/kill` |
| 引擎停損距離 | L2、L4 各一 | `stops/engine_stop` |
| 凍結初始停損、% 與點數上限 | L2、L4 | `stops/initial_stop`、`stops/caps` |
| 追蹤停損：最低收盤＋ATR（L2）、最低低點＋ATR 棘輪（L4） | L2、L4 | `stops/trailing` 兩個函式 |
| 硬停損 | L2 | `stops/hard_stop` |
| 優先序 0、峰值回吐、結構停利、回抽停利、TP1、時間、週線、箱體失效出場 | L2、L4 `_exits` | `exits/*` ＋ `exits/chain` |
| 空頭跌破、暴跌腿、箱體、誘多跌回 | L2、L4 | `signals/*` |

## 陷阱與刻意跳過

- 跳過：實盤執行層（停損碰價即送、進場收盤即送）。本次只重構邏輯層，執行層另案處理。
- 陷阱：模組化後 L2、L4 共用同一個 `trailing` 模組，名稱相同但語意不同 → 依 R3 拆成兩個函式。
