# -*- coding: utf-8 -*-
"""收斂類 6 種的檢查表量測 —— 進入逐一邏輯規劃之前.

P01 NR4 / P02 NR7 / P03 內含線x2 / P04 內含線x3 / P05 ID-NR4 / P06 三根遞減區間

定義原樣取自 docs/research/S16S_chart_pattern_catalogue_20260824.md：
  P01  當根區間是最近 4 根最窄        N=4（Crabel 常數）
  P02  最近 7 根最窄                  N=7（Crabel 常數）
  P03  連續兩根內含線                 0
  P04  連續三根                       0
  P05  內含線 AND NR4                 N=4
  P06  R < R[1] < R[2]                0

★ 這六個不是樞紐型態

它們讀相鄰 K 棒，不讀樞紐鏈。所以檢查表 A 區（樞紐層）多半不適用，
但第 3 條「相鄰依賴不可跨時段」反而是核心：2026-08-21 的 12 個兩根型態
就是因為漏掉 v_Bars_In_Sess >= 2 而產生 177 次跨時段誤觸發。

本檔一次量完檢查表要的數字，避免像 P29 那樣母體被重定義五次：
  第 3 條   跨時段：不設限 vs 設限，差幾個
  第 15 條  平均幾根出現一次（>500 就必須換 K 棒顏色）
  第 17 條  定義裡的「相等」：嚴格 vs 非嚴格，代價多少
  第 18 條  跨度（這六個都是固定跨度，列出來對照）

Run:  python scripts/research/s16s_conv6_scan.py
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


def main():
    rows = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    Y = [r['ymd'] for r in rows]
    N = len(rows)
    R = [H[i] - L[i] for i in range(N)]
    print('母體 %s 根   %s ~ %s' % (format(N, ','), Y[0], Y[-1]))
    print()

    # ---- 述詞。sess = 需要幾根同時段的相鄰 K 棒 --------------------------
    def nr(i, n, strict):
        """當根區間是最近 n 根最窄。strict=True 表示平手不算。"""
        if i < n - 1:
            return False
        others = [R[i - k] for k in range(1, n)]
        return R[i] < min(others) if strict else R[i] <= min(others)

    def inside(i, strict):
        """內含線。strict=True 表示高低都要嚴格在內。"""
        if i < 1:
            return False
        if strict:
            return H[i] < H[i - 1] and L[i] > L[i - 1]
        return H[i] <= H[i - 1] and L[i] >= L[i - 1]

    DEFS = [
        ('P01', 'NR4', 4, lambda i, st: nr(i, 4, st)),
        ('P02', 'NR7', 7, lambda i, st: nr(i, 7, st)),
        ('P03', '內含線 x2', 3, lambda i, st: inside(i, st) and inside(i - 1, st)),
        ('P04', '內含線 x3', 4,
         lambda i, st: inside(i, st) and inside(i - 1, st) and inside(i - 2, st)),
        ('P05', 'ID-NR4', 4, lambda i, st: inside(i, st) and nr(i, 4, st)),
        ('P06', '三根遞減區間', 3,
         lambda i, st: (R[i] < R[i - 1] < R[i - 2]) if i >= 2 else False),
    ]

    def same_sess(i, need):
        """i 往回 need-1 根都在同一個時段內。"""
        return S[i] >= need

    print('=' * 88)
    print(' 第 3 條　跨時段：相鄰依賴的型態必須同時段')
    print('=' * 88)
    print('%-6s %-14s %5s %12s %12s %10s %8s'
          % ('代號', '名稱', '需根', '不設限', '設限同時段', '誤觸發', '佔比'))
    print('-' * 88)
    keep = {}
    for code, zh, need, fn in DEFS:
        loose = [i for i in range(N) if fn(i, False)]
        tight = [i for i in loose if same_sess(i, need)]
        keep[code] = tight
        bad = len(loose) - len(tight)
        print('%-6s %-14s %5d %12s %12s %10s %7.2f%%'
              % (code, zh, need, format(len(loose), ','), format(len(tight), ','),
                 format(bad, ','), 100.0 * bad / max(len(loose), 1)))

    print()
    print('=' * 88)
    print(' 第 15 條　平均幾根出現一次（> 500 根必須換 K 棒顏色）')
    print('=' * 88)
    print('%-6s %-14s %10s %10s %10s %8s'
          % ('代號', '名稱', '個數', '佔母體', '每 N 根', '掛零年'))
    print('-' * 88)
    for code, zh, need, fn in DEFS:
        hs = keep[code]
        yr = collections.Counter(Y[i][:4] for i in hs)
        z = sum(1 for y in YRS if yr[y] == 0)
        print('%-6s %-14s %10s %9.2f%% %10.1f %8d'
              % (code, zh, format(len(hs), ','), 100.0 * len(hs) / N,
                 N / float(max(len(hs), 1)), z))

    print()
    print('=' * 88)
    print(' 第 17 條　定義裡的「相等」：嚴格 vs 非嚴格')
    print('=' * 88)
    print('  NR 的「最窄」：平手算不算？　內含線：高低相等算不算內含？')
    print()
    print('%-6s %-14s %12s %12s %10s'
          % ('代號', '名稱', '非嚴格', '嚴格', '差'))
    print('-' * 88)
    for code, zh, need, fn in DEFS:
        a = len([i for i in range(N) if fn(i, False) and same_sess(i, need)])
        b = len([i for i in range(N) if fn(i, True) and same_sess(i, need)])
        d = a - b
        print('%-6s %-14s %12s %12s %9s (%.1f%%)'
              % (code, zh, format(a, ','), format(b, ','), format(d, ','),
                 100.0 * d / max(a, 1)))

    print()
    print('=' * 88)
    print(' 第 18 條　跨度：這六個都是固定跨度，沒有樞紐尺度問題')
    print('=' * 88)
    for code, zh, need, fn in DEFS:
        print('  %-6s %-14s 固定 %d 根' % (code, zh, need))

    print()
    print('=' * 88)
    print(' 逐年（設限同時段後）')
    print('=' * 88)
    for code, zh, need, fn in DEFS:
        yr = collections.Counter(Y[i][:4] for i in keep[code])
        print('  %-6s %s' % (code, '  '.join('%s=%s' % (y, format(yr[y], ','))
                                             for y in YRS)))

    print()
    print('=' * 88)
    print(' 重疊：這六個彼此包含多少')
    print('=' * 88)
    codes = [c for c, _, _, _ in DEFS]
    sets = {c: set(keep[c]) for c in codes}
    print('        ' + ''.join('%8s' % c for c in codes))
    for a in codes:
        line = '  %-6s' % a
        for b in codes:
            if a == b:
                line += '%8s' % '-'
            else:
                ov = len(sets[a] & sets[b])
                line += '%7.0f%%' % (100.0 * ov / max(len(sets[a]), 1))
        print(line)
    print()
    print('  讀法：列 a 的第 b 欄 ＝ a 之中有幾成同時也是 b')


if __name__ == '__main__':
    main()
