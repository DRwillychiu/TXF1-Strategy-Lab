# TXF1-Strategy-Lab

## 專案概述
台指期貨（TXF1）量化策略研究庫。所有策略以 MultiCharts 12 PowerLanguage 撰寫，用 Python 做模擬回測驗證。

## 技術規格（2026-08-04 依 MC12 策略屬性截圖校正，完整版見 `docs/policies/BACKTEST_COST_SPEC.md`）
- 商品：TXF1（台指期近月連續），1 點 = 200 NTD
- 平台：MultiCharts 12 / PowerLanguage（EasyLanguage 相容）
- 手續費：無｜滑價：**1,000 NTD 每口每邊**（非 round-trip）→ 來回 2,000 NTD = **10 點**
  - **任何保本／成本門檻常數必須 >= 10 點**，低於此值掛保本標籤仍淨虧（S16_S v1.11.0 實證）
- 固定口數：**2 口**｜原始資金：2,000,000 NTD（% 報酬與 MDD% 基準）｜利率 2%
- MaxBarsBack：**100** → 任何指標回看長度不得 > 99（現行最長 ML_ATR_LongLen=90）
- 回測區間：2020/01/01 ~ 今天
- 交易時段：日盤 08:45-13:45 / 夜盤 15:00-05:00

## 目錄結構

完整樹狀圖見 **`docs/REPO_STRUCTURE.md`**（2026-08-04 自本檔拆出，原文剪貼未改寫）。

拆檔原因：本檔受 300 行硬上限約束（MAINTENANCE_PROTOCOL §2）。目錄結構是純參考資訊、
非強制規範，且隨每次新增策略而變動，留在 CLAUDE.md 只會持續擠壓規範內容的空間。
規範性內容（技術規格、三層晉升流程、PowerLanguage 規範、品質門檻）一律留在本檔。

> ⚠️ `docs/REPO_STRUCTURE.md` 已知有過時處（live 策略實際帶子目錄），待完整重新審計。


## 三層晉升流程

```
research/  ──[Phase 1-3 通過]──►  live_simulation/  ──[模擬實證]──►  live/
（開發中）                       （MC12 模擬）                      （MC9 實盤）
```

**晉升條件**：
- research → live_simulation：通過 WFE > 50%、MC 95% MDD < 帳戶 30%、OOS PF > 1.0
- live_simulation → live：模擬 ≥ 30 筆交易、模擬 PF ≥ 1.2、回測偏離度 ≤ 30%

## PowerLanguage 程式碼規範
1. 所有參數用 `inputs:` 宣告，不可寫死
2. 變數用 `variables:` 宣告，`v_` 前綴
3. Data2 引用用 `[1]` 已收盤索引（Data2 當根不可靠）
4. 不使用未來函數（不可用 `highest(high, N)[0]` 前瞻引用）
5. 進場：`buy/sell short next bar at X stop/limit`
6. 出場：`sell/buy to cover next bar at X stop`
7. 不在同根 K 棒使用 `marketposition` 後立即引用
8. 用 `v_Prev_MP` 追蹤前根部位狀態，腳本最末行更新
9. 策略名稱 `STRATEGY_GEN_` 前綴
10. 每隻策略 < 150 行，進場條件 ≤ 5 個
11. **★ 強制規範**：所有策略必須含 Settlement_Flat 模組（7 元素）
    - 詳見 [docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md](docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
    - Priority 0 出場順序：Kill > Registry > Holiday > **Settlement** > 原邏輯
    - 進場 gate 必含 `v_Settlement_Day = false`
    - 驗證腳本 `scripts/verify_settlement_flat.py` 必須通過
12. **★ 強制規範**：所有策略必須含 P3b Immediate Stop Guard（SetStopContract + SetStopLoss + SL_Pct）
    - 詳見 [docs/policies/P3b_immediate_stop_guard_design_20260618.md](docs/policies/P3b_immediate_stop_guard_design_20260618.md)
    - **SetStopContract**：必須在 SetStopLoss 前呼叫。使 SetStopLoss 金額為 PER-CONTRACT
      而非 TOTAL POSITION。實盤統一 2 口，缺此呼叫 = 引擎停損 2 倍過窄。
      （2026-07-26 發現 L2/L4/L5/S16_S 全部缺漏，已修復）
    - **SetStopLoss**：MC 引擎層級函數，進場成交瞬間即生效（無 IOG 依賴）
    - **SL_Pct**：ATR 停損距離的百分比上限。ATR 在極端行情可飆升數倍，
      SL_Pct 以進場價的固定百分比封頂停損距離，防止不可預期災難。
      Long: Floor = EntryPrice - EntryPrice * SL_Pct / 100
      Short: Ceiling = EntryPrice + EntryPrice * SL_Pct / 100
      MC sweep 0.00-5.00 step 0.25 找收斂點（最窄不降效值），寫回 input 預設。
    - 必須在進場區塊之前、指標計算之後呼叫
    - Guard 條件：Long 策略 `if MP <= 0`、Short 策略 `if MP >= 0`（進場後自動凍結）
    - 距離公式必須與該策略的 Frozen SL 使用相同變數和乘數
    - 金額 = 點數距離 × `BigPointValue`（TXF1 = 200）
    - 每隻策略僅限 1 組 `SetStopContract` + `SetStopLoss` 呼叫（不可重複）
    - 新策略開發時，此三件套（SetStopContract + SetStopLoss + SL_Pct）與 Settlement_Flat 同為必備結構模組
13. **★ 強制規範**：所有新策略 / 既有策略優化必須通過機構級 10 維度評估
    - 詳見 [docs/policies/institutional_risk_framework_20260619.md](docs/policies/institutional_risk_framework_20260619.md)
    - 10 維度：Sharpe/Sortino/Calmar、VaR/CVaR、跨策略相關性 < 0.7、
      Drawdown clustering、樣本數 ≥ 100、WFE > 50%、三市況 PF > 1.0、
      成本分析、Operational risk、法規 / 帳戶限制
    - 任一維度 fail → 不可上 live_simulation
    - 即使是 1-line input 改動，也須評估這 10 維度的變化
14. **★ 強制規範**：策略開發必須嚴格按照 OFFICIAL_ROADMAP.md 排程，不可發明新策略名稱
    - 詳見 [docs/policies/OFFICIAL_ROADMAP.md](docs/policies/OFFICIAL_ROADMAP.md)
    - 完整排程（拆解後 21 隻）：
      `S3_L → S3_S → S4_L → S4_S → S5_L → S5_S → S6 → S7 → S8 → S9_L → S9_S`
      `→ S10_L → S10_S → S11 → S12_L → S12_S → S13 → S14_L → S14_S → S15_L → S15_S`
    - **不允許**：發明新策略名稱（RapidPullbackShort / TurnOfMonth / SPX_Overnight 等）
    - **不允許**：跳號（S3_L 完成必直接進 S3_S → S4_L）
    - **不允許**：平行開發（一次只開發一隻）
    - **拆解規則（Rule R-6）**：原始排程雙向策略**必拆**為 `Sx_L` (純多) + `Sx_S` (純空)
    - **順序鐵則**：一律先 L 後 S（TXF1 偏多 regime，Long 驗證較快）
    - 每隻策略必有 W0 Alpha Pre-verify (Python 真實資料) → 才寫 .pla
    - 違反本規則 = 違反用戶 2026-06-22 明確指示
15. **★ 強制規範**：所有 .pla 檔必須 100% ASCII（無中文、無 em dash、無 emoji、無全形標點）
    - MC PowerLanguage 對非 ASCII 字元行為 build-dependent，曾發生 v1.1 因 em dash + 勾號炸 line 0 編譯錯誤
    - 違規 = MC 編譯失敗（通常 line 0 col 0 通用錯誤，極難 debug）
    - 強制驗證腳本：`python scripts/verify_pla_ascii.py --strict`
    - Commit 前**必須跑驗證**通過才能 push
    - 適用範圍：`strategies/live/`、`strategies/live_simulation/`、`strategies/research/`（排除 archive/）
    - 違反本規則 = 違反 memory rule `feedback_mc_english_only` + 用戶 2026-06-22 明確指示
16. **★ 強制規範**：五支柱工程系統（Rules / Context / Verification / Memory / Format）
    - 每次設計決策、程式碼修改、版本推進，必須通過五支柱檢查
    - 設計 spec 文件必含 Engineering System Checklist（5 區段）
    - Handoff 文件必含 7 區段（Status / Changed / State / Decisions / Next / Files / Git）
    - 反模式 AP-1~6 逐條檢查，觸發任一 = 立即 KILL
    - 完整規範：[`docs/methodology/ENGINEERING_SYSTEM.md`](docs/methodology/ENGINEERING_SYSTEM.md)
    - 違反本規則 = 違反用戶 2026-06-29 明確指示
17. **★ 強制規範**：極端行情策略必須採用多層停損 SOP（商辦大樓架構）
    - 詳見 [`docs/methodology/extreme_sl_multilayer_sop_20260629.md`](docs/methodology/extreme_sl_multilayer_sop_20260629.md)
    - ATR 停損 = 最後防線（地基），不是主要出場機制
    - 1M 五層即時監控（1F K棒 / 2F 量價 / 3F 動能 / 4F 結構 / 5F 波動率）
    - 觸發機制：加權積分 ≥ 65% + 跨類別 ≥ 3 層 + 虧損啟動門檻
    - 禁止固定點數 cap（在 vol-adaptive 架構中是設計矛盾）
    - 適用範圍：所有操作於極端波動環境的策略（S3_S、S6、S9 等）
    - 所有新策略的停損設計 spec 必須引用本 SOP 並檢查合規
    - 違反本規則 = 違反用戶 2026-06-29 明確指示
18. **★ 強制規範**：所有策略 promote 前必跑 Non-WFA 5 件套驗證
    - 詳見 [`docs/methodology/non_WFA_validation_SOP_20260630.md`](docs/methodology/non_WFA_validation_SOP_20260630.md)
    - 5 件套：Monte Carlo Simulation + Bootstrap Resampling + Stress Testing + Regime Analysis + Robustness Testing
    - 不包含 Paper Trading（本來就會在 live_simulation 期間執行）
    - 適用範圍：所有 future strategies (S4_S 以後)，含 hot-fix 之外的所有重大改動
    - Pass criteria：≥ 4/5 件套 pass 才考慮 promote
    - 對 low-frequency strategy（< 10 trades/yr）尤其重要，因短週期 WFA 不公平
    - 違反本規則 = 違反用戶 2026-06-30 明確指示
19. **★ 強制規範**：research → live_simulation PROMOTE 必跑 PROMOTE_CHECKLIST 6 項檢查
    - 詳見 [`docs/policies/PROMOTE_CHECKLIST.md`](docs/policies/PROMOTE_CHECKLIST.md)
    - 觸發事件：2026-07-10 S16_S v1.0-PROD 帶著 W2 draft placeholder `v_Holiday_Block = False` 通過 PROMOTE，違反 Rule #11，直到 2026-07-16 才發現
    - 6 項檢查：
      1. Placeholder Scan（grep `v_*_Block = False;` / `placeholder` / `TODO` / `FIXME` / `Wx draft`）
      2. Rule #11 Settlement_Flat 7 元素齊全（模組**有效**，不只**存在**）
      3. Rule #12 SetStopLoss Guard 正確
      4. Rule #15 ASCII 100%
      5. Rule #13 10 維度 + Rule #18 5 件套
      6. Sniper 特殊條件（若為低頻策略 <20 trades/yr）
    - Fail Check 1-4 任一項 = **拒絕 PROMOTE**
    - PROMOTE 後才發現 gap = 立即 patch + 版本號 +.1 + 更新 DEPLOYMENT.md + 更新 CHECKLIST（新增 lesson）+ commit/push
    - 適用範圍：所有 research → live_simulation 動作
    - 違反本規則 = 違反用戶 2026-07-16 明確指示（「不要又有犯錯空間」）

## 優化工作流程（Claude Code 使用時遵守）

### Phase 1: 參數敏感度分析
對每個 input 參數，在合理範圍內掃描，繪製 3D 表面圖。
目標：確認參數有「高原」而非「尖峰」（尖峰 = 過度擬合）。

### Phase 2: Walk-Forward 優化
- In-Sample: 滾動 2 年
- Out-of-Sample: 滾動 6 個月
- 步長: 6 個月
- 合格標準: OOS PF > 1.0 且 OOS 淨利 > 0

### Phase 3: Monte Carlo 壓力測試
- 隨機打亂交易序列 10,000 次
- 計算 95% 信心水準下的 MDD
- 計算破產機率（帳戶虧損 > 50%）

### Phase 4: 策略組合分析
- 計算策略間相關性矩陣
- 模擬等權組合 equity curve
- 找最佳配置（Sharpe 最大化）

## 品質門檻
- Walk-Forward Efficiency > 50%
- Monte Carlo 95% MDD < 帳戶 30%
- 參數高原寬度 > 參數範圍的 20%
- OOS Profit Factor > 1.0
- 每月至少 2 筆交易

## 常用指令
```bash
# 抓取最新資料
python backtest/fetch_data.py

# 跑全策略回測
python backtest/run_backtest.py

# 單策略參數優化
python backtest/optimize/param_sensitivity.py --strategy NightMomentum --param LookbackBars --range 2,10

# Walk-Forward 驗證
python backtest/optimize/walk_forward.py --strategy NightMomentum

# Monte Carlo 壓力測試
python backtest/optimize/monte_carlo.py --strategy NightMomentum --iterations 10000

# 策略組合分析
python scripts/strategy_comparison.py
```
