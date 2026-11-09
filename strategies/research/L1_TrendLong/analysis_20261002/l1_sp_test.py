import sys, datetime as dt
sys.argv=['x','std']
exec(open('l1_replay_lib.py').read())
A=dt.datetime
def pnl(tr): return (tr[3]-tr[2]-SLIP)*20
def stats(T,a,b):
    Q=[t for t in T if a<=t[0]<b]; eq=pk=mdd=s=c=0;n=cn=0
    for t in Q:
        x=pnl(t); eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if x<0: c+=x;cn+=1
        else: c=0;cn=0
        if c<s: s=c;n=cn
    w=sum(pnl(t)>0 for t in Q)
    return len(Q),round(eq),round(mdd),round(s),n,round(w/max(1,len(Q))*100)
base=run(A(2024,9,2),{})
print('check 2026 windows', stats(base,A(2026,6,17),A(2026,7,25)), stats(base,A(2026,7,25),A(2026,9,11)))
print('variant | 2025-01..2026-09-24 (n,net,MDD,streak,cnt,win%) | 2026 only | live 6/17-9/24')
for nm,ov in [('base SP200/55',{}),('SP300',{'SPP':300}),('SP400',{'SPP':400}),('SP500',{'SPP':500}),('SP off',{'SPP':10**9}),('SP200 giveback70',{'SPR':70}),('SP300 giveback70',{'SPP':300,'SPR':70}),('SP 0.6%≈',{'SPP':275})]:
    T=run(A(2024,9,2),ov)
    print(f"{nm:<18}", stats(T,A(2025,1,1),A(2026,9,25)), stats(T,A(2026,1,1),A(2026,9,25)), stats(T,A(2026,6,17),A(2026,9,25)))
