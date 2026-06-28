# S4_S MACDDivergenceShort — Strategy Definition (W1 spec)

**啟動日**：2026-06-28
**版本**：W1 spec v1.0（待 W2 .pla 實作）
**狀態**：🔵 CURRENT — W0 marginal PASS (3/4)，進入 Stage-1 4 段討論 lock
**對應 archive**：`strategies/research/archive/batch01_S2-S5/S4_MACDDivergence.pla`
**R-6 配對**：S4_L MACDDivergenceLong（推延至 S16 後開發）

---

## 一、策略本質（一句話 tagline）

> **「強多頭末端動能衰竭捕手 — 抓 MACD 頂背離 + RSI 過熱的反轉空頭。」**

---

## 二、Stage-1 4 段討論（user-confirmed lock）

### A. 內容

| 維度 | spec |
|------|------|
| **類別** | D 類動量逆勢 |
| **主週期** | **60M**（沿用 archive S4 設計）|
| **方向** | 純空（R-6 拆解，配 S4_L 待後續）|
| **指標** | MACD(12, 26, 9) + RSI(14) |
| **進場觸發** | 三條件 AND： |
| | 1. **價格新高**（過去 20 K 棒 highest）|
| | 2. **MACD histogram 未同步新高**（頂背離）|
| | 3. **RSI ≥ 70**（過熱確認）|
| **出場** | 4 層 priority： |
| | 1. **TP at ATR × 3.0**（中期目標）|
| | 2. **SL at ATR × 2.0**（緊停損）|
| | 3. **TimeStop 40 K 棒**（~1.7 天）|
| | 4. **Mid exit**：MACD histogram 回正（背離失效）|
| **頻率預期** | 5-7 signals/yr（W0 實證 5.2/yr）|

### B. 優點

1. **逆勢 alpha source 結構性不同於既有 4 隻做空**
   - L2 順勢空（週線過濾 + Donchian）
   - L4 假突破空（Wyckoff Spring Trap）
   - S3 拉回空（過熱 + RSI > 65 不同邏輯）
   - S3_S 波動率突破空（BBW squeeze + breakdown）
   - **S4_S 動量衰竭空（首隻 momentum exhaustion 邏輯）**

2. **W0 2024 +21.44% alpha 強證據**
   - 趨勢轉折期（多頭末端）alpha 真實存在
   - 2023 +6.3% / 2022 +1.4% 跨年也有微利
   - 雖 2020 -15.56%（疫情超多頭失效），但結構性 acceptable

3. **60M 時框跟 S3_S 一致**（chart setup 簡單）

4. **可解釋性高**：背離 + 過熱 = 直覺驗證

### C. 缺點

1. **逆勢策略 inherent risk**
   - 趨勢延伸時連續 SL（如 2020 -15.56%）
   - 背離可能持續多次失敗（多頭年）

2. **W0 marginal**：G3 RR ratio 1.33 < 1.5 gate（marginal fail）
   - 60M MC12 baseline 必須 verify 真實 RR

3. **頻率低**（5-7 筆/年）
   - sample 不足 statistical power
   - W4 WFA 每窗 OOS 可能 1-2 trades = noise

4. **W0 結果 2020 + 2026 H1 大虧** = inherent regime weakness
   - 超強多頭中背離訊號全錯（2020 -15.56%）
   - Trump 期 noise（2026 H1 -6.19%）

### D. 為什麼合適

1. **補強做空 sleeve 厚度**（用戶 2026-06-28 ruling 主旨）
2. **首隻 D 類動量逆勢 sleeve**（補上 portfolio 缺類別）
3. **跟 L1/L5 強勢多頭結構性對沖**（多頭末端 = L1 SP 啟動時，S4_S 進場）
4. **2024 +21% alpha 證明趨勢轉折期有效**（值得 W3 真實 verify）

---

## 三、進場規則（W2 .pla 寫作 spec）

8 個 gates 全 True → 次根市價放空：

1. **目前空手**（MarketPosition = 0）
2. **價格新高**：High > Highest(High, 20)[1]（過去 20 K 棒最高）
3. **MACD 頂背離**：histogram[0] < prior_swing_high_histogram
4. **RSI 過熱**：RSI(14) ≥ 70
5. **非同日冷卻期**（前次平倉滿 1 日）
6. **非假日尾段**（63 筆登錄表，Time < 500）
7. **非結算日**（每月第 3 週三 15-21）
8. **註冊有效期內**（Date ≤ 1270101）

---

## 四、出場規則（6 層 priority）

| Priority | 條件 | 動作 | Label |
|---|---|---|---|
| 1 | Manual Kill = True | 市價平倉 | SX_MD_Kill |
| 2 | 註冊期失效 | 市價平倉 | SX_MD_RegistryEnd |
| 3 | 假日尾段 + Time 415-455 | 市價平倉 | SX_MD_HolFlat |
| 4 | 結算日 + Time ≥ 1230 | 市價平倉 | SX_MD_Settlement |
| 5 | **TP**：到「進場價 − 3.0×ATR」| Limit 鎖利 | SX_MD_TP |
| 6 | **MidExit**：MACD histogram > 0（背離失效）| 市價認錯 | SX_MD_Mid |
| 7 | **TimeStop**：持倉 ≥ 40 K 棒 | 市價平倉 | SX_MD_TimeStop |
| 8 | **SL**：止損「進場價 + 2.0×ATR」| Stop 兜底 | SX_MD_SL |

---

## 五、賺什麼錢

**賺「趨勢末端動能衰竭反轉」的反向空頭錢**：
- 強多頭跑了一陣子後，價格仍創新高，但內部動能（MACD histogram）已不跟
- 加上 RSI ≥ 70 過熱
- 預期短中期反轉下殺
- 目標 3 ATR 下方 limit，最多持倉 40 K 棒（1.7 天）

---

## 六、適合行情

| Regime | 進場？| 預期效果 |
|--------|------|---------|
| **強勢多頭末端**（cluster top）| ✅ | 主 alpha 來源 |
| **過熱回檔**（RSI 70+ 後）| ✅ | 中等 |
| **空頭中的反彈頂**（rare）| ✅ | 順勢加碼 |
| 趨勢中段 | ❌ | 連續 SL 風險 |
| 盤整 | ❌ | 無動能可衰竭 |
| 超強多頭延續（如 2020 後疫情）| ❌ | W0 證實大虧 |

---

## 七、Portfolio sleeve 角色

- **D 類動量逆勢 sleeve**（首隻）
- 補上 portfolio 中缺的「逆勢空頭」邏輯
- 跟 S3_S（順勢突破空）、L4（假突破空）、L2（順勢空）、S3（拉回空）形成 **5 種不同 alpha source**

### 預期 portfolio cap
- **W6 promote 後 3-5%**（待 W5 institutional eval 結果）
- 配 S4_L（待後續開發）形成 R-6 hedge pair

---

## 八、合規模組（Rule #11/#12/#14/#15）

- Settlement_Flat（Priority 0）
- SetStopLoss guard（MP ≥ 0 short variant per Rule #12）
- HolidayFlat_v3（63 筆 TAIFEX 登錄表）
- Manual_Kill_Switch
- Registry_Valid_Until 1270101
- IntrabarOrderGeneration = false
- ASCII 100%（`verify_pla_ascii.py --strict`）

---

## 九、W0 → W6 進度

| 階段 | 狀態 | 結果 |
|------|------|------|
| **W0** Alpha pre-verify | ✅ 完成 | **MARGINAL 3/4**（G3 RR 1.33 marginal fail）|
| **W1** Strategy doc | ✅ 本檔 | 4 段討論 lock |
| W2 .pla 實作 | ⏳ next | 7 模組合規 |
| W3 MC12 baseline | ⏳ | 60M alpha real verify |
| W4 WFA | ⏳ | 9 windows |
| W5 10-dim eval | ⏳ | institutional |
| W6 promote OR KILL | ⏳ | user ruling |

---

## 十、Kill triggers（若 W3 後續 fail）

| 條件 | 動作 |
|------|------|
| W3 PF < 1.1 | KILL with FINAL_VERDICT |
| W3 Sample < 30 trades | sample 不足，60M 不適合 |
| W4 < 3/9 windows pass | WFA fail KILL |
| W5 fail > 3 dimensions | institutional KILL |

---

## 十一、相關文件

- W0 result: `W0_alpha_preverify_result_20260628.md`
- W0 script: `_w0_alpha_preverify.py`
- Stage-1 spec: `S4_S_stage1_spec.md`
- Archive ref: `strategies/research/archive/batch01_S2-S5/S4_MACDDivergence.pla`
- ROADMAP: `docs/policies/OFFICIAL_ROADMAP.md` Batch 01 S4_S (CURRENT)
- L24 lesson: 禁止加 regime filter 救績效
