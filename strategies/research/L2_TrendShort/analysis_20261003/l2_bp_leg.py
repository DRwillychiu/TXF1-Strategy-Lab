# BP path with leg limit: at most K entries per pullback leg; leg resets when High >= the leg's anchor high (LB-bar high at first signal). Estimate (replay, not MC).
import datetime as dt, numpy as np, itertools, sys
from l2_bp_sim2 import BE,O,H,L,C,ATR,FOK,HH,n
from l2_bp_tp import stats
W=[('20/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('22/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('24/10-26/9',dt.datetime(2024,10,1),dt.datetime(2026,9,25))]
def sim(DD=3.0,LB=20,BODY=1.0,SLK=1.5,CAP=450,TRK=1.0,TMAX=40,K=1,TPR=0,start=dt.datetime(2020,6,1),end=dt.datetime(2026,9,25)):
    out=[]; pos=None; pend=False; leg_hh=None; leg_n=0
    def close(px): pos['pnl']+=2*((pos['ep']-px-10)*10)
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if leg_hh is not None and H[i]>=leg_hh: leg_hh=None; leg_n=0
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP)
            pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i],pnl=0.0,tgt=(ep-TPR*dist) if TPR else None); pend=False
        elif pos is not None and pos.get('mkt'):
            close(O[i]); out.append((BE[pos['ei']],pos['pnl'])); pos=None
        if pos is not None:
            if H[i]>=pos['stop']:
                close(max(O[i],pos['stop']) if i>pos['ei'] else pos['stop']); out.append((BE[pos['ei']],pos['pnl'])); pos=None
            elif pos['tgt'] is not None and i>pos['ei'] and L[i]<=pos['tgt']:
                close(min(O[i],pos['tgt'])); out.append((BE[pos['ei']],pos['pnl'])); pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i])
            if TRK: pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        if e.weekday()==2 and 15<=e.day<=21: continue
        if (not FOK[i]) and (1-C[i]/HH(i,LB))*100>=DD and (O[i]-C[i])>=BODY*ATR[i]:
            if K and leg_hh is not None and leg_n>=K: continue
            if leg_hh is None: leg_hh=HH(i,LB)
            leg_n+=1; pend=True
    return out
def ws(o): return [stats(o,a,b) for _,a,b in W]
def fmt(s): return f"n {s['n']} net {s['net']} MDD {s['mdd']} stk {s['streak']}({s['mcl']}) pf {s['pf']}"
def run(kw): return kw, ws(sim(**kw))
if __name__=='__main__':
    from multiprocessing import Pool
    jobs=[dict(K=k) for k in (0,1,2,3)]
    jobs+=[dict(K=1,DD=d,LB=lb,BODY=b) for d in (2.5,3.0,3.5,4.0) for lb in (15,20,30) for b in (0.8,1.0,1.2)]
    jobs+=[dict(K=1,TRK=t) for t in (0.75,1.25,1.5,2.0)]+[dict(K=1,SLK=s) for s in (1.0,1.25,2.0)]+[dict(K=1,TMAX=t) for t in (20,60)]
    with Pool(8) as p: res=p.map(run,jobs)
    import json; json.dump([(k,[dict(x) for x in s]) for k,s in res],open('/tmp/claude-0/l2_bp_leg.json','w'))
    for kw,s in res: print(f"{str(kw):45s} | "+" | ".join(fmt(x) for x in s))
