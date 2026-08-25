# -*- coding: utf-8 -*-
"""S1 two-scale robustness -- what does requiring window 2 actually COST?

Ruling 5 (2026-08-25) picked S1: the same pattern must hold on window-1 AND
window-2 pivots. That has stood as a DESIGN claim with no number attached.
Before a line of it reaches the .pla, the cost has to be on the table, because
the answer decides whether S1 is cheap insurance or a pattern-killer.

  window 1   H[i] > H[i-1]  and  H[i] > H[i+1]
  window 2   window 1  AND  H[i] > H[i-2]  and  H[i] > H[i+2]

Window 2 is strictly stronger, so its pivots are a SUBSET of window 1's --
which means "hold at both" reduces to "hold at window 2". Worth stating,
because it makes the rule simpler than it reads.

Two readings are measured, since the spec sentence admits both:
  A  filter -- keep the 172 window-1 patterns whose six pivots are ALSO
     window-2 pivots
  B  re-detect -- run the whole symmetric scan on window-2 pivots from
     scratch, then see how much A and B overlap

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

    def pivots(win):
        """win=1 or 2. i-win .. i+win must all sit in the same session."""
        ph, pl = [], []
        for i in range(win, N - win):
            if S[i] < win + 1:
                continue
            if any(S[t] == 1 for t in range(i - win + 1, i + win + 1)):
                continue
            if all(H[i] > H[i + d] for d in range(-win, win + 1) if d):
                ph.append(i)
            if all(L[i] < L[i + d] for d in range(-win, win + 1) if d):
                pl.append(i)
        return ph, pl

    PH1, PL1 = pivots(1)
    PH2, PL2 = pivots(2)
    print('樞紐數')
    print('  視窗 1   高 %6d   低 %6d   合計 %6d  (%.2f%% of bars)'
          % (len(PH1), len(PL1), len(PH1) + len(PL1),
             100.0 * (len(PH1) + len(PL1)) / N))
    print('  視窗 2   高 %6d   低 %6d   合計 %6d  (%.2f%%)  存活 %.1f%%'
          % (len(PH2), len(PL2), len(PH2) + len(PL2),
             100.0 * (len(PH2) + len(PL2)) / N,
             100.0 * (len(PH2) + len(PL2)) / (len(PH1) + len(PL1))))
    sub = set(PH2) <= set(PH1) and set(PL2) <= set(PL1)
    print('  視窗 2 是視窗 1 的子集：%s  -> 「兩個都成立」等於「視窗 2 成立」'
          % ('是' if sub else '否'))

    def scan(ph, pl):
        piv = sorted([(i, 'H') for i in ph] + [(i, 'L') for i in pl])
        out = []
        for k in range(len(piv) - 5):
            w = piv[k:k + 6]
            if any(w[j][1] == w[j + 1][1] for j in range(5)):
                continue
            ix = [x[0] for x in w]
            if any(S[t] == 1 for t in range(ix[0] + 1, ix[-1] + 1)):
                continue
            hs = [x[0] for x in w if x[1] == 'H']
            ls = [x[0] for x in w if x[1] == 'L']
            if not (H[hs[0]] < H[hs[1]] < H[hs[2]]):
                continue
            if not (L[ls[0]] > L[ls[1]] > L[ls[2]]):
                continue
            if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
                continue
            out.append((w[0][1], hs, ls, ix))
        return out

    A_all = scan(PH1, PL1)
    B_all = scan(PH2, PL2)
    s2 = set(PH2) | set(PL2)
    A_pass = [x for x in A_all if all(i in s2 for i in x[3])]

    print()
    print('=' * 76)
    print(' 讀法 A：把 172 個拿去過濾，六個樞紐必須也是視窗 2 樞紐')
    print('=' * 76)
    print('  視窗 1 偵測到     %d' % len(A_all))
    print('  六樞紐全數通過視窗 2  %d   存活 %.1f%%'
          % (len(A_pass), 100.0 * len(A_pass) / len(A_all)))
    cnt = collections.Counter()
    for x in A_all:
        cnt[sum(1 for i in x[3] if i in s2)] += 1
    print('  通過幾個樞紐的分布：' + '  '.join('%d個:%d' % (k, cnt[k])
                                          for k in sorted(cnt)))

    print()
    print('=' * 76)
    print(' 讀法 B：直接用視窗 2 樞紐重跑整套偵測')
    print('=' * 76)
    print('  視窗 2 偵測到     %d' % len(B_all))
    ka = set(tuple(x[3]) for x in A_pass)
    kb = set(tuple(x[3]) for x in B_all)
    print('  A 與 B 完全相同的型態  %d' % len(ka & kb))
    print('  只在 A 出現 %d   只在 B 出現 %d' % (len(ka - kb), len(kb - ka)))

    print()
    print('=' * 76)
    print(' 讀法 B 的樣貌（n = %d）' % len(B_all))
    print('=' * 76)
    spb = sorted(x[3][-1] - x[3][0] for x in B_all)
    yrb = collections.Counter(Y[x[3][0]][:4] for x in B_all)
    print('  跨度 中位數 %d 根   最短 %d   最長 %d' % (spb[len(spb) // 2], spb[0], spb[-1]))
    print('  逐年 ' + '  '.join('%s:%d' % (y, yrb.get(y, 0))
                               for y in sorted(set(Y[i][:4] for i in range(0, N, 5000)))))
    print('  年均 %.1f 個' % (len(B_all) / 7.64))

    keep = A_pass if A_pass else B_all
    if keep:
        sp = sorted(x[3][-1] - x[3][0] for x in keep)
        yr = collections.Counter(Y[x[3][0]][:4] for x in keep)
        c = collections.Counter(x[0] for x in keep)
        print()
        print('=' * 76)
        print(' 通過 S1 者的樣貌（讀法 A，n = %d）' % len(keep))
        print('=' * 76)
        print('  跨度 中位數 %d 根   最短 %d   最長 %d' % (sp[len(sp) // 2], sp[0], sp[-1]))
        print('  排列 先出現高 %d   先出現低 %d' % (c['H'], c['L']))
        print('  逐年 ' + '  '.join('%s:%d' % (y, yr[y]) for y in sorted(yr)))
        print('  年均 %.1f 個' % (len(keep) / 7.64))
    return 0


if __name__ == '__main__':
    sys.exit(main())
