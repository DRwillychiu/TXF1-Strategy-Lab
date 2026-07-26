# L4 ConsolidationShort v15 Macro Block Modification -- FINAL VERDICT

**Status**: KILLED (2026-07-26)
**Duration**: v15.0 + v15.1 + v15.1 optimized (3 sub-experiments)
**Decision**: All v15 experiments FAILED. v14.6 confirmed as PRODUCTION.

---

## 一、研究假說

**v15 系列試圖改善 L4 的 Macro Block（regime filter），尋找更好的進場條件。**

兩個方向：
1. **v15.0**：收緊 Macro Block 邏輯（OR → AND），測試是否能提升信號品質
2. **v15.1**：新增 Pressure Zone 進場路徑，擴展策略觸發場景

---

## 二、實驗證據

### v15.0: Macro Block OR → AND 修改

| 項目 | 修改前 (v14.6) | v15.0 | 變化 |
|------|----------------|-------|------|
| Macro Block 邏輯 | ADX<25 **OR** Close<200MA | ADX<25 **AND** Close<200MA | 收緊 |
| 淨利變化 | baseline | **-41.8%** | ❌ 嚴重惡化 |

**結論**：OR 條件是 load-bearing regime filter。ADX<25（盤整市）和 Close<200MA（空頭市）
是兩個獨立的 alpha 來源，缺一不可。改 AND 等於砍掉一半有效交易場景。

### v15.1: Pressure Zone 進場

| 項目 | 內容 |
|------|------|
| 進場條件 | Price < Box_Bottom - ATR * 0.4 + 陽線確認 |
| 概念 | 價格跌破箱底壓力區後反彈進場 |
| 結果 | 淨負（net negative） |

**結論**：Pressure Zone 進場本質上是 mean-reversion 邏輯，與 L4 的 trap-based alpha
（假突破反轉）互斥。L4 賺錢靠的是「被騙的人停損出場推動價格回歸」，不是「跌深反彈」。

### v15.1 Optimized: MC Sweep 參數空間搜索

| 項目 | 內容 |
|------|------|
| 方法 | MC sweep 掃描 Pressure Zone 所有參數組合 |
| 搜索空間 | ATR 乘數、陽線定義、偏移距離 |
| 結果 | **整個參數空間無 sweet spot** |

**結論**：不是參數沒調好，是 Pressure Zone 進場與 L4 alpha 結構不相容。
全參數空間搜索排除了「只是沒找到對的參數」的可能性。

---

## 三、失敗根因

**L4 alpha = bear/neutral market trap signal ONLY.**

1. Macro Block OR 條件覆蓋兩個獨立 regime（盤整 + 空頭），收緊為 AND 等於自廢武功
2. Trap-based alpha 的機制是：其他交易者被假突破誘騙 → 停損出場 → 推動價格反轉
3. Pressure Zone 進場不觸發這個機制 -- 沒有「被騙的人」提供反轉動力
4. 對 L4 進場條件的任何修改都會破壞這個精密的 trap 結構

---

## 四、Self-check

- [x] 是否基於 MC12 真實回測數據？是（v15.0 -41.8% 來自 MC12 回測）
- [x] KILL 決策是否基於結構性原因而非參數調整？是（OR 是 load-bearing、Pressure Zone 與 alpha 互斥）
- [x] 是否有足夠多的子實驗排除偶然？是（3 個子實驗 + 全參數空間 sweep）
- [x] 投入更多時間是否可能改變結論？否（根因是結構性的）

---

## 五、Lessons

**L28**: Regime filter 中的 OR 條件不可輕易改為 AND。當 OR 連接的是兩個獨立 alpha
來源（盤整 regime + 空頭 regime），收緊為 AND 會切斷其中一個來源，導致大幅淨利下降。
修改 regime filter 前必須先理解每個分支獨立貢獻的 alpha。

**L29**: Trap-based alpha 與 mean-reversion alpha 是互斥的進場邏輯。Trap 靠的是
「其他交易者被誘騙後停損推動反轉」，mean-reversion 靠的是「跌深反彈」。
混合兩種邏輯不會擴展 alpha，反而稀釋信號品質。

**L30**: 全參數空間 sweep 結果為零 sweet spot 時，問題出在邏輯結構而非參數值。
此時應立即 KILL 該方向，不要繼續微調。

---

## 六、對 Production 的影響

v15 全系列 FAIL 確認：

- **v14.6 為 PRODUCTION**（SetStopContract + SL_Pct 1.50%）
- Macro Block OR 條件不可修改
- 進場邏輯不可擴展（trap 進場是唯一有效路徑）

---

## 七、研究線狀態

```
v15 研究線：CLOSED (2026-07-26)

若你看到本檔（L4_v15_FINAL_VERDICT.md）：
  ❌ 不要修改 Macro Block OR 條件
  ❌ 不要新增 Pressure Zone 進場
  ❌ 不要對 v15 做任何延伸實驗
  ✅ 可以引用 Lessons L28-L30
  ✅ 可以讀本文件理解 Macro Block 結構
```

---

## 八、相關文件

- **Production .pla**: `strategies/live/L4_ConsolidationShort.pla` (v14.6)
- **v15 .pla**: `strategies/research/L4_v15/L4_ConsolidationShort_v15.pla`
- **L4 策略審查**: `strategies/live/L4_ConsolidationShort_review.md`
- **v16 FINAL_VERDICT**: `strategies/research/L4_v16/L4_v16_FINAL_VERDICT.md`
- **L4 研究總覽**: `strategies/research/L4_RESEARCH_SUMMARY.md`
