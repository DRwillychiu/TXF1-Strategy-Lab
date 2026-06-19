# S2 InsideBarBreak — Research Suspended

**狀態變更日**：2026-06-20
**狀態**：⏸️ **RESEARCH SUSPENDED**（暫緩，**不是 archive**）
**用戶決策**：2026-06-20 ultracode session
**最後版本**：v0.6（仍在原處未修改）

---

## 一、為什麼暫緩

### 三個關鍵原因

#### 1. Portfolio 戰略轉折
- 2026-06-20 用戶宣告：「**L1-L5 + S1 凍結 + 焦點轉向新策略開發**」
- 同邏輯延伸：S2 v0.6 是「**實驗中的策略**」，已投入 5 版迭代
- 與其繼續優化 marginal alpha，不如開發 portfolio 缺口策略

#### 2. Alpha 已實證 marginal
- v0.6 Naive Long-only PF **1.057**
- 6 年累積 +48K（**年化 0.85%**）
- 對比 Buy and Hold 落後 **56×**
- E-series 論證已確認：**alpha 大幅衰減**

#### 3. S3 PullbackShort 是更高優先
- 5 個 deep-discovery agents 一致推薦 S3 為 Q1 #1
- 直接填補用戶 2026-06-19 發現的 portfolio gap
- 預估 portfolio Sharpe 1.329 → ~1.75（單一策略貢獻最大）

---

## 二、為什麼選「暫緩」而非「Archive」

| 維度 | 暫緩（本選擇）| Archive |
|------|----------|---------|
| 檔案位置 | 保留原處 | 移到 archive/ |
| 心理意義 | **「未來可能回來」** | **「正式終結」** |
| 開發紀錄 | 完整可見 | 需要 dig archive |
| 重啟成本 | 極低（git status 看得到）| 中等（需要 mv 回來）|

**用戶語意**：「進度先**暫緩**」 = 不是 reject，是 pause。

---

## 三、S2 完整工作成果（**保留供未來參考**）

### 已完成的工作（**沒有浪費**）

| 階段 | 產出 | 狀態 |
|------|------|------|
| Phase 1 | 從 archive 拉出 + 模組化（Settlement / Holiday / Kill / Registry）| ✅ |
| v0.3 | B+C 系列（假突破過濾 + 4 層 SL 保護）| ✅ |
| v0.4 | A 系列（波動率壓縮量化）| ✅ |
| v0.5 | Long-only + TargetMult 1.0 | ✅ |
| v0.6 | B 系列元兇修正（VolFilter / ConfirmBars）+ MaxDailyEntries | ✅ |
| Phase 2 | MC 真實回測 4 配置 | ✅ 部分（Naive + v0.2 復刻已跑）|
| Issue tracker | 30 題 / 18 解 / 12 未解 | 詳見 S2_known_issues.md |

### 完整文件清單

```
strategies/research/S02_InsideBarBreak/
├── STATUS_SUSPENDED.md ★ 本檔
├── S2_InsideBarBreak.pla              (v0.6, 705 行)
├── S2_InsideBarBreak_strategy.md      (完整策略說明)
├── S2_InsideBarBreak_annotated.md     (中文逐段註解)
├── S2_known_issues.md                  (29→30 題 / 18 解 / 12 待)
├── S2_v03_design_spec.md              (B+C 設計)
├── S2_v04_design_spec.md              (A 設計)
├── S2_E_series_alpha_decay_analysis.md (E 論證)
├── S2_phase2_validation_framework.md  (Phase 2 框架)
├── S2_backtest_journal.md             (工作底稿 — 盲點承認)
├── S2_phase2_initial_findings_20260617.md  (8 個發現)
├── S2_phase2_naive_fixed_analysis.md  (Naive 5.6 年分析)
├── S2_why_long_bias_works.md          (Long-only 論證)
├── S2_v05_naive_longonly_analysis.md  (v0.5 部分驗證)
├── S2_handoff_to_laptop_20260617.md   (歷史 handoff)
└── backtests/
    ├── README.md
    ├── MC12_backtest_SOP.md
    └── (待放 xlsx)
```

---

## 四、何時可能重啟

### 條件 1：S3-S7 7 個新策略完成後（**Q4 2026 之後**）
- 若 12 月 roadmap 7 個 candidate 全部部署
- 還有開發資源 → 可回頭做 S2 v0.7（更深 alpha 挖掘）

### 條件 2：新發現顛覆設計
- 若機構級新研究顯示母子線在 TXF1 上仍有殘餘 alpha
- 或新的 filter / regime detection 技術出現

### 條件 3：用戶明確要求
- 任何時候用戶決定回來繼續

---

## 五、所學教訓已永久保留

13 個從 S2 失敗演化中學到的教訓（已寫入 memory）：

1. Python 日線代理 PF 不可信
2. 設計超前實證 = 紙上談兵
3. MC Time 24-hour 必須閉區間
4. **突破類策略 → Long-only 是常態**
5. **教科書公開策略 alpha 已大幅衰減**
6. MC12 input persistence 必須完全移除重載
7. MTF 設計前先驗證持倉天數
8. TP 倍率必從 MFE 統計推導
9. 過濾類 input 必須驗證歷史通過率
10. 同日多進場需 cooldown
11. **Buy and Hold 是現實檢驗**
12. 4 次設計迭代 + 0 實證 = 警訊
13. **新 filter 必須做重疊度 + 通過率雙重檢查**

**這 13 個教訓比 S2 本身更有價值**，永久指導未來所有新策略開發。

---

## 六、不再投入時間的承諾

未來 Claude / 用戶：

```
若你看到這份 STATUS_SUSPENDED.md：
  ❌ 不要修改 S2 任何代碼
  ❌ 不要跑 S2 回測
  ❌ 不要寫 S2 新版本
  ✅ 可以讀文件參考設計思路
  ✅ 可以引用 13 個教訓
  ✅ 只有用戶明確要求重啟才可動 S2
```

---

## 七、相關 / 替代方向

- **S3 PullbackShort**（取代了 S2 在 Q1 pipeline 的位置）：[../S03_PullbackShort/](../S03_PullbackShort/)
- **12 月 roadmap**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **Portfolio v2**：[../../../docs/portfolio_allocation_v2_20260620.md](../../../docs/portfolio_allocation_v2_20260620.md)
