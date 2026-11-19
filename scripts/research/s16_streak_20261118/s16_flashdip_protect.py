"""Willy 11/19 第 1、2 問（推論；Python，5 分 K，B 引擎＝MC v1281c 逐筆）

一、急殺後反彈：事件研究（定義看結果前寫死）
- 一盤＝日盤 08:45–13:45 或夜盤 15:00–05:00；期間 2020-01-01～2026-11-16。
- 急殺：盤中某根收盤，距過去 30 分鐘（6 根，含本根）最高價跌 ≥ X%，X＝1.0／1.2／1.5／2.0；每盤只取第一次。
  只用當下看得到的價格；不用「事後有沒有反彈」挑事件。
- 下一根開盤進場，同一盤內：
  - 做多 A：持有 30 分、60 分、120 分、到收盤的報酬
  - 做多 B（簡單規則）：停損 −1%、停利＝拉回急殺跌幅的一半、到收盤平倉；同一根停損停利都碰算停損
  - 做空：持有到收盤（＝做多 A 收盤的反向）
- 成本：滑價每邊 5 點（MC 口徑）＋稅＋手續費 12 元／口／邊，微台 2 口。
- 事後標記（只用來理解尾端風險，不能當進場條件）：那個交易日整天有沒有跌到 2%。

二、獲利保護：B 每筆的最大浮盈（持有期間最低價）和實拿
- 保本：浮盈 ≥ 0.70% 後停損移到進場價 −20 點。
- 結構移動停損：最大浮盈 ≥ 0.60% 後，用最近 20 根收盤最高價 ＋12 點。
- 2.3% 限價停利、黃金交叉出場、48 根時間出場。

Usage: python -I scripts/research/s16_streak_20261118/s16_flashdip_protect.py <1min.txt> <out.md>
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
S20 = datetime(2020, 1, 1)
A23 = datetime(2023, 1, 1)
XS = [1.0, 1.2, 1.5, 2.0]
SLIP = 5


def in_sess(b):
    t = b.mc_time
    return (845 < t <= 1345) or t > 1500 or t <= 500


def sess_key(b):
    if 845 < b.mc_time <= 1345:
        return (b.dt.date(), "D")
    return ((b.dt - timedelta(days=1)).date() if b.dt.hour < 8 else b.dt.date(), "N")


def trade_date(b):
    return (b.dt - timedelta(days=1)).date() if b.dt.hour < 8 else b.dt.date()


def net2(pts, px_in, px_out):
    """做多或做空的點數（已帶正負）→ 微台 2 口淨額。"""
    return (pts - 2 * SLIP) * 10 * 2 - (px_in + px_out) * 10 * 0.00002 * 2 - 12 * 2 * 2


def summ(v):
    if not v:
        return "0 筆", "—", "—", "—", "—"
    s = sorted(v)
    return (f"{len(v)}", f"{sum(1 for x in v if x > 0) / len(v) * 100:.0f}%", f"{sum(v) / len(v):,.0f}",
            f"{sum(v):,.0f}", f"{s[0]:,.0f}")


def flashdip(bars):
    sess = defaultdict(list)
    for i, b in enumerate(bars):
        if in_sess(b) and S20 <= b.dt <= CUT:
            sess[sess_key(b)].append(i)
    # 交易日整天報酬（事後標記用）
    last = {}
    for k in sorted(sess):
        last[k[0]] = sess[k][-1]
    ds = sorted(last)
    dret = {d: (bars[last[d]].c / bars[last[ds[n - 1]]].c - 1) * 100 for n, d in enumerate(ds) if n}
    out = ["## 一、急殺後反彈：事件研究（2020-01～2026-11-16，只用當下價格觸發）", "",
           "金額＝微台 2 口淨額，已扣滑價、稅、手續費。", ""]
    for X in XS:
        rec = []
        for k, ix in sess.items():
            for n, i in enumerate(ix):
                if n + 1 >= len(ix):
                    break
                w = ix[max(0, n - 5):n + 1]
                hi = max(bars[j].h for j in w)
                if (hi - bars[i].c) / hi * 100 < X:
                    continue
                e = ix[n + 1]; px = bars[e].o
                rest = ix[n + 1:]
                fw = {}
                for lab, h in (("30分", 6), ("60分", 12), ("120分", 24)):
                    j = rest[min(h, len(rest)) - 1]
                    fw[lab] = net2(bars[j].c - px, px, bars[j].c)
                end_c = bars[rest[-1]].c
                fw["收盤"] = net2(end_c - px, px, end_c)
                fw["空到收盤"] = net2(px - end_c, px, end_c)
                stop, tgt = px * 0.99, px + (hi - bars[i].c) * 0.5
                res = None
                for j in rest:
                    if bars[j].l <= stop:
                        res = net2(stop - px, px, stop); break
                    if bars[j].h >= tgt:
                        res = net2(tgt - px, px, tgt) + 2 * SLIP * 10 * 2 * 0.5; break   # 限價停利：出場不計滑價
                if res is None:
                    res = fw["收盤"]
                fw["規則B"] = res
                rec.append(dict(dt=bars[i].dt, yr=bars[i].dt.year, crash=dret.get(k[0], 0) <= -2, **fw))
                break
        out += [f"### 急殺門檻 {X}%：{len(rec)} 盤（其中事後是大跌 2% 日 {sum(1 for r in rec if r['crash'])} 盤）", "",
                "| 做法 | 期間 | 筆數 | 勝率 | 每筆平均 | 合計 | 最差一筆 |", "|---|---|---|---|---|---|---|"]
        for lab, nm in (("30分", "做多 持有 30 分"), ("60分", "做多 持有 60 分"), ("120分", "做多 持有 120 分"),
                        ("收盤", "做多 持有到收盤"), ("規則B", "做多 停損 1%／停利拉回一半"), ("空到收盤", "做空 持有到收盤")):
            for pn, f in (("2020–2022", lambda r: r["yr"] <= 2022), ("2023–2026", lambda r: r["yr"] >= 2023)):
                out.append(f"| {nm} | {pn} | " + " | ".join(summ([r[lab] for r in rec if f(r)])) + " |")
        rb = [r for r in rec if r["yr"] >= 2023]
        out += ["", "做多 停損 1%／停利拉回一半，2023–2026 依事後標記拆開：",
                f"- 平日：{' ／ '.join(summ([r['規則B'] for r in rb if not r['crash']]))}（筆數／勝率／平均／合計／最差）",
                f"- 大跌 2% 日：{' ／ '.join(summ([r['規則B'] for r in rb if r['crash']]))}",
                "逐年（做多 停損 1%／停利拉回一半）：" + "、".join(
                    f"{y} {sum(1 for r in rec if r['yr'] == y)} 筆 {sum(r['規則B'] for r in rec if r['yr'] == y):,.0f}" for y in range(2020, 2027)), ""]
    return out


def protect(bars, p, hol):
    tr = [t for t in s16.run(bars, p, hol).trades if S20 <= t.exit_dt <= CUT]
    ix = {b.dt: i for i, b in enumerate(bars)}
    rows = []
    for t in tr:
        a, z = ix[t.entry_dt], ix[t.exit_dt]
        lo = min(bars[j].l for j in range(a, z + 1))
        mfe = (t.entry_px - lo) / t.entry_px * 100
        real = (t.entry_px - t.exit_px) / t.entry_px * 100
        rows.append(dict(t=t, mfe=mfe, real=real, net=micro_net(t), mfe_nt=net2(t.entry_px - lo, t.entry_px, lo)))
    out = ["## 二、獲利保護：最大浮盈 vs 實拿（B；Python＝MC 逐筆）", ""]
    for pn, f in (("2023–2026", lambda r: r["t"].exit_dt >= A23), ("2020–2026", lambda r: True)):
        sel = [r for r in rows if f(r)]
        out += [f"### {pn}（{len(sel)} 筆）", "",
                "| 最大浮盈 | 筆數 | 最後賺錢 | 最後虧損 | 平均最大浮盈 | 平均實拿 | 實拿佔浮盈 | 實拿合計 |", "|---|---|---|---|---|---|---|---|"]
        for lo_, hi_, nm in ((0, 0.3, "< 0.3%"), (0.3, 0.6, "0.3–0.6%"), (0.6, 1.0, "0.6–1.0%（保護啟動）"),
                             (1.0, 2.3, "1.0–2.3%"), (2.3, 99, "≥ 2.3%（碰到停利）")):
            s = [r for r in sel if lo_ <= r["mfe"] < hi_]
            if not s:
                continue
            am = sum(r["mfe"] for r in s) / len(s); ar = sum(r["real"] for r in s) / len(s)
            out.append(f"| {nm} | {len(s)} | {sum(1 for r in s if r['net'] > 0)} | {sum(1 for r in s if r['net'] <= 0)} | "
                       f"{am:.2f}% | {ar:+.2f}% | {ar / am * 100 if am > 0 else 0:.0f}% | {sum(r['net'] for r in s):,.0f} |")
        prot = [r for r in sel if r["mfe"] >= 0.6]
        out += ["", f"- 浮盈到 0.6% 以上（保護啟動）共 {len(prot)} 筆，最後虧損 {sum(1 for r in prot if r['net'] <= 0)} 筆"
                f"（合計 {sum(r['net'] for r in prot if r['net'] <= 0):,.0f}）。",
                f"- 這 {len(prot)} 筆最大浮盈合計 {sum(r['mfe_nt'] for r in prot):,.0f}，實拿 {sum(r['net'] for r in prot):,.0f}"
                f"（{sum(r['net'] for r in prot) / max(1, sum(r['mfe_nt'] for r in prot)) * 100:.0f}%）。", ""]
        by = defaultdict(list)
        for r in prot:
            by[r["t"].exit_label].append(r)
        out += ["| 保護啟動後的出場方式 | 筆數 | 平均最大浮盈 | 平均實拿 | 合計 |", "|---|---|---|---|---|"]
        for k, s in sorted(by.items(), key=lambda kv: -len(kv[1])):
            out.append(f"| {k} | {len(s)} | {sum(r['mfe'] for r in s) / len(s):.2f}% | {sum(r['real'] for r in s) / len(s):+.2f}% | "
                       f"{sum(r['net'] for r in s):,.0f} |")
        out.append("")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    out = ["# S16 第 1、2 問：急殺後反彈、獲利保護（推論）", ""] + flashdip(bars) + protect(bars, p, hol)
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
