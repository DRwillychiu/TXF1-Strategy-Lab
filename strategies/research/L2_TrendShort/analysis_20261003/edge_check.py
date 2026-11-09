# Edge-case checks on an MC trade list (finalized versions): holiday tails, settlement Wednesdays, loss points, overlap.
import sys, re, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load, positions
def tails(pla):
    s=open(pla).read(); return sorted({int(x) for x in re.findall(r'=\s*(1[0-9]{6})\s*;',s) if 1190000<int(x)<1280000})
def d2i(d): return (d.year-1900)*10000+d.month*100+d.day
def settle(d): return d.weekday()==2 and 15<=d.day<=21
def check(rep,pla,side,pts_per_lot_div=400,cap=450,label=''):
    T=load(rep); P=positions(T); H=set(tails(pla))
    out=collections.OrderedDict()
    # holiday: any position open across a tail date 05:00 (tail date = bars 00:00-05:00 stamped that date)
    hol=[]
    for p in P:
        for h in H:
            hd=dt.datetime(1900+h//10000,(h//100)%100,h%100,5,0)
            if p['edt']<hd and p['xdt']>hd: hol.append((p['edt'],p['xdt'],h))
    out['持倉跨過假日尾盤 05:00']=len(hol)
    out['假日尾盤（00:00-05:00）進場']=sum(1 for p in P if d2i(p['edt'].date()) in H and p['edt'].hour<5 or (p['edt'].hour==5 and p['edt'].minute==0 and d2i(p['edt'].date()) in H))
    st=[p for p in P if settle(p['edt'].date()) and p['edt'].hour>=8 and p['edt'].hour<14]
    out['結算日日盤進場']=len(st)
    sx=[p for p in P if any(settle((p['edt']+dt.timedelta(days=k)).date()) and p['edt']<dt.datetime.combine((p['edt']+dt.timedelta(days=k)).date(),dt.time(13,30))<p['xdt'] for k in range(0,40))]
    out['持倉跨過結算 13:30']=len(sx)
    lp=[((p['epx']-p['xpx']) if side=='L' else (p['xpx']-p['epx']), p) for p in P]
    big=[(round(a),p['edt'],p['xs']) for a,p in lp if a>cap]
    out[f'單筆虧損 > {cap} 點']=len(big)
    out['最大單筆虧損點數']=round(max(a for a,_ in lp))
    ov=sum(1 for a,b in zip(sorted(P,key=lambda p:p['edt']),sorted(P,key=lambda p:p['edt'])[1:]) if b['edt']<a['xdt'])
    out['部位重疊']=ov
    print('==',label,len(P),'positions'); [print('  ',k,v) for k,v in out.items()]
    if big: print('   >cap detail',big[:8])
    if hol: print('   holiday detail',hol[:5])
    if sx: print('   settle detail',[(p['edt'],p['xdt']) for p in sx[:5]])
    return out
if __name__=='__main__':
    check(sys.argv[1],sys.argv[2],sys.argv[3],cap=float(sys.argv[4]) if len(sys.argv)>4 else 450,label=sys.argv[5] if len(sys.argv)>5 else '')
