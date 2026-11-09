# TXF1-Strategy-Lab — PROJECT.md
<!-- 依 docs/policies/templates_v1.0/PROJECT_template.md（v1.0，2026-10-31）。CLAUDE.md 放規則，這裡放現況。
     「目前狀態」「下一步」每次收工更新；「決策紀錄」只追加不改寫；「考題」每犯一次錯就加一題。
     2026-10-31 以前的逐筆進度：docs/archive/progress/PROGRESS_20260906_20261031.md；完整待辦：docs/ops/project_breakdown_20261009.md -->

> 目標：第二階段（10/1–12/31）在控制 MDD 與連虧的前提下，讓 L1–L5 實盤帳上超過 30 萬；同時把策略轉成 Python。
> 成功定義（可驗證）：12/31 13:45 帳上總資金 > 300,000（未平倉以結算價計）；Python 版每支對 MC 報表逐筆相同。

## 目前狀態
- 階段：實盤（MC，10/5 換版）＋ Python 開發
- 最後更新：2026-11-09
- 已可運作：
  - MC 實盤五支：L1 V3.2（⚠ 版本待確認）、L2 v5.11、L3 v18.4、L4 v14.10、L5 v19.20；下單經下單大師
  - 上架 .pla 檢查（10/22、10/31）：G1 5／5、委託名稱 5／5、登錄表到期 2027/1/1；Q4 休市（10/9、10/26、12/25）與結算日（10/21、11/18、12/16）判斷正確。L1 檢查的是 `strategies/live/` 的 V3.1 檔，不一定是實際在跑的版本
  - Python：L2 v5.11 對 MC 96／96、L4 v14.10 對 MC 135／135 逐筆相同；單元測試全過
  - 一鍵檢查 `verify.bat`：G0、G0b、G1（上架檔）、委託名稱、pytest
- 未完成／已知問題：
  - GitHub 停在 9/30；10/1 之後的成果只在同步包
  - L1 實際版本待確認：10/28 圖上下單大師檔名是 `L1_TrendLong_v3.8.txt`，紀錄是 V3.2
  - 10/5 之後的實盤紀錄沒有進到專案，實盤面無法判斷
  - 從沒在 MC 實測：Kill 開關、登錄表到期、450 點上限、雙停損同價、L4 TP1 後停損口數、Data2／Data3 盤中讀值
  - Python 待做：多單版模組 → L3 → L5 → L1；實盤執行層；錄製系統與下單大師 API；Q4 平行比對
  - 待 Willy 決定：進場成交價定義、L1 基準 A4 或 G4、回覆格式以哪份為準

## 下一步（最多 3 項，依優先序）
1. C：L2、L4 出場效率量化報告（Python 全歷史：最大浮盈／浮虧、實拿比例、回吐、收盤出場延遲成本、逐年、依波動分段；空方帳戶組合回撤）→ 決定 v5.12 哪幾項進 MC、L4 第二口怎麼保護
2. Willy 推送同步包，GitHub 補上 10/1 之後的成果
3. MA空：Willy 在 MC 重測 v1.25 基準＋8/2 之後樣本外

## 考題（eval）
- 控制組（本來就該對，防退步）：
  - L2 v5.11 對 MC v5.10 報表 96／96 逐筆相同：`tests/test_port_l2_v5_11.py::test_matches_mc_v510_trade_by_trade`（需 TXF1_MIN_DATA）
  - L4 v14.10 對 T8 報表 135／135：`tests/test_port_l4_v14_10.py::test_matches_mc_t8_row_by_row`（需 TXF1_MIN_DATA）
  - 設定檔參數 ＝ .pla 預設值：`tests/test_modules.py::test_configs_equal_pla_defaults`
  - 分層邊界不被打破：`tests/test_layer_boundaries.py`
  - 上架 .pla 規範與委託名稱：`verify.bat` 的 G1 與委託名稱步驟
- 歷史失敗（出過錯，修好後要一直通過）：
  - 連虧跳過的判斷被短路跳過，L2 掉到 11 筆（審查 B1）：`test_skip_next_run_skips_whole_run_then_resets`＋L2 逐筆考題
  - 靜態結算規則漏掉遞延結算日（2023-01-30、2026-02-23）：`tests/test_engine.py::test_static_rule_misses_deferred_settlements`
  - 換了 1 分 K 資料，結算日曆卻沒重推：`test_data_guard_rejects_wrong_version`、`test_settlement_source_hash_recorded`
  - .pla 註解裡的文字被當成參數：`test_inputs_match_pla`
  - L5 v19.9 出場名稱重複（MC 會停掉策略）：`tools/check_order_names.py`（verify.bat）
  - G1 掃的是 10/5 前的舊上架檔：`tests/test_verify_docs.py::test_live_folder_matches_live_versions`
- 邊界案例（應拒絕、停單或標「待確認」）：
  - 1 分 K 雜湊不符：拒絕使用結算日曆（`test_data_guard_rejects_wrong_version`）
  - 設定檔 ≠ .pla：載入時直接報錯（`txfcore/config/loader.py`）
  - Kill、登錄表到期、假日前最後一盤、結算日：強制平倉且優先序正確（`test_forced_exit_priority_and_times`）

## 決策紀錄（只追加）
- 2026-09-22｜決定：第二階段及格 ＝ 12/31 帳上超過 30 萬；不論結果 12/31 都檢討｜原因：給第二階段一條可驗證的線｜放棄的選項：未記錄
- 2026-09-28｜決定：L3 排名規則 B（樣本外優先）｜原因：樣本外是唯一沒拿來設計的資料｜放棄的選項：只看樣本內（`docs/decisions/L3_ranking_rule_B_20260928.md`）
- 2026-09-28｜決定：L3 10/1 上架 v18 系列（後定 v18.2），覆蓋同日鎖定的規則 B 結果｜原因：Willy 以報酬與樣本外為優先；v18 未過門檻（最大連虧沒有變小），風險已揭露｜放棄的選項：規則 B 第一名「上架版＋間隔 72 小時」（`docs/decisions/L3_deploy_v18_20260928.md`）
- 2026-10-03｜決定：L2 優先降風險；連虧後只跳過下一筆｜原因：停到空頭結束會讓 12/31 前都沒有交易｜放棄的選項：停到空頭結束（`docs/decisions/L2_risk_build_20261003.md`）
- 2026-10-03｜決定：L5 `State_Start_Date` 維持 1261005｜原因：損失記憶只認 10/5 起的實盤｜放棄的選項：改用歷史起算（`docs/decisions/L5_state_start_date_20261003.md`）
- 2026-10-04｜決定：L1 A4 回歸未通過 → 10/5 L1 維持 V3.2，其餘四支換版｜原因：事前規則｜放棄的選項：L1 換 V3.8（`docs/decisions/go_live_20261005.md`）
- 2026-10-04｜決定：實盤下單全部經下單大師，MC 不直接下到實盤帳戶｜原因：只留一條下單路徑，解除重複下單風險（`docs/ops/order_lifecycle_simulation_20261004.md`）｜放棄的選項：MC 直連券商（`docs/decisions/go_live_20261005.md`）
- 2026-10-07｜決定：Q4 Python 只做訊號平行比對，最快 2027/1 接下單大師 API；進度可超前｜原因：先驗證再接手｜放棄的選項：Q4 就用 Python 下單
- 2026-10-07｜決定：Python 先模組化，策略檔只組裝｜原因：規則要能跨策略重用｜放棄的選項：每支策略一份完整 .py
- 2026-10-07｜決定：MA空（S16_S）暫停｜原因：型態判斷階段效率太低｜放棄的選項：繼續改版
- 2026-10-14｜決定：近遠月價差收斂策略放在本 repo，但作為獨立專案，資金另外準備｜原因：未記錄（Willy 10/14 指示）｜放棄的選項：未記錄
- 2026-10-31｜決定：採用 v1.0 範本：CLAUDE.md 只放規則、PROJECT.md 放現況；PROGRESS.md 歸檔｜原因：Willy 10/31 優化清單｜放棄的選項：PROGRESS.md 與 PROJECT.md 並存（兩處進度會互相矛盾）
- 2026-10-31｜決定：10/5 換版的四支複製進 `strategies/live/`，舊上架檔移到 `strategies/research/archive/live_until_20261005/`｜原因：G1 一直在檢查舊版、舊版沒有備份｜放棄的選項：維持 `strategies/live/` 舊檔
- 2026-11-06｜決定：L2 出場改版 v5.12（研究）：出場線全部盤中觸價、取最緊；獲利 ≥ 2,500 點保留 70%；跌停先走；跌破 −8% 回升保本並當天不進場；驗收：MC 全期淨利 ≥ v5.11、最大回撤不變大、逐年列出、受影響交易逐筆列出｜原因：11/6 實盤單最高 +2,177 點，移動停利線只在收盤檢查，以 TS_StopProfit +979 點出場，回吐 55%｜放棄的選項：維持 v5.11 收盤確認出場
- 2026-11-09｜決定：舊做法「實盤一筆 → 補一條規則」歸檔；規則改動改為先量化全歷史、再設計、再驗證（含樣本外與空方帳戶組合回撤）；L2 v5.12 凍結待量化；L4 第一批後保本不採用｜原因：L4 保本經 Python 全歷史驗證反而變差（淨利 −21～−34%、平倉回撤 12,950 → 20,340～22,230），證明單筆推規則不可靠｜放棄的選項：直接把 v5.12 送 MC、L4 開 TP1_BE_On

## 已知坑
- MC 會保留上次的輸入值，整批報表作廢 → 每份報表先跑 G2 設定比對
- MC 日 K 依收盤日歸屬（前一晚夜盤＋當天日盤）；Python 要用 NIGHT_FIRST
- MC 引擎停損只在進場那根有效；停損價進位到整點
- L1 是唯一 IOG ＝ true：離線重放要做到逐筆，K 棒級不夠；載入名寫 60M、實際 45M，不要改名
- 兩台電腦的 MC 回測可能不同（L1 A4）
- 雲端工作區會被重置；沒推上 GitHub 的變更只剩同步包
- 下單大師只核對部位、只提醒不補單
- L2 v5.11 的移動停利只在 60 分 K 收盤檢查、下一根才出場；同一根 K 棒急拉時，會先碰到較寬的獲利保護線（11/6 實例：少賺約 620 點）
- 完整 38 坑：`docs/methodology/retro_TXF1_20261007.md`
