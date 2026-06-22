# S6 ForeignPositionFade — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（**用戶 prompt 即 KILL，0.1 天 — 史上最快**）
**狀態**：💀 **KILLED — NOT FEASIBLE**（不可行，正式結案）
**用戶決策**：2026-06-21 ultracode session（兩個質疑直接命中）
**最後版本**：N/A（連 W0 pre-verify 都沒跑，user gate kill）

---

## 一、為什麼 KILL — 一句話總結

> **「外資 z-score > 2 → 反向 fade」邏輯本身存在 fade-vs-continuation 雙刃劍問題（2022 外資全年賣超 5000 億，TAIEX 仍跌 24% = fade 做多會連虧）；
> 更致命的是 **MC12 無法 native execute** TAIFEX 三大法人資料（需手動每日 import CSV），
> 違反 portfolio 既有 6 策略 + S3 v2.0.4 全 MC12 自動執行的 operational 原則。
> 即使 alpha 真實存在，execution gate 已 fail → 不需要跑 alpha 預檢。**

---

## 二、KILL 觸發 — 用戶兩個質疑直接命中

### 質疑 #1（alpha 層面）：「S6 本身就有利可圖？」

> 「外資/投信不會有連續買超但行情持續跌嗎？」

**我的承認**：無法 ex-ante 證明 fade 邏輯有勝面。

**歷史反例**（fade 做多會被砍頭）：

| 案例 | 外資行為 | 行情 | S6 結果 |
|------|---------|------|---------|
| 2022 整年 | 累積賣超 ~5000 億 | TAIEX 18619→14137 (-24%) | 連續 fade 做多 = 連虧 |
| 2008/05-10 | 連續賣超 | TAIEX 9295→4089 (-56%) | Fade 做多被砍頭 |
| 2020/03 COVID | 瘋狂賣 (z 應 < -3) | 急跌再 V 反彈 | 進場時機差 1 天結果完全相反 |

**Fade vs Continuation 雙刃劍**：
- Fade 假設：z > 2 = 過熱 → mean reversion → 區間震盪市對
- Continuation 假設：z > 2 = 強趨勢 → 跟單 → 大趨勢市對
- 同一 signal 在不同 regime 下**完全相反方向才賺**
- 跟 S5 LONG/SHORT asymmetry **同類陷阱（L20）**

→ **沒有實證下不能保證哪個 dominant**

### 質疑 #2（execution 層面）：「MC12 能執行嗎？我認為不行！」

**用戶 100% 對。MC12 架構限制致命**：

```
TAIFEX 三大法人資料流：
  15:05  TAIFEX 官網 publish 三大法人交易資料 (HTML/CSV)
  需要:
    1. 人工/scraper 下載 CSV
    2. 解析欄位（外資期貨多空餘額）
    3. import 到 MC12 作為 custom data series
    4. MC 計算 60-day z-score
    5. 隔日 08:45 開盤前完成所有步驟
  
MC12 native 能力：
  ❌ 不能直接 fetch HTTP API
  ❌ 不能讀外部 CSV 自動更新
  ❌ 不能在收盤後自動觸發 import
  ✓ 可以手動 import CSV 為 ASCII Mapping data feed
  ✓ 可以在 PowerLanguage 中讀取 Data2/Data3
```

### 部署選項都不及格

| 選項 | 動作 | 評估 |
|------|------|------|
| A 完全手動 | 每日 15:30 下載 → MC import → 隔日手動下單 | ❌ 違反自動化原則 |
| B 半自動 | Python signal → Telegram → 手動下 MC12 | ⚠️ 仍手動 |
| C 完全脫離 MC12 | Python + 券商 API | ❌ 跟既有架構脫鉤 |
| D MC custom DataFeed | 寫 MC 插件接 TAIFEX | 🔴 開發成本 > 策略價值 |

### Operational risk dimension FAIL

CLAUDE.md Rule #13 institutional 10-dim 之一 = operational risk。
- 既有 portfolio：6 策略 + S3 v2.0.4 = 100% MC12 自動執行
- S6 = **唯一需要人工介入** = operational risk FAIL → 直接 disqualify

---

## 三、KILL 速度演進（lessons compound 達到極致）

| 策略 | KILL 速度 | KILL 觸發點 |
|------|---------|-----------|
| S2 InsideBarBreak | 5 版本 + 多週 | 5 次迭代後實證 |
| S4 TurnOfMonth | 1 天 | W1 同日 28y robustness |
| S5 SPX_Overnight | 0.5 天 | W0 pre-verify |
| **S6 ForeignPositionFade** | **0.1 天** | **用戶 prompt 即 KILL（pre-W0）** |

**S6 KILL 速度比 S2 快 50×+** → lessons + 用戶 sharp judgment compound 到極致

---

## 四、學自 S6 的 **1 個關鍵 lesson (L21)**

7. **L21: MC12 Execution Feasibility 是 pre-everything gate**
   - 任何策略在開始 alpha pre-verify **之前**必須先確認 MC12 native auto-execute 可行
   - Non-MC12-native data source（如 TAIFEX 三大法人、券商主力券商、自家爬蟲）= 直接 KILL
   - 即使 alpha 真實存在，無法 deploy 就沒有 research 意義
   - 機構級紀律：operational risk 是 pre-alpha gate，不是 post-alpha consideration

**判定流程**（**新 SOP 必加**）：
```
Pre-W0 Gate 1: MC12 execution feasibility check
  ✓ 資料源 native to MC12 (價格 / volume / 持倉量) → PASS
  ✓ 已有 ASCII Mapping 載入機制 (像 SPX via yfinance + CSV) → PASS
  ❌ 需要人工 daily import → FAIL
  ❌ 需要外部 API (TAIFEX scraper / 三大法人) → FAIL
  ❌ 需要 alert + manual order → FAIL

Pre-W0 Gate 2: Operational complexity vs portfolio coherence
  ✓ 跟既有 6+1 策略架構一致 → PASS
  ❌ 引入新 operational layer → FAIL
```

---

## 五、累積 lessons 演進（S2-S6）

| 策略 | Lessons | 累計 |
|------|---------|------|
| S2 InsideBarBreak | L1-L13 (13 個) | 13 |
| S4 TurnOfMonth | L14-L18 (5 個) | 18 |
| S5 SPX_Overnight | L19-L20 (2 個) | 20 |
| **S6 ForeignPositionFade** | **L21 (1 個)** | **21** |

每個 KILL 都在 distill 新 lessons → 將加速 S7+ 預判

---

## 六、Roadmap 嚴重損傷評估

**4/6 候選 KILLED**（S2, S4, S5, S6）→ Roadmap 設計品質受質疑

| 策略 | 狀態 | KILL 階段 |
|------|------|----------|
| ~~S2 InsideBarBreak~~ | 💀 KILLED | 多週實證 |
| ~~S4 TurnOfMonth~~ | 💀 KILLED | W1 同日 |
| ~~S5 SPX_Overnight~~ | 💀 KILLED | W0 pre-verify |
| ~~**S6 ForeignPositionFade**~~ | 💀 **KILLED** | **pre-W0 user gate** |
| S7 PreSettlementHarvest | 🔴 高風險未動 | (L16 calendar decay 預警)|
| S8 FOMC_OvernightFade | 🟡 中風險未動 | (樣本 8/yr 不足) |

---

## 七、KILL 規範

```
若你看到本檔（S6_FINAL_VERDICT.md）：
  ❌ 不要寫 S6 spec / .pla
  ❌ 不要寫 TAIFEX scraper for S6
  ❌ 不要試圖在 MC12 import 三大法人 CSV
  ✅ 可以讀本檔 + L21
  
重啟條件（極嚴）：
  1. MC12 平台升級為原生支援 TAIFEX feed (極不可能)
  2. 或建立 separate non-MC12 execution platform (跳脫 portfolio)
  3. 用戶明確要求 + 接受 operational risk
```

---

## 八、資源轉向 + Roadmap 重評估強烈建議

剩餘 candidates 風險（用 L14-L21 預判）：

| 策略 | L14 跨期 | L16 教科書 | L19 microstructure | **L21 MC12 execute** | 綜合 |
|------|---------|----------|------------|---------|------|
| S7 PreSettlementHarvest | ⚠️ | 🔴 | ✓ | ✓ | 🔴 高風險（Calendar）|
| S8 FOMC_OvernightFade | ⚠️ 樣本不足 | ✓ | ⚠️ | ✓ | 🟡 中 |
| S9-S15 | TBD | TBD | TBD | TBD | 全部 TBD |

**強烈建議**：
1. 暫停按 roadmap 順序開新策略
2. 認知 portfolio **可能已 saturate**（6 frozen + S3 v2.0.4 = 7 個 sleeves）
3. 把資源轉去 portfolio refinement / monitoring 而不是新策略
4. 或者：用 L1-L21（21 個 lessons）寫 STRATEGY_RD_SOP_v2.md 強化未來流程

---

## 九、相關文件交叉參考

- **S2 結案**：[../S02_InsideBarBreak/S2_FINAL_VERDICT.md](../S02_InsideBarBreak/S2_FINAL_VERDICT.md)
- **S4 KILLED**：[../S04_TurnOfMonth/S4_FINAL_VERDICT.md](../S04_TurnOfMonth/S4_FINAL_VERDICT.md)
- **S5 KILLED**：[../S05_SPX_Overnight/S5_FINAL_VERDICT.md](../S05_SPX_Overnight/S5_FINAL_VERDICT.md)
- **Roadmap (需 update)**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **Memory feedback (KILL 必文件化)**：`feedback_strategy_kill_must_document.md`

---

## 十、用戶聲明

> 「1. S6 這策略是本身就有利可圖? 你要怎麼確認外資大買後，隔天做空有贏面?
>    外資跟投信不會有連續買超但行情持續跌?
>  2. S6 的策略，實戰角度來說，能夠完整在 MTC 執行? 我認為不行!」  
> — 2026-06-21 ultracode session

用戶**兩個質疑都打中要害**：第一個直擊 alpha 假設不對稱性，第二個直擊 execution feasibility。**第二個直接 disqualify 策略**，第一個讓 alpha 預檢變得 moot。

對機構而言這是**理想 KILL 流程**：問對問題比跑大量分析更有效率。

---

## 十一、Final stamp

```
S6 ForeignPositionFade
Status: KILLED
Date:   2026-06-21 (same day as S4 and S5)
Reason: 
  1. MC12 native execution NOT FEASIBLE (TAIFEX data needs manual import)
  2. Operational risk dimension FAIL (Rule #13)
  3. Alpha thesis (fade z>2) has fade-vs-continuation ambiguity, 
     2022 case proves continuation can dominate
Effort: 0.1 day (no pre-verify, no spec, no .pla)
Lessons: L21 contributed (MC12 execution as pre-everything gate)
KILL speed: 50x+ faster than S2 (user gate compound with lessons)
Replaced by: ROADMAP RE-EVALUATION REQUIRED
```

---

**Four strikes (S2, S4, S5, S6) in one day — roadmap quality itself is now the question.**
