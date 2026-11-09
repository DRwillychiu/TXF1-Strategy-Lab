exec(open('l5/budget.py').read().split("IS=[p for p in P if p['edt']<LIVE]")[0])
import statistics as st
IS=[p for p in P if p['edt']<LIVE]; OOS=[p for p in P if p['edt']>=LIVE]
print('2026 planned loss (stop x2 lots, micro): >3%%: %d, >5%%: %d of %d, max %d'%(sum(p['stopd']*20>9000 for p in P if p['edt'].year==2026),sum(p['stopd']*20>15000 for p in P if p['edt'].year==2026),sum(1 for p in P if p['edt'].year==2026),max(p['stopd']*20 for p in P if p['edt'].year==2026)))
print('winners 2026 exits:',collections.Counter(p['xs'][-1].rsplit('_',1)[0] for p in P if p['edt'].year==2026 and p['pnl']>0))
W26=[p for p in P if p['edt'].year==2026 and p['pnl']>0]
print('2026 winners: realized/MFE = %.0f%%; winners with MFE>=1%% but realized<0.5%%: %d'%(100*sum(p['pnl']/20 for p in W26)/sum(p['mfep'] for p in W26),sum(1 for p in W26 if p['mfep']/p['epx']>=0.01 and p['pnl']/20/p['epx']<0.005)))
def st3(key):
    out=[]
    for X in (IS,OOS):
        eq=pk=mdd=r=w=0;m1=0
        for p in sorted(X,key=lambda p:p['xdt']):
            v=p[key];eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk);r=r+v if v<0 else 0;w=min(w,r);m1=min(m1,v)
        out.append('%7d %7d %7d max1 %7d'%(eq,mdd,w,m1))
    return ' | '.join(out)
print('cap planned risk (tighter stop only when ATR stop exceeds cap)   IS net/MDD/streak/max1 | OOS')
for pct in [3,4,5,6]:
    B=3000*pct
    for p in P: p['hc']=capped(p,B/20) if p['stopd']*20>B else p['pnl']
    print('cap %d%% (%4d pts)  %s  | affected %d'%(pct,B/20,st3('hc'),sum(1 for p in P if p['stopd']*20>B)))
# LM variants with release
def lm(seq,thr=9000,alpha=0.5,release_days=None,mid_only=False):
    eq=pk=mdd=r=w=0;m1=0;Lref=None;tgt=None;since=None;out=0;outwin=0;last_trade=None;maxgap=0
    for p in seq:
        planned=p['stopd']*20
        if Lref is not None and release_days is not None and since is not None and (p['edt']-since).days>release_days*7/5: Lref=None
        if Lref is not None and planned>alpha*Lref and (not mid_only or p['esig']=='Mid'):
            out+=1; outwin+=p['pnl']>0; continue
        if last_trade: maxgap=max(maxgap,(p['edt']-last_trade).days)
        last_trade=p['edt']
        v=p['pnl'];eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk);r=r+v if v<0 else 0;w=min(w,r);m1=min(m1,v)
        if v<=-thr: Lref=-v;tgt=eq-v;since=p['xdt']
        elif Lref is not None and eq>=tgt: Lref=None
    return eq,mdd,w,m1,out,outwin,maxgap
print('loss memory variants (thr 9000, alpha 0.5):  IS net/MDD/streak/max1/blocked/blocked-winners/longest-no-trade-days | OOS')
for lab,kw in [('none',dict(thr=10**9)),('block until recovered',{}),('block, release after 10 trading days',dict(release_days=10)),('block, release after 20 trading days',dict(release_days=20)),('Mid only blocked',dict(mid_only=True)),('Mid only, release 10d',dict(mid_only=True,release_days=10))]:
    a=lm(IS,**kw); c=lm(OOS,**kw)
    print('%-38s IS %7d %7d %7d %7d out %2d(win %2d) gap %3dd | OOS %7d %7d %7d %7d out %2d(win %2d) gap %3dd'%(lab,*a,*c))
print('Mid-only loss memory grid: IS net/MDD | OOS net/MDD/streak')
for thr in [6000,9000,12000]:
    row=[]
    for a in [0.4,0.5,0.6,0.7,0.8,1.0]:
        x=lm(IS,thr=thr,alpha=a,mid_only=True); y=lm(OOS,thr=thr,alpha=a,mid_only=True)
        row.append('a%.1f %5d/%6d | %5d/%6d/%6d'%(a,x[0],x[1],y[0],y[1],y[2]))
    print('thr',thr); [print('   ',r) for r in row]
