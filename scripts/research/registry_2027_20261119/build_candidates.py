"""Build 2027 holiday-registry candidates for the live strategies (2026-11-19).

Each candidate = its base file + (1) Holiday_Tail[64]..[74] for 2027, (2) Registry_Valid_Until
1270101 -> 1271231, (3) header / comment notes. No other code change. The bases are the versions
Willy reported running live on 11/19 (L1 V3.8, L2 v5.12, L3 v18.4, L4 v14.10, L5 v19.20); the
output version is V1.1.0 for all five (Willy 11/19: 2nd live test, 1st = V1.0).

Source: TAIFEX 116 calendar, letter 1150003597 (2026-11-10). Rule (same as 2026): tail = last
trading day before a closure + 1 calendar day = Date of the after-midnight night-session bars.
The independent check is tests/test_registry_2027_candidates.py (derives the tails from the
closed-day list and diffs the comment-stripped code against the base).

Usage:  python scripts/research/registry_2027_20261119/build_candidates.py
Writes each .pla plus an identical .txt, and a unified diff per candidate under diffs/.
Refuses to overwrite a candidate that already exists unless --force is given.
"""
import difflib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
DATE = "2026-11-19"

# (index, tail, comment) - comments say which closure and which last trading day ("eve")
ROWS_2027 = [
    (64, 1270202, "CNY: last trading day Mon 2/1, closed 2/2-2/10"),
    (65, 1270227, "228: Mon 3/1 off (2/28 Sun), eve Fri 2/26, Saturday tail"),
    (66, 1270403, "Children/Tomb 4/5-4/6 off (4/4 Sun), eve Fri 4/2, Saturday tail"),
    (67, 1270430, "Labor: Fri 4/30 off (5/1 Sat), eve Thu 4/29"),
    (68, 1270609, "Dragon Boat Wed 6/9, eve Tue 6/8"),
    (69, 1270915, "Mid-Autumn Wed 9/15, eve Tue 9/14 (3rd Wed: settlement Thu 9/16)"),
    (70, 1270928, "Teachers Tue 9/28, eve Mon 9/27"),
    (71, 1271009, "National: Mon 10/11 off (10/10 Sun), eve Fri 10/8, Saturday tail"),
    (72, 1271023, "Retrocession Mon 10/25, eve Fri 10/22, Saturday tail"),
    (73, 1271224, "Constitution: Fri 12/24 off (12/25 Sat), eve Thu 12/23"),
    (74, 1271231, "2028 New Year: Fri 12/31 off (1/1 Sat), eve Thu 12/30"),
]
NEW_HORIZON = 1271231
SOURCE = "TAIFEX 116-yr calendar, letter 1150003597, 2026-11-10"
GAP = ("KNOWN GAP: 2027-09-15 (3rd Wed) is a holiday and settlement",
       "moves to Thu 2027-09-16; the 3rd-Wednesday rule does not",
       "flatten on 09-16. Fix before 2027-09.")


def verbose_rows(indent):
    out = [f"{indent}{{ --- 2027 ({SOURCE}) --- }}"]
    for i, d, c in ROWS_2027:
        out.append(f"{indent}Holiday_Tail[{i}] = {d};  {{ {c} }}")
    return out


def compact_rows(indent):
    out = [f"{indent}{{ 2027 ({SOURCE}).",
           f"{indent}  Tail = last trading day + 1; Saturday tail = Monday holiday.",
           f"{indent}  0202 CNY (last day Mon 2/1); 0227 228; 0403 Children/Tomb;",
           f"{indent}  0430 Labor; 0609 Dragon Boat; 0915 Mid-Autumn (3rd Wed,",
           f"{indent}  settlement Thu 9/16); 0928 Teachers; 1009 National;",
           f"{indent}  1023 Retrocession; 1224 Constitution; 1231 2028 New Year. }}"]
    rows = [f"Holiday_Tail[{i}] = {d};" for i, d, _ in ROWS_2027]
    for k in range(0, len(rows), 2):
        out.append(indent + "  ".join(rows[k:k + 2]))
    return out


def note(lead, width_pad, ver, base_ver, reb_off=False):
    """Version note lines; lead = text before the version label, width_pad = continuation indent."""
    if reb_off:      # L2 only (Willy 11/19 "關掉"): TS_Rebound default off, as decided 11/16
        what = [f"{base_ver} + 2027 holiday registry + one default",
                f"({SOURCE}):",
                "Holiday_Tail[64]-[74] added (11 rows), Registry_Valid_Until",
                "1270101 -> 1271231; Reb_On default 1 -> 0 (TS_Rebound off,",
                "Willy 11/19 = his 11/16 decision). No other code change.",
                "After saving under the live name, set the chart inputs",
                "Registry_Valid_Until = 1271231 AND Reb_On = 0 (MC keeps the",
                "old chart input values 1270101 / 1)."]
    else:
        what = [f"{base_ver} + 2027 holiday registry only",
                f"({SOURCE}):",
                "Holiday_Tail[64]-[74] added (11 rows), Registry_Valid_Until",
                "1270101 -> 1271231. No other code change; trades before",
                "2027-02-02 are unchanged. After saving under the live name,",
                "check the chart input Registry_Valid_Until = 1271231 (MC can",
                "keep the old input value 1270101)."]
    body = [*what,
            "Numbering (Willy 2026-11-19): V1.x.y = live version (1st live",
            "test V1.0, 2nd live test V1.1.0); V0.x.y = development.",
            *GAP]
    first = f"{lead}{ver} (11/19) "
    return [first + body[0]] + [width_pad + b for b in body[1:]]


# name, base, out version, header replacements, insert-after-version-line, row style
# 11/19 Willy: live = L1 V3.8, L2 v5.12, L3 v18.4, L4 v14.10, L5 v19.20 (2nd live test); with the
# 2027 holidays the live version number becomes V1.1.0 for all five (1st live test = V1.0, failed).
# (The earlier v*.1 names of this morning were never deployed and are replaced by V1.1.0.)
SPECS = [
    dict(name="L1_TrendLong", ver="v1.1.0",
         base="strategies/research/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla",
         head=[("  L1 TREND LONG (Adaptive Farmer)  -  V3.8  (2026-10-03)",
                "  L1 TREND LONG (Adaptive Farmer)  -  V1.1.0  (2026-11-19; logic = V3.8)"),
               ("  Source: TAIFEX annual calendars (2026 verified). ===== }",
                "  Source: TAIFEX annual calendars (2026 verified; 2027 from the 116-yr\n"
                "  calendar, letter 1150003597). ===== }")],
         after="  VERSION", note=("   ", " " * 16, "V3.8"), style="verbose"),
    dict(name="L2_TrendShort", ver="v1.1.0",
         # 11/19 live-machine export: = research v5.12 except Reb_On default 1 (research 0) and 2 comment
         # lines -> V1.1.0 is built from the live code itself.
         base="strategies/live_machine_snapshot/20261119/L2_TrendShort_live.txt",
         head=[("  L2 TREND SHORT (Adaptive Farmer)  -  v5.12  (2026-11-16, RESEARCH)\n"
                "  MC Load Name : Trendbearish_V1_RESEARCH  (research alias). The live name\n"
                "                 Trendbearish_V1 is used ONLY after Willy approves and the\n"
                "                 chart and broker are both flat.",
                "  L2 TREND SHORT (Adaptive Farmer)  -  V1.1.0  (2026-11-19; logic = v5.12)\n"
                "  MC Load Name : Trendbearish_V1  (live name). Backtest / dry run under\n"
                "                 an alias first; save under the live name ONLY when flat."),
               # Willy 11/19 "關掉": -8% rebound breakeven off (= his 11/16 13:34 decision)
               ("   Reb_On                 ( 1 ),         { 1 = TS_Rebound on }",
                "   Reb_On                 ( 0 ),         { 1 = TS_Rebound on; off by default (Willy 11/16, 11/19) }")],
         after="  VERSION", note=("   ", " " * 17, "v5.12 (live code)"), style="verbose", reb_off=True),
    dict(name="L3_ConsolidationLong", ver="v1.1.0",
         base="strategies/research/L3_ConsolidationLong/L3_v18.4/L3_ConsolidationLong_v18.4.pla",
         head=[(" L3 CONSOLIDATION LONG (Adaptive Farmer)  -  v18.4  (2026-10-03)",
                " L3 CONSOLIDATION LONG (Adaptive Farmer)  -  V1.1.0  (2026-11-19; logic = v18.4)")],
         after=" VERSION", note=("  ", " " * 16, "v18.4"), style="compact"),
    dict(name="L4_ConsolidationShort", ver="v1.1.0",
         base="strategies/research/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla",
         head=[(" L4 CONSOLIDATION SHORT (Adaptive Farmer)  -  v14.10  (2026-10-03)",
                " L4 CONSOLIDATION SHORT (Adaptive Farmer)  -  V1.1.0  (2026-11-19; logic = v14.10)")],
         after=" VERSION", note=("  ", " " * 18, "v14.10"), style="compact"),
    dict(name="L5_BreakoutLong", ver="v1.1.0",
         base="strategies/research/L5_BreakoutLong/L5_v19.20/L5_BreakoutLong_v19.20.pla",
         head=[(" L5 BREAKOUT LONG (Adaptive Farmer)  -  v19.20  (2026-10-03)",
                " L5 BREAKOUT LONG (Adaptive Farmer)  -  V1.1.0  (2026-11-19; logic = v19.20)")],
         after=" VERSION", note=("  ", " " * 18, "v19.20"), style="compact"),
]


def build(spec):
    base = ROOT / spec["base"]
    raw0 = base.read_bytes()
    eol = "\r\n" if b"\r\n" in raw0 else "\n"           # keep the base file's line ending
    text = raw0.decode("ascii")
    assert text.count(eol) == text.count("\n"), f"{base}: mixed line endings"
    text = text.replace("\r\n", "\n")
    for old, new in spec["head"]:
        assert text.count(old) == 1, f"{spec['ver']}: header text not found once: {old!r}"
        text = text.replace(old, new)
    # registry horizon: the single input default
    pat = re.compile(r"(Registry_Valid_Until\s*\(\s*)1270101(\s*\))")
    assert len(pat.findall(text)) == 1, f"{spec['ver']}: Registry_Valid_Until default not found once"
    text = pat.sub(lambda m: f"{m.group(1)}{NEW_HORIZON}{m.group(2)}", text)
    lines = text.split("\n")
    # version note under the VERSION / CHANGELOG line
    vi = [i for i, s in enumerate(lines) if s == spec["after"]]
    assert len(vi) == 1, f"{spec['ver']}: version anchor {spec['after']!r} not found once"
    lead, pad, base_ver = spec["note"]
    ver_label = "V" + spec["ver"][1:]                 # V1.1.0 (Willy 11/19 numbering)
    lines[vi[0] + 1:vi[0] + 1] = note(lead, pad, ver_label, base_ver, spec.get("reb_off", False))
    # 2027 rows right after the line holding Holiday_Tail[63] = 1270101
    hi = [i for i, s in enumerate(lines) if re.search(r"Holiday_Tail\[63\]\s*=\s*1270101;", s)]
    assert len(hi) == 1, f"{spec['ver']}: Holiday_Tail[63] anchor not found once"
    indent = re.match(r"\s*", lines[hi[0]]).group(0)
    rows = verbose_rows(indent) if spec["style"] == "verbose" else compact_rows(indent)
    lines[hi[0] + 1:hi[0] + 1] = rows
    out = eol.join(lines)
    raw = out.encode("ascii")                      # MC only takes ASCII
    code = spec["name"].split("_")[0]                # L1 ... L5
    folder = ROOT / "strategies/research" / spec["name"] / f"{code}_{spec['ver']}"
    pla = folder / f"{spec['name']}_{spec['ver']}.pla"
    return base, pla, raw


def main(force=False):
    (HERE / "diffs").mkdir(exist_ok=True)
    sys.path.insert(0, str(HERE))
    from slim_comments import INFO, slim          # 11/19 Willy: condensed comments, code unchanged
    for spec in SPECS:
        base, pla, raw = build(spec)
        raw = slim(raw.decode("ascii"), INFO[spec["name"]]).encode("ascii")
        if pla.exists() and not force:
            if pla.read_bytes() == raw and pla.with_suffix(".txt").read_bytes() == raw:
                print(f"same      {pla.relative_to(ROOT).as_posix()}"); continue
            sys.exit(f"exists and differs (use --force): {pla}")
        pla.parent.mkdir(parents=True, exist_ok=True)
        pla.write_bytes(raw)
        pla.with_suffix(".txt").write_bytes(raw)
        a = base.read_bytes().decode("ascii").replace("\r\n", "\n").split("\n")
        b = raw.decode("ascii").replace("\r\n", "\n").split("\n")
        diff = difflib.unified_diff(a, b, base.relative_to(ROOT).as_posix(), pla.relative_to(ROOT).as_posix(), lineterm="", n=1)
        (HERE / "diffs" / f"{pla.stem}.diff").write_text("\n".join(diff) + "\n", encoding="ascii")
        print(f"written   {pla.relative_to(ROOT).as_posix()}  ({len(a)} -> {len(b)} lines)")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
