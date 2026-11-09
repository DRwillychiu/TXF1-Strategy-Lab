# L1-L5 final portfolio (MC Portfolio Trader, Willy 10/3 19:52): uniform metrics per year / per strategy.
# Units: micro NTD (MC / 20); account 300,000. Partial exits merged into one position.
import sys, json, datetime as dt, collections, openpyxl
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
FULL=U+'d31a04b0-____________.xlsx'
ACC=300_000
def strat(mkt,esig):
    if '45' in mkt: return 'L1'
    if '60' in mkt: return 'L2'
    return {'CL':'L3','CS':'L4','BL':'L5'}[esig.split('_')[0]]
def load_pf(path):
    ws=openpyxl.load_workbook(path,read_only=True,data_only=True)['交易明細']
    tr=[];cur=None
    for r in list(ws.iter_rows(values_only=True))[3:]:
        if r[3] is None: continue
        d=dt.datetime.combine(r[5].date(), r[6] if isinstance(r[6],dt.time) else dt.time(0,0))
        if '進入' in r[3]: cur=dict(s=strat(r[1],r[4]),esig=r[4],edt=d,epx=r[7],qty=r[8],pnl=r[9],mae=r[15])
        elif '離開' in r[3] and cur: cur.update(xsig=r[4],xdt=d,xpx=r[7]); tr.append(cur); cur=None
    return tr
def positions(tr):
    g=collections.OrderedDict()
    for t in tr: g.setdefault((t['s'],t['edt'],t['epx'],t['esig']),[]).append(t)
    return [dict(s=k[0],edt=k[1],esig=k[3],pnl=sum(x['pnl'] for x in v)/20,xdt=max(x['xdt'] for x in v),rows=len(v)) for k,v in g.items()]
def metrics(P):
    P=sorted(P,key=lambda p:p['xdt']); eq=pk=mdd=0; pkd=tr=None
    s=c=0; sn=cn=0; mcl=0; worst=0
    for p in P:
        x=p['pnl']; eq+=x
        if eq>pk: pk=eq; pkd=p['xdt']
        if eq-pk<mdd: mdd=eq-pk; tr=(pkd,p['xdt'])
        if x<0: c+=x; cn+=1; s=min(s,c); mcl=max(mcl,cn)
        else: c=0; cn=0
        worst=min(worst,x)
    w=[p['pnl'] for p in P if p['pnl']>0]; l=[p['pnl'] for p in P if p['pnl']<=0]
    return dict(n=len(P),net=round(eq),win=round(100*len(w)/len(P),1) if P else 0,
                pf=round(sum(w)/-sum(l),2) if l and sum(l)<0 else None,mdd=round(mdd),mdd_pct=round(100*mdd/ACC,1),
                dd_from=str(tr[0])[:10] if tr and tr[0] else None,dd_to=str(tr[1])[:10] if tr else None,
                streak=round(s),mcl=mcl,worst=round(worst))
if __name__=='__main__':
    T=load_pf(FULL); P=positions(T)
    print('rows',len(T),'positions',len(P),'MC net check',sum(t['pnl'] for t in T))
    out={'full':{},'year':{}}
    for k in ['ALL','L1','L2','L3','L4','L5']:
        Q=P if k=='ALL' else [p for p in P if p['s']==k]
        out['full'][k]=metrics(Q); out['full'][k]['rows']=sum(1 for t in T if k=='ALL' or t['s']==k)
        out['full'][k]['first']=str(min(p['edt'] for p in Q))[:16]
    for y in range(2018,2027):
        out['year'][y]={}
        for k in ['ALL','L1','L2','L3','L4','L5']:
            Q=[p for p in P if p['xdt'].year==y and (k=='ALL' or p['s']==k)]
            out['year'][y][k]=metrics(Q) if Q else None
    json.dump(out,open('/tmp/claude-0/pf_eval.json','w'),ensure_ascii=False,indent=1,default=str)
    for k,v in out['full'].items(): print(k,v)
    for y,v in out['year'].items(): print(y,{k:(m['net'],m['n'],m['mdd'],m['streak'],m['mcl']) if m else None for k,m in v.items()})
