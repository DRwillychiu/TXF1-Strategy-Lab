# -*- coding: utf-8 -*-
"""
S16_S 5-min bar loader -- SELF-CONTAINED.

Reads the local 1-minute export, aggregates to 5-minute bars, and reproduces
the .pla session logic exactly so Python and MultiCharts agree on which bar
sits where in a session.

Provenance is printed on every run: byte count + MD5 of the source file.
No external script is exec()'d.  Replaces the unreproducible
A1_kbtype_census.py dependency recorded in the spec section 2.1.

Session logic mirrored from S16_S_MACrossShort_v1.26.0.pla lines 574-593:
    v_In_Day   = Time >  845  and Time <= 1345
    v_In_Night = Time > 1500  or  Time <=  500
    v_Sess_First    -> transition from outside a session to inside
    v_Bars_In_Sess  -> 1 on the session's first bar, else +1

5-minute bucketing: a bar stamped T covers the five 1-minute bars stamped
T-4..T, because MultiCharts stamps a bar at its CLOSE.  Bucketing is done on
absolute minutes so the night session crosses midnight without splitting.
"""
import sys, os, csv, hashlib, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r"C:\Users\WILLY CHIU\Desktop\Multichart_9\report\TXF1 1 min.txt"
SRC = os.environ.get('S16S_SRC', SRC)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's16s_5min.csv')

DAY_START, DAY_END = 845, 1345
NGT_START, NGT_END = 1500, 500


def provenance(path):
    n = os.path.getsize(path)
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return n, h.hexdigest()


def dord(y, m, d):
    """Days since 1970-01-01, proleptic Gregorian. Avoids datetime overhead."""
    if m <= 2:
        y -= 1
        m += 12
    return (365 * y + y // 4 - y // 100 + y // 400 + (153 * (m - 3) + 2) // 5 + d - 1) - 719468


def load_1min(path):
    rows = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        rd = csv.reader(f)
        next(rd)                                   # header
        for r in rd:
            if len(r) < 6:
                continue
            ds = r[0].strip()
            ts = r[1].strip()
            if not ds or not ts:
                continue
            y, mo, dy = (int(x) for x in ds.split('/'))
            hh, mi = int(ts[0:2]), int(ts[3:5])
            absm = dord(y, mo, dy) * 1440 + hh * 60 + mi
            rows.append((absm, float(r[2]), float(r[3]), float(r[4]), float(r[5])))
    return rows


def to_5min(rows):
    """Group by ceil(absolute_minute / 5) * 5.  Returns list of dicts."""
    out, cur, key = [], None, None
    for absm, o, h, l, c in rows:
        k = -((-absm) // 5) * 5                    # ceil to next multiple of 5
        if k != key:
            if cur:
                out.append(cur)
            key = k
            cur = {'k': k, 'o': o, 'h': h, 'l': l, 'c': c, 'n': 1}
        else:
            cur['h'] = max(cur['h'], h)
            cur['l'] = min(cur['l'], l)
            cur['c'] = c
            cur['n'] += 1
    if cur:
        out.append(cur)
    return out


def stamp(k):
    """absolute minute -> (yyyymmdd, HHMM as MC integer)"""
    days, rem = divmod(k, 1440)
    hh, mm = divmod(rem, 60)
    # civil date from days since epoch
    z = days + 719468
    era = (z if z >= 0 else z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    if m <= 2:
        y += 1
    return y * 10000 + m * 100 + d, hh * 100 + mm


def sessionise(bars):
    """Attach in_day / in_night / bars_in_sess exactly as the .pla computes them."""
    prev_day = prev_ngt = False
    bis = 0
    for b in bars:
        ymd, t = stamp(b['k'])
        b['ymd'], b['t'] = ymd, t
        in_day = (t > DAY_START) and (t <= DAY_END)
        in_ngt = (t > NGT_START) or (t <= NGT_END)
        first = (in_day and not prev_day) or (in_ngt and not prev_ngt)
        if first:
            bis = 1
        elif in_day or in_ngt:
            bis += 1
        else:
            bis = 0
        b['in_day'], b['in_ngt'], b['bis'] = in_day, in_ngt, bis
        prev_day, prev_ngt = in_day, in_ngt
    return bars


def main():
    if not os.path.exists(SRC):
        print('SOURCE NOT FOUND: %s' % SRC)
        print('set S16S_SRC to the 1-minute export and re-run')
        return 1

    nbytes, md5 = provenance(SRC)
    print('=' * 74)
    print('  S16_S 5-MIN BAR LOADER -- provenance')
    print('=' * 74)
    print('  source : %s' % SRC)
    print('  bytes  : %d' % nbytes)
    print('  md5    : %s' % md5)

    rows = load_1min(SRC)
    print('  1-min rows parsed : %d' % len(rows))

    bars = sessionise(to_5min(rows))
    print('  5-min bars built   : %d' % len(bars))

    full = sum(1 for b in bars if b['n'] == 5)
    part = len(bars) - full
    print('  built from 5 x 1-min : %d  (%.2f%%)' % (full, 100.0 * full / len(bars)))
    print('  built from fewer     : %d  (%.2f%%)' % (part, 100.0 * part / len(bars)))
    from collections import Counter
    cnt = Counter(b['n'] for b in bars)
    print('  minute-count histogram : %s' % dict(sorted(cnt.items())))

    d = sum(1 for b in bars if b['in_day'])
    n = sum(1 for b in bars if b['in_ngt'])
    x = len(bars) - d - n
    print('  in day session   : %d' % d)
    print('  in night session : %d' % n)
    print('  in NEITHER       : %d   <- must be 0' % x)

    print('  first bar : %d %04d' % (bars[0]['ymd'], bars[0]['t']))
    print('  last  bar : %d %04d' % (bars[-1]['ymd'], bars[-1]['t']))

    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ymd', 'hhmm', 'open', 'high', 'low', 'close', 'n1min',
                    'in_day', 'in_night', 'bars_in_sess'])
        for b in bars:
            w.writerow([b['ymd'], '%04d' % b['t'], b['o'], b['h'], b['l'], b['c'],
                        b['n'], int(b['in_day']), int(b['in_ngt']), b['bis']])
    print('  cache written : %s' % OUT)
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())
