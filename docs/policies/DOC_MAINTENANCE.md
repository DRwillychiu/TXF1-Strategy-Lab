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

## 5. 版本／參數／上線決定同步清單（2026-09-29 起）

> 起因：9/28–9/29 的 L3 決定（v18 覆蓋決定、v18.2 定案、v18.3 否決、R2 延後、停用線改人工盯）只寫在 `docs/decisions/`、`docs/ops/`，入口文件停在 9/24–9/27，閘門日期和回退版本都寫錯，G0 卻是 PASS。

**什麼時候要做**（符合任一項）
- 新增或修改 `strategies/research/<策略>/<代號>_v*/`
- 修改 `strategies/live/`
- 改了 `.pla` 的 inputs 預設值
- 改了閘門日期、上線日期或回退版本

**同一次 push 要一起更新**
1. `docs/decisions/<策略>_*.md` 追加一行：時間、決定人、內容、依據的報表（只增不改）
2. `PROGRESS.md` 追加一行：對應的 Task，或「決定：…見 `docs/decisions/…`」
3. `docs/LIVE_VERSIONS.md`：影響上架的改 §1（含排定切換）；研究版改 §2 或 §3，並寫狀態（研究／上架檔／否決）
4. 影響上線時：`docs/ops/` 的閘門表，以及 DEPT_OPS、DEPT_RISK 的「重點」
5. 研究版的 MC Load Name 沒有 `_RESEARCH` 結尾（例如上架檔）：登記到 `tools/version_exceptions.txt`，一行一個檔案，`#` 後面寫理由
6. 有事實被淘汰（日期、版本、回退版）：把舊說法加進 `tools/retired_phrases.txt`。之後入口文件如果還要提到舊說法，那一行要寫「原寫」「更正」或「已被取代」，檢查才會放過
7. 新增的 `docs/decisions/`、`docs/ops/` 文件：至少要被 PROGRESS、CLAUDE.md、部門檔、登記簿或 LIVE_VERSIONS 其中一份連到
8. 基準檔照原規定：Willy 核准後單獨 commit

**自動檢查：`verify.bat` 的 G0b（`tools/verify_versions.py`）**

| 規則 | 檢查什麼 | 沒過會怎樣 |
|---|---|---|
| R1 | `strategies/research/` 下每個 `<代號>_v*` 資料夾，都出現在 LIVE_VERSIONS（資料夾名稱，或同一行寫了策略代號和版號） | FAIL |
| R2 | 研究版 `.pla` 標頭的 MC Load Name 以 `_RESEARCH` 結尾，或登記在 `tools/version_exceptions.txt` | FAIL |
| R3 | 入口文件（CLAUDE.md、PROGRESS.md、LIVE_VERSIONS、`docs/departments/`、`docs/ops/`）沒有 `tools/retired_phrases.txt` 裡的舊說法 | FAIL |
| R4 | `docs/decisions/`、`docs/ops/` 的每個 .md，都被上面第 7 點的其中一份文件連到 | FAIL |
| R5 | `strategies/research/` 有檔案比 LIVE_VERSIONS 新 | 只警告 |

- `strategies/research/` 底下名為 `archive` 的資料夾是封存區，R1、R2 不檢查
- 紅燈時照印出的 `x` 行逐項補文件；不要為了過關刪清單或放寬規則，要改規則先問 Willy
