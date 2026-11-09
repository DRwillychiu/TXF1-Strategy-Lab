# "Does L2 only fit the past?" (Willy 10/3 14:22). Base = v5.6 (#26 2 regime pause). Replay estimate.
# 1) fixed-point constant stopProfitPoints_Shrt 250: at today's index 250 pts = 0.52% of price (vs ~1.5% in 2020-22).
#    Emulate "250 at 48,091" with a % threshold 0.52%, and test ATR / % forms that do not drift with the index level.
# 2) volatility inside the live (filter-on) region by year.
import datetime as dt, collections, numpy as np
import l2_replay_pause as R
from l2_v56_expect import st, W
from l2_funnel import BE, C, ATR
idx={e:i for i,e in enumerate(BE)}
def run(**ov): return R.run(OV=ov,start=dt.datetime(2020,1,1),PN=2,PR=True)
base=run(); assert len(base)==40, len(base)
ep=[t[1] for t in base]; print('v5.6 entry price range',round(min(ep)),round(max(ep)),'| 250 pts as % of entry: median',round(float(np.median([250/x*100 for x in ep])),2),'% ; at 48,091 =',round(250/48091*100,2),'%')
# ATR at entry in pts and 250/ATR
ar=[ATR[idx[t[0]]-1] for t in base]; print('ATR(60M) at signal: median',round(float(np.median(ar))),'pts | 250/ATR median',round(float(np.median([250/a for a in ar])),2),'| today ATR ~ 0.8% x 48,091 =',round(0.008*48091))
def show(nm,T):
    s=[st(T,a,b) for _,a,b in W]; print(f'{nm:30s} | '+' | '.join(f'{W[k][0]} n {x[0]} net {x[1]} MDD {x[2]} stk {x[3]}({x[4]})' for k,x in enumerate(s)))
show('v5.6 base (SPP 250 pts)',base)
show('SPP 0.52% (= 250 at 48,091)',run(SPPPCT=0.52))
for p in (1.0,1.5,2.0): show(f'SPP {p}% of entry',run(SPPPCT=p))
for k in (1.5,2.0,2.5,3.0): show(f'SPP {k} x ATR',run(SPPATR=k))
# live-region trades by volatility and year (v5.3 = all 78)
T=R.run(start=dt.datetime(2020,1,1))
hv=collections.defaultdict(lambda:[0,0.0]); lv=collections.defaultdict(lambda:[0,0.0])
for t in T:
    s=idx[t[0]]-1; a=ATR[s]/C[s]*100; d=hv if a>=0.55 else lv; d[t[0].year][0]+=1; d[t[0].year][1]+=R.pnl(t)
print('live region ATR%>=0.55 by year',{k:(v[0],round(v[1])) for k,v in sorted(hv.items())})
print('live region ATR%< 0.55 by year',{k:(v[0],round(v[1])) for k,v in sorted(lv.items())})
