# P29 指標顯示設計 — 從 MC12 PowerLanguage 撰寫角度

**日期** 2026-08-26　**指標** `IND_S16S_P29.pla`（Build_ID 260826）
**起因** 用戶：「指標完整呈現了，可是我沒有辦法做到肉眼辨識。」

---

## 0. 先診斷：問題不只是「畫得不夠」，是「找不到」

```
202 個型態 ／ 421,513 根 = 平均每 2,086 根才出現一個
5 分 K 一天約 228 根  ->  平均 9.2 個交易日才有一個
```

**在圖上捲動本來就幾乎不可能撞到。**
現行指標只畫兩條趨勢線，沒有任何「這裡有型態」的標記，
所以即使畫對了，也要先知道時間才找得到。

**分兩層解決：先讓人找得到（§1），再讓人看得懂（§2）。**

---

## 1. 找得到 —— 兩個工具

### A. `PlotPaintBar` 把型態的 K 棒整段換色　★ 最高槓桿

MC12 內建，直接重畫價格棒本身，**不需要額外物件、不受物件數量上限影響**。

```powerlanguage
{ 型態存活期間，把 K 棒換色。狀態不同顏色不同 }
if v_State > 0 then begin
    if      v_State = 1 then v_BarCol = Yellow      { 形成中 }
    else if v_State = 2 then v_BarCol = Cyan        { 成立，等待 }
    else if v_State = 3 then v_BarCol = Magenta     { 測試中 }
    else if v_State = 4 then v_BarCol = Red;        { 已跌破 }
    PlotPaintBar( High, Low, Open, Close, "P29", v_BarCol );
end
else
    NoPlot( 1 );
```

**效果**：整段型態在圖上是一條變色的帶子，**捲動時一眼就看得到**。

⚠️ `PlotPaintBar` 佔用 Plot1-4，需重排現有 plot 編號。

### E. 副圖 locator —— 壓縮視圖上的「型態在哪」

```powerlanguage
{ 放在副圖。壓縮到半年視圖時，每個尖峰就是一個型態 }
Plot6( IFF( v_State > 0, v_State, 0 ), "Locator" );
```

**用法**：把圖壓到半年，副圖出現 20 幾個尖峰 -> 對著尖峰放大。
**這是「找得到」的關鍵**，比任何畫線都重要。

---

## 2. 看得懂 —— 四個工具

### B. `Text_New` 在型態起點掛標籤

```powerlanguage
{ 型態成立那一根，在上緣線上方掛一個標籤 }
if v_JustFormed then begin
    v_Lbl = Text_New( v_PvDt[1], v_PvTm[1], v_PvPx[1] + v_Gap,
                      "P29 #" + NumToStr( v_Seq, 0 )
                      + IFF( v_Dir > 0, " UP", IFF( v_Dir < 0, " DN", " FLAT" ) )
                      + "  S1=" + NumToStr( v_S1, 0 ) + "/6" );
    Text_SetColor( v_Lbl, Col_Upper );
    Text_SetStyle( v_Lbl, 2, 1 );        { 水平置中，垂直靠下 }
    Text_SetSize( v_Lbl, 9 );
end;
```

**顯示**：`P29 #47 DN S1=5/6` —— 編號、方向、穩健度分數一次到位。
**編號對得上 `s16s_p29_clean.json`**，可以直接跟離線資料對帳。

### C. 六個樞紐各掛一個文字標記

**不要用 `Plot`** —— 現行 Plot3/Plot4 對**全部 151,177 個樞紐**開火（35.9% 的棒），
型態會淹沒在鋸齒裡。這是 2026-08-26 已修的 bug。

```powerlanguage
{ 只標這個型態的六個樞紐，不是全部樞紐 }
for v_i = 1 to 6 begin
    v_T = Text_New( v_PvDt[v_i], v_PvTm[v_i], v_PvPx[v_i], v_PvName[v_i] );
    Text_SetColor( v_T, IFF( v_PvIsHigh[v_i], Col_Upper, Col_Lower ) );
    Text_SetStyle( v_T, 2, IFF( v_PvIsHigh[v_i], 0, 1 ) );   { 高在上、低在下 }
    Text_SetSize( v_T, 8 );
end;
```

**`v_PvName` 存 `"PH3"` / `"PL3"` … —— 和圖鑑、規格文件的命名完全一致。**

⚠️ Rule #15：`.pla` 必須 100% ASCII，標籤只能用 `PH3` 這類字串，不可用箭頭符號。

### D. `TL_SetStyle` 區分「已確認段」與「外推段」

```powerlanguage
{ 已確認段（樞紐到樞紐）實線；外推段虛線 }
TL_SetStyle( v_TLup_solid, 1 );          { 1 = 實線 }
TL_SetStyle( v_TLup_ext,   2 );          { 2 = 虛線 }
TL_SetSize ( v_TLup_ext,   1 );          { 外推段細一點 }
```

**這樣「哪一段是事實、哪一段是推測」在圖上分得開** —— 和示意圖的視覺語言一致。

### F. `TL_New` 方框（可選）

沒有矩形原語，用四條線組。若已採用 A（PaintBar），**方框是多餘的**，
兩者擇一即可，不要同時上。

---

## 3. ⚠️ 物件數量上限 —— 必須處理

```
202 個型態 × ( 2 條主線 + 2 條外推 + 1 個標籤 + 6 個樞紐標記 ) = 2,222 個物件
```

MultiCharts 對 `TL_New` / `Text_New` 有實務上限，且物件過多會拖慢重繪。

**解法：只畫最近 N 個型態。**

```powerlanguage
inputs: Draw_Last_N( 20 );      { 0 = 全部畫。預設只畫最近 20 個 }

if Draw_Last_N > 0 and v_Seq <= v_TotalSoFar - Draw_Last_N then
    v_SkipDraw = True;
```

**注意**：`PlotPaintBar` 與副圖 locator **不受此限**（它們是 plot 不是物件），
所以「找得到」那一層永遠完整，只有「看得懂」那一層限制在最近 N 個。

---

## 4. 建議的實作順序

| 順位 | 項目 | 為什麼先做 |
|---|---|---|
| **1** | **A `PlotPaintBar`** | 解決「找不到」，一行就有效果 |
| **2** | **E 副圖 locator** | 壓縮視圖導航，配合 A 就能自己找到型態 |
| 3 | B `Text_New` 標籤 | 知道自己在看第幾號、方向、S1 |
| 4 | C 六樞紐標記 | 對得上規格文件的命名 |
| 5 | D 實線／虛線 | 分開事實與推測 |
| 6 | 物件上限管理 | 3-5 上線後才需要 |

**1 與 2 做完就足以驗收**，3-5 是錦上添花。

---

## 5. 現行指標要改的地方

| 現況 | 問題 | 改法 |
|---|---|---|
| Plot1/Plot2 = 上下緣線 | 已被 `TL_New` 取代，`Line_Mode=2` 才用 | 保留為對照 |
| Plot3/Plot4 = 全部樞紐 | 對 151,177 個樞紐開火 | **改成只標本型態六個樞紐** |
| Plot5 = State | 與價格共用軸，預設關 | **移到副圖當 locator** |
| 無 PaintBar | 找不到型態 | **新增** |
| 無文字標籤 | 不知道在看什麼 | **新增** |
| 線全為實線 | 分不出確認段與外推段 | `TL_SetStyle` |

---

## 6. 驗收方式

**不要再靠「捲動找找看」。** 改成：

1. 掛上指標，把圖壓到**半年**
2. 副圖 locator 應出現約 **10-15 個尖峰**（202 / 7.64 年 ≈ 26 個/年）
3. 對著尖峰放大 -> PaintBar 換色的那一段就是型態
4. 標籤讀出編號 -> 回 `s16s_p29_clean.json` 對帳

**這樣驗收不需要事先知道時間，也不需要截圖清單。**
