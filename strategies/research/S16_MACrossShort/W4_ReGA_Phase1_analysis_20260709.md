# S16_S v0.3-P0FIX Phase 1 GA — Critical Analysis

**Date**: 2026-07-09
**Strategy**: v0.3-P0FIX (P0 bugs F1/F2/F3 fixed)
**Sweep**: ~260 combinations (Fast × Slow × Slope × QuickStop_MaxLoss)
**Verdict**: 🚨 **STRUCTURAL FAILURE — All combinations negative**

---

## 一、Headline

**每一個組合都虧錢**。從 top rank 到 bottom rank 沒有任何一個 candidate 通過任何 Rule #13 gate。

| Rank | Combo | Net | PF | MDD $ | WR% | Trades |
|------|-------|-----|-----|--------|-----|--------|
| **Best** | F14/S44/Slope8/QS40 | **-698K** | 0.947 | -1,660K | 24.5% | 2569 |
| Top 2 | F14/S44/Slope7.5/QS40 | -897K | 0.936 | -1,828K | 24.6% | 2771 |
| Top 3 | F14/S34/Slope8/QS15 | -1,108K | 0.919 | -1,901K | 22.9% | 2809 |
| ... | ... | ... | ... | ... | ... | ... |
| Worst | F14/S30/Slope7.5/QS30 | **-3,122K** | 0.816 | -3,611K | 24.7% | 3190 |

**Compare Rule #13 gates**：
- **MDD < 30% 帳戶（-300K）** → 0/260 pass
- **PF > 1.0** → 0/260 pass
- **Net > 0** → 0/260 pass
- **WR > 30%** → 0/260 pass

---

## 二、Sweep Range 觀察

從 xlsx 前 260 rows 反推 sweep 值：

| 參數 | Sweep 值 | 我原本建議 | 差異 |
|------|---------|----------|------|
| Fast | 10, 11, 12, 13, 14, 15 | 10, 12, 15 | ✅ 對齊 |
| Slow | 30, 34, 36, 38, 40, 42, 44, 46, 48, 50 | 30, 50 | 比建議廣 |
| **MinSlope** | **5.5, 6, 6.5, 7, 7.5, 8** | **0.5, 1, 2, 3, 5, 8** | 🚨 **只 sweep 我建議的最高 1/6 範圍** |
| QuickStop_MaxLoss_Pts | 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80 | 15, 30, 50, 80 | 更細但 range 對 |

**MinSlope 5.5-8 太嚴** — 我原本建議 0.5-8 完整 range，但 MC12 只跑 5.5-8。

---

## 三、根本原因診斷（F2 fix 後語意變更）

### F2 fix 前後對比

```
OLD (v0.1-DRAFT):
  v_Slope = AbsValue(v_ZLEMA_Slow - v_ZLEMA_Slow[1])
  = 任意方向的 Slow 斜率絕對值
  = 遲鈍（Slow ZLEMA 反應慢）+ 方向盲（漲跌都算）

NEW (v0.3-P0FIX):
  v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast
  = Fast ZLEMA 每 K 下跌點數
  = 敏銳 + 定向（只算下跌）
```

### 5M TXF1 上 Fast ZLEMA(15) delta-per-bar 統計估算

| Percentile | Slope 值 | 意義 |
|-----------|--------|------|
| Median | ~0.5-1 pt | 「典型」 |
| 75th | ~2-3 pts | 「明顯移動」 |
| 90th | ~5-6 pts | 「強烈移動」 |
| **95th** | **~8-10 pts** | **「極端事件」** |
| 99th | ~15-20 pts | 「崩盤級」 |

**當前 sweep 5.5-8 全部落在 85-95th percentile** → **只在極端下跌時進場**

---

## 四、為何全部虧錢？（結構分析）

### 觀察每組合的 signature

```
Trades: 2000-4500  (高頻，非設計預期 50-80/年)
WR:     20-26%     (遠低於 W0 daily proxy 45.8%)
Avg Win: 17-20K   (正常)
Avg Loss: -5.5 to -7.5K  (太小，被 M5 快速砍)
Win/Loss ratio: 2.4-3.2 (看起來 OK)
PF: 0.82-0.95  (整體虧損)
```

**問題結構**：
- **進場太多**（2000-4500 trades in 6.5 years = ~300-700/年，甚至比預期 50-80 多 5-10 倍）
- **WR 太低**（20-26% vs W0 期望 45%）
- **平均虧損被 M5 QuickStop 限制在 -5-7K**（每筆 -25-35 pts 而已）
- **但發生太頻繁** → 累積虧損爆表

### 意味著

**Slope 5.5-8 filter 沒有真正阻擋噪音，反而只在「已經噪音爆表的時候」進場，然後被 whipsaw 砍**。

**設計核心矛盾**：
- ZLEMA(15) 用來抓 5M 上動能 → 但延遲太少 → 每個小波動都觸發
- Slope filter 想擋噪音 → 但抓太高 threshold → 只在極端動能時 fire → 極端動能 = 高機率 V 轉

---

## 五、3 條可能路徑

### 路徑 A — **Phase 2 Re-Sweep with LOWER MinSlope**（**推薦，快速驗證**）

**理由**：Phase 1 只 sweep 我建議 range 的最高 1/6。可能低 Slope 值有 sweet spot。

**Sweep 建議**：
```
Fast:        12, 15
Slow:        30, 40, 50
MinSlope:    0.5, 1, 1.5, 2, 3  ← 極端 lower range
QuickStop_MaxLoss_Pts: 50, 80, 120  ← 更寬鬆讓 profit 發展
```
- 組合數：2 × 3 × 5 × 3 = **90 組合**（1 小時 MC12）

**預期**：
- 若找到 Net > 0：確認 sweet spot 在 low Slope
- 若仍全負：**結構性 alpha 缺失** → 進路徑 B 或 C

---

### 路徑 B — **深度診斷：Slope 分布統計**（更嚴謹）

**方法**：寫 Python 腳本讀 TXF1 5M 資料，實測 ZLEMA_Fast delta 分布。

**產出**：
- Slope 每個 percentile 的實際值
- 找到「Slope filter 過 X% bars」的對應 threshold
- 給精準的 GA sweep range

**時間**：需要 5M 資料（我們目前沒有）+ 30 分鐘分析

**限制**：我們沒 5M 資料，只能用 daily 估算或請你 export

---

### 路徑 C — **回退 F2 fix**（如果 A/B 都失敗）

**假設**：F2 fix 本身雖然邏輯正確（原本方向盲確實錯），但 **AbsValue 語意在實戰上恰好抓對了 alpha**（可能因為 TXF1 空頭常伴隨大反彈，抓「動能絕對值」比抓「方向」更有效）。

**回退 code**：
```pla
v_Slope = AbsValue(v_ZLEMA_Slow - v_ZLEMA_Slow[1]);
```

**Trade-off**：
- 保持 pre-fix 那組 Candidate E 的可能表現（Net +1,095K）
- 但接受方向盲「bug」（用戶昨天已 flag F2 為需修）

**Real question**：F2 是否是 bug 或 feature？

---

### 路徑 D — **簡化：完全移除 MinSlope filter**

**思路**：如果 Slope filter 無論高低都無 alpha，可能它根本不必要。純死叉 + 出場控管。

**Sweep 建議**：
```
Fast:        10, 12, 15
Slow:        30, 40, 50
MinSlope:    0 (disabled)
QuickStop_MaxLoss_Pts: 50, 80, 120
BE_Trigger_ATR: 0.5, 1.0, 1.5
```

**組合數**：3 × 3 × 3 × 3 = 81

**優點**：符合原 spec「進場門戶大開」哲學
**缺點**：可能 whipsaw 更爆

---

## 六、Rule #14 決策 — 若 Phase 2 也 FAIL 需考慮

| 選項 | 說明 |
|-----|------|
| KILL S16_S | 寫 FINAL_VERDICT.md，正式 KILL，進 S16_L 或 S5_L |
| 保留 W2 code + 記錄 failure | 完整記錄後暫停，未來若有新想法再來 |
| 找架構性改動 | 換 5M → 10M / 15M（更少雜訊）|

---

## 七、我的推薦順序

1. **立刻做**：**路徑 A** — Re-sweep with MinSlope 0.5-3 range
2. **若 A 找到 sweet spot**：進 Phase 3 fine-tune → W5 validation
3. **若 A 也全負**：**路徑 D**（純死叉無 slope）+ 更寬 QS
4. **若 D 也全負**：**KILL S16_S**（W0 daily proxy 過關但 5M 不 translate）

---

## 八、Rule #16 五支柱檢查（本文）

- Rules：Rule #14/#18 決策節點觸發（Phase 1 全負 = W5 阻擋）
- Context：完整 GA sweep + 根本原因診斷
- Verification：sweep range vs 建議對比揭露 MinSlope range 錯位
- Memory：對齊 memory `reference_strategy_rd_sop`（fail-fast 原則）
- Format：完整分析 md + 3 條路徑 + 決策節點

---

**End of Analysis — 2026-07-09 Desktop**
