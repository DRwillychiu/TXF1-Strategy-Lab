"""候選規則用完整引擎（veto 掛鉤）重跑 2000–2026，依預先登記的切分評分。

規則族：
  CB(k, d)   連虧熔斷：最近 k 筆實際交易全虧 → 從最後一筆出場起 d 個交易日內不接新的死亡交叉
  MA60(x)    日線濾網：前一日收盤高於 60 日均線超過 x% 時不放空（設計期唯一 p<0.05 的因子，BH 未通過）
  VOL(x)     波動濾網：ATR/價格 低於 x% 不進場（設計期與驗證期方向相反，只作對照）
"""
from __future__ import annotations

import csv
import pickle
import sys
from bisect import bisect_left
from datetime import timedelta
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
from common import CAP, micro_net, seg_of, stats  # noqa: E402

BARS = None
P = s16.pla_params(s16.PLA_260825)
HOL = s16.holiday_tail(s16.PLA_260825)


def init(path):
    global BARS, DAYS, DCLOSE, NATR
    BARS = pickle.loads(Path(path).read_bytes())
    dc = {}
    for b in BARS:
        dc[b.dt.date()] = b.c
    DAYS = sorted(dc)
    DCLOSE = [dc[d] for d in DAYS]
    C = [b.c for b in BARS]; H = [b.h for b in BARS]; L = [b.l for b in BARS]
    NATR = [0.0] * len(C)
    s = 0.0
    trs = [H[0] - L[0]] + [max(H[i], C[i - 1]) - min(L[i], C[i - 1]) for i in range(1, len(C))]
    for i in range(len(C)):
        s += trs[i] - (trs[i - 14] if i >= 14 else 0)
        NATR[i] = s / min(i + 1, 14) / C[i] * 100


def make_veto(rule):
    kind = rule[0]
    if kind == "BASE":
        return None
    if kind == "CB":
        k, d = rule[1], rule[2]

        def v(i, trades):
            if len(trades) < k:
                return False
            last = trades[-k:]
            if all(t.net_ntd < 0 for t in last):
                return (BARS[i].dt.date() - last[-1].exit_dt.date()).days < d
            return False
        return v
    if kind == "MA60":
        x = rule[1]

        def v(i, trades):
            kk = bisect_left(DAYS, BARS[i].dt.date())
            if kk < 60:
                return False
            prev = DCLOSE[kk - 60:kk]
            return (prev[-1] / (sum(prev) / 60) - 1) * 100 > x
        return v
    if kind == "VOL":
        x = rule[1]
        return lambda i, trades: NATR[i] < x
    raise ValueError(rule)


def evaluate(rule):
    res = s16.run(BARS, P, HOL, veto=make_veto(rule))
    out = {"rule": rule}
    for sg in ("design", "valid", "hold"):
        ts = [t for t in res.trades if seg_of(t.exit_dt.isoformat()) == sg]
        s = stats([micro_net(t) for t in ts])
        s["qs"] = sum(t.exit_label.startswith("SX_MA_QuickStop") for t in ts)
        s["top10"] = sorted((round(micro_net(t)) for t in ts), reverse=True)[:10]
        out[sg] = s
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    rules = [("BASE",)]
    rules += [("CB", k, dd) for k in (2, 3, 4, 5, 6) for dd in (1, 2, 3, 5, 10)]
    rules += [("MA60", x) for x in (0.0, 2.0, 4.0, 6.0, 8.0)]
    rules += [("VOL", x) for x in (0.15, 0.20, 0.25)]
    with Pool(6, initializer=init, initargs=(str(d / "bars.pkl"),)) as pool:
        results = pool.map(evaluate, rules)
    base = results[0]
    hdr = (f"{'規則':<14}" + "".join(f"{sg + ' 筆/淨/回撤%/連虧/快停':>40}" for sg in ("design", "valid", "hold")))
    print(hdr)
    rows = []
    for r in results:
        cells = []
        for sg in ("design", "valid", "hold"):
            s = r[sg]
            cells.append(f"{s['n']:>4}/{s['net']:>9,.0f}/{s['mdd'] / CAP * 100:>6.1f}%/{s['streak']:>3}/{s['qs']:>4}")
        print(f"{str(r['rule']):<14}" + "".join(f"{c:>40}" for c in cells))
        v, b = r["valid"], base["valid"]
        rows.append(dict(rule=str(r["rule"]),
                         **{f"{sg}_{k}": r[sg][k] for sg in ("design", "valid", "hold")
                            for k in ("n", "net", "mdd", "streak", "qs", "pf")},
                         valid_top10_kept=int(sorted(v["top10"]) == sorted(b["top10"]))))
    with open(d / "evaluate.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
