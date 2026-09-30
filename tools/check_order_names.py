#!/usr/bin/env python3
"""Order-name uniqueness check for MultiCharts PowerLanguage (.pla/.txt).

MultiCharts raises a run-time error
    "<name>" name of the order has already been used for the other order
when two DIFFERENT order statements (Buy/Sell/SellShort/BuyToCover) carry the
same name and both get executed during one backtest. The check below lists
every order statement and fails when a name is used by more than one statement.

usage: python tools/check_order_names.py file.pla [file.pla ...]
exit code 1 if any name is shared by 2+ statements.
"""
import re, sys, collections

PAT = re.compile(r'\b(Buy|Sell|SellShort|BuyToCover)\s*\(\s*"([^"]+)"\s*\)', re.I)

def strip_comments(s):
    # PowerLanguage comments: { ... } (multi-line) and // to end of line
    s = re.sub(r'\{.*?\}', lambda m: '\n' * m.group(0).count('\n'), s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)

def scan(path):
    src = strip_comments(open(path, encoding='ascii', errors='replace').read())
    uses = collections.defaultdict(list)
    for m in PAT.finditer(src):
        line = src.count('\n', 0, m.start()) + 1
        uses[m.group(2)].append((m.group(1), line))
    return uses

def main(paths):
    bad = 0
    for p in paths:
        uses = scan(p)
        dup = {k: v for k, v in uses.items() if len(v) > 1}
        print(f"{p}: {len(uses)} order names, {sum(len(v) for v in uses.values())} statements")
        for k, v in sorted(dup.items()):
            print(f"  [DUP] {k}: " + ", ".join(f"{t} line {n}" for t, n in v))
        if dup: bad = 1
        else: print("  [PASS] every order name is used by exactly one statement")
    return bad

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
