"""產生 L6_MACrossShort_v1.0.0（Willy 11/19：正式版號「L6_MACrossShort_v1.0.0」）。
內容＝S16 v1.28.1 候選（B，Build 2611191），只改：檔頭說明、Build_ID 2611191 → 2611193。程式碼一個字都不動。
輸出 CRLF＋純 ASCII，.txt 與 .pla 相同。

Usage: python -I scripts/research/s16_streak_20261118/build_l6_v100.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.28.1_candidate.pla"
OUT = ROOT / "strategies/research/L6_MACrossShort/L6_MACrossShort_v1.0.0"
BUILD_OLD, BUILD_NEW = "2611191", "2611193"

HEAD_OLD = [
    "  S16_S - MOVING AVERAGE CROSS SHORT STRATEGY",
    "  Signal Name : S16_S_MACrossShort",
    "  MC Load Name: STRATEGY_GEN_S16_S_MACrossShort_v1281c_RESEARCH",
    "  Version     : v1.28.1 CANDIDATE   Build_ID 2611191   (base v1.26.0 b260825)",
]
HEAD_NEW = [
    "  L6 MA CROSS SHORT  -  V1.0.0  (2026-11-19; logic = S16 v1.28.1 Set B)",
    "  Signal Name : L6_MACrossShort",
    "  MC Load Name: L6_MACrossShort_v1.0.0  (live load name, Willy 11/19)",
    "  Version     : V1.0.0   Build_ID 2611193   (logic = S16 v1.28.1 b2611191)",
    "",
    "  V1.0.0 (2026-11-19, first live version, Willy naming 11/19):",
    "  Code is byte-identical to S16_S_MACrossShort v1.28.1 CANDIDATE except",
    "  Build_ID 2611191 -> 2611193. Defaults = Set B (TOD_Gate_Days 90,",
    "  TOD_Gate_Q 0.70), SL_Pct 1.00, 2027 holidays, Registry_Valid_Until",
    "  1271231. Data: TXF1 5M, day + night, 2 micro lots.",
    "  Account: short account 150,000 (with L2, L4); L6 capital 120,000",
    "  (2 lots x margin 60,000).",
    "  Stop rules (manual, Manual_Kill_Switch = true to stop):",
    "    - L6 equity falls 18,000 from its peak, or 10 losses in a row",
    "      -> stop L6 and review.",
    "    - short account equity below start capital by 15% (22,500)",
    "      -> stop all short strategies and review.",
    "  Compile the live load name only when the chart and the broker are",
    "  both flat.",
]


def main():
    raw = SRC.read_bytes().decode("ascii")
    txt = raw.replace("\r\n", "\n")
    lines = txt.split("\n")
    i = lines.index(HEAD_OLD[0])
    assert lines[i:i + 4] == HEAD_OLD, lines[i:i + 4]
    lines[i:i + 4] = HEAD_NEW
    out = "\n".join(lines)
    assert out.count(f"Build_ID                ( {BUILD_OLD} )") == 1
    out = out.replace(f"Build_ID                ( {BUILD_OLD} )", f"Build_ID                ( {BUILD_NEW} )")
    out.encode("ascii")
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in (".pla", ".txt"):
        with open(OUT / f"L6_MACrossShort_v1.0.0{ext}", "w", encoding="ascii", newline="\r\n") as f:
            f.write(out)
    print(OUT, len(out.split("\n")), "lines")


if __name__ == "__main__":
    main()
