# S2 InsideBarBreak — Reactivation Track

> S2 是從 `archive/batch01_S2-S5/` 重啟開發的策略。
> 它不屬於每週新批次（W24/W25/...），而是獨立的「**舊策略升級**」軌道。

---

## 為什麼 reactivate S2

batch01 五隻研究策略中，S2 是**唯一表現可期**的：

| 策略 | PF | 淨利 | 結論 |
|------|-----|-----|------|
| **S2 InsideBarBreak** | **4.61** | **+791,754** | ⭐ 可期 |
| S3 VolSqueeze | 0.88 | -115,622 | ❌ 失敗 |
| S4 MACDDivergence | n/a | +38,000 (僅 2 筆) | ❌ 樣本不足 |
| S5 SettlementWeek | 0.60 | -367,000 | ❌ 失敗 |

雖然 batch01 是 Python ^TWII 日線代理回測（精度有限），但 PF 4.61 + WR 64.7% 的訊號值得用 MC 30M 真實資料驗證。

---

## 當前狀態

| 項目 | 狀態 |
|------|------|
| Phase 1 模組化 | ✅ 完成（2026-06-17 v0.2）|
| Phase 2 MC 真實回測 | ⏳ 待用戶在 MC12 上跑 |
| Phase 3 P1-P3 驗證 | ⏳ |
| Phase 4 晉升 live_simulation | ⏳ |

---

## 檔案結構

```
S02_InsideBarBreak/
├── README.md                          ← 本檔
├── S2_InsideBarBreak.pla              ← MC PowerLanguage 完整代碼（v0.2）
└── S2_InsideBarBreak_annotated.md     ← 中文逐段註解 + Phase 路線圖
```

---

## 下一步行動

### 給用戶

1. **MC12 載入 `S2_InsideBarBreak.pla`**
2. **設定圖表**：Data1 = TXF1 30M / Data2 = TXF1 Daily
3. **跑回測** 2020/01/01 ~ 今天
4. **匯出 xlsx 績效報告**到 Downloads
5. **回報數據**，我會跑分類驗證 + 寫 Phase 2 報告

### 給 Claude（接續開發）

1. 接到 MC 30M 真實 xlsx 後跑：
   - `analyze_settlement_backtest.py`（看 IB_Settlement 觸發狀況）
   - `verify_strategy_holding_classification.py`（確認 Swing-Trend）
2. 對比 v0.1 Python 日線 vs v0.2 MC 30M 績效差距
3. 評估是否符合 P1-P3 標準
4. 規劃 Phase 3 優化方向

---

## 相關文件

- [策略 annotated](S2_InsideBarBreak_annotated.md)
- [原 v0.1 archive 版本](../archive/batch01_S2-S5/S2_InsideBarBreak.pla)
- [batch01 績效總覽](../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md)
- [Constitution v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
