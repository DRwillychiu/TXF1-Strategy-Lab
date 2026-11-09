# Why A4 profit-lock exits differ from G4: implied peak vs 45M high / open / close (1-min rebuilt 45M bars)
import sys, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
A=stopstruct.load('/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/820f30b4-TXF1__L1_TrendLong_v3.8_________.xlsx'); G=stopstruct.load('/tmp/L1_G4.xlsx')
ga={(t['edt'],t['epx']):t for t in G}
pairs=[(t,ga[(t['edt'],t['epx'])]) for t in A if (t['edt'],t['epx']) in ga and t['xsig']=='TL_SP' and ga[(t['edt'],t['epx'])]['xsig']=='TL_SP' and t['xdt']==ga[(t['edt'],t['epx'])]['xdt'] and t['xpx']!=ga[(t['edt'],t['epx'])]['xpx']]
need=set()
for a,g in pairs:
    d=a['edt'].date()-dt.timedelta(days=1)
    while d<=a['xdt'].date(): need.add(d); d+=dt.timedelta(days=1)
def bar_end(t):
    hm=t.hour*100+t.minute
    if 846<=hm<=1345:
        base=t.replace(hour=8,minute=45); k=(int((t-base).total_seconds()//60)-1)//45
        return min(base+dt.timedelta(minutes=45*(k+1)),t.replace(hour=13,minute=45))
    if hm>=1501: base=t.replace(hour=15,minute=0)
    elif hm<=500: base=(t-dt.timedelta(days=1)).replace(hour=15,minute=0)
    else: return None
    k=(int((t-base).total_seconds()//60)-1)//45
    return min(base+dt.timedelta(minutes=45*(k+1)),(base+dt.timedelta(days=1)).replace(hour=5,minute=0))
B=collections.OrderedDict()
with open('/mnt/user-data/uploads/TXF1_1_分鐘_2.txt') as fh:
    next(fh)
    for line in fh:
        p=line.split(','); y,m,d=map(int,p[0].split('/'))
        if dt.date(y,m,d) not in need: continue
        t=dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5])); e=bar_end(t)
        if e is None: continue
        o,h,l,c=map(float,p[2:6])
        if e not in B: B[e]=[o,h,l,c]
        else: b=B[e]; b[1]=max(b[1],h); b[2]=min(b[2],l); b[3]=c
res=collections.Counter(); rows=[]
for a,g in pairs:
    ks=[k for k in B if a['edt']<=k<a['xdt']]   # bars from entry bar to bar before exit
    if not ks: continue
    ep=a['epx']
    hi=max(B[k][1] for k in ks)-ep; oc=max(max(B[k][0],B[k][3]) for k in ks)-ep; cl=max(B[k][3] for k in ks)-ep
    ia=(a['xpx']-ep)/0.45; ig=(g['xpx']-ep)/0.45
    near=lambda x,y: abs(x-y)<=3
    res[('G4~high',near(ig,hi))]+=1; res[('A4~close',near(ia,cl))]+=1; res[('A4~open/close',near(ia,oc))]+=1
    rows.append((str(a['edt']),round(ig,1),hi,round(ia,1),cl,oc))
print(len(pairs),dict(res)); print(rows[:8])
