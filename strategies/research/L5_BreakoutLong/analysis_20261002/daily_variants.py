import sys, pickle, numpy as np, datetime as dt, collections
sys.path.insert(0,'..'); sys.path.insert(0,'.')
from stopstruct import load, positions
F='/mnt/user-data/uploads/TXF1_1_分鐘_1.txt'
rows=[]
with open(F) as fh:
    next(fh)
    for line in fh:
        p=line.strip().split(',')
        if len(p)<6: continue
        y,m,d=map(int,p[0].split('/')); hh,mm=int(p[1][0:2]),int(p[1][3:5])
        rows.append((dt.datetime(y,m,d,hh,mm),float(p[3]),float(p[4]),float(p[5])))
rows.sort()
def build(kind):
    bars=collections.OrderedDict()
    tdates=sorted({r[0].date() for r in rows if 845<r[0].hour*100+r[0].minute<=1345})
    import bisect
    for t,h,l,c in rows:
        hm=t.hour*100+t.minute
        if kind=='cal':   # same calendar-day close merge: night minutes -> date of 05:00 close
            if 845<hm<=1345: key=(t.date(),dt.time(13,45))
            elif hm>1345: key=(t.date()+dt.timedelta(days=1),None)
            else: key=(t.date(),None)
        elif kind=='1345':  # all sessions close at 13:45 -> night goes to next day-session date
            if 845<hm<=1345: D=t.date()
            else:
                S0=t.date() if hm>1345 else t.date()-dt.timedelta(days=1)
                i=bisect.bisect_right(tdates,S0)
                if i>=len(tdates): continue
                D=tdates[i]
            key=(D,dt.time(13,45))
        b=bars.get(key[0])
        if b is None: bars[key[0]]=[h,l,c,key[1]]
        else:
            b[0]=max(b[0],h); b[1]=min(b[1],l); b[2]=c
            if key[1]: b[3]=key[1]
    out=[]
    for D,(h,l,c,ct) in sorted(bars.items()):
        ct=ct or dt.time(5,0)
        out.append((dt.datetime.combine(D,ct),h,l,c))
    return out
P=positions(load('v1918_desk.xlsx'))
be=[p for p in P if any('BreakExit' in x for x in p['xs'])]
def test(bars,N=4,shrink=0.6):
    st=[];cons=False;top=btm=0
    H=np.array([b[1] for b in bars]);L=np.array([b[2] for b in bars])
    for k in range(len(bars)):
        old=cons
        if k>=N:
            rh=H[k-N:k].max(); rl=L[k-N:k].min(); rr=rh-rl; cr=H[k]-L[k]
            if H[k]<=rh and L[k]>=rl and rr>0 and cr/rr<=shrink: cons=True; top,btm=rh,rl
        if cons and (H[k]>top or L[k]<btm): cons=False
        st.append((bars[k][0],old,cons))
    hit=0; miss=[]
    for p in be:
        ok=any(p['edt']<=t<=p['xdt'] and o and not n for t,o,n in st)
        hit+=ok
        if not ok: miss.append((p['edt'],p['xdt']))
    return hit,miss
for kind in ('1345','cal'):
    b=build(kind); h,m=test(b)
    print(kind,'bars',len(b),'BreakExit explained',h,'/',len(be)); print('  miss',m[:6])
pickle.dump({k:build(k) for k in ('1345','cal')},open('daily_variants.pkl','wb'))
