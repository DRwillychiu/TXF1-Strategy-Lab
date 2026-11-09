"""全部 .md 清單（每週五 agent.md A09）：一檔一句話＋資料夾用途。用法：python tools/md_inventory.py <repo> <輸出.md>"""
import pathlib, re, collections, sys
root = pathlib.Path(sys.argv[1]); out_path = pathlib.Path(sys.argv[2])
PURPOSE = {
 "根目錄": "規則（CLAUDE.md）、現況與考題（PROJECT.md）、例行工作（agent.md）、說明",
 "docs（根）": "全庫共用的參考：上架版本、結構、名詞",
 "docs/departments": "七個部門的重點與團隊清單（CLAUDE.md 的下一層）",
 "docs/decisions": "決定紀錄，只增不改",
 "docs/registers": "問題登記簿：P 已發生、Q 待裁決",
 "docs/ops": "上線操作、換版 SOP、當天計畫、項目拆解",
 "docs/specs": "規格：策略、Python 移植、模組設計",
 "docs/policies": "規範：回覆格式、文件維護、命名",
 "docs/methodology": "方法與回顧（坑洞清單）",
 "docs/research": "研究、驗證報告、規則手冊、審查",
 "docs/diagrams": "定案圖與附錄",
 "docs/archive": "歸檔：不再更新，README 記錄被誰取代",
 "docs/strategy_archive": "已淘汰策略的總結",
 "docs/live_optimization": "上架後優化紀錄",
 "strategies/live": "MC 正在跑的上架檔（10/31 起與 LIVE_VERSIONS 第 1 節一致）",
 "strategies/live_simulation": "模擬盤版本與說明",
 "strategies/research": "各版本研究、結果、語意對照",
 "strategies/batch01": "早期策略批次",
 ".claude": "專案技能（對抗式工程 SOP 等）",
 "txfcore": "Python 專案說明與分層規則",
 "optimization": "早期參數優化紀錄",
 "backtest": "回測說明",
 "scripts": "腳本說明",
}
def first_line(t):
    for ln in t.splitlines():
        s = ln.strip().lstrip("#").strip()
        if s and not s.startswith("---"): return s[:110]
    return "（空檔）"
groups = collections.OrderedDict(); n = 0
for p in sorted(root.rglob("*.md")):
    if {".git", "__pycache__", ".pytest_cache"} & set(p.parts): continue
    rel = p.relative_to(root).as_posix(); parts = rel.split("/")
    if len(parts) == 1: g = "根目錄"
    elif parts[0] == "docs" and len(parts) == 2: g = "docs（根）"
    else: g = "/".join(parts[:2]) if parts[0] in ("docs","strategies") else parts[0]
    groups.setdefault(g, []).append((rel, first_line(p.read_text(encoding="utf-8", errors="ignore")))); n += 1
order = sorted(groups, key=lambda g: (g != "根目錄", -len(groups[g])))
out = [f"# repo 全部 .md 清單（2026-10-09 歸檔後，共 {n} 份）", "",
       "> 一句話＝檔案第一個標題（自動擷取）；資料夾用途寫在小標下方。重產：`python tools/md_inventory.py . docs/ops/md_inventory_年月日.md`（步驟見 agent.md A09）。", ""]
for g in order:
    out += [f"## {g}（{len(groups[g])}）", "", f"用途：{PURPOSE.get(g, '（未分類）')}", ""]
    out += [f"- `{r}` — {s}" for r, s in groups[g]] + [""]
out_path.write_text("\n".join(out), encoding="utf-8")
print(n, [(g, len(groups[g])) for g in order])
