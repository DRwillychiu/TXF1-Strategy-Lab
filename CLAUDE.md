# TXF1-Strategy-Lab — CLAUDE.md
<!-- 依 docs/policies/templates_v1.0/project_CLAUDE.md（v1.0，2026-10-31）。
     只放本專案特有的東西；跨專案通用規則在全域 CLAUDE.md（docs/policies/templates_v1.0/global_CLAUDE.md）。
     規則的新增／刪除原因寫在推送說明，不寫在這裡。懷疑某條過時：刪掉後跑考題，沒退步就永久刪除。 -->

<context>
- 專案：TXF1-Strategy-Lab｜目的：台指期六支策略（L1–L6）在 MultiCharts 實盤；Python（txfcore）逐筆重現 MC，逐步接手
- 實盤：微台每支 2 口；多方帳戶 15 萬（L1、L3、L5；2026-11-20 Willy 定）、空方帳戶 15 萬（L2、L4、L6；L6 資金 12 萬，2026-11-20 起）；MC → 下單大師 → 凱基期貨
- 商品：大台 1 點 200 元、微台 1 點 10 元；日盤 08:45–13:45、夜盤 15:00–05:00
- MC 回測口徑：2 口、滑價每口每邊 1,000 元（限價單不計）、手續費 0
- 技術棧：PowerLanguage（MC9 實盤、MC12 研究）；Python 3.11 標準庫＋pytest
- 上架版本：`docs/LIVE_VERSIONS.md`（唯一來源）
- 慣例：`strategies/live/` 是 MC 正在跑的 .pla（檔名不帶版號）；`strategies/research/archive/` 是退役區；`tests/fixtures/` 是 MC 報表（唯讀）；PowerLanguage 規則在 `~/.claude/rules/powerlanguage.md`，碰 .pla 時自動載入
- 已終止的策略都在 `strategies/research/archive/`（資料夾名含 killed／archived，各附終止理由）；新點子先查這裡，不重做已終止的
- 現況、下一步、考題、決策紀錄：@PROJECT.md
- 例行工作（開工、收工、打包、收 MC 報表、換版）：`agent.md`
- 全域規則：Willy 電腦上放 `~/.claude/CLAUDE.md`；雲端工作階段沒有該檔時，先讀 `docs/policies/templates_v1.0/global_CLAUDE.md`
</context>

<commands>
- 全部檢查（推送前必跑）：`verify.bat` ＝ G0 文件＋G0b 版本同步＋G1 上架 .pla 規範＋委託名稱＋pytest
- 單元測試：`python -m pytest -q -p no:cacheprovider tests`
- MC 逐筆考題：`set TXF1_MIN_DATA=<1 分 K 檔>` 後跑 `tests/test_port_l2_v5_11.py`、`tests/test_port_l4_v14_10.py`（9/24 資料，約 70 秒）
- 報表設定比對（G2）：`python tools/verify_settings.py <策略.pla> <MC 報表.xlsx>`
- 推送（Willy 執行）：`push.bat "說明"`
- .md 清單：`python tools/md_inventory.py . <輸出.md>`
</commands>

<project_rules>
- 會動到實盤的動作先停下，等 Willy 同意才做：覆蓋 `strategies/live/`、更新 `tools/baselines/`、上架編譯、券商與下單大師設定。研究和研究檔的修改，一路做到交付物（能匯入的 .pla＋跑完就能判對錯的預測）才停，中間步驟不停。原因：直接賠錢的是實盤；Willy 2026-11-26 裁示，每個中間步驟都停下等審查只會拖慢進度、產生過程文件。
- Spec 沒寫的設計決策不自行發明；矛盾或缺漏就標註並停下來問。原因：策略邏輯、參數、上架版本都是 Willy 的決定（9/28 定）。
- 基準檔（`tools/baselines/`）只能由 Willy 核准的版本產生，更新單獨一次推送。原因：基準檔是 G3 的答案卷，基準錯了，錯誤會通過驗證。
- 文件同步：版本、參數、上線決定，同一次推送要一起更新 `docs/LIVE_VERSIONS.md`、`PROJECT.md` 決策紀錄、`docs/decisions/`、受影響的部門檔與 `docs/ops/`（清單見 `docs/policies/DOC_MAINTENANCE.md` §5）。原因：9/28–9/29 的 L3 決定只寫進 decisions、ops，入口文件停在舊版。
- Claude 不 commit、不 push（`.claude/settings.json` 與 hook 已強制）；整理成同步包，由 Willy 用 push.bat 推。原因：Willy 規定；push.bat 會在他電腦上先跑檢查、列出檔案給他確認。
- 每完成一項工作就做同步包並提醒推送，不累積。原因：雲端工作區會被重置；10/28 重置時，10/22 的變更只存在工作區而遺失。
- .env、TG 金鑰、帳密不進 git，只提交 .env.example。原因：資安。
- 只在圖上與券商都空手時，用上架載入名編譯。原因：編譯會重算歷史，持倉中會讓 MC 部位和券商不一致。
- 換版時，舊上架檔先移到 `strategies/research/archive/`，再覆蓋 `strategies/live/`，同一次更新 LIVE_VERSIONS 與決策紀錄。原因：10/31 補做時發現 L2 v5.3、L4 v14.6、L5 v19.9 沒有備份，G1 也一直在檢查舊版。
- MC 數字只採用 Willy 自己跑的報表；自己推導的結論標「推論」，來源不明的數字標「待確認」。原因：估算不能當實證（9/27 定）。
- 驗收標準在看到結果前寫死，附對照組，逐年看而不只看全期。原因：避免事後挑數字、單一好年撐起整體。
- 參數取高原區裡最常出現的值，不取孤立最佳值。原因：孤立最佳值是過度擬合。
- 每支策略是組合的一角：抓該賺的行情、小虧大賺，不獨立最大化 PF；最佳化先看大行情參與率（≥ 90%）再看 PF，虧損交給出場，不推更嚴的進場條件。原因：2026-08-01 S16_S 為了 PF 封殺七成死叉，七月大跌進場太晚。
- 持倉保護：趨勢策略用高觸發門檻＋寬容忍＋保本；反轉、突破策略不加中段 BE／SP；Top-10 佔淨利 > 70% 就不加 SP；源頭過濾優於中段保護。MFE 只能提假說，保護效果只能逐 bar 回測。原因：L4 v14.2、L5 v19.8 的 SP 變體全數淨損，100% 勝率的 SP 也是淨損。
- 蓋新機制前先量：X 現在發生幾次、那些是賺是賠、已經在發生的話為什麼還要蓋；新機制零觸發時先問它該不該存在。原因：L4 二次進場蓋了 983 行狀態機，原版其實早就會二次進場（`docs/policies/lesson_L28_measure_before_you_build.md`）。
- 比較兩份 MC12 報表前先跑 `python scripts/compare_mc12_reports.py A.xlsx B.xlsx`，exit 2＝不可比，一個數字都別讀。原因：設定表的「結束日期」是要求範圍，實際資料終點只看最後一筆平倉時間（2026-08-23 誤判 L1 不可重現）。
- 一次只解一題，MC 實測完再開下一題；同一題 5 版沒改善就停。原因：10/3 多題混著推進效率低；S16_S 連續改版沒有改善。
- 新策略、改版、研究題開工前先寫三行：成果（做完拿到哪個檔案或數字）、判定（用什麼判對錯，例如 MC12 跑完的筆數與 PF 範圍）、範圍（能動和不能動的檔案）。再寫一句「結果是 A 就做什麼、是 B 就做什麼」；兩種結果都做同一件事，就不跑。原因：Willy 2026-11-26 判定產出大多是過程；這三行取代舊的 9 點 intake。
- 終止一支策略或一條研究線時，在 PROJECT.md 決策紀錄追加一行（決定：終止 X｜原因：2–3 個關鍵數字、一句教訓、一句重啟條件｜放棄的選項：…），不另寫 FINAL_VERDICT.md。原因：Willy 2026-11-26 裁示；一行就能說清楚為什麼停，也能防止重做已經終止的策略。
- Python 對 MC 一律用 `txfcore/profiles/mc_compat.py`；移植多單策略（L3、L5、L1）前，先用 MC 報表驗證多單方向的進位與限價進場成本。原因：7 項成交差異只在 L2、L4（空單）逐筆實證過，多單方向尚未驗證（審查 M4）。
- 策略檔只組裝；規則寫在 `txfcore/modules/`，參數寫在 `config/strategies/*.toml`。原因：同一規則兩份實作會漂移（10/9 審查 H1：營運工具還在用舊移植版）。
- 換 1 分 K 資料要重新反推結算日曆。原因：日曆綁資料檔雜湊，不重推程式會擋。
- 上線基準在實盤機產生。原因：L1 A4 在另一台電腦三次回測都對不上 G4，原因未查明，可能是電腦環境不同。
- 給老闆看的圖：一張一個結論，不放術語與檔名，技術細節放附錄。原因：讀者是資產百億的投資人。
- 程式交付另附 .txt 閱讀版。原因：Willy 用 .txt 閱讀程式。
- 實盤單只用來發現問題，不直接決定規則。規則改動前，先用 Python 全歷史量化問題大小（最大浮盈／浮虧、實拿比例、回吐、逐年、依波動分段），再設計、再用全歷史與 9/24 之後的樣本外驗證，並以同帳戶組合的回撤判定。原因：11/3–11/9 從單筆推出的 L2 v5.12 五項與 L4 保本，L4 保本經全歷史驗證反而變差（淨利 −21～−34%、回撤變大）；舊做法已歸檔 `docs/archive/thinking/old_approach_trade_patching_20261109.md`。
- 一次派多個子 agent 前，先報時間與 token 並取得同意。原因：10/7 平行代理 token 用量過大，Willy 兩次要求停下。
</project_rules>
