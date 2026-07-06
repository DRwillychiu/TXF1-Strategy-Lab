# S16 MACrossShort — HANDOFF Desktop 2026-07-06 → Laptop 2026-07-07

**用戶指示**：明天筆電端接續深度討論 S16 MA 策略規劃。

---

## 一、今日進度快速回顧（2026-07-06 桌機）

### ✅ S3_S v1.9.6-OPT PROMOTE 完成
- v1.8.0-PROD → v1.9.6-OPT-PROD 升級部署至 `strategies/live_simulation/`
- Rule #18 quantitative gates: **7/7 PASS**（MC / Bootstrap / Stress / Sensitivity + concentration）
- WFA Path A 豁免（low-freq structural）
- Portfolio Correlation 豁免（用戶 ruling：S3_L/S3_S 非鏡像）
- Portfolio cap 3%，S3_L 5% 保留
- Archive: `strategies/research/archive/S3_S_v180_replaced_20260706/`
- 用戶已完成 MC12 實體部署

### 🎯 S16 MACrossShort — Stage-1 深度討論已啟動
- 用戶要求：**先深度了解 MA + 規劃策略操作**（不急著跑 W0 或決策）
- Stage-1 spec 已有初稿：`S16_stage1_spec.md`
- 桌機端已完整提供 MA 深度知識 + S16 策略操作規劃（見本檔第三節）

---

## 二、Roadmap 狀態確認

| 策略 | 狀態 | Next Action |
|------|------|-----------|
| S3_S | ✅ live_simulation v1.9.6-OPT-PROD | 每週監控 |
| **S4_S MACDDivergenceShort** | ⚠️ **W0 pre-verify 3/4 MARGINAL**（RR 1.33 < 1.5）| **待用戶 ruling: KILL or 續 W1** |
| **S16 MACrossShort** | 📋 **Stage-1 討論中** | 明天筆電端繼續 |
| S4_L MACDDivergenceLong | ⏳ Queue（推延至 S16 後）| - |

### 用戶 2026-06-28 ruling
- **順序**：S4_S → S16 → S4_L（explicit override Rule R-1）
- **原因**：補強做空 sleeve 厚度（4 空 vs 5 多 略偏多）

### 🚨 決策未定事項（明天筆電端可能要處理）
1. **S4_S 命運**：KILL（RR fail）or 續 W1（用 FWD_N=20 版本 RR 1.60 PASS）
2. **S16 vs S4_S 順序**：先 close S4_S 再開 S16 or 直接跳 S16
3. **S16 是否加 trend filter**：純規則簡單 vs 救 whipsaw

---

## 三、S16 MACrossShort 完整策略設計文件

### A. 策略一句話
在 15 分鐘 K 線上，Fast MA 跌破 Slow MA「死亡交叉」做空，直到「黃金交叉」出場，賺中短期動能下行趨勢。

### B. MA 深度知識重點

**MA 家族**：
- **EMA 首選**（反應快、業界標準、MC12 內建）
- HMA 進階（若 whipsaw 太重）
- SMA 太延遲不適合 15M

**15M 時框下 MA 週期意義**：
| MA(N) | 對應時間 | 交易性格 |
|-------|--------|--------|
| MA(5) | 75 min | 極短線 |
| MA(20) | 5 hr ≈ 1 交易日 | 日內 swing ⭐ |
| MA(50) | 12.5 hr ≈ 1.5 日 | Overnight swing |

**S16 建議範圍**：
- Fast: 5-15
- Slow: 20-50
- 約束: Slow > Fast × 2, Slow ≤ 50

### C. 進場 / 出場 架構

```
Entry Signal:
  Fast MA(N1) crosses BELOW Slow MA(N2) at Data1 (15M) close
  AND v_Settlement_Day = False
  AND v_Holiday_Block = False
  AND v_Registry_Expired = False
  AND Manual_Kill_Switch = False
  [OPTIONAL] AND Regime OK (Daily MA filter, 待決定)
Order:
  sell short next bar at market

Exit Priority:
  P0: Kill / Registry / Holiday / Settlement (Rule #11/#12)
  P1: Golden Cross -> buy to cover at market
  P2: Time-based Exit (跨假日保護)
  P3: ATR-based SL (v_ATR x StopATRMult)
  P4: SetStopLoss engine guard (Rule #12 backup)

NO TP - trend running per feedback_trend_let_profits_run
```

### D. 待優化參數（W4 Phase 2 GA）

| Input | 範圍 |
|-------|------|
| Fast MA | 5 / 8 / 10 / 12 / 15 |
| Slow MA | 20 / 25 / 30 / 40 / 50 |
| StopATRMult | 1.5 / 2.0 / 2.5 / 3.0 |
| ATR_Len | 10 / 14 / 20 |

### E. 5 種進場信號變體（漸進複雜度）

| # | 變體 | 說明 |
|---|------|------|
| **1** | **純雙 MA 交叉** | Fast cross below Slow ⭐ 起手用 |
| 2 | 三 MA 排列 | Fast < Mid < Slow 且都下彎 |
| 3 | MA + 價格關係 | 交叉 + Close < Slow 確認 |
| 4 | MA 斜率過濾 | Slow MA 下彎才允許 |
| 5 | MA + Volume | 交叉 + 量增 |

### F. 6 個抗 Whipsaw 手段

| # | 手段 | 保護 | 副作用 |
|---|------|------|------|
| 1 | Slow MA 提高 | ⭐⭐⭐ | 訊號延遲 |
| 2 | ATR/Vol filter | ⭐⭐⭐ | 規則複雜 |
| 3 | 最小 bar 持倉 | ⭐⭐ | 部分虧損固定化 |
| 4 | Daily/60M trend filter | ⭐⭐⭐⭐ | **違反規則簡單** |
| 5 | HMA / KAMA | ⭐⭐⭐ | 複雜度大幅上升 |
| 6 | MACD/RSI 二次確認 | ⭐⭐ | Overfit 風險 |

### G. TXF1 特殊挑戰對應

| 挑戰 | 對策 |
|------|------|
| 長期偏多 regime | 接受年報酬低 or 加多頭過濾（trade-off）|
| 夜盤流動性稀薄 | 夜盤封鎖 or 量確認 |
| 假日 gap | Rule #11 假日平倉 |
| 結算日 | Rule #11 Settlement_Flat 12:30 |
| 1 點 200 NTD 高槓桿 | 必加 SL + SetStopLoss |
| 滑價 500/邊 | trade 頻率支撐成本 |

### H. 預期表現框架

| 指標 | 樂觀 | 中性 | 悲觀 |
|------|------|------|------|
| 年 trade 數 | 60-80 | 30-50 | < 20 |
| Win Rate | 45-55% | 35-45% | < 35% |
| PF | 1.5-2.0 | 1.0-1.3 | < 0.9 |
| MDD | -15% | -20-25% | -30%+ |
| Sharpe | 0.6-0.9 | 0.3-0.5 | < 0.2 |

### I. 與現有 sleeve 對比 — S16 獨特性

| 策略 | 時框 | Trigger | 出場 | Alpha 來源 |
|------|------|---------|------|-----------|
| L2 | Daily | Donchian | ATR trail | 中長線趨勢 |
| L4 | 60M | Range 假破 | ATR stop | 盤整突破 |
| S3_RPS | 60M | 拉回狙擊 | Reversal | 反彈失敗 |
| S3_S | 60M | BB 壓縮 | TP/SP/1M | 波動率爆發 |
| **S16** | **15M** | **MA 死叉** | **黃金交叉** | **中短期動能** ⭐ 唯一 |

---

## 四、明天筆電端 4 個可能討論方向

用戶已明確：**先深度理解 MA 不急著決策**。明天筆電端可能想深入：

### 方向 1 — MA 種類深度對比
- EMA 數學公式 + smoothing factor 意義
- HMA 為何 whipsaw 少（Weighted Hull 演算法）
- KAMA 自適應機制
- Backtest 對比 EMA vs HMA vs KAMA on TXF1 15M

### 方向 2 — Whipsaw 深度量化分析
- 定義 whipsaw event（entry + 3 bar 內反向）
- TXF1 15M 2020-2026 whipsaw 發生率統計
- Regime 分類下 whipsaw rate 差異
- 抗 whipsaw 手段的實測 trade-off

### 方向 3 — 進場信號變體 A/B 比較
- 5 種變體用 Python simulate on 2020-2026 TWII 15M
- 找 sample size / PF / whipsaw 3D trade-off
- 給用戶 GO/NO-GO 建議

### 方向 4 — 策略哲學討論
- 規則簡單 vs 加 filter：Lesson L24 邊界
- 純動能 vs 動能 + regime：portfolio 角度
- Sharpe 0.5 crash insurance vs Sharpe 1.0 momentum
- S3_S (crash insurance) + S16 (momentum trend) 組合 Sharpe 預估

---

## 五、關鍵檔案清單

### S16 相關
- `strategies/research/S16_MACrossShort/S16_stage1_spec.md` — 初稿 spec
- `strategies/research/S16_MACrossShort/HANDOFF_20260706_desktop_to_laptop.md` — 本檔

### S4_S 相關（待決策）
- `strategies/research/S04_MACDDivergenceShort/S4_S_stage1_spec.md`
- `strategies/research/S04_MACDDivergenceShort/S4_S_strategy.md`
- `strategies/research/S04_MACDDivergenceShort/W0_alpha_preverify_result_20260628.md` — 3/4 MARGINAL
- `strategies/research/S04_MACDDivergenceShort/_w0_alpha_preverify.py`

### S3_S 部署（剛完成，明天不動）
- `strategies/live_simulation/S3_S_VolSqueezeShort.pla` v1.9.6-OPT-PROD
- `strategies/research/S03_VolSqueezeShort/PROMOTION_20260706.md`

### Roadmap
- `docs/policies/OFFICIAL_ROADMAP.md`

---

## 六、Git 狀態

**今日 commits（S3_S promote batch）**：
```
e81c26b  feat(S3_S): PROMOTE v1.8.0-PROD to v1.9.6-OPT-PROD
d6647b8  feat(S3_S): Stress Test 6/6 Event-Net PASS
0af3f8e  docs(S3_S): update README + spec with MC+Bootstrap 5/5 PASS
e247025  feat(S3_S): v1.9.6 Config B + OPT MC + Bootstrap 5/5 PASS
9bce00a  docs: add 2026-07-05 cowork sync handoff
```

**本地 = 雲端 100% 同步** ✅
Repo: https://github.com/DRwillychiu/TXF1-Strategy-Lab.git

---

## 七、規則遵守 checklist（S16 開發起始）

- Rule #14 OFFICIAL_ROADMAP：S16 已寫入 roadmap（用戶 2026-06-28 override），非發明
- Rule #16 五支柱：新策略要走 SOP v2 完整流程
- Rule #18 Non-WFA 5 件套：promote 前必跑
- Lesson L24：規則簡單哲學，加 filter 需 explicit justify
- memory `feedback_trend_let_profits_run`：不設 TP，讓 golden cross 自然出場
- memory `feedback_holiday_flatten_rule`：假日前平倉
- memory `feedback_mc_time_24hr_pitfall`：時段條件必閉區間

---

**Handoff Complete — 2026-07-06 桌機端**
**明天筆電端見** 🌙
