"""Compare the code Willy copied from the LIVE machine with the repo base of V1.1.0 (2026-11-19).

Why: V1.1.0 was built from the repo research copies (L1 V3.8, L2 v5.12, L3 v18.4, L4 v14.10, L5 v19.20).
The ground truth is what the live MC is running. If the live code differs, V1.1.0 must be rebuilt from it.

  python scripts/research/registry_2027_20261119/check_live_paste.py L2 strategies/live_machine_snapshot/20261119/L2_TrendShort.txt

The pasted file is raw evidence: it is read, never modified.
Verdict:
  SAME FILE   text identical (line endings / trailing spaces ignored)        -> V1.1.0 stands as built
  SAME CODE   only comments / spacing differ; every statement and default same -> V1.1.0 trades the same;
              rebuild from the paste only if you want the live comments kept
  DIFFERENT   code or input defaults differ                                  -> rebuild V1.1.0 from the paste
"""
import difflib, importlib.util, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("verify_static", ROOT / "tools" / "verify_static.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

R = "strategies/research"
BASE = {
    "L1": f"{R}/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla",
    "L2": f"{R}/L2_TrendShort/L2_v5.12/L2_TrendShort_v5.12.pla",
    "L3": f"{R}/L3_ConsolidationLong/L3_v18.4/L3_ConsolidationLong_v18.4.pla",
    "L4": f"{R}/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla",
    "L5": f"{R}/L5_BreakoutLong/L5_v19.20/L5_BreakoutLong_v19.20.pla",
}


def norm_lines(text):
    return [l.rstrip() for l in text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")]


def stmts(text):
    code = vs.strip_comments(text)
    return [re.sub(r"\s+", " ", s).strip() for s in code.split(";") if s.strip()]


def main(code, paste_path):
    base = (ROOT / BASE[code]).read_bytes().decode("ascii")
    raw = pathlib.Path(paste_path).read_bytes()
    nonascii = sum(1 for b in raw if b > 127)
    paste = raw.decode("utf-8", errors="replace")
    print(f"paste : {paste_path}  ({len(norm_lines(paste))} lines, non-ASCII bytes {nonascii})")
    print(f"base  : {BASE[code]}  ({len(norm_lines(base))} lines)")
    if nonascii:
        print("  ! non-ASCII characters in the paste (MC only takes ASCII; often a copy artefact)")
    if norm_lines(paste) == norm_lines(base):
        print("[SAME FILE] identical text (line endings / trailing spaces ignored) -> V1.1.0 stands as built")
        return 0
    a, b = stmts(base), stmts(paste)
    ia, ib = vs.inputs_block(vs.strip_comments(base)), vs.inputs_block(vs.strip_comments(paste))
    reg = re.findall(r"Registry_Valid_Until\s*\(\s*(\d+)\s*\)", vs.strip_comments(paste))
    tails = re.findall(r"Holiday_Tail\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)", vs.strip_comments(paste))
    print(f"paste : {len(ib)} inputs, Registry_Valid_Until {reg}, Holiday_Tail rows {len(tails)}")
    diff_inputs = sorted(k for k in set(ia) | set(ib) if ia.get(k) != ib.get(k))
    for k in diff_inputs:
        print(f"  input {k}: repo {ia.get(k)}  live {ib.get(k)}")
    if a == b and not diff_inputs:
        print("[SAME CODE] every statement and default identical; only comments / spacing differ")
        for line in list(difflib.unified_diff(norm_lines(base), norm_lines(paste), "repo", "live", lineterm="", n=0))[:40]:
            print("    " + line[:160])
        return 0
    print("[DIFFERENT] code differs -> rebuild V1.1.0 from the live paste. First differences (statements):")
    for line in list(difflib.unified_diff(a, b, "repo", "live", lineterm="", n=0))[:60]:
        print("    " + line[:200])
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in BASE:
        sys.exit("usage: check_live_paste.py L1|L2|L3|L4|L5 <pasted file>")
    sys.exit(main(sys.argv[1], sys.argv[2]))
