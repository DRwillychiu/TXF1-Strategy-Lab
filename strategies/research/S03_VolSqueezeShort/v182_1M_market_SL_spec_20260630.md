# S3_S v1.8.2 EXPERIMENTAL — 1M Market Exit for SP/SL（取代 Stop order）

**日期**：2026-06-30
**驅動 ruling**：user 2026-06-30：「初始停損的出場是否可以直接是採用 1mins 作為出場?」
**目標**：解 Bug 2 SP IOG 副作用（v1.8.0 SP maxL -132K 災難）
**Status**：🟡 EXPERIMENTAL，待 user 跑 backtest verify

---

## 一、Headline

| 改動 | v1.8.0-PROD | **v1.8.2 EXPERIMENTAL** |
|------|------------|----------------------|
| SP/SL 機制 | `next bar at X Stop` | **1M K close 評估 + `next bar at Market`** |
| Fill timing | IOG=true intrabar worst tick | **next 1M K open（可控）**|
| 預期 BoJ case | -132K（worse case fill）| **-80~-100K（控制 fill）**|
| 1M_Exit 機制 | 保留 | 保留（不變）|

---

## 二、Root Cause Recap: 為什麼 Stop order 在 IOG=true 受傷

### v1.8.0 SP Stop order 行為
```pla
{ Section 11 S-4: Stop order 一旦 set 就 active }
buy to cover ( "SX_VS_SP" ) next bar at v_SP_Floor_Price Stop;
```

| 環境 | Stop fill 行為 |
|------|--------------|
| IOG=false | Next Data1=60M K open，受 60M K 範圍限制 |
| **IOG=true** | **任何 1M tick 都可 fire，fill at intrabar worst tick** 🚨 |

### 2024-08-05 BoJ case
- 進場：日盤後 16:00 夜盤
- 隔日開盤 gap up + 1M K 內極端反彈
- SP Stop 在 1M K intrabar fire，fill 在 1M K 最高點
- 結果 SP maxL -132,200（-661 點）

---

## 三、v1.8.2 設計：1M Market Exit 取代 Stop

### 新邏輯

```pla
{ 每根 1M K 收盤評估 SP/SL (取代 Stop order) }
if MarketPosition = -1 and ExitFired = 0 then begin

    { SP 機制 (1M-based) }
    if v_SP_Armed = True then begin
        { 評估 1M K close 是否穿過 SP Floor }
        if Close of Data3 >= v_SP_Floor_Price then begin
            buy to cover ( "SX_VS_SP" ) next bar at Market;
            ExitFired = 1;
        end;
    end
    else begin
        { SL 機制 (1M-based) - SP 未 arm fallback }
        if v_SL_Locked = True and Close of Data3 >= v_SL_Level then begin
            buy to cover ( "SX_VS_SL" ) next bar at Market;
            ExitFired = 1;
        end;
    end;
end;
```

### 關鍵差異

| Aspect | v1.8.0 Stop | **v1.8.2 1M Market** |
|--------|------------|---------------------|
| 觸發時點 | 1M tick intra-bar | **1M K close** |
| 觸發判定 | 價格 >= Stop price | **Close >= SL/SP Level** |
| Fill timing | Intra-bar at stop price | **Next 1M K open** |
| Worst case slippage | 大（intrabar gap）| **小（限於 1M K open）**|
| Latency | 0（即時）| **~1 min** |
| Predictability | 低（任何 tick 觸發）| **高（K close 確定）**|

---

## 四、Trade-off 分析

### Pros（v1.8.2 優於 v1.8.0 Stop）
1. **Fill 可控**：next 1M K open，不是 intra-bar worst tick
2. **避免 Bug 2 SP IOG 副作用**：BoJ 級 case 預期改善 25-40%
3. **滑價可預測**：限於 1M K 開盤滑價
4. **跟 1M_Exit 機制一致**：都是 Market order 設計

### Cons（v1.8.2 代價）
1. **~1 min latency**：1M K 收盤才 evaluate，可能多虧 1 分鐘
2. **可能 fill 在 reversal 後**：若 1 min 內 reversal，fill price worse
3. **失去 stop order 的 absolute floor 保護**：理論上 IOG=true stop 是 "instant"
4. **需重新 verify all exit scenarios**：W3 baseline 必跑

---

## 五、預期效果（基於 v1.8.0 數據推估）

### Case analysis: 2024-08-05 BoJ

| 版本 | Trigger | Fill | PnL |
|------|---------|------|-----|
| **v1.8.0** | SP intra-bar (any tick > floor) | Intra-bar worst tick | **-132,200** 🚨 |
| **v1.8.2 預估** | SP at 1M K close > floor | Next 1M K open | **-80,000 ~ -100,000** ✅ |

### 整體預估
| 指標 | v1.8.0 | **v1.8.2 預估** |
|------|--------|---------------|
| Net Profit | +846K | +900K-+950K |
| SP maxL | -132K | **-80~-100K** |
| 1M_Exit 機制 | 2 次（保留）| 2 次 |
| BoJ trade | -132K | -80K |
| 整體 MDD % | -19.4% | **~-16-17%** |

---

## 六、實作 spec

### .pla 改動範圍

| Section | 改動 |
|---------|------|
| Section 1 INPUTS | 不變 |
| Section 9 Frozen SL Setup + SetStopLoss | 不變（保留 engine guard 作 backup）|
| Section 9.5 1M Multi-layer Exit | 不變 |
| **Section 11 Exit chain S-4** | **大改：Stop → 1M Market** |
| 其他 | 不變 |

### Section 11 改動細節

```pla
{ === v1.8.0 ORIGINAL S-4 (REMOVED in v1.8.2) === }
{
if ExitFired = 0 then begin
    if v_SP_Armed = True then
        buy to cover ( "SX_VS_SP" ) next bar at v_SP_Floor_Price Stop
    else if v_SL_Locked = True then
        buy to cover ( "SX_VS_SL" ) next bar at v_SL_Level Stop;
end;
}

{ === v1.8.2 NEW S-4: 1M Market Exit === }
if ExitFired = 0 and MarketPosition = -1 then begin
    { SP armed: check if 1M K close crossed floor }
    if v_SP_Armed = True and Close of Data3 >= v_SP_Floor_Price then begin
        buy to cover ( "SX_VS_SP" ) next bar at Market;
        ExitFired = 1;
    end
    { SL fallback: check if 1M K close crossed SL level }
    else if v_SL_Locked = True and Close of Data3 >= v_SL_Level then begin
        buy to cover ( "SX_VS_SL" ) next bar at Market;
        ExitFired = 1;
    end;
end;

{ === SetStopLoss engine guard 保留作 backup (Section 9) === }
{ 仍提供 absolute floor 保護, 防止 1M evaluation 失效 }
```

---

## 七、Backtest Verify Plan

### Step 1: 寫 v1.8.2 EXPERIMENTAL .pla
- 加 1M Market exit 邏輯
- 保留 SetStopLoss 作 backup
- ML 10 個 inputs 鎖 GA-best

### Step 2: MC12 Backtest（**user 跑**）
- Chart: Data1=60M / Data2=Daily / Data3=1M / IOG=TRUE
- 期間: 2020-03 ~ 2026-06
- 對比 v1.8.0-PROD 同期間

### Step 3: 比對 5 個 metric
| Metric | v1.8.0 | v1.8.2 (目標) |
|--------|--------|--------------|
| Net | +846K | > +900K |
| **SP maxL** | -132K | **< -100K** ⭐ |
| MDD % | -19.4% | < -17% |
| BoJ trade | -132K | < -100K |
| 1M_Exit 仍 2 次 | 2 | 2 |

### Step 4: 5 件套 non-WFA 驗證
- Monte Carlo 10K
- Bootstrap 10K
- Stress Test
- Regime Analysis
- Robustness ±10%

→ 5/5 pass → promote v1.8.2 取代 v1.8.0

---

## 八、Honest Caveats

### Caveat 1: 1 min latency 風險
- 1M K 收盤後評估，若該 1M K 內反彈急 → 1 min 後 fill 可能 worse
- 但平均而言，1 min 內 reversal 不常見

### Caveat 2: Backup SetStopLoss 仍需保留
- 防 1M evaluation 出問題（e.g. Data3 feed 中斷）
- 保留 engine guard 作 absolute floor

### Caveat 3: 跟 1M_Exit 邏輯衝突 check
- 1M_Exit 在 11 factor scoring trigger
- SP/SL 在 1M K close 穿過 level trigger
- 兩個都用 Market exit
- Priority order: 1M_Exit > TP > Mid > Time > SP > SL (per Section 11)
- 確保 ExitFired flag 正確 propagate

### Caveat 4: BoJ-like extreme case 仍有 limitation
- 即使 1M K close 評估，BoJ 級 gap up 仍可能 fill 在 worse 1M open price
- 真正解法可能需要 + Gap Detection (Open >> Close[1])
- 但這是 future enhancement (v1.8.3+)

---

## 九、相關文件

- `S3_VolSqueezeShort_v180_EXPERIMENTAL.pla` v1.8.0-PROD（base）
- `live_simulation/S3_S_VolSqueezeShort.pla` v1.8.0-PROD（current production）
- `v181_BarStatusFix_FAILED_20260629.md`（v1.8.1 BarStatus gate 失敗）
- `v181_GA_FAILED_architecture_verdict_20260629.md`（v1.8.1-GA 失敗）
- 本檔 v1.8.2 spec（**新方向**：1M Market 取代 Stop）

---

## 十、Status

- v1.8.0-PROD：✅ production（live_simulation, 不動）
- v1.7.3-FINAL：🟡 archive（可 rollback fallback）
- **v1.8.2 EXPERIMENTAL**：🟡 **spec ready, .pla 待寫, backtest 待跑**

---

## 十一、Next Steps（**待 user confirm**）

1. ✅ 寫 spec（本檔）
2. ⏳ 寫 v1.8.2 .pla（含 1M Market exit）
3. ⏳ ASCII verify + commit
4. ⏳ User 跑 MC12 backtest
5. ⏳ 5 件套 non-WFA 驗證
6. ⏳ Promote decision (取代 v1.8.0 or 並行 portfolio)
