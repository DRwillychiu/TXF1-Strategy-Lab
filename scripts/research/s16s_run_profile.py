# -*- coding: utf-8 -*-
"""Consecutive-loss profile of a strategy, from an MC12 Trades List export.

Willy 2026-11-08: "接下來的 MA 空從 V1.25 開始優化最大連續小虧損"

WHY A SEPARATE TOOL AND NOT A .pla CHANGE

  The exit NAME is the thing the analysis turns on, and a strategy cannot
  report its own exit names reliably: six of v1.25.0's fifteen exits are
  stop or limit orders, placed on one bar and filled on another, so a code
  latched at placement time names an order that may never have filled.

  MC12's Trades List already carries the filled exit name.  That is where
  the exit-label table in S16S_version_performance_history_20260810.md came
  from.  The export was simply never saved into the repo -- `reports/` holds
  L1 through L5 and no S16.

WHAT "SMALL" MEANS HERE

  Nothing is assumed.  The loss-size distribution is MEASURED first and
  printed, and runs are then reported two ways:

    all-loss runs    every trade with net < 0.  This is the metric the
                     2026-08-18 sweep recorded as 最長連虧, so it is the
                     one that can be checked against a known baseline.
    small-loss runs  runs restricted to losses at or under the median
                     loss, which is where the bleed lives.

  Reference to reproduce, v1.25.0 / QuickStop_MaxBars 4, from
  S16S_version_performance_history_20260810.md section 0.8:

      trades 180   net 2,615,600   losers 125   longest all-loss run 9

  If this tool does not reproduce those four on the S16 export, the tool is
  wrong, not the baseline.

Run:  python scripts/research/s16s_run_profile.py <trades.csv> [--md OUT.md]
      python scripts/research/s16s_run_profile.py reports/L1_trades.csv
"""
import argparse
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

COLS = ('進場日期', '進場時間', '進場價', '進場標籤',
        '出場日期', '出場時間', '出場價', '出場標籤',
        '方向', '口數', '點數', '毛損益', '成本', '淨損益')


def num(s):
    """MC12 exports use thousands separators, parentheses and minus signs."""
    s = (s or '').strip().replace(',', '').replace('−', '-')
    if not s:
        return 0.0
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def load(path):
    with io.open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('  %s 沒有資料列' % path)
    missing = [c for c in COLS if c not in rows[0]]
    if missing:
        raise SystemExit('  缺少欄位：%s\n  實際欄位：%s'
                         % ('、'.join(missing), '、'.join(rows[0].keys())))
    out = []
    for r in rows:
        out.append(dict(
            din=r['進場日期'].strip(), tin=r['進場時間'].strip(),
            ein=r['進場標籤'].strip(), eout=r['出場標籤'].strip(),
            dout=r['出場日期'].strip(),
            pts=num(r['點數']), net=num(r['淨損益'])))
    return out


def runs_of(trades, is_bad):
    """Maximal runs of consecutive trades satisfying is_bad, in order."""
    out, cur = [], []
    for t in trades:
        if is_bad(t):
            cur.append(t)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def hist(runs):
    h = {}
    for r in runs:
        h[len(r)] = h.get(len(r), 0) + 1
    return h


def median(v):
    v = sorted(v)
    n = len(v)
    if not n:
        return 0.0
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def tally(runs, key):
    t = {}
    for r in runs:
        for x in r:
            t[x[key]] = t.get(x[key], 0) + 1
    return t


def report(trades, label):
    L = []
    w = L.append
    n = len(trades)
    los = [t for t in trades if t['net'] < 0]
    win = [t for t in trades if t['net'] > 0]
    flat = n - len(los) - len(win)
    net = sum(t['net'] for t in trades)

    w('## %s' % label)
    w('')
    w('| | |')
    w('|---|---|')
    w('| 筆數 | %d |' % n)
    w('| 淨利 | %s |' % '{:,.0f}'.format(net))
    w('| 虧損筆數 | %d（%.1f%%）|' % (len(los), 100.0 * len(los) / n))
    w('| 獲利筆數 | %d |' % len(win))
    if flat:
        w('| 平手 | %d |' % flat)
    w('')

    if not los:
        w('沒有虧損筆，無連虧可言。')
        return '\n'.join(L), {}

    mag = sorted(abs(t['net']) for t in los)
    med = median(mag)
    w('### 虧損大小分布（實測，非假設）')
    w('')
    w('| | 金額 | 點數 |')
    w('|---|---|---|')
    for nm, v in (('最小', mag[0]), ('25%', mag[len(mag) // 4]),
                  ('中位', med), ('75%', mag[len(mag) * 3 // 4]),
                  ('最大', mag[-1])):
        w('| %s | %s | %.1f |' % (nm, '{:,.0f}'.format(v), v / 400.0))
    w('')
    w('*點數＝金額 ÷ 400（2 口 × 200 NTD／點）。*')
    w('')

    res = {}
    for nm, bad in (('全虧 run（任何虧損）', lambda t: t['net'] < 0),
                    ('小虧 run（虧損 <= 中位 %s）'
                     % '{:,.0f}'.format(med),
                     lambda t: t['net'] < 0 and abs(t['net']) <= med)):
        rr = runs_of(trades, bad)
        if not rr:
            continue
        longest = max(rr, key=len)
        worst = min(rr, key=lambda r: sum(x['net'] for x in r))
        h = hist(rr)
        res[nm] = dict(longest=len(longest), count=len(rr),
                       worst=sum(x['net'] for x in worst))
        w('### %s' % nm)
        w('')
        w('| | |')
        w('|---|---|')
        w('| **最長連虧** | **%d 筆** |' % len(longest))
        w('| run 段數 | %d |' % len(rr))
        w('| 最長那段金額 | %s |'
          % '{:,.0f}'.format(sum(x['net'] for x in longest)))
        w('| 最長那段期間 | %s ~ %s |' % (longest[0]['din'], longest[-1]['dout']))
        w('| **單段最大失血** | **%s**（%d 筆，%s ~ %s）|'
          % ('{:,.0f}'.format(sum(x['net'] for x in worst)), len(worst),
             worst[0]['din'], worst[-1]['dout']))
        w('')
        w('長度分布：' + '　'.join('%d 筆×%d' % (k, h[k])
                                 for k in sorted(h)))
        w('')
        w('**最長那一段的組成**')
        w('')
        w('| # | 進場標籤 | 出場標籤 | 點數 | 淨損益 |')
        w('|---|---|---|---|---|')
        for i, t in enumerate(longest, 1):
            w('| %d | %s | %s | %.0f | %s |'
              % (i, t['ein'] or '-', t['eout'] or '-', t['pts'],
                 '{:,.0f}'.format(t['net'])))
        w('')
        ti = tally(rr, 'ein')
        to = tally(rr, 'eout')
        w('**所有 run 的標籤歸因**（這是「是哪個機制在製造連虧」的答案）')
        w('')
        w('| 進場標籤 | 筆數 | | 出場標籤 | 筆數 |')
        w('|---|---|---|---|---|')
        ki = sorted(ti, key=lambda k: -ti[k])
        ko = sorted(to, key=lambda k: -to[k])
        for a in range(max(len(ki), len(ko))):
            c1 = '%s | %d' % (ki[a], ti[ki[a]]) if a < len(ki) else ' | '
            c2 = '%s | %d' % (ko[a], to[ko[a]]) if a < len(ko) else ' | '
            w('| %s | | %s |' % (c1, c2))
        w('')
    return '\n'.join(L), res


def replay(trades, n):
    """R1-style candidate rule: after n consecutive losses, skip the next trade.

    This is the rule shape DEPT_RISK.md R1 already approves for L3/L4/L5
    ("連虧 2 筆／3 筆 -> 跳過下一筆"), so n is the only thing to choose.
    The skip consumes the streak: the counter resets after one pause.

    ** THE ASSUMPTION, STATED **

      Replaying a rule over a historical trade LIST assumes the trades that
      follow a removed trade still exist.  For an entry that came from a
      fresh death cross that is reasonable -- the cross does not know the
      previous trade happened.  For a RE-ENTRY it is false: the re-entry is
      armed by the previous exit and priced at the previous entry, so
      removing the parent removes the child.

      So this is a SCREEN for choosing n, not a result.  The function
      reports how many skipped trades were re-entries, which is the size of
      the exposure.  The number that counts comes from MC12 with the rule
      coded.
    """
    consec = 0
    kept, skipped = [], []
    for t in trades:
        if consec >= n:
            skipped.append(t)
            consec = 0
            continue
        kept.append(t)
        consec = consec + 1 if t['net'] < 0 else 0
    return kept, skipped


def rule_table(trades, med, title):
    """Sweep n and show both sides of the trade-off for each."""
    L = []
    w = L.append
    base_runs = runs_of(trades, lambda t: t['net'] < 0)
    base_long = max((len(r) for r in base_runs), default=0)
    base_net = sum(t['net'] for t in trades)

    w('### %s' % title)
    w('')
    w('基準：%d 筆、淨利 %s、最長連虧 **%d**'
      % (len(trades), '{:,.0f}'.format(base_net), base_long))
    w('')
    w('| 連虧 N 筆跳過 | 跳過筆數 | 少掉的虧損 | 其中小虧 | **錯過的獲利** | '
      '淨效果 | 新最長連虧 | 跳過的是再進場 |')
    w('|---|---|---|---|---|---|---|---|')
    rows = []
    for n in range(1, 7):
        kept, sk = replay(trades, n)
        if not sk:
            continue
        cut = [t for t in sk if t['net'] < 0]
        cut_small = [t for t in cut if abs(t['net']) <= med]
        miss = [t for t in sk if t['net'] > 0]
        new_runs = runs_of(kept, lambda t: t['net'] < 0)
        new_long = max((len(r) for r in new_runs), default=0)
        delta = sum(t['net'] for t in kept) - base_net
        re_n = sum(1 for t in sk if 'ReEntry' in t['ein'])
        rows.append((n, new_long, delta))
        w('| **%d** | %d | %s（%d 筆）| %s（%d 筆）| **%s（%d 筆）** | '
          '%s%s | **%d** | %d／%d |'
          % (n, len(sk),
             '{:,.0f}'.format(-sum(t['net'] for t in cut)), len(cut),
             '{:,.0f}'.format(-sum(t['net'] for t in cut_small)),
             len(cut_small),
             '{:,.0f}'.format(sum(t['net'] for t in miss)), len(miss),
             '+' if delta > 0 else '', '{:,.0f}'.format(delta),
             new_long, re_n, len(sk)))
    w('')
    w('*「淨效果」是跳過那些筆之後的淨利變化。*')
    w('*最後一欄是本回放的假設曝險：跳過的筆裡有幾筆是再進場 —— '
      '那些筆被移除會連帶改變後續，清單回放算不出來（見 `replay()` 註解）。*')
    w('')
    if rows:
        best = min(rows, key=lambda r: (r[1], -r[2]))
        w('**此回放下最長連虧最小、且淨效果最好的是 N = %d**'
          '（最長連虧 %d，淨效果 %s%s）—— '
          '這是**篩選結果**，不是判決；判決要 MC12 把規則寫進程式再跑。'
          % (best[0], best[1], '+' if best[2] > 0 else '',
             '{:,.0f}'.format(best[2])))
        w('')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv', nargs='?', default='reports/L1_trades.csv')
    ap.add_argument('--md', default=None, help='也寫成 markdown 檔')
    ap.add_argument('--label', default=None)
    ap.add_argument('--oos', default=None,
                    help='樣本外起始日 YYYY-MM-DD，依進場日期切分')
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        raise SystemExit('  找不到 %s' % a.csv)
    trades = load(a.csv)
    lab = a.label or os.path.basename(a.csv)

    parts = [('全樣本 — %s' % lab, trades)]
    if a.oos:
        ins = [t for t in trades if t['din'] < a.oos]
        oos = [t for t in trades if t['din'] >= a.oos]
        if not ins or not oos:
            raise SystemExit('  --oos %s 把樣本切成空的一邊（%d / %d）'
                             % (a.oos, len(ins), len(oos)))
        parts.append(('樣本內（< %s）' % a.oos, ins))
        parts.append(('樣本外（>= %s）' % a.oos, oos))

    blocks, summary = [], []
    for title, tr in parts:
        md, res = report(tr, title)
        los = [abs(t['net']) for t in tr if t['net'] < 0]
        med = median(sorted(los)) if los else 0.0
        blocks.append(md)
        if los:
            blocks.append(rule_table(tr, med, '候選規則回放 — %s' % title))
        for k, v in res.items():
            summary.append('  [%s] %s -> 最長 %d 筆，單段最大失血 %s'
                           % (title, k, v['longest'],
                              '{:,.0f}'.format(v['worst'])))

    out = '\n'.join(blocks)
    print('=' * 74)
    print(out)
    print('=' * 74)
    for s in summary:
        print(s)
    if a.md:
        io.open(a.md, 'w', encoding='utf-8', newline='\n').write(out + '\n')
        print('  -> %s' % a.md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
