import sys, datetime as dt, collections, openpyxl
sys.path.insert(0,'.'); sys.path.insert(0,'/home/claude/repo/tools')
from stopstruct import load, positions
import mc_report
A=dt.datetime
files=[('R0','/tmp/L4R0.xlsx')]+[(f'T{i}',f'/tmp/L4T{i}.xlsx') for i in range(1,7)]
def params(f):
    ws=openpyxl.load_workbook(f,read_only=True)['設定']; d={}
    for row in ws.iter_rows(values_only=True):
        r=[c for c in row if c is not None]
        if len(r)==2 and isinstance(r[0],str): d[r[0]]=r[1]
    return {k:d.get(k) for k in ('SL_Pct','Streak_Skip_N','Macro_Mode','TP1_Room_Pct','TP1_BE_On')}
def st(Q):
    Q=sorted(Q,key=lambda p:p['xdt'])
    eq=pk=mdd=s=c=0; n=cn=0
    for p in Q:
        eq+=p['pnl']; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if p['pnl']<0: c+=p['pnl']; cn+=1
        else: c=0; cn=0
        if c<s: s=c; n=cn
    w=[p['pnl'] for p in Q if p['pnl']>0]; l=[p['pnl'] for p in Q if p['pnl']<0]
    pay=(sum(w)/len(w))/(-sum(l)/len(l)) if w and l else 0
    return dict(n=len(Q),net=round(eq),mdd=round(mdd),stk=round(s),stkn=n,big=round(min([p['pnl'] for p in Q],default=0)),win=len(w)/max(1,len(Q)),pay=pay)
R={}
for name,f in files:
    r=mc_report.read(f); P=positions(load(f))
    R[name]=dict(p=params(f) if name!='R0' else {'SL_Pct':1.5,'Streak_Skip_N':0,'Macro_Mode':0,'TP1_Room_Pct':0,'TP1_BE_On':False},
        mc=r['summary'],rows=len(r['trades']),
        full=st(P),IS=st([p for p in P if A(2021,9,16)<=p['edt']<A(2026,6,17)]),OOS=st([p for p in P if A(2026,6,17)<=p['edt']<A(2026,9,18)]))
    y=collections.defaultdict(float)
    for p in P: y[p['xdt'].year]+=p['pnl']
    R[name]['yr']={k:round(v) for k,v in sorted(y.items())}
    tot=sum(p['pnl'] for p in P); top=sorted(P,key=lambda p:-p['pnl'])[:10]
    R[name]['top10']=sum(p['pnl'] for p in top)/tot if tot>0 else None
    ex=collections.Counter(x for p in P for x in p['xs']); R[name]['exits']=dict(ex)
import json
json.dump(R,open('/tmp/l4t.json','w'),default=str,ensure_ascii=False)
for k,v in R.items(): print(k,v['p'],v['mc'],v['rows']); print('  full',v['full']); print('  IS',v['IS']); print('  OOS',v['OOS']); print('  yr',v['yr'],'top10',v['top10']); print('  exits',v['exits'])
