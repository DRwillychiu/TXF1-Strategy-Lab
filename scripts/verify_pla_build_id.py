# -*- coding: utf-8 -*-
"""Fail when a .pla header states a Build_ID that its input no longer holds.

2026-08-27.  IND_S16S_P29's header drifted from its input twice in one day:
260830 while the input said 260840, then 260841 while the input said 260842.
Both times the code was right and the first thing a reader sees was wrong --
and the second time Willy caught it before I did, by opening the file on
GitHub and reading the top.

The input is the single source of truth: it is what MC compiles, what the
indicator prints on bar 1, and what shows in the study's properties.  The
header restates it for human readers, so the two can disagree.  Remembering to
update both is exactly the kind of discipline that fails; checking is not.

Counts only what it can prove: files with no Build_ID input, and files whose
header never mentions one, are reported as skipped rather than passed.

    python scripts/verify_pla_build_id.py            report
    python scripts/verify_pla_build_id.py --strict   exit 1 on any mismatch
"""
import io, os, re, sys, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPE = ('strategies/live', 'strategies/live_simulation', 'strategies/research')


def main():
    strict = '--strict' in sys.argv
    files = []
    for d in SCOPE:
        files += glob.glob(os.path.join(ROOT, d, '**', '*.pla'), recursive=True)
    files = sorted(f for f in files if 'archive' not in f.replace(os.sep, '/'))

    ok = bad = skip = 0
    rows = []
    for f in files:
        txt = open(f, encoding='utf-8', errors='replace').read()
        m = re.search(r'^\s*Build_ID\s*\(\s*(\d+)\s*\)', txt, re.M)
        if not m:
            skip += 1
            continue
        val = m.group(1)

        # the header is the comment block before the inputs section
        head = txt[:m.start()]
        cut = head.rfind('inputs:')
        if cut > 0:
            head = head[:cut]
        stated = re.findall(r'Build_ID\s+(\d{6})\b', head)
        # BUILD HISTORY lines are dated facts about past builds and do not
        # drift; only a bare "Build_ID NNNNNN." claim about the current build
        # is checked, and that is the first one in the header.
        if not stated:
            skip += 1
            rows.append(('SKIP', os.path.relpath(f, ROOT), val, '(檔頭未宣告)'))
            continue
        if stated[0] == val:
            ok += 1
            rows.append(('OK', os.path.relpath(f, ROOT), val, ''))
        else:
            bad += 1
            rows.append(('FAIL', os.path.relpath(f, ROOT), val,
                         '檔頭寫 %s' % stated[0]))

    print('=' * 78)
    print(' Build_ID header / input consistency')
    print('=' * 78)
    for st, path, val, note in rows:
        if st == 'OK':
            continue
        print('  [%-4s] %-58s input=%s  %s' % (st, path, val, note))
    if not bad:
        print('  沒有不一致')
    print('-' * 78)
    print('  掃描 %d 檔   相符 %d   不符 %d   無 Build_ID/檔頭未宣告 %d'
          % (len(files), ok, bad, skip))
    print('=' * 78)
    if bad and strict:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
