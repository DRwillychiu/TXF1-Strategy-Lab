# -*- coding: utf-8 -*-
"""
Move long comment blocks out of a .pla into a markdown record, and PROVE the
code did not change.

The proof is the whole point. On 2026-08-15 an earlier version of this script
refused to write twice; the second refusal caught

    [IntrabarOrderGeneration = False]

sitting at the bottom of what looked like a 2,401-line comment banner. Deleting
the banner would have silently changed fill behaviour, and the diff would have
read as "removed comments". In this file that directive sits at line 315,
one line after a 313-line header block -- the same trap, one line away.

Method: strip every comment from the before and after files, collapse all
whitespace, and require the remainder to be BYTE-IDENTICAL. Anything that is
not inside braces survives stripping, so a directive hidden in a banner shows
up as a difference and the script refuses to write.

Usage:  python scripts/slim_pla_v2.py <file.pla> --plan
        python scripts/slim_pla_v2.py <file.pla> --apply <record.md>
"""
import io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MIN_BLOCK = 5          # consecutive comment lines before a block is movable


def strip_comments(text):
    """Remove brace comments, honouring nesting. Everything else survives."""
    out = []
    depth = 0
    for ch in text:
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
            else:
                out.append(ch)
        elif depth == 0:
            out.append(ch)
    return ''.join(out)


def canon(text):
    """Comment-free, whitespace-collapsed form. This is what must not change."""
    return re.sub(r'\s+', ' ', strip_comments(text)).strip()


def classify(lines):
    """Per line: (carries code outside braces, brace depth at line start)."""
    flags = []
    depth = 0
    for l in lines:
        start_depth = depth
        has_code = False
        for ch in l:
            if ch == '{':
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
            elif depth == 0 and not ch.isspace():
                has_code = True
        flags.append((has_code, start_depth))
    return flags


def find_blocks(lines):
    """Runs of >= MIN_BLOCK consecutive comment-only, non-blank lines."""
    flags = classify(lines)
    blocks = []
    start = None
    for i, l in enumerate(lines):
        has_code, d0 = flags[i]
        # a blank line INSIDE a comment region belongs to the block
        pure = (not has_code) and (l.strip() != '' or d0 > 0)
        if pure and start is None:
            start = i
        elif not pure and start is not None:
            if i - start >= MIN_BLOCK:
                blocks.append((start, i))
            start = None
    if start is not None and len(lines) - start >= MIN_BLOCK:
        blocks.append((start, len(lines)))
    return blocks


def title_of(chunk):
    """A one-line label. Braces are stripped -- a '}' left in the title would
    close the pointer comment early and leak into the code. The byte-identity
    proof caught exactly that on the first run of this script."""
    for l in chunk:
        t = l.replace('{', ' ').replace('}', ' ').strip()
        t = t.strip('=').strip('-').strip()
        if t and not set(t) <= set('=-* '):
            return t[:70]
    return 'block'


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path = sys.argv[1]
    mode = sys.argv[2]
    original = open(path, encoding='ascii').read()
    lines = original.split('\n')
    blocks = find_blocks(lines)

    print('=' * 74)
    print('  %s' % os.path.basename(path))
    print('=' * 74)
    print('  lines %d   movable blocks %d   lines in them %d'
          % (len(lines), len(blocks), sum(b - a for a, b in blocks)))
    for a, b in blocks:
        print('    %5d +%-4d  %s' % (a + 1, b - a, title_of(lines[a:b])))

    if mode == '--plan':
        return 0
    if mode != '--apply' or len(sys.argv) < 4:
        print('  need: --apply <record.md>')
        return 2
    record = sys.argv[3]

    # build the new file: each block becomes a one-line pointer
    keep = []
    ptr = {}
    bi = 0
    bounds = dict((a, b) for a, b in blocks)
    i = 0
    while i < len(lines):
        if i in bounds:
            bi += 1
            end = bounds[i]
            ptr[bi] = (i + 1, lines[i:end])
            indent = len(lines[i]) - len(lines[i].lstrip())
            keep.append('%s{ %s -- see design record, block %d }'
                        % (' ' * indent, title_of(lines[i:end]), bi))
            i = end
        else:
            keep.append(lines[i])
            i += 1
    new = '\n'.join(keep)

    # ---- THE PROOF ----
    a, b = canon(original), canon(new)
    if a != b:
        print()
        print('  REFUSING TO WRITE -- the comment-free code is NOT identical.')
        for k in range(min(len(a), len(b))):
            if a[k] != b[k]:
                print('  first difference at char %d' % k)
                print('    before: %r' % a[max(0, k - 90):k + 90])
                print('    after : %r' % b[max(0, k - 90):k + 90])
                break
        else:
            print('  lengths differ: %d vs %d' % (len(a), len(b)))
        return 1

    if any(ord(c) > 127 for c in new):
        print('  REFUSING TO WRITE -- non-ASCII introduced')
        return 1

    with io.open(record, 'w', encoding='utf-8') as f:
        f.write('# %s -- 完整註解記錄\n\n' % os.path.basename(path))
        f.write('本檔存放從 `.pla` 移出的長註解區塊。程式碼一個字元都沒有改動 ——\n')
        f.write('`scripts/slim_pla_v2.py` 剝除前後兩檔的全部註解、正規化空白，\n')
        f.write('要求剩餘位元完全相同，否則拒絕寫檔。\n\n')
        f.write('`.pla` 裡每個被移出的區塊都留下一行指標，標號對應下面的段號。\n\n---\n\n')
        for k in sorted(ptr):
            ln, chunk = ptr[k]
            f.write('## 區塊 %d — 原第 %d 行起，共 %d 行\n\n' % (k, ln, len(chunk)))
            f.write('```\n')
            for l in chunk:
                f.write(l.rstrip() + '\n')
            f.write('```\n\n')

    open(path, 'w', encoding='ascii').write(new)
    print()
    print('  PROOF PASSED -- comment-free code is byte-identical')
    print('  lines %d -> %d  (-%d, %.1f%%)'
          % (len(lines), len(new.split('\n')),
             len(lines) - len(new.split('\n')),
             100.0 * (len(lines) - len(new.split('\n'))) / len(lines)))
    print('  record: %s' % record)
    return 0


if __name__ == '__main__':
    sys.exit(main())
