# S16_S 已發布的線上文件（Artifact 網址）

這些頁面同時存在於 repo 內（HTML 原始檔）與 claude.ai 上（可分享的網址）。
**改內容一律改 repo 裡的產生器，再重新發布同一個網址**，網址不會變。

| 頁面 | 網址 | repo 原始檔 | 產生器 |
|---|---|---|---|
| **缺口型態組 P31／P62／P67** | https://claude.ai/code/artifact/572a7a51-447c-4762-a0da-2d62f930b0db | `docs/research/S16S_gap_group_diagram.html` | `scripts/research/s16s_gap_make_diagram.py` ＋ `_diagram.css` |
| **鑽石型態 P30／P61** | https://claude.ai/code/artifact/b6deabc7-3607-4647-a0c8-5766d5f74a18 | `docs/research/S16S_diamond_diagram.html` | `scripts/research/s16s_diamond_make_diagram.py` ＋ `_diagram.css` |
| **★ 型態層總覽**（狀態表） | https://claude.ai/code/artifact/95285d4d-a64a-47d7-a81e-15cd2db8c2a9 | `docs/research/S16S_pattern_layer_status.html` | `scripts/research/s16s_status_make_page.py` |
| **樞紐型 A 組七型態** | https://claude.ai/code/artifact/adf56543-4a72-4048-9d68-cdb65f9bed57 | `docs/research/S16S_groupA_diagram.html` | `scripts/research/s16s_groupA_make_page.py` |
| **★ 樞紐尺度** | https://claude.ai/code/artifact/031763a0-9b43-4cea-872e-ad81f65df25f | `docs/research/S16S_pivot_scale.html` | `scripts/research/s16s_scale_make_page.py` |
| **型態全圖鑑**（143 種） | https://claude.ai/code/artifact/22fa588b-51f5-43ce-8e11-bc301d4c35ef | `docs/research/S16S_pattern_atlas_full.html` | `scripts/research/s16s_make_full_atlas.py` ＋ `_atlas.css` |
| **P51-P54 擴散楔形家族** | https://claude.ai/code/artifact/62ab6ce8-09e2-4deb-a7f3-784357258278 | `docs/research/S16S_P51_P54_diagram.html` | `scripts/research/s16s_p51_p54_make_diagram.py` ＋ `_diagram.css` |
| **P49 / P50 擴散頂底示意圖** | https://claude.ai/code/artifact/30ee09ef-fae0-4742-9323-12c7a3cb7e67 | `docs/research/S16S_P49_P50_diagram.html` | `scripts/research/s16s_p49_make_diagram.py` |
| **P29 擴散三角示意圖** | https://claude.ai/code/artifact/79ff51ff-ec21-4a24-9bc1-be99c4215c25 | `docs/research/S16S_P29_diagram.html` | `scripts/research/s16s_p29_make_diagram.py` |
| K 棒型態圖鑑（33 種） | https://claude.ai/code/artifact/5dbdffac-f3aa-4096-870b-bf8453f2427b | `docs/research/S16S_kbar_atlas_33.html` | `scripts/research/s16s_make_atlas.py` |
| 全版本績效總表 | https://claude.ai/code/artifact/365d908f-8ca1-4c09-ba9c-f13381efb8cc | `docs/research/S16S_version_performance_table.html` | 資料寫在 HTML 的 `const D = [...]` |

---

## 型態全圖鑑 — 143 種怎麼拆

```
K 棒型態  71 種   已編碼 33 ／ 因跳空排除 23 ／ 單根 15
圖形型態  72 種   已定義並檢定 33 ／ 未編碼 39
合計     143 種   每一種都附一句話說明
```

⚠️ **「純圖形型態」是 72 種，不是 143 種。** 143 是含 K 棒型態的總數。

### P29 示意圖 — 重生所需的輸入

```bash
python scripts/research/s16s_p29_make_diagram.py
```

| 輸入 | 在 git？ | 說明 |
|---|---|---|
| `scripts/research/s16s_p29_example.json` | ✅ | 真實案例的 29 根 K 棒與六個樞紐（2.8 KB） |
| `scripts/research/s16s_5min.csv` | ❌ | 32 MB，**不進 git**，由 1 分 K 母檔重建 |

`example.json` **必須進 git** —— 沒有它就重生不出圖。
`s16s_5min.csv` 只有 `s16s_p29_find_example.py` 需要（重新挑案例時），
產圖本身不需要。**驗證：重跑產圖器與 git 版位元組完全相同。**

### 型態全圖鑑 — 更新流程

```bash
python scripts/research/s16s_make_full_atlas.py
```

改資料只動產生器裡的六個清單：`CODED` / `GAPX` / `ONEBAR` / `CHART`（含 `CHART2`）/
`NOTCODED`（含 `NOTCODED2`），文字說明在 `DESC` / `GAPD` / `ONED` / `CHD` 四個字典。
**渲染邏輯不需要動。**

出現次數來自兩支普查腳本，**兩支都無損益欄**：

| 腳本 | 產出 |
|---|---|
| `scripts/research/s16s_pattern_census.py` | 33 種 K 棒型態的次數與進場棒命中數 |
| `scripts/research/s16s_chart_pattern_census.py` | 圖形型態第一波 17 種 |
| `scripts/research/s16s_chart_pattern_wave2.py` | 圖形型態第二波 16 種 |
