"""Move the G0/G1 additions to BEFORE 'exit 0' in .githooks/pre-commit.
Run from the repo root:   py hook\fix_hook.py
Safe: writes a .bak2 backup first, keeps LF line endings, ASCII only."""
import pathlib, sys

BLOCK = """
echo ""
echo "  --- G0  docs check (CLAUDE.md / PROGRESS.md) ---"
python tools/verify_docs.py . --soft-links
if [ $? -ne 0 ]; then
  echo ""
  echo "  G0 FAILED - commit blocked."
  exit 1
fi

echo ""
echo "  --- G1  static check (strategies/live) ---"
python tools/verify_static.py strategies/live
if [ $? -ne 0 ]; then
  echo ""
  echo "  G1 FAILED - commit blocked."
  exit 1
fi
"""

def main():
    p = pathlib.Path(".githooks/pre-commit")
    if not p.exists():
        print("[x] .githooks/pre-commit not found. Run this from the repo root."); return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    p.with_suffix(p.suffix + ".bak2").write_bytes(p.read_bytes())
    lines = text.split("\n")

    # 1) cut everything after the last 'exit 0' if it is the previously appended patch
    idx = max(i for i, ln in enumerate(lines) if ln.strip() == "exit 0")
    tail = "\n".join(lines[idx + 1:])
    if "verify_docs.py" in tail or "verify_static.py" in tail:
        keep = lines[:idx + 1]           # drop the whole mis-placed tail
    else:
        keep = lines[:]                  # nothing appended yet
    # remove any earlier copy of the block so it is not duplicated
    body = "\n".join(keep)
    if "verify_docs.py" in body:
        out_lines, skip = [], False
        for ln in keep:
            s = ln.strip()
            if s.startswith('echo "  --- G0') or s.startswith('echo "  --- G1'):
                skip = True
            if skip:
                if s == "fi":
                    skip = False
                continue
            out_lines.append(ln)
        keep = out_lines

    # 2) insert the block right before the final 'exit 0'
    i2 = max(i for i, ln in enumerate(keep) if ln.strip() == "exit 0")
    out = keep[:i2] + BLOCK.strip("\n").split("\n") + ["", keep[i2]]

    p.write_bytes(("\n".join(out).rstrip("\n") + "\n").encode("utf-8"))
    print("[OK] patched. G0/G1 now run before 'exit 0'.")
    print("     backup: .githooks/pre-commit.bak2")
    return 0

sys.exit(main())
