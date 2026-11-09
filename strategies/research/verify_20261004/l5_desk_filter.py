exec(open('l5_logic_check.py').read().split("for k,v in o.items(): print(k,':',v)")[0])
sys.path.insert(0,'/home/claude/repo/strategies/research/portfolio_20261003')
from portfolio_eval import load_pf, FULL
PT=[t for t in load_pf(FULL) if t['s']=='L5']
for name,TT in (('research_chart',T),('desktop_portfolio',PT)):
    cnt=collections.Counter(); bad=[]; seen=set()
    for t in TT:
        if (t['edt'],t['epx']) in seen: continue
        seen.add((t['edt'],t['epx'])); s=sig_bar(t['edt']); i=bisect.bisect_right(DT,s)-1
        ok=DC[i]>sma(DC,i,60); cnt[ok]+=1
        if not ok: bad.append(str(t['edt']))
    print(name,dict(cnt),bad)
