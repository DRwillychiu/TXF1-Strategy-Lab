"""少數候選：2020 起連續資金曲線（驗證＋保留）、逐年、指數 43,000 等價回撤、前 10 大單是否保留。"""
from __future__ import annotations

import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as E  # noqa: E402
from common import CAP, micro_net, stats  # noqa: E402


def one(rule):
    res = E.s16.run(E.BARS, E.P, E.HOL, veto=E.make_veto(rule))
    ts = [t for t in res.trades if t.exit_dt.year >= 2020]
    pn = [micro_net(t) for t in ts]
    sc = [micro_net(t) * 43000 / t.entry_px for t in ts]
    by = defaultdict(list)
    for t in ts:
        by[t.exit_dt.year].append(micro_net(t))
    top = sorted(((round(micro_net(t)), t.entry_dt.isoformat(sep=" ")[:16]) for t in ts), reverse=True)[:10]
    return rule, stats(pn), stats(sc), {y: stats(v) for y, v in sorted(by.items())}, \
        sum(t.exit_label.startswith("SX_MA_QuickStop") for t in ts), top


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    rules = [("BASE",), ("VOL", 0.15), ("VOL", 0.20), ("VOL", 0.25), ("CB", 2, 5), ("CB", 2, 2)]
    with Pool(6, initializer=E.init, initargs=(str(d / "bars.pkl"),)) as pool:
        out = pool.map(one, rules)
    base_top = {x[1] for x in out[0][5]}
    for rule, s, sc, by, qs, top in out:
        kept = len(base_top & {x[1] for x in top})
        print(f"== {rule}  2020 起：{s['n']} 筆 淨利 {s['net']:,.0f} PF {s['pf']:.2f} 回撤 {s['mdd']:,.0f}"
              f"（{s['mdd'] / CAP * 100:.1f}%）最長連虧 {s['streak']} 快停 {qs}｜指數 43,000 等價回撤 {sc['mdd']:,.0f}"
              f"（{sc['mdd'] / CAP * 100:.1f}%）｜基準前 10 大單保留 {kept}/10")
        print("   " + "  ".join(f"{y}:{v['n']}筆 {v['net']:,.0f}" for y, v in by.items()))


if __name__ == "__main__":
    main()
