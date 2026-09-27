#!/usr/bin/env python3
"""G2 settings gate (v2, 2026-09-27).

v1 (verify_switches.py) compared the .pla defaults with a hand-typed table.
That table was my memory: when I typed 28 it passed 28, when I typed 34 it
passed 34. It verified "file == what I typed", not "file == what was run".

v2 takes the expected values from the MC report itself (sheet 設定), which is
the only record of what actually produced the numbers.

Usage
  python verify_settings.py <strategy.pla|.txt> <mc_report.xlsx>
      S1  every input default in the file == the value in the report
      S2  a switch whose TRUE branch the Python engine never modelled is ON
      S3  comment tags still carry an older version number
  python verify_settings.py --compare <report_a.xlsx> <report_b.xlsx>
      S5  two reports are comparable only if start date, end date, capital,
          slippage, commission and bar compression are identical
exit 0 = PASS, 1 = FAIL
"""
import re, sys
import openpyxl

UNMODELLED = {"Box_New_On", "Qual_New_On"}
RUN_KEYS = ("開始日期", "結束日期", "原始資本", "滑價", "佣金", "壓縮")

def report_settings(path):
    ws = openpyxl.load_workbook(path, data_only=True)["設定"]
    rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    params, run, name, in_params = {}, {}, None, False
    for r in rows:
        k = str(r[0]).strip(); v = r[1] if len(r) > 1 else None
        if k == "設定": in_params = True; continue
        if in_params and v is None and name is None: name = k; continue
        if k == "商品名稱": in_params = False
        if in_params and v is not None: params[k] = v
        elif v is not None: run[k] = v
    return name, params, run

def strip_comments(text):
    """PowerLanguage comments are { ... } and // ... ; strip them BEFORE looking
    for the ';' that ends an inputs block, or a ';' inside a comment ends it early
    (v2.0 bug: only 9 of 53 inputs were read)."""
    out, depth = [], 0
    for ch in text:
        if ch == "{": depth += 1; continue
        if ch == "}" and depth: depth -= 1; continue
        if depth == 0: out.append(ch)
    return re.sub(r"//[^\n]*", " ", "".join(out))

def pla_inputs(text):
    code = strip_comments(text)
    got = {}
    for m in re.finditer(r"\binputs?\s*:(.*?);", code, re.S | re.I):
        for k, v in re.findall(r"([A-Za-z_]\w*)\s*\(\s*([-\w.\"]+)\s*\)", m.group(1)):
            got.setdefault(k, v)
    return got

def norm(v):
    s = str(v).strip().strip('"').lower()
    if s in ("true", "false"): return s
    try: return f"{float(s):g}"
    except ValueError: return s

def check_file(pla, rep):
    text = open(pla, encoding="ascii", errors="replace").read()
    got = pla_inputs(text)
    name, want, _ = report_settings(rep)
    fails, warns = [], []
    for k, v in want.items():
        if k not in got: fails.append(f"S1 in report, missing in file: {k} = {v}")
        elif norm(got[k]) != norm(v): fails.append(f"S1 {k}: file={got[k]}  report={v}")
    for k in got:
        if k not in want: warns.append(f"S1 in file, not in report: {k} = {got[k]} (report from an older build?)")
    for k in UNMODELLED:
        if norm(got.get(k, "false")) == "true":
            fails.append(f"S2 {k} = true: branch never modelled in Python, quoted numbers invalid")
    ver = re.search(r"Version\s*:\s*v(\d+)", text)
    if ver:
        cur = int(ver.group(1))
        for old in sorted({int(x) for x in re.findall(r"\{\s*v(\d+)\s*[:(]", text)}):
            if old != cur and old >= 14:
                warns.append(f"S3 comments still tagged v{old}, file is v{cur}")
    tag = pla.split("/")[-1]
    print(f"  report strategy name: {name}   params in report: {len(want)}   inputs in file: {len(got)}")
    for w in warns: print(f"[WARN] {tag}: {w}")
    for f in fails: print(f"[FAIL] {tag}: {f}")
    if not fails: print(f"[PASS] {tag}: all {len(want)} report parameters match the file defaults")
    return 1 if fails else 0

def compare(a, b):
    _, _, ra = report_settings(a); _, _, rb = report_settings(b)
    fails = [f"S5 {k}: A={ra.get(k)}  B={rb.get(k)}" for k in RUN_KEYS if str(ra.get(k)) != str(rb.get(k))]
    for f in fails: print("[FAIL] " + f)
    if not fails: print("[PASS] S5 the two reports share period, capital, slippage, commission and bars")
    return 1 if fails else 0

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    sys.exit(check_file(sys.argv[1], sys.argv[2]))
