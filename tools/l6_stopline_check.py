"""L6 停單線檢查（Willy 11/19 定案；人工停單：MC 的 Manual_Kill_Switch 改 true）。

停單線：
  1. L6 自己的平倉權益，從最高點回落 ≥ 18,000 → 停 L6 檢討
  2. L6 連續虧損 ≥ 10 筆 → 停 L6 檢討
  3. 空方帳戶（L2＋L4＋L6）累計損益 ≤ −22,500（起始資金 150,000 的 15%，從起始資金算）→ 全部停單檢討
另外在到達線的 80% 時先預警。

輸入：MC Trades List 轉成的 CSV（欄位 exit_dt, net_ntd；net_ntd 是 MC 口徑＝大台），或已是微台淨額的 CSV（欄位 exit_dt, net）。
MC 口徑換微台：÷20（同 tests/fixtures 的報表格式）。只算 --start 以後平倉的交易（實戰起算日）。

Usage:
  python tools/l6_stopline_check.py --start 2026-11-23 --l6 L6.csv [--other L2.csv --other L4.csv] [--notify]
結束碼：0 正常、1 預警、2 碰線。
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

DD_STOP, STREAK_STOP, ACCT_STOP = 18_000, 10, 22_500
WARN = 0.8


def read(path: str, start: str) -> list[tuple[str, float]]:
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["exit_dt"][:10] < start:
                continue
            if "net" in r and r["net"] != "":
                v = float(r["net"])
            else:   # MC 口徑 → 微台 2 口淨額：÷20，再扣期交稅與手續費（同研究的 micro_net）
                v = float(r["net_ntd"]) / 20 - (float(r["entry_px"]) + float(r["exit_px"])) * 10 * 0.00002 * 2 - 12 * 2 * 2
            out.append((r["exit_dt"], v))
    return sorted(out)


def check(l6: list[tuple[str, float]], others: list[list[tuple[str, float]]]) -> dict:
    eq = pk = dd = 0.0; run = streak = 0
    for _, v in l6:
        eq += v; pk = max(pk, eq); dd = min(dd, eq - pk)
        run = run + 1 if v < 0 else 0
        streak = max(streak, run)
    cur_dd = eq - pk
    acct = eq + sum(v for o in others for _, v in o)
    level = 0
    msgs = []
    for name, val, lim in (("L6 從最高點回落", -cur_dd, DD_STOP), ("L6 目前連虧", run, STREAK_STOP),
                           ("空方帳戶比起始資金少", -acct, ACCT_STOP)):
        if val >= lim:
            level = 2; msgs.append(f"🔴 {name} {val:,.0f}（線 {lim:,}）→ 停單")
        elif val >= lim * WARN:
            level = max(level, 1); msgs.append(f"🟡 {name} {val:,.0f}（線 {lim:,}，已到 {val / lim * 100:.0f}%）")
    return dict(level=level, l6_net=eq, l6_dd=cur_dd, l6_max_dd=dd, l6_run=run, l6_max_streak=streak, acct=acct, msgs=msgs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--l6", required=True)
    ap.add_argument("--other", action="append", default=[])
    ap.add_argument("--notify", action="store_true")
    a = ap.parse_args(argv)
    r = check(read(a.l6, a.start), [read(p, a.start) for p in a.other])
    head = {0: "🟢 L6 停單線正常", 1: "🟡 L6 停單線預警", 2: "🔴 L6 碰到停單線"}[r["level"]]
    lines = [head, f"L6 累計 {r['l6_net']:,.0f}、從最高點回落 {-r['l6_dd']:,.0f}／18,000、目前連虧 {r['l6_run']}／10；"
                   f"空方帳戶累計 {r['acct']:,.0f}（停單線 −22,500）"] + r["msgs"]
    if r["level"] == 2:
        lines.append("你要做的：MC 把 Manual_Kill_Switch 改 true，再檢討")
    print("\n".join(lines))
    if a.notify and r["level"] > 0:
        root = Path(__file__).resolve().parents[1]
        import os
        ops = os.environ.get("OPS_STATE_ROOT", str(Path.home() / "ops-state"))
        subprocess.run([sys.executable, str(Path(ops) / "tools/notify.py"), "send", "\n".join(lines),
                        "--tier", "P0" if r["level"] == 2 else "P1", "--thread", "L6停單線"], cwd=root, check=False)
    return r["level"]


if __name__ == "__main__":
    sys.exit(main())
