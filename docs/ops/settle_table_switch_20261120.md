# 換版步驟：六支加結算日遞延表（2027-09-16）

決定與證據：`docs/decisions/settle_table_20261120.md`。

## 一、不換會怎樣

- 2027-09-16（四）是 9 月合約結算日，因為 9/15 中秋休市而順延。
- 現行六支（L1–L5 V1.1.0、L6 V1.0.0）那天不擋進場，12:30 也不平倉。
- 結果是持倉被券商用結算價現金交割，MC 圖上卻還有部位，兩邊對不上。

## 二、檔案（開發版 V0.1.0；上架時才給 V1.x.y 編號）

| 策略 | 檔案（`.txt` 內容相同） | MC 載入名（不變） | 輸入個數 |
|---|---|---|---|
| L1 | `strategies/research/L1_TrendLong/L1_v0.1.0/L1_TrendLong_v0.1.0.pla` | `WILLY_ATR_LONG_60M` | 32 |
| L2 | `strategies/research/L2_TrendShort/L2_v0.1.0/L2_TrendShort_v0.1.0.pla` | `Trendbearish_V1` | 47 |
| L3 | `strategies/research/L3_ConsolidationLong/L3_v0.1.0/L3_ConsolidationLong_v0.1.0.pla` | `STRATEGY_WILLY_LONG_C` | 23 |
| L4 | `strategies/research/L4_ConsolidationShort/L4_v0.1.0/L4_ConsolidationShort_v0.1.0.pla` | `STRATEGY_WILLY_SHORT_CTEST2` | 29 |
| L5 | `strategies/research/L5_BreakoutLong/L5_v0.1.0/L5_BreakoutLong_v0.1.0.pla` | `STRATEGY_WILLY_LONG_BREAKOUT_C` | 41 |
| L6 | `strategies/research/L6_MACrossShort/L6_v0.1.0/L6_MACrossShort_v0.1.0.pla` | `L6_MACrossShort_v1.0.0` | 91 |

- 和現行版只差兩行：
  - `if Date = 1270915 then v_Settlement_Day = False;`
  - `if Date = 1270916 then v_Settlement_Day = True;`
- 另外只改了標頭註解；L6 的 `Build_ID` 2611193 改成 2611201。
- 輸入個數和現行版相同。
- 開發版標頭的載入名：L1–L5 寫上架名，L6 寫測試別名 `L6_MACrossShort_v010_RESEARCH`。換版時一律用上表的上架名編譯。

## 三、MC 檢查（可省略）

- 2027-09-15 以前每一根 K 棒的行為都和現行版相同，`tests/test_settle_table_l1_l5.py` 已逐詞證明，所以不必另跑 MC 對照報表。
- 要自己看的話：換版後重算，圖上的歷史交易應該和換版前完全相同（筆數、最後幾筆的進出時間與價格）。不同就停下，換回現行版，把截圖給 Claude。

## 四、換版步驟（Willy；照 `docs/ops/switch_sop_20261005.md`，一次一支）

- **時機**：Willy 決定。最晚 2027-08-02，因為從這天起 `verify.bat` 會因為上架檔沒有遞延表而失敗（`tests/test_settle_table_l1_l5.py` 的提醒閘）。
- **換版前一天**：告訴 Claude 換版日。Claude 會把六個檔案的標頭版號改成 V1.x.y，程式碼和 V0.1.0 一字不差，並附上 repo 換版腳本。

1. 圖上和券商都空手才換。關閉該圖自動交易，到券商確認沒有委託、沒有部位。
2. 截圖該圖的輸入參數，核對個數（第二節表格）。個數不對代表圖上不是預期版本，停下來。
3. 打開圖上正在用的那支訊號，整份換成新版 `.txt` 內容，然後編譯。
4. 輸入值不用改，MC 會保留圖上原本的值。只有 L6 要把 `Build_ID` 改成 2611201（只用來辨認版本，不影響交易）。
5. 圖表重新計算後確認：
   - 最後狀態是空手。
   - 歷史交易和換版前相同。
   - IOG：L1 開，其他關。
   - 每支 2 口。
6. 開啟自動交易，起始部位 0。下單大師不用改對應，出場單名沒有新增。
7. 回退：換回現行版。檔案在 `strategies/live/`，或研究版的 V1.1.0、V1.0.0。
8. 六支都換完後，在 repo 執行 Claude 給的換版腳本（先預演，再加 `--apply`），然後跑 `verify.bat`，再用 `push.bat` 推送。
