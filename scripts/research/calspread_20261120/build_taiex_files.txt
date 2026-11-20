"""把證交所每 5 秒加權指數（每天一個 csv）整理成兩個檔：
1. TAIEX_5s_<起>_<迄>.csv：date,time,taiex 全部合併
2. TAIEX 1 分鐘.txt：MultiCharts ASCII 格式（和 TXF1 1 分鐘.txt 同欄位），K 棒時間＝收盤時間
   09:01 那根含 09:00:00～09:01:00，之後每根含 (前一分, 本分]；成交量欄填 0（指數沒有量）
Usage: python -I scripts/research/calspread_20261120/build_taiex_files.py <taiex_5s 資料夾> <輸出資料夾>
原始每日 csv 不改。
"""
import csv
import os
import sys


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    files = sorted(f for f in os.listdir(src) if f.endswith(".csv") and len(f) == 12)
    d0, d1 = files[0][:8], files[-1][:8]
    p5 = os.path.join(outdir, f"TAIEX_5s_{d0}_{d1}.csv")
    p1 = os.path.join(outdir, "TAIEX 1 分鐘.txt")
    n5 = n1 = 0
    short = []
    with open(p5 + ".tmp", "w", encoding="utf-8", newline="") as f5, \
            open(p1 + ".tmp", "w", encoding="ascii", newline="") as f1:
        w5 = csv.writer(f5, lineterminator="\r\n")
        w5.writerow(["date", "time", "taiex"])
        f1.write("<Date>, <Time>, <Open>, <High>, <Low>, <Close>, <UpVolume>, <DownVolume>, <TotalVolume>, "
                 "<UpTicks>, <DownTicks>, <TotalTicks>\r\n")
        for fn in files:
            y, m, d = fn[:4], fn[4:6], fn[6:8]
            with open(os.path.join(src, fn), encoding="utf-8") as f:
                rows = [(r["time"], r["taiex"]) for r in csv.DictReader(f)]
            if len(rows) != 3241:
                short.append(f"{fn[:8]}({len(rows)})")
            ds = f"{y}-{m}-{d}"
            for t, v in rows:
                w5.writerow([ds, t, v])
                n5 += 1
            bars = {}
            for t, v in rows:
                h, mi, s = int(t[:2]), int(t[3:5]), int(t[6:8])
                k = h * 60 + mi + (1 if s > 0 else 0)
                k = max(k, 9 * 60 + 1)  # 09:00:00 併入 09:01
                x = float(v)
                if k in bars:
                    o, hi, lo, _ = bars[k]
                    bars[k] = (o, max(hi, x), min(lo, x), x)
                else:
                    bars[k] = (x, x, x, x)
            dm = f"{int(y)}/{int(m)}/{int(d)}"
            for k in sorted(bars):
                o, hi, lo, c = bars[k]
                f1.write(f"{dm},{k // 60:02d}:{k % 60:02d}:00.000,{o:.2f},{hi:.2f},{lo:.2f},{c:.2f},0,0,0,0,0,0\r\n")
                n1 += 1
    os.replace(p5 + ".tmp", p5)
    os.replace(p1 + ".tmp", p1)
    print(f"days {len(files)} ({d0}~{d1})  5s rows {n5}  1m bars {n1}  not-3241 days: {short or 'none'}")
    print(p5)
    print(p1)


if __name__ == "__main__":
    main()
