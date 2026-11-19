"""S16 跳框分析的獨立樣本：2001–2019（門檻設計時沒用到），B vs R0（門檻關＝0825 邏輯）。
驗收標準事先寫死在 docs/ops/S16_boss_20261120/S16_reframe_oos_criteria_20261119.md。
Python 引擎（2020 以來和 MC 逐筆一致），結果是推論。損益換算今天指數位階（today_net）。

Usage: python -I scripts/research/s16_streak_20261118/s16_reframe_oos.py <1min.txt> <out.md>
"""
import bisect
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from s16_prelive import today_net  # noqa: E402

A, Z = datetime(2001, 1, 1), datetime(2020, 1, 1)
YRS = (Z - A).days / 365
EDGES = [-3, -2, -1, 0, 1, 2, 3]
LABS = ["≤ −3%", "−3% ～ −2%", "−2% ～ −1%", "−1% ～ 0%", "0% ～ +1%", "+1% ～ +2%", "+2% ～ +3%", "≥ +3%"]


def session_date(dt):
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), Z)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    runs = {}
    for name, days in (("B", 90.0), ("R0", 0.0)):
        q = dict(p); q["TOD_Gate_Days"] = days
        runs[name] = [t for t in s16.run(bars, q, hol).trades if A <= t.exit_dt < Z]
    # 逐筆存檔（MC 單位：大台 2 口、滑價每口每邊 1,000），給 MC 跑 2001–2019 時逐筆對照
    import csv
    ddir = Path(__file__).resolve().parents[3] / "data/research_s16_20261118"
    for k, v in runs.items():
        with open(ddir / f"py_oos_2001_2019_{k}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_ntd"])
            for n, t in enumerate(v, 1):
                w.writerow([n, f"{t.entry_dt:%Y-%m-%d %H:%M}", t.entry_label, t.entry_px, f"{t.exit_dt:%Y-%m-%d %H:%M}",
                            t.exit_label, t.exit_px, round(t.net_ntd)])
        print(f"{k}: {len(v)} 筆，MC 單位淨利 {sum(t.net_ntd for t in v):,.0f}")
    sc = {}
    for b in bars:
        sc[session_date(b.dt)] = b.c
    sd = sorted(sc)
    ret = {d: (sc[d] / sc[p_] - 1) * 100 for p_, d in zip(sd, sd[1:]) if d >= A.date()}

    out = ["# S16 獨立樣本 2001–2019：本質與門檻是否仍成立（推論：Python 引擎）", "",
           "驗收標準（事先寫死）：`S16_reframe_oos_criteria_20261119.md`。損益換算今天指數位階，2 口微台，資金 140,200。",
           "2017-05 以前沒有夜盤；長假前出場規則只有 2019 以後的假日表，較早年份不會觸發。", ""]
    st = {k: full_stats([today_net(t) for t in v], YRS) for k, v in runs.items()}
    for k, v in runs.items():
        pn = [today_net(t) for t in v]
        gp = sum(x for x in pn if x > 0); gl = -sum(x for x in pn if x < 0)
        st[k]["pf"] = gp / gl if gl else float("inf")
    out += ["## 全期（2001–2019）", "", "| 指標 | R0（門檻關＝0825 邏輯） | B（新版） |", "|---|---|---|"]
    for lab, key, fmt in (("筆數", "n", "{:,.0f}"), ("淨利", "net", "{:,.0f}"), ("年化（單利）", "ann", "{:.1f}%"),
                          ("每筆期望值", "exp", "{:,.0f}"), ("PF", "pf", "{:.2f}"), ("勝率", "win", "{:.1%}"),
                          ("最大回撤", "mdd", "{:,.0f}"), ("最長連虧", "streak", "{:.0f}"), ("最長連虧金額", "streak_amt", "{:,.0f}")):
        out.append(f"| {lab} | {fmt.format(st['R0'][key])} | {fmt.format(st['B'][key])} |")
    out.append("")

    # 逐年
    out += ["## 逐年淨利（今天指數位階）", "", "| 年 | 台指跌 2% 以上天數 | R0 筆數 | R0 淨利 | B 筆數 | B 淨利 | B ≥ R0 |", "|---|---|---|---|---|---|---|"]
    yr_ok = 0
    for y in range(2001, 2020):
        r0 = [today_net(t) for t in runs["R0"] if t.exit_dt.year == y]
        b = [today_net(t) for t in runs["B"] if t.exit_dt.year == y]
        ok = sum(b) >= sum(r0)
        yr_ok += ok
        dn = sum(1 for d, v in ret.items() if d.year == y and v <= -2)
        out.append(f"| {y} | {dn} | {len(r0)} | {sum(r0):,.0f} | {len(b)} | {sum(b):,.0f} | {'是' if ok else '否'} |")
    out.append("")

    # 報酬型態
    pnl = {k: defaultdict(float) for k in runs}
    for k, v in runs.items():
        for t in v:
            pnl[k][session_date(t.entry_dt)] += today_net(t)
    agg = defaultdict(lambda: [0, 0.0, 0.0])
    for d, r in ret.items():
        a = agg[LABS[bisect.bisect_right(EDGES, r)]]
        a[0] += 1; a[1] += pnl["R0"].get(d, 0.0); a[2] += pnl["B"].get(d, 0.0)
    out += ["## 報酬型態：依台指當天漲跌分組", "", "| 台指當天 | 天數 | R0 淨利 | B 淨利 |", "|---|---|---|---|"]
    for k in LABS:
        if k in agg:
            a = agg[k]
            out.append(f"| {k} | {a[0]} | {a[1]:,.0f} | {a[2]:,.0f} |")
    down2 = sum(v for d, v in pnl["B"].items() if ret.get(d, 0) <= -2)
    upl = sum(v for d, v in pnl["B"].items() if ret.get(d, 0) > 0)
    calm = {k: sum(v for d, v in pnl[k].items() if abs(ret.get(d, 9)) < 1) for k in runs}
    out += ["", f"- 平淡日（±1% 內）：R0 {calm['R0']:,.0f}、B {calm['B']:,.0f}。", ""]

    # 進場時機：進場後 120 分鐘（放空角度）；和 2020 以來 B 的 +0.232%、走 1% 以上 22% 對照
    idx = {b.dt: i for i, b in enumerate(bars)}

    def fwd(e, k=24):
        x = e + k - 1
        if x >= len(bars) or bars[x].dt - bars[e].dt != timedelta(minutes=5 * (k - 1)):
            return None
        return (bars[e].o - bars[x].c) / bars[e].o * 100

    out += ["## 進場時機（進場後 120 分鐘，放空角度）", "", "| 版本 | 期間 | 樣本 | 平均 | 走 1% 以上 |", "|---|---|---|---|---|"]
    for k in runs:
        for lab, a, z in (("2001–2010", 2001, 2010), ("2011–2019", 2011, 2019)):
            v = [fwd(idx[t.entry_dt]) for t in runs[k] if a <= t.entry_dt.year <= z and t.entry_dt in idx]
            v = [x for x in v if x is not None]
            if v:
                out.append(f"| {k} | {lab} | {len(v)} | {sum(v)/len(v):+.3f}% | {sum(1 for x in v if x >= 1)/len(v)*100:.1f}% |")
    out += ["", "（2020 以來 B 的 MC 進場：平均 +0.232%、走 1% 以上 22.0%；門檻放行的隨機時點：−0.007%、2.8%。）", ""]
    lab_cnt = defaultdict(lambda: [0, 0.0])
    for t in runs["B"]:
        lab_cnt[t.exit_label][0] += 1; lab_cnt[t.exit_label][1] += today_net(t)
    out += ["## B 出場原因（檢查引擎在舊資料是否正常）", "", "| 出場 | 筆數 | 淨利 |", "|---|---|---|"]
    out += [f"| {k} | {v[0]} | {v[1]:,.0f} |" for k, v in sorted(lab_cnt.items(), key=lambda kv: -kv[1][0])]
    out.append("")

    # 判定
    h1 =down2 > 0 and (upl >= 0 or -upl < down2 / 3)
    c = [st["B"]["exp"] > st["R0"]["exp"], st["B"]["mdd"] >= st["R0"]["mdd"],
         st["B"]["streak"] <= st["R0"]["streak"], st["B"]["net"] >= st["R0"]["net"]]
    h3 = yr_ok >= 12
    yn = lambda x: "通過" if x else "不通過"
    out += ["## 判定（依事先寫死的標準）", "",
            f"- H1 本質：B 在跌 2% 以上日子 {down2:,.0f}；上漲日 {upl:,.0f} → {yn(h1)}",
            f"- H2 門檻：期望值 {yn(c[0])}、回撤 {yn(c[1])}、連虧 {yn(c[2])}、淨利 {yn(c[3])} → {yn(all(c))}",
            f"- H3 穩定：B ≥ R0 的年份 {yr_ok}/19 → {yn(h3)}", ""]
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
