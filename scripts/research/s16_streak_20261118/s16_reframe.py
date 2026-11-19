"""S16 跳框分析：不再問「門檻怎麼調」，改問「這支策略本質上是什麼、錢從哪來、怕什麼」。
全部用 MC 報表交易（0825、B）＋MC 匯出 1 分 K（聚成 5 分 K），2 口微台、資金 140,200。

四個視角（各自實際跑一次該領域的方法）：
  1. 選擇權交易員：把 S16 當成一張「賣權」看——依台指當天漲跌幅分組，S16 在每組賺賠多少（報酬型態）。
  2. 放空研究員（拆解回測）：進場訊號本身有沒有時機優勢？B 進場後 15–120 分鐘的走勢 vs 同樣波動門檻放行的隨機時點。
     出場有沒有把錢吐回去？每筆最大浮盈／浮虧（MFE／MAE）。
  3. 資金配置者：資金實際使用率（持倉時間佔比）、每小時持倉賺多少；逐年波動環境 vs 報酬。
  4. 市場結構：依進場時段（日盤、夜盤歐洲、美股開盤、深夜）拆損益，看錢是在誰的時段賺到的。

Usage: python -I scripts/research/s16_streak_20261118/s16_reframe.py <1min.txt> <0825_trades.csv> <B_trades.csv> <out.md>
"""
import bisect
import random
import statistics as stx
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import load_bars, micro_net, CAP  # noqa: E402
from mc_boss_stats import load  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
START = datetime(2020, 1, 1)
YRS = (CUT - START).days / 365
FWD = (3, 6, 12, 24)  # 5 分 K 根數：15、30、60、120 分鐘


def session_date(dt):
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def tod_gate(bars, days=90, q=0.70, atr_len=14):
    """和 v1.28.1 相同的同時段門檻：ATR14/收盤×100 ≥ 同一個 5 分鐘時點過去 days 天的第 q 百分位（資料不足一半時放行）。"""
    H = [b.h for b in bars]; L = [b.l for b in bars]; C = [b.c for b in bars]
    buf, gate = {}, [False] * len(bars)
    for i in range(atr_len, len(bars)):
        atr = sum(max(H[j], C[j - 1]) - min(L[j], C[j - 1]) for j in range(i - atr_len + 1, i + 1)) / atr_len
        ap = atr / C[i] * 100
        t = bars[i].dt.hour * 100 + bars[i].dt.minute
        hist = buf.setdefault((t // 100) * 12 + (t % 100) // 5, deque(maxlen=days))
        if len(hist) >= days // 2:
            srt = sorted(hist)
            gate[i] = ap >= srt[min(len(srt) - 1, int(len(srt) * q + 1e-9))]
        else:
            gate[i] = True
        hist.append(ap)
    return gate


def fwd_short(bars, e, k):
    """從第 e 根開盤放空，持有到第 e+k-1 根收盤的報酬（%）；跨盤（中間斷檔）回傳 None。"""
    x = e + k - 1
    if x >= len(bars) or bars[x].dt - bars[e].dt != timedelta(minutes=5 * (k - 1)):
        return None
    return (bars[e].o - bars[x].c) / bars[e].o * 100


def grp_stats(v):
    v = [x for x in v if x is not None]
    if len(v) < 2:
        return None
    m, sd = stx.mean(v), stx.pstdev(v)
    return dict(n=len(v), mean=m, med=stx.median(v), t=m / (sd / len(v) ** 0.5) if sd else 0.0,
                big=sum(1 for x in v if x >= 1.0) / len(v), bad=sum(1 for x in v if x <= -0.5) / len(v))


def spearman(a, b):
    def rk(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0] * len(x)
        for k, i in enumerate(o):
            r[i] = k
        return r
    ra, rb = rk(a), rk(b); n = len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(ra, rb)) / (n * (n * n - 1))


def bucket_of(r):
    for lo, lab in ((-99, "≤ −3%"), (-3, "−3% ～ −2%"), (-2, "−2% ～ −1%"), (-1, "−1% ～ 0%"),
                    (0, "0% ～ +1%"), (1, "+1% ～ +2%"), (2, "+2% ～ +3%"), (3, "≥ +3%")):
        pass
    edges = [-3, -2, -1, 0, 1, 2, 3]
    labs = ["≤ −3%", "−3% ～ −2%", "−2% ～ −1%", "−1% ～ 0%", "0% ～ +1%", "+1% ～ +2%", "+2% ～ +3%", "≥ +3%"]
    return labs[bisect.bisect_right(edges, r)], labs


def slot_name(dt):
    t = dt.hour * 100 + dt.minute
    if 845 <= t <= 1000:
        return "日盤開盤 08:45–10:00"
    if 1000 < t <= 1345:
        return "日盤 10:00–13:45"
    if 1500 <= t < 2100:
        return "夜盤前段 15:00–21:00（歐洲）"
    if t >= 2100:
        return "夜盤 21:00–24:00（美股開盤）"
    return "深夜 00:00–05:00（美股盤中）"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    base = [t for t in load(sys.argv[2]) if START <= t.exit_dt <= CUT]
    B = [t for t in load(sys.argv[3]) if START <= t.exit_dt <= CUT]
    idx = {b.dt: i for i, b in enumerate(bars)}
    gate = tod_gate(bars)
    out = ["# S16 跳框分析：這支策略本質上是什麼（2026-11-19）", "",
           "資料：MC 報表交易（0825 11/16 報表、B v1281c 報表），平倉 2020-01-01～2026-11-16 12:20；",
           "台指漲跌與進場後走勢用 MC 匯出 1 分 K（聚成 5 分 K）。損益＝2 口微台淨額（扣滑價、手續費、期交稅）。", ""]

    # ---------- 0. 對齊檢查 ----------
    miss = [t for t in B if t.entry_dt not in idx or t.exit_dt not in idx]
    eq = sum(1 for t in B if t.entry_dt in idx and abs(bars[idx[t.entry_dt]].o - t.entry_px) <= 5.01)
    g_ok = sum(1 for t in B if t.entry_dt in idx and gate[idx[t.entry_dt] - 1])
    out += ["## 0. 資料對齊（檢查用）", "",
            f"- B {len(B)} 筆；找不到進出場 K 棒 {len(miss)} 筆；進場價＝該根開盤 ±5 點（MC 滑價）{eq} 筆。",
            f"- 本程式重算的同時段門檻，在 B 的訊號 K 棒是放行狀態：{g_ok}/{len(B)} 筆（用來確認門檻重算正確）。", ""]

    # ---------- 1. 選擇權交易員：報酬型態 ----------
    sess_close = {}
    for b in bars:
        sess_close[session_date(b.dt)] = b.c
    sd = sorted(sess_close)
    ret = {d: (sess_close[d] / sess_close[p] - 1) * 100 for p, d in zip(sd, sd[1:]) if d >= START.date()}
    pnl = {"0825": defaultdict(float), "B": defaultdict(float)}
    for name, tr in (("0825", base), ("B", B)):
        for t in tr:
            pnl[name][session_date(t.entry_dt)] += micro_net(t)
    agg = defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0.0])
    for d, r in ret.items():
        k, labs = bucket_of(r)
        a = agg[k]
        a[0] += 1; a[1] += d in pnl["B"]; a[2] += pnl["B"].get(d, 0.0); a[3] += pnl["0825"].get(d, 0.0)
        a[4] += d in pnl["0825"]; a[5] += r
    _, labs = bucket_of(0)
    out += ["## 1. 選擇權交易員視角：S16 像一張什麼樣的部位？", "",
            "依「台指當天（日盤＋接續夜盤）收盤對收盤漲跌幅」把 2020 以來每個交易日分組，看 S16 在每一組賺賠多少。", "",
            "| 台指當天漲跌 | 天數 | B 有交易的天數 | B 淨利 | B 平均每天 | 0825 淨利 | 0825 有交易天數 |", "|---|---|---|---|---|---|---|"]
    for k in labs:
        a = agg.get(k)
        if not a:
            continue
        out.append(f"| {k} | {a[0]} | {a[1]} | {a[2]:,.0f} | {a[2]/a[0]:,.0f} | {a[3]:,.0f} | {a[4]} |")
    tot_b = sum(pnl["B"].values())
    down2 = sum(v for d, v in pnl["B"].items() if ret.get(d, 0) <= -2)
    calm = sum(v for d, v in pnl["B"].items() if abs(ret.get(d, 9)) < 1)
    up = sum(v for d, v in pnl["B"].items() if ret.get(d, 0) > 0)
    calm0 = sum(v for d, v in pnl["0825"].items() if abs(ret.get(d, 9)) < 1)
    out += ["", f"- B 總淨利 {tot_b:,.0f}；其中台指跌 2% 以上的日子賺 {down2:,.0f}（{down2/tot_b*100:.0f}%）；"
            f"漲跌在 ±1% 內的平淡日 {calm:,.0f}（每年 {calm/YRS:,.0f}，0825 是 {calm0:,.0f}）；台指上漲的日子 {up:,.0f}。", ""]
    worst = sorted(ret, key=ret.get)[:20]; best = sorted(ret, key=ret.get, reverse=True)[:20]
    for lab, ds in (("台指跌最多的 20 天", worst), ("台指漲最多的 20 天", best)):
        v = [pnl["B"].get(d, 0.0) for d in ds]
        out.append(f"- {lab}（{ret[ds[-1]]:+.1f}% 以{'下' if ds is worst else '上'}）：B 有交易 {sum(1 for d in ds if d in pnl['B'])} 天，"
                   f"合計 {sum(v):,.0f}。")
    out.append("")

    # ---------- 2. 放空研究員：進場時機與出場回吐 ----------
    out += ["## 2. 放空研究員視角：錢是進場賺的，還是出場賺的？", "",
            "比較「B 實際進場後」與「同樣波動門檻放行、隨便一根 K 棒進場放空」之後 15–120 分鐘的走勢（放空的報酬，%）。",
            "隨機對照只取 2020 以來、門檻放行的 K 棒；跨盤的視窗不算。", ""]
    ent = [idx[t.entry_dt] for t in B if t.entry_dt in idx]
    base_all = [j + 1 for j in range(len(bars) - 1) if bars[j].dt >= START]
    base_gate = [j + 1 for j in range(len(bars) - 1) if bars[j].dt >= START and gate[j]]
    base_dn = [j for j in base_gate if j - 13 >= 0 and bars[j - 1].c < bars[j - 13].c]
    groups = (("B 實際進場", ent), ("門檻放行的任一 K 棒", base_gate), ("門檻放行＋前 1 小時下跌", base_dn), ("所有 K 棒（不分條件）", base_all))
    out += ["| 群組 | 視窗 | 樣本 | 平均 | 中位數 | t 值 | 走 1% 以上的機率 | 逆向 0.5% 以上的機率 |", "|---|---|---|---|---|---|---|---|"]
    res = {}
    for name, es in groups:
        for k in FWD:
            s = grp_stats([fwd_short(bars, e, k) for e in es])
            res[(name, k)] = s
            if s:
                out.append(f"| {name} | {k*5} 分 | {s['n']:,} | {s['mean']:+.3f}% | {s['med']:+.3f}% | {s['t']:.2f} | "
                           f"{s['big']*100:.1f}% | {s['bad']*100:.1f}% |")
    # 隨機抽樣：從門檻放行的 K 棒抽與 B 同樣筆數，看 B 的 120 分鐘平均排第幾
    rnd = random.Random(20261119)
    pool = [v for v in (fwd_short(bars, e, 24) for e in base_gate) if v is not None]
    bv = [v for v in (fwd_short(bars, e, 24) for e in ent) if v is not None]
    bm = stx.mean(bv)
    sims = [stx.mean(rnd.sample(pool, len(bv))) for _ in range(5000)]
    p_rand = sum(1 for s in sims if s >= bm) / len(sims)
    out += ["", f"- 隨機抽 {len(bv)} 個「門檻放行」時點、抽 5,000 次：120 分鐘平均 ≥ B（{bm:+.3f}%）的比例＝{p_rand:.3f}"
            f"（越小代表 B 的進場時機越不是運氣）。", ""]

    # MFE / MAE
    rows = []
    for t in B:
        if t.entry_dt not in idx or t.exit_dt not in idx:
            continue
        e, x = idx[t.entry_dt], idx[t.exit_dt]
        lo = min(b.l for b in bars[e:x + 1]); hi = max(b.h for b in bars[e:x + 1])
        rows.append(dict(t=t, mfe=(t.entry_px - lo) / t.entry_px * 100, mae=(hi - t.entry_px) / t.entry_px * 100,
                         real=(t.entry_px - t.exit_px) / t.entry_px * 100, net=micro_net(t)))
    win = [r for r in rows if r["net"] > 0]; los = [r for r in rows if r["net"] <= 0]
    cap = stx.median(r["real"] / r["mfe"] for r in win if r["mfe"] > 0)
    gb = stx.median(r["mfe"] - r["real"] for r in win)
    out += ["**出場：每筆最大浮盈（MFE）與最後實拿**（% of 價格；用 5 分 K 高低點估計，盤中真實極值可能更大）", "",
            f"- 賺錢單 {len(win)} 筆：實拿／最大浮盈的中位數 {cap*100:.0f}%；中位數回吐 {gb:.2f}%。",
            f"- 賠錢單 {len(los)} 筆：曾經浮盈 ≥ 0.3% 的有 {sum(1 for r in los if r['mfe'] >= 0.3)} 筆、≥ 0.5% 的有 "
            f"{sum(1 for r in los if r['mfe'] >= 0.5)} 筆（賺過再賠回去）；從頭到尾浮盈 < 0.1% 的有 {sum(1 for r in los if r['mfe'] < 0.1)} 筆（一進場就錯）。",
            f"- 賠錢單最大浮虧中位數 {stx.median(r['mae'] for r in los):.2f}%；賺錢單最大浮虧中位數 {stx.median(r['mae'] for r in win):.2f}%。", ""]
    big = sorted(rows, key=lambda r: -r["net"])[:13]
    out += ["**獲利最大的 13 筆（佔總淨利約 100%）長什麼樣**", "",
            "| 進場 | 時段 | 台指當天 | 持倉 | 出場 | 最大浮盈 | 實拿 | 淨利 |", "|---|---|---|---|---|---|---|---|"]
    for r in big:
        t = r["t"]
        out.append(f"| {t.entry_dt:%Y-%m-%d %H:%M} | {slot_name(t.entry_dt)} | {ret.get(session_date(t.entry_dt), float('nan')):+.1f}% | "
                   f"{(t.exit_dt - t.entry_dt).total_seconds()/60:,.0f} 分 | {t.exit_label} | {r['mfe']:.2f}% | {r['real']:.2f}% | {r['net']:,.0f} |")
    out.append("")

    # M8 停利之後行情還走多遠（停利 2.3% 是不是太早）
    m8 = []
    for t in B:
        if "TimeStop_Pct" not in t.exit_label or t.exit_dt not in idx:
            continue
        x = idx[t.exit_dt]; j = x + 1
        while j < len(bars) and j - x <= 24 and bars[j].dt - bars[j - 1].dt == timedelta(minutes=5):
            j += 1
        w = bars[x + 1:j]
        if not w:
            continue
        m8.append(((t.exit_px - min(b.l for b in w)) / t.exit_px * 100, (t.exit_px - w[-1].c) / t.exit_px * 100))
    if m8:
        out += [f"**2.3% 停利（M8）出場後 2 小時內**（{len(m8)} 筆）：再往下跌的最大幅度中位數 {stx.median(a for a, _ in m8):.2f}%，"
                f"≥ 1% 的 {sum(1 for a, _ in m8 if a >= 1)} 筆；2 小時後收盤相對出場價（放空角度）中位數 {stx.median(b for _, b in m8):+.2f}%，"
                f"> 0 的 {sum(1 for _, b in m8 if b > 0)} 筆。", ""]

    # 台指跌最多的 20 天：跌在跳空還是盤中？S16 為什麼沒進場？
    first_open, prev_close = {}, {}
    for b in bars:
        d = session_date(b.dt)
        first_open.setdefault(d, b.o)
    out += ["**台指跌最多的 20 天：跌幅是跳空還是盤中？**", "",
            "| 日期 | 當天 | 開盤跳空 | 開盤後 | B 交易 | B 損益 |", "|---|---|---|---|---|---|"]
    gap_sum = intr_sum = 0.0
    for d in sorted(worst):
        p_ = sd[sd.index(d) - 1]
        gap = (first_open[d] / sess_close[p_] - 1) * 100
        intr = (sess_close[d] / first_open[d] - 1) * 100
        gap_sum += gap; intr_sum += intr
        n = sum(1 for t in B if session_date(t.entry_dt) == d)
        out.append(f"| {d} | {ret[d]:+.1f}% | {gap:+.1f}% | {intr:+.1f}% | {n} | {pnl['B'].get(d, 0.0):,.0f} |")
    out += ["", f"- 20 天平均：開盤跳空 {gap_sum/20:+.2f}%、開盤後 {intr_sum/20:+.2f}%。", ""]

    # ---------- 3. 資金配置者 ----------
    hold_min = sum((t.exit_dt - t.entry_dt).total_seconds() / 60 for t in B)
    mkt_min = sum(1 for b in bars if b.dt >= START) * 5
    gate_rate = sum(1 for j, b in enumerate(bars) if b.dt >= START and gate[j]) / sum(1 for b in bars if b.dt >= START)
    out += ["## 3. 資金配置者視角：這筆錢有多少時間在工作？", "",
            f"- B 持倉時間合計 {hold_min/60:,.0f} 小時，佔 2020 以來開盤時間 {hold_min/mkt_min*100:.2f}%；每持倉 1 小時淨賺 {tot_b/(hold_min/60):,.0f} 元。",
            f"- 同時段門檻放行的 K 棒比例 {gate_rate*100:.1f}%（設計上約 30%）。", "",
            "| 年 | 台指年化波動 | 台指跌 2% 以上天數 | B 筆數 | B 報酬率 | 0825 報酬率 |", "|---|---|---|---|---|---|"]
    vols, rets_b, dn_cnt = [], [], []
    for y in range(2020, 2027):
        r = [v for d, v in ret.items() if d.year == y]
        vol = stx.pstdev(r) * 252 ** 0.5
        nb = [micro_net(t) for t in B if t.exit_dt.year == y]
        n0 = [micro_net(t) for t in base if t.exit_dt.year == y]
        yf = (CUT.date() - datetime(2026, 1, 1).date()).days / 365 if y == 2026 else 1.0
        rb, r0 = sum(nb) / CAP / yf * 100, sum(n0) / CAP / yf * 100
        dn = sum(1 for v in r if v <= -2)
        vols.append(vol); rets_b.append(rb); dn_cnt.append(dn)
        out.append(f"| {y}{'（換算全年）' if y == 2026 else ''} | {vol:.1f}% | {dn} | {len(nb)} | {rb:.1f}% | {r0:.1f}% |")
    out += ["", f"- 逐年等級相關（7 年，只供參考）：B 報酬率 vs 台指波動 {spearman(vols, rets_b):+.2f}；vs 跌 2% 以上天數 {spearman(dn_cnt, rets_b):+.2f}。", ""]

    # ---------- 4. 市場結構：時段 ----------
    out += ["## 4. 市場結構視角：錢在哪個時段賺到？", "", "| 進場時段 | 筆數 | 淨利 | 平均 | 勝率 | 前 13 大獲利單 |", "|---|---|---|---|---|---|"]
    top_ids = {id(r["t"]) for r in big}
    by = defaultdict(list)
    for t in B:
        by[slot_name(t.entry_dt)].append(t)
    for k in ("日盤開盤 08:45–10:00", "日盤 10:00–13:45", "夜盤前段 15:00–21:00（歐洲）", "夜盤 21:00–24:00（美股開盤）", "深夜 00:00–05:00（美股盤中）"):
        v = by.get(k, [])
        if not v:
            out.append(f"| {k} | 0 | 0 | — | — | 0 |")
            continue
        pn = [micro_net(t) for t in v]
        out.append(f"| {k} | {len(v)} | {sum(pn):,.0f} | {sum(pn)/len(v):,.0f} | {sum(1 for x in pn if x > 0)/len(v)*100:.0f}% | "
                   f"{sum(1 for t in v if id(t) in top_ids)} |")
    out.append("")
    Path(sys.argv[4]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
