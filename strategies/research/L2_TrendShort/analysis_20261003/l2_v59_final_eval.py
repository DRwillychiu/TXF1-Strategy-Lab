# v5.9 final crash set full report check (Willy 10/3 16:44). MC big units (2 lots); micro = /20.
# Checks: settings, summary, windows (closed MDD; acceptance recent-2y MDD not worse than plan B -6,380),
# trades since 2025/6/4, top-10 winners, largest single win removed, max loss points, crash trades and exits.
import sys, datetime as dt, collections, openpyxl
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
import l2_v56_mc_eval as E
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
FB=U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx'
FC=U+'e235d8fe-TXF1__L2_TrendShort_v5.9__________Crash_On__1.xlsx'
FF=sys.argv[1] if len(sys.argv)>1 else U+'a9d3b5a2-TXF1__L2_TrendShort_v5.9_________F.xlsx'
B,C,F=load(FB),load(FC),load(FF)
W=E.W+[('2025/6/4 起',dt.datetime(2025,6,4),dt.datetime(2026,9,25))]
print('final MC summary',E.mc(FF))
for nm,T in (('plan B (v5.8)',B),('v5.9 Crash_On 1 default',C),('v5.9 final set',F)):
    print('==',nm)
    for wn,a,b in W:
        s=E.st(T,a,b); print(f'   {wn:12s} n {s["n"]:3d} net {s["net"]:7d} MDD {s["mdd"]:7d} streak {s["stk"]}({s["sn"]}) maxLosers {s["mcl"]}')
cr=[r for r in F if r['esig']=='CR_Entry']
print('crash trades:',len(cr),'net micro',round(sum(r['pnl'] for r in cr)/20))
for r in cr:
    print(f"   {r['edt']:%Y/%m/%d %H:%M} ep {r['epx']} -> {r['xdt']:%Y/%m/%d %H:%M} xp {r['xpx']} {r['xsig']:10s} pts {r['epx']-r['xpx']:6.0f} micro {round(r['pnl']/20):7d} MFE {round((r['mfe'] or 0)/20)} MAE {round((r['mae'] or 0)/20)}")
print('crash exit labels',dict(collections.Counter(r['xsig'] for r in cr)))
# trades are 2 lots per entry? check grouping by entry
g=collections.Counter((r['edt'],r['esig']) for r in F); print('rows per entry',collections.Counter(g.values()))
top=sorted(F,key=lambda r:-r['pnl'])[:10]
print('top-10 winners (micro):',[(f"{r['edt']:%Y/%m/%d}",r['esig'],round(r['pnl']/20)) for r in top])
tc=sorted(C,key=lambda r:-r['pnl'])[:10]
print('top-10 winners Crash_On 1 default:',[(f"{r['edt']:%Y/%m/%d}",r['esig'],round(r['pnl']/20)) for r in tc])
big=top[0]; R=[r for r in F if r is not big]
s=E.st(R,*W[0][1:]); s2=E.st(R,*W[3][1:])
print('without largest trade: full net',s['net'],'MDD',s['mdd'],'| recent2y net',s2['net'],'MDD',s2['mdd'],'| crash net without it',round(sum(r['pnl'] for r in cr if r is not big)/20))
crw=sorted(cr,key=lambda r:-r['pnl'])
print('crash net without its largest trade',round(sum(r['pnl'] for r in crw[1:])/20),'largest crash',round(crw[0]['pnl']/20))
# max loss in points per entry (2 lots)
lp=sorted([(r['xpx']-r['epx'],f"{r['edt']:%Y/%m/%d %H:%M}",r['esig'],r['xsig']) for r in F],reverse=True)[:6]
print('largest losses in points (short: xpx-epx):',lp)
print('largest loss micro',round(min(r['pnl'] for r in F)/20))
# compare entries vs plan B
be=set(r['edt'] for r in B); fe=set(r['edt'] for r in F)
print('bear trades lost vs plan B:',sorted(f"{x:%Y/%m/%d %H:%M}" for x in be-fe),'| new non-crash entries:',sorted(f"{r['edt']:%Y/%m/%d %H:%M}" for r in F if r['edt'] not in be and r['esig']!='CR_Entry'))
print('yearly final',E.yr(F)); print('yearly B    ',E.yr(B))
