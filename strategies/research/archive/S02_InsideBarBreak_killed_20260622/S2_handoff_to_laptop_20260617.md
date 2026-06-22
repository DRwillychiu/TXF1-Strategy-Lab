# S2 筆電端接手 Handoff Prompt (2026-06-17 → 2026-06-18)

**生效日**：2026-06-17 結束
**接收方**：明日筆電端 Claude
**前置**：請在筆電上 git pull origin main 取得最新狀態
**git 最後 commit**：[`96196c8`](https://github.com/DRwillychiu/TXF1-Strategy-Lab/commit/96196c8)

---

## 一、今日完成的主要工作（21 個 commit）

### 大主題 A：Settlement_Flat 結算日防護體系（成功）
1. Settlement_Flat 模組部署 L1-L5+S1 (`ee8e14c`)
2. 132/132 月偵測證明 (`6df6b36`)
3. 完整流程圖 SVG (`bf530a4`)
4. 設計憲法 v1.0 (`f9e627b`)
5. 部署後 6 策略實證分析 — L1 67.3% PnL 來自 Settlement (`7841697`)
6. 憲法 v1.1：三象限分類強制 (`2628172`)

### 大主題 B：L3/L4 RangeForceExit 失敗 + 回滾（教訓）
7. L3 v13.3 / L4 v14.3 加 RangeForceExit (`3e27f46`)
8. Hotfix v13.3.1 / v14.3.1 — 夜盤誤觸 bug (`fad1005`)
9. 完全 ROLLBACK v13.4 / v14.4 (`61233bc`) — 用戶決定
10. 憲法降為 v1.2 — 條款 7/8 撤回

### 大主題 C：S2 InsideBarBreak 全程設計到實證（部分完成）
11. S2 Phase 1 reactivation (`498db0a`)
12. S2 strategy.md (`096bc34`)
13. S2 issue tracker 29 題 (`cddc23f`)
14. S2 v0.3 B+C 系列 (`a05f2a2`)
15. S2 v0.4 A 系列 (`c7304f3`)
16. S2 E 系列論證 + Phase 2 框架 (`99e3303`)
17. S2 backtest journal — 承認設計超前實證 (`1c91e05`)
18. S2 MC12 操作 SOP (`5a54ba5`)
19. S2 Phase 2 初步發現 — 8 個問題 (`aa49ca1`)
20. S2 Phase 2 Naive 修正版分析 — alpha 已死 (`19e5ed1`)
21. S2 v0.5 Long_Only_Mode + TargetMult 1.0 (`9601202`)
22. S2 v0.5 部分驗證 — Long-only 有效但 TP 沒改 (`96196c8`)

---

## 二、S2 InsideBarBreak 當前狀態

### 程式碼版本：v0.5
**位置**：[`strategies/research/S02_InsideBarBreak/S2_InsideBarBreak.pla`](../S2_InsideBarBreak.pla)
**行數**：705 行
**Inputs**：33 個（v0.4 32 + Long_Only_Mode）
**Variables**：50 個

### 預設配置（v0.5）
- `Long_Only_Mode(true)` ★ 新增（H 系列解決）
- `TargetMult(1.0)` ★ 從 1.5 改為 1.0（基於 MC TP 觸及率 19%）
- 所有 A+B+C 系列 _On = true（v0.4 預設保留）

### Issue tracker：29 題 / 16 解 / 13 未解
- ✅ B-1~4 (v0.3 B 系列)
- ✅ C-1~4 (v0.3 C 系列)
- ✅ A-1~3 (v0.4 A 系列)
- ✅ E-1~3 (E 系列論證)
- ✅ H-1~2 (v0.5 H 系列 Long-only)
- ❌ D-1~5 (MC 真實回測 — Phase 2 待完成)
- ❌ F-1~3 (與 L5 相關性)
- ❌ G-1~3 (MTF 設計)
- ❌ I-1~3 (MFE/MAE)

### 實證資料（已跑的回測）
1. v0.1 Python 代理（不可信）：PF 4.61
2. Naive 修正版（5.6 年）：**PF 0.92 整體虧錢**
3. Naive Long-only（5.6 年）：**PF 1.057 / 年化 0.85%**

### 對照：Buy and Hold
- S2 Long-only 6 年：+48K（年化 0.85%）
- 台股 Buy and Hold 6 年：+2.8M（年化 27.18%）
- **落後 56 倍**

---

## 三、用戶今日最後的決策方向

用戶選擇了路徑 B（Long-only + 調 TP），跑了 v0.5 但發現 **TargetMult 沒改成 1.0**（MC12 input persistence trap）。

### 我給用戶的最後建議是路徑 C（archive）

理由：
- Naive Long-only PF 1.057 即使優化到 2.0
- 年化最多 5-8%
- 仍輸 Buy and Hold 3-5 倍
- 知識價值（12 條教訓）已經獲得

### 但用戶尚未明確選擇

用戶說：「**先幫我完整更新 git，然後我明天會直接在筆電端繼續執行今天沒有完成的進度**」

→ 明天用戶會決定走 A、B、C。

---

## 四、明日筆電端 3 條可能路徑

### 路徑 A：重跑 v0.5 真實預設（TargetMult = 1.0）

**動作**：
1. 用戶 MC12 上**完全移除** S2 策略（避免 input persistence）
2. 從 [`S2_InsideBarBreak.pla`](../S2_InsideBarBreak.pla) 重新載入
3. **確認** Inputs 看到 `TargetMult = 1.0`
4. 跑 1 次回測 → 匯出 `S2_v05_LongOnly_TP10_20260618.xlsx`

**你（筆電 Claude）做的事**：
- 等用戶 xlsx 回來
- 分析 TP=1.0 是否真的提升 PF
- 對比 Naive Long-only (TP 1.5) vs v0.5 (TP 1.0)
- 寫對比報告

**預期**：PF 1.2-1.4 範圍

### 路徑 B：A+B+C 完整版（找 B-2/B-3 元兇 + 完整測試）

**動作**：
1. 用戶跑 2 個診斷回測：
   - `S2_B2_only_20260618.xlsx` (Confirm_On=true, 其他 B/C 仍 false)
   - `S2_B3_only_20260618.xlsx` (VolFilter_On=true, 其他 B/C 仍 false)
2. 你找出元兇（極可能是 VolFilter）
3. 修 .pla 預設值（v0.6）
4. 用戶跑 v0.6 完整版回測

**你做的事**：
- 寫 v0.6 設計（基於診斷結果調整元兇 input 預設）
- 修 .pla
- 分析 v0.6 完整版績效

**預期**：PF 1.3-1.8 範圍

### 路徑 C：誠實 Archive S2

**動作**：
1. 移 S2 到 `strategies/research/archive/S02_attempted_20260617/`
2. 寫完整 archive 報告含 12 條教訓
3. 把 12 條教訓寫入專案知識庫
4. 轉戰其他研究（評估 S6-S15 或新策略）

**你做的事**：
- 寫 `S2_archive_report.md`
- 寫 `LESSONS_LEARNED_from_S02.md` 入 docs/
- 評估下一個研究目標（建議避開「教科書策略」）

---

## 五、重要警告（請筆電 Claude 務必記住）

### 警告 1：MC12 Input Persistence Trap

```
.pla 改了預設值後，MC12 上既有的策略 inputs 仍是舊值
解決：「完全移除策略 → 重新從 .pla 載入」
否則新預設值不生效
```

**v0.5 部分失敗就是這原因**：TargetMult 1.5 沒改成 1.0。

### 警告 2：MC Time 24-hour 制陷阱

```
Time >= X 在夜盤 15:00-23:59 都為 true
必須加 Time <= Y 上界 OR 用 v_Settlement_Day / v_Holiday_Block AND
否則夜盤誤觸發 (RangeForceExit 失敗教訓)
```

### 警告 3：設計超前實證的危險

```
v0.1 → v0.4 連續 4 次設計都沒 MC 驗證
今天才知道整個方向有誤
未來：每次 input 預設變動 → 立刻 MC baseline 對比
```

### 警告 4：突破類策略應該 Long-only

```
台股結構性偏多 + Inside Bar 在多頭結構更穩 + 散戶心理
→ 突破類默認 Long-only，雙向是例外
這條規則寫入 [S2_why_long_bias_works.md]
```

---

## 六、需要明天做的具體事項

### 必做 1：確認用戶選擇 A / B / C

問用戶：「**MC12 上是否已完全移除 S2 並重新從 v0.5 .pla 載入？**」

- 若「**已重載**」→ 路徑 A 進行中，等回測結果
- 若「**還沒重載**」→ 確認用戶要走哪條路

### 必做 2：根據用戶選擇執行

依照路徑 A / B / C 的具體動作執行（見第四節）。

### 必做 3：完整更新 git

用戶今日多次強調「**完整更新 git 必含 push**」（feedback_git_full_push.md 記憶）。
每次有變動立刻 commit + push。

### 必做 4：避免再次「設計超前實證」

若用戶想做新的 v0.6/v0.7 改進：
- 先要求 MC baseline 跑出來
- 不要直接設計新版本

---

## 七、檔案完整清單（S2 資料夾）

```
strategies/research/S02_InsideBarBreak/
├── README.md
├── S2_InsideBarBreak.pla              ← v0.5 705 行
├── S2_InsideBarBreak_strategy.md      ← 完整策略說明
├── S2_InsideBarBreak_annotated.md     ← 中文逐段註解
├── S2_known_issues.md                  ← 29 題 / 16 解
├── S2_v03_design_spec.md              ← B+C 設計
├── S2_v04_design_spec.md              ← A 設計
├── S2_E_series_alpha_decay_analysis.md ← E 論證
├── S2_phase2_validation_framework.md  ← Phase 2 框架
├── S2_backtest_journal.md             ← 工作底稿（盲點承認）
├── S2_phase2_initial_findings_20260617.md  ← 8 個發現
├── S2_phase2_naive_fixed_analysis.md  ← Naive 5.6 年分析
├── S2_why_long_bias_works.md          ← 為何 Long-only
├── S2_v05_naive_longonly_analysis.md  ← v0.5 部分驗證
├── S2_handoff_to_laptop_20260617.md   ← 本檔
└── backtests/
    ├── README.md                       ← 4 版本 input 配置
    ├── MC12_backtest_SOP.md           ← MC12 操作 SOP
    └── (待放 xlsx 檔)
```

---

## 八、git 環境

```
Repo: https://github.com/DRwillychiu/TXF1-Strategy-Lab
Branch: main
最後 commit: 96196c8 (Today's last)
Working tree: clean
Origin/main: up to date (本地 push 已成功)

筆電端首次操作:
  git pull origin main
  → 應該獲得所有今日 21 個 commit
```

---

## 九、明天 Claude 接手檢查清單

```
[ ] git pull origin main 拿到所有今日更新
[ ] 讀 strategies/research/S02_InsideBarBreak/S2_handoff_to_laptop_20260617.md (本檔)
[ ] 讀 strategies/research/S02_InsideBarBreak/S2_known_issues.md 知道剩 13 題
[ ] 讀 strategies/research/S02_InsideBarBreak/S2_v05_naive_longonly_analysis.md 知道最新結果
[ ] 問用戶選 A / B / C
[ ] 根據選擇執行對應動作
[ ] 每次變更後 git commit + push
[ ] 持續記錄到 backtest_journal.md
```

---

## 十、給筆電 Claude 的特別提示

### 用戶的核心鐵律（從記憶）
1. **完整更新 git 必含 push** — 不可只本地 commit
2. **對話語言：繁體中文** — code/identifiers 保持英文
3. **不問休息問題** — 用戶自管節奏
4. **MC Time 24 小時制陷阱** — 跨日商品時段條件必須閉區間
5. **趨勢策略讓利潤奔跑** — 勿建議獲利回檔保護
6. **假日前平倉鐵律** — TXF1 策略休市前必平倉
7. **MC 進出場標籤規範** — LE_/LX_/SE_/SX_ 前綴

### 用戶風格
- 直接、不囉嗦
- 反應快、會立刻指出邏輯漏洞
- 寧可 archive 也要誠實面對 alpha 不存在
- 不會強求設計成功

### 我（今日 Claude）的最後建議
**若用戶猶豫不決，建議推薦路徑 C** — 因為從數據看 S2 已死，繼續優化只是延後告別。但 30 分鐘的路徑 A 是可以接受的「最後嘗試」。

---

## 十一、預估明日完成時程

| 路徑 | 預估完成時間 | 預期產出 |
|------|-------------|--------|
| A | 1-2 小時 | v0.5 TP=1.0 真實 PF 數據 + 對比分析 |
| B | 3-4 小時 | v0.6 完整版 + 元兇診斷 + 完整 Phase 2 報告 |
| C | 30 分鐘 - 1 小時 | S2 archive 報告 + 12 教訓入庫 + 下一個研究目標評估 |

---

**祝筆電端 Claude 接手順利。所有 context 都在 git 中。**
