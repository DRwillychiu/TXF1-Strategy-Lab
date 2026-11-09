# L3 v18.4 trading-logic evidence: MC L3_182 report (= v18.4 trades), 1-min data for entry fill = bar open check.
import sys, re, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
T=stopstruct.load(U+'abf84359-TXF1__L3_ConsolidationLong_v18_2_________.xlsx')
src=open('/home/claude/repo/strategies/research/L3_ConsolidationLong/L3_v18.4/L3_ConsolidationLong_v18.4.pla').read()
HT={int(x) for x in re.findall(r'Holiday_Tail\[\d+\]\s*=\s*(\d+)',src)}
def ymd(d): return (d.year-1900)*10000+d.month*100+d.day
def hm(t): return t.hour*100+t.minute
def settle(d): return d.weekday()==2 and 15<=d.day<=21
night=lambda t: hm(t)>=1530 or hm(t)<=500
o=collections.OrderedDict()
o['rows']=len(T); o['net']=sum(t['pnl'] for t in T)
o['entry_sig']=collections.Counter(t['esig'] for t in T); o['exit_sig']=collections.Counter(t['xsig'] for t in T)
o['entry_outside_1530_0500']=[str(t['edt']) for t in T if not night(t['edt'])]
o['entry_settle_wed']=[str(t['edt']) for t in T if settle(t['edt'].date())]
o['entry_holiday_tail']=[str(t['edt']) for t in T if hm(t['edt'])<=500 and ymd(t['edt'].date()) in HT]
pts=lambda t:t['xpx']-t['epx']
sl=[t for t in T if t['xsig'] in ('CL_SL','Stop Loss')]
o['SL_pts_min_max']=(min(-pts(t) for t in sl), max(-pts(t) for t in sl))
o['SL_over_0.7pct_or_450']=[(str(t['edt']),t['xsig'],round(-pts(t)),round(min(t['epx']*0.007,450)),str(t['xdt'])) for t in sl if -pts(t)>min(t['epx']*0.007,450)+1]
o['SL_under_60']=[(str(t['edt']),round(-pts(t))) for t in sl if -pts(t)<59]
o['TP_not_profit']=[(str(t['edt']),round(pts(t))) for t in T if t['xsig']=='CL_TP' and pts(t)<=0]
o['engine_stop_not_entry_bar']=sum(1 for t in T if t['xsig']=='Stop Loss' and t['xdt']!=t['edt'])
o['engine_stop_on_entry_bar']=sum(1 for t in T if t['xsig']=='Stop Loss' and t['xdt']==t['edt'])
for nm in ('CL_Holiday','CL_Settlement'):
    o[nm+'_times']=collections.Counter(hm(t['xdt']) for t in T if t['xsig']==nm)
o['holiday_exit_not_tail']=[str(t['xdt']) for t in T if t['xsig']=='CL_Holiday' and ymd(t['xdt'].date()) not in HT]
o['settle_exit_not_wed']=[str(t['xdt']) for t in T if t['xsig']=='CL_Settlement' and not settle(t['xdt'].date())]
def crosses(t):
    d=t['edt'].date(); b=[]
    while d<=t['xdt'].date():
        if settle(d) and t['edt']<dt.datetime.combine(d,dt.time(13,30))<t['xdt']: b.append('settle')
        if ymd(d) in HT and t['edt']<dt.datetime.combine(d,dt.time(5,0))<t['xdt']: b.append('holiday')
        d+=dt.timedelta(days=1)
    return b
o['hold_across_forced']=[(str(t['edt']),crosses(t)) for t in T if crosses(t)]
# entry fill = open of the 15M fill bar? (buy stop at box bottom sits below price -> fills at open)
need={t['edt'].date() for t in T if t['edt']>=dt.datetime(2019,1,3)}|{(t['edt']-dt.timedelta(days=1)).date() for t in T}
M={}
with open('/mnt/user-data/uploads/TXF1_1_分鐘_2.txt') as fh:
    next(fh)
    for line in fh:
        p=line.split(','); y,m,d=map(int,p[0].split('/')); D=dt.date(y,m,d)
        if D in need: M[dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5]))]=float(p[2])
c=collections.Counter(); diff=[]
for t in T:
    if t['edt']<dt.datetime(2019,1,3): continue
    st=t['edt']-dt.timedelta(minutes=14)
    op=M.get(st)
    if op is None: c['no_data']+=1; continue
    if abs(op-t['epx'])<0.5: c['fill_at_open']+=1
    elif t['epx']<op: c['fill_below_open']+=1; diff.append((str(t['edt']),op,t['epx']))
    else: c['fill_above_open']+=1; diff.append((str(t['edt']),op,t['epx']))
o['entry_fill_vs_open']=dict(c); o['entry_fill_not_open_sample']=diff[:8]
for k,v in o.items(): print(k,':',v)
