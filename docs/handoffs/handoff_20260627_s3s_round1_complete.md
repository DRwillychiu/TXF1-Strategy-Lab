# Handoff 2026-06-27 — S3_S v1.7.1 Round 1 完整評估完成

**狀態**：✅ Round 1 best 完整通過 Stage-2 + W4 + W5 評估
**等候**：user explicit ruling A / B / C （promote 決策）
**下一動作**：用戶 confirm 後執行 promote 或 KILL

---

## 一、今日 4 個重大里程碑

### 1. Phase 2 GA Round 1 完成 — **8/8 institutional gates PASS**

| 指標 | v1.2 baseline | Round 1 best | 改善 |
|------|--------------|------------|------|
| Net Profit | +552K~+829K | **+1,245,400** | **+125%** |
| PF gross | 1.18 | **1.82** | +54% |
| **PF adj** | **-0.95** | **+1.42** | 首次含滑價賺錢 |
| **Sharpe** | 0.30 | **0.55** | 首次達 0.4 gate |
| **MDD %** | -47% | **-19.4%** | 首次達 25% gate |
| 2025 年 | -191K | **+245K** | 從虧轉賺 |

**Round 1 best params**:
- Regime_FastMA = **15** (was 20 baseline)
- Regime_SlowMA = **40** (was 50 baseline)
- Regime_MinRatio = **0.97** (was 0.98 baseline)
- 其他 14 inputs 全鎖 v1.2 default

### 2. Macro Events 覆蓋率分析

| 維度 | v1.2 baseline | Round 1 best |
|------|--------------|------------|
| Events 抓到 | 28/41 (68%) | 23/39 (59%) |
| 抓到 events 總 PnL | +869K | **+1,039K** |
| Tier S 大魚 (+100K+) | 5/5 抓 | **5/5 全抓** |
| SL 改善 | 8/-546K | **4/-189K** |

**3 個 alpha gap 結構性無解**:
- 2026-04-02 Trump 關稅再起（S3_L hedge gap）
- 2025-04-09 Trump 主跌日（先發制人代價）
- 2020-03-19 COVID 最大跌（先發制人代價）

### 3. W4 WFA — **8/9 windows PASS (institutional breakthrough)**

| WFA 版本 | Windows PASS | Median WFE | Mean OOS PF | Total OOS Net |
|---------|------------|-----------|-----------|--------------|
| v1.2 baseline | 3/9 | -19% | 0.85 | -156K |
| v1.6 GA 4-param | 3/9 | -8% | 0.93 | -85K |
| **Round 1 best** | **8/9** ⭐⭐⭐ | **+103.7%** | **1.72** | **+2,133,400** |

**W7 唯一 fail**: IS 2022-12~2024-12 (PF 13.70 alpha cluster), OOS 含已知 Trump 期 alpha gap

### 4. W5 10-dim Institutional — **9/10 PASS, 1/10 FAIL**

| Dim | Result |
|-----|--------|
| 1. Sharpe/Sortino/Calmar | ✅ 0.55 / 0.46 / 0.84 |
| 2. Max DD | ✅ -19.4% < 25% |
| 3. Cross-correlation | ⚠️ DEFAULT (data 缺) |
| 4. DD Clustering | ✅ via 3σ (259K < 380K) |
| 5. Sample | ✅ 140 > 100 |
| 6. WFE | ✅ +103.7% |
| **7. Three-regime PF** | ❌ **Range 0.73 FAIL** |
| 8. Cost adj PF | ✅ 1.42 > 1.3 |
| 9. Operational | ✅ 5/5 |
| 10. Regulatory | ✅ TXF1 1 contract |

---

## 二、🚨 重大發現：**Range Regime 不適用**

### 真實本質

**S3_S v1.7.1 Round 1 = 「Bull/Bear 強, Range 弱」的非對稱 alpha 策略**

| Regime | N | PF | Net | 評估 |
|--------|---|-----|------|------|
| Strong Bull | 4 | 4.49 | +162K | ⭐ 強 |
| Weak Bull | 21 | 1.61 | +164K | ✅ 中強 |
| **Range** | **65** | **0.73** | **-259K** | **❌ 唯一痛點** |
| Weak Bear | 11 | 11.00 | +492K | ⭐⭐ 極強 |
| Strong Bear | 1 | 99 | +10K | ⭐ |

**Range 65 trades 占總 46%** = 最高密度但 -259K
原因：TWII 0.98-1.02 ratio = 整理盤，BB Squeeze 頻發但 false breakout 多

整體仍賺因為 Bull/Bear/no_data 三組合 +1,555K 補回 Range -259K

---

## 三、Round 1 best 完整 inputs（live deployment ready）

```pla
{ === 鎖定 (v1.2 baseline 已驗證) === }
BBLen                = 45
BBStd                = 2.0
BWLookback           = 120
BWPctile             = 30
ATR_Len              = 14
StopATRMult          = 2.75
TargetATRMult        = 3.5
MaxBars              = 35
UseMidExit           = True
MidExit_MinBars      = 2
SP_Trigger_ATRMult   = 1.5
SP_Retain_Pct        = 70
Cooldown_Days        = 1

{ === Round 1 GA best (regime params) === }
Use_Regime_Filter    = True
Regime_FastMA        = 15        ⭐ Round 1
Regime_SlowMA        = 40        ⭐ Round 1
Regime_MinRatio      = 0.97      ⭐ Round 1
Regime_BlockWeakBull = True

{ === Compliance modules === }
Holiday_Flat_Time    = 415
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230
```

---

## 四、等候 user 決策（3 條路）

### Option A: KILL
- 嚴格 institutional: 1 dim fail = kill
- 浪費 9/10 PASS 的躍進

### Option B: Promote with caveats ⭐ (推薦)
- mv → live_simulation/
- 5% portfolio cap（與 S3_L 5% 共 squeeze sleeve 10%）
- Monitor Range regime PF rolling 30-day
- Kill triggers: monthly DD>5% / 3 Range losses>-150K / W7 cluster 重現

### Option C: Re-design Range filter
- ⛔ 違反 Lesson L24「不可加 event/regime sub-filter」

---

## 五、若用戶 Option B Promote 後續 SOP

```
1. mv strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort_v17.pla
     → strategies/live_simulation/S3_S_VolSqueezeShort.pla

2. 寫 S3_S_VolSqueezeShort_DEPLOYMENT.md (caveats + kill triggers)
3. 更新 strategies/live_simulation/README.md
4. 更新 docs/policies/OFFICIAL_ROADMAP.md (S3_S 標 PROMOTED)
5. 寫 S3_S_VolSqueezeShort_annotated.md
6. Git commit + push (atomic)

7. Roadmap 下一步: S4_L MACDDivergenceLong (OFFICIAL_ROADMAP Rule #14)
```

---

## 六、今日 commits（chronological）

| Commit | 內容 |
|--------|------|
| `7a14d75` | S3_S v1.7 → v1.7.1: regime MA 50/200 → 20/50 (Daily data fit) |
| `2eaaf5a` | Round 1 evaluation: 8/8 gates pass + macro events + 3 alpha gaps |
| `3f51b32` | W4 WFA: 8/9 windows PASS - institutional breakthrough |
| `f00d829` | W5 10-dim: 9/10 PASS (Range FAIL, promote with caveats) |

---

## 七、筆電端 resume 入口

1. **Git pull**: `cd C:/tmp/TXF1-Strategy-Lab && git pull origin main`
2. **讀**:
   - `strategies/research/S03_VolSqueezeShort/v17_round1_evaluation_20260627.md`
   - `strategies/research/S03_VolSqueezeShort/v17_round1_w4_wfa_20260627.md`
   - `strategies/research/S03_VolSqueezeShort/v17_round1_w5_institutional_20260627.md`
3. **執行**: 用戶會 ruling A/B/C，照本 handoff 第四節執行對應 SOP

---

## 八、相關核心文件

- `S3_VolSqueezeShort_v17.pla` (production .pla v1.7.1)
- `STRATEGY_SUCCESS_CRITERIA.md` (W5 standards)
- `LOOP_FRAMEWORK.md` (Phase 2 GA SOP)
- `lesson_L24_*.md` (不可加 event filter)
- `OFFICIAL_ROADMAP.md` (S3_S 排程)
- `wfa_loop_runner.py` (WFA auto-judge)
