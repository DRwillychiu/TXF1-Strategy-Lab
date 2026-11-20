"""L1-L5 V0.1.0 (development) = live V1.1.0 + settlement deferral table (Willy 11/20: 「把 2027-09-16 結算日缺口先修掉」).

The five .pla call a day "settlement" only when it is the 3rd Wednesday (day 15-21). TAIFEX moves final
settlement to the next business day when that Wednesday is closed; 2027-09-15 (Mid-Autumn) is closed, so the
2027-09 contract settles Thu 2027-09-16 and V1.1.0 would neither block entries nor flatten at 12:30 that day.

ONE change per file, the same two lines L6 V0.1.0 uses (scripts/research/s16_streak_20261118/build_l6_v010.py):
    if Date = 1270915 then v_Settlement_Day = False;  { Settle_Skip ... }
    if Date = 1270916 then v_Settlement_Day = True;   { Settle_Add  ... }
placed right after the 3rd-Wednesday rule. The table is computed from data/taifex_market_closures.json for the
years from 2027 (live period) to the registry end; earlier years are left as in V1.1.0 so the history is trade by
trade the same as V1.1.0 (2023-01-30 and 2026-02-23 were deferred too; the MC reports keep the old rule there).
Header: title + one block replacing the "Known gap" line. Output ASCII with the base's line ending (LF),
.txt = .pla.

  python -I scripts/research/settle_table_20261120/build_v010_l1_l5.py
"""
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLOSURES = ROOT / "data/taifex_market_closures.json"
FIRST_YEAR = 2027          # live period starts here; earlier deferrals stay as in V1.1.0 (MC reports)
LAST_YEAR = 2027           # Registry_Valid_Until 1271231
NAMES = ["L1_TrendLong", "L2_TrendShort", "L3_ConsolidationLong", "L4_ConsolidationShort", "L5_BreakoutLong"]
BASE, NEW = "v1.1.0", "v0.1.0"

RULE = re.compile(r"^v_Settlement_Day = \(\s*DayOfWeek\(\s*Date\s*\)\s*=\s*3\s*\) and\n"
                  r"[ ]+\(\s*DayOfMonth\(\s*Date\s*\)\s*>=\s*15\s*\) and\n"
                  r"[ ]+\(\s*DayOfMonth\(\s*Date\s*\)\s*<=\s*21\s*\);\n", re.M)
TITLE = re.compile(r"^(  L\d [A-Z ]+\(Adaptive Farmer\))  -  V1\.1\.0  \(2026-11-19; (logic = [^)]+)\)$", re.M)
GAP = "  Known gap    : 2027-09-16 settlement (moved from Wed 9/15) is not flattened.\n"
NOTE = ("  V0.1.0 DEV   : not live. ONE change on top of V1.1.0: settlement deferral\n"
        "                 table - a closed 3rd Wednesday moves settlement to the next\n"
        "                 business day (2027-09-15 -> 2027-09-16, TAIFEX 116-yr calendar).\n"
        "                 Years before 2027 are left as in V1.1.0: same history trades.\n")


def deferrals(first=FIRST_YEAR, last=LAST_YEAR):
    """[(closed 3rd Wednesday, settlement day)] from the closures registry, years first..last."""
    closed = {x["date"] for x in json.loads(CLOSURES.read_text(encoding="utf-8"))["closed_weekdays"]}
    out = []
    for y in range(first, last + 1):
        for m in range(1, 13):
            wed = next(dt.date(y, m, k) for k in range(15, 22) if dt.date(y, m, k).weekday() == 2)
            if str(wed) in closed:
                nxt = wed + dt.timedelta(1)
                while nxt.weekday() > 4 or str(nxt) in closed:
                    nxt += dt.timedelta(1)
                out.append((wed, nxt))
    return out


def mc(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def table(defer):
    out = ["{ ---- Settlement deferral table (V0.1.0): 3rd Wed closed -> next business day ---- }"]
    for w, n in defer:
        out.append(f"if Date = {mc(w)} then v_Settlement_Day = False;  {{ Settle_Skip {w} closed }}")
        out.append(f"if Date = {mc(n)} then v_Settlement_Day = True;   {{ Settle_Add  {n} deferred }}")
    return "\n".join(out) + "\n"


def path(name, ver):
    code = name.split("_")[0]
    return ROOT / "strategies/research" / name / f"{code}_{ver}" / f"{name}_{ver}.pla"


def build(name, defer):
    raw = path(name, BASE).read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"           # keep the base's line ending (V1.1.0 files are LF)
    t = raw.decode("ascii").replace("\r\n", "\n")
    assert len(RULE.findall(t)) == 1, f"{name}: 3rd-Wednesday rule found {len(RULE.findall(t))} times"
    assert "Settle_Add" not in t, f"{name}: base already has a deferral table"
    t = RULE.sub(lambda m: m.group(0) + table(defer), t)
    t, n = TITLE.subn(r"\1  -  V0.1.0 DEV  (2026-11-20; \2)", t)
    assert n == 1, f"{name}: title found {n} times"
    assert t.count(GAP) == 1, f"{name}: Known gap line found {t.count(GAP)} times"
    t = t.replace(GAP, NOTE)
    head_end = t.index("}") + 1                        # header comment only: the rule text there
    t = t[:head_end].replace("settlement Wednesday", "settlement day") + t[head_end:]
    out = t.replace("\n", eol).encode("ascii")
    p = path(name, NEW)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(out)
    p.with_suffix(".txt").write_bytes(out)
    return p, len(t.split("\n")) - 1


def main():
    defer = deferrals()
    assert defer == [(dt.date(2027, 9, 15), dt.date(2027, 9, 16))], defer
    for name in NAMES:
        p, n = build(name, defer)
        print(f"{p.relative_to(ROOT).as_posix()}  {n} lines")


if __name__ == "__main__":
    main()
