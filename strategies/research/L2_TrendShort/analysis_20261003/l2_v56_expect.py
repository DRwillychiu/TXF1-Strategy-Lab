# Expected MC values for the v5.6 batch (replay estimate; replay v5.3 = 78 trades / 144,406 micro vs MC 144,120).
# Also counts how often the v5.3 trailing stop (Active_TSL) sits ABOVE the initial trigger SL_Trig (stop loosening).
import datetime as dt
import l2_replay_pause as R
W=[('全期 2020/1-26/9',dt.datetime(2020,1,1),dt.datetime(2026,9,25)),('2020/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('2022/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('近兩年',dt.datetime(2024,10,1),dt.datetime(2026,9,25))]
def st(T,a,b):
    T=[t for t in T if a<=t[0]<b]; eq=pk=m=0; c=s=0; cn=sn=0
    for t in T:
        x=R.pnl(t); eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return len(T),round(eq),round(m),round(s),sn
if __name__=='__main__':
    rows=[]
    for slm in (0,450):
        for pn in range(0,6):
            T=R.run(OV=dict(SLMAX=slm),start=dt.datetime(2020,1,1),PN=pn,PK=-1 if pn else 0)
            rows.append((slm,pn,[st(T,a,b) for _,a,b in W],T))
    for slm,pn,s,T in rows:
        f=s[0]
        print(f"#25 {slm:3d} #26 {pn} | 全期 n {f[0]} net {f[1]} (MC {f[1]*20:,}) MDD {f[2]} (MC {f[2]*20:,}) stk {f[3]}({f[4]}) | "+" | ".join(f"{W[k][0]} n {x[0]} net {x[1]} MDD {x[2]} stk {x[3]}({x[4]})" for k,x in enumerate(s[1:],1)))
    base=[t for t in rows[0][3]]; p2=set(t[0] for t in rows[2][3]); p3=set(t[0] for t in rows[3][3])
    print('removed by N=3:',[f'{t[0]:%Y/%m/%d %H:%M} {round(R.pnl(t))}' for t in base if t[0] not in p3])
    print('added by N=3:',[f'{t[0]:%Y/%m/%d %H:%M} {round(R.pnl(t))}' for t in rows[3][3] if t[0] not in set(x[0] for x in base)])
    print('removed by N=2:',len([t for t in base if t[0] not in p2]),'added:',len([t for t in rows[2][3] if t[0] not in set(x[0] for x in base)]))

