import sys, datetime as dt, openpyxl, json
sys.path.insert(0,'.')
from stopstruct import load, positions
A=dt.datetime
names=['R0']+[f'T{i}' for i in range(1,7)]
def grab(f):
    wb=openpyxl.load_workbook(f,read_only=True); out={}
    for sh in ('策略分析','交易分析'):
        for row in wb[sh].iter_rows(values_only=True):
            r=[c for c in row if c is not None]
            if len(r)>=2 and isinstance(r[0],str) and any(k in r[0] for k in ('連續','最大策略虧損','最大平倉交易虧損','交易總次數','%勝率','獲利因子')) and r[0] not in out:
                out[r[0]]=r[1]
    return out
for n in names:
    f=f'/tmp/L4{n}.xlsx'; g=grab(f)
    P=sorted(positions(load(f)),key=lambda p:p['xdt'])
    eq=pk=0; pkd=P[0]['xdt']; mdd=0; md=None; uw=0; uws=None
    for p in P:
        eq+=p['pnl']
        if eq>=pk: 
            if uws: uw=max(uw,(p['xdt']-uws).days)
            pk=eq; pkd=p['xdt']; uws=None
        else:
            if uws is None: uws=pkd
            if eq-pk<mdd: mdd=eq-pk; md=(pkd.date(),p['xdt'].date())
    if uws: uw=max(uw,(A(2026,9,24)-uws).days)
    crash=sum(p['pnl'] for p in P if A(2025,4,1)<=p['xdt']<A(2025,4,12))
    oos=[(p['edt'].strftime('%m/%d %H:%M'),p['xdt'].strftime('%m/%d'),round(p['pnl']),p['xs']) for p in P if p['edt']>=A(2026,6,17)]
    print(n,{k:g[k] for k in g if '連續' in k or '最大' in k},'\n   MDD',mdd,md,'UW',uw,'crash0401-11',round(crash),'\n   OOS',oos)
