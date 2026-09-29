# L3_ConsolidationLong 研究版一覽

> 9/29 17:10 校對。版本與上架狀態以 [`docs/LIVE_VERSIONS.md`](../../../docs/LIVE_VERSIONS.md) 為準；本檔只是這個資料夾的索引。
> MC Load Name 取自各版 `.pla` 標頭。

- **10/1 上架檔是 `L3_v18.2`**。現行上架版 v15.0 會一直跑到 10/1 空手切換；9/30 閘門沒過，就維持 v15.0。
- **⚠ 同名風險**：下表標 ⚠ 的版本，標頭 Load Name 和上架中的 v15.0 一樣是 `STRATEGY_WILLY_LONG_C`。用這個名稱編譯或匯入 MC9，會直接蓋掉上架中的程式。
  - v18.2：只能在 10/1 空手切換當下用這個名稱；空跑要用別名編譯
  - 其他各版：研究時一律用別名編譯；標頭第 4 季改成 `_RESEARCH`
  - 這些例外都登記在 [`tools/version_exceptions.txt`](../../../tools/version_exceptions.txt)，由 G0b 檢查

| 資料夾 | 狀態 | MC Load Name（標頭） | 決定／依據 |
|---|---|---|---|
| `L3_v14.1/` | 歷史版，已被 v15.0 取代 | `STRATEGY_WILLY_LONG_C_V141_RESEARCH` | [`LIVE_VERSIONS.md`](../../../docs/LIVE_VERSIONS.md) §3 |
| `L3_v15.0/` | 現行上架版的封存（程式和 `strategies/live/L3_ConsolidationLong/` 相同）；10/1 切換後是回退用 | `STRATEGY_WILLY_LONG_C_V150_RESEARCH` | [`LIVE_VERSIONS.md`](../../../docs/LIVE_VERSIONS.md) §1；回退見 [`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md) |
| `L3_v15.1/` | 研究版，純標籤（`CL_ReEntry`），和 v15.0 逐筆相同，未 promote | `STRATEGY_WILLY_LONG_C_V151_RESEARCH` | [`L3_v15.1_label_anchor_result_20260825.md`](../../../docs/research/L3_v15.1_label_anchor_result_20260825.md) |
| `L3_v18.0/` | 研究版，需要週線。9/28 21:19 決定上架 v18（覆蓋決定），後來由 v18.1／v18.2 取代 | ⚠ `STRATEGY_WILLY_LONG_C` | [`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md)（9/28 21:19） |
| `L3_v18.1/` | 研究版：v18.0 精簡（不需週線）＋停損上限輸入 `SL_Pct`（預設 0＝關）；9/28 22:10 確認和 v18.0 逐筆相同 | ⚠ `STRATEGY_WILLY_LONG_C` | [`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md)（22:10 追加） |
| `L3_v18.2/` | **10/1 上架檔**（9/29 15:56 定案）：v18.1 程式＋預設值 `Stop_Day_Pct` 30、`Target_Room_Pct` 90、`SL_Pct` 0.7；基準報表 `L3_182` | ⚠ `STRATEGY_WILLY_LONG_C` | [`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md)（9/29 15:56）；[`L3_v18.2_verification_20260929.md`](../../../docs/ops/L3_v18.2_verification_20260929.md) |
| `L3_v18.3/` | 研究版：v18.2＋`Loser_Flat_On`（05:00 前平掉虧損單）。**9/29 16:35 否決**（樣本內淨利 −34.7%，超過 15% 上限） | `STRATEGY_WILLY_LONG_C_V183_RESEARCH` | [`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md)（9/29 16:20、16:35） |
| `L3_v19.0/` | 研究版，未上架：預設＝v15.0 行為＋`Target_Mode`、`Min_Gap_Hrs`、`Size_Mode` 開關。組 6 曾是 9/30 候選，9/28 21:19 被 v18 取代 | ⚠ `STRATEGY_WILLY_LONG_C` | [`MC_run_sheet_20260927.md`](L3_v19.0/MC_run_sheet_20260927.md)（已被取代）；[`L3_deploy_v18_20260928.md`](../../../docs/decisions/L3_deploy_v18_20260928.md) |
| `L3_v19.1/` | 研究版，未上架：v19.0＋`Stop_Cap_Pct`（組 8） | ⚠ `STRATEGY_WILLY_LONG_C` | [`MC_run_sheet_20260927.md`](L3_v19.0/MC_run_sheet_20260927.md)；[`MC_batch_20260928_L3L1L5.md`](../MC_batch_20260928_L3L1L5.md) |
| `L3_v19.2/` | 研究版，未上架：v19.1＋`Day_Pat_On`（同交易日暫停）。沒有文件記錄它的 MC 結果或結論 | ⚠ `STRATEGY_WILLY_LONG_C` | 無決定紀錄 |
| `L3_v19.3/` | 研究版，未上架：v19.2＋被跳過的單改用虛擬單追蹤。沒有文件記錄它的 MC 結果或結論 | ⚠ `STRATEGY_WILLY_LONG_C` | 無決定紀錄；語意關卡 `tools/semtest_L3_daypat.py` |
| `L3_v19.4/` | 研究版，未上架：v19.3＋`Day_Pat_Mode` 2（隔日 15:00 恢復）。沒有文件記錄它的 MC 結果或結論 | ⚠ `STRATEGY_WILLY_LONG_C` | 無決定紀錄；開關見 [`L3_v18_next_optimizations_20260928.md`](../../../docs/research/L3_v18_next_optimizations_20260928.md) |

**v18 設計（v18.2 的預設值）**
- 停損 ＝ 前一日振幅 % × 30%，下限 60 點，上限為進場價 0.7%
- 停利 ＝ 進場價 ＋（箱頂 − 進場價）× 90%
- 只在夜盤進場，部位可以留到日盤
- 停用線 1,500 點、連虧 2 筆暫停都不在程式裡，10/1 起人工盯；`Manual_Kill_Switch` 不擋新進場

**新增一版時**：同一次 push 在本表加一行，並照 [`docs/policies/DOC_MAINTENANCE.md`](../../../docs/policies/DOC_MAINTENANCE.md) §5 同步其他文件。
