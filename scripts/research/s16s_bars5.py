# -*- coding: ascii -*-
"""
S16_S 5-minute bar loader -- reads the MC12 5-minute export directly.

Replaces the aggregate-from-1-minute path in s16s_bars.py. The export is
already 5-minute bars produced by MultiCharts itself, so there is no
bucketing step and no chance of Python and MC12 disagreeing about which
minutes belong to which bar.

The export also carries the strategy's own indicator columns -- ZLEMA_F,
ZLEMA_S, Entry, Blocked, GoldenX -- so the death-cross population can be
read off rather than recomputed. That removes a whole class of
reimplementation error from anything built on top of it.

Session logic is mirrored from S16_S_MACrossShort_v1.26.0.pla:
    v_In_Day   = Time >  845  and Time <= 1345
    v_In_Night = Time > 1500  or  Time <=  500
    v_Sess_First    -> transition from outside a session to inside, OR a
                       wall-clock gap larger than one bar (Sess_GapReset_On)
    v_Bars_In_Sess  -> 1 on a session's first bar, else +1

Provenance -- byte count and MD5 -- prints on every run.

Run:  python scripts/research/s16s_bars5.py
"""
import io, os, sys, csv, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r"C:\Users\User\Desktop\MC9_20260108\report\TXF1 5min.txt"
SRC = os.environ.get('S16S_SRC5', SRC)
if not os.path.exists(SRC):
    _alt = os.path.join(os.path.expanduser('~'), 'Desktop', 'MC9_20260108',
                        '\u5831\u50f9', 'TXF1 5 \u5206\u9418.txt')
    if os.path.exists(_alt):
        SRC = _alt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's16s_5min.csv')


def provenance(path):
    h = hashlib.md5()
    n = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            n += len(b)
            h.update(b)
    return n, h.hexdigest()


def load(path):
    """Returns bars oldest-first with session state attached."""
    bars = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        rd = csv.reader(f)
        head = next(rd)
        cols = [c.strip().strip('<>').lower() for c in head]
        idx = dict((c, i) for i, c in enumerate(cols))
        for row in rd:
            if len(row) < 6 or not row[0].strip():
                continue
            y, m, d = [int(x) for x in row[idx['date']].strip().split('/')]
            hh, mm = row[idx['time']].strip().split(':')[:2]
            t = int(hh) * 100 + int(mm)
            b = dict(ymd=y * 10000 + m * 100 + d, t=t,
                     mins=(y * 10000 + m * 100 + d, int(hh) * 60 + int(mm)),
                     o=float(row[idx['open']]), h=float(row[idx['high']]),
                     l=float(row[idx['low']]), c=float(row[idx['close']]),
                     v=float(row[idx['volume']]))
            for extra in ('zlema_f', 'zlema_s', 'entry', 'blocked', 'goldenx'):
                if extra in idx and idx[extra] < len(row):
                    try:
                        b[extra] = float(row[idx[extra]])
                    except ValueError:
                        b[extra] = 0.0
            bars.append(b)
    return bars


def dord(y, m, d):
    """Days since epoch, so a multi-day hole is measurable."""
    if m <= 2:
        y -= 1
        m += 12
    return 365 * y + y // 4 - y // 100 + y // 400 + (153 * (m - 3) + 2) // 5 + d - 1


def sessionise(bars):
    prev_in = False
    prev_abs = None
    n = 0
    for b in bars:
        t = b['t']
        in_day = (845 < t <= 1345)
        in_ngt = (t > 1500 or t <= 500)
        inside = in_day or in_ngt
        y, m, d = b['ymd'] // 10000, (b['ymd'] // 100) % 100, b['ymd'] % 100
        absmin = dord(y, m, d) * 1440 + (t // 100) * 60 + (t % 100)

        gap_reset = False
        if prev_abs is not None:
            delta = absmin - prev_abs
            if delta > 5 or delta <= 0:
                gap_reset = True

        first = inside and ((not prev_in) or gap_reset)
        if first:
            n = 1
        elif inside:
            n += 1
        else:
            n = 0

        b['in_day'] = in_day
        b['in_ngt'] = in_ngt
        b['first'] = first
        b['bis'] = n
        prev_in = inside
        prev_abs = absmin
    return bars


def main():
    if not os.path.exists(SRC):
        print('SOURCE NOT FOUND: %s' % SRC)
        print('set S16S_SRC5 to the 5-minute export and re-run')
        return 1

    nbytes, md5 = provenance(SRC)
    print('=' * 74)
    print('  S16_S 5-MIN LOADER  (direct MC12 export, no aggregation)')
    print('=' * 74)
    print('  source : %s' % SRC)
    print('  bytes  : %d' % nbytes)
    print('  md5    : %s' % md5)

    bars = sessionise(load(SRC))
    print('  bars   : %d' % len(bars))
    print('  first  : %d %04d' % (bars[0]['ymd'], bars[0]['t']))
    print('  last   : %d %04d' % (bars[-1]['ymd'], bars[-1]['t']))

    d = sum(1 for b in bars if b['in_day'])
    n = sum(1 for b in bars if b['in_ngt'])
    x = len(bars) - d - n
    print('  in day / night / NEITHER : %d / %d / %d   <- last must be 0' % (d, n, x))
    print('  sessions : %d' % sum(1 for b in bars if b['first']))

    if 'zlema_f' in bars[0]:
        warm = sum(1 for b in bars if b['zlema_f'] == 0.0)
        dx = 0
        for i in range(1, len(bars)):
            a, c = bars[i - 1], bars[i]
            if a['zlema_f'] == 0 or c['zlema_f'] == 0:
                continue
            if a['zlema_f'] >= a['zlema_s'] and c['zlema_f'] < c['zlema_s']:
                dx += 1
        print('  zlema warm-up rows (0.00) : %d' % warm)
        print('  DEATH CROSSES read from the export : %d' % dx)

    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ymd', 'hhmm', 'open', 'high', 'low', 'close', 'volume',
                    'in_day', 'in_night', 'bars_in_sess',
                    'zlema_f', 'zlema_s'])
        for b in bars:
            w.writerow([b['ymd'], '%04d' % b['t'], b['o'], b['h'], b['l'], b['c'],
                        b['v'], int(b['in_day']), int(b['in_ngt']), b['bis'],
                        b.get('zlema_f', ''), b.get('zlema_s', '')])
    print('  cache written : %s' % OUT)
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())
