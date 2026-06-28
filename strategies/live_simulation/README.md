# strategies/live_simulation/ — 上架但模擬中策略

> 這裡的策略已部署到 MultiCharts 12 **模擬帳戶**運行，但 **尚未** 進入實盤。
> 必須累積足夠模擬實證後才能晉升到 [`strategies/live/`](../live/)。

---

## 模擬中策略清單（截至 2026-06-28）

| 策略 | 類別 | 方向 | 版本 | 標籤前綴 | 模擬起始 |
|------|------|------|------|----------|----------|
| **S1** NightMomentum | A 類時段型 | 純多 | **v2.6 + Settlement + ImmediateStop + HolidayFlat_v3** | `LE_NM_` / `LX_NM_` | 2026-06-07 |
| **S3** RapidPullbackShort | 多頭過熱拉回 | 純空 | **v2.0.4** | `SE_RPS_` / `SX_RPS_` | 2026-06-20 |
| **S3_L** VolSqueezeLong | C 類波動率（純多）| 純多 | **v1.0 (W5 PASS, 5% portfolio cap)** | `LE_VS_` / `LX_VS_` | **2026-06-23** |
| **S3_S** VolSqueezeShort | C 類波動率（純空）| 純空 | **v1.7.3-FINAL (BWPctile 25, SlowMA 40, 3% cap, precision hedge)** | `SE_VS_` / `SX_VS_` | **2026-06-28** |

⚠️ **S3_L 部署 caveats**：portfolio 5% 上限 + 不可加 event filter + 已配對 S3_S。詳見 [S3_VolSqueezeLong_DEPLOYMENT.md](S3_VolSqueezeLong_DEPLOYMENT.md)。

⚠️ **S3_S 部署 caveats**：3% 上限 + 4 trades/year by design + 接受 Tier S 偶有漏抓 + 12 個月 0 trades 觸發 review。詳見 [S3_S_VolSqueezeShort_DEPLOYMENT.md](S3_S_VolSqueezeShort_DEPLOYMENT.md) + [S3_S_VolSqueezeShort_strategy.md](S3_S_VolSqueezeShort_strategy.md) + [S3_S_VolSqueezeShort_BOSS_VIEW.md](S3_S_VolSqueezeShort_BOSS_VIEW.md)。

---

## 📋 BOSS_VIEW 規範（2026-06-28 新增）

**每隻** promoted 到 `live_simulation/` 或 `live/` 的策略**強制**附 `_BOSS_VIEW.md`，作為老闆 / 主管 / 投委會的快速 view（< 1 頁）。
規範詳見 [`docs/methodology/BOSS_VIEW_TEMPLATE.md`](../../docs/methodology/BOSS_VIEW_TEMPLATE.md)。

| 策略 | BOSS_VIEW 狀態 |
|------|--------------|
| S1 NightMomentum | ⏳ 待補 |
| S3 RapidPullbackShort | ⏳ 待補 |
| S3_L VolSqueezeLong | ⏳ 待補 |
| **S3_S VolSqueezeShort** | ✅ [BOSS_VIEW](S3_S_VolSqueezeShort_BOSS_VIEW.md) (2026-06-28 首份) |

---

## S1 v2.2 重要變更（2026-06-13）

### P0 Critical Bug Fix
- **ExitTime 500 → 415**（原 500 = 夜盤最後一根 K 棒，`next bar at market` 卡到 08:45 日盤）
- 修正後：04:15 觸發 → 04:30 成交（夜盤內）→ 04:45/05:00 重試
- 解決「純夜盤策略卻在 09:00 出場」的核心 bug

### P1 HolidayFlat_v3 模組
- 與 L1-L5 byte-identical 的 63 筆 TAIFEX 登錄表
- Manual_Kill_Switch / Registry_Valid_Until / 30 天警告
- 新出場標籤：`LX_NM_Kill` / `LX_NM_RegistryEnd` / `LX_NM_Holiday`

---

## 晉升到 `live/` 的條件

模擬期需累積以下證據：

| 指標 | 門檻 | 目的 |
|------|------|------|
| 模擬實戰交易筆數 | ≥ 30 筆 | 樣本充足 |
| 模擬期 PF | ≥ 1.2 | 確認獲利穩定 |
| 模擬期 MDD | ≤ 帳戶 25% | 風險可承受 |
| 與回測 PF 偏離度 | ≤ 30% | 模擬接近回測 |
| 假日鐵律觸發 | 0 次違規 | 安全性確認 |
| 滑價成本符合預估 | 單邊 ≤ 500 NTD | 執行品質 OK |

---

## CLAUDE.md 規範對齊（研究→上架轉換 PHASE）

研究階段 (`research/`)：
1. Phase 1: 參數敏感度
2. Phase 2: Walk-Forward Analysis（IS:OOS = 4:1，9 窗口）
3. Phase 3: Monte Carlo 壓力測試

模擬階段 (`live_simulation/`)：
4. **Phase 4**: 真實 MC 模擬帳戶部署（**S1 目前在此**）
5. Phase 5: 累積 ≥ 30 筆模擬交易 + 對比回測

上架階段 (`live/`)：
6. 進入實盤（**L1-L5 目前在此**）

---

## 驗證腳本

```bash
# S1 v2.2 sanity check
python scripts/verify_s1_v22.py     # 26/26 項
```

---

## 與 live/ 策略的差異

| 維度 | live/ | live_simulation/ |
|------|-------|------------------|
| 平台 | MC9 實盤帳戶 | MC12 模擬帳戶 |
| 資金 | 真金白銀 | 紙上交易 |
| 變更頻率 | 嚴格（空手才能改）| 較寬鬆 |
| Verification | verify_all_live.py（必通過）| verify_s1_v22.py（單檔）|
| Risk 上限 | 帳戶 MDD ≤ 30% | 隨意（模擬無資金限制）|

---

## 已通過 P1-P3 但等模擬驗證的後續策略候選

（待研究完成後從 [`research/`](../research/) 升級至此）：
- 待新策略陸續產出
