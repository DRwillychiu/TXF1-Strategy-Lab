# L6_MACrossShort_v1.0.0 上架步驟單（給 Willy；2026-11-19）

> **前提**：老闆 11/20 拍板同意上線，並且空方帳戶已入金到 15 萬。沒拍板就不要做第 3 步之後的步驟。

## 已完成（Claude，11/19，全部有測試）
| 項目 | 結果 | 證據 |
|---|---|---|
| 上架候選檔 | `strategies/research/L6_MACrossShort/L6_v1.0.0/` .pla／.txt；程式碼＝S16 v1.28.1 B，只改 Build_ID 2611193 | `test_l6_v100_is_v1281_code_except_build_id` |
| MC 逐筆一致 | 144／144（到 11/19，含 11/17 以後 5 筆） | `test_l6_v100_matches_mc_v1281c_to_20261119` |
| 假日表、結算日 | 2026-11-20～2027-12-31 的假日表全部正確；結算日只有 2027-09-15 會漏（實戰期內不受影響） | `L6_calendar_check_20261119.md` |
| 參數檔 | `config/strategies/L6_v1.0.0.toml`，載入時自動和 .pla 比對 | `test_l6_v100_config_and_calendar` |
| 停單線檢查 | `tools/l6_stopline_check.py`：歷史重播最大回落 16,727，不碰 18,000；碰線情境全部觸發 | `tests/test_l6_stopline.py` |

## 你要做的（依順序）
1. **上架載入名**：`L6_MACrossShort_v1.0.0`（Willy 11/19 確認）。
2. **審查上架檔**：`strategies/research/L6_MACrossShort/L6_v1.0.0/L6_MACrossShort_v1.0.0.txt`。同意後回「L6 放上架」，我會：
   - 複製到 `strategies/live/L6_MACrossShort/L6_MACrossShort.pla`
   - 更新版本總表 §1，以及 CLAUDE.md 的帳戶資金（空方 15 萬）
   - 跑 verify
3. **券商**：空方帳戶入金到 15 萬，確認微台一口保證金 60,000。
4. **MC 載入**（圖上與券商都空手時）：
   1. 商品 TXF1，5 分 K，日盤＋夜盤，2 口。圖上歷史至少 120 個交易日，同時段門檻需要 90 天的資料。
   2. 匯入 .pla，用上架載入名編譯。
   3. 在設定頁核對輸入值（其餘一律預設）：
      - `Build_ID` 2611193
      - `TOD_Gate_Days` 90、`TOD_Gate_Q` 0.70
      - `SL_Pct` 1.00
      - `Registry_Valid_Until` 1271231
      - `Manual_Kill_Switch` false
   4. 截圖設定頁給我核對。
5. **上線第一天**：第一筆單的進出場時間、價格，和券商回報核對。
6. **每天收盤後（停單線）**：
   1. 把 MC 的 Trades List 匯出成 CSV，欄位要有 `exit_dt, entry_px, exit_px, net_ntd`。
   2. 執行下面的指令。第 2 行的 `--other` 放 L2、L4 的匯出檔，可省略。
   3. 結果是 🔴 時：**先在券商把 L6 的單平倉，再把 MC 的 `Manual_Kill_Switch` 改 true**。改輸入值會讓 MC 從頭重算，以為自己空手，但不會平掉券商的單。

完整上線確認與 SOP：`L6_golive_audit_20261120.md`

```powershell
python tools/l6_stopline_check.py --start 2026-11-23 --l6 <L6匯出.csv> --notify
```

```powershell
python tools/l6_stopline_check.py --start 2026-11-23 --l6 <L6匯出.csv> --other <L2匯出.csv> --other <L4匯出.csv> --notify
```

## 回退
- MC 停用 L6 即可。L6 是新增策略，不影響 L1–L5。
- 研究版原檔保留在 `strategies/research/S16_MACrossShort/`。
