"""L2 v5.12（11/16 版：v5.11＋三項極端日出場）Python 預測，給 MC 報表對答案用。
用法：python predict.py <1分K 7欄格式> [結束日 YYMMDD，預設 260924] [worst|open]
同一根 K 棒有兩張買停損都被觸發時誰先成交：worst＝較差的價先（mc_compat 現行，v5.11 從沒遇過）、
open＝離開盤價近的先（MC 用 O-H-L-C 路徑時的結果）。MC 實際是哪一種，要看 MC 報表。
R0（三項全關）必須和 v5.11 逐筆相同；T（預設）列出和 v5.11 不同的交易。"""
import collections, csv, dataclasses, datetime as dt, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from txfcore.instruments.spec import TXF
from txfcore.profiles import mc_compat
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.history import MC12MinuteSource
from txfcore.strategies.base import StrategyConfig
from txfcore.strategies.l2_trendshort_v5_11 import DEFAULT_PARAMS, L2TrendShortV511, STRATEGY_NAME
from txfcore.types.mctime import mc_date_to_date
from txfcore.engine.fill_mc12 import IntrabarPolicy
from txfcore.types.orders import MarketPosition, OrderIntent, OrderType, Side

NEW = dict(SP_Tier_Pts=2500, SP_Tier_Keep=70, LimitDn_On=1, LimitDn_Pct=9.8, Reb_On=0, Reb_Pct=8.0)   # 預設 ＝ .pla（11/16：3 關）


class L2V512(L2TrendShortV511):
    def __init__(self, config=None, new=None):
        super().__init__(config) if config else super().__init__()
        self.n = dict(NEW if new is None else new)
        self.ref = 0.0; self.ready = False; self.reb_line = 0.0; self.armed = False
        self.limdn = 0.0; self.peak = 0.0; self.tier = 0.0

    def on_bar(self, view, state):
        n, bars = self.n, view.data1
        low, close = bars.low[0], bars.close[0]
        if self.ready:                                   # .pla：先用舊參考價判斷，再在 13:45 換參考價
            self.reb_line = self.ref * (1 - n["Reb_Pct"] / 100)
            self.limdn = round(self.ref * (1 - n["LimitDn_Pct"] / 100))
            if n["Reb_On"] and low <= self.reb_line:
                self.armed = True
        if view.mc_time == 1345:
            self.ref, self.ready, self.armed = close, True, False
            self.reb_line = self.ref * (1 - n["Reb_Pct"] / 100)
            self.limdn = round(self.ref * (1 - n["LimitDn_Pct"] / 100))
        state, d = super().on_bar(view, state)
        pos = view.position
        if pos.market_position is MarketPosition.SHORT:
            ep = pos.entry_price
            self.peak = max(0.0, ep - low) if pos.bars_since_entry == 0 else max(self.peak, ep - low)
            self.tier = ep - self.peak * n["SP_Tier_Keep"] / 100 if n["SP_Tier_Pts"] > 0 and self.peak >= n["SP_Tier_Pts"] else 0.0
            hard = [o for o in d.orders if o.label == "TS_HardSL"]
            d.orders[:] = [o for o in d.orders if o.label != "TS_HardSL"]
            add = lambda lbl, px, ot: d.add(OrderIntent(strategy=STRATEGY_NAME, label=lbl, side=Side.BUY_TO_COVER,
                                                       order_type=ot, price=px, signal_date=view.mc_date,
                                                       signal_time=view.mc_time, seq=state.next_seq()))
            if self.tier > 0:
                add("TS_SPTier", self.tier, OrderType.STOP)
            if n["LimitDn_On"] and self.ready and 0 < self.limdn < ep:
                add("TS_LimitDn", float(self.limdn), OrderType.LIMIT)
            if n["Reb_On"] and self.armed and 0 < self.reb_line < ep:
                add("TS_Rebound", self.reb_line, OrderType.STOP)
            for o in hard:
                d.add(dataclasses.replace(o, seq=state.next_seq()))
        else:
            self.peak = self.tier = 0.0
        return state, d


def main():
    data, end = sys.argv[1], int("1" + (sys.argv[2] if len(sys.argv) > 2 else "260924"))
    pol = mc_compat.POLICY if (sys.argv[3] if len(sys.argv) > 3 else "worst") == "worst" else \
        dataclasses.replace(mc_compat.POLICY, intrabar=IntrabarPolicy.OPEN_PROXIMITY)
    mins = [m for m in MC12MinuteSource(data).stream() if 1190102 <= m.mc_date <= end]
    b60 = list(aggregate_bars(mins, 60))
    ts = lambda d_, t: dt.datetime.combine(mc_date_to_date(d_), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")
    mc0 = next(csv.DictReader(open(os.path.join(ROOT, "tests", "fixtures", "mc_L2_v5.10_trades.csv"))))["entry_dt"]
    base = L2TrendShortV511().config

    def run(strat):
        tr = [t for t in mc_compat.single_runner(strat, pol).run(b60).trades if ts(t.entry_date, t.entry_time) >= mc0]
        return [(ts(t.entry_date, t.entry_time), t.entry_label, t.entry_price, ts(t.exit_date, t.exit_time),
                 t.exit_label, t.exit_price, round(t.net_ntd(TXF))) for t in tr]

    def stats(tr):
        eq = pk = mdd = 0; yr = collections.Counter()
        for t in sorted(tr, key=lambda x: x[3]):
            eq += t[6]; pk = max(pk, eq); mdd = max(mdd, pk - eq); yr[t[3][:4]] += t[6]
        return len(tr), eq, mdd, dict(sorted(yr.items()))

    v511 = run(L2TrendShortV511())
    print("同根多張停損：", pol.intrabar.value)
    r0 = run(L2V512(new=dict(NEW, SP_Tier_Pts=0, LimitDn_On=0, Reb_On=0)))
    print("R0 三項全關 == v5.11 逐筆：", r0 == v511, "筆數", len(r0))
    t = run(L2V512())
    print("v5.11（大台 2 口）: 筆%d 淨利%s MDD%s 逐年%s" % stats(v511))
    print("v5.12 T          : 筆%d 淨利%s MDD%s 逐年%s" % stats(t))
    a, b = set(v511), set(t)
    print("只在 v5.11：")
    for x in sorted(a - b): print("   ", x)
    print("只在 v5.12：")
    for x in sorted(b - a): print("   ", x)


if __name__ == "__main__":
    main()
