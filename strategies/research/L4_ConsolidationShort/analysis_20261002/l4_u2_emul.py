# U2 emulation (estimate): TP1 limit fills only if price trades THROUGH the limit by >= 1 pt (1-min data),
# checked from the TP1 bar until the other lot exits; otherwise the TP1 lot exits with the other lot.
import sys, datetime as dt, bisect, collections
sys.path.insert(0,'.')
from stopstruct import load
F='/mnt/user-data/uploads/TXF1_1_分鐘.txt'
f=sys.argv[1] if len(sys.argv)>1 else '/tmp/L4T8.xlsx'
tr=load(f)
pos=collections.defaultdict(list)
for r in tr: pos[(r['edt'],r['epx'])].append(r)
need=[]
for k,rs in pos.items():
    t=[r for r in rs if r['xsig']=='CS_TP1']
    if t: need.append((k,t[0],[r for r in rs if r['xsig']!='CS_TP1'][0]))
lo_t=min(t['xdt'] for _,t,_ in need)-dt.timedelta(minutes=20); hi_t=max(o['xdt'] for _,_,o in need)
T=[];L=[]
with open(F) as fh:
    next(fh)
    for line in fh:
        p=line.split(',')
        y,m,d=map(int,p[0].split('/')); hh=int(p[1][0:2]); mm=int(p[1][3:5])
        ts=dt.datetime(y,m,d,hh,mm)
        if ts<lo_t or ts>hi_t: continue
        T.append(ts); L.append(float(p[4]))
def minlow(a,b):  # 1-min bars with stamp in (a,b]
    i=bisect.bisect_right(T,a); j=bisect.bisect_right(T,b)
    return min(L[i:j]) if j>i else None
touch=0; lost=0; delta=0; rows=[]
adj={}
for k,t,o in need:
    lim=t['xpx']; a=t['xdt']-dt.timedelta(minutes=15)
    ml=minlow(a,t['xdt'])
    if ml is None: print('no data',t['xdt']); continue
    if ml<=lim-1: continue
    touch+=1
    ml2=minlow(t['xdt'],o['xdt'])
    if ml2 is not None and ml2<=lim-1: continue   # fills later at same limit
    lost+=1; d=o['pnl']-t['pnl']; delta+=d; adj[id(t)]=o['pnl']
    rows.append((t['xdt'].strftime('%Y/%m/%d %H:%M'),lim,ml,round(t['pnl']),round(o['pnl']),round(d)))
print('positions with TP1',len(need),'touch-only at TP1 bar',touch,'never filled through',lost,'net delta MC',round(delta))
for r in rows: print('  ',r)
# rebuild equity: base vs conservative (position level, closed); intraday approx via row MAE
def run(cons):
    P=[]
    for k,rs in pos.items():
        pnl=0; mae=0
        tp=[r for r in rs if r['xsig']=='CS_TP1']; ot=[r for r in rs if r['xsig']!='CS_TP1']
        for r in rs:
            if cons and id(r) in adj: pnl+=adj[id(r)]; mae+=ot[0]['mae']
            else: pnl+=r['pnl']; mae+=r['mae']
        P.append((max(r['xdt'] for r in rs),pnl,mae))
    P.sort(); eq=pk=mdd=idd=0
    for x,p,m in P:
        idd=min(idd,eq+m-pk); eq+=p; pk=max(pk,eq); mdd=min(mdd,eq-pk)
    return round(eq),round(mdd),round(idd)
b=run(False); c=run(True)
print('base   net/closedMDD/intraday(approx)',b)
print('cons   net/closedMDD/intraday(approx)',c)
