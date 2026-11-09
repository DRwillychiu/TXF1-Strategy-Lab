# End-state checks for the BP path before writing v5.6 (replay estimate, not MC):
# year concentration, MC-only forced exits (settlement / holiday), blocked entry bars, filter flips,
# stop-distance and gap ratio, leg-timeout frequency, overlap/hedge vs L1 V3.7 MC trades (L1_G4).
import datetime as dt, re, sys, collections
import l2_bp_leg as M
from l2_bp_leg import BE,O,H,L,C,ATR,FOK,HH,n
from l2_bp_tp import stats
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
src=open('/home/claude/repo/strategies/research/L2_TrendShort/L2_v5.5/L2_TrendShort_v5.5.pla').read()
HOL=set(int(x) for x in re.findall(r'Holiday_Tail\[\d+\]\s*=\s*(\d+);',src))
def mcdate(e): return (e.year-1900)*10000+e.month*100+e.day
def hol_bar(e): return mcdate(e) in HOL and e.hour*100+e.minute<=500
def settle_day(e): return e.weekday()==2 and 15<=e.day<=21
def sim(K=1,DD=3.0,LB=20,BODY=1.0,SLK=1.5,CAP=450,TRK=1.0,TMAX=40,LEGT=0,start=dt.datetime(2020,6,1),end=dt.datetime(2026,9,25),MCFLAT=False,MCBLOCK=False):
    out=[]; pos=None; pend=False; leg_hh=None; leg_n=0; leg_i=0
    def fin(i,px,why):
        p=2*((pos['ep']-px-10)*10); out.append(dict(ei=pos['ei'],xi=i,pnl=p,why=why,ep=pos['ep'],dist=pos['dist'],px=px))
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if leg_hh is not None and (H[i]>=leg_hh or (LEGT and i-leg_i>=LEGT)): leg_hh=None; leg_n=0
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP); pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i],dist=dist); pend=False
        elif pos is not None and pos.get('mkt'):
            fin(i,O[i],pos['mkt']); pos=None
        if pos is not None and H[i]>=pos['stop']:
            px=max(O[i],pos['stop']) if i>pos['ei'] else pos['stop']; fin(i,px,'STOP'); pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i]); pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            if MCFLAT and ((hol_bar(e) and e.hour*100+e.minute>=300) or (settle_day(e) and 1230<=e.hour*100+e.minute<=1345)): pos['mkt']='FLAT'
            continue
        if settle_day(e): continue
        if MCBLOCK and hol_bar(e): continue
        if (not FOK[i]) and (1-C[i]/HH(i,LB))*100>=DD and (O[i]-C[i])>=BODY*ATR[i]:
            if K and leg_hh is not None and leg_n>=K: continue
            if leg_hh is None: leg_hh=HH(i,LB); leg_i=i
            leg_n+=1; pend=True
    return out
def st(T,a,b): return stats([(BE[t['ei']],t['pnl']) for t in T],a,b)
W=M.W
if __name__=='__main__':
    base=sim(K=1)
    assert [round(t['pnl']) for t in base]==[round(p) for _,p in M.sim(K=1)], 'anchor mismatch vs l2_bp_leg'
    print('anchor OK: endcheck sim == l2_bp_leg K=1 trade for trade')
    for k in (0,1):
        T=sim(K=k); y=collections.defaultdict(float)
        for t in T: y[BE[t['ei']].year]+=t['pnl']
        print(f'K{k} by year:',{a:round(b) for a,b in sorted(y.items())})
    # 2 MC-only rules: forced flats + holiday entry block
    T=base
    hold=[t for t in T if any((hol_bar(BE[j]) and BE[j].hour*100+BE[j].minute>=300) or (settle_day(BE[j]) and BE[j].hour*100+BE[j].minute>=1230) for j in range(t['ei'],t['xi']+1))]
    print('K1 trades crossing MC forced-flat bars:',len(hold),[f"{BE[t['ei']]:%Y/%m/%d %H:%M}" for t in hold])
    mc=sim(K=1,MCFLAT=True,MCBLOCK=True)
    print('K1 with MC forced flats + holiday entry block | '+' | '.join(M.fmt(st(mc,a,b)) for _,a,b in W))
    flip=[t for t in T if any(FOK[j] for j in range(t['ei'],t['xi']+1))]
    print('K1 trades where weekly FilterOK turns on while open:',len(flip),[f"{BE[t['ei']]:%Y/%m/%d}" for t in flip])
    # stop distance, gap ratio
    print('max planned dist pts',round(max(t['dist'] for t in T)),'| stop exits realized/planned >120%:',
          [(f"{BE[t['ei']]:%Y/%m/%d}",round((t['px']-t['ep'])/t['dist']*100)) for t in T if t['why']=='STOP' and t['px']-t['ep']>1.2*t['dist']])
    print('exit types K1:',collections.Counter(t['why'] for t in T),' bars held median',sorted(t['xi']-t['ei'] for t in T)[len(T)//2])
    # leg timeout
    for lt in (0,200,400,800):
        print(f'K1 leg timeout {lt:3d} | '+' | '.join(M.fmt(st(sim(K=1,LEGT=lt),a,b)) for _,a,b in W))
    # L1 V3.7 overlap / portfolio
    from stopstruct import load
    L1=load('/tmp/L1_G4.xlsx')
    for r in L1: r['m']=r['pnl']/20
    def l1_open(t0,t1): return [r for r in L1 if r['edt']<t1 and r['xdt']>t0]
    a2,b2=W[2][1],W[2][2]
    rows=[]
    for t in T:
        t0=BE[t['ei']-1]; t1=BE[t['xi']]
        if t0<a2: continue
        ov=l1_open(t0,t1); rows.append((t0,round(t['pnl']),len(ov),round(sum(r['m'] for r in ov))))
    print('recent-2y BP K1 vs L1 V3.7 open at the same time: (BP entry, BP pnl, #L1 trades overlapping, their L1 pnl)')
    for r in rows: print('  ',f'{r[0]:%Y/%m/%d %H:%M}',r[1:])
    def eq_mdd(ev):
        ev.sort(); eq=pk=m=0
        for _,x in ev: eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        return round(eq),round(m)
    l1ev=[(r['xdt'],r['m']) for r in L1 if a2<=r['edt']<b2]
    bpev=[(BE[t['xi']],t['pnl']) for t in T if a2<=BE[t['ei']]<b2]
    print('recent-2y closed-trade net/MDD  L1 alone',eq_mdd(list(l1ev)),' L1+BP',eq_mdd(l1ev+bpev))
    # worst L1 drawdown windows: what did BP do inside them
    ev=sorted(l1ev); eq=pk=0; pkt=None; worst=None
    for x_t,x in ev:
        eq+=x
        if eq>=pk: pk=eq; pkt=x_t
        elif worst is None or eq-pk<worst[0]: worst=(eq-pk,pkt,x_t)
    print('L1 recent-2y MDD window',worst[1],'->',worst[2],round(worst[0]),'| BP pnl closed inside:',round(sum(p for x_t,p in bpev if worst[1]<x_t<=worst[2])))
