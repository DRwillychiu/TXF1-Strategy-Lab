# -*- coding: utf-8 -*-
"""Chart-pattern sweep, wave 2 -- the families the first 32 missed.

The first pass (s16s_chart_pattern_census.py) covered the Edwards-and-Magee
shapes: triangles, wedges, channels, flags, double tops. Re-reading the
literature end to end turns up whole families that pass was blind to, and one
of them -- MARKET STRUCTURE -- is the only family that can be written with
ZERO free parameters using the fractal pivot the first pass already built.

  upthrust / spring     sweep a swing extreme, close back inside
  break of structure    close beyond a swing extreme and stay
  change of character   the first structural break against the prior swing run
  three falling peaks   three consecutive descending pivot highs
  wide range            the mirror of NR4/NR7
  key reversal          a new extreme that closes beyond the prior bar's other side
  prior-session break   take out the previous session's extreme
  horn / pipe           twin spikes, one bar apart or adjacent

Same discipline as wave 1: counts and a powered screen on the 7,703 death
crosses, no P&L column, Bonferroni across everything tested.
"""
import io, os, sys, csv, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
CACHE = os.path.join(HERE, 's16s_5min.csv')
HZ = 12


def main():
    rows = list(csv.DictReader(open(CACHE, encoding='utf-8')))
    O = [float(r['open']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    F = [float(r['zlema_f']) for r in rows]
    W = [float(r['zlema_s']) for r in rows]
    MIN = [int(r['hhmm'][:2]) * 60 + int(r['hhmm'][2:]) for r in rows]
    YMD = [r['ymd'] for r in rows]
    N = len(rows)
    R = [H[i] - L[i] for i in range(N)]
    UP = [H[i] - max(O[i], C[i]) for i in range(N)]     # upper shadow
    DN = [min(O[i], C[i]) - L[i] for i in range(N)]
    BD = [abs(C[i] - O[i]) for i in range(N)]
    print('bars %d   %s -> %s' % (N, YMD[0], YMD[-1]))

    # ---- fractal pivots, confirmed one bar late (no look-ahead) ----
    PH = [i for i in range(1, N - 1) if S[i] >= 2 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1) if S[i] >= 2 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    lastH = [None] * N       # (i2, i1) = the two most recent CONFIRMED pivot highs
    lastL = [None] * N
    hs, ls, hp, lp = [], [], 0, 0
    for i in range(N):
        while hp < len(PH) and PH[hp] + 1 <= i:
            hs.append(PH[hp]); hp += 1
        while lp < len(PL) and PL[lp] + 1 <= i:
            ls.append(PL[lp]); lp += 1
        lastH[i] = tuple(hs[-3:])
        lastL[i] = tuple(ls[-3:])

    # ---- previous session extremes ----
    sess_lo, sess_hi = [None] * N, [None] * N
    plo = phi = None
    clo = chi = None
    for i in range(N):
        if S[i] == 1:
            plo, phi = clo, chi
            clo, chi = L[i], H[i]
        else:
            if clo is not None:
                clo = min(clo, L[i]); chi = max(chi, H[i])
        sess_lo[i], sess_hi[i] = plo, phi

    P = {}

    def mark(name, need, fn):
        P[name] = [i for i in range(need, N - 1) if S[i] >= need and fn(i)]

    def h1(i):
        return lastH[i][-1] if lastH[i] else None

    def l1(i):
        return lastL[i][-1] if lastL[i] else None

    # ---------- market structure: zero free parameters ----------
    def upthrust(i):
        p = h1(i)
        return p is not None and H[i] > H[p] and C[i] < H[p]

    def spring(i):
        p = l1(i)
        return p is not None and L[i] < L[p] and C[i] > L[p]

    def bos_dn(i):
        p = l1(i)
        return p is not None and C[i] < L[p]

    def bos_up(i):
        p = h1(i)
        return p is not None and C[i] > H[p]

    def choch_dn(i):
        a, b = lastH[i], lastL[i]
        if len(a) < 2 or len(b) < 1:
            return False
        # prior swing run was UP (last two pivot highs ascending), and price
        # now closes below the most recent pivot low -- the first break against
        return H[a[-1]] > H[a[-2]] and C[i] < L[b[-1]]

    def choch_up(i):
        a, b = lastL[i], lastH[i]
        if len(a) < 2 or len(b) < 1:
            return False
        return L[a[-1]] < L[a[-2]] and C[i] > H[b[-1]]

    mark('P33 上衝回落 Upthrust        空', 4, upthrust)
    mark('P34 彈簧 Spring             多', 4, spring)
    mark('P35 結構破壞 BOS 向下        空', 4, bos_dn)
    mark('P36 結構破壞 BOS 向上        多', 4, bos_up)
    mark('P37 性格轉變 CHoCH 向下      空', 6, choch_dn)
    mark('P38 性格轉變 CHoCH 向上      多', 6, choch_up)
    mark('P39 三下降峰                空', 8,
         lambda i: len(lastH[i]) == 3 and H[lastH[i][0]] > H[lastH[i][1]] > H[lastH[i][2]])
    mark('P40 三上升谷                多', 8,
         lambda i: len(lastL[i]) == 3 and L[lastL[i][0]] < L[lastL[i][1]] < L[lastL[i][2]])

    # ---------- volatility expansion: the mirror of NR ----------
    mark('P41 WR4 最近 4 根最寬        中性', 4,
         lambda i: R[i] == max(R[i - 3:i + 1]) and R[i] > max(R[i - 3:i]))
    mark('P42 WR7 最近 7 根最寬        中性', 7,
         lambda i: R[i] == max(R[i - 6:i + 1]) and R[i] > max(R[i - 6:i]))

    # ---------- single-bar reversal geometry (2 bars, so allowed) ----------
    mark('P43 關鍵反轉 Key Reversal    空', 2,
         lambda i: H[i] > H[i - 1] and C[i] < C[i - 1] and C[i] < L[i - 1])
    mark('P44 關鍵反轉 Key Reversal    多', 2,
         lambda i: L[i] < L[i - 1] and C[i] > C[i - 1] and C[i] > H[i - 1])

    # ---------- prior-session extremes ----------
    mark('P45 破前時段低              空', 2,
         lambda i: sess_lo[i] is not None and L[i] < sess_lo[i] <= L[i - 1])
    mark('P46 破前時段高              多', 2,
         lambda i: sess_hi[i] is not None and H[i] > sess_hi[i] >= H[i - 1])

    # ---------- twin spikes ----------
    def horn_top(i):
        # two pivot highs exactly two bars apart, both with a dominant upper shadow
        a = lastH[i]
        if len(a) < 2 or a[-1] - a[-2] != 2:
            return False
        return all(UP[k] >= BD[k] and UP[k] >= DN[k] for k in (a[-1], a[-2]))

    def pipe_top(i):
        # two ADJACENT bars, both dominated by upper shadow, both above neighbours
        if i < 3:
            return False
        a, b = i - 1, i
        return (UP[a] >= 2 * BD[a] and UP[b] >= 2 * BD[b]
                and H[a] > H[a - 1] and H[b] > H[i + 1] if i + 1 < N else False)

    mark('P47 號角頂 Horn Top         空', 6, horn_top)
    mark('P48 管狀頂 Pipe Top         空', 5, pipe_top)

    # ---------------------------------------------------------------
    THR = 0.050
    sig = []
    for i in range(5, N):
        if S[i] < 2 or C[i] == 0:
            continue
        if not (F[i] < W[i] and F[i - 1] >= W[i - 1]):
            continue
        el = MIN[i] - MIN[i - 1]
        if el <= 0:
            el += 1440
        if ((C[i - 1] - C[i]) / C[i] * 100.0) / el > THR:
            sig.append(i)
    SIG = set(sig)
    dxi = [i for i in range(5, N - HZ)
           if S[i] >= 2 and F[i] < W[i] and F[i - 1] >= W[i - 1]]
    fwd = dict((i, C[i] - C[i + HZ]) for i in dxi)
    isera = dict((i, YMD[i] < '20240101') for i in dxi)
    allv = [fwd[i] for i in dxi]
    mu = sum(allv) / len(allv)
    sd = (sum((x - mu) ** 2 for x in allv) / (len(allv) - 1)) ** 0.5

    print('death crosses %d   slope survivors %d' % (len(dxi), len(sig)))
    print()
    print('=' * 100)
    print(' 第二波：%d 個新型態' % len(P))
    print('=' * 100)
    print('%-30s %10s %8s %9s %10s %9s %8s %16s'
          % ('型態', '次數', '佔比', '訊號棒上', '有型態', '無型態', 't', '2024前→後'))
    print('-' * 100)
    res = []
    for k in sorted(P):
        st = set(P[k])
        a = [fwd[i] for i in dxi if i in st]
        b = [fwd[i] for i in dxi if i not in st]
        on = sum(1 for i in P[k] if i in SIG)
        if len(a) < 30:
            print('%-30s %10s %7.2f%% %9d   樣本不足 (%d)'
                  % (k, format(len(P[k]), ','), 100.0 * len(P[k]) / N, on, len(a)))
            continue
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
        vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
        se = (va / len(a) + vb / len(b)) ** 0.5
        t = (ma - mb) / se if se else 0.0
        ai = [fwd[i] for i in dxi if i in st and isera[i]]
        ao = [fwd[i] for i in dxi if i in st and not isera[i]]
        era = ('%+.1f -> %+.1f' % (sum(ai) / len(ai), sum(ao) / len(ao))
               if len(ai) >= 30 and len(ao) >= 30 else '-')
        res.append((k, len(a), ma, mb, t, on))
        print('%-30s %10s %7.2f%% %9d %+9.2f %+9.2f %+7.2f %16s'
              % (k, format(len(P[k]), ','), 100.0 * len(P[k]) / N, on, ma, mb, t, era))

    def z_for(pp):
        lo, hi = 0.0, 8.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if math.erfc(mid / math.sqrt(2)) > pp:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    m = len(res)
    total = m + 17                                    # wave 1 tested 17
    thr = z_for(0.05 / total)
    print()
    print('  母體平均 %+.2f 點  sd %.2f' % (mu, sd))
    print('  本波 %d 檢定，累計 %d 檢定 -> Bonferroni 門檻 |t| > %.2f' % (m, total, thr))
    win = [r for r in res if abs(r[4]) > thr]
    print('  過 Bonferroni：%s' % (', '.join(r[0].split()[0] for r in win) or '無'))
    win2 = [r for r in res if abs(r[4]) > 1.96]
    print('  過未校正 1.96：%s' % (', '.join('%s (t=%+.2f)' % (r[0].split()[0], r[4])
                                             for r in win2) or '無'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
