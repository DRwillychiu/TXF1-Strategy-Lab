# Evaluate the crash grid: pass = recent-2y closed MDD >= plan B (-6,365 replay); robustness = crash ex-2026 >= 0 and crash minus top > 0; plateau = share of 1-step neighbours that pass.
import json, collections, itertools
R=json.load(open('/tmp/claude-0/l2_crash_grid.json')); B=-6365
V=[(0.5,0.55,0.6,0.65,0.7),(2.5,3.0,3.5,4.0),(15,20,25,30),(0.8,1.0,1.2),(0.75,1.0,1.25)]
idx={tuple(r['p']):r for r in R}
ok=lambda r: r['rmdd']>=B
robust=lambda r: ok(r) and r['ex26']>=0 and r['mtop']>0
def neigh(p):
    out=[]
    for k in range(5):
        i=V[k].index(p[k])
        for j in (i-1,i+1):
            if 0<=j<len(V[k]): q=list(p); q[k]=V[k][j]; out.append(idx[tuple(q)])
    return out
print('pass recent MDD:',sum(ok(r) for r in R),'/',len(R),'| pass + robust:',sum(robust(r) for r in R))
names=['Crash_ATRPct_Min','Crash_Drop_Pct','Crash_Lookback','Crash_Body_ATR','Crash_Trail_ATR']
for k in range(5):
    print(f'  {names[k]:18s}',{v:f"{sum(robust(r) for r in R if r['p'][k]==v)}/{sum(1 for r in R if r['p'][k]==v)}" for v in V[k]})
d=idx[(0.6,3.0,20,1.0,1.0)]; print('default',d)
C=[]
for r in R:
    if not robust(r): continue
    nb=neigh(tuple(r['p'])); sc=sum(robust(x) for x in nb)/len(nb)
    C.append((sc,r['rnet'],r))
C.sort(key=lambda x:(-x[0],-x[1]))
print('top by plateau score then recent net:')
for sc,_,r in C[:12]: print(f"  {r['p']} plateau {sc:.2f} | 近兩年 net {r['rnet']} MDD {r['rmdd']} stk {r['rstk']} | 全期 net {r['net']} MDD {r['fmdd']} stk {r['fstk']} | crash n {r['crn']} net {r['crnet']} ex26 {r['ex26']} -top {r['mtop']} | 2025/6/4後 {r['newn']} 筆 {r['newnet']}")
sc_d=sum(robust(x) for x in neigh((0.6,3.0,20,1.0,1.0)))/len(neigh((0.6,3.0,20,1.0,1.0))); print('default plateau score',round(sc_d,2))
