# -*- coding: utf-8 -*-
"""Shared gap layer for P31 / P62 / P67, measured before any ruling is drafted.

Checklist section G: one script computes the layer, the rest read its JSON.
Three patterns share a single gap detector, which is why this group was put
first -- the marginal cost of the second and third is close to zero.

Checklist discipline 1: measure, then speak.  Nothing here is a
recommendation; every number below exists so the rulings have evidence.

The zero-parameter gap:

    up    Low[t]  > High[t-1]
    down  High[t] < Low[t-1]

Strict inequality, no minimum size.  A minimum would be the first swept
threshold in this project.

The question that decides the population is SESSION.  TXF1 runs 08:45-13:45
and 15:00-05:00, so the first bar of every session sits against a 75-minute or
3h45m break.  Those boundaries produce a price gap almost mechanically, and
there are roughly two of them every trading day.  Whether they count is the
gap layer's version of checklist question 3, and it is measured here rather
than assumed.

Counts only.  No P&L column.
"""
import io, os, sys, csv, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def pct(v, q):
    v = sorted(v)
    return v[min(int(len(v) * q), len(v) - 1)] if v else 0


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    print('母體 %s 根   %s ~ %s\n' % (format(N, ','), rows[0]['ymd'], rows[-1]['ymd']))

    # ---- 1. gaps, split by whether they sit on a session boundary ----------
    up, dn = [], []
    for t in range(1, N):
        if L[t] > H[t - 1]:
            up.append((t, L[t] - H[t - 1], S[t] == 1))
        elif H[t] < L[t - 1]:
            dn.append((t, L[t - 1] - H[t], S[t] == 1))

    print('=' * 78)
    print(' 1. 缺口母體 —— 時段邊界是不是缺口，這題決定一切')
    print('=' * 78)
    print('  %-16s %10s %10s %10s' % ('', '合計', '時段內', '時段首根'))
    print('  ' + '-' * 50)
    for nm, g in (('向上跳空', up), ('向下跳空', dn)):
        b = sum(1 for _, _, o in g if o)
        print('  %-16s %10s %10s %10s' % (nm, format(len(g), ','),
                                          format(len(g) - b, ','), format(b, ',')))
    allg = up + dn
    nb = sum(1 for _, _, o in allg if o)
    print('  %-16s %10s %10s %10s' % ('合計', format(len(allg), ','),
                                      format(len(allg) - nb, ','), format(nb, ',')))
    days = len({r['ymd'] for r in rows})
    print()
    print('  交易日 %s 天 -> 時段首根缺口 %.2f 個/天（結構性，幾乎每個時段都有）'
          % (format(days, ','), nb / float(days)))
    print('  時段內缺口 %s 個 -> 每 %.0f 根出現一次'
          % (format(len(allg) - nb, ','), N / float(max(len(allg) - nb, 1))))

    # ---- 2. size, to show a minimum threshold would be a knob --------------
    print()
    print('=' * 78)
    print(' 2. 缺口大小（點）—— 「最小幅度」會是自由參數，這裡只呈現分布')
    print('=' * 78)
    for nm, sel in (('時段內', [g[1] for g in allg if not g[2]]),
                    ('時段首根', [g[1] for g in allg if g[2]])):
        if not sel:
            continue
        print('  %-10s n=%-8s 中位 %5.0f   90%% %5.0f   99%% %6.0f   最大 %6.0f'
              % (nm, format(len(sel), ','), pct(sel, .5), pct(sel, .9),
                 pct(sel, .99), max(sel)))
    ties = sum(1 for t in range(1, N) if L[t] == H[t - 1] or H[t] == L[t - 1])
    print('  （嚴格不等式，剛好相等 %s 次不算缺口）' % format(ties, ','))

    # ---- 3. fill horizon: P67's four-way split needs one, and it is a knob -
    print()
    print('=' * 78)
    print(' 3. ★ 回補率 —— P67 四分類的難題就在這裡')
    print('=' * 78)
    intra = [g for g in allg if not g[2]]
    print('  時段內缺口 %s 個。回補 = 之後某根 K 棒觸及缺口的另一端。' % format(len(intra), ','))
    print('  %-14s %10s %8s' % ('視窗（根）', '已回補', '比率'))
    print('  ' + '-' * 36)
    for w in (5, 10, 20, 50, 100, 500):
        f = 0
        for t, _, _ in intra:
            lo, hi = min(H[t - 1], L[t]), max(H[t - 1], L[t])
            e = min(t + w, N - 1)
            if any(L[u] <= lo and H[u] >= lo for u in range(t, e + 1)) or \
               any(H[u] >= hi and L[u] <= hi for u in range(t, e + 1)):
                f += 1
        print('  %-14s %10s %7.1f%%' % (w, format(f, ','), 100.0 * f / len(intra)))
    print()
    print('  提醒：Common / Breakaway / Runaway / Exhaustion 的傳統分法依賴')
    print('  「多快被回補」與「在趨勢的哪個階段」。兩者都是門檻。上表是給裁示依據。')

    # ---- 4. islands -------------------------------------------------------
    print()
    print('=' * 78)
    print(' 4. 島狀型態 —— P31 島狀反轉 / P62 島狀底')
    print('=' * 78)
    upset = {t for t, _, o in up if not o}
    dnset = {t for t, _, o in dn if not o}

    def islands(entry, exitset, want_top):
        """entry gaps in, exitset gaps out the other way, island fully isolated."""
        out = []
        for a in sorted(entry):
            for b in range(a + 1, min(a + 60, N)):
                if b in exitset:
                    body = range(a, b)
                    if want_top:
                        ok = (min(L[u] for u in body) > max(H[a - 1], H[b]))
                    else:
                        ok = (max(H[u] for u in body) < min(L[a - 1], L[b]))
                    if ok:
                        out.append((a, b, b - a))
                    break
                if S[b] == 1:
                    break               # a session boundary is not a gap out
        return out

    tops = islands(upset, dnset, True)      # gap UP in, gap DOWN out  -> top
    bots = islands(dnset, upset, False)     # gap DOWN in, gap UP out  -> bottom
    print('  %-22s %8s %10s %10s %10s'
          % ('', '個數', '年均', '島長中位', '島長最大'))
    print('  ' + '-' * 64)
    for nm, g in (('島狀頂（先上後下）', tops), ('島狀底（先下後上）', bots)):
        if not g:
            print('  %-22s %8d' % (nm, 0))
            continue
        ln = [x[2] for x in g]
        print('  %-22s %8s %10.1f %10d %10d'
              % (nm, format(len(g), ','), len(g) / 7.64, pct(ln, .5), max(ln)))
    tot = len(tops) + len(bots)
    if tot:
        print('  合計 %s 個 -> 每 %.0f 根出現一次' % (format(tot, ','), N / float(tot)))
    yr = collections.Counter(rows[a]['ymd'][:4] for a, _, _ in tops + bots)
    if yr:
        print('  逐年  %s' % '  '.join('%s=%d' % (y, yr[y]) for y in sorted(yr)))

    # ---- 5. hand the layer on --------------------------------------------
    out = dict(
        bars=N,
        up=[[t, round(d, 1), o] for t, d, o in up],
        dn=[[t, round(d, 1), o] for t, d, o in dn],
        island_top=tops, island_bot=bots,
    )
    p = os.path.join(HERE, 's16s_gaps.json')
    json.dump(out, open(p, 'w', encoding='utf-8'))
    print()
    print('  共用資料層 -> %s（其餘腳本只讀這個，不重算）' % p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
