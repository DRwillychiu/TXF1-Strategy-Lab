# S16_S v0.6-ADAPTIVE — Test SOP (2026-07-10)

**版本**：v0.6-ADAPTIVE
**改動核心**：MinSlope 從純點數 → ATR 自適應
**Backward compat**：`UseAdaptiveSlope = False` → 完全 v0.5 行為

---

## 一、Code 改動摘要

### 新增 2 個 inputs

```pla
UseAdaptiveSlope        ( True  ),   { True = ATR adaptive, False = legacy pure pts }
MinSlope_ATRMult        ( 0.7   ),   { When adaptive, slope must > ATR * this mult }
```

### 保留 1 個 legacy input（backward compat）

```pla
MinSlope                ( 28    ),   { Only used if UseAdaptiveSlope = False }
```

### 新增 1 個 variable

```pla
v_SlopeGate             ( 0     ),   { Dynamic slope threshold at each bar }
```

### Section 9 邏輯改動

```pla
{ v0.6: Compute adaptive slope gate }
if UseAdaptiveSlope = True then
    v_SlopeGate = v_ATR * MinSlope_ATRMult      { Adaptive }
else
    v_SlopeGate = MinSlope;                      { Legacy }

if MarketPosition = 0 and
   v_Death_Cross         = True and
   v_Slope               > v_SlopeGate and       { <-- changed from MinSlope }
   ... other gates ...
then Entry;
```

---

## 二、初始值 0.7 的推導

### v0.5 backtest 期間平均 ATR 估算

從已知資料反推：
- Max Single Loss = -42,600 (÷ 200 NTD/pt = 213 pts)
- StopATRMult = 4.0
- 若 SL 觸發：4 × ATR ≈ 213 pts → **ATR ≈ 53**
- 但實際 SL 通常不是完美 fill，保守估算 **ATR 平均 30-50 pts**

### v0.5 MinSlope=28 → v0.6 ATRMult 等價換算

| 假設 ATR 平均 | MinSlope=28 / ATR = ATRMult 等價 |
|-------------|---------------------------|
| 30 pts | 0.93 |
| **40 pts (中位估)** | **0.70** ⭐ 建議起始 |
| 50 pts | 0.56 |

**選 0.7 為起始值**：中庸值，接近 v0.5 行為

---

## 三、Test A/B 對比計畫

### 測試 1 — **v0.6 default (UseAdaptiveSlope=True, ATRMult=0.7)**

用 default 值直接跑 backtest 2020-2026。

**MC12 設定**：
```
UseAdaptiveSlope        = True
MinSlope_ATRMult        = 0.7
ZLEMA_Fast              = 25
ZLEMA_Slow              = 70
其他所有 inputs 保持 v0.5-FINAL 值
```

**預期**：
- Trade 數 similar to v0.5（~100-120 range）
- Net / PF / MDD similar 或略有不同
- **若 profitable → v0.6 概念驗證成功**

### 測試 2 — **v0.5 legacy 對照組（UseAdaptiveSlope=False）**

```
UseAdaptiveSlope        = False
MinSlope                = 28  (legacy 值)
其他保持 v0.5-FINAL
```

**預期**：**應該與 v0.5-FINAL 完全一樣**（Net +1,028K / PF 1.885 / MDD -271K）
若不同 → code 有 bug，需 debug

---

## 四、若測試 1 通過，接續 GA sweep

### Sweep MinSlope_ATRMult

```
UseAdaptiveSlope        = True (lock)
MinSlope_ATRMult        Sweep [0.3, 0.5, 0.7, 0.9, 1.2, 1.5, 2.0]  (7 values)

其他 inputs 保持 v0.5-FINAL:
  ZLEMA_Fast              = 25
  ZLEMA_Slow              = 70
  QuickStop_MaxLoss_Pts   = 60
  MaxHoldingBars          = 24
  StopATRMult             = 4.0
```

**Total**：7 combos Exhaustive
**時間**：~30-40 分鐘
**目的**：找 ATR multiplier 的 sweet spot

---

## 五、預期 3 種可能結果

### 情境 A — **v0.6 default (ATRMult=0.7) 直接 profitable**
- 若績效 ≈ v0.5 → 概念驗證成功，繼續 GA sweep 精修
- 若績效 > v0.5 → **意外驚喜**（adaptive 有 alpha 加成）
- 若績效 < v0.5 但仍正 → 可接受，看 sweep 能否救

### 情境 B — **v0.6 default 虧錢或大幅衰退**
- 檢查 v0.5 legacy (`UseAdaptiveSlope=False`) 是否還原
- 若還原 = code 對，但 0.7 這個值不對
- 用 GA sweep 找對的 ATRMult

### 情境 C — **v0.6 default 完全無 trade**
- ATR 太小或 ATRMult 太高
- 用 sweep [0.3, 0.5, 0.7] 較低值再試

---

## 六、A/B backtest 執行流程

### Step 1 — 部署 v0.6 pla
- Reload S16_S_MACrossShort.pla 到 MC12
- 確認新 inputs 出現（UseAdaptiveSlope + MinSlope_ATRMult）

### Step 2 — 跑 v0.6 default backtest
- 全部 inputs 用 v0.6 default
- 期間 2020-2026
- 匯出 xlsx

### Step 3 — 跑 v0.5 legacy 對照
- 只改：UseAdaptiveSlope = False
- 期間 2020-2026
- 匯出 xlsx
- **應與 v0.5-FINAL 完全相同**

### Step 4 — 貼給 Claude 分析
- 兩份 xlsx 路徑
- Headline metrics 對比
- Claude 產出 v0.6 vs v0.5 對比 md

### Step 5 — 若 v0.6 概念 OK，跑 GA sweep
- Sweep MinSlope_ATRMult
- 找 sweet spot

### Step 6 — v0.6 若表現優於 v0.5 → 進 W5 re-run
- 用新 config 跑 Rule #18 Sniper-adapted 5 件套
- 若 8/8 PASS → **v0.6-FINAL LOCK**

---

## 七、關鍵決策節點

| 若... | 則... |
|------|-----|
| v0.6 default profitable + PF > 1.5 | ✅ 進 sweep → 進 W5 → v0.6-FINAL |
| v0.6 default marginal (Net +0-500K) | ⚠️ sweep 找 sweet spot |
| v0.6 default 虧錢或 0 trade | ❌ ATRMult 起始值錯，需重估算 ATR |
| v0.5 legacy 對照組不還原 | 🚨 code bug，需 debug |
| GA sweep 找不到 profitable | ⚠️ ATR adaptive 概念不適用，回 v0.5 |

---

## 八、與 v0.5-FINAL 對照

| 面向 | v0.5-FINAL | v0.6-ADAPTIVE |
|------|-----------|--------------|
| MinSlope 語意 | 純點數 (28 pts) | ATR × 倍數 (0.7 × ATR) |
| Vol regime 適應 | ❌ 不適應 | ✅ 自動適應 |
| Index level 適應 | ❌ TXF1 若漲一倍就失效 | ✅ 隨 ATR 自動調整 |
| Rule #16 五支柱 | LOCKED | 待重新 W3-W5 |
| GA 結果 | 8/8 Sniper PASS | 待重跑 |
| 向後兼容 | - | ✅ 可退回 v0.5 (UseAdaptiveSlope=False) |

---

**Ready for user MC12 test.**
