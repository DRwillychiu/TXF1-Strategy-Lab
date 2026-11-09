# BP path: leg limit K + pause after PN consecutive BP losses for PB 60M bars. Estimate (replay, not MC).
import datetime as dt
import l2_bp_leg as M
from l2_bp_leg import BE,O,H,L,C,ATR,FOK,HH,n,ws,fmt
def sim(K=1,PN=0,PB=0,DD=3.0,LB=20,BODY=1.0,SLK=1.5,CAP=450,TRK=1.0,TMAX=40,start=dt.datetime(2020,6,1),end=dt.datetime(2026,9,25)):
    out=[]; pos=None; pend=False; leg_hh=None; leg_n=0; cl=0; pause_to=-1
    def close(px): pos['pnl']+=2*((pos['ep']-px-10)*10)
    def done(i):
        nonlocal cl,pause_to
        out.append((BE[pos['ei']],pos['pnl']))
        cl=cl+1 if pos['pnl']<0 else 0
        if PN and cl>=PN: pause_to=i+PB; cl=0
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if leg_hh is not None and H[i]>=leg_hh: leg_hh=None; leg_n=0
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP); pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i],pnl=0.0); pend=False
        elif pos is not None and pos.get('mkt'):
            close(O[i]); done(i); pos=None
        if pos is not None and H[i]>=pos['stop']:
            close(max(O[i],pos['stop']) if i>pos['ei'] else pos['stop']); done(i); pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i]); pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        if e.weekday()==2 and 15<=e.day<=21: continue
        if i<=pause_to: continue
        if (not FOK[i]) and (1-C[i]/HH(i,LB))*100>=DD and (O[i]-C[i])>=BODY*ATR[i]:
            if K and leg_hh is not None and leg_n>=K: continue
            if leg_hh is None: leg_hh=HH(i,LB)
            leg_n+=1; pend=True
    return out
if __name__=='__main__':
    assert [round(t[1]) for t in sim(K=1)]==[round(t[1]) for t in M.sim(K=1)]
    for k in (0,1,2):
        for pn,pb in ((0,0),(2,200),(3,200),(3,400),(3,800)):
            print(f"K{k} pause {pn}/{pb:4d} | "+" | ".join(fmt(x) for x in ws(sim(K=k,PN=pn,PB=pb))))
