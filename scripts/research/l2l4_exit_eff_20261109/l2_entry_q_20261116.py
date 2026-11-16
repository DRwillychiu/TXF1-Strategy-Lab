"""用法：python l2_entry_q_20261116.py <1分K 7欄> crash|c0|old|leg|legold|today|legtoday"""
import sys, collections, datetime as dt, inspect, textwrap, dataclasses
import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
sys.path.insert(0,ROOT); sys.path.insert(0,os.path.join(ROOT,"scripts","research","l2_v5_12_20261116"))
import txfcore.strategies.l2_trendshort_v5_11 as M
import predict as P
from txfcore.quotes.history import MC12MinuteSource
from txfcore.quotes.bars import aggregate_bars
from txfcore.profiles import mc_compat
from txfcore.instruments.spec import TXF
from txfcore.strategies.base import StrategyConfig
from txfcore.types.mctime import mc_date_to_date
ts=lambda d_,t: dt.datetime.combine(mc_date_to_date(d_),dt.time(t//100,t%100)).strftime("%Y-%m-%d %H:%M")
# variant: crash path also when weekly filter is bearish (remove FilterOK = False)
src=textwrap.dedent(inspect.getsource(M.L2TrendShortV511.on_bar)); assert src.count("not ps.wk.ok and not bear_sig")==1
ns=dict(vars(M)); exec(src.replace("not ps.wk.ok and not bear_sig","not bear_sig"), ns)
class CrashAll(M.L2TrendShortV511): pass
CrashAll.on_bar=ns["on_bar"]
class CrashAll512(P.L2V512): pass
def _ob(self, view, state):   # v5.12 wrapper around the crash-all on_bar
    return P.L2V512.on_bar.__wrapped__(self, view, state) if hasattr(P.L2V512.on_bar,"__wrapped__") else None
mode=sys.argv[2]
start,end=(1190102,(1261116,1145)) if mode not in ("old","legold") else (1000101,(1191231,2359))
mins=[m for m in MC12MinuteSource(sys.argv[1]).stream() if start<=m.mc_date and (m.mc_date,m.mc_time)<=end]
b60=list(aggregate_bars(mins,60))
mc0="2020-01-31 01:00" if mode not in ("old","legold") else "2001-01-01 00:00"
def run(strat):
    tr=[t for t in mc_compat.single_runner(strat).run(b60).trades if ts(t.entry_date,t.entry_time)>=mc0]
    eq=pk=mdd=0; yr=collections.Counter(); oos=0; n_cr=0
    for t in sorted(tr,key=lambda t:(t.exit_date,t.exit_time)):
        n=t.net_ntd(TXF)/20; eq+=n; pk=max(pk,eq); mdd=max(mdd,pk-eq); yr[ts(t.exit_date,t.exit_time)[:4]]+=n
        if ts(t.entry_date,t.entry_time)>"2026-09-24 23:59": oos+=n
        n_cr+=t.entry_label=="CR_Entry"
    w=sum(1 for t in tr if t.net_ntd(TXF)>0)
    return dict(n=len(tr),cr=n_cr,net=round(eq),mdd=round(mdd),oos=round(oos),win=round(w/len(tr)*100,1) if tr else 0,yr={k:round(v) for k,v in sorted(yr.items())}),tr
def cfg(over):
    base=M.L2TrendShortV511().config; p=dict(M.DEFAULT_PARAMS); p.update(over)
    return StrategyConfig(name=base.name,instrument=base.instrument,holiday_flat_time=base.holiday_flat_time,params=p)
if mode=="old":
    r,tr=run(M.L2TrendShortV511()); print("v5.11 2001-2019:",r)
elif mode=="c0":
    for c in (0.0,0.15,0.3,0.45,0.6,0.75):
        r,_=run(M.L2TrendShortV511(cfg({"C0_ATR_Filter":c}))); print(f"C0={c}:",r)
else:
    r,_=run(M.L2TrendShortV511()); print("v5.11       :",r)
    r,tr=run(CrashAll()); print("急跌單也在週線空頭:",r)
    print("新增/不同的急跌單(2026):",[(ts(t.entry_date,t.entry_time),t.entry_price,t.exit_label,t.exit_price,round(t.net_ntd(TXF)/20)) for t in tr if t.entry_label=="CR_Entry" and t.entry_date>=1260101])
if mode=="today":
    class T(CrashAll):
        def on_bar(self, view, state):
            st_,d=CrashAll.on_bar(self,view,state)
            if view.mc_date==1261116: print(view.mc_time,view.position.market_position.name,[o.label for o in d.orders])
            return st_,d
    run(T())
if mode in ("leg","legold"):
    import itertools
    combos=[("v5.11（現行）",M.L2TrendShortV511,{}),("只刪「同段只進一次」",M.L2TrendShortV511,{"Crash_Leg_Max":0}),
            ("只開週線空頭急跌",CrashAll,{}),("兩個都改",CrashAll,{"Crash_Leg_Max":0})]
    for nm,cls,over in combos:
        s=cls(cfg(over)) if over else cls()
        r,tr=run(s); print(nm,r)
        if mode=="leg" and nm=="兩個都改":
            print("  2026 急跌單:",[(ts(t.entry_date,t.entry_time),t.entry_price,t.exit_label,t.exit_price,round(t.net_ntd(TXF)/20)) for t in tr if t.entry_label=="CR_Entry" and t.entry_date>=1261001])
if mode=="legtoday":
    class T(CrashAll):
        def on_bar(self, view, state):
            st_,d=CrashAll.on_bar(self,view,state)
            if view.mc_date==1261116: print(view.mc_time,view.position.market_position.name,[(o.label,o.price) for o in d.orders])
            return st_,d
    run(T(cfg({"Crash_Leg_Max":0})))
