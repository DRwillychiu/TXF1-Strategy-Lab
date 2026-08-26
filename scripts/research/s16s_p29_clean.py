# -*- coding: utf-8 -*-
"""P29 measured on the CLEAN definition, and symmetrically.

Two defects found on 2026-08-25, both by drawing the thing:

  A. Sec 2 never required the six pivots to ALTERNATE in time, nor the lows to
     sit below the highs. Nine in ten hits under the old wording were shapes
     whose two trendlines cross -- not broadenings at all.

  B. The detector anchored on "the three most recent pivot HIGHS, then the
     three most recent lows before PH1". Every low therefore preceded the last
     high, so it could only ever return patterns that END on a pivot high.
     Patterns ending on a pivot low were invisible. Found because the user
     asked what happens when PL3 comes first.

This walks the merged pivot series and takes ANY six consecutive alternating
pivots, so both orderings are reachable and neither is privileged. No zigzag
reduction rule is used -- windows that do not alternate are simply skipped,
which needs no parameter.

Counts only. No P&L column.
"""
import io, os, sys, csv, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    O = [float(r['open']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    Y = [r['ymd'] for r in rows]
    N = len(rows)
    print('母體 %d 根   %s ~ %s' % (N, Y[0], Y[-1]))

    # ---- S1 window-2 pivots, for the robustness SCORE (ruling D) ----
    # Not a filter. Every pattern keeps a 0-6 count of how many of its six
    # pivots also survive the wider neighbourhood. Filtering on it would cost
    # 90% of the population and empty out three whole years; recording it
    # costs nothing and leaves the threshold decision for later, on evidence.
    def piv2(hi_lo, cmp2):
        out = []
        for i in range(2, N - 2):
            if S[i] < 3 or any(S[t] == 1 for t in range(i - 1, i + 3)):
                continue
            if all(cmp2(hi_lo[i], hi_lo[i + d]) for d in (-2, -1, 1, 2)):
                out.append(i)
        return out
    W2 = set(piv2(H, lambda a, b: a > b)) | set(piv2(L, lambda a, b: a < b))

    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    print('樞紐 %d 高 / %d 低' % (len(PH), len(PL)))

    # merged, sorted by time. a bar can only be one or the other here.
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])
    print('合併後 %d 個樞紐' % len(piv))

    hits = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue                                  # must alternate
        idx = [x[0] for x in w]
        a, b = idx[0], idx[-1]
        # 2026-08-26 RULING: chart patterns MAY span a session gap. Only the
        # PIVOT test is adjacency-dependent (i-1/i/i+1 must share a session,
        # enforced above); assembling six pivots into a shape is swing
        # geometry and a 75-minute gap does not break it. The old
        # one-session-only line applied the K-bar rule to a chart pattern and
        # discarded 30 of 202 -- 20 of them starting in the 04:00 hour, which
        # is why that hour was empty in the coverage table.
        n_gaps = sum(1 for t in range(a + 1, b + 1) if S[t] == 1)
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (H[hs[0]] < H[hs[1]] < H[hs[2]]):
            continue                                  # highs rising
        if not (L[ls[0]] > L[ls[1]] > L[ls[2]]):
            continue                                  # lows falling
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue                                  # lows below highs
        kind = 'H_first' if w[0][1] == 'H' else 'L_first'
        mid_old = (H[hs[0]] + L[ls[0]]) / 2.0
        mid_new = (H[hs[2]] + L[ls[2]]) / 2.0
        drift = mid_new - mid_old
        s1 = sum(1 for t in idx if t in W2)          # 0-6 robustness score
        su = (H[hs[2]] - H[hs[0]]) / float(hs[2] - hs[0])
        sl = (L[ls[2]] - L[ls[0]]) / float(ls[2] - ls[0])
        m2 = (su + sl) / 2.0                          # adopted direction measure
        hits.append(dict(k=kind, a=a, b=b, span=b - a, drift=drift, s1=s1, m2=m2, gaps=n_gaps,
                         hs=hs, ls=ls, last=w[-1][1],
                         ymd=Y[a], sess='day' if 845 <= int(rows[a]['hhmm']) <= 1345 else 'night'))

    print()
    print('=' * 78)
    print(' 1. 兩種排列順序 —— 用戶 2026-08-25 提問')
    print('=' * 78)
    c = collections.Counter(x['k'] for x in hits)
    tot = len(hits)
    print('  總計 %d 個乾淨 P29' % tot)
    print('  %-10s %5d  %5.1f%%   序列 H L H L H L，**以樞紐低收尾**'
          % ('先出現高', c['H_first'], 100.0 * c['H_first'] / max(tot, 1)))
    print('  %-10s %5d  %5.1f%%   序列 L H L H L H，**以樞紐高收尾**'
          % ('先出現低', c['L_first'], 100.0 * c['L_first'] / max(tot, 1)))
    print()
    print('  ⚠️ 舊偵測只錨定「最近三個樞紐高」，低點一律取在 PH1 之前，')
    print('     因此只找得到以樞紐高收尾者 —— 先出現高的那 %d 個被系統性漏掉。'
          % c['H_first'])

    print()
    print('=' * 78)
    print(' 2. 三向細分 —— 重新量在乾淨定義上')
    print('=' * 78)
    for lab, sub in (('全部', hits),
                     ('先出現高', [x for x in hits if x['k'] == 'H_first']),
                     ('先出現低', [x for x in hits if x['k'] == 'L_first'])):
        n = len(sub)
        if not n:
            continue
        up = sum(1 for x in sub if x['drift'] > 0)
        dn = sum(1 for x in sub if x['drift'] < 0)
        fl = n - up - dn
        print('  %-8s n=%4d   上升 %5.1f%%   下降 %5.1f%%   水平 %4.1f%%'
              % (lab, n, 100.0 * up / n, 100.0 * dn / n, 100.0 * fl / n))
    print()
    print('  對照：舊定義（未要求交替）報 上升 47.1% / 下降 50.4% / 水平 2.5%')

    print()
    print('=' * 78)
    print(' 3. 分布')
    print('=' * 78)
    sp = sorted(x['span'] for x in hits)
    print('  跨度  中位數 %d 根   最短 %d   最長 %d' % (sp[len(sp) // 2], sp[0], sp[-1]))
    yr = collections.Counter(x['ymd'][:4] for x in hits)
    print('  逐年  ' + '  '.join('%s:%d' % (y, yr[y]) for y in sorted(yr)))
    ss = collections.Counter(x['sess'] for x in hits)
    print('  時段  日盤 %d   夜盤 %d' % (ss['day'], ss['night']))
    print('  年均  %.1f 個' % (tot / 7.64))

    print()
    print('=' * 78)
    print(' 4. 六格分類（裁示：M2 兩線斜率平均 ＋ 排列攤開）')
    print('=' * 78)
    print('  %-22s %5s %8s %8s %8s' % ('排列', 'n', '上升', '下降', '水平'))
    for lab, kk in (('先出現高（以低收尾）', 'H_first'), ('先出現低（以高收尾）', 'L_first')):
        sub = [x for x in hits if x['k'] == kk]
        n = len(sub)
        u = sum(1 for x in sub if x['m2'] > 1e-9)
        d = sum(1 for x in sub if x['m2'] < -1e-9)
        print('  %-22s %5d %7.1f%% %7.1f%% %7.1f%%'
              % (lab, n, 100.0 * u / n, 100.0 * d / n, 100.0 * (n - u - d) / n))
    u = sum(1 for x in hits if x['m2'] > 1e-9)
    d = sum(1 for x in hits if x['m2'] < -1e-9)
    print('  %-22s %5d %7.1f%% %7.1f%% %7.1f%%'
          % ('合計', tot, 100.0 * u / tot, 100.0 * d / tot, 100.0 * (tot - u - d) / tot))

    print()
    print('=' * 78)
    print(' 5. S1 穩健度分數（裁示 D：屬性，不是濾網）')
    print('=' * 78)
    sc = collections.Counter(x['s1'] for x in hits)
    for k in range(7):
        n = sc.get(k, 0)
        bar = '#' * int(round(40.0 * n / max(sc.values())))
        print('  %d / 6 個樞紐通過視窗 2   %4d  %5.1f%%  %s'
              % (k, n, 100.0 * n / tot, bar))
    print('  平均 %.2f / 6' % (sum(x['s1'] for x in hits) / float(tot)))

    json.dump([dict(k=x['k'], a=x['a'], b=x['b'], span=x['span'], drift=x['drift'], gaps=x['gaps'],
                    s1=x['s1'], m2=x['m2'], hs=x['hs'], ls=x['ls'], ymd=x['ymd'])
               for x in hits],
              open(os.path.join(HERE, 's16s_p29_clean.json'), 'w', encoding='utf-8'))
    print()
    print('  wrote s16s_p29_clean.json  (%d 筆)' % tot)
    return 0


if __name__ == '__main__':
    sys.exit(main())
