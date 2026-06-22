# S2 策略回測工作底稿（Backtest Journal）

**建立日**：2026-06-17
**目的**：誠實記錄 S2 各版本的回測狀態，避免「設計超前實證」的盲點
**重大警告**：**目前 0/4 個版本有 MC 30M+Daily 真實回測紀錄**

---

## 一、嚴重盲點承認

### 1.1 當前狀態

| 版本 | 設計完成日 | MC 30M+Daily 真實回測 | 唯一存在的「回測」|
|------|----------|------------------|---------------|
| v0.1 | 2026-06-07 | ❌ **無** | Python ^TWII 日線代理（34 筆 / PF 4.61）|
| v0.2 | 2026-06-17 | ❌ **無** | （模組化未跑回測）|
| v0.3 | 2026-06-17 | ❌ **無** | （B+C 改進未跑回測）|
| v0.4 | 2026-06-17 | ❌ **無** | （A 改進未跑回測）|

### 1.2 我犯的錯誤

**錯誤性質**：設計超前實證 4 個版本 = 危險的「**紙上談兵**」。

具體錯誤：
1. v0.2 模組化時沒要求用戶先跑 MC 確認 v0.1 在真實 30M 上的表現
2. v0.3 加 B+C 改進時，沒有 v0.2 baseline 可對比
3. v0.4 加 A 改進時，沒有 v0.3 baseline 可對比
4. **我引用了 4.61 PF 多次**，這是 Python 代理數字，不是 MC 真實
5. 我寫的「v0.3 預期 PF 1.5-2.5」「v0.4 預期 PF 2.0-2.8」全是**推測**，沒有實證支持

**結果**：我們有一隻 663 行代碼、32 個 input、50 個 variable 的策略，**但沒有任何一筆真實的 30M MC 回測**。

### 1.3 對照憲法 v1.2 規範

按 [`SETTLEMENT_DAY_DESIGN_CONSTITUTION.md`](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) 第四章 onboarding checklist：

```
任何 research → live_simulation 晉升必須回答：
[ ] 對策略 PF / MDD 的衝擊是否 < 5%？  ← 沒有 baseline 怎麼算衝擊？
```

**我違反了**「**input 調整必須重跑驗證**」的補充規則 5（憲法 v1.2）。

---

## 二、完整工作底稿應有的回測

### 2.1 必須建立的回測清單（按優先序）

#### 🔴 P0 - 立刻：v0.4 完整版（v0.3 B+C + v0.4 A 全 on）

**目的**：知道現在最完整版本的真實表現

| 設定 | 值 |
|------|---|
| 圖表 | Data1 = TXF1 30M / Data2 = TXF1 Daily |
| 回測區間 | 2020/01/01 ~ 2026/06/17 |
| 初始資金 | 1,000,000 NTD |
| 滑價 | 1,000 NTD / 口 |
| 手續費 | 30 NTD / 口 |
| Inputs | **預設值**（所有 _On = true）|

**預期輸出**：`backtests/S2_v04_full_20260617.xlsx`

#### 🔴 P0 - 並列：v0.3 復刻（B+C on, A off）

**目的**：分離 A 系列改進的單獨效果

| 設定變更 |
|---------|
| `Compression_On = false` |
| `BB_Filter_On = false` |
| `ATR_Filter_On = false` |
| 其他保持 v0.4 預設 |

**預期輸出**：`backtests/S2_v03_replica_20260617.xlsx`

**對比 P0 第一份**：算出 A 系列獨立貢獻
- 若 v0.4 PF > v0.3 PF → A 有效
- 若 v0.4 PF ≈ v0.3 PF → A 無效（過度過濾）
- 若 v0.4 PF < v0.3 PF → A 有害

#### 🟡 P1：v0.2 復刻（A+B+C 全 off）

**目的**：分離 B+C 系列改進的效果

| 設定變更 |
|---------|
| `Compression_On = false` |
| `BB_Filter_On = false` |
| `ATR_Filter_On = false` |
| `Confirm_On = false` |
| `VolFilter_On = false` |
| `BE_On = false` |
| `Trail_On = false` |
| `SP_On = false` |
| `BreakOffset_Mode = 1`（動態 BreakOffset 仍開）|

**預期輸出**：`backtests/S2_v02_replica_20260617.xlsx`

**對比 P0 第二份**：算出 B+C 系列獨立貢獻

#### 🟡 P1：Naive 教科書版（全部關閉）

**目的**：取得「**無任何過濾的基準 PF**」

| 設定變更 |
|---------|
| `Compression_On = false` |
| `BB_Filter_On = false` |
| `ATR_Filter_On = false` |
| `Confirm_On = false` |
| `VolFilter_On = false` |
| `BE_On = false` |
| `Trail_On = false` |
| `SP_On = false` |
| `BreakOffset_Mode = 0`（固定 5pt 偏移）|

**預期輸出**：`backtests/S2_naive_20260617.xlsx`

**對比意義**：殘餘 alpha 量化
- Naive PF > 1.0 → 母子線本身仍有殘餘 alpha
- Naive PF < 1.0 → alpha 已被市場消化，靠過濾才能賺

---

## 三、4 份回測的對比分析框架

跑完後將形成這張表：

| 版本 | 樣本 | WR | PF | 淨利 | MDD | 增量 alpha |
|------|------|-----|-----|------|------|----------|
| Naive | ? | ? | ? | ? | ? | baseline |
| v0.2 | ? | ? | ? | ? | ? | + B-1 dynamic offset |
| v0.3 | ? | ? | ? | ? | ? | + B-2/3 + C 系列 |
| v0.4 | ? | ? | ? | ? | ? | + A-1/2/3 |

**判定每個改進的價值**：

| 對比 | 結論 |
|------|------|
| v0.2 - Naive | B-1 動態 offset 的價值 |
| v0.3 - v0.2 | B-2/3 + C 系列的價值 |
| v0.4 - v0.3 | A 系列的價值 |
| v0.4 - Naive | 全部改進的累積價值 |

**若任一改進增量 < 0** → 該改進**有害**，應評估退回。

---

## 四、回測後的延伸分析

每份 xlsx 跑完後可以再做：

| 分析 | 目的 | 對應 issue |
|------|------|----------|
| 樣本年度分布 | 確認不集中在某年 | H-2 |
| Long vs Short 分布 | 拆兩個子集計算 | H-1 |
| 持倉天數分布 | 驗證 MTF 設計合理 | G-1, I-2 |
| MFE / MAE 統計 | TP/SL 倍率合理性 | I-1, I-3 |
| Settlement 觸發數 | 預期 ≤ 5% | 已驗證 |
| 與 L5 訊號重疊率 | 雙重曝險評估 | F-1 |
| 2022 熊市單獨 PF | 順風期外驗證 | D-5 |

**這些分析都需要實際 xlsx 才能做**。

---

## 五、檔案位置標準

### 5.1 建議資料夾結構

```
strategies/research/S02_InsideBarBreak/
├── backtests/                              ← ★ 新建
│   ├── README.md                           ← 命名規則 / 對比指引
│   ├── S2_v04_full_YYYYMMDD.xlsx           ← 你 MC 跑完放這
│   ├── S2_v03_replica_YYYYMMDD.xlsx
│   ├── S2_v02_replica_YYYYMMDD.xlsx
│   └── S2_naive_YYYYMMDD.xlsx
├── S2_InsideBarBreak.pla                   (策略代碼 v0.4)
├── S2_InsideBarBreak_strategy.md           (策略說明)
├── S2_InsideBarBreak_annotated.md          (註解)
├── S2_known_issues.md                      (Issue tracker)
├── S2_v03_design_spec.md                   (B+C 設計)
├── S2_v04_design_spec.md                   (A 設計)
├── S2_E_series_alpha_decay_analysis.md     (E 論證)
├── S2_phase2_validation_framework.md       (Phase 2 框架)
├── S2_backtest_journal.md                  (★ 本檔)
└── README.md
```

### 5.2 命名規則

`S2_<版本配置>_<YYYYMMDD>.xlsx`

範例：
- `S2_v04_full_20260618.xlsx` = 6/18 跑的 v0.4 完整版
- `S2_v03_replica_20260618.xlsx` = 同日跑的 v0.3 復刻
- `S2_v02_replica_20260618.xlsx` = 同日跑的 v0.2 復刻
- `S2_naive_20260618.xlsx` = 同日跑的 Naive

---

## 六、未來流程修正（避免再犯）

### 6.1 新規矩：「**設計 → 立刻回測 → 才能做下一個設計**」

```
v0.2 模組化 → MC 跑 → 確認 baseline 表現 → 才能設計 v0.3
v0.3 B+C   → MC 跑 → 確認 B+C 有效     → 才能設計 v0.4
v0.4 A     → MC 跑 → 確認 A 有效       → 才能設計 v0.5
```

**每次代碼修改後不跑 MC 回測 = 紙上談兵 = 違反實證精神**。

### 6.2 寫入憲法 v1.3 候選條款

```
條款 9（候選）：策略迭代必須伴隨 baseline 回測

任何策略每次 input 預設值變動或 logic 變動：
  1. 改動前必須有當前版本的 MC 真實回測 baseline
  2. 改動後必須立刻跑新的 MC 真實回測
  3. 必須產出「改動前 vs 改動後」對比報告
  4. 對比報告需 commit + push 後才能進行下一次迭代

違反 → 該迭代不計入版本歷史。
```

**S2 v0.2/v0.3/v0.4 的演化「違反」這個候選條款**，需要補回測補對比。

---

## 七、現階段唯一可信的數字

```
v0.1 績效（Python ^TWII 日線代理回測）：
  總交易    : 34 筆
  勝率      : 64.7%
  PF        : 4.61
  淨利      : +791,754 NTD
  MDD       : -64k NTD
  回測期間   : 2020-2026 (6.4 年)

  ⚠️ 警告：這不是 MC 30M 真實回測，是 Python 簡化模擬。
          所有 v0.2/v0.3/v0.4 的「預期改進」都基於此數字推測，
          沒有任何實證支持。
```

**這是唯一存在的回測資料**。

---

## 八、立刻要做的事

### 給用戶
1. **MC12 載入 v0.4 .pla**（從 `strategies/research/S02_InsideBarBreak/`）
2. **建立 4 個 input 配置**（v0.4 / v0.3 / v0.2 / Naive）
3. **依序跑回測，匯出 4 份 xlsx**
4. **放到 `backtests/` 子資料夾**（待建立）

### 給我（Claude）
1. ✅ 寫本檔（已完成）
2. ⏳ 建立 `backtests/` 子資料夾 + README
3. ⏳ 寫 `analyze_s2_phase2.py` 分析腳本（等用戶 xlsx 完成後再寫，避免再次「設計超前實證」）

---

## 九、未來進度追蹤

| 版本 | xlsx 檔案 | 完成日 | PF | WR | 樣本 |
|------|----------|------|-----|-----|------|
| v0.4 完整 | `S2_v04_full_*.xlsx` | ❌ 待跑 | — | — | — |
| v0.3 復刻 | `S2_v03_replica_*.xlsx` | ❌ 待跑 | — | — | — |
| v0.2 復刻 | `S2_v02_replica_*.xlsx` | ❌ 待跑 | — | — | — |
| Naive | `S2_naive_*.xlsx` | ❌ 待跑 | — | — | — |

**進度：0/4 完成**

---

## 十、誠實的反省

我為以下事情承擔責任：

1. **沒有在 v0.2 完成後立刻要求 MC 真實回測**
2. **在沒有 baseline 的情況下持續設計 v0.3 → v0.4**
3. **多次引用 PF 4.61 卻沒明確標註「Python 代理而非 MC 真實」**
4. **寫了大量「預期改進」論述卻沒實證支持**

但有以下值得保留的：

1. ✅ 設計層面的論證仍然有理論價值
2. ✅ 程式碼結構符合憲法 v1.2 規範
3. ✅ 所有 input 都 switch 化，方便 A/B 測試
4. ✅ 完整的 issue tracker / 設計規格 / E 論證文件
5. ✅ Phase 2 驗證框架已就位，等資料就能立刻分析

**修正之後就好**。下一步是補回測，不是繼續做更多沒實證的設計。

---

## 十一、相關文件

- [Issue tracker](S2_known_issues.md)
- [策略完整說明](S2_InsideBarBreak_strategy.md)
- [v0.3 設計規格](S2_v03_design_spec.md)
- [v0.4 設計規格](S2_v04_design_spec.md)
- [E 系列論證](S2_E_series_alpha_decay_analysis.md)
- [Phase 2 驗證框架](S2_phase2_validation_framework.md)
- [憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
