# Boundary check: the robust plateau sat at the grid edge (ATR% 0.7, drop 4.0) -> extend both. Same rule as l2_crash_grid_eval.
import itertools, json
from multiprocessing import Pool
from l2_crash_grid import ev
V=[(0.6,0.65,0.7,0.75,0.8),(3.5,4.0,4.5,5.0),(20,25,30),(0.8,1.0,1.2),(1.0,1.25)]
if __name__=='__main__':
    grid=list(itertools.product(*V))
    with Pool(2) as pool: R=pool.map(ev,grid,chunksize=8)
    json.dump(R,open('/tmp/claude-0/l2_crash_grid2.json','w'))
    idx={tuple(r['p']):r for r in R}; B=-6365
    robust=lambda r: r['rmdd']>=B and r['ex26']>=0 and r['mtop']>0
    def neigh(p):
        out=[]
        for k in range(5):
            i=V[k].index(p[k])
            for j in (i-1,i+1):
                if 0<=j<len(V[k]): q=list(p); q[k]=V[k][j]; out.append(idx[tuple(q)])
        return out
    names=['ATRPct_Min','Drop_Pct','Lookback','Body_ATR','Trail_ATR']
    for k in range(5): print(f'  {names[k]:11s}',{v:f"{sum(robust(r) for r in R if r['p'][k]==v)}/{sum(1 for r in R if r['p'][k]==v)}" for v in V[k]})
    C=[(sum(robust(x) for x in neigh(tuple(r['p'])))/len(neigh(tuple(r['p']))),r) for r in R if robust(r)]
    C.sort(key=lambda x:(-x[0],-x[1]['rnet']))
    for sc,r in C[:10]: print(f"  {r['p']} plateau {sc:.2f} | 近兩年 net {r['rnet']} MDD {r['rmdd']} stk {r['rstk']} | 全期 net {r['net']} MDD {r['fmdd']} | crash n {r['crn']} net {r['crnet']} ex26 {r['ex26']} -top {r['mtop']} | 2025/6/4後 {r['newn']} 筆 {r['newnet']}")
    for p in ((0.7,4.0,25,0.8,1.0),(0.75,4.0,25,0.8,1.0),(0.7,4.5,25,0.8,1.0),(0.8,4.0,25,0.8,1.0),(0.7,5.0,25,0.8,1.0)):
        r=idx[p]; print('  check',p,'近兩年 net',r['rnet'],'MDD',r['rmdd'],'全期 MDD',r['fmdd'],'crash n',r['crn'],'2025/6/4後',r['newn'],r['newnet'],'robust',robust(r))
