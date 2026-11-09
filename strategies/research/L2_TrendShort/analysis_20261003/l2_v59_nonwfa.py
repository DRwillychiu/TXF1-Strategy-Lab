# Rule #18 non-WFA 5-piece suite, pieces 1-4 (Python) for L2 v5.9 Crash_On 1 (defaults; MC 3,398,000 / 96).
# SOP: docs/methodology/non_WFA_validation_SOP_20260630.md. Units: micro NTD (MC / 20); account 300,000.
# Piece 5 (robustness +-10/20%) needs MC12 runs by Willy.
import sys, datetime as dt, collections, numpy as np
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
FILES={'v5.9 Crash_On 1':U+'e235d8fe-TXF1__L2_TrendShort_v5.9__________Crash_On__1.xlsx',
       'plan B (v5.8)':U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx'}
ACC=300_000; N=10_000; SEED=20261003
def mdd_of(x):
    eq=np.concatenate([[0],np.cumsum(x)]); return (eq-np.maximum.accumulate(eq)).min()
def pf(x):
    g=x[x>0].sum(); l=-x[x<0].sum(); return g/l if l>0 else np.inf
def piece1(x,rng):
    m=np.empty(N); ruin=0
    for k in range(N):
        s=rng.permutation(x); eq=ACC+np.concatenate([[0],np.cumsum(s)])
        m[k]=(eq-np.maximum.accumulate(eq)).min(); ruin+= eq.min()<ACC*0.5
    p95=np.percentile(m,5)
    return dict(mdd_hist=round(mdd_of(x)),mdd_p95=round(p95),mdd_p95_pct=round(-p95/ACC*100,1),ruin_pct=ruin/N*100,final=round(x.sum()),
                ok=(-p95<0.30*ACC) and ruin/N<0.01 and x.sum()>0)
def piece2(x,rng):
    P=[];S=[];T=[]
    for k in range(N):
        s=rng.choice(x,len(x),replace=True); P.append(pf(s)); S.append(s.mean()/s.std() if s.std()>0 else 0); T.append(s.sum())
    lo=lambda a:np.percentile(a,2.5)
    r=dict(pf_ci=(round(lo(P),2),round(np.percentile(P,97.5),2)),sharpe_lo=round(lo(S),3),net_ci=(round(lo(T)),round(np.percentile(T,97.5))),
           p_net_pos=round(np.mean(np.array(T)>0)*100,1))
    r['ok']=r['pf_ci'][0]>1 and r['sharpe_lo']>0 and r['net_ci'][0]>0
    return r
EV=[('2020 COVID',dt.datetime(2020,2,19),dt.datetime(2020,4,1)),('2024/8/5 BoJ',dt.datetime(2024,7,25),dt.datetime(2024,8,20)),
    ('2025/4 關稅',dt.datetime(2025,4,1),dt.datetime(2025,5,1)),('2026/6 急跌',dt.datetime(2026,6,1),dt.datetime(2026,7,1))]
def piece3(T):
    out=[];ok=True
    for nm,a,b in EV:
        tt=sorted([r for r in T if a<=r['edt']<b],key=lambda r:r['xdt']); x=np.array([r['pnl']/20 for r in tt])
        worst=x.min() if len(x) else 0; cl=0;c=0
        for v in x:
            c=c+v if v<0 else 0; cl=min(cl,c)
        e_ok= (-worst<0.05*ACC) and (-cl<0.15*ACC); ok&=e_ok
        out.append((nm,len(x),round(x.sum()) if len(x) else 0,round(worst),round(cl),e_ok))
    return out,ok
def daily_regime():
    from l2_funnel import BE,C
    d={}
    for e,c in zip(BE,C):
        if e.hour*100+e.minute<=1345 and e.hour>=8: d[e.date()]=c   # last day-session close of the date
    days=sorted(d); cl=np.array([d[x] for x in days])
    reg={}
    for i in range(50,len(days)):
        r=cl[i-20:i].mean()/cl[i-50:i].mean()      # MA20/MA50 of prior closes (no look-ahead)
        reg[days[i]]='多頭' if r>1.05 else ('空頭' if r<0.98 else '盤整')
    return reg,days
def piece4(T,reg,days):
    g=collections.defaultdict(list)
    for r in T:
        dd=r['edt'].date()
        while dd not in reg and dd>days[0]: dd-=dt.timedelta(days=1)
        g[reg.get(dd,'NA')].append(r['pnl']/20)
    res={k:(len(v),round(sum(v)),round(pf(np.array(v)),2)) for k,v in g.items()}
    pfs=[v[2] for v in res.values() if v[0]>0]; main=max(res.values(),key=lambda v:v[1])
    ok=sum(p>1 for p in pfs)>=2 and main[2]>2 and all(v[1]>-0.10*ACC for v in res.values())
    return res,ok
if __name__=='__main__':
    reg,days=daily_regime()
    for nm,f in FILES.items():
        T=load(f); x=np.array([r['pnl']/20 for r in sorted(T,key=lambda r:r['xdt'])]); rng=np.random.default_rng(SEED)
        p1=piece1(x,rng); p2=piece2(x,rng); p3,ok3=piece3(T); p4,ok4=piece4(T,reg,days)
        print(f'===== {nm}: n {len(x)} net {round(x.sum())} PF {pf(x):.2f}')
        print(' 1 MonteCarlo shuffle:',p1)
        print(' 2 Bootstrap:',p2)
        print(' 3 Stress (event, n, net, worst trade, worst cluster, ok):',p3,'OK' if ok3 else 'FAIL')
        print(' 4 Regime (n, net, PF):',p4,'OK' if ok4 else 'FAIL')
        srt=np.sort(x)[::-1]; print(' extra: remove top1 net',round(x.sum()-srt[0]),'top3',round(x.sum()-srt[:3].sum()),'| HHI of wins',round(((x[x>0]/x[x>0].sum())**2).sum(),3))
        cr=np.array([r['pnl']/20 for r in T if r['esig']=='CR_Entry'])
        if len(cr):
            rng2=np.random.default_rng(SEED); b=[rng2.choice(cr,len(cr)).sum() for _ in range(N)]
            print(f' crash subset: n {len(cr)} net {round(cr.sum())} PF {pf(cr):.2f} bootstrap P(net>0) {np.mean(np.array(b)>0)*100:.1f}% 95%CI ({round(np.percentile(b,2.5))},{round(np.percentile(b,97.5))}) | without top1 {round(cr.sum()-cr.max())}')
