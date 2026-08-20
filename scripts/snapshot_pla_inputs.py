# -*- coding: utf-8 -*-
"""
把一支 .pla 的 input 清單與檔案指紋寫成快照，進 git。

為什麼需要：MC12 保留上一次執行的 input 值，不會重新讀檔。策略名稱在打補丁時
也不會變。因此光看 MC 的參數對話框，無法判斷載入的是哪一個 build ——
2026-08 這一週已經因此作廢六批最佳化。

兩層防護：
  1. .pla 第一個 input 是 Build_ID（YYMMDD），對話框第一列就看得到
  2. 本腳本產生的快照進 git，git diff 直接顯示兩次 commit 之間哪些 input 動過

用法：
    python scripts/snapshot_pla_inputs.py <path-to.pla> [...]
    python scripts/snapshot_pla_inputs.py --all       掃 live + live_simulation + research

輸出：docs/build_snapshots/<檔名去副檔名>.txt
     欄位順序 = 宣告順序 = MC12 對話框的顯示順序，可逐列對照。
"""
import io
import os
import re
import sys
import glob
import hashlib

OUT_DIR = os.path.join('docs', 'build_snapshots')

# input 區塊：從 inputs: 到第一個分號結尾的宣告串
RE_BLOCK = re.compile(r'^inputs:(.*?);\s*$', re.S | re.M | re.I)
# 單一宣告：名稱 ( 預設值 )
RE_DECL = re.compile(r'^\s{2,}([A-Za-z_]\w*)\s*\(\s*([^)]*?)\s*\)\s*,?\s*$', re.M)


def strip_comments(text):
    """PowerLanguage 註解是 { }，可跨行。剝乾淨再解析，否則註解裡的括號會誤判。"""
    out, depth = [], 0
    for ch in text:
        if ch == '{':
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
        elif depth == 0:
            out.append(ch)
    return ''.join(out)


def fingerprint(path):
    n = os.path.getsize(path)
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return n, h.hexdigest()


def snapshot(path):
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    m = RE_BLOCK.search(strip_comments(raw))
    if not m:
        return None, 'no inputs block'

    decls = RE_DECL.findall(m.group(1))
    if not decls:
        return None, 'inputs block parsed empty'

    nbytes, md5 = fingerprint(path)
    build = next((v for k, v in decls if k.lower() == 'build_id'), '(none)')
    width = max(len(k) for k, _ in decls)

    lines = [
        '=' * 74,
        '  PLA INPUT SNAPSHOT',
        '=' * 74,
        '  file     : %s' % path.replace(os.sep, '/'),
        '  bytes    : %d' % nbytes,
        '  md5      : %s' % md5,
        '  Build_ID : %s' % build,
        '  inputs   : %d' % len(decls),
        '=' * 74,
        '',
        '  順序 = 宣告順序 = MC12 參數對話框的顯示順序，可逐列對照。',
        '',
    ]
    for i, (k, v) in enumerate(decls, 1):
        lines.append('  %3d  %-*s  %s' % (i, width, k, v))
    lines.append('')
    return '\n'.join(lines), None


def main(argv):
    if not argv:
        print(__doc__)
        return 1

    if argv[0] == '--all':
        targets = []
        for root in ('strategies/live', 'strategies/live_simulation',
                     'strategies/research'):
            targets += glob.glob(os.path.join(root, '**', '*.pla'),
                                 recursive=True)
        targets = [t for t in targets
                   if 'archive' not in t.replace(os.sep, '/')
                   and not t.endswith('.bak')]
    else:
        targets = argv

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    ok = bad = 0
    for t in sorted(targets):
        if not os.path.exists(t):
            print('  MISSING  %s' % t)
            bad += 1
            continue
        text, err = snapshot(t)
        if err:
            print('  SKIP     %s  (%s)' % (t, err))
            bad += 1
            continue
        name = os.path.splitext(os.path.basename(t))[0] + '.txt'
        dest = os.path.join(OUT_DIR, name)
        io.open(dest, 'w', encoding='utf-8', newline='\n').write(text)
        print('  WROTE    %s' % dest.replace(os.sep, '/'))
        ok += 1

    print('')
    print('  %d written, %d skipped' % (ok, bad))
    return 0 if bad == 0 else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
