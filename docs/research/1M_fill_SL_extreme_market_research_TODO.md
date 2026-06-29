# 「1M 還沒形成幾根就 fill SL」深度研究 TODO

**日期**：2026-06-29
**Trigger**：v1.8.0 backtest 揭露 2026-06-08 case（gap 開盤 fill -1,560 點）
**用戶 ruling**：「絕對會出現偶發生的一瞬間 1M 還沒形成幾根就 fill SL，因此會需要思考以及深度研究如何優化」
**Status**：⏳ **待 v1.8.0 R1 GA 後深度討論**

---

## 一、Problem Statement

### Concrete case
- 2026-06-08 開盤
- v1.7.3-FINAL (ATR-based): 估 -530 點
- v1.7.4 cap 100: **-466 點**（cap 失效）
- v1.8.0 1M multilayer: **-1,560 點**（無 cap, 1M 沒形成）

### Core issue
極端行情（gap up 開盤、Flash crash、macro event 瞬間）：
- 開盤 / 異常 K 棒**直接 fill 越過 SL Level**
- 1M monitor 還沒形成 5 根（評分系統需要 5+ bars）
- 評分系統來不及計算 → 0 trigger
- 任何 stop order fill 在 open price（worst case）

### Root cause classification
| 類型 | 描述 |
|------|------|
| **Market structure** | 跳空 gap 是市場本質，無法 algo 完全防護 |
| **Stop order behavior** | Stop 在 gap 中 fill at open（市價單行為）|
| **Monitor latency** | 1M K 棒收盤才形成，極端開盤瞬間無數據 |
| **MC12 IOG fill** | IOG=true 環境 next bar fill 不確定性大 |

---

## 二、候選研究方向

### 方向 1: Gap Detection（**開盤即時檢測**）

```pla
{ 開盤後第一根 60M K 內檢查 }
if Time = 0845 then begin   { 日盤開盤 }
    v_Gap_Pts = AbsValue( Open - Close[1] );
    if v_Gap_Pts > GapAlertThreshold then begin
        { Gap 警示 → 主動 market exit (反向, 不等 stop) }
        if MarketPosition = -1 and Open > EntryPrice then
            buy to cover ( "SX_VS_GapExit" ) next bar at Market;
    end;
end;
```

| Pro | Con |
|-----|-----|
| 不依賴 1M | 需 hardcode 時段（8:45 / 15:00 夜盤）|
| 直接 catch gap | 仍 fill 在 Open 價（救不了實際虧損）|
| 簡單實作 | 增加 input + 邏輯複雜度 |

### 方向 2: Pre-bar Order（**盤前 cancel stop**）

```
邏輯:
1. 日盤收盤前（13:30）cancel pending SL stop
2. 夜盤開盤後（15:05+）重掛 SL
3. 避開 13:45-15:00 收盤跳空風險
```

| Pro | Con |
|-----|-----|
| 避開收盤 gap risk | 失去 60 分鐘保護期 |
| 開盤跳空時可主動處理 | 增加 operational complexity |
| - | MC12 stop order 取消重掛邏輯複雜 |

### 方向 3: Tick-level monitor（**Data4 = tick**）

| Pro | Con |
|-----|-----|
| 真正即時反應 | MC12 setup 極複雜 |
| 微秒級 | tick data storage huge |
| - | Backtest 速度極慢 |
| - | 過度工程 |

### 方向 4: Position sizing reduce（**動態減倉**）

```
邏輯:
1. 偵測高 vol 環境（ATR 短期 / 長期 ratio > X）
2. 部位減半 or 跳過進場
3. 避免 vol expansion 期間部位過大
```

| Pro | Con |
|-----|-----|
| 從源頭控 risk | 預測性策略 → 過去 alpha 大魚被截 |
| 業界常見 | 違反 L24（regime filter）|
| - | TXF1 固定 1 口無法減倉 |

### 方向 5: Time-of-day filter（**避開 vol 高時段**）

```
邏輯:
1. 禁止開盤前 30 分鐘進場
2. 禁止 macro release 前進場
```

| Pro | Con |
|-----|-----|
| 直接避免 | 削掉 alpha（v1.7.3 早盤有真實 trades）|
| 簡單 | 違反 L24 event filter |

### 方向 6: VIX-equivalent regime detector

```
邏輯:
1. 偵測隱含波動率高 (TVIX > X)
2. 高 vol 期暫停策略
```

| Pro | Con |
|-----|-----|
| 業界 standard | TVIX 不一定即時 |
| 預測性強 | 違反 L24 |

---

## 三、業界 best practice 觀察

從昨日廣泛 SL research catalog（`docs/research/stop_loss_mechanisms_catalog_20260628.md`）：

- **Circuit Breaker**: 市場層級，非策略可控（TXF1 ±10% 熔斷已存在）
- **Capitulation Volume Spike**: 量價背離 → exit
- **Multi-TF Confirmation**: 上層 trigger + 下層 monitor（v1.8.0 嘗試方向）
- **Disaster Stop**: 兩層保護（trail + 固定遠 stop）

### Honest 結論
**沒有完美的 algo 防護 gap risk**：
- Gap = market structure
- Stop order 在 gap 中 fill at open 是物理事實
- 任何 algo 機制都有 latency

→ **真正解決方案是 portfolio sizing**：
- 單筆 max loss = 帳戶 × X%
- × 帳戶 cap 比例 = portfolio 級 manageable
- v1.7.3-FINAL 已 3% cap = 單筆 -10.6% × 3% = -0.32% portfolio = 可承受

---

## 四、研究 Plan（待 v1.8.0 R1 GA 後決定 priority）

### Step 1: 量化 gap events 統計（**先做這個**）
- 用 TWII 60M / 1M data 統計 2020-2026
- 開盤 gap > 200 點次數
- gap > 500 點次數
- gap > 1000 點次數
- 對 S3_S 影響評估

### Step 2: 模擬各 path 效果
- Path A: Gap detection (TWII gap > 200 → exit)
- Path B: 開盤 30 min 禁止
- Path C: Position sizing reduce
- 跑 backtest 看 v1.7.3 + 各 path 效果

### Step 3: Lesson L33 候選撰寫
「Gap risk 是 market structure 限制，algo 防護有極限，必須 portfolio level 解」

---

## 五、Status

- ⏳ **暫緩**：等 v1.8.0 R1 GA 結果後再 prioritize
- 若 R1 GA pass → 此 research 仍要做（補完 v1.8.0 缺陷）
- 若 R1 GA fail → 此 research 可能不必（接受 v1.7.3 + portfolio cap）

---

## 六、相關文件

- `docs/research/stop_loss_mechanisms_catalog_20260628.md`（業界 12 種機制）
- `strategies/research/S03_VolSqueezeShort/v174_v180_desktop_threeway_analysis_20260629.md`（3-way 對比）
- `strategies/research/S03_VolSqueezeShort/v180_Phase2_GA_R1_spec_20260629.md`（GA R1）
- `docs/methodology/extreme_sl_multilayer_sop_20260629.md`（多層 SL SOP）
