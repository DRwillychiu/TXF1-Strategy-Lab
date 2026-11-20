"""研究 A：跨月價差回歸（規則見 docs/research/calspread_criteria_draft_20261120.md 定案補充）。
Usage: python -I scripts/research/calspread_20261120/research_a.py <TXF1 1分.txt> <TXF2 1分.txt> <out.md> [起始年=2020]
"""
import sys, statistics as st
from collections import defaultdict
sys.path.insert(0, __file__.rsplit("research_a.py", 1)[0])
from profile_spread import load, dkey

TAX = 2e-5
H = 3

def build(f1, f2, y0):
    a, b = load(f1, y0), load(f2, y0)
    last1, cnt1 = defaultdict(str), defaultdict(int)
    for (d, t) in a:
        last1[d] = max(last1[d], t); cnt1[d] += 1
    days = sorted(cnt1, key=dkey)
    settle = {d for d in days if last1[d] <= "13:30" and cnt1[d] > 200}
    bars = defaultdict(list)
    for (d, t), (c2, v2) in b.items():
        if t <= "13:30" and (d, t) in a and v2 > 0 and a[(d, t)][1] > 0:
            bars[d].append((t, c2 - a[(d, t)][0], a[(d, t)][0]))
    for d in bars:
        bars[d].sort()
    cycles, cur = [], []
    for d in days:
        if d in settle:
            if cur:
                cycles.append(cur)
            cur = []
        else:
            cur.append(d)
    return bars, cycles

def run(bars, cycles, N, K, slip, hold=H):
    trades = []
    for D in cycles:
        pos = None
        for i, d in enumerate(D):
            if i < N:
                continue
            hist = [s for dd in D[i - N:i] for (_, s, _) in bars.get(dd, [])]
            day = bars.get(d, [])
            if len(hist) < 50 or not day:
                continue
            med = st.median(hist)
            sig = 1.4826 * max(st.median([abs(x - med) for x in hist]), 2.0)
            pend = None
            for (t, s, p1) in day:
                if pend == "in":
                    pos = dict(side=side, s=s, p=p1, i=i, d=d, t=t); pend = None; continue
                if pend == "out":
                    trades.append(close(pos, s, p1, d, slip)); pos = None; pend = None; continue
                if pos is None:
                    z = (s - med) / sig
                    if abs(z) >= K:
                        side = -1 if z > 0 else 1; pend = "in"
                elif (pos["side"] < 0 and s <= med) or (pos["side"] > 0 and s >= med):
                    pend = "out"
            if pos and (pend == "out" or i - pos["i"] >= hold or i == len(D) - 1):
                t, s, p1 = day[-1]
                trades.append(close(pos, s, p1, d, slip)); pos = None
        if pos:  # 週期最後幾天沒有資料時的保險
            trades.append(close(pos, pos["s"], pos["p"], pos["d"], slip))
    return trades

def close(pos, s, p1, d, slip):
    gross = pos["side"] * (s - pos["s"])
    cost = TAX * 2 * (pos["p"] + p1) + slip
    return dict(d=pos["d"], x=d, side=pos["side"], gross=gross, net=gross - cost)

def summ(tr):
    if not tr:
        return dict(n=0, win=0, avg_g=0, avg=0, tot=0, dd=0, worst=0)
    net = [t["net"] for t in tr]
    eq = pk = dd = 0.0
    for x in net:
        eq += x; pk = max(pk, eq); dd = max(dd, pk - eq)
    return dict(n=len(tr), win=sum(x > 0 for x in net) / len(tr) * 100, avg_g=st.mean(t["gross"] for t in tr),
                avg=st.mean(net), tot=sum(net), dd=dd, worst=min(net))

def main():
    f1, f2, out = sys.argv[1:4]
    y0 = int(sys.argv[4]) if len(sys.argv) > 4 else 2020
    bars, cycles = build(f1, f2, y0)
    L = [f"# 研究 A：跨月價差回歸（{y0} 起，{len(cycles)} 個結算週期）", "",
         "- 單位：點（一組＝近月、次月各 1 口）。主口徑成本＝期交稅＋滑價來回 4 點；手續費未計（待確認）。",
         "- K＝0.5 是對照組。", "",
         "## 一、參數格（主口徑，持有上限 3 天）",
         "| N | K | 筆數 | 勝率 | 每筆毛利 | 每筆淨利 | 總淨利 | 最大回落 | 最大單筆虧損 |", "|---|---|---|---|---|---|---|---|---|"]
    res = {}
    for N in (3, 5, 10):
        for K in (0.5, 2, 3, 4, 6):
            tr = run(bars, cycles, N, K, 4.0); res[(N, K)] = tr; s = summ(tr)
            L.append(f"| {N} | {K} | {s['n']} | {s['win']:.0f}% | {s['avg_g']:.1f} | {s['avg']:.1f} | {s['tot']:.0f} | {s['dd']:.0f} | {s['worst']:.0f} |")
    L += ["", "## 二、滑價敏感度（每筆淨利，點）", "| N | K | 滑價 0 | 滑價 4 | 滑價 8 |", "|---|---|---|---|---|"]
    for N in (3, 5, 10):
        for K in (2, 3, 4, 6):
            v = [summ(run(bars, cycles, N, K, sl))["avg"] for sl in (0.0, 4.0, 8.0)]
            L.append(f"| {N} | {K} | {v[0]:.1f} | {v[1]:.1f} | {v[2]:.1f} |")
    L += ["", "## 三、逐年總淨利（主口徑，點）", "| N | K | " + " | ".join(str(y) for y in range(y0, 2027)) + " | 正的年數 |",
          "|---|---|" + "---|" * (2027 - y0 + 1)]
    for (N, K), tr in res.items():
        by = defaultdict(float)
        for t in tr:
            by[dkey(t["d"])[0]] += t["net"]
        ys = [by.get(y, 0.0) for y in range(y0, 2027)]
        L.append(f"| {N} | {K} | " + " | ".join(f"{v:.0f}" for v in ys) + f" | {sum(v > 0 for v in ys)} |")
    L += ["", "## 四、除息季（5–8 月進場）與其他月份（主口徑）", "| N | K | 除息季筆數 | 除息季每筆淨利 | 其他筆數 | 其他每筆淨利 |", "|---|---|---|---|---|---|"]
    for (N, K), tr in res.items():
        a = [t for t in tr if 5 <= dkey(t["d"])[1] <= 8]; b = [t for t in tr if not 5 <= dkey(t["d"])[1] <= 8]
        L.append(f"| {N} | {K} | {len(a)} | {summ(a)['avg']:.1f} | {len(b)} | {summ(b)['avg']:.1f} |")
    L += ["", "## 五、持有上限敏感度（N＝5，主口徑，每筆淨利）", "| K | 1 天 | 3 天 | 5 天 |", "|---|---|---|---|"]
    for K in (2, 3, 4, 6):
        v = [summ(run(bars, cycles, 5, K, 4.0, h))["avg"] for h in (1, 3, 5)]
        L.append(f"| {K} | {v[0]:.1f} | {v[1]:.1f} | {v[2]:.1f} |")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))

if __name__ == "__main__":
    main()
