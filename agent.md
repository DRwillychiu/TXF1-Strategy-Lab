# agent.md — 例行工作手冊（會重複做的事）

> Willy 定義（2026-10-09）：agent.md 寫「會重複發生的事」。每一項都照固定步驟做，不重新發明。
> 規則在 `CLAUDE.md`；現況、下一步、考題、決策紀錄在 `PROJECT.md`（2026-10-31 起依 v1.0 範本，取代 PROGRESS.md 與每日計畫檔）。
> Willy 開工、收工、修正時用的提示句：`docs/policies/templates_v1.0/conversation_template.md`。

## A01 開工（新的一天，或接續舊工作）

- 觸發：Willy 說「新的一天，今天是 X 月 X 日」、提到新日期，或用對話模板 E「開工」
- 步驟：
  1. 讀 `PROJECT.md` 的「目前狀態」「下一步」；需要時再讀 `docs/registers/doubt_problems.md` 待回覆的題目
  2. 確認 GitHub 是否已推到最新；沒有就把「推送同步包」列為第一件事
  3. 第一段用早上格式：日期／標題／重點目標（30 字內）／潛在問題／解決方法／預期結果，並用三點回報目前狀態與下一步
  4. 上次沒回答的問題完整重問一次，每題附建議
- 完成：Willy 確認後才開工。不再建每日計畫檔

## A02 收工（晚上匯報）

- 觸發：「收工」「晚上匯報」、對話模板 D，或當天最後一個任務完成
- 格式：日期／標題／重點目標（30 字內）／已完成（附數據）／未完成（到哪、卡在哪、還要多久）／結果呈現／反思
- 同時更新 `PROJECT.md`：
  - 「目前狀態」「下一步」（最多 3 項）改寫成收工當下的樣子，「最後更新」改成今天
  - 新決定追加到「決策紀錄」（只追加）
  - 今天出錯的情境加進「考題」，並補對應的測試
- 最後做同步包（A04），提醒 Willy 推送

## A03 Stop hook 要求 commit／push

- 一律不 commit、不 push（Willy 規定），只回一行：變更在雲端工作區，要推時打包

## A04 打包同步 GitHub

- 觸發：「打包」「推上去」、收工，或任何一項工作完成（工作區會被重置，不累積）
- 步驟：
  1. `git fetch`；列出本機與 GitHub 不同的檔
  2. 本機比 GitHub 舊的檔不打包（避免蓋掉 GitHub 較新的）
  3. 做同步包（含 apply.py：檢查版本、檔案完整、自動清理），在 GitHub 全新複本實測 `verify.bat` 的每一步
  4. 給完整可貼上的指令：git pull → 解壓 → `python TXF1_sync_年月日\apply.py` → `push.bat "說明"`

## A05 收到 MC 報表（xlsx）

- 步驟：
  1. 讀設定頁，對 .pla 預設值（`tools/verify_settings.py`，G2）
  2. 讀交易清單：筆數、淨利、最大回撤
  3. 與答案檔或上一版逐筆比對，差異逐筆歸因
- 報告：先結論（相同／不同幾筆），再寫原因

## A06 策略轉成 Python（新策略或新版本）

- 步驟：
  1. 讀 .pla 全文
  2. 對照 `docs/research/py_modularize_rules.md` 的 R1–R13
  3. 缺的才新增模組，其餘用 `txfcore/modules/` 現有模組組裝
  4. 參數寫進 `config/strategies/`（檔名：策略_版本.toml）
  5. MC 報表存成 `tests/fixtures/`，寫逐筆考題，並登記到 `PROJECT.md`「考題」的控制組
- 完成：考題逐筆相同＋全部測試綠燈＋獨立審查（執行者不審自己）

## A07 程式交付

- 正本放 repo 正確資料夾
- 閱讀版合併成一份 `.txt` 給 Willy
- 每支完成就給，不等全部做完

## A08 新問題發生

- 已發生、已證實的 → `docs/registers/appear_problems.md`，P 編號
- 待釐清、待裁決的 → `docs/registers/doubt_problems.md`，Q 編號
- 同一次補一條會失敗的測試或檢查，並加進 `PROJECT.md`「考題」的歷史失敗

## A09 每週盤點（週五）

- 文件：過期的移到 `docs/archive/` 對應子資料夾，並在 `docs/archive/README.md` 記下被誰取代
- 登記簿：更新狀態
- `PROJECT.md`：「下一步」是否仍是真正的前 3 項；「目前狀態」是否過期
- 規則：懷疑 `CLAUDE.md` 某條規則過時 → 刪掉後跑全部考題，沒退步就提議永久刪除
- 重產 .md 清單：`python tools/md_inventory.py . docs/ops/md_inventory_年月日.md`，舊清單移到 `docs/archive/ops/`

## A10 換版上架

- 照 `docs/ops/switch_sop_20261005.md` 的格式另寫一份當次 SOP
- 條件：圖上與券商都空手、決策紀錄已寫
- 同一次完成：舊上架檔移到 `strategies/research/archive/`，新版複製進 `strategies/live/`，更新 `docs/LIVE_VERSIONS.md` 第 1 節；`verify.bat` 的 R6 會檢查三者一致

## A11 同一個修正出現第二次

- 提議寫成 `CLAUDE.md` 的規則（附原因）或 `PROJECT.md` 的考題，由 Willy 決定是否加入

## A12 實盤單出現問題（例如回吐太多、出場太慢）

- 觸發：Willy 回報某筆實盤單的出場不理想
- 步驟：
  1. 先算這一筆的事實：出場價對不對、和程式一致嗎（不是 BUG 就不要當 BUG 修）
  2. 把它當「假設」，不是規則：寫成「如果改成 X，全歷史會怎樣」
  3. 用 Python 全歷史量化：受影響幾筆、逐年、回撤、連虧、同帳戶組合回撤
  4. 結果好才寫研究版給 MC；結果變差就寫進決策紀錄並停止
- 不做：看一筆就直接改程式
