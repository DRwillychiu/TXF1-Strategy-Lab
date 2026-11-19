"""S16 大殺盤 5 項優化：逐項掃參數 → 依事先寫死的標準判定 → 高原取值 → 依序組合 → 逐年完整績效。
標準：docs/ops/S16_boss_20261120/S16_crash_opt_criteria_20261119.md（看結果前寫死）。
Python 引擎（全部關閉時＝MC v1281c 逐筆），結果標推論。2 口微台淨額、資金 140,200。

Usage: python -I scripts/research/s16_streak_20261118/s16_crash_opt.py <1min.txt> <out.md> <final_trades.csv> [v2]
v2＝第 2 版：1–3 加 Crash_Struct=1（只在 ZLEMA 快線 < 慢線時），只掃 1–3。
"""
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
A = datetime(2023, 1, 1)
YRS = (CUT - A).days / 365
YF26 = (CUT - datetime(2026, 1, 1)).days / 365
GRID = {
    "Crash30_Pct": [0.8, 1.0, 1.2, 1.5, 1.8],
    "Crash60_Pct": [1.0, 1.2, 1.5, 1.8, 2.2],
    "DayTrend_Pct": [0.8, 1.0, 1.2, 1.5, 2.0],
    "CrashDay_Pct": [1.0, 1.5, 2.0, 2.5, 3.0],
    "ContRe_On": [1.0],
}
NAME = {"Crash30_Pct": "1. 30 分急殺進場", "Crash60_Pct": "2. 1 小時下殺進場", "DayTrend_Pct": "3. 日盤長黑進場",
        "CrashDay_Pct": "4. 大殺盤讓獲利跑", "ContRe_On": "5. 停利後破低再空"}


def session_date(dt):
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def crash_days(bars):
    """2023 起台指當天（日盤＋接續夜盤）跌 2% 以上的日子 → 型態。定義同 s16_crash_diag.py。"""
    by = defaultdict(list)
    for i, b in enumerate(bars):
        by[session_date(b.dt)].append(i)
    sd = sorted(by); out = {}
    for k, d in enumerate(sd[1:], 1):
        if d < A.date():
            continue
        ix = by[d]; pc = bars[by[sd[k - 1]][-1]].c
        ret = (bars[ix[-1]].c / pc - 1) * 100
        if ret > -2:
            continue
        day = [i for i in ix if 845 < bars[i].mc_time <= 1345]
        dr = (bars[day[-1]].c / bars[day[0]].o - 1) * 100 if day else 0.0
        dh = max(bars[i].h for i in day) if day else 0; dl = min(bars[i].l for i in day) if day else 0
        loc = (bars[day[-1]].c - dl) / (dh - dl) if day and dh > dl else 0.5

        def md(k_):
            best = 0.0
            for n, i in enumerate(ix):
                hi = max(bars[j].h for j in ix[max(0, n - k_ + 1):n + 1])
                best = max(best, (hi - bars[i].c) / hi * 100)
            return best
        gap = (bars[ix[0]].o / pc - 1) * 100
        if day and dr <= -1.5 and loc <= 0.25:
            typ = "日盤長黑"
        elif md(6) >= 1.2:
            typ = "30 分急殺"
        elif md(12) >= 1.5:
            typ = "1 小時下殺"
        elif abs(gap) >= 1.0:
            typ = "跳空"
        else:
            typ = "緩跌"
        out[d] = typ
    return out


def metrics(tr, cdays):
    sel = [t for t in tr if A <= t.exit_dt <= CUT]
    pn = [micro_net(t) for t in sel]
    x = full_stats(pn, YRS)
    gp = sum(v for v in pn if v > 0); gl = -sum(v for v in pn if v < 0)
    x["pf"] = gp / gl if gl else float("inf")
    x["yr"] = {y: sum(micro_net(t) for t in sel if t.exit_dt.year == y) for y in range(2023, 2027)}
    x["val"] = sum(micro_net(t) for t in tr if datetime(2020, 1, 1) <= t.exit_dt < A)
    hit = defaultdict(float)
    for t in sel:
        d = session_date(t.entry_dt)
        if d in cdays:
            hit[d] += micro_net(t)
    x["cd_n"] = len(hit); x["cd_pnl"] = sum(hit.values()); x["cd_hit"] = hit
    lab = defaultdict(lambda: [0, 0.0])
    for t in sel:
        lab[t.entry_label][0] += 1; lab[t.entry_label][1] += micro_net(t)
    x["lab"] = dict(lab)
    return x


def passes(x, b, plateau_ok=True):
    c = [x["net"] >= b["net"] * 1.05,
         -x["mdd"] <= CAP * 0.15 and -x["mdd"] <= -b["mdd"] * 1.2,
         x["streak"] <= max(b["streak"] + 2, 9),
         all(x["yr"][y] >= b["yr"][y] for y in (2024, 2025, 2026)) and x["yr"][2023] >= b["yr"][2023] - 2000,
         plateau_ok,
         x["val"] >= b["val"] - 5000]
    return c


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    base = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    cdays = crash_days(bars)

    v2 = len(sys.argv) > 4 and sys.argv[4] == "v2"
    grid = {k: v for k, v in GRID.items() if not v2 or k in ("Crash30_Pct", "Crash60_Pct", "DayTrend_Pct")}

    def run(extra):
        q = dict(base); q.update(extra)
        if v2:
            q["Crash_Struct"] = 1.0
        return s16.run(bars, q, hol).trades

    trB = run({})
    B = metrics(trB, cdays)
    out = [f"# S16 大殺盤 5 項優化結果{'（第 2 版：1–3 只在空頭結構）' if v2 else '（第 1 版）'}（2023-01～2026-11-16；推論：Python 引擎，關閉時＝MC 逐筆）", "",
           "驗收標準看結果前寫死：`S16_crash_opt_criteria_20261119.md`。2 口微台淨額、資金 140,200。", "",
           f"對照 B：{B['n']} 筆、淨利 {B['net']:,.0f}、回撤 {B['mdd']:,.0f}、連虧 {B['streak']}、大跌日有交易 {B['cd_n']}/{len(cdays)} 天；"
           f"驗證段 2020–2022 淨利 {B['val']:,.0f}。", "",
           "## 單項掃描", "", "| 優化點 | 參數 | 筆數 | 淨利 | 變化 | 回撤 | 連虧 | 2023 | 2024 | 2025 | 2026 | 2020–22 | 大跌日 | (a)(b)(c)(d)(f) |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    single = {}
    for k, vals in grid.items():
        res = []
        for v in vals:
            x = metrics(run({k: v}), cdays)
            c = passes(x, B)
            res.append((v, x, c))
            flag = "".join("✓" if ok else "✗" for j, ok in enumerate(c) if j != 4)
            out.append(f"| {NAME[k]} | {v:g} | {x['n']} | {x['net']:,.0f} | {(x['net']/B['net']-1)*100:+.1f}% | {x['mdd']:,.0f} | {x['streak']} | "
                       f"{x['yr'][2023]:,.0f} | {x['yr'][2024]:,.0f} | {x['yr'][2025]:,.0f} | {x['yr'][2026]:,.0f} | {x['val']:,.0f} | "
                       f"{x['cd_n']} 天 {x['cd_pnl']:,.0f} | {flag} |")
            print(k, v, round(x["net"]), flush=True)
        single[k] = res
    # 高原：通過 (a)(b)(c)(d)(f) 且相鄰格也通過 (a)；取最長連續通過區段的中間值
    chosen = {}
    out += ["", "## 單項判定（高原取值）", ""]
    for k, res in single.items():
        ok = [all(c[j] for j in (0, 1, 2, 3, 5)) for _, _, c in res]
        a_ok = [c[0] for _, _, c in res]
        plat = []
        for j, o in enumerate(ok):
            nb = [a_ok[n] for n in (j - 1, j + 1) if 0 <= n < len(res)]
            plat.append(o and (all(nb) if len(res) > 1 else True))
        runs, cur = [], []
        for j, o in enumerate(plat):
            if o:
                cur.append(j)
            else:
                if cur:
                    runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        if runs:
            best = max(runs, key=len)
            j = best[(len(best) - 1) // 2]
            chosen[k] = res[j]
            out.append(f"- {NAME[k]}：**通過**，取 {res[j][0]:g}（通過區段 {', '.join(f'{res[n][0]:g}' for n in best)}）；淨利 {res[j][1]['net']:,.0f}")
        else:
            out.append(f"- {NAME[k]}：**不通過**（沒有任何值同時符合全部條件與高原）")
    # 組合
    order = sorted(chosen, key=lambda k: -chosen[k][1]["net"])
    combo, cx = {}, B
    out += ["", "## 組合（依淨利增加排序，逐一加入）", "", "| 步驟 | 加入 | 淨利 | 回撤 | 連虧 | 結果 |", "|---|---|---|---|---|---|"]
    for k in order:
        trial = dict(combo); trial[k] = chosen[k][0]
        x = metrics(run(trial), cdays)
        c = passes(x, B)
        good = all(c[j] for j in (0, 1, 2, 3, 5)) and x["net"] > cx["net"]
        out.append(f"| {len(combo)+1} | {NAME[k]}＝{chosen[k][0]:g} | {x['net']:,.0f} | {x['mdd']:,.0f} | {x['streak']} | {'加入' if good else '不加入'} |")
        if good:
            combo, cx = trial, x
    trF = run(combo)
    F = metrics(trF, cdays)
    out += ["", f"**最終組合**：{('、'.join(f'{NAME[k]}＝{v:g}' for k, v in combo.items())) or '無（維持 B）'}", ""]

    # 逐年完整績效
    def yr_table(tr, lab):
        rows = [f"### {lab}", "", "| 年 | 筆數 | 淨利 | 報酬率 | 每筆期望值 | 每 1 萬元每筆 | 每 1 萬元全年 | 勝率 | PF | 最大回撤 | 最長連虧 |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for y, a, z, yrs in ((2023, datetime(2023, 1, 1), datetime(2024, 1, 1), 1.0), (2024, datetime(2024, 1, 1), datetime(2025, 1, 1), 1.0),
                             (2025, datetime(2025, 1, 1), datetime(2026, 1, 1), 1.0), ("2026（換算全年）", datetime(2026, 1, 1), CUT, YF26),
                             ("2023–2026 全期", A, CUT, YRS)):
            pn = [micro_net(t) for t in tr if a <= t.exit_dt <= z and not (t.exit_dt == z and z != CUT)]
            x = full_stats(pn, yrs)
            gp = sum(v for v in pn if v > 0); gl = -sum(v for v in pn if v < 0)
            pf = gp / gl if gl else float("inf")
            rows.append(f"| {y} | {x['n']} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | {x['exp']/CAP*10000:,.0f} | "
                        f"{x['ann']*100:,.0f} | {x['win']*100:.0f}% | {pf:.2f} | {x['mdd']/CAP*100:.1f}% | {x['streak']} |")
        return rows + [""]
    out += ["## 逐年完整績效（2 口微台、資金 140,200）", ""] + yr_table(trB, "現行 B（v1.28.1）") + yr_table(trF, "大殺盤優化版（候選）")

    # 大跌日捕捉
    out += ["## 大跌日（台指跌 2% 以上）捕捉", "", "| 型態 | 天數 | B 有交易 | B 損益 | 優化版有交易 | 優化版損益 |", "|---|---|---|---|---|---|"]
    for typ in ("日盤長黑", "30 分急殺", "1 小時下殺", "緩跌", "跳空"):
        ds = [d for d, t in cdays.items() if t == typ]
        out.append(f"| {typ} | {len(ds)} | {sum(1 for d in ds if d in B['cd_hit'])} | {sum(B['cd_hit'].get(d, 0) for d in ds):,.0f} | "
                   f"{sum(1 for d in ds if d in F['cd_hit'])} | {sum(F['cd_hit'].get(d, 0) for d in ds):,.0f} |")
    out += ["", "## 優化版各進場方式（2023 起）", "", "| 進場 | 筆數 | 淨利 |", "|---|---|---|"]
    out += [f"| {k} | {v[0]} | {v[1]:,.0f} |" for k, v in sorted(F["lab"].items(), key=lambda kv: -kv[1][1])]
    out.append("")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    with open(sys.argv[3], "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_ntd", "micro_net"])
        for n, t in enumerate(trF, 1):
            w.writerow([n, f"{t.entry_dt:%Y-%m-%d %H:%M}", t.entry_label, t.entry_px, f"{t.exit_dt:%Y-%m-%d %H:%M}",
                        t.exit_label, t.exit_px, round(t.net_ntd), round(micro_net(t))])
    print("\n".join(out))
    print("COMBO", combo)


if __name__ == "__main__":
    main()
