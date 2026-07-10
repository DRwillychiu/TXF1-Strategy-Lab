# S16_S MACrossShort — Promotion Report (2026-07-10)

**Promote Type**: research → live_simulation
**Version**: v1.0-PROD
**Portfolio Cap**: 3%
**Backtest 期間**: 2020-01-01 ~ 2026-07-06

---

## 一、Promote Decision Evidence

### W0 Alpha Pre-Verify (2026-07-08)
STRONG PASS — Daily proxy 40/216 combos 4/4 gates

### W1 Strategy Definition (2026-07-08)
14 章機構級規格

### W2 .pla 實作 (2026-07-08)
初版 v0.1-DRAFT → v0.3-P0FIX → v0.4-CANDIDATE → v0.5-FINAL → v1.0-PROD

### W3 MC12 Backtest (2026-07-09)
Multiple candidates tested

### W4 GA Optimization (2026-07-09)
1024-combo Genetic Algorithm

### W4 Walk-Forward Analysis (2026-07-10)
**STRONG PASS — WFE 77.4%**
- 9 windows / 416 OOS trades / +1,737,800 aggregate
- 7/9 windows profitable
- Parameter drift CV 21-25% MODERATE

### W5 Rule #18 Non-WFA 5-piece (2026-07-09)
Sniper-adapted 8/8 PASS

---

## 二、Rule Compliance

| Rule | 判定 |
|------|------|
| #11 Settlement_Flat | ✅ |
| #12 SetStopLoss guard | ✅ |
| #13 10-dim (7/10 PASS) | ✅ 接受 |
| #14 OFFICIAL_ROADMAP | ✅ Batch 04 |
| #15 ASCII 100% | ✅ 27/27 |
| #16 五支柱 | ✅ |
| #17 Multi-Layer SL | ✅ M6 |
| #18 Non-WFA + WFA | ✅ |

---

## 三、Promote SOP 10 Steps Checklist

- [x] Step 1: Rename version v0.5-FINAL → v1.0-PROD
- [x] Step 2: Move .pla → `live_simulation/S16_S_MACrossShort.pla`
- [x] Step 3: 寫 `S16_S_MACrossShort_DEPLOYMENT.md`
- [x] Step 4: 寫 `S16_S_MACrossShort_BOSS_VIEW.md`
- [x] Step 5: 寫本 PROMOTION.md
- [ ] Step 6: Update `strategies/live_simulation/README.md`
- [ ] Step 7: Update `strategies/research/README.md`
- [ ] Step 8: Update `docs/policies/OFFICIAL_ROADMAP.md`
- [ ] Step 9: ASCII verify
- [ ] Step 10: Commit + push

---

## 四、Key Development Milestones

| 日期 | 里程碑 |
|------|-------|
| 2026-06-28 | 用戶 override Rule R-1 加入 S16 到 roadmap |
| 2026-07-07 | Layer 1 進場設計 lock（M1 KEEP, M2/M3/M4 DROP）|
| 2026-07-08 | Layer 2 出場 8 層 priority chain + Layer 3 Option A |
| 2026-07-08 | W0 STRONG PASS + W1 spec 完成 + W2 pla |
| 2026-07-09 | v0.4 → v0.5 sweet spot, W5 Sniper 8/8 PASS |
| 2026-07-10 | v0.6 ATR 拒絕 + revert v0.5, W4 WFA WFE 77.4% |
| **2026-07-10** | **v1.0-PROD PROMOTE** |

---

## 五、Rejected Alternatives (Audit Trail)

| Alternative | 決定 | 理由 |
|-----------|------|------|
| 加 Regime Filter | 拒絕 | Option A 純規則簡單 |
| 加 ATR gate (M3) | 拒絕 | ATR 延遲，錯過 burst 起點 |
| 加 Volume gate (M4) | 拒絕 | 夜盤 volume 稀薄 |
| Fast N-bar delay (M2) | 拒絕 | 5M 承擔不起延遲 |
| v0.6 ATR-based Slope | 拒絕 | ATR 混淆方向與波動 |

---

## 六、Portfolio 影響

### 新配置

| 策略 | Cap | 角色 |
|------|-----|------|
| S3_L VolSqueezeLong | 5% | 多頭波動率 |
| S3_S VolSqueezeShort | 3% | 空頭波動率 |
| S1 NightMomentum | ? | 時段動能 |
| S3 RapidPullbackShort | ? | 拉回狙擊 |
| **S16_S MACrossShort** | **3%** | **動能 sniper（新）** |
| L1-L5 | 各 % | 趨勢 / 盤整 |

---

## 七、Next Steps

1. **模擬期部署**（今日起）
2. **每季 review**（監控紅線）
3. **累積 30 筆 + PF ≥ 1.2 + 偏離度 ≤ 30% → 升 live**
4. **預估模擬期**：~24 個月

---

## 八、Files Migration

### From research/ (歷史保留)
- `S16_S_MACrossShort.pla` (v1.0-PROD)
- `S16_S_strategy.md`
- `S16_S_entry_exit_spec_20260708.md`
- `S16_S_FINAL_SUMMARY_20260710.md`
- `W0_alpha_preverify_result_20260708.md`
- `W3_MC12_backtest_SOP.md`
- `W4_ReGA_Phase1_analysis_20260709.md`
- `W4_WFA_analysis_20260710.md`
- `W5_fivepack_validation_20260709.md`
- `v04_CANDIDATE_analysis_20260709.md`
- `v06_ADAPTIVE_test_SOP_20260710.md`
- `PENDING_DECISION_20260709.md`
- `MA_deep_research_20260707.md`
- 3 handoffs

### To live_simulation/ (production)
- `S16_S_MACrossShort.pla` (v1.0-PROD)
- `S16_S_MACrossShort_DEPLOYMENT.md`
- `S16_S_MACrossShort_BOSS_VIEW.md`

---

**Promoted 2026-07-10 Desktop** 🎯

Ready for MC12 simulation deployment.
