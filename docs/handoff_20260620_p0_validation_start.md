# 2026-06-20 起 P0 驗證工作 Handoff

**寫於**：2026-06-19 結束
**收件人**：明日 Claude（不論桌機 / 筆電端）
**git 最後 commit**：e5d842e Portfolio audit
**狀態**：working tree clean，所有 commit 已 push

---

## 一、為什麼從 P0 重新驗證

過去 3 天（6/17-6/19）所有設計改進都暴露同一個結構性問題：
**設計超前實證、各別策略局部優化、缺乏 portfolio 級驗證**

具體失敗鏈：
1. S2 v0.4 → 4 版迭代後 0 進場（VolFilter 元兇）
2. S2 v0.6 → 修正後 alpha 仍微弱（PF 1.057）
3. L3/L4 RangeForceExit → 夜盤誤觸 + 完全 rollback
4. L4 v14.5 → A 與 Macro_Block redundant + B 過度激進，完全 rollback

**根因**：缺乏機構級的「**先驗證 portfolio 級指標**再改個別策略」紀律。

---

## 二、明天起的 P0 工作清單（**順序執行**）

### 🔴 P0-1：跨策略相關性矩陣（最高優先 / 預估 2 小時）

**為什麼最先做**：
- 不影響任何代碼
- 純資料分析
- 立刻知道 portfolio 是否重複曝險
- 結果決定後續配置邏輯

**輸入**：6 份既有 xlsx（用戶 Downloads 中已有）
- `TXF1  WILLY_ATR_LONG_60M 策略回測績效報告.xlsx` (L1)
- `TXF1  Trendbearish_V1 策略回測績效報告.xlsx` (L2)
- `TXF1  STRATEGY_WILLY_LONG_C 策略回測績效報告.xlsx` (L3)
- `TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告.xlsx` (L4)
- `TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告.xlsx` (L5)
- `TXF1  STRATEGY_GEN_NightMomentum 策略回測績效報告.xlsx` (S1)

**輸出**：
1. 寫 `scripts/analyze_portfolio_correlation.py`
2. 把每筆交易 daily PnL 攤平（同日多筆加總）
3. 算 6×6 daily PnL correlation matrix
4. 算 monthly PnL correlation matrix（穩定性更高）
5. 找出 > 0.7 的高相關對
6. 寫 `docs/portfolio_correlation_matrix_20260620.md` 報告

**判定**：
- 若 L1-L5 / L1-S1 / L5-S1 高相關 → 多單重複曝險 → 配置降低
- 若 L2-L4 高相關 → 空單重複曝險
- 若各對 < 0.3 → portfolio 多樣化良好

### 🔴 P0-2：Walk-Forward Analysis（中優先 / 預估 4-6 小時）

**先決條件**：先做 P0-1（會發現問題決定 WFA 順序）

**步驟**：
1. 寫 `scripts/walk_forward.py` 通用框架
   - IS 2 年滾動
   - OOS 6 個月滾動
   - 步長 6 個月
2. 對 6 隻策略各跑 WFA
3. 計算 WFE = OOS_PF / IS_PF
4. WFE < 50% → 該策略警示

**輸出**：
- 6 隻策略各自 WFE 數字
- 寫 `docs/walk_forward_results_20260620.md`

**判定**：
- WFE > 70% → 強 robust
- WFE 50-70% → 可接受
- WFE 30-50% → 警示但仍可用
- WFE < 30% → 嚴重過擬合，**重新評估**

### 🔴 P0-3：三市況 PF 拆解（低於前兩個 / 預估 3-4 小時）

**先決條件**：P0-1 + P0-2 完成

**步驟**：
1. 識別 2020-2026 的 bull / bear / range 區段
   - 用 Daily MA(50) vs Daily MA(200) 黃金 / 死亡交叉
   - 或用 ATR 區分 trending vs ranging
2. 把 6 隻策略的交易按市況分類
3. 每策略 × 每市況 各算 PF
4. 找出「**只在 1 種市況有效**」的策略

**輸出**：
- 6×3 PF 矩陣（共 18 格）
- 寫 `docs/three_regime_pf_analysis_20260620.md`

**判定**：
- 三市況皆 PF > 1.2 → 全天候策略
- 兩市況 > 1.0 → 中等
- 一市況 < 1.0 → 警示
- 多市況 < 1.0 → 機構級不可接受

---

## 三、P0 完成後的決策樹

```
P0-1 / P0-2 / P0-3 三項全部完成
   │
   ↓
重新計算 portfolio 配置：
   - 高相關策略 → 倉位減半
   - 低 WFE 策略 → 倉位降低
   - 單市況依賴策略 → 標記「regime-specific」
   │
   ↓
寫 docs/portfolio_allocation_v2_20260620.md
   │
   ↓
用戶 review → 決定上 live 配置
   │
   ↓
進 P1 階段（既有策略個別優化）
```

---

## 四、P0 期間嚴格遵守的紀律

### 紀律 1：不改任何 .pla 程式碼

P0 是「**純資料分析**」階段，不改策略邏輯。

### 紀律 2：每個分析腳本必須 commit + push

按用戶 [`feedback_git_full_push.md`](../README.md) 規範。

### 紀律 3：遵守 CLAUDE.md 規則 #13

任何提案必須回答 10 維度變化（已加入規則）。

### 紀律 4：每完成 P0 一項立刻寫報告 + 反饋用戶

不要全做完才回報，每完成一個 commit + push + 用戶反饋一次。

---

## 五、明天可能會用到的腳本參考

### 既有可參考的分析腳本

- `scripts/analyze_settlement_backtest.py` — 讀 xlsx 抽交易明細的範本
- `scripts/analyze_s2_phase2.py`（待寫）
- `scripts/analyze_l4_v145_ab.py` — A/B 對比範本
- `scripts/verify_settlement_flat.py` — 驗證腳本範本

### 預計新增

- `scripts/analyze_portfolio_correlation.py` (P0-1)
- `scripts/walk_forward.py` (P0-2)
- `scripts/three_regime_pf.py` (P0-3)

---

## 六、6 策略當前快照（明天確認用）

| 策略 | 版本 | 狀態 |
|------|------|------|
| L1 TrendLong | V2.6 + Settlement + ImmediateStop | ✅ Stable |
| L2 TrendShort | 5.2 + Settlement + ImmediateStop | ✅ Stable |
| L3 ConsolidationLong | v13.4 + Settlement + ImmediateStop | ✅ Stable |
| L4 ConsolidationShort | **v14.4 (純) + ImmediateStop** | ✅ **剛回滾今天** |
| L5 BreakoutLong | v19.8 + Settlement + ImmediateStop | ✅ Stable |
| S1 NightMomentum | v2.7 + Settlement + ImmediateStop | ✅ Stable |
| S2 InsideBarBreak | v0.6 (research, 0 進場修了但未 MC 驗證) | ⏳ Pending |

---

## 七、CLAUDE.md 規則完整清單（給未來 Claude）

| # | 規則 | 強制等級 |
|---|------|--------|
| 1-10 | PowerLanguage 程式碼基本規範 | 必守 |
| **11** | **所有策略必須含 Settlement_Flat 7 元素** | **強制** |
| **12** | **所有策略必須含 P3b ImmediateStop** | **強制** |
| **13** | **所有新策略 / 優化必須通過 10 維度評估** | **強制** |

---

## 八、教訓記憶清單（已寫入 memory）

| 記憶檔 | 主題 |
|--------|------|
| feedback_mc_time_24hr_pitfall.md | MC Time 24 小時制陷阱 |
| feedback_filter_redundancy_check.md | 新 filter 須做重疊度+通過率雙重檢查 |
| feedback_trend_let_profits_run.md | 趨勢策略讓利潤奔跑 |
| feedback_holiday_flatten_rule.md | 假日前平倉鐵律 |
| feedback_mc_entry_exit_labels.md | MC 進出場標籤規範 |
| feedback_git_full_push.md | 完整更新 git 必含 push |
| feedback_no_break_questions.md | 不問休息問題 |

---

## 九、明日 Claude 開機 SOP

```bash
# 1. Pull 最新（如果跨裝置）
cd C:/Users/User/Desktop/TXF1-Strategy-Lab
git pull origin main

# 2. 確認狀態
git status   # 應該 working tree clean
git log --oneline -5

# 3. 讀本檔（你正在讀的）

# 4. 詢問用戶想從哪一個 P0 開始
#    建議: P0-1 (correlation matrix) — 最快有結果

# 5. 開始工作
```

---

## 十、最後一句話

**明天的工作比個別策略優化重要 10 倍。**
**Portfolio 級指標決定整體 alpha 上限，個別策略只能在框架內優化。**

完成 P0 之後再回頭看 S2 / L4 / S6-S15，會有完全不同的視角。
