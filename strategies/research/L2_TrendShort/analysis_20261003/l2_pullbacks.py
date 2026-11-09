# Bull pullbacks = 5% zigzag on daily high/low (2023+, excl. 2024/7-2025/4 bear segment) vs L2 entry funnel. Estimate.
import datetime as dt, numpy as np
from l2_funnel import BE,H,L,C,FOK,C0,CA,CB
dk={}
for i,e in enumerate(BE):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    dk.setdefault(k,[i,i]); dk[k][1]=i
D=sorted(dk); DH=np.array([H[dk[k][0]:dk[k][1]+1].max() for k in D]); DL=np.array([L[dk[k][0]:dk[k][1]+1].min() for k in D])
up=True; hi=0; lo=0; legs=[]
for i in range(len(D)):
    if up:
        if DH[i]>=DH[hi]: hi=i
        if DL[i]<=DH[hi]*0.95: up=False; lo=i
    else:
        if DL[i]<=DL[lo]: lo=i
        if DH[i]>=DL[lo]*1.05: legs.append((hi,lo)); up=True; hi=i
if not up: legs.append((hi,lo))
keep=[(a,b) for a,b in legs if D[a]>=dt.date(2023,1,1) and not (dt.date(2024,7,1)<=D[a]<dt.date(2025,5,1))]
rows=[]
for a,b in keep:
    i0=dk[D[a]][0]; i1=dk[D[b]][1]; win=range(i0,i1+1)
    sig=[i for i in win if C0[i] and CA[i] and CB[i]]
    r=dict(peak=D[a],ph=DH[a],trough=D[b],tl=DL[b],depth=(DL[b]/DH[a]-1)*100,days=b-a,fok=sum(FOK[i] for i in win),nsig=len(sig))
    if sig:
        s=sig[0]; r.update(first=BE[s],px=C[s],left=(C[s]-DL[b])/(DH[a]-DL[b])*100,pts=C[s]-DL[b])
    rows.append(r)
if __name__=='__main__':
    print(len(rows))
    for r in rows:
        st=f"{r['first']:%Y/%m/%d %H:%M} {r['px']:.0f} left {r['left']:.0f}% ({r['pts']:.0f} pts)" if r['nsig'] else 'none'
        print(f"{r['peak']} {r['ph']:.0f} -> {r['trough']} {r['tl']:.0f} {r['depth']:.1f}% {r['days']}d FOK {r['fok']} sig {r['nsig']} first {st}")
