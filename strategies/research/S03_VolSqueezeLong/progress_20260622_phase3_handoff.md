# S3_L VolSqueezeLong — Phase 3 Progress Handoff (2026-06-22)

**寫於**：2026-06-22 桌機端 session 結束
**收件人**：明日（2026-06-23）筆電端 Claude
**狀態**：✅ Phase 1/2/3 完成（**7/7 機構 gates PASS + overtake B&H**）
**下一步**：等用戶決定 A (Phase 4) / B (W4 WFO) / C (W5 eval)

---

## 一、4 階段完整結果對比（**核心進度**）

策略屬性統一：1,000,000 NTD 帳戶 + 1,000 NTD round-trip 滑價 + 1 contract + 60M TXF1 + 2020-01-20 ~ 2026-06-06

| 指標 | Baseline | Phase 1 (GA) | Phase 2 (Refine) | **Phase 3 (邊角推外)** |
|------|---------|-------------|------------------|----------------------|
| 淨利 | 519K | 1,380K | 2,132K | **2,654K** |
| **PF (毛)** | 1.28 | 2.04 | 2.41 | **2.55** |
| **PF (含滑價)** | 1.02 | 1.59 | 1.87 | **2.00** |
| 樣本 | 170 | 127 | 124 | **134** |
| WR | 42.4% | 52.8% | 54.0% | **53.0%** |
| **Sharpe (年化)** | 0.46 | 0.81 | **1.05** | **1.02** |
| 索丁諾 | 0.44 | 0.66 | 0.82 | **0.84** |
| **Max DD %** | — | 17.3% | 16.2% | **13.1%** |
| **vs B&H** | — | 0.56× | 0.86× | **1.07×** ⭐ |
| 年化報酬 | — | 21.6% | 33.4% | **41.6%** |
| 滑價支付 | 137K | 198K | 198K | 231K |

---

## 二、Phase 3 best params（**目前 lock 值**）

```
BBLen                = 45
BBStd                = 2.0      (一直鎖, 未掃)
BWLookback           = 120      (一直鎖, 未掃)
BWPctile             = 30
ATR_Len              = 14       (一直鎖, 未掃)
StopATRMult          = 2.75     (Phase 2 plateau confirmed)
TargetATRMult        = 8.0      (⚠️ 仍上邊角)
MaxBars              = 70       (Phase 2 plateau confirmed)
UseMidExit           = True
MidExit_MinBars      = 3
Cooldown_Days        = 1
Holiday_Flat_Time    = 415      (rule fixed)
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230     (Rule #11 fixed)
```

---

## 三、機構 gates 評估（**7/7 PASS + overtake B&H**）

| Gate | 標準 | Phase 3 結果 | Status |
|------|------|-------------|--------|
| PF gross | > 1.3 | 2.55 | ✅✅ |
| PF 含滑價 | > 1.3 | 2.00 | ✅✅ |
| Sharpe (年化) | > 0.4 | 1.02 | ✅✅ (excellent threshold > 1.0) |
| 樣本 | > 100 | 134 | ✅ |
| WR | > 50% | 53.0% | ✅ |
| Max DD | < 25% | 13.1% | ✅✅ |
| **vs B&H** | be diversifier (> 0) | **1.07×** | ⭐⭐⭐ OVERTAKE |

→ **Institutional excellent**

---

## 四、邊角值狀態（**仍有 1/3 未解決**）

| Input | P3 Best | 範圍 | 邊角狀態 |
|-------|---------|------|---------|
| BBLen | 45 | 35-55 | ✅ 中間 plateau |
| BWPctile | 30 | 20-35 | ✅ 中間 |
| **TargetATRMult** | **8.0** | 5.5-8.0 | 🔴 **仍上邊角** |
| StopATRMult | 2.75 | (鎖 P2 best) | ✅ Plateau (P2 confirmed) |
| MaxBars | 70 | (鎖 P2 best) | ✅ Plateau (P2 confirmed) |

**Plateau 分析**：
- Sharpe 從 P2 1.05 → P3 1.02 微降 = alpha 接近 plateau ceiling
- PF 仍緩升 (2.41→2.55)
- Max DD 大幅改善 (-19%)
- Mid exit 大增 (30%→37%) = TargetATR 8 已超過大多 trade MFE
- TargetATR 仍上邊角但繼續推 = 過擬合 risk 升高

---

## 五、Exit 分布演進

| Exit | Baseline | P1 | P2 | P3 |
|------|---------|----|----|----|
| TP | — | 39% | 40% | **28%** ↓ |
| SL | — | 36% | 24% | 28% → 29% |
| Mid | — | 18% | 31% | **37%** ↑↑ |
| Settlement | — | 0 | 1 | 5 |
| TimeStop | — | — | — | 2 |

→ TargetATR 8 ATR 太遠 → Mid exit 取代 TP 成主要出場

---

## 六、跨年穩定（**所有 7 年都有交易，無 regime 集中**）

| Year | Baseline | Phase 3 |
|------|---------|---------|
| 2020 | 29 | 20 |
| 2021 | 27 | 21 |
| 2022 | 14 | 15 |
| 2023 | 31 | 19 |
| 2024 | 30 | 24 |
| 2025 | 26 | 22 |
| 2026 | 13 | 13 |

→ 不像 S3 v1.1 集中 2026 H1 (54%) 的 regime over-fit

---

## 七、3 條路（**等用戶決定**）

### A. Phase 4 推 TargetATRMult (8-12)
- 確認真 plateau
- 風險: 過擬合風險升高
- 預估 ~50-100 組合，可 Exhaustive

### B. 接受 P3，進 **W4 Walk-Forward** (我推薦)
- IS 2020-2024 / OOS 2025-2026
- Gate: WFE > 50% + OOS PF > 1.0 + OOS Sharpe > 0
- WFO 是 institutional robustness gate
- 通過 → W5 10-dim eval → 晉升 live_simulation
- 失敗 → 回頭看是 P3 over-fit 還是 OOS regime change

### C. 直接 W5 10-dim eval
- Phase 3 已 7/7 gates PASS
- 跳過 WFO 風險（無 OOS 驗證）

**我（桌機端 Claude）的推薦：B**

理由:
1. Phase 3 已 institutional excellent
2. Sharpe 持平暗示 alpha 接近 plateau ceiling
3. TargetATR 還能推但 marginal + 過擬合 risk 升
4. WFO 是真正 robustness gate
5. 通過 WFO 後 W5 → live_sim 是 OFFICIAL_ROADMAP 順序

---

## 八、用戶 conversation context（**明天筆電端 Claude 必讀**）

### 用戶今天的關鍵 instructions

1. **「直接給我 .pla 給我去進行回測」**（2026-06-22 早）
   → 我寫了 S3_VolSqueezeLong.pla v1.0 (529 LOC, commit 2519435)

2. **「給我能夠做最佳化的參數完整範圍」**（baseline 後）
   → Phase 1 GA 5 inputs × 1024 組合

3. **「採用 A」**（Phase 2 後）
   → 用戶選 Phase 3 邊角推外（**問了過擬合 risk**）

4. **「先更新現階段的進度到 git」**（Phase 3 後）
   → 本檔

### 用戶 institutional discipline 重點

- **不要自動 KILL/GO** — 用戶要看分析後**自己決定**
- **完整 SOP** — Stage -1 必先給
- **按 OFFICIAL_ROADMAP** — 不發明、不跳號、不平行開發
- **R-6 鐵則** — 先 L 後 S
- **Stage -1 強制**: 內容/優點/缺點/為什麼合適 4 段

### 明日筆電端 Claude SOP

```
1. git pull origin main 確認同步
2. 讀本檔 progress_20260622_phase3_handoff.md
3. 詢問用戶選 A / B / C
4. 不主動決定 — 等用戶 explicit instruction
5. 若用戶選 B (W4 WFO):
   - 提供 MC12 WFO 設定 (IS/OOS 切分)
   - 等用戶跑完傳 xlsx
   - 分析 WFE
6. 若用戶選 A (Phase 4):
   - TargetATRMult: 8 → 12 step 0.5 (8 values)
   - 其他全鎖 P3 best
   - Exhaustive ~8 組合 + GA 50/30
```

---

## 九、相關文件 + commit

### 今日 commit 軌跡
- `2519435` S3_L VolSqueezeLong .pla v1.0 (529 LOC, MC12 ready)
- (本檔將補在下一個 commit)

### 重要參考文件
- `docs/policies/OFFICIAL_ROADMAP.md` — 排程鎖定（R-1 ~ R-6）
- `docs/STRATEGY_RD_SOP_v2.md` — 流程 SOP (含 Stage -1)
- `CLAUDE.md` Rule #11/#12/#13/#14 — 強制規範
- `strategies/research/S03_VolSqueezeLong/README.md` — 策略入口
- `strategies/research/S03_VolSqueezeLong/S3_VolSqueezeLong.pla` — v1.0 程式碼

### 用戶手上 xlsx（**未進 git**）
- baseline (預設值): TXF1  S3_VolSqueezeLong 策略回測績效報告.xlsx
- Phase 1 (GA after): TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後.xlsx (100K 帳戶)
- Phase 1 honest (1M+1000): TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後.xlsx (修正)
- Phase 2 (Refine GA): TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後2.xlsx
- Phase 3 (邊角推外 Exhaustive): TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後3.xlsx

---

## 十、git 狀態

- Latest commit: `2519435` (S3_L .pla v1.0)
- Working tree: clean (除本檔將 commit)
- Remote: 同步 origin/main
- 桌機端今日進度: 完整 commit + push

---

**明日筆電端見**。用戶 explicit 說「明天繼續」，**不要自動跑 Phase 4 / WFO**，等用戶 instruction。
