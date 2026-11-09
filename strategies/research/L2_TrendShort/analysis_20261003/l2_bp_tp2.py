# BP path take-profit v2: depth target anchored at the 20-bar high (TPD %), R / % targets, plus re-entry cooldown. Estimate (replay, not MC).
import datetime as dt, numpy as np
from l2_bp_sim2 import BE,O,H,L,C,ATR,FOK,HH,n
from l2_bp_tp import stats
W=[('20/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('22/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('24/10-26/9',dt.datetime(2024,10,1),dt.datetime(2026,9,25))]
def sig(i,DD=3.0,LB=20,BODY=1.0): return (not FOK[i]) and (1-C[i]/HH(i,LB))*100>=DD and (O[i]-C[i])>=BODY*ATR[i]
def sim(SLK=1.5,CAP=450,TRK=1.0,TPR=0,TPP=0,TPD=0,COOL=0,LEG=0,TMAX=40,start=dt.datetime(2020,6,1),end=dt.datetime(2026,9,25)):
    out=[]; pos=None; pend=None; block=-1; anchor=None
    def close(px): pos['pnl']+=2*((pos['ep']-px-10)*10)
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if pend is not None and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP); hh=pend; tgt=None
            if TPR: tgt=ep-TPR*dist
            if TPP: tgt=ep*(1-TPP/100)
            if TPD:
                t=hh*(1-TPD/100); tgt=t if t<ep else None
            pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i],pnl=0.0,tgt=tgt,hh=hh); pend=None
        elif pos is not None and pos.get('mkt'):
            close(O[i]); out.append((BE[pos['ei']],pos['pnl'],'T')); block=(i+COOL if COOL else -1); anchor=pos['hh']; pos=None
        if pos is not None:
            if H[i]>=pos['stop']:
                close(max(O[i],pos['stop']) if i>pos['ei'] else pos['stop']); out.append((BE[pos['ei']],pos['pnl'],'S')); block=(i+COOL if COOL else -1); anchor=pos['hh']; pos=None
            elif pos['tgt'] is not None and i>pos['ei'] and L[i]<=pos['tgt']:
                close(min(O[i],pos['tgt'])); out.append((BE[pos['ei']],pos['pnl'],'P')); block=(i+COOL if COOL else -1); anchor=pos['hh']; pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i])
            if TRK: pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        if e.weekday()==2 and 15<=e.day<=21: continue
        if i<=block: continue
        if LEG and anchor is not None:
            if H[i]>=anchor: anchor=None   # leg over: new high made
            else: continue
        if sig(i): pend=HH(i,20)
    return out
def row(name,o):
    s=[stats([(t[0],t[1]) for t in o],a,b) for _,a,b in W]
    return f"{name:22s} | "+" | ".join(f"n {x['n']} net {x['net']} MDD {x['mdd']} stk {x['streak']}({x['mcl']}) pf {x['pf']}" for x in s)
if __name__=='__main__':
    from l2_pullbacks import rows
    d=[r['depth'] for r in rows if r['peak']>=dt.date(2024,10,1)]
    print('leg depth since 2024/10 (5% zigzag):',len(d),'median',round(float(np.median(d)),1),'p25',round(float(np.percentile(d,25)),1),'p75',round(float(np.percentile(d,75)),1))
    print(row('trail only',sim()))
    for c in (10,20): print(row(f'trail COOL{c}',sim(COOL=c)))
    print(row('trail LEG',sim(LEG=1)))
    for p in (5,6,7,8): 
        print(row(f'D{p}%+trail',sim(TPD=p)))
        print(row(f'D{p}%+trail LEG',sim(TPD=p,LEG=1)))
    for r in (1.0,1.5,2.0):
        print(row(f'R{r}+trail LEG',sim(TPR=r,LEG=1)))
    for p in (1.0,1.5,2.0):
        print(row(f'P{p}%+trail LEG',sim(TPP=p,LEG=1)))
