# T3 (Macro_Mode 2) vs T1 (Macro_Mode 0): which positions were added/removed, and their daily state at entry. Estimate.
import sys, pickle, bisect, datetime as dt, numpy as np, collections
sys.path.insert(0,'.')
from stopstruct import load, positions
S='/tmp/claude-0/-home-claude/80321d76-5295-5bee-b187-42c9b8d27a01/scratchpad/'
tdates,daily=pickle.load(open(S+'daily_1500.pkl','rb'))
DC=np.array([daily[d][3] for d in tdates]); DH=np.array([daily[d][1] for d in tdates]); DL=np.array([daily[d][2] for d in tdates])
ma=lambda x,n: np.convolve(x,np.ones(n)/n,'full')[:len(x)]
m20=ma(DC,20); m60=ma(DC,60)
pc=np.r_[DC[0],DC[:-1]]; tr=np.maximum(DH,pc)-np.minimum(DL,pc); atr20=ma(tr,20)
def di(t):
    d=t.date() if t.hour*100+t.minute<1500 else t.date()+dt.timedelta(days=1)
    return bisect.bisect_left(tdates,d)-1
def feat(t):
    j=di(t); A=DC[j]>m60[j] and m60[j]>=m60[j-1]; B=m20[j]>m60[j]
    er=abs(DC[j]-DC[j-20])/np.abs(np.diff(DC[j-20:j+1])).sum()
    return dict(A=A,B=B,d60=(DC[j]/m60[j]-1)*100,slope=(m60[j]/m60[j-5]-1)*100,g=(m20[j]/m60[j]-1)*100,datr=(DC[j]-m60[j])/atr20[j],er=er,c20=DC[j]<m20[j])
P1={p['edt']:p for p in positions(load('/tmp/L4T1.xlsx'))}
P3={p['edt']:p for p in positions(load('/tmp/L4T3.xlsx'))}
add=[P3[k] for k in sorted(set(P3)-set(P1))]; rem=[P1[k] for k in sorted(set(P1)-set(P3))]
print('added',len(add),round(sum(p['pnl'] for p in add)),' removed',len(rem),round(sum(p['pnl'] for p in rem)))
for p in rem: print('  REM',p['edt'],round(p['pnl']),p['xs'])
rows=[]
for p in add:
    f=feat(p['edt']); rows.append((p,f))
    print(f"{p['edt']:%Y/%m/%d %H:%M} {round(p['pnl']):>7} {'/'.join(x.replace('CS_','') for x in p['xs']):<18} A={int(f['A'])} B={int(f['B'])} d60={f['d60']:+5.1f}% slope5={f['slope']:+5.2f}% gap20/60={f['g']:+5.1f}% datr={f['datr']:+5.1f} er={f['er']:.2f} c<m20={int(f['c20'])}")
def grp(name,fn):
    g=collections.defaultdict(list)
    for p,f in rows: g[fn(f)].append(p['pnl'])
    print(name,{k:(len(v),round(sum(v)),sum(x>0 for x in v)) for k,v in sorted(g.items())})
grp('c<m20',lambda f:f['c20'])
grp('d60 bucket',lambda f:'<0' if f['d60']<0 else ('0-3' if f['d60']<3 else '>=3'))
grp('slope',lambda f:'down' if f['slope']<0 else 'up')
grp('er',lambda f:'<0.3' if f['er']<0.3 else '>=0.3')
grp('year',lambda f:None)
yr=collections.defaultdict(list)
for p,f in rows: yr[p['edt'].year].append(p['pnl'])
print('by year',{k:(len(v),round(sum(v))) for k,v in sorted(yr.items())})
