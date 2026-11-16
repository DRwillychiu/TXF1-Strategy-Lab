import sys, collections, datetime as dt, csv
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT); os.chdir(ROOT)
from txfcore.strategies.l2_trendshort_v5_11 import DEFAULT_PARAMS, L2TrendShortV511, STRATEGY_NAME
from txfcore.strategies.base import StrategyConfig
from txfcore.profiles import mc_compat
from txfcore.instruments.spec import TXF
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.history import MC12MinuteSource
from txfcore.types.mctime import mc_date_to_date
mins=[m for m in MC12MinuteSource(sys.argv[1]).stream() if 1190102<=m.mc_date<=1261107]
b60=list(aggregate_bars(mins,60))
ts=lambda d,t: dt.datetime.combine(mc_date_to_date(d),dt.time(t//100,t%100)).strftime("%Y-%m-%d %H:%M")
mc0=next(csv.DictReader(open("tests/fixtures/mc_L2_v5.10_trades.csv")))["entry_dt"]
base=L2TrendShortV511().config
def run(over):
    p=dict(DEFAULT_PARAMS); p.update(over)
    s=L2TrendShortV511(StrategyConfig(name=base.name,instrument=base.instrument,holiday_flat_time=base.holiday_flat_time,params=p)) if over else L2TrendShortV511()
    tr=[t for t in mc_compat.single_runner(s).run(b60).trades if ts(t.entry_date,t.entry_time)>=mc0]
    eq=pk=mdd=0; yr=collections.Counter(); oos=0
    for t in sorted(tr,key=lambda t:(t.exit_date,t.exit_time)):
        n=t.net_ntd(TXF)/20; eq+=n; pk=max(pk,eq); mdd=max(mdd,pk-eq); yr[str(t.exit_date)[1:3]]+=n
        if ts(t.entry_date,t.entry_time)>"2026-09-24 23:59": oos+=n
    return len(tr),eq,mdd,oos,yr
print("cfg",base.name,base.holiday_flat_time)
for rp in (35,45,55,65):
  for ma in (2.0,3.0,4.0):
    n,e,m,o,yr=run({} if (rp,ma)==(55,4.0) else {"profitReturnPrcnt_Shrt":rp,"TTP_MinAtr":ma})
    print(f"保留{100-rp}% TTP≥{ma}ATR: 筆{n} 淨{e:,.0f} MDD{m:,.0f} 9/25後{o:,.0f} 逐年",{k:round(v) for k,v in sorted(yr.items())})
