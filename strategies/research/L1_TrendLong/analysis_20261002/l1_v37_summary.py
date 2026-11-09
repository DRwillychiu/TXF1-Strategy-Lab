# L1 V3.2 vs V3.7 (=G4 report; #29 450 does not bind at SL_Pct 0.5, S batch row 0.5 == G4) full summary numbers.
import sys, datetime as dt, collections, openpyxl; sys.path.insert(0,'.')
from stopstruct import load
A=dt.datetime; NOW=48091; ACC=300000
K=['淨利','毛利','毛損','獲利因子','交易總次數','%勝率','最大策略虧損','最大平倉交易虧損','最大連續虧損交易次數','最大連續虧損金額','最大的交易虧損','平均獲利交易','平均虧損交易 ','平均獲利/平均虧損  比率','平均交易(獲利 & 虧損)','最大策略虧損日期']
def mc(f):
    wb=openpyxl.load_workbook(f,read_only=True); m={}
    for sh in ('策略分析','交易分析'):
        for row in wb[sh].iter_rows(values_only=True):
            r=[c for c in row if c is not None]
            if len(r)>=2 and isinstance(r[0],str) and r[0] in K and r[0] not in m: m[r[0]]=r[1]
    return m
def curve(T,key='m',s0=None):
    T=sorted(T,key=lambda r:r['xdt']); eq=pk=mdd=s=c=0;n=cn=0;mc_=0;pkd=s0;md=None;sd=None;cs=None
    for r in T:
        x=r[key]; eq+=x
        if eq>=pk: pk=eq; pkd=r['xdt']
        elif eq-pk<mdd: mdd=eq-pk; md=(pkd,r['xdt'])
        if x<0:
            if c==0: cs=r['edt']
            c+=x;cn+=1
        else: c=0;cn=0
        if c<s: s=c;n=cn;sd=(cs,r['xdt'])
        mc_=max(mc_,cn)
    return dict(net=round(eq),mdd=round(mdd),mdd_w=md,streak=round(s),sn=n,sd=sd,mcl=mc_)
def basic(T):
    W=[r['m'] for r in T if r['m']>0]; L=[r['m'] for r in T if r['m']<=0]
    gp=sum(W); gl=sum(L)
    return dict(n=len(T),win=len(W)/max(1,len(T))*100,gp=round(gp),gl=round(gl),pf=gp/abs(gl) if gl else 0,aw=gp/max(1,len(W)),al=gl/max(1,len(L)),avg=(gp+gl)/max(1,len(T)),maxloss=round(min([r['m'] for r in T],default=0)))
R={}
for n,f in (('V3.2','/tmp/L1_P0.xlsx'),('P1','/tmp/L1_P1.xlsx'),('B1','/tmp/L1_B1.xlsx'),('V3.7','/tmp/L1_G4.xlsx')):
    T=load(f)
    for r in T: r['m']=r['pnl']/20; r['norm']=r['m']/r['epx']*NOW
    R[n]=(T,mc(f))
def win(T,a,b): return [r for r in T if a<=r['edt']<b]
P={'全期':(A(2019,1,1),A(2026,9,25)),'近兩年':(A(2024,10,1),A(2026,9,25)),'2026':(A(2026,1,1),A(2026,9,25)),'樣本外6/17-9/24':(A(2026,6,17),A(2026,9,25))}
out={}
for n,(T,m) in R.items():
    out[n]={}
    for pn,(a,b) in P.items():
        Q=win(T,a,b); c=curve(Q,s0=a); bs=basic(Q); nc=curve(Q,'norm',s0=a)
        gaps=sum(1 for r in Q if r['xsig']=='TL_SL_Gap'); eng=sum(1 for r in Q if r['xsig']=='Stop Loss')
        over=sum(1 for r in Q if r['xsig'] in ('TL_SL','TL_SL_Gap','Stop Loss') and (r['epx']-r['xpx'])>r['epx']*0.005*1.2)
        out[n][pn]=dict(**bs,**c,nmdd=-nc['mdd']/ACC*100,nstreak=-nc['streak']/ACC*100,gaps=gaps,eng=eng,over=over)
    out[n]['MC']={k.strip():v for k,v in m.items()}
    y=collections.defaultdict(list)
    for r in T: y[r['xdt'].year].append(r)
    out[n]['yearly']={yr:(round(sum(r['m'] for r in v)),curve(v)['mdd'],len(v)) for yr,v in sorted(y.items())}
import json
print(json.dumps(out,default=str,ensure_ascii=False,indent=0)[:200])
json.dump(out,open('/tmp/claude-0/l1_v37_summary.json','w'),default=str,ensure_ascii=False)
