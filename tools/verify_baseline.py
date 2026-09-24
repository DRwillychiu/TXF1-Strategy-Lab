"""G3 backtest-baseline gate. Compares a new MC report with an approved baseline over their common period.
Usage: python tools/verify_baseline.py <new_report.xlsx> <baseline.json>      exit 0 = PASS, 1 = FAIL"""
import json, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from mc_report import read

MUST_MATCH = ("開始日期", "滑價", "原始資本", "壓縮")

def main(new_path, base_path):
    new, base = read(new_path), json.load(open(base_path, encoding="utf-8"))
    fails = []
    for k in MUST_MATCH:
        a, b = base["settings"].get(k), new["settings"].get(k)
        if a is not None and str(a) != str(b): fails.append(f"setting {k}: baseline={a}  new={b}")
    bp, np_ = base["settings"].get("策略參數"), new["settings"].get("策略參數")
    if bp and np_ and bp != np_: fails.append(f"setting 策略參數 differ:\n      baseline={bp}\n      new     ={np_}")
    lo = max(t[0] for t in (base["trades"][:1] + new["trades"][:1]))
    hi = min(str(base["settings"].get("結束日期")), str(new["settings"].get("結束日期")))
    key = lambda t: (t[0], t[1], t[2], t[3], t[4], t[5])
    B = {key(t) for t in base["trades"] if lo <= t[0] <= hi}
    N = {key(t) for t in new["trades"] if lo <= t[0] <= hi}
    only_b, only_n = sorted(B - N), sorted(N - B)
    if only_b or only_n:
        fails.append(f"trades in common period {lo[:10]}..{hi[:10]}: {len(B & N)} identical, {len(only_b)} only in baseline, {len(only_n)} only in new")
        for t in only_b[:5]: fails.append(f"      - baseline {t[0][:16]} {t[4]} {t[5]:,.0f}")
        for t in only_n[:5]: fails.append(f"      + new      {t[0][:16]} {t[4]} {t[5]:,.0f}")
    print(f"[{'FAIL' if fails else 'PASS'}] G3 baseline  {new_path}  vs  {base_path}")
    for f in fails: print("    x " + f)
    if not fails: print(f"    {len(B & N)} trades identical in common period; settings match")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
