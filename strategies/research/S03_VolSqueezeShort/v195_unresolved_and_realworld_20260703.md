# S3_S v1.9.5 — 未解決問題 + 實戰延伸分析

**日期**：2026-07-03
**當前版本**：v1.9.5-EXPERIMENTAL（GA-best defaults）
**Baseline**：68 trades / Net +513,400 / PF 1.574 / MDD -19.05% / WR 50%

---

## 一、策略本質重申（用戶 2026-07-03 / 07-04 ruling）

**目標**：**在白天或半夜的突然快速下殺中，完整捕捉崩盤利潤**

- 🛡️ **Crash Insurance 角色** — 不是穩定 alpha
- 📊 **低頻 + 大回報** — 17/82 個月活躍（20.7%），事件驅動
- 💰 **成功標準**：**MDD 在「一口大台指原始保證金以內」= 好策略**
  - 台指期大台 TX 原始保證金：**636,000 NTD**（2026-07 期交所公告）
  - 維持保證金：488,000 NTD
- 🏦 **實戰配置**（用戶 2026-07-04 ruling）：
  - **S3_S 專用帳戶 100 萬**（獨立 sleeve，不與其他策略共享）
  - **大台 1 口**
  - 其他策略有**各自的 100 萬 sleeve**

---

## 二、未解決問題清單（7 項）

### 🔴 Level 1：Rule #18 validation 未完成（3 件套 out of 5）

#### 問題 #1：MC 95% MDD boundary FAIL
- **值**：-30.64%（gate < -30% 差 0.64%）
- **性質**：邊界值，非結構性 fail
- **影響**：機構級 gate FAIL 但可爭辯（crash insurance 本質）
- **後續**：需搭配其他 4 件套判斷

#### 問題 #2：Trade Concentration Top 3 佔 103% Net
- **值**：移除 top 3 → -17,200 NTD 轉負
- **性質**：Crash insurance 結構性特徵（不是 bug）
- **HHI 0.077** = 分散指標其實 PASS
- **判定**：可接受（大 event 本來就集中）

#### 問題 #3：**Parameter Sensitivity Analysis 未跑** ⚠️
- **需要**：8 個 GA-changed params 各 ±10% / ±20% 掃描
- **交叉**：StopATRMult × TargetATRMult 2D surface
- **判準**：**高原寬度 > 20% 範圍**（避免 spike overfit）
- **工具**：MC12 optimization sweep
- **時間**：2-4 小時

#### 問題 #4：**W4 Walk-Forward 未跑** ⚠️
- **需要**：9 個 IS 2y / OOS 6m 滾動 window
- **判準**：WFE > 50%，OOS PF > 1.0
- **Caveat**：低頻策略 68 trades / 6.5yr = 10.5 trades/yr，WFA 可能不 fair
- **時間**：6-8 小時

#### 問題 #5：**Stress Testing 6 events 未跑** ⚠️
- **標準事件**：1987 Black Monday / 2008 雷曼 / 2010 Flash Crash / 2015 中國股災 / 2020 COVID / 2024 BoJ
- **TXF1 specific**：2026-04-02 Trump 關稅 / 2025-04-09 Trump 主跌
- **判準**：任何 event 單筆 loss < 帳戶 5%，cluster loss < 帳戶 15%
- **工具**：MC12 isolate 期間 backtest

### 🟠 Level 2：Backtest 顯示的 residual issue

#### 問題 #6：T68 2026-06-08 V 轉 -135.4K single loss
- **性質**：MAE -202K → actual -135K（1M_Exit 有 save 67K）
- **問題**：single -135K = 帳戶 13.5%，過於集中
- **可能解**：加 MAE Guard（MAE > 100 pts force exit）
- **風險**：可能誤殺 crash 主段

#### 問題 #7：06-08 → 06-30 21 天空窗
- **診斷完成**：策略本質（vol expansion 期 Squeeze=False）
- **06-26 case**：+138K 被 Regime block 掉（唯一 false positive）
- **判定**：策略本質限制，可接受

---

## 三、💰 MDD 保證金實戰分析（**核心決策依據**）

### 台指期保證金結構（2026-07 期交所公告）

| 契約 | 1 點 | 原始保證金 OM | 維持保證金 MM | 當沖減半 |
|------|------|--------------|-------------|---------|
| **大台 TX** | 200 NTD | **636,000** | **488,000** | 318,000 |
| 小台 MTX | 50 NTD | 159,000 | 122,000 | 79,500 |
| 微台 TMF | 10 NTD | 31,800 | 24,400 | 15,900 |

### 用戶實戰配置：**S3_S 專用帳戶 100 萬 + 大台 1 口**

```
帳戶淨值：1,000,000 NTD
持倉：1 口大台 TX
鎖定 OM：636,000
可承受 MDD buffer（到 MM 觸發）：1,000,000 - 488,000 = 512,000 (51.2%)
```

### v1.9.5 MDD 情境對比（三重標準）

| 情境 | MDD % | 損失 | vs OM 636K | vs Buffer 512K | 距 MC buffer | 判定 |
|------|-------|------|-----------|---------------|-------------|------|
| **Backtest** | **-19.05%** | **-190,500** | 用 30% | 用 37% | **322K** | ✅✅ |
| MC 中位數 | -18.13% | -181,300 | 用 29% | 用 35% | 331K | ✅✅ |
| MC 95% | -30.64% | -306,400 | 用 48% | 用 60% | 206K | ✅ 安全 |
| MC 99% 極端 | -37.89% | -378,900 | 用 60% | 用 74% | 133K | ✅ 邊界 |
| T68 single | -13.54% | -135,400 | 用 21% | 用 26% | 377K | ✅✅ |
| **Margin Call 門檻** | -51.2% | -512,000 | 用 80% | 100% | 0 | 🚨 觸發 |

### 💡 **雙重標準判定**

**標準 1：MDD ≤ 一口大台 OM 636K**
- ✅ Backtest -190K < 636K
- ✅ MC 95% -306K < 636K
- ✅ MC 99% -379K < 636K
- **三個情境全通過**

**標準 2：Margin Call 安全（Buffer < 512K）**
- ✅ Backtest 用 37% buffer
- ✅ MC 95% 用 60% buffer（剩 206K）
- ✅ MC 99% 用 74% buffer（剩 133K）
- **三個情境全通過，不會 margin call**

### 📊 S3_S 獨立 sleeve 年度期望

| 指標 | Backtest 6.5 年 | 年化 | 相對 100 萬 |
|------|---------------|-----|-----------|
| Net Profit | +513,400 | +79,000 | **+7.9%/年** |
| MDD (Worst MC 95%) | -306,400 | - | -30.6% |
| Return / MDD | - | - | 0.26 |
| 活躍月份 | 17/82 | ~2.6 個月/年 | 80% 空倉 |

**Profile 定位**：平均年報 **7.9%**，但 -30% MDD 可能 → 典型 **crash insurance** 曲線。

---

## 四、實戰延伸問題（**Backtest 沒 model 的**）

### 🏦 A. 資金/保證金風險（4 項）

#### A1. **維持保證金追繳（Margin Call）**
- **問題**：實際盤中未實現 MDD 可能瞬間高於帳面 MDD
- **例**：2026-06-08 MAE -202K，仍距 MM buffer 512K 有 310K
- **未處理**：backtest 不 model intra-day margin check
- **實戰 SOP**：**S3_S 專用帳戶 100 萬**（用戶 2026-07-04 ruling）→ MC 99% 仍剩 133K buffer

#### A2. **假期跳空風險**
- **問題**：春節/長假結束後開盤 gap 可能 > SL 距離
- **例**：長假期 3-9 天，若期間國際大跌，開盤 gap down 500+ pts
- **backtest 誤導**：SL 假設 fill at Stop price，實戰 fill at Open
- **實戰 SOP**：**假期前強制平倉**（Rule #11 已含）

#### A3. **交易稅 & 手續費**
- **backtest**：滑價 1000 NTD/round-trip
- **實戰真實成本**：
  - 期交稅：0.00002 × 契約值 × 2（進出）≈ 32 NTD（大台 40K 時）
  - 手續費：40-60 NTD/round-trip（大戶談判價）
  - **總成本**：~1080 NTD/round-trip（與 backtest 差 8%）
- **68 trades × 80 NTD 差距 = -5,440 NTD**（可忽略）

#### A4. **資金效率低**
- **17/82 個月活躍**（20.7%）
- **剩餘 82.3% 時間空倉**，資金閒置
- **實戰考量**：組合部署（S3_L + L1 + S1 等）分攤

### 🌐 B. 執行風險（5 項）

#### B1. **夜盤流動性稀薄**
- **問題**：凌晨 2-5AM 委買賣單稀疏，Market order fill 可能超差
- **例**：2026-06-05 21:01 SP fire，若夜盤 spread 30 pts，實戰滑價 ×3
- **backtest 誤導**：假設 1000 NTD 滑價（實戰夜盤可能 3000+）
- **實戰 SOP**：**改用 limit order + 5 pt buffer** or 只做日盤

#### B2. **API 交易接口穩定性**
- **當前**：MC12 手動下單 / 或 API auto
- **風險**：連線斷開、API rate limit、期貨商 server 延遲
- **例**：2020 COVID 期間期貨商 server 塞爆，order queue 堵塞
- **實戰 SOP**：**建立備援管道**（手機 app + 期貨商電話直下）

#### B3. **停電/斷網 SOP**
- **問題**：MC12 執行中電腦當機，未執行的 stop order 消失
- **例**：Windows Update 強制重啟，SP/SL 委託單消失
- **實戰 SOP**：
  - UPS 不斷電系統
  - 期貨商內建 stop（獨立於 MC12）
  - 每日重啟 pre-check

#### B4. **Stop Order fill 不確定性**
- **問題**：Stop 觸發後 fill at Market，實戰可能 fill 於超差價
- **例**：2026-06-08 V 轉，MC12 backtest 假設 -135K，實戰可能 -160K+
- **未 model**：market impact + queue jump
- **實戰 SOP**：**Catastrophic Stop cap**（絕對 max loss 硬限 -150 pts）

#### B5. **月結算日夜盤劇烈**
- **問題**：第 3 週三結算日夜盤流動性極差
- **backtest**：Rule #11 已有 Settlement_Flat 保護
- **實戰**：**強制 12:30 前平倉不進場**（v1.9.5 已 code in）

### 🧠 C. 策略層 residual（3 項）

#### C1. **策略衰減（Alpha Decay）**
- **問題**：BB 壓縮 breakdown 隨市場演化可能失效
- **例**：2020-2022 表現差（-111K total）vs 2025-2026 +604K
- **原因**：低利率 + 夜盤延長 + 演算法交易增加
- **實戰 SOP**：**每季 re-optimize + PF < 1.0 連 3 個月 → KILL trigger**

#### C2. **Regime Shift（政策改變）**
- **問題**：央行政策、期交所規則變更（如夜盤時段延長/縮短）
- **backtest 假設**：夜盤 15:00-05:00 固定
- **實戰風險**：若期交所改夜盤結束時間，Holiday_Flat_Time 需重寫
- **實戰 SOP**：**訂閱期交所公告 + 半年 code review**

#### C3. **Portfolio Correlation**
- **未 test**：S3_S 與 S3_L、L1-L5、S1 的實戰相關性
- **backtest 期間**：2020-2026 都是 individual test
- **問題**：崩盤時所有 short 策略同時觸發，portfolio MDD 疊加
- **實戰 SOP**：**Portfolio-level Kill Switch**（總 MDD > 30% 強制 flat all）

### 📱 D. 心理 & 操作面（3 項）

#### D1. **短期連虧堅持**
- **問題**：Backtest 顯示連 5 筆 1M_Exit 損失是正常（保費）
- **心理**：實戰連 3 筆 -30K 後可能停止執行
- **實戰 SOP**：**簽紙本 commitment**「連虧 5 筆內不停策略」

#### D2. **策略手動介入**
- **問題**：看新聞感覺 crash 快來，想手動加碼
- **backtest 沒 model** 這行為
- **實戰 SOP**：**嚴禁手動介入**，除非 v_Registry_Expired

#### D3. **實戰記錄 & PDCA**
- **問題**：需要記錄實盤 fill vs backtest fill 差距
- **未有工具**：目前無實盤日誌自動比對
- **未來**：需建 `실盘 diff logger`

---

## 五、實戰問題彙總（**15 項優先度**）

| # | 問題 | 影響 | 優先度 | 需要動作 |
|---|------|------|--------|---------|
| A1 | Margin call | 帳戶爆倉 | 🚨 P0 | 帳戶 ≥ 60 萬 |
| A2 | 假期跳空 | 單筆爆虧 | 🚨 P0 | Rule #11 已含 |
| B1 | 夜盤流動性 | 滑價 3× | 🚨 P0 | 改 limit or 只做日盤 |
| B4 | Stop fill 不確定 | -25% surprise | 🚨 P0 | Catastrophic cap |
| C1 | 策略衰減 | 未來 alpha 消失 | 🟠 P1 | 季度 re-opt |
| C3 | Portfolio 相關性 | 組合 MDD 疊加 | 🟠 P1 | 上線後 test |
| B2 | API 穩定性 | order 執行失敗 | 🟠 P1 | 備援管道 |
| B3 | 停電斷網 | Stop 消失 | 🟠 P1 | UPS + 期貨商 stop |
| B5 | 結算日夜盤 | 流動性差 | 🟢 P2 | Rule #11 已含 |
| C2 | Regime shift | code 需改 | 🟢 P2 | 半年 review |
| D1 | 心理堅持 | 停止執行 | 🟢 P2 | 紙本 commitment |
| D2 | 手動介入 | 破壞策略 | 🟢 P2 | 嚴禁 rule |
| A3 | 交易稅 | -0.5% Net | 🟢 P2 | 可忽略 |
| A4 | 資金效率 | 82% 閒置 | 🟢 P2 | 組合部署 |
| D3 | 實戰日誌 | 無法 PDCA | 🟢 P2 | 建 logger |

---

## 六、決策路徑（**簡化選項**）

### 選項 A：**完成 5 件套 validation 後 promote**
1. Parameter Sensitivity（MC12，2-4 hr）
2. W4 WFA 9 windows（MC12，6-8 hr）
3. Stress Testing 6 events（MC12，2 hr）
4. 3/5 → 5/5 → 進 promote

### 選項 B：**接受 v1.9.5 為 crash insurance 保留**
- 承認 crash insurance 本質無法過 institutional gate
- 直接 promote 但保守 3% cap（60 萬帳戶只做 1 口）
- 並行進 S4_S（roadmap 下一隻）

### 選項 C：**加實戰保護層再 promote**
- 加 Catastrophic Stop cap（單筆 -150 pts 硬限）
- 加 MAE Guard（V 轉保護）
- 完成 sensitivity + WFA
- promote 5% cap

---

## 七、版本狀態鎖定

**v1.9.5 EXPERIMENTAL = 當前 baseline**
- GA-best defaults 已套（8 個 params）
- Rule #18 5 件套 2/5 完成（MC + Bootstrap PASS）
- 3/5 待 MC12 執行（Sensitivity + WFA + Stress）

**v1.8.0-PROD 保留在 live_simulation**（暫不 KILL）
**v1.9.6 已棄用**（continuation hunt failed）

---

## 八、簽核

**用戶 ruling（2026-07-03）**：
- ✅ 認同「crash insurance」定位
- ✅ MDD 標準 =「一口大台原始保證金以內」
- ✅ 未解決 7 項全記錄，逐步探討
- ⏳ 實戰延伸 15 項待進一步討論

**下一步決策**：**用戶 A/B/C 選一** → 執行

---

## 附錄 A：v1.9.5 8 大參數區塊實戰邏輯逐項驗證（2026-07-04 用戶 Q&A）

### A1. BB Squeeze 偵測邏輯確認

- **BBStd = 2.0**：上下各 2 個標準差（涵蓋 95.4% 常態分布）
- **BWLookback = 120**：一天約 19 個 60M K，120/19 ≈ **6.3 交易日**
- **用戶 2026-07-04 ruling**：6 天太寬鬆，應改 **5 天（95 K）** 或更嚴 **3 天（57 K）**
- **BWRank 計算隱藏 bug**：當 lookback 內所有 BW 相等時，count(<) = 0 → BWRank = 0 → v_Squeeze=True 誤觸發
  - v1.9.5 由於仍有 `Close < LowerBand` 進場 gate 攔截，未實際造成大損
  - **建議**：加 guard `if v_BWCount = 0 and 所有 BW 相同 then v_Squeeze = False`

### A2. 兩次壓縮處理原則（用戶 ruling）

- **絕對當作獨立事件**（不論中間結構是否修復）
- 目的：完整捕捉每一次交易機會，不因狀態機延續而錯失

### A3. Exit 時間管理優化需求

- **UseMidExit** = True + MidExit_MinBars = 2
- 用戶 ruling：**至關重要，code 邏輯需優化至極致**
- 目標：假 breakdown 判斷精準，不因短暫波動誤退

### A4. SP Arm 實戰缺點清單

1. 保護獲利 = 犧牲 upside（若行情續跌，SP 早退錯過大 profit）
2. 反彈幅度誤判（小反彈觸發，之後又下殺）
3. 1M K 夜盤波動觸發（夜盤稀薄可能瞬間觸及 Floor）
4. Retain % 固定（不同波動環境同一 retain 可能不對）
5. Slippage 不對稱（Market order fill 於 next 1M K open）

### A5. P0.5 SP Fire timing

- 觸發判斷：**1M K close** 反彈到 `v_SP_Floor_Price`
- Fill：**next 1M K open at Market**
- （不是 60M K）

### A6. Hunt Quality Gates 過擬合疑慮

- Thrust_Margin_ATR = 0.15：針對 T73 -93.8K case 設計
- Hunt_Max_Stops = 2：針對 v1.9.4 9 個 churn episodes 設計
- 都是 GA 對已知 flaw 的 targeted fix
- **未經 sensitivity 驗證 plateau 寬度**

### A7. 1M Multi-Layer Exit 實戰缺點與擴充需求

見主文 Q8 詳細表格。


---

## 附錄 B：v1.9.6-ANTIHUNT 規劃（2026-07-04 用戶 ruling）

### B0. 用戶新觀察（2026-06 起夜盤現象）

**Stop Hunting / Liquidity Grab**：
- 對手方故意掃散戶程式單 stop → 行情立即反轉回原位
- 夜盤流動性稀薄 = hunt 高發時段
- S3_S BB 突破策略在 LowerBand 附近有 stop 密集區 → 特別容易被 hunt

### B1. 反掃單 5 層設計

| 層 | 機制 | 說明 |
|----|------|------|
| L1 | 夜盤 SL 加寬 22:00-05:00 × 1.3 | Time-based widening |
| L2 | Confirmation SL：連 2 根 1M K close < SL 才觸發 | 過濾單根 spike |
| L3 | Hunt Detection Log | MAE 觸 SL 後 5min 內回升的事件記錄 |
| L4 | Fake Break Re-entry | Hunt 後回升 → 再進場（反利用）|
| L5 | 時段風險 Modifier | Dynamic SL 依時段調整 |

### B2. Round 1 立即實作項目（v1.9.6-ANTIHUNT）

| 順序 | 來源 | 機制 |
|------|------|------|
| 1 | ⑤ L1 | 夜盤 SL 加寬 |
| 2 | ⑤ L2 | Confirmation SL |
| 3 | ① Bug | BWRank equal-BW guard |
| 4 | ③ Exit | 連 2 根 60M K > MidBand |
| 5 | ③ Exit | Peak >= ATR×0.5 才啟 Mid Exit |
| 6 | ④ SP | Peak <100 pts 不 fire |
| 7 | ④ SP | 夜盤 SP fire 需 Volume 確認 |

### B3. Round 2 驗證項目

- BWLookback 敏感度 57/95/120 三組
- 獨立 episode 缺點測試
- Hunt Detection Log 建立
- Hunt Gates plateau sensitivity

### B4. Round 3 進階實驗

- Fake Break Re-entry
- 時段風險 Modifier
- Regime 動態 Exit
- SP Slippage 補救

### B5. 每次 squeeze = 獨立事件的 5 個缺點

1. 繞過 Circuit Breaker（max_stops=2 失效）
2. Fresh Thrust 每次重算（可能誤觸發二次 entry）
3. v_Hunt_Low 被拉高
4. 短期 6.3 天內反覆 squeeze churn
5. 1M_Exit 剛 fire 又 arm

**平衡配套**：Cooldown 期 或 Session Anti-Churn

### B6. BWRank Bug 驗證方案

| # | 驗證項目 | 方法 |
|---|---------|------|
| A | BWLookback 敏感度 | MC12 sweep 57/95/120 |
| B | Bug 觸發頻率 | Python 讀 xlsx 計算 |
| C | Bug 修正前後 | Guard 加後 vs 原版對比 |

