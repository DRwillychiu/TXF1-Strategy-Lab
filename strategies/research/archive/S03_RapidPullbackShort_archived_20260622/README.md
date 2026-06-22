# S3 PullbackShort — Bull-Regime Counter-Trend Short

**建立日**：2026-06-20
**狀態**：📋 **設計討論階段**（pre-code）
**Q1 優先序**：**#1**（5 個 deep-discovery agents 一致推薦）
**Portfolio gap 填補**：用戶 2026-06-19 親自發現的「**多頭中段拉回對沖**」缺口

---

## 一、策略一句話

**強多頭結構中，當技術過熱訊號出現 → 短線做空 1-3 天的回檔**

= Counter-Trend Mean Reversion Short  
= Short the Rip / Fade the Rally

---

## 二、Portfolio 角色（**為什麼必須做**）

```
現有 6 策略覆蓋市況：
─────────────────────────────────────────────────────────
強多頭 → 多頭中段拉回 → 區間震盪 → 區間破壞 → 空頭趨勢
   ✓       ❌ GAP ❌      ✓         L4         L2
                  ↓
              S3 補在這
```

**為何不能讓 L4 / L2 補這缺口**：
- L4 等盤整破壞，5% 回檔不算破壞
- L2 等空頭趨勢確認，回檔不是空頭

→ **S3 是 portfolio 結構性必要補件**。

---

## 三、檔案清單

```
S03_PullbackShort/
├── README.md                          ← 本檔（入口）
├── S3_PullbackShort_design_spec.md    ← 完整設計規格（Agent D 深度設計）
└── (未來會加)
    ├── S3_PullbackShort_strategy.md   ← 策略完整說明（仿 S2 格式）
    ├── S3_PullbackShort_annotated.md  ← 中文逐段註解
    ├── S3_PullbackShort.pla           ← MC12 程式碼（待設計討論完成）
    ├── S3_known_issues.md             ← issue tracker
    └── backtests/                      ← MC 回測 xlsx
```

---

## 四、開發路線（**先深度討論，後實作**）

依用戶 2026-06-20 指示「先做深層規劃與深度討論」：

### Phase 0：深度設計討論（**現在**）
- 讀 design spec
- 用戶逐項決策（見 design_spec.md 「Critical Design Decisions」）
- 確認 alpha 來源 / 訊號組合 / 出場機制
- **不直接寫 .pla**

### Phase 1：寫策略文件（用戶確認設計後）
- strategy.md（給機構級審視）
- annotated.md（中文逐段註解）
- 仿 S2 完整文件結構

### Phase 2：寫 .pla（design + docs 完整後）
- 用 L2 + L5 為 template
- ~340 LOC 預估
- 嚴格遵守 rule #11 / #12 / #13

### Phase 3：驗證 + MC 回測
- 寫 verify_s3_pullbackshort.py（~67 項）
- MC12 多配置 A/B test
- 機構級 10 維度評估

### Phase 4：晉升 live_simulation
- 通過所有 mandatory checkpoints
- 加入 portfolio allocation v3

---

## 五、深度設計決策入口

完整 design spec 詳見 [S3_PullbackShort_design_spec.md](S3_PullbackShort_design_spec.md)。

**需要用戶決策的 7 個關鍵點**（避免重蹈 S2 設計超前實證之失敗）：

1. **訊號組合**：RSI / BB / MA deviation / Volume divergence 選哪 2-3 個
2. **進場時機**：突破當下 vs 收盤確認 vs 下一根 K 開盤
3. **出場機制**：Fixed TP vs Trail vs MA touch
4. **持倉時間**：純日內 vs 1-2 天 swing
5. **倉位管理**：固定 1 口 vs 分批
6. **regime filter 嚴格度**：寬（更多訊號 vs 嚴（更少但更精）
7. **S3 vs S2 重定位**：✅ 已確認從零做 S3（roadmap 已 reject 重定位）

---

## 六、相關文件

- **完整設計 spec**：[S3_PullbackShort_design_spec.md](S3_PullbackShort_design_spec.md)
- **12 月 roadmap**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **Portfolio v2**：[../../../docs/portfolio_allocation_v2_20260620.md](../../../docs/portfolio_allocation_v2_20260620.md)
- **S2 暫緩說明**：[../S02_InsideBarBreak/STATUS_SUSPENDED.md](../S02_InsideBarBreak/STATUS_SUSPENDED.md)
- **機構級風險框架**：[../../../docs/institutional_risk_framework_20260619.md](../../../docs/institutional_risk_framework_20260619.md)

---

## 七、開發紀律（從 S2 13 個教訓學到的）

```
S3 開發必須遵守：
1. ✅ 先深度討論，後寫 .pla（不再設計超前實證）
2. ✅ 任何 filter 必須做重疊度 + 通過率雙重檢查
3. ✅ Time 條件必須閉區間
4. ✅ Long/Short 從一開始就決定 Long-only 或雙向
5. ✅ TP 倍率必從 MFE 統計推導
6. ✅ 同日多進場必有 cooldown
7. ✅ 與 Buy and Hold 對比作為現實檢驗
8. ✅ MC 真實回測前不可宣稱 alpha 真實
```

---

**Phase 0 深度討論啟動中**。等用戶逐項決策完成才進 Phase 1。
