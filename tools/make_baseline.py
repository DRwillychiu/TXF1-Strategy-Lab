"""Create a G3 baseline from an approved MC report.  Usage: python tools/make_baseline.py <report.xlsx> <out.json>"""
import json, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from mc_report import read
r = read(sys.argv[1]); r["source"] = sys.argv[1]
json.dump(r, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(f"baseline written: {sys.argv[2]}  trades={len(r['trades'])}  net={r['summary'].get('淨利')}")
