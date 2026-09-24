#!/usr/bin/env python3
"""產出可以打開來看的回測報告。

**2026-09-07 補**：先前所有輸出都是終端機文字，跑完就消失。
沒有交易清單、沒有權益曲線、沒有可以拿給別人看的東西。

本工具產出：

    reports/backtest_report.html   總覽 + 權益曲線 + 對 anchor 比較
    reports/L2_trades.csv          逐筆交易清單
    reports/L3_trades.csv
    reports/L4_trades.csv
    reports/summary.csv            三支的彙總指標

用法：
    python tools/report.py "data\\mc_export\\TXF1 1 分鐘.txt"
"""
from __future__ import annotations

import argparse
import collections
import csv
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from txfcore.instruments.spec import TXF
from txfcore.metrics.drawdown import compute
from txfcore.parity.anchors import ANCHORS, window
from txfcore.parity.windows import IN_SAMPLE, OUT_SAMPLE, split
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.daily import DAY_FIRST, NIGHT_FIRST, build as build_daily
from txfcore.quotes.guard import banner, check
from txfcore.quotes.history import MC12MinuteSource
from txfcore.runtime.backtest import BacktestRunner
from txfcore.runtime.multi import MultiStreamRunner
from txfcore.strategies.l1_trendlong import L1TrendLong
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.strategies.l3_consollong import L3ConsolLong
from txfcore.strategies.l4_consolshort import L4ConsolShort
from txfcore.strategies.l5_breakoutlong import L5BreakoutLong
from txfcore.types.mctime import DayOfWeek, day_of_week
from txfcore.types.bar import Bar
from txfcore.types.mctime import mc_date_to_date, trading_day

C = dict(bg="#16202B", panel="#1D2A38", p2="#223347", rule="#33475C",
         ink="#DCE6EE", mu="#8399AC", up="#6FD1B4", dn="#E8735E", hd="#F0B45A")


def daily_bars(mins):
    b: dict = {}
    for m in mins:
        b.setdefault(trading_day(m.mc_date, m.mc_time), []).append(m)
    out = []
    for d in sorted(b):
        g = b[d]
        last = g[-1]
        out.append(Bar(last.mc_date, last.mc_time, g[0].open,
                       max(x.high for x in g), min(x.low for x in g),
                       g[-1].close, sum(x.volume for x in g), len(g)))
    return out


def weekly_bars(dd):
    """週線：以週五收盤合成。"""
    wk, buf = [], []
    for x in dd:
        buf.append(x)
        if day_of_week(x.mc_date) is DayOfWeek.FRI:
            wk.append(Bar(x.mc_date, x.mc_time, buf[0].open,
                          max(y.high for y in buf), min(y.low for y in buf),
                          x.close, sum(y.volume for y in buf), len(buf)))
            buf = []
    if buf:
        x = buf[-1]
        wk.append(Bar(x.mc_date, x.mc_time, buf[0].open,
                      max(y.high for y in buf), min(y.low for y in buf),
                      x.close, sum(y.volume for y in buf), len(buf)))
    return wk


def cached(cd: Path, name: str, build):
    f = cd / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = build()
    f.write_bytes(pickle.dumps(v))
    return v


def stats(trades, inst=TXF) -> dict:
    if not trades:
        return dict(n=0, net=0.0, pf=0.0, wr=0.0, avg_win=0.0, avg_loss=0.0,
                    best=0.0, worst=0.0)
    pnl = [t.net_ntd(inst) for t in trades]
    w = [x for x in pnl if x > 0]
    l = [x for x in pnl if x <= 0]
    return dict(
        n=len(trades), net=sum(pnl),
        pf=sum(w) / -sum(l) if l and sum(l) else 0.0,
        wr=len(w) / len(pnl) * 100,
        avg_win=sum(w) / len(w) if w else 0.0,
        avg_loss=sum(l) / len(l) if l else 0.0,
        best=max(pnl), worst=min(pnl),
    )


def equity_svg(equity: list[float], w: int = 880, h: int = 200) -> str:
    if len(equity) < 2:
        return ""
    lo, hi = min(equity), max(equity)
    span = hi - lo or 1
    pk = equity[0]
    peaks = []
    for v in equity:
        pk = max(pk, v)
        peaks.append(pk)
    def pt(i, v):
        x = 40 + (w - 60) * i / (len(equity) - 1)
        y = h - 26 - (h - 46) * (v - lo) / span
        return f"{x:.1f},{y:.1f}"
    line = " ".join(pt(i, v) for i, v in enumerate(equity))
    peak = " ".join(pt(i, v) for i, v in enumerate(peaks))
    base = pt(0, equity[0]).split(",")[1]
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>'
        f'<line x1="40" y1="{base}" x2="{w-20}" y2="{base}" '
        f'stroke="{C["rule"]}" stroke-dasharray="3 3"/>'
        f'<polyline points="{peak}" fill="none" stroke="{C["rule"]}" stroke-width="1"/>'
        f'<polyline points="{line}" fill="none" stroke="{C["up"]}" stroke-width="1.6"/>'
        f'<text x="6" y="18" font-size="10" fill="{C["mu"]}">{hi:,.0f}</text>'
        f'<text x="6" y="{h-8}" font-size="10" fill="{C["mu"]}">{lo:,.0f}</text>'
        f"</svg>"
    )


def write_trades_csv(path: Path, trades, inst=TXF) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["進場日期", "進場時間", "進場價", "進場標籤",
                     "出場日期", "出場時間", "出場價", "出場標籤",
                     "方向", "口數", "點數", "毛損益", "成本", "淨損益"])
        for t in trades:
            wr.writerow([
                mc_date_to_date(t.entry_date), f"{t.entry_time:04d}",
                f"{t.entry_price:.0f}", t.entry_label,
                mc_date_to_date(t.exit_date), f"{t.exit_time:04d}",
                f"{t.exit_price:.0f}", t.exit_label,
                "多" if t.direction.value == 1 else "空", t.quantity,
                f"{t.gross_points:.0f}", f"{t.gross_ntd(inst):.0f}",
                f"{t.cost:.0f}", f"{t.net_ntd(inst):.0f}",
            ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--cache-dir", default=".")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    cd = Path(args.cache_dir)

    print(banner(args.data))
    check(args.data)
    print("讀取與聚合…")
    mins = list(MC12MinuteSource(args.data).stream())
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m45 = cached(cd, "45m", lambda: list(aggregate_bars(mins, 45)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: build_daily(mins, DAY_FIRST))
    mdn = cached(cd, "dn", lambda: build_daily(mins, NIGHT_FIRST))
    mw = cached(cd, "w", lambda: weekly_bars(md))
    mwn = cached(cd, "wn", lambda: weekly_bars(mdn))
    print(f"  1分K {len(mins):,}   15M {len(m15):,}   45M {len(m45):,}"
          f"   60M {len(m60):,}   D {len(md):,}   W {len(mw):,}\n")

    runs = []
    for key, runner in (
        ("L1", lambda: MultiStreamRunner(L1TrendLong(), TXF,
                                         warmup_bars=200).run(m45, md, mw)),
        ("L2", lambda: BacktestRunner(L2TrendShort(), TXF).run(m60)),
        ("L3", lambda: MultiStreamRunner(L3ConsolLong(), TXF,
                                         warmup_bars=200).run(m15, m60, md)),
        ("L4", lambda: MultiStreamRunner(L4ConsolShort(), TXF,
                                         warmup_bars=200).run(m15, m60, md)),
        ("L5", lambda: MultiStreamRunner(L5BreakoutLong(), TXF,
                                         warmup_bars=200).run(m15, mdn, mwn)),
    ):
        print(f"跑 {key}…")
        r = runner()
        a = ANCHORS[key]
        tl = window(r.trades, a)
        s = stats(tl)
        ins, outs, _ = split(r.trades)   # 樣本內 / 樣本外
        write_trades_csv(out / f"{key}_trades.csv", tl)
        runs.append((key, a, r, tl, s, ins, outs))
        print(f"  {s['n']} 筆   淨 {s['net']:,.0f}   PF {s['pf']:.3f}"
              f"   vs MC {a.total_trades} 筆   差 {s['n']-a.total_trades:+d}")

    # ---- summary.csv ----
    with (out / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["策略", "版本", "視窗起", "視窗迄", "筆數", "MC筆數", "差",
                     "淨利", "MC淨利", "PF", "MC PF", "勝率", "MC勝率",
                     "最大回撤%", "最大回撤金額", "最長回撤期數", "水下比例%"])
        for key, a, r, tl, s, ins, outs in runs:
            dd = compute(r.ledger.equity())
            wr.writerow([
                a.strategy, a.version,
                a.backtest_start or "—", a.backtest_end or a.export_date,
                s["n"], a.total_trades, s["n"] - a.total_trades,
                f"{s['net']:.0f}", f"{a.net_profit:.0f}",
                f"{s['pf']:.4f}", f"{a.profit_factor:.4f}",
                f"{s['wr']:.2f}", f"{a.win_rate:.2f}" if a.win_rate else "—",
                f"{dd.max_drawdown*100:.2f}", f"{dd.max_drawdown_amount:.0f}",
                f"{dd.drawdown_duration}", f"{dd.underwater_ratio*100:.1f}",
            ])

    # ---- HTML ----
    h = [f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TXF1 Python 移植 回測報告</title><style>
body{{margin:0;background:{C['bg']};color:{C['ink']};
font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
font-size:15px;line-height:1.7}}
.w{{max-width:960px;margin:0 auto;padding:40px 20px 80px}}
h1{{font-size:30px;font-weight:600;margin:0 0 6px}}
.sub{{color:{C['mu']};font-family:ui-monospace,Menlo,monospace;font-size:12px;margin:0 0 34px}}
h2{{font-size:20px;margin:52px 0 4px;padding-bottom:10px;border-bottom:1px solid {C['rule']}}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:14px 0}}
th,td{{text-align:right;padding:8px 10px;border-bottom:1px solid {C['rule']}}}
th:first-child,td:first-child{{text-align:left}}
th{{color:{C['mu']};font-size:12.5px;background:{C['p2']}}}
td.m{{font-family:ui-monospace,Menlo,monospace}}
.up{{color:{C['up']}}} .dn{{color:{C['dn']}}} .hd{{color:{C['hd']}}}
svg{{display:block;width:100%;height:auto;margin:10px 0}}
.card{{border:1px solid {C['rule']};background:{C['panel']};margin:0 0 24px}}
.card h3{{margin:0;padding:14px 18px;background:{C['p2']};font-size:16px;
border-bottom:1px solid {C['rule']}}}
.card .b{{padding:14px 18px}}
.note{{border-left:3px solid {C['hd']};background:rgba(240,180,90,.06);
padding:10px 15px;font-size:13.5px;margin:12px 0}}
.f{{border-top:1px solid {C['rule']};margin-top:50px;padding-top:18px;
color:{C['mu']};font-size:13px}}
</style></head><body><div class="w">
<h1>TXF1 Python 移植 回測報告</h1>
<p class="sub">{banner(args.data)}　·　1分K {len(mins):,} 列</p>

<h2>一 三支對 MC12 anchor</h2>
<table><thead><tr><th>策略</th><th>版本</th><th>視窗</th>
<th>筆數</th><th>MC</th><th>差</th><th>淨利</th><th>MC淨利</th>
<th>PF</th><th>MC PF</th><th>勝率</th></tr></thead><tbody>"""]
    for key, a, r, tl, s, ins, outs in runs:
        d = s["n"] - a.total_trades
        cls = "up" if abs(d) <= 3 else "hd"
        win = f"{a.backtest_start}~{a.backtest_end or a.export_date}"
        h.append(
            f'<tr><td><b>{key}</b> {a.strategy.split("_")[1]}</td>'
            f'<td class="m">{a.version}</td><td class="m">{win}</td>'
            f'<td class="m">{s["n"]}</td><td class="m">{a.total_trades}</td>'
            f'<td class="m {cls}"><b>{d:+d}</b></td>'
            f'<td class="m">{s["net"]:,.0f}</td><td class="m">{a.net_profit:,.0f}</td>'
            f'<td class="m">{s["pf"]:.3f}</td><td class="m">{a.profit_factor:.3f}</td>'
            f'<td class="m">{s["wr"]:.1f}%</td></tr>')
    h.append("</tbody></table>")
    # ---- 樣本內 / 樣本外 ----
    h.append("<h2>二 樣本內 vs 樣本外</h2>")
    h.append('<div class="note"><b>2026-06-17 是真實下單開始的日子。</b>'
             '先前所有回測都跑到 2026-09-05，把樣本內外混在一起——'
             '**樣本外的衰退完全看不出來**。</div>')
    h.append('<table><thead><tr><th>策略</th>'
             '<th>樣本內筆數</th><th>樣本內淨利</th><th>樣本內 PF</th>'
             '<th>樣本外筆數</th><th>樣本外淨利</th><th>樣本外 PF</th>'
             "</tr></thead><tbody>")
    ti = to = 0
    ni = no = 0.0
    for key, a, r, tl, s, ins, outs in runs:
        si, so = stats(ins), stats(outs)
        ti += si["n"]; to += so["n"]; ni += si["net"]; no += so["net"]
        cls = "up" if so["pf"] >= 1 else "dn"
        h.append(f'<tr><td><b>{key}</b></td>'
                 f'<td class="m">{si["n"]}</td>'
                 f'<td class="m">{si["net"]:,.0f}</td>'
                 f'<td class="m">{si["pf"]:.3f}</td>'
                 f'<td class="m">{so["n"]}</td>'
                 f'<td class="m {cls}">{so["net"]:,.0f}</td>'
                 f'<td class="m {cls}">{so["pf"]:.3f}</td></tr>')
    h.append(f'<tr><td><b>合計</b></td><td class="m">{ti}</td>'
             f'<td class="m">{ni:,.0f}</td><td></td>'
             f'<td class="m">{to}</td><td class="m">{no:,.0f}</td><td></td></tr>')
    h.append("</tbody></table>")
    h.append(f'<div class="note w">Python 樣本外 <b>{to} 筆</b>，'
             f'實戰紀錄 <b>59 筆</b>（微台 2 口，期初 300,000）。<br>'
             '商品不同，金額需換算；筆數可直接比。</div>')
    h.append('<h2>三 對 MC12 anchor</h2>')
    h.append('<div class="note">差 = Python 筆數 − MC 筆數。'
             '<b>視窗每支不同，且影響極大</b>——L3 用 2019-12-16 是 +23，'
             '用標頭明載的 2020-05-12 是 +3。</div>')

    for key, a, r, tl, s, ins, outs in runs:
        dd = compute(r.ledger.equity())
        ex = collections.Counter(t.exit_label for t in tl)
        en = collections.Counter(t.entry_label for t in tl)
        h.append(f'<h2>{key} {a.strategy} {a.version}</h2><div class="card">'
                 f'<h3>權益曲線（期初 {MC_BACKTEST_CAPITAL:,.0f}，MC 對帳基準）</h3><div class="b">')
        h.append(equity_svg(r.ledger.equity()))
        h.append(f"""</div></div>
<table><tbody>
<tr><td>筆數</td><td class="m">{s['n']}</td><td>淨利</td><td class="m">{s['net']:,.0f}</td>
<td>PF</td><td class="m">{s['pf']:.4f}</td><td>勝率</td><td class="m">{s['wr']:.2f}%</td></tr>
<tr><td>平均獲利</td><td class="m up">{s['avg_win']:,.0f}</td>
<td>平均虧損</td><td class="m dn">{s['avg_loss']:,.0f}</td>
<td>最大單筆</td><td class="m up">{s['best']:,.0f}</td>
<td>最差單筆</td><td class="m dn">{s['worst']:,.0f}</td></tr>
<tr><td>最大回撤</td><td class="m">{dd.max_drawdown*100:.2f}%</td>
<td>金額</td><td class="m">{dd.max_drawdown_amount:,.0f}</td>
<td>最長回撤</td><td class="m">{dd.drawdown_duration} 期</td>
<td>水下比例</td><td class="m">{dd.underwater_ratio*100:.1f}%</td></tr>
</tbody></table>
<table><thead><tr><th>進場標籤</th><th>筆數</th><th>出場標籤</th><th>筆數</th>
<th>勝率</th><th>淨損益</th></tr></thead><tbody>""")
        rows = max(len(en), len(ex))
        ei = list(en.most_common())
        xi = list(ex.most_common())
        for i in range(rows):
            a1 = f'<td>{ei[i][0]}</td><td class="m">{ei[i][1]}</td>' if i < len(ei) else "<td></td><td></td>"
            if i < len(xi):
                lbl, n = xi[i]
                grp = [t.net_ntd(TXF) for t in tl if t.exit_label == lbl]
                wn = sum(1 for x in grp if x > 0) / len(grp) * 100
                cls = "up" if sum(grp) > 0 else "dn"
                a2 = (f'<td>{lbl}</td><td class="m">{n}</td>'
                      f'<td class="m">{wn:.1f}%</td>'
                      f'<td class="m {cls}">{sum(grp):,.0f}</td>')
            else:
                a2 = "<td></td><td></td><td></td><td></td>"
            h.append(f"<tr>{a1}{a2}</tr>")
        h.append("</tbody></table>")
        if a.exit_labels:
            merged = dict(ex)
            if "ENGINE_STOP" in merged and "CS_SL" in a.exit_labels:
                merged["CS_SL"] = merged.get("CS_SL", 0) + merged.pop("ENGINE_STOP")
            cmp_rows = "".join(
                f'<tr><td>{k}</td><td class="m">{merged.get(k,0)}</td>'
                f'<td class="m">{v}</td>'
                f'<td class="m {"up" if merged.get(k,0)==v else "hd"}">'
                f'{merged.get(k,0)-v:+d}</td></tr>'
                for k, v in a.exit_labels.items())
            h.append('<div class="note"><b>對 MC 的出場標籤</b>'
                     f'<table><thead><tr><th>標籤</th><th>Python</th>'
                     f'<th>MC</th><th>差</th></tr></thead>'
                     f"<tbody>{cmp_rows}</tbody></table></div>")

    h.append(f"""<div class="f">
<p>逐筆清單：<code>{out}/L2_trades.csv</code>　<code>L3_trades.csv</code>　
<code>L4_trades.csv</code>　彙總：<code>summary.csv</code></p>
<p><b>五支全部移植完成。</b>本報告不證明「符合 MC」——那需要 MC 報告做逐筆 diff。<br>L1 為收盤評估，不是 IOG 逐 tick；L5 的 Stage 2/3 追蹤機制尚未觸發，兩者的落差已記錄。</p>
</div></div></body></html>""")

    (out / "backtest_report.html").write_text("".join(h), encoding="utf-8")
    print(f"\n產出於 {out.resolve()}")
    for f in sorted(out.glob("*")):
        print(f"  {f.name:<26}{f.stat().st_size:>9,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
