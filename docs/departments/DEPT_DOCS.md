# 文件部

> 負責：規範、進度、溝通、登記簿的維護

## 重點
- **2026-10-31 起依 v1.0 範本**（`docs/policies/templates_v1.0/`）：`CLAUDE.md` 只放規則（每條附原因），`PROJECT.md` 放目前狀態、下一步（最多 3 項）、考題、決策紀錄（只追加）、已知坑；G0 會檢查兩份的格式
- 全部 .md 一句話清單：`docs/ops/md_inventory_20261031.md`（每週五重產，agent.md A09）
- `PROGRESS.md` 已歸檔到 `docs/archive/progress/PROGRESS_20260906_20261031.md`（Phase 1–10 歷史）；不再建每日計畫檔
- `CLAUDE.md` 上限 300 行；懷疑某條規則過時 → 刪掉後跑全部考題，沒退步就提議永久刪除（agent.md A09）
- 三層架構：**CLAUDE.md（總管）→ 部門 .md（重點）→ 團隊 .md（完整細節）**
- 討論階段不給程式碼；交付一律 `.txt`；repo 存 `.pla`
- 每完成一項工作就做同步包，Willy 用 `push.bat "說明"` 推送（驗證→commit→push）
- 每週盤查 .md：已定案的新版取代舊內容，舊的進 `docs/archive/`（到 9/29 沒有任何執行紀錄；版本類的過期改由 G0b 在每次 verify.bat 自動抓）
- 版本、參數、上線決定：同一次 push 要同步的文件，照 `docs/policies/DOC_MAINTENANCE.md` §5 清單；被淘汰的舊說法加進 `tools/retired_phrases.txt`

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| 文件維護 | `docs/policies/DOC_MAINTENANCE.md` |
| 溝通規範 | `docs/policies/CONVERSATION_PROTOCOL.md` |
| 問題登記簿 | `docs/registers/appear_problems.md`（待處理）、`docs/registers/doubt_problems.md`（已裁決） |
| 決定紀錄 | `docs/decisions/`（逐條決定：時間、決定人、內容、依據；只增不改）；上線操作 `docs/ops/` |
| 版本同步檢查（G0b） | `tools/verify_versions.py`；例外清單 `tools/version_exceptions.txt`、退役說法 `tools/retired_phrases.txt` |
| 工程系統 | `docs/methodology/ENGINEERING_SYSTEM.md` |
