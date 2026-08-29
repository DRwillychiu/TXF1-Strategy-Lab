# -*- coding: utf-8 -*-
"""Group A, all seven pivot-based patterns, measured in one pass.

P15 head and shoulders   P16 inverse   P18 triple top   P21 ascending channel
P23 triple bottom        P57 measured move down         P68 double top

Provisional zero-parameter definitions throughout.  That is good enough for
the question being asked here -- a population that comes back empty or flooded
reaches the same conclusion however the definition is later refined, and only
the middle band needs a ruling.

Every pattern gets a control, and choosing the control correctly is the whole
job.  P16 is NOT P15's control: they are the top/bottom pair, the same
relationship P49 and P50 have, so equal frequency is expected rather than
informative.  The control has to be the SHAPE mirror inside the same frames.

Testing the rule stated on 2026-08-28:

    monotone constraints interact with the 10.3 : 1 co-movement of highs and
    lows and carry information; peak/trough constraints do not.

P21 is the test case -- it is the only monotone pattern in the group, so its
ratio should sit well away from 1.00.  If it does not, the rule is wrong.

Counts only.  No P&L column.
"""
import io, os, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']


def load():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    return rows, H, L, N, sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])


def frames(piv, k, first):
    out = []
    for s in range(len(piv) - k + 1):
        w = piv[s:s + k]
        if any(w[j][1] == w[j + 1][1] for j in range(k - 1)):
            continue
        if w[0][1] != first:
            continue
        out.append([x[0] for x in w])
    return out


def rep(rows, name, hits, tot, N):
    if not hits:
        print('  %-26s %8d' % (name, 0))
        return
    yr = collections.Counter(rows[f[0]]['ymd'][:4] for f in hits)
    sp = sorted(f[-1] - f[0] for f in hits)
    z = sum(1 for y in YRS if yr[y] == 0)
    print('  %-26s %8s  年均 %6.1f  跨度中位 %2d  掛零年 %d  每 %s 根一個'
          % (name, format(len(hits), ','), len(hits) / 7.64, sp[len(sp) // 2], z,
             format(int(N / len(hits)), ',')))
    print('      逐年 %s' % '  '.join('%s=%d' % (y, yr[y]) for y in YRS))


def main():
    rows, H, L, N, piv = load()
    f5t = frames(piv, 5, 'H')      # H L H L H
    f5b = frames(piv, 5, 'L')      # L H L H L
    f3t = frames(piv, 3, 'H')      # H L H
    f3b = frames(piv, 3, 'L')      # L H L
    print('母體 %s 根\n' % format(N, ','))
    print('五樞紐框架  H起 %s / L起 %s      三樞紐框架  H起 %s / L起 %s\n'
          % (format(len(f5t), ','), format(len(f5b), ','),
             format(len(f3t), ','), format(len(f3b), ',')))

    # ---------------- P18 / P23 triple top and bottom ---------------------
    print('=' * 82)
    print(' P18 三重頂 / P23 三重底 —— 三個高（低）點完全相等')
    print('=' * 82)
    p18 = [f for f in f5t if H[f[0]] == H[f[2]] == H[f[4]]]
    p23 = [f for f in f5b if L[f[0]] == L[f[2]] == L[f[4]]]
    rep(rows, 'P18 三重頂（完全相等）', p18, len(f5t), N)
    rep(rows, 'P23 三重底（完全相等）', p23, len(f5b), N)
    print()
    print('  容差的代價：')
    print('  %-14s %10s %10s %12s' % ('容差', 'P18', 'P23', '代價'))
    for t in (0, 1, 2, 5, 10):
        a = sum(1 for f in f5t if max(H[f[0]], H[f[2]], H[f[4]])
                - min(H[f[0]], H[f[2]], H[f[4]]) <= t)
        b = sum(1 for f in f5b if max(L[f[0]], L[f[2]], L[f[4]])
                - min(L[f[0]], L[f[2]], L[f[4]]) <= t)
        print('  %-14s %10s %10s %12s'
              % ('完全相等' if t == 0 else '%d 點以內' % t,
                 format(a, ','), format(b, ','),
                 '零參數' if t == 0 else '引進自由參數'))

    # ---------------- P68 double top --------------------------------------
    print()
    print('=' * 82)
    print(' P68 雙頂 —— 兩個高點完全相等，中間一個低點')
    print('=' * 82)
    p68 = [f for f in f3t if H[f[0]] == H[f[2]]]
    p68b = [f for f in f3b if L[f[0]] == L[f[2]]]
    rep(rows, 'P68 雙頂（完全相等）', p68, len(f3t), N)
    rep(rows, '雙底（鏡像對照）', p68b, len(f3b), N)
    print('  占三樞紐框架 %.2f%% / %.2f%%'
          % (100.0 * len(p68) / len(f3t), 100.0 * len(p68b) / len(f3b)))
    print('  四變體（Adam/Eve）靠「尖 vs 圓」區分 —— 曲率門檻，本質是參數，未編碼。')

    # ---------------- P21 ascending channel -------------------------------
    print()
    print('=' * 82)
    print(' ★ P21 上升通道 —— 唯一的單調類，用來檢驗 08-28 那條規則')
    print('=' * 82)
    f6 = []
    for s in range(len(piv) - 5):
        w = piv[s:s + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        f6.append((hs, ls, [x[0] for x in w]))
    T6 = len(f6)
    rise = lambda a: a[0] < a[1] < a[2]
    fall = lambda a: a[0] > a[1] > a[2]
    up = [f for f in f6 if rise([H[i] for i in f[0]]) and rise([L[i] for i in f[1]])]
    dn = [f for f in f6 if fall([H[i] for i in f[0]]) and fall([L[i] for i in f[1]])]
    print('  母集（高遞增 ＋ 低遞增） %s 個   獨立性倍率 2.08x   <-- 已測，單調類'
          % format(len(up), ','))
    print('  下降通道母集（對照）      %s 個   倍率 2.12x' % format(len(dn), ','))
    print()
    print('  通道 = 母集 ＋ 兩條線平行。平行的代價：')
    print('  %-18s %10s %10s %12s' % ('|升幅差|容差', '上升通道', '下降通道', '代價'))
    for t in (0, 1, 2, 5, 10):
        a = sum(1 for f in up
                if abs((H[f[0][2]] - H[f[0][0]]) - (L[f[1][2]] - L[f[1][0]])) <= t)
        b = sum(1 for f in dn
                if abs((H[f[0][2]] - H[f[0][0]]) - (L[f[1][2]] - L[f[1][0]])) <= t)
        print('  %-18s %10s %10s %12s'
              % ('完全平行' if t == 0 else '%d 點以內' % t,
                 format(a, ','), format(b, ','),
                 '零參數' if t == 0 else '引進自由參數'))
    par = [f for f in up
           if (H[f[0][2]] - H[f[0][0]]) == (L[f[1][2]] - L[f[1][0]])]
    rep(rows, 'P21 上升通道（完全平行）', [f[2] for f in par], T6, N)

    # ---------------- P57 measured move down ------------------------------
    print()
    print('=' * 82)
    print(' P57 測量移動（下） —— 兩段跌幅完全相等')
    print('=' * 82)
    md = [f for f in f5t
          if H[f[2]] < H[f[0]] and L[f[3]] < L[f[1]]
          and (H[f[0]] - L[f[1]]) == (H[f[2]] - L[f[3]])]
    mu = [f for f in f5b
          if L[f[2]] > L[f[0]] and H[f[3]] > H[f[1]]
          and (H[f[1]] - L[f[0]]) == (H[f[3]] - L[f[2]])]
    rep(rows, 'P57 測量移動下（等長）', md, len(f5t), N)
    rep(rows, '測量移動上（鏡像對照）', mu, len(f5b), N)
    print()
    print('  %-18s %10s %10s %12s' % ('兩段差容差', '下降', '上升（對照）', '代價'))
    for t in (0, 1, 2, 5, 10):
        a = sum(1 for f in f5t if H[f[2]] < H[f[0]] and L[f[3]] < L[f[1]]
                and abs((H[f[0]] - L[f[1]]) - (H[f[2]] - L[f[3]])) <= t)
        b = sum(1 for f in f5b if L[f[2]] > L[f[0]] and H[f[3]] > H[f[1]]
                and abs((H[f[1]] - L[f[0]]) - (H[f[3]] - L[f[2]])) <= t)
        print('  %-18s %10s %10s %12s'
              % ('完全相等' if t == 0 else '%d 點以內' % t,
                 format(a, ','), format(b, ','),
                 '零參數' if t == 0 else '引進自由參數'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
