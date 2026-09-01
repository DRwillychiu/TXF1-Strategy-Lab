# -*- coding: utf-8 -*-
"""Which committed HTML pages would change if their generator were re-run?

WHY THIS EXISTS

  2026-09-01: the desktop and the laptop hold different s16s_5min.csv files
  -- same 421,513 rows, same first and last bar, different content.  The
  file is gitignored (.gitignore line 14), so the repo cannot see it.

  Eleven page generators read CSV-derived data.  Re-running all of them on
  the laptop moved THREE committed pages:

    S16S_eleven_diagram    desktop counts -> laptop counts
    S16S_diamond_diagram   example case 20220107 2110 -> 20211117 0930
    S16S_gap_group_diagram example case 20191022 0320 -> 20190419 1640

  None of those is wrong.  Both machines drew a real case from their own
  data.  The problem is that the flip is SILENT: a page can be regenerated
  as a side effect of an unrelated rebuild, and the commit looks like a
  documentation change.

  The other eight produced byte-identical output here.  That proves they
  are stable ON THIS MACHINE.  It does NOT prove they are machine
  independent -- they were last generated here.

WHAT IT DOES

  Runs every page generator, records which tracked files under
  docs/research/ changed, restores every one of them, and reports.
  Nothing is left modified.

  REFUSES TO RUN on a dirty docs/research/, because it cannot then tell
  its own edits from yours.

Run:  python scripts/verify_page_drift.py
Exit: 0 when nothing drifts, 1 when something does.
"""
import glob
import io
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')
PAGES = 'docs/research'
PATTERNS = ('scripts/research/s16s_*make*page*.py',
            'scripts/research/s16s_*diagram*.py',
            'scripts/research/s16s_landing_map_page.py',
            'scripts/research/s16s_day0831_review.py')
MASTER = 's16s_make_master_page.py'      # runs last: it embeds the others


def dirty():
    r = subprocess.run(['git', 'status', '--porcelain', PAGES],
                       capture_output=True)
    return [l[3:].strip() for l in r.stdout.decode('utf-8').split('\n')
            if l.strip()]


def main():
    if not os.path.isdir('.git'):
        print('  not a git repo'); return 1
    pre = dirty()
    if pre:
        print('=' * 74)
        print('  REFUSED -- %s 有未提交的變更，無法分辨是誰改的：' % PAGES)
        for f in pre[:10]:
            print('    %s' % f)
        print('=' * 74)
        return 1

    gens = []
    for p in PATTERNS:
        gens.extend(glob.glob(p))
    gens = sorted(set(gens))
    gens = [g for g in gens if os.path.basename(g) != MASTER]
    m = os.path.join('scripts', 'research', MASTER)
    if os.path.exists(m):
        gens.append(m)                    # master last, it embeds the rest

    print('=' * 74)
    print('  頁面漂移檢查   %d 支生成器' % len(gens))
    print('-' * 74)
    bad = 0
    for g in gens:
        r = subprocess.run([sys.executable, g], capture_output=True)
        if r.returncode != 0:
            tail = r.stderr.decode('utf-8', 'replace').strip().split('\n')[-1]
            print('  ERROR  %-34s %s' % (os.path.basename(g), tail[:34]))
            bad += 1

    moved = dirty()
    if moved:
        print('-' * 74)
        for f in moved:
            print('  DRIFT  %s' % f)
        subprocess.run(['git', 'checkout', '--'] + moved,
                       capture_output=True)
        print('-' * 74)
        print('  %d 個頁面與其生成器不同步 -- 已全部還原，工作樹未被更動。' % len(moved))
        print('  這通常表示該頁的來源資料（CSV）與產出這份 commit 的機器不同。')
        print('  見 docs/research/S16S_CSV_DIVERGENCE_20260901.md')
    else:
        print('-' * 74)
        print('  所有頁面都與其生成器同步。')
    print('=' * 74)
    return 1 if (moved or bad) else 0


if __name__ == '__main__':
    sys.exit(main())
