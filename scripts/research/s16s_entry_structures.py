# -*- coding: utf-8 -*-
"""
實際成交的每一筆進場，訊號那根帶了哪些空方結構？

回答的是一個很具體的問題：空方結構在歷史上到底出不出現，
以及它們和「策略真的進場了」這件事是什麼關係。

沒有損益欄。次數而已。
"""
import io, os, re, sys, csv, datetime, collections
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from s16s_kbar_unittest import (load_source, extract_section, strip_comments,
                               parse_inputs, parse_rules, parse_helpers, transpile)
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

CACHE = os.path.join(HERE, 's16s_5min.csv')
TRADES = (r'C:\Users\User\Downloads'
          r'\TXF1  S16_S_MACrossShort_v1.26.0 策略回測績效報告_原始.xlsx')

NAMES = {
    1: 'A01 空頭吞噬', 2: 'A05 空頭孕線', 3: 'A07 空頭十字孕線', 4: 'A18 鑷子頂',
    5: 'A20 高價配', 6: 'B25 三隻烏鴉', 7: 'B27 三內部下跌', 8: 'B29 三外部下跌',
    9: 'B34 三胎鴉', 10: 'B35 大敵當前', 11: 'B36 步步為營', 12: 'C41 下降三法',
    13: 'C45 三線打擊(跌)', 14: 'D47 空頭Hikkake', 15: 'D48 下降之鷹',
    16: 'A02 多頭吞噬', 17: 'A06 多頭孕線', 18: 'A08 多頭十字孕線', 19: 'A19 鑷子底',
    20: 'A21 低價配', 21: 'B26 三白兵', 22: 'B28 三內部上漲', 23: 'B30 三外部上漲',
    24: 'B37 南方三星', 25: 'B38 獨特三河床', 26: 'C42 上升三法', 27: 'C43 梯底',
    28: 'C46 三線打擊(漲)', 29: 'A09 內含線', 30: 'A10 外包線',
}
SUP = list(range(1, 16))
OPP = list(range(16, 29))
NEU = [29, 30]


def main():
    src = load_source()
    sec = strip_comments(extract_section(src))
    thr = parse_inputs(src)
    rules = dict(parse_rules(sec))
    helpers = parse_helpers(sec)

    O = []; H = []; L = []; C = []; BIS = []; KEY = {}
    with open(CACHE, encoding='utf-8') as f:
        for i, r in enumerate(csv.DictReader(f)):
            O.append(float(r['open'])); H.append(float(r['high']))
            L.append(float(r['low']));  C.append(float(r['close']))
            BIS.append(int(r['bars_in_sess']))
            KEY[(r['ymd'], r['hhmm'])] = i

    td = openpyxl.load_workbook(TRADES, data_only=True)['交易明細']
    T = []
    r = 4
    while r <= td.max_row:
        a = [c.value for c in td[r]]
        if a[0] is None or a[2] is None:
            r += 1; continue
        d = a[4].date() if hasattr(a[4], 'date') else a[4]
        T.append((d, a[5], a[3]))
        r += 2

    hcode = [(n, compile(transpile(e), '<h>', 'eval')) for n, e in helpers]
    rcode = dict((n, compile(transpile(e), '<r>', 'eval')) for n, e in rules.items())
    g = dict(thr); g['abs'] = abs; g['max'] = max; g['min'] = min
    g['__builtins__'] = {}

    def hits_at(i):
        g['O'] = [O[i], O[i-1], O[i-2], O[i-3], O[i-4]]
        g['H'] = [H[i], H[i-1], H[i-2], H[i-3], H[i-4]]
        g['L'] = [L[i], L[i-1], L[i-2], L[i-3], L[i-4]]
        g['C'] = [C[i], C[i-1], C[i-2], C[i-3], C[i-4]]
        g['v_Bars_In_Sess'] = BIS[i]
        for name, code in hcode:
            try: g[name] = eval(code, g)
            except Exception: g[name] = None
        out = []
        for c in range(1, 31):
            try:
                if eval(rcode[c], g) is True:
                    out.append(c)
            except Exception:
                pass
        return out

    per = collections.Counter()
    nsup = nopp = nneu = nnone = 0
    matched = 0
    rows = []
    for d, t, ent in T:
        ymd = '%d%02d%02d' % (d.year, d.month, d.day)
        hhmm = '%02d%02d' % (t.hour, t.minute)
        i = KEY.get((ymd, hhmm))
        if i is None or i < 5:
            continue
        matched += 1
        h = hits_at(i - 1)            # 訊號那根 = 成交那根的前一根
        for c in h:
            per[c] += 1
        s = [c for c in h if c in SUP]
        o = [c for c in h if c in OPP]
        n = [c for c in h if c in NEU]
        if s: nsup += 1
        if o: nopp += 1
        if n: nneu += 1
        if not h: nnone += 1
        rows.append((d, hhmm, s, o, n))

    print('=' * 90)
    print('  實際成交 %d 筆，訊號棒對上 %d 筆' % (len(T), matched))
    print('=' * 90)
    print('  帶「支持空單」結構        %4d 筆  (%.1f%%)' % (nsup, 100.0 * nsup / matched))
    print('  帶「反對空單」結構        %4d 筆  (%.1f%%)' % (nopp, 100.0 * nopp / matched))
    print('  帶「中性」結構            %4d 筆  (%.1f%%)' % (nneu, 100.0 * nneu / matched))
    print('  完全沒有任何結構          %4d 筆  (%.1f%%)' % (nnone, 100.0 * nnone / matched))

    print()
    print('=' * 90)
    print('  逐一結構：在實際成交的訊號棒上出現幾次')
    print('=' * 90)
    for c in range(1, 31):
        fam = '支持' if c <= 15 else ('反對' if c <= 28 else '中性')
        print('  %-4d %-18s %-4s  %4d 次  (%.1f%%)'
              % (c, NAMES[c], fam, per[c], 100.0 * per[c] / matched))
    return 0


if __name__ == '__main__':
    sys.exit(main())
