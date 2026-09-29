"""G0b version-sync gate: keeps LIVE_VERSIONS / entry docs in step with strategies/research.
Usage: python tools/verify_versions.py [repo_root]        exit 0 = PASS, 1 = FAIL

  R1  every strategies/research/<strategy>/<code>_v*/ folder is mentioned in docs/LIVE_VERSIONS.md
      (folder name, or one line holding both the code and the version, e.g. "L3 ... v18.2";
       a same-major range such as "v19.0–v19.4" on a line with the code counts for every version in it)
  R2  every research .pla whose header "MC Load Name" does not end in _RESEARCH
      is listed in tools/version_exceptions.txt (one path per line, "# reason" required)
  R3  no phrase from tools/retired_phrases.txt appears in the entry docs
      (CLAUDE.md, PROGRESS.md, docs/LIVE_VERSIONS.md, docs/departments/*.md, docs/ops/*.md);
      lines containing 原寫 / 更正 / 已被取代 are correction notes and are skipped
  R4  every .md in docs/decisions/ and docs/ops/ is mentioned (path or file name) by PROGRESS.md,
      CLAUDE.md, docs/departments/*.md, docs/registers/*.md or docs/LIVE_VERSIONS.md
  R5  WARN only: a file under strategies/research/ is newer than docs/LIVE_VERSIONS.md
      (mtime; after a fresh clone or pull this can be noise)

Folders named "archive" under strategies/research/ are the retired area and are skipped by R1 and R2.
Standard library only. Files are read as UTF-8 with errors="replace", so a non-UTF-8 file never crashes it."""
import datetime, pathlib, re, sys

HEADER_LINES = 40                      # MC Load Name must sit in the header block
SKIP_WORDS = ("原寫", "更正", "已被取代")
LOAD_RE = re.compile(r"MC\s+Load\s+Name\s*:\s*(\S+)", re.I)
VDIR_RE = re.compile(r"^(?P<code>.+?)_(?P<ver>[vV]\d[\w.\-]*)$")
RANGE_RE = re.compile(r"(?<![\w.])v(\d+)\.(\d+)\s*[–—~～\-－]\s*v?(\d+)\.(\d+)(?![\d])", re.I)


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def rel(root, path):
    return path.relative_to(root).as_posix()


def load_list(path):
    """Lines of '<value>  # reason'. Blank lines and lines starting with # are comments."""
    out = []
    if not path.exists(): return out
    for i, raw in enumerate(read(path).splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        val, _, reason = s.partition("#")
        out.append((val.strip(), reason.strip(), i))
    return out


def norm(s):
    """Loose match for R3: ignore whitespace, markdown * and `, and full-width ＝."""
    return re.sub(r"[\s*`]+", "", s).replace("＝", "=")


def research_dirs(root):
    base = root / "strategies" / "research"
    out = []
    if not base.is_dir(): return out
    for strat in sorted(base.iterdir()):
        if not strat.is_dir() or strat.name == "archive": continue
        for d in sorted(strat.iterdir()):
            m = VDIR_RE.match(d.name)
            if d.is_dir() and m: out.append((d, m.group("code"), m.group("ver")))
    return out


def ver_forms(ver):
    forms = {ver}
    if "_" in ver: forms.add(ver.replace("_", "-"))
    return forms


def mentioned(lv_text, lv_lines, folder, code, ver):
    if re.search(r"(?<![A-Za-z0-9])" + re.escape(folder) + r"(?![0-9])", lv_text, re.I): return True
    code_re = re.compile(r"(?<![A-Za-z0-9])" + re.escape(code) + r"(?![0-9])", re.I)
    ver_res = [re.compile(r"(?<![\w.])" + re.escape(v) + r"(?![0-9])", re.I) for v in ver_forms(ver)]
    mv = re.fullmatch(r"[vV](\d+)\.(\d+)", ver)
    for line in lv_lines:
        if not code_re.search(line): continue
        if any(r.search(line) for r in ver_res): return True
        if mv:
            for a, b, c, d in RANGE_RE.findall(line):
                if a == c == mv.group(1) and int(b) <= int(mv.group(2)) <= int(d): return True
    return False


def check(root):
    root = pathlib.Path(root).resolve(); fails = []; warns = []; info = []
    lv = root / "docs" / "LIVE_VERSIONS.md"

    # R1 research folders registered in LIVE_VERSIONS
    dirs = research_dirs(root)
    if not lv.exists():
        fails.append("R1 docs/LIVE_VERSIONS.md 不存在")
    else:
        lv_text = read(lv); lv_lines = lv_text.splitlines()
        miss = [d for d, code, ver in dirs if not mentioned(lv_text, lv_lines, d.name, code, ver)]
        info.append(f"R1 研究版資料夾 {len(dirs)} 個：LIVE_VERSIONS 有提到 {len(dirs) - len(miss)} 個、沒提到 {len(miss)} 個")
        for d in miss: fails.append(f"R1 LIVE_VERSIONS 沒提到：{rel(root, d)}/")

    # R2 research Load Names must end in _RESEARCH unless listed as exceptions
    base = root / "strategies" / "research"
    plas = [p for p in sorted(base.rglob("*.pla")) if "archive" not in p.relative_to(base).parts] if base.is_dir() else []
    exc_path = root / "tools" / "version_exceptions.txt"
    exc = {}
    for val, reason, ln in load_list(exc_path):
        key = val.replace("\\", "/")
        if key.startswith("./"): key = key[2:]
        if not reason: fails.append(f"R2 tools/version_exceptions.txt 第 {ln} 行沒寫理由（格式：路徑  # 理由）：{val}")
        exc[key] = ln
    offenders = {}; no_header = 0
    for p in plas:
        head = "\n".join(read(p).splitlines()[:HEADER_LINES])
        m = LOAD_RE.search(head)
        if not m: no_header += 1; continue
        if not m.group(1).endswith("_RESEARCH"): offenders[rel(root, p)] = m.group(1)
    new = [k for k in offenders if k not in exc]
    info.append(f"R2 研究版 .pla {len(plas)} 個（沒有 Load Name 標頭 {no_header} 個，略過）："
                f"不是 _RESEARCH 結尾 {len(offenders)} 個，其中已登記例外 {len(offenders) - len(new)} 個")
    for k in new: fails.append(f"R2 Load Name 不是 _RESEARCH 結尾、也沒登記例外：{k}（{offenders[k]}）")
    if not exc_path.exists() and offenders: fails.append("R2 tools/version_exceptions.txt 不存在")
    for k, ln in exc.items():
        if k not in offenders:
            why = "檔案不存在" if not (root / k).exists() else "Load Name 已經是 _RESEARCH 結尾或沒有標頭"
            warns.append(f"R2 tools/version_exceptions.txt 第 {ln} 行可以刪除（{why}）：{k}")

    # R3 retired phrases in entry docs
    phrases = [(val, reason) for val, reason, _ in load_list(root / "tools" / "retired_phrases.txt") if norm(val)]
    entry = [root / "CLAUDE.md", root / "PROGRESS.md", lv]
    entry += sorted((root / "docs" / "departments").glob("*.md")) + sorted((root / "docs" / "ops").glob("*.md"))
    entry = [f for f in entry if f.exists()]
    hits = 0
    for f in entry:
        for i, line in enumerate(read(f).splitlines(), 1):
            if any(w in line for w in SKIP_WORDS): continue
            nl = norm(line)
            found = [(ph, why) for ph, why in phrases if norm(ph) in nl]
            if not found: continue
            hits += 1
            shown = "」「".join(ph for ph, _ in found)
            why = found[0][1]
            fails.append(f"R3 {rel(root, f)}:{i} 出現退役說法「{shown}」" + (f"（{why}）" if why else ""))
    info.append(f"R3 入口文件 {len(entry)} 個 × 退役說法 {len(phrases)} 條：命中 {hits} 行"
                "（含「原寫／更正／已被取代」的行略過）")

    # R4 decisions / ops docs must be linked from an index doc
    targets = sorted((root / "docs" / "decisions").glob("*.md")) + sorted((root / "docs" / "ops").glob("*.md"))
    idx = [root / "PROGRESS.md", root / "CLAUDE.md", lv]
    idx += sorted((root / "docs" / "departments").glob("*.md")) + sorted((root / "docs" / "registers").glob("*.md"))
    idx_text = "\n".join(read(f) for f in idx if f.exists())
    unlinked = []
    for t in targets:
        stem_re = r"(?<![A-Za-z0-9_])" + re.escape(t.stem) + r"(?![A-Za-z0-9_])"
        if t.name not in idx_text and not re.search(stem_re, idx_text): unlinked.append(t)
    info.append(f"R4 decisions／ops 文件 {len(targets)} 個：有被入口連到 {len(targets) - len(unlinked)} 個、沒被連到 {len(unlinked)} 個")
    for t in unlinked:
        fails.append(f"R4 沒有被 PROGRESS／CLAUDE.md／部門檔／登記簿／LIVE_VERSIONS 連到：{rel(root, t)}")

    # R5 (warn) research newer than LIVE_VERSIONS
    if lv.exists() and base.is_dir():
        files = [p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        if files:
            newest = max(files, key=lambda p: p.stat().st_mtime)
            t_new, t_lv = newest.stat().st_mtime, lv.stat().st_mtime
            if t_new > t_lv:
                fmt = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
                warns.append(f"R5 LIVE_VERSIONS 可能過期（may be stale）：{rel(root, newest)} {fmt(t_new)} "
                             f"晚於 docs/LIVE_VERSIONS.md {fmt(t_lv)}")

    for s in info: print("    " + s)
    for w in warns: print("    ! " + w + "（警告，不擋）")
    return fails


if __name__ == "__main__":
    try: sys.stdout.reconfigure(errors="replace")
    except Exception: pass
    f = check(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(f"[{'FAIL' if f else 'PASS'}] G0b 版本同步")
    for x in f: print("    x " + x)
    sys.exit(1 if f else 0)
