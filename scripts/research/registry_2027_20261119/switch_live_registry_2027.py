"""Repo switch: the five live strategies -> 2027 holiday-registry version V1.1.0, all at once.

Run ONLY after Willy has switched all five in MC (each compiled under its live name while the chart
and the broker were flat, input Registry_Valid_Until checked = 1271231). Tier 1: Willy runs it.

  python scripts/research/registry_2027_20261119/switch_live_registry_2027.py --date 20261225            dry run
  python scripts/research/registry_2027_20261119/switch_live_registry_2027.py --date 20261225 --apply    do it
  verify.bat                                                                                               expect ALL PASS
  push.bat "2027 holiday registry: five live strategies switched"

--date = the day the MC switch was done (YYYYMMDD).

The repo L1 / L2 live files were never synced to what MC ran (L1 holds V3.1 content, L2 v5.11); the code
MC really ran before V1.1.0 is the 11/19 live-machine export in strategies/live_machine_snapshot/20261119/.
V1.1.0 is built from that export, so no intermediate sync is needed.

--apply only if every check passes (otherwise nothing is written):
  1. each strategies/live/<name>/<name>.pla must be a known current file
     (L1 = the V3.1-content file or research v3.8; L2 v5.11 or v5.12; L3 v18.4; L4 v14.10; L5 v19.20)
     -> strategies/research/archive/live_until_<date>/<name>_<version>.pla
  2. strategies/research/<name>/<code>_v1.1.0/<name>_v1.1.0.pla -> strategies/live/<name>/<name>.pla (byte copy)
  3. text: LIVE_VERSIONS (last-check line, section 1 rows, note, section 1.1a status), tools/live_exceptions.txt
     (L1 line removed: L1 live = research V1.1.0 now), strategies/live/README.md rows, PROJECT.md
     (last-updated, live line, decision log appended at the end), DEPT_OPS live line,
     docs/decisions/registry_2027_20261119.md (execution record appended).
Optional edits (skipped with a note if their old text is already gone): the L1 "version unconfirmed"
notes in LIVE_VERSIONS and PROJECT.md, "登錄表到期 2027/1/1" in PROJECT.md, the 63 / 1270101 rows of the
shared-module table in strategies/live/README.md.
"""
import argparse, datetime, difflib, hashlib, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
RES = "strategies/research"
# strategies/live/L1_TrendLong/L1_TrendLong.pla as of 2026-11-19 (V3.1 content; MC runs V3.8)
L1_FILE_SHA = "4d9ad2799f7031be"
LIVE_NAMES = "五支 V1.1.0（第二次上架測試）"
LOGIC = "交易邏輯 ＝ L1 V3.8、L2 v5.12、L3 v18.4、L4 v14.10、L5 v19.20"
NEW = "v1.1.0"          # folder / file spelling (G0b R6 builds research paths with a lower-case v)
SHOW = "V1.1.0"         # Willy 11/19 numbering: V1.x.y = live version, 1st live test V1.0, 2nd = V1.1.0

# name, version MC ran before (text), new version, known current repo files {label: research path or None}
STRATS = [
    ("L1_TrendLong", "V3.8", NEW, {"v3.1": None, "v3.8": f"{RES}/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla"}),
    ("L2_TrendShort", "v5.12", NEW, {"v5.11": f"{RES}/L2_TrendShort/L2_v5.11/L2_TrendShort_v5.11.pla",
                                     "v5.12": f"{RES}/L2_TrendShort/L2_v5.12/L2_TrendShort_v5.12.pla"}),
    ("L3_ConsolidationLong", "v18.4", NEW,
     {"v18.4": f"{RES}/L3_ConsolidationLong/L3_v18.4/L3_ConsolidationLong_v18.4.pla"}),
    ("L4_ConsolidationShort", "v14.10", NEW,
     {"v14.10": f"{RES}/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla"}),
    ("L5_BreakoutLong", "v19.20", NEW,
     {"v19.20": f"{RES}/L5_BreakoutLong/L5_v19.20/L5_BreakoutLong_v19.20.pla"}),
]
README_ROW = {"L1_TrendLong": "| **L1** TrendLong |", "L2_TrendShort": "| **L2** TrendShort |",
              "L3_ConsolidationLong": "| **L3** ConsolidationLong |",
              "L4_ConsolidationShort": "| **L4** ConsolidationShort |", "L5_BreakoutLong": "| **L5** BreakoutLong |"}
LOAD = {"L1_TrendLong": "WILLY_ATR_LONG_60M", "L2_TrendShort": "Trendbearish_V1",
        "L3_ConsolidationLong": "STRATEGY_WILLY_LONG_C", "L4_ConsolidationShort": "STRATEGY_WILLY_SHORT_CTEST2",
        "L5_BreakoutLong": "STRATEGY_WILLY_LONG_BREAKOUT_C"}


def cand(name, ver):
    code = name.split("_")[0]
    return ROOT / RES / name / f"{code}_{ver}" / f"{name}_{ver}.pla"


def read(rel):
    """Text with '\\n' line ends + the file's own line ending."""
    b = (ROOT / rel).read_bytes()
    eol = "\r\n" if b"\r\n" in b else "\n"
    return b.decode("utf-8").replace("\r\n", "\n"), eol


def write(rel, text, eol):
    (ROOT / rel).write_bytes(text.replace("\n", eol).encode("utf-8"))


def section(text, start, errs, label):
    """(begin, end) of the block that starts at the line `start` and ends at the next heading."""
    i = text.find("\n" + start)
    if i < 0:
        errs.append(f"{label}: heading not found: {start!r}")
        return None
    j = re.compile(r"\n#{2,3} ").search(text, i + 1 + len(start))
    return i + 1, (j.start() + 1 if j else len(text))


def sub_once(text, pattern, repl, errs, label, flags=re.M):
    new, n = re.subn(pattern, repl, text, count=0, flags=flags)
    if n != 1:
        errs.append(f"{label}: pattern found {n} times: {pattern[:60]!r}")
        return text
    return new


def plan(date, apply_date_text):
    d = apply_date_text
    errs, notes, moves, texts = [], [], [], {}
    arch_dir = ROOT / RES / "archive" / f"live_until_{date}"

    # ---- files
    for name, mc_old, new, known in STRATS:
        live = ROOT / "strategies" / "live" / name / f"{name}.pla"
        c = cand(name, new)
        if not live.exists():
            errs.append(f"missing {live}"); continue
        if not c.exists() or not c.with_suffix(".txt").exists():
            errs.append(f"missing candidate {c} (+ .txt)"); continue
        cb = c.read_bytes()
        if max(cb) > 127: errs.append(f"{c.name} is not ASCII")
        if cb != c.with_suffix(".txt").read_bytes(): errs.append(f"{c.name}: .txt differs from .pla")
        lb = live.read_bytes()
        if lb == cb:
            errs.append(f"{name}: live file is already {new} (switch done?)"); continue
        label = None
        for lab, path in known.items():
            if path is None:
                if hashlib.sha256(lb).hexdigest().startswith(L1_FILE_SHA): label = lab
            elif lb == (ROOT / path).read_bytes():
                label = lab
        if label is None:
            hint = ""
            errs.append(f"{name}: live file is not a known current version ({', '.join(known)}){hint}")
            continue
        arch = arch_dir / f"{name}_{label}.pla"
        if arch.exists(): errs.append(f"archive target exists: {arch}")
        moves.append((name, live, arch, c, label, len(cb.splitlines())))

    # ---- LIVE_VERSIONS
    rel = "docs/LIVE_VERSIONS.md"
    t = read(rel)[0]
    t = sub_once(t, r"^\*\*最後校對：([^*]+)\*\*（",
                 lambda m: (f"**最後校對：{d}**（§1 五支換成 2027 假日表版：{LIVE_NAMES}；舊上架檔在 "
                            f"`strategies/research/archive/live_until_{date}/`）；前一次 {m.group(1)}（"),
                 errs, rel + " last-check line")
    sec = section(t, "## 1. LIVE", errs, rel)
    if sec:
        a, b = sec
        body = t[a:b]
        nlines = {m[0]: m[5] for m in moves}
        for name, mc_old, new, _ in STRATS:
            rows = re.findall(rf"^\| \*\*{name}\*\* \|.*$", body, flags=re.M)
            if len(rows) != 1:
                errs.append(f"{rel} section 1: {name} row found {len(rows)} times"); continue
            cells = [x.strip() for x in rows[0].strip().strip("|").split("|")]
            if len(cells) != 6:
                errs.append(f"{rel} section 1: {name} row has {len(cells)} cells, expected 6"); continue
            row = (f"| **{name}** | **{SHOW}**（{d} 起；＝ {mc_old} ＋ 2027 假日表） | `{LOAD[name]}` | "
                   f"{cells[3]} | {cells[4]} | {nlines.get(name, cells[5])} |")
            body = body.replace(rows[0], row)
        anchor = "**⚠ L1 的 MC Load Name 寫 `60M`"
        if body.count(anchor) != 1:
            errs.append(f"{rel} section 1: anchor found {body.count(anchor)} times: {anchor!r}")
        else:
            note = (f"- **2027 假日表換版（{d}）**：Willy 在 MC 換完五支（{LIVE_NAMES}；{LOGIC}，只加 2027 假日 11 筆、"
                    f"`Registry_Valid_Until` 1271231）。`strategies/live/` 換成這五個研究版原檔；舊上架檔在 "
                    f"`strategies/research/archive/live_until_{date}/`，回退用。決定：`docs/decisions/registry_2027_20261119.md`\n\n")
            body = body.replace(anchor, note + anchor)
        l1 = re.findall(r"^- \*\*⚠ L1 版本待確認.*$", body, flags=re.M)
        if len(l1) == 1:
            body = body.replace(l1[0], f"- L1 版本（{d} 更正）：Willy 11/19 確認實盤是 V3.8，{d} 換成 V1.1.0，"
                                       "`strategies/live/L1_TrendLong/` 已是 V1.1.0 原檔（原寫：L1 版本待確認，上架資料夾是 V3.1 檔）")
        else:
            notes.append(f"{rel}: L1 'version unconfirmed' note not found ({len(l1)}); left as is")
        t = t[:a] + body + t[b:]
    sec = section(t, "### 1.1a ", errs, rel)
    if sec:
        a, b = sec
        body = t[a:b]
        if body.count("| 排定 |") != 5:
            errs.append(f"{rel} section 1.1a: '| 排定 |' found {body.count('| 排定 |')} times, expected 5")
        else:
            t = t[:a] + body.replace("| 排定 |", f"| **已換版 {d}** |") + t[b:]
    texts[rel] = t

    # ---- live exceptions: L1 live = research V1.1.0 now
    rel = "tools/live_exceptions.txt"
    t = read(rel)[0]
    texts[rel] = "\n".join(l for l in t.split("\n") if not l.startswith("L1_TrendLong"))

    # ---- strategies/live/README.md
    rel = "strategies/live/README.md"
    t = read(rel)[0]
    for name, mc_old, new, _ in STRATS:
        rows = [l for l in t.split("\n") if l.startswith(README_ROW[name])]
        if len(rows) != 1:
            errs.append(f"{rel}: {name} row found {len(rows)} times"); continue
        cells = rows[0].split(" | ")
        if len(cells) < 5:
            errs.append(f"{rel}: {name} row has too few cells"); continue
        cells[3] = f"**{SHOW}**（{d} 起；＝ {mc_old} ＋ 2027 假日表）"
        t = t.replace(rows[0], " | ".join(cells))
    texts[rel] = t

    # ---- PROJECT.md
    rel = "PROJECT.md"
    t = read(rel)[0]
    t = sub_once(t, r"^- 最後更新：.*$", f"- 最後更新：{d}", errs, rel + " last-updated")
    t = sub_once(t, r"^  - MC 實盤五支：.*$",
                 f"  - MC 實盤五支：{LIVE_NAMES}（{d} 換 2027 假日表；{LOGIC}）；下單經下單大師", errs, rel + " live line")
    l1 = re.findall(r"^  - L1 (?:實盤是 V3\.8|實際版本待確認).*\n", t, flags=re.M)
    if len(l1) == 1:
        t = t.replace(l1[0], "")
    else:
        notes.append(f"{rel}: L1 note line not found ({len(l1)}); left as is")
    sec = section(t, "## 決策紀錄", errs, rel)
    if sec:
        a, b = sec
        body = t[a:b].rstrip("\n")
        line = (f"- {d}｜決定：（Willy 執行 11/19 的決定）MC 五支換成 2027 假日表版（{LIVE_NAMES}）；repo 同步："
                f"舊上架檔移到 `strategies/research/archive/live_until_{date}/`，`strategies/live` 換成研究版原檔"
                f"｜原因：`Registry_Valid_Until` 1270101 到期（`docs/decisions/registry_2027_20261119.md`）｜放棄的選項：無")
        t = t[:a] + body + "\n\n" + line + "\n\n" + t[b:]
    texts[rel] = t

    # ---- L2 exits that go live with V1.1.0 (v5.12 logic) - DEPT_RISK and the order-name list
    for rel, anchor, add in [
        ("docs/departments/DEPT_RISK.md", "- **R2 帳戶層**：",
         f"- **L2 極端日出場（V1.1.0，{d} 起；v5.12 邏輯）**：v5.11 出場鏈之外另掛三張單：用 K 棒最低點算的最高獲利 ≥ 2,500 點後保留 70%"
         "（`TS_SPTier`）、跌停先走（前一個 13:45 收盤 × 90.2% 買限價，`TS_LimitDn`）、−8% 回升保本（`TS_Rebound`；"
         "V1.1.0 預設關 `Reb_On` 0，Willy 11/19「關掉」，見 `docs/decisions/registry_2027_20261119.md`）\n"),
        ("docs/ops/order_names_L1-L5_20261004.md", "## L2 v5.11（18 個）\n",
         f"> {d}：L2 換成 V1.1.0（v5.12 邏輯），比 v5.11 多 3 個出場單名 `TS_SPTier`、`TS_LimitDn`、`TS_Rebound`"
         "（`tools/check_order_names.py`：17 個 → 20 個）；下單大師對應要有這 3 個。\n\n"),
    ]:
        texts.setdefault(rel, read(rel)[0])
        if texts[rel].count(anchor) == 1:
            texts[rel] = texts[rel].replace(anchor, add + anchor)
        else:
            notes.append(f"{rel}: anchor {anchor!r} found {texts[rel].count(anchor)} times; L2 exit note not added")

    # ---- optional one-line facts (skipped with a note when the old text is already gone)
    for rel, old, new in [
        ("PROJECT.md", "登錄表到期 2027/1/1", f"登錄表到期 2027/12/31（{d} 換 2027 假日表）"),
        ("strategies/live/README.md", "| Holiday_Tail[80] 63 筆 TAIFEX 登錄表 |",
         f"| Holiday_Tail[80] 74 筆 TAIFEX 登錄表（{d} 起，到 2027 年底） |"),
        ("strategies/live/README.md", "| Registry_Valid_Until = 1270101 |", "| Registry_Valid_Until = 1271231 |"),
    ]:
        t = texts[rel]
        if t.count(old) == 1:
            texts[rel] = t.replace(old, new)
        else:
            notes.append(f"{rel}: {old!r} found {t.count(old)} times; left as is")

    # ---- DEPT_OPS
    rel = "docs/departments/DEPT_OPS.md"
    t = read(rel)[0]
    texts[rel] = sub_once(t, r"^- \*\*上架現況（[^）]*）\*\*：.*$",
                          f"- **上架現況（{d} 更新）**：五支換成 2027 假日表版（{LIVE_NAMES}；{LOGIC}），"
                          "`Registry_Valid_Until` 1271231（2028 年曆公布後再換）。版本以 `docs/LIVE_VERSIONS.md` 為準",
                          errs, rel + " live line")

    # ---- decision record
    rel = "docs/decisions/registry_2027_20261119.md"
    t = read(rel)[0]
    texts[rel] = t.rstrip("\n") + (
        f"\n\n## 執行紀錄（{d}）\n\n"
        f"- MC：Willy {d} 換完五支（{LIVE_NAMES}）\n"
        f"- repo：舊上架檔 → `strategies/research/archive/live_until_{date}/`"
        f"（{'、'.join(f'{m[0]}_{m[4]}.pla' for m in moves)}）；`strategies/live/` ＝ 五個研究版原檔\n"
        "- `tools/live_exceptions.txt` 的 L1 例外刪除（L1 上架檔 ＝ 研究版 V1.1.0）\n")
    return errs, notes, moves, texts


def main():
    ap = argparse.ArgumentParser(description="2027 holiday-registry repo switch (five live strategies)")
    ap.add_argument("--date", required=True, help="MC switch day, YYYYMMDD")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    try:
        day = datetime.datetime.strptime(a.date, "%Y%m%d").date()
    except ValueError:
        print("[STOP] --date must be YYYYMMDD"); return 1
    if not datetime.date(2026, 11, 19) <= day <= datetime.date.today():
        print(f"[STOP] --date {a.date} must be between 2026-11-19 and today"); return 1
    if day > datetime.date(2027, 1, 4):
        print("! note: after 2027-01-04 08:45 the old versions were blocking entries (registry expired)")
    errs, notes, moves, texts = plan(a.date, day.isoformat())
    for name, live, arch, c, label, n in moves:
        print(f"move  {live.relative_to(ROOT).as_posix()}  ({label})  -> {arch.relative_to(ROOT).as_posix()}")
        print(f"copy  {c.relative_to(ROOT).as_posix()}  ({n} lines)  -> {live.relative_to(ROOT).as_posix()}")
    for rel, t in texts.items():
        old = read(rel)[0].split("\n")
        for line in difflib.unified_diff(old, t.split("\n"), rel, rel, lineterm="", n=0):
            print(line if len(line) < 220 else line[:217] + "...")
    for n_ in notes:
        print("  note: " + n_)
    if errs or len(moves) != 5:
        print("[STOP] nothing written:")
        for e in errs: print("    x " + e)
        return 1
    if not a.apply:
        print("[DRY RUN OK] all checks pass; run again with --apply"); return 0
    for name, live, arch, c, label, n in moves:
        arch.parent.mkdir(parents=True, exist_ok=True)
        before = live.read_bytes()
        shutil.move(str(live), str(arch))
        shutil.copyfile(c, live)
        assert live.read_bytes() == c.read_bytes() and arch.read_bytes() == before
    for rel, t in texts.items():
        write(rel, t, read(rel)[1])
    print("[APPLIED] now run verify.bat (expect ALL PASS), then push.bat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
