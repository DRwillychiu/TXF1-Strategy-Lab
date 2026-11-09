import sys, datetime as dt
sys.argv=['x','std']
exec(open('l1_replay_lib.py').read())
A=dt.datetime
def pnl(tr): return (tr[3]-tr[2]-SLIP)*20
def stats(T,a,b):
    Q=[t for t in T if a<=t[0]<b]; eq=pk=mdd=s=c=0;n=cn=0;mc=cc=0
    for t in Q:
        x=pnl(t); eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if x<0: c+=x;cn+=1; cc+=1; mc=max(mc,cc)
        else: c=0;cn=0;cc=0
        if c<s: s=c;n=cn
    return len(Q),round(eq),round(mdd),round(s),n,mc
S0=A(2024,3,1)
grid=[('base',{}),('SL_Pct 0.4',{'SLP':0.4}),('SL_Pct 0.3',{'SLP':0.3}),('SL_Pct 0.6',{'SLP':0.6}),('日線閘門',{'DT':1}),
('暫停 3/1',{'PN':3,'PK':1}),('暫停 3/2',{'PN':3,'PK':2}),('暫停 4/2',{'PN':4,'PK':2}),('暫停 5/2',{'PN':5,'PK':2}),
('閘門+3/1',{'DT':1,'PN':3,'PK':1}),('閘門+4/2',{'DT':1,'PN':4,'PK':2}),('閘門+5/2',{'DT':1,'PN':5,'PK':2}),
('0.4+閘門+3/1',{'SLP':0.4,'DT':1,'PN':3,'PK':1})]
print('設定 | 2024/3-2026/9: 筆,淨利,MDD,連虧金額,連虧筆(金額段),最長連虧筆 | 實盤期 6/17-9/24')
for nm,ov in grid:
    T=run(S0,ov)
    print(f"{nm:<14}", stats(T,S0,A(2026,9,25)), stats(T,A(2026,6,17),A(2026,9,25)), flush=True)
