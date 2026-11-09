# BP path take-profit variants: R-multiple target, percent target, partial (1 of 2 lots), with/without trailing. Estimate.
import datetime as dt, numpy as np, itertools
from l2_bp_sim2 import BE,O,H,L,C,ATR,FOK,HH,n
R2=(dt.datetime(2024,10,1),dt.datetime(2026,9,25)); IS=(dt.datetime(2023,1,1),dt.datetime(2024,10,1))
def sig(i,DD=3.0,LB=20,BODY=1.0): return (not FOK[i]) and (1-C[i]/HH(i,LB))*100>=DD and (O[i]-C[i])>=BODY*ATR[i]
def sim(SLK=1.5,CAP=450,TRK=1.0,TPR=0,TPP=0,PART=0,TMAX=40,start=dt.datetime(2023,1,1),end=dt.datetime(2026,9,25)):
    # returns list of (entry_time, pnl_micro) ; 2 lots, 10 per point per lot, cost 1000/side/lot -> 10 pts per lot round trip
    out=[]; pos=None; pend=False
    def close(lots,px):
        pos['pnl']+=lots*((pos['ep']-px-10)*10); pos['lots']-=lots
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP)
            tgt=None
            if TPR: tgt=ep-TPR*dist
            if TPP: tgt=ep*(1-TPP/100)
            pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i],lots=2,pnl=0.0,tgt=tgt,tgt_done=False); pend=False
        elif pos is not None and pos.get('mkt'):
            close(pos['lots'],O[i]); out.append((BE[pos['ei']],pos['pnl'])); pos=None
        if pos is not None:
            # intrabar: assume worst case order: stop checked before target if both touched in same bar
            if H[i]>=pos['stop']:
                px=max(O[i],pos['stop']) if i>pos['ei'] else pos['stop']
                close(pos['lots'],px); out.append((BE[pos['ei']],pos['pnl'])); pos=None
            elif pos['tgt'] is not None and not pos['tgt_done'] and i>pos['ei'] and L[i]<=pos['tgt']:   # MC: limit exit placed from entry-bar close
                px=min(O[i],pos['tgt']) if i>pos['ei'] else pos['tgt']
                lots=1 if PART else pos['lots']
                close(lots,px); pos['tgt_done']=True
                if pos['lots']==0: out.append((BE[pos['ei']],pos['pnl'])); pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i])
            if TRK and (pos['tgt'] is None or PART==0 or pos['tgt_done'] or PART==2):
                pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        if e.weekday()==2 and 15<=e.day<=21: continue
        if sig(i): pend=True
    return out
def stats(out,a,b):
    T=[t for t in out if a<=t[0]<b]; eq=pk=m=0; s=c=0; mc=cn=0
    for t in T:
        x=t[1]; eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        s=min(s,c); mc=max(mc,cn)
    W=[t[1] for t in T if t[1]>0]; Lo=[t[1] for t in T if t[1]<=0]
    return dict(n=len(T),net=round(eq),mdd=round(m),streak=round(s),mcl=mc,win=round(len(W)/max(1,len(T))*100),pf=round(sum(W)/abs(sum(Lo)),2) if Lo else 9.9)
if __name__=='__main__':
    cases=[('trail1.0 only',dict(TRK=1.0))]
    for r in (1.0,1.5,2.0,3.0):
        cases+= [(f'R{r} full',dict(TRK=0,TPR=r)),(f'R{r} full+trail',dict(TRK=1.0,TPR=r)),(f'R{r} half+trail',dict(TRK=1.0,TPR=r,PART=1))]
    for p in (1.0,1.5,2.0,3.0):
        cases+= [(f'P{p}% full',dict(TRK=0,TPP=p)),(f'P{p}% full+trail',dict(TRK=1.0,TPP=p)),(f'P{p}% half+trail',dict(TRK=1.0,TPP=p,PART=1))]
    for name,kw in cases:
        o=sim(**kw); a=stats(o,*R2); b=stats(o,*IS)
        print(f'{name:18s} | R2y n {a["n"]} net {a["net"]} MDD {a["mdd"]} streak {a["streak"]}({a["mcl"]}) win {a["win"]}% pf {a["pf"]} | 23-24/9 n {b["n"]} net {b["net"]}')
