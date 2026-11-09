# Python 模組化重構：獨立審查報告（2026-10-09）

> 審查對象：2026-10-07 L2 v5.11、L4 v14.10 的 Python 移植與模組拆分（規則手冊 `docs/research/py_modularize_rules.md` R1–R13）。
> 立場：預設有 BUG。只寫報告，沒有修改任何程式、設定、.pla 或考題。
> 審查用的腳本放在 session 暫存區，沒有進 repo。

## 結論

- 問題數：高 1、中 7、低 13
- 新移植本身：L2、L4 組裝檔逐行對照 .pla，**沒有找到交易邏輯錯誤**（含預設值沒走到的路徑）。問題集中在「新舊兩版並存」「相容設定沒被使用」「測試與一鍵驗證的缺口」
- 其他三支舊移植：全套 pytest 353 過、2 跳過（兩個慢測）。另外把 HEAD 版 txfcore 抽出來，和工作區各跑一次 L1、L3、L5，**逐筆相同**（517／457／258 筆，價格與淨損益都相同）
- 慢測等價重跑：指定的 `TXF1_1_分鐘_1.txt` 不存在，改用 `/mnt/user-data/uploads/TXF1_1_分鐘.txt`（到 2026/9/11 19:55）。MC 考題的每一列出場都早於這個日期，所以考題全部涵蓋：L2 96／96、L4 135／135，**依原順序逐列比對**也相同

## 一、問題清單

| 編號 | 嚴重度 | 位置（檔案:行） | 問題 | 證據（.pla 行號或重現方式） | 建議修法 |
|---|---|---|---|---|---|
| H1 | 高 | `tools/signals.py:41,43`、`tools/report.py:40,42,186,189`、`tools/m2.py:34,36`、`tools/verify_claims.py:33,35`、`tools/flow_check.py:42,44`、`tools/slippage_impact.py:40,42`、`txfcore/parity/golden.py:97`、`txfcore/strategies/versions.py:48,62` | 舊檔 `l2_trendshort.py`（v5.4）、`l4_consolshort.py`（v14.7＝v14.6 行為）仍在，而且所有工具都還在用舊檔。`signals.py` 的用途是「輸出下一根要下的單，拿去跟 MC12 實盤比對」，但 MC 實盤從 10/5 起跑 v5.11／v14.10。舊檔沒有暴跌腿、方案 B 跳過、450 上限、硬停損、TP1、0.8% 上限等規則，算出來的訊號版本不同。同時違反 R2：週線濾網、引擎停損距離、停損上限、追蹤停損、出場鏈各有兩份實作 | `grep -rn "l2_trendshort import\|l4_consolshort import"` 列出 6 支工具、`parity/golden.py`、3 個測試檔；舊檔 docstring 第 1 行寫「移植自 v5.4」「移植自 v14.7」；`versions.py:62` 仍寫 L4「v14.6 PRODUCTION」 | 依規則手冊 Q3「新組裝版通過即刪舊」：工具與 `golden.py` 改用 `l2_trendshort_v5_11`、`l4_consolshort_v14_10`。舊檔要留作研究，就改名成 `_v5_4`、`_v14_7` 並從工具移除。`versions.py` 同步更新 |
| M1 | 中 | `tests/test_port_l2_v5_11.py:51`、`tests/test_port_l4_v14_10.py:103` | 兩個慢測都用「進場時間 ≥ MC 第一筆」過濾 Python 交易，把 MC 圖表起算日前的 Python 交易丟掉，不檢查也不報數量。Python 比 MC 早開始交易，這些交易會改變狀態（L2 的連虧計數、跳過次數）。目前 96／96 是「狀態剛好對齊」，不是「起算點對齊」；如果 Python 在 MC 第一筆之前多出假交易，測試照樣會過 | 重跑結果：L2 有 10 筆被丟（2019-05-23 起，前 5 筆全是虧損，例如 -10,400、-21,600），L4 有 18 列被丟（2019-05-24 起） | 在考題檔記錄 MC 圖表第一根 K 棒的日期，Python 從同一天開始餵資料；或斷言被丟的筆數等於固定值，並寫明原因。至少要 assert 被丟筆數並印出 |
| M2 | 中 | `txfcore/profiles/mc_compat.py:20-33`；`tests/test_port_l2_v5_11.py:47-48`；`tests/test_port_l4_v14_10.py:97-100`；`txfcore/strategies/l4_consolshort_v14_10.py:33`；`txfcore/modules/gates/basic.py:10` | 違反 R4（MC 引擎行為集中在一個相容設定）。整個 repo 沒有任何地方 import `mc_compat`：兩個考題自己組 `FillPolicy`、成本 1000、`allow_multi_exit_per_bar`、迄日 1260924；`DAILY_MODE`、`STATIC_SETTLEMENT`、`MC_LAST_DATE` 三個常數沒人用；靜態結算日寫死在 `calendar_flags` 的預設參數；MaxBarsBack 100 寫在 L4 策略檔裡。相容設定改了，考題不會跟著變 | `grep -rn mc_compat` 只找到它自己；`grep STATIC_SETTLEMENT\|DAILY_MODE\|MC_LAST_DATE` 只有定義列 | 考題改用 `mc_compat.single_runner`／`multi_runner` 與 `DAILY_MODE`、`MC_LAST_DATE`；`calendar_flags` 的 static 參數由 profile 傳入；`MAX_BARS_BACK` 移進 profile 或設定檔 |
| M3 | 中 | `txfcore/modules/gates/basic.py:9-18`；`l2_trendshort_v5_11.py:98`；`l4_consolshort_v14_10.py:92` | 新策略呼叫 `calendar_flags` 時沒有傳參數，固定用 .pla 靜態結算日規則。回測對 MC 是對的，但 Python 實盤也會用這條規則。這條規則漏標農曆年後遞延的結算日（2023-01-30、2026-02-23），9/8 已修正成用資料反推（`tradecal/gates.py:39-42` 寫明「那兩天實盤上不會強制平倉」）。新模組繞過了這個修正，而且策略沒有開關可以切換 | `tradecal.gates.evaluate` 預設 `use_data_settlement=True`，`calendar_flags` 預設 `static_settlement=True`，兩者相反；舊移植用的是 `view.calendar`（資料反推） | 由執行模式決定：MC 對帳時 profile 傳 static，實盤傳資料反推。實盤啟用前補一個測試：1230130、1260223 這兩天要判定為結算日 |
| M4 | 中 | `txfcore/engine/fill_mc12.py:154-162`（round_trigger）；`runtime/backtest.py:229-235`、`runtime/multi.py:199-205`（_cost）；`mc_compat.py:3-10` | `mc_compat` 說「每一項都有逐筆實證」，但 tick 進位與限價免滑價的證據只來自空單出場（L2 的 TS_StopProfit 買停損、L4 的 TP1 買限價）。多單方向的進位（賣停損往下、賣限價往上、買限價往下）、**限價進場**免滑價（L5 Bot／Mid 兩腿都是限價進場），都沒有驗證。D10 用這份 profile 組裝 L3、L5 時會直接套用 | 審查重跑：L3、L5 開 `round_to_tick` 後交易列不變，但淨利分別 -37,179、-32,987；開 `mc_cost_per_lot_side=1000` 後，L5 限價進場那一邊的成本變 0。**未驗證**：MC 對限價進場是否真的不加滑價 | D10 前拿 L3、L5 的 MC 報表逐筆驗證這兩項。在驗證前，`mc_compat` 的 docstring 註明「只對空單出場驗證過」 |
| M5 | 中 | `verify.bat` | 違反 R8。一鍵驗證完全不跑 pytest，所以 `test_modules.py`、兩個移植考題（含 R6 的設定檔比對）都不在一鍵驗證裡。慢測也沒有「設了環境變數就跑並記錄結果」的機制 | `grep -n pytest verify.bat` 沒有結果；`git diff verify.bat` 只新增 G0b | 在 verify.bat 加入 `python -m pytest -q tests/`；`TXF1_MIN_DATA` 有設時跑慢測，並把筆數與結果寫進 log |
| M6 | 中 | `txfcore/config/loader.py:30-38`；`l2_trendshort_v5_11.py:34`；`l4_consolshort_v14_10.py:30` | R6 只做了一半。規則是「載入時比對 .pla，不一致即紅燈」，實際上策略載入時沒有比對，只有單元測試比（而且 M5 讓這個測試不在一鍵驗證裡）。比對也太寬：數值參數寫成布林、布林寫成 1 都會通過；呼叫端傳入的 `StrategyConfig.params` 拼錯字（例如 `SL_pct`）會被 `setdefault` 吞掉，靜默改用預設值 | 審查重跑：`Hard_Stop_On=True` → `check_against_pla` 回 `[]`；`Freeze_SL_On=1` → 回 `[]` | `load_strategy` 內呼叫 `check_against_pla`，不一致就 raise；型別必須和 .pla 一致；`__init__` 檢查傳入參數名稱都存在於 .pla |
| M7 | 中 | `tests/test_modules.py` | R7「每個模組附單元測試，含邊界」沒有做到。下列模組完全沒有單元測試，而預設值沒走到的路徑剛好都在這些模組裡：`WeeklySmaFilter`、`DailyMaBlock`（Macro_Mode 1／2／3）、`CloseInvalidatedBox`、`CrashLeg`（Leg_Max、Reset_Bars）、`Zlema`、`LowestCloseTrail`、`StreakSkip`（N>0、State_Start_Date）、`SkipNextRun` 的 Pause_Mode 0 與 `release_pause`、假日／結算／Kill 不消耗跳過次數、`calendar_flags` 登錄表到期、`weekly_exit_short`、`box_break_exit_short`、`structure_tp_short`、BE／SP 價位 | 檢視 `tests/test_modules.py` 第 1-113 行的 import 與測試函式 | 每個模組依 .pla 行號補輸入→輸出測試，至少涵蓋第三節列出的非預設分支 |
| L1 | 低 | `tests/test_port_l4_v14_10.py:104-109` | 比對前先 `sorted`，又沒有比進出場價。因為每列都帶進場時間，配對不會被蓋掉；但同一根 K 棒上 TP1 與停損兩列的先後順序錯了不會被發現，而這個順序會影響 TotalTrades／NetProfit 的時序（R1 連虧開啟時有影響） | 審查用原順序重跑，135 列逐列相同，所以**目前沒有被蓋掉的錯誤** | 改成依原順序 `zip` 比對（同 L2 考題），並加上進出場價 |
| L2 | 低 | `txfcore/modules/exits/core.py:59-63` | 違反 R3：`time_exit` 用 `zero_means_off` 參數硬湊兩種語意（L2：0 ＝ 關；L4：0 ＝ 每根成立） | L2 .pla 708 有 `Crash_Time_Bars > 0`；L4 .pla 482 沒有 | 拆成 `time_exit_zero_off` 與 `time_exit_mc_literal` 兩個函式 |
| L3 | 低 | `txfcore/modules/gates/loss_streak.py:11-53` | `SkipNextRun` 用 `mode` 參數同時包了 Pause_Mode 0（暫停到濾網關閉）與 1（跳過下一段），屬於 R3 的灰色地帶。邏輯照抄 .pla 380-406，沒有錯 | 對照 .pla 388-392、401-406 | 把 mode 0 拆成 `PauseUntilFilterOff` |
| L4 | 低 | `tests/test_port_l2_v5_11.py:19-26`、`tests/test_port_l4_v14_10.py:76-83`、`txfcore/config/loader.py:17-27` | 解析 .pla Inputs 的程式有三份（R2） | 三處都用同一個正規式 | 測試改呼叫 `loader.pla_inputs` |
| L5 | 低 | `txfcore/runtime/multi.py:128`、`runtime/backtest.py:167` | `_entry_limit` 只記「最後一次進場」的單別，套用到所有腿的出場成本。L5 兩腿都是限價，所以目前不受影響；如果兩腿單別不同，用 mc 成本時會算錯 | 程式閱讀 | 進場單別記在每一腿（`open_leg`）上 |
| L6 | 低 | `txfcore/engine/fill_mc12.py` 的 `_adversity`、`_sort_key` | 排序同根成交先後時用的是未進位的價格，觸發判斷與成交價用的是進位後的價格。只有價位差不到 1 點的同根競爭才可能排錯 | 程式閱讀 | 排序也用 `round_trigger` 之後的價格 |
| L7 | 低 | `txfcore/runtime/multi.py`（`res.oco_cancelled += ...`） | 開啟 `allow_multi_exit_per_bar` 後，同一根成交兩張出場單時 OCO 撤單數會重複計算（只影響統計） | 程式閱讀 | 改成每根只算一次 |
| L8 | 低 | L2 .pla 314-326、L4 .pla 209-221 | 「登錄表到期前 30 天在圖上警示」沒有移植。回測沒影響；Python 實盤會少一個到期提醒 | 新組裝檔沒有對應段落 | 實盤層補告警（不放進策略邏輯） |
| L9 | 低 | `txfcore/strategies/base.py:143-150` 與兩份 toml | 登錄表期限、假日平倉時間各有兩個來源：`StrategyConfig.registry_valid_until`、`holiday_flat_time`，以及 `params["Registry_Valid_Until"]`、`params["Holiday_Flat_Time"]`。執行器的 `view.calendar` 用前者，新策略用後者，改 toml 時兩邊會不一致 | 程式閱讀 | 新策略的 config 欄位由 params 帶入，或在載入時檢查兩邊相等 |
| L10 | 低 | `docs/specs/python_module_design_20261007.md:96-123`、規則手冊差異清單 52-63 | 文件和實際結構不一致：設計列的 `calendar_gate`、`kill`、`cooldown`、`session_block`、`chain.py`、`data/`、`calendar/` 都不存在（D2、D3 沒做完，出場鏈仍留在策略檔）；差異清單寫「假日表搬到 calendar」，實際仍在 `tradecal/registry.py` | 檢視 `txfcore/modules/` 目錄 | 更新設計與差異清單，或補完 D2、D3 |
| L11 | 低 | `l2_trendshort_v5_11.py:83-84`、`l4_consolshort_v14_10.py:77-78` | `expected_trigger_range` 寫 (96, 96)、(135, 135)，但 Python 全期是 106 筆、153 列（多出的是 MC 起算日前的交易）。用這個值做完整度檢查會誤報 | 審查重跑 | 改成 Python 全期筆數，或註明只適用於 MC 區間 |
| L12 | 低 | `tools/status.py:74`、`signals.py:55`、`equity.py:50`、`flow_check.py:133`、`m2.py:42`、`report.py:66`、`slippage_impact.py:48` | `weekly_bars` 有 7 份實作（R2，這次重構之前就存在） | `grep -rn "def weekly_bars"` | 移到 `quotes/daily.py`，只留一份 |
| L13 | 低 | `tests/fixtures/`、`strategies/research/L2_TrendShort/L2_v5.11/`、`L4_v14.10/` | R13 的答案卷與 .pla 都還沒進 git（untracked），沒有雜湊基準，無法證明沒被改過 | `git status --short` 顯示 `?? tests/fixtures/` 等 | 提交，並在考題檔記錄 SHA-256 |

## 二、.pla 區塊 → Python 對照（執行順序一致）

### L2 v5.11（`l2_trendshort_v5_11.py`）

- 197-205 IsDay／IsNight → `in_closed_window(t, 845, 1245)`（含 1245，與 .pla 的 `<=` 一致）
- 293-312 假日、登錄表、結算 → `calendar_flags`（登錄表到期 ⇒ 假日封鎖為真，`tradecal/gates.py:72-74`）
- 329-365 週線 → `WeeklySmaFilter.update`（觸發條件 Time[1]=1245 且 Date[1] 為週五；存 Close[1]；暖機未滿 13 週時 ok＝False）
- 368-372 指標 → `avg_true_range`、`lowest(low, 30, offset=1)`、`Zlema.update`（每根無條件更新）
- 376-377 部位類型 → `pend_bar == bar_no - 1`
- 380-398 連虧計數 → `SkipNextRun.count`（只算 `pos_type != 1`；用 NetProfit 差額判斷輸贏）
- 401-406 Pause_Mode 0 解除 → `release_pause`（同根先設定再判斷，順序與 .pla 一致）
- 409-425 空頭訊號 → `channel_breakdown`、`falling`、`below_ema`、`Wk_Entry_Filter`
- 429-449 跳過段與進場閘門 → `SkipNextRun.allow`（每根都呼叫；假日／結算／Kill 不消耗跳過次數）
- 452-458 腿結束 → `CrashLeg.update_leg`（`High >= leg_hh` 或 `Reset_Bars > 0` 且滿 N 根）
- 461-487 暴跌 → `CrashLeg.check`（Highest 每根都算；距離 MinList 取小，因為是「距離」）
- 491-502 引擎停損 → `engine_stop_distance`（只在空手時設定，暴跌時改用暴跌距離）
- 505-513 進場 → 空頭優先，暴跌其次
- 517-536 凍結初始停損 → `initial_stop_short`（BarsSinceEntry＝0 且未鎖定；空手時重置）
- 539-568 追蹤啟動 → `accel_newlow_bar`＋`TwoBarArm`（C1_Bar[1] ＝ 上一根的值，空手時歸零）
- 572-608 追蹤 → `LowestCloseTrail.active_stop`（比較的是「線 < 初始停損」，採用的是「線＋1.1 ATR」，照抄 .pla）
- 611-612 450 上限 → `cap_short(..., pct=0, max_pts)`
- 615-644 回抽停利 → `retrace_tp_short`（`>=` 與 `>` 的方向和 .pla 一致）
- 647-664 峰值回吐 → `PeakGivebackShort`（空手時重置；達門檻才更新峰值）
- 667-674 暴跌停損 → `ratchet_lowest_low_short`（BarsSinceEntry＝0 時以進場價＋距離起算）
- 679-777 出場鏈 → `_exits`：優先序 0 → 暴跌單專用出場後直接結束 → 週線 → 結構 → 回抽 → 峰值回吐 → 日盤停損單 → 夜盤收盤確認；硬停損在鏈外、每根都掛

### L4 v14.10（`l4_consolshort_v14_10.py`）

- 188-207 行事曆 → `calendar_flags`；224-226 深夜封鎖 → `in_window(t, 200, 500)`（含 200、不含 500）
- 229-241 日線封鎖 → `DailyMaBlock.update`（MA60[1] ＝ 上一根 15 分 K 時的值，每根都呼叫，所以 [1] 的語意正確；Macro_Mode 0／1／2／3 分支與 .pla 相同）
- 244-269 60 分箱 → `CloseInvalidatedBox.update`＋`below_ma`
- 272 ATR → `avg_true_range(d1, 60)`
- 278-295 R1 連虧 → `StreakSkip.update`（只在空手時結算；`prev_tt` 每根都更新；N ≤ 0 時清除）
- 299-304 冷卻 → `Cooldown.update`（MarketPosition[1] ＝ `state.prev_market_position`）
- 306-353 箱內：誘多區 → `TrapZone`；引擎停損 → `engine_stop_distance`；進場 → 條件同 .pla，跳過時照樣關閉誘多區
- 357-376 空手：鎖箱（只看 `is_in_consolidation`，不看上下緣大小）與全部重置 → 相同
- 378-441 持倉管理 → 最低低點、追蹤啟動、凍結、`v_Stop_Level[1]`（`ps.stop_level` 保存上一根封頂後的值）、Freeze_SL_On=false 的箱頂下修、0.8% 與 450 上限、峰值、TP1 價、TP1_Done、BE／SP 啟動 → 相同
- 445-506 出場鏈 → 優先序 0 → 箱體失效 → 時間（0 照 .pla 每根成立）→ TP1 限價 1 口 → SP ＞ BE ＞ SL 擇一停損單；送出市價出場的那一根不送 TP1 與停損

## 三、預設值沒走到的路徑

逐行比對沒有發現差異。另外在 MC 相容模式下各跑一次，確認不會當掉、行為方向合理（資料到 2026/9/11）：

| 情境 | 筆數（列數） | 淨利 | 觀察 |
|---|---|---|---|
| L2 預設 | 106 | 3,310,000 | MC 區間內 96／96 |
| L2 Kill＝True | 0 | 0 | 擋進場 ✓ |
| L2 登錄表＝1250101 | 88 | 1,367,600 | 最後一筆進場 2024-09-11，之後沒有進場 ✓（到期當下沒有持倉，所以 TS_RegistryEnd 沒有被觸發，**這條出場未實測**） |
| L2 Pause_Mode 0 | 79 | 3,058,800 | 暫停生效 |
| L2 Pause_Mode 0＋Bear_Pause_Bars 30 | 109 | 3,169,600 | 會提早解除 |
| L2 Crash_Leg_Reset_Bars 10 | 126 | 3,072,400 | 暴跌單 11 → 28 |
| L2 Crash_Leg_Max 0 | 128 | 3,052,000 | 暴跌單 30 |
| L2 Crash_Time_Bars 0 | 106 | 3,310,000 | 與預設相同（預設 40 本來就沒有觸發過 CR_Time），符合「0 ＝ 關」 |
| L2 Skip_K 2 | 102 | 3,264,400 | — |
| L4 預設 | 153 | 693,800 | MC 區間內 135／135 |
| L4 Kill＝True | 0 | 0 | ✓ |
| L4 登錄表＝1250101 | 131 | -156,800 | 最後一筆進場 2024-12-12 ✓（CS_RegistryEnd **未實測**） |
| L4 Macro_Mode 1／2／3 | 255／228／562 | 777,400／889,000／-355,800 | 封鎖逐級放寬 ✓ |
| L4 Freeze_SL_On false | 153 | 684,200 | 有差異，箱頂下修路徑有執行 |
| L4 BE 100 | 154 | 619,200 | 出現 CS_BE 12 |
| L4 SP 150 | 152 | 586,600 | 出現 CS_SP 5 |
| L4 TP1_BE_On | 157 | 455,400 | CS_BE 53 |
| L4 Time_Stop_Bars 0 | 102 | 169,200 | CS_TimeExit 96（照 .pla，進場後下一根就出場）✓ |
| L4 Streak_Skip_N 2 | 131 | 264,000 | — |
| L4 Streak 2＋State_Start_Date 1240101 | 149 | 186,400 | 起算日之前不計 ✓ |

- 這些數字只證明「路徑有執行、方向合理」，**沒有 MC 報表可以逐筆對照，屬於未驗證**

## 四、執行器與撮合的改動

- 預設參數下全部是空操作：`round_to_tick=False` 時直接回傳原價；`engine_stop_entry_bar_only=False` 時條件不變；`mc_cost_per_lot_side=None` 時走原本的 `trade_cost`；`allow_multi_exit_per_bar=False` 時 `closed_this_bar` 恆為 True；PositionView 新增的兩個欄位舊策略不會讀
- 實證：HEAD 與工作區分別跑 L1、L3、L5（照 `tools/report.py` 的組法），逐筆相同
- 限價不計滑價：只在傳了 `mc_cost_per_lot_side` 時才生效，舊移植不受影響；套到 L3、L5 前要先驗證（M4）
- 多出場同根：在 L3、L5 開啟後，歷史交易逐筆不變（沒有發生同根兩張出場的情況）。程式面：L5 同一腿的第二張出場會因為 `pos.leg(from_entry) is None` 被作廢；全倉出場在平倉後因 `pos.is_flat` 被擋；部分出場後的全倉單數量會被截成剩餘口數。**判定安全**，只剩 L7 的統計重複計算。但 L5 兩腿同根各自出場的情況，開關前後行為不同（關閉時第二腿要延到下一根），D10 時要用 MC 報表確認哪一種才對

## 五、測試偽陽性

- L2 考題：依原順序 `zip` 比對，並比較價格、淨損益、標籤 → 結構正確；缺口是 M1（MC 起算日前的交易被丟掉）
- L4 考題：用 `sorted`，但每列都帶進場時間與出場時間，所以配對不會被蓋掉；審查用原順序重跑，135 列逐列相同 → 目前沒有被蓋掉的錯誤，但測試本身偏弱（L1）
- `test_modules.py`：有涵蓋的邊界都正確（例如 `in_window` 不含 500、`time_exit` 的 0、`cap_short` 在 56,250 點上下由哪一條綁住）；缺口是 M7

## 六、確認沒問題的項目

- L2 v5.11、L4 v14.10 組裝檔與 .pla 逐行語意一致，執行順序一致（第二節）
- 邊界條件：`>=`／`>`、MinList 方向（空單的價格與距離都取小 ＝ 較緊）、`[1]` 歷史值（ZLEMA、C1_Bar、MA60、v_Stop_Level、MarketPosition）、BarsSinceEntry＝0 的初始化、空手時的重置，全部與 .pla 相同
- 預設值沒走到的路徑（Kill、登錄表到期、Pause_Mode 0、Crash_Leg_Reset_Bars、Streak_Skip_N、State_Start_Date、Freeze_SL_On false、Macro_Mode 1／2／3、BE、SP、TP1_BE_On、Time_Stop_Bars 0）逐行比對無差異，並且都實際跑過（第三節）
- 假日表只剩一份（`tradecal/registry.py`），63 筆，與兩份 .pla 的 `Holiday_Tail` 逐筆相同；舊 L2 檔內的假日表已刪除
- 兩份 toml 與 .pla 預設值一致（41／29 個 input）
- R3：L2 的最低收盤追蹤與 L4 的最低低點棘輪分成兩個函式；L2 方案 B 與 L4 R1 分成兩個類別；`ratchet_lowest_low_short` 同時給 L4 追蹤與 L2 暴跌停損用，兩者公式相同，合併正確
- 全套 pytest：353 過、2 跳過
- 執行器與撮合改動在預設參數下不改變 L1、L3、L5（逐筆實證）
- MC 相容模式下，L2 96／96、L4 135／135 依原順序逐列相同（用到 9/11 的資料，涵蓋考題全部列）
