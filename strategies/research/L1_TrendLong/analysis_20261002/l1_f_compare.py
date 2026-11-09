import sys, openpyxl, datetime as dt, collections
sys.path.insert(0,'.')
from stopstruct import load
A=dt.datetime; NOW=48091; ACC=300000
K=['淨利','毛利','毛損','獲利因子','交易總次數','%勝率','最大的交易虧損','最大策略虧損','最大平倉交易虧損','最大連續虧損交易次數','最大連續虧損金額','最大策略虧損日期','最大平倉交易虧損日期']
def info(f):
    wb=openpyxl.load_workbook(f,read_only=True); d={}; m={}
    for row in wb['設定'].iter_rows(values_only=True):
        r=[c for c in row if c is not None]
        if len(r)==2 and isinstance(r[0],str): d[r[0]]=r[1]
    for sh in ('策略分析','交易分析'):
        for row in wb[sh].iter_rows(values_only=True):
            r=[c for c in row if c is not None]
            if len(r)>=2 and isinstance(r[0],str) and r[0] in K and r[0] not in m: m[r[0]]=r[1]
    return d,m
def curve(Q,key='m'):
    Q=sorted(Q,key=lambda r:r['xdt']); eq=pk=mdd=s=c=0;n=cn=0;pkd=None;md=None;sd=None;cs=None
    for r in Q:
        x=r[key]; eq+=x
        if eq>=pk: pk=eq; pkd=r['xdt']
        elif eq-pk<mdd: mdd=eq-pk; md=(pkd,r['xdt'])
        if x<0:
            if c==0: cs=r['edt']
            c+=x;cn+=1
        else: c=0;cn=0
        if c<s: s=c;n=cn;sd=(cs,r['xdt'])
    return round(eq),round(mdd),md,round(s),n,sd
F={'L1_0':'/tmp/L1_0.xlsx','F1':'/tmp/L1_F1.xlsx','F2':'/tmp/L1_F2.xlsx'}
R={}
for n,f in F.items():
    d,m=info(f); T=load(f)
    for r in T: r['m']=r['pnl']/20; r['norm']=r['m']/r['epx']*NOW
    R[n]=T
    print(n,{k:d.get(k) for k in ('SL_Pct','ReEntry_On','DTrend_Gate','Loss_Pause_N','Loss_Pause_K','SL_Max_Pts','Day_Loss_Stop_N','細部資料','結束日期')})
    print('  MC',{k:(round(v/20) if isinstance(v,(int,float)) and abs(v)>1000 else v) for k,v in m.items()})
    e,mdd,md,s,c,sd=curve(T); print('  full net',e,'MDD',mdd,[x.date() for x in md],'streak',s,c,[x.date() for x in sd])
    for nm,a,b in (('IS<6/17',A(2019,1,1),A(2026,6,17)),('OOS 6/17-9/24',A(2026,6,17),A(2026,9,25)),('2026',A(2026,1,1),A(2026,9,25)),('2025',A(2025,1,1),A(2026,1,1))):
        Q=[r for r in T if a<=r['edt']<b]; e2,m2,_,s2,c2,_=curve(Q); print(f'  {nm}: n {len(Q)} net {e2} MDD {m2} streak {s2}({c2})')
    e3,m3,md3,s3,c3,_=curve(T,'norm'); print('  norm@48091 MDD',m3,f'{-m3/ACC*100:.1f}%','streak',s3,c3,f'{-s3/ACC*100:.1f}%')
    y=collections.defaultdict(float)
    for r in T: y[r['xdt'].year]+=r['m']
    print('  yearly',{k:round(v) for k,v in sorted(y.items())})
b={(r['edt'],r['epx']):r for r in R['L1_0']}
for n in ('F1','F2'):
    x={(r['edt'],r['epx']):r for r in R[n]}
    miss=[b[k] for k in b if k not in x]; new=[x[k] for k in x if k not in b]
    print(n,'missing vs base',len(miss),round(sum(r['m'] for r in miss)),'winners missed',sum(r['m']>0 for r in miss),'max missed',round(max([r['m'] for r in miss],default=0)),'| new',len(new),round(sum(r['m'] for r in new)))
