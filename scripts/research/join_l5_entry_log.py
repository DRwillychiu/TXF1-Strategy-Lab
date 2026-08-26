"""Join the L5 v19.9-R1 entry log to an MC12 trade report.

The .pla prints one line per fill to the MC output window:

    L5_ENTRY,Date,Time,EntryPrice,EpisodeID,EntryNo,BoxTop,BoxBtm

EntryNo is the flag: 1 = first entry inside the box, >= 2 = re-entry.
This script pairs those lines with the trade report on Date + Time and
reports what the re-entries actually earned.

Why a log and not a label: all 28 of L5's exit orders bind via
from Entry ("BL_Entry_Bot" / "BL_Entry_Mid"). Renaming an entry orphans
them and the position loses every stop. See the .pla header.

Usage
    python scripts/research/join_l5_entry_log.py --log OUT.txt --report R.xlsx
"""
import argparse
import collections
import re
import sys

FIELDS = ("date", "time", "price", "episode", "entry_no", "box_top", "box_btm")
LINE_RE = re.compile(r"L5_ENTRY\s*,\s*" + r"\s*,\s*".join([r"(-?[\d.]+)"] * 7))
ENTER_PREFIX = "進入"   # MC12 Chinese report: "enter"


def parse_log(path):
    """Return {(Date, Time): record} keyed in EasyLanguage number form."""
    out, dupes = {}, 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            m = LINE_RE.search(raw)
            if not m:
                continue
            rec = dict(zip(FIELDS, (float(g) for g in m.groups())))
            key = (int(rec["date"]), int(rec["time"]))
            if key in out:
                dupes += 1
            out[key] = rec
    if dupes:
        print("  WARNING: %d duplicate Date+Time keys." % dupes)
        print("           Scale-out splits one fill into two report rows and")
        print("           both inherit the same flag. Counts of re-entry")
        print("           TRADES will exceed re-entry EVENTS by that amount.")
    return out


def to_mc_date(dt):
    """datetime -> EasyLanguage Date (YYYMMDD, years since 1900)."""
    return (dt.year - 1900) * 10000 + dt.month * 100 + dt.day


def to_mc_time(tm):
    """time -> EasyLanguage Time (HHMM)."""
    return tm.hour * 100 + tm.minute


def load_report(path):
    """Return trades from an MC12 Trades List export.

    Column layout confirmed against a real export on 2026-08-26:
      0 trade no | 1 order no | 2 type | 3 signal | 4 date | 5 time
      6 price    | 7 qty      | 8 profit
    The profit sits on the ENTRY row, not the exit row.
    """
    try:
        import openpyxl
    except ImportError:
        sys.exit("openpyxl is required: pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.worksheets[0]
    rows = list(ws.iter_rows(min_row=4, values_only=True))
    wb.close()

    trades, cur = [], None
    for r in rows:
        if r[3] is None:
            continue
        kind = str(r[2]) if r[2] else ""
        if kind.startswith(ENTER_PREFIX):
            cur = {
                "id": r[0],
                "entry_label": str(r[3]),
                "entry_price": r[6],
                "qty": r[7],
                "pnl": float(r[8]) if isinstance(r[8], (int, float)) else None,
                "key": (to_mc_date(r[4]), to_mc_time(r[5])) if r[4] and r[5] else None,
                "exit_label": None,
            }
            trades.append(cur)
        elif cur is not None:
            cur["exit_label"] = str(r[3])
    return trades


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="MC output window text")
    ap.add_argument("--report", required=True, help="MC12 Trades List .xlsx")
    args = ap.parse_args()

    log = parse_log(args.log)
    trades = load_report(args.report)
    print("  log lines parsed : %d" % len(log))
    print("  trades in report : %d" % len(trades))
    if not log:
        sys.exit("  No L5_ENTRY lines found. Is Debug_Entry_Log = True?")

    hit = 0
    for tr in trades:
        rec = log.get(tr["key"])
        tr["entry_no"] = int(rec["entry_no"]) if rec else None
        tr["episode"] = int(rec["episode"]) if rec else None
        hit += 1 if rec else 0

    print("  joined           : %d" % hit)
    print("  unmatched        : %d" % (len(trades) - hit))
    if hit != len(trades):
        print("  STOP. Every trade must match a log line before any number")
        print("  below can be trusted. First few unmatched:")
        for tr in [x for x in trades if x["entry_no"] is None][:5]:
            print("      trade %s  key %s  %s" % (tr["id"], tr["key"], tr["entry_label"]))
        sys.exit(1)

    tot = sum(t["pnl"] for t in trades if t["pnl"] is not None)

    def block(name, rows):
        rows = [r for r in rows if r["pnl"] is not None]
        if not rows:
            print("  %-12s none" % name)
            return
        s = sum(r["pnl"] for r in rows)
        w = [r for r in rows if r["pnl"] > 0]
        print("  %-12s %3d trades   net %12s   win %5.1f%%   avg %10s   %6.1f%% of net"
              % (name, len(rows), format(int(s), ","),
                 100.0 * len(w) / len(rows), format(int(s / len(rows)), ","),
                 100.0 * s / tot if tot else 0.0))

    print("")
    print("  === first entry vs re-entry ===")
    block("first", [t for t in trades if t["entry_no"] == 1])
    block("re-entry", [t for t in trades if t["entry_no"] >= 2])
    print("  %-12s %3d trades   net %12s" % ("all", len(trades), format(int(tot), ",")))

    print("")
    print("  === by entry number inside the box ===")
    for n in sorted(set(t["entry_no"] for t in trades)):
        block("entry #%d" % n, [t for t in trades if t["entry_no"] == n])

    again = [t for t in trades if t["entry_no"] >= 2]
    print("")
    print("  === re-entry trades by exit label ===")
    for k, v in collections.Counter(t["exit_label"] for t in again).most_common():
        s = sum(t["pnl"] for t in again if t["exit_label"] == k and t["pnl"] is not None)
        print("      %-22s %3d   net %12s" % (k, v, format(int(s), ",")))

    print("")
    print("  Numbers come from the joined report, not the log alone.")
    print("  A duplicate-key warning above means re-entry TRADES exceed")
    print("  re-entry EVENTS; reconcile before quoting a count.")


if __name__ == "__main__":
    main()
