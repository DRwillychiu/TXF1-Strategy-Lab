# RangeForceExit 模組回滾報告

**回滾日**：2026-06-17（提出當天即回滾）
**影響策略**：L3 ConsolidationLong、L4 ConsolidationShort
**回滾後版本**：L3 v13.4 / L4 v14.4（皆為「Settlement_Flat only」）

---

## 一、事件時間軸

| 時間 | 事件 |
|------|------|
| 2026-06-17 早 | 用戶要求加入 RangeForceExit 模組（Constitution v1.1 條款 7）|
| Commit [3e27f46](https://github.com/DRwillychiu/TXF1-Strategy-Lab/commit/3e27f46) | L3 v13.3 / L4 v14.3 部署，條件僅 `Time >= 1200` |
| 用戶 MC 重載 L4 | 績效轉負 |
| 用戶 30 秒內反饋 | "為甚麼我剛剛更新 L4，績效直接變成負的" |
| Commit [fad1005](https://github.com/DRwillychiu/TXF1-Strategy-Lab/commit/fad1005) | Hotfix v13.3.1 / v14.3.1，加 `Time <= 1330` 上界 |
| 用戶決策 | **「L3/L4 直接回歸原始版本」**（連 hotfix 版本都不要）|
| 本 commit | **v13.4 / v14.4 完全移除 RangeForceExit** |

---

## 二、技術 Bug：MC PowerLanguage Time 24 小時制陷阱

### 根本原因
MC PowerLanguage 的 `Time` 變數是 24 小時 HHMM 整數：
- 12:00 = 1200
- 13:30 = 1330
- 15:00 = 1500（夜盤開盤）
- 23:59 = 2359（夜盤）
- 00:00 = 0（凌晨）
- 04:00 = 400（凌晨）

### 錯誤代碼
```powerlanguage
{ v13.3 / v14.3 錯誤版本 }
if Time >= Range_ForceExit_Time then  { Time >= 1200 }
    Sell ("CL_RangeForceExit") next bar at Market;
```

### 為何破壞 L4
台指期跨日商品包含夜盤 15:00~05:00：
- 日盤 12:00~13:45 → `Time >= 1200` ✓ 預期觸發
- 夜盤 15:00~23:59 → `Time >= 1200` ✓ **意外觸發**

任何持倉到 15:00 夜盤開盤的 L4 部位，**第一根夜盤 K 棒就被強制平倉** → 破壞 L4 「日內進場、隔日早盤反彈」的核心邏輯。

### 修正版（已 hotfix 但仍回滾）
```powerlanguage
{ v13.3.1 / v14.3.1 hotfix - 加上界 }
if (Time >= Range_ForceExit_Time) and
   (Time <= Range_ForceExit_End) then  { 1200 <= Time <= 1330 }
    Sell ("CL_RangeForceExit") next bar at Market;
```

---

## 三、用戶為何選擇完全回滾（不止 hotfix）

即使 hotfix 修好夜盤誤觸 bug，**RangeForceExit 概念本身對既有 L3/L4 仍是破壞性的**：

1. **L3/L4 既有部位行為已被 backtest 驗證**：歷史 PF / WR / MDD 都基於「自然出場」邏輯
2. **強制 12:00-13:30 出場 = 剪掉部分尾段獲利**：盤整策略中段可能正在 mean reversion 過程，主動切斷會丟失 alpha
3. **0 Settlement 觸發 = 模組本來就無實質需求**：L3/L4 歷史上沒有任何一筆撐到結算 12:30，加 RangeForceExit 是「**過度防禦未發生的風險**」
4. **「跨日盤整 = 災難」這個論點需要實證資料才能支持**：目前我們是「邏輯推論」而非「歷史證明」

---

## 四、保留的部分

| 項目 | 保留？ | 原因 |
|------|--------|------|
| Settlement_Flat 模組 | ✅ 保留 | L1 67.3% PnL 實證有效，L2-L5+S1 兜底零成本 |
| 三象限分類（條款 6）| ✅ 保留 | 概念正確，分類腳本仍可用 |
| L5 重新分類為 Swing-Trend | ✅ 保留 | 純分類調整，與代碼無關 |
| 補充規則 4（手動 Roll 同步）| ✅ 保留 | 實戰常識 |
| 補充規則 5（input 調整重跑驗證）| ✅ 保留 | 工程紀律 |
| **條款 7 RangeForceExit 強制** | ❌ **撤回** | 實作失敗 + 概念尚未驗證 |
| **條款 8 Trail/BE 強制 TimeExit** | ❌ **撤回** | 同樣有 Time 24-hour 陷阱 + 未實證 |

---

## 五、教訓清單（寫入記憶以避免再犯）

### 教訓 1：MC Time 24 小時制必須閉區間
**任何 `Time >= X` 條件，必須同時有 `Time <= Y`，否則夜盤誤觸發**。
已寫入記憶：[`feedback_mc_time_24hr_pitfall.md`](C:/Users/User/.claude/projects/C--Users-User-Desktop/memory/feedback_mc_time_24hr_pitfall.md)

### 教訓 2：「邏輯推論」不等於「實證證明」
- 「跨日盤整撐到 12:30 = 反轉前砍倉」是邏輯推論
- 實際上 L3/L4 歷史 0 Settlement 觸發 = **沒實證過這個災難**
- 「邏輯推論」不夠作為「強制條款」的依據，必須要有歷史回測證明

### 教訓 3：對既有 PF > 1.0 策略的破壞性變更要極度謹慎
- L3 / L4 已是 live 上架策略，PF 1.17 / 1.39
- 任何新模組加入前，應該先在 backtest 跑「啟用/停用」對比
- 直接 commit + push 然後叫用戶 MC 重載是**繞過 backtest 對比**的危險動作

### 教訓 4：驗證腳本要涵蓋「邊界條件」
- 我寫的 verify_range_force_exit.py 第一版只檢查「有沒有下界」
- 沒檢查「有沒有上界」這個關鍵防呆
- 測試覆蓋不足 = bug 滑過去

### 教訓 5：用戶 30 秒反饋讓我們避免實盤虧損
- 你立刻發現「L4 績效直接變成負的」並反饋
- 換成靜默 deploy 到實盤交易 = 損失就不只是 backtest 數字
- **這個快速反饋鏈是專案最重要的安全機制**

---

## 六、後續研究方向（暫不上架）

### 方向 A：限定條件的 RangeForceExit
不在「每天 12:00」強制平倉，而是限定：
- **僅結算日當天** + 盤整策略 → 12:00 提前平倉（避免結算前噪訊）
- 一般日仍允許自然出場

優點：不影響 P&L 主要來源（一般日的 mean reversion）
缺點：每月只觸發 12 次，效益有限

### 方向 B：基於持倉天數的強制平倉
- 盤整策略持倉 > 5 個商品交易日 → 強制平倉
- 邏輯：mean reversion 5 天還沒發生 = alpha 信號可能失效

### 方向 C：實證對比
先做歷史回測對比：
- 變體 A：L3 v13.2B（無 RangeForceExit）→ 已知數據
- 變體 B：L3 + RangeForceExit 1200-1330 → 跑回測
- 變體 C：L3 + RangeForceExit 1200-1330 限定結算日 → 跑回測

**有歷史回測對比 + PF/MDD 改善 ≥ 5% 才考慮重新上架**。

---

## 七、目前 6 隻策略最終狀態

| 策略 | 版本 | Settlement_Flat | RangeForceExit | 三象限分類 |
|------|------|----------------|----------------|---------|
| L1 TrendLong | v2.6 + Settlement | ✅ 鎖利 | 無 | A Swing-Trend ★ |
| L2 TrendShort | 5.2 + Settlement | ✅ 兜底 | 無 | A Swing-Trend |
| L3 ConsolidationLong | **v13.4** | ✅ 兜底 | 無 | B Intraday-Mixed |
| L4 ConsolidationShort | **v14.4** | ✅ 兜底 | 無 | B Intraday-Mixed |
| L5 BreakoutLong | v19.8 + Settlement | ✅ 兜底 | 無 | A Swing-Trend（重新分類）|
| S1 NightMomentum | v2.7 + Settlement | ✅ 兜底 | 無 | Night-Leaky |

**所有驗證**：
- `verify_settlement_flat.py` 42/42 PASS ✅
- `verify_range_force_exit.py` 6/6 clean（反向驗證）✅
- `verify_all_live.py` 110/110 PASS ✅
- `verify_strategy_holding_classification.py` L1/L2/L5 PASS，L3/L4/S1 WARN（無法 PASS 因為它們確實是 Mixed/Leaky）

---

## 八、你的後續動作

1. **MC12 完全移除舊版 L3 v13.3.1 / L4 v14.3.1**
2. **從 v13.4 / v14.4 .pla 重新載入**
3. **確認 Inputs 沒有 `Range_ForceExit_Time` 與 `Range_ForceExit_End`**（這兩個欄位應消失）
4. **重跑回測，績效應該回到 v13.2B + Settlement / v14.2B + Settlement 的水準**
5. （選擇性）跑 `verify_strategy_holding_classification.py` 確認 L3/L4 仍是「Swing-Mixed 但 0 Settlement 觸發」狀態

---

## 九、相關文件
- [`docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`](SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) v1.2
- [`scripts/verify_range_force_exit.py`](../scripts/verify_range_force_exit.py)（反向化）
- 記憶：`feedback_mc_time_24hr_pitfall.md`
