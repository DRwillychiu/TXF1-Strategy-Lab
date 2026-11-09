# L1 V3.2 (L1_0) attribution vs L1_0b (ReEntry_On 0). micro = MC/20. NOTE: both reports have Bar Magnifier OFF.
import sys, datetime as dt, collections, statistics as stt
sys.path.insert(0,'.')
from stopstruct import load
A=dt.datetime; NOW=48091; ACC=300000
def rows(f):
    R=load(f)
    for r in R: r['m']=r['pnl']/20; r['hrs']=(r['xdt']-r['edt']).total_seconds()/3600; r['pct']=-(r['xpx']-r['epx'])/r['epx']*100 if r['pnl']<0 else 0
    return sorted(R,key=lambda r:r['xdt'])
def sess(t):
    hm=t.hour*100+t.minute
    return 'D' if 845<=hm<=1345 else 'N'
def curve(R,key='m'):
    eq=pk=0;pkd=R[0]['xdt'];mdd=0;md=None;s=c=0;n=cn=0;sd=None;cs=None
    for r in R:
        x=r[key]; eq+=x
        if eq>=pk: pk=eq;pkd=r['xdt']
        elif eq-pk<mdd: mdd=eq-pk; md=(pkd,r['xdt'])
        if x<0:
            if c==0: cs=r['edt']
            c+=x;cn+=1
        else: c=0;cn=0
        if c<s: s=c;n=cn;sd=(cs,r['xdt'])
    return eq,mdd,md,s,n,sd
R=rows('/tmp/L1_0.xlsx'); B=rows('/tmp/L1_0b.xlsx')
for r in R: r['norm']=r['m']/r['epx']*NOW
print('trades',len(R),'reentry',sum(r['esig']=='TL_ReEntry' for r in R))
eq,mdd,md,s,n,sd=curve(R); print('full net',round(eq),'MDD',round(mdd),[d.date() for d in md],'streak',round(s),n,[d.date() for d in sd])
def seg(a,b,RR=R):
    Q=[r for r in RR if a<=r['edt']<b]; e,m,_,s_,n_,_=curve(Q) if Q else (0,0,None,0,0,None)
    w=sum(r['m']>0 for r in Q); return len(Q),round(e),round(m),round(s_),n_,round(w/max(1,len(Q))*100,1)
print('IS 2019/12-2026/6/16',seg(A(2019,1,1),A(2026,6,17)),' OOS 6/17-9/24',seg(A(2026,6,17),A(2026,9,25)))
print('L1_0b IS',seg(A(2019,1,1),A(2026,6,17),B),' OOS',seg(A(2026,6,17),A(2026,9,25),B))
y=collections.defaultdict(lambda:[0,0.0]); 
for r in R: y[r['xdt'].year][0]+=1; y[r['xdt'].year][1]+=r['m']
print('yearly',{k:(v[0],round(v[1])) for k,v in sorted(y.items())})
for yr in sorted(y):
    Q=[r for r in R if r['xdt'].year==yr]; e,m,_,s_,n_,_=curve(Q); print('  ',yr,'MDD',round(m),'streak',round(s_),n_)
ex=collections.defaultdict(lambda:[0,0.0])
for r in R: ex[r['xsig']][0]+=1; ex[r['xsig']][1]+=r['m']
print('exits',{k:(v[0],round(v[1]),round(v[1]/v[0])) for k,v in sorted(ex.items(),key=lambda kv:kv[1][1])})
hb=collections.defaultdict(lambda:[0,0.0,0])
for r in R:
    k='<4h' if r['hrs']<4 else ('4-24h' if r['hrs']<24 else '>=24h'); hb[k][0]+=1; hb[k][1]+=r['m']; hb[k][2]+=r['m']>0
print('hold',{k:(v[0],round(v[1]),round(v[2]/v[0]*100)) for k,v in hb.items()})
tot=sum(r['m'] for r in R); top=sorted(R,key=lambda r:-r['m'])
print('top10 share',round(sum(r['m'] for r in top[:10])/tot*100),'top20',round(sum(r['m'] for r in top[:20])/tot*100))
# session of entry
se=collections.defaultdict(lambda:[0,0.0,0])
for r in R: k=sess(r['edt']); se[k][0]+=1; se[k][1]+=r['m']; se[k][2]+=r['m']>0
print('entry session',{k:(v[0],round(v[1]),round(v[2]/v[0]*100)) for k,v in se.items()})
# losses vs 0.5% cap (realized loss % of entry)
L=[r for r in R if r['m']<0]
print('losers',len(L),'sum',round(sum(r['m'] for r in L)))
over=[r for r in L if r['pct']>0.6]
print('loss > 0.6% of entry (120% of 0.5% cap):',len(over),round(sum(r['m'] for r in over)))
cross=[r for r in over if sess(r['edt'])!=sess(r['xdt']) or (r['xdt']-r['edt']).total_seconds()>6*3600]
for r in sorted(over,key=lambda r:r['m'])[:25]:
    print('   ',r['edt'].strftime('%Y/%m/%d %H:%M'),sess(r['edt']),'->',r['xdt'].strftime('%m/%d %H:%M'),sess(r['xdt']),r['xsig'],round(r['m']),'pts/lot',round(-r['m']/20),f"{r['pct']:.2f}%")
yo=collections.Counter(r['xdt'].year for r in over); print('over by year',dict(sorted(yo.items())))
# normalized
e2,m2,md2,s2,n2,_=curve(R,'norm'); print('norm@48091 net',round(e2),'MDD',round(m2),f'{-m2/ACC*100:.1f}%','streak',round(s2),n2,f'{-s2/ACC*100:.1f}%', [d.date() for d in md2])
big=min(R,key=lambda r:r['norm']); print('norm max single',round(big['norm']),round(-big['norm']/20),'pts',big['edt'])
# MDD window composition
a,b=md; W=[r for r in R if a<r['xdt']<=b]
cw=collections.defaultdict(lambda:[0,0.0])
for r in W: cw[r['xsig']][0]+=1; cw[r['xsig']][1]+=r['m']
print('MDD window trades',len(W),{k:(v[0],round(v[1])) for k,v in cw.items()}, 'winrate',round(sum(r['m']>0 for r in W)/len(W)*100))
# reentry
for r in R:
    if r['esig']=='TL_ReEntry': print('  RE',r['edt'].strftime('%Y/%m/%d %H:%M'),r['epx'],r['xsig'],round(r['m']))
