import pandas as pd, numpy as np
F='/mnt/user-data/uploads/TXF1_1_分鐘_1.txt'
df=pd.read_csv(F,skipinitialspace=True)
df.columns=[c.strip('<> ') for c in df.columns]
df['dt']=pd.to_datetime(df['Date']+' '+df['Time'].str[:8],format='%Y/%m/%d %H:%M:%S')
df=df.set_index('dt')[['Open','High','Low','Close','Volume']]
# 15m bars, bar end time label (MC style: 08:46-09:00 -> 09:00)
b=df.resample('15min',label='right',closed='right').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
# trading day: bars ending after 15:00 belong to next weekday
t=b.index
hm=t.hour*100+t.minute
d=pd.Series(t.normalize(),index=t)
nxt=(hm>1500)|(hm<=500)
td=d.copy()
td[hm>1500]=d[hm>1500]+pd.Timedelta(days=1)
# map to next business day (skip weekends); holidays: next trading day present in data handled later
td=td.apply(lambda x: x if x.weekday()<5 else x+pd.Timedelta(days=7-x.weekday()))
b['td']=td.values
b['sess']=np.where((hm>=900)&(hm<=1345),'D','N')
b.to_pickle('b15.pkl')
print(len(b),b.index[0],b.index[-1])
