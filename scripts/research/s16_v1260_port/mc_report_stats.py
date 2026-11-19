"""MC 報表的官方摘要＋由 MC 交易明細算出的逐年、分段、最長連虧（全部是 MC 數字，不是 Python 推論）。

Usage: python -I scripts/research/s16_v1260_port/mc_report_stats.py <MC報表.xls> <trades.csv>
"""
import csv
import os
import shutil
import sys
import tempfile
from collections import defaultdict

import openpyxl

KEYS = ["淨利", "毛利", "毛損", "獲利因子", "調整獲利因子", "最大策略虧損", "最大策略虧損 (%)",
        "夏普比率", "索丁諾比率", "年報酬率", "初始資本報酬"]


def fix(s):
    if isinstance(s, str):
        try:
            return s.encode("latin-1").decode("big5")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def summary(path):
    tmp = os.path.join(tempfile.mkdtemp(), "r.xlsx")
    shutil.copyfile(path, tmp)
    ws = openpyxl.load_workbook(tmp, read_only=True, data_only=True).worksheets[0]
    out = {}
    for row in ws.iter_rows(values_only=True):
        k = fix(row[0]).strip() if row and isinstance(row[0], str) else None
        if k in KEYS and k not in out:
            out[k] = row[1]
    return out


def seg(trades):
    net = sum(t[1] for t in trades)
    gp = sum(t[1] for t in trades if t[1] > 0)
    gl = -sum(t[1] for t in trades if t[1] < 0)
    eq = peak = dd = 0
    run = longest = 0
    for _, p in trades:
        eq += p
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
        run = run + 1 if p < 0 else 0
        longest = max(longest, run)
    wins = sum(1 for t in trades if t[1] > 0)
    pf = gp / gl if gl else float("inf")
    return len(trades), net, pf, dd, longest, (wins / len(trades) * 100 if trades else 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    s = summary(sys.argv[1])
    print("== MC 官方摘要")
    for k in KEYS:
        print(f"  {k}: {s.get(k)}")
    tr = [(r["exit_dt"], float(r["net_ntd"])) for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))]
    tr.sort()
    hdr = f"{'區段':<22}{'筆數':>5}{'淨利':>12}{'PF':>7}{'平倉回撤':>11}{'最長連虧':>6}{'勝率%':>7}"
    print("\n== 由 MC 交易明細計算（依平倉日）\n" + hdr)
    by = defaultdict(list)
    for t in tr:
        by[t[0][:4]].append(t)

    def line(name, ts):
        n, net, pf, dd, lg, w = seg(ts)
        print(f"{name:<22}{n:>5}{net:>12,.0f}{pf:>7.2f}{dd:>11,.0f}{lg:>6}{w:>7.1f}")
    for y in sorted(by):
        line(y, by[y])
    line("全期", tr)
    line("至 2026-08-07（舊錨點窗）", [t for t in tr if t[0] <= "2026-08-07 23:59"])
    line("2026-08-08 起（新資料）", [t for t in tr if t[0] > "2026-08-07 23:59"])
    line("2026-08-23 起（定版後）", [t for t in tr if t[0] >= "2026-08-23"])


if __name__ == "__main__":
    main()
