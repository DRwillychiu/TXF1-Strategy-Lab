"""S16 大殺盤診斷（2023–2026）：每個台指跌 2% 以上的交易日，拆成 30 分急殺、1 小時下殺、日盤長黑，
看 B（v1.28.1 預設，Python＝MC 逐筆）抓到多少、沒抓到的原因（沒有死亡交叉／門檻擋／持倉中）。
Usage: python -I scripts/research/s16_streak_20261118/s16_crash_diag.py <1min.txt> <out.md>
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
A = date(2023, 1, 1)


def session_date(dt):
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def max_drop(bars, idxs, k):
    """session 內任一 k 根視窗：視窗內最高價到該根收盤的最大跌幅（%）與發生時間。"""
    best, when = 0.0, None
    for n, i in enumerate(idxs):
        w = idxs[max(0, n - k + 1):n + 1]
        hi = max(bars[j].h for j in w)
        d = (hi - bars[i].c) / hi * 100
        if d > best:
            best, when = d, bars[i].dt
    return best, when


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    sig = []
    tr = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611191), on_signal=lambda i, mp: sig.append((i, mp))).trades
    ent_sig = {t.sig_i for t in tr}
    by_sess = defaultdict(list)
    for i, b in enumerate(bars):
        by_sess[session_date(b.dt)].append(i)
    sd = sorted(by_sess)
    rows = []
    for k, d in enumerate(sd[1:], 1):
        if d < A:
            continue
        ix = by_sess[d]
        prev_c = bars[by_sess[sd[k - 1]][-1]].c
        ret = (bars[ix[-1]].c / prev_c - 1) * 100
        if ret > -2:
            continue
        day = [i for i in ix if 845 < bars[i].mc_time <= 1345]
        ngt = [i for i in ix if i not in set(day)]
        d_o = bars[day[0]].o if day else 0; d_c = bars[day[-1]].c if day else 0
        d_h = max(bars[i].h for i in day) if day else 0; d_l = min(bars[i].l for i in day) if day else 0
        day_ret = (d_c / d_o - 1) * 100 if day else 0.0
        loc = (d_c - d_l) / (d_h - d_l) if day and d_h > d_l else 0.5
        gap = (bars[ix[0]].o / prev_c - 1) * 100
        m30, w30 = max_drop(bars, ix, 6)
        m60, w60 = max_drop(bars, ix, 12)
        mday, _ = max_drop(bars, day, len(day)) if day else (0.0, None)
        night_ret = (bars[ngt[-1]].c / bars[ngt[0]].o - 1) * 100 if ngt else 0.0
        tds = [t for t in tr if session_date(t.entry_dt) == d]
        s_all = [(i, mp) for i, mp in sig if i in set(ix)]
        n_flat = sum(1 for i, mp in s_all if mp == 0)
        n_ent = sum(1 for i, mp in s_all if i in ent_sig)
        # 型態：日盤長黑＝日盤開到收 ≤ −1.5% 且收在當日區間下 25%；否則看 30 分／60 分最大跌幅
        if day and day_ret <= -1.5 and loc <= 0.25:
            typ = "日盤長黑"
        elif m30 >= 1.2:
            typ = "30 分急殺"
        elif m60 >= 1.5:
            typ = "1 小時下殺"
        elif abs(gap) >= 1.0:
            typ = "跳空"
        else:
            typ = "緩跌"
        rows.append(dict(d=d, ret=ret, gap=gap, day_ret=day_ret, loc=loc, night=night_ret, m30=m30, w30=w30, m60=m60,
                         typ=typ, n=len(tds), pnl=sum(micro_net(t) for t in tds), sig=len(s_all), sig_flat=n_flat,
                         ent=n_ent, lab=",".join(t.exit_label.replace("SX_MA_", "") for t in tds)))
    out = ["# S16 大殺盤診斷（2023-01～2026-11-16；台指當天跌 2% 以上；B＝v1.28.1 預設，Python＝MC 逐筆）", "",
           "型態：日盤長黑＝日盤開到收 ≤ −1.5% 且收在日盤區間下 25%；30 分急殺＝任 30 分鐘內最高到收盤跌 ≥ 1.2%；",
           "1 小時下殺＝任 60 分鐘內跌 ≥ 1.5%；其他依跳空／緩跌。訊號＝死亡交叉且通過原有濾網（門檻之前）。", "",
           "| 日期 | 當天 | 跳空 | 日盤開→收 | 30 分最大跌 | 60 分最大跌 | 型態 | 訊號（空手時） | B 筆數 | B 損益 | 出場 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['d']} | {r['ret']:+.1f}% | {r['gap']:+.1f}% | {r['day_ret']:+.1f}% | {r['m30']:.1f}%（{r['w30']:%H:%M}） | "
                   f"{r['m60']:.1f}% | {r['typ']} | {r['sig']}（{r['sig_flat']}） | {r['n']} | {r['pnl']:,.0f} | {r['lab']} |")
    out += ["", "## 依型態彙總", "", "| 型態 | 天數 | B 有交易天數 | B 損益 | 有訊號但沒進場的天數 | 完全沒訊號的天數 |", "|---|---|---|---|---|---|"]
    agg = defaultdict(lambda: [0, 0, 0.0, 0, 0])
    for r in rows:
        a = agg[r["typ"]]
        a[0] += 1; a[1] += r["n"] > 0; a[2] += r["pnl"]; a[3] += (r["sig_flat"] > 0 and r["n"] == 0); a[4] += r["sig"] == 0
    for k, a in agg.items():
        out.append(f"| {k} | {a[0]} | {a[1]} | {a[2]:,.0f} | {a[3]} | {a[4]} |")
    tot = [r for r in rows]
    out += ["", f"- 合計 {len(tot)} 天；B 有交易 {sum(1 for r in tot if r['n'])} 天、損益 {sum(r['pnl'] for r in tot):,.0f}；"
            f"Python B 2023 起全部 {sum(1 for t in tr if t.exit_dt.date() >= A)} 筆、{sum(micro_net(t) for t in tr if t.exit_dt.date() >= A):,.0f}。", ""]
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
