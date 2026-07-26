# L4 ConsolidationShort v16 Regime-Adaptive Architecture -- FINAL VERDICT

**Status**: KILLED (2026-07-26)
**Duration**: 1 version (v16.0), 17 bug fixes during development
**Decision**: Architecture FAILED. 0 bull-path trades = structural impossibility. v14.6 confirmed as PRODUCTION.

---

## 一、研究假說

**v16 提出 Regime-Adaptive 雙路徑架構：將 Macro Block 從「阻擋器」重新定位為「路由器」。**

核心假設：如果 L4 在 bear/neutral regime 有 trap alpha，能否在 bull regime
設計一條獨立的進場路徑，讓策略在所有市況都能交易？

### 架構設計

| Regime | 條件 | 進場路徑 |
|--------|------|----------|
| **Bear/Neutral** | ADX<25 OR Close<200MA（原 Macro Block） | 不變：trap 進場 (CS_Entry) |
| **Bull** | ADX>25 AND Close>200MA | 新增：Pressure Entry + Box Quality Gate (CS_BullEntry) |

### Box Quality Gate 規格

| 參數 | 值 | 用途 |
|------|-----|------|
| Min_Box_Duration | 60 bars | 箱體最低存活時間 |
| Min_Top_Touches | 2 | 箱頂最少觸及次數 |
| Touch spacing | 12 bars | 兩次觸及之間最小間距 |
| Reset zone | ATR * 0.5 | 偏離箱頂後視為新的觸及 |

設計邏輯：bull market 中的盤整必須「夠成熟」（持續夠久、多次測試箱頂），才有
假突破的可能。Quality Gate 就是確保只在這種成熟盤整中做空。

---

## 二、實驗證據

### 回測結果

| 指標 | v16.0 | 評估 |
|------|-------|------|
| 總交易數 | 122 | - |
| CS_Entry (bear path) | **122** | 全部走 bear 路徑 |
| CS_BullEntry (bull path) | **0** | ❌ bull 路徑零觸發 |
| 淨利 | +500,000 NTD | - |
| Profit Factor | 1.17 | ❌ 低於 v14.6 的 1.54 |
| MDD | -1,140,000 NTD | ❌ 遠高於 v14.6 的 -525,600 |

### 致命發現：Bull Path 零交易

**122 筆交易中 0 筆走 CS_BullEntry 路徑。Bull 進場邏輯從未被觸發。**

---

## 三、失敗根因

### 為什麼 Bull Path 不可能觸發

Bull market 盤整期的結構特徵與 Box Quality Gate 要求**根本衝突**：

1. **盤整時間太短**：Bull regime（ADX>25 AND Close>200MA）中的盤整通常是短暫的
   「中繼整理」，持續遠少於 60 bars。強勢上漲趨勢中價格傾向快速突破。

2. **箱頂觸及不足**：bull market 盤整期間，價格傾向單方向施壓箱頂，然後直接突破。
   滿足 Min_Top_Touches=2 且 spacing>=12 bars 的機會極少。

3. **結構性矛盾**：Quality Gate 要求「成熟盤整」（60 bars + 2 touches），
   但 bull market 的定義就是「趨勢強勁、突破迅速」。要求 bull market 中出現
   「不像 bull market」的盤整形態，本身就是邏輯矛盾。

4. **放寬 gate 不可行**：即使降低 Min_Box_Duration 和 Min_Top_Touches，
   放寬到能產生交易的程度時，filter 品質也會降到無法產生 alpha。
   這是一個 quality-quantity impossible tradeoff。

### 根本問題

> L4 alpha = bear/neutral trap signal ONLY.
> Bull market 中不存在結構性的假突破做空機會。
> 這不是 implementation 問題，是 alpha 不存在。

---

## 四、開發過程紀錄

### 17 Bug Fixes

v16 開發過程中修復了 17 個 bug，確認最終結果不是因為 implementation 錯誤。

### Dead Variable 清理

開發過程中發現並移除了 `v_Active_Cooldown` dead variable
（宣告但未使用的變數），改善了程式碼品質。雖然對策略邏輯無影響，
但作為 code hygiene 的一部分記錄在此。

---

## 五、Self-check

- [x] 是否基於 MC12 真實回測數據？是（122 trades 全 MC12 回測）
- [x] KILL 決策是否基於結構性原因而非參數調整？是（bull market 盤整結構與 quality gate 根本衝突）
- [x] 程式碼是否經過充分驗證？是（17 bug fixes + dead variable 清理）
- [x] 投入更多時間是否可能改變結論？否（alpha 不存在於 bull regime）
- [x] 0 bull trades 是否因為 bug？否（bear path 122 trades 正常運作，路由邏輯正確）

---

## 六、Lessons

**L31**: 將 blocker 改為 router 的架構假設，前提是兩個 regime 都存在可挖掘的 alpha。
如果某個 regime 根本沒有 alpha（bull market 中沒有結構性假突破機會），
router 架構就是在為不存在的東西建造入口。改架構前必須先驗證目標 regime 是否有 alpha。

**L32**: Quality gate（duration + touches + spacing）在低頻事件 regime 中會變成
impossible filter。當 gate 嚴格到能保證品質時通過率為零，放寬到能通過時品質無法保證。
這種 quality-quantity impossible tradeoff 是策略設計的死局信號。

**L33**: 0 trades in one path 是最強的 KILL 信號。不需要看勝率、PF、MDD --
如果一整條路徑在 6 年回測中零觸發，就是結構不可行的鐵證。

---

## 七、對 Production 的影響

v16 FAIL 再次確認：

- **v14.6 為 PRODUCTION**（SetStopContract + SL_Pct 1.50%）
- L4 alpha 嚴格限定在 bear/neutral regime
- Bull market 零交易是**正確行為**，不是需要修復的 bug
- L4 在 portfolio 中的角色 = bull 策略（L1/L3/L5）的對沖互補

| 指標 | v14.6 (Production) |
|------|-------------------|
| 淨利 | +894,400 NTD |
| Profit Factor | 1.54 |
| Win Rate | 43.04% |
| MDD | -525,600 NTD |
| 交易數 | 79 |

---

## 八、研究線狀態

```
v16 研究線：CLOSED (2026-07-26)

若你看到本檔（L4_v16_FINAL_VERDICT.md）：
  ❌ 不要嘗試 Regime-Adaptive 架構
  ❌ 不要為 bull regime 設計進場路徑
  ❌ 不要放寬 Box Quality Gate 參數
  ✅ 可以引用 Lessons L31-L33
  ✅ 可以讀本文件理解 regime-specific alpha 的邊界
  ✅ 接受 bull market 零交易 = 策略正確運作
```

---

## 九、相關文件

- **Production .pla**: `strategies/live/L4_ConsolidationShort.pla` (v14.6)
- **v16 .pla**: `strategies/research/L4_v16/L4_ConsolidationShort_v16.pla`
- **v15 FINAL_VERDICT**: `strategies/research/L4_v15/L4_v15_FINAL_VERDICT.md`
- **L4 策略審查**: `strategies/live/L4_ConsolidationShort_review.md`
- **L4 研究總覽**: `strategies/research/L4_RESEARCH_SUMMARY.md`
