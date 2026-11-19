"""文獻逐篇落到 S16（Willy 11/18：「文獻完整利用到我的策略」「給我現階段的績效數據與0825的版本做變化率比較」
「現階段年化才不到20%???」）。

每篇文獻 → 一個可回測的做法。全部只擋「新的死亡交叉進場」；口數固定 2 口（Willy 11/18），停損出場不動；
全部只用當下以前的資料。
  量測（波動怎麼量；同時段 N 日 p70，和 A／B 同一框架，只換量測）
    Parkinson 1980        park{N}   14 根 ln(H/L)² 估計量
    Garman & Klass 1980   gk{N}     14 根開高低收估計量
    Yang & Zhang 2000     yz{N}     14 根、含跳空的開高低收估計量
    ABDL 2003             rv{N}     14 根內 1 分 K 報酬平方和（實現波動，不含開盤跳空）
  基準（拿什麼比）
    Andersen & Bollerslev 1997／1998  A＝tod60d_p70、B＝tod90d_p70（候選版）
    RiskMetrics 1996      rm{λ}_k   同時段跨日 EWMA（λ 0.94／0.97），ATR% ≥ k × 基準
    Engle & Lee 1999、Engle & Rangel 2008、Engle-Ghysels-Sohn 2013
                          tc{H}_k   兩成分：ATR% ÷（同時段季節因子 × 慢變成分）≥ k；慢變＝半衰期 H 日 EWMA，
                                    季節因子＝同時段過去 60 天「ATR% ÷ 慢變」的平均
  狀態（策略什麼時候有效）
    Hamilton 1989         ms、ms+A  日盤實現波動（對數）兩狀態馬可夫轉換；參數只用 2001–2019 估計，之後只往前濾波；
                                    最近一個已收盤日盤的「高波動狀態」機率 ≥ 0.5 才放行
    Daniel & Moskowitz 2016  A+panic{x}、B+panic5  恐慌狀態（比 5 個已收盤日盤前跌超過 x%）不追空
  部位（Moreira & Muir 2017、Harvey et al. 2018、Kim-Tse-Wald 2016）：波動縮放部位；口數固定，本次不測
  檢定（和 11/18 的 45 種合併成 66 種）
    White 2000 Reality Check、Hansen 2005 SPA：日損益減 base，定態 bootstrap（平均區塊 10 日，2,000 次）
    Harvey-Liu-Zhu 2016：日損益差 t 值（Newey-West 10 日），門檻 3.0
    Bailey & López de Prado 2014 DSR、Bailey et al. 2017 PBO：試驗數 66
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_literature.py <1min.txt> <out.md> <is2020_daily.csv> <new_daily.csv>
"""
import bisect
import csv
import itertools
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import fmean, pstdev

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats, ewma_series, BARS_PER_DAY  # noqa: E402
from vol_gate_robust import tod_veto  # noqa: E402
from vol_gate_is2020 import session_date, sharpe_from, moments, dsr  # noqa: E402
from txfcore.quotes.history import MC12MinuteSource  # noqa: E402

END = datetime(2026, 11, 16, 12, 20)
IS_START = datetime(2020, 1, 1)
L23 = datetime(2023, 1, 1)
HOLD = datetime(2026, 8, 23)
N_WIN = 14
LN2 = math.log(2)
# MC 口徑（大台 2 口、滑價 1,000）的 Python 預測，來源：S16_v1280_python_check_20261118.md
MC_UNITS = {"base": 3_232_800, "A": 3_652_000, "B": 3_997_600}


# ------------------------------------------------------------------ 量測
def roll_mean(v, n=N_WIN):
    out, s = [], 0.0
    for i, x in enumerate(v):
        s += x
        if i >= n:
            s -= v[i - n]
        out.append(s / min(i + 1, n))
    return out


def park_series(bars):
    return [math.sqrt(max(x, 0) / (4 * LN2)) for x in roll_mean([math.log(b.h / b.l) ** 2 for b in bars])]


def gk_series(bars):
    g = [0.5 * math.log(b.h / b.l) ** 2 - (2 * LN2 - 1) * math.log(b.c / b.o) ** 2 for b in bars]
    return [math.sqrt(max(x, 0)) for x in roll_mean(g)]


def yz_series(bars, n=N_WIN):
    o = [0.0] + [math.log(bars[j].o / bars[j - 1].c) for j in range(1, len(bars))]
    c = [math.log(b.c / b.o) for b in bars]
    rs = [math.log(b.h / b.c) * math.log(b.h / b.o) + math.log(b.l / b.c) * math.log(b.l / b.o) for b in bars]
    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    out = []
    for i in range(len(bars)):
        lo = max(0, i - n + 1)
        m = i - lo + 1
        if m < 3:
            out.append(0.0)
            continue
        oo, cc = o[lo:i + 1], c[lo:i + 1]
        mo, mc = sum(oo) / m, sum(cc) / m
        so = sum((x - mo) ** 2 for x in oo) / (m - 1)
        sc = sum((x - mc) ** 2 for x in cc) / (m - 1)
        srs = sum(rs[lo:i + 1]) / m
        out.append(math.sqrt(max(so + k * sc + (1 - k) * srs, 0)))
    return out


def rv_series(path, bars, start):
    """每根 5 分 K 內 1 分 K 對數報酬平方和（與 aggregate_5m 同一套分格；開盤第一分鐘用 ln(收/開)，不含跳空）。"""
    rv = defaultdict(float)
    prev_dt, prev_c = None, None
    for m in MC12MinuteSource(path, validate=False).stream():
        d = m.mc_date
        dd = date(1900 + d // 10000, d // 100 % 100, d % 100)
        t = m.mc_time
        mins = (t // 100) * 60 + t % 100
        if not ((526 <= mins <= 825) or mins >= 901 or mins <= 300):
            continue
        dt = datetime(dd.year, dd.month, dd.day, t // 100, t % 100)
        if dt < start:
            continue
        if dt > END:
            break
        up = -(-mins // 5) * 5
        key = datetime(dd.year, dd.month, dd.day) + timedelta(minutes=up)
        if prev_dt is not None and (dt - prev_dt) <= timedelta(minutes=10):
            r = math.log(m.close / prev_c)
        else:
            r = math.log(m.close / m.open)
        rv[key] += r * r
        prev_dt, prev_c = dt, m.close
    per_bar = [rv.get(b.dt, 0.0) for b in bars]
    return [math.sqrt(x * N_WIN) for x in roll_mean(per_bar)]


# ------------------------------------------------------------------ 基準
def rm_baseline(bars, x, lam):
    m, out = {}, []
    for b, v in zip(bars, x):
        s = (b.dt.hour, b.dt.minute)
        out.append(m.get(s, v))
        m[s] = lam * m[s] + (1 - lam) * v if s in m else v
    return out


def tc_veto(bars, ap, slot_idx, half_life, k, season_days=60):
    slow = ewma_series(ap, half_life)
    ratio = [a / s if s > 0 else 1.0 for a, s in zip(ap, slow)]
    pos_in_slot = {}
    for s, lst in slot_idx.items():
        for p, i in enumerate(lst):
            pos_in_slot[i] = p

    def veto(i, _t):
        lst = slot_idx[(bars[i].dt.hour, bars[i].dt.minute)]
        p = pos_in_slot[i]
        hist = [ratio[j] for j in lst[max(0, p - season_days):p]]
        if len(hist) < season_days // 2:
            return False
        return ratio[i] / (sum(hist) / len(hist)) < k
    return veto


# ------------------------------------------------------------------ 狀態（Hamilton 1989）
def hmm2_filter(x, mu, sd, P, pi):
    T = len(x)
    filt, pred = np.zeros((T, 2)), np.zeros((T, 2))
    ll = 0.0
    for t in range(T):
        pr = pi if t == 0 else filt[t - 1] @ P
        pred[t] = pr
        dens = np.exp(-0.5 * ((x[t] - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
        num = pr * dens
        s = num.sum()
        filt[t] = num / s
        ll += math.log(s)
    return filt, pred, ll


def hmm2_fit(x, iters=300):
    x = np.asarray(x, dtype=float)
    T = len(x)
    mu = np.array([np.quantile(x, 0.3), np.quantile(x, 0.8)])
    sd = np.array([x.std(), x.std()]) * 0.7
    P = np.array([[0.97, 0.03], [0.03, 0.97]])
    pi = np.array([0.5, 0.5])
    prev = -1e18
    for _ in range(iters):
        filt, pred, ll = hmm2_filter(x, mu, sd, P, pi)
        sm = np.zeros_like(filt)
        sm[-1] = filt[-1]
        xi = np.zeros((2, 2))
        for t in range(T - 2, -1, -1):
            ratio = sm[t + 1] / pred[t + 1]
            sm[t] = filt[t] * (P @ ratio)
            xi += np.outer(filt[t], ratio) * P
        P = xi / xi.sum(1, keepdims=True)
        w = sm / sm.sum(0)
        mu = (w * x[:, None]).sum(0)
        sd = np.sqrt((w * (x[:, None] - mu) ** 2).sum(0))
        pi = sm[0]
        if abs(ll - prev) < 1e-7:
            break
        prev = ll
    if mu[0] > mu[1]:
        mu, sd, P, pi = mu[::-1], sd[::-1], P[::-1, ::-1], pi[::-1]
    return mu, sd, P, pi, ll


def day_session_series(bars00):
    """日盤（08:50–13:45）日實現波動與收盤。回傳 dates、log_rv、close。"""
    by = defaultdict(list)
    for b in bars00:
        hm = b.dt.hour * 100 + b.dt.minute
        if 850 <= hm <= 1345:
            by[b.dt.date()].append(b)
    dates, lrv, close = [], [], []
    for d in sorted(by):
        bs = by[d]
        if len(bs) < 20:
            continue
        rv = math.log(bs[0].c / bs[0].o) ** 2 + sum(math.log(bs[j].c / bs[j - 1].c) ** 2 for j in range(1, len(bs)))
        if rv <= 0:
            continue
        dates.append(d); lrv.append(math.log(rv)); close.append(bs[-1].c)
    return dates, lrv, close


def completed_day_index(dt, dates):
    """dt 當下最近一個已收盤的日盤在 dates 的索引。"""
    hm = dt.hour * 100 + dt.minute
    if hm >= 1500 or hm < 800:          # 夜盤：當天（或前一天）的日盤已收
        return bisect.bisect_right(dates, session_date(dt)) - 1
    return bisect.bisect_left(dates, dt.date()) - 1


# ------------------------------------------------------------------ 檢定
def stationary_boot_idx(T, B, L, rng):
    idx = np.empty((B, T), dtype=np.int64)
    idx[:, 0] = rng.integers(0, T, B)
    newb = rng.random((B, T)) < 1.0 / L
    rnd = rng.integers(0, T, (B, T))
    for t in range(1, T):
        idx[:, t] = np.where(newb[:, t], rnd[:, t], (idx[:, t - 1] + 1) % T)
    return idx


def spa_rc(D, B=2000, L=10, seed=20261118):
    """D：K×T（候選日損益 − base 日損益）。回傳 RC p、SPA_c p、統計量。"""
    K, T = D.shape
    rng = np.random.default_rng(seed)
    idx = stationary_boot_idx(T, B, L, rng)
    dbar = D.mean(1)
    boot = np.empty((B, K))
    for b in range(B):
        boot[b] = D[:, idx[b]].mean(1)
    rt = math.sqrt(T)
    omega = (rt * boot).std(0)
    omega[omega == 0] = 1e-12
    # White RC
    V = (rt * dbar).max()
    Vb = (rt * (boot - dbar)).max(1)
    p_rc = float((Vb >= V).mean())
    # Hansen SPA（consistent）
    tstat = rt * dbar / omega
    Tspa = max(0.0, tstat.max())
    # Hansen 2005：明顯很差的模型（t ≤ −√(2 log log n)）虛無平均設為自己的樣本平均，其他設在邊界 0
    poor = tstat <= -math.sqrt(2 * math.log(math.log(T)))
    mu_c = np.where(poor, dbar, 0.0)
    Tb = np.maximum(0.0, (rt * (boot - dbar + mu_c) / omega).max(1))
    p_spa = float((Tb >= Tspa).mean())
    return p_rc, p_spa, float(V), Tspa, int(np.argmax(tstat))


def nw_t(d, lag=10):
    d = np.asarray(d, dtype=float)
    T = len(d)
    m = d.mean()
    e = d - m
    v = (e @ e) / T
    for l in range(1, lag + 1):
        v += 2 * (1 - l / (lag + 1)) * (e[l:] @ e[:-l]) / T
    return m / math.sqrt(v / T)


# ------------------------------------------------------------------ 指標
def perf(pnls, years, dvals):
    x = full_stats(pnls, years)
    w = [p for p in pnls if p > 0]
    lo = [p for p in pnls if p < 0]
    x["avg_win"] = fmean(w) if w else 0.0
    x["avg_loss"] = fmean(lo) if lo else 0.0
    x["payoff"] = x["avg_win"] / -x["avg_loss"] if lo else float("inf")
    x["max_loss"] = min(pnls) if pnls else 0.0
    x["mdd_pct"] = x["mdd"] / CAP * 100
    x["calmar"] = x["ann"] / abs(x["mdd_pct"]) if x["mdd"] else float("inf")
    x["recovery"] = x["net"] / abs(x["mdd"]) if x["mdd"] else float("inf")
    x["per_year"] = x["n"] / years
    sd = pstdev(dvals)
    x["sharpe"] = fmean(dvals) / sd * math.sqrt(252) if sd else 0.0
    return x


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src, out_md, old_csv, new_csv = sys.argv[1:5]
    bars00 = load_bars(src, datetime(2000, 1, 1), END)
    i0 = next(i for i, b in enumerate(bars00) if b.dt >= datetime(2019, 1, 1))
    bars = bars00[i0:]
    print("bars", len(bars00), len(bars), flush=True)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    ap = atr_pct_series(bars)
    slot_idx = defaultdict(list)
    for i, b in enumerate(bars):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)

    series = {"park": park_series(bars), "gk": gk_series(bars), "yz": yz_series(bars),
              "rv": rv_series(src, bars, datetime(2019, 1, 1))}
    print("series done", flush=True)

    # Hamilton：日盤日實現波動，2001–2019 估參數
    dates, lrv, dclose = day_session_series(bars00)
    est = [x for d, x in zip(dates, lrv) if date(2001, 1, 1) <= d <= date(2019, 12, 31)]
    mu, sd, P, pi, ll = hmm2_fit(est)
    filt, _, _ = hmm2_filter(np.asarray(lrv), mu, sd, P, pi)
    p_high = filt[:, 1]
    print("hmm", mu, sd, P, flush=True)
    cdi = [completed_day_index(b.dt, dates) for b in bars]

    def ms_veto(i, _t):
        k = cdi[i]
        return k < 0 or p_high[k] < 0.5

    def panic_veto(x):
        def veto(i, _t):
            k = cdi[i]
            return k >= 5 and bars[i].c / dclose[k - 5] - 1 <= -x / 100
        return veto

    def any_of(*vs):
        return lambda i, t: any(v(i, t) for v in vs)

    A = tod_veto(bars, ap, slot_idx, 60, 0.70)
    Bv = tod_veto(bars, ap, slot_idx, 90, 0.70)
    V = {"base": None, "A": A, "B": Bv}
    lit = {"base": "—", "A": "Andersen & Bollerslev 1997／1998", "B": "Andersen & Bollerslev 1997／1998"}
    names_lit = {"park": "Parkinson 1980", "gk": "Garman & Klass 1980", "yz": "Yang & Zhang 2000", "rv": "ABDL 2003"}
    for m, ser in series.items():
        for d in (60, 90):
            V[f"{m}{d}"] = tod_veto(bars, ser, slot_idx, d, 0.70)
            lit[f"{m}{d}"] = names_lit[m]
    for lam in (0.94, 0.97):
        base_l = rm_baseline(bars, ap, lam)
        for k in (1.0, 1.25):
            V[f"rm{int(lam*100)}_k{k}"] = (lambda bl, k: lambda i, _t: ap[i] < k * bl[i])(base_l, k)
            lit[f"rm{int(lam*100)}_k{k}"] = "RiskMetrics 1996（同時段）"
    for H in (20, 60):
        for k in (1.0, 1.25):
            V[f"tc{H}_k{k}"] = tc_veto(bars, ap, slot_idx, H, k)
            lit[f"tc{H}_k{k}"] = "Engle & Lee 1999／Engle & Rangel 2008／GARCH-MIDAS 2013"
    V["ms"] = ms_veto
    V["ms+A"] = any_of(ms_veto, A)
    V["A+panic3"] = any_of(A, panic_veto(3))
    V["A+panic5"] = any_of(A, panic_veto(5))
    V["B+panic5"] = any_of(Bv, panic_veto(5))
    for k in ("ms", "ms+A"):
        lit[k] = "Hamilton 1989"
    for k in ("A+panic3", "A+panic5", "B+panic5"):
        lit[k] = "Daniel & Moskowitz 2016"

    runs = {}
    for k, v in V.items():
        runs[k] = [t for t in s16.run(bars, dict(p), hol, veto=v).trades if t.exit_dt >= IS_START]
        print("done", k, len(runs[k]), flush=True)

    days = sorted({session_date(b.dt) for b in bars if b.dt >= IS_START})
    di = {d: j for j, d in enumerate(days)}
    daily = {}
    for k, tr in runs.items():
        v = [0.0] * len(days)
        for t in tr:
            v[di[session_date(t.exit_dt)]] += micro_net(t)
        daily[k] = v

    def P_(k, a, b, yrs):
        pn = [micro_net(t) for t in runs[k] if a <= t.exit_dt < b]
        dv = [daily[k][j] for j, d in enumerate(days) if a.date() <= d < b.date()]
        return perf(pn, yrs, dv)

    s20 = {k: P_(k, IS_START, datetime(2099, 1, 1), 6.876) for k in runs}
    s23 = {k: P_(k, L23, datetime(2099, 1, 1), 3.876) for k in runs}
    hold = {k: P_(k, HOLD, datetime(2099, 1, 1), 0.233) for k in runs}

    out = ["# S16：文獻逐篇落地回測＋現階段績效對 0825 變化率＋年化拆解（推論，Python；2 口微台、資金 140,200）", ""]
    out += ["## 1. 文獻 → 做法 → 結果（2020 起；括號為 2023 起）", "",
            "| 文獻 | 做法 | 筆數 | 年化 | 每筆期望值 | 最大回撤 | 最長連虧 | 四項勝 0825 | 四項勝 A |",
            "|---|---|---|---|---|---|---|---|---|"]

    def wins(x, b):
        return sum([x["ann"] > b["ann"], x["exp"] > b["exp"], x["mdd"] > b["mdd"], x["streak"] < b["streak"]])

    for k in runs:
        x, y = s20[k], s23[k]
        out.append(f"| {lit[k]} | {k} | {x['n']}（{y['n']}） | {x['ann']:.1f}%（{y['ann']:.1f}%） | "
                   f"{x['exp']:,.0f}（{y['exp']:,.0f}） | {x['mdd_pct']:.1f}%（{y['mdd_pct']:.1f}%） | "
                   f"{x['streak']}（{y['streak']}） | {wins(x, s20['base'])}/4 | {wins(x, s20['A'])}/4 |")
    out += ["", "Moreira & Muir 2017、Harvey et al. 2018、Kim-Tse-Wald 2016（波動縮放部位）：需要改口數，Willy 11/18 定口數固定，本次不測。", ""]

    # 檢定：合併 11/18 的 45 種
    old = {}
    with open(old_csv, encoding="utf-8") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        rows = list(rd)
    od = [date.fromisoformat(r[0]) for r in rows]
    assert od == days, "日期序列不一致"
    for c, name in enumerate(hdr[1:], 1):
        old[name] = [float(r[c]) for r in rows]
    assert max(abs(a - b) for a, b in zip(old["base"], daily["base"])) < 1, "base 日損益不一致"
    assert max(abs(a - b) for a, b in zip(old["tod60d_p70"], daily["A"])) < 1
    allv = dict(old)
    for k in runs:
        if k not in ("base", "A", "B"):
            allv[k] = daily[k]
    with open(new_csv, "w", encoding="utf-8", newline="") as f:
        f.write("date," + ",".join(runs) + "\n")
        for j, d in enumerate(days):
            f.write(f"{d}," + ",".join(f"{daily[k][j]:.0f}" for k in runs) + "\n")
    names = list(allv)
    N = len(names)
    base = np.asarray(allv["base"])
    cand = [k for k in names if k != "base"]
    D = np.asarray([np.asarray(allv[k]) - base for k in cand])
    p_rc, p_spa, Vst, Tst, ibest = spa_rc(D)
    out += [f"## 2. 統計檢定（2020 起日損益，{len(days)} 個交易日；門檻種類合計 {N}）", "",
            f"- White（2000）Reality Check：「{N-1} 種門檻裡最好的那個，其實沒有贏 0825」的 p 值＝**{p_rc:.3f}**",
            f"- Hansen（2005）SPA：同一個虛無假設，p 值＝**{p_spa:.3f}**（t 值最高的是 {cand[ibest]}）",
            "- p < 0.05＝扣掉「試了很多種」之後，最好的門檻仍顯著贏 0825。", ""]
    out += ["| 方法 | 日損益差 t 值（對 0825，Newey-West） | 日損益 t 值（對 0） | Harvey-Liu-Zhu 門檻 3.0 |", "|---|---|---|---|"]
    for k in ("A", "B"):
        tk = "tod60d_p70" if k == "A" else "tod90d_p70"
        t1 = nw_t(np.asarray(allv[tk]) - base)
        t0 = nw_t(allv[tk])
        out.append(f"| {k} | {t1:.2f} | {t0:.2f} | {'過' if t0 >= 3 else '未過'}（對 0）；{'過' if t1 >= 3 else '未過'}（對 0825） |")
    t0b = nw_t(base)
    out.append(f"| 0825 | — | {t0b:.2f} | {'過' if t0b >= 3 else '未過'}（對 0） |")
    out.append("")

    # PBO、DSR（N＝66）
    T = len(days)
    S = 16
    edges = [round(T * s / S) for s in range(S + 1)]
    agg = {}
    for k in names:
        r = [x / CAP for x in allv[k]]
        agg[k] = [(edges[s + 1] - edges[s], sum(r[edges[s]:edges[s + 1]]),
                   sum(x * x for x in r[edges[s]:edges[s + 1]])) for s in range(S)]
    lam, beat = [], 0
    allb = set(range(S))
    for c in itertools.combinations(range(S), S // 2):
        oos = tuple(allb - set(c))
        best = max(names, key=lambda k: sharpe_from(agg[k], c))
        o = {k: sharpe_from(agg[k], oos) for k in names}
        rk = sum(1 for k in names if o[k] < o[best]) + 0.5 * (sum(1 for k in names if o[k] == o[best]) - 1) + 1
        w = rk / (N + 1)
        lam.append(math.log(w / (1 - w)))
        beat += o[best] > o["base"]
    pbo = sum(1 for x in lam if x <= 0) / len(lam)
    srs = {k: moments([x / CAP for x in allv[k]]) for k in names}
    vsr = pstdev([srs[k][0] for k in names]) ** 2
    out += [f"- PBO（CSCV 16 段、12,870 種切法，N＝{N}）：**{pbo*100:.1f}%**；挑出的門檻在另一半贏 0825 的比例 {beat/len(lam)*100:.1f}%"]
    for k, tk in (("A", "tod60d_p70"), ("B", "tod90d_p70")):
        sr, g3, g4 = srs[tk]
        sr0, d, _ = dsr(sr, g3, g4, T, N, vsr)
        out.append(f"- DSR {k}（N＝{N}）：{d*100:.1f}%（年化夏普 {sr*math.sqrt(252):.2f}，門檻 {sr0*math.sqrt(252):.2f}）")
    out.append("")

    # 樣本外保留期（common.py 事前登記：2026-08-23 起）
    out += ["## 3. 事前登記的保留期（2026-08-23～11-16，common.py 寫死）", "",
            "| 方法 | 筆數 | 淨利 | 每筆期望值 | 最大回撤 | 最長連虧 |", "|---|---|---|---|---|---|"]
    for k in runs:
        x = hold[k]
        out.append(f"| {k} | {x['n']} | {x['net']:,.0f} | {x['exp']:,.0f} | {x['mdd_pct']:.1f}% | {x['streak']} |")
    out += ["", "注意：11 月的個案在 11/18 已經被看過（選 A／B 時看過 11 月放行表），保留期不是完全乾淨。", ""]

    # 現階段績效 vs 0825
    rows_def = [("筆數", "n", "{:,.0f}", 0), ("淨利（元）", "net", "{:,.0f}", 1), ("年化（單利）", "ann", "{:.1f}%", 1),
                ("每筆期望值（元）", "exp", "{:,.0f}", 1), ("獲利因子 PF", "pf", "{:.2f}", 1), ("勝率", "win", "{:.1%}", 1),
                ("平均獲利（元）", "avg_win", "{:,.0f}", 1), ("平均虧損（元）", "avg_loss", "{:,.0f}", 1),
                ("賺賠比", "payoff", "{:.2f}", 1), ("單筆最大虧損（元）", "max_loss", "{:,.0f}", 1),
                ("最大回撤（元）", "mdd", "{:,.0f}", 1), ("最大回撤佔資金", "mdd_pct", "{:.1f}%", 1),
                ("最長連虧（筆）", "streak", "{:.0f}", -1), ("最長連虧金額（元）", "streak_amt", "{:,.0f}", 1),
                ("年化夏普（日）", "sharpe", "{:.2f}", 1), ("Calmar（年化÷回撤%）", "calmar", "{:.2f}", 1),
                ("淨利÷最大回撤", "recovery", "{:.2f}", 1), ("每年筆數", "per_year", "{:.1f}", 0)]

    mag_keys = {"avg_loss", "max_loss", "mdd", "mdd_pct", "streak_amt"}

    def chg(v, b, key=""):
        if key in mag_keys:
            v, b = abs(v), abs(b)
        if b == 0:
            return "—"
        return f"{(v - b) / abs(b) * 100:+.1f}%"

    for title, st in (("2020-01～2026-11（6.9 年）", s20), ("2023-01～2026-11（3.9 年）", s23)):
        out += [f"## 4. 現階段績效 vs 0825：{title}", "",
                "| 指標 | 0825 | A（60 日 p70） | A 變化率 | B（90 日 p70） | B 變化率 |", "|---|---|---|---|---|---|"]
        for lab, key, fmt, _ in rows_def:
            b, a, bb = st["base"][key], st["A"][key], st["B"][key]
            out.append(f"| {lab} | {fmt.format(b)} | {fmt.format(a)} | {chg(a, b, key)} | {fmt.format(bb)} | {chg(bb, b, key)} |")
        out.append("")
    out += ["MC 口徑（大台 2 口、滑價 1,000，資料到 2026-11-16）Python 預測淨利：",
            f"0825 {MC_UNITS['base']:,}；A {MC_UNITS['A']:,}（{chg(MC_UNITS['A'], MC_UNITS['base'])}）；"
            f"B {MC_UNITS['B']:,}（{chg(MC_UNITS['B'], MC_UNITS['base'])}）", "",
            "變化率＝（新－0825）÷｜0825｜。虧損、回撤類用絕對值算：負＝虧損變小（變好）；最長連虧（筆）負＝變好。", ""]

    # 年化拆解
    yr_close = defaultdict(list)
    for b in bars00:
        if b.dt >= IS_START:
            yr_close[b.dt.year].append(b.c)
    last_c = bars00[-1].c
    out += ["## 5. 年化為什麼不到 20%：逐年拆解", "",
            f"最新收盤 {last_c:,.0f}。資金固定 140,200＝今天 2 口微台保證金 70,100 的 2 倍。",
            "「同價位資金」＝140,200 ×（該年平均指數 ÷ 最新收盤）：同樣 2 口、同樣 2 倍保證金，換到當年的指數位階需要的資金（假設保證金和指數同比例；微台 2024-07 才上市，之前是假設值）。", "",
            "| 年 | 平均指數 | 0825 淨利 | A 淨利 | B 淨利 | 固定資金報酬 0825／A／B | 同價位資金 | 同價位資金報酬 0825／A／B |",
            "|---|---|---|---|---|---|---|---|"]
    tw_cap = {"base": 0.0, "A": 0.0, "B": 0.0}
    tot = {"base": 0.0, "A": 0.0, "B": 0.0}
    for y in range(2020, 2027):
        avg = fmean(yr_close[y])
        frac = (date(2026, 11, 16) - date(2026, 1, 1)).days / 365 if y == 2026 else 1.0
        capy = CAP * avg / last_c
        nets = {k: sum(micro_net(t) for t in runs[k] if t.exit_dt.year == y) for k in ("base", "A", "B")}
        for k in nets:
            tw_cap[k] += capy * frac
            tot[k] += nets[k]
        fr = "／".join(f"{nets[k]/CAP/frac*100:.1f}%" for k in ("base", "A", "B"))
        nr = "／".join(f"{nets[k]/capy/frac*100:.1f}%" for k in ("base", "A", "B"))
        tag = "（年化，至 11/16）" if y == 2026 else ""
        out.append(f"| {y}{tag} | {avg:,.0f} | {nets['base']:,.0f} | {nets['A']:,.0f} | {nets['B']:,.0f} | {fr} | {capy:,.0f} | {nr} |")
    out += ["", "| 口徑 | 0825 | A | B |", "|---|---|---|---|"]
    out.append("| 2020 起，固定資金 140,200（單利） | " + " | ".join(f"{s20[k]['ann']:.1f}%" for k in ("base", "A", "B")) + " |")
    out.append("| 2020 起，同價位資金（時間加權） | " + " | ".join(f"{tot[k]/tw_cap[k]*100:.1f}%" for k in ("base", "A", "B")) + " |")
    out.append("| 2023 起，固定資金（單利） | " + " | ".join(f"{s23[k]['ann']:.1f}%" for k in ("base", "A", "B")) + " |")
    out.append("")
    Path(out_md).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
