"""Condense the comments of a live .pla (Willy 2026-11-19: 「精簡化註解，同時讓篇幅縮減」). Code is not touched.

slim(text, info) returns the same program with:
  1. header: title, MC load name, data, what this version changed, known gap + the LOGIC section of the
     old header kept word for word; version history and old verify numbers dropped (they live in git
     and docs/LIVE_VERSIONS.md)
  2. Holiday_Tail table: 4 assignments per line, one comment line (same statements, same order)
  3. comments spanning several lines -> one line (long ones cut at a sentence end)
  4. runs of blank lines -> one; trailing spaces removed
The caller checks that the comment-stripped program is unchanged (tests/test_registry_2027_candidates.py).
"""
import re

ROW = re.compile(r"Holiday_Tail\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)\s*;")


def _blocks(t):
    """(start, end) of every top-level { } comment, string-aware (same rule as tools/verify_static.py)."""
    out, depth, start, in_str = [], 0, 0, False
    for i, ch in enumerate(t):
        if depth == 0 and ch == '"':
            in_str = not in_str
        elif not in_str and ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif not in_str and ch == "}" and depth > 0:
            depth -= 1
            if depth == 0:
                out.append((start, i + 1))
    return out


def _one_line(body, limit):
    """'{ a \\n b }' -> '{ a b }'; if longer than limit, keep whole sentences that fit."""
    inner = re.sub(r"\s+", " ", body[1:-1]).strip()
    banner = inner.startswith("=====") and inner.endswith("=====")
    if len(inner) + 4 > limit:
        parts = re.split(r"(?<=[.;:])\s", inner)
        keep = ""
        for p in parts:
            if len(keep) + len(p) + 5 > limit:
                break
            keep = (keep + " " + p).strip()
        inner = keep or inner          # nothing fits: keep it whole rather than cut a word
        if banner and not inner.endswith("====="):
            inner = inner.rstrip(".;:") + " ====="
    return "{ " + inner + " }"


def _header(t, info):
    a, b = _blocks(t)[0]
    assert t[:a].strip() == "", "file must start with the header comment"
    lines = t[a:b].split("\n")
    li = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("LOGIC"))
    logic = lines[li:-1]
    w = info
    head = ["{ " + "=" * 74,
            f"  {w['title']}  -  V1.1.0  (2026-11-19; logic = {w['logic']})",
            f"  MC Load Name : {w['load']}",
            "                 Test under an alias; compile the live name only when the",
            "                 chart and the broker are both flat.",
            f"  Data         : {w['data']}",
            "  V1.1.0       : 2027 holiday rows Holiday_Tail[64]-[74] (TAIFEX 116-yr",
            "                 calendar, letter 1150003597) + Registry_Valid_Until 1271231" + w.get("extra", "") + ".",
            "                 Chart inputs after the switch: " + w["inputs"] + ".",
            "  Known gap    : 2027-09-16 settlement (moved from Wed 9/15) is not flattened.",
            *logic,
            "  " + "=" * 74 + " }"]
    return "\n".join(head) + t[b:]


def _table(t):
    rows = list(ROW.finditer(t))
    idx = [int(m.group(1)) for m in rows]
    assert idx == list(range(1, len(idx) + 1)), "Holiday_Tail rows must be 1..N in order"
    first, last = rows[0], rows[-1]
    ls = t.rfind("\n", 0, first.start()) + 1
    indent = re.match(r"[ \t]*", t[ls:]).group(0)
    prefix = t[ls:first.start()]
    # a year label on its own line right above row 1 (e.g. "{ --- 2019 --- }") belongs to the table
    while ls > 0:
        pl = t.rfind("\n", 0, ls - 1) + 1
        if not re.fullmatch(r"[ \t]*\{[\s-]*20\d\d[^{}]*\}[ \t]*", t[pl:ls - 1]):
            break
        ls = pl
    le = t.find("\n", last.end())
    le = len(t) if le < 0 else le
    span = t[ls:le]
    from_code = re.sub(r"\{[^{}]*\}", " ", span)
    assert prefix.strip() == "" or prefix.strip().startswith("{"), "unexpected code before Holiday_Tail[1]"
    assert re.sub(r"\s+", "", ROW.sub("", from_code)) == "", "only Holiday_Tail rows and comments may sit in the table"
    stmts = [f"Holiday_Tail[{i}] = {d};" for i, d in ((int(m.group(1)), m.group(2)) for m in rows)]
    out = [indent + "{ last trading day + 1 before each closure, 2019-2027 (TAIFEX calendars) }"]
    for k in range(0, len(stmts), 3):
        out.append(indent + "  ".join(stmts[k:k + 3]))
    return t[:ls] + "\n".join(out) + t[le:]


VTAG = re.compile(r"^\{\s*v\d+(\.\d+)+\s*\}$")                 # "{ v19.11 }": old version marker only
VPRE = re.compile(r"^\{\s*v\d+(\.\d+)+[a-zA-Z]?\s*[:,]?\s*")       # "{ v19.7: Freeze ..." -> "{ Freeze ..."
VTOK = re.compile(r"(?<![\w.])[vV]\d+\.\d+[a-zA-Z]?(?![\w.])\s*:?\s*(?=\S)")   # "[SEC-7] v19.7 Frozen" -> "[SEC-7] Frozen"


VAR1 = re.compile(r"^([ \t]*)([A-Za-z_]\w*\s*\([^(){}\"]*\))\s*,\s*$")   # one plain declaration per line


def _pack_vars(t, width=92):
    """In the variables block, put runs of plain one-per-line declarations side by side (same order)."""
    m = re.search(r"(?im)^[ \t]*(variables|vars)[ \t]*:", t)
    if not m:
        return t
    end = t.find(";", m.end())
    while _in_comment(t, end):
        end = t.find(";", end + 1)
    head, block, tail = t[:m.end()], t[m.end():end], t[end:]
    out, run, ind = [], [], ""

    def flush():
        line = ""
        for item in run:
            piece = item + ","
            if line and len(ind) + len(line) + 1 + len(piece) > width:
                out.append(ind + line)
                line = ""
            line = piece if not line else line + " " + piece
        if line:
            out.append(ind + line)
        run.clear()

    for l in block.split("\n"):
        v = VAR1.match(l)
        if v and (not run or v.group(1) == ind):
            ind = v.group(1)
            run.append(v.group(2).strip())
            continue
        flush()
        if v:
            ind = v.group(1); run.append(v.group(2).strip()); continue
        out.append(l)
    flush()
    return head + "\n".join(out) + tail


def _in_comment(t, pos):
    return any(a <= pos < b for a, b in _blocks(t))


def _blank_lines(t):
    """Keep a blank line only in front of a comment-only line or a declaration block; drop the rest."""
    lines, out = t.split("\n"), []
    for i, l in enumerate(lines):
        if l.strip():
            out.append(l)
            continue
        nxt = next((x.strip() for x in lines[i + 1:] if x.strip()), "")
        if (nxt.startswith("{") and nxt.endswith("}")) or re.match(r"(?i)(inputs|variables|vars|arrays)\s*:", nxt) \
                or nxt.startswith("["):
            if out and out[-1].strip():
                out.append("")
    return "\n".join(out)


def _comments(t):
    out, pos = [], 0
    for a, b in _blocks(t):
        out.append(t[pos:a])
        body = t[a:b]
        ls = t.rfind("\n", 0, a) + 1
        le = t.find("\n", b)
        le = len(t) if le < 0 else le
        trailing = t[ls:a].strip() != ""
        own_line = not trailing and t[b:le].strip() == ""
        body = _one_line(body, 70 if trailing else 110) if "\n" in body else body
        if VTAG.match(body) and own_line:
            out[-1] = out[-1][:len(out[-1]) - (a - ls)]       # drop the indent, the comment
            pos = min(le + 1, len(t))                         # and its line break: the line is gone
            continue
        body = VPRE.sub("{ ", body)
        body = VTOK.sub("", body)                             # old version labels inside the text
        out.append(body)
        pos = b
    out.append(t[pos:])
    return "".join(out)


def slim(text, info):
    nl = "\r\n" if "\r\n" in text else "\n"
    t = text.replace("\r\n", "\n")
    t = _header(t, info)
    a, b = _blocks(t)[0]
    t = t[:b] + _comments(_table(t[b:]))
    t = "\n".join(l.rstrip() for l in t.split("\n"))
    t = _pack_vars(t)
    t = _blank_lines(t).rstrip("\n") + "\n"
    return t.replace("\n", nl)


INFO = {
    "L1_TrendLong": dict(title="L1 TREND LONG (Adaptive Farmer)", logic="V3.8",
                         load="WILLY_ATR_LONG_60M  (live name; the chart is 45M, name kept)",
                         data="Data1 TXF1 45M / Data2 daily / Data3 weekly. IOG = true. 2 lots.",
                         inputs="Registry_Valid_Until = 1271231"),
    "L2_TrendShort": dict(title="L2 TREND SHORT (Adaptive Farmer)", logic="v5.12",
                          load="Trendbearish_V1  (live name)",
                          data="TXF1 60M, one stream, day + night. IOG off. 2 lots.\n"
                               "                 Chart history >= 13 weeks.",
                          extra="\n                 + Reb_On 0 (TS_Rebound off; Willy 11/19, as decided 11/16)",
                          inputs="Registry_Valid_Until = 1271231\n                 and Reb_On = 0"),
    "L3_ConsolidationLong": dict(title="L3 CONSOLIDATION LONG (Adaptive Farmer)", logic="v18.4",
                                 load="STRATEGY_WILLY_LONG_C  (live name)",
                                 data="Data1 TXF1 15M / Data2 60M / Data3 daily. IOG off. 2 lots.",
                                 inputs="Registry_Valid_Until = 1271231"),
    "L4_ConsolidationShort": dict(title="L4 CONSOLIDATION SHORT (Adaptive Farmer)", logic="v14.10",
                                  load="STRATEGY_WILLY_SHORT_CTEST2  (live name)",
                                  data="Data1 TXF1 15M / Data2 60M / Data3 daily. IOG off. 2 lots.",
                                  inputs="Registry_Valid_Until = 1271231"),
    "L5_BreakoutLong": dict(title="L5 BREAKOUT LONG (Adaptive Farmer)", logic="v19.20",
                            load="STRATEGY_WILLY_LONG_BREAKOUT_C  (live name)",
                            data="Data1 TXF1 15M / Data2 daily / Data3 weekly. IOG off. 2 lots.",
                            inputs="Registry_Valid_Until = 1271231"),
}
