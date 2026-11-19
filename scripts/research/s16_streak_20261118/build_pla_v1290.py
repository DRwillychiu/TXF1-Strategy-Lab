"""由 v1.28.1 候選 .pla 產生 v1.29.0 候選（大殺盤 5 項）。只插入新段落、不改既有邏輯；五個新 input 全 0 時＝v1.28.1。
Usage: python -I scripts/research/s16_streak_20261118/build_pla_v1290.py <Crash30> <Crash60> <DayTrend> <CrashDay> <ContRe> <Crash_Struct>
輸出：strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.29.0_candidate.pla 與相同內容的 .txt
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIR = ROOT / "strategies/research/S16_MACrossShort"
SRC = DIR / "S16_S_MACrossShort_v1.28.1_candidate.pla"
DST = DIR / "S16_S_MACrossShort_v1.29.0_candidate.pla"


def rep(txt, old, new, count=1):
    n = txt.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (want {count}): {old[:60]!r}")
    return txt.replace(old, new)


def fmt(v):
    return f"{float(v):.2f}"


def main():
    c30, c60, dtr, cday, cont, cst = sys.argv[1:7]
    t = SRC.read_text(encoding="ascii")
    head = (
        "  Version     : v1.29.0 CANDIDATE   Build_ID 2611192   (base v1.28.1 b2611191)\n\n"
        "  v1.29.0 CANDIDATE (2026-11-19, research only, NOT live): crash capture.\n"
        "  Willy 11/19: the strategy earns the launch of a sell-off -- a 30-minute\n"
        "  drop, a 1-hour drop, or a long black day session -- and it must be able\n"
        "  to catch the big sell-off days. Six inputs, every one 0 = v1.28.1:\n"
        "  (1) Crash30_Pct : in this session, (highest high of the last\n"
        "      MinList(6, bars in session) bars - Close) / that high * 100 >= X\n"
        "      -> sell short next bar at market (SE_MA_Crash30). No death cross\n"
        "      needed. Once per session.\n"
        "  (2) Crash60_Pct : same with 12 bars (SE_MA_Crash60). Once per session.\n"
        "  (3) DayTrend_Pct: day session only; (day open - Close) / day open * 100\n"
        "      >= Z and Close below every Low of the earlier bars of this session\n"
        "      -> sell short next bar at market (SE_MA_DayTrend). Once per session.\n"
        "      (1)-(3) need: flat, no death-cross order this bar, >= 2 bars in\n"
        "      session, no bullish structure, the TOD gate, and every existing\n"
        "      time / settlement / holiday / gap / last-bar / kill block.\n"
        "      Crash_Struct = 1: (1)-(3) only while ZLEMA fast < slow.\n"
        "  (4) CrashDay_Pct: when (session open - Close) / session open * 100 >= D\n"
        "      the 2.3% target (SX_MA_TimeStop_Pct) is not placed on that bar; the\n"
        "      structure / BE / SL / time exits protect the trade instead.\n"
        "  (5) ContRe_On   : after a WINNING exit (ExitPrice(1) < EntryPrice(1)),\n"
        "      sell stop at the lowest Low of that trade (exit bar included)\n"
        "      (SE_MA_ContRe), while ZLEMA fast < slow, same session only, same\n"
        "      blocks as (1)-(3) except the TOD gate. When it is sent, the old\n"
        "      SE_MA_ReEntry order is not sent on that bar.\n"
        "  RESULT 2026-11-19 (Python, engine = MC trade by trade when all 0):\n"
        "  NONE of the five passed the criteria written before the run\n"
        "  (S16_crash_opt_criteria_20261119.md), in either design version.\n"
        "  Every default is 0 = v1.28.1. RESEARCH ONLY. DO NOT DEPLOY.\n"
        "  Evidence: docs/ops/S16_boss_20261120/S16_crash_opt_20261119.md, _v2_20261119.md\n\n"
    )
    t = rep(t, "  Version     : v1.28.1 CANDIDATE   Build_ID 2611191   (base v1.26.0 b260825)\n\n", head)
    t = rep(t, "MC Load Name: STRATEGY_GEN_S16_S_MACrossShort_v1281c_RESEARCH",
            "MC Load Name: STRATEGY_GEN_S16_S_MACrossShort_v1290c_RESEARCH")
    t = rep(t, "    Build_ID                ( 2611191 ),", "    Build_ID                ( 2611192 ),")
    t = rep(t, "    TOD_Gate_Q              ( 0.70  );",
            "    TOD_Gate_Q              ( 0.70  ),\n"
            "    { v1.29.0 CANDIDATE: crash capture. Every one 0 = v1.28.1. }\n"
            f"    Crash30_Pct             ( {fmt(c30)}  ),\n"
            f"    Crash60_Pct             ( {fmt(c60)}  ),\n"
            f"    DayTrend_Pct            ( {fmt(dtr)}  ),\n"
            f"    CrashDay_Pct            ( {fmt(cday)}  ),\n"
            f"    ContRe_On               ( {int(float(cont))}     ),\n"
            f"    Crash_Struct            ( {int(float(cst))}     );")
    t = rep(t, "    v_TOD_ATRPct            ( 0     );",
            "    v_TOD_ATRPct            ( 0     ),\n\n"
            "    { ===== v1.29.0 crash capture ===== }\n"
            "    v_Crash_Src             ( 0     ),\n"
            "    v_Crash_W               ( 0     ),\n"
            "    v_Crash_Hi              ( 0     ),\n"
            "    v_Fired30               ( False ),\n"
            "    v_Fired60               ( False ),\n"
            "    v_FiredDT               ( False ),\n"
            "    v_Sess_Low              ( 0     ),\n"
            "    v_Trade_Low             ( 0     ),\n"
            "    v_Cont_Armed            ( False ),\n"
            "    v_Cont_Px               ( 0     ),\n"
            "    v_Cont_Sent             ( False ),\n"
            "    v_DC_Sent               ( False ),\n"
            "    v_CrashDay              ( False );")
    # 4.5：每盤第一根重設
    t = rep(t, "    { ---- Last bar of a session (v1.17.0, ITEM A) -----------------  -- md 3.27 }",
            "    { ---- v1.29.0: per-session reset of the crash-capture state ---- }\n"
            "if v_Sess_First then begin\n"
            "    v_Fired30    = False;\n"
            "    v_Fired60    = False;\n"
            "    v_FiredDT    = False;\n"
            "    v_Sess_Low   = 0;\n"
            "    v_Cont_Armed = False;\n"
            "end;\n\n"
            "    { ---- Last bar of a session (v1.17.0, ITEM A) -----------------  -- md 3.27 }")
    # 5.5：獲利出場後掛「破低再空」
    t = rep(t, "if v_Death_Cross = True then begin\n    v_ReEntry_Armed = False;\n    v_ReEntry_Price = 0;\nend;\n",
            "if v_Death_Cross = True then begin\n    v_ReEntry_Armed = False;\n    v_ReEntry_Price = 0;\nend;\n\n"
            "    { v1.29.0 (5) ContRe: arm after a winning exit, at the trade's lowest Low }\n"
            "if v_Prev_MP = -1 and MarketPosition = 0 then begin\n"
            "    if ContRe_On <> 0 and ExitPrice(1) < EntryPrice(1) then begin\n"
            "        v_Cont_Armed = True;\n"
            "        v_Cont_Px    = MinList( v_Trade_Low, Low );\n"
            "    end;\n"
            "end;\n"
            "if v_Cont_Armed = True and ( v_Golden_Cross = True or v_ZLEMA_Fast >= v_ZLEMA_Slow ) then\n"
            "    v_Cont_Armed = False;\n")
    # 7：持倉中記錄最低價
    t = rep(t, "if MarketPosition = -1 then begin\n    v_Last_EntryPrice = EntryPrice;\n",
            "if MarketPosition = -1 then begin\n    v_Last_EntryPrice = EntryPrice;\n"
            "    { v1.29.0: lowest Low while short; disarm ContRe while in a position }\n"
            "    if v_Prev_MP <> -1 then\n"
            "        v_Trade_Low = Low\n"
            "    else\n"
            "        v_Trade_Low = MinList( v_Trade_Low, Low );\n"
            "    v_Cont_Armed = False;\n")
    # 8.8：三種下殺發動（在 8.9 門檻之前）
    t = rep(t, "    { SECTION 8.9 - v1.28.0 TIME-OF-DAY VOLATILITY GATE }",
            "    { SECTION 8.8 - v1.29.0 CRASH LAUNCH SOURCES (no death cross needed) }\n"
            "v_Crash_Src = 0;\n"
            "if MarketPosition = 0 and ( Crash30_Pct > 0 or Crash60_Pct > 0 or DayTrend_Pct > 0 )\n"
            "   and v_Bars_In_Sess >= 2 and v_KB_BullNow = False\n"
            "   and ( Crash_Struct = 0 or v_ZLEMA_Fast < v_ZLEMA_Slow ) then begin\n"
            "    if Crash30_Pct > 0 and v_Fired30 = False then begin\n"
            "        v_Crash_W  = MinList( 6, v_Bars_In_Sess );\n"
            "        v_Crash_Hi = Highest( High, v_Crash_W );\n"
            "        if v_Crash_Hi > 0 and ( v_Crash_Hi - Close ) / v_Crash_Hi * 100 >= Crash30_Pct then\n"
            "            v_Crash_Src = 1;\n"
            "    end;\n"
            "    if v_Crash_Src = 0 and Crash60_Pct > 0 and v_Fired60 = False then begin\n"
            "        v_Crash_W  = MinList( 12, v_Bars_In_Sess );\n"
            "        v_Crash_Hi = Highest( High, v_Crash_W );\n"
            "        if v_Crash_Hi > 0 and ( v_Crash_Hi - Close ) / v_Crash_Hi * 100 >= Crash60_Pct then\n"
            "            v_Crash_Src = 2;\n"
            "    end;\n"
            "    if v_Crash_Src = 0 and DayTrend_Pct > 0 and v_FiredDT = False and v_In_Day = True\n"
            "       and v_First_Open > 0 and v_Sess_Low > 0\n"
            "       and ( v_First_Open - Close ) / v_First_Open * 100 >= DayTrend_Pct\n"
            "       and Close < v_Sess_Low then\n"
            "        v_Crash_Src = 3;\n"
            "end;\n\n"
            "    { SECTION 8.9 - v1.28.0 TIME-OF-DAY VOLATILITY GATE }")
    t = rep(t, "    if MarketPosition = 0 and v_Filt_Pass = True and v_TOD_N >= IntPortion( v_TOD_Days / 2 ) then begin",
            "    if MarketPosition = 0 and ( v_Filt_Pass = True or v_Crash_Src > 0 ) and v_TOD_N >= IntPortion( v_TOD_Days / 2 ) then begin")
    # 9：死亡交叉送單旗標＋三種下殺進場＋破低再空
    t = rep(t, "    { SECTION 9 - ENTRY (Death Cross + M1 Slope + Rule #11 gates)  -- md 3.48 }\nif MarketPosition = 0 and",
            "    { SECTION 9 - ENTRY (Death Cross + M1 Slope + Rule #11 gates)  -- md 3.48 }\n"
            "v_DC_Sent   = False;\n"
            "v_Cont_Sent = False;\n"
            "if MarketPosition = 0 and")
    t = rep(t, "    v_IsReEntry = False;\n    if v_Entry_Src = 1 then\n",
            "    v_IsReEntry = False;\n    v_DC_Sent   = True;\n    if v_Entry_Src = 1 then\n")
    t = rep(t, "        sell short ( \"SE_MA_StructLate\" ) next bar at market;\nend;\n",
            "        sell short ( \"SE_MA_StructLate\" ) next bar at market;\nend;\n\n"
            "    { v1.29.0 (1)-(3) crash launch entries, only when no death-cross order was sent }\n"
            "if MarketPosition = 0 and\n"
            "   v_DC_Sent             = False and\n"
            "   v_Crash_Src           > 0 and\n"
            "   v_TOD_OK              = True and\n"
            "   v_FirstBar_Block      = False and\n"
            "   v_Tail_Entry_OK       = True and\n"
            "   v_Settlement_Day      = False and\n"
            "   v_Holiday_Block       = False and\n"
            "   v_Registry_Expired    = False and\n"
            "   Manual_Kill_Switch    = False and\n"
            "   v_Gap_Block           = False and\n"
            "   v_Sess_LastBar_Block  = False then begin\n"
            "    v_IsReEntry = False;\n"
            "    v_DC_Sent   = True;\n"
            "    if v_Crash_Src = 1 then begin\n"
            "        sell short ( \"SE_MA_Crash30\" ) next bar at market;\n"
            "        v_Fired30 = True;\n"
            "    end\n"
            "    else if v_Crash_Src = 2 then begin\n"
            "        sell short ( \"SE_MA_Crash60\" ) next bar at market;\n"
            "        v_Fired60 = True;\n"
            "    end\n"
            "    else begin\n"
            "        sell short ( \"SE_MA_DayTrend\" ) next bar at market;\n"
            "        v_FiredDT = True;\n"
            "    end;\n"
            "end;\n\n"
            "    { v1.29.0 (5) ContRe: break of the last winning trade's low }\n"
            "if MarketPosition = 0 and\n"
            "   v_DC_Sent             = False and\n"
            "   v_Cont_Armed          = True and\n"
            "   v_ZLEMA_Fast          < v_ZLEMA_Slow and\n"
            "   v_FirstBar_Block      = False and\n"
            "   v_Tail_Entry_OK       = True and\n"
            "   v_Settlement_Day      = False and\n"
            "   v_Holiday_Block       = False and\n"
            "   v_Registry_Expired    = False and\n"
            "   Manual_Kill_Switch    = False and\n"
            "   v_Gap_Block           = False and\n"
            "   v_Sess_LastBar_Block  = False then begin\n"
            "    v_IsReEntry = False;\n"
            "    v_Cont_Sent = True;\n"
            "    sell short ( \"SE_MA_ContRe\" ) next bar at v_Cont_Px stop;\n"
            "end;\n")
    t = rep(t, "if MarketPosition = 0 and\n   v_ReEntry_On          = True and\n",
            "if MarketPosition = 0 and\n   v_Cont_Sent           = False and\n   v_ReEntry_On          = True and\n")
    # 10：大殺盤不掛 2.3% 停利
    t = rep(t, "        if M8_Form = 2 then begin\n            v_M8_Target",
            "        v_CrashDay = CrashDay_Pct > 0 and v_First_Open > 0 and\n"
            "                     ( v_First_Open - Close ) / v_First_Open * 100 >= CrashDay_Pct;\n"
            "        if M8_Form = 2 and v_CrashDay = False then begin\n            v_M8_Target")
    # 11：本盤最低價（用完才更新）
    t = rep(t, "v_Prev_MP = MarketPosition;",
            "    { v1.29.0: session low through this bar, used from the next bar on }\n"
            "if v_Bars_In_Sess >= 1 then begin\n"
            "    if v_Sess_Low <= 0 then\n"
            "        v_Sess_Low = Low\n"
            "    else\n"
            "        v_Sess_Low = MinList( v_Sess_Low, Low );\n"
            "end;\n\n"
            "v_Prev_MP = MarketPosition;")
    t.encode("ascii")
    DST.write_text(t, encoding="ascii", newline="\r\n")
    DST.with_suffix(".txt").write_text(t, encoding="ascii", newline="\r\n")
    print(DST, len(t.splitlines()), "lines")


if __name__ == "__main__":
    main()
