"""產生 L6_MACrossShort_v0.1.0（開發版）：＝L6 v1.0.0，只加「結算日遞延表」（2027 年第 3 個週三遇休市 → 順延到下一個營業日）。
遞延表由 data/taifex_market_closures.json 計算，只取 2027 年；Build_ID 2611193 → 2611201；其餘程式碼一字不動。
輸出 CRLF＋純 ASCII，.txt 與 .pla 相同。

Usage: python -I scripts/research/s16_streak_20261118/build_l6_v010.py
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "strategies/research/L6_MACrossShort/L6_v1.0.0/L6_MACrossShort_v1.0.0.pla"
OUT = ROOT / "strategies/research/L6_MACrossShort/L6_v0.1.0"
CLOSURES = ROOT / "data/taifex_market_closures.json"
YEAR = 2027
BUILD_OLD, BUILD_NEW = "2611193", "2611201"


def settle_deferrals(year: int = YEAR) -> list[tuple[dt.date, dt.date]]:
    closed = {x["date"] for x in json.loads(CLOSURES.read_text(encoding="utf-8"))["closed_weekdays"]}
    out = []
    for m in range(1, 13):
        wed = next(dt.date(year, m, k) for k in range(15, 22) if dt.date(year, m, k).weekday() == 2)
        if str(wed) in closed:
            nxt = wed + dt.timedelta(1)
            while nxt.weekday() > 4 or str(nxt) in closed:
                nxt += dt.timedelta(1)
            out.append((wed, nxt))
    return out


def mc(d: dt.date) -> int:
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


HEAD_OLD = [
    "  L6 MA CROSS SHORT  -  V1.0.0  (2026-11-19; logic = S16 v1.28.1 Set B)",
    "  Signal Name : L6_MACrossShort",
    "  MC Load Name: L6_MACrossShort_v1.0.0  (live load name, Willy 11/19)",
    "  Version     : V1.0.0   Build_ID 2611193   (logic = S16 v1.28.1 b2611191)",
]
HEAD_NEW = [
    "  L6 MA CROSS SHORT  -  V0.1.0 DEV  (2026-11-20; = L6 V1.0.0 + settle table)",
    "  Signal Name : L6_MACrossShort",
    "  MC Load Name: L6_MACrossShort_v010_RESEARCH  (DEV, NOT live; swap after 2027-01-05)",
    "  Version     : V0.1.0   Build_ID 2611201   (base L6 V1.0.0 b2611193)",
    "",
    "  V0.1.0 (2026-11-20, development): ONE change on top of V1.0.0.",
    "  Settlement deferral table: when the 3rd Wednesday is a TAIFEX",
    "  closure, final settlement moves to the next business day. Source:",
    "  data/taifex_market_closures.json, year 2027 only (2027-09-15 ->",
    "  2027-09-16). Earlier years are left as in V1.0.0 so the history",
    "  matches the MC report trade by trade.",
]
RULE_OLD = """v_Settlement_Day = ( DayOfWeek(Date) = 3 ) and
                   ( DayOfMonth(Date) >= 15 ) and
                   ( DayOfMonth(Date) <= 21 );
"""


def main():
    defer = settle_deferrals()
    assert defer == [(dt.date(2027, 9, 15), dt.date(2027, 9, 16))], defer
    txt = SRC.read_bytes().decode("ascii").replace("\r\n", "\n")
    lines = txt.split("\n")
    i = lines.index(HEAD_OLD[0])
    assert lines[i:i + 4] == HEAD_OLD, lines[i:i + 4]
    lines[i:i + 4] = HEAD_NEW
    out = "\n".join(lines)
    assert out.count(f"Build_ID                ( {BUILD_OLD} )") == 1
    out = out.replace(f"Build_ID                ( {BUILD_OLD} )", f"Build_ID                ( {BUILD_NEW} )")
    table = ["{ ---- Settlement deferral table (V0.1.0): 3rd Wed closed -> next business day ---- }"]
    for w, n in defer:
        table.append(f"if Date = {mc(w)} then v_Settlement_Day = False;  {{ Settle_Skip {w} closed }}")
        table.append(f"if Date = {mc(n)} then v_Settlement_Day = True;   {{ Settle_Add  {n} deferred }}")
    assert out.count(RULE_OLD) == 1
    out = out.replace(RULE_OLD, RULE_OLD + "\n".join(table) + "\n")
    out.encode("ascii")
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in (".pla", ".txt"):
        with open(OUT / f"L6_MACrossShort_v0.1.0{ext}", "w", encoding="ascii", newline="\r\n") as f:
            f.write(out)
    print(OUT, len(out.split("\n")), "lines", defer)


if __name__ == "__main__":
    main()
