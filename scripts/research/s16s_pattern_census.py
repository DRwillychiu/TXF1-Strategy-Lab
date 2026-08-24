# -*- coding: utf-8 -*-
"""
S16_S pattern census -- how often does each structure occur, and where.

NO P&L COLUMN. Deliberately. The configuration that was voided on
2026-08-21 was chosen by reading net profit next to pattern names, and
anyone who sees that pairing will select on it. This file emits
occurrence counts only.

The 30 conditions are parsed out of the shipped .pla and transpiled, same
discipline as the unit-test harness -- the thing measured is the thing
that runs in MC12.

Populations reported:
  ALL       every bar in the export
  DEATH     bars where the exported ZLEMA columns show a death cross
  SLOPE     death-cross bars that also clear MinSlope_Rate, i.e. the bars
            the strategy would actually consider

Run:  python scripts/research/s16s_pattern_census.py
"""
import io, os, re, sys, csv, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from s16s_kbar_unittest import (load_source, extract_section, strip_comments,
                               parse_inputs, parse_rules, parse_helpers, transpile)

# the imported module wraps stdout in an ascii writer; detach before replacing
# it so the discarded wrapper cannot close the underlying buffer
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

CACHE = os.path.join(HERE, 's16s_5min.csv')

NAMES = {
    1: 'A01 空頭吞噬', 2: 'A05 空頭孕線', 3: 'A07 空頭十字孕線', 4: 'A18 鑷子頂',
    5: 'A20 高價配', 6: 'B25 三隻烏鴉', 7: 'B27 三內部下跌', 8: 'B29 三外部下跌',
    9: 'B34 三胎鴉', 10: 'B35 大敵當前', 11: 'B36 步步為營', 12: 'C41 下降三法',
    13: 'C45 三線打擊(跌)', 14: 'D47 空頭Hikkake', 15: 'D48 下降之鷹',
    16: 'A02 多頭吞噬', 17: 'A06 多頭孕線', 18: 'A08 多頭十字孕線', 19: 'A19 鑷子底',
    20: 'A21 低價配', 21: 'B26 三白兵', 22: 'B28 三內部上漲', 23: 'B30 三外部上漲',
    24: 'B37 南方三星', 25: 'B38 獨特三河床', 26: 'C42 上升三法', 27: 'C43 梯底',
    28: 'C46 三線打擊(漲)', 29: 'A09 內含線', 30: 'A10 外包線',
    31: 'D 多頭Hikkake', 32: 'D 家鴿', 33: 'D 三明治',
}
GROUP = dict((c, '支持' if c <= 15 else ('反對' if c <= 28 else '中性'))
             for c in range(1, 34))


def load_cache():
    O, H, L, C, BIS, ZF, ZS = [], [], [], [], [], [], []
    with open(CACHE, 'r', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        for r in rd:
            O.append(float(r['open'])); H.append(float(r['high']))
            L.append(float(r['low']));  C.append(float(r['close']))
            BIS.append(int(r['bars_in_sess']))
            ZF.append(float(r['zlema_f']) if r['zlema_f'] else 0.0)
            ZS.append(float(r['zlema_s']) if r['zlema_s'] else 0.0)
    return O, H, L, C, BIS, ZF, ZS


def main():
    if not os.path.exists(CACHE):
        print('cache missing -- run s16s_bars5.py first')
        return 1

    src = load_source()
    sec = strip_comments(extract_section(src))
    thr = parse_inputs(src)
    rules = dict(parse_rules(sec))
    helpers = parse_helpers(sec)
    assert sorted(rules) == list(range(1, 34)), sorted(rules)
    print('rules parsed: %d   helpers: %d' % (len(rules), len(helpers)))

    O, H, L, C, BIS, ZF, ZS = load_cache()
    N = len(O)
    print('bars: %d   md5(cache) %s' % (N, hashlib.md5(open(CACHE, 'rb').read()).hexdigest()))

    hcode = [(n, compile(transpile(e), '<h>', 'eval')) for n, e in helpers]
    rcode = dict((n, compile(transpile(e), '<r>', 'eval')) for n, e in rules.items())

    minslope = 0.050
    m = re.search(r'MinSlope_Rate\s*\(\s*([\d.]+)\s*\)', src)
    if m:
        minslope = float(m.group(1))

    cnt_all = dict((c, 0) for c in range(1, 34))
    cnt_dx = dict((c, 0) for c in range(1, 34))
    cnt_sl = dict((c, 0) for c in range(1, 34))
    n_dx = n_sl = 0
    any_all = any_dx = any_sl = 0

    g = dict(thr)
    g['abs'] = abs; g['max'] = max; g['min'] = min
    g['__builtins__'] = {}

    for i in range(5, N):
        g['O'] = [O[i], O[i-1], O[i-2], O[i-3], O[i-4]]
        g['H'] = [H[i], H[i-1], H[i-2], H[i-3], H[i-4]]
        g['L'] = [L[i], L[i-1], L[i-2], L[i-3], L[i-4]]
        g['C'] = [C[i], C[i-1], C[i-2], C[i-3], C[i-4]]
        g['v_Bars_In_Sess'] = BIS[i]
        if BIS[i] < 2:
            continue
        for name, code in hcode:
            try:
                g[name] = eval(code, g)
            except Exception:
                g[name] = None

        hits = []
        for c in range(1, 34):
            try:
                if eval(rcode[c], g) is True:
                    hits.append(c)
            except Exception:
                pass

        for c in hits:
            cnt_all[c] += 1
        if hits:
            any_all += 1

        # death cross on this bar, read from the exported indicator columns
        if ZF[i-1] and ZS[i-1] and ZF[i] and ZS[i] \
           and ZF[i-1] >= ZS[i-1] and ZF[i] < ZS[i]:
            n_dx += 1
            for c in hits:
                cnt_dx[c] += 1
            if hits:
                any_dx += 1
            # slope: close-to-close fall over the bar, per cent per minute
            if C[i] > 0:
                rate = ((C[i-1] - C[i]) / C[i] * 100.0) / 5.0
                if rate > minslope:
                    n_sl += 1
                    for c in hits:
                        cnt_sl[c] += 1
                    if hits:
                        any_sl += 1

    print()
    print('=' * 96)
    print('  母體')
    print('=' * 96)
    print('  全部可判定的棒子      %8d' % (N - 5))
    print('  死叉                  %8d' % n_dx)
    print('  死叉且過斜率閘門      %8d   <- 這才是策略真正會考慮的棒子' % n_sl)

    print()
    print('=' * 96)
    print('  逐型態次數  ——  沒有損益欄，這是刻意的')
    print('=' * 96)
    print('  %-4s %-18s %-5s %10s %8s %10s %8s %10s %8s'
          % ('代碼', '型態', '家族', '全部', '佔%', '死叉', '佔%', '過閘門', '佔%'))
    for c in range(1, 34):
        print('  %-4d %-18s %-5s %10d %7.2f%% %10d %7.2f%% %10d %7.2f%%'
              % (c, NAMES[c], GROUP[c],
                 cnt_all[c], 100.0 * cnt_all[c] / (N - 5),
                 cnt_dx[c], 100.0 * cnt_dx[c] / max(n_dx, 1),
                 cnt_sl[c], 100.0 * cnt_sl[c] / max(n_sl, 1)))

    print()
    print('=' * 96)
    print('  家族合計（至少命中一種，不重複計算）')
    print('=' * 96)
    print('  %-10s %10s %10s %10s' % ('母體', '全部', '死叉', '過閘門'))
    print('  %-10s %10d %10d %10d' % ('任一型態', any_all, any_dx, any_sl))
    print('  %-10s %9.2f%% %9.2f%% %9.2f%%'
          % ('佔母體', 100.0 * any_all / (N - 5),
             100.0 * any_dx / max(n_dx, 1), 100.0 * any_sl / max(n_sl, 1)))

    print()
    print('=' * 96)
    print('  結構性惰性檢查 —— 在「過閘門」母體上為 0 的型態')
    print('=' * 96)
    dead = [c for c in range(1, 34) if cnt_sl[c] == 0]
    for c in dead:
        print('  %-4d %-18s %-5s   全部 %d 次，死叉 %d 次，過閘門 0 次'
              % (c, NAMES[c], GROUP[c], cnt_all[c], cnt_dx[c]))
    print('  合計 %d / 30' % len(dead))
    return 0


if __name__ == '__main__':
    sys.exit(main())
