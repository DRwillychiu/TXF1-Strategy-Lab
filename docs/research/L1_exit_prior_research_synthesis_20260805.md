---
title: L1_TrendLong 出場機制既有研究總表 — 已知結論與已否決方案
created: 2026-08-05
author: Claude (research synthesis)
type: synthesis
scope: L1_TrendLong exit architecture (P3 initial SL / P3b engine guard / P4 trail / P7 stop profit)
data_source: 既有研究文件之整理，未執行任何新回測、未執行任何新模擬
new_backtest: false
new_simulation: false
read_only_note: 本文為唯讀彙整，不修改任何既有檔案；所有數字皆搬運自出處，不重新計算
primary_sources:
  - docs/research/L1_*.md (18 份)
  - docs/handoffs/HANDOFF_L1_*.md
  - docs/strategy_archive/L1_v26_20260622_gap_miss_case.md
  - strategies/live/L1_TrendLong/*.pla|*.md
  - docs/policies/lesson_L2*.md
  - .claude/skills/adversarial-engineering-sop/SKILL.md
---

# L1_TrendLong 出場機制 — 既有研究總表

> **本文用途**：2026-08-05 使用者要重新檢視 L1 出場結構（急拉時移動停利跟不上）。
> 2026-07 曾有一整輪密集的 "L1 stop campaign"，已試過並否決大量方案。
> 本文把那些結論搬運出來，避免重跑已失敗的實驗、避免把已證實有害的機制裝回去。
>
> **鐵律三條（引用自出處，非本文發明）**
> 1. `docs/research/L1-L5_structural_audit_20260721.md:149` —
>    「Out-of-ideas on exit side (3 independent attempts failed, direction permanently closed
>    per feedback_trend_let_profits_run.md).」
> 2. `docs/handoffs/HANDOFF_L1_STOP_CAMPAIGN_20260722_EOD.md:31` —
>    「已封死的路 (勿重開): 停損收緊 34 變體 / 固定點數 cap / 固定 % 0.4-1.0% /
>    daily loss cap (V2.8) / P3b buffer / 窄域 reclaim / 廣義再進場 (Plan C)」
> 3. `strategies/live/L1_TrendLong/L1_TrendLong_review.md:41` — TL_TP 25% 虧損出場，
>    「依用戶裁示，此為讓利潤奔跑的必要成本，不再視為缺陷」

---

## 0. 驗證來源分級（讀本文前必看）

附錄 C「幻想成交」陷阱的存在，就是因為離線數字與原生回測數字可以差 26 倍。
本文所有數字都標記來源等級：

| 標記 | 意義 | 可信度處置 |
|---|---|---|
| `[MC12]` | MultiCharts 12 原生回測報表匯出 | 可直接引用 |
| `[MC9]` | MultiCharts 9 實盤平台原生回測 / A/B | 可直接引用 |
| `[離線-py]` | Python / 1M bar 重建 / 重播測試台 / MAE 模擬 | **不可直接宣稱上線效益**（SOP 第 7 步禁止） |
| `[離線-代理]` | 以 Daily bar 代理 45M、或以 MFE 端點代理路徑 | 僅為一階訊號 |
| `[推導]` | 純邏輯 / 算術推導，無回測 | 僅供設計討論 |
| `[未標明]` | 出處未寫明用哪個工具產生 | 需要重新確認才可引用 |

> **關鍵對照案例（記住這組數字）**：同一個 1.2% clip 提案，
> MAE 離線模擬 = **+600 pts**；改用真實 bar 路徑重播 = **+23 pts**（`docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:38-40`）。
> 另一組：P3b 取腿修復的離線悲觀估計 = **-124 pts**；MC12 實測 = **-36 pts**（`docs/research/L1_V29_p3b_fix_spec_20260722.md:83,89`）。

---

# A. 已否決方案總表

## A-0. 「出場端保護三次陣亡」是哪三次

memory `feedback_trend_let_profits_run` 記載的三次陣亡，primary source 全部找到。
**重要：三次裡沒有一次是 L1**——兩次是 L5，一次是 S1。這代表「出場端保護方向永久關閉」
這條鐵律，對 L1 是**繼承而來的跨策略禁令**，不是 L1 自己撞過的牆。

| # | 策略/版本 | 機制（一句話） | 陣亡日期 | 量化依據 | 根因 | 出處:行號 |
|---|---|---|---|---|---|---|
| **陣亡一** | **S1 NightMomentum v2.5 Variant B**（Trail_Mode=2） | 真移動停損：獲利達 `TrailActATR(1.5)×ATR` 啟動，之後停損鎖在 `HighestClose − TrailOffATR(0.7)×ATR`，只進不退 | 2026-06-13 | 淨利 +1,720,600 → +1,335,000（**−385K NTD**）；MDD −269,800 → −315,000（惡化）；Trail_B 自身**勝率 88.2%**、觸發 68 筆；TP 219→204（−15）、Time 460→438（−22，大尾巴被截）`[未標明]` | 「高勝率 trail 卻截斷大尾巴，跟 L4/L5 詛咒一樣」；「證實『保護獲利型 trail』會破壞 gap 套利 alpha」 | `docs/archive/handoffs/handoff_20260613_s1_v26.md:45,56,58-61,69,243`；程式碼 `strategies/live_simulation/S1_NightMomentum/S1_NightMomentum.pla:130,171,458,466-469` |
| **陣亡二** | **L5 BreakoutLong v19.8**（SP 五變體 B/C/D/E/F） | Stage 1 停利地板 = `EntryPrice + Peak×(1−Retain%)`，五種參數組合 A/B 測試 | 2026-06-13 | A baseline 淨利 **+1,563,200** / PF 1.93 / MDD −215,600 / Top-10 保留 100%；B +777,200（**−50.3%**）、C +1,040,200（−33.5%）、D +1,344,800（−14.0%，最佳仍 FAIL）、E +968,800（−38.0%）、F +1,280,200（−18.1%）。三筆巨型贏家被全變體斬首（2026-04-07 +376,400→最低 +6,800 等），合計**被殺 −680,400** `[MC9]` | 「策略尾巴集中度 >70% 時，任何 SP 截斷都會自殺」（L5 Top-10 佔淨利 88%）；「Scale-Out 緩衝是理論上的保護，實證上不存在」 | `docs/strategy_archive/L5_v198_variant_results.md:3,26-31,55-61,94,144,171`；設計 `docs/strategy_archive/L5_v198_pretrail_sp_design.md:34-46,115-124` |
| **陣亡三** | **L5 BreakoutLong v19.9 Stage1_BE** | Stage 1 保本機制（breakeven） | 2026-07-05 CLOSED | **−19K MC9 A/B result** `[MC9]`；另一處記載為「Stage1_BE FAILED (**PF<1.0**)」（無 NTD 數字） | repo 內**未見 Stage1_BE 專屬 root cause 陳述**，只有 P9 段落對三次嘗試的統一結論 | `docs/research/L1-L5_structural_audit_20260721.md:145,149`；`docs/live_optimization/README.md:17` |

**三次陣亡的統一結論（原文）**
`docs/research/L1-L5_structural_audit_20260721.md:149`：
「Out-of-ideas on exit side (3 independent attempts failed, direction permanently closed
per feedback_trend_let_profits_run.md).」

**同段的痛點量化**（`docs/research/L1-L5_structural_audit_20260721.md:147`，L5）：
58 trades with MFE > 0 ended at or below zero, totaling **1,826,000 NTD** of wasted profit；
最差案例 2024-05-03，MFE +244 pts → exit at breakeven −10 pts。
→ 即：**已知有 182 萬的浪費利潤，但三次嘗試回收它都失敗，故接受為結構成本。**

**⚠️ 陣亡一的策略歸屬有 [來源衝突]**：見 §F-1。ENGINEERING_SYSTEM.md 兩處都把 Trail_B −385K
記在 L1/L24 名下，但 10 處獨立 primary source 一致指向 **S1**。

**第四個相關案例（不在「三次」之內，但同向）**：
`docs/methodology/ENGINEERING_SYSTEM.md:151`（AP-4）「100% 勝率機制 = 淨損 | L4 BE/SP **−345K~−82K**」`[未標明]`；
`docs/methodology/ENGINEERING_SYSTEM.md:62`（R-D1）「進場品質過濾 > 持倉中段保護 | L4 Path A **+106K** 完勝 BE/SP」`[未標明]`。

---

## A-1. L1 專屬的已否決方案（依時間排序）

### A-1-a. 出場層直接相關（最相關於今天的議題）

| 代號/版本 | 機制描述 | 否決日期 | 量化依據 | 根因 | 出處:行號 |
|---|---|---|---|---|---|
| **Option D 週線反轉出場** | 加一層「週線收盤跌破 W20+W60 雙均線即出場」（移植自 L2） | 2026-06-12 | 虧損單平均持倉僅 **14.5 小時**；週線雙均線跌破需**數週** `[離線-py 交易明細統計]` | 時間尺度論證：「追蹤停損永遠先打到，**週線出場層對 L1 是死碼**」 | `strategies/live/L1_TrendLong/L1_TrendLong_review.md:317`；`:395` |
| **L2 的 TTP（1.5% 反彈出場）不移植** | L2 StopProfit 模組附帶的追蹤停利，V2.6 移植時刻意丟棄 | 2026-06-12 | 無量化，純角色論證 `[推導]` | 「與 MA55 追蹤角色重複」 | `strategies/live/L1_TrendLong/L1_TrendLong_review.md:380`；`strategies/live/L1_TrendLong/L1_TrendLong_annotated.md:130` |
| **冷卻機制（L4 式 Cooldown）** | 停損後強制冷卻一段時間才允許再進場 | 2026-06-12 | 虧損後 **<6h 再進場勝率 34.7%（四組中最高）**，+512,000；6-24h 25.0%；24-72h 32.4%；>72h 24.7% `[離線-py 469 筆明細統計]` | 「突破失敗後立刻再突破常是真趨勢的二次確認。**冷卻機制對 L1 有害，不做**」 | `strategies/live/L1_TrendLong/L1_TrendLong_review.md:395`（§9.5 表） |
| **Plan C：被動出場後再進場（廣義再進場）** | TL_SL / TL_SP / TL_SL_Gap 出場後主動再進場 | 2026-07-02 | 假說 +2.1M，但 **MC9 path-level A/B（A+C 合併，SP500）= Net 3,018K vs Plan A 單獨 3,938K = −920K drag**；69 筆再進場交易淨負 `[MC9]` | 「Re-entry positions hit SL at worse prices than original breakout entries」→ Plan C code removed | `strategies/live/L1_TrendLong/L1_TrendLong.pla:72-79` |
| **窄域 Reclaim**（停損後 N 根內收盤重回進場價 → 免 cross 再進場） | 針對 64 筆死亡候選 | 2026-07-22 夜 | N=3：TRUE reclaim 4 筆 +474 / FALSE reclaim 11 筆 −1,263 / 淨 **−789**；N=5：TRUE 4 筆 +474 / FALSE 16 筆 −1,682 / 淨 **−1,208** `[離線-py 重播]` | 「深度死亡的輸家也常在 3 根內反彈回進場價之上（死貓反彈）——FALSE:TRUE = 3:1~4:1」；「用戶直覺『二次進場品質不如第一次』被定量證實」 | `docs/research/L1_buffer_reclaim_tests_20260722.md:34-42,47,49` |
| **SP giveback 收緊（`profitReturnPrcnt_Long` 55 → 35/30）** | **⚠️ 狀態 = PLAUSIBLE，非否決**。列在此表是為了記錄它的紅旗 | （未結案） | +1,565~+1,948 pts / MDD 零變化 / Top-10 存活 `[離線-py 重播]`，但帶 **±300 pts noise floor**（B6 錨點殘差 −269）且 **+1,688 (86.6%) 來自 2026 單一年**，前六年僅 +259（B7） | 「列為 PLAUSIBLE 候選, 只可經 MC12 一鍵 A/B + 分年檢視後再議, **不得直接上 live**」 | `docs/research/L1_stop_mechanism_deep_research_20260722.md:236`；`docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:48-56,68` |
| **P7 threshold × giveback 64-combo sweep** | 8 檔 threshold × 8 檔 giveback 完整掃描 | 2026-07-23 DEPRIORITIZED（**從未執行**） | — | 「P7 is not the primary optimization target...**Decision NOT to pursue**: P7 parameter sweep. Focus shifts to P3 optimization.」 | `docs/research/L1_V30_backtest_analysis_20260723.md:139,141`；規劃 `docs/research/L1_IOG_migration_spec_20260723.md:413-416,525-526` |

### A-1-b. 停損層（P3/P3b）已否決 — 34+ 變體

> `docs/research/L1_stop_forensics_20260722.md:101`：
> 「7 月 MDD 由 C-up 出血區的三連追多構成; **34 個停損 overlay 全部失敗**的原因也在此:
> 停損在錯誤的進場後怎麼調都是輸。」

| 代號 | 機制描述 | 否決日期 | 量化依據 | 根因 | 出處:行號 |
|---|---|---|---|---|---|
| **固定點數 cap**（cap150~cap500） | MAE > cap 者改於 −(cap+5) 出場 | 2026-07-22 | cap150 淨利 +8 / 觸發 39 / 誤殺贏家 7；cap200 −309；cap250 −923；**cap300 −1,927**；**cap350 −2,768**；cap400 −1,211；cap500 +219 `[離線-py MAE 模擬]` | 「2025-2026 年代所有 cap 全部虧損（−308~−2,348）…收緊停損救不了現在的 regime，反而在現在的 regime 傷害最大」；另違反 CLAUDE.md Rule #17「禁止固定點數 cap」 | `docs/research/L1_stop_mechanism_deep_research_20260722.md:90,92-100,102-104` |
| **固定 % 停損 0.4-1.0%** | MAE > cap% × 進場價 → 該價位出場（455 筆全期） | 2026-07-22 | 0.4%：淨利 −654 / **MDD +194（惡化）**；0.5%：+257 / +89；0.6%：−1,422 / **+720**；0.7%：−2,153 / **+1,300**；0.8%：−3,024 / **+1,807**；1.0%：+58 / 0 `[離線-py MAE 模擬]` | 「0.5%-0.8% 全部是陷阱區…殺掉 6 月壓線倖存者 #447/#449（**+2,305 pts**），且 Closed MDD 不減反增——收緊停損無法改善用戶最在意的 MDD」 | `docs/research/L1_stop_mechanism_deep_research_20260722.md:110-118,120-124` |
| **V2.9 提案：per-trade 災難斷路器（1.2% clip）** | `Frozen_SL = MaxList(ATR停損價, EntryPrice×0.988)` | **2026-07-22 死亡** | 原宣稱 **+600 pts**/6.5 年 → 對抗式審查後修正為 **+23 pts / 6.5 年觸發 1 次** `[離線-py，兩版]` | **BUG B4 幻想成交**：深 MAE 事件多為跳空/崩盤棒，tighter stop 的實際成交價與 ATR 停損幾乎相同。「殘值僅剩『連續陰跌型黑天鵝』保險，無 EV 主張，不值得動 live 程式碼」 | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:38-41`；`docs/research/L1_stop_mechanism_deep_research_20260722.md:118,123,230-231` |
| **K 棒重播內層停損 第一輪 19 變體**（A 訊號棒低點 / B swing low / C 大陰吞噬 / D 時間停損 / E 連續收低） | 在既有停損內再加一層 K 棒結構觸發 | 2026-07-22 | baseline net 12,203 pts / MDD 2,038。A 最佳 d_net **−1,108**；B 最佳（N=3）**−3,763**、誤殺贏家 **128**；C 最佳 **−5,370**、誤殺贏家 **127**；D 最佳 −936；E 最佳（k=5）**−1,726** `[離線-py 重播]`。B2/B5 修正執行模型後 A 惡化至 −1,904~−2,435、B 惡化至 −5,857~−5,966 | 全數負值；45M K 棒訊號無法分辨贏家/輸家（L33 原則） | `docs/research/L1_stop_mechanism_deep_research_20260722.md:132-140`；修正 `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:28-31,43-46` |
| **K 棒重播 第二輪：水面下閘控版 8 變體**（只在浮虧時觸發） | 同上，加「僅浮虧時啟用」閘門 | 2026-07-22 | E 連續收低 k=4 underwater：d_net **+25** / d_MDD +86（"唯一非負, 但為 no-op 級"）；B swing N=3 underwater：d_net **−1,067** / d_MDD −152（「買 MDD −152 要花 −1,067」）；其餘 3 變體 −849~−2,397 `[離線-py 重播]` | 「19+8 個變體中無任何一個能實質拯救 7 月 −2,038 streak 而不同時摧毀更多獲利」 | `docs/research/L1_stop_mechanism_deep_research_20260722.md:142-148,152` |
| **P3b Buffer 全掃描**（0~50 pts） | 引擎層停損加緩衝點數，pen ≤ buf 者存活 | 2026-07-22 夜 | buf10 −204 / buf15 **+64**（相對 buf=0 +343）/ buf20 +20 / buf30 −122 / buf50 −241 `[離線-py]` | 「校準樣本實質只有 2 個可測事件（#66 pen=8, #95 pen=11）；效益量級與**模型殘差（±279）同數量級**；違反『進出場禁用固定點數』強制規範」→ 不推薦實作 | `docs/research/L1_buffer_reclaim_tests_20260722.md:14-28,46-48` |
| **P8 Daily Loss Cap（V2.8）** | `DailyLoss_Enable=True, MaxCount=3, MaxNTD=100000`，觸發後封鎖新進場 | 2026-07-22 | Net 2,292,800 → **2,125,800（−167,000）**；PF 1.383 → 1.357；**MDD −502,200 → −602,400（−100,200 惡化）**；Sharpe 0.263→0.257；Return/MDD 4.57x→3.53x `[MC12]` | ① L1 ATR 停損在正常高波動就產生 80-100K 虧損，NTD 門檻 100K = 一次正常停損就觸發；② 停損後再進場是 L1 最高 EV 型態（<6h 勝率 34.7% 最高）；③ Count 觸發在 6.5 年回測**從未觸發**（L1 每日僅 0.29 筆）；④ 擋掉 #121 虧損 −20,600 卻同時擋掉 #449 獲利 **+187,600** | `docs/research/L1_V28_backtest_verdict_20260722.md:5-7,13,19-34,36,44-59,60,67-73` |
| **封鎖所有停損後第 2 筆進場**（假設性） | 極端版的冷卻機制 | 2026-07-22（PAUSED，數據不支持） | 避開損失 31 筆 +2,994 pts；錯失獲利 19 筆 **−8,038 pts**；淨 50 筆 **−5,044 pts / −1,008,800 NTD** `[MC12 明細 + 離線推算]` | 「Blocking 2nd trades would destroy **49.8%** of L1's total net profit」；2nd trade after stop-out 的 EV = **+100 pts/trade** | `docs/research/L1_daily_loss_cap_points_analysis_20260722.md:83-84,90-98,117-122` |
| **Layer 1b 行為觸發收緊**（連三黑 / 大陰吞噬 → Primary SL 距離減半，觸發一次鎖定） | P3 架構的第 1b 層 | **2026-07-24 KILLED** | GATE1：TriggerA↔Family E k=5 = −1,726 pts；TriggerB↔Family C ungated = 殺 127 個贏家 / −5,370 pts `[離線-py]`。GATE2 Fire-Quality Proxy（81 fires）：**Saved rate 50.6%（上限 40%，超標 10.6pp）**、Killed rate 40.7%（僅壓線）、False-halving rate 46.9% `[離線-代理，Daily bar 代理 45M]` | 四個獨立原因：① 觸發偵測重複已否決變體 ② L33 系統性原則（45M K 棒訊號無法分辨贏家/輸家）③ GATE2 數據面否決 ④ 用戶 2026-07-24 裁示「今天不會做任何減碼」框架限制。原文：「Layer 1b as specified does not distinguish winners from losers with acceptable precision on daily data.」 | `docs/research/L1_Layer1b_kill_summary_20260724.md:6,31-38,53-75,77-83,111`；`docs/research/L1_P3_python_analysis_20260724.md:111-176,158-168,173,176`；`strategies/research/L1_TrendLong/L1_v31/L1_v31_spec_20260724.md:12,29,660` |
| **L1_c 每日回撤停損**（10-day max close-to-close drawdown × ratio 取代 ATR 主停損） | P3 Layer 1 候選 | 2026-07-24 ABANDONED | Ratio=0.7 時 L1_c 僅約束 **8.7% of trades (41/469)**；index ≥ 20K 時 L1_c×0.7 比 ATR×1.5 **寬 2-8 倍** `[未標明——出處只寫 "Diagnostic log"]` | 「L1_c scales WITH volatility (same direction as ATR)」→ 沒解決問題，退回 V3.0 改採 SL_Pct | `docs/research/L1_V31_SL_Pct_optimization_summary_20260724.md:139-149`；`docs/handoffs/HANDOFF_L1_V31_20260724_EOD.md:17-20` |
| **X4 Breakout Quality Filter（V3.2）** | 用 Data4(1M) 對每個突破訊號打分（Momentum / Flirtation / Ascending Lows），夜盤需 score=3、日盤 ≥2 — **進場端，非出場端，但示範了跨時框脆弱性** | **2026-07-25 KILLED** | V3.1 MC12：445 筆 / +1,772,600 / PF 1.359 / MDD −476,600；V3.2 MC12：371 筆 / **+1,536,800** / PF 1.323 → **−235,800（−13.3%）**；同期 **Python projection：283 筆 / +3,464,800 / PF 2.614**（≈ MC12 實測的 2.25 倍） `[MC12 兩欄 + 離線-py 一欄，文件自帶三欄對照]` | 「Flirtation cliff-edge」：Breakout_Level 在 MC12 原生 45M bar 與 Python `resample('45min')` 產生的 bar 邊界不同 →「This is structural and unfixable — the two platforms will never produce identical 45M bar boundaries.」 | `strategies/research/L1_TrendLong/L1_v31/L1_V32_X4_FINAL_VERDICT.md:3,5,9-19,23-30,37-40,49-50,64-69,83-96` |

### A-1-c. 只在 handoff 被列名、量化細節未在 repo 找到

`docs/handoffs/HANDOFF_L1_STOP_CAMPAIGN_20260722_EOD.md:31` 的封死清單中，
「停損收緊 34 變體」是上表 19+8+若干變體的合稱；其餘各項均已在上表找到量化細節。
**唯一沒找到獨立量化文件的是「廣義再進場 (Plan C)」的 2026-07-22 版本**——
但 `L1_TrendLong.pla:72-79` 有 2026-07-02 的 Plan C MC9 A/B 數字（−920K），推測為同一件事。
標記 `[來源衝突]` 見 §F-5。

---

# B. 已採用並仍在線上的機制（v3.1）

程式碼真相源：`strategies/live/L1_TrendLong/L1_TrendLong.pla`（706 行，header 版本 `V3.1`，第 5 行）。
出場架構總覽在 `:189-207`；`Final_Exit_Price = MaxList(Exit_Price_Trail, MaxList(Exit_Price_SL, stopProfitPrice_L))`（`:590-591`）——
**單一停損單、三個地板取最嚴者**。

| 機制 | 採用時的量化依據 | 當時的對照組 | 出處:行號 |
|---|---|---|---|
| **P3 凍結初始停損（V2.5, 2026-06-12）**：進場當根收盤算一次後鎖死 | 無 A/B 數字。動機是使用者實盤 reload 觀察到停損改變 → 確認舊碼每根 K 棒用當下 ATR 重算（漂移缺陷） `[使用者實盤觀察]` | 舊碼（每根重算） | `strategies/live/L1_TrendLong/L1_TrendLong.pla:36-43`；`L1_TrendLong_review.md:394` |
| **P3 Leg1 ATR 腿 `Entry − ATR45 × 1.5`** | 無獨立依據；沿用 V2.5 之前的設計 | — | `.pla:192,228` |
| **P3 Leg2 Daily cap 腿 `Entry − Daily_ATR × 0.5`** | 設計意圖是「日線腿作為停損距離上限」，但法醫證實 **ATR45×1.5 在 99-100% 的進場當下都是較小腿 → Daily 腿實際上是死碼** `[離線-py 1M 重建，456 筆，p90 誤差 1 pt]` | — | `.pla:193,229`；`docs/research/L1_stop_forensics_20260722.md:17,20,47-52` |
| **P3 Leg3 SL_Pct 百分比腿（V3.1, 2026-07-24）**：`Entry − Entry × SL_Pct/100` | MC12 optimizer sweep SL_Pct 0.3-1.5 step 0.1（13 組）。Winner 0.5%：Net **1,901K** / PF **1.330** / MDD −477K / 481 筆 / WR 35.3%。Head-to-Head vs V3.0：**Net +57K (+3.1%)**、PF +0.009、MDD +3K（較佳）、5/7 年改善 `[MC12]` | **V3.0 baseline（SL_Pct=0 兩腿模式）**：Net 1,843K / PF 1.321 / MDD −480K / 474 筆 | `docs/research/L1_V31_SL_Pct_optimization_summary_20260724.md:29-38,53-69,87-95,99-109` |
| **P3b Immediate Stop Guard（V2.6+，V2.9 修正為 MinList + SetStopContract）**：`SetStopContract` + `SetStopLoss`，進場成交瞬間生效 | MC12 Gate（2026-07-22）：預測 12 筆同棒死獲救 → **12/12 全命中**；預測 2 筆反殺 → **2/2 命中**（#66 +447→−38 / #95 +273→−120）；淨利影響離線預估 −124 pts、**MC12 實測僅 −36 pts（−7,200 NTD / 6.5 年）**；Closed MDD 2,038 → **2,038 不變** `[MC12]` | V2.7（舊 MaxList 取鬆腿版本） | `docs/research/L1_V29_p3b_fix_spec_20260722.md:77,81-85,89`；`.pla:97-127,130-136,516-531` |
| **P4 MA55 追蹤停損**：`v_Trail_High = MaxList(v_Trail_High, maTrail − TrailOffset)` | 無獨立採用依據（策略原生機制，V2.3 之前即存在）。出場標籤統計：TL_TP **157 筆 / 33.5% / 勝率 74.5% / +7,367,600** `[MC9 469 筆明細]` | — | `.pla:201,585-589`；`L1_TrendLong_review.md:34,86` |
| **P4 單向棘輪（V3.0, 2026-07-23）**：`MaxList` 保證 trail 不下降 | 無獨立 A/B。理由：「Old bi-directional breathing let the effective stop sag during pullbacks」 `[推導]` | 舊雙向 breathing 版 | `.pla:163-165` |
| **P7 Stop Profit Guard（V2.6, 2026-06-12，移植自 L2 Trendbearish_V1 SECTION 12）** | **469 筆 MFE 審計**：83 筆曾達 +100 pts 卻虧損收場（**−1,520,200**）；MFE≥250 的 130 筆回吐中位 **50%** / P75 80% / P90 **112%（轉虧）**；**Top-10 終點回吐最大僅 28%（中位 ~18%）→ 55% 容忍對肥尾有巨大安全邊際**。回檔規則模擬（樂觀界）250/55% = 受影響 55 筆 / **+1,927,630** `[離線-代理：僅終點檢查，中途路徑觸發不可見]` | V2.5（無 SP 層） | `L1_TrendLong_review.md:326-355,344-355,370-374`；`.pla:47-66` |
| **P7 IOG 化 + 門檻 500→200（V3.0, 2026-07-23）** | MC12 兩跑對照：T500 Net **2,399,000** / PF **1.396** / MDD −498,000 / 458 筆；T200 Net **2,074,000** / PF 1.348 / MDD −493,200 / 508 筆 → **T200 在淨利、PF、Sharpe 全期皆劣於 T500** `[MC12]` | T500 | `docs/research/L1_V30_backtest_analysis_20260723.md:5-7,11-35,37-47,76,90-91,130-141` |
| **V2.9.1 出場標籤 taxonomy（損益側互斥）** | MC12 re-gate：**462/462 筆進出場價/時間/損益完全相同**，淨利 12,167.0 = 12,167.0；TL_TP 138→103（−35）、TL_TSL 0→35（+35）；損益側互斥 **0 違規** `[MC12]` | V2.9 | `docs/research/L1_V29_p3b_fix_spec_20260722.md:109,118-127` |
| **P5 v3 假日平倉**（出場層第 8 層） | TL_Holiday **24 筆 / 勝率 83.3% / +913,800 = 淨利的 28%** `[MC9 469 筆明細]`；且屬「假日平倉鐵律」（用戶裁示，不需 A/B 驗收） | — | `L1_TrendLong_review.md:35,42`；`docs/methodology/entry_exit_sop.md:79-91` |
| **無目標停利（第 4 層刻意留空）** | Top 5 交易 = 淨利 73.0%；**Top 10 交易 = 淨利 104.4%**（拿掉前 10 名，L1 在 6.5 年是虧損策略） `[MC9 469 筆明細]` | — | `L1_TrendLong_review.md:48-54`；`docs/methodology/entry_exit_sop.md:48,57` |

**出場九層 SOP 對 L1 的現況判定**（`docs/methodology/entry_exit_sop.md:155`）：
初損 ✅雙層+凍結(V2.5)｜回檔保護 ✅SP 250/55(V2.6)｜追蹤 ✅MA55｜目標 —（正確）｜
時間 —（數據判免：虧損單 14.5h 自亡）｜結構失效 —（數據判免：追蹤必先觸發）｜
夜盤保護 —（數據判免：跳空僅 −1,460/筆）｜行事曆 ✅｜手動 ✅

---

# C. 七個參數的由來

| 參數 | 現值 | 由來分類 | 依據 | 出處:行號 |
|---|---|---|---|---|
| `Length20` | **55** | **沿用（無記錄）**，且**明示尚未排入優化** | 全 repo 找不到任何 sweep / 實證 / 決策記錄。只確認它是既有值，且被列為「P3 完成後才做」的待辦：「P4 trailing stop optimization (MA type, length sweep, TrailOffset)」——**至今未執行** | `.pla:233`；待辦 `docs/research/L1_P3_initial_SL_architecture_20260723.md:199`；`docs/research/L1_V30_backtest_analysis_20260723.md:151-152`；`docs/research/L1_IOG_migration_spec_20260723.md:527-528`。**命名怪異點**：input 叫 `Length20` 但值是 55，文件未解釋 `[文件未涵蓋]` |
| `TrailOffset` | **50** | **沿用（無記錄）**，同上待辦 | 同 `Length20`，兩者被綁在同一個未執行的 sweep 待辦內。文件對其功能的唯一說明是「TrailOffset = 50 點 = 給趨勢回調空間」（無數據） | `.pla:234`；`strategies/live/L1_TrendLong/L1_TrendLong_annotated.md:155,200`；待辦出處同上 |
| `stopProfitPoints_Long` | **200** | **三段歷史：L2 移植(250) → 實證優化(500) → 使用者裁示(200)。現值 200 未經 sweep 驗證** | ① **V2.6 (2026-06-12) = 250**，沿用 L2 實戰值，用戶指定以 L2 StopProfit 為藍本移植 `[推導/移植]`。② **V2.7 (2026-07-02) = 250→500**，Plan A backtest：Net **+3,938K (+22.5%)** / PF 1.484 / MDD −461K / 451 筆；TL_SP exits 68→12，釋放的交易流向 TL_TP（103→141），讓趨勢跑更久 `[MC9]`。③ **V3.0 (2026-07-23) = 500→200**：見下方專節 | `.pla:237`；V2.6 `.pla:47-49`、`L1_TrendLong_review.md:380`；V2.7 `.pla:67-71`；V3.0 `.pla:161-162` |
| `profitReturnPrcnt_Long` | **55**（= 容忍回吐峰值 55%、**保留 45%**） | **從 L2 直接沿用實戰值，但有 469 筆 MFE 審計背書**（唯一有明確數據背書的 P7 參數） | 「參數沿用 L2 實戰值 **250 點 / 55%**」。數據背書：MFE≥250 的 130 筆回吐中位 50% / P90 112%；**Top-10 終點回吐最大僅 28%（中位 ~18%）→ 55% 容忍對肥尾有巨大安全邊際**（`[離線-代理]`，僅終點檢查）。語義確認：`.pla:203`「lock floor = Entry + peak x **45** pct」、`.pla:238`「allowed giveback pct of peak profit」、annotated:184「峰值回吐 55%，鎖住 45%」——**三處一致** | `.pla:238,203`；`L1_TrendLong_review.md:353-355,380`；`L1_TrendLong_annotated.md:184,203`；`.pla:56-60` |
| `SL_Multiplier` | **1.5** | **沿用（無記錄）** | 全 repo 無 sweep 或推導過程。V3.1 spec 明列在「Existing inputs retained unchanged」。ATR 停損機制本身在 P3 架構中被批判（40-48K 指數位階產生 500-1000 點停損，0.78% vs 10-15K 時的 0.35%），但**乘數 1.5 這個數字從未被重新驗證**，只是角色從「主要停損」降為「最後防線」 | `.pla:228`；`strategies/research/L1_TrendLong/L1_v31/L1_v31_spec_20260724.md:37,171`；批判 `docs/research/L1_P3_initial_SL_architecture_20260723.md:9-12` |
| `Daily_Cap_Multiplier` | **0.5** | **沿用（無記錄）＋ 已證實為死碼** | 同 `SL_Multiplier`，無 sweep。法醫額外發現：「ATR45×1.5 在 **99-100%** 的進場當下都是較小腿…Daily 腿唯一實際出場的地方是 P3b——以**有害的方向（加寬）**；V2.5 設計的 cap 保護在現實中是**死碼**」 | `.pla:229`；`docs/research/L1_stop_forensics_20260722.md:14,17,20,47-52` |
| `SL_Pct` | **0.5** | **唯一經 MC12 完整 sweep 決定的參數**，但為**局部尖峰非高原** | MC12 optimizer sweep 0.3-1.5 step 0.1（13 組）：0.3 → 1,622K；0.4 → 1,839K；**0.5 → 1,901K（Winner）**；0.6 → 1,791K；0.7 → 1,698K（0.6/0.7 標為 "Death valley"）；0.8-1.0 "MDD plateau"；1.1+ 收斂回 V3.0。**明確警告：「SL_Pct=0.5 is a local PEAK (both neighbors lower). 0.6-0.7 is a death valley. This is not a plateau.」** `[MC12]`。註：專案 CLAUDE.md Rule #12 規定的通用方法論是「MC sweep 0.00-5.00 step 0.25」，L1 實際掃的是 0.3-1.5 step 0.1，**範圍與步長皆不同** | `.pla:230`；`docs/research/L1_V31_SL_Pct_optimization_summary_20260724.md:53-69`；警告 `docs/research/L1_V31_rule18_validation_20260724.md:105-107`；規範 `CLAUDE.md` Rule #12 |

## C-專節：`stopProfitPoints_Long` 500 → 200 的依據

**結論：不是 sweep 出來的，是 user ruling；且在全期數據上 T200 全面劣於 T500。**

1. **觸發動機是一筆真實交易**（`docs/research/L1_IOG_migration_spec_20260723.md:20-22`）：
   「User's trade 2026-07-22: entry 44,739, intrabar High **+466 pts**, bar Close max +416 pts.
   P7 threshold 500 never reached. Trade exited at **−89 pts**.」
   → 帳面從 +466 回吐到 −89（回吐 555 點），根因是 bar-close-only 看不到 intrabar 高點。
2. **MC12 兩跑對照的結果是 T200 較差**（`docs/research/L1_V30_backtest_analysis_20260723.md:11-35,76,90-91`）`[MC12]`：
   - T500：Net **2,399,000** / PF **1.396** / MDD −498,000 (−18.2%) / 458 筆 / Sharpe 0.927
   - T200：Net **2,074,000** / PF 1.348 / MDD −493,200 (−21.7%) / 508 筆 / Sharpe 0.879
   - 出場標籤 delta：**TL_TP −48**（原文註記 "Big winners cut short by P7"）、TL_SP +95
   - 2026 月度：保護收益（Jan/May/Jul）+565K vs 截斷成本（Feb/Jun）−695K → **Net 2026: −119K worse with T200**
   - 整體 EV：T200 **+20.4 pts/trade** vs T500 **+26.2 pts/trade**
3. **裁示與理由**（`docs/research/L1_V30_backtest_analysis_20260723.md:130-141`）：
   「**Ruling**: Adopt T200 as V3.0 baseline.」理由全為質化：
   ① T500 的歷史優勢是 backward-looking，未來 regime 可能出現 <500 pts 的短趨勢，屆時 T500 提供零保護；
   ② P7 不是主要優化目標；③ chase-back 機制 EV 為正（+31 pts/attempt）；
   ④ **「P7 threshold × giveback sweep (64 combos) is DEPRIORITIZED」**。
4. **程式碼註解與文件的對應**：`.pla:237` 註解「(V3.0: 500->200, IOG)」與 `.pla:161-162`
   「Threshold lowered 500 -> 200 pts (IOG makes lower viable)」屬實，但註解**未記載 T200 全期劣於 T500 這件事**。

## C-專節：`profitReturnPrcnt_Long = 55` 的來源

**結論：從 L2 Trendbearish_V1 直接沿用的實戰值，未針對 L1 做過參數掃描；
但有一份 469 筆 MFE 審計證明「55% 容忍不會傷到 L1 的肥尾」。**

- 移植宣告（`L1_TrendLong_review.md:380`）：「用戶指定以 **L2 的 StopProfit 模組為藍本**移植…
  參數**沿用 L2 實戰值 250 點 / 55%**。」
- L2 側的原始設定（`docs/methodology/entry_exit_sop.md:28`）：「L2 StopProfit：獲利 ≥250 點啟動，
  回吐最大獲利 55% 即出場」。
- 支撐 55% 的 L1 數據（`L1_TrendLong_review.md:353-355`）`[離線-代理]`：
  「Top 10 終點回吐最大僅 **28%**（中位 ~18%）——真趨勢單 MA55 追蹤收得住，
  55% 容忍對肥尾有巨大安全邊際。」
- SOP 通則（`docs/methodology/entry_exit_sop.md:70`）：「趨勢策略容忍回吐 ≥50%（參考 L2 的 55%）」。
- **從未針對 L1 掃過 giveback**：唯一規劃過的 64-combo sweep 被 DEPRIORITIZED（見上）。
  2026-07-22 的離線重播曾測 55→35/30，狀態停在 PLAUSIBLE，未進 MC12（見 §A-1-a）。

---

# D. 已知的 L1 出場病理

| # | 問題描述 | 是否已修 | 修法 / 現況 | 出處:行號 |
|---|---|---|---|---|
| **D1** | **TL_TP 有 25%（40 筆，共 −367,400）以虧損出場**、48% 抓不到 100 點；40 筆虧損 TL_TP 的 **MFE 中位數 = 214 點**（半數曾有 4 萬+ 帳面獲利仍虧錢出場） | **未修，已裁示不修** | 用戶裁示：「讓利潤奔跑為本意，**暫緩**」；「此為讓利潤奔跑的必要成本，**不再視為缺陷**」 | `L1_TrendLong_review.md:22,41,335`；`docs/methodology/entry_exit_sop.md:146` |
| **D2** | **贏轉虧傷害**：83 筆曾達 MFE ≥+100 pts 卻虧損收場，合計 **−1,520,200**，平均 MFE 231 點。最慘一筆曾 **+909 點（≈18 萬帳面獲利）回頭虧錢出場** | **部分已修** | V2.6 P7 StopProfit（250/55）為此而生：「觸發後天然保本，地板 = 進場價 + MaxFav×45% > 進場價」。**但 P7 只覆蓋 ≥ threshold 的區間**，門檻以下仍裸露 | `L1_TrendLong_review.md:326-336,357-368`；`.pla:47-66` |
| **D3** | **真空區（The Vacuum Problem）**：進場後 0 ~ +199 pts 區間**完全無保護**，只剩可能達 −300 點的 initial SL。P4 MA55 trail 需要價格走出相當幅度才形成有效水位 | **未修** | 原設計要用 Layer 1b 行為觸發填補 → **Layer 1b 已於 2026-07-24 KILLED**。明確拒絕 price-based breakeven（「會扼殺趨勢策略核心優勢」） | `docs/research/L1_P3_initial_SL_architecture_20260723.md:53-65` |
| **D4** | **MA55 追蹤太慢**：MFE ≥250 點的 130 筆，回吐中位 **50%**、P75 **80%**、P90 **112%（轉虧）**，回吐 >55% 者 55 筆 | **部分已修** | V2.6 P7 SP 層 + V3.0 P4 單向棘輪。**但 maTrail 本身仍只在 45M bar close 更新**（IOG 只讓「檢查」變逐 tick，MA 水位不逐 tick 上移）→ 單根 45M K 棒內急拉，Layer 3 在該根收盤前不會跟上 | `L1_TrendLong_review.md:338-342`（標題原文「MA55 追蹤太慢的鐵證」）；結構限制 `docs/research/L1_IOG_migration_spec_20260723.md:301-304` |
| **D5** | **P7 bar-close 盲區**：2026-07-22 使用者實單，entry 44,739，intrabar High **+466 pts**，bar Close max +416 pts，P7 門檻 500 從未觸及，最終 **−89 pts** 出場 | **已修** | V3.0 IOG migration：P7 改逐 tick 追蹤 intrabar 峰值（`IntraBarPersist`），門檻 500→200 | `docs/research/L1_IOG_migration_spec_20260723.md:20-22,278-292`；`.pla:161-167` |
| **D6** | **P3b 反向取腿（F1）**：P3 用 `MaxList` 於**價格**＝取緊腿；P3b V2.6+ 抄了 header 誤植的「entry − MaxList(distances)」公式形狀，於**距離**上用 MaxList ＝ 取鬆腿 → 進場棒暴露 **1.6-2.8 倍**。2026-07-22 實測**鬆腿 736 pts vs 意圖 266 pts（2.77x）** | **已修（V2.9）** | `MaxList` → `MinList`，並新增 `SetStopContract`。MC12 Gate PASS：12/12 同棒死獲救、2/2 反殺命中、淨 −36 pts / Closed MDD 2,038 不變 | `docs/research/L1_stop_forensics_20260722.md:10-30`；`docs/research/L1_V29_p3b_fix_spec_20260722.md:10-22,27-32,77-89`；`.pla:97-127` |
| **D7** | **雙層 cap 靜默退化（F2）**：`Daily_Cap_Multiplier` 命名意圖是「日線腿作為停損距離上限」，但 ATR45×1.5 在 **99-100%** 的進場當下都是較小腿 → **V2.5 設計的 cap 保護在現實中是死碼**，六年來從未生效 | **未修（僅記錄）** | 法醫僅列為 F2 發現，未提出修法 | `docs/research/L1_stop_forensics_20260722.md:47-52,100` |
| **D8** | **跳空穿透停損**：#94（2021-05）凍結停損 158 pts，實際 **−716**（連 P3b 腿 192 都被貫穿 524 pts）；2026 gap 群 #438/#448 超額 75-91 pts。標籤統計 TL_SL_Gap **27 筆 / 勝率 3.7% / −510,600** | **未修（判定為結構成本）** | SOP 審計：夜盤保護「—（數據判免：跳空僅 −1,460/筆）」 | `docs/research/L1_stop_forensics_20260722.md:56-57`；`L1_TrendLong_review.md:36`；`docs/methodology/entry_exit_sop.md:155` |
| **D9** | **L1_v26 跳空未接住案例（2026-06-22 端午節後）**：6/18 停利出場 @~47,500（+250 點）→ 6/19 休市 → 6/22 跳空開盤 48,531 未進場 → 48,744 仍未進場。機會成本 **約 1,244 點 ≈ 248,800 NTD/口** | **✅ 判定為按設計運作，不修改程式碼** | 根因是 `Cond_Breakout = Close Crosses Over Breakout_Level`：6/18 進場後收盤價持續高於門檻（含跳空後），`Close[1] > Breakout_Level[1]` 恆成立 → Crosses Over 永遠 False。理由：Cross Over 防止追高重複進場；「469 筆歷史交易中避免 ~80 筆上方追高被套損失」`[未標明]` | `docs/strategy_archive/L1_v26_20260622_gap_miss_case.md:4,6-7,15-19,21,39-84,94,96,100,133` |
| **D10** | **七月連續虧損（法醫解剖結論）**：#451 −375 / #452 −444 / #453 −432（皆 C-up 出血區，日 MA20 斜率仍為正 +1.07~+1.96%）；#454 −342 / #455 −445（C-down 邊界）；#456 +739（C-down alpha 家園，進行中）。Closed MDD **2,038 pts** | **不修出場端** | 結論原文：「**虧損的原因是脈絡, 不是停損寬度** — 7 月 MDD 由 C-up 出血區的三連追多構成; **34 個停損 overlay 全部失敗**的原因也在此: 停損在錯誤的進場後怎麼調都是輸。」「停損只是放大器」 | `docs/research/L1_stop_forensics_20260722.md:80-87,89,100-102` |
| **D11** | **TL_SL 佔比過高**：初始停損 **261 筆 / 55.7% / 勝率 0.0% / −4,554,600** | **不視為缺陷** | 「55.7% 的進場直接死在初始停損（**低勝率高盈虧比的本質**）」 | `L1_TrendLong_review.md:37,40` |
| **D12** | **肥尾集中度極端**：Top 5 = 淨利 73.0%；**Top 10 = 淨利 104.4%**（拿掉前 10 名，L1 在 6.5 年是虧損策略）。且 Top 10 中有兩筆含「抱倉跨假日的跳空運氣」成分 | **結構性事實** | 「這就是必須讓利潤奔跑的數學依據（用戶裁示與數據一致）」。同時是所有出場截斷型提案的否決依據（對照 L5 Top-10 88% 的 SP 禁區規則 R-D3） | `L1_TrendLong_review.md:48-58`；`docs/methodology/ENGINEERING_SYSTEM.md:64` |
| **D13** | **V2.9.1 之前標籤語義破損**：TL_TP（trail）可在進場價下方觸發（#452 −444 pts, 2026-07-07）；TL_SL_Gap 可在進場價上方觸發 | **已修（V2.9.1）** | 新路由 = leg × side-of-entry。MC12 re-gate：462/462 筆完全相同，標籤重分佈 TL_TP 138→103、TL_TSL 0→35，損益側互斥 0 違規 | `.pla:137-153`；`docs/research/L1_V29_p3b_fix_spec_20260722.md:118-127` |

---

# E. 研究方法論的陷阱紀錄（附錄 C 八陷阱 × L1 原始案例）

來源：`.claude/skills/adversarial-engineering-sop/SKILL.md:241-252`「附錄 C：策略優化研究陷阱清單
（源自 2026-07-22 L1 停損研究實戰）」。以下把每個陷阱回填到原始研究文件的具體案例與數字。
**這些數字就是未來任何新出場提案的驗收標準。**

| # | 陷阱 | L1 具體案例與數字 | 原始出處:行號 | SOP 對策原文 |
|---|---|---|---|---|
| **E1** | **幻想成交** | **1.2% clip**：MAE 模擬假設「MAE > cap 的交易能在 cap 價位出場」→ 宣稱 **+600 pts**。真實 bar 路徑重播（深 MAE 事件多為跳空/崩盤棒，tighter stop 的實際成交價與 ATR 停損幾乎相同）→ **+23 pts / 6.5 年觸發 1 次**。**差距 26 倍**，直接殺死 V2.9 per-trade 災難斷路器提案 | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:38-41`（B4）；`docs/research/L1_stop_mechanism_deep_research_20260722.md:118,123,230-231` | 「停損提案必先聲明執行模型，用真實 bar 路徑重播」 |
| **E2** | **執行模型錯配** | **A/B 家族 swing low 變體**：重播用「收盤確認 → 次根開盤」，但實務是 intrabar stop 單。修正執行模型後 **A 家族由 −1,108 惡化至 −1,904~−2,435；B 家族由 −3,763 惡化至 −5,857~−5,966**。文件自承「與自己寫的 L34 教訓自相矛盾」。反向的 B5：重播把原始出場棒排除在內層評估外，**低估**了內層停損的節省（偏袒否決結論） | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:28-31`（B2）、`:43-46`（B5） | 「intrabar stop 與 close-based 兩種模型都跑，取符合實作者」 |
| **E3** | **再進場盲區** | **B1**：重播不模擬「停損後再進場」，懲罰全計、補償零計 → **所有 34+ 變體的否決值系統性偏悲觀**。實測 EV：停損後第 2 筆進場 **+100 pts/trade**；<6h 再進場勝率 **34.7%（四組最高）**。實證對照：P3b 修復的離線悲觀估計 **−124 pts**，MC12 原生實測僅 **−36 pts**（原文：「MC12 原生回測自動補償」）。B swing N=3 被標為「唯一可能翻案者」：July 連損 −2,038 → −279、MDD −522，但表面總帳 −5,966 | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:22-26`（B1）、`:25,31,67`；`docs/research/L1_daily_loss_cap_points_analysis_20260722.md:83-84`；`docs/research/L1_V29_p3b_fix_spec_20260722.md:83,89` | 「終審一律 MC12 原生回測」 |
| **E4** | **單年集中度** | **B7 — SP giveback 網格**：500/70% 的 **+1,948 pts 中，+1,688（86.6%）來自 2026 單一年**，前六年合計僅 **+259**。且 75% 是懸崖（+11，#431 從 3,342 被剪到 1,322）。風險判定：「recent-bias / 少數事件擬合 — 與 S8/S9 被 KILL 的 pattern（L23）同構」→ 只可經 MC12 A/B + 分年檢視後再議，**不得直接上 live** | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:52-56`（B7） | 「必附分年拆解」（SOP 第 7 步門檻：效益不集中單一年 >50%） |
| **E5** | **邊界脆弱性** | ① **#431 最大贏家 +3,342 pts，MA20 斜率 −0.12%，距 C-up 濾網邊界一髮之遙**——「斜率門檻的微小位移就會殺掉它」（帶紅旗）。② **壓線倖存者**：#447（MAE **428**）、#449（MAE **375**）合計 **+2,305 pts**，若停損收緊至 0.5-0.8% 全數陣亡。③ #94（2021-05）凍結停損 158 pts，實際 **−716**，連 P3b 腿（192）都被貫穿 524 pts。④ **SL_Pct=0.5 本身是局部尖峰不是高原**：「0.5 is a local PEAK (both neighbors lower). 0.6-0.7 is a **death valley**. This is not a plateau.」 | `docs/research/L1_stop_mechanism_deep_research_20260722.md:69,77`；`docs/research/L1_stop_forensics_20260722.md:56,93-94`；`docs/research/L1_V31_rule18_validation_20260724.md:105-107` | 「參數敏感度掃描，確認高原非尖峰」 |
| **E6** | **自我驗證錨點** | **B6 — SP 網格錨點測試**：以現行參數（500 / 保留 45%）重播，**理論上應零變化**，實測 **−269 pts / 10 筆偏差** → 「我的 P7 模型與 MC 實作存在細節差異（peak 更新時序/掛單時點）」。處置：**所有 SP 網格數字帶 ±300 pts noise floor 解讀**。→ 意即 §A-1-a 那個 +1,565~+1,948 的 SP giveback 候選，訊號本身只有噪音的 5-6 倍 | `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:48-51`（B6） | 「每個重播模型必跑錨點」 |
| **E7** | **症狀 vs 病因** | **七月連損法醫**：「**虧損的原因是脈絡, 不是停損寬度** — 7 月 MDD 由 C-up 出血區的**三連追多**構成; **34 個停損 overlay 全部失敗**的原因也在此: 停損在錯誤的進場後怎麼調都是輸。」因果鏈：指數自 47,400 下跌期間，日 MA20 因落後仍上升 → L1 把每個反彈突破當新趨勢追 → 三連全額停損（#451 −375 / #452 −444 / #453 −432）。「**停損只是放大器**」。deep_research §3 標題本身：「真正的病因 — 部位規模危機穿著停損機制的外衣」；L30 教訓：「停損寬度不是病, 是症狀」 | `docs/research/L1_stop_forensics_20260722.md:80-87,89,101`；`docs/research/L1_stop_mechanism_deep_research_20260722.md:164,250` | 「overlay 測試前先跑虧損法醫解剖（進場當下市場脈絡 × 結果）」 |
| **E8** | **雙腿選擇函數** | **P3b vs P3 反向取腿**：P3（凍結停損，`.pla` 對應 line 438 當時版本）`MaxList(Entry_P − ATR×1.5, Entry_P − D_ATR×0.5)` 用在**價格** = 取緊腿（正確）；P3b（line 412 當時版本）`MaxList(Current_ATR*SL_Multiplier, Daily_ATR*Daily_Cap_Multiplier)` 用在**距離** = 取鬆腿（錯誤）。同一設計意圖下兩處取相反腿。2026-07-22 實測 **P3 腿 266 pts vs P3b 腿 736 pts，倍率 2.77**。**且驗證器 V-4 把此 BUG 斷言為標準，通過驗證一年**。L37 教訓：「程式碼的『形狀』不攜帶『語義』」 | `docs/research/L1_stop_forensics_20260722.md:10-30`；`docs/research/L1_V29_p3b_fix_spec_20260722.md:13-22,18-19`；`docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:72` | 「多腿停損的每個引用點必須逐一驗證選擇方向與設計意圖一致」 |

## E-補充：SOP 第 7 步的收案門檻（任何新提案適用）

`.claude/skills/adversarial-engineering-sop/SKILL.md:231-237`：
宣稱「最理想 / 收案」的必要條件（**全部滿足**才可宣稱）：
1. MC12 原生回測驗證（含再進場效應）
2. 分年拆解穩健（效益不集中單一年 > 50%）
3. 參數高原確認（非尖峰、非邊界擬合）
4. 用戶裁示（執行者不得自行收案）

**禁止**：用離線模擬數字直接宣稱上線效益；執行者自行宣告收案。

## E-補充：Rule #18 五件套對 V3.1 的判定（2/5 PASS）

`docs/research/L1_V31_rule18_validation_20260724.md`，481 筆交易，回測 2020-08-17 ~ 2026-07-23，
帳戶假設 1,000,000 TWD。**這五個判定本身是站在 MC12 交易清單上的離線 Python 二次模擬**
（`rule18_five_suite.py`, scratchpad, not committed）`[離線-py]`：

| 件套 | 結果 | 數字 | 行號 |
|---|---|---|---|
| Monte Carlo | **FAIL** | 95% MDD **−803,800 TWD（80.4% of account）** | `:15,27` |
| Bootstrap | **FAIL** | PF 95% CI lower = **0.993** | `:16,45` |
| Stress Test | **FAIL** | Max single loss **−145,200** > 5% account | `:17,68` |
| Regime | PASS | Bull PF 1.264 + Range PF 1.417 | `:19,83-84` |
| Robustness | PASS | ±20% → PF change < 2% | `:20,99-102` |

判讀原文（`:113-119`）：「All 3 FAILs are structural L1 characteristics that exist equally in V3.0…
V3.1 did not worsen any of these.」
**⚠️ 帳戶分母落差**：使用者實際配置是「200 萬 / 2 口大台」
（`docs/handoffs/HANDOFF_L1_STOP_CAMPAIGN_20260722_EOD.md:28`），
而 Rule #18 的「% of account」是用 1,000,000 TWD 算的，文件未做換算 → 見 §F-6。

---

# F. [來源衝突] 清單

| # | 衝突事實 | 說法 A | 說法 B | 處置 |
|---|---|---|---|---|
| **F-1** | **Trail_B −385K 屬於哪支策略** | **L1**：`docs/methodology/ENGINEERING_SYSTEM.md:151`（AP-1）「L1 Trail_B −385K」；另 `:63`（R-D2）記為「**L24**: Trail_B −385K」 | **S1**：`docs/archive/handoffs/handoff_20260613_s1_v26.md` 全篇；`strategies/live_simulation/S1_NightMomentum/S1_NightMomentum.pla:103,130,173`；3 份 2026-07-30 colleague 分析文件 | **兩邊都列**。10 處獨立來源指向 S1，1 份方法論檔指向 L1。另 `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md` 全文是 S3_L −124,200 事件，**通篇未提 Trail_B** → L24 標籤亦不符 |
| **F-2** | **memory 中「L5 Stage1_BE −19K **L26**」的 L26 標籤** | memory `feedback_trend_let_profits_run` 記為 L26 | repo 中 L26 有**兩套互斥定義**：軌道甲（`ENGINEERING_SYSTEM.md:174-177` + `stop_loss_mechanisms_catalog_20260628.md:166-184`，2026-06-28）L26 = 「Hard Cap ≥ SP arm distance」（S3_S 話題）；軌道乙（正式 codified，2026-07-25）L26 = 「盤整策略須避開日盤開盤」（L3 話題）。另 `docs/research/L1_V28_backtest_verdict_20260722.md:117` 又把 L26 定義為「Risk parameters must be derived top-down」 | **全文搜尋未發現任何文件把 Stage1_BE 與編號 "L26" 連結** → 該 L26 標籤 `[文件未涵蓋]`，疑為 memory 標籤誤植。**Lesson 編號在此 repo 不可靠，引用時必須連同日期+檔名** |
| **F-3** | **L27 對 L5 的 BE 立場** | `docs/live_optimization/README.md:17`：L5 Stage1_BE 已於 **2026-07-05** 測試 FAILED | `docs/policies/lesson_L27_breakeven_incompatible_consolidation.md:117-119`（**2026-07-25**，晚 20 天）把 **L1/L5/S1 列為「CANDIDATE for future BE research」** | **兩邊都列**。L27 未引用 20 天前已存在的 L5 失敗記錄。若今天有人根據 L27 提出 BE 提案，必須先回頭看 README:17 |
| **F-4** | **「固定 % 0.4-1.0%」封死 vs SL_Pct 採用** | `HANDOFF_L1_STOP_CAMPAIGN_20260722_EOD.md:31`（2026-07-22）：「已封死的路（勿重開）…**固定 % 0.4-1.0%**…」 | 兩天後 `docs/research/L1_V31_SL_Pct_optimization_summary_20260724.md:53-67`：SL_Pct sweep **0.3-1.5%（直接涵蓋 0.4-1.0%）**，Winner 落在 **0.5%** 並被採用進 V3.1；`HANDOFF_L1_V31_20260724_EOD.md:42` 自稱「**fixed percentage (SL_Pct) adopted instead**」 | **兩邊都列**。差異可能在：7/22 測的是「MAE > cap% 即出場」的離線 MAE 模擬（`deep_research:110-124`），7/24 測的是「以進場價百分比封頂 initial SL 距離」的 MC12 原生 sweep——機制形狀相似但**執行模型與驗證工具不同**。文件未自行澄清此點 |
| **F-5** | **V3.1 是 live 還是 research** | `strategies/live/L1_TrendLong/L1_TrendLong.pla:5` header 寫「Version : **V3.1**」，且檔案位於 `strategies/live/` | 同一檔 `:178` changelog 寫「V3.1 (2026-07-24) P3 percentage-based SL cap (**research**)」；`HANDOFF_L1_V31_20260724_EOD.md:14` 指向 `strategies/research/L1_v31/L1_TrendLong_v31.pla`；handoff Status 僅寫「P3 Initial SL DONE, MDD Research NEXT」，**未見 MC9 部署完成記錄** | **兩邊都列**。動 L1 出場之前必須先跟使用者確認**實盤 MC9 上跑的到底是 V3.0 還是 V3.1（SL_Pct=0.5 是否已生效）** |
| **F-6** | **V3.1 的回測筆數/淨利 baseline** | `L1_V31_SL_Pct_optimization_summary_20260724.md:59,89` + `L1_V31_rule18_validation_20260724.md:5`：**481 筆 / Net 1,901K**（回測 2020-08-17 起） | `L1_V32_X4_FINAL_VERDICT.md:23-27`「V3.1 MC12」欄：**445 筆 / +1,772,600 / PF 1.359**（未自陳回測區間）。另 `L1_v31_spec_20260724.md:374` 的 V3.0 XLS baseline：474 筆 / 1,843,400，vs `L1_V30_backtest_analysis_20260723.md:27` 的 V3.0/T200：**508 筆 / 2,074,000** | **全部列出**。`L1_v31_spec_20260724.md:378-390` 自陳「V3.0 Baseline Discrepancy Note (S-6 record)」：差 231K / 34 trades，四個可能原因（回測區間 / 滑價手續費 / IOG+Bar Magnifier 設定 / 資料快照）**皆標註 unresolved** |
| **F-7** | **L1 V2.7 的總淨利與筆數** | `docs/research/L1_daily_loss_cap_points_analysis_20260722.md:34,42` `[MC12 XLS]`：Net **10,136 pts** / **424 筆(1 open)** | `docs/research/L1_stop_mechanism_deep_research_20260722.md:5`：**455 筆已平倉**；同文 `:132` 重播 baseline **net 12,203 pts**；`docs/research/L1_stop_forensics_20260722.md:61`：**456 筆** | **全部列出**。MDD 2,038 pts 四處一致，不受影響。文件間未互相校對或註明差異原因 |
| **F-8** | **2021 極端單筆虧損的日期與點數** | `docs/research/L1_stop_forensics_20260722.md:56`：#94 **2021-05-15**，**−716 pts** | `docs/research/L1_stop_mechanism_deep_research_20260722.md:18,25` + `L1_daily_loss_cap_points_analysis_20260722.md:85` + `bug_ledger:41`：**726 pts / 2021-05-12** | **兩邊都列**。三份對一份 |
| **F-9** | **−145,200 最大單筆虧損的事件日期（同一文件內矛盾）** | `docs/research/L1_V31_rule18_validation_20260724.md:68`：「−145,200 on **2021-05-15**」 | 同文 `:73-74`：「The −145K is a gap event (**2021-05-17** market crash)」；`L1_V31_SL_Pct_optimization_summary_20260724.md:124` 亦作 **2021-05-17** | **兩邊都列**。疑為筆誤，文件未自行更正 |
| **F-10** | **#431 最大贏家（+3,342 pts）的日期** | `docs/research/L1_daily_loss_cap_points_analysis_20260722.md:88`：**2026-04-07** | `docs/research/L1_stop_mechanism_deep_research_20260722.md:63,243`：**2026-04-08** | **兩邊都列** |
| **F-11** | **`profitReturnPrcnt_Long=55` 是否落在規劃 sweep 範圍外** | `docs/research/L1_IOG_migration_spec_20260723.md:415` 規劃的 Giveback % sweep = **10, 15, 20, 25, 30, 35, 40, 45**（最高 45，**不含 55**） | 但 bug_ledger 的 SP 網格用「500/45%」「500/70%」表示法（`bug_ledger:49,53`），其中 45% = 保留比例（對應 profitReturnPrcnt_Long=55），70% = 保留（對應 =30）→ **兩份文件的百分比語義相反**（一份是 giveback，一份是 retain） | **兩邊都列**。這是命名歧義而非數值錯誤，但若照 IOG spec 的 8 檔直接跑 sweep，可能掃到完全錯誤的區間 |
| **F-12** | **Lesson 編號 L25/L26/L27 重複使用** | `docs/research/L1_V28_backtest_verdict_20260722.md:116-118`（2026-07-22）：L25=daily loss cap 有害 / L26=risk params top-down / L27=NTD 門檻需按口數重校 | `strategies/research/L1_TrendLong/L1_v31/L1_V32_X4_FINAL_VERDICT.md:83-96`（2026-07-25）：L25=跨時框特徵結構脆弱 / L26=ON rate >90% 的特徵無過濾力 / L27=Python 離線回測對跨時框特徵不可靠。另有正式 codified 的 `docs/policies/lesson_L25_L26...` / `lesson_L27...`（2026-07-25）內容又不同 | **三套並存**。引用 lesson 時必須連同日期與檔名 |
| **F-13** | **Family E (連續收低 k=5) 的欄位語義** | `docs/research/L1_stop_mechanism_deep_research_20260722.md:134,140` 表頭「d_net / d_MDD / 誤殺贏家」→ k=5：−1,726 / +999 / 31 | `docs/research/L1_Layer1b_kill_summary_20260724.md:35` 轉述為「−1,726 pts net over **999 winners killed / 31 losers saved**」 | **兩邊都列**。kill_summary 疑似把 d_MDD(+999) 誤讀為 winners killed、誤殺贏家(31) 誤讀為 losers saved；來源表根本沒有「losers saved」欄位 |
| **F-14** | **1.2% clip 的損益（同一文件內新舊並存）** | `docs/research/L1_stop_mechanism_deep_research_20260722.md:118,123`：**+600 pts** | 同文 `:230-231` + `bug_ledger:40`：**+23 pts**（修正後） | **兩邊都列**。只讀 §2.4 會拿到過期數字，**相差 26 倍** |

---

# G. [文件未涵蓋] 清單

| # | 查不到的東西 | 已搜尋範圍 |
|---|---|---|
| **G-1** | `Length20 = 55` 的選值依據 | 全 repo grep；只找到「待辦，尚未執行」 |
| **G-2** | `TrailOffset = 50` 的選值依據 | 同上 |
| **G-3** | `SL_Multiplier = 1.5` 的選值依據 | 全 repo；V3.1 spec 僅列為 "Existing inputs retained unchanged" |
| **G-4** | `Daily_Cap_Multiplier = 0.5` 的選值依據 | 同上 |
| **G-5** | input 名 `Length20` 為何配值 55（命名由來） | 全 repo |
| **G-6** | L5 **Stage1_BE 的公式/程式碼定義**與逐筆結果檔 | `docs/` + `strategies/` 全庫 grep（Stage1_BE / Stage1 / breakeven / BE_ / 19K / v19.9 / v199 / Cooldown-D / GA Trail）；`L5_v199_1contract_removed_code.md` 與 `L5_BreakoutLong_v199.pla` 皆不含 "Stage1_BE" 字串 |
| **G-7** | L5 Stage1_BE 的**專屬 root cause 陳述** | 同上；只有 P9 段落的三次統一結論 |
| **G-8** | S1 Trail_B −385K 是 MC9 還是 MC12 產生 | `handoff_20260613_s1_v26.md` 未在數字旁標明 |
| **G-9** | L1_c 診斷日誌（`v31_sl_log.txt`）是 MC12 輸出還是 Python 輸出 | `L1_V31_SL_Pct_optimization_summary_20260724.md:142` + `HANDOFF_L1_V31_20260724_EOD.md:96` 皆未寫明 |
| **G-10** | L1_v26 gap-miss 案的「469 筆中避免 ~80 筆上方追高」的驗證工具 | `L1_v26_20260622_gap_miss_case.md:94,96` 未標明 |
| **G-11** | 「廣義再進場 (Plan C)」2026-07-22 版本的獨立量化文件 | `docs/` 全庫；只有 2026-07-02 的 `.pla:72-79` MC9 數字 |
| **G-12** | `stop_loss_mechanisms_catalog_20260628.md` 對 **L1** 的任何裁定 | 已全文讀畢：該文件目的是「為 S3_S v1.7.4 Hard SL Cap 設計提供業界 best practice 參考」；全文「L1」僅出現一次且是美股熔斷分級代稱（`:44`）→ **與策略 L1 TrendLong 無關** |
| **G-13** | `portfolio_DD_postmortem_202607_L1-L5.md` 對 L1 **出場端**的結論 | 已全文讀畢：全篇對 L1 的診斷落在**進場端**（濾網全開、無冷卻、無連虧熔斷）與**組合層**，**未對 L1 出場機制提出任何修改建議** |
| **G-14** | X1 / X2 / X3 變體、L1a / L1b 變體、P3a 模組 | 全 repo；只存在 X4、L1_c、P3/P3b。上述名稱疑為不存在的推測性標籤 |
| **G-15** | 「急拉」情境下 trail 跟進速度的**任何已完成分析** | 全 repo。P4 MA type / length sweep / TrailOffset 三項在 `L1_P3_initial_SL_architecture_20260723.md:199`、`L1_V30_backtest_analysis_20260723.md:151-152`、`L1_IOG_migration_spec_20260723.md:527-528` 三處被列為 deferred → **此方向不是「測過但失敗」，而是「根本還沒排上」** |

---

# H. 給 2026-08-05 決策者的三條最相關既有結論

> 以下三條是搬運，不是建議。是否動 L1 出場由使用者裁示。

1. **P4 trail 的速度問題是「尚未研究」，不是「已否決」。**
   MA type / length sweep / TrailOffset 敏感度三項，在三份不同文件裡都被列為 deferred，
   至今沒有任何完成的分析。且已知結構限制：`maTrail` 只在 45M bar close 更新
   （IOG 只讓「檢查」變逐 tick，MA 水位不逐 tick 上移）→ 單根 45M K 棒內急拉，
   Layer 3 在該根收盤前不會跟上。
   出處：`docs/research/L1_P3_initial_SL_architecture_20260723.md:199`；
   `docs/research/L1_IOG_migration_spec_20260723.md:301-304,527-528`。

2. **但凡是「截斷式」的出場端保護，跨策略已有四筆失敗記錄，方向永久關閉。**
   S1 Trail_B −385K（88.2% 勝率卻截斷大尾巴）、L5 SP 五變體全滅（最佳仍 −14.0%）、
   L5 Stage1_BE −19K、L4 BE/SP −345K~−82K。規則 R-D3：「策略尾巴集中度 >70% = SP 禁區」，
   而 **L1 的 Top-10 = 淨利 104.4%**（拿掉前 10 名 L1 是虧損策略）。
   出處：`docs/research/L1-L5_structural_audit_20260721.md:149`；
   `docs/methodology/ENGINEERING_SYSTEM.md:64,151`；`L1_TrendLong_review.md:51-54`。

3. **L1 現有的「急拉回吐」痛點，已經有一個現成但未被掃過的旋鈕：`profitReturnPrcnt_Long`。**
   離線重播顯示 55 → 35/30 可得 +1,565~+1,948 pts 且 MDD 零變化、Top-10 存活，
   **但**帶 ±300 pts 噪音底（B6 錨點殘差 −269）且 86.6% 效益來自 2026 單一年（B7）。
   狀態停在 PLAUSIBLE，明文「不得直接上 live」，須經 MC12 一鍵 A/B + 分年檢視。
   同時注意：規劃中的 giveback sweep 範圍（10-45）與現值 55 的語義有歧義（見 §F-11）。
   出處：`docs/research/L1_stop_mechanism_deep_research_20260722.md:236`；
   `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md:48-56,68`。

---

## 附：本文未做的事

- 未執行任何回測、未執行任何 Python 模擬、未修改任何既有檔案。
- 未對「該不該動 L1 出場」下判斷——這是使用者裁示範圍。
- 表中所有數字皆為搬運，未重新計算；若與原始 XLS 不符，以原始文件為準。
