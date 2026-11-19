"""空方帳戶合併回撤：L2 V1.1.0（＝v5.12 回升保本關）＋ L4 V1.1.0（＝v14.10）＋ S16 B（v1.28.1）。推論。

- 三支都用 Python 重現：
  - L2 對 MC v5.10 報表逐筆相同 96/96。
  - L4 對 MC T8 報表逐筆相同 135 列。
  - S16 B 對 MC v1281c 逐筆相同 139/139。
  - 11/19 已用新 1 分 K 檔重跑確認。
  - L2 V1.1.0 和 v5.11 的差異（v5.12 三項，回升保本關）沒有 MC 報表，是推論。
- 每支微台 2 口（L4 可能分批出場，依每列口數）。
- 金額＝微台淨額：MC 口徑 ÷20，再扣期交稅與手續費 12 元／口／邊。
- 回撤兩種算法：
  - 平倉：只看出場後的帳。
  - 盯市：每根 5 分 K 收盤，連同未平倉一起算。
- 資金兩種假設（待 Willy 確認 S16 放哪個帳戶）：
  - 10 萬：現有空方帳戶，只放 L2、L4。
  - 24 萬 200：再加 S16 的 140,200。
- 保證金：微台每口原始保證金待確認，只報同時最多幾口。

Usage: python -I scripts/research/s16_streak_20261118/short_account_combo.py <1min.txt> <out.md>
"""
import bisect
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/research/l2_v5_12_20261116"))
from vol_gate_years import s16, load_bars, micro_net  # noqa: E402
from predict import NEW, L2V512  # noqa: E402
from txfcore.instruments.spec import TXF  # noqa: E402
from txfcore.profiles import mc_compat  # noqa: E402
from txfcore.quotes.bars import aggregate_bars  # noqa: E402
from txfcore.quotes.daily import NIGHT_FIRST, build  # noqa: E402
from txfcore.quotes.history import MC12MinuteSource  # noqa: E402
from txfcore.strategies.l4_consolshort_v14_10 import L4ConsolShortV1410  # noqa: E402
from txfcore.types.mctime import mc_date_to_date  # noqa: E402

CUT = dt.datetime(2026, 11, 16, 12, 20)
S20 = dt.datetime(2020, 1, 1)
A23 = dt.datetime(2023, 1, 1)
CAPS = [("10 萬（只有 L2、L4 的現有空方帳戶）", 100_000), ("24 萬 200（再加 S16 的 140,200）", 240_200)]


def to_dt(d, t):
    return dt.datetime.combine(mc_date_to_date(d), dt.time(t // 100, t % 100))


def conv(t, name):
    q = t.quantity
    sign = -1 if t.direction.name == "SHORT" else 1
    net = t.net_ntd(TXF) / 20 - (t.entry_price + t.exit_price) * 10 * 0.00002 * q - 12 * 2 * q
    return dict(s=name, e=to_dt(t.entry_date, t.entry_time), x=to_dt(t.exit_date, t.exit_time),
                ep=t.entry_price, xp=t.exit_price, q=q, sign=sign, net=net)


def mdd_of(eq):
    pk = mdd = 0.0; at = None
    for k, v in eq:
        if v > pk:
            pk = v
        if v - pk < mdd:
            mdd, at = v - pk, k
    return mdd, at


def streak(tr):
    run = best = 0; amt = worst = 0.0
    for t in sorted(tr, key=lambda r: r["x"]):
        if t["net"] < 0:
            run += 1; amt += t["net"]
        else:
            run = 0; amt = 0.0
        best = max(best, run); worst = min(worst, amt)
    return best, worst


def load_all(path):
    """三支策略的交易（2020 起、CUT 前平倉）與 2020 起的 5 分 K。"""
    mins = [m for m in MC12MinuteSource(path, validate=False).stream() if 1180101 <= m.mc_date <= 1261116]
    l2 = mc_compat.single_runner(L2V512(new=dict(NEW)), mc_compat.POLICY).run(
        list(aggregate_bars([m for m in mins if m.mc_date >= 1190102], 60)))
    l4 = mc_compat.multi_runner(L4ConsolShortV1410()).run(
        list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)), build(mins, NIGHT_FIRST))
    del mins
    bars = load_bars(path, dt.datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    s16tr = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611191)).trades
    tr = [conv(t, "L2") for t in l2.trades] + [conv(t, "L4") for t in l4.trades]
    tr += [dict(s="S16", e=t.entry_dt, x=t.exit_dt, ep=t.entry_px, xp=t.exit_px, q=2, sign=-1, net=micro_net(t)) for t in s16tr]
    tr = [t for t in tr if S20 <= t["e"] and t["x"] <= CUT]
    return tr, [b for b in bars if S20 <= b.dt <= CUT]


def mtm_series(sel, bars, bdt):
    """每根 5 分 K 收盤的盯市權益（已實現＋未平倉）。"""
    n = len(bars)
    u = [0.0] * n; r = [0.0] * n
    for t in sel:
        a = bisect.bisect_left(bdt, t["e"]); z = bisect.bisect_left(bdt, t["x"])
        for j in range(a, min(z, n)):
            u[j] += (bars[j].c - t["ep"]) * t["sign"] * 10 * t["q"]
        if z < n:
            r[z] += t["net"]
    eq, cum = [], 0.0
    for j in range(n):
        cum += r[j]
        eq.append((bdt[j], cum + u[j]))
    return eq


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1]
    mins = [m for m in MC12MinuteSource(path, validate=False).stream() if 1180101 <= m.mc_date <= 1261116]
    l2 = mc_compat.single_runner(L2V512(new=dict(NEW)), mc_compat.POLICY).run(
        list(aggregate_bars([m for m in mins if m.mc_date >= 1190102], 60)))
    l4 = mc_compat.multi_runner(L4ConsolShortV1410()).run(
        list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)), build(mins, NIGHT_FIRST))
    del mins
    bars = load_bars(path, dt.datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    s16tr = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611191)).trades
    tr = [conv(t, "L2") for t in l2.trades] + [conv(t, "L4") for t in l4.trades]
    tr += [dict(s="S16", e=t.entry_dt, x=t.exit_dt, ep=t.entry_px, xp=t.exit_px, q=2, sign=-1, net=micro_net(t)) for t in s16tr]
    tr = [t for t in tr if S20 <= t["e"] and t["x"] <= CUT]
    names = ["L2", "L4", "S16"]

    # 盯市權益（每根 5 分 K）
    bars = [b for b in bars if S20 <= b.dt <= CUT]
    bdt = [b.dt for b in bars]
    n = len(bars)

    def mtm(sel):
        u = [0.0] * n; r = [0.0] * n
        for t in sel:
            a = bisect.bisect_left(bdt, t["e"]); z = bisect.bisect_left(bdt, t["x"])
            for j in range(a, min(z, n)):
                u[j] += (bars[j].c - t["ep"]) * t["sign"] * 10 * t["q"]
            if z < n:
                r[z] += t["net"]
        eq, cum = [], 0.0
        for j in range(n):
            cum += r[j]
            eq.append((bdt[j], cum + u[j]))
        return eq

    combos = [("L2", ["L2"]), ("L4", ["L4"]), ("S16", ["S16"]), ("L2＋L4（現在的空方帳戶）", ["L2", "L4"]),
              ("L2＋L4＋S16", names)]
    out = ["# 空方帳戶合併回撤：L2＋L4＋S16（推論；2 口微台淨額）", "",
           "定義寫在程式開頭 `short_account_combo.py`。", ""]
    for pn, a0 in (("2020-01～2026-11-16", S20), ("2023-01～2026-11-16", A23)):
        out += [f"## {pn}", "",
                "| 組合 | 筆數 | 淨利 | 平倉最大回撤 | 盯市最大回撤（發生時間） | 最長連虧（筆／金額） | 盯市回撤佔 10 萬 | 佔 24 萬 200 |",
                "|---|---|---|---|---|---|---|---|"]
        for nm, ss in combos:
            sel = [t for t in tr if t["s"] in ss and t["e"] >= a0]
            closed, cum = [], 0.0
            for t in sorted(sel, key=lambda r: r["x"]):
                cum += t["net"]; closed.append((t["x"], cum))
            cm, _ = mdd_of(closed)
            mm, at = mdd_of([(k, v) for k, v in mtm(sel) if k >= a0])
            st, sa = streak(sel)
            out.append(f"| {nm} | {len(sel)} | {sum(t['net'] for t in sel):,.0f} | {cm:,.0f} | {mm:,.0f}（{at:%Y-%m-%d}） | "
                       f"{st}／{sa:,.0f} | {-mm / 1e5 * 100:.1f}% | {-mm / 240_200 * 100:.1f}% |")
        out.append("")
        sel = [t for t in tr if t["e"] >= a0]
        out += ["逐年淨利：", "", "| 年 | L2 | L4 | S16 | 合計 | 合計盯市年內最大回撤 |", "|---|---|---|---|---|---|"]
        eq_all = mtm(sel)
        for y in range(a0.year, 2027):
            v = [sum(t["net"] for t in sel if t["s"] == s and t["x"].year == y) for s in names]
            ey = [(k, v_) for k, v_ in eq_all if k.year == y]
            base = ey[0][1] if ey else 0.0
            m_, _ = mdd_of([(k, v_ - base) for k, v_ in ey])
            out.append(f"| {y} | " + " | ".join(f"{x:,.0f}" for x in v) + f" | {sum(v):,.0f} | {m_:,.0f} |")
        out.append("")

    # 同時持倉、每日損益相關
    sel = tr
    cnt = defaultdict(int)
    for t in sel:
        a = bisect.bisect_left(bdt, t["e"]); z = bisect.bisect_left(bdt, t["x"])
        for j in range(a, min(z, n)):
            cnt[j] += t["q"]
    held = [j for j in range(n) if cnt[j] > 0]
    strat_at = defaultdict(set)
    for t in sel:
        a = bisect.bisect_left(bdt, t["e"]); z = bisect.bisect_left(bdt, t["x"])
        for j in range(a, min(z, n)):
            strat_at[j].add(t["s"])
    multi = sum(1 for j in held if len(strat_at[j]) >= 2)
    three = sum(1 for j in held if len(strat_at[j]) >= 3)
    mx = max(cnt.values()) if cnt else 0
    out += ["## 同時持倉（2020 起，5 分 K 計）", "",
            f"- 有部位的時間裡，2 支以上同時持空 {multi / max(1, len(held)) * 100:.1f}%，3 支同時 {three / max(1, len(held)) * 100:.1f}%。",
            f"- 同時最多 {mx} 口微台空單（保證金每口金額待確認）。", ""]
    day_pnl = {}
    for s in names:
        eq = mtm([t for t in sel if t["s"] == s])
        last = {}
        for k, v in eq:
            d = (k - dt.timedelta(days=1)).date() if k.hour < 8 else k.date()
            last[d] = v
        ds = sorted(last)
        day_pnl[s] = {d: last[d] - last[ds[i - 1]] for i, d in enumerate(ds) if i}
    ds = sorted(day_pnl["L2"])

    def corr(a, b):
        x = [day_pnl[a][d] for d in ds]; y = [day_pnl[b][d] for d in ds]
        mx_, my = sum(x) / len(x), sum(y) / len(y)
        sx = sum((v - mx_) ** 2 for v in x) ** 0.5; sy = sum((v - my) ** 2 for v in y) ** 0.5
        return sum((u - mx_) * (v - my) for u, v in zip(x, y)) / (sx * sy) if sx and sy else 0.0
    tot = {d: sum(day_pnl[s][d] for s in names) for d in ds}
    worst = sorted(tot.items(), key=lambda kv: kv[1])[:5]
    out += ["## 每日盯市損益相關係數（2020 起）", "",
            f"- L2–L4 {corr('L2', 'L4'):.2f}、L2–S16 {corr('L2', 'S16'):.2f}、L4–S16 {corr('L4', 'S16'):.2f}",
            "- 合計最差 5 天：" + "、".join(f"{d} {v:,.0f}（L2 {day_pnl['L2'][d]:,.0f}／L4 {day_pnl['L4'][d]:,.0f}／S16 {day_pnl['S16'][d]:,.0f}）" for d, v in worst), ""]
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
