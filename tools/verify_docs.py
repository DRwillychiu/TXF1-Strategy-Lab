"""G0 document gate (v1.0 templates, 2026-10-31): keeps CLAUDE.md / PROJECT.md honest.
Usage: python tools/verify_docs.py [repo_root] [--soft-links]      exit 0 = PASS, 1 = FAIL

  CLAUDE.md   <context> <commands> <project_rules> blocks; every rule line carries 「原因：」;
              points to @PROJECT.md; at most LINE_CAP lines
  PROJECT.md  required sections; 「最後更新：YYYY-MM-DD」; 下一步 ≤ 3 numbered items;
              決策紀錄 lines are 「- YYYY-MM-DD｜決定：…｜原因：…｜放棄的選項：…」 in date order (append-only)
  links       backtick paths in CLAUDE.md, PROJECT.md, agent.md, docs/departments/*.md exist;
              an eval `tests/x.py::test_y` or a bare `test_y` must name a real test function
Standard library only."""
import pathlib, re, sys

LINE_CAP = 300
CLAUDE_BLOCKS = ["context", "commands", "project_rules"]
PROJECT_SECTIONS = ["## 目前狀態", "## 下一步", "## 考題", "## 決策紀錄", "## 已知坑"]
MAX_NEXT = 3
DECISION_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})｜決定：[^｜]+｜原因：[^｜]+｜放棄的選項：.+$")
PATH_RE = re.compile(r"`((?:docs|tools|strategies|tests|config|txfcore)/[^`<>*{}]+?)(?:::(\w+))?`")
BARE_TEST_RE = re.compile(r"`(test_\w+)`")

SOFT = "--soft-links" in sys.argv


def block(text, tag):
    """Text inside <tag>...</tag>, or None when the block is missing."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.S)
    return m.group(1) if m else None


def section(text, heading):
    """Body of a '## ' section (up to the next '## ' heading)."""
    i = text.find(heading)
    if i < 0: return None
    rest = text[i + len(heading):]
    j = rest.find("\n## ")
    return rest if j < 0 else rest[:j]


def check_claude(text):
    fails = []
    lines = text.count("\n") + 1
    if lines > LINE_CAP: fails.append(f"CLAUDE.md {lines} 行 > 上限 {LINE_CAP}：只放規則，現況移到 PROJECT.md")
    for tag in CLAUDE_BLOCKS:
        if block(text, tag) is None: fails.append(f"CLAUDE.md 缺少 <{tag}>…</{tag}> 區塊")
    ctx = block(text, "context") or ""
    if "@PROJECT.md" not in ctx: fails.append("CLAUDE.md 的 <context> 沒有指向 @PROJECT.md")
    for ln in (block(text, "project_rules") or "").splitlines():
        s = ln.strip()
        if s.startswith("- ") and "原因：" not in s:
            fails.append(f"CLAUDE.md 規則沒寫原因：{s[:40]}")
    return fails


def check_project(text):
    fails = []
    for h in PROJECT_SECTIONS:
        if h not in text: fails.append(f"PROJECT.md 缺少段落：{h}")
    state = section(text, "## 目前狀態") or ""
    if not re.search(r"最後更新：\d{4}-\d{2}-\d{2}", state):
        fails.append("PROJECT.md「目前狀態」沒有「最後更新：YYYY-MM-DD」")
    nxt = section(text, "## 下一步") or ""
    items = [l for l in nxt.splitlines() if re.match(r"^\d+\.\s*\S", l)]
    if len(items) > MAX_NEXT: fails.append(f"PROJECT.md「下一步」有 {len(items)} 項 > {MAX_NEXT} 項")
    if not items: fails.append("PROJECT.md「下一步」是空的")
    dates = []
    for l in (section(text, "## 決策紀錄") or "").splitlines():
        if not l.startswith("- "): continue
        m = DECISION_RE.match(l)
        if not m: fails.append(f"PROJECT.md 決策紀錄格式錯誤（- 日期｜決定：｜原因：｜放棄的選項：）：{l[:40]}"); continue
        dates.append(m.group(1))
    if dates != sorted(dates): fails.append("PROJECT.md 決策紀錄日期沒有依序（只追加，不插入舊日期）")
    return fails


def test_names(root):
    names = set()
    for f in (root / "tests").glob("*.py"):
        names.update(re.findall(r"^def (test_\w+)\(", f.read_text(encoding="utf-8", errors="replace"), re.M))
    return names


def check_links(root, files):
    fails = []; known = test_names(root)
    for f in files:
        txt = f.read_text(encoding="utf-8")
        for m in PATH_RE.finditer(txt):
            tgt, func = m.group(1).rstrip("/"), m.group(2)
            after = txt[m.end():m.end() + 6]
            if "（待寫）" in after or "待建" in after: continue
            p = root / tgt
            if not p.exists():
                fails.append(f"{f.name} 指向的檔案不存在：{tgt}"); continue
            if func and p.is_file() and not re.search(rf"^def {func}\(", p.read_text(encoding="utf-8"), re.M):
                fails.append(f"{f.name} 的考題 {tgt}::{func} 找不到這個測試")
        if f.name == "PROJECT.md":
            for name in BARE_TEST_RE.findall(txt):
                if name not in known: fails.append(f"PROJECT.md 的考題 {name} 在 tests/ 裡找不到")
    return fails


def check(root):
    root = pathlib.Path(root); fails = []
    c, p = root / "CLAUDE.md", root / "PROJECT.md"
    if not c.exists(): fails.append("CLAUDE.md 不存在")
    if not p.exists(): fails.append("PROJECT.md 不存在")
    if fails: return fails
    fails += check_claude(c.read_text(encoding="utf-8"))
    fails += check_project(p.read_text(encoding="utf-8"))
    files = [c, p] + [f for f in [root / "agent.md"] if f.exists()]
    files += sorted((root / "docs" / "departments").glob("DEPT_*.md"))
    links = check_links(root, files)
    if SOFT:
        for x in links: print("    ! " + x + "（警告，不擋）")
    else:
        fails += links
    nxt = section(p.read_text(encoding="utf-8"), "## 下一步") or ""
    first = next((l.strip() for l in nxt.splitlines() if re.match(r"^\d+\.\s*\S", l)), "—")
    print(f"    下一步：{first[:60]}")
    return fails


if __name__ == "__main__":
    try: sys.stdout.reconfigure(errors="replace")
    except Exception: pass
    f = check(next((a for a in sys.argv[1:] if not a.startswith("--")), "."))
    print(f"[{'FAIL' if f else 'PASS'}] G0 文件檢查")
    for x in f: print("    x " + x)
    sys.exit(1 if f else 0)
