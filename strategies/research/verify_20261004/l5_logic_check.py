# L5 v19.20 trading-logic evidence: research-chart MC reports v19.17 defaults (= v19.20 all defaults) and v19.18 (= State 0).
import sys, re, datetime as dt, collections, bisect
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
T=stopstruct.load('/tmp/claude-0/l5/2b73daa1.xlsx'); S0=stopstruct.load('/tmp/claude-0/l5/53d2884b.xlsx')
src=open('/home/claude/repo/strategies/research/L5_BreakoutLong/L5_v19.20/L5_BreakoutLong_v19.20.pla').read()
HT={int(x) for x in re.findall(r'Holiday_Tail\[\d+\]\s*=\s*(\d+)',src)}
def ymd(d): return (d.year-1900)*10000+d.month*100+d.day
def hm(t): return t.hour*100+t.minute
def settle(d): return d.weekday()==2 and 15<=d.day<=21
o=collections.OrderedDict()
o['rows']=len(T); o['net']=sum(t['pnl'] for t in T)
o['entry_sig']=collections.Counter(t['esig'] for t in T); o['exit_sig']=collections.Counter(t['xsig'] for t in T)
pts=lambda t:t['xpx']-t['epx']
o['entry_fill_0415_0500']=[str(t['edt']) for t in T if 415<=hm(t['edt'])<=500]
o['entry_settle_wed']=[str(t['edt']) for t in T if settle(t['edt'].date())]
o['entry_holiday_tail']=[str(t['edt']) for t in T if hm(t['edt'])<=500 and ymd(t['edt'].date()) in HT]
o['loss_over_450']=[(str(t['edt']),t['xsig'],round(-pts(t))) for t in T if -pts(t)>450]
o['TP_rows']=collections.Counter((t['xsig'],t['qty']) for t in T if t['xsig'].startswith('BL_TP'))
o['TP_not_profit']=[str(t['edt']) for t in T if t['xsig'].startswith('BL_TP') and pts(t)<=0]
for nm in ('Holiday','Settlement','TimeExit'):
    o[nm+'_exit_times']=collections.Counter(hm(t['xdt']) for t in T if nm in t['xsig'])
o['engine_stop']=[(str(t['edt']),str(t['xdt'])) for t in T if t['xsig']=='Stop Loss']
# loss memory: trades in defaults but not in State 0 should be Mid entries after a >=450-pt (per lot) closed loss
k0={(t['edt'],t['epx']) for t in S0}; kd={(t['edt'],t['epx']) for t in T}
rem=[t for t in T if (t['edt'],t['epx']) not in k0]; add=[t for t in S0 if (t['edt'],t['epx']) not in kd]
o['LM_removed_rows']=len(rem); o['LM_added_rows']=len(add)
o['LM_removed_entry_types']=collections.Counter(t['esig'] for t in rem)
P0=stopstruct.positions(S0)
first_trigger=min((p['xdt'] for p in P0 if p['pnl']*20/400 <= -450), default=None)
o['LM_first_trigger_in_State0']=str(first_trigger)
o['LM_removed_before_trigger']=[str(t['edt']) for t in rem if first_trigger and t['edt']<first_trigger]
# daily filter: last completed daily close > MA60 (MC composition), using signal bar = fill bar - 15 min
D=collections.OrderedDict()
with open('/mnt/user-data/uploads/TXF1_1_分鐘_2.txt') as fh:
    next(fh)
    for line in fh:
        p=line.split(','); y,m,d=map(int,p[0].split('/')); t=dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5])); h=hm(t)
        if not (846<=h<=1345 or h>=1501 or h<=500): continue
        k=t.date()+dt.timedelta(days=1) if h>=1500 else t.date()
        D[k]=(t,float(p[5]))
DK=list(D); DT=[D[k][0] for k in DK]; DC=[D[k][1] for k in DK]
def sma(a,i,n): return sum(a[i-n+1:i+1])/n if i>=n-1 else None
def sig_bar(e):
    if hm(e)==900: return dt.datetime.combine(e.date()-dt.timedelta(days=2) if e.weekday()==0 else e.date(), dt.time(5,0))
    if hm(e)==1515: return e.replace(hour=13,minute=45)
    return e-dt.timedelta(minutes=15)
# weekly: group completed daily bars by ISO week of the daily key; weekly close = last daily close of that week
WK=collections.OrderedDict()
for i,k in enumerate(DK): WK[k.isocalendar()[:2]]=i
WKEYS=list(WK); WEND=[DT[WK[w]] for w in WKEYS]; WC=[DC[WK[w]] for w in WKEYS]
res=collections.Counter(); bad=[]; seen=set()
for t in T:
    if not t['esig'].startswith('BL_Entry') or (t['edt'],t['epx']) in seen: continue
    seen.add((t['edt'],t['epx'])); s=sig_bar(t['edt'])
    i=bisect.bisect_right(DT,s)-1; dok=DC[i]>sma(DC,i,60)
    j=bisect.bisect_right(WEND,s)-1
    # weekly bar [0] = last week whose last daily bar has closed; current week in progress excluded
    wok=WC[j]>sma(WC,j,20) and WC[j]>sma(WC,j,60) if j>=59 else None
    res[('daily',dok)]+=1; res[('weekly',wok)]+=1
    if not dok or wok is False: bad.append((str(t['edt']),dok,wok))
o['filter_check']=dict(res); o['filter_mismatch']=bad[:10]; o['filter_mismatch_n']=len(bad)
for k,v in o.items(): print(k,':',v)
for e in ['2021-07-29 10:15:00','2021-09-10 09:15:00','2025-02-05 09:15:00']:
    ed=dt.datetime.strptime(e,'%Y-%m-%d %H:%M:%S'); s=sig_bar(ed); i=bisect.bisect_right(DT,s)-1
    print(e,'sig',s,'last daily',DK[i],DC[i],'ma60',round(sma(DC,i,60),1),'gap%',round((DC[i]/sma(DC,i,60)-1)*100,3),'| alt(prev day incl):',DK[i-1],DC[i-1],round(sma(DC,i-1,60),1))
