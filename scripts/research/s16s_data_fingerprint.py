# -*- coding: utf-8 -*-
"""Fingerprint the reference CSV, because it is not in version control.

2026-08-28.  Two machines spent parts of two days disagreeing about whether
the P29 reference is 202 or 203, and the disagreement was treated as a code
question on both sides.  It is not.

    .gitignore lines 14 and 16 exclude scripts/research/s16s_5min.csv.

Nothing guarantees the desktop and the laptop hold the same file, so every
"reference number" derived from it is machine-local.  Concretely, on the
desktop today:

    s16s_p29_clean.py, unmodified, on this CSV  ->  203
    the committed s16s_p29_clean.json           ->  202

The JSON no longer matches the generator that is supposed to produce it.  That
is reproducible in one command and is not a matter of opinion.

Windowing does not explain it either.  Truncating to MC12's start bar
(2019-01-02 13:40, 58 bars later) still gives 203, and the pivot counts on
neither window match the 75,136 / 76,017 recorded on 2026-08-28.

So: print a fingerprint both machines can compare in one line, plus the
derived counts, so a data difference announces itself instead of being
rediscovered as a code bug.

    python scripts/research/s16s_data_fingerprint.py
"""
import io, os, sys, csv, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
CSV = os.path.join(HERE, 's16s_5min.csv')


def main():
    if not os.path.exists(CSV):
        print('  找不到 %s' % CSV)
        return 1
    h = hashlib.sha256()
    with open(CSV, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)

    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])

    n29 = 0
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (H[hs[0]] < H[hs[1]] < H[hs[2]]):
            continue
        if not (L[ls[0]] > L[ls[1]] > L[ls[2]]):
            continue
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        n29 += 1

    print('=' * 74)
    print(' s16s_5min.csv fingerprint   （此檔不在版控，兩台機器必須自行比對）')
    print('=' * 74)
    print('  sha256       %s' % h.hexdigest())
    print('  bytes        %s' % format(os.path.getsize(CSV), ','))
    print('  bars         %s' % format(N, ','))
    print('  first        %s %s' % (rows[0]['ymd'], rows[0]['hhmm']))
    print('  last         %s %s' % (rows[-1]['ymd'], rows[-1]['hhmm']))
    print('  pivot_high   %s' % format(len(PH), ','))
    print('  pivot_low    %s' % format(len(PL), ','))
    print('  P29          %s' % n29)
    print('=' * 74)
    print('  sha256 一致 -> 所有參考值必然一致，數字對不上就是程式問題。')
    print('  sha256 不同 -> 先把資料弄成一樣，再談任何參考值。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
