"""抓證交所「每 5 秒指數統計」的發行量加權股價指數，一天一檔（time,taiex）。
- 交易日清單由 TXF1 1 分 K 反推；先抓有期交所結算價的日子，再抓其他，都由新到舊。
- 已存在的檔案跳過（可中斷續抓）；HTTP 403 或連續 5 次錯誤就停。
Usage: python -I scripts/research/calspread_20261120/fetch_taiex_5s.py <TXF1 1分.txt> <結算價.csv> <輸出資料夾> [起始年=2020] [間隔秒=5] [上限筆數]
"""
import json, os, sys, time, urllib.request, urllib.error

URL = "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_INDEX?date={d}&response=json"

def trading_days(f1, y0):
    days = set()
    with open(f1, encoding="utf-8", errors="replace") as f:
        next(f)
        for ln in f:
            d, t = ln.split(",", 2)[:2]
            if int(d.split("/")[0]) >= y0 and "09:01" <= t[:5] <= "13:30":
                days.add(d)
    return days

def ymd(d):
    y, m, dd = d.split("/")
    return f"{int(y):04d}{int(m):02d}{int(dd):02d}"

def main():
    f1, fsp, out = sys.argv[1:4]
    y0 = int(sys.argv[4]) if len(sys.argv) > 4 else 2020
    gap = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
    limit = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 9
    os.makedirs(out, exist_ok=True)
    days = trading_days(f1, y0)
    pri = {ln.split(",")[0] for ln in open(fsp, encoding="utf-8").read().splitlines()[1:]} & days
    order = sorted(pri, key=ymd, reverse=True) + sorted(days - pri, key=ymd, reverse=True)
    if os.environ.get("FETCH_OLDEST_FIRST") == "1":
        order = sorted(days, key=ymd)
    todo = [d for d in order if not os.path.exists(os.path.join(out, ymd(d) + ".csv"))
            and not os.path.exists(os.path.join(out, ymd(d) + ".nodata"))]
    print(f"days {len(days)}  priority {len(pri)}  todo {len(todo)}", flush=True)
    errs = done = 0
    for d in todo[:limit]:
        k = ymd(d)
        if os.path.exists(os.path.join(out, k + ".csv")):
            continue
        try:
            req = urllib.request.Request(URL.format(d=k), headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"{k} HTTP {e.code}", flush=True)
            if e.code in (403, 429):
                print("STOP: blocked", flush=True); sys.exit(2)
            errs += 1
        except Exception as e:
            print(f"{k} ERR {type(e).__name__}: {e}", flush=True); errs += 1
        else:
            rows = j.get("data") or []
            if j.get("stat") == "OK" and len(rows) > 100:
                tmp = os.path.join(out, k + ".tmp")
                with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                    f.write("time,taiex\n")
                    for r in rows:
                        f.write(f"{r[0]},{r[1].replace(',', '')}\n")
                os.replace(tmp, os.path.join(out, k + ".csv"))
                errs = 0; done += 1
                if done % 50 == 0 or done <= 3:
                    print(f"{k} ok rows {len(rows)}  done {done}/{len(todo)}", flush=True)
            else:
                open(os.path.join(out, k + ".nodata"), "w").write(str(j.get("stat")))
                print(f"{k} nodata stat={j.get('stat')} rows={len(rows)}", flush=True)
        if errs >= 5:
            print("STOP: 5 errors in a row", flush=True); sys.exit(3)
        time.sleep(gap)
    print(f"FINISHED done {done}", flush=True)

if __name__ == "__main__":
    main()
