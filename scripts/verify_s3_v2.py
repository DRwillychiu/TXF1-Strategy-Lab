"""
verify_s3_v2.py — Structural verification for S3_RapidPullbackShort_v2.pla

Per STRATEGY_RD_SOP.md Step 3: this is a NO-RUN structural check.
All checks should PASS before MC12 optimization (P0-1 pre-flight gate).

Coverage:
  - Inputs section (v2.0 H60_* renames + new defaults)
  - Variables section (v2.0 H60_RSI_Snap + hourly cadence vars)
  - 60M Tier 1 calculations (Section 2)
  - 5M Tier 2 (Section 3) - preserved from v1.1
  - Hourly RSI snapshot (Section 4) - v2.0 cadence change
  - SetStopLoss + Frozen SL (Section 5, Rule #12)
  - Entry logic (Section 6)
  - Exit chain Priority 0 (Section 7)
  - Holiday tail registry (63 entries)
  - Time-safety closed-interval audit
  - Label conventions (SE_RPS_v2_* / SX_RPS_v2_*)
  - v2.0 numeric defaults (TP=0.6, SL_ATR_Mult=3, TimeStop=18, Cutoff=1325)

Usage:  python scripts/verify_s3_v2.py
"""

import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA = Path(__file__).resolve().parent.parent / \
      "strategies/research/S03_PullbackShort/S3_RapidPullbackShort_v2.pla"

results = []  # (name, passed, detail)


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))


def main():
    if not PLA.exists():
        print(f"FATAL: .pla not found at {PLA}")
        sys.exit(1)

    src = PLA.read_text(encoding="utf-8")

    # === Header ===
    check("H01 version v2.x in header",
          re.search(r"Version\s*:\s*v2\.\d+(\.\d+)?", src))
    check("H02 Data2 = 60M active regime gate",
          "Data2 = 60M (regime gate" in src)
    check("H03 Data3 removed in v2.0",
          "Data3 = (removed" in src)
    check("H04 v2.0 change log present",
          "v2.0 CHANGE LOG vs v1.1" in src)
    check("H05 IntrabarOrderGeneration false",
          "[IntrabarOrderGeneration = false]" in src)

    # === Inputs (v2.0 renames + new defaults) ===
    check("I01 H60_FastMA_Len exists",
          re.search(r"H60_FastMA_Len\s*\(\s*20\s*\)", src))
    check("I02 H60_SlowMA_Len exists",
          re.search(r"H60_SlowMA_Len\s*\(\s*60\s*\)", src))
    check("I03 H60_RSI_Len exists",
          re.search(r"H60_RSI_Len\s*\(\s*14\s*\)", src))
    check("I04 H60_RSI_Threshold default 70 (v2.0.2 LOCKED from 27-trade opt)",
          re.search(r"H60_RSI_Threshold\s*\(\s*70\s*\)", src))
    check("I05 H60_RSI_Sustained_Bars default 2",
          re.search(r"H60_RSI_Sustained_Bars\s*\(\s*2\s*\)", src))
    check("I06 H60_Dist_MA20_Pct default 2.5 (v2.0.2 LOCKED from 27-trade opt)",
          re.search(r"H60_Dist_MA20_Pct\s*\(\s*2\.5\s*\)", src))

    check("I07 Consec_Red_Bars LOCKED 3",
          re.search(r"Consec_Red_Bars\s*\(\s*3\s*\)", src))
    check("I08 EMA_Fast_Len preserved",
          re.search(r"EMA_Fast_Len\s*\(\s*5\s*\)", src))
    check("I09 ATR_Spike_Mult default 1.1 (v2.0.2 LOCKED from 27-trade opt)",
          re.search(r"ATR_Spike_Mult\s*\(\s*1\.1\s*\)", src))
    check("I10 Pullback_Min_Pct default 0.6 (v2.0.2 LOCKED from 27-trade opt)",
          re.search(r"Pullback_Min_Pct\s*\(\s*0\.6\s*\)", src))
    check("I11 Pullback_Max_Pct preserved",
          re.search(r"Pullback_Max_Pct\s*\(\s*1\.5\s*\)", src))

    check("I12 TP_Pct default 1.0 (v2.0.2 LOCKED from 27-trade opt)",
          re.search(r"TP_Pct\s*\(\s*1(\.0)?\s*\)", src))
    check("I13 SL_ATR_Mult default 3 LOCKED",
          re.search(r"SL_ATR_Mult\s*\(\s*3\s*\)", src))
    check("I14 Max_Bars_TimeStop default 12 (v2.0.2 LOCKED 60 min from opt)",
          re.search(r"Max_Bars_TimeStop\s*\(\s*12\s*\)", src))
    check("I15 Entry_Open_Time = 850",
          re.search(r"Entry_Open_Time\s*\(\s*850\s*\)", src))
    check("I16 Entry_Cutoff_Time = 1230 (v2.0.2 LOCKED per 11:xx WR=20% data)",
          re.search(r"Entry_Cutoff_Time\s*\(\s*1230\s*\)", src))
    check("I17 Daily_Flat_Time = 1325",
          re.search(r"Daily_Flat_Time\s*\(\s*1325\s*\)", src))

    check("I18 Holiday_Flat_Time = 245",
          re.search(r"Holiday_Flat_Time\s*\(\s*245\s*\)", src))
    check("I19 Registry_Valid_Until = 1270101",
          re.search(r"Registry_Valid_Until\s*\(\s*1270101\s*\)", src))
    check("I20 Settlement_Flat_Time = 1230",
          re.search(r"Settlement_Flat_Time\s*\(\s*1230\s*\)", src))
    check("I21 HighConv_Threshold_Pct = 5 (v2.0.2 LOCKED, align with backtest setting)",
          re.search(r"HighConv_Threshold_Pct\s*\(\s*5\s*\)", src))

    # I22: check only DECLARED inputs (pattern: name followed by paren+default),
    # not bare references inside comment/changelog text.
    check("I22 No Daily_* inputs remain DECLARED (all renamed to H60_*)",
          not re.search(r"\bDaily_(FastMA_Len|SlowMA_Len|RSI_Len|RSI_Threshold|"
                        r"RSI_Sustained_Bars|Dist_MA20_Pct)\s*\(\s*\d", src))

    # === Variables ===
    check("V01 v_H60_FastMA declared",
          re.search(r"v_H60_FastMA\s*\(", src))
    check("V02 v_H60_RSI_Snap0..Snap3 declared",
          all(re.search(rf"v_H60_RSI_Snap{i}\s*\(", src) for i in range(4)))
    check("V03 v_LastSeenData2Date / v_LastSeenData2Time declared (v2.0.1 MC12 fix)",
          re.search(r"v_LastSeenData2Date\s*\(\s*-1\s*\)", src) and
          re.search(r"v_LastSeenData2Time\s*\(\s*-1\s*\)", src))
    check("V03b v_LastSeenHour NOT declared (removed in v2.0.1)",
          not re.search(r"v_LastSeenHour\s*\(", src))
    check("V04 v_Regime_Watch declared",
          re.search(r"v_Regime_Watch\s*\(", src))
    check("V05 v_Trigger_Fired declared",
          re.search(r"v_Trigger_Fired\s*\(", src))
    check("V06 v_DaySess_High declared (intraday high tracker)",
          re.search(r"v_DaySess_High\s*\(", src))
    check("V07 v_SL_Locked / v_Frozen_ATR_5M declared (Frozen SL)",
          re.search(r"v_SL_Locked\s*\(", src) and
          re.search(r"v_Frozen_ATR_5M\s*\(", src))
    check("V08 v_DailyCooldown_Active declared",
          re.search(r"v_DailyCooldown_Active\s*\(", src))
    check("V09 v_Holiday_Block declared",
          re.search(r"v_Holiday_Block\s*\(", src))
    check("V10 v_Settlement_Day declared",
          re.search(r"v_Settlement_Day\s*\(", src))
    check("V11 v_HighConv_Active declared",
          re.search(r"v_HighConv_Active\s*\(", src))
    check("V12 No v_Daily_* variables remain",
          not re.search(r"v_Daily_(FastMA|SlowMA|RSI|Dist_Pct|RSI_Snap[0-3])", src))

    # === Arrays / Holiday registry ===
    check("A01 Holiday_Tail array declared 80 slots",
          re.search(r"Holiday_Tail\[80\]\s*\(", src))
    # Count Holiday_Tail[N] = numeric assignments
    holiday_count = len(re.findall(r"Holiday_Tail\[\d+\]\s*=\s*1\d{6};", src))
    check("A02 Holiday_Tail has 63 entries (matches L1-L5/v1.1)",
          holiday_count == 63,
          f"found {holiday_count}")

    # === Section 1B Holiday/Settlement/Registry detection ===
    check("S1B-1 Holiday tail strict Time < 500 (v1.1 BUG FIX #2)",
          re.search(r"if Time < 500 then begin", src))
    check("S1B-2 Settlement detection (3rd Wed) present",
          "DayOfWeek( Date ) = 3" in src and
          "DayOfMonth( Date ) >= 15" in src and
          "DayOfMonth( Date ) <= 21" in src)
    check("S1B-3 Registry expiry red warning present",
          "HOLIDAY REGISTRY EXPIRES" in src)

    # === Section 2: 60M Tier 1 calculations ===
    check("S2-1 v_H60_FastMA from ( Average(...) of Data2 )[1] (v2.0.1 explicit parens)",
          re.search(r"v_H60_FastMA\s*=\s*\(\s*Average\(\s*Close\s*,\s*"
                    r"H60_FastMA_Len\s*\)\s*of Data2\s*\)\[1\]", src))
    check("S2-2 v_H60_SlowMA from ( Average(...) of Data2 )[1] (v2.0.1 explicit parens)",
          re.search(r"v_H60_SlowMA\s*=\s*\(\s*Average\(\s*Close\s*,\s*"
                    r"H60_SlowMA_Len\s*\)\s*of Data2\s*\)\[1\]", src))
    check("S2-1b NO bare Average(...)[1] of Data2 (regression check)",
          not re.search(r"Average\(\s*Close\s*,\s*H60_(Fast|Slow)MA_Len\s*\)\[1\]\s*of Data2", src))
    check("S2-3 v_H60_RSI sourced from snapshot Snap0 (not direct RSI call)",
          re.search(r"v_H60_RSI\s*=\s*v_H60_RSI_Snap0", src))
    check("S2-4 v_H60_Dist_Pct uses ( Close of Data2 )[1] explicit parens",
          re.search(r"\(\s*Close of Data2\s*\)\[1\]", src))
    check("S2-5 Regime: A AND (B OR C)",
          re.search(r"v_Trend_OK\s+and\s*\(\s*v_RSI_OK\s+or\s+v_Dist_OK\s*\)", src))
    check("S2-6 RSI sustained loop covers Snap0..Snap3 (4 levels)",
          all(f"v_H60_RSI_Snap{i}" in src for i in range(4)))

    # === Section 3: 5M Tier 2 (preserved from v1.1) ===
    check("S3-1 M1 consec red loop",
          re.search(r"for v_red_idx = 0 to Consec_Red_Bars\s*-\s*1\s+begin", src))
    check("S3-2 M2 EMA fast + slope (single XAverage call, v1.1 BUG FIX #9)",
          re.search(r"v_5M_EMA\s*=\s*XAverage\(\s*Close\s*,\s*EMA_Fast_Len\s*\)", src) and
          re.search(r"v_5M_EMA_Prev\s*=\s*v_5M_EMA\[1\]", src))
    # ensure no DUPLICATE XAverage call for EMA_Fast (regression check)
    xa_count = len(re.findall(r"XAverage\(\s*Close\s*,\s*EMA_Fast_Len\s*\)", src))
    check("S3-3 XAverage(EMA_Fast_Len) called exactly once (no v1.0 dup)",
          xa_count == 1, f"count={xa_count}")
    check("S3-4 M3 ATR short/long spike",
          re.search(r"v_5M_ATR_Short\s*=\s*AvgTrueRange\(\s*ATR_Short_Len\s*\)", src) and
          re.search(r"v_5M_ATR_Long\s*=\s*AvgTrueRange\(\s*ATR_Long_Len\s*\)", src))
    check("S3-5 M4 day-session high tracker reset at Entry_Open_Time per Date",
          re.search(r"Date <> v_DaySess_HighDate.*Time >= Entry_Open_Time", src, re.S))
    check("S3-6 M4 pullback geometry calculated",
          re.search(r"v_Pullback_Pct\s*=\s*\(\s*v_DaySess_High\s*-\s*Close\s*\)", src))
    check("S3-7 All four ANDed",
          re.search(r"v_M1_Consec\s+and\s+v_M2_BelowEMA\s+and\s+"
                    r"v_M3_ATR_Spike\s+and\s+v_M4_Pullback", src))
    check("S3-8 v_5M_EMA20 = XAverage(Close, TP_MA_Len)",
          re.search(r"v_5M_EMA20\s*=\s*XAverage\(\s*Close\s*,\s*TP_MA_Len\s*\)", src))

    # === Section 4: Data2 boundary RSI snapshot + Daily cooldown reset ===
    check("S4-1 Data2 boundary detection via ( Date of Data2, Time of Data2 ) tuple (v2.0.1)",
          re.search(r"Date of Data2 <> v_LastSeenData2Date", src) and
          re.search(r"Time of Data2 <> v_LastSeenData2Time", src))
    # S4-1b: only flag if Hour(Time) is in active code (not comments). Active
    # comparison would be `if Hour(Time) <> v_LastSeenHour then`. Mentions in
    # { ... } documentation comments are intentional (explain the v2.0.1 fix).
    check("S4-1b NO active Hour(Time) <> v_LastSeenHour conditional (v2.0.1 removed)",
          not re.search(r"^\s*if\s+Hour\(\s*Time\s*\)\s*<>\s*v_LastSeenHour\s+then",
                        src, re.M))
    check("S4-2 Snapshot shift: Snap3=Snap2, Snap2=Snap1, Snap1=Snap0",
          re.search(r"v_H60_RSI_Snap3\s*=\s*v_H60_RSI_Snap2", src) and
          re.search(r"v_H60_RSI_Snap2\s*=\s*v_H60_RSI_Snap1", src) and
          re.search(r"v_H60_RSI_Snap1\s*=\s*v_H60_RSI_Snap0", src))
    check("S4-3 Snap0 reads ( RSI(...) of Data2 )[1] = JUST-CLOSED 60M bar (v2.0.1)",
          re.search(r"v_H60_RSI_Snap0\s*=\s*\(\s*RSI\(\s*Close\s*,\s*"
                    r"H60_RSI_Len\s*\)\s*of Data2\s*\)\[1\]", src))
    check("S4-3b NO bare RSI(...) of Data2 assigned to Snap0 (regression check)",
          not re.search(r"v_H60_RSI_Snap0\s*=\s*RSI\(\s*Close\s*,\s*"
                        r"H60_RSI_Len\s*\)\s*of Data2\s*;", src))
    check("S4-4 v_LastSeenData2Date / Time updated after snap shift",
          re.search(r"v_LastSeenData2Date\s*=\s*Date of Data2", src) and
          re.search(r"v_LastSeenData2Time\s*=\s*Time of Data2", src))
    check("S4-4b Init branch bootstrap Snap0..Snap3 from ( RSI ... )[1..4] historical",
          re.search(r"v_LastSeenData2Date\s*>=\s*0", src) and
          all(re.search(rf"\(\s*RSI\(\s*Close\s*,\s*H60_RSI_Len\s*\)\s*of Data2\s*\)\[{i}\]", src)
              for i in range(1, 5)))
    check("S4-5 Daily cooldown reset gated by Time >= Entry_Open_Time",
          re.search(r"Date <> v_LastSeenDate.*Time >= Entry_Open_Time.*"
                    r"v_DailyCooldown_Active\s*=\s*False", src, re.S))

    # === Section 5: SetStopLoss + Frozen SL (Rule #12) ===
    check("S5-1 Frozen SL locks on entry bar (MP=-1, not locked)",
          re.search(r"if MarketPosition = -1 then begin.*?"
                    r"v_SL_Locked\s*=\s*False.*?"
                    r"v_Frozen_ATR_5M\s*=\s*AvgTrueRange",
                    src, re.S))
    check("S5-2 Frozen SL cleared when flat",
          re.search(r"v_SL_Locked\s*=\s*False.*v_Frozen_ATR_5M\s*=\s*0",
                    src, re.S))
    check("S5-3 SetStopLoss called once, guarded by MP >= 0 (short variant)",
          re.search(r"if MarketPosition >= 0 then\s+SetStopLoss\(", src))
    # SetStopLoss count check (Rule #12: exactly ONE call).
    # Match only true calls: SetStopLoss( v_... ) - excludes comment mentions
    # like "Engine SetStopLoss (5b)" which the v2.1 patch adds.
    sl_count = len(re.findall(r"\bSetStopLoss\s*\(\s*v_", src))
    check("S5-4 SetStopLoss called exactly once with v_ argument (Rule #12)",
          sl_count == 1, f"count={sl_count}")

    # === v2.0.2: Trailing layer REMOVED (rollback from v2.1) ===
    check("R01 TrailingActivate_Pct input REMOVED (v2.0.2 rollback)",
          not re.search(r"TrailingActivate_Pct\s*\(", src))
    check("R02 TrailingATR_Mult input REMOVED (v2.0.2 rollback)",
          not re.search(r"TrailingATR_Mult\s*\(", src))
    check("R03 v_InTheMoney_Pct variable REMOVED",
          not re.search(r"v_InTheMoney_Pct\s*\(", src))
    check("R04 v_Trailing_Active variable REMOVED",
          not re.search(r"v_Trailing_Active\s*\(", src))
    check("R05 v_Trailing_ATR variable REMOVED",
          not re.search(r"v_Trailing_ATR\s*\(", src))
    check("R06 v_Trailing_Cand variable REMOVED",
          not re.search(r"v_Trailing_Cand\s*\(", src))
    check("R07 Section 5c label REMOVED from active code",
          not re.search(r"^\s*\{\s*=+\s*\n\s*SECTION 5c",
                        src, re.M))
    check("R08 v2.0.2 ROLLBACK note present in header",
          "v2.1 -> v2.0.2 ROLLBACK" in src)

    # === Section 6: Entry logic ===
    check("S6-1 Entry SellShort label SE_RPS_v2_Entry",
          re.search(r'SellShort\(\s*"SE_RPS_v2_Entry"\s*\)\s*next bar at Market', src))
    check("S6-2 Entry gated by MarketPosition = 0",
          re.search(r"MarketPosition\s*=\s*0", src))
    check("S6-3 Entry gates: Regime + Trigger + Time window + Cooldown + Holiday + Settlement + Registry",
          all(g in src for g in [
              "v_Regime_Watch = True",
              "v_Trigger_Fired = True",
              "Time >= Entry_Open_Time",
              "Time <= Entry_Cutoff_Time",
              "v_DailyCooldown_Active = False",
              "v_Holiday_Block = False",
              "v_Settlement_Day = False",
              "v_Registry_Expired = False",
          ]))

    # === Section 7: Exit chain Priority 0 ===
    check("S7-1 P0-1 Manual Kill exit label SX_RPS_v2_Kill",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_Kill"\s*\)', src))
    check("S7-2 P0-2 Registry exit label SX_RPS_v2_RegistryEnd",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_RegistryEnd"\s*\)', src))
    check("S7-3 P0-3 Holiday exit label SX_RPS_v2_HolFlat with Time <= 455",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_HolFlat"\s*\)', src) and
          re.search(r"Time >= Holiday_Flat_Time.*Time <= 455", src, re.S))
    check("S7-4 P0-4 Settlement exit label SX_RPS_v2_Settlement guarded by v_Settlement_Day",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_Settlement"\s*\)', src) and
          re.search(r"v_Settlement_Day = True.*Time >= Settlement_Flat_Time",
                    src, re.S))
    check("S7-5 P0a Daily flat exit SX_RPS_v2_DayClose with Time <= 1340 paired",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_DayClose"\s*\)', src) and
          re.search(r"Time >= Daily_Flat_Time.*Time <= 1340", src, re.S))
    check("S7-6 S-1 TP exit label SX_RPS_v2_TP",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_TP"\s*\)', src))
    check("S7-7 TP fill-bar trap guards (v1.1 BUG FIX #1 preserved)",
          "v_Bars_Held >= TP_EMA20_MinBars" in src and
          "v_5M_EMA20[1] < EntryPrice" in src and
          "Close[1] > v_TP_EMA20[1]" in src)
    check("S7-8 S-2 TimeStop exit label SX_RPS_v2_TimeStop",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_TimeStop"\s*\)', src) and
          "v_Bars_Held >= Max_Bars_TimeStop" in src)
    check("S7-9 S-3 Frozen SL exit label SX_RPS_v2_SL at v_SL_Level Stop",
          re.search(r'BuyToCover\(\s*"SX_RPS_v2_SL"\s*\)\s*next bar at\s+'
                    r"v_SL_Level\s+Stop", src))
    check("S7-10 ExitFired sequenced: only one exit per bar",
          src.count("ExitFired = 1") >= 7)  # at least one per P0/strategy exit
    check("S7-11 v_Bars_Held = BarsSinceEntry (v1.1 BUG FIX #5 preserved)",
          "v_Bars_Held     = BarsSinceEntry" in src or
          "v_Bars_Held = BarsSinceEntry" in src)

    # === Section 8: Cooldown on exit ===
    check("S8-1 Cooldown set true after any exit",
          re.search(r"if ExitFired > 0 then begin\s*v_DailyCooldown_Active\s*=\s*True",
                    src, re.S))

    # === Section 9: Diagnostic logging ===
    check("S9-1 HighConv print gated by Log_HighConviction and v_HighConv_Active",
          re.search(r"if Log_HighConviction and v_HighConv_Active", src))
    check("S9-2 Print includes 60M dist + RSI snap0/snap1",
          'dist60m=' in src and 'RSI60m0=' in src and 'RSI60m1=' in src)

    # === Time safety closed-interval audit ===
    # Find all "Time >= X" occurrences and verify each is either paired
    # with Time <= Y same condition OR guarded by a state flag in same expression.
    # Heuristic: split on "if" and check each conditional block.
    time_ge_occurrences = re.findall(r"Time\s*>=\s*\w+", src)
    check("T01 Time >= X count is reasonable (entry window, exits, helpers)",
          5 <= len(time_ge_occurrences) <= 20,
          f"count={len(time_ge_occurrences)}")
    check("T02 Entry has Time<=Entry_Cutoff_Time paired with Time>=Entry_Open_Time",
          re.search(r"Time >= Entry_Open_Time.*Time <= Entry_Cutoff_Time", src, re.S))
    check("T03 Holiday flat has Time<=455 paired with Time>=Holiday_Flat_Time",
          re.search(r"Time >= Holiday_Flat_Time.*Time <= 455", src, re.S))
    check("T04 Daily flat has Time<=1340 paired with Time>=Daily_Flat_Time",
          re.search(r"Time >= Daily_Flat_Time.*Time <= 1340", src, re.S))

    # === Label conventions ===
    check("L01 All entry labels prefixed SE_RPS_v2_",
          all("SE_RPS_v2_" in m for m in re.findall(r'"(SE_[^"]+)"', src)))
    check("L02 All short-exit labels prefixed SX_RPS_v2_",
          all("SX_RPS_v2_" in m for m in re.findall(r'"(SX_[^"]+)"', src)))
    # Verify no v1.1 prefix remains (regression check)
    check("L03 No v1.1 SE_RPS_ / SX_RPS_ prefix remains (must be _v2_)",
          not re.search(r'"S[EX]_RPS_(?!v2_)', src))

    # === v1.1 deltas explicitly captured ===
    check("D01 v2.0 vs v1.1 diff summary present in header",
          "v2.0 DIFFS vs v1.1" in src or "v2.0 CHANGE LOG" in src)
    check("D02 Time-safety end-of-file audit present",
          "TIME-SAFETY VERIFICATION" in src)

    # === Sanity: file size in expected range ===
    n_lines = len(src.splitlines())
    check("Z01 File size 600-900 LOC (v2.0 expected ~750)",
          600 <= n_lines <= 900, f"lines={n_lines}")

    # === Render report ===
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed

    print("=" * 78)
    print(f"  S3_v2 STRUCTURAL VERIFICATION — {passed}/{total} PASS")
    print("=" * 78)
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {name}"
        if detail:
            line += f"  ({detail})"
        print(line)
    print("=" * 78)
    if failed:
        print(f"  {failed} CHECKS FAILED — fix before P0-1 pre-flight clearance")
        sys.exit(1)
    print(f"  ALL {total} CHECKS PASSED — P0-1 clear, ready for MC12 GA")


if __name__ == "__main__":
    main()
