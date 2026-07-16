# S16_S Holiday Patch — Post-Promote Compliance Fix

**Date**: 2026-07-16
**Trigger**: 例行 self-audit 發現 v1.0-PROD `v_Holiday_Block = False;` W2 draft placeholder 未替換
**Severity**: 🔴 HIGH（合規紅線，但無實際虧損記錄）
**Resolution**: v1.0-PROD → v1.0.1-HOLIDAY (live_sim) / v1.1-PCT → v1.2-HOLIDAY (research)
**Related**: Issue F1 in [S16_S_OPEN_ISSUES_20260713.md](S16_S_OPEN_ISSUES_20260713.md)
**Enforcement Doc**: [docs/policies/PROMOTE_CHECKLIST.md](../../../docs/policies/PROMOTE_CHECKLIST.md)

---

## 一、Gap 描述

### 原程式碼（v1.0-PROD line 261-262）
```pla
{ Holiday block: placeholder, expand with HolidayFlat_v3 registry }
v_Holiday_Block = False;
```

### 影響
- 進場 gate line 358 有 `v_Holiday_Block = false` 檢查
- 但 `v_Holiday_Block` **永遠是 False**，等於**沒有假日封鎖**
- 假日夜盤若出現死叉 + Slope > 28，會照常進場
- 出場 gate 也永遠不觸發 SX_MA_Holiday

### 為什麼通過 PROMOTE
- W2 draft 明說「placeholder」但 W3/W4/W5 review 未 flag
- `verify_pla_ascii.py` 只驗 ASCII，不做語意 lint
- Rule #11 只要求「模組存在」，未要求「模組有效」

---

## 二、Patch 內容

### research 版 v1.1-PCT → v1.2-HOLIDAY
- HolidayFlat_v3 63-entry registry（同 L1-L5 / S1 / S3_S）
- Date arithmetic 改 EL-standard (Year-1900)
- Registry_Valid_Until: 1280101 (民國) → 1270101 (EL-std = 2027-01-01)
- UsePercentSlope toggle **保留**（O-1 REJECTED 但 code 保留 audit）
- 新增 `hidx` variable + `arrays: Holiday_Tail[80](0);` 宣告

### live_simulation 版 v1.0-PROD → v1.0.1-HOLIDAY
- 同上 registry patch
- 不含 UsePercentSlope（保持 production 版簡潔）
- Alpha 邏輯完全不變（Config LOCKED: F25/S70/Slope28/QS60/MH24/StopATRx4）

---

## 三、Patch 前後對照

### Section 3 - Priority 0 Compliance Checks

| 項目 | v1.0-PROD (before) | v1.0.1-HOLIDAY / v1.2-HOLIDAY (after) |
|-----|-------------------|-----|
| Holiday_Tail array 宣告 | ❌ 無 | ✅ `arrays: Holiday_Tail[80](0);` |
| Registry init (63 dates) | ❌ 無 | ✅ 於 `CurrentBar = 1` 一次性 init |
| Holiday detection loop | ❌ 無 | ✅ `for hidx = 1 to 80` 逐一比對 |
| Registry expiry logic | Year-1911 (民國) 混用 | Year-1900 (EL-std) 一致 |
| Registry expired → force block | ❌ 無 | ✅ 過期立即封鎖進場 |
| v_Holiday_Block value | 恆等 False | Time <= 500 時 = Date match ? True : False |

---

## 四、驗證

### ASCII 驗證
```
python scripts/verify_pla_ascii.py --strict
Result: 27/27 PASS
```

### Rule #11 完整性
- ✅ 進場 gate `v_Settlement_Day = false and v_Holiday_Block = false` 已存在
- ✅ 出場 Priority 0 有 SX_MA_Holiday / SX_MA_Settlement / SX_MA_Kill / SX_MA_Registry
- ✅ Registry 63 個假日與 L1-L5 / S1 / S3_S 一致
- ✅ Registry_Valid_Until 對齊主線 (2027-01-01)

### 預期回測衝擊
- 假日極少（63 個 / 8 年 ≈ 每年 8 天）
- 5M 級別在假日封鎖前若已進場，會在 Time = 04:15 強制平倉
- **預期對績效影響 < 1%**（原本假日進場的極少數 case 消失）
- 需要 MC12 重跑確認實際數字（用戶 backtest 執行）

---

## 五、Lessons Learned (加入 PROMOTE_CHECKLIST L-P1~L-P5)

1. **L-P1**: W2 draft 內 `placeholder` / `TODO` 必須 PROMOTE 前 grep 掃過
2. **L-P2**: Rule #11 存在 ≠ Rule #11 有效
3. **L-P3**: ASCII verification 不足以做 promotion gate
4. **L-P4**: 每個 hardcoded `v_X = False;` 必須有 justification comment
5. **L-P5**: PROMOTE 是「合規契約」，不只是「績效通過」

---

## 六、Follow-up Actions

- [x] research 版 v1.2-HOLIDAY patched (2026-07-16)
- [x] live_simulation 版 v1.0.1-HOLIDAY patched (2026-07-16)
- [x] ASCII verify PASS
- [x] Risk Register F1 標記 CLOSED
- [x] PROMOTE_CHECKLIST.md 建立
- [ ] MC12 重跑回測確認績效衝擊 < 1%（用戶執行）
- [ ] 2026-12 前 refresh Registry 2027-2028 假日（F2 議題）
- [ ] （可選）建 `scripts/verify_promote_readiness.py` 自動化 Check 1-6

---

**End of S16_S Holiday Patch Documentation — 2026-07-16**
