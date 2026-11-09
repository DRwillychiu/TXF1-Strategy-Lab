# Willy 10/3 14:43: disciplined stop in % instead of ATR; ATR lags in volatility spikes. BP all-% variants on v5.6. Replay estimate.
import datetime as dt, numpy as np
import l2_v57_research as X, l2_v57_replay as V
from l2_funnel import BE, O, C, ATR
NOW=48091
B=dict(fm=-7386,fs=-4880,rm=-7386,rs=-4619,pm=-24920)
def norm_mdd(T):
    T=sorted(T,key=lambda t:t[2]); eq=pk=m=0
    for t in T: x=V.pnl(t)/t[1]*NOW; eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
    return round(m)
def line(nm,T):
    s=[X.st(T,a,b) for _,a,b in X.W]; bp=[t for t in T if t[5]=='BP']; x=[V.pnl(t) for t in bp]
    ex26=sum(V.pnl(t) for t in bp if t[0].year!=2026); top=max(x) if x else 0; worst=min(x) if x else 0
    p2=X.port(T,*X.W[3][1:])
    L1=s[0]['mdd']>=B['fm'] and s[0]['stk']>=B['fs'] and s[3]['mdd']>=B['rm'] and s[3]['stk']>=B['rs'] and s[1]['mdd']>=-3762 and s[2]['mdd']>=-5879
    L3=bool(x) and ex26>=0 and sum(x)-top>0
    print(f"{nm:30s} | 全期 net {s[0]['net']} MDD {s[0]['mdd']} stk {s[0]['stk']} | 2y net {s[3]['net']} MDD {s[3]['mdd']} stk {s[3]['stk']} | 22-24 {s[2]['mdd']} | BP n {len(bp)} net {round(sum(x))} worst {round(worst)} ex26 {round(ex26)} -top {round(sum(x)-top)} | norm MDD {norm_mdd(T)} | port2y {p2} | {'L1 ok' if L1 else 'L1 x'} {'L2 ok' if p2>=B['pm'] else 'L2 x'} {'L3 ok' if L3 else 'L3 x'}")
    return L1 and p2>=B['pm'] and L3
if __name__=='__main__':
    # how far ATR lags at BP signals: ATR(21) at the signal bar vs the true range realised over the next 5 bars
    T=X.run(BP=1,BPATR=0.6); idx={e:i for i,e in enumerate(BE)}
    print('reference ATR version:'); line('BP ATR%>=0.6 SL 1.5ATR trail 1ATR',T)
    print('-- %-stop, ATR trail, ATR% gate 0.6')
    for sp in (0.75,1.0,1.25,1.5): line(f'stop {sp}% trail 1ATR gate ATR0.6',X.run(BP=1,BPATR=0.6,BPSLP=sp))
    print('-- all-%: body gate % of price (no ATR anywhere), stop %, trail %')
    ok=[]
    for bd in (0.5,0.7,0.9):
        for sp in (0.75,1.0,1.25):
            for tp in (0.5,0.75,1.0):
                if line(f'body>={bd}% stop {sp}% trail {tp}%',X.run(BP=1,BPBODYP=bd,BPSLP=sp,BPTRP=tp)): ok.append((bd,sp,tp))
    print('pass all three layers:',ok)
