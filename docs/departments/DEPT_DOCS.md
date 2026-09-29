# 文件部

> 負責：規範、進度、溝通、登記簿的維護

## 重點
- `PROGRESS.md` 是進度唯一來源：**第一個未勾選的 Task ＝ 下一步**；只增不改；格式 `- [ ] Task N.M：摘要`
- `CLAUDE.md` 只放現行規範與入口，上限 300 行；達 280 行就備份切割到 `docs/archive/`
- 三層架構：**CLAUDE.md（總管）→ 部門 .md（重點）→ 團隊 .md（完整細節）**
- 討論階段不給程式碼；交付一律 `.txt`；repo 存 `.pla`
- 每個 Task 收尾用 `push.bat "Task N.M：摘要"`（驗證→commit→push 一行完成）
- 每週盤查 .md：已定案的新版取代舊內容，舊的進 `docs/archive/`（到 9/29 沒有任何執行紀錄；版本類的過期改由 G0b 在每次 verify.bat 自動抓）
- 版本、參數、上線決定：同一次 push 要同步的文件，照 `docs/policies/DOC_MAINTENANCE.md` §5 清單；被淘汰的舊說法加進 `tools/retired_phrases.txt`

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| 文件維護 | `docs/policies/DOC_MAINTENANCE.md` |
| 溝通規範 | `docs/policies/CONVERSATION_PROTOCOL.md` |
| 問題登記簿 | `docs/registers/issues_open.md`（待處理）、`docs/registers/issues_decided.md`（已裁決） |
| 決定紀錄 | `docs/decisions/`（逐條決定：時間、決定人、內容、依據；只增不改）；上線操作 `docs/ops/` |
| 版本同步檢查（G0b） | `tools/verify_versions.py`；例外清單 `tools/version_exceptions.txt`、退役說法 `tools/retired_phrases.txt` |
| 工程系統 | `docs/methodology/ENGINEERING_SYSTEM.md` |
