# -*- coding: utf-8 -*-
"""Willy's band device: relax "exactly equal" without spending a parameter.

Rulings of 2026-08-28:

  P18 / P23  "不需要完全等於，可以是相似 ... 讓 PH1、PH2 先定義出區間，
              然後找 PH3 的位置"
  P21        "(PH3-PH1) = (PL3-PL1) 這件事應該當作是相似平行才對"

The P18 device is zero-parameter and I should say why rather than assume it.
The tolerance is |PH1 - PH2|, taken from the pattern itself, so nothing is
imported from outside -- it is the third knob-killing device this project
uses, derive it from something already fixed.  It is also causally ordered:
the first two peaks establish the zone, the third tests it, and nothing looks
ahead.

But it has a property worth measuring before adopting: the band WIDENS as the
first two peaks disagree.  Two peaks 50 points apart license a 50-point zone.
That may be right -- a resistance zone genuinely is that wide -- or it may
admit anything.  The band-width distribution answers it, not opinion.

P21 has no equivalent pair to define a band, so two self-referential
candidates are measured instead:

  C1  tolerance = the pattern's own straightness, the middle pivots'
      deviation from the straight line through the outer two
  C2  tolerance = the channel's own starting width, PH1 - PL1

Each gets the block-local control that survived three rewrites.
Counts only.  No P&L column.
"""
import io, os, sys, csv, random, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(20260828)
NP, BLK = 2000, 200
YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']


def pct(v, q):
    v = sorted(v)
    return v[min(int(len(v) * q), len(v) - 1)] if v else 0


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

    def fr(k, first):
        o = []
        for s in range(len(piv) - k + 1):
            w = piv[s:s + k]
            if any(w[j][1] == w[j + 1][1] for j in range(k - 1)):
                continue
            if w[0][1] != first:
                continue
            o.append([x[0] for x in w])
        return o

    f5t, f5b = fr(5, 'H'), fr(5, 'L')
    f6 = []
    for s in range(len(piv) - 5):
        w = piv[s:s + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        f6.append((hs, ls))

    def yr(hits, idx):
        c = collections.Counter(rows[f[idx]]['ymd'][:4] for f in hits)
        return '  '.join('%s=%d' % (y, c[y]) for y in YRS), sum(1 for y in YRS if c[y] == 0)

    def ctrl(name, vals, hit_fn):
        """vals: [(anchor_lo, anchor_hi, tested)] ; shuffle tested block-locally."""
        n = len(vals)
        obs = sum(1 for a, b, t in vals if hit_fn(a, b, t))
        T0 = [v[2] for v in vals]
        cnt = []
        for _ in range(NP):
            T = T0[:]
            for s in range(0, n, BLK):
                seg = T[s:s + BLK]
                random.shuffle(seg)
                T[s:s + BLK] = seg
            cnt.append(sum(1 for (a, b, _), t in zip(vals, T) if hit_fn(a, b, t)))
        exp = sum(cnt) / float(NP)
        p = (sum(1 for c in cnt if c >= obs) + 1) / float(NP + 1)
        print('    %-30s 觀測 %-6s 期望 %8.1f   倍率 %5.2fx   p=%.5f   %s'
              % (name, format(obs, ','), exp, obs / exp if exp else 0, p,
                 '★ 通過' if p < 0.001 and exp and obs / exp > 1.5 else '與隨機無異'))

    print('=' * 84)
    print(' 1. P18 三重頂 —— 用戶版：PH1、PH2 定義區間，PH3 落在區間內')
    print('=' * 84)
    band = [abs(H[f[0]] - H[f[2]]) for f in f5t]
    print('  區間寬度 |PH1 − PH2| 分布（點）')
    print('    中位 %.0f   75%% %.0f   90%% %.0f   99%% %.0f   最大 %.0f'
          % (pct(band, .5), pct(band, .75), pct(band, .9), pct(band, .99), max(band)))
    print('    寬度 <= 10 點者 %.1f%%   <= 30 點者 %.1f%%'
          % (100.0 * sum(1 for b in band if b <= 10) / len(band),
             100.0 * sum(1 for b in band if b <= 30) / len(band)))
    hit = [f for f in f5t
           if min(H[f[0]], H[f[2]]) <= H[f[4]] <= max(H[f[0]], H[f[2]])]
    ytxt, z = yr(hit, 0)
    print()
    print('  母體 %s 個（占框架 %.2f%%）   年均 %.1f   掛零年 %d'
          % (format(len(hit), ','), 100.0 * len(hit) / len(f5t), len(hit) / 7.64, z))
    print('  逐年 %s' % ytxt)
    print('  對照（PH3 於鄰近 200 框架內打散）：')
    ctrl('PH3 落在 [PH1, PH2] 區間內',
         [(H[f[0]], H[f[2]], H[f[4]]) for f in f5t],
         lambda a, b, t: min(a, b) <= t <= max(a, b))
    print('  對照（完全相等，供比較）：')
    ctrl('PH1 = PH2 = PH3',
         [(H[f[0]], H[f[2]], H[f[4]]) for f in f5t],
         lambda a, b, t: a == b == t)

    print()
    print('=' * 84)
    print(' 2. P23 三重底 —— 同一裝置')
    print('=' * 84)
    hitb = [f for f in f5b
            if min(L[f[0]], L[f[2]]) <= L[f[4]] <= max(L[f[0]], L[f[2]])]
    ytxt, z = yr(hitb, 0)
    print('  母體 %s 個（占框架 %.2f%%）   年均 %.1f   掛零年 %d'
          % (format(len(hitb), ','), 100.0 * len(hitb) / len(f5b), len(hitb) / 7.64, z))
    print('  逐年 %s' % ytxt)
    ctrl('PL3 落在 [PL1, PL2] 區間內',
         [(L[f[0]], L[f[2]], L[f[4]]) for f in f5b],
         lambda a, b, t: min(a, b) <= t <= max(a, b))

    print()
    print('=' * 84)
    print(' 3. P21 上升通道 —— 「相似平行」的兩個自我指涉候選')
    print('=' * 84)
    ri = lambda a: a[0] < a[1] < a[2]
    up = [(hs, ls) for hs, ls in f6
          if ri([H[i] for i in hs]) and ri([L[i] for i in ls])]
    print('  母集（高遞增 ＋ 低遞增）%s 個' % format(len(up), ','))

    def straight(hs, ls):
        """middle pivots' deviation from the straight line through the outer two"""
        du = (H[hs[2]] - H[hs[0]]) / float(hs[2] - hs[0])
        dl = (L[ls[2]] - L[ls[0]]) / float(ls[2] - ls[0])
        a = abs(H[hs[1]] - (H[hs[0]] + du * (hs[1] - hs[0])))
        b = abs(L[ls[1]] - (L[ls[0]] + dl * (ls[1] - ls[0])))
        return a + b

    rows_ = []
    for nm, tol in (('C0 完全平行（差 = 0）', lambda hs, ls: 0.0),
                    ('C1 容差 = 型態自身直度', straight),
                    ('C2 容差 = 通道起始寬度', lambda hs, ls: H[hs[0]] - L[ls[0]])):
        n = sum(1 for hs, ls in up
                if abs((H[hs[2]] - H[hs[0]]) - (L[ls[2]] - L[ls[0]])) <= tol(hs, ls))
        c = collections.Counter(rows[min(hs + ls)]['ymd'][:4] for hs, ls in up
                                if abs((H[hs[2]] - H[hs[0]]) - (L[ls[2]] - L[ls[0]]))
                                <= tol(hs, ls))
        print('  %-24s %6s 個  年均 %6.1f  占母集 %5.1f%%  掛零年 %d'
              % (nm, format(n, ','), n / 7.64, 100.0 * n / len(up),
                 sum(1 for y in YRS if c[y] == 0)))
        print('      逐年 %s' % '  '.join('%s=%d' % (y, c[y]) for y in YRS))
    d = [straight(hs, ls) for hs, ls in up]
    print('  型態自身直度分布（點）：中位 %.0f  75%% %.0f  90%% %.0f'
          % (pct(d, .5), pct(d, .75), pct(d, .9)))
    w = [H[hs[0]] - L[ls[0]] for hs, ls in up]
    print('  通道起始寬度分布（點）：中位 %.0f  75%% %.0f  90%% %.0f'
          % (pct(w, .5), pct(w, .75), pct(w, .9)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
