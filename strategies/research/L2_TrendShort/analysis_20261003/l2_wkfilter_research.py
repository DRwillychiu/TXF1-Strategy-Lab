# Weekly filter research (Willy 10/3 14:18): what does FilterOK (Friday 12:45 close < 13-week SMA) block in bull years?
# Replay v5.3 logic (78/78 vs MC) with the entry filter removed, every trade tagged with the weekly state at its signal bar. Estimate.
import datetime as dt, collections, numpy as np
import l2_replay as R
from l2_funnel import BE,O,H,L,C
n=len(C); idx={e:i for i,e in enumerate(BE)}
# weekly state per bar, same update rule as v5.3 SECTION 5
wk=[]; FOK=np.zeros(n,bool); SMA=np.full(n,np.nan); LASTW=np.full(n,np.nan); SL4=np.full(n,np.nan); hist=[]
for i in range(1,n):
    if BE[i-1].hour==12 and BE[i-1].minute==45 and BE[i-1].weekday()==4:
        wk.insert(0,C[i-1]); wk=wk[:13]
        if len(wk)==13: hist.append(sum(wk)/13)
    if len(wk)==13:
        SMA[i]=sum(wk)/13; LASTW[i]=wk[0]; FOK[i]=wk[0]<SMA[i]
        if len(hist)>=5: SL4[i]=(hist[-1]/hist[-5]-1)*100
def tag(t):
    s=idx[t[0]]-1   # signal bar = bar before the entry bar
    return dict(et=t[0],pnl=R.pnl(t),fok=bool(FOK[s]),gap=(LASTW[s]/SMA[s]-1)*100,cur=(C[s]/SMA[s]-1)*100,slope=SL4[s],lab=t[4])
def summ(T,name):
    if not T: print(f'  {name:34s} n 0'); return
    x=[t['pnl'] for t in T]; W=[v for v in x if v>0]; Lo=[v for v in x if v<=0]
    eq=pk=m=0
    for v in x: eq+=v; pk=max(pk,eq); m=min(m,eq-pk)
    print(f'  {name:34s} n {len(T):3d} net {round(sum(x)):8d} avg {round(sum(x)/len(T)):6d} win {len(W)/len(T)*100:4.0f}% pf {sum(W)/abs(sum(Lo)) if Lo else 9.9:4.2f} MDD {round(m)}')
if __name__=='__main__':
    base=R.run(start=dt.datetime(2020,1,1)); assert len(base)==78
    for nm,ov in (('A1 no entry filter, weekly exit ON',dict(WKIN=0)),('A2 no entry filter, weekly exit OFF',dict(WKIN=0,WKEX=0))):
        T=[tag(t) for t in R.run(OV=ov,start=dt.datetime(2020,1,1))]
        print(f'== {nm}')
        summ(T,'all'); summ([t for t in T if t['fok']],'FilterOK on (= live trades region)'); off=[t for t in T if not t['fok']]; summ(off,'FilterOK off (blocked in live)')
        for a,b,lab in ((-99,0,'off & last weekly close < SMA ?'),(0,2,'off, weekly gap 0-2%'),(2,4,'off, gap 2-4%'),(4,7,'off, gap 4-7%'),(7,99,'off, gap > 7%')):
            summ([t for t in off if a<=t['gap']<b],lab)
        summ([t for t in off if t['cur']<0],'off, but price NOW below SMA13')
        summ([t for t in off if t['cur']>=0],'off, price now above SMA13')
        summ([t for t in off if t['slope']<0],'off, SMA13 falling (4 wk)')
        summ([t for t in off if t['slope']>=0],'off, SMA13 rising (4 wk)')
        y=collections.defaultdict(list)
        for t in off: y[t['et'].year].append(t)
        for k in sorted(y): summ(y[k],f'off, year {k}')
        print('   exit labels (off):',dict(collections.Counter(t['lab'] for t in off)))
    # lag: each FilterOK-on episode since 2020 - decline already done when it turns on, and what came after
    print('== filter lag (FilterOK on episodes since 2020)')
    ep=[]; prev=False
    for i in range(n):
        if BE[i]<dt.datetime(2020,1,1): prev=FOK[i]; continue
        if FOK[i] and not prev: s=i
        if prev and not FOK[i]: ep.append((s,i))
        prev=FOK[i]
    for s,e in ep:
        pk=C[max(0,s-13*19):s+1].max(); low=C[s:e+1].min()
        print(f'  on {BE[s]:%Y/%m/%d} -> off {BE[e]:%Y/%m/%d} ({(BE[e]-BE[s]).days:3d}d) | down from 13w high when ON {(C[s]/pk-1)*100:5.1f}% | further low after ON {(low/C[s]-1)*100:5.1f}% | price at OFF vs ON {(C[e]/C[s]-1)*100:5.1f}%')
    # volatility split of the blocked (FilterOK off) trades: is the bull-year problem price-vs-SMA or volatility?
    from l2_funnel import ATR
    T=[tag(t) for t in R.run(OV=dict(WKIN=0),start=dt.datetime(2020,1,1))]
    for t in T: s=idx[t['et']]-1; t['atrp']=ATR[s]/C[s]*100
    off=[t for t in T if not t['fok']]
    print('== A1 blocked trades by ATR% at signal')
    for a,b in ((0,0.45),(0.45,0.55),(0.55,0.7),(0.7,9)):
        summ([t for t in off if a<=t['atrp']<b],f'off, ATR% {a}-{b}')
    on=[t for t in T if t['fok']]
    for a,b in ((0,0.55),(0.55,9)):
        summ([t for t in on if a<=t['atrp']<b],f'ON (live region), ATR% {a}-{b}')
    L=[(BE[s],(C[s]/C[max(0,s-13*19):s+1].max()-1)*100) for s,e in ep]
    print('median decline already done when filter turns ON:',round(float(np.median([x for _,x in L])),1),'% | long episodes (>=60d):',sum(1 for s,e in ep if (BE[e]-BE[s]).days>=60),'of',len(ep))
