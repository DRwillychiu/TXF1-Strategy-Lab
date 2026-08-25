# S16_S 已發布的線上文件（Artifact 網址）

這些頁面同時存在於 repo 內（HTML 原始檔）與 claude.ai 上（可分享的網址）。
**改內容一律改 repo 裡的產生器，再重新發布同一個網址**，網址不會變。

| 頁面 | 網址 | repo 原始檔 | 產生器 |
|---|---|---|---|
| **型態全圖鑑**（143 種） | https://claude.ai/code/artifact/22fa588b-51f5-43ce-8e11-bc301d4c35ef | `docs/research/S16S_pattern_atlas_full.html` | `scripts/research/s16s_make_full_atlas.py` ＋ `_atlas.css` |
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
