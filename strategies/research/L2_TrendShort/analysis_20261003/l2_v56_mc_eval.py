# Evaluate MC v5.6 reports (10/3 14:08): regression vs L2_540, windows, streaks, trade diff vs replay. MC big units; micro = /20.
import sys, glob, datetime as dt, collections, openpyxl
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
F={'v5.6 default':U+'a599c996-TXF1__L2_TrendShort_v5.6_________.xlsx','#26 2 #27 0':U+'6788b1da-TXF1__L2_TrendShort_v5.6__________26_2.xlsx',
   '#26 2 #27 800':U+'7fc2b763-TXF1__L2_TrendShort_v5.6__________26_2_800.xlsx','#26 3 #27 0':U+'b3a07a1d-TXF1__L2_TrendShort_v5.6__________26_3.xlsx'}
K=['淨利','交易總次數','最大策略虧損','最大連續虧損交易次數','最大連續虧損金額','最大的交易虧損','獲利因子']
def mc(f):
    wb=openpyxl.load_workbook(f,read_only=True); m={}
    for sh in ('策略分析','交易分析'):
        for row in wb[sh].iter_rows(values_only=True):
            r=[c for c in row if c is not None]
            if len(r)>=2 and isinstance(r[0],str) and r[0].strip() in K and r[0].strip() not in m: m[r[0].strip()]=r[1]
    return m
W=[('全期',dt.datetime(2019,1,1),dt.datetime(2026,9,25)),('2020/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('2022/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('近兩年',dt.datetime(2024,10,1),dt.datetime(2026,9,25))]
def st(T,a,b):
    T=sorted([r for r in T if a<=r['edt']<b],key=lambda r:r['xdt']); eq=pk=m=0; c=s=0; cn=sn=mc_=0
    for r in T:
        x=r['pnl']/20; eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
        mc_=max(mc_,cn)
    return dict(n=len(T),net=round(eq),mdd=round(m),stk=round(s),sn=sn,mcl=mc_)
R={k:load(f) for k,f in F.items()}; M={k:mc(f) for k,f in F.items()}
L540=load('/tmp/L2_540.xlsx')
a=[(r['edt'],r['xdt'],round(r['pnl'])) for r in R['v5.6 default']]; b=[(r['edt'],r['xdt'],round(r['pnl'])) for r in L540]
print('regression vs L2_540 trade-by-trade:', 'IDENTICAL' if a==b else f'DIFF {len(a)} vs {len(b)}', len(a))
for k in F:
    print(f'== {k} | MC summary:',{x:M[k].get(x) for x in K})
    for wn,a_,b_ in W:
        s=st(R[k],a_,b_); print(f'   {wn:13s} n {s["n"]} net {s["net"]} MDD {s["mdd"]} streak {s["stk"]}({s["sn"]}) maxLosers {s["mcl"]}')
    lab=collections.Counter(r.get('xsig') or r.get('exit') or r.get('xlab') for r in R[k]); print('   exit labels:',dict(lab))
print('keys in trade rec:',list(R['v5.6 default'][0].keys()))
# trade diff vs replay predictions
import l2_replay_pause as RP
for k,(pn,pb) in (('#26 2 #27 0',(2,0)),('#26 2 #27 800',(2,800)),('#26 3 #27 0',(3,0))):
    rp=RP.run(start=dt.datetime(2020,1,1),PN=pn,PR=True,PB=pb)
    re_=set(t[0] for t in rp); me=set(r['edt'] for r in R[k])
    print(k,'MC n',len(me),'replay n',len(re_),'| in MC not replay',sorted(me-re_)[:5],'| in replay not MC',sorted(re_-me)[:5])

# normalized to index 48,091 (P&L / entry price x 48,091), yearly split, removed trades
NOW=48091
def norm(T):
    U=[dict(r) for r in T]
    for r in U: r['pnl']=r['pnl']/r['epx']*NOW
    return U
for k in ('v5.6 default','#26 2 #27 0','#26 3 #27 0'):
    s=st(norm(R[k]),*W[0][1:]); r2=st(norm(R[k]),*W[3][1:])
    print(f'{k:14s} normalized@48,091 全期 MDD {s["mdd"]} ({-s["mdd"]/3000:.1f}%) streak {s["stk"]} ({-s["stk"]/3000:.1f}%) | 近兩年 MDD {r2["mdd"]} streak {r2["stk"]}')
def yr(T):
    y=collections.defaultdict(float)
    for r in T: y[r['edt'].year]+=r['pnl']/20
    return {a:round(b) for a,b in sorted(y.items())}
print('yearly v5.3 ',yr(R['v5.6 default'])); print('yearly #26 2',yr(R['#26 2 #27 0'])); print('yearly #26 3',yr(R['#26 3 #27 0']))
keep=set(r['edt'] for r in R['#26 2 #27 0']); rem=[r for r in R['v5.6 default'] if r['edt'] not in keep]
W_=[r['pnl']/20 for r in rem if r['pnl']>0]; L_=[r['pnl']/20 for r in rem if r['pnl']<=0]
print('removed by #26 2:',len(rem),'winners',len(W_),round(sum(W_)),'losers',len(L_),round(sum(L_)))
print('top removed winners:',sorted([(f"{r['edt']:%Y/%m/%d}",round(r['pnl']/20)) for r in rem],key=lambda x:-x[1])[:6])
