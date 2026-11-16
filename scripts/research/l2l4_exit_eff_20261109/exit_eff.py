"""L2 v5.11 / L4 v14.10 出場效率量化（2026-11-09）。Python mc_compat 全歷史，資料迄 9/24。
每筆部位：最大浮盈 MFE、最大浮虧 MAE（1 分 K 盤中）、實拿、回吐、實拿比例；逐年；依波動分段；
L2 盤中觸價反事實（各出場線改盤中觸價取最緊，沿原路徑第一次觸價）；L4 第二口保護候選篩選；L2+L4 組合回撤。
單位：點／口；金額換成微台 2 口（大台 2 口 ÷ 20）。"""
import bisect, collections, csv, datetime as dt, json, statistics as stt, sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from txfcore.indicators.core import avg_true_range
from txfcore.instruments.spec import TXF
from txfcore.profiles import mc_compat
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.daily import NIGHT_FIRST, build
from txfcore.quotes.history import MC12MinuteSource
from txfcore.strategies.base import StrategyConfig
from txfcore.strategies.l2_trendshort_v5_11 import L2TrendShortV511
from txfcore.strategies.l4_consolshort_v14_10 import DEFAULT_PARAMS as L4P, L4ConsolShortV1410, STRATEGY_NAME as L4N
from txfcore.types.orders import MarketPosition
from txfcore.types.mctime import mc_date_to_date

DATA = sys.argv[1]
OUT = sys.argv[2]
K = lambda d, t: d * 10000 + t
ts = lambda d, t: dt.datetime.combine(mc_date_to_date(d), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")
MICRO = 20      # 大台 2 口 → 微台 2 口

mins = [m for m in MC12MinuteSource(DATA).stream() if 1190102 <= m.mc_date <= 1261107]
IS_END = "2026-09-24 23:59"
mkeys = [K(m.mc_date, m.mc_time) for m in mins]
b15, b60, daily = list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)), build(mins, NIGHT_FIRST)
print("minutes", len(mins), "60m", len(b60), "15m", len(b15))


def bar_minutes(prev_key, key):
    i, j = bisect.bisect_right(mkeys, prev_key), bisect.bisect_right(mkeys, key)
    return range(i, j)


# ---------- 記錄每根 K 棒的出場線 ----------
class L2Rec(L2TrendShortV511):
    log = []

    def on_bar(self, view, state):
        state, d = super().on_bar(view, state)
        ps, pos = state.per_session, view.position
        if pos.market_position is MarketPosition.SHORT:
            p = self.config.params
            atr = avg_true_range(view.data1, p["ATR_Len"])
            ttp = (ps.lowest_close * (1 + p["TTP_RebPct"] / 100)
                   if pos.entry_price - ps.lowest_close >= atr * p["TTP_MinAtr"] else 0.0)
            self.log.append((K(view.mc_date, view.mc_time), pos.entry_price, ps.pos_type,
                             ps.pg.price, ps.pg.peak, ps.active_sl, ttp, ps.lowest_close))
        return state, d


class L4Rec(L4ConsolShortV1410):
    log = []

    def on_bar(self, view, state):
        state, d = super().on_bar(view, state)
        ps, pos = state.per_session, view.position
        if pos.market_position is MarketPosition.SHORT:
            atr = avg_true_range(view.data1, self.config.params["ATR_Len"]) if "ATR_Len" in self.config.params else 0
            self.log.append((K(view.mc_date, view.mc_time), pos.entry_price, ps.stop_level,
                             ps.tp1_done, pos.current_contracts if hasattr(pos, "current_contracts") else 0, atr))
        return state, d


l2 = L2Rec()
r2 = mc_compat.single_runner(l2).run(b60)
fix2 = list(csv.DictReader(open(os.path.join(ROOT, "tests", "fixtures/mc_L2_v5.10_trades.csv"))))
t2 = [t for t in r2.trades if ts(t.entry_date, t.entry_time) >= fix2[0]["entry_dt"]]
for p_, m_ in zip(t2, fix2):
    assert ts(p_.entry_date, p_.entry_time) == m_["entry_dt"] and ts(p_.exit_date, p_.exit_time) == m_["exit_dt"], (m_, p_)
l4 = L4Rec(StrategyConfig(name=L4N, instrument="TXF", holiday_flat_time=415, params=dict(L4P)))
r4 = mc_compat.multi_runner(l4).run(b15, b60, daily)
fix4 = list(csv.DictReader(open(os.path.join(ROOT, "tests", "fixtures/mc_L4_T8_trades.csv"))))
t4 = [t for t in r4.trades if ts(t.entry_date, t.entry_time) >= fix4[0]["entry_dt"]]
for p_, m_ in zip(t4, fix4):
    assert ts(p_.entry_date, p_.entry_time) == m_["entry_dt"] and ts(p_.exit_date, p_.exit_time) == m_["exit_dt"], (m_, p_)
print("parity OK on fixture range; total L2", len(t2), "L4", len(t4))

bars_by = {60: [K(b.mc_date, b.mc_time) for b in b60], 15: [K(b.mc_date, b.mc_time) for b in b15]}


def fill_index(bar_key, px, tf):
    """成交那根 K 棒內，第一個價格區間含成交價的 1 分 K（市價單 ＝ 開盤那分鐘）。"""
    keys = bars_by[tf]
    i = bisect.bisect_left(keys, bar_key)
    rng = bar_minutes(keys[i - 1] if i > 0 else 0, bar_key)
    for j in rng:
        if mins[j].low - 0.5 <= px <= mins[j].high + 0.5:
            return j
    return rng.start


# 日線 ATR(20)/價：波動分段
dayrows = []
for i, b in enumerate(daily):
    dayrows.append((b.mc_date, b.high, b.low, b.close))
dkeys = [r[0] for r in dayrows]


def vol_at(mc_date):
    i = bisect.bisect_left(dkeys, mc_date) - 1      # 進場前一天收盤已知
    if i < 21:
        return None
    trs = []
    for k in range(i - 19, i + 1):
        h, l, pc = dayrows[k][1], dayrows[k][2], dayrows[k - 1][3]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / 20 / dayrows[i][3] * 100


def positions(trades, tf):
    pos = collections.OrderedDict()
    for t in trades:
        k = (t.entry_date, t.entry_time)
        pos.setdefault(k, []).append(t)
    out = []
    for k, legs in pos.items():
        e = legs[0]
        last = max(legs, key=lambda x: K(x.exit_date, x.exit_time))
        i0 = fill_index(K(e.entry_date, e.entry_time), e.entry_price, tf)
        i1 = fill_index(K(last.exit_date, last.exit_time), last.exit_price, tf)
        seg = mins[i0:i1 + 1]
        lo_j = min(range(i0, i1 + 1), key=lambda j: mins[j].low)
        mfe = e.entry_price - mins[lo_j].low
        mae = max(m.high for m in seg) - e.entry_price
        qty = sum(x.quantity for x in legs)
        real = sum(x.gross_points * x.quantity for x in legs) / qty
        net = sum(x.net_ntd(TXF) for x in legs)
        out.append(dict(entry=ts(e.entry_date, e.entry_time), exit=ts(last.exit_date, last.exit_time),
                        elabel=e.entry_label, xlabel="+".join(x.exit_label for x in legs), ep=e.entry_price,
                        mfe=max(mfe, 0), mae=max(mae, 0), real=real, net=net / MICRO, i0=i0, i1=i1,
                        mfe_t=ts(mins[lo_j].mc_date, mins[lo_j].mc_time), vol=vol_at(e.entry_date),
                        legs=legs, key=K(e.entry_date, e.entry_time)))
    return out


P2, P4 = positions(t2, 60), positions(t4, 15)


def summarize(P, name):
    s = {}
    win = [p for p in P if p.get("net", 0) > 0]
    s["筆數"] = len(P)
    s["淨利_微台"] = round(sum(p["net"] for p in P))
    s["平均MFE點"] = round(stt.mean(p["mfe"] for p in P))
    s["平均MAE點"] = round(stt.mean(p["mae"] for p in P))
    s["平均實拿點"] = round(stt.mean(p["real"] for p in P))
    tot_mfe = sum(p["mfe"] for p in P)
    s["總實拿÷總MFE_%"] = round(sum(p["real"] for p in P) / tot_mfe * 100, 1)
    big = [p for p in P if p["mfe"] >= 1000]
    s["MFE≥1000點筆數"] = len(big)
    if big:
        s["MFE≥1000_總MFE點"] = round(sum(p["mfe"] for p in big))
        s["MFE≥1000_總實拿點"] = round(sum(p["real"] for p in big))
        s["MFE≥1000_實拿比例_%"] = round(sum(p["real"] for p in big) / sum(p["mfe"] for p in big) * 100, 1)
    s["曾浮盈≥300點卻虧損出場_筆"] = sum(1 for p in P if p["mfe"] >= 300 and p["real"] < 0)
    s["曾浮盈≥300點卻虧損_虧損點合計"] = round(sum(p["real"] for p in P if p["mfe"] >= 300 and p["real"] < 0))
    s["總回吐點(MFE−實拿)"] = round(sum(p["mfe"] - p["real"] for p in P))
    return s


def by_bucket(P, keyf):
    g = collections.defaultdict(list)
    for p in P:
        g[keyf(p)].append(p)
    res = {}
    for k in sorted(g, key=str):
        q = g[k]
        tm = sum(p["mfe"] for p in q)
        res[str(k)] = dict(n=len(q), net=round(sum(p["net"] for p in q)), mfe=round(tm),
                           real=round(sum(p["real"] for p in q)),
                           cap=round(sum(p["real"] for p in q) / tm * 100, 1) if tm else None)
    return res


vols = sorted(p["vol"] for p in P2 + P4 if p["vol"] is not None)
v1, v2 = vols[len(vols) // 3], vols[2 * len(vols) // 3]
vb = lambda p: ("?" if p["vol"] is None else "1低波動" if p["vol"] < v1 else "2中波動" if p["vol"] < v2 else "3高波動")

# ---------- L2 反事實：出場線改盤中觸價、取最緊 ----------
L2LOG = collections.defaultdict(list)
for row in L2Rec.log:
    L2LOG[row[1]].append(row)       # 依進場價分組不可靠 → 改用時間落點
logkeys = [r[0] for r in L2Rec.log]


def l2_counterfactual(p, tier=None, hard=450):
    """沿原路徑：第 k 根收盤算出的線，套用到第 k+1 根的 1 分 K。tier=(點, 保留%)。"""
    if p["elabel"] != "TS_Entry":
        return None
    keys = bars_by[60]
    ib = bisect.bisect_left(keys, p["key"])
    xb = bisect.bisect_left(keys, K(p["legs"][-1].exit_date, p["legs"][-1].exit_time))
    li = {r[0]: r for r in L2Rec.log}
    ep = p["ep"]
    for b in range(ib, xb):
        r = li.get(keys[b])
        if r is None:
            continue
        _, _, ptype, pg, peak, asl, ttp, lc = r
        if tier and peak >= tier[0]:
            pg = ep - peak * tier[1] / 100
        lines = [x for x in (pg, asl, ttp, ep + hard) if x > 0]
        line = min(lines)
        for j in bar_minutes(keys[b], keys[b + 1]):
            m = mins[j]
            if m.high >= line:
                px = max(line, m.open)
                return dict(px=px, t=ts(m.mc_date, m.mc_time), real=ep - px, j=j,
                            which=["SP", "TSL", "TTP", "Hard"][[pg, asl, ttp, ep + hard].index(line)])
    return None


cf_rows = []
for name, tier in (("盤中觸價", None), ("盤中觸價＋2500點保留70%", (2500, 70))):
    d_pts = 0
    rows = []
    for p in P2:
        c = l2_counterfactual(p, tier)
        if c and c["j"] < p["i1"]:
            delta = c["real"] - p["real"]
            d_pts += delta
            rows.append((p["entry"], p["xlabel"], round(p["real"]), c["which"], round(c["real"]), round(delta), c["t"]))
    cf_rows.append((name, round(d_pts), rows))

# ---------- L4 第二口 ----------
L4LOG = {r[0]: r for r in L4Rec.log}


def l4_second_lot(p):
    legs = p["legs"]
    tp1 = [x for x in legs if x.exit_label == "CS_TP1"]
    rest = [x for x in legs if x.exit_label != "CS_TP1"]
    if not tp1 or not rest:
        return None
    t1, r = tp1[0], rest[0]
    j1 = fill_index(K(t1.exit_date, t1.exit_time), t1.exit_price, 15)
    seg = range(j1, p["i1"] + 1)
    lo = min(mins[j].low for j in seg)
    return dict(entry=p["entry"], ep=p["ep"], tp1=t1.exit_price, j1=j1, mfe2=p["ep"] - lo,
                real2=r.gross_points, label=r.exit_label, exit=ts(r.exit_date, r.exit_time))


S4 = [x for x in (l4_second_lot(p) for p in P4) if x]


def l4_protect(s, p, mode, a, b):
    """第二口保護篩選（沿原路徑第一次觸價）。
    mode 'lock': 浮盈 ≥ a 點後，停在 進場 − 浮盈峰值×b%（峰值用 1 分 K 低點，下一分鐘起生效）
    mode 'half': TP1 後停損距離減半：線 ＝ 進場 + (原停損 − 進場)×a%（每根 15 分 K 收盤更新）"""
    ep = p["ep"]
    keys = bars_by[15]
    if mode == "lock":
        peak, line = 0.0, None
        for j in range(s["j1"], p["i1"] + 1):
            m = mins[j]
            if line is not None and m.high >= line:
                return ep - max(line, m.open)
            peak = max(peak, ep - m.low)
            if peak >= a:
                line = ep - peak * b / 100
        return None
    if mode == "half":
        b0 = bisect.bisect_left(keys, K(mins[s["j1"]].mc_date, mins[s["j1"]].mc_time))
        bx = bisect.bisect_left(keys, K(p["legs"][-1].exit_date, p["legs"][-1].exit_time))
        for b in range(b0, bx):
            r = L4LOG.get(keys[b])
            if not r:
                continue
            stop = r[2]
            line = ep + (stop - ep) * a / 100
            if line >= stop:
                continue
            for j in bar_minutes(keys[b], keys[b + 1]):
                m = mins[j]
                if m.high >= line:
                    return ep - max(line, m.open)
        return None


p4_by_entry = {p["entry"]: p for p in P4}
cands = [("鎖利 浮盈≥100 保留50%", "lock", 100, 50), ("鎖利 浮盈≥150 保留50%", "lock", 150, 50),
         ("鎖利 浮盈≥200 保留50%", "lock", 200, 50), ("鎖利 浮盈≥300 保留50%", "lock", 300, 50),
         ("鎖利 浮盈≥200 保留30%", "lock", 200, 30), ("停損距離×50%", "half", 50, 0),
         ("停損距離×70%", "half", 70, 0)]
l4c = []
for nm, mode, a, b in cands:
    tot = 0; hit = 0; better = 0; worse = 0; peryr = collections.Counter()
    for s in S4:
        p = p4_by_entry[s["entry"]]
        v = l4_protect(s, p, mode, a, b)
        if v is None:
            continue
        dlt = v - s["real2"]
        if abs(dlt) < 0.01:
            continue
        hit += 1; tot += dlt; peryr[s["exit"][:4]] += dlt
        better += dlt > 0; worse += dlt < 0
    l4c.append(dict(name=nm, changed=hit, better=better, worse=worse, delta_pts=round(tot),
                    delta_micro=round(tot * 10 * 2), peryr={k: round(v * 20) for k, v in sorted(peryr.items())}))

# ---------- 組合回撤（每日收盤盯市，微台 2 口）----------
def daily_mtm(P):
    """回傳 {mc_date: 當日收盤權益變化}（含持倉未實現）。"""
    eq = collections.Counter()
    for p in P:
        for leg in p["legs"]:
            ep, q = leg.entry_price, leg.quantity
            i0, i1 = p["i0"], fill_index(K(leg.exit_date, leg.exit_time), leg.exit_price, 60 if p in P2 else 15)
            prev = ep
            last_day = None
            for j in range(i0, i1 + 1):
                m = mins[j]
                if last_day is not None and m.mc_date != last_day:
                    pass
                last_day = m.mc_date
            # 逐日：每個交易日最後一分鐘收盤
            days = collections.OrderedDict()
            for j in range(i0, i1 + 1):
                days[daily_of[j]] = mins[j].close
            ks = list(days)
            for n, dkey in enumerate(ks):
                px = leg.exit_price if n == len(ks) - 1 else days[dkey]
                eq[dkey] += (prev - px) * q * 200 / MICRO
                prev = px
            eq[ks[-1]] -= leg.cost / MICRO
    return eq


# 每分鐘所屬交易日（NIGHT_FIRST：夜盤歸下一個日盤）
dclose = [b.mc_date for b in daily]
daily_of = []
for m in mins:
    k = K(m.mc_date, m.mc_time)
    daily_of.append(None)
di = 0
dend = []
# 用日 K 的 (mc_date, mc_time) 當截止點
dkk = [K(b.mc_date, b.mc_time) for b in daily]
for j, k in enumerate(mkeys):
    i = bisect.bisect_left(dkk, k)
    daily_of[j] = daily[min(i, len(daily) - 1)].mc_date


def dd_stats(eq):
    cum = pk = mdd = 0
    for d in sorted(eq):
        cum += eq[d]; pk = max(pk, cum); mdd = max(mdd, pk - cum)
    return round(cum), round(mdd)


e2, e4 = daily_mtm(P2), daily_mtm(P4)
ec = collections.Counter(e2); ec.update(e4)
first = max(min(e2), min(e4))
dd = {"L2": dd_stats(e2), "L4": dd_stats(e4), "L2+L4": dd_stats(ec)}

# 逐年
yr = lambda P: by_bucket(P, lambda p: p["exit"][:4])

OOS2 = [p for p in P2 if p["entry"] > IS_END]; OOS4 = [p for p in P4 if p["entry"] > IS_END]
IS2 = [p for p in P2 if p["entry"] <= IS_END]; IS4 = [p for p in P4 if p["entry"] <= IS_END]
cfmap = {}
for n_, d_, rows_ in cf_rows:
    for r_ in rows_:
        cfmap.setdefault(r_[0], {})[n_] = r_
oos_list = [(p["entry"], p["elabel"], p["ep"], p["exit"], p["xlabel"], round(p["mfe"]), round(p["mae"]), round(p["real"]),
             round(p["net"]), p["mfe_t"], cfmap.get(p["entry"])) for p in OOS2 + OOS4]
cf_split = []
for n_, d_, rows_ in cf_rows:
    a_ = sum(r_[5] for r_ in rows_ if r_[0] <= IS_END); b_ = sum(r_[5] for r_ in rows_ if r_[0] > IS_END)
    yy = collections.Counter()
    for r_ in rows_: yy[r_[0][:4]] += r_[5] * 400 / MICRO
    cf_split.append(dict(name=n_, changed=len(rows_), better=sum(r_[5] > 0 for r_ in rows_), worse=sum(r_[5] < 0 for r_ in rows_),
                         IS_pts=a_, OOS_pts=b_, micro=round(d_ * 400 / MICRO), peryr={k: round(v) for k, v in sorted(yy.items())}))
rep = dict(OOS=oos_list, L2_cf_split=cf_split, L2_IS=summarize(IS2, "L2"), L4_IS=summarize(IS4, "L4"),
    vol_cut=[round(v1, 2), round(v2, 2)],
    L2=summarize(P2, "L2"), L4=summarize(P4, "L4"),
    L2_year=yr(P2), L4_year=yr(P4), L2_vol=by_bucket(P2, vb), L4_vol=by_bucket(P4, vb),
    L2_label=by_bucket(P2, lambda p: p["xlabel"]), L4_label=by_bucket(P4, lambda p: p["xlabel"]),
    L2_entrytype=by_bucket(P2, lambda p: p["elabel"]),
    L2_cf=[(n, d, len(r), round(d * 400 / MICRO)) for n, d, r in cf_rows],
    L2_cf_rows=cf_rows,
    L4_second=dict(n=len(S4), mfe2_avg=round(stt.mean(s["mfe2"] for s in S4)),
                   real2_sum=round(sum(s["real2"] for s in S4)),
                   real2_neg=sum(1 for s in S4 if s["real2"] < 0),
                   real2_neg_sum=round(sum(s["real2"] for s in S4 if s["real2"] < 0)),
                   tp1_then_loss_after_mfe200=sum(1 for s in S4 if s["real2"] < 0 and s["mfe2"] >= 200),
                   labels=collections.Counter(s["label"] for s in S4)),
    L4_cands=l4c, DD=dd,
    L2_top_giveback=sorted(((p["entry"], p["xlabel"], round(p["mfe"]), round(p["real"]), round(p["mfe"] - p["real"]))
                            for p in P2), key=lambda x: -x[4])[:10],
)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in rep.items() if k not in ("L2_cf_rows",)}, ensure_ascii=False, indent=1, default=str))
