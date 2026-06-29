# Handoff 2026-06-29 Evening — Bug 2 SP IOG 未解，明日重新探討

**Session 結束**：2026-06-29 23:55（晚）
**User ruling**：「明天繼續重新探討 BUG2 的優化方式以及後續的內容」
**Status**：所有 commits push 完成，工作樹 clean，待明日繼續

---

## 一、Status 速查

| 項目 | 狀態 |
|------|------|
| Git working tree | ✅ clean |
| Local = origin/main | ✅ 100% sync |
| 待 push | 0 |
| v1.7.3-FINAL production | ✅ 維持（live_simulation, **未動**）|
| v1.8.1-GA | 🟡 **EXPERIMENTAL，明日繼續探討** |
| 全 v1.8.x archive decision | ⏸️ **延後** — user 想明日重新探討 |

---

## 二、今日完整 commits（**10 個**）

| Commit | 內容 |
|--------|------|
| `820c873` | Add extreme market multi-layer SL SOP (Fine Dining) |
| `feab813` | SL SOP user-approved 1F-5F building metaphor |
| `bf96e5a` | Rule #17: extreme SL SOP mandatory |
| `9bad4cf` | v1.8.0 EXPERIMENTAL: 1M multi-layer preemptive exit |
| `9808163` | v1.8.0 backtest: SX_VS_1M_Exit=0 triggers (笔电) |
| `ff73231` | 3-way analysis: v1.7.3 vs v1.7.4 vs v1.8.0 |
| `54f6256` | v1.8.0 Phase 2 GA R1 spec + 1M fill SL future TODO |
| `289d7db` | **v1.8.0-GA: 救活! PF 4.13 + 6/8 case 完美救援** ⭐ |
| `51d4150` | v1.8.1 EXPERIMENTAL: Bug 2 SP IOG Fix (BarStatus gate) |
| `0a9bf85` | v1.8.1 BarStatus Fix FAILED: SP -143K worse |
| `d17434d` | **v1.8.1-GA FAILED: architecture issue confirmed** |

---

## 三、6-Version Evidence Chain（**Bug 2 未解的證據**）

| # | 版本 | 試 | Net | SP maxL | Lesson |
|---|------|-----|-----|---------|--------|
| 1 | **v1.7.3** | Baseline | **+1,013K** ⭐ | **-5K** ⭐ | - |
| 2 | v1.7.4 | + Hard Cap 100 | +792K | -4.8K | L29 (gap fail) |
| 3 | v180-orig | + 1M default ML | +502K | -132K | L30 (IOG risk) |
| 4 | v180-GA | + GA on ML | +846K | -132K | L31 (partial) |
| 5 | v181-single | + BarStatus gate | +585K | -143K | L32 (gate ineffective) |
| 6 | **v181-GA** | + Re-GA | **+536K** | **-143K** | **L33 (GA can't fix arch)** |

→ **6 個版本，5 lessons (L29-L33)，但 Bug 2 仍未解**

---

## 四、明日重新探討的方向（**未 codify 為 final，明日再決定**）

### 用戶 explicit ruling 留 v1.8.1 為 active research
- **不 archive** v1.7.4 / v1.7.5 / v180-* / v181-* （等明日討論）
- **v1.7.3-FINAL 仍是 production 不動**
- 明日要 deep 探討 Bug 2 「優化方式以及後續」

### Bug 2 真正 root cause（已 confirmed）
- IOG=true 必伴隨 stop order intrabar fill
- BarStatus gate 只控 SET 不控 FIRE
- SetStopLoss engine guard 平行 active
- GA threshold tune 無法 escape

### 候選 next directions（**明日討論 priority**）

#### 方向 A: 雙策略架構
```
策略 1 (Monitor): IOG=true + Data3 1M
  - 純 indicator 計算 ML score
  - 不直接 fire order
  - 把 score 寫入 named "Global Variable" (GV1, GV2)

策略 2 (Executor): IOG=false 60M
  - 讀 Global Variable
  - 用 60M K close 邏輯 fire order
  - SP/SL 機制不受 IOG 副作用
```

| Pro | Con |
|-----|-----|
| 真解 Bug 2 | 極複雜 (兩個策略同步) |
| SP fill 行為恢復 v1.7.3 | MC12 GV 跨策略邊界問題 |
| 1M_Exit 仍即時 | 需重新 verify entire pipeline |

#### 方向 B: 純 indicator 1M 監測
```
單一策略 IOG=false
1M 監測改用 indicator (e.g. RSI(1M), volume spike on 1M)
但這些 indicators 在 60M strategy 中 [1] reference 取 1M data
不需要 IOG=true
```

| Pro | Con |
|-----|-----|
| 單策略 | 失去即時反應 (60M K 才執行) |
| 不破 IOG=false 規範 | 1M_Exit 慢半拍 |
| SP 機制保留 | 6/8 case 可能救不了 |

#### 方向 C: Limit order 取代 Stop order
```
SP/SL 改用 limit (不是 stop)
SP_Limit_Price = EntryPrice - peak × 70%
SL_Limit_Price = EntryPrice + 2.75 × ATR

問題: limit 在反向時不會 fill (跳空越過時等不到 fill)
失去 gap protection
```

| Pro | Con |
|-----|-----|
| 避免 intrabar stop fill | Gap 跳空 limit 不 fill |
| 簡單實作 | Worst case 變大 |

#### 方向 D: 接受 v1.7.3 (Path D)
- 完整證據鏈閉合
- 5 lessons codified
- 不投資更多 backtest

#### 方向 E: MC12 forum 深度研究
- 查 IntrabarOrderGeneration + Stop order fire timing 邊界情況
- 看是否有 undocumented 解法
- 不確定可行性

### 用戶明日要 evaluate
- A vs B vs C vs D vs E
- 投資報酬率
- 時間成本
- 風險

---

## 五、明日筆電端 / 桌機端 resume SOP

### Step 1: Pull git
```bash
cd C:/tmp/TXF1-Strategy-Lab
git pull origin main
```

### Step 2: 讀本檔 + 6-version evidence chain
```
docs/handoffs/handoff_20260629_evening_bug2_unsolved_revisit_tomorrow.md (本檔)
strategies/research/S03_VolSqueezeShort/v181_GA_FAILED_architecture_verdict_20260629.md
strategies/research/S03_VolSqueezeShort/v180_GA_R1_result_20260629.md
strategies/research/S03_VolSqueezeShort/v174_v180_desktop_threeway_analysis_20260629.md
docs/methodology/extreme_sl_multilayer_sop_20260629.md
```

### Step 3: 用戶決定方向 A/B/C/D/E（**今日未決定**）
- Claude 給 3-5 個 candidate 深度比較
- 用戶 ruling
- 若選 A → 設計雙策略架構 spec
- 若選 D → 寫 L29-L33 lessons + archive 全 v1.8.x + 進 S4_S

---

## 六、其他待處理項目（**priority 暫降**）

| Task | Status |
|------|--------|
| #136 S16_MACrossShort 啟動 | 等 S4_S 完成 |
| #142 1M fill SL future research | 等 v1.7.3 promote 後評估 |
| S4_S W2 .pla 實作 | 等 S3_S architecture closure |

---

## 七、Key Insights for 明日

### Bug 2 不是 thresholds 問題
- v180-GA → v181-GA 變更 8/10 params
- 但 SP maxL 仍 -143K（v180-GA -132K worse）
- 證實 **不是 GA 能解的問題**

### v1.7.3-FINAL 仍是 honest winner
- 6 version 對比後仍 Net / Sharpe / Sortino / WR best
- portfolio cap 3% 已控單筆風險
- 業界 standard 接受 -10% 帳戶 worst case

### 真要救 Bug 2 需重新設計 architecture
- 雙策略 / pure indicator / limit order 等
- 都需要重新 W3-W5 verify
- 投資報酬率不確定

---

## 八、Status snapshot

| 項目 | 狀態 |
|------|------|
| live/ 5 隻 | ✅ 全有 BOSS_VIEW + 實盤 |
| live_simulation/ 4 隻 | ✅ S1/S3/S3_L/**S3_S v1.7.3-FINAL** |
| research/ S03 v1.8.x | 🟡 EXPERIMENTAL，明日重新探討 Bug 2 |
| research/ S4_S | 🔵 W0+W1 done, W2 待 |
| research/ S16 | 🟡 Stage-1 done, 等 S4_S |
| Git sync | ✅ 100% pushed |

---

## 九、Token / 時間

- 今日 session: ~ 12+ hr
- 11 commits / ~3,500 行 documentation
- 6 個 backtest verification rounds
- 5 個 new lessons (L29-L33) 候選
- 1 個 GA Round (256 pop × 30 gen)

---

## 十、晚安

今日證實 v1.8.x 整個 IOG=true 架構受限於 MC12 engine 行為。
v1.7.3-FINAL 仍是 production，**未動**。
v1.8.x 全保留為 EXPERIMENTAL，等明日繼續探討。

明日見。
