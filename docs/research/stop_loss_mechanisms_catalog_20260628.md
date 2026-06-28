# 極端行情停損機制 — 廣泛 Research 整理（12 種主流方案）

**日期**：2026-06-28
**目的**：為 S3_S v1.7.4 Hard SL Cap 設計提供業界 best practice 參考
**Sources**：6 個 WebSearch (CME / TradingSim / LuxAlgo / TrendSpider / StockCharts / GitHub backtrader 等)
**Audience**：明日筆電端 SL 機制 KPI 工作 reference

---

## 一、Headline 結論（**3 大類**）

| 類別 | 代表機制 | 適合情境 |
|------|---------|---------|
| **A. 帳戶級風控** | 2% Rule、Hard Cap by % | 機構基本盤，systemic risk control |
| **B. 波動率自適應** | ATR-based、Chandelier、SuperTrend、Multi-step Trail | 趨勢策略主力，**有 vol expansion 弱點** |
| **C. 事件驅動 / 結構性 exit** | 多時框確認、Capitulation Volume、VIX-adaptive、Triple Barrier | **極端行情專用**，配合 A/B 使用 |

→ **業界共識：A + B + C 三層協同**（單獨任何一種都不足）

---

## 二、12 種機制完整對照表

| # | 機制名稱 | 邏輯 | 預設參數 | 優點 | 缺點 | 適合 S3_S？ |
|---|---------|------|---------|------|------|----------|
| **1** | **2% Rule (Hard Cap)** | SL 距離 = 帳戶 × 2% / 點價值 | 1M × 2% / 200 = **100 點** | 簡單明確、強制單筆 risk 上限、機構標準 | 不適應 vol、可能截斷正常波動 | ⭐⭐⭐ **直接適用** |
| **2** | **1% Rule (Prop Firm 變體)** | 同上但 1% | 1M × 1% / 200 = **50 點** | 更保守、適 FTMO-style drawdown rules | TXF1 50 點過緊、whipsaw | ⭐ 過緊 |
| **3** | **ATR Multiplier** | SL = N × ATR(14) | 2-3 × ATR | 適應 vol、無需 hard cap | **Vol expansion 進場時 SL 自動變大**（S3_S 痛點）| ⭐⭐ **現有方案，有缺陷** |
| **4** | **Chandelier Exit** | SL = HighestHigh(22) - 3×ATR | 22 期 / 3×ATR | 趨勢追蹤鎖利、抗噪 | **反應慢**，極端反彈 K 棒可能穿越 | ⭐⭐ 適合 trail 不適合初始 |
| **5** | **Parabolic SAR** | 加速因子 AF 從 0.02 遞增 | AF 0.02 step 0.02 max 0.2 | 越接近趨勢頂越緊 | **range 盤連續假信號**、極端 K 線穿越 | ⭐ 不適合 |
| **6** | **SuperTrend** | ATR + MA 平滑組合 | 10 期 / 3×ATR | 比 SAR 平滑、less noise | 仍有 lag、極端反彈會穿 | ⭐⭐ 同 Chandelier |
| **7** | **Multi-step ATR Trail** | 3xATR → 2xATR (after 2x profit) → 1.5xATR (after 4x profit) | progressive | 給趨勢空間 + 後期收緊 | 複雜、初始 SL 仍可能遠 | ⭐⭐⭐ **可借鏡** |
| **8** | **Disaster Stop + Adaptive Trail** | Trail (ATR adaptive) + 固定 disaster stop | Trail 3×ATR + Disaster 5×ATR fixed | 兩層保護 | Disaster 仍可能極遠 | ⭐⭐⭐ **可借鏡** |
| **9** | **Multi-Timeframe Confirmation** | 上層 TF trigger + 下層 TF 監測反彈 | 60M entry + 1M reversal | 抓 capitulation 反彈 | 複雜、IOG 設定 / 滑價問題 | ⭐⭐⭐⭐ **與 RBE 概念一致** |
| **10** | **Capitulation Volume Spike Exit** | 1M volume > 2-5× 20-day avg → exit | Volume 3×, K 棒反向 | 抓真實 reversal、有 volume 確認 | TXF1 perpetual volume 連續性弱、需 1M volume data | ⭐⭐⭐ 需驗證 |
| **11** | **Triple Barrier Method** | TP / SL / Time barriers 並存 | (符合 S3_S 現有設計) | 系統化 backtest 框架 | 已是現有架構 | ✅ **S3_S 已採用** |
| **12** | **VIX-adaptive Sizing** | VIX spike → 減 size 或 widen SL | VIX > 30 → size ÷ 2 | 系統性 macro 風控 | TXF1 無直接 VIX、需 TVIX proxy | ⭐⭐ 中長期可考慮 |

---

## 三、極端行情（Flash Crash / Capitulation）專屬機制

### A. Circuit Breaker（市場層級）
- 美股 7% (L1) / 13% (L2) / 20% (L3) 三階段
- TXF1 對應：盤中漲跌幅 10% 熔斷
- **不是策略可控**，但要 aware

### B. Capitulation 特徵（業界共識）
- Volume spike 2-5× 20 日均量
- 大量 stop-loss cascading triggered
- 來自 margin calls + mutual fund redemptions
- **90% VIX > 30 spike 在 3 個月內 resolve**

### C. 對策略 design 啟示
1. **不要單獨依賴 ATR-based SL**（vol expansion 時自然變大）
2. **Hard cap by account %** 是 systemic protection
3. **Multi-timeframe**（下層 TF 看反彈速度）是 best-in-class
4. **Volume confirmation** 是 sophistication 加分項

---

## 四、業界 best practice（**institutional 多層 stop loss 架構**）

按 Volatility Box 整理：

```
Layer 1 [Disaster Stop / Hard Cap]
  - Fixed % of account or fixed points
  - 最後防線，絕對不可穿
  - 例：S3_S 100-200 點 cap
  
Layer 2 [Initial Volatility-adjusted SL]
  - ATR × N (進場時 frozen)
  - 給策略發揮空間
  - 例：S3_S 2.75 × Frozen_ATR
  
Layer 3 [Trailing Stop / Profit Lock]
  - Chandelier / Multi-step ATR / SuperTrend
  - 利潤鎖定
  - 例：S3_S Layer 2 SP (peak × 70%)
  
Layer 4 [Time-based / Structural Exit]
  - TimeStop / Mid Exit / Triple Barrier
  - 避免無限套牢
  - 例：S3_S MaxBars 35 + Mid Exit
  
Layer 5 [Event-driven / Catastrophe Exit] ← 新加
  - Multi-TF capitulation 反彈
  - Volume spike confirmation
  - VIX-adaptive position reduction
  - 例：候選 1M reversal exit (v1.7.4 RBE)
```

→ **S3_S 已有 Layer 2/3/4，缺 Layer 1 + Layer 5**
→ Layer 1 = Hard Cap（v1.7.4 cap 100 探索）
→ Layer 5 = RBE 1M reversal exit（候選）

---

## 五、GitHub 具體 implementations 參考

### `mementum/backtrader` - `stop-loss-approaches.py`
- 經典示範 5 種 stop loss approach
- ATR-based / fixed point / trailing / Parabolic SAR / Chandelier
- URL: `github.com/mementum/backtrader/blob/master/samples/stop-trading/stop-loss-approaches.py`

### `wangzhe3224/awesome-systematic-trading`
- 量化 trading 完整 library list
- 含 risk management module 多種實作

### `leoncuhk/awesome-quant-ai`
- AI/ML 在 quant trading 應用
- 含 ML-based dynamic stop loss research

### `je-suis-tm/quant-trading`
- Python 完整策略 (含 Parabolic SAR / Bollinger Bands 等)
- 可參考其 SL 處理

---

## 六、S3_S v1.7.4 設計 → 業界對照建議

### 當前 v1.7.4 cap 100 評估
| 業界視角 | 我們 cap 100 |
|---------|-------------|
| 符合 2% Rule | ✅ |
| 符合 institutional hard cap 概念 | ✅ |
| **但 cap < SP arm distance（1.5 ATR ~290 點）** | ❌ **這是 bug** |
| 解法：cap >= max(SP arm distance, 100) | 業界 Multi-step ATR 概念類似 |

### **明日筆電端 KPI 建議改良**

**Option Sweet (推薦)**: Conditional Hard Cap
```pla
v_Frozen_SL_Dist = MinList(
    v_Frozen_ATR * StopATRMult,    { ATR-based 2.75 ATR }
    MaxList(
        SL_Hard_Cap_Pts,            { 100 absolute floor }
        v_Frozen_ATR * SP_Trigger_ATRMult  { SP arm 距離保底，避免 SP 失效 }
    )
);
```

意思：
- ATR-based 上限
- Hard cap 100 點 或 SP arm 距離 (1.5 ATR) **取大** 作下限
- = **保留 SP 機制 + Hard cap 風控雙重保護**

預期效果：
- 平時 ATR 60 點 → cap 165 點 (2.75 ATR)，SP arm 距離 90 點 → cap = 165 (ATR-based 主導)
- Vol expansion ATR 193 點 → cap 530 點 (2.75 ATR)，SP arm 距離 290 點 → cap = max(100, 290) = 290 (SP 保底)
- → SL 介於 290-530 點之間 (cap by SP arm distance)
- → SP 機制不失效 + max SL 仍受控

### **Option D/E/F backtest 順序**

| 組別 | 邏輯 | 預期 |
|------|------|------|
| D | Cap 150 (固定) | 緊一點看 cluster losses |
| E | Cap 200 (固定) | 推測 sweet spot |
| F | Cap 250 (固定) | 接近 v1.7.3 |
| **G** | **Conditional Cap (max with SP arm)** | **最 institutional 解法** |

---

## 七、Lessons 候選（L26-L28）

### L26: 「Hard SL Cap 必須 >= SP arm distance」
- v1.7.4 cap 100 證實：cap < SP arm → SP 機制失效 → alpha 損失
- 解法：cap = max(fixed, SP_Trigger × ATR)

### L27: 「業界 SL 是 5 層架構，非單層」
- Layer 1: Hard cap
- Layer 2: ATR Initial
- Layer 3: Trailing (SP/Chandelier)
- Layer 4: Time/Structural
- Layer 5: Event-driven (multi-TF / volume)
- S3_S 缺 Layer 1 + Layer 5

### L28: 「Volatility expansion 進場是 short 策略 systemic risk」
- BBW squeeze breakdown → vol 已 expand
- ATR-based SL 在這時最大
- 必須 hard cap 或 multi-TF confirmation

---

## 八、明日 KPI 建議優先順序

| Priority | Action | 預估時間 |
|----------|--------|---------|
| 1 | **跑 cap 150 / 200 / 250 三組對照** (D/E/F) | 20 分鐘 MC |
| 2 | **跑 Option G: Conditional Cap (max with SP arm)** | 10 分鐘 MC |
| 3 | 5 組對比分析 → 推薦 final 機制 | Claude 10 分鐘 |
| 4 | 若 sweet spot 找到 → W4 WFA 9 windows verify | 1.5 小時 MC |
| 5 | promote v1.7.4 or 接受 v1.7.3 | 視結果 |

---

## 九、Sources

- [9 Market Volatility Strategies for Futures Traders in 2026 - AquaFutures](https://www.aquafutures.io/blogs/market-volatility-strategies)
- [Stock Market Circuit Breakers - Investor.gov](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-market-circuit-breakers)
- [What Is Capitulation in Trading - TradingSim](https://www.tradingsim.com/blog/capitulate)
- [Volatility-Adjusted Stop Losses: ATR, Chandelier, and Keltner Methods - Volatility Box](https://volatilitybox.com/research/volatility-adjusted-stop-losses/)
- [Essential Stop Loss Strategies - Optimus Futures](https://learn.optimusfutures.com/stop-loss-strategies)
- [The 2% Rule - CME Group](https://www.cmegroup.com/education/courses/trade-and-risk-management/the-2-percent-rule)
- [The 2 Percent Rule - IncredibleCharts](https://www.incrediblecharts.com/trading/2_percent_rule.php)
- [The 1% Risk Rule for Day Trading and Swing Trading - Trade That Swing](https://tradethatswing.com/the-1-risk-rule-for-day-trading-and-swing-trading/)
- [Dynamic ATR Trailing Stop Trading Strategy - Medium](https://medium.com/@redsword_23261/dynamic-atr-trailing-stop-trading-strategy-market-volatility-adaptive-system-2c2df9f778f2)
- [ATR-Based Stop-Loss for High Volatility Breakouts - LuxAlgo](https://www.luxalgo.com/blog/atr-based-stop-loss-for-high-volatility-breakouts/)
- [Volatility Stop Indicator: Volatility-Based Trailing Stop Strategy - LuxAlgo](https://www.luxalgo.com/blog/volatility-stop-indicator-volatility-based-trailing-stop-strategy/)
- [Chandelier Exit - StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- [Essential Stop-Loss Indicators - TrendSpider Learning Center](https://trendspider.com/learning-center/essential-stop-loss-indicators-every-trader-should-know/)
- [Parabolic SAR Trading Indicator: A Comprehensive Guide - Enlightened Stock Trading](https://enlightenedstocktrading.com/parabolic-sar/)
- [Stop-Loss, Take-Profit, Triple-Barrier & Time-Exit: Advanced Strategies for Backtesting - Medium](https://medium.com/@jpolec_72972/stop-loss-take-profit-triple-barrier-time-exit-advanced-strategies-for-backtesting-8b51836ec5a2)
- [Backtrader stop-loss-approaches.py - GitHub mementum/backtrader](https://github.com/mementum/backtrader/blob/master/samples/stop-trading/stop-loss-approaches.py)
- [Awesome Systematic Trading - GitHub wangzhe3224](https://github.com/wangzhe3224/awesome-systematic-trading)
- [Awesome Quant AI - GitHub leoncuhk](https://github.com/leoncuhk/awesome-quant-ai)
- [Quant Trading Strategies - GitHub je-suis-tm](https://github.com/je-suis-tm/quant-trading)
- [The Ultimate Guide to Futures Volatility Management - Tradeify](https://tradeify.co/post/futures-volatility-management)
- [The Ultimate Guide to Volatility Stop-Losses - Trading Setups Review](https://www.tradingsetupsreview.com/ultimate-guide-volatility-stop-losses/)
- [1 minute Scalping Strategy - StockGro](https://www.stockgro.club/blogs/trading/1-minute-scalping-strategy/)
- [ATR-Based Dynamic Stop-Loss Support Breakout Short - FMZQuant Medium](https://medium.com/@FMZQuant/atr-based-dynamic-stop-loss-support-breakout-short-quantitative-trading-strategy-92e48aeafe1f)
