# S2 Phase 2 驗證框架

**寫於**：2026-06-17（v0.4 完成同日）
**目的**：等用戶 MC 30M 真實回測完成後，立即套用的「分析模板」
**前置**：S2 v0.4 .pla 已部署到 MC12 並跑完回測
**輸入**：MC 匯出的 xlsx 績效報告（放 `C:/Users/User/Downloads/`）

---

## 一、Phase 2 七大驗證任務

### 任務 1：基礎績效指標確認

對照 [`S2_E_series_alpha_decay_analysis.md`](S2_E_series_alpha_decay_analysis.md) 中的預測：

| 指標 | v0.1 Python | v0.4 MC 預期（中性）| 通過門檻 |
|------|----------|----------|--------|
| 總筆數 | 34 | 12-24（v0.4 嚴格）/ 40-60（v0.4 寬鬆）| ≥ 30 |
| WR | 64.7% | 55-70% | ≥ 50% |
| **Profit Factor** | 4.61 | **2.0 - 2.8** | **≥ 1.5** |
| 淨利 | +791k | +200k - +800k | > 0 |
| MDD | -64k | -50k ~ -150k | < 帳戶 30% |
| 平均單筆獲利 | +45k | +20k ~ +50k | > 0 |
| 平均單筆虧損 | -18k | -10k ~ -25k | < 平均獲利 |
| 盈虧比 | 2.51 | 1.5 - 2.5 | > 1.3 |

**通過判定**：
- ✅ 全綠 → 進 Phase 3
- ⚠️ 任一黃燈 → 深入檢視
- ❌ PF < 1.5 → 評估是否 archive

### 任務 2：A/B 對比測試（殘餘 alpha 驗證）

**在 MC 上分 4 次跑回測**，每次調整 input：

| 配置 | 設定 | 預期 PF |
|------|------|---------|
| **Naive 教科書版** | 全部 _On = false, BreakOffset_Mode = 0 | < 1.2 |
| **v0.3 復刻** | 只關 A 系列 (Compression/BB/ATR _On = false) | 1.5 - 2.0 |
| **v0.4 完整** | 全部預設（A+B+C 都開） | 2.0 - 2.8 |
| **只開 A** | 只 A _On = true，B/C 全 false | 1.8 - 2.5 |

**判定**：
- v0.4 > v0.3 > Naive → **三層改進都有效**
- v0.3 > v0.4 → **A 系列過度過濾，需調寬**
- 全部接近 → **alpha 已被市場消化**

### 任務 3：樣本品質分析

讀 xlsx 交易明細，逐筆檢查：

```python
# 預備分析腳本概念
import pandas as pd

df = pd.read_excel(xlsx_path, sheet_name='交易明細')

# 統計每年訊號數
df['Year'] = df['進場日'].dt.year
yearly_count = df.groupby('Year').size()

# 統計每月訊號數
df['YearMonth'] = df['進場日'].dt.to_period('M')
monthly_count = df.groupby('YearMonth').size()

# Long vs Short 分布
long_pct = (df['類型'].str.contains('Long')).mean()

# 持倉天數分布
df['Holding_Days'] = (df['出場日'] - df['進場日']).dt.days
holding_dist = df['Holding_Days'].value_counts().sort_index()
```

**關鍵問題**：
- 每年訊號是否均衡？（不能集中在某年）
- Long vs Short 是否對稱？（< 30% 不對稱 = OK，> 50% = 不對稱）
- 持倉天數分布是否合理？（多數應 1-3 天）

### 任務 4：MFE / MAE 分析（解決 I-1, I-2, I-3）

從 xlsx 「最大可能獲利 / 虧損」欄位：

```python
df['MFE'] = df['最大可能獲利(¤)']
df['MAE'] = df['最大可能虧損(¤)']
df['Realized'] = df['獲利(¤)']

# 進場後行情走勢分析
mfe_p90 = df['MFE'].quantile(0.9)   # 90% 交易的最高有利移動
mae_p90 = df['MAE'].quantile(0.1)   # 10% 交易的最差不利移動

# Capture rate (實現獲利 / 最大可能獲利)
df['Capture_Rate'] = df['Realized'] / df['MFE']
winners_capture = df[df['Realized'] > 0]['Capture_Rate'].mean()

# 解讀
# Capture > 0.8 → TP/Trail 接得很好
# Capture < 0.4 → 太早出場（TP 設太近）
```

**對 C 系列驗證**：
- BE 是否「打到」？（看 LX_IB_BE / SX_IB_BE 標籤次數）
- Trail 是否「打到」？（看 LX_IB_Trail 次數）
- SP 是否「打到」？（看 LX_IB_SP 次數）
- 如果三者都 0 觸發 → C 系列無效

### 任務 5：Settlement 觸發驗證

延用 [`scripts/analyze_settlement_backtest.py`](../../../scripts/analyze_settlement_backtest.py) 邏輯：

```python
# 標記結算日交易
df['is_settlement_day'] = df['出場日'].apply(
    lambda d: d.weekday() == 2 and 15 <= d.day <= 21
)

settlement_exits = df[df['出場訊號'].str.contains('Settlement')]
print(f"S2 Settlement 觸發: {len(settlement_exits)}")
```

**預期**：
- Settlement 觸發 ≤ 5%（S2 持倉 1-3 天，撞結算日機率約 1/22 = 4.5%）
- 若 > 10% → 持倉時間設計需檢視

### 任務 6：與 L5 訊號重疊度（F-1 預備）

需要 S2 + L5 兩份 xlsx 對比：

```python
s2_df = pd.read_excel('S2.xlsx', sheet_name='交易明細')
l5_df = pd.read_excel('L5.xlsx', sheet_name='交易明細')

# 取 S2 Long 進場日
s2_long_dates = set(s2_df[s2_df['類型'].str.contains('Long')]['進場日'])
l5_long_dates = set(l5_df['進場日'])

overlap = s2_long_dates & l5_long_dates
overlap_rate = len(overlap) / max(len(s2_long_dates), 1)

print(f"S2 vs L5 多單重疊率: {overlap_rate:.1%}")
```

**判定**：
- < 20% → S2 與 L5 互補，可同時上架
- 20-50% → 部分重疊，需評估雙重曝險
- > 50% → **建議 S2 改為 Short-only**

### 任務 7：2022 熊市單獨檢驗

```python
df_2022 = df[df['進場日'].dt.year == 2022]
pf_2022 = ...
mdd_2022 = ...

print(f"2022 PF: {pf_2022}")
print(f"2022 MDD: {mdd_2022}")
```

**判定**：
- 2022 PF > 1.2 → 通過熊市考驗
- 2022 PF < 1.0 → 策略可能只在順風期 work

---

## 二、回測前 MC 設定 checklist

執行 MC 回測前確認：

```
[ ] MC12 已完全移除舊版 S2（如有）
[ ] 從 strategies/research/S02_InsideBarBreak/S2_InsideBarBreak.pla 載入
[ ] 圖表設定：Data1 = TXF1 30M / Data2 = TXF1 Daily
[ ] 回測區間：2020/01/01 ~ 2026/06/17
[ ] 初始資金：1,000,000 NTD
[ ] 滑價：每口 1,000 NTD（500 單邊 × 2）
[ ] 手續費：每口 30 NTD
[ ] 期交稅：0.002%（已內建）
[ ] Inputs 確認：32 個 inputs 全部出現
[ ] Inputs 預設值：所有 _On = true（v0.4 完整版）
[ ] 進場張數：1 口固定
```

## 三、要產出的回測 xlsx

**至少 4 份 xlsx**（A/B 對比用）：

| 檔名 | 設定 |
|------|------|
| `S2_v04_full.xlsx` | v0.4 預設（A+B+C 全 on）|
| `S2_v03_replica.xlsx` | A 全 off（A+B+C 中只 B+C 開）|
| `S2_v02_replica.xlsx` | A+B+C 全 off（v0.2 純原版）|
| `S2_naive.xlsx` | A+B+C 全 off + BreakOffset_Mode=0 |

---

## 四、回測完成後立即執行的命令

```bash
# 1. 把 4 份 xlsx 放到 Downloads
# 2. 跑分析腳本（待寫）
cd C:/Users/User/Desktop/TXF1-Strategy-Lab
python scripts/analyze_s2_phase2.py

# 3. 預期輸出：
#    - 基礎績效對比表
#    - A/B 對比結論
#    - 樣本品質分析
#    - MFE/MAE 統計
#    - Settlement 觸發確認
#    - 與 L5 重疊率（若有 L5 xlsx）
#    - 2022 熊市單獨表現
```

---

## 五、決策樹：Phase 2 結果 → 下一步行動

```
                    MC 跑完 v0.4 完整版
                            │
                ┌───────────┼───────────┐
                │           │           │
         PF > 2.5     PF 1.5-2.5    PF < 1.5
                │           │           │
                ↓           ↓           ↓
          進 Phase 3   進 Phase 3   評估是否 archive
          做 P1-P3     A/B 對比      ↓
          嚴謹驗證     必驗證       ┌─────┴─────┐
                                   │           │
                              v0.3>v0.4    v0.3≈v0.4
                                   │           │
                                   ↓           ↓
                              退回 v0.3     archive
                              再 Phase 2    寫 alpha 已耗盡報告
```

---

## 六、預期工作分工

| 步驟 | 負責 |
|------|------|
| 1. MC 載入 v0.4 + 跑 4 份回測 | **你** |
| 2. 匯出 xlsx 到 Downloads | **你** |
| 3. 寫 `analyze_s2_phase2.py` 分析腳本 | 我 |
| 4. 跑腳本 + 寫 Phase 2 分析報告 | 我 |
| 5. 根據結果決定 Phase 3 或 archive | 我們一起 |

---

## 七、相關文件

- [E 系列論證](S2_E_series_alpha_decay_analysis.md)
- [v0.4 設計規格](S2_v04_design_spec.md)
- [Issue tracker](S2_known_issues.md)
- [Settlement 分析腳本參考](../../../scripts/analyze_settlement_backtest.py)
