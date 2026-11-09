# v5.9 MC check (Willy 10/3 16:01): batch 0 (defaults = plan B) and batch 1 (Crash_On 1) vs replay and vs plan B report.
import sys, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
import l2_v56_mc_eval as E, l2_v57_replay as V
from l2_crash_on_b import run
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
B=load(U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx')
D=load(U+'a036799f-TXF1__L2_TrendShort_v5.9_________.xlsx'); C=load(U+'e235d8fe-TXF1__L2_TrendShort_v5.9__________Crash_On__1.xlsx')
print('batch 0 summary',E.mc(U+'a036799f-TXF1__L2_TrendShort_v5.9_________.xlsx'))
print('batch 0 vs plan B report trade-by-trade:', [(r['edt'],r['xdt'],r['pnl']) for r in D]==[(r['edt'],r['xdt'],r['pnl']) for r in B], len(D))
print('batch 1 summary',E.mc(U+'e235d8fe-TXF1__L2_TrendShort_v5.9__________Crash_On__1.xlsx'))
R=run(BP=1,BPATR=0.6,BPSLP=1.0)
me=[r['edt'] for r in C]; re_=[t[0] for t in R]
print('batch 1 vs replay entry times equal:',me==re_,len(me),len(re_))
if me!=re_:
    print('  only MC',sorted(set(me)-set(re_))[:8]); print('  only replay',sorted(set(re_)-set(me))[:8])
cr=[r for r in C if r['esig']=='CR_Entry']
print('crash trades MC:',[(f"{r['edt']:%Y/%m/%d %H:%M}",round(r['pnl']/20),r['xsig']) for r in cr])
rc=[(t[0],round(V.pnl(t))) for t in R if t[5]=='BP']; mc_=[(r['edt'],round(r['pnl']/20)) for r in cr]
print('crash pnl equal to replay:',rc==mc_)
print('exit labels of crash trades:',dict(collections.Counter(r['xsig'] for r in cr)))
for nm,T in (('plan B',B),('v5.9 Crash_On 1',C)):
    print('==',nm)
    for wn,a,b in E.W+[('2025/6/4 起',dt.datetime(2025,6,4),dt.datetime(2026,9,25))]:
        s=E.st(T,a,b); print(f'   {wn:14s} n {s["n"]:3d} net {s["net"]:7d} MDD {s["mdd"]:7d} streak {s["stk"]}({s["sn"]}) maxLosers {s["mcl"]}')
NOW=48091
def norm(T):
    U_=[dict(r) for r in T]
    for r in U_: r['pnl']=r['pnl']/r['epx']*NOW
    return U_
for nm,T in (('plan B',B),('v5.9',C)):
    s=E.st(norm(T),*E.W[0][1:]); print(f'  normalized@48,091 {nm}: MDD {s["mdd"]} ({-s["mdd"]/3000:.1f}%)')
