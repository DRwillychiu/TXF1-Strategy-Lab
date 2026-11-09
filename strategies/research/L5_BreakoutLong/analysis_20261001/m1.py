import pandas as pd, numpy as np
F='/mnt/user-data/uploads/TXF1_1_分鐘_1.txt'
df=pd.read_csv(F,skipinitialspace=True); df.columns=[c.strip('<> ') for c in df.columns]
t=pd.to_datetime(df['Date']+' '+df['Time'].str[:8],format='%Y/%m/%d %H:%M:%S')
np.savez('m1.npz',t=t.values.astype('datetime64[m]'),o=df.Open.values.astype(float),h=df.High.values.astype(float),l=df.Low.values.astype(float),c=df.Close.values.astype(float))
print(len(df))
