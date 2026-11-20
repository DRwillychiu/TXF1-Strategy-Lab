import sys, os, datetime as D
sys.path.insert(0, "."); sys.path.insert(0, "tools")
import mc_report
from pathlib import Path
from txfcore.strategies import s16_s_v1_26 as s16
from txfcore.quotes.history import MC12MinuteSource
from tests.test_l6_v020_clean import _params
DL = Path(r"C:\Users\WILLY CHIU\Downloads")
def trades(f):
    wb = mc_report._open(DL / f); out=[]; cur=None
    for r in list(wb["交易明細"].iter_rows(values_only=True))[3:]:
        t=str(r[2] or "")
        dt = D.datetime.combine(r[4].date(), r[5]) if r[4] else None
        if "進入" in t: cur=[dt.isoformat(" ")[:16], r[3], r[6], r[8] or 0]
        elif "離開" in t and cur: out.append((cur[0], cur[1], cur[2], dt.isoformat(" ")[:16], str(r[3]), r[6], cur[3])); cur=None
    st=[r for r in wb["設定"].iter_rows(values_only=True) if any(c is not None for c in r)]
    return out, st
new, st = trades("TXF1  L6_MACrossShort_v020_RESEARCH 策略回測績效報告.xls")
old, st_old = trades("TXF1  L6_MACrossShort_v1.0.0 策略回測績效報告.xls")
for r in st: print([c for c in r if c is not None][:6])
PLA = Path("strategies/research/L6_MACrossShort/L6_v0.2.0/L6_MACrossShort_v0.2.0.pla")
print("MC v020", len(new), "MC v100", len(old), "identical:", new == old)
bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(), D.datetime(2019,1,1), D.datetime(2026,11,20,9,35))
py = [t for t in s16.run(bars, _params(), s16.holiday_tail(PLA), settle_shift=s16.settle_shift(PLA)).trades if t.entry_dt.strftime("%Y-%m-%d %H:%M") >= new[0][0]]
bad=[(i+1,a,m) for i,(t,m) in enumerate(zip(py,new)) for a in [(t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.entry_px, t.exit_dt.strftime("%Y-%m-%d %H:%M"), t.exit_label[:19], t.exit_px)] if a!=m[:6] or abs(t.net_ntd-m[6])>=1]
print("python", len(py), "diffs", len(bad), bad[:3])
print("net MC", sum(m[6] for m in new), "py", round(sum(t.net_ntd for t in py)))
vals=[r for r in st if r[0]=="策略參數"][0][1].strip("()").split(",")
p=list(s16.pla_params(PLA).values())
conv=lambda s: (s.strip().lower()=="true") if s.strip().lower() in("true","false") else float(s)
print("params", len(vals), len(p), "equal:", [conv(v) for v in vals]==p)
a={r[0]:r[1] for r in st if r[0] not in("策略名稱","策略參數")}; b={r[0]:r[1] for r in st_old if r[0] not in("策略名稱","策略參數")}
print("other settings same as v1.0.0:", a==b, {k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)})
