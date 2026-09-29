# 驗證部

> 負責：五道關卡、基準檔、放行與退回｜任何東西上線前都要經過這裡

## 重點
| 關卡 | 檢查 | 指令 | 何時 |
|---|---|---|---|
| G0 文件 | CLAUDE.md 行數／段落／連結、PROGRESS 格式 | `python tools\verify_docs.py .` | 每 Task |
| G1 靜態 | ASCII、結算平倉、停損三件套、進場需空手、回看 ≤ 99、無佔位 | `python tools\verify_static.py strategies\live` | 每 Task |
| G2 設定比對 | S1 報表參數 ＝ 程式預設值；S3 註解還帶舊版號；S5 兩份報表可比（期間、資本、滑價、佣金、K 棒相同） | `python tools\verify_settings.py 策略.pla 報表.xlsx`；`--compare 報表A.xlsx 報表B.xlsx` | 每份新 MC 報表 |
| 單元測試（未編號） | 規則層純函式（待建） | `pytest` | 每 Task |
| G3 基準 | 設定與逐筆交易 vs 核准基準 | `python tools\verify_baseline.py 報告.xlsx tools\baselines\Lx.json` | Phase 結束 |
| G4 券商 | 下單／改單／刪單／部位對帳（待建） | — | 上線前 |
| G5 設定 | 圖表 Data1/2/3、時段（部分由 G3 涵蓋） | — | 回測前 |

- 紅燈：退回團隊，附「問題＋三個解法」，不得放行
- 策略類 Phase 另加非 WFA 五件套（≥ 4/5 通過）
- **基準檔只能由 Willy 核准的版本產生**（`tools/make_baseline.py`），更新單獨 commit——屬 Tier 1
- 踩過的坑 → 結案時必須新增一條檢查
- 「G2」9/27 起指設定比對（`tools/verify_settings.py`，已建，目前手動執行）；原本的單元測試改為未編號、待建
- G3 的 L3 基準：`tools/baselines/L3.json` 是 v15.0 上架版報表。10/1 切換後，G3 應比對 v18.2 的 `L3_182` 報表；目前沒有這個基準檔，要等 Willy 核准後用 `tools/make_baseline.py` 產生，並單獨 commit
- L3 v18.2 上線前驗證：87 項，通過 49、沒通過 6、接受風險 2、警示 17、待實測 10、未觸發 3（9/29 19:01 更新） → `docs/ops/L3_v18.2_verification_20260929.md`；空跑與 9/30 閘門表 → `docs/ops/L3_dryrun_0929_gate_0930.md`

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| SOP 全文 | `docs/policies/VERIFICATION_SOP.md` |
| 檢查腳本 | `tools/verify_docs.py`、`verify_static.py`、`verify_baseline.py`、`mc_report.py`、`verify_settings.py`（G2 設定比對）、`verify_versions.py`（版本比對，由 `verify.bat` 執行） |
| 判定與語意檢查 | `tools/rank_cap.py`（A/B 判定：只允許指定參數不同）、`rank_l3.py`（規則 B）、`semtest_L3_daypat.py`（v19.3 語意關卡）。這三支寫死了 repo 外的路徑（`/home/claude/l3r`、`/mnt/user-data/outputs`、`/tmp/...`），在 Willy 的電腦無法直接重現；`rank_cap.py` 預設基準仍是 v18.1 |
| 基準檔 | `tools/baselines/L1.json` ~ `L5.json`（`L3.json` ＝ v15.0 上架版；v18.2 的 `L3_182` 基準待建） |
| 上線前驗證報告 | `docs/ops/L3_v18.2_verification_20260929.md` |
| 空跑與閘門 | `docs/ops/L3_dryrun_0929_gate_0930.md` |
| 五件套 | `docs/methodology/non_WFA_validation_SOP_20260630.md` |
