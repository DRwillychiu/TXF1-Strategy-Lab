# S3_S v1.8.1 BarStatus Fix — **FAILED** verdict

**日期**：2026-06-29
**Verdict**：🚨 **Bug 2 SP IOG fix FAILED — BarStatus(1)=2 gate 在 IOG=true 環境下無效**
**Critical**：v1.8.1 SP maxL **更糟**（-132K → -143K）+ 引入新問題（Mid -107K）

---

## 一、Headline FAIL

| 指標 | v1.8.0-GA | **v1.8.1** | 變化 |
|------|----------|-----------|------|
| **SP maxL** | -132,200 | **-143,200** 🚨 | **更糟 -11K** |
| Net | +846K | +585K | **-31%** ❌ |
| PF gross | 4.13 | 3.18 | -23% |
| PF adj | 2.24 | 1.69 | -25% |
| MDD % | -19.4% | -25.2% | **-5.8pp 更糟** |
| Sharpe | 0.56 | 0.43 | -23% |
| Sortino | 0.47 | 0.29 | -38% |

→ **5 verify gates 2/5 pass**（only 1M_Exit 救援功能保留）

---

## 二、Root Cause: BarStatus gate **無法控制 stop order fire timing**

### 設計初衷
```pla
if BarStatus(1) = 2 then begin   { 只在 60M K 收盤後設 stop }
    buy to cover ( "SX_VS_SP" ) next bar at v_SP_Floor_Price Stop;
end;
```

### 實際 MC12 engine 行為
1. **Stop order 一旦 set 就 active**（不論何時 set）
2. **IOG=true 下 stop 在任何 1M tick 都可 fire**
3. **Fill 在 1M K 的 worst tick**（intrabar）
4. **BarStatus gate 只 gates SET 時點，不 gates FIRE 時點**

### 還有 Section 9 SetStopLoss 平行 fire
- Engine-level guard 在 IOG=true 仍 intrabar fill
- 跟 Section 11 stop order 雙重 active
- BarStatus gate 完全沒控住

### 同 case 證據（2024-08-05 BoJ）

| 版本 | SP fill | 點數 |
|------|---------|------|
| v1.7.3 IOG=false | (不同 trade 邏輯) | n/a |
| v1.8.0-GA IOG=true | -132,200 | -661 點 |
| **v1.8.1 BarStatus gate** | **-143,200** | **-716 點 更糟** |

→ **BarStatus gate 完全無效**，反而 SP 觸發推遲導致 fill 更糟

### 新引入問題：Mid Exit 多虧
- v1.8.0-GA Mid: 0 筆
- v1.8.1 Mid: **2 筆 / avg -53K / maxL -58K**
- BarStatus gate 推遲 Mid exit → 錯過小虧出場機會

---

## 三、5-Way 對照（**v1.8.1 反而退步**）

| 指標 | v1.7.3 | v1.7.4 | v180-orig | v180-GA | **v1.8.1** |
|------|--------|--------|-----------|---------|-----------|
| Net | **+1,013K** | +792K | +502K | +846K | +585K |
| PF gross | 3.95 | 2.81 | 1.87 | **4.13** | 3.18 |
| PF adj | 2.17 | 1.72 | -0.99 | **2.24** | 1.69 |
| Sharpe | **0.69** | 0.64 | 0.40 | 0.56 | 0.43 |
| Sortino | **1.08** | 1.18 | 0.27 | 0.47 | 0.29 |
| **MDD %** | -22.1% | -19.2% | -19.9% | **-19.4%** | **-25.2%** 🚨 |
| **SP maxL** | -5K | -4.8K | -132K | -132K | **-143K** 🚨 |

→ **v1.7.3-FINAL 仍是 best**

---

## 四、5 Verify Gates 完整 audit

| Gate | 標準 | v1.8.1 實際 | 結果 |
|------|------|------------|------|
| G1 SP maxL > -15K | > -15K | **-143K** | ❌ **FAIL** |
| G2 Net > +900K | > +900K | +585K | ❌ FAIL |
| G3 PF gross > 3.95 | > 3.95 | 3.18 | ❌ FAIL |
| G4 1M_Exit ≥ 2 | ≥ 2 | 2 | ✅ PASS |
| G5 6/8 case < -20 pts | < -20 pts | -10 pts | ✅ PASS |

→ **2/5 pass**（只有 1M_Exit 救援保留）

---

## 五、Lesson L32 候選（**永久 codify**）

### Lesson L32: BarStatus Gate 在 IOG=true 下無法控制 Stop Order Fire Timing

**Why**:
- MC12 stop order 一旦 set 就 active 整個 1M K cycle
- BarStatus gate 只控制 SET 時點，不控制 FIRE 時點
- IOG=true 環境下，stop order fill 仍在 1M intrabar 任意 tick
- SetStopLoss engine-level guard 跟 limit/stop orders 平行 fire

**How to apply**:
- 不要嘗試用 BarStatus gate fix IOG=true 的 stop order 副作用
- 真要解需用其他架構（雙策略 / IOG=false + 監測 indicator）
- 或接受 IOG=false 的 limitation

---

## 六、4 個 Lessons 完整 catalog（v1.7.4 → v1.8.1 學到的）

| # | Lesson | 證據版本 |
|---|--------|---------|
| **L29** | Hard SL Cap 在 Gap 風險下完全失效 | v1.7.4 cap 100 (6/8 -466 pts) |
| **L30** | 1M Multilayer 在 IOG=true 引入新風險 | v180-orig SP -132K |
| **L31** | 多複雜度 ≠ 多保護（GA 證明 architecture 但 IOG 仍壞 SP）| v180-GA |
| **L32** | **BarStatus Gate 在 IOG=true 下無法控 stop fire timing** | **v1.8.1 本檔** |

---

## 七、Final Decision: **Path D 接受 v1.7.3-FINAL**

### 證據鏈
1. **v1.7.3-FINAL 仍是 7/9 指標 best**（Net / Sharpe / Sortino / WR）
2. **v1.7.4 / v1.8.0-orig / v1.8.0-GA / v1.8.1 全試過**，均未超越
3. **Bug 2 SP IOG 是 MC12 engine 限制**，邏輯無法解
4. **業界對策**：portfolio cap（v1.7.3 已 3% cap）+ 接受偶爾 SL 大虧為 alpha 代價

### 該做的
1. **接受 v1.7.3-FINAL 為 final production**
2. **archive v1.7.4 / v1.8.0 / v1.8.1** 為 learning records
3. **永久 codify L29-L32 lessons** to `docs/policies/`
4. **後續：portfolio cap 控制單筆風險**（DEPLOYMENT.md 已設 3%）

---

## 八、未來研究方向（**待時再做**）

### 若要真解 SP IOG 副作用
| Path | 邏輯 | 風險 |
|------|------|------|
| 雙策略架構 | IOG=true 監測 + IOG=false 執行 | 極複雜，IPC 同步問題 |
| MC12 forum 研究 | BarStatus + IOG 邊界情境 | 不確定可解 |
| 改用 limit order | 避免 stop fill | 失去 gap protection |
| 改 1M_Exit 為純 indicator | 不用 IOG | 失去即時反應 |

### 1M fill SL future research（Task #142 仍 pending）
- 已 codify 在 `docs/research/1M_fill_SL_extreme_market_research_TODO.md`
- 6 候選方向待 v1.7.3 promote 後再評估

---

## 九、相關文件

- `S3_VolSqueezeShort_v181_EXPERIMENTAL.pla` (本檔對應 .pla, archived)
- `v181_SP_IOG_fix_spec_20260629.md` (原 fix spec, 預估 vs 實際差距)
- `v180_GA_R1_result_20260629.md` (GA 救活 architecture 證據)
- `v174_v180_desktop_threeway_analysis_20260629.md` (3-way 對比)
- `live_simulation/S3_S_VolSqueezeShort.pla` v1.7.3-FINAL (production)

---

## 十、Status

- **v1.7.3-FINAL**: ✅ **PRODUCTION**（live_simulation, 不動）
- v1.7.4 cap 100: ⚠️ ARCHIVED (L29 gap failure proof)
- v1.7.5 conditional: SUPERSEDED
- v180-orig: ARCHIVED (L30 complexity failure)
- v180-GA: ARCHIVED (L31 GA 證明 architecture 但 SP IOG 不解)
- **v1.8.1: ARCHIVED (L32 BarStatus gate 失敗)**
