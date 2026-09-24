# 風控部

> 負責：停損、連虧與上限規則、結算日平倉、下單防呆｜**Tier 1，每個 Task 停下等 Willy 審查**

## 重點（詳細見團隊文件）
- **停損三件套**：`SetStopContract` → `SetStopLoss` → `SL_Pct` 上限；每支只能一組，放在進場區塊之前
- **結算日平倉**：Priority 0 出場順序 Kill > Registry > Holiday > Settlement > 原邏輯；進場 gate 必含 `v_Settlement_Day = false`
- **R1 策略層**：L1／L2 日虧 300 點、週虧 750 點；L3／L5 連虧 2 筆、L4 連虧 3 筆 → 跳過下一筆；停用線 L3 1,500 點（帳戶 10%）、L4 923、L5 1,384
- **R2 帳戶層**（開發中）：部位與券商不一致 → 停止下單；出場口數 ≤ 實際持倉；帳戶回撤 20% → TG 通知；每日心跳
- **極端行情**：多層停損 SOP，ATR 停損是最後防線；禁止固定點數 cap
- 單筆風險上限：帳戶 1%–3%

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| R1 規則 | `docs/specs/spec_R1_loss_rules.md` |
| R2 帳戶防呆 | `docs/specs/spec_R2_account_guard.md`（待寫） |
| 停損三件套 | `docs/policies/P3b_immediate_stop_guard_design_20260618.md` |
| 結算日 | `docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md` |
| 極端行情 | `docs/methodology/extreme_sl_multilayer_sop_20260629.md` |
| 機構級 10 維度 | `docs/policies/institutional_risk_framework_20260619.md` |
