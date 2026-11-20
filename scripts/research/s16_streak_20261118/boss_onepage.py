"""S16 老闆一頁式重點圖 v2（Willy 11/19 逐段確認的內容）。
數字全部由 MC 報表交易重算（v1281c＝新版 B、R0＝現行 0825），2023-01-01～2026-11-16 12:20 平倉。
資金由參數給（Willy 11/19：「報酬率以單策略資金 60,000 計」）。報酬率、回落比例都用這個資金算。
配色：新版 #c98500、現行 #3987e5，底色 #141517（dataviz 驗色深色模式全部通過）。

Usage: python -I boss_onepage.py <mc_B.csv> <mc_0825.csv> <out.png> [資金，預設 60000]
"""
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mc_boss_stats import load  # noqa: E402
from vol_gate_years import micro_net  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402

plt.rcParams.update({"font.family": "Microsoft JhengHei", "axes.unicode_minus": False})
BG, PANEL, GRID = "#141517", "#1d1e21", "#2c2d31"
NEWBG, OLDBG = "#2a2214", "#15202e"          # 新版／現行欄位底色（同色系深底）
INK, INK2, INK3 = "#f2f2f0", "#b9bab6", "#85867f"
NEW, OLD, HL = "#c98500", "#3987e5", "#f0b429"
SY = int(sys.argv[5]) if len(sys.argv) > 5 else 2023      # 起始年：2025＝簡報版（Willy 11/19），2023＝保留版
A, CUT = datetime(SY, 1, 1), datetime(2026, 11, 16, 12, 20)
YRS = (CUT - A).days / 365
W, H = 9.0, (18.2 if SY <= 2023 else 17.45)
L0, R0 = 0.5, 8.5


def stats(tr, cap):
    sel = [t for t in tr if A <= t.exit_dt <= CUT]
    pn = [micro_net(t) for t in sel]
    x = full_stats(pn, YRS)
    x["ann"] = x["net"] / cap / YRS * 100
    x["mddp"] = -x["mdd"] / cap * 100
    x["yr"] = {}
    for y in range(SY, 2027):
        v = [micro_net(t) for t in sel if t.exit_dt.year == y]
        x["yr"][y] = dict(n=len(v), net=sum(v), win=sum(1 for z in v if z > 0) / len(v) if v else 0.0)
    x["curve"] = sorted((t.exit_dt, micro_net(t)) for t in sel)
    return x


def main():
    cap = float(sys.argv[4]) if len(sys.argv) > 4 else 60_000
    b, o = stats(load(sys.argv[1]), cap), stats(load(sys.argv[2]), cap)
    fig = plt.figure(figsize=(W, H), dpi=150, facecolor=BG)
    tr = fig.dpi_scale_trans
    rend = fig.canvas.get_renderer()

    def T(x, y, s, size=11, color=INK, weight="normal", ha="left", va="top"):
        return fig.text(x, H - y, s, transform=tr, fontsize=size, color=color, fontweight=weight, ha=ha, va=va)

    def rich(x, y, parts, size, weight="bold"):
        for s, c in parts:
            t = T(x, y, s, size, c, weight)
            x += t.get_window_extent(rend).width / fig.dpi

    def hline(y, x0=L0, x1=R0, color=GRID, lw=0.8):
        fig.add_artist(plt.Line2D([x0, x1], [H - y, H - y], transform=tr, color=color, lw=lw))

    def box(x, y, w, h, fc, ec="none", lw=0):
        fig.add_artist(FancyBboxPatch((x, H - y - h), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                      transform=tr, facecolor=fc, edgecolor=ec, lw=lw))

    # 1. 標題與結論
    y = 0.45
    T(L0, y, "空方 MA 趨勢策略", 21, INK, "bold"); y += 0.62
    rich(L0, y, [("只多一條進場規則：最深回落 ", INK), (f"{o['mddp']:.0f}% → {b['mddp']:.0f}%", HL), ("，", INK)], 15.5)
    y += 0.40
    rich(L0, y, [("年化報酬 ", INK), (f"{o['ann']:.0f}% → {b['ann']:.0f}%", HL),
                 (f"，{SY}–2026 每一年都比現行版多賺。", INK)], 15.5)
    y += 0.62

    # 2. 策略是什麼：左（賺什麼、憑什麼）右（最不適合）
    bh = 1.95
    cw = (R0 - L0 - 0.2) / 2
    box(L0, y, cw, bh, PANEL); box(L0 + cw + 0.2, y, cw, bh, PANEL)
    xl, xr = L0 + 0.2, L0 + cw + 0.4
    T(xl, y + 0.16, "賺什麼錢", 10, INK3)
    T(xl, y + 0.40, "台指期往下急跌那一段", 12, INK, "bold")
    T(xl, y + 0.78, "憑什麼賺錢", 10, INK3)
    for k, s in enumerate(("轉空後急跌機率高 8 倍", "虧損快砍、獲利抱到停利", "只在波動夠大時出手")):
        T(xl, y + 1.02 + k * 0.28, f"・{s}", 11, INK)
    T(xr, y + 0.16, "最不適合哪些行情", 10, INK3)
    for k, s in enumerate(("波動很小的盤整", "跌一下就拉回的假急殺", "一路慢漲的多頭", "開盤直接跳空大跌")):
        T(xr, y + 0.44 + k * 0.32, f"・{s}", 11, INK)
    y += bh + 0.2

    # 3. 新版四個數字
    kp = [("每口每筆期望值", f"{b['exp'] / 2:,.0f} 元"), ("年化報酬", f"{b['ann']:.1f}%"),
          ("勝率", f"{b['win'] * 100:.1f}%"), ("最深回落（MDD）", f"{b['mddp']:.1f}%")]
    tw = (R0 - L0 - 0.15 * 3) / 4
    for k, (lab, v) in enumerate(kp):
        x = L0 + k * (tw + 0.15)
        box(x, y, tw, 0.95, PANEL)
        T(x + 0.15, y + 0.13, f"新版　{lab}", 9.5, INK2)
        T(x + 0.15, y + 0.42, v, 19, HL, "bold")
    y += 0.95 + 0.5

    # 4. 這次優化了什麼
    T(L0, y, "這次優化了什麼", 13, INK, "bold"); y += 0.38
    for s in (f"最長連續虧損：{o['streak']} 筆 → {b['streak']} 筆（少 {(1 - b['streak'] / o['streak']) * 100:.0f}%）",
              f"年化報酬：{o['ann']:.0f}% → {b['ann']:.0f}%",
              f"最深回落（MDD）：{o['mddp']:.0f}% → {b['mddp']:.0f}%"):
        T(L0, y, f"・{s}", 11.5, INK); y += 0.30
    y += 0.3

    # 5. 前後差異（Willy 確認的格式）
    T(L0, y, "前後差異", 13, INK, "bold"); y += 0.40
    cx = [L0, 3.0, 4.6, 6.2]
    t0 = y - 0.08
    for x, s in zip(cx, ["項目", "現行", "新版", "變化"]):
        T(x, y, s, 9.5, HL if s == "新版" else INK3, "bold")
    y += 0.30; hline(y)
    rows = [("年化報酬", f"{o['ann']:.1f}%", f"{b['ann']:.1f}%", f"+{b['ann'] - o['ann']:.1f} 個百分點"),
            ("最深回落（佔資金）", f"{o['mddp']:.1f}%", f"{b['mddp']:.1f}%", f"少 {(1 - b['mdd'] / o['mdd']) * 100:.0f}%"),
            ("最長連續虧損", f"{o['streak']} 筆", f"{b['streak']} 筆", f"{o['streak_amt']:,.0f} → {b['streak_amt']:,.0f} 元"),
            ("勝率", f"{o['win'] * 100:.1f}%", f"{b['win'] * 100:.1f}%", f"+{(b['win'] - o['win']) * 100:.1f} 個百分點"),
            ("每口每筆平均賺", f"{o['exp'] / 2:,.0f} 元", f"{b['exp'] / 2:,.0f} 元", f"多 {(b['exp'] / o['exp'] - 1) * 100:.0f}%")]
    for r in rows:
        y += 0.10
        for x, s in zip(cx, r):
            T(x, y, s, 11.5 if x == 4.6 else 10.5, HL if x == 4.6 else INK, "bold" if x == 4.6 else "normal")
        y += 0.27; hline(y)
    fig.add_artist(FancyBboxPatch((4.5, H - y - 0.06), 1.45, y + 0.06 - t0, boxstyle="round,pad=0,rounding_size=0.05",
                                  transform=tr, facecolor="none", edgecolor=HL, lw=1.6))
    y += 0.5

    # 6. 累積獲利圖
    T(L0, y, "累積獲利：新版較高，而且中途回落較小", 13, INK, "bold"); y += 0.32
    rich(L0, y, [("━ ", NEW), ("新版", INK2), ("    ━ ", OLD), ("現行版", INK2), ("    ● ", "#e66767"), ("新版創新高", INK2), ("    單位：萬元", INK3)], 9.5, "normal")
    y += 0.30
    ch_h = 2.7
    ax = fig.add_axes([(L0 + 0.55) / W, (H - y - ch_h) / H, (R0 - L0 - 1.75) / W, ch_h / H], facecolor=BG)
    for name, x_, col in (("新版", b, NEW), ("現行版", o, OLD)):
        d, cum, s = [A], [0.0], 0.0
        for dt_, v in x_["curve"]:
            s += v; d.append(dt_); cum.append(s / 10000)
        d.append(CUT); cum.append(cum[-1])
        ax.plot(d, cum, color=col, lw=2, drawstyle="steps-post")
        if name == "新版":                      # 創新高的那筆：紅色實心點（Willy 11/19）
            pk = 0.0; hx, hy = [], []
            for dd_, cc in zip(d[1:-1], cum[1:-1]):
                if cc > pk:
                    pk = cc; hx.append(dd_); hy.append(cc)
            ax.scatter(hx, hy, s=22, color="#e66767", edgecolors=BG, linewidths=0.8, zorder=5)
        ax.text(CUT, cum[-1], f"  {name} {cum[-1]:.1f} 萬", color=INK, fontsize=10, va="center",
                fontweight="bold" if name == "新版" else "normal")
    ax.axhline(0, color=INK3, lw=0.8, ls=(0, (3, 3)))
    ax.grid(axis="y", color=GRID, lw=0.6)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=INK3, labelsize=9, length=0)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(A, CUT)
    y += ch_h + 0.5

    # 7. 逐年表（新版／現行分色區塊）
    T(L0, y, f"逐年績效：{2027 - SY} 年裡每一年，新版都比現行版多賺", 13, INK, "bold"); y += 0.42
    gx = [(L0, 1.95), (1.95, 5.75), (5.75, 7.35), (7.35, R0)]   # 年｜新版｜現行版｜差異
    tbl_top = y
    n_rows = 2028 - SY
    tbl_h = 0.32 + 0.30 + n_rows * 0.37 + 0.05
    for (x0, x1), fc in zip(gx[1:3], (NEWBG, OLDBG)):
        fig.add_artist(Rectangle((x0, H - tbl_top - tbl_h), x1 - x0 - 0.04, tbl_h, transform=tr, facecolor=fc, edgecolor="none"))
    T((gx[1][0] + gx[1][1]) / 2, y + 0.05, "新版", 10, HL, "bold", ha="center")
    T((gx[2][0] + gx[2][1]) / 2, y + 0.05, "現行版", 10, OLD, "bold", ha="center")
    T((gx[3][0] + gx[3][1]) / 2, y + 0.05, "差異", 10, INK2, "bold", ha="center")
    y += 0.32
    cols = [(L0 + 0.05, "年", "left"), (2.55, "筆數", "right"), (3.65, "淨利", "right"), (4.75, "報酬率", "right"),
            (5.6, "勝率", "right"), (6.65, "報酬率", "right"), (7.25, "勝率", "right"), (R0 - 0.05, "新版多賺", "right")]
    for x, s, ha in cols:
        T(x, y, s, 9.5, INK3, ha=ha)
    y += 0.30; hline(y)
    rws = []
    for yr in range(SY, 2027):
        nb, no = b["yr"][yr], o["yr"][yr]
        rws.append(["2026（至 11/16）" if yr == 2026 else str(yr), f"{nb['n']}", f"{nb['net']:,.0f}", f"{nb['net'] / cap * 100:.1f}%",
                    f"{nb['win'] * 100:.0f}%", f"{no['net'] / cap * 100:.1f}%", f"{no['win'] * 100:.0f}%", f"{nb['net'] - no['net']:+,.0f}"])
    rws.append([f"{2027 - SY} 年合計", f"{b['n']}", f"{b['net']:,.0f}", f"年化 {b['ann']:.1f}%", f"{b['win'] * 100:.0f}%",
                f"年化 {o['ann']:.1f}%", f"{o['win'] * 100:.0f}%", f"{b['net'] - o['net']:+,.0f}"])
    for i, r in enumerate(rws):
        last = i == len(rws) - 1
        y += 0.10
        for (x, _, ha), s in zip(cols, r):
            T(x, y, s, 10.5, HL if (last and x == 4.75) else INK, "bold" if last else "normal", ha=ha)
        y += 0.27; hline(y)
    y += 0.4

    # 8. 註腳
    T(L0, y, f"數字來源：下單軟體 MultiCharts 回測，和電腦模擬逐筆一致。報酬率以單策略資金 {cap:,.0f} 計。", 8.8, INK3); y += 0.24
    T(L0, y, f"回測時間：{SY}–2026（{SY}/1/1～2026/11/16）", 8.8, INK3); y += 0.24
    out = Path(sys.argv[3]); out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG)
    print(f"{out} 用到 {y:.2f}/{H} 吋")
    print("KPI:", kp); print("rows:", rows); print("yr:", rws)


if __name__ == "__main__":
    main()
