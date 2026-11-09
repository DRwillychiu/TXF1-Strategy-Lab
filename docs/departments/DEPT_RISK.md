# 風控部

> 負責：停損、連虧與上限規則、結算日平倉、下單防呆｜**Tier 1，每個 Task 停下等 Willy 審查**

## 重點（詳細見團隊文件）
- **停損三件套**：`SetStopContract` → `SetStopLoss` → `SL_Pct` 上限；每支只能一組，放在進場區塊之前
- **結算日平倉**：Priority 0 出場順序 Kill > Registry > Holiday > Settlement > 原邏輯；進場 gate 必含 `v_Settlement_Day = false`
- **R1 策略層**：L1／L2 日虧 300 點、週虧 750 點；L3／L5 連虧 2 筆、L4 連虧 3 筆 → 跳過下一筆；停用線 L3 1,500 點（帳戶 10%）、L4 923、L5 1,384
  - 現況（2026-09-29 查核）：R1 目前不在任何上架程式裡（只在 `strategies/research/R1_loss_rules/`，舊 PROGRESS Task 3.3–3.8 未完成；10/5 版本後的現況見下方「連虧規則」）；L3 v18.x 已拿掉 R1（`Rule_On` 關）
  - 10/1 起停用線與連虧暫停都靠人工監看；寫進程式列第 4 季（舊 PROGRESS Task 9.11）
  - L3 停用線口徑（9/29 19:01 Willy 定案）：只算已平倉的虧損，1,500 點；v18.2 平倉後最大回撤 1,318 點。含未平倉 1,578 點（2026-08-20）只作參考
- **Kill Switch 實際語意（2026-10-31 更新）**：L2–L5 的 10/5 版本平倉**並擋新進場**；L1：V3.2 只平倉、**不擋新進場**；若實際跑的是 V3.8，則平倉並擋新進場（版本待確認）。都從未在 MC 實測。要停用策略，仍要關閉圖表自動交易，並到券商確認沒有委託和部位
- **連虧規則（10/5 版）**：L2 連虧 3 筆空頭單後跳過下一段（計數沒有起算日，實盤會延續圖上歷史的連虧）；L5 是單筆損失記憶（虧損 ≥ 450 點的單會被記住，從 2026/10/05 起算）；L4 連虧跳過預設關；L3 沒有；L1 V3.2 沒有，V3.8 有連虧 3 筆暫停（`Loss_Pause_N` 3）
- **R2 帳戶層**：延後到第 4 季第一週（Willy 9/29 08:59 選 B）；10/1 起每天收盤後人工核對券商與 MC 部位。設計：部位與券商不一致 → 停止下單；出場口數 ≤ 實際持倉；帳戶回撤 20% → TG 通知；每日心跳
- 程式防不住的風險（週末跳空、颱風停市、開盤跳空）與人工 SOP：見 `docs/ops/L3_v18.2_verification_20260929.md` 第五、六段
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
| L3 上線決定（停用線、Kill Switch 查核） | `docs/decisions/L3_deploy_v18_20260928.md` |
| L3 空跑與 9/30 閘門表 | `docs/ops/L3_dryrun_0929_gate_0930.md` |
| L3 v18.2 上線前驗證 | `docs/ops/L3_v18.2_verification_20260929.md` |
