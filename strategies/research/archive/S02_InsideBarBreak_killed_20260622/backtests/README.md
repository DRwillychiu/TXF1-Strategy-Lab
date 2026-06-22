# S2 InsideBarBreak Backtests 資料夾

**用途**：存放 S2 策略各版本的 MC 真實回測 xlsx 檔案。

**警告**：本資料夾建立於 2026-06-17，**目前空無一物**。
S2 從 v0.1 到 v0.4 從未有任何 MC 30M+Daily 真實回測紀錄。

詳見 [`../S2_backtest_journal.md`](../S2_backtest_journal.md)。

---

## 一、檔案命名規則

```
S2_<版本配置>_YYYYMMDD.xlsx
```

範例：
- `S2_v04_full_20260618.xlsx` ← v0.4 完整版（A+B+C 全 on）
- `S2_v03_replica_20260618.xlsx` ← v0.3 復刻（A off, B+C on）
- `S2_v02_replica_20260618.xlsx` ← v0.2 復刻（A+B+C 全 off）
- `S2_naive_20260618.xlsx` ← Naive 教科書版（全關 + 固定 offset）

---

## 二、4 個必跑版本的 input 配置

### v0.4 完整版（預設值）
**所有 _On 維持預設 true，BreakOffset_Mode = 1**

| Input | 值 |
|-------|---|
| BreakOffset_Mode | 1 |
| Confirm_On | true |
| VolFilter_On | true |
| BE_On | true |
| Trail_On | true |
| SP_On | true |
| Compression_On | true |
| BB_Filter_On | true |
| ATR_Filter_On | true |

### v0.3 復刻（A 系列關閉，B+C 開）
**改 A 系列 3 個開關為 false，其他保持 v0.4 預設**

| Input | 值 |
|-------|---|
| Compression_On | **false** |
| BB_Filter_On | **false** |
| ATR_Filter_On | **false** |
| 其他 | 同 v0.4 |

### v0.2 復刻（A+B+C 全關，動態 offset 仍開）

| Input | 值 |
|-------|---|
| BreakOffset_Mode | 1（動態）|
| Confirm_On | **false** |
| VolFilter_On | **false** |
| BE_On | **false** |
| Trail_On | **false** |
| SP_On | **false** |
| Compression_On | **false** |
| BB_Filter_On | **false** |
| ATR_Filter_On | **false** |

### Naive 教科書版（全關 + 固定 offset）

| Input | 值 |
|-------|---|
| BreakOffset_Mode | **0**（固定 5pt）|
| 其他 _On 全部 | **false** |

---

## 三、MC 回測共通設定

```
[ ] 商品: TXF1 (台指期近月連續)
[ ] Data1: 30 分鐘
[ ] Data2: 日線
[ ] 回測區間: 2020/01/01 ~ 今天
[ ] 初始資金: 1,000,000 NTD
[ ] 滑價: 1,000 NTD / 口（單邊 500）
[ ] 手續費: 30 NTD / 口
[ ] 期交稅: 內建（0.002%）
[ ] 進場張數: 1 口固定
[ ] 計算方式: 點對點（不含複利）
```

---

## 四、跑完後預期對比表

| 版本 | 樣本 | WR | PF | 淨利 | MDD | vs Naive 增量 |
|------|------|-----|-----|------|------|------------|
| Naive | TBD | TBD | TBD | TBD | TBD | baseline |
| v0.2 | TBD | TBD | TBD | TBD | TBD | + B-1 動態 offset |
| v0.3 | TBD | TBD | TBD | TBD | TBD | + B-2/3 + C 系列 |
| v0.4 | TBD | TBD | TBD | TBD | TBD | + A 系列 |

---

## 五、放入 xlsx 後我會做的事

1. 跑 `analyze_s2_phase2.py`（我會寫，等你 xlsx 來了立刻寫）
2. 產出對比報告，存於 `../S2_phase2_results_YYYYMMDD.md`
3. 更新 issue tracker（D / F / G / H / I 系列）
4. commit + push
5. 一起決定 Phase 3 路線

---

## 六、目前進度

| 版本 | xlsx 檔案 | 完成日 |
|------|----------|------|
| v0.4 完整 | ❌ 待跑 | — |
| v0.3 復刻 | ❌ 待跑 | — |
| v0.2 復刻 | ❌ 待跑 | — |
| Naive | ❌ 待跑 | — |

**進度：0/4**
