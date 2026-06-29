# Engineering System — 五支柱工程規範

**建立**：2026-06-29
**適用**：所有 TXF1 策略開發、修改、部署
**強制等級**：Rule #16（CLAUDE.md 強制引用）

> 每一次設計決策、程式碼修改、版本推進，必須通過五支柱檢查。
> 缺任何一支柱 = 不可 commit。

---

## 總覽

```
┌─────────────────────────────────────────────────┐
│              ENGINEERING SYSTEM                  │
│                                                  │
│   Rules ──→ Context ──→ Verification             │
│     │                        │                   │
│     └──── Memory ◄───────────┘                   │
│              │                                   │
│           Format                                 │
└─────────────────────────────────────────────────┘
```

| 支柱 | 核心問題 | 失敗代價 |
|------|---------|---------|
| **Rules** | 這個改動違反哪條硬約束？ | v1.7.2 刪 Bear alpha（違反 L24） |
| **Context** | 我讀完所有相關資料了嗎？ | cap 100 不知 SP arm 距離 → 截斷 SP |
| **Verification** | 怎麼證明改動有效且不傷其他？ | v1.7.3 WFA 2/9 FAIL（sample 太少） |
| **Memory** | 過去犯過類似的錯嗎？ | 重複犯 "保護機制截斷 alpha" |
| **Format** | 交接後下一端能無損接手嗎？ | 筆電/桌機交接遺漏 → 重工 |

---

## 一、Rules（規則）— 不可違反的硬約束

### 1.1 通用規則（已編碼）

| 類別 | 規則 | 來源 |
|------|------|------|
| 結算日 | 7 元素 Settlement_Flat 模組 | Rule #11 |
| 停損 | SetStopLoss 進場前必呼叫 | Rule #12 |
| 評估 | 10 維度 institutional eval | Rule #13 |
| 排程 | OFFICIAL_ROADMAP 嚴守順序 | Rule #14 |
| 編碼 | .pla 100% ASCII | Rule #15 |
| 安全 | 5 個 P0 參數永不優化 | CLAUDE.md §P0 |

### 1.2 停損專屬規則（v1.7.4 實證後新增）

| 編號 | 規則 | 證據 |
|------|------|------|
| **R-SL1** | 單筆 risk ≤ 帳戶 2%（100 pts at 1M） | 業界 2% Rule (CME) |
| **R-SL2** | Hard Cap ≥ SP arm 距離，否則 SP 失效 | v1.7.4 cap 100: 8 筆 SP→SL, -432K |
| **R-SL3** | SL 結構改動後 SP/TP 筆數偏移 ≤ 20% | cap 100 SP 從 21→13 = -38% 違反 |
| **R-SL4** | 任何 SL 改動必標明影響哪一層（5 層架構） | SL catalog Layer 1-5 |

### 1.3 設計決策規則

| 編號 | 規則 | 證據 |
|------|------|------|
| **R-D1** | 進場品質過濾 > 持倉中段保護 | L4 Path A +106K 完勝 BE/SP |
| **R-D2** | 保護機制不可截斷 alpha source | L24: Trail_B -385K |
| **R-D3** | 策略尾巴集中度 > 70% = SP 禁區 | L5 Top-10 88% |
| **R-D4** | Regime filter 不可造成 sample < 100 trades | v1.7.3 WFA FAIL (76 trades) |

### 使用方式
設計 spec 文件必須包含「**Rules Checklist**」區段：
```
## Rules Checklist
- [ ] R-SL1: 單筆 risk 計算 = ___K = ___%
- [ ] R-SL2: Hard Cap ___ pts vs SP arm ___ pts (Cap ≥ SP arm? Y/N)
- [ ] R-SL3: SP/TP 筆數預估偏移 ≤ 20%?
- [ ] R-D2: 此改動是否截斷已知 alpha source?
- [ ] Rule #11-#15: 通用規則全部遵守?
```

---

## 二、Context（上下文）— 動手前必讀的資訊

### 2.1 必讀清單（每次設計前）

| 優先 | 資料 | 目的 |
|------|------|------|
| **P0** | 當前 live_simulation 生產版 .pla | 知道改什麼 |
| **P0** | 對應 strategy.md + BOSS_VIEW | 理解策略本質 |
| **P1** | 相關 Lesson 文件（L24-L28） | 避免重蹈覆轍 |
| **P1** | 上一版 KILL/FAIL verdict | 知道為什麼失敗 |
| **P2** | 跨策略影響（同類策略有幾隻？） | L2/L4/S3 同為 short |
| **P2** | ATR 分布 / vol 分區數據 | 參數選擇依據 |
| **P3** | 業界 reference（SL catalog 等） | best practice 對照 |

### 2.2 Context Loading 格式
設計 spec 文件必須包含「**Context Loaded**」區段：
```
## Context Loaded
- Production: v1.7.3-FINAL in live_simulation/ (29 trades, PF 3.95)
- Last FAIL: v1.7.3 WFA 2/9 (sample loss from regime filter)
- Lessons: L24 (alpha preservation), L26 candidate (cap ≥ SP arm)
- Cross-strategy: L2/L4/S3 same SL architecture, pending rollout
- Data: ATR(14) 60M median ~60 pts, vol expansion ~193 pts
```

### 2.3 Context 不足 = 不可動手
如果以下任一項缺失，停下來先補齊：
- 不知道當前生產版是什麼 → `git pull` + 讀 TRACKER
- 不知道上次為什麼 FAIL → 讀 verdict 文件
- 不知道改動影響幾隻策略 → 盤點跨策略影響

---

## 三、Verification（驗證）— 怎麼證明改動有效

### 3.1 五級驗證協議

| 級別 | 名稱 | 內容 | 門檻 |
|------|------|------|------|
| **V1** | Control Group | 改動 vs 原版完整對照 | 必有 baseline |
| **V2** | Exit Distribution | SP/SL/TP 筆數 + 平均 PnL | SP 偏移 ≤ 20% |
| **V3** | Year Stability | 每年 PnL 不可任一年崩潰 > 50% | 無單年 -80% |
| **V4** | WFA 9-window | Walk-Forward 4+ gates | ≥ 4/9 PASS |
| **V5** | 10-dim Eval | Rule #13 institutional | 全 PASS |

### 3.2 必做 vs 選做

| 場景 | 必做 | 選做 |
|------|------|------|
| 參數微調（同結構） | V1 + V2 | V3 |
| 結構改動（新 input / 新邏輯） | V1 + V2 + V3 + V4 | V5 |
| Promote 到 live_simulation | V1-V5 全部 | — |
| Promote 到 live | V1-V5 + MC9 空手部署 | — |

### 3.3 Verification 紅旗（立即停止）

| 紅旗 | 代表什麼 | 動作 |
|------|---------|------|
| SP 筆數下降 > 20% | 改動截斷 alpha | 立即 KILL |
| 單年 PnL 下降 > 80% | 改動破壞特定市況 | 調查 root cause |
| WFA < 4/9 PASS | 過擬合或 sample 不足 | KILL 或退版 |
| SL trades 暴增 > 3 倍 | 參數過緊 | 放寬或重新設計 |

---

## 四、Memory（錯誤記憶）— 不可重蹈的覆轍

### 4.1 已確認的反模式（Anti-patterns）

| 編號 | 反模式 | 實證案例 | 如何避免 |
|------|--------|---------|---------|
| **AP-1** | 保護機制截斷 alpha | L1 Trail_B -385K; v1.7.4 cap100 -432K | R-D2 checklist |
| **AP-2** | Filter 造成 sample collapse | v1.7.3 WFA FAIL 76 trades | R-D4: sample ≥ 100 |
| **AP-3** | Lower-bound 誤殺好區間 | v1.7.2 MinRatio 殺 Bear PF 11.0 | 改用 band-reject |
| **AP-4** | 100% 勝率機制 = 淨損 | L4 BE/SP -345K~-82K | 先算截斷 alpha |
| **AP-5** | 盤整策略套用趨勢保護 | L3 BE 100筆 0勝率; L5 SP 全敗 | 策略分類先行 |
| **AP-6** | Cap < SP arm 距離 | v1.7.4 cap100: SP 還沒 arm 就觸 SL | R-SL2 |

### 4.2 已確認的正模式（Proven Patterns）

| 編號 | 正模式 | 實證 |
|------|--------|------|
| **PP-1** | Frozen ATR 初始停損 | 全 9 隻策略標配 |
| **PP-2** | 進場品質過濾 > 持倉保護 | L4 Night Block +106K |
| **PP-3** | Band-reject（保留好區間，擋壞區間） | v1.7.3 Bear PF 11.0 保留 |
| **PP-4** | 5 層 SL 架構（多層協同） | 業界共識 + SL catalog |
| **PP-5** | W4 WFA 作為最終 gate-keeper | v1.7.3 2/9 正確 KILL |

### 4.3 Lesson 索引

| Lesson | 內容 | 文件位置 |
|--------|------|---------|
| L1-L23 | off-roadmap KILL 經驗 | `docs/archive/offRoadmap_2026Q2/` |
| **L24** | Risk overlay 不可削 alpha source | `docs/policies/lesson_L24_*` |
| L25 候選 | Regime filter sample collapse | `v173_w4_wfa_FAIL_verdict` |
| L26 候選 | Hard Cap ≥ SP arm distance | `v174_cap100_result` |
| L27 候選 | 業界 SL 是 5 層架構 | `stop_loss_mechanisms_catalog` |
| L28 候選 | Vol expansion 進場是 short systemic risk | `v174_HardSLCap_spec` |

### 4.4 使用方式
設計 spec 文件必須包含「**Memory Check**」區段：
```
## Memory Check
- AP check: 此改動是否觸發已知反模式? (列出 AP-1~6 逐條)
- PP alignment: 此改動是否對齊已知正模式?
- Lesson review: 讀了哪些 Lesson? 是否有新 Lesson 候選?
```

---

## 五、Format（交接格式）— 無損交接標準

### 5.1 Handoff 文件（筆電↔桌機）

**必含 7 區段**：

| # | 區段 | 內容 |
|---|------|------|
| 1 | **Status** | 一句話狀態 + 從哪端到哪端 |
| 2 | **What Changed** | Commit 列表 + 每個 commit 一句摘要 |
| 3 | **Current State** | 策略版本 + live_sim 生產版 + research 實驗版 |
| 4 | **Key Decisions** | 本次 session 做了什麼決定、為什麼 |
| 5 | **Next Steps** | 接手端要做什麼，含 MC12 input 配置表 |
| 6 | **Files Modified** | 完整路徑列表 |
| 7 | **Git State** | 最新 commit hash + `git log --oneline -5` |

### 5.2 Backtest 結果文件

**檔名**：`TXF1  <策略名>_v<版本> <組別>_<描述>.xlsx`
**結果 .md 檔必含**：

| 區段 | 內容 |
|------|------|
| Headline | 一句話 verdict |
| Comparison Table | vs baseline 完整指標對照 |
| Exit Distribution | SP/SL/TP 筆數 + avg PnL |
| Year by Year | 每年 PnL 對照 |
| Root Cause | 為什麼好/壞 |
| Honest Verdict | 達成/代價/結論 |

### 5.3 設計 Spec 文件

**必含 5 支柱 checklist**：
```
## Engineering System Checklist
### Rules: [列出適用規則 + 逐條 pass/fail]
### Context Loaded: [列出已讀資料]
### Verification Plan: [V1-V5 哪些必做]
### Memory Check: [AP/PP/Lesson 檢查結果]
### Format: [輸出文件命名 + 交接計劃]
```

### 5.4 KILL / PROMOTE Verdict 文件

| 區段 | 內容 |
|------|------|
| Headline | PASS/FAIL + 一句話原因 |
| Side-by-Side | vs baseline 完整對照表 |
| Per-Window Detail | W4 WFA 9 windows 明細（若有） |
| Root Cause | 為什麼成功/失敗 |
| Lesson Candidate | 此次經驗可編碼為什麼 Lesson? |
| Action | KILL (archive/) 或 PROMOTE (live_simulation/) |

---

## 六、工作流整合

```
新需求 / 改動請求
       │
       ▼
  ┌─ Context Loading ─┐
  │  讀生產版 .pla     │
  │  讀 verdict/lesson │
  │  盤點跨策略影響     │
  └────────┬──────────┘
           │
           ▼
  ┌─ Rules Check ──────┐
  │  R-SL1~4 checklist │
  │  R-D1~4 checklist  │
  │  Rule #11~15       │
  └────────┬──────────┘
           │
           ▼
  ┌─ Memory Check ─────┐
  │  AP-1~6 逐條       │
  │  PP alignment      │
  │  Lesson review     │
  └────────┬──────────┘
           │
           ▼
  ┌─ Design Spec ──────┐
  │  含 5 支柱 checklist│
  │  寫 Why/What/Effect │
  │  寫 Caveats        │
  └────────┬──────────┘
           │
           ▼
  ┌─ Implementation ───┐
  │  .pla 改動          │
  │  最小改動原則       │
  └────────┬──────────┘
           │
           ▼
  ┌─ Verification ─────┐
  │  V1-V5 按場景執行  │
  │  紅旗即停          │
  └────────┬──────────┘
           │
           ▼
  ┌─ Format Output ────┐
  │  Handoff / Result  │
  │  Verdict / Commit  │
  │  Git push          │
  └────────────────────┘
```

---

## 七、違規後果

| 違規 | 後果 |
|------|------|
| 跳過 Rules Check | 不可 commit，退回設計階段 |
| Context 不足就動手 | 強制暫停，先補齊上下文 |
| 未做 V1 Control Group | 結果無效，重跑 |
| 忽視已知 Anti-pattern | commit 即 revert，加寫 Lesson |
| Handoff 缺區段 | 補齊後才推送 |

---

## 八、版本

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-29 | v1.0 | 初版：5 支柱建立（源自 v1.7.2~v1.7.4 開發教訓） |
