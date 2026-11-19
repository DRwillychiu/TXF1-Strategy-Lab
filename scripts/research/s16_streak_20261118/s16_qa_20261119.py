"""Willy 11/19 四問的數字：
A. 勝率、每口期望值（MC 報表交易，B＝v1281c、現行＝R0／0825；2 口微台淨額 ÷ 2＝每口）
B. 平日急殺後反彈，B 賺不賺（Python 引擎，B 上＝MC 逐筆；推論）

B 的定義（看結果前寫死）：
- 一盤＝日盤 08:45–13:45 或夜盤 15:00–05:00。期間 2023-01-01～2026-11-16。
- 急殺：盤中某一根，過去 30 分鐘（6 根 5 分 K，含這一根）最高價到這一根收盤跌 ≥ 1.2%（同大殺盤診斷的 30 分急殺）。每盤取第一次。
- 反彈：急殺後到收盤之間的最低價記為低點；收盤從低點拉回 ≥ 急殺高點到低點距離的 50%。
- 平日：那個交易日（日盤＋接續夜盤）整天跌幅沒有到 2%（不是大殺盤日）。
- B 的交易：持有期間和這一盤重疊的交易。分三類：持有期間跨過急殺（進場 ≤ 低點時間且出場 ≥ 高點時間）；
  進場在低點之後＝空在低點附近；急殺前就已出場＝和這次急殺無關。
  （11/19 第一次跑用「進場在低點之前」分類，把急殺前就出場的 2 筆也算進去，改成三類；事件與交易本身沒變。）
- 沒交易的盤：這一盤有沒有死亡交叉訊號被同時段波動門檻擋掉。

Usage: python -I scripts/research/s16_streak_20261118/s16_qa_20261119.py <1min.txt> <mc_B.csv> <mc_0825.csv> <out.md>
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from mc_boss_stats import load  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
A = datetime(2023, 1, 1)
DROP, REB = 1.2, 0.5


def sess_key(b):
    t = b.mc_time
    if 845 < t <= 1345:
        return (b.dt.date(), "日盤")
    d = (b.dt - timedelta(days=1)).date() if b.dt.hour < 8 else b.dt.date()
    return (d, "夜盤")


def trade_date(dt):
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def part_a(B, R0):
    out = ["## A. 勝率與每口期望值（MC 報表交易；2 口微台淨額，每口＝÷2；1 點＝10 元）", "",
           "| 期間 | 版本 | 筆數 | 勝率 | 每筆期望值（2 口） | 每口期望值 | 每口期望值（點） | 年化報酬 | 最長連虧（筆／金額） |",
           "|---|---|---|---|---|---|---|---|---|"]
    periods = [("2023–2026/11/16", A, CUT)] + [(str(y), datetime(y, 1, 1), min(CUT, datetime(y + 1, 1, 1)))
                                                for y in range(2023, 2027)] + [("2020–2026/11/16", datetime(2020, 1, 1), CUT)]
    for name, a, b in periods:
        yrs = (b - a).days / 365
        for vn, tr in (("新版 B", B), ("現行 0825", R0)):
            pn = [micro_net(t) for t in tr if a <= t.exit_dt < b]
            x = full_stats(pn, yrs)
            out.append(f"| {name} | {vn} | {x['n']} | {x['win'] * 100:.1f}% | {x['exp']:,.0f} | {x['exp'] / 2:,.0f} | "
                       f"{x['exp'] / 2 / 10:,.1f} | {x['ann']:.1f}% | {x['streak']}／{x['streak_amt']:,.0f} |")
    out += ["", "2026 年化＝2026/1/1～11/16 淨利 ÷ 140,200 ÷ 0.874 年（換算全年）。", ""]
    return out


def part_b(bars, p, hol):
    sig = []
    tr = s16.run(bars, p, hol, on_signal=lambda i, mp: sig.append((i, mp))).trades
    tr = [t for t in tr if datetime(2022, 12, 1) <= t.exit_dt <= CUT]
    sess = defaultdict(list)
    for i, b in enumerate(bars):
        t = b.mc_time
        if (845 < t <= 1345) or t > 1500 or t <= 500:
            sess[sess_key(b)].append(i)
    keys = sorted(sess)
    # 交易日整天報酬（日盤＋接續夜盤），用每個交易日最後一根收盤
    day_last = {}
    for k in keys:
        day_last[k[0]] = sess[k][-1]
    dsort = sorted(day_last)
    dret = {d: (bars[day_last[d]].c / bars[day_last[dsort[n - 1]]].c - 1) * 100 for n, d in enumerate(dsort) if n}
    sig_by = defaultdict(list)
    for i, mp in sig:
        sig_by[sess_key(bars[i])].append((i, mp))
    entered = {t.sig_i for t in tr}
    ev = []
    for k in keys:
        if not (A.date() <= k[0] <= CUT.date()) or dret.get(k[0], 0) <= -2:
            continue
        ix = sess[k]
        trig = None
        for n, i in enumerate(ix):
            w = ix[max(0, n - 5):n + 1]
            hi = max(bars[j].h for j in w)
            if (hi - bars[i].c) / hi * 100 >= DROP:
                trig = (n, hi, max(w, key=lambda j: bars[j].h)); break
        if not trig:
            continue
        n0, hi, hi_i = trig
        rest = ix[n0:]
        lo_i = min(rest, key=lambda j: bars[j].l)
        lo = bars[lo_i].l
        reb = (bars[ix[-1]].c - lo) / (hi - lo) if hi > lo else 0
        if reb < REB:
            continue
        s0, s1 = bars[ix[0]].dt, bars[ix[-1]].dt
        ts = [t for t in tr if t.entry_dt <= s1 and t.exit_dt >= s0]
        blocked = [i for i, mp in sig_by[k] if mp == 0 and i not in entered]
        ev.append(dict(k=k, hi=hi, lo=lo, drop=(hi - lo) / hi * 100, reb=reb * 100, lo_dt=bars[lo_i].dt, hi_dt=bars[hi_i].dt,
                       trades=ts, blocked=len(blocked), dret=dret.get(k[0], 0)))
    out = ["## B. 平日急殺後反彈：B 賺不賺（2023-01～2026-11-16；推論：Python 引擎＝MC 逐筆）", "",
           f"急殺＝30 分鐘內從高點跌 ≥ {DROP}%；反彈＝收盤拉回 ≥ 跌幅的 {REB * 100:.0f}%；平日＝當天沒有跌到 2%。", ""]
    with_t = [e for e in ev if e["trades"]]
    allt = {id(t): t for e in with_t for t in e["trades"]}.values()
    before = [t for e in with_t for t in e["trades"] if t.entry_dt <= e["lo_dt"] and t.exit_dt >= e["hi_dt"]]
    after = [t for e in with_t for t in e["trades"] if t.entry_dt > e["lo_dt"]]
    unrel = [t for e in with_t for t in e["trades"] if t.exit_dt < e["hi_dt"]]

    def sm(ts):
        pn = [micro_net(t) for t in ts]
        return f"{len(pn)} 筆、賺 {sum(1 for x in pn if x > 0)} 筆、合計 {sum(pn):,.0f}"
    out += [f"- 平日急殺後反彈的盤：**{len(ev)} 盤**（日盤 {sum(1 for e in ev if e['k'][1] == '日盤')}、夜盤 {sum(1 for e in ev if e['k'][1] == '夜盤')}）",
            f"- B 有交易：{len(with_t)} 盤；交易 {sm(list(allt))}",
            f"  - 持有期間跨過急殺（高點到低點之間有部位）：{sm(before)}",
            f"  - 進場在低點之後（空在低點附近）：{sm(after)}",
            f"  - 急殺前就已出場（和這次急殺無關）：{sm(unrel)}",
            f"- B 沒交易：{len(ev) - len(with_t)} 盤；其中有死亡交叉但被同時段門檻擋掉 {sum(1 for e in ev if not e['trades'] and e['blocked'])} 盤", "",
            "| 盤 | 當天漲跌 | 急殺高點時間 | 低點時間 | 跌幅 | 反彈 | B 交易（進場→出場、方式、淨額） |", "|---|---|---|---|---|---|---|"]
    for e in ev:
        tt = "；".join(f"{t.entry_dt:%H:%M}→{t.exit_dt:%m-%d %H:%M} {t.exit_label.replace('SX_MA_', '')} {micro_net(t):,.0f}" for t in e["trades"])
        if not tt:
            tt = "門檻擋掉" if e["blocked"] else "沒有訊號"
        out.append(f"| {e['k'][0]} {e['k'][1]} | {e['dret']:+.1f}% | {e['hi_dt']:%H:%M} | {e['lo_dt']:%H:%M} | "
                   f"{e['drop']:.1f}% | {e['reb']:.0f}% | {tt} |")
    by_y = defaultdict(list)
    for t in allt:
        by_y[t.exit_dt.year].append(micro_net(t))
    out += ["", "逐年（B 在這些盤的交易）：" + "、".join(f"{y} {len(v)} 筆 {sum(v):,.0f}" for y, v in sorted(by_y.items())), ""]
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    B, R0 = load(sys.argv[2]), load(sys.argv[3])
    out = ["# S16 Willy 11/19 四問的數字", ""] + part_a(B, R0)
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    out += part_b(bars, p, hol)
    Path(sys.argv[4]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
