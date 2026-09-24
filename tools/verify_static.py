"""G1 static gate for PowerLanguage strategies (.pla). Exit code 0 = all PASS, 1 = any FAIL.
Usage: python tools/verify_static.py <folder or .pla> [...]"""
import re, sys, pathlib

def strip_comments(code):
    """Remove { } block comments (nesting-aware, as MultiCharts accepts nested braces) and // comments."""
    out, depth, i, n, in_str = [], 0, 0, len(code), False
    while i < n:
        ch = code[i]
        if depth == 0 and ch == '"':
            in_str = not in_str; out.append(ch); i += 1; continue
        if not in_str:
            if ch == "{":
                depth += 1; i += 1; continue
            if ch == "}" and depth > 0:
                depth -= 1; i += 1; continue
            if depth == 0 and code.startswith("//", i):
                j = code.find("\n", i); i = n if j < 0 else j; continue
        if depth == 0:
            out.append(ch)
        i += 1
    return "".join(out)

def inputs_block(code):
    m = re.search(r"\binputs\s*:(.*?);", code, flags=re.S | re.I)
    return dict((k, v.strip()) for k, v in re.findall(r"([A-Za-z_]\w*)\s*\(\s*([^)]*)\)", m.group(1))) if m else {}

def check(path):
    raw = pathlib.Path(path).read_bytes()
    res = []
    bad = [i for i, b in enumerate(raw) if b > 127]
    res.append(("C1 ASCII 100%", not bad, f"{len(bad)} non-ASCII bytes" if bad else ""))
    code = strip_comments(raw.decode("ascii", errors="replace"))
    lab = re.search(r"(Sell|BuyToCover|Buy\s*To\s*Cover)\s*\(\s*\"\w*Settlement\w*\"", code, re.I)
    gate = re.search(r"v_Settlement_Day\s*=\s*false", code, re.I) or re.search(r"if\s+v_Settlement_Day\s+then", code, re.I)
    res.append(("C2 Settlement flat (exit + entry gate)", bool(lab and gate), "" if lab and gate else ("no Settlement exit" if not lab else "no entry gate")))
    sc = [m.start() for m in re.finditer(r"\bSetStopContract\b", code, re.I)]
    sl = [m.start() for m in re.finditer(r"\bSetStopLoss\s*\(", code, re.I)]
    ins = inputs_block(code)
    one_group = len(sl) == 1 or (len(sl) == 2 and re.search(r"\belse\b", code[sl[0]:sl[1]], re.I) and sl[1] - sl[0] < 1500)
    ok3 = len(sc) == 1 and bool(sl) and one_group and sc[0] < sl[0] and any(k.lower() == "sl_pct" for k in ins)
    res.append(("C3 P3b: 1x SetStopContract before one SetStopLoss group + SL_Pct input", ok3, f"SetStopContract={len(sc)} SetStopLoss={len(sl)} SL_Pct={'yes' if any(k.lower()=='sl_pct' for k in ins) else 'no'}"))
    g = re.search(r"MarketPosition\s*=\s*0|\bMP\s*=\s*0", code, re.I)
    res.append(("C4 entry requires flat position", bool(g), "" if g else "no MarketPosition = 0 guard"))
    over = [f"{k}={v}" for k, v in ins.items() if re.search(r"len|length|lookback|period", k, re.I) and re.fullmatch(r"\d+(\.\d+)?", v) and float(v) > 99]
    res.append(("C5 lookback inputs <= 99 (MaxBarsBack 100)", not over, ", ".join(over)))
    ph = re.findall(r"\b(TODO|FIXME|placeholder)\b", code, re.I)
    blocks = set(re.findall(r"\b(v_\w+_Block)\s*=\s*false\s*;", code, re.I))
    dead = [b for b in blocks if not re.search(re.escape(b) + r"\s*=\s*true", code, re.I)]
    res.append(("C6 no placeholders / dead Block flags", not ph and not dead, ", ".join(ph + dead)))
    return res

def main(args):
    files = []
    for a in args or ["strategies/live"]:
        p = pathlib.Path(a)
        files += sorted(p.rglob("*.pla")) if p.is_dir() else [p]
    files = [f for f in files if "archive" not in f.parts]
    fail = 0
    for f in files:
        rs = check(f)
        ok = all(r[1] for r in rs)
        fail += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {f}")
        for name, passed, note in rs:
            if not passed: print(f"    x {name}: {note}")
    print(f"G1 static: {len(files) - fail}/{len(files)} PASS")
    return 1 if fail or not files else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
