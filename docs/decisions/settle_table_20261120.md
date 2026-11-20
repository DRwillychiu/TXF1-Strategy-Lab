# 決定：六支補「結算日遞延表」，修 2027-09-16 缺口（2026-11-20）

## Willy 原話（11/20）

- 「把 2027-09-16 結算日缺口先修掉。包含最新的L6策略。」

## 問題

- 六支（L1–L6）判定結算日只認「第三個週三（15–21 日）」。期交所規則：第三個週三休市時，最後交易日順延到下一個營業日。
- 2027-09-15（三）中秋休市 → 9 月合約 **2027-09-16（四）結算**。現行版（L1–L5 V1.1.0、L6 V1.0.0）那天不擋進場、12:30 不平倉；持倉會被券商用結算價現金交割，MC 圖上卻還有部位，兩邊脫鉤。
- 2019–2027 第三個週三休市共 3 次：2023-01-30、2026-02-23（已過去）、2027-09-16。來源：`data/taifex_market_closures.json`（2027 年 ＝ 期交所 116 年行事曆，台期交字第1150003597號）。

## 做法

- 六支加同樣兩行，放在第三個週三判定的下一行：

```
if Date = 1270915 then v_Settlement_Day = False;  { Settle_Skip 2027-09-15 closed }
if Date = 1270916 then v_Settlement_Day = True;   { Settle_Add  2027-09-16 deferred }
```

- 順延日當結算日處理：整天擋進場、12:30 起平倉，和一般結算日完全相同。這就是 `docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` §6.1 預定的處理方式（登錄表）；`v_Settlement_Day` 仍是純日期判定，條款 9 的豁免不受影響。
- **只放 2027 年起（實戰期）**。2023-01-30、2026-02-23 不補：這樣 2027-09-15 以前每一根 K 棒的行為都和現行版相同，歷史交易和 MC 報表逐筆一致，不必重跑 MC 驗收。
- 其他程式碼、參數、假日表都不動。L6 另把 `Build_ID` 2611193 改成 2611201（只用來辨認版本）。

## 檔案

| 策略 | 開發版 | 底版（現行上架） | 產生器 |
|---|---|---|---|
| L1_TrendLong | `strategies/research/L1_TrendLong/L1_v0.1.0/` | V1.1.0 | `scripts/research/settle_table_20261120/build_v010_l1_l5.py` |
| L2_TrendShort | `strategies/research/L2_TrendShort/L2_v0.1.0/` | V1.1.0 | 同上 |
| L3_ConsolidationLong | `strategies/research/L3_ConsolidationLong/L3_v0.1.0/` | V1.1.0 | 同上 |
| L4_ConsolidationShort | `strategies/research/L4_ConsolidationShort/L4_v0.1.0/` | V1.1.0 | 同上 |
| L5_BreakoutLong | `strategies/research/L5_BreakoutLong/L5_v0.1.0/` | V1.1.0 | 同上 |
| L6_MACrossShort | `strategies/research/L6_MACrossShort/L6_v0.1.0/` | V1.0.0 | `scripts/research/s16_streak_20261118/build_l6_v010.py` |

- 每支都有 `.pla` 和內容相同的 `.txt`。
- 編號：開發版一律 V0.X.X（Willy 11/19），上架時才給 V1.x.y。

## Python 同步

- `txfcore/tradecal/settlement.py`：新增 `SETTLE_SKIP`、`SETTLE_ADD`（＝ .pla 的兩行）與 `pla_rule()`；超出 1 分 K 驗證範圍的日子改用 `pla_rule()`，所以 Python 也會把 2027-09-16 當結算日。
- `txfcore/tradecal/gates.py`：mc12 模式（重現 MC）改用 `pla_rule()`；2027 年以前逐日與舊規則相同。
- L6 移植（`txfcore/strategies/s16_s_v1_26.py`）從 .pla 讀遞延表（`settle_shift()`）。

## 驗證

- `tests/test_settle_table_l1_l5.py`：
  - L1–L5 去註解逐詞比對 V1.1.0，只多這兩句，而且緊接在第三個週三判定後面。
  - 六支的遞延表 ＝ 休市資料算出的結果。
  - Python 行事曆：2027-09-16 是結算日、9/15 不是；2019–2026 逐日和舊規則相同。
  - 檔案全為 ASCII，G1 規範全過。
- `tests/test_l6_v010_settle.py`：
  - 合成 2027-09 行情：L6 v0.1.0 在 9/16 12:35 以 `SX_MA_Settlement` 平倉，v1.0.0 不會。
  - 2020 年起和 MC 報表 144 筆逐筆相同。
- 提醒閘：從下一個順延結算日前 45 天（2027-08-02）起，`strategies/live/` 六支若還沒有遞延表，`verify.bat` 失敗、擋推送。以後換 2028 年假日表時，同一道閘也會要求補上 2028 年的順延日。

## 上架

- 換法：`docs/ops/settle_table_switch_20261120.md`。
- 時機由 Willy 決定，最晚 2027-08-02。
