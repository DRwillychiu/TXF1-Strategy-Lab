# -*- coding: utf-8 -*-
"""2x2 家族的五個新格子 —— 檢查表量測.

P08 下降三角 / P10 對稱三角 / P11 上升楔形 / P20 下降通道 / P22 箱型

定義原樣取自 docs/research/S16S_chart_pattern_catalogue_20260824.md：
  P08  高遞減 + 低完全相等
  P10  高遞減 + 低遞增
  P11  高低同升，高的漲幅較小
  P20  高遞減 + 低遞減
  P22  高完全相等 + 低完全相等

★ 這五個跟已編碼的擴散家族填同一個格子

六樞紐、三高三低，每邊方向屬於 {升, 降, 平}，得到 3x3 格：

          低升            低降            低平
  高升  P51(高快)/P11   P29             P54
  高降  P10             P52(低快)/P20   P08
  高平  （空缺）         P53             P22

粗體那些 IND_S16S_P29 SECTION 6a 已經在算 v_RiseH / v_FallH / v_FlatH /
v_RiseL / v_FallL / v_FlatL / v_LowUnder。所以這五個是同一個 cascade 的
新分支，不是新骨架 —— 本檔因此直接重放那條鏈，而不是另寫一份
（2026-08-30 普查跑錯鏈的教訓）。

★ 兩件要量的事

1. P08 與 P22 定義裡有「完全相等」。P53/P54 用完全相等的結果是八年 7 個
   和 8 個 —— 檢查表第 17 條說這種要用區間裝置。兩種都量，讓代價可見。

2. P20 沒有跨距條件，所以它應該是整個「降降格」；而 P52 是降降格裡
   低跌得比較快的那部分。P20 是否真的包含 P52，量出來看。

Run:  python scripts/research/s16s_grid5_scan.py
"""
import collections
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, 's16s_5min.csv')
YRS = [str(y) for y in range(2019, 2027)]
SLOTS = 12


def main():
    rows = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    Y = [r['ymd'] for r in rows]
    T = [r['hhmm'] for r in rows]
    N = len(rows)
    print('母體 %s 根   %s ~ %s' % (format(N, ','), Y[0], Y[-1]))

    def is_ph(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and H[i] > H[i - 1] and H[i] > H[i + 1])

    def is_pl(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and L[i] < L[i - 1] and L[i] < L[i + 1])

    def band(x, p, q):
        return min(p, q) <= x <= max(p, q)

    hit = collections.defaultdict(list)
    cell = collections.Counter()
    chain = []
    for b in range(1, N):
        i = b - 1
        for k in (1, 2):
            if not (is_ph(i) if k == 1 else is_pl(i)):
                continue
            if chain and chain[-1][2] == k:
                chain = []
            if len(chain) >= SLOTS:
                chain = chain[1:]
            chain.append((i, H[i] if k == 1 else L[i], k))
            if len(chain) < 6:
                continue
            w = chain[-6:]
            hs = [x[1] for x in w if x[2] == 1]
            ls = [x[1] for x in w if x[2] == 2]
            if len(hs) != 3 or len(ls) != 3:
                continue
            if not (ls[0] < hs[0] and ls[2] < hs[2]):     # 低在高下，裁示 6
                continue
            rH = hs[0] < hs[1] < hs[2]
            fH = hs[0] > hs[1] > hs[2]
            eH = hs[0] == hs[1] == hs[2]
            bH = band(hs[2], hs[0], hs[1])                 # 區間裝置版的「高平」
            rL = ls[0] < ls[1] < ls[2]
            fL = ls[0] > ls[1] > ls[2]
            eL = ls[0] == ls[1] == ls[2]
            bL = band(ls[2], ls[0], ls[1])
            sH, sL = hs[2] - hs[0], ls[2] - ls[0]
            a, z = w[0][0], w[-1][0]

            # 3x3 格的分布（用嚴格三分，平 = 完全相等）
            dh = 'r' if rH else ('f' if fH else ('e' if eH else '-'))
            dl = 'r' if rL else ('f' if fL else ('e' if eL else '-'))
            cell[dh + dl] += 1

            if fH and eL:               hit['P08e'].append((a, z))
            if fH and bL and not fL and not rL: hit['P08b'].append((a, z))
            if fH and rL:               hit['P10'].append((a, z))
            if rH and rL and sH < sL:   hit['P11'].append((a, z))
            if fH and fL:               hit['P20'].append((a, z))
            if fH and fL and abs(sL) > abs(sH): hit['P52'].append((a, z))
            if eH and eL:               hit['P22e'].append((a, z))
            if bH and bL and not (rH or fH) and not (rL or fL):
                hit['P22b'].append((a, z))

    print('六樞紐框架的 3x3 分布（平 = 完全相等，- = 非單調也不全等）')
    print('  ' + '  '.join('%s%s=%s' % (h, l, format(cell[h + l], ','))
                           for h in 'rfe-' for l in 'rfe-' if cell[h + l]))
    print()
    print('=' * 86)
    print('%-8s %-16s %10s %9s %10s %8s'
          % ('代號', '名稱', '個數', '年均', '跨度中位', '掛零年'))
    print('-' * 86)
    NAMES = [('P08e', '下降三角 完全相等'), ('P08b', '下降三角 區間裝置'),
             ('P10', '對稱三角'), ('P11', '上升楔形'),
             ('P20', '下降通道'), ('P52', '  其中低跌較快 = P52'),
             ('P22e', '箱型 完全相等'), ('P22b', '箱型 區間裝置')]
    for code, zh in NAMES:
        hs = hit[code]
        if not hs:
            print('%-8s %-16s %10d' % (code, zh, 0))
            continue
        yr = collections.Counter(Y[a][:4] for a, _ in hs)
        sp = sorted(z - a for a, z in hs)
        print('%-8s %-16s %10s %9.1f %10d %8d'
              % (code, zh, format(len(hs), ','), len(hs) / 7.64,
                 sp[len(sp) // 2], sum(1 for y in YRS if yr[y] == 0)))

    print()
    print('P52 是否真的在 P20 之內：%s'
          % ('是' if set(hit['P52']) <= set(hit['P20']) else '否'))
    print('已編碼的 P52 母體 1,670 / 1,716 對照本檔 P52 %s'
          % format(len(hit['P52']), ','))

    print()
    print('=' * 86)
    print(' 真實案例（取跨度中位、不跨時段者）')
    print('=' * 86)
    for code, zh in NAMES:
        hs = hit[code]
        if not hs:
            continue
        clean = [(a, z) for a, z in hs
                 if all(S[t] > 1 for t in range(a + 1, z + 1))]
        if not clean:
            clean = hs
        clean.sort(key=lambda p: p[1] - p[0])
        a, z = clean[len(clean) // 2]
        print('  %-8s %-16s %s %s  ->  %s %s   跨度 %d 根'
              % (code, zh, Y[a], T[a], Y[z], T[z], z - a))


if __name__ == '__main__':
    main()
