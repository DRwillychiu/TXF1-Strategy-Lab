# Strategy R&D SOP — 策略研發標準作業流程

> **強制位階**：所有新策略開發 / 既有策略 redesign / cowork 拉入的新策略，必須**先完成 Step 0 (9 點 Intake)** 才能進入後續開發。
>
> **建立日期**：2026-06-20
> **依據**：用戶 SOP 規範（從每週 cowork 抓取最新 5 隻策略 → git 拉下 → 開始探討時的固定流程）

---

## 觸發時機

下列任一情境必須走本 SOP：

| 情境 | 範例 |
|------|------|
| 全新策略開發 | 每週批次 S16+ 新策略 |
| 既有策略 redesign | S3 v1.1 → v2.0、L4 v1.42 → v1.45 |
| Cowork 自動拉入新策略 | 每週從 cowork 抓最新 5 隻 |
| 回顧/評估歷史策略 | archive/ 內舊策略重新評估 |
| 接續對話跨 session | 新 Claude session 接手既有策略 |

---

## Step 0 — 9 點 Intake（必填，無例外）

開始任何 code 動作前，**用以下 9 點骨架完整描述策略**，每點都要有具體內容：

| # | 項目 | 必填內容 | 範例（S3 v2.0 Path C） |
|---|------|---------|----------------------|
| 1 | **名稱** | 策略代號 + 一句話定位 | S3 v2.0 Path C — 強勢日內反轉做空 |
| 2 | **操作週期** | 主要進場/出場 K 線時間框架 | 5M K |
| 3 | **是否有觀察週期** | Y/N + 長度（用什麼 lookback / regime gate） | Y — 當日 session（08:45 起到當下） |
| 4 | **賺什麼錢** | 賺哪一種結構性 edge / inefficiency | 日內多方強勢拉升後的短線 mean reversion |
| 5 | **適合什麼行情** | 哪種市況有效、哪種會失效 | 適合：多方主導且 5M 動能衰竭。失效：純趨勢延續日 |
| 6 | **為什麼這樣規劃** | 設計 thesis、alpha 來源、為什麼這組條件 | 5-AND 篩出「日內強勢 + 5M 動能轉空」雙重結構，避免做空底部反彈 |
| 7 | **預期結果** | 觸發/年、WR、R:R、PF gross、PF 含滑價 | 25-40/yr、WR 50-55%、R:R 1.4、PF gross 1.3+、PF 含滑價 1.1+ |
| 8 | **程式碼** | .pla 檔案完整路徑（已存在）或計畫 LOC（待寫） | `strategies/research/S03_PullbackShort/S3_RapidPullbackShort_v2.pla`（~600 LOC，待寫） |
| 9 | **最佳化參數驗證範圍** | 每個 input 的 sweep min/max/step、合理性依據 | C_RelStr 0.3-0.8 step 0.1（TXF1 日均波動 ~1%）、C_Pullback_Max 1.0-2.0 step 0.2 ... |

### 9 點完成判定
- 每點必須有**具體可驗證**內容（不可寫「TBD」/「待定」/「視情況」）
- 第 7 點數字必須有依據（從相似策略外推 / 真實數據統計 / 文獻）
- 第 9 點 ranges 必須有理由（每個 min/max 為何選此值）

### Intake 文件位置
- 新策略：`strategies/research/2026-Wxx/Sxx_Name/Sxx_Name_intake.md`
- Redesign：`strategies/<層級>/<策略資料夾>/Sxx_vN_intake.md`
- 必填的 9 點直接用上表格式

---

## Step 1 — 策略邏輯文件化

Intake 過了才寫程式。三份標準文件：

1. **`Sxx_Name_intake.md`** — Step 0 的 9 點完整版（必須）
2. **`Sxx_Name_strategy.md`** — 策略邏輯白話版 + 進出場規則完整列表（必須）
3. **`Sxx_Name_annotated.md`** — 中文逐行 .pla 註解（必須）

---

## Step 2 — .pla 程式碼撰寫

依 [CLAUDE.md](../CLAUDE.md) 第 1-13 條程式碼規範：
- 所有 input 宣告、`v_` 前綴變數、`STRATEGY_GEN_` 名稱
- 進場條件 ≤ 5 個（OR 分支可超過，但單一 path 內 ≤ 5）
- **必含 Settlement_Flat 模組（規範 #11）**
- **必含 SetStopLoss Immediate Stop Guard（規範 #12）**
- 進出場標籤 LE_/LX_/SE_/SX_ 嚴格區分（[user memory](../../.claude/projects/.../feedback_mc_entry_exit_labels.md)）
- 跨日商品時段條件閉區間 `Time>=X AND Time<=Y`（[user memory](../../.claude/projects/.../feedback_mc_time_24hr_pitfall.md)）
- 新 input 前 grep 既有 conditions 確認非 redundant（[user memory](../../.claude/projects/.../feedback_filter_redundancy_check.md)）

---

## Step 3 — Verify Script

`scripts/verify_<strategy>.py`：結構面驗證（無需跑 MC），檢查項目：
- 必填段落齊全（Settlement_Flat、SetStopLoss、Frozen SL、Holiday、Kill switch）
- 進出場標籤命名正確
- Time 條件閉區間
- inputs 全數宣告、無 hardcode
- 預期通過率 100%

---

## Step 4 — MC 回測 P1-P3

| Phase | 工具 | 通過標準 |
|-------|------|--------|
| P1 參數敏感度 | `backtest/optimize/param_sensitivity.py` | 高原寬度 > 參數範圍 20% |
| P2 Walk-Forward | `backtest/optimize/walk_forward.py` | WFE > 50%、OOS PF > 1.0 |
| P3 Monte Carlo | `backtest/optimize/monte_carlo.py` | 95% MDD < 帳戶 30% |

---

## Step 5 — 機構級 10 維度評估（CLAUDE.md #13）

任一維度 fail → 不可上 live_simulation：
1. Sharpe / Sortino / Calmar
2. VaR / CVaR
3. 跨策略相關性 < 0.7
4. Drawdown clustering
5. 樣本數 ≥ 100
6. WFE > 50%
7. 三市況 PF > 1.0
8. 成本分析
9. Operational risk
10. 法規 / 帳戶限制

詳見 [docs/institutional_risk_framework_20260619.md](institutional_risk_framework_20260619.md)。

---

## Step 6 — 升級判定

- **research → live_simulation**：P1-P3 PASS + 10 維度 PASS
- **live_simulation → live**：模擬 ≥ 30 筆 + 模擬 PF ≥ 1.2 + 回測偏離度 ≤ 30%

`git mv` 對應資料夾，更新 README。

---

## 完成檢核（每隻策略 sign-off 前）

- [ ] Step 0 — 9 點 intake 全填、每點具體可驗證
- [ ] Step 1 — strategy.md / annotated.md 對應每點 intake
- [ ] Step 2 — .pla 寫好、通過 CLAUDE.md 第 1-13 條
- [ ] Step 3 — verify_script.py 100% PASS
- [ ] Step 4 — P1-P3 三階段通過標準
- [ ] Step 5 — 機構級 10 維度全 PASS
- [ ] git commit + push（[user memory](../../.claude/projects/.../feedback_git_full_push.md)：「更新 git」一律 commit + push）

---

## 反 SOP 範例（為什麼要有這個流程）

**S3 v1.0 → v1.1 → v2.0 redesign 案例**（2026-06-19）：
- v1.0 沒做完整 9 點 intake，直接寫了 .pla
- v1.1 補修 16 bugs 但 alpha 沒重驗
- v2.0 redesign 時，新 Claude session 接手又花一輪重新組織問題（因為沒文件化的 intake 模板）
- 用戶兩次提醒「不要浪費 token」「不要過度設計」
- 教訓：**先 9 點 intake → 再動手**，可省下後續所有「方向錯誤的開發」成本

---

## 參考

- [CLAUDE.md](../CLAUDE.md) — 程式碼規範 + 強制位階
- [strategies/research/README.md](../strategies/research/README.md) — 週批次資料夾結構
- [docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md](SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) — Settlement_Flat 模組
- [docs/P3b_immediate_stop_guard_design_20260618.md](P3b_immediate_stop_guard_design_20260618.md) — SetStopLoss 規範
- [docs/institutional_risk_framework_20260619.md](institutional_risk_framework_20260619.md) — 10 維度評估
