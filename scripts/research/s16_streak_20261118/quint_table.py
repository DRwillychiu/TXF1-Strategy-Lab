"""指定因子的五分位表（切點取自設計期），設計期與驗證期並列：快停率、平均報酬、筆數。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import factors as F  # noqa: E402
import csv  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    feats = sys.argv[2].split(",")
    ev = list(csv.DictReader(open(d / "events.csv", encoding="utf-8")))
    tr = {int(t["sig_i"]): t for t in csv.DictReader(open(d / "trades_base.csv", encoding="utf-8"))}
    rows = []
    for e in ev:
        i = int(e["i"])
        if i not in tr:
            continue
        t = tr[i]
        r = dict(seg=F.seg_of(e["dt"]), qs=int(t["exit_label"].startswith("SX_MA_QuickStop")),
                 ret=float(t["net_micro2"]) / (float(t["entry_px"]) * 20) * 100, p=float(t["net_micro2"]))
        for f in feats:
            r[f] = float(e[f]) if e[f] not in ("", "nan") else None
        rows.append(r)
    for f in feats:
        D = [r for r in rows if r["seg"] == "design" and r[f] is not None]
        V = [r for r in rows if r["seg"] == "valid" and r[f] is not None]
        cuts, _ = F.quint([r[f] for r in D], [0] * len(D))
        print(f"== {f} 切點 {[round(c, 4) for c in cuts]}")
        for name, S in (("設計", D), ("驗證", V)):
            bins = [[] for _ in range(5)]
            for r in S:
                bins[sum(r[f] >= c for c in cuts)].append(r)
            print("  " + name + "  " + "  ".join(
                f"Q{q + 1} n={len(b):>3} 快停 {sum(r['qs'] for r in b) / len(b):.0%} 報酬 {sum(r['ret'] for r in b) / len(b):+.3f}% 淨 {sum(r['p'] for r in b):>8,.0f}"
                if b else f"Q{q + 1} -" for q, b in enumerate(bins)))


if __name__ == "__main__":
    main()
