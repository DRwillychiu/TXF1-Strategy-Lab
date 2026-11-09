exec(open('l5_logic_check.py').read().split("for k,v in o.items(): print(k,':',v)")[0])
cnt=collections.Counter(); det=[]
seen=set()
for t in T:
    if not t['esig'].startswith('BL_Entry') or (t['edt'],t['epx']) in seen: continue
    seen.add((t['edt'],t['epx'])); s=sig_bar(t['edt']); i=bisect.bisect_right(DT,s)-1
    h1=DC[i]>sma(DC,i,60)
    h2=DC[i+1]>sma(DC,i+1,60) if i+1<len(DC) else None   # bar in progress at signal time (final close)
    h3=DC[i-1]>sma(DC,i-1,60)                            # one more bar back
    sess='day' if 845<hm(s)<=1345 else 'night'
    cnt[(sess,'H1',h1)]+=1; cnt[(sess,'H2',h2)]+=1; cnt[(sess,'H3',h3)]+=1
print(sorted(cnt.items()))
