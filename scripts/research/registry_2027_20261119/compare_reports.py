"""Compare two MC strategy reports trade by trade (base version vs 2027-registry candidate).

Usage:  python scripts/research/registry_2027_20261119/compare_reports.py <base.xlsx> <candidate.xlsx>
PASS = same settings (except the strategy name), same net profit / max strategy drawdown / profit
factor, and every trade identical (entry time + price, exit time + price, exit order name, P&L).
Exit code 0 = PASS, 1 = FAIL. Uses tools/mc_report.py (MC Excel export, sheets 設定 / 策略分析 / 交易明細).
"""
import importlib.util, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
_s = importlib.util.spec_from_file_location("mc_report", ROOT / "tools" / "mc_report.py")
mc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(mc)

SKIP_SETTINGS = ("策略", "訊號", "名稱", "Name", "Signal", "Strategy", "報表", "Report", "日期", "Date")


def main(a_path, b_path):
    a, b = mc.read(a_path), mc.read(b_path)
    fails = []
    keys = set(a["settings"]) | set(b["settings"])
    for k in sorted(keys):
        if any(w in k for w in SKIP_SETTINGS): continue
        if a["settings"].get(k) != b["settings"].get(k):
            fails.append(f"setting {k}: {a['settings'].get(k)!r} != {b['settings'].get(k)!r}")
    for k in a["summary"]:
        if a["summary"][k] != b["summary"][k]:
            fails.append(f"summary {k}: {a['summary'][k]} != {b['summary'][k]}")
    ta, tb = a["trades"], b["trades"]
    if len(ta) != len(tb):
        fails.append(f"trade count {len(ta)} != {len(tb)}")
    for i, (x, y) in enumerate(zip(ta, tb), 1):
        if x != y:
            fails.append(f"trade {i}: {x} != {y}")
            if sum(f.startswith("trade ") for f in fails) >= 10: break
    print(f"base      {a_path}: {len(ta)} trades, {a['summary']}")
    print(f"candidate {b_path}: {len(tb)} trades, {b['summary']}")
    if ta: print(f"first trade {ta[0][0]}  last trade {ta[-1][0]}")
    print("[PASS] identical trade by trade" if not fails else "[FAIL]")
    for f in fails: print("    x " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
