"""研究 C：近月期現價差收斂（規則見 docs/research/basis_criteria_20261120.md，看結果前寫死）。
Usage: python -I scripts/research/calspread_20261120/basis_study.py <TXF1 1分.txt> <taiex_5s 資料夾> <結算價.csv> <out.md> [起始年=2020]
"""
import csv
import os
import random
import statistics as st
import sys
from collections import defaultdict

TAX, SLIP, SEED, NRAND = 2e-5, 2.0, 20261120, 200
GRID_N, GRID_K, GRID_H = (3, 5, 10), (0.5, 2, 3, 4, 6), (30, 60, 120)


def dkey(s):
    y, m, d = s.split("/")
    return (int(y), int(m), int(d))


def ymd(d):
    y, m, dd = dkey(d)
    return f"{y:04d}{m:02d}{dd:02d}"


def load_spot(folder, day):
    p = os.path.join(folder, ymd(day) + ".csv")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return [(r["time"], float(r["taiex"])) for r in csv.DictReader(f)]


def spot_minutes(rows):
    """每分鐘 t（09:01..13:30）取時間 <= t:00 的最後一筆。"""
    out, j, last = {}, 0, None
    for h in range(9, 14):
        for m in range(60):
            t = f"{h:02d}:{m:02d}"
            if t < "09:01" or t > "13:30":
                continue
            while j < len(rows) and rows[j][0] <= t + ":00":
                last = rows[j][1]
                j += 1
            if last is not None:
                out[t] = last
    return out


def settle_avg(rows):
    a = [x for t, x in rows if "13:00:00" <= t <= "13:25:00"] + [rows[-1][1]]
    return st.mean(a)


def minutes(t):
    return int(t[:2]) * 60 + int(t[3:])


def summ(tr):
    if not tr:
        return dict(n=0, avg=0.0, tot=0.0, win=0.0, g=0.0, bas=0.0, spt=0.0)
    return dict(n=len(tr), avg=st.mean(t["net"] for t in tr), tot=sum(t["net"] for t in tr),
                win=sum(t["net"] > 0 for t in tr) / len(tr) * 100, g=st.mean(t["gross"] for t in tr),
                bas=st.mean(t["basis"] for t in tr), spt=st.mean(t["spot"] for t in tr))


def main():
    f1, folder, fsp_csv, out = sys.argv[1:5]
    y0 = int(sys.argv[5]) if len(sys.argv) > 5 else 2020
    fut, last1, cnt1 = defaultdict(dict), defaultdict(str), defaultdict(int)
    with open(f1, encoding="utf-8", errors="replace") as f:
        next(f)
        for ln in f:
            p = ln.split(",")
            if int(p[0].split("/")[0]) < y0:
                continue
            t = p[1][:5]
            if "08:46" <= t <= "13:45":
                last1[p[0]] = max(last1[p[0]], t)
                cnt1[p[0]] += 1
                if "09:01" <= t <= "13:30":
                    fut[p[0]][t] = float(p[5])
    days = sorted(cnt1, key=dkey)
    settle = {d for d in days if last1[d] <= "13:30" and cnt1[d] > 200}

    with open(fsp_csv, encoding="utf-8") as f:
        fsp = {r["date"]: float(r["tx_final_settlement"]) for r in csv.DictReader(f)}
    spot, rec = {}, []
    for d in days:
        rows = load_spot(folder, d)
        if rows and len(rows) > 100:
            spot[d] = spot_minutes(rows)
            if d in fsp:
                rec.append((d, settle_avg(rows) - fsp[d]))
    ok = sum(abs(x) <= 2 for _, x in rec)
    L = [f"# 研究 C：近月期現價差收斂（{y0} 起）", "",
         f"- 有現貨資料的交易日：{len(spot)} / {len(days)}", "",
         "## 零、資料對帳（期交所最後結算價）",
         f"- 結算日 {len(rec)} 天；|自算 − 官方| ≤ 2 點：{ok} 天（{ok / max(1, len(rec)) * 100:.1f}%）；"
         f"最大差 {max((abs(x) for _, x in rec), default=0):.2f} 點"]
    bad = [f"{d}({x:+.1f})" for d, x in rec if abs(x) > 2]
    if bad:
        L.append(f"- 超過 2 點：{', '.join(bad[:30])}")
    if not rec or ok / len(rec) < 0.95:
        L.append("- **未達 95%，依規則停止。**")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(L) + "\n")
        sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))
        return

    cycles, cur = [], []
    for d in days:
        cur.append(d)
        if d in settle:
            cycles.append(cur)
            cur = []
    if cur:
        cycles.append(cur)
    dts = {}
    for c in cycles:
        for i, d in enumerate(c):
            dts[d] = len(c) - 1 - i

    bars = {}
    for d in spot:
        b = [(t, fut[d][t], spot[d][t]) for t in sorted(fut[d]) if t in spot[d] and t <= "13:25"]
        if len(b) > 100:
            bars[d] = b

    norm = {}
    for N in GRID_N:
        for c in cycles:
            for i, d in enumerate(c):
                if i < N or d not in bars:
                    continue
                hist = [fv - sv for dd in c[i - N:i] for (_, fv, sv) in bars.get(dd, [])]
                if len(hist) < 100:
                    continue
                med = st.median(hist)
                norm[(N, d)] = (med, 1.4826 * max(st.median([abs(x - med) for x in hist]), 2.0))

    def run(N, K, H):
        tr = []
        for d in sorted(bars, key=dkey):
            if (N, d) not in norm:
                continue
            med, sig = norm[(N, d)]
            b = bars[d]
            i = 0
            while i < len(b) - 2:
                z = ((b[i][1] - b[i][2]) - med) / sig
                if abs(z) < K:
                    i += 1
                    continue
                side = -1 if z > 0 else 1
                e = i + 1
                t0, fe, se = b[e]
                x = e
                while x < len(b) - 1:
                    tb = b[x][1] - b[x][2]
                    held = minutes(b[x][0]) - minutes(t0)
                    x += 1
                    if (side < 0 and tb <= med) or (side > 0 and tb >= med) or held >= H:
                        break
                _, fx, sx = b[x]
                gross = side * (fx - fe)
                tr.append(dict(d=d, side=side, fe=fe, fx=fx, gross=gross,
                               net=gross - TAX * (fe + fx) - SLIP,
                               spot=side * (sx - se), basis=side * ((fx - sx) - (fe - se))))
                i = x + 1
        return tr

    rng = random.Random(SEED)

    def rand_ctrl(tr):
        if not tr:
            return 0.0, 0.0
        v = sorted(st.mean(rng.choice((-1, 1)) * (t["fx"] - t["fe"]) - TAX * (t["fe"] + t["fx"]) - SLIP for t in tr)
                   for _ in range(NRAND))
        return st.median(v), v[int(0.95 * len(v)) - 1]

    res = {}
    L += ["", "## 一、參數格（主口徑：期交稅＋滑價來回 2 點）",
          "| N | K | 持有上限 | 筆數 | 勝率 | 每筆毛利 | 其中價差收斂 | 其中現貨變動 | 每筆淨利 | 隨機方向中位 | 隨機 95% | 總淨利 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for N in GRID_N:
        for K in GRID_K:
            for H in GRID_H:
                tr = run(N, K, H)
                res[(N, K, H)] = tr
                s = summ(tr)
                rm, r95 = rand_ctrl(tr)
                L.append(f"| {N} | {K} | {H} | {s['n']} | {s['win']:.0f}% | {s['g']:.2f} | {s['bas']:.2f} | "
                         f"{s['spt']:.2f} | {s['avg']:.2f} | {rm:.2f} | {r95:.2f} | {s['tot']:.0f} |")

    years = list(range(y0, 2027))
    L += ["", "## 二、逐年總淨利（點）",
          "| N | K | 持有上限 | " + " | ".join(map(str, years)) + " | 正的年數 |",
          "|---|---|---|" + "---|" * (len(years) + 1)]
    for k, tr in res.items():
        by = defaultdict(float)
        for t in tr:
            by[dkey(t["d"])[0]] += t["net"]
        ys = [by.get(y, 0.0) for y in years]
        L.append(f"| {k[0]} | {k[1]} | {k[2]} | " + " | ".join(f"{v:.0f}" for v in ys) + f" | {sum(v > 0 for v in ys)} |")

    L += ["", "## 三、分組每筆淨利（另外列出，不列入通過條件；括號為筆數）",
          "| N | K | 持有上限 | 除息季 | 其他月份 | 距結算 0–4 天 | 5 天以上 |", "|---|---|---|---|---|---|---|"]
    for k, tr in res.items():
        def g(fn):
            return summ([t for t in tr if fn(t)])
        a = g(lambda t: 5 <= dkey(t["d"])[1] <= 8)
        o = g(lambda t: not 5 <= dkey(t["d"])[1] <= 8)
        c = g(lambda t: dts[t["d"]] <= 4)
        e = g(lambda t: dts[t["d"]] > 4)
        L.append(f"| {k[0]} | {k[1]} | {k[2]} | {a['avg']:.2f}（{a['n']}） | {o['avg']:.2f}（{o['n']}） | "
                 f"{c['avg']:.2f}（{c['n']}） | {e['avg']:.2f}（{e['n']}） |")

    L += ["", "## 四、研究 C2：理想對沖下的價差收斂（每筆，點；推論）",
          "| N | K | 持有上限 | 筆數 | 價差收斂中位 | 平均 | 收斂為正的比例 |", "|---|---|---|---|---|---|---|"]
    for k, tr in res.items():
        if k[1] == 0.5 or not tr:
            continue
        v = [t["basis"] for t in tr]
        L.append(f"| {k[0]} | {k[1]} | {k[2]} | {len(v)} | {st.median(v):.1f} | {st.mean(v):.2f} | "
                 f"{sum(x > 0 for x in v) / len(v) * 100:.0f}% |")

    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
