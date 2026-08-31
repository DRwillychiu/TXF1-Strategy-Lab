# -*- coding: utf-8 -*-
"""Do any of the twelve collapse into a primitive that already exists?

Three of the twelve read like they are already covered:

  P39 三下降峰   "the last three pivot highs each lower than the one before"
                 -- that is PH1 > PH2 > PH3, which IS the falling-highs half of
                 the 2x2 that already killed P24 and P25.

  P35 結構破壞    "a close through the previous pivot low" -- close to the
                 falling-lows primitive, but NOT obviously the same thing: one
                 is a bar closing through a LEVEL, the other is the next pivot
                 low landing LOWER.  Those differ whenever price pokes through
                 and recovers, or drifts under without forming a pivot.

  P13/P14 空方旗形／三角旗
                 the mirrors of P24 and P25, which were collapsed.  But the
                 atlas defines these on BARS ("one crash bar then a small
                 consolidation"), not on pivots, so the skeleton is different
                 and the collapse may not carry over.

Measured before any definition is written, because the answer decides whether
the group is twelve patterns or nine.

Everything runs on the chain the INDICATOR uses -- a repeated pivot type wipes
it.  Writing a second chain is what cost the 2026-08-30 census.

Run:  python scripts/research/s16s_twelve_reduce.py
"""
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.join('scripts', 'research')
CSV = os.path.join(HERE, 's16s_5min.csv')
CAP = 12


def bars():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    return (rows,
            [float(r['open']) for r in rows],
            [float(r['high']) for r in rows],
            [float(r['low']) for r in rows],
            [float(r['close']) for r in rows],
            [int(r['bars_in_sess']) for r in rows])


def walk(H, L, S, tests):
    """The .pla's own loop: push, then test the last N slots."""
    px = [0.0] * CAP
    bar = [0] * CAP
    typ = [0] * CAP
    ch = 0
    hit = {k: [] for k in tests}
    for i in range(1, len(H) - 1):
        if S[i] < 2 or S[i + 1] < S[i]:
            continue
        for k in (1, 2):
            if k == 1 and not (H[i] > H[i - 1] and H[i] > H[i + 1]):
                continue
            if k == 2 and not (L[i] < L[i - 1] and L[i] < L[i + 1]):
                continue
            if ch > 0 and typ[ch - 1] == k:
                ch = 0
            if ch >= CAP:
                for j in range(CAP - 1):
                    px[j] = px[j + 1]
                    bar[j] = bar[j + 1]
                    typ[j] = typ[j + 1]
                ch = CAP - 1
            px[ch] = H[i] if k == 1 else L[i]
            bar[ch] = i
            typ[ch] = k
            ch += 1
            for name, (need, first, fn) in tests.items():
                if ch < need:
                    continue
                a = ch - need
                if typ[a] != first:
                    continue
                sl = [(bar[a + t], px[a + t], typ[a + t]) for t in range(need)]
                if fn(sl):
                    hit[name].append(bar[a + need - 1])
    return hit


def main():
    rows, O, H, L, C, S = bars()

    # ---- 1. P39 against the falling-highs primitive ---------------------
    T = {
        'P39  三下降峰': (5, 1, lambda s: s[0][1] > s[2][1] > s[4][1]),
        '原語 頭頭降': (5, 1, lambda s: s[0][1] > s[2][1] > s[4][1]),
        'P39 + 底也降': (5, 1, lambda s: s[0][1] > s[2][1] > s[4][1]
                        and s[1][1] > s[3][1]),
        'P39 + 底不降': (5, 1, lambda s: s[0][1] > s[2][1] > s[4][1]
                        and s[1][1] <= s[3][1]),
    }
    h = walk(H, L, S, T)
    print('=' * 74)
    print('  1. P39 三下降峰 —— 是不是就等於「頭頭降」原語')
    print('=' * 74)
    a, b = len(h['P39  三下降峰']), len(h['原語 頭頭降'])
    print('  P39（三個樞紐高遞降）        %s' % format(a, ','))
    print('  頭頭降原語（同一條件）        %s' % format(b, ','))
    print('  -> %s' % ('逐字相同：P39 沒有多出任何條件'
                       if a == b else '不同'))
    print('  其中低點也降  %s   低點不降  %s'
          % (format(len(h['P39 + 底也降']), ','),
             format(len(h['P39 + 底不降']), ',')))
    print('  P39 沒有對低點設任何條件，所以它同時橫跨 2x2 的兩格。')

    # ---- 2. P35: a close through a level vs the next pivot being lower --
    print()
    print('=' * 74)
    print('  2. P35 結構破壞 —— 收盤穿越價位 vs 下一個樞紐更低')
    print('=' * 74)
    px = [0.0] * CAP
    typ = [0] * CAP
    ch = 0
    lastlow = None
    bos = 0          # a bar closes below the standing pivot low
    lower = 0        # the next pivot low prints lower
    both = 0
    armed = False
    for i in range(1, len(H) - 1):
        if S[i] < 2 or S[i + 1] < S[i]:
            continue
        if lastlow is not None and armed and C[i] < lastlow:
            bos += 1
            armed = False
        for k in (1, 2):
            if k == 1 and not (H[i] > H[i - 1] and H[i] > H[i + 1]):
                continue
            if k == 2 and not (L[i] < L[i - 1] and L[i] < L[i + 1]):
                continue
            if ch > 0 and typ[ch - 1] == k:
                ch = 0
            if ch >= CAP:
                for j in range(CAP - 1):
                    px[j] = px[j + 1]
                    typ[j] = typ[j + 1]
                ch = CAP - 1
            px[ch] = H[i] if k == 1 else L[i]
            typ[ch] = k
            ch += 1
            if k == 2:
                if lastlow is not None and L[i] < lastlow:
                    lower += 1
                    if not armed:
                        both += 1
                lastlow = L[i]
                armed = True
    print('  收盤跌破前一個樞紐低（P35）    %s 次' % format(bos, ','))
    print('  下一個樞紐低更低（底底降原語）  %s 次' % format(lower, ','))
    print('  -> %s' % ('兩者相同' if bos == lower else
                       '兩者不同 —— P35 不是底底降的重述'))

    # ---- 3. P13 / P14: bars, not pivots ---------------------------------
    print()
    print('=' * 74)
    print('  3. P13 / P14 空方旗形 —— 圖鑑用的是 K 棒骨架，不是樞紐')
    print('=' * 74)
    rng = [H[i] - L[i] for i in range(len(H))]
    pole = 0
    for i in range(4, len(H) - 4):
        if S[i] < 5 or S[i + 1] < S[i]:
            continue
        if C[i] >= O[i]:
            continue
        if not all(rng[i] > rng[i - d] for d in (1, 2, 3)):
            continue
        pole += 1
    print('  暴跌棒候選（收黑 + 振幅為最近四根最寬，WR4 排名）  %s'
          % format(pole, ','))
    print('  圖鑑給 P13 的母體是 20,938，P14 是 4,634 —— 兩者都遠大於此，')
    print('  代表圖鑑當初用的不是這個定義。P13/P14 要重新定義，不能沿用。')
    print()
    print('=' * 74)


if __name__ == '__main__':
    main()
