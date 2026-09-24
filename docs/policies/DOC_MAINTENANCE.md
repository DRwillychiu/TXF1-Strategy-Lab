# 文件維護規則（2026-09-23）

## 1. CLAUDE.md
- **只放「現行規範」**：技術規格、強制規範、流程、品質門檻、文件地圖
- **不放**：歷史、變更紀錄、已被取代的版本、個案討論
- 上限 300 行；由 `tools/verify_docs.py`（G0）自動檢查，超過即擋下 commit
- 達到 280 行時處理：
  1. 整份備份到 `docs/archive/CLAUDE_YYYYMMDD.md`
  2. 把「已被取代」「只在特定專案用到」的段落移到對應的 `docs/policies/*.md`
  3. CLAUDE.md 留一行指向新位置
- 切割後舊資料仍查得到：`docs/archive/` ＋ git 歷史

## 2. PROGRESS.md
- 只增不改；完成的 Phase 不回頭編輯
- 格式固定 `- [ ] Task N.M：摘要`，由 G0 檢查
- 每季（或超過 600 行）封存：`docs/archive/PROGRESS_2026Q3.md`，主檔留最近兩個 Phase ＋ 一行索引

## 3. 其他 .md
- 每週盤查一次：已定案的新版本取代舊內容，舊內容移到 `docs/archive/`
- 規則類放 `docs/policies/`、流程類放 `docs/methodology/`、設計類放 `docs/specs/`、報告放 `docs/reports/<季度>_<主題>/`

## 4. 在其他平台／AI／裝置接手
- 必讀：`CLAUDE.md` → `PROGRESS.md` → 目前 Phase 的 Spec
- 需要時再讀：`docs/policies/VERIFICATION_SOP.md`、`docs/registers/`
