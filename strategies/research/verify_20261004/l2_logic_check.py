# L2 v5.11 trading-logic evidence: MC v5.10 report (= v5.11 trades), v5.7 vs v5.8 (plan B only), 1-min data for weekly filter.
import sys, datetime as dt, collections, statistics, openpyxl
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
T=stopstruct.load(U+'e4a43657-TXF1__L2_TrendShort_v5.10_________.xlsx')
def hm(t): return t.hour*100+t.minute
def settle(d): return d.weekday()==2 and 15<=d.day<=21
o=collections.OrderedDict()
o['rows']=len(T); o['net']=sum(t['pnl'] for t in T)
o['entry_sig']=collections.Counter(t['esig'] for t in T); o['exit_sig']=collections.Counter(t['xsig'] for t in T)
pts=lambda t:t['epx']-t['xpx']   # short
o['max_loss_pts']=max(-pts(t) for t in T); o['loss_over_450']=[(str(t['edt']),round(-pts(t))) for t in T if -pts(t)>450]
o['entry_on_settle_wed']=[str(t['edt']) for t in T if settle(t['edt'].date())]
for nm in set(t['xsig'] for t in T):
    o['exit_times_'+nm]=collections.Counter(f"{t['xdt'].strftime('%a')} {hm(t['xdt'])}" for t in T if t['xsig']==nm).most_common(6)
# weekly filter from 1-min data: Friday close at 12:45 (last minute <= 12:45)
fri={}
with open('/mnt/user-data/uploads/TXF1_1_分鐘_2.txt') as fh:
    next(fh)
    for line in fh:
        p=line.split(','); y,m,d=map(int,p[0].split('/')); D=dt.date(y,m,d)
        if D.weekday()!=4: continue
        h=int(p[1][:2]); mi=int(p[1][3:5])
        if 845<h*100+mi<=1245: fri[D]=float(p[5])
F=sorted(fri)
def filter_ok(sig_end):
    cl=[fri[d] for d in F if dt.datetime.combine(d,dt.time(12,45))<sig_end]
    if len(cl)<13: return None
    w=cl[-13:]; return cl[-1]<sum(w)/13
# signal bar = 60-min bar before the entry bar
def prev_bar_end(e):
    h=hm(e)
    seq_day=[945,1045,1145,1245,1345]; seq_n=[1600,1700,1800,1900,2000,2100,2200,2300,0,100,200,300,400,500]
    if h==945: return (e-dt.timedelta(days=2 if e.weekday()==0 else 0)).replace(hour=5,minute=0)  # 08:45 open fill: 05:00 bar of the same date (Monday: Saturday)
    if h in seq_day: return e-dt.timedelta(hours=1)
    if h==1600: return e.replace(hour=13,minute=45)
    return e-dt.timedelta(hours=1)
chk=collections.Counter(); bad=[]
for t in T:
    ok=filter_ok(prev_bar_end(t['edt']))
    kind='crash' if t['esig'].startswith('CR') else 'bear'
    chk[(kind,ok)]+=1
    if (kind=='bear' and ok is not True) or (kind=='crash' and ok is not False): bad.append((str(t['edt']),t['esig'],ok))
o['weekly_filter_check']=dict(chk); o['weekly_filter_mismatch']=bad
# plan B: v5.7 (SP 0.75) vs v5.8 (Bear_Pause_N 3, Skip_K 1): settings diff then trade diff
def settings(f):
    r=[[x for x in row if x is not None] for row in openpyxl.load_workbook(f,read_only=True)['設定'].iter_rows(values_only=True)]
    return {x[0]:x[1] for x in r if len(x)==2}
a,b=U+'8f5e7c50-TXF1__L2_TrendShort_v5.7__________SL_0.75.xlsx',U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx'
sa,sb=settings(a),settings(b)
o['planB_settings_diff']={k:(sa.get(k),sb.get(k)) for k in set(sa)|set(sb) if sa.get(k)!=sb.get(k)}
A=stopstruct.load(a); B=stopstruct.load(b)
kb={(t['edt'],t['epx']) for t in B}; ka={(t['edt'],t['epx']) for t in A}
rem=[t for t in A if (t['edt'],t['epx']) not in kb]; add=[t for t in B if (t['edt'],t['epx']) not in ka]
res=[]
for r in rem:
    prior=[t for t in B if t['xdt']<=r['edt'] and t['esig']=='TS_Entry']
    res.append(all(t['pnl']<0 for t in prior[-3:]) and len(prior)>=3)
o['planB_removed']=len(rem); o['planB_added']=len(add); o['planB_removed_after_3_bear_losses']=sum(res)
for k,v in o.items(): print(k,':',v)
# extra checks
day=lambda t:845<hm(t)<=1345
o2={}
o2['InitSL_D_not_day']=[str(t['xdt']) for t in T if t['xsig']=='TS_InitSL_D' and not day(t['xdt'])]
o2['InitSL_N_not_night']=[str(t['xdt']) for t in T if t['xsig']=='TS_InitSL_N' and day(t['xdt'])]
o2['engine_stop_not_entry_bar']=[(str(t['edt']),str(t['xdt'])) for t in T if t['xsig']=='Stop Loss' and t['xdt']!=t['edt']]
o2['stopprofit_below_0.3375pct']=[(str(t['edt']),round(pts(t)),round(t['epx']*0.003375)) for t in T if t['xsig']=='TS_StopProfit' and pts(t)<t['epx']*0.003375-1]
o2['holiday_exit']=[(str(t['xdt'])) for t in T if t['xsig']=='TS_Holiday']
o2['crash_one_per_leg_min_gap_hours']=min(((b['edt']-a['xdt']).total_seconds()/3600) for a,b in zip([t for t in T if t['esig']=='CR_Entry'],[t for t in T if t['esig']=='CR_Entry'][1:]))
for k,v in o2.items(): print(k,':',v)
