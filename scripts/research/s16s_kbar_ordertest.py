# -*- coding: ascii -*-
"""
S16_S K-bar selector -- does test ORDER change any decision?

T5 in s16s_kbar_unittest.py showed six patterns get reported under another
pattern's code. That raised the obvious question and it has to be answered
before anything is refactored:

    HYPOTHESIS  the cascade's order affects only the diagnostic NAME, never
                the block/allow decision, because the cascade

                    if v_KB_Code = 0 and <cond_n> then v_KB_Code = n;

                sets a non-zero code if and only if ANY enabled cond_n is
                true, which is an OR and an OR does not care about order.

    RISK        the group blocks are nested and guarded separately
                (v_KB_Sup / v_KB_Opp / v_KB_Neu), and each pattern also
                carries its own v_Bars_In_Sess guard. Either could break the
                equivalence in a way inspection would miss.

This file tests the hypothesis by brute force on random bars rather than by
reading the code, which is the same discipline as the unit-test harness: the
conditions are parsed out of the shipped .pla, not retyped.

Three checks, over every combination of the three switches:

    C1  cascade result == plain OR of the enabled conditions
    C2  cascade result is unchanged under random permutations of the tests
        WITHIN each group
    C3  how often each pattern is the code REPORTED, under source order
        versus under most-specific-wins -- this quantifies the masking that
        T5 found, without needing the real data

Prices are small integers so the exact-equality patterns (tweezers, matching
high/low, three identical crows) actually occur.

Run:  python scripts/research/s16s_kbar_ordertest.py
"""
import os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from s16s_kbar_unittest import (load_source, extract_section, strip_comments,
                                parse_inputs, parse_rules, parse_helpers,
                                split_top_and, Env)

SEQ = 200000
SEED = 20260818

GROUP_OF = {}
for _c in range(1, 31):
    GROUP_OF[_c] = 'SUP' if _c <= 15 else ('OPP' if _c <= 28 else 'NEU')
GROUPS = ['SUP', 'OPP', 'NEU']
MEMBERS = dict((g, [c for c in range(1, 31) if GROUP_OF[c] == g]) for g in GROUPS)


def make_bars(rng, n):
    """n valid OHLC bars, integers, tight range so equalities happen."""
    out = []
    base = 100
    for _ in range(n):
        o = base + rng.randint(-6, 6)
        c = base + rng.randint(-6, 6)
        h = max(o, c) + rng.randint(0, 3)
        l = min(o, c) - rng.randint(0, 3)
        out.append((o, h, l, c))
        base = c
    return out


def main():
    src = load_source()
    sec = strip_comments(extract_section(src))
    thr = parse_inputs(src)
    rules = dict(parse_rules(sec))
    helpers = parse_helpers(sec)
    nclause = dict((c, len(split_top_and(e))) for c, e in rules.items())
    print('rules parsed: %d   sequences: %d   seed: %d' % (len(rules), SEQ, SEED))
    print()

    rng = random.Random(SEED)
    combos = [(s, o, n) for s in (0, 1) for o in (0, 1) for n in (0, 1)]

    fail_c1 = dict((k, 0) for k in combos)
    fail_c2 = dict((k, 0) for k in combos)
    nblock = dict((k, 0) for k in combos)
    report_src = dict((c, 0) for c in range(1, 31))
    report_spec = dict((c, 0) for c in range(1, 31))
    nfire_any = 0

    perms = []
    for _ in range(8):
        p = {}
        for g in GROUPS:
            m = list(MEMBERS[g])
            rng.shuffle(m)
            p[g] = m
        perms.append(p)

    for i in range(SEQ):
        bars = make_bars(rng, 5)
        e = Env(bars, thr)
        e.run_helpers(helpers)
        hit = set(c for c in range(1, 31) if e.ev(rules[c]) is True)

        if hit:
            nfire_any += 1
            # source order across groups then code
            w_src = sorted(hit, key=lambda c: (GROUPS.index(GROUP_OF[c]), c))[0]
            report_src[w_src] += 1
            # most-specific-wins: more top-level clauses beats fewer, tie by code
            w_spec = sorted(hit, key=lambda c: (-nclause[c], c))[0]
            report_spec[w_spec] += 1

        for k in combos:
            on = set()
            if k[0]:
                on |= set(MEMBERS['SUP'])
            if k[1]:
                on |= set(MEMBERS['OPP'])
            if k[2]:
                on |= set(MEMBERS['NEU'])

            # C1 -- the plain OR
            or_res = bool(hit & on)
            if or_res:
                nblock[k] += 1

            # cascade, source order
            code = 0
            for g, flag in zip(GROUPS, k):
                if not flag:
                    continue
                for c in MEMBERS[g]:
                    if code == 0 and c in hit:
                        code = c
            if (code != 0) != or_res:
                fail_c1[k] += 1

            # C2 -- cascade under permuted order within each group
            for p in perms:
                code2 = 0
                for g, flag in zip(GROUPS, k):
                    if not flag:
                        continue
                    for c in p[g]:
                        if code2 == 0 and c in hit:
                            code2 = c
                if (code2 != 0) != (code != 0):
                    fail_c2[k] += 1
                    break

    print('=' * 78)
    print(' C1  cascade == plain OR      C2  cascade invariant under 8 permutations')
    print('=' * 78)
    print('  %-5s %-5s %-5s   %9s   %8s   %8s' %
          ('SUP', 'OPP', 'NEU', 'blocked', 'C1 fail', 'C2 fail'))
    bad = 0
    for k in combos:
        bad += fail_c1[k] + fail_c2[k]
        print('  %-5d %-5d %-5d   %9d   %8d   %8d'
              % (k[0], k[1], k[2], nblock[k], fail_c1[k], fail_c2[k]))
    print()
    print('  sequences where at least one pattern fired: %d / %d  (%.2f%%)'
          % (nfire_any, SEQ, 100.0 * nfire_any / SEQ))

    print()
    print('=' * 78)
    print(' C3  which pattern gets REPORTED -- source order vs most-specific-wins')
    print('=' * 78)
    print('  %-4s %-10s %4s %10s %10s %10s' %
          ('code', 'group', 'cls', 'src order', 'specific', 'delta'))
    for c in range(1, 31):
        a, b = report_src[c], report_spec[c]
        if a == 0 and b == 0:
            continue
        print('  %-4d %-10s %4d %10d %10d %+10d'
              % (c, GROUP_OF[c], nclause[c], a, b, b - a))

    print()
    print('=' * 78)
    print(' VERDICT')
    print('=' * 78)
    if bad == 0:
        print('  HYPOTHESIS HOLDS. Over %d random 5-bar sequences x 8 switch'
              % SEQ)
        print('  combinations x 8 within-group permutations, the block/allow')
        print('  decision NEVER differed. Order is a diagnostic concern only.')
    else:
        print('  HYPOTHESIS REFUTED -- %d disagreements. Do not proceed.' % bad)
    print()
    print('  FAILURES: %d' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
