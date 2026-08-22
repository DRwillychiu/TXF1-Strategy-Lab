# S16_S_MACrossShort_v1.26.0.pla -- 完整註解記錄

本檔存放從 `.pla` 移出的長註解區塊。程式碼一個字元都沒有改動 ——
`scripts/slim_pla_v2.py` 剝除前後兩檔的全部註解、正規化空白，
要求剩餘位元完全相同，否則拒絕寫檔。

`.pla` 裡每個被移出的區塊都留下一行指標，標號對應下面的段號。

---

## 區塊 1 — 原第 1 行起，共 313 行

```
{ ================================================================================
  S16_S - MOVING AVERAGE CROSS SHORT STRATEGY
  Signal Name : S16_S_MACrossShort
  MC Load Name: STRATEGY_GEN_S16_S_MACrossShort
  Version     : v1.26.0 K-bar Admission (2026-08-17, base v1.25.0)

  ADOPTED 2026-08-19. This file now SHIPS WITH THE FILTER ON.

    KB_Block_Support 1 / KB_Block_Oppose 1 / KB_Block_Neutral 0
    KB_Filter_Mode 2 / KB_Filter_Win 3

    anchor   160 trades / 2,796,800 / PF 2.3295303290 / -337,200
             adjusted PF 1.8282191963 / sharpe 0.2150697367
             sortino 1.4236697865 / annual return 18.4562%

  2026-08-21 -- THE TWO 2026-08-20 FIXES ARE MEASURED. ANCHOR UNCHANGED.

  A 4-cell sweep settled both, and the attribution is exact.

    Sess_GapReset  ReEntry  net        trades  gross loss   drawdown
       0              0     2,796,800    160   -2,103,600   -337,200
       1              0     2,796,800    160   -2,103,600   -337,200   ADOPTED
       0              1     2,769,200    161   -2,131,200   -364,800
       1              1     2,769,200    161   -2,131,200   -364,800

  Sess_GapReset_On is FREE. Rows sharing a ReEntry value are bit-identical,
  so it changed not one trade in sample. It still ships ON -- the 240-bar
  phantom day session was measured and is real; this sample simply held no
  entry decision on an affected bar. Insurance at zero cost.

  ReEntry_Filt_Mode carries the ENTIRE difference, and it is one trade.
  Gross profit is identical at 4,900,400 in all four cells; gross loss moves
  by exactly 27,600 and the drawdown deepens by exactly 27,600. Setting it to
  1 opens one extra re-entry, that trade loses 27,600, and it lands inside
  the worst stretch.

  USER RULING 2026-08-21: ReEntry_Filt_Mode = 0. Explicitly NOT because it
  is better in sample -- that is n = 1 and would be a bad reason. Because:

    the re-entry path's filter rule has never been swept EITHER way, so
    Mode 2 / Win 3 exists only as a death-cross measurement and pushing it
    onto re-entry extrapolates a result off the path it was measured on;

    the two paths are not the same event -- a fresh death cross at market
    versus a stop order at a price that already failed once -- so demanding
    the entry bar itself be clean is a coherent higher bar for a retry,
    independent of any number;

    re-entry is 7 to 8 trades and can never be measured to significance, so
    this was always going to be a design decision. Better to say so than to
    dress it as an optimisation.

    Sess_GapReset_On   v_Bars_In_Sess could not see a session boundary when
                       an entire session was missing from the data. Measured:
                       20210901 0850 to 20210906 1345 counted as one 240-bar
                       "day session". The K-bar session gate then over-permits
                       -- a 3 or 5 bar pattern built across a boundary nobody
                       detected. 131 of 3,670 sessions are abnormal, of which
                       91 are settlement days ending 1330 and legitimate.

    ReEntry_Filt_Mode  the two entry paths were using DIFFERENT K-bar rules.
                       The death cross gate reads v_Filt_Pass, which at Win = 3
                       accepts a clean bar up to three back. Re-entry read
                       v_KB_Block, demanding the entry bar itself be clean --
                       stricter than the path the sweep measured. Not a
                       decision; the flag was added after the death cross gate
                       had already moved to v_Filt_Pass.

  To reproduce v1.25.0 from this file, set the three block switches AND
  KB_Filter_Mode AND KB_Filter_Win all to 0. That returns 180 trades /
  2,615,600 / PF 2.0923822252 / -364,800 -- verified in MC12 on 2026-08-18.
  The two 2026-08-20 switches do not need to be zeroed for that: with
  KB_Filter_Win 0 the re-entry mode collapses, but Sess_GapReset_On still
  bites, so zero it as well for a bit-exact v1.25.0.

  Any edit must reproduce one of those sets before its own result is read.
  MC12 retains the previous run's input values rather than reloading the
  file, and that has voided whole batches in this project.

  STILL OPEN, ranked: the K-bar filter's +181,200 was selected and measured
  on the SAME 180 trades, so it is not out-of-sample evidence. A permutation
  test, a transfer to S16_S_10M or L2_TrendShort without retuning, and W4
  WFA with PER-WINDOW re-derivation are the three things that would test it.
  None has been run.

  ================================================================
  WHY THIS CELL, AND WHAT IT COST
  ================================================================

  The comparison is unusually clean: the 160 trades are a strict SUBSET of
  v1.25.0's 180, no trade was added, and every surviving trade has an
  IDENTICAL P&L. So the entire +181,200 is exactly the removal of 20
  trades, with nothing else moving.

  Those 20 were worth -181,200 at a 20% win rate and PF 0.38, and 15 of
  them died to the 4-bar quick stop. NONE of them was a big fish -- all
  seven survive, and the top-7 total is 2,384,800 in both versions. The
  filter did not touch the tail.

  It was not free. It also removed a +80,800 structure exit on 2025-04-09
  and a +20,800 golden cross on 2020-09-21. 2025 is the only year that
  gets worse, and that trade is why.

  THE WINDOW IS WHAT MAKES IT AFFORDABLE

  Blocking at the entry bar -- Mode 2 with Win 0, or equivalently Mode 0
  with the switches on -- leaves 102 trades, 1.31 a month, well under the
  floor. Requiring only that a CLEAN bar existed within the last three
  keeps 160. Win is a quality-for-quantity slider and both curves are
  monotone:

    Win     0      1      2      3      4      5      6
    trades  102    127    149    160    167    170    174
    PF     3.29   2.54   2.45   2.33   2.19   2.18   2.13
    net    2.657  2.447  2.760  2.797  2.661  2.668  2.612  (millions)

  Net peaks at 3 because that is where the two curves cross. Win 3, 4, 5
  and 6 all land between 2.61M and 2.80M with an IDENTICAL -337,200
  drawdown -- four of seven values, so the plateau is 57% of the swept
  range against a 20% requirement. Win 0, 1 and 2 fail the trade floor.

  Win 5 is the alternative if the trade-count margin matters: 170 trades
  and 14 of headroom instead of 4, costing 129,200. It was rejected
  because the drawdown is flat across the whole plateau, so those ten
  extra trades buy no protection -- they only dilute.

  NO REPLACEMENT EFFECT. AT ALL.

  Earlier notes in this file assumed MC12 would refill a blocked slot with
  a later cross, making every offline count a FLOOR. It does not. Zero
  trades were added at any Win value; the count moves only as the block
  loosens. A blocked death cross does not free the position for another
  one, because the next cross needs a golden cross in between. Offline
  counts are the actual counts.

  ================================================================
  THE SELECTOR: 28 PATTERNS, ONE INTEGER, NO WEIGHTS
  ================================================================

  Every A, B and C class pattern is computed here -- 13 pro-short, 13
  anti-short, 2 neutral. They do not vote and they do not score. The
  first one that matches writes its own number into v_KB_Code and every
  later test is skipped. The gate is one comparison: v_KB_Code = 0.

  A SCORE WOULD HAVE NOTHING TO FIT. Measured on the 180 v1.25.0 trades,
  the number of patterns an entry carries does not predict anything:

    patterns hit    trades    average    win%     PF
        0              95     26,332     35.8    3.10
        1              65        412     21.5    1.03
        2              14      5,171     35.7    1.44
        3               6      2,466     33.3    1.23

  Hitting three is no worse than hitting one; two is better than one.
  There is no dose-response, so weights would be fitted to noise, and
  every weight is a free parameter this file would then have to defend.
  The signal is binary -- a pattern is present, or none is -- and that
  is exactly what one integer and one comparison express.

  Because the gate only asks whether the code is zero, the ORDER of the
  tests changes the diagnostic label and nothing else. No ordering
  argument is needed, and none was made.

  WHY ALL 28 AND NOT THE 14 THAT CAN FIRE

  The entry gate forces a black bar, so any pattern ending in a white
  one is structurally unreachable and 14 of the 28 must report zero.
  They are coded anyway. The offline census claims anti-short patterns
  never appear on an entry bar; with those 14 present, MC12 tests that
  claim itself instead of taking the Python census on trust -- which
  matters, because section 2.1 of the spec has that census pipeline
  under an open audit. A pattern that fires when it was predicted not
  to is a finding, and there is no way to see it if it is not coded.

  FILTER ORDER: TWO OF THE THREE OPTIONS ARE THE SAME OPTION

  v_Slope_Pass and v_KB_Block are both pure functions of the current bar
  and neither reads the other -- they meet only in the entry gate, ANDed.
  AND commutes, so "slope first then pattern" and "pattern first then
  slope" select the IDENTICAL set of bars. That is provable, not
  arguable, and no backtest can separate them.

  Order can only matter if a condition is allowed to persist. So each
  gets an age -- 0 means it holds on this bar, n means it last held n
  bars ago, 999 means not since the session opened -- and KB_Filter_Mode
  chooses which one is allowed to be stale:

    0  both must hold on this bar               v1.25.0 exactly
    1  slope may be up to Win bars old          slope is the first filter
    2  a clean bar arms for Win bars            pattern is the first filter
    3  either arms, the other confirms          independent, first to fire

  KB_Filter_Win = 0 pins both ages to 0, so all four modes collapse to
  the same-bar AND and the anchor cannot drift no matter what mode is
  left set.

  RE-ENTRY NOW CARRIES THE PATTERN GATE TOO

  SE_MA_ReEntry checked every other block flag but not v_KB_Block, so 7
  trades worth 152,400 -- 3.9% of trades and 5.8% of net profit -- ran
  outside the filter being measured. Not a leak of blocked signals, since
  a blocked entry never opens a position to re-enter, but it would have
  diluted every cell of the sweep. Fixed.

  THE TWO QUICKSTOP LEGS NOW HAVE THEIR OWN SWITCHES

  QuickStop_On turned both legs off together, so "run without the time
  quick-stop but keep the loss stop" was not expressible and had to be
  faked by pushing MaxBars past the hold cap. QS_Time_On and QS_Loss_On
  are explicit, default to 1, and reproduce the old behaviour exactly.

  Both legs are still market orders on a price condition. That is fine
  for the TIME leg, which is a bar-count rule -- but for the LOSS leg it
  is a known defect: the threshold is breached at a bar close and the
  fill lands at the next open, wherever that is. It stays harmless only
  while QS_MaxLoss_Pct is unreachable at 0.70.

  ** ANY SWEEP CELL THAT ACTUALLY FIRES THE LOSS LEG IS MEASURING THAT
  DEFECT. ** Those numbers are informative about the mechanism and are
  NOT a deployment candidate. Fixing it means placing a resting stop
  every bar, which changes what preempts what in the priority chain --
  a separate design question, not a parameter.

  WHAT BLOCKING COSTS

    block                        trades  /month     net      PF
    nothing                         180    2.31  2,615,600  2.09
    pro-short only                  105    1.35  2,581,600  3.06
    pro-short + neutral              95    1.22  2,501,600  3.10

  Those counts assume a blocked slot stays empty. MC12 will REFILL --
  blocking a trade frees the position for a later cross that was
  previously skipped -- so each count is a FLOOR, and how far above it
  the real number lands is the one thing this sweep exists to find out.
  Every option shown already breaks the 156-trade floor on arithmetic.

  Note the last row: net profit FALLS while PF rises. A18 tweezer top,
  B29 three outside down and A10 outside bar are profitable and go out
  with the rest. Quality and size separate here, so "maximise PF" and
  "maximise net" are different instructions.

  THRESHOLDS ARE PINNED, NOT TUNED

    long body   >= 50% of range        body exceeds shadow
    doji        <  10% of range, range >= 3 pts, both shadows >= 1 pt
    equal       EXACTLY equal, zero tolerance
    Eight patterns times three knobs would be enough free parameters to
    manufacture significance on 7,775 crosses. The doji threshold is
    relative because the absolute form drifts: median range went 4 points
    in 2019 to 48 in 2026, so "body <= 1 point" silently tightens from
    25% of range to 2%, and doji frequency falls 15.4% -> 4.6% on nothing
    but definitional creep.

  WHY THESE EIGHT AND NOT MORE

    Seventeen gap-dependent patterns were deleted. Not because intraday
    bars never gap -- 14.65% of them open outside the prior body -- but
    because the median of those gaps is ONE POINT against 17 at the
    session open. Dark Cloud Cover means "opened higher then got pushed
    back"; opening one point higher and closing black is just a black
    bar. The condition would be met by quote noise 60,716 times.

    Six further patterns are defined but too rare to test (three black
    crows 30, advance block 14, deliberation 11, three white soldiers 3,
    three stars in the south 0, unique three river bottom 0). Three black
    crows stays in this file at group 5 because the author ruled that
    strictness beats sample size: its strict form appears 30 times and
    its loose form 1,237, and the loose form's "opens inside the prior
    body" clause is a daily-chart artifact that on 5-min bars amounts to
    demanding a gap.

  PRE-REGISTERED: GROUP 11 IS THE HYPOTHESIS

    Groups 1-10 are diagnostic. Reading eleven cells and adopting the
    best is selection, not evidence. Acceptance needs all three: the
    added trades must be profitable ON THEIR OWN, the original 180 must
    survive at 170 or better, and the drawdown must not worsen.

  FULL DESIGN RECORD AND VERSION HISTORY
      docs/research/S16S_design_record.md

  Nothing was deleted when this file was slimmed on 2026-08-15. Every
  block that used to live here is in that document, and each divider
  below carries the section number that explains it. The move was
  verified by stripping all comments from the before and after files
  and asserting the remaining code was byte-identical.

  CURRENT ANCHOR  (MC12, every input at the default in this file)
      net profit                2,615,600
      trades                          180
      profit factor                  2.09
      max strategy drawdown      -364,800
      return on account            908.19

  Any edit must reproduce those five numbers before its own result is
  read. MC12 keeps the previous run's input values instead of reloading
  the file, and that has voided whole batches in this project.

  COST SPEC  (CLAUDE.md)
      slippage 1,000 NTD per contract per side = 10 points round trip
      2 lots, 2,000,000 initial capital, MaxBarsBack 100
      day 0845-1345, night 1500-0500

  RULE COMPLIANCE
      #11 Settlement_Flat, 7 elements
      #12 SetStopContract + SetStopLoss + SL_Pct
      #15 100 percent ASCII
      #17 multi-layer stop loss

  SEMANTIC AUDIT  scripts/verify_pla_semantics.py -- 22 checks, all pass
      Four dead lines removed 2026-08-15 (v_ML_Loss, v_Prev_Open,
      v_Prev_Close, v_Prev_Body). Details in the design record.
================================================================================ }
```

## 區塊 2 — 原第 317 行起，共 9 行

```
    { ===== Group 0: BUILD STAMP -- declared FIRST so it is the first row in ===== }
    { the MC12 settings dialog. The strategy NAME does not change when the file }
    { is patched, so before this there was no way to tell from the dialog which }
    { build MC had loaded. MC12 retains input values rather than reloading the  }
    { file, and that has voided six batches in this project.                    }
    {                                                                           }
    { Format YYMMDD of the last behaviour-changing edit. Compare against        }
    { docs/build_snapshots/ before trusting any run. Generated and checked by   }
    { scripts/snapshot_pla_inputs.py.                                           }
```

## 區塊 3 — 原第 391 行起，共 5 行

```
    { --- 2026-08-20 defect fixes, 2026-08-21 measured and settled by 4 cells --- }
    { Sess_GapReset_On is FREE: cells (0,0) and (1,0) are bit-identical, as are   }
    { (0,1) and (1,1). It closed a real defect and changed no trade in sample.    }
    { ReEntry_Filt_Mode stays 0 by USER RULING -- see the header. The anchor is   }
    { unchanged at 160T / 2,796,800.                                              }
```

## 區塊 4 — 原第 402 行起，共 5 行

```
    { --- Pattern-selector thresholds. NOTE: these are NOT the KB_Body_* inputs --- }
    { of the legacy 17-type single-bar classifier in SECTION 6. Two separate       }
    { systems, two separate meanings of "long body". Sweeping KB_Body_Long does    }
    { NOT move anything below. User ruling 2026-08-18: exposed as inputs so the    }
    { decision is made on measured P&L, not on reasoning.                          }
```

## 區塊 5 — 原第 808 行起，共 16 行

```
    { ---- First bar of a session ----------------------------------  -- md 3.26 }
    { 2026-08-20 DEFECT FIX. The transition test alone CANNOT see a boundary    }
    { when an entire session is missing from the data. Measured: 20210901 0850  }
    { through 20210906 1345 was counted as ONE 240-bar "day session", because   }
    { the night sessions in between have no bars at all, so v_In_Day never went }
    { False and the counter never reset. The K-bar session gate then over-      }
    { permits: a 3 or 5 bar pattern can reach across a boundary nobody saw.     }
    {                                                                           }
    { A wall-clock gap larger than one bar now also starts a session. Date is   }
    { carried through DateToJulian so a multi-DAY hole is measured, which the   }
    { existing v_Elapsed_Min cannot do -- it wraps at 1440 and would report a   }
    { five-day hole as a few minutes.                                           }
    {                                                                           }
    { Erring toward RESET is the safe direction. A spurious reset only makes    }
    { patterns unavailable for a few bars; a MISSED reset lets a pattern be     }
    { built out of bars from two different markets.                             }
```

## 區塊 6 — 原第 1128 行起，共 10 行

```
    { SECTION 8.6 - K-BAR PATTERN SELECTOR (v1.26.0) }
    { 30 patterns. First match writes its code and stops. Gate is code = 0.  }
    { Thresholds are pinned and must never be swept: long body >= 50% of     }
    { range, doji < 10% of range with range >= 3 points and each shadow >= 1 }
    { point, "equal" means EXACTLY equal, "star" means half the reference    }
    { body. Derivations in docs/research/S16S_kbar_pattern_spec_20260816.md. }
    {                                                                        }
    { Every pattern is gated on v_Bars_In_Sess so no comparison reaches      }
    { across a session break -- the bar before a session open is a different }
    { market, and the gap programme already covers that boundary.            }
```

## 區塊 7 — 原第 1277 行起，共 8 行

```
    { 14  D47 bearish hikkake -- five bars, no gap anywhere in it       }
    {     bar[3] sits inside bar[4]; bar[2] breaks UP out of it and     }
    {     fails; this bar takes out bar[3]'s low, which is the trap     }
    {     closing. Chesler's own window is three bars -- here the       }
    {     window is one, because the current architecture requires a    }
    {     pattern to COMPLETE on the entry bar. The two- and three-bar  }
    {     delayed confirmations need the persistence state machine and  }
    {     are deliberately NOT coded yet.                               }
```

## 區塊 8 — 原第 1291 行起，共 5 行

```
    { 15  D48 descending hawk -- two bars. Both white, the second's     }
    {     body contained in the first's and smaller: a rally losing     }
    {     its stride. STRUCTURALLY INERT under the slope gate, which    }
    {     forces a black entry bar -- coded so MC12 proves that rather  }
    {     than the spec assuming it, same as codes 16-28.               }
```

## 區塊 9 — 原第 1425 行起，共 12 行

```
    { SECTION 8.7 - FILTER ORDER (v1.26.0) }
    { The slope gate and the K-bar gate are both pure functions of the CURRENT }
    { bar and neither reads the other, so ANDing them is commutative: "slope   }
    { first" and "pattern first" select the identical set of bars. Order can   }
    { only matter if one of them is allowed to persist, so each gets an age.   }
    {                                                                          }
    {   age 0     the condition holds on THIS bar                              }
    {   age n     it last held n bars ago                                      }
    {   age 999   it has not held since the session opened                     }
    {                                                                          }
    { KB_Filter_Win = 0 forces both ages to 0, which is the plain same-bar AND,}
    { so every mode collapses to the anchor and the anchor cannot drift.       }
```

## 區塊 10 — 原第 1486 行起，共 6 行

```
    { 2026-08-20 DEFECT FIX. The two entry paths were using DIFFERENT K-bar     }
    { rules. The death cross gate reads v_Filt_Pass, which at Win = 3 accepts a  }
    { clean bar up to three bars back. Re-entry read v_KB_Block directly, which  }
    { demands the entry bar ITSELF be clean -- STRICTER than the path the sweep  }
    { actually measured. That asymmetry was not a decision; the flag was added   }
    { on 2026-08-19 after the death cross gate had already moved to v_Filt_Pass. }
```

