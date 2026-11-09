import openpyxl, datetime as dt, collections, sys
sys.path.insert(0,'.')
from stopstruct import load
f='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/a1f27026-________260617_______.xlsx'
ws=openpyxl.load_workbook(f,read_only=True,data_only=True)['交易紀錄']
rows=[r for r in ws.iter_rows(values_only=True)][1:]
L=collections.OrderedDict()
for r in rows:
    if not r or r[0]!='實戰' or r[12]!='L1_趨勢多頭': continue
    k=r[2].replace(second=0)
    p=L.setdefault(k,dict(edt=r[2],xdt=r[3],epx=[],xpx=[],pts=0,amt=0,n=0))
    p['epx'].append(r[6]); p['xpx'].append(r[7]); p['pts']+=r[8]; p['amt']+=r[9]; p['n']+=r[5]; p['xdt']=max(p['xdt'],r[3])
LP=list(L.values())
B=[r for r in load('/tmp/L1_0.xlsx') if dt.datetime(2026,6,17)<=r['edt']<dt.datetime(2026,9,25)]
print('LIVE L1 positions',len(LP),'total',round(sum(p['amt'] for p in LP)))
eq=0;run=0;worst=0
for p in LP:
    eq+=p['amt']; run = run+p['amt'] if p['amt']<0 else 0; worst=min(worst,run)
    hrs=(p['xdt']-p['edt']).total_seconds()/3600
    print(f"  {p['edt']:%m/%d %H:%M} -> {p['xdt']:%m/%d %H:%M} {hrs:5.1f}h lots {p['n']} entry {sum(p['epx'])/len(p['epx']):.0f} pts {p['pts']:6} amt {p['amt']:8,} cum {eq:9,}")
print('worst losing run (amt)',worst)
print('BACKTEST L1_0 same window',len(B),'total',round(sum(r['pnl']/20 for r in B)))
for r in B: print(f"  {r['edt']:%m/%d %H:%M} -> {r['xdt']:%m/%d %H:%M} {r['esig']:<11}{r['xsig']:<14} {r['epx']} pnl {r['pnl']/20:8,.0f}")
