# 驗證部

> 負責：五道關卡、基準檔、放行與退回｜任何東西上線前都要經過這裡

## 重點
| 關卡 | 檢查 | 指令 | 何時 |
|---|---|---|---|
| G0 文件 | CLAUDE.md 行數／段落／連結、PROGRESS 格式 | `python tools\verify_docs.py .` | 每 Task |
| G1 靜態 | ASCII、結算平倉、停損三件套、進場需空手、回看 ≤ 99、無佔位 | `python tools\verify_static.py strategies\live` | 每 Task |
| G2 單元 | 規則層純函式（待建） | `pytest` | 每 Task |
| G3 基準 | 設定與逐筆交易 vs 核准基準 | `python tools\verify_baseline.py 報告.xlsx tools\baselines\Lx.json` | Phase 結束 |
| G4 券商 | 下單／改單／刪單／部位對帳（待建） | — | 上線前 |
| G5 設定 | 圖表 Data1/2/3、時段（部分由 G3 涵蓋） | — | 回測前 |

- 紅燈：退回團隊，附「問題＋三個解法」，不得放行
- 策略類 Phase 另加非 WFA 五件套（≥ 4/5 通過）
- **基準檔只能由 Willy 核准的版本產生**（`tools/make_baseline.py`），更新單獨 commit——屬 Tier 1
- 踩過的坑 → 結案時必須新增一條檢查

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| SOP 全文 | `docs/policies/VERIFICATION_SOP.md` |
| 檢查腳本 | `tools/verify_docs.py`、`verify_static.py`、`verify_baseline.py`、`mc_report.py` |
| 基準檔 | `tools/baselines/L1–L5.json` |
| 五件套 | `docs/methodology/non_WFA_validation_SOP_20260630.md` |
