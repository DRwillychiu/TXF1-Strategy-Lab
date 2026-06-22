# ARCHIVED — S3 RapidPullbackShort (off-roadmap diversion)

**歸檔日期**：2026-06-22
**歸檔原因**：
1. 此策略名為 "S3" 但**並非原始 roadmap 的 S3**。原始 S3 = `S3_VolSqueeze`（見 [../batch01_S2-S5/](../batch01_S2-S5/)）。
2. RapidPullbackShort 是 2026-06-19/20 桌機端 ultracode session 偏離原始排程自行衍生的設計。
3. v2.0.4 已通過 institutional eval，**生產 .pla 已部署到 [live_simulation/S3_RapidPullbackShort.pla](../../../live_simulation/S3_RapidPullbackShort.pla)**。
4. 此資料夾保留所有設計歷史供未來追溯。

---

## 對應檔案位置

| 用途 | 路徑 |
|------|------|
| **生產 .pla** | `strategies/live_simulation/S3_RapidPullbackShort.pla` |
| **生產 annotated** | `strategies/live_simulation/S3_RapidPullbackShort_annotated.md` |
| 設計歷史（本資料夾） | `strategies/research/archive/S03_RapidPullbackShort_archived_20260622/` |

---

## 為什麼歸檔（決策紀錄）

2026-06-22 用戶在新對話中發現：
> 「你所推的程式以及策略根本不是 archive 所規畫以及排程的策略」

→ 桌機端 6/19-6/21 工作（v2 redesign + S4-S9 KILL session）全部偏離 [`archive/README.md`](../README.md) 排程。
→ 為避免未來繼續偏離，原始 S3 (= VolSqueeze) 必須正式啟動。
→ RapidPullbackShort 因已成功部署到 live_simulation，**作為「歪打正著」的成品保留**，但 `S03_` 編號歸還給原始 VolSqueeze。

---

## 檔案清單

```
S3_PullbackShort_design_spec.md           ← v1 設計規格（Agent D 雛形）
S3_PullbackShort_design_spec_v2.md        ← v2 設計規格（6 agents workflow 產出）
S3_RapidPullbackShort.pla                 ← v1.x 舊版（v1.0 → v1.1 修 bug 後）
S3_RapidPullbackShort_annotated.md        ← v1.x 中文逐段註解
S3_RapidPullbackShort_strategy.md         ← v1.x 策略說明
S3_RapidPullbackShort_v2_strategy.md      ← v2 策略說明
S3_optimization_ranges_20260620.md        ← v1 最佳化範圍
S3_v2_optimization_ranges.md              ← v2 最佳化範圍
README.md                                 ← 原始 S03_PullbackShort 入口
```

---

## 相關文件交叉參考

- 機構級評估：[../../../docs/S3_v204_institutional_eval_20260620.md](../../../docs/S3_v204_institutional_eval_20260620.md)
- 重新設計 handoff：[../../../docs/handoff_20260619_s3_v2_redesign.md](../../../docs/handoff_20260619_s3_v2_redesign.md)
- 驗證腳本：`scripts/verify_s3_pullbackshort.py`、`scripts/verify_s3_v2.py`、`scripts/eval_s3_v204_institutional.py`

---

**真正的 S3 VolSqueeze 從 2026-06-22 起在 [../../S03_VolSqueeze/](../../S03_VolSqueeze/) 正式開發。**
