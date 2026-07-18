# strategies/research/ — 研究中策略（OFFICIAL_ROADMAP 單軌）

> **2026-06-23 更新**：原雙軌系統（軌道 B 每週批次）已正式廢除。
> 開發**嚴守 OFFICIAL_ROADMAP 單軌順序**（CLAUDE.md Rule #14 強制）。

---

## 一、現行策略狀態

### Active 開發中

| 編號 | 策略 | 狀態 | 位置 |
|------|------|------|------|
| **S16_S_10M** | **MACrossShort 10M 時框延伸** | 🔵 **CURRENT — 2026-07-18 重啟 Stage-1 討論（S16_S v1.4 收官上架後主線）** | 待建 folder |

### SUSPENDED（暫停）

| 編號 | 策略 | 狀態 | 位置 |
|------|------|------|------|
| S16_L | MACrossLong | 🟡 SUSPENDED 2026-07-10（用戶優先做時框延伸實驗）| [`S16_MACrossLong/`](S16_MACrossLong/) |

### 最近 PROMOTED (history archived)

| 編號 | 策略 | 狀態 | 位置 |
|------|------|------|------|
| **S16_S** | **MACrossShort** | ✅ **v1.4-BELATE 正式上架 2026-07-18**（718 baseline 107T/+1,094,800/PF 1.91；5件套通用4/5 適性5/5；參數凍結鐵則；原 WFE 77.4% 已作廢見 WFA_AUDIT）| [`S16_MACrossShort/`](S16_MACrossShort/)（完整研發史 26 份文件保留）|
| **S3_S** | **VolSqueezeShort** | ✅ **PROMOTED 2026-07-06 v1.9.6-OPT-PROD (7/7 gates PASS)** | [`S03_VolSqueezeShort/`](S03_VolSqueezeShort/)（history 保留研究資料夾）|
| S3_L | VolSqueezeLong | ✅ Promoted 2026-06-23 → live_simulation/ | [`archive/S03_VolSqueezeLong_promoted_20260620/`](archive/S03_VolSqueezeLong_promoted_20260620/) |

### 最近 KILLED (roadmap 依 explicit user ruling 跳過)

| 編號 | 策略 | 狀態 |
|------|------|------|
| S4_L | MACDDivergenceLong | ⚰️ KILLED 2026-07-07（MACD 不適合作獨立策略）|
| S4_S | MACDDivergenceShort | ⚰️ KILLED 2026-07-07（同上）|

→ S3_S / S3_L production .pla 在 [`../live_simulation/`](../live_simulation/)
→ W0-W5 開發歷史已歸檔至 archive/

---

## 二、OFFICIAL_ROADMAP 完整排程

按 [`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md) Rule R-6 拆解後：

```
S3_L ✅PROMOTED → S3_S ✅PROMOTED → S4_L ⚰️KILLED → S4_S ⚰️KILLED
→ S16_S ✅PROMOTED → S16_L 🔵CURRENT → S5_L → S5_S → S6 → S7 → S8
→ S9_L → S9_S → S10_L → S10_S → S11 → S12_L → S12_S → S13 → S14_L → S14_S → S15_L → S15_S
```

**鐵則**（Rule #14）：
- 不發明新策略名稱
- 不跳號（S3_S 完成必直接 S4_L）
- 不平行開發（一次一隻）
- 必先 L 後 S（R-6 順序）
- 每隻必走 W0 alpha pre-verify → W1-W5 流程

---

## 三、開發流程（W0-W6）

| Phase | 內容 | KILL Gate |
|-------|------|-----------|
| Stage -1 | 策略 4 段討論（內容/優點/缺點/為什麼合適）| 用戶 NO-GO |
| W0 | Python 真實資料 alpha pre-verify | alpha 不存在 → KILL |
| W1 | strategy.md (規格) + annotated.md (中文逐段) | — |
| W2 | .pla 實作 (Rule #11/#12/#14 必含) | — |
| W3 | MC12 baseline backtest | — |
| W4 | Walk-Forward (IS 2y / OOS 6m, WFE > 50%) | WFE fail → KILL |
| W5 | 10-dim institutional eval (Rule #13) | 任 dim fail → KILL or 退回 |
| W6 | Promote live_simulation OR KILL with FINAL_VERDICT.md | — |

詳見 [`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md) 完整 SOP。

---

## 四、品質門檻（Rule #13 10 dimensions）

| 指標 | 門檻 | 來源 |
|------|------|------|
| Sharpe / Sortino / Calmar | ≥ 0.15 | Rule #13 |
| Max DD | < 25% account | Rule #13 |
| 跨策略相關性 | < 0.7 | Rule #13 |
| DD Clustering | < 3 sigma (or event-level acceptable) | Rule #13 |
| 樣本數 | ≥ 100 | Rule #13 |
| WFE | > 50% | Rule #13 |
| 三市況 PF | > 1.0 各別 | Rule #13 |
| Adj PF (含滑價) | > 1.3 | Rule #13 |
| Operational risk | 5 元素 (Settlement / SetStopLoss / Holiday / Kill / IOG) | Rule #11/#12 |
| Regulatory | 標準 TXF1 1 contract | — |

---

## 五、Lesson 機構級規範（codified to date）

| Lesson | 內容 | 文件 |
|--------|------|------|
| L1-L23 | KILL 經驗累積（off-roadmap S4-S9 全 KILL）| `docs/archive/offRoadmap_2026Q2/` |
| **L24** | **Risk overlay 不可削 alpha source** | [`../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md`](../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md) |

---

## 六、archive/ 歷史結構

| 子資料夾 | 內容 | 保留原因 |
|---------|------|---------|
| [`archive/batch01_S2-S5/`](archive/batch01_S2-S5/) | 原始排程 S2-S5 .pla 雛形 + 設計文件 | 規格依據 |
| [`archive/batch02_S6-S10/`](archive/batch02_S6-S10/) | 原始排程 S6-S10 .pla 雛形 | 規格依據 |
| [`archive/batch03_S11-S15/`](archive/batch03_S11-S15/) | 原始排程 S11-S15 .pla 雛形 | 規格依據 |
| [`archive/S02_InsideBarBreak_killed_20260622/`](archive/S02_InsideBarBreak_killed_20260622/) | S2 開發到 v0.6 後 KILLED | KILL audit trail |
| [`archive/S03_RapidPullbackShort_archived_20260622/`](archive/S03_RapidPullbackShort_archived_20260622/) | S3 off-roadmap 命名（已部署 live_sim 用 S3_RapidPullbackShort）| 命名衝突解決 audit |
| [`archive/offRoadmap_2026Q2_killed/`](archive/offRoadmap_2026Q2_killed/) | 2026-06-19~21 偏離排程 6 隻 KILLED | Lessons L14-L23 證據 |
| [`archive/_batch_summaries/`](archive/_batch_summaries/) | 批次摘要 docs | reference |

---

## 七、相關核心文件

- 排程鐵則：[`docs/policies/OFFICIAL_ROADMAP.md`](../../docs/policies/OFFICIAL_ROADMAP.md) (Rule #14)
- 規範總覽：[`CLAUDE.md`](../../CLAUDE.md) (Rules #1-#14)
- Lesson L24：[`docs/policies/lesson_L24_risk_overlay_alpha_preservation.md`](../../docs/policies/lesson_L24_risk_overlay_alpha_preservation.md)
- 進度追蹤：[`optimization/TRACKER.md`](../../optimization/TRACKER.md)

---

## 八、雙軌系統廢除說明（2026-06-23 archive）

原 `2026-W24/`（Cowork 每週批次軌道 B）已**廢除並刪除**，原因：
- OFFICIAL_ROADMAP Rule #14 鎖定**單軌順序**（用戶 2026-06-22 ruling）
- 軌道 B "每週 5 組 S16+" 平行開發 = 違反 Rule #14
- Cowork 自動化生成 = 違反「先 Stage -1 + W0 alpha pre-verify」流程
- 雙軌混淆 OFFICIAL_ROADMAP 順序 = 重蹈 2026-06-21 off-roadmap 覆轍

當前單軌：S3_S → S4_L → S4_S → ...
