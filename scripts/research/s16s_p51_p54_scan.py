# -*- coding: utf-8 -*-
"""P51-P54 broadening-wedge family: measure BEFORE the rulings are drafted.

Discipline 1 of pattern-definition-checklist, written the day after ruling 12
admitted I had recommended from argument rather than evidence: any option
comparison runs the numbers first.

All four are P29's structure with the monotonic requirement changed, so the
whole detector carries over -- six alternating pivots, one session for pivot
detection but not for the formation, lows below highs. Only the edge condition
differs:

  P29  highs rising      lows falling     (the two edges diverge symmetrically)
  P51  highs rising      lows RISING      and the highs rise faster
  P52  highs FALLING     lows falling     and the lows fall faster
  P53  highs EQUAL       lows falling     (flat top, right angle)
  P54  highs rising      lows EQUAL       (flat bottom, right angle)

"Equal" means exactly equal, the same zero-parameter convention P29 uses for
matching highs and lows. Whether that is too strict on 5-minute TXF1 is a
question the counts answer, not an opinion.

Counts only. No P&L column.
"""
import io, os, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    Y = [r['ymd'] for r in rows]
    N = len(rows)
    print('母體 %d 根   %s ~ %s' % (N, Y[0], Y[-1]))

    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])
    print('樞紐 %d 高 / %d 低   合併 %d' % (len(PH), len(PL), len(piv)))

    # ---- every six alternating pivots, exactly the P29 frame ----
    frames = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        ix = [x[0] for x in w]
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue                                  # lows under highs
        frames.append((w[0][1], hs, ls, ix))
    print('六樞紐交替且低在高下的框架 %s 個' % format(len(frames), ','))

    def rise(a):
        return a[0] < a[1] < a[2]

    def fall(a):
        return a[0] > a[1] > a[2]

    def flat(a):
        return a[0] == a[1] == a[2]

    def spanH(hs):
        return H[hs[2]] - H[hs[0]]

    def spanL(ls):
        return L[ls[2]] - L[ls[0]]

    DEF = {
        'P29 擴散三角（對照）': lambda hs, ls: rise([H[i] for i in hs]) and fall([L[i] for i in ls]),
        'P51 上升擴散楔形': lambda hs, ls: (rise([H[i] for i in hs]) and rise([L[i] for i in ls])
                                       and spanH(hs) > spanL(ls)),
        'P52 下降擴散楔形': lambda hs, ls: (fall([H[i] for i in hs]) and fall([L[i] for i in ls])
                                       and abs(spanL(ls)) > abs(spanH(hs))),
        'P53 右角擴散（上）': lambda hs, ls: flat([H[i] for i in hs]) and fall([L[i] for i in ls]),
        'P54 右角擴散（下）': lambda hs, ls: rise([H[i] for i in hs]) and flat([L[i] for i in ls]),
    }

    print()
    print('=' * 84)
    print(' 嚴格定義（「相等」＝完全相等）')
    print('=' * 84)
    print('%-22s %8s %10s %8s %10s' % ('型態', '個數', '年均', '跨度中位', '日/夜'))
    print('-' * 84)
    res = {}
    for name, fn in DEF.items():
        hit = [f for f in frames if fn(f[1], f[2])]
        res[name] = hit
        if not hit:
            print('%-22s %8d      —          —          —' % (name, 0))
            continue
        sp = sorted(f[3][-1] - f[3][0] for f in hit)
        day = sum(1 for f in hit if 845 <= int(rows[f[3][0]]['hhmm']) <= 1345)
        print('%-22s %8s %9.1f %9d %6d/%d'
              % (name, format(len(hit), ','), len(hit) / 7.64,
                 sp[len(sp) // 2], day, len(hit) - day))

    # ---- how much does "exactly equal" cost?  the same question 3+2 raised ----
    print()
    print('=' * 84)
    print(' ★ 「完全相等」有多嚴格 —— P53 / P54 靠它，值得先量')
    print('=' * 84)
    tol = collections.OrderedDict()
    for t in (0, 1, 2, 5, 10):
        n53 = sum(1 for f in frames
                  if max(H[i] for i in f[1]) - min(H[i] for i in f[1]) <= t
                  and fall([L[i] for i in f[2]]))
        n54 = sum(1 for f in frames
                  if max(L[i] for i in f[2]) - min(L[i] for i in f[2]) <= t
                  and rise([H[i] for i in f[1]]))
        tol[t] = (n53, n54)
    print('  %-14s %10s %10s' % ('容差（點）', 'P53', 'P54'))
    for t, (a, b) in tol.items():
        print('  %-14s %10s %10s   %s'
              % ('%d' % t, format(a, ','), format(b, ','),
                 '<- 零容差（現行慣例）' if t == 0 else ''))
    print()
    print('  提醒：容差是自由參數。上表是為了讓裁示有依據，不是建議採用非零值。')

    print()
    print('=' * 84)
    print(' 逐年（檢查有沒有整年掛零）')
    print('=' * 84)
    yrs = sorted({y[:4] for y in Y})
    print('  %-22s %s' % ('型態', '  '.join(yrs)))
    for name, hit in res.items():
        c = collections.Counter(Y[f[3][0]][:4] for f in hit)
        print('  %-22s %s' % (name, '  '.join('%4d' % c.get(y, 0) for y in yrs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
