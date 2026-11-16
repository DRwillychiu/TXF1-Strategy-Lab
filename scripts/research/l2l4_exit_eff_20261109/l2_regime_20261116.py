"""用法：python l2_regime_20261116.py <1分K 7欄> leg|regime"""
import sys, os, collections, datetime as dt, bisect, statistics as stt
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..","..")); sys.path.insert(0,ROOT)
import txfcore.strategies.l2_trendshort_v5_11 as M
from txfcore.quotes.history import MC12MinuteSource
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.daily import NIGHT_FIRST, build
from txfcore.profiles import mc_compat
from txfcore.instruments.spec import TXF
from txfcore.strategies.base import StrategyConfig
from txfcore.types.mctime import mc_date_to_date
ts=lambda d_,t: dt.datetime.combine(mc_date_to_date(d_),dt.time(t//100,t%100)).strftime("%Y-%m-%d %H:%M")
allm=list(MC12MinuteSource(sys.argv[1]).stream())
def trades(start,end,mc0,over=None):
    mins=[m for m in allm if start<=m.mc_date and (m.mc_date,m.mc_time)<=end]
    b60=list(aggregate_bars(mins,60))
    base=M.L2TrendShortV511().config; p=dict(M.DEFAULT_PARAMS); p.update(over or {})
    s=M.L2TrendShortV511(StrategyConfig(name=base.name,instrument=base.instrument,holiday_flat_time=base.holiday_flat_time,params=p))
    return [t for t in mc_compat.single_runner(s).run(b60).trades if ts(t.entry_date,t.entry_time)>=mc0]
mode=sys.argv[2]
if mode=="leg":
    for nm,(st_,en,m0) in {"2020-11/16":(1190102,(1261116,1145),"2020-01-31 01:00"),"2001-2019":(1000101,(1191231,2359),"2001-01-01 00:00")}.items():
        a=trades(st_,en,m0); b=trades(st_,en,m0,{"Crash_Leg_Max":0})
        key=lambda t:(t.entry_date,t.entry_time,t.entry_label,t.entry_price,t.exit_date,t.exit_time,t.exit_price)
        ka={key(t) for t in a}
        extra=[t for t in b if t.entry_label=="CR_Entry" and key(t) not in ka]
        n=[t.net_ntd(TXF)/20 for t in extra]
        print(nm,"多出的急跌單",len(n),"勝率%.0f%%"%(sum(x>0 for x in n)/len(n)*100),"平均每筆%.0f"%stt.mean(n),"合計%.0f"%sum(n),"中位數%.0f"%stt.median(n))
    sys.exit()
# regime descriptors per entry, from daily bars known before entry day
daily=build([m for m in allm],NIGHT_FIRST)
dk=[b.mc_date for b in daily]
wk=collections.OrderedDict()
for b in daily:
    d=mc_date_to_date(b.mc_date); y,w,_=d.isocalendar(); wk.setdefault((y,w),[]).append(b)
wkeys=list(wk)
def feats(mc_date):
    i=bisect.bisect_left(dk,mc_date)-1
    if i<25: return None
    trs=[max(daily[k].high-daily[k].low,abs(daily[k].high-daily[k-1].close),abs(daily[k].low-daily[k-1].close)) for k in range(i-19,i+1)]
    atrp=sum(trs)/20/daily[i].close*100
    d=mc_date_to_date(mc_date); y,w,_=d.isocalendar(); j=wkeys.index((y,w))
    ws=[wk[wkeys[k]] for k in range(j-4,j)]         # 4 個已完成的週
    wr=[(max(b.high for b in x)-min(b.low for b in x))/x[-1].close*100 for x in ws]
    eff=[(max(b.high for b in x)-min(b.low for b in x))/sum(b.high-b.low for b in x) for x in ws]
    return atrp, stt.mean(wr), stt.mean(eff)
rows={}
for nm,(st_,en,m0) in {"IS":(1190102,(1261116,1145),"2020-01-31 01:00"),"OOS":(1000101,(1191231,2359),"2001-01-01 00:00")}.items():
    pos=collections.OrderedDict()
    for t in trades(st_,en,m0):
        pos.setdefault((t.entry_date,t.entry_time),[]).append(t)
    rows[nm]=[(feats(k[0]),sum(x.net_ntd(TXF) for x in v)/20) for k,v in pos.items()]
    rows[nm]=[r for r in rows[nm] if r[0]]
for fi,fn in enumerate(["日ATR%(20日)","週振幅%(前4週平均)","週效率(週振幅÷5日振幅和)"]):
    v=sorted(r[0][fi] for r in rows["IS"]); c1,c2=v[len(v)//3],v[2*len(v)//3]
    print(f"\n{fn}  切點(用2020-2026算)：{c1:.2f} / {c2:.2f}")
    for nm in ("IS","OOS"):
        g=collections.defaultdict(list)
        for f,n in rows[nm]: g[0 if f[fi]<c1 else 1 if f[fi]<c2 else 2].append(n)
        print("  ",nm, "  ".join(f"{['低','中','高'][k]}: {len(g[k])}筆 淨{sum(g[k]):,.0f} 平均{(sum(g[k])/len(g[k]) if g[k] else 0):,.0f}" for k in range(3)))
