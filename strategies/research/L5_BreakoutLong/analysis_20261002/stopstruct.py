import openpyxl, datetime, collections, statistics as st
LO,LIVE,HI=datetime.datetime(2021,9,16),datetime.datetime(2026,6,17),datetime.datetime(2026,9,25)
def load(path):
    ws=openpyxl.load_workbook(path,read_only=True,data_only=True)['交易明細']
    rows=list(ws.iter_rows(values_only=True))[3:]
    tr=[];cur=None
    for r in rows:
        if r[2] is None: continue
        dt=datetime.datetime.combine(r[4].date(), r[5] if isinstance(r[5],datetime.time) else datetime.time(0,0))
        if '進入' in r[2]: cur=dict(esig=r[3],edt=dt,epx=r[6],qty=r[7],pnl=r[8],mfe=r[12],mae=r[14])
        elif '離開' in r[2] and cur:
            cur.update(xsig=r[3],xdt=dt,xpx=r[6]); tr.append(cur); cur=None
    return tr
def tday(dt):
    d=dt.date()
    if dt.hour*100+dt.minute>=1500: d+=datetime.timedelta(days=1)
    while d.weekday()>=5: d+=datetime.timedelta(days=1)
    return d
def sess(dt): return '日' if 845<=dt.hour*100+dt.minute<=1345 else '夜'
def positions(tr):
    g=collections.OrderedDict()
    for t in tr: g.setdefault((t['edt'],t['epx'],t['esig']),[]).append(t)
    P=[]
    for (edt,epx,esig),v in g.items():
        P.append(dict(edt=edt,epx=epx,esig=esig.split('_')[-1],pnl=sum(x['pnl'] for x in v)/20,
                      xs=[x['xsig'] for x in v],xdt=max(x['xdt'] for x in v),xpx=v[-1]['xpx'],
                      mfe=max((x['mfe'] or 0) for x in v)/20,mae=min((x['mae'] or 0) for x in v)/20,
                      stop=any('_SL_' in x['xsig'] or x['xsig']=='Stop Loss' for x in v),sess=sess(edt),td=tday(edt)))
    return P
