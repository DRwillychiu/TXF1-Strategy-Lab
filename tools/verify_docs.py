"""G0 document gate: keeps CLAUDE.md / PROGRESS.md / specs honest.
Usage: python tools/verify_docs.py [repo_root]        exit 0 = PASS, 1 = FAIL"""
import pathlib, re, sys

LINE_CAP = 300
REQUIRED_CLAUDE = ["## 文件三層", "## 我的部門", "## 技術規格", "## 驗證關卡", "## 兩套流程", "## 規矩"]

SOFT = "--soft-links" in sys.argv

def check(root):
    root = pathlib.Path(root); fails = []; warns = []
    c = root / "CLAUDE.md"; p = root / "PROGRESS.md"
    if not c.exists(): fails.append("CLAUDE.md 不存在")
    if not p.exists(): fails.append("PROGRESS.md 不存在")
    if fails: return fails
    ct = c.read_text(encoding="utf-8"); lines = ct.count("\n") + 1
    if lines > LINE_CAP: fails.append(f"CLAUDE.md {lines} 行 > 上限 {LINE_CAP}：請切割到 docs/archive/")
    for s in REQUIRED_CLAUDE:
        if s not in ct: fails.append(f"CLAUDE.md 缺少必要段落：{s}")
    for f in [c] + sorted((root / "docs" / "departments").glob("DEPT_*.md")):
        txt = f.read_text(encoding="utf-8")
        for m in re.finditer(r"`(docs/[^`]+\.md|tools/[^`]+\.(?:py|json)|strategies/[^`]+)`", txt):
            tgt = m.group(1)
            if "（待寫）" in txt[m.end():m.end() + 6] or "待建" in txt[m.end():m.end() + 6]: continue
            if not (root / tgt).exists():
                (warns if SOFT else fails).append(f"{f.name} 指向的檔案不存在：{tgt}")
    pt = p.read_text(encoding="utf-8")
    phases = re.findall(r"^## Phase (\d+)：", pt, flags=re.M)
    if not phases: fails.append("PROGRESS.md 找不到任何 Phase")
    nums = [int(x) for x in phases]
    if nums != sorted(nums): fails.append(f"PROGRESS.md Phase 編號未遞增：{nums}")
    cur = None; seen = set()
    for line in pt.splitlines():
        mp = re.match(r"^## Phase (\d+)：", line)
        if mp: cur = mp.group(1); continue
        mt = re.match(r"^- \[([ xX])\] Task (\d+)\.(\d+)：", line)
        if line.strip().startswith("- [") and not mt:
            fails.append(f"PROGRESS.md 格式錯誤（應為 `- [ ] Task N.M：摘要`）：{line.strip()[:40]}")
        elif mt:
            if cur and mt.group(2) != cur: fails.append(f"Task {mt.group(2)}.{mt.group(3)} 出現在 Phase {cur} 之下")
            k = (mt.group(2), mt.group(3))
            if k in seen: fails.append(f"Task 編號重複：{k[0]}.{k[1]}")
            seen.add(k)
    for m in re.finditer(r"Spec：`([^`]+\.md)`", pt):
        if not (root / m.group(1)).exists():
            (warns if SOFT else fails).append(f"PROGRESS.md 指向的 Spec 不存在：{m.group(1)}")
    for w in warns: print("    ! " + w + "（警告，不擋）")
    todo = [f"{a}.{b}" for a, b in sorted(seen) if f"- [ ] Task {a}.{b}：" in pt]
    print(f"    Phase {len(phases)} 個、Task {len(seen)} 個；未完成 {len(todo)} 個，下一步 Task {todo[0] if todo else '—'}")
    return fails

if __name__ == "__main__":
    f = check(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(f"[{'FAIL' if f else 'PASS'}] G0 文件檢查")
    for x in f: print("    x " + x)
    sys.exit(1 if f else 0)
