# S3_S v1.8.1-GA FAILED — **Architecture Issue Confirmed**

**日期**：2026-06-29
**Verdict**：🚨🚨 **v1.8.x 整個架構 FAIL，Bug 2 不可用 GA 解**
**Final Decision**：**接受 v1.7.3-FINAL 為 absolute production**，archive 全 v1.7.4/v1.7.5/v180/v181

---

## 一、Headline DOUBLE FAIL

| 指標 | v1.8.0-GA | v1.8.1-single | **v1.8.1-GA** |
|------|----------|--------------|---------------|
| Net | +846K | +585K | **+536K** ❌ |
| PF gross | 4.13 | 3.18 | **3.02** ❌ |
| PF adj | 2.24 | 1.69 | **1.56** ❌ |
| Sharpe | 0.56 | 0.43 | **0.39** ❌ |
| Sortino | 0.47 | 0.29 | **0.26** ❌ |
| MDD % | -19.4% | -25.2% | **-26.2%** ❌ |
| **SP maxL** | -132K | -143K | **-143K** ❌ |
| 1M_Exit | 2 | 2 | **1** ❌ 救援退步 |

→ **GA 試過了，結果更差**

---

## 二、GA 確實在新環境找不同 best（**證實架構改變**）

| Input | v180-GA | **v181-GA** | 變化 |
|-------|---------|------------|------|
| ML_ActivationPct | 30 | **20** | -33% |
| ML_ScoreTrigger | 30 | 30 | = |
| ML_MinCategories | 3 | **1** | -66% |
| ML_VolSpikeMult | 1.5 | 1.5 | = |
| ML_VolAvgLen | 15 | **20** | +33% |
| ML_SpeedBars | 5 | **7** | +40% |
| ML_SpeedThreshPts | 30 | **40** | +33% |
| ML_ATR_Short_Len | 3 | **8** | +166% |
| ML_ATR_Long_Len | 90 | **60** | -33% |
| ML_ATR_Ratio | 2.5 | **2** | -20% |

→ **8/10 params 變了** = 環境確實不同
→ **但「不同 best」反而 Net 更差 -310K** = 證明架構傷 alpha

---

## 三、6 個版本完整 evidence chain（**所有 path 已 exhausted**）

| # | 版本 | 試過什麼 | Net | 結果 |
|---|------|---------|-----|------|
| 1 | **v1.7.3** | Baseline (IOG=false) | **+1,013K** | ✅ **WINNER** |
| 2 | v1.7.4 | + Hard Cap 100 pts | +792K | 6/8 gap -466 pts |
| 3 | v180-orig | + 1M Multi-layer default | +502K | sub-optimal |
| 4 | v180-GA | + GA on ML thresholds | +846K | PF 4.13 BUT SP -132K |
| 5 | v181-single | + BarStatus gate fix | +585K | SP -143K (WORSE) |
| 6 | **v181-GA** | **+ Re-GA in BarStatus env** | **+536K** | **更糟** |

### 結論
**Bug 2 SP IOG 不是 thresholds 問題，是 MC12 engine 架構限制**：
- IOG=true 必伴隨 stop order intrabar fill
- BarStatus gate 無法控制 fire timing
- 即使 GA 在新環境也找不到 escape
- **v1.8.x IOG=true 整個方向錯**，需重新設計架構（雙策略 / pure indicator / 等）

---

## 四、Lessons L29-L33 完整 catalog（永久 codify）

| # | Lesson | 證據 |
|---|--------|------|
| **L29** | Hard SL Cap 在 Gap 風險下失效 | v1.7.4: 6/8 cap 100 → -466 pts |
| **L30** | 1M Multilayer 在 IOG=true 引入新風險 | v180-orig: SP -132K vs v1.7.3 -5K |
| **L31** | GA 可救觸發但 SP IOG 不解 | v180-GA: PF 4.13 但 SP 仍 -132K |
| **L32** | BarStatus Gate 在 IOG=true 無法控 stop fire | v181-single: SP -143K worse |
| **L33** | **GA 在錯架構下無能為力** | **v181-GA: 8/10 params 變但 Net 更差** |

### L33 完整 wording
**「GA 在錯架構下無能為力 — 當 architecture 是 root cause，threshold optimization 救不了」**
- 條件：fix 後新環境 GA 找到的 best 仍 < 原版本
- 解讀：問題在架構不在參數
- 建議：放棄該 architecture，回 baseline 或重新設計

---

## 五、Final Decision

### **接受 v1.7.3-FINAL 為 absolute final production**

證據鏈完整 6 版本驗證 + 5 個 lessons codified

### Archive 全 v1.8.x
- v1.7.4 → archive (L29 proof)
- v1.7.5 → archive (superseded)
- v180-orig → archive (L30 proof)
- v180-GA → archive (L31 proof)
- v181-single → archive (L32 proof)
- v181-GA → archive (L33 proof)

### 維持 v1.7.3-FINAL
- `live_simulation/S3_S_VolSqueezeShort.pla` (不動)
- BOSS_VIEW 不動
- DEPLOYMENT 不動
- Portfolio cap 3% 控單筆風險

---

## 六、未來研究方向（**待時，priority 暫降**）

### 若未來想真解 Bug 2
| Path | 難度 | 預期 |
|------|------|------|
| 雙策略架構（IOG=true 監測 + IOG=false 執行）| 極高 | 不確定可行 |
| 改 1M_Exit 為純 indicator（不直接 fire order）| 中 | 失去即時反應 |
| MC12 forum 深度研究 BarStatus + IOG | 中 | 不確定可解 |
| Limit order 取代 stop order | 低 | 失去 gap protection |

→ **暫不投資**，因 5 個 lessons 已證明此 path 結構性限制

---

## 七、Status Final

| 版本 | 狀態 | Lesson |
|------|------|--------|
| **v1.7.3-FINAL** | ✅ **PRODUCTION** (live_simulation, 不動) | - |
| v1.7.4 | 🟡 ARCHIVED | L29 |
| v1.7.5 | 🟡 SUPERSEDED | - |
| v180-orig | 🟡 ARCHIVED | L30 |
| v180-GA | 🟡 ARCHIVED | L31 |
| v181-single | 🟡 ARCHIVED | L32 |
| **v181-GA** | 🟡 **ARCHIVED** | **L33** |

---

## 八、Next Per OFFICIAL_ROADMAP

S3_S 完成（最終版 v1.7.3-FINAL promoted），下一個按 OFFICIAL_ROADMAP（user 2026-06-28 ruling）：
**S4_S MACDDivergenceShort**（W0 + W1 已 done，等 W2 .pla 實作）

---

## 九、相關文件

- `v174_v180_desktop_threeway_analysis_20260629.md`（3-way 對比）
- `v180_GA_R1_result_20260629.md`（GA 救活 architecture 證據）
- `v181_SP_IOG_fix_spec_20260629.md`（v1.8.1 fix 設計）
- `v181_BarStatusFix_FAILED_20260629.md`（v1.8.1-single FAIL）
- 本檔（v1.8.1-GA FAIL + 架構 verdict）
