# S2 InsideBarBreak — FINAL VERDICT

**結案日**：2026-06-21
**狀態**：📁 **ARCHIVED FINAL**（從 SUSPENDED 升級為正式結案）
**用戶決策**：2026-06-21（30M 實證 + 接受結果後選擇結案）

---

## 一、結案決策

**S2 InsideBarBreak（母子線突破）正式結案，alpha 已確認死亡。**

從 2026-06-20 RESEARCH SUSPENDED 升級為 ARCHIVED FINAL。檔案保留供 reference 與教訓延續，**未來不再投入開發資源**。

---

## 二、2026-06-21 新增證據（結案直接觸發）

### 30M 版本實證結果

用戶在 2026-06-21 跑了 **30 分鐘 timeframe Naive Long-only** 配置（試圖透過拉長 timeframe 提升樣本品質），結果：

| 指標 | 30M Naive | v0.6 5M | 變化 | 評估 |
|------|-----------|---------|------|------|
| 淨利 | **+48,400** NTD | +48,000 NTD | 持平 | ❌ |
| **PF (毛)** | **1.057** | 1.057 | **完全一致** | ❌ alpha 結構不變 |
| **PF (含滑價)** | **-0.77** | -0.93 | 都負 | ❌ 結構性虧損 |
| 交易筆數 / 年 | **14** | 9 | +56% | ✓ 樣本提升 |
| **勝率** | **42.86%** | — | < 50% | ❌ |
| 最大策略虧損 | **-25.08%** | — | 接近 30% 警戒 | ⚠️ |
| **年化夏普** | **-0.042** | — | **負值** | ❌ |
| 帳戶年化報酬 | 0.80% | 0.85% | < 通膨 | ❌ |
| **對比 Buy & Hold** | 落後 **59×** | 落後 56× | 略差 | ❌ |

### Exit 原因分布（致命診斷）

| 出場原因 | 佔比 | 解讀 |
|---------|------|------|
| LX_IB_Time | **42%** | ❌ 進場後不動 = follow-through 失效 |
| LX_IB_SL | **37%** | ❌ 突破後被打回 = fakeout 比例極高 |
| LX_IB_TP | **19%** | ❌ 真正成功只 19% |
| LX_IB_Settlement | 2% | OK |

**TP : SL : Time = 19% : 37% : 42% = 典型 alpha 死亡型態**

---

## 三、Alpha 死亡確認（多重證據）

### 跨 timeframe 一致性
- **5M v0.6 PF 1.057**
- **30M Naive PF 1.057**
- 換 timeframe 不解決 → **不是 timeframe 問題，是 alpha 本質衰減**

### 跨年穩定性 vs 收益
- 30M 跨年分布：2020-16 / 2021-14 / 2022-8 / 2023-14 / 2024-12 / 2025-18 / 2026-2
- 跨年穩定（不像 S3 v1.1 集中 2026）
- **但每年都不賺錢** — alpha 結構性消失

### 5 個迭代版本實證歷史
| 版本 | 主要改動 | 結論 |
|------|---------|------|
| v0.2 (Naive) | 從 archive 拉出基線 | PF ~1.0 |
| v0.3 (B+C) | 加假突破過濾 + 4 層 SL | 沒救 |
| v0.4 (A) | 加波動率壓縮量化 | 0 進場（VolFilter 元兇）|
| v0.5 | Long-only + TargetMult 1.0 | PF 1.057 |
| v0.6 | B 修正 + MaxDailyEntries | 持平 |
| **30M** | 拉長 timeframe | **持平** |

→ **6 個迭代 + 2 個 timeframe + 8 個 filter 系列 = 全部證實沒有可挖掘 alpha**

### 機構級不可接受
- PF 含滑價 -0.77 → 滑價成本吃掉所有毛利
- Sharpe -0.042 → 比現金還差
- 落後 B&H 59× → 機構絕對不會配置
- 同期 L1/L5 Long-only 都遠遠贏過 → alpha 不在母子線

---

## 四、根本原因（理論層面）

**母子線突破是教科書級公開策略**：
- 任何技術分析教材都教
- 2020-2026 全市場玩家都看得到
- Algo / quant fund 早已大量套利
- **Alpha 已被市場效率消化**

→ 公開策略 alpha 衰減是必然，不是 implementation 問題

---

## 五、13 個 Lessons 永久保留

從 S2 失敗演化中提煉的 13 個教訓**永久寫入 memory 指導未來策略開發**：

1. Python 日線代理 PF 不可信
2. 設計超前實證 = 紙上談兵
3. MC Time 24-hour 必須閉區間
4. **突破類策略 → Long-only 是常態** ⭐
5. **教科書公開策略 alpha 已大幅衰減** ⭐
6. MC12 input persistence 必須完全移除重載
7. MTF 設計前先驗證持倉天數
8. TP 倍率必從 MFE 統計推導
9. 過濾類 input 必須驗證歷史通過率
10. 同日多進場需 cooldown
11. **Buy and Hold 是現實檢驗** ⭐
12. 4 次設計迭代 + 0 實證 = 警訊
13. **新 filter 必須做重疊度 + 通過率雙重檢查** ⭐

**這 13 個教訓比 S2 本身更有價值**。S3/S4/S5... 都將受惠。

---

## 六、Archive 規範

```
若你看到本檔（S2_FINAL_VERDICT.md）：
  ❌ 不要修改 S2 任何代碼
  ❌ 不要跑 S2 回測
  ❌ 不要寫 S2 新版本
  ✅ 可以讀文件參考設計思路（especially 13 lessons）
  ✅ 可以引用 13 個教訓
  ❌ 「重啟條件」已從 SUSPENDED 的 3 條收緊為:
     ONLY IF 新研究顛覆性證明母子線在 TXF1 仍有可挖掘 alpha
     （門檻：發表於 SSRN / arXiv 的 peer-review-level 研究）
```

---

## 七、資源轉向

S2 結案釋放出的開發資源 → 直接投入：

**S4 TurnOfMonth_Long**（calendar effect 月末做多）
- Sharpe-additive 最高（ρ ≈ 0 與其他策略）
- 複雜度最低（純 calendar 邏輯 ~150 LOC）
- 預期 12 trades/yr × 6.5 年 = ~78 trades 充足樣本
- 路徑：`strategies/research/S04_TurnOfMonth/`

---

## 八、相關文件交叉參考

- **30M 證據檔**（用戶 Downloads）：
  `C:\Users\User\Downloads\TXF1  InsideBarBreak_30M 策略回測績效報告.xlsx`
- **歷史 SUSPENDED 文件**：[STATUS_SUSPENDED.md](STATUS_SUSPENDED.md)
- **完整 S2 工作底稿**：[S2_backtest_journal.md](S2_backtest_journal.md)
- **Alpha 衰減論證**：[S2_E_series_alpha_decay_analysis.md](S2_E_series_alpha_decay_analysis.md)
- **12 月 roadmap**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **下一個策略 S4**：[../S04_TurnOfMonth/](../S04_TurnOfMonth/)

---

## 九、用戶聲明

> 「A，結案後，立即朝 S4 前進」  
> — 2026-06-21 ultracode session

S2 從研究歷史中正式畢業。alpha 已死，但 13 lessons 永生。
