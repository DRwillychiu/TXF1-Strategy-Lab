# 驗證工具包（放到 repo 根目錄）

- `verify.bat`：commit 前執行
  - `verify.bat` → 只跑 G1
  - `verify.bat 報告.xlsx tools\baselines\L4.json` → G1＋G3
- 檢查單一草稿：`python tools\verify_static.py strategies\research\...\草稿.pla`
- 產生新基準（僅限核准版本）：`python tools\make_baseline.py 報告.xlsx tools\baselines\L4.json`
- 需要：Python 3 ＋ `pip install openpyxl`
