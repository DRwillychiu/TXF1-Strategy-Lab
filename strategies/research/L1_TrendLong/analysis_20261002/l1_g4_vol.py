# G4 (gate + slope 4 + loss pause 3/1, engine stop always on) replay: stop-width variants, recent 2y. Estimate, NOT MC.
import sys, datetime as dt, itertools
sys.argv=['x']
import l1_replay_lib as R
S=dt.datetime(2024,10,1)
def pnl(t): return (t[3]-t[2]-R.SLIP)*20
def stats(T):
    T=[t for t in T if t[0]>=S]; T.sort(key=lambda t:t[1]); eq=pk=mdd=0; c=s=0; n=cn=0; mc=0
    for t in T:
        x=pnl(t); eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; n=cn
        mc=max(mc,cn)
    return len(T),round(eq),round(mdd),round(s),n,mc
if __name__=='__main__':
    G4=dict(DT=1,DSL=4,PN=3,PK=1)
    print('V3.2 replay  ',stats(R.run(dt.datetime(2024,3,1),{})))
    print('G4 replay    ',stats(R.run(dt.datetime(2024,3,1),G4)))
    for slp,dcm,slm in itertools.product((0.5,0.6,0.7,0.8),(0.5,0.7,1.0),(1.5,2.0)):
        ov=dict(G4,SLP=slp,DCM=dcm,SLM=slm)
        print(f'SLP {slp} DCM {dcm} SLM {slm}',stats(R.run(dt.datetime(2024,3,1),ov)))
