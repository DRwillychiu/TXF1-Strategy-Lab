# strategies/research/ — 研究中策略（未部署）

> 這裡的策略還在開發/優化階段，**未部署到任何平台**。
> 通過 P1（敏感度）+ P2（WFA）+ P3（Monte Carlo）三關後才能晉升到 [`live_simulation/`](../live_simulation/)。

---

## 研究中策略一覽（截至 2026-06-13）

### Batch01（第一批 batch markdown 整合）
位於 `research/batch01/`：

| 策略 | 類別 | 狀態 |
|------|------|------|
| S2 InsideBarBreak | 短線突破 | 未通過 P1-P3 |
| S3 VolSqueeze | 波動率壓縮 | 未通過 P1-P3 |
| S4 MACDDivergence | 動能背離 | 未通過 P1-P3 |
| S5 SettlementWeek | 結算週特性 | 未通過 P1-P3 |

> 注意：S1（已升級到 `live_simulation/`）原本也在 batch01，已遷出。

### S06-S15（獨立資料夾結構）

| 策略 | 類別 | 狀態 |
|------|------|------|
| S06 FlashCrashMomentum | 急殺反彈 | 研究中 |
| S07 BullPullbackLong | 牛回多 | 研究中 |
| S08 BearBounceSell | 熊反彈空 | 研究中 |
| S09 VolExplosion | 波動爆發 | 研究中 |
| S10 AdaptiveBreakout | 自適應突破 | 研究中 |
| S11 MiddayCompression | 中午壓縮 | 研究中 |
| S12 WeekdayMomentum | 週幾動能 | 研究中 |
| S13 VolCollapseShort | 波動崩塌空 | 研究中 |
| S14 TripleTFTrend | 三時框趨勢 | 研究中 |
| S15 BBReversion | 布林反轉 | 研究中 |

---

## 研究→模擬→實盤 三層工作流（按 CLAUDE.md）

### 階段 1：研究（這層）
- **Phase 1**: 參數敏感度分析（3D 表面圖、確認高原而非尖峰）
- **Phase 2**: Walk-Forward 優化（IS 24m / OOS 6m / 步長 6m / 9 窗口）
- **Phase 3**: Monte Carlo 壓力測試（10,000 次序列打亂、95% MDD）
- **品質門檻**：
  - Walk-Forward Efficiency > 50%
  - Monte Carlo 95% MDD < 帳戶 30%
  - 參數高原寬度 > 參數範圍 20%
  - OOS Profit Factor > 1.0
  - 每月至少 2 筆交易

### 階段 2：模擬（晉升到 [`live_simulation/`](../live_simulation/)）
- 部署到 MC12 模擬帳戶
- 累積實戰交易紀錄
- 對比回測 vs 模擬績效

### 階段 3：實盤（晉升到 [`live/`](../live/)）
- 進入 MC9 真金白銀帳戶
- 通過 master verification（verify_all_live.py）
- 跨策略一致性檢查

---

## 新策略加入流程

當有新策略想加入這個專案：

1. **建立資料夾** `strategies/research/Sxx_StrategyName/` 或加入 batch
2. **必備檔案**：
   - `Sxx_StrategyName.pla`（PowerLanguage 程式碼）
   - `Sxx_StrategyName_strategy.md`（策略邏輯描述）
   - `Sxx_StrategyName_annotated.md`（中文逐行註解）
3. **遵守 CLAUDE.md 程式碼規範**：
   - `v_` 變數前綴
   - 進場條件 ≤ 5 個
   - 每隻策略 < 150 行
   - `STRATEGY_GEN_` 名稱前綴
   - `v_Prev_MP` 追蹤前根部位
4. **跑 P1-P3 驗證**：
   - `python backtest/optimize/param_sensitivity.py --strategy Sxx`
   - `python backtest/optimize/walk_forward.py --strategy Sxx`
   - `python backtest/optimize/monte_carlo.py --strategy Sxx`
5. **通過後晉升**：`git mv strategies/research/Sxx_*/ strategies/live_simulation/`

---

## _batch_summaries/
集中存放各批次的策略整合報告。
