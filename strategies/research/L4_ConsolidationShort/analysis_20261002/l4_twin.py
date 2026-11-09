import sys, datetime as dt
sys.path.insert(0,'.')
from stopstruct import load, positions
A=dt.datetime
def seg(P,a,b):
    Q=[p for p in P if a<=p['xdt']<b]; eq=pk=mdd=dd=s=c=0; n=cn=0
    for p in Q:
        dd=min(dd,eq+p.get('mae',0)-pk) if p.get('mae') is not None else dd
        eq+=p['pnl']; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if p['pnl']<0: c+=p['pnl']; cn+=1
        else: c=0; cn=0
        if c<s: s=c; n=cn
    return len(Q),round(eq),round(mdd),round(s),n
S=A(2019,1,1)
W=[('W3 至2023/12/31',S,A(2024,1,1)),('W2 至2024/12/31',S,A(2025,1,1)),('W1 至2025/12/31',S,A(2026,1,1)),('測試2024',A(2024,1,1),A(2025,1,1)),('測試2025',A(2025,1,1),A(2026,1,1)),('測試2026',A(2026,1,1),A(2026,9,25))]
P={n:sorted(positions(load(f'/tmp/L4{n}.xlsx')),key=lambda p:p['xdt']) for n in ('R0','T1','T3')}
print('mae sample',P['T1'][0].get('mae'))
print('| 區段 | R0 部位/淨利/MDD/連虧 | T1 部位/淨利/MDD/連虧 | T1 MDD Δ% | T1 連虧金額 Δ% | 判定 |')
for nm,a,b in W:
    r=seg(P['R0'],a,b); t=seg(P['T1'],a,b)
    dm=(abs(t[2])-abs(r[2]))/abs(r[2])*100 if r[2] else float('nan'); ds=(abs(t[3])-abs(r[3]))/abs(r[3])*100 if r[3] else float('nan')
    ok= abs(t[2])<=abs(r[2]) and abs(t[3])<=abs(r[3])
    print(f"| {nm} | {r[0]}/{r[1]:,}/{r[2]:,}/{r[3]:,}({r[4]}) | {t[0]}/{t[1]:,}/{t[2]:,}/{t[3]:,}({t[4]}) | {dm:+.1f}% | {ds:+.1f}% | {'✅' if ok else '❌'} |")
