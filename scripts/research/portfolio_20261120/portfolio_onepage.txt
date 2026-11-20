"""六支策略組合 老闆一頁式（版型同 scripts/research/s16_streak_20261118/boss_onepage.py）。
數字全部讀 MC 投資組合績效報告（Willy 11/20 匯出），大台 → 微台 ÷20，資金 30 萬（多單帳戶 15 萬＋空單帳戶 15 萬，Willy 11/20）。
- 組合每日損益：「Daily 週期分析」；筆數、勝率：「Annual 週期分析」（Daily 的次數會把分批出場重複算，不用）
- 各支：「商品概要」「權益曲線分析」；策略名稱由「交易明細」訊號名對應（TL→L1、CR/TS→L2、CL→L3、CS→L4、BL→L5、SE→L6）
- 年化＝單利（淨利 ÷ 資金 ÷ 年數）；回落＝每日平倉累積的最深回落（不含持倉浮動）

Usage: python -I scripts/research/portfolio_20261120/portfolio_onepage.py <報告.xls> <out.png> [起始年=2025] [資金=300000]
"""
import collections
import datetime as dt
import shutil
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import openpyxl  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

plt.rcParams.update({"font.family": "Microsoft JhengHei", "axes.unicode_minus": False})
BG, PANEL, GRID = "#141517", "#1d1e21", "#2c2d31"
NEWBG, OLDBG = "#2a2214", "#15202e"
INK, INK2, INK3 = "#f2f2f0", "#b9bab6", "#85867f"
NEW, OLD, HL = "#c98500", "#3987e5", "#f0b429"
SCALE = 20
SIG = {"TL": "L1", "CR": "L2", "TS": "L2", "CL": "L3", "CS": "L4", "BL": "L5", "SE": "L6"}
INFO = {"L1": ("趨勢多", "多"), "L2": ("趨勢空", "空"), "L3": ("盤整多", "多"),
        "L4": ("盤整空", "空"), "L5": ("突破多", "多"), "L6": ("均線空", "空")}


def read(path):
    tmp = tempfile.mkdtemp()
    wb = openpyxl.load_workbook(shutil.copy(path, tmp + "/r.xlsx"), read_only=True, data_only=True)
    cfg = {r[0]: r[1] for r in wb["設定"].iter_rows(values_only=True) if r[0]}
    daily = sorted((r[0], r[1], r[4], r[5]) for r in wb["Daily 週期分析"].iter_rows(values_only=True)
                   if isinstance(r[0], dt.datetime))
    syms = [r for r in wb["商品概要"].iter_rows(values_only=True) if r[0] and str(r[0]).startswith("TXF1")]
    eqa = [r for r in wb["權益曲線分析"].iter_rows(values_only=True) if r[0] and str(r[0]).startswith("TXF1")]
    cor = [r for r in wb["相關性分析"].iter_rows(values_only=True)][3:9]
    ann = {r[0]: (r[4], r[5]) for r in wb["Annual 週期分析"].iter_rows(values_only=True) if isinstance(r[0], int)}
    # 由交易明細的訊號名，對應各支（筆數＋第一筆日期必須和商品概要一致）
    cnt, first = collections.Counter(), {}
    for r in list(wb["交易明細"].iter_rows(values_only=True))[3:]:
        if r[1] == "TXF1":
            k = SIG[r[4][:2]]
            cnt[k] += 1
            first.setdefault(k, r[5].date())
    strat = []
    for s, e in zip(syms, eqa):
        m = [k for k in cnt if cnt[k] == s[4] and first[k] == s[1].date()]
        assert len(m) == 1, (s, m)
        strat.append(dict(id=m[0], tf=s[0].replace("TXF1 (", "").replace(" Minutes)", " 分"), n=s[4],
                          net=s[3] / SCALE, dd=e[1] / SCALE, start=s[1]))
    offd = [cor[i][j + 1] for i in range(6) for j in range(6) if j > i]
    return cfg, daily, sorted(strat, key=lambda x: x["id"]), offd, ann


def stats(daily, a, b, cap, ann):
    sel = [(d, v / SCALE) for d, v, _, _ in daily if a <= d <= b]
    yrs = (b - a).total_seconds() / 86400 / 365.25
    eq = pk = mdd = 0.0
    curve = []
    for d, v in sel:
        eq += v; pk = max(pk, eq); mdd = max(mdd, pk - eq); curve.append((d, eq))
    ys = [y for y in ann if a.year <= y <= b.year]
    n = sum(ann[y][0] for y in ys)
    wins = sum(ann[y][0] * ann[y][1] / 100 for y in ys)
    return dict(net=eq, n=n, win=wins / n, ann=eq / cap / yrs * 100, mdd=mdd, mddp=mdd / cap * 100,
                exp=eq / n, curve=curve, yrs=yrs)


def main():
    src, out = sys.argv[1], Path(sys.argv[2])
    SY = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
    cap = float(sys.argv[4]) if len(sys.argv) > 4 else 300_000
    cfg, daily, strat, offd, ann = read(src)
    END = cfg["結束日期"]
    A = max(dt.datetime(SY, 1, 1), dt.datetime(cfg["開始日期"].year, cfg["開始日期"].month, cfg["開始日期"].day))
    S = stats(daily, A, END, cap, ann)
    yr = {}
    for y in range(SY, END.year + 1):
        yr[y] = stats(daily, max(A, dt.datetime(y, 1, 1)), min(END, dt.datetime(y, 12, 31, 23, 59)), cap, ann)
    sum_dd = -sum(s["dd"] for s in strat)
    s0 = cfg["開始日期"]
    full = stats(daily, dt.datetime(s0.year, s0.month, s0.day), END, cap, ann)
    top = max(strat, key=lambda x: x["net"])
    low_cor = sum(1 for c in offd if c <= 0.2)

    W = 9.0
    H = 18.0 + 0.37 * (len(yr) - 2)
    L0, R0 = 0.5, 8.5
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

    def box(x, y, w, h, fc):
        fig.add_artist(FancyBboxPatch((x, H - y - h), w, h, boxstyle="round,pad=0,rounding_size=0.06",
                                      transform=tr, facecolor=fc, edgecolor="none"))

    allpos = all(v["net"] > 0 for v in yr.values())
    span = f"{SY}–{END.year}"
    # 1. 標題與結論
    y = 0.45
    T(L0, y, "台指期六支策略組合", 21, INK, "bold"); y += 0.62
    rich(L0, y, [("多空各三支、彼此低相關：年化報酬 ", INK), (f"{S['ann']:.0f}%", HL), ("，", INK)], 15.5)
    y += 0.40
    rich(L0, y, [("最深回落只有資金的 ", INK), (f"{S['mddp']:.0f}%", HL),
                 (f"，{span} {'每一年都賺錢' if allpos else ''}。", INK)], 15.5)
    y += 0.62

    # 2. 賺什麼／憑什麼／最不適合
    bh = 1.95
    cw = (R0 - L0 - 0.2) / 2
    box(L0, y, cw, bh, PANEL); box(L0 + cw + 0.2, y, cw, bh, PANEL)
    xl, xr = L0 + 0.2, L0 + cw + 0.4
    T(xl, y + 0.16, "賺什麼錢", 10, INK3)
    T(xl, y + 0.40, "台指期多空兩邊的趨勢、盤整與突破", 12, INK, "bold")
    T(xl, y + 0.78, "憑什麼賺錢", 10, INK3)
    for k, s in enumerate((f"六支邏輯不同，{len(offd)} 組兩兩相關有 {low_cor} 組不到 0.2",
                           "多方三支、空方三支，漲跌都有策略在賺",
                           "每支固定 2 口、都有停損，虧損有上限")):
        T(xl, y + 1.02 + k * 0.28, f"・{s}", 11, INK)
    T(xr, y + 0.16, "最不適合哪些行情", 10, INK3)
    for k, s in enumerate(("多空來回急速反轉，兩邊都被停損", "連假前後的大跳空", "波動很小、沒有方向的月份")):
        T(xr, y + 0.44 + k * 0.32, f"・{s}", 11, INK)
    y += bh + 0.2

    # 3. 四個數字
    kp = [("年化報酬", f"{S['ann']:.1f}%"), ("最深回落（MDD）", f"{S['mddp']:.1f}%"),
          ("勝率", f"{S['win'] * 100:.1f}%"), ("每筆平均賺", f"{S['exp']:,.0f} 元")]
    tw = (R0 - L0 - 0.15 * 3) / 4
    for k, (lab, v) in enumerate(kp):
        x = L0 + k * (tw + 0.15)
        box(x, y, tw, 0.95, PANEL)
        T(x + 0.15, y + 0.13, f"組合　{lab}", 9.5, INK2)
        T(x + 0.15, y + 0.42, v, 19, HL, "bold")
    y += 0.95 + 0.5

    # 4. 組合比單支好在哪
    T(L0, y, "組合比單支好在哪", 13, INK, "bold"); y += 0.38
    for s in (f"六支各自最深回落加總 {sum_dd:,.0f} 元 → 組合只有 {full['mdd']:,.0f} 元（少 {(1 - full['mdd'] / sum_dd) * 100:.0f}%）",
              f"多單、空單兩邊都賺：多方 {sum(s['net'] for s in strat if INFO[s['id']][1] == '多'):,.0f} 元、"
              f"空方 {sum(s['net'] for s in strat if INFO[s['id']][1] == '空'):,.0f} 元（全期）",
              f"不靠單一支：賺最多的 {top['id']} 只佔全部淨利 {top['net'] / sum(x['net'] for x in strat) * 100:.0f}%；每日損益相關最高只有 {max(offd):.2f}"):
        T(L0, y, f"・{s}", 11.5, INK); y += 0.30
    y += 0.3

    # 5. 六支各自（全期）
    T(L0, y, "六支各自貢獻（全期，2 口微台）", 13, INK, "bold"); y += 0.40
    cx = [(L0, "策略", "left"), (2.3, "方向", "left"), (3.1, "K 線", "left"), (4.3, "起算", "left"),
          (6.1, "筆數", "right"), (7.3, "淨利", "right"), (R0, "最深回落", "right")]
    for x, s, ha in cx:
        T(x, y, s, 9.5, INK3, "bold", ha=ha)
    y += 0.30; hline(y)
    for s in strat:
        nm, side = INFO[s["id"]]
        r = [f"{s['id']} {nm}", side, s["tf"], f"{s['start']:%Y/%m}", f"{s['n']}", f"{s['net']:,.0f}", f"{s['dd']:,.0f}"]
        y += 0.10
        for (x, _, ha), v in zip(cx, r):
            T(x, y, v, 10.5, HL if x == 7.3 else INK, "bold" if x == 7.3 else "normal", ha=ha)
        y += 0.27; hline(y)
    y += 0.10
    tot = ["六支合計", "", "", "", f"{sum(s['n'] for s in strat)}", f"{sum(s['net'] for s in strat):,.0f}", f"{-full['mdd']:,.0f}"]
    for (x, _, ha), v in zip(cx, tot):
        T(x, y, v, 10.5, HL if x == 7.3 else INK, "bold", ha=ha)
    y += 0.27; hline(y)
    y += 0.5

    # 6. 累積獲利
    T(L0, y, "累積獲利：每次回落後都再創新高", 13, INK, "bold"); y += 0.32
    rich(L0, y, [("━ ", NEW), ("六支組合", INK2), ("    ● ", "#e66767"), ("創新高", INK2), ("    單位：萬元", INK3)], 9.5, "normal")
    y += 0.30
    ch_h = 2.7
    ax = fig.add_axes([(L0 + 0.55) / W, (H - y - ch_h) / H, (R0 - L0 - 1.75) / W, ch_h / H], facecolor=BG)
    d = [A] + [c[0] for c in S["curve"]] + [END]
    cum = [0.0] + [c[1] / 10000 for c in S["curve"]]
    cum.append(cum[-1])
    ax.plot(d, cum, color=NEW, lw=2, drawstyle="steps-post")
    pk, hx, hy = 0.0, [], []
    for dd_, cc in zip(d[1:-1], cum[1:-1]):
        if cc > pk:
            pk = cc; hx.append(dd_); hy.append(cc)
    ax.scatter(hx, hy, s=10 if len(hx) > 80 else 22, color="#e66767", edgecolors=BG, linewidths=0.6, zorder=5)
    ax.text(END, cum[-1], f"  {cum[-1]:.1f} 萬", color=INK, fontsize=10, va="center", fontweight="bold")
    ax.axhline(0, color=INK3, lw=0.8, ls=(0, (3, 3)))
    ax.grid(axis="y", color=GRID, lw=0.6)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=INK3, labelsize=9, length=0)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(A, END)
    y += ch_h + 0.5

    # 7. 逐年
    T(L0, y, f"逐年績效：{len(yr)} 年裡{'每一年都賺錢' if allpos else '的每一年'}", 13, INK, "bold"); y += 0.42
    gx = [(L0, 2.3), (2.3, 6.9), (6.9, R0)]
    tbl_top = y
    tbl_h = 0.32 + 0.30 + (len(yr) + 1) * 0.37 + 0.05
    fig.add_artist(Rectangle((gx[1][0], H - tbl_top - tbl_h), gx[1][1] - gx[1][0] - 0.04, tbl_h, transform=tr,
                             facecolor=NEWBG, edgecolor="none"))
    fig.add_artist(Rectangle((gx[2][0], H - tbl_top - tbl_h), gx[2][1] - gx[2][0], tbl_h, transform=tr,
                             facecolor=OLDBG, edgecolor="none"))
    T((gx[1][0] + gx[1][1]) / 2, y + 0.05, "六支組合", 10, HL, "bold", ha="center")
    T((gx[2][0] + gx[2][1]) / 2, y + 0.05, "風險", 10, OLD, "bold", ha="center")
    y += 0.32
    cols = [(L0 + 0.05, "年", "left"), (3.0, "筆數", "right"), (4.2, "淨利", "right"), (5.5, "報酬率", "right"),
            (6.6, "勝率", "right"), (R0 - 0.05, "年內最深回落", "right")]
    for x, s, ha in cols:
        T(x, y, s, 9.5, INK3, ha=ha)
    y += 0.30; hline(y)
    rws = []
    for k, v in yr.items():
        lab = f"{k}（至 {END:%m/%d}）" if k == END.year else str(k)
        rws.append([lab, f"{v['n']}", f"{v['net']:,.0f}", f"{v['net'] / cap * 100:.1f}%", f"{v['win'] * 100:.0f}%", f"{v['mddp']:.1f}%"])
    rws.append([f"{len(yr)} 年合計", f"{S['n']}", f"{S['net']:,.0f}", f"年化 {S['ann']:.1f}%", f"{S['win'] * 100:.0f}%", f"{S['mddp']:.1f}%"])
    for i, r in enumerate(rws):
        last = i == len(rws) - 1
        y += 0.10
        for (x, _, ha), s in zip(cols, r):
            T(x, y, s, 10.5, HL if (last and x == 5.5) else INK, "bold" if last else "normal", ha=ha)
        y += 0.27; hline(y)
    y += 0.4

    # 8. 註腳
    T(L0, y, f"數字來源：下單軟體 MultiCharts 投資組合回測（六支同時跑），每支 2 口微台。報酬率以資金 {cap:,.0f} 計（多單帳戶 15 萬＋空單帳戶 15 萬）。", 8.8, INK3); y += 0.24
    T(L0, y, f"回測時間：{span}（{A:%Y/%m/%d}～{END:%Y/%m/%d}）；全期 {full['yrs']:.1f} 年年化 {full['ann']:.1f}%、最深回落 {full['mddp']:.1f}%。", 8.8, INK3); y += 0.24
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG)
    print(f"{out} 用到 {y:.2f}/{H:.2f} 吋")
    print("KPI:", kp)
    print("strat:", [(s['id'], s['n'], round(s['net']), round(s['dd'])) for s in strat])
    print("sum_dd", round(sum_dd), "full mdd", round(full["mdd"]), "offd max", round(max(offd), 3), "low", low_cor)
    print("yr:", rws)


if __name__ == "__main__":
    main()
