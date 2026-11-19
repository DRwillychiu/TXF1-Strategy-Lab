"""L2 −8% 回升保本（Reb_On）開／關績效比對 ＋ 最近幾天 L2、L4 為什麼沒有空單（2026-11-19）。

用法：python scripts/research/l2_reb_20261119/compare_reb_and_recent.py <1分K檔> [結束日 YYMMDD，預設 261119]
- L2 三個版本同一份資料、同一套 MC 相容成交（mc_compat，worst）：v5.11（10/5 上架版）、
  v5.12 Reb_On 0（11/16 決定）、v5.12 Reb_On 1（上架機原碼，11/19 匯出）
- 交易只算 MC L2 報表起始日以後（同 l2_v5_12_20261116/predict.py）；金額 ＝ MC 口徑（大台 2 口、滑價每口每邊 1,000）
- 最近 N 個交易日逐根列出 L2、L4 的進場條件
Python 結果是推論，不是 MC 報表。
"""
import collections, csv, datetime as dt, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "research", "l2_v5_12_20261116"))
from predict import NEW, L2V512                                         # noqa: E402
from txfcore.indicators.core import avg_true_range, lowest, average    # noqa: E402
from txfcore.instruments.spec import TXF                               # noqa: E402
from txfcore.modules.gates.trend_filter import DailyMaBlock            # noqa: E402
from txfcore.modules.signals.core import channel_breakdown             # noqa: E402
from txfcore.profiles import mc_compat                                 # noqa: E402
from txfcore.quotes.bars import aggregate_bars                         # noqa: E402
from txfcore.quotes.daily import NIGHT_FIRST, build                    # noqa: E402
from txfcore.quotes.history import MC12MinuteSource                    # noqa: E402
from txfcore.strategies.l2_trendshort_v5_11 import L2TrendShortV511    # noqa: E402
from txfcore.strategies.l4_consolshort_v14_10 import L4ConsolShortV1410  # noqa: E402
from txfcore.types.mctime import mc_date_to_date                       # noqa: E402

RECENT_DAYS = 12


def ts(d_, t):
    return dt.datetime.combine(mc_date_to_date(d_), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")


class L2Diag(L2V512):
    """記錄每根 60 分 K 的進場條件（呼叫原本的 on_bar，不改任何行為）。"""
    log = []

    def on_bar(self, view, state):
        state, d = super().on_bar(view, state)
        p, ps, b = self.config.params, state.per_session, view.data1
        atr = avg_true_range(b, p["ATR_Len"])
        dcl = lowest(b.low, p["DC_Len"], offset=1)
        brk = channel_breakdown(b.close[0], dcl, atr, p["C0_ATR_Filter"])
        sig = (ps.wk.ok or p["Wk_Entry_Filter"] == 0) and brk and ps.zl.falling and ps.zl.below_ema
        ent = [o.label for o in d.orders if o.label in ("TS_Entry", "CR_Entry")]
        self.log.append(dict(d=view.mc_date, t=view.mc_time, c=b.close[0], wk_ok=ps.wk.ok,
                             wk_last=ps.wk.closes[1], wk_sma=ps.wk.sma if ps.wk.ready else 0.0,
                             brk=brk, dcl=dcl - atr * p["C0_ATR_Filter"], zf=ps.zl.falling,
                             zb=ps.zl.below_ema, sig=sig, pos=view.position.market_position.name, ent=ent))
        return state, d


class L4Diag(L4ConsolShortV1410):
    log = []

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.shadow = DailyMaBlock()

    def on_bar(self, view, state):
        p = self.config.params
        d2, d3 = view.data2, view.data3
        ready = not (d2 is None or d3 is None or len(d2) < 100 or len(d3) < 100)
        macro = self.shadow.update(d3.close, p["Daily_FastMA_Len"], p["Daily_SlowMA_Len"], p["Macro_Mode"]) if ready else None
        state, d = super().on_bar(view, state)
        if ready:
            ps = state.per_session
            down = d2.close[0] < average(d2.close, p["Weekly_MA_Len"])
            ent = [o.label for o in d.orders if o.label == "CS_Entry"]
            self.log.append(dict(d=view.mc_date, t=view.mc_time, c=view.data1.close[0], down=down, macro=macro,
                                 box=ps.box.valid, trap=ps.trap.active,
                                 slow=average(d3.close, p["Daily_SlowMA_Len"]),
                                 ma60m=average(d2.close, p["Weekly_MA_Len"]),
                                 pos=view.position.market_position.name, ent=ent))
        return state, d


def stats(tr):
    eq = pk = mdd = 0
    win = loss = gp = gl = streak = maxl = 0
    for t in sorted(tr, key=lambda x: x[3]):
        eq += t[6]; pk = max(pk, eq); mdd = max(mdd, pk - eq)
        if t[6] > 0:
            win += 1; gp += t[6]; streak = 0
        else:
            loss += 1; gl += -t[6]; streak += 1; maxl = max(maxl, streak)
    pf = gp / gl if gl else float("inf")
    return dict(n=len(tr), net=eq, mdd=mdd, pf=pf, win=(win / len(tr) * 100 if tr else 0), maxl=maxl)


def main():
    data = sys.argv[1]
    end = int("1" + (sys.argv[2] if len(sys.argv) > 2 else "261119"))
    out = []
    say = lambda s="": (print(s), out.append(s))
    mins = [m for m in MC12MinuteSource(data).stream() if 1180101 <= m.mc_date <= end]
    say(f"資料：{data}  {ts(mins[0].mc_date, mins[0].mc_time)} → {ts(mins[-1].mc_date, mins[-1].mc_time)}，{len(mins):,} 根 1 分 K（2018 起）")
    l2mins = [m for m in mins if m.mc_date >= 1190102]
    b60 = list(aggregate_bars(l2mins, 60))
    mc0 = next(csv.DictReader(open(os.path.join(ROOT, "tests", "fixtures", "mc_L2_v5.10_trades.csv"))))["entry_dt"]
    pol = mc_compat.POLICY

    def run(strat):
        res = mc_compat.single_runner(strat, pol).run(b60)
        tr = [t for t in res.trades if ts(t.entry_date, t.entry_time) >= mc0]
        return [(ts(t.entry_date, t.entry_time), t.entry_label, t.entry_price, ts(t.exit_date, t.exit_time),
                 t.exit_label, t.exit_price, round(t.net_ntd(TXF))) for t in tr], res

    v511, _ = run(L2TrendShortV511())
    r0, _ = run(L2V512(new=dict(NEW, Reb_On=0)))
    L2Diag.log = []
    r1, res1 = run(L2Diag(new=dict(NEW, Reb_On=1)))
    rows = [("v5.11（10/5 上架版）", v511), ("v5.12 回升保本關（11/16 決定）", r0), ("v5.12 回升保本開（上架機原碼）", r1)]

    periods = [("全期（MC 報表起 %s）" % mc0[:10], lambda t: True),
               ("2020–2025", lambda t: "2020" <= t[3][:4] <= "2025"),
               ("2026", lambda t: t[3][:4] == "2026"),
               ("11/16 決定時的資料（到 2026-11-07）", lambda t: t[3][:10] <= "2026-11-07"),
               ("決定後的新資料（2026-11-08 起）", lambda t: t[3][:10] >= "2026-11-08"),
               ("上架以來（2026-10-05 起）", lambda t: t[0][:10] >= "2026-10-05")]
    say()
    say("## L2 三版績效（推論；MC 口徑 大台 2 口，微台 ＝ ÷20）")
    for pname, f in periods:
        say(f"### {pname}")
        say("| 版本 | 筆數 | 淨利 | 最大回撤 | 獲利因子 | 勝率 | 最長連虧 |")
        say("|---|---|---|---|---|---|---|")
        for name, tr in rows:
            s = stats([t for t in tr if f(t)])
            say(f"| {name} | {s['n']} | {s['net']:,} | {s['mdd']:,} | {s['pf']:.2f} | {s['win']:.0f}% | {s['maxl']} |")
    say()
    say("### 逐年淨利")
    years = sorted({t[3][:4] for _, tr in rows for t in tr})
    say("| 年 | " + " | ".join(n for n, _ in rows) + " | 開 − 關 |")
    say("|---|" + "---|" * (len(rows) + 1))
    for y in years:
        v = [sum(t[6] for t in tr if t[3][:4] == y) for _, tr in rows]
        say(f"| {y} | " + " | ".join(f"{x:,}" for x in v) + f" | {v[2] - v[1]:+,} |")
    say()
    say("### 回升保本開／關 交易不同的地方（開 − 關）")
    a, b = set(r0), set(r1)
    for x in sorted(a - b): say(f"- 只在「關」：{x}")
    for x in sorted(b - a): say(f"- 只在「開」：{x}")
    reb = [t for t in r1 if t[4] == "TS_Rebound"]
    say(f"- 「開」版本以 TS_Rebound 出場 {len(reb)} 筆")

    # ---- 最近 N 個交易日
    days = sorted({m.mc_date for m in mins})[-RECENT_DAYS:]
    first = days[0]
    say()
    say(f"## 最近 {RECENT_DAYS} 個交易日（{ts(first, 0)[:10]} → {ts(days[-1], 0)[:10]}）")
    say("### 日線收盤")
    daily = {}
    for m in mins:
        if m.mc_date >= first and m.mc_time == 1345:
            daily[m.mc_date] = m.close
    say("| 日期 | 13:45 收盤 |")
    say("|---|---|")
    for k in sorted(daily): say(f"| {ts(k, 0)[:10]} | {daily[k]:,.0f} |")
    lg = [r for r in L2Diag.log if r["d"] >= first]
    last_tr = [t for t in res1.trades][-5:]
    say("### L2（上架機原碼，60 分 K）")
    say(f"- 最近 5 筆交易：")
    for t in last_tr:
        say(f"  - {ts(t.entry_date, t.entry_time)} {t.entry_label} {t.entry_price:,.0f} → {ts(t.exit_date, t.exit_time)} {t.exit_label} {t.exit_price:,.0f}  {round(t.net_ntd(TXF)):,}")
    say(f"- 週線濾網（上週五 12:45 收盤 < 13 週均線才准一般空單）：最後一根 wk_ok={lg[-1]['wk_ok']}，上週收盤 {lg[-1]['wk_last']:,.0f}，13 週均線 {lg[-1]['wk_sma']:,.0f}")
    cnt = collections.Counter()
    for r in lg:
        cnt["根數"] += 1; cnt["週線准空"] += r["wk_ok"]; cnt["跌破通道"] += r["brk"]
        cnt["ZLEMA 下彎"] += r["zf"]; cnt["ZLEMA 在均線下"] += r["zb"]; cnt["一般空單訊號"] += r["sig"]
        cnt["實際下進場單"] += bool(r["ent"])
    say("- 條件成立根數：" + "、".join(f"{k} {v}" for k, v in cnt.items()))
    say("| 時間 | 收盤 | 週線准空 | 通道下緣−0.45ATR | 跌破 | ZLEMA 下彎 | ZLEMA 在均線下 | 訊號 | 部位 | 進場單 |")
    say("|---|---|---|---|---|---|---|---|---|---|")
    for r in lg:
        say(f"| {ts(r['d'], r['t'])} | {r['c']:,.0f} | {'是' if r['wk_ok'] else '否'} | {r['dcl']:,.0f} | {'是' if r['brk'] else '否'} | "
            f"{'是' if r['zf'] else '否'} | {'是' if r['zb'] else '否'} | {'是' if r['sig'] else '否'} | {r['pos']} | {','.join(r['ent'])} |")

    say("### L4（15 分 K；60 分、日線）")
    L4Diag.log = []
    res4 = mc_compat.multi_runner(L4Diag()).run(list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)),
                                                build(mins, NIGHT_FIRST))
    say("- 最近 5 筆交易：")
    for t in res4.trades[-5:]:
        say(f"  - {ts(t.entry_date, t.entry_time)} {t.entry_label} {t.entry_price:,.0f} → {ts(t.exit_date, t.exit_time)} {t.exit_label} {t.exit_price:,.0f}  {round(t.net_ntd(TXF)):,}")
    l4 = [r for r in L4Diag.log if r["d"] >= first]
    cnt = collections.Counter()
    for r in l4:
        cnt["根數"] += 1; cnt["60 分在 48 均線下"] += r["down"]; cnt["日線沒擋"] += (not r["macro"])
        cnt["有盤整箱"] += r["box"]; cnt["誘多區啟動"] += r["trap"]; cnt["實際下進場單"] += bool(r["ent"])
    say("- 條件成立根數：" + "、".join(f"{k} {v}" for k, v in cnt.items()))
    say(f"- 最後一根：收盤 {l4[-1]['c']:,.0f}、日線 60 日均線 {l4[-1]['slow']:,.0f}、60 分 48 均線 {l4[-1]['ma60m']:,.0f}、日線擋空 {l4[-1]['macro']}")
    byday = collections.defaultdict(collections.Counter)
    for r in l4:
        c = byday[r["d"]]
        c["n"] += 1; c["down"] += r["down"]; c["open"] += (not r["macro"]); c["box"] += r["box"]; c["trap"] += r["trap"]; c["ent"] += bool(r["ent"])
    say("| 日期 | 根數 | 60 分在均線下 | 日線沒擋 | 有盤整箱 | 誘多區 | 進場 |")
    say("|---|---|---|---|---|---|---|")
    for k in sorted(byday):
        c = byday[k]
        say(f"| {ts(k, 0)[:10]} | {c['n']} | {c['down']} | {c['open']} | {c['box']} | {c['trap']} | {c['ent']} |")

    path = os.path.join(os.path.dirname(__file__), f"result_{end % 1000000:06d}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("寫入", path)


if __name__ == "__main__":
    main()
