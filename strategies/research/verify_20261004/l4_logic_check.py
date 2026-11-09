# L4 v14.10 trading-logic evidence: MC T8 report (= v14.10 trades); 1-min data rebuilds daily (MC composition) and 60M bars.
import sys, re, datetime as dt, collections, bisect
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
T=stopstruct.load('/tmp/L4T8.xlsx')
src=open('/home/claude/repo/strategies/research/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla').read()
HT={int(x) for x in re.findall(r'Holiday_Tail\[\d+\]\s*=\s*(\d+)',src)}
def ymd(d): return (d.year-1900)*10000+d.month*100+d.day
def hm(t): return t.hour*100+t.minute
def settle(d): return d.weekday()==2 and 15<=d.day<=21
o=collections.OrderedDict()
o['rows']=len(T); o['net']=sum(t['pnl'] for t in T)
o['entry_sig']=collections.Counter(t['esig'] for t in T); o['exit_sig']=collections.Counter(t['xsig'] for t in T)
o['qty']=collections.Counter((t['xsig'],t.get('qty')) for t in T)
pts=lambda t:t['epx']-t['xpx']
o['entry_fill_0215_0500']=[str(t['edt']) for t in T if 215<=hm(t['edt'])<=500]
o['entry_settle_wed']=[str(t['edt']) for t in T if settle(t['edt'].date())]
o['entry_holiday_tail']=[str(t['edt']) for t in T if hm(t['edt'])<=500 and ymd(t['edt'].date()) in HT]
sl=[t for t in T if t['xsig'] in ('CS_SL','Stop Loss')]
o['SL_over_cap']=[(str(t['edt']),t['xsig'],round(-pts(t)),round(min(t['epx']*0.008,450)),str(t['xdt'])) for t in sl if -pts(t)>min(t['epx']*0.008,450)+1]
o['max_loss_pts']=max(-pts(t) for t in T)
o['TP1_not_profit']=[str(t['edt']) for t in T if t['xsig']=='CS_TP1' and pts(t)<=0]
for nm in ('CS_Holiday','CS_Settlement'): o[nm+'_times']=collections.Counter(hm(t['xdt']) for t in T if t['xsig']==nm)
o['engine_stop_rows']=[(str(t['edt']),str(t['xdt'])) for t in T if t['xsig']=='Stop Loss']
# ---- rebuild daily (MC composition) and 60M bars ----
D=collections.OrderedDict(); H=collections.OrderedDict()
with open('/mnt/user-data/uploads/TXF1_1_分鐘_2.txt') as fh:
    next(fh)
    for line in fh:
        p=line.split(','); y,m,d=map(int,p[0].split('/')); t=dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5])); c=float(p[5]); h=hm(t)
        if not (846<=h<=1345 or h>=1501 or h<=500): continue
        k=t.date()+dt.timedelta(days=1) if h>=1500 else t.date()
        D[k]=(t,c)   # last minute and close
        if 846<=h<=1345: e=t.replace(minute=45) if t.minute<=45 and t.minute>0 else (t.replace(minute=45)+dt.timedelta(hours=1))
        else: e=t.replace(minute=0) if t.minute==0 else (t.replace(minute=0)+dt.timedelta(hours=1))
        if 846<=h<=1345:
            e=t.replace(minute=45) if t.minute>45 else t.replace(minute=45)
            if t.minute>45: e=e+dt.timedelta(hours=1)
            if t.minute==0: e=t.replace(minute=45)  # 09:00 belongs to 08:46-09:45
        H[e]=c
DK=list(D); DT=[D[k][0] for k in DK]; DC=[D[k][1] for k in DK]
HK=sorted(H); HC=[H[k] for k in HK]
def sma(a,i,n): return sum(a[i-n+1:i+1])/n if i>=n-1 else None
def last_daily(t): return bisect.bisect_right(DT,t)-1
def last_60(t): return bisect.bisect_right(HK,t)-1
def sig_bar(e):
    if hm(e)==900:   # 08:45 open fill: signal = 05:00 bar of the same date (Monday: Saturday 05:00)
        d=e.date()-dt.timedelta(days=2) if e.weekday()==0 else e.date()
        return dt.datetime.combine(d,dt.time(5,0))
    if hm(e)==1515: return e.replace(hour=13,minute=45)
    return e-dt.timedelta(minutes=15)
res=collections.Counter(); bad=[]
seen=set()
for t in T:
    if t['esig']!='CS_Entry' or (t['edt'],t['epx']) in seen: continue
    seen.add((t['edt'],t['epx']))
    s=sig_bar(t['edt']); i=last_daily(s); ip=last_daily(s-dt.timedelta(minutes=15))
    m60=sma(DC,i,60); m20=sma(DC,i,20); m60p=sma(DC,ip,60)
    A=(DC[i]>m60) and (m60>=m60p); B=(m20>m60); blk=A or B
    j=last_60(s); ma48=sma(HC,j,48); trend=-1 if HC[j]<ma48 else 1
    res[('macro_block',blk)]+=1; res[('trend',trend)]+=1
    if blk or trend!=-1: bad.append((str(t['edt']),'A' if A else '','B' if B else '',trend))
o['entry_filter_check']=dict(res); o['entry_filter_mismatch']=bad
for k,v in o.items(): print(k,':',v)
