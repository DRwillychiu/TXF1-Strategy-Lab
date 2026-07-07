# Handoff 2026-07-07 — S3_S 進場閘門審計完成（Laptop → Home）

## 1. Status

- S3_S v1.9.6-OPT-PROD（`strategies/live_simulation/S3_S_VolSqueezeShort.pla`，1,124 行）進場條件審計**完成**。
- 總體判定：**無立即性進場永久失效 bug**；1 個 BLOCKER（有日期）+ 4 個 MODERATE。
- 完整報告：`docs/research/S3_S_v196_entry_gate_audit_20260707.md`（15 項 findings，附行號）。
- 本 session **未修改任何策略程式碼**——純診斷。

## 2. Changed

- 新增 `docs/research/S3_S_v196_entry_gate_audit_20260707.md`（審計報告）
- 新增本 handoff
- 無 .pla 改動

## 3. State

- S3_S 已於 2026-07-06 PROMOTE 至 live_simulation（commit `e81c26b`，Config B + 5-param OPT）。
- OPT 基準：70T / +770.8K / PF 1.823 / MDD -16.02%。
- WFA 標注 structural exemption（用戶 ruling Path A），驗證主軸 = MC + Bootstrap + Stress Testing。
- 執行環境：Google Cloud VM MC12。

## 4. Decisions

- 審計為純診斷，所有修改延至維護窗口，不動剛 promote 的 PROD 檔（避免破壞 5 件套驗證的基準組態）。
- .bak 備份檔維持不入 git（git 歷史即備份）。

## 5. Next（優先序）

1. **F1 BLOCKER**：`Registry_Valid_Until(1270101)` 2027-01-01 到期 → 進場全滅。Q4 2026 用 TAIFEX 116 年曆重建 registry，建議列入 `optimization/TRACKER.md`。
2. **F14**：核對 `Thrust_Margin_ATR = 0.15`（:224）vs 檔頭註解 0.25——是 GA 定案還是誤植？對照 2026-07-06 回測參數表。**未驗證，需人工確認。**
3. **F12 + F8**（下次維護窗口一併修）：Kill Switch 加入進場閘門；結算日規則的假日順延錯位。
4. 續行 7/6 既定驗證路線：Monte Carlo + Bootstrap 用 OPT 參數重跑 → T68 V-turn → promote 檢核。
5. 營運設定：MC12 圖表資料範圍下限 ≥ 60 個交易日（F4，BW 緩衝 120 根 60M + Regime 41 根日線）。

## 6. Files

- `strategies/live_simulation/S3_S_VolSqueezeShort.pla` — 審計對象（未改動）
- `docs/research/S3_S_v196_entry_gate_audit_20260707.md` — 完整審計報告（15 findings + 除錯順序）
- `docs/handoffs/handoff_20260707_s3s_entry_gate_audit.md` — 本檔

## 7. Git

- 起點：`c24ceba`（docs(S16): split S16 into S16_S + S16_L...）
- 本次 commit：docs only（審計報告 + handoff），詳見 `git log`
- 未追蹤殘留：各 `.bak_*` 備份檔（刻意不入庫）
