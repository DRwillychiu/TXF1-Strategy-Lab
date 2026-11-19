"""基準（260825 原樣）全歷史：逐段、逐年、出場類型、回撤組成、連虧理論與蒙地卡羅。"""
from __future__ import annotations

import csv
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CAP, LIMIT_D3, seg_of, stats  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    T = list(csv.DictReader(open(d / "trades_base.csv", encoding="utf-8")))
    for t in T:
        t["p"] = float(t["net_micro2"])
        t["seg"] = seg_of(t["exit_dt"])
        t["qs"] = t["exit_label"].startswith("SX_MA_QuickStop")
        t["px"] = float(t["entry_px"])

    def line(name, ts):
        s = stats([t["p"] for t in ts])
        print(f"{name:<26}{s['n']:>5}{s['net']:>11,.0f}{s['pf']:>7.2f}{s['mdd']:>10,.0f}"
              f"{s['mdd'] / CAP * 100:>7.1f}%{s['streak']:>5}{s['win'] * 100:>7.1f}%")
    print("== 微台 2 口實際規模（含滑價、手續費 12、期交稅）")
    print(f"{'區段':<24}{'筆數':>5}{'淨利':>11}{'PF':>7}{'平倉回撤':>10}{'佔資金':>8}{'連虧':>5}{'勝率':>8}")
    for sg in ("design", "valid", "hold"):
        line(sg, [t for t in T if t["seg"] == sg])
    line("all", T)
    by = defaultdict(list)
    for t in T:
        by[t["exit_dt"][:4]].append(t)
    for y in sorted(by):
        line(y, by[y])

    # 以「目前指數水準」重算點數風險：每筆點數 × 2 口 × 10，按 43,000 / 進場價縮放（前瞻用）
    scaled = [t["p"] * 43000 / t["px"] for t in T]
    s = stats(scaled)
    print(f"\n== 指數水準調到 43,000 的等價（前瞻風險）：全期回撤 {s['mdd']:,.0f}（{s['mdd'] / CAP * 100:.1f}%）"
          f"　淨利 {s['net']:,.0f}")
    for sg in ("design", "valid", "hold"):
        ss = stats([t["p"] * 43000 / t["px"] for t in T if t["seg"] == sg])
        print(f"   {sg}: 回撤 {ss['mdd']:,.0f}（{ss['mdd'] / CAP * 100:.1f}%）淨利 {ss['net']:,.0f} 筆 {ss['n']}")

    # 出場類型
    print("\n== 出場類型（全期，微台 2 口）")
    g = defaultdict(list)
    for t in T:
        g[t["exit_label"][:19]].append(t["p"])
    for k, v in sorted(g.items(), key=lambda kv: sum(kv[1])):
        print(f"  {k:<22}{len(v):>4}{sum(v):>11,.0f}  勝率 {sum(x > 0 for x in v) / len(v) * 100:5.1f}%")

    # 回撤組成：最深回撤區間（峰 → 谷）裡，小虧（快速停損）佔多少
    def worst_dd(ts):
        eq = peak = 0.0; pi = 0; best = (0.0, 0, 0)
        for k, t in enumerate(ts):
            eq += t["p"]
            if eq > peak:
                peak, pi = eq, k + 1
            if eq - peak < best[0]:
                best = (eq - peak, pi, k + 1)
        return best
    print("\n== 回撤組成（每段最深回撤：峰 → 谷之間的交易）")
    for sg in ("design", "valid", "hold", "all"):
        ts = T if sg == "all" else [t for t in T if t["seg"] == sg]
        dd, a, b = worst_dd(ts)
        w = ts[a:b]
        qs = sum(t["p"] for t in w if t["qs"])
        oth = sum(t["p"] for t in w if not t["qs"] and t["p"] < 0)
        win = sum(t["p"] for t in w if t["p"] > 0)
        print(f"  {sg:<7} 回撤 {dd:>9,.0f}　{w[0]['entry_dt'][:10] if w else ''}～{w[-1]['exit_dt'][:10] if w else ''}　"
              f"{len(w)} 筆：快速停損 {sum(t['qs'] for t in w)} 筆 {qs:,.0f}／其他虧損 {oth:,.0f}／獲利 {win:,.0f}"
              f"　→ 快速停損佔總虧損 {qs / (qs + oth) * 100 if qs + oth else 0:.0f}%")

    # 連虧理論：獨立假設下，n 筆、敗率 q 的最長連虧期望 ≈ log(n(1-q)) / log(1/q)
    print("\n== 連虧：實際 vs 獨立隨機（同勝率）")
    for sg in ("design", "valid", "all"):
        ts = T if sg == "all" else [t for t in T if t["seg"] == sg]
        pn = [t["p"] for t in ts]
        q = sum(x < 0 for x in pn) / len(pn)
        theo = math.log(len(pn) * (1 - q)) / math.log(1 / q)
        rnd = random.Random(7)
        sims = []
        for _ in range(2000):
            x = pn[:]
            rnd.shuffle(x)
            sims.append(stats(x)["streak"])
        sims.sort()
        print(f"  {sg:<7} 敗率 {q:.2f}　實際最長連虧 {stats(pn)['streak']}　理論 {theo:.1f}　"
              f"洗牌中位 {sims[1000]}、95% {sims[1900]}　→ 實際{'高於' if stats(pn)['streak'] > sims[1900] else '在'}隨機範圍{'外' if stats(pn)['streak'] > sims[1900] else '內'}")

    # 蒙地卡羅：用驗證期（2020–8/22）的每筆損益，抽一年份（約 30 筆）連續序列 → P(回撤 > 15%)
    print("\n== 蒙地卡羅（區塊自助抽樣，區塊 5 筆）：未來 12 個月回撤超過 15%（21,030）的機率")
    for sg, scale in (("valid", False), ("valid", True), ("all", True)):
        ts = T if sg == "all" else [t for t in T if t["seg"] == sg]
        pn = [t["p"] * (43000 / t["px"] if scale else 1) for t in ts]
        rnd = random.Random(11)
        hits = 0; mdds = []
        n_year = 60 if scale else 30
        for _ in range(5000):
            seq = []
            while len(seq) < n_year:
                k = rnd.randrange(0, len(pn) - 5)
                seq += pn[k:k + 5]
            m = stats(seq[:n_year])["mdd"]
            mdds.append(m)
            hits += m < -LIMIT_D3
        mdds.sort()
        print(f"  {sg}{'（指數 43,000 等價）' if scale else ''} 每年 {n_year} 筆：P(>15%) = {hits / 5000:.1%}　"
              f"回撤中位 {mdds[2500]:,.0f}、5% 最壞 {mdds[250]:,.0f}")


if __name__ == "__main__":
    main()
