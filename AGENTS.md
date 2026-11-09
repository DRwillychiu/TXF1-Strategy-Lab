# Codex 轉接檔（2026-10-19，從 Claude Code 搬過來）

本專案的正本守則是同資料夾的 **`CLAUDE.md`**。Codex 不會自動讀它，所以：

1. **開工第一件事：完整讀 `CLAUDE.md`**，並遵守其中所有規則；它和本檔衝突時，以 `CLAUDE.md` 為準（全域安全規則除外）。
2. `CLAUDE.md` 裡的 Claude 專用說法，在 Codex 這樣對應：
   - 「CLAUDE.md」＝本專案守則正本（改它之前先備份 `.bak_YYYYMMDD`，上限 300 行）
   - 「派 subagent」＝Codex subagent（負責人要求或守則要求時才派；同一任務只派一個）
   - 「auto-memory／跨對話記憶」＝`C:\Users\WILLY CHIU\AI_RULES\memory\`（索引 MEMORY.md）
   - 「~/.claude/playbooks」＝`C:\Users\WILLY CHIU\AI_RULES\playbooks\`
   - 「SendUserFile／交檔」＝寫成檔案並在回覆裡給路徑
   - 「TodoWrite」＝Codex 的計畫清單（plan）
3. 全域守則（回覆格式、安全、PowerShell 習慣）在 `~/.codex/AGENTS.md`。

## 本專案相關的記憶檔（`AI_RULES\memory\`，動工前讀相關的）
- feedback_official_roadmap_lock.md：策略開發嚴守 archive/ 原始 batch01-03 排程，不可發明新名稱、不可跳號
- feedback_mc_english_only.md：.pla 檔所有註解與字串必須全英文 ASCII
- feedback_planning_before_code.md：新策略先完成規劃文件，期間不動程式碼
- feedback_trend_let_profits_run.md、feedback_target_profile_small_win_big_win.md、feedback_sl_fine_dining_philosophy.md、feedback_nightsession_alpha_source.md：交易哲學與已關閉的方向
- feedback_mc_optimizer_hygiene.md、feedback_validation_precheck.md、feedback_verify_the_foundation.md：MC12 最佳化與驗證陷阱
- feedback_pattern_logic_diagram.md：每討論完一個型態的邏輯，必附對照圖
- feedback_settlement_holiday_rule.md：推算結算日必驗國定假日
- feedback_machine_name_policy.md：不要改 CLAUDE.md 的機器名標籤
- project_adaptive_farmer_framework.md、project_s3s_*.md、project_s16s_v1220_campaign_state.md：策略與戰役狀態
