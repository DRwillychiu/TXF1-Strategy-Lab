# L1 V3.8 trading-logic evidence from MC trade lists (V3.8 = V3.7 G4 trades; B1 vs P1 isolates the loss pause).
# Points = price difference per contract (slippage excluded). Output -> stdout.
import sys, re, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
PLA='/home/claude/repo/strategies/research/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla'
T=stopstruct.load('/tmp/L1_G4.xlsx')
src=open(PLA).read()
HT={int(x) for x in re.findall(r'Holiday_Tail\[\d+\]\s*=\s*(\d+)',src)}
def ymd(d): return (d.year-1900)*10000+d.month*100+d.day
def settle(d): return d.weekday()==2 and 15<=d.day<=21
def hm(t): return t.hour*100+t.minute
BARENDS={930,1015,1100,1145,1230,1315,1345}|{1545,1630,1715,1800,1845,1930,2015,2100,2145,2230,2315,0,45,130,215,300,345,430,500}
out=collections.OrderedDict()
out['rows']=len(T); out['net']=sum(t['pnl'] for t in T)
out['entry_sig']=collections.Counter(t['esig'] for t in T)
out['exit_sig']=collections.Counter(t['xsig'] for t in T)
out['entry_not_barend']=[str(t['edt']) for t in T if hm(t['edt']) not in BARENDS]
out['entry_on_settlement_wed']=[str(t['edt']) for t in T if settle(t['edt'].date())]
out['entry_in_holiday_tail']=[str(t['edt']) for t in T if hm(t['edt'])<=500 and ymd(t['edt'].date()) in HT]
pts=lambda t:t['xpx']-t['epx']
sl=[t for t in T if t['xsig'] in ('TL_SL','Stop Loss')]
out['SL_over_0.5pct']=[(str(t['edt']),t['xsig'],t['epx'],round(-pts(t))) for t in sl if -pts(t)>t['epx']*0.005+1]
out['SL_max_pts']=max(-pts(t) for t in sl)
out['all_loss_over_450']=[(str(t['edt']),t['xsig'],round(-pts(t))) for t in T if -pts(t)>450]
out['SP_below_90']=[(str(t['edt']),round(pts(t))) for t in T if t['xsig']=='TL_SP' and pts(t)<90]
out['TP_below_entry']=[(str(t['edt']),round(pts(t))) for t in T if t['xsig']=='TL_TP' and pts(t)<0]
out['TSL_above_entry']=[(str(t['edt']),round(pts(t))) for t in T if t['xsig']=='TL_TSL' and pts(t)>0]
st=[t for t in T if t['xsig']=='TL_Settlement']
out['settle_exit_bad']=[str(t['xdt']) for t in st if not (settle(t['xdt'].date()) and hm(t['xdt'])>=1230 and hm(t['xdt'])<=1345)]
out['settle_exit_times']=collections.Counter(hm(t['xdt']) for t in st)
ho=[t for t in T if t['xsig']=='TL_Holiday']
out['holiday_exit_bad']=[str(t['xdt']) for t in ho if not (ymd(t['xdt'].date()) in HT and 345<=hm(t['xdt'])<=500)]
out['holiday_exit_times']=collections.Counter(hm(t['xdt']) for t in ho)
# hold across settlement 13:30 / holiday 05:00
def crosses(t):
    d=t['edt'].date(); bad=[]
    while d<=t['xdt'].date():
        if settle(d):
            c=dt.datetime.combine(d,dt.time(13,30))
            if t['edt']<c<t['xdt']: bad.append('settle')
        if ymd(d) in HT:
            c=dt.datetime.combine(d,dt.time(5,0))
            if t['edt']<c<t['xdt']: bad.append('holiday')
        d+=dt.timedelta(days=1)
    return bad
out['hold_across_forced']=[(str(t['edt']),crosses(t)) for t in T if crosses(t)]
# re-entries
re_=[]
for i,t in enumerate(T):
    if t['esig']=='TL_ReEntry':
        p=T[i-1]; re_.append(dict(e=str(t['edt']),prev_exit=p['xsig'],prev_entry=p['epx'],entry=t['epx'],fill_ge_prev=t['epx']>=p['epx'],pnl=t['pnl']))
out['reentries']=re_
# loss pause: P1 (no pause) vs B1 (pause 3/1), otherwise identical inputs
P1=stopstruct.load('/tmp/L1_P1.xlsx'); B1=stopstruct.load('/tmp/L1_B1.xlsx')
kb={(t['edt'],t['epx']) for t in B1}
removed=[t for t in P1 if (t['edt'],t['epx']) not in kb]
first_diff=removed[0]['edt'] if removed else None
seq=[t for t in P1 if t['edt']<first_diff] if first_diff else []
last3=[t['pnl']<0 for t in seq[-3:]]
out['pause_first_removed']=(str(first_diff),'prior 3 trades losing in P1:',last3)
out['pause_removed_count']=len(removed)
for k,v in out.items(): print(k,':',v)
