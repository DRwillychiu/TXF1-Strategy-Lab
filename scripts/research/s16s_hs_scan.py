# -*- coding: utf-8 -*-
"""P15 head and shoulders top / P16 inverse -- measured before any ruling.

First of group A, taken one at a time as Willy directed on 2026-08-28.

A head and shoulders is inherently 3 highs and 2 lows: left shoulder, head,
right shoulder, with two troughs between them forming the neckline.  That is
an ASYMMETRIC frame, and checklist question 5 warns about exactly that:

    3+2 是陷阱 -- 不對稱定義會機械性造出方向

The P29 case was Bulkowski's 3+2 minimum, which reports 75.5% "ascending"
while its mirror 2+3 reports 76.9% descending.  Here the asymmetry is not a
choice -- it is what the shape IS -- so the question is whether it biases the
count, and the mirror (P16, 3 lows and 2 highs) answers that directly.

Three rulings will be needed and each is measured rather than argued:

  shoulders   no symmetry requirement / exactly equal / a tolerance
  neckline    unconstrained / the two lows exactly equal / sloping allowed
  head        must exceed both shoulders -- this one is not optional, it is
              what makes it a head

Counts only.  No P&L column.
"""
import io, os, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])
    print('母體 %s 根   樞紐 %s 高 / %s 低\n'
          % (format(N, ','), format(len(PH), ','), format(len(PL), ',')))

    # ---- five alternating pivots, H L H L H  (and the mirror L H L H L) ----
    top, bot = [], []
    for k in range(len(piv) - 4):
        w = piv[k:k + 5]
        if any(w[j][1] == w[j + 1][1] for j in range(4)):
            continue
        (top if w[0][1] == 'H' else bot).append([x[0] for x in w])
    print('=' * 80)
    print(' 1. 五樞紐交替框架')
    print('=' * 80)
    print('  H L H L H（頭肩頂的框架） %s 個' % format(len(top), ','))
    print('  L H L H L（頭肩底的框架） %s 個' % format(len(bot), ','))
    print('  兩者相差 %.1f%% -- 框架本身沒有偏斜'
          % (100.0 * abs(len(top) - len(bot)) / max(len(top), len(bot))))

    def rep(name, hits, tot):
        if not hits:
            print('  %-30s %8d' % (name, 0))
            return
        yr = collections.Counter(rows[f[0]]['ymd'][:4] for f in hits)
        sp = sorted(f[-1] - f[0] for f in hits)
        z = sum(1 for y in YRS if yr[y] == 0)
        print('  %-30s %8s  年均 %6.1f  跨度中位 %2d  掛零年 %d  占框架 %5.2f%%'
              % (name, format(len(hits), ','), len(hits) / 7.64,
                 sp[len(sp) // 2], z, 100.0 * len(hits) / tot))
        print('      逐年 %s' % '  '.join('%s=%d' % (y, yr[y]) for y in YRS))

    # ---- head must exceed both shoulders; that is the only mandatory part --
    print()
    print('=' * 80)
    print(' 2. 頭必須高過兩肩（唯一非選擇性的條件），肩不設對稱要求')
    print('=' * 80)
    hs_loose = [f for f in top if H[f[0]] < H[f[2]] > H[f[4]]]
    ihs_loose = [f for f in bot if L[f[0]] > L[f[2]] < L[f[4]]]
    rep('P15 頭肩頂（肩無對稱要求）', hs_loose, len(top))
    rep('P16 頭肩底（鏡像對照）', ihs_loose, len(bot))
    print()
    print('  虛無對照：三個高點中「中間最高」的排列有 2/6 種，理論占比 33.3%%')
    print('  觀測 %.2f%% vs 33.33%%  ->  倍率 %.2fx'
          % (100.0 * len(hs_loose) / len(top),
             (len(hs_loose) / float(len(top))) / (1 / 3.0)))

    # ---- what the shoulder-symmetry ruling would cost ---------------------
    print()
    print('=' * 80)
    print(' 3. 肩的對稱要求要花多少')
    print('=' * 80)
    print('  %-22s %10s %10s %10s' % ('肩的容差', 'P15', 'P16', '代價'))
    print('  ' + '-' * 58)
    for t in (None, 0, 1, 2, 5, 10):
        if t is None:
            a, b = len(hs_loose), len(ihs_loose)
            lab, cost = '不要求（最寬鬆）', '零參數'
        else:
            a = sum(1 for f in hs_loose if abs(H[f[0]] - H[f[4]]) <= t)
            b = sum(1 for f in ihs_loose if abs(L[f[0]] - L[f[4]]) <= t)
            lab = ('完全相等' if t == 0 else '%d 點以內' % t)
            cost = '零參數' if t == 0 else '引進自由參數'
        print('  %-22s %10s %10s %10s' % (lab, format(a, ','), format(b, ','), cost))

    # ---- and the neckline ------------------------------------------------
    print()
    print('=' * 80)
    print(' 4. 頸線要不要求水平')
    print('=' * 80)
    print('  %-22s %10s %10s %10s' % ('兩個頸線點的容差', 'P15', 'P16', '代價'))
    print('  ' + '-' * 58)
    for t in (None, 0, 1, 2, 5, 10):
        if t is None:
            a, b = len(hs_loose), len(ihs_loose)
            lab, cost = '不要求（最寬鬆）', '零參數'
        else:
            a = sum(1 for f in hs_loose if abs(L[f[1]] - L[f[3]]) <= t)
            b = sum(1 for f in ihs_loose if abs(H[f[1]] - H[f[3]]) <= t)
            lab = ('完全相等' if t == 0 else '%d 點以內' % t)
            cost = '零參數' if t == 0 else '引進自由參數'
        print('  %-22s %10s %10s %10s' % (lab, format(a, ','), format(b, ','), cost))

    # ---- both at once, the strict zero-parameter reading -------------------
    print()
    print('=' * 80)
    print(' 5. 兩者都要求完全相等（唯一的嚴格零參數版本）')
    print('=' * 80)
    strict_t = [f for f in hs_loose if H[f[0]] == H[f[4]] and L[f[1]] == L[f[3]]]
    strict_b = [f for f in ihs_loose if L[f[0]] == L[f[4]] and H[f[1]] == H[f[3]]]
    rep('P15 嚴格（肩相等 ＋ 頸線水平）', strict_t, len(top))
    rep('P16 嚴格（鏡像對照）', strict_b, len(bot))
    return 0


if __name__ == '__main__':
    sys.exit(main())
