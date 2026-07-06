# Session Handoff: 2026-07-05 Cowork 進度同步 → 新對話接續

> **用途**：在新對話框開啟本檔即可接續進度。本檔由 18:00 git-progress-sync 自動判讀結果整理而成。
> **當前策略（Rule #14 單軌）**：S3_S（S03_VolSqueezeShort）— v1.9.6-ANTIHUNT 實驗中

---

## 1. Status（當前狀態）

- **CURRENT 策略**：`strategies/research/S03_VolSqueezeShort/`
- **Baseline**：v1.9.5-EXPERIMENTAL（`S3_VolSqueezeShort_v195_EXPERIMENTAL.pla`，969 LOC）
  - Backtest：68T / +513.4K / PF 1.574 / MDD -19.05% / WR 50%
  - Rule #18 Non-WFA 5 件套：3/5 pass（MC / Bootstrap PASS；MDD 邊界 FAIL 0.64%）
- **實驗版**：v1.9.6-ANTIHUNT（`S3_VolSqueezeShort_v196_ANTIHUNT.pla`，1107 LOC）
  - Spec：`v196_ANTIHUNT_spec_20260704.md`
  - 7 features 全 input 預設 OFF/0 = v1.9.5 baseline（除 BWRank guard 預設 ON）
  - Round 1 code 完成 + ASCII PASS（Rule #15）
- **其他線**：L5 審查已 CLOSED — v19.9 優化 REJECTED，保留 v19.8 production；L4 審查 CLOSED

## 2. Changed（今日 git 紀錄，2026-07-05 篩選窗共 7 commits）

```
23:15  docs(S3_S): handoff 2026-07-04 desktop to laptop
23:09  feat(S3_S): v1.9.6-ANTIHUNT Round 1 - 7 items anti-hunt + BWRank bug fix   (57d4b9f)
23:03  docs(S3_S): plan v1.9.6-ANTIHUNT + anti-hunt 5-layer design                (cc83988)
21:55  docs(S3_S): append 2026-07-04 Q&A on 8 parameter blocks                    (77c78c4)
20:37  L5: revert to v19.8 production — v19.9 optimization REJECTED               (396ed12)
20:27  docs: L5 review CLOSED — v19.8 production retained
00:11  docs: L4 review CLOSED, L5 BreakoutLong review IN PROGRESS
```

- **CHIP_RADAR_TW**：今日 1 筆人工 commit（`data: weekly LOOP audit refresh 2026-07-05`），KEEPALIVE 已排除。

## 3. State（v1.9.6-ANTIHUNT 7 Feature 對照表）

| # | Item | Section | Input | Default |
|---|------|---------|-------|---------|
| 1 | 夜盤 SL 加寬 22:00-05:00 | 7, 9 | `NightSL_Widen_On` | **False** |
| 2 | Confirmation SL 連 N 根 | 11 S-4 | `ConfirmSL_On` / `ConfirmSL_Bars=2` | **False** |
| 3 | BWRank equal-BW guard | 6 | `BWRank_EqualGuard_On` | **True**（bug fix） |
| 4 | Mid Exit Confirm Bars | 11 S-2 | `MidExit_ConfirmBars` | 1 |
| 5 | Mid Exit Peak Min ATR | 11 S-2 | `MidExit_PeakMinATR` | 0 |
| 6 | SP Peak Min Pts | 11 P0.5 | `SP_Peak_Min_Pts` | 0 |
| 7 | 夜盤 SP Volume 確認 | 11 P0.5 | `SP_Night_VolConfirm_On` | **False** |

**反掃單 5 層進度**：

| 層 | 機制 | 進度 |
|----|------|------|
| L1 | 夜盤 SL 加寬 22:00-05:00 × 1.3 | ✅ Round 1 落實 |
| L2 | Confirmation SL 連 2 根 1M K close > SL | ✅ Round 1 落實 |
| L3 | Hunt Detection Log（MAE 觸 SL 後 5min 回升） | ⏳ Round 2 |
| L4 | Fake Break Re-entry（反利用 hunt） | ⏳ Round 3 |
| L5 | 時段風險 Modifier（動態 SL） | ⏳ Round 3 |

## 4. Decisions（用戶 ruling 溯源，2026-07-04）

- Q1 BB Squeeze：BWStd=2.0 / BWLookback=120（6.3 天）→ **後續 ruling：改 5 或 3 天（Round 2 待實作）**
- Q4 Cooldown 移除（`Use_Cooldown=False`）
- 兩次壓縮 = **獨立事件**（Round 2 評估缺點後實作）
- Fire 用 1M K close（確認）
- 26/06 夜盤 stop hunting 觀察 → 落實 Anti-Hunt L1+L2（Round 1）
- L5：v19.9 REJECTED，v19.8 production 保留

## 5. Next（未解決問題 / 下一步，等用戶 ruling 選項）

**未解決問題（3 條重點）**：
1. v1.9.6-ANTIHUNT 4 組 Config 回測尚未執行（等 ruling 選 A/B/C）
2. Round 2 待辦：BWLookback 改 5/3 天敏感度、Hunt Gates 過擬合 sensitivity、BWRank 週期 + bug 驗證、獨立 episode 缺點測試
3. Anti-Hunt L3-L5 未落實（L3 → Round 2；L4/L5 → Round 3）

**下一步選項**：
- **選項 A（推薦）：立刻回測 v1.9.6**
  1. Config A（全關）→ sanity check = v1.9.5 baseline
  2. Config B（只開 BWRank guard）→ 測 bug fix 影響
  3. Config D（只開 L1+L2）→ 測 anti-hunt 純效果
  4. Config C（Round 1 全開）→ 完整版
- **選項 B：先跑 Round 2 Sensitivity**（BWLookback 57/95/120、Hunt Gates plateau、獨立 episode）
- **選項 C：直接 Round 3 進階實驗**（Fake Break Re-entry、時段風險 Modifier）

## 6. Files(關鍵檔案)

- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v196_ANTIHUNT.pla` — 實驗版
- `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v195_EXPERIMENTAL.pla` — baseline
- `strategies/research/S03_VolSqueezeShort/v196_ANTIHUNT_spec_20260704.md` — spec
- `strategies/research/S03_VolSqueezeShort/HANDOFF_20260704_to_laptop.md` — 前一份 handoff（含 4 組 Config 對照）
- `docs/policies/OFFICIAL_ROADMAP.md` — Rule #14 排程
- `docs/methodology/non_WFA_validation_SOP_20260630.md` — Rule #18

## 7. Git

- Repo：https://github.com/DRwillychiu/TXF1-Strategy-Lab.git
- 本地 = 雲端已同步（2026-07-04 桌機端確認）
- 最新 commit：`docs(S3_S): handoff 2026-07-04 desktop to laptop`
- 提醒：commit 前必跑 `python scripts/verify_pla_ascii.py --strict`（Rule #15）

---

## 新對話接續指令（複製貼上即可）

> 請讀取 `docs/handoffs/handoff_20260705_cowork_sync.md` 與 `strategies/research/S03_VolSqueezeShort/HANDOFF_20260704_to_laptop.md`，接續 S3_S v1.9.6-ANTIHUNT 進度。我選擇：選項 __（A / B / C）。
