# Willy 10/3 14:39: BP = filter unchanged; when filter is OFF and volatility qualifies, trade a disciplined stop for profit.
# Grid: BP ATR% gate x BP stop (ATR multiple, cap 450). Base v5.6. Pass marks vs v5.6 (full MDD -7,386 / streak -4,880; recent -7,386 / -4,619). Replay estimate.
import datetime as dt
import l2_v57_research as X, l2_v57_replay as V
B=dict(fm=-7386,fs=-4880,rm=-7386,rs=-4619,pm=-24920)
rows=[]
for atr in (0.55,0.6,0.65,0.7):
    for sl in (0.75,1.0,1.25,1.5):
        T=X.run(BP=1,BPATR=atr,BPSL=sl)
        s=[X.st(T,a,b) for _,a,b in X.W]; bp=[t for t in T if t[5]=='BP']; x=[V.pnl(t) for t in bp]
        ex26=sum(V.pnl(t) for t in bp if t[0].year!=2026); top=max(x) if x else 0; worst=min(x) if x else 0
        p2=X.port(T,*X.W[3][1:])
        L1=s[0]['mdd']>=B['fm'] and s[0]['stk']>=B['fs'] and s[3]['mdd']>=B['rm'] and s[3]['stk']>=B['rs'] and all(s[k]['mdd']>=m for k,m in ((1,-3762),(2,-5879)))
        L3=ex26>=0 and sum(x)-top>0
        print(f"ATR%>={atr} SL {sl:4} | L2 全期 net {s[0]['net']} MDD {s[0]['mdd']} stk {s[0]['stk']}({s[0]['sn']}) | 近兩年 net {s[3]['net']} MDD {s[3]['mdd']} stk {s[3]['stk']} | 20-22 {s[1]['mdd']} 22-24 {s[2]['mdd']} | BP n {len(bp)} net {round(sum(x))} worst {round(worst)} ex26 {round(ex26)} -top {round(sum(x)-top)} | port2y {p2} | L1 {'PASS' if L1 else 'fail'} L2 {'PASS' if p2>=B['pm'] else 'fail'} L3 {'PASS' if L3 else 'fail'}")
