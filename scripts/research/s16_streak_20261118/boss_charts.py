"""11/20 老闆版的三張圖（一張一個結論；2 口微台、資金 140,200；MC 報表交易）。
資料：data/research_s16_20261118/mc_daily_0825_vs_B.csv（mc_boss_stats.py 產生；base＝0825、tod90d_p70＝B）
起點：Willy 11/19「今天的回測只放2023-2026」→ 傳 2023-01-01；不傳＝2020-01-01。
Usage: python -I scripts/research/s16_streak_20261118/boss_charts.py <daily.csv> <out_dir> [start YYYY-MM-DD]
"""
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

CAP = 140_200
NEW, OLD = "#2a78d6", "#eb6834"          # 參考色盤 slot 1、2（已跑 validate_palette：ALL PASS）
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({"font.family": "Microsoft JhengHei", "axes.unicode_minus": False, "font.size": 11})


def style(ax, title, sub):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.figure.text(0.06, 0.95, title, fontsize=16, fontweight="bold", color=INK, ha="left", va="top")
    ax.figure.text(0.06, 0.885, sub, fontsize=11, color=INK2, ha="left", va="top")


def main():
    start = date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else date(2020, 1, 1)
    rows = [r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")) if date.fromisoformat(r["date"]) >= start]
    per = f"{start.year}/{start.month}–2026/11/16"
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    d = [date.fromisoformat(r["date"]) for r in rows]
    series = {"新版 B": [float(r["tod90d_p70"]) for r in rows], "現行 0825": [float(r["base"]) for r in rows]}
    color = {"新版 B": NEW, "現行 0825": OLD}

    # 1. 累積損益
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150, facecolor=SURF)
    fig.subplots_adjust(top=0.80, left=0.09, right=0.86, bottom=0.10)
    for k, v in series.items():
        cum, s = [], 0.0
        for x in v:
            s += x; cum.append(s)
        ax.plot(d, cum, color=color[k], linewidth=2, label=k)
        ax.text(d[-1], cum[-1], f"  {k}\n  約 {cum[-1]/10000:.1f} 萬", color=INK, fontsize=10, va="center")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", frameon=False, labelcolor=INK2)
    style(ax, "新版累積獲利較高，而且中途回落較小", f"{per} 累積淨利（元）｜2 口微台、含滑價手續費稅｜MC 回測實證")
    fig.savefig(out / "s16_boss_1_equity.png", facecolor=SURF); plt.close(fig)

    # 2. 回落（佔資金 %）
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150, facecolor=SURF)
    fig.subplots_adjust(top=0.80, left=0.09, right=0.86, bottom=0.10)
    worst = {}
    for k, v in series.items():
        s = peak = 0.0; dd = []
        for x in v:
            s += x; peak = max(peak, s); dd.append((s - peak) / CAP * 100)
        worst[k] = min(dd)
        ax.plot(d, dd, color=color[k], linewidth=2 if k == "新版 B" else 1.6, label=k)
    ax.axhline(-15, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(d[0], -15.6, "上限：資金的 15%（21,030 元）", color=INK2, fontsize=10, va="top")
    for k in series:
        ax.text(d[-1], worst[k], f"  {k} 最深 {worst[k]:.1f}%", color=INK, fontsize=10, va="center")
    ax.set_ylim(min(worst.values()) - 3, 1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="lower left", frameon=False, labelcolor=INK2)
    style(ax, "最深回落從資金的 20% 降到 12%，回到 15% 上限之內", f"從最高點回落多少（佔 140,200 資金 %）｜{per}")
    fig.savefig(out / "s16_boss_2_drawdown.png", facecolor=SURF); plt.close(fig)

    # 3. 每年比 0825 多賺多少
    by = defaultdict(float)
    for dt, a, b in zip(d, series["新版 B"], series["現行 0825"]):
        by[dt.year] += a - b
    years = [y for y in sorted(by) if y >= max(2020, start.year)]   # 2019-12-31 夜盤只是日期歸屬，沒有交易
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150, facecolor=SURF)
    fig.subplots_adjust(top=0.80, left=0.09, right=0.97, bottom=0.10)
    ax.bar([str(y) for y in years], [by[y] for y in years], color=NEW, width=0.5)
    for y in years:
        ax.text(str(y), by[y], f"+{by[y]:,.0f}" if by[y] >= 0 else f"{by[y]:,.0f}", color=INK, fontsize=10,
                ha="center", va="bottom")
    ax.axhline(0, color=AXIS, linewidth=1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
    n_up = sum(1 for y in years if by[y] > 0)
    ttl = f"{len(years)} 年裡每一年，新版都比現行版多賺" if n_up == len(years) else f"{len(years)} 年裡有 {n_up} 年，新版比現行版多賺"
    style(ax, ttl, "每年淨利差：新版 B 減 現行 0825（元）｜2026 年至 11/16")
    fig.savefig(out / "s16_boss_3_yearly_gain.png", facecolor=SURF); plt.close(fig)
    print({y: round(by[y]) for y in years}, {k: round(v, 1) for k, v in worst.items()})


if __name__ == "__main__":
    main()
