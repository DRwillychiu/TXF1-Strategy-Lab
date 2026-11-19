# S16 v1.27.0 候選 — MC 跑法單（2026-11-18）

## 要跑的檔
`C:\Users\WILLY CHIU\Desktop\TXF1-Strategy-Lab\strategies\research\S16_MACrossShort\S16_S_MACrossShort_v1.27.0_candidate.txt`
（與同名 .pla 逐位元相同；.pla 雙擊會被 MC 當封裝檔，請用 .txt 複製貼上）

## 步驟
1. PowerLanguage Editor → 新增訊號，名稱 `S16_S_MACrossShort_v1270c`（新名字，避免 MC 沿用舊參數）→ 貼上 → 編譯。
2. 加到 TXF1 5 分 K 圖，設定與 11/16 的 260825 報表完全相同：2 口、滑價每口 1,000、手續費 0、原始資本 2,000,000、資料到 2026-11-16。
3. 打開參數視窗確認：第一列 `Build_ID = 261118`；最後一列 `Vol_Gate_Pct = 0.20`；共 89 個參數；其他全部是預設值。
4. 跑兩次，各匯出含交易明細的報表到 Downloads：
   - **R0**：`Vol_Gate_Pct = 0` → 必須等於 260825：**192 筆、淨利 3,232,800**。不等於就停，代表檔案或設定不對。
   - **R1**：`Vol_Gate_Pct = 0.20`（預設）→ Python 預測：**85 筆、淨利 3,582,800**（首筆 2020-03-10 10:45，末筆 2026-11-16 09:10）。

## 拿到報表後 Claude 做的事
- `python -I scripts/research/s16_v1260_port/extract_mc_trades.py <報表.xls> <trades.csv> <settings.txt>`
- 逐筆比對 R1 與 Python（`data/research_s16_20261118/candidate_v1270_trades_2020on.csv`）；對上才把 Python 的「推論」改成 MC 實證。

## 微台 2 口的預期（Python 推論，含手續費 12、期交稅）
| | 260825 | v1.27.0 候選 |
|---|---|---|
| 2020 起筆數 | 192 | 85 |
| 淨利 | 148,710 | 173,301 |
| 平倉最大回撤 | −28,113（20.1%） | −16,727（11.9%） |
| 最長連虧 | 9 | 5 |
| 快速停損筆數 | 125 | 46 |
