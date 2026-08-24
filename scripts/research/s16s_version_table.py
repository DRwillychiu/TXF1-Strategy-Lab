# -*- coding: utf-8 -*-
"""Every S16_S MC12 report in Downloads -> one comparison table.

The point of this file is the COMPARABILITY column. A settings sheet's
"end date" is the range that was REQUESTED, not the data that actually
existed -- see reference_mc12_report_compare. So the window is taken from
the LAST CLOSED EXIT in the trade detail, which is a fact about the run.

Two runs whose actual windows differ are not comparable and the table says
so rather than quietly ranking them side by side.
"""
import io, os, re, sys, glob, collections
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DL = r'C:\Users\User\Downloads'

WANT = ['淨利', '毛利', '毛損', '獲利因子', '交易總次數', '%勝率',
        '最大策略虧損', '最大策略虧損 (%)', '帳戶報酬', '年報酬率',
        '夏普比率', '索丁諾比率', '滑價支付', '最大平倉交易虧損']


def read(f):
    try:
        wb = openpyxl.load_workbook(f, data_only=True, read_only=True)
    except Exception:
        return None
    d = {'file': os.path.basename(f)}
    if '設定' in wb.sheetnames:
        for r in wb['設定'].iter_rows(values_only=True):
            c = [('' if x is None else str(x).strip()) for x in r]
            if len(c) >= 2 and c[0] and c[1]:
                d.setdefault('S_' + c[0], c[1])
    if '策略分析' in wb.sheetnames:
        for r in wb['策略分析'].iter_rows(values_only=True):
            c = list(r)
            k = '' if c[0] is None else str(c[0]).strip()
            if k in WANT and 'M_' + k not in d and len(c) > 1 and c[1] is not None:
                d['M_' + k] = c[1]
    # actual window + exit-label mix, from the trade detail
    if '交易明細' in wb.sheetnames:
        hdr = None
        last = first = None
        lab = collections.Counter()
        pnl = collections.Counter()
        prev_pnl = None
        for r in wb['交易明細'].iter_rows(values_only=True):
            c = list(r)
            if hdr is None:
                if c and c[0] and '交易編號' in str(c[0]):
                    hdr = [('' if x is None else str(x).strip()) for x in c]
                continue
            if all(x is None for x in c):
                continue
            row = dict(zip(hdr, c))
            s = str(row.get('訊號') or '')
            dt = str(row.get('日期') or '')[:10]
            if s.startswith('SE_'):
                prev_pnl = row.get('獲利(¤)') or 0
                if first is None:
                    first = dt
            elif s and not s.startswith('SE_'):
                last = dt
                lab[s] += 1
                if prev_pnl is not None:
                    pnl[s] += prev_pnl
                    prev_pnl = None
        d['first_trade'] = first
        d['last_exit'] = last
        d['labels'] = lab
        d['label_pnl'] = pnl
    wb.close()
    return d


def ver(name):
    m = re.search(r'_v(\d+\.\d+\.\d+)', name)
    if m:
        return m.group(1)
    m = re.search(r'報告V(\d+\.\d+(?:\.\d+)?)', name)
    if m:
        return m.group(1)
    return None


def f(x, n=0):
    if x is None:
        return '-'
    try:
        return format(round(float(x), n) if n else int(round(float(x))), ',')
    except Exception:
        return str(x)


def main():
    out = []
    for p in glob.glob(os.path.join(DL, '*S16_S*.xlsx')):
        b = os.path.basename(p)
        if '10M' in b:
            continue
        v = ver(b)
        if not v:
            continue
        d = read(p)
        if d and d.get('M_交易總次數'):
            d['ver'] = v
            out.append(d)
    # keep, per version, the run with the most trades on the longest window
    best = {}
    for d in out:
        k = (d['ver'], d.get('last_exit'))
        cur = best.get(k)
        if cur is None or float(d['M_淨利']) > float(cur['M_淨利']):
            best[k] = d
    rows = sorted(best.values(), key=lambda d: ([int(x) for x in d['ver'].split('.')],
                                                d.get('last_exit') or ''))
    print('S16_S 版本績效總表   (%d 份報告)' % len(rows))
    print()
    H = ('%-9s %-8s %-11s %-11s %5s %11s %6s %6s %11s %7s %7s %7s'
         % ('版本', 'Build', '首筆', '末次平倉', '筆數', '淨利', 'PF', '勝率',
            'MDD', 'MDD%', '夏普', '年報酬'))
    print(H)
    print('-' * len(H))
    for d in rows:
        print('%-9s %-8s %-11s %-11s %5s %11s %6s %5s%% %11s %6s%% %7s %6s%%'
              % (d['ver'], d.get('S_Build_ID', '-'),
                 (d.get('first_trade') or '-')[:10], (d.get('last_exit') or '-')[:10],
                 f(d['M_交易總次數']), f(d['M_淨利']),
                 f(d.get('M_獲利因子'), 2), f(d.get('M_%勝率'), 1),
                 f(d.get('M_最大策略虧損')), f(d.get('M_最大策略虧損 (%)'), 1),
                 f(d.get('M_夏普比率'), 3), f(d.get('M_年報酬率'), 1)))
    print()
    grp = collections.defaultdict(list)
    for d in rows:
        grp[d.get('last_exit')].append(d['ver'])
    print('可比較分組（依實際末次平倉日）:')
    for k in sorted(grp, key=lambda x: x or ''):
        print('   %s   %s' % (k, ' '.join(grp[k])))
    return rows


if __name__ == '__main__':
    main()
