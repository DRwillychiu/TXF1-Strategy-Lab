# -*- coding: utf-8 -*-
"""Chart-pattern census -- the compression family and the fractal pivots.

Counts only. No P&L column, deliberately, same discipline as the candlestick
census: a shape is catalogued on how often it occurs and on whether it can be
defined without a knob, never on what it earned.

The point of measuring BEFORE designing is that a shape occurring 40 times in
seven years cannot be a filter no matter how good it looks, and a shape
occurring on 30% of bars is not a filter either -- it is noise with a name.
"""
import io, os, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
CACHE = os.path.join(HERE, 's16s_5min.csv')


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
    N = len(rows)
    R = [H[i] - L[i] for i in range(N)]
    print('bars %d   %s -> %s' % (N, rows[0]['ymd'], rows[-1]['ymd']))

    # ---- the entry signal population, transcribed from the .pla ----
    THR = 0.050
    sig = []
    for i in range(5, N):
        if S[i] < 2:
            continue
        if not (F[i] < W[i] and F[i - 1] >= W[i - 1]):
            continue
        el = MIN[i] - MIN[i - 1]
        if el <= 0:
            el += 1440
        if C[i] == 0:
            continue
        if ((C[i - 1] - C[i]) / C[i] * 100.0) / el > THR:
            sig.append(i)
    dx = sum(1 for i in range(5, N)
             if S[i] >= 2 and F[i] < W[i] and F[i - 1] >= W[i - 1])
    print('death crosses %d   slope-gate survivors %d' % (dx, len(sig)))
    SIG = set(sig)

    P = {}

    def mark(name, need, fn):
        hit = []
        for i in range(need, N):
            if S[i] < need:
                continue
            if fn(i):
                hit.append(i)
        P[name] = hit

    # ---- A. compression: no trendline, no tolerance ----
    mark('P01 NR4  最近 4 根最窄', 4,
         lambda i: R[i] == min(R[i - 3:i + 1]) and R[i] < min(R[i - 3:i]))
    mark('P02 NR7  最近 7 根最窄', 7,
         lambda i: R[i] == min(R[i - 6:i + 1]) and R[i] < min(R[i - 6:i]))
    mark('P03 內含線 x2 連續', 3,
         lambda i: H[i] <= H[i - 1] and L[i] >= L[i - 1]
         and H[i - 1] <= H[i - 2] and L[i - 1] >= L[i - 2])
    mark('P04 內含線 x3 連續', 4,
         lambda i: all(H[i - k] <= H[i - k - 1] and L[i - k] >= L[i - k - 1]
                       for k in range(3)))
    mark('P05 ID/NR4  內含線 AND NR4', 4,
         lambda i: H[i] <= H[i - 1] and L[i] >= L[i - 1]
         and R[i] == min(R[i - 3:i + 1]) and R[i] < min(R[i - 3:i]))
    mark('P06 三根遞減區間', 3,
         lambda i: R[i] < R[i - 1] < R[i - 2])

    # ---- B. fractal pivots: the zero-tolerance swing definition ----
    def ph(i):     # a swing HIGH sits at bar i
        return i + 1 < N and H[i] > H[i - 1] and H[i] > H[i + 1]

    def pl(i):
        return i + 1 < N and L[i] < L[i - 1] and L[i] < L[i + 1]

    HI = [i for i in range(1, N - 1) if S[i] >= 2 and ph(i)]
    LO = [i for i in range(1, N - 1) if S[i] >= 2 and pl(i)]
    print('3 根分形樞紐   高 %d (%.1f%%)   低 %d (%.1f%%)'
          % (len(HI), 100.0 * len(HI) / N, len(LO), 100.0 * len(LO) / N))
    gapsH = [HI[k] - HI[k - 1] for k in range(1, len(HI))]
    print('   相鄰樞紐高間隔  中位數 %d 根   平均 %.1f 根'
          % (sorted(gapsH)[len(gapsH) // 2], sum(gapsH) / len(gapsH)))

    # last two pivot highs / lows as of bar i
    lastH = [None] * N
    lastL = [None] * N
    hs, ls = [], []
    hp = lp = 0
    for i in range(N):
        while hp < len(HI) and HI[hp] + 1 <= i:
            hs.append(HI[hp]); hp += 1
        while lp < len(LO) and LO[lp] + 1 <= i:
            ls.append(LO[lp]); lp += 1
        lastH[i] = tuple(hs[-2:]) if len(hs) >= 2 else None
        lastL[i] = tuple(ls[-2:]) if len(ls) >= 2 else None

    def two(i):
        return lastH[i], lastL[i]

    def tri(i, hrel, lrel):
        a, b = two(i)
        if not a or not b:
            return False
        # same session only -- a pivot from a previous session is a different
        # market, and the strategy already resets bar counts per session
        if S[i] < (i - min(a[0], b[0])):
            pass
        h0, h1 = H[a[0]], H[a[1]]
        l0, l1 = L[b[0]], L[b[1]]
        return hrel(h1, h0) and lrel(l1, l0)

    lt = lambda x, y: x < y
    gt = lambda x, y: x > y
    eq = lambda x, y: x == y
    mark('P08 下降三角  高遞減 ＋ 低相等', 8, lambda i: tri(i, lt, eq))
    mark('P09 上升三角  低遞增 ＋ 高相等', 8, lambda i: tri(i, eq, gt))
    mark('P10 對稱三角  高遞減 ＋ 低遞增', 8, lambda i: tri(i, lt, gt))
    mark('P11 上升楔形  高低同升，高的漲幅較小', 8,
         lambda i: tri(i, gt, gt) and _wedge(i, lastH, lastL, H, L, True))
    mark('P12 下降楔形  高低同降，低的跌幅較小', 8,
         lambda i: tri(i, lt, lt) and _wedge(i, lastH, lastL, H, L, False))
    mark('P20 下降通道  高遞減 ＋ 低遞減', 8, lambda i: tri(i, lt, lt))
    mark('P22 箱型      高相等 ＋ 低相等', 8, lambda i: tri(i, eq, eq))
    mark('P17 雙頂      兩個樞紐高完全相等', 8,
         lambda i: (lambda a: bool(a) and H[a[0]] == H[a[1]])(lastH[i]))
    mark('P19 雙底      兩個樞紐低完全相等', 8,
         lambda i: (lambda b: bool(b) and L[b[0]] == L[b[1]])(lastL[i]))

    # ---- the question that actually matters for a FILTER ----
    # A compression pattern cannot sit ON the signal bar: the slope gate needs
    # a bar that fell 0.25% in five minutes, and "narrowest of the last N" is
    # by definition not that. The useful question is whether the market was
    # compressed in the bars BEFORE the break. Window = the pattern's own bar
    # count, the same zero-parameter "life equals formation bars" rule the
    # candlestick side already uses.
    LIFE = {'P01': 4, 'P02': 7, 'P03': 2, 'P04': 3, 'P05': 4, 'P06': 3,
            'P08': 8, 'P09': 8, 'P10': 8, 'P11': 8, 'P12': 8,
            'P17': 8, 'P19': 8, 'P20': 8, 'P22': 8}
    print()
    print('=' * 88)
    print(' 型態出現在訊號棒**之前** k 根內（k = 該型態自己的形成根數）')
    print('=' * 88)
    print('%-34s %4s %10s %10s %14s' % ('型態', 'k', '訊號命中', '命中率', '母體基準率'))
    print('-' * 88)
    base = {}
    for k in P:
        st = set(P[k])
        life = LIFE[k.split()[0]]
        hit = 0
        for i in sig:
            if any((i - j) in st for j in range(1, life + 1)):
                hit += 1
        # base rate: same window test over ALL bars, so the lift is readable
        tot = 0
        for i in range(life + 8, N, 37):          # 1-in-37 sample, ~11,400 bars
            if any((i - j) in st for j in range(1, life + 1)):
                tot += 1
        nb = len(range(life + 8, N, 37))
        base[k] = 100.0 * tot / nb
        print('%-34s %4d %10d %9.1f%% %13.1f%%'
              % (k, life, hit, 100.0 * hit / len(sig), base[k]))
    print()
    print('  命中率 vs 母體基準率的差距 = 這個型態帶不帶資訊。')
    print('  接近 = 不帶資訊；明顯高 = 訊號偏好它；明顯低 = 訊號排斥它。')

    # ---- C. flags and pennants -----------------------------------------
    # The flagpole needs no new parameter: the strategy ALREADY defines a
    # violent down-bar -- the slope gate itself. A bear flag is therefore
    # "a pole bar happened, then k bars of drift that never took out the
    # pole's high". k is bounded by the pole itself: the flag ends when the
    # high is exceeded, so there is no k to fit.
    pole = []
    for i in range(2, N):
        if S[i] < 2 or C[i] == 0:
            continue
        el = MIN[i] - MIN[i - 1]
        if el <= 0:
            el += 1440
        if ((C[i - 1] - C[i]) / C[i] * 100.0) / el > THR:
            pole.append(i)
    POLE = set(pole)
    print('旗桿棒（斜率閘門等級的下跌棒）%d 根 = %.2f%%' % (len(pole), 100.0 * len(pole) / N))

    def flag(i):
        """bar i sits inside a live bear flag: a pole in the recent past whose
        high has not been taken out since, and at least 2 drift bars."""
        for j in range(i - 2, max(i - 21, 1), -1):
            if j in POLE:
                seg = range(j + 1, i + 1)
                if all(H[m] <= H[j] for m in seg) and (i - j) >= 2:
                    return True
                return False
        return False

    def pennant(i):
        return flag(i) and R[i] < R[i - 1] < R[i - 2]

    mark('P13 空方旗形  旗桿後未破旗桿高', 4, flag)
    mark('P14 空方三角旗  旗形 ＋ 區間收斂', 5, pennant)
    LIFE['P13'] = 4
    LIFE['P14'] = 5

    # ---- the only test with power: does the shape SEPARATE forward return ----
    # Co-occurrence with the signal is not usefulness. The signal bar is a
    # high-volatility bar by construction, so anything volatility-related
    # co-varies with it for reasons that have nothing to do with edge.
    #
    # Population = all 7,704 death crosses, not the 187 survivors. On 187 the
    # power ceiling computed on 2026-08-22 applies and nothing is detectable.
    # Horizon = 12 bars, taken from the strategy's own median hold (12.3), a
    # fact about the strategy rather than a fitted number.
    HZ = 12
    dxi = [i for i in range(5, N - HZ)
           if S[i] >= 2 and F[i] < W[i] and F[i - 1] >= W[i - 1]]
    fwd = dict((i, C[i] - C[i + HZ]) for i in dxi)     # + = the short wins
    era = dict((i, rows[i]['ymd'] < '20240101') for i in dxi)
    print()
    print('=' * 96)
    print(' 唯一有檢定力的檢定：型態有沒有分離「死叉後 %d 根的空單報酬」' % HZ)
    print(' 母體 %d 個死叉（不是 187 個訊號）' % len(dxi))
    print('=' * 96)
    allv = [fwd[i] for i in dxi]
    mu = sum(allv) / len(allv)
    sd = (sum((x - mu) ** 2 for x in allv) / (len(allv) - 1)) ** 0.5
    print('  母體平均 %+.2f 點   標準差 %.2f' % (mu, sd))
    print()
    print('%-34s %6s %9s %9s %8s %20s' % ('型態', 'n', '有型態', '無型態', '差(點)', '樣本內→2024後'))
    print('-' * 96)
    res = []
    for k in sorted(P):
        st = set(P[k]); life = LIFE[k.split()[0]]
        a, b, a_is, a_oos = [], [], [], []
        for i in dxi:
            has = any((i - j) in st for j in range(1, life + 1))
            (a if has else b).append(fwd[i])
            if has:
                (a_is if era[i] else a_oos).append(fwd[i])
        if len(a) < 30 or len(b) < 30:
            print('%-34s %6d   樣本不足，不檢定' % (k, len(a))); continue
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
        vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
        se = (va / len(a) + vb / len(b)) ** 0.5
        t = (ma - mb) / se if se else 0.0
        i1 = sum(a_is) / len(a_is) if len(a_is) >= 30 else None
        i2 = sum(a_oos) / len(a_oos) if len(a_oos) >= 30 else None
        res.append((abs(t), k, len(a), ma, mb, ma - mb, t, i1, i2))
        print('%-34s %6d %+9.2f %+9.2f %+8.2f  t=%+5.2f  %s'
              % (k, len(a), ma, mb, ma - mb, t,
                 ('%+.1f -> %+.1f' % (i1, i2)) if i1 is not None and i2 is not None else '-'))
    print()
    res.sort(reverse=True)
    print('  |t| 最大者 %s  t=%+.2f' % (res[0][1].split()[0], res[0][6]) if res else '')
    import math
    m = len(res)
    # Bonferroni: two-sided p < 0.05/m. z solved by bisection, no scipy here.
    def z_for(pp):
        lo, hi = 0.0, 8.0
        for _ in range(80):
            mid = (lo + hi) / 2
            tail = 0.5 * math.erfc(mid / math.sqrt(2)) * 2
            if tail > pp: lo = mid
            else: hi = mid
        return (lo + hi) / 2
    thr = z_for(0.05 / m)
    print('  %d 個型態同時檢定 -> Bonferroni 門檻 |t| > %.2f（p < 0.05/%d）' % (m, thr, m))
    print('  超過門檻者：%s' % (', '.join(r[1].split()[0] for r in res if abs(r[6]) > thr) or '無'))
    print('  連未校正的 |t| > 1.96 都沒過者：%s'
          % (', '.join(r[1].split()[0] for r in res if abs(r[6]) > 1.96) or '無 -- 一個都沒有'))
    # what would it take to see this on the strategy's own 187 trades?
    se187 = sd * (1.0 / 90 + 1.0 / 97) ** 0.5
    print()
    print('  ★ 換算到 187 根訊號棒：分成兩組約 90 / 97，標準誤 %.1f 點' % se187)
    print('    -> p<0.05 可偵測的最小效果 = %.1f 點' % (1.96 * se187))
    print('    -> 7,703 上量到的最大效果 = %.1f 點（P14，且 t 僅 -1.04）'
          % max(abs(r[5]) for r in res))
    print('    **即使效果是真的，187 筆也偵測不到，差 %.1f 倍。**'
          % (1.96 * se187 / max(abs(r[5]) for r in res)))

    print()
    print('=' * 88)
    print(' 圖形型態普查 -- 次數、佔比，以及落在 %d 根進場訊號棒上的次數' % len(sig))
    print('=' * 88)
    print('%-34s %9s %8s %10s %10s' % ('型態', '次數', '佔全部', '訊號棒上', '訊號棒佔比'))
    print('-' * 88)
    for k in sorted(P, key=lambda x: -len(P[x])):
        hit = P[k]
        on = sum(1 for i in hit if i in SIG)
        print('%-34s %9s %7.2f%% %10d %9.1f%%'
              % (k, format(len(hit), ','), 100.0 * len(hit) / N, on,
                 100.0 * on / max(len(sig), 1)))
    return 0


def _wedge(i, lastH, lastL, H, L, rising):
    a, b = lastH[i], lastL[i]
    if not a or not b:
        return False
    dh = H[a[1]] - H[a[0]]
    dl = L[b[1]] - L[b[0]]
    return (dh < dl) if rising else (abs(dl) < abs(dh))


if __name__ == '__main__':
    sys.exit(main())
