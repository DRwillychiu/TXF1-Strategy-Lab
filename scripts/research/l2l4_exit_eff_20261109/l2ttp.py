import os
import sys; sys.argv=[sys.argv[0], sys.argv[1], "/dev/null"]
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exit_eff.py"),encoding="utf-8").read().split("# ---------- L4 第二口")[0]
src=src.replace("ps.pg.price, ps.pg.peak, ps.active_sl, ttp, ps.lowest_close))","ps.pg.price, ps.pg.peak, ps.active_sl, ttp, ps.lowest_close, atr))")
src=src.replace("_, _, ptype, pg, peak, asl, ttp, lc = r","_, _, ptype, pg, peak, asl, ttp, lc, atr = r\n        ttp = lc*(1+REB/100) if ep-lc >= atr*MINATR else 0.0\n        if not USE_SL: asl = 0.0")
src=src.replace("lines = [x for x in (pg, asl, ttp, ep + hard) if x > 0]","lines = [x for x in (pg, asl, ttp, ep + hard) if x > 0]")
src=src.split("cf_rows = []")[0]
exec(src)
import collections
for USE_SL in (False,):
  for MINATR in (2.0,3.0,4.0):
    for REB in (1.0,1.5):
        tot=0; rows=[]; yy=collections.Counter()
        for p in P2:
            c=l2_counterfactual(p)
            if c and c["j"]<p["i1"]:
                d=c["real"]-p["real"]; tot+=d; rows.append((p["entry"],round(p["real"]),round(c["real"]),round(d))); yy[p["entry"][:4]]+=d*20
        print(f"只加盤中TTP 波段≥{MINATR}ATR 反彈{REB}%: 改變{len(rows)}筆 好{sum(r[3]>0 for r in rows)} 壞{sum(r[3]<0 for r in rows)} 合計{tot:+.0f}點=微台{tot*20:+,.0f}", {k:round(v) for k,v in sorted(yy.items())})
        for r in rows:
            if abs(r[3])>=150: print("    ",r)
