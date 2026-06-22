# ARCHIVED — S2 InsideBarBreak (on-roadmap, KILLED in development)

**歸檔日期**：2026-06-22
**歸檔原因**：S2 InsideBarBreak **是原始 batch01 排程**（見 [../README.md](../README.md)），但開發到 v0.6 後因 alpha 衰退被 KILL。

---

## 為什麼 KILL

詳見 `S2_FINAL_VERDICT.md`。簡而言之：
- 6/15 教科書 alpha 在 TXF1 2020-2026 已衰減（樣本不足、PF < 1.0）
- v0.3 → v0.6 多次嘗試：增加 filter / 改 long-only / MaxDailyEntries 等均無法救回
- 最終 verdict：**alpha 已不存在於 TXF1**，停止迭代

---

## 與原始 archive/batch01_S2-S5/S2_InsideBarBreak.pla 的關係

- 原始 batch01 是 2026-06-07 之前的概念雛形（73 行）
- 本資料夾是 2026-06-13 之後的正式開發（v0.3 → v0.6 多版迭代）
- 同一個策略名稱、同一個概念，**這是開發成果死亡的歸檔**，不是「偏離排程」

---

## 是否影響 S3 開發？

不影響。S3 VolSqueeze 是獨立的 C 類波動率策略，與 S2 結構不同。

---

## 檔案內容

```
S2_InsideBarBreak.pla              — v0.6 最終版（KILLED）
S2_InsideBarBreak_annotated.md
S2_InsideBarBreak_strategy.md
S2_v03_design_spec.md
S2_v04_design_spec.md
S2_v05_naive_longonly_analysis.md
S2_FINAL_VERDICT.md                 — KILL 決策完整紀錄
STATUS_SUSPENDED.md                  — 中間 suspended 狀態
S2_E_series_alpha_decay_analysis.md
S2_backtest_journal.md
S2_handoff_to_laptop_20260617.md
S2_known_issues.md                   — 13+ issues 完整追蹤
S2_phase2_initial_findings_20260617.md
S2_phase2_naive_fixed_analysis.md
S2_phase2_validation_framework.md
S2_why_long_bias_works.md
backtests/                           — MC12 回測 xlsx 結果
_analyze_scripts/                    — verify_s2_v06.py 驗證腳本
```
