# IND_S16S_P29 --- comment record (moved out at Build 260873)

The `.pla` carried 682 comment lines in 1,751, 39% of the file, the
longest block 202 lines.  That is a design record living inside the
source.  It lives here now; the source keeps what a reader needs at
that line and a pointer to the rest.

Line numbers are the ones from git `7780b3c`, before the move.

## IND_S16S_P29  --  broadening formation detector (P29 / P49 /

*was lines 1-202*

```
{ ==========================================================================
  IND_S16S_P29  --  broadening formation detector (P29 / P49 / P50)

  Build_ID 260872.  DETECTION ONLY.  This file places no orders and holds no
  position.  It exists so the detection can be checked by eye and by diff
  before a single line of it goes near the strategy.

  BUILD HISTORY
    260830  detection plus back-paint of the formation body
    260840  ruling C break tracking in three slots, white break bar,
            counting labels ("P49 #12" and its matching "#12 DN")
    260841  latch the pattern's own anchors.  v_H3 / v_L3 / v_H3b / v_L3b are
            rewritten by every later pivot push once the chain reaches six,
            while the slopes are only recomputed when the pattern test passes,
            so SECTION 7 was extending each line from a stranger's anchor.
            It hit 202 of 202 patterns, first at a median of 3 bars in.
    260842  v_PvDt / v_PvTm were missing from the six-slot shift, so a line
            started at the right price on the wrong bar.  Adds the P29 DIAG
            print -- bars, first, last, pivot counts -- because the MC12 run
            returned 199 formations against the reference and the four
            numbers separate a data difference from a code difference.
    260850  the whole broadening family, not just P29.  P51 / P52 / P53 /
            P54 join it behind their own switches, definitions transcribed
            from s16s_p51_p54_scan.py.  P51 and P52 default OFF: 1,670 and
            1,716 against P29's 202, so painting them buries the thing they
            sit beside.  Ruling A1 had already called both attributes rather
            than filters, and the switch default now matches the ruling.
    260843  per-year formation histogram.  P49 was short by 2 and P50 by 2,
            so the M7 split is not the cause and four formations are simply
            never seen.  Eight numbers say whether the shortfall sits in one
            year -- a data window -- or is scattered.
    260851  every reference number in this file was wrong.  See REFERENCE
            below: the count is 202, not 203, and the 203 was never
            reproducible.  Corrected here: formations, the break split,
            the per-year row, the pivot counts, the P51 / P52 totals and
            the P49 / P50 split.  No detection logic changed.
    260852  the P29 acceptance instruments were counting every enabled
            variant.  With the shipped defaults (P29 + P53 + P54) the
            formation count would have read 217, the per-year row would
            not have matched its reference, and P53 / P54 fell into the
            else branch and drew their labels off the P50 sequence -- so
            "P53 #91" would have carried a P50 number.  v_CntForm,
            v_YrCnt, v_Seq49 and v_Seq50 are now gated on v_Var = 29, and
            P51-P54 number themselves off their own counters.  The
            acceptance count now holds under ANY switch combination.
            The break tally is gated the same way, through a new v_BkVar
            slot field, so formations / break_down / break_up / expired
            still sum to 202 with P53 and P54 drawing beside them.
            slot_overflow stays GLOBAL -- it is a capacity diagnostic and
            three slots cannot hold P51 or P52, which is a reason those
            two ship OFF rather than something to hide.
    260853  records the MC12 verification above.  Comments only.
    260854  P52 DIAG.  MC12 printed 1,716 P52 on a 421,455-bar chart; the
            reference on that same window is 1,715, and the one frame the
            full csv has extra sits at 2019-01-02 10:30-11:25, inside the
            morning MC12 does not load.  So MC12 finds one the reference
            does not, somewhere in the common data.  Ruled out already:
            the enumeration (a rolling-chain replay of this file's own
            algorithm gives 1,715 too), the branch conditions, and the
            v_Ok reset, which sits inside the k loop.  A per-year row
            localises it the way the P29 row did.  P29, P51, P53 and P54
            all matched exactly, so this is contained to the P52 branch.
    260855  all five variants ON by default, per the 2026-08-28 ruling: a
            shape that occurs gets drawn and labelled, full stop.  Break
            slots 3 -> 8; with every variant detecting, 3,602 formations
            share the window and measured peak concurrency is 6, so three
            slots would have overflowed and stolen slot 0 from a live P29.
    260856  records the 260855 run: eleven numbers, all exact, P52 included.
            Comments only, no re-import needed.

  WHY AN INDICATOR FIRST
    The pattern layer publishes STATE.  The signal layer decides whether to
    trade.  Keeping them in separate files makes the first question -- is the
    implementation correct -- answerable on its own.  Print emits one line per
    event; diff those lines against the 202 patterns that
    scripts/research/s16s_p29_clean.py finds.  Any difference is an
    implementation bug, not a strategy question.

  REFERENCE, and why it says 202
    Commit aa836a0 claimed the reference was 203 and that the committed json
    was one pattern stale.  That claim does not survive a re-run.
    s16s_p29_clean.py has no diff since that commit, s16s_5min.csv has not
    been touched since 2026-08-25 10:36 -- which PREDATES it -- and the same
    code on the same data now yields 202.  s16s_p51_p54_scan.py, which
    rebuilds the frame independently, also yields 202.
    The 203rd was 2019-02-19 02:55 to 04:50.  That window is missing four
    bars in the csv (03:20, 03:50, 04:00, 04:40) and MC12 is missing the
    same four, so both sides agree the pattern is not there.  Those four
    timestamps occur ~1,850 times each across the series, so their absence
    is a property of that night, not of the pipeline.
    The reference is 202.  Every number below was re-measured on it.

  VERIFIED IN MC12, 2026-08-28, build 260852
    Every instrument matched exactly, on a chart whose first bar was
    2019-01-02 13:40 rather than the csv's 08:50:

      bars 421,455   pivot_high 75,136   pivot_low 76,017
      formations 202   P49 112   P50 90
      by_year 8 15 18 31 24 31 42 33
      break_down 75   break_up 88   expired 39   slot_overflow 0

    The bar and pivot figures sit below the csv reference because MC12 loaded
    58 fewer bars -- the whole 08:50 to 13:35 of the first session.  Cutting
    the csv to the same first bar reproduces 421,455 / 75,136 / 76,017 exactly,
    and the 202 is unchanged, so nothing was lost but that first morning.
    Read the pivot reference below as the FULL-csv figure; a chart that starts
    later will legitimately print fewer, and only the P29 count is invariant.

    The 199 that build 260842 reported is not explained by code.  The P29
    condition in 260843 was

        v_H1 < v_H2 and v_H2 < v_H3 and v_L1 > v_L2 and v_L2 > v_L3
        and v_L1 < v_H1 and v_L3 < v_H3

    which is exactly what v_RiseH and v_FallL and v_LowUnder evaluate to now.
    Detection did not change between the two builds.  That run's bars= was
    never recorded, so a shorter chart is the remaining explanation and it
    cannot be confirmed after the fact.

    ALL SEVEN VERIFIED at 260855, 2026-08-28, every variant switched on:

      bars 421,455   pivot_high 75,136   pivot_low 76,017
      formations 202   P49 112   P50 90
      by_year        8 15 18 31 24 31 42 33
      P29 202   P51 1670   P52 1715   P53 7   P54 8
      P52 by_year   94 172 229 267 169 258 302 224
      break_down 75   break_up 88   expired 39   slot_overflow 0

    Eleven quantities, all exact against the reference for a chart starting
    2019-01-02 13:40.  slot_overflow 0 confirms eight slots carry the peak
    concurrency of 6 that 3,602 formations produce.

  THE 1,716 THAT PRECEDED IT -- unexplained, and worth remembering
    An earlier run of the SAME counting code printed P52 1,716.  Same bar
    count, same pivot counts, same everything else.  The settings differed
    (Break_Mode, Line_Mode, Show_Labels, Paint_Mode all 0 in that run) but
    the counters sit at lines 672-687 and the first Break_Mode gate is at
    758, so the counting path is structurally above every switch that
    differed.  No setting can reach it.

    The difference was that the 1,715 run followed a fresh import with stock
    defaults, while the 1,716 run followed hand-edited inputs on an already
    loaded study.  MC12 not fully recalculating in that case is the standing
    hypothesis -- the same family as its habit of keeping the previous run's
    inputs instead of rereading the file -- but it is a HYPOTHESIS, not a
    finding, and nothing here proves it.

    Operational rule taken from it: an MC12 number counts only after a fresh
    import and a full recalculation.  A number produced by editing inputs on
    a loaded study is a draft.  The 199 formations that build 260842 reported
    against a reference of 202 is very likely the same phenomenon, which is
    consistent with the detection condition being provably unchanged between
    that build and this one.

  ACCEPTANCE, printed on the last bar as P29 TALLY
    P29 only, the defaults:
      formations 202   break_down 75   break_up 88   expired 39   overflow 0
      these six are P29-only and hold under any switch combination
      P49 112   P50 90
      break split from s16s_break_outcome.py, C1 close x D2 horizontal --
      the pairing this file draws.  75 + 88 + 39 = 202.
    per variant, all five counted in ONE run because all five detect:
      P29 202    P51 1,670    P52 1,716    P53 7    P54 8   (full csv)
      P52 reads 1,715 on a chart starting 20190102 1340 -- one sits in that
      morning.  MEASURED 1,715 there, so the two agree.
      3,602 formations in total, roughly 11,000 drawing objects.
    P53 and P54 are near-never: eight years, four of them empty for each.
    Their absence is the finding, which is why nothing is switched off.

  WHAT IT DETECTS
    P29  six alternating fractal pivots, three highs rising and three lows
         falling, lows under highs, symmetric 3+3
    P49  P29 whose prior hour trended up    -> broadening top,    bearish
    P50  P29 whose prior hour trended down  -> broadening bottom, bullish

  PINNED CONSTANTS -- two, both trading rulings, NEITHER may be swept
    M7_Bars  = 12   one hour of 5-minute bars (ruling 11, 2026-08-26)
    Run_Bars = 3    a run needs three; two is only a pair (ruling 18)

  RULINGS BUILT IN
     1  pivots are plain fractals, no ATR gate
     7  the six pivots must alternate, and lows must sit under highs
    10  the pattern MAY span a session gap; the pivot test may not
    12  M7 is the least-squares slope over 13 closes, not the endpoint diff
    13  opening size is recorded as an attribute, never as a threshold
    14  an ambiguous break waits for the next pivot, not for a fixed N
    18  three same-direction bars at the break is decisive on its own.
        Long bodies were measured and dropped: with a 50 percent body
        requirement only 2 of 44 upward breaks qualified, which makes the
        rule dead code.  Plain red/black fires on 45.5 percent.
    19  a breakdown carries a strength tag: run-of-three, or pivot-confirmed
    20  this file never emits an order

  NO FORWARD REFERENCE
    A pivot at bar i is only known at i+1, so every test reads [1] and [2].
    Nothing reads [0] of a series it is deciding about.

  NO DEEP LOOKBACK
    Pivot prices, bars and M7 are latched into arrays when the pivot forms.
    The pattern test is arithmetic on latched values, so MaxBarsBack only has
    to cover M7's 13 closes, not the pattern's span.
  ========================================================================== }
```

## 260870, ruling X3 of 2026-08-28

*was lines 208-232*

```
    { ---- 260870, ruling X3 of 2026-08-28.  How many bars a pivot must beat
      on each side.  1 reproduces every number verified so far, word for word.

      Willy asked whether I had noticed that a chart pattern is made of MANY
      bars.  At w=1, 35.9% of all bars are pivots -- one every 2.8 -- and the
      double top spans a median of THREE bars, which is a high, a bar, and a
      high.  Coarser windows give shapes that are what they claim to be:

          w   one pivot per   P29 span   double-top span
          1        2.8            12            3
          3        6.8            30            8
          5       11.1            44           11

      MaxBarsBack 100 caps it at 3: a pattern needs its span twice over --
      formation plus its own validity window -- plus w bars of confirmation
      delay, and w=5 puts 39% of patterns past 99 bars, w=8 puts 93%.

      ** A COARSER WINDOW IS NOT A COARSER TIMEFRAME.  The bars stay 5-minute,
      the entries, exits and stops stay 5-minute.  This changes only which
      bar counts as a pivot.

      The conclusions do not move with it -- P29 runs 0.16x / 0.18x / 0.20x
      at w = 1 / 2 / 3, the diamond stays level with its mirror, head and
      shoulders stays at parity -- so switching costs no re-derivation, only
      new counts. ---- }
```

## 1 = log every TL_New and TL_SetEnd

*was lines 241-245*

```
    Log_Lines               ( 0     ),     { 1 = log every TL_New and TL_SetEnd.
                                             Default off since 2026-08-26: the
                                             four-cyan-lines question it was
                                             built for turned out to be the
                                             chart's scale setting, not the code }
```

## Cyan until 260840, Green in 260840

*was lines 249-252*

```
    Col_Lower               ( LightGray ), { Cyan until 260840, Green in 260840.
                                             Green moved to Col_BreakUp, and Cyan
                                             is the P50 body, so the line takes
                                             the one neutral shade left }
```

## state 1, alive and waiting

*was lines 255-259*

```
    Col_Active              ( Blue    ),   { state 1, alive and waiting.  was Cyan,
                                             which 260840 also gave the P50 body --
                                             a whole P50 then rendered one colour.
                                             This is the least important state, so
                                             it takes the dimmest shade }
```

## P50 broadening BOTTOM, prior down

*was lines 262-264*

```
    Col_Shape_Bot           ( Cyan    ),   { P50 broadening BOTTOM, prior down.
                                             was White until build 260840, when
                                             White was reserved for the break }
```

## ruling C, 2026-08-27

*was lines 268-274*

```
    { ---- ruling C, 2026-08-27.  BREAK = close through the formation's OWN
      horizontal extreme.  Window opens the bar after the last pivot confirms
      and runs for the bars the formation itself took.  No point buffer and no
      N-bar confirmation: either would be the first swept threshold in this
      project.  The sloped-trendline alternative was rejected on evidence --
      it reports P51 breaking down 78% of the time and 96.5% of those fire
      while price is still above the formation's own lowest low. ---- }
```

## broadening family, 2026-08-28

*was lines 275-293*

```
    { ---- broadening family, 2026-08-28.  Seven variants share one frame:
      six alternating pivots, symmetric 3+3, lows under highs.  Only the two
      EDGES differ.  Definitions transcribed from s16s_p51_p54_scan.py, which
      is the reference the counts below were measured on.

      ALL FIVE DEFAULT ON.  Ruling of 2026-08-28: "if a shape occurs in the
      tape, draw it and label it -- that simple."

      260850 shipped P51 and P52 OFF because they fire 1,670 and 1,716 times
      against P29's 202 and would bury it on screen.  That was an aesthetic
      call standing in for a spec, and it broke the 2026-08-21 ruling that the
      census be complete: Enable_Pxx does not merely hide a variant, it stops
      v_Ok, so the shape is never registered, never counted, never classified.
      "I would rather not look at it" had become "it is not measured".

      The clutter is real -- 3,602 formations, roughly 11,000 drawing objects.
      If MC12 cannot carry that, the answer is to bound the DRAWN RANGE, the
      way Paint_MaxBack already bounds the back-paint.  It is not to stop
      detecting a shape that happened. ---- }
```

## P30 / P61 diamond, ruling I1 of 2026-08-28

*was lines 304-306*

```
    { ---- P30 / P61 diamond, ruling I1 of 2026-08-28.  Coded and drawn,
      not researched further.  ONE exists in 421,513 bars, so these are
      here for the day a second one forms, not for a population. ---- }
```

## the four edges

*was lines 311-313*

```
    Col_Dia_Line            ( Magenta     ),  { the four edges.  Bright is safe
                                                here: with one instance in eight
                                                years it cannot crowd anything }
```

## closes above the ceiling

*was lines 318-321*

```
    Col_BreakUp             ( Green   ),   { closes above the ceiling.  NOT a dark
                                             shade: the chart background is black.
                                             Magenta in 260840 collided with
                                             Col_Testing }
```

## 260870

*was lines 327-337*

```
    { ---- 260870.  The three BEARISH patterns that survived a block-local
      permutation control.  S16_S is short only, so the bullish half of
      group A is not a candidate at all -- P21's ascending channel is among
      the statistically cleanest and is excluded for being bullish.

      All three rest on an equality, and all three have MIRRORS THAT ALSO
      PASS, so what they establish is that price levels and move sizes get
      revisited exactly -- not a direction.  Direction has to come from
      elsewhere, which for S16_S is its own ZLEMA death cross.

      Reference at Pivot_Window = 1:  P18 6,352   P57 255   P17 1,365 ---- }
```

## ruling C break tracking

*was lines 427-429*

```
    { ---- ruling C break tracking.  Independent of SECTION 7: that lifecycle
      carries rulings 14 and 18 and breaks against the SLOPED line.  Both are
      kept, so neither ruling is silently overwritten by the other. ---- }
```

## 260841

*was lines 464-469*

```
    { ---- 260841.  This pattern's OWN anchors, latched at formation.
      v_H3 / v_L3 / v_H3b / v_L3b are rewritten by every later pivot push once
      the chain reaches six, but v_SlopeUp / v_SlopeDn are only recomputed when
      the pattern test passes.  Extending from the shared variables therefore
      mixes a later pivot's anchor with this pattern's slope.  Measured: it hits
      202 of 202 patterns, first at a median of 3 bars in. ---- }
```

## 260842 diagnostics

*was lines 475-477*

```
    { ---- 260842 diagnostics.  199 against a reference of 202, with the
      tracker internally consistent, means three formations were never seen.
      These four numbers say whether the INPUT differs or the CODE does. ---- }
```

## EIGHT slots

*was lines 494-499*

```
    { EIGHT slots.  three was sized for P29 alone.  With all five variants
      detecting, 3,602 formations share the window and the measured maximum
      concurrency is 6, so three would have overflowed and silently stolen
      slot 0 from a live P29.  Eight leaves two spare.  window = confirmation
      bar to confirmation + life, per section 6.  slot_overflow must read 0;
      if it ever does not, this array is undersized again. }
```

## 260843

*was lines 511-513*

```
    { 260843.  Formations per calendar year, 2019 at index 0.  Reference,
      from scripts/research/s16s_p29_clean.json:
        2019=9  2020=15  2021=18  2022=31  2023=24  2024=31  2025=42  2026=33 }
```

## SECTION 2 - M7, THE PRIOR-HOUR SLOPE

*was lines 544-549*

```
    { ---------- SECTION 2 - M7, THE PRIOR-HOUR SLOPE ------------------
      Ruling 12.  Least squares over the 13 closes ending on this bar.
      With a fixed window the denominator is a constant: sum of (k-6)^2
      for k = 0..12 is 182.  The mean term cancels because the weights
      sum to zero, so the whole fit collapses to one weighted sum.
      Weight for C[j] is (6 - j).  C[6] therefore drops out entirely.  }
```

## SECTION 2

*was lines 558-563*

```
    { ---------- SECTION 2.5 - RUNS OF Run_Bars SAME-DIRECTION BARS ----
      Ruling 18.  Read the input rather than hard-coding three, so the
      constant stays visible in the dialog and cannot silently drift out
      of step with the spec.  It is PINNED, not swept.
      Plain red/black only: a 50 percent body requirement was measured and
      dropped -- it fired on 2 of 44 upward breaks, which is dead code. }
```

## SECTION 3 - FRACTAL PIVOTS

*was lines 578-584*

```
    { ---------- SECTION 3 - FRACTAL PIVOTS ----------------------------
      The pivot sits on bar [1] and is confirmed here on bar [0].
      v_BIS >= 3 guarantees [0], [1] and [2] share one session, which is
      what ruling 10 requires: the pivot test is adjacency-dependent even
      though the pattern it feeds is not.
      A bar can be both a pivot high and a pivot low -- an outside bar.
      The high is pushed first, matching the Python sort order.           }
```

## resolve last bar's pending window-2 verdict, BEFORE any push

*was lines 586-595*

```
    { ---- resolve last bar's pending window-2 verdict, BEFORE any push ----
      A window-2 pivot at bar i needs bars i-2..i+2.  The window-1 pivot is
      confirmed at i+1, one bar too early, so the verdict is deferred by one
      bar and written back into the slot the pivot already occupies.
      Resolving before the push keeps the slot index valid: the chain only
      shifts or resets while pushing.
      The first version tested High[2] on the confirming bar, which asks
      whether the bar BEFORE the pivot was a window-2 pivot -- and since
      High[1] > High[2] is the pivot condition itself, High[2] > High[1] is
      false by construction.  S1 came out 0 on every pattern.               }
```

## 260870: the window-1 fractal generalised

*was lines 625-627*

```
{ 260870: the window-1 fractal generalised.  At Pivot_Window = 1 this is the
  old test character for character -- High[1] > High[2] and High[1] > High[0] --
  which is what protects the counts already verified on MC12. }
```

## SECTIONS 4-6 - PUSH, TEST, ADOPT

*was lines 659-674*

```
    { ---------- SECTIONS 4-6 - PUSH, TEST, ADOPT ----------------------
      One pass per pivot, NOT one pass per bar.

      An outside bar is both a pivot high and a pivot low.  The first
      version pushed both and then ran the pattern test once, so the
      intermediate chain -- the one ending on the HIGH -- was never tested.
      Python tests every six-window, so it saw those and the indicator did
      not.  The diff caught exactly two misses out of 48, 20250804 0945 and
      20251023 0250, and both sit on an outside bar.

      Wrapping push and test in a two-iteration loop makes the indicator
      test after every push, which is what the reference does.

      A run of same-type pivots cannot sit inside a valid window, so a
      repeat restarts the chain at one -- the surviving windows are exactly
      the alternating runs.                                              }
```

## 260842: v_PvDt and v_PvTm were missing from this shift, so

*was lines 688-691*

```
            { 260842: v_PvDt and v_PvTm were missing from this shift, so after
              any shift slot j held a correct PRICE with a stale DATE -- and
              TL_New anchors the line on exactly those two.  The line started
              at the right price on the wrong bar. }
```

## 260860: the same pivot also feeds the diamond's ten-slot chain

*was lines 720-723*

```
        { ---- 260860: the same pivot also feeds the diamond's ten-slot chain.
          Identical rules -- a repeated type resets, a full chain shifts by one
          -- so the two chains always agree about which pivots exist and differ
          only in how many they hold. ---- }
```

## classify into the seven variants

*was lines 784-791*

```
            { ---- classify into the seven variants ----
              rise / fall / flat are strict and exact.  "Equal" means EXACTLY
              equal, the same zero-parameter convention P29 already uses for
              the tweezers and matching-high candlestick patterns.  A tolerance
              here would be the first swept threshold in the family, and the
              scan measured what it would cost: one tick of slack takes P53
              from 7 to 40-plus, so the constant would be doing the work the
              shape is supposed to do. }
```

## Only P29 splits by M7

*was lines 831-834*

```
            { Only P29 splits by M7.  The other four are told apart by their
              own edges, so v_Kind carries the variant number unchanged and
              every label, colour and count downstream keeps working off one
              field instead of two. }
```

## ruling C: claim a break slot, and number this formation

*was lines 881-886*

```
            { ---- ruling C: claim a break slot, and number this formation ----
              The horizontal extremes come from the six pivots that define the
              formation, so they need no lookback -- the prices are already
              latched.  The window opens NEXT bar, which is p_last + 2: the
              last pivot only confirms on the bar we are standing on, so acting
              here would be look-ahead. }
```

## 260852: these four are the P29 ACCEPTANCE instruments and must

*was lines 887-892*

```
            { 260852: these four are the P29 ACCEPTANCE instruments and must
              stay P29-only.  Left ungated they counted every enabled variant,
              so the shipped defaults would have printed 217 formations
              against a reference of 202 and put P53 / P54 on the P50
              sequence.  Gating here keeps the acceptance test meaningful no
              matter which switches are on. }
```

## each variant numbers itself off the counter the

*was lines 908-910*

```
                { each variant numbers itself off the counter the
                  classification cascade already incremented, so a label
                  reads "P53 #1", "P53 #2" and not a borrowed P50 number. }
```

## measured maximum concurrency is 3, so this should never fire

*was lines 931-933*

```
                { measured maximum concurrency is 3, so this should never fire.
                  if it does, the measurement was wrong and the counter says so
                  rather than the tracker quietly dropping a formation. }
```

## the label

*was lines 947-950*

```
            { ---- the label.  Kind plus its own running number, so the last
              label of a kind on the chart says how many of that kind the
              loaded data holds.  Reset on every recalculation, so it counts
              within this chart's range, not since 2019. }
```

## top-shaped variants label above the ceiling, bottom-shaped

*was lines 953-955*

```
                { top-shaped variants label above the ceiling, bottom-shaped
                  below the floor.  P49 broadening top and P53 flat-top sit
                  above; P50, P51, P52 and P54 sit below. }
```

## draw the two E1 lines as OBJECTS, not as plots

*was lines 980-987*

```
            { ---- draw the two E1 lines as OBJECTS, not as plots ----
              Plot1/Plot2 looked right in isolation and wrong on a chart:
              MC12 joins across a NoPlot gap, so the last bar of one
              pattern was connected by a straight line to the first bar of
              the next, days later.  On 2026-06-10 18:00 to 06-11 13:10
              only 9 of 185 bars should carry a line -- 4.9 percent -- and
              the screenshot showed two lines spanning the whole chart.
              A trendline object is a discrete segment and joins nothing. }
```

## 260872: SECTIONS 6b AND 6c BELONG HERE, INSIDE `if v_Push`,

*was lines 1039-1055*

```
        { ---- 260872: SECTIONS 6b AND 6c BELONG HERE, INSIDE `if v_Push`,
          beside the P29 detection that has always been correct.

          260870 had them after the whole for loop: once per BAR, so a
          formation was recounted until the next pivot arrived 2.8 bars
          later.  P18 read 16,565 against a true 6,352.

          260871 moved them inside the for loop but still after this
          `if v_Push` block -- and the loop runs twice on EVERY bar
          whether or not a pivot exists, so it went to twice per bar and
          got WORSE: P18 37,662, and the diamond 1 -> 3.

          The requirement was never "inside the loop".  It is "only when a
          pivot is actually pushed", which is this block and nothing
          wider.  An outside bar enters it TWICE, once for the high and
          once for the low, and the chain differs after each, so both
          pushes are tested -- which a per-bar flag could not do. ---- }
```

## SECTION 6b - P30 / P61 DIAMOND

*was lines 1056-1078*

```
            { ---------- SECTION 6b - P30 / P61 DIAMOND ------------------------
              Ruling I1, 2026-08-28.  Coded and drawn, NOT researched further.

              A diamond is a broadening half followed by a converging half sharing an
              apex.  P29's founding rule -- two points define a line, three confirm the
              direction is sustained -- makes that five highs and five lows:

                  broadening   H1 < H2 < H3     L1 > L2 > L3
                  converging   H3 > H4 > H5     L3 < L4 < L5

              "Widest in the middle" needs no separate condition: H2 > H1 with L2 < L1
              forces H2-L2 > H1-L1, and the same on the right.  Zero free parameters.

              Measured over 421,513 bars: ONE exists, 2025-09-08 09:55 to 11:50, a
              bottom, span 23 bars.  The mirror (narrowest in the middle) has two.  The
              six-pivot relaxation has 1,467 against a mirror of 1,581 -- identical
              independence ratios, 0.80x each -- which is why only the ten-pivot form
              is coded: the loose one is not a confirmed diamond, it is what
              non-monotone pivots do by chance.

              Note that every complete diamond CONTAINS a P29: its broadening half is
              P29's condition word for word.  So the six-pivot chain will have flagged
              the P29 first and this block adds the completed shape on top.           }
```

## the four edges, as objects

*was lines 1163-1165*

```
                { ---- the four edges, as objects.  A diamond that is only recoloured
                  bars does not read as a diamond; the edges are the shape.  One
                  instance in eight years means four more drawing objects is free. ---- }
```

## 260861: the label takes the EDGE colour, not the body colour

*was lines 1199-1204*

```
                        { 260861: the label takes the EDGE colour, not the body colour.
                          Col_Shape_P30/P61 are dark by design -- they tint bars that
                          already have shape -- but as text on a black chart they are
                          unreadable, and the 2025-09-08 screenshot showed "P61 #1"
                          smudged against a neighbouring P50 label.  The edges are
                          already bright, so this spends no new colour. }
```

## SECTION 6c - P18 / P57 / P17

*was lines 1220-1249*

```
            { ---------- SECTION 6c - P18 / P57 / P17 -------------------------
              The three BEARISH patterns of group A that survived their control, coded
              per Willy's ruling of 2026-08-28.

              No new chain.  The six-pivot chain holds the last six alternating pivots,
              so the last three and the last five are slices of it:

                  P17  last 3   H L H
                  P18  last 5   H L H L H
                  P57  last 5   H L H L H   (uses the first four)

              The chain enforces alternation, so testing the FIRST pivot's type settles
              the whole slice.

              P18 uses Willy's band device rather than exact equality: PH1 and PH2
              define the zone and PH3 is tested against it.  The tolerance is
              |PH1 - PH2|, taken from the pattern itself, so no parameter is spent, and
              the order is causal -- the first two peaks form the zone, the third tests
              it.  Exact equality gives 43 instances with 2026 empty; the band gives
              6,352 with no empty year AND THE SAME RATIO, 10.20x against 10.19x,
              because the zone widens with the market while a fixed zero does not.

              P57 is tested on a five-pivot slice although it reads only four.  That
              matches the reference scan exactly, and matching the reference is worth
              more here than saving one pivot of delay.

              NO BAR PAINTING.  Fourteen of PowerLanguage's sixteen colours are already
              spoken for and the two left are invisible on a black chart; P18 alone
              runs 831 a year and would bury the P29 family under it.  The labels carry
              what matters and the counters carry the rest.                          }
```

## SECTION 7 - LIFECYCLE

*was lines 1341-1347*

```
    { ---------- SECTION 7 - LIFECYCLE ---------------------------------
      Precedence, most terminal first:
        expiry           lifetime equals the bars the pattern took to form
        run of three     decisive on its own, no wait                (r18)
        ambiguous break  hold as TESTING until the next pivot rules   (r14)
      A false break returns the pattern to ACTIVE.  It is never consumed
      by emitting a signal -- that is the signal layer's business.     }
```

## one row per extension

*was lines 1363-1365*

```
        { one row per extension.  If a line spans the whole chart, these rows
          are what shows how far the end was pushed and on which bar it
          stopped -- the moment the state machine let go. }
```

## SECTION 7b - RULING C BREAK

*was lines 1448-1457*

```
    { ---------- SECTION 7b - RULING C BREAK ---------------------------
      Deliberately separate from SECTION 7.  That lifecycle breaks against the
      SLOPED extended trendline and carries rulings 14 and 18; this one breaks
      against the formation's OWN horizontal extreme, per ruling C of
      2026-08-27.  Keeping both means neither ruling is silently overwritten,
      and the two answer different questions: SECTION 7 decides when the
      pattern stops being live, this decides which side it left through.

      Three slots, scanned every bar.  Down is checked before up and wins a
      tie, matching s16s_break_outcome.py so the counts are comparable. }
```

## SECTION 8 - PLOTS

*was lines 1539-1553*

```
    { ---------- SECTION 8 - PLOTS -------------------------------------
      Only the two extended trendlines, and only while the pattern can
      still act.  A dead pattern plots nothing, so what is on screen is
      exactly what the state machine holds.

      Show_Pivots defaults to OFF, and that is the important part.
      Plot3/Plot4 fire on EVERY fractal pivot in the series -- 75,145 highs
      plus 76,032 lows across 421,513 bars, or 35.9% of all bars.  Drawn as
      a line that is a full-screen zigzag, and the 25-per-year patterns
      vanish inside it.  The first screenshot attempt on 2026-08-26 showed
      exactly that.  Turn them on only to inspect pivot detection itself,
      and set their style to Point in Format Indicator when you do.

      Colours and width are set in code so the picture does not depend on
      whatever the Format dialog happens to remember.                     }
```

## SECTION 8a - PAINT THE PATTERN'S OWN BARS

*was lines 1555-1577*

```
    { ---------- SECTION 8a - PAINT THE PATTERN'S OWN BARS -------------
      The reason this exists is not that too little was drawn.  It is that
      the patterns cannot be FOUND: 202 of them across 421,513 bars is one
      every 2,086 bars, about one per nine trading days, so scrolling will
      essentially never land on one.  Two trendlines on an empty chart are
      invisible until you already know where to look.

      PlotPaintBar recolours the price bars themselves, so a pattern reads
      as a coloured band in the price series.  It costs no drawing objects,
      which matters because 202 patterns times nine objects each would sit
      near MultiCharts' ceiling -- the paint is never subject to that.

      Colour carries the state, so the picture says what the state machine
      holds without a second pane:

          yellow    the bar the pattern completed on
          cyan      state 1, alive and waiting
          magenta   state 2, price is testing an edge

      A dead pattern paints nothing, exactly as it plots nothing.

      PlotPaintBar occupies Plot1..Plot4 internally.  That is why the
      trendline plots moved to 5/6, the pivots to 7/8 and the state to 9.  }
```

## the pattern's OWN span, painted backwards on the forming bar

*was lines 1579-1594*

```
{ ---- the pattern's OWN span, painted backwards on the forming bar ----
  This is the half that matters and the half Build_ID 260827 missed.
  v_State only turns 1 when the sixth pivot is CONFIRMED, which is after
  the shape is complete: on 2026-06-11 the six pivots run 01:20 to 02:05
  and state turns 1 at 02:10.  Painting forward from there colours bars
  that are not part of the pattern and leaves every pivot uncoloured.

  v_PvBar already holds each pivot's bar number, so the distance back to
  the first pivot is known without a lookback on price.  Offsets 1 to span
  are painted; offset 0 is the confirming bar and belongs to the forward
  paint below.

  Span median is 12 bars and the longest measured is 43, so the two paints
  together mark roughly 24 bars -- enough to catch the eye at a normal
  zoom, with the six pivots INSIDE the coloured region rather than to the
  left of it.                                                             }
```

## 260860: the diamond paints first, and it paints over the P29

*was lines 1596-1599*

```
{ 260860: the diamond paints first, and it paints over the P29 inside it.
  Every complete diamond CONTAINS a P29 -- the broadening half is P29's
  condition word for word -- so without this the rarer shape would be hidden
  under the commoner one it is made of. }
```

## P49 and P50 are the same SHAPE told apart by M7, the trend

*was lines 1618-1622*

```
    { P49 and P50 are the same SHAPE told apart by M7, the trend over the
      twelve bars before the first pivot.  v_Kind already carries it, but
      until now it only reached the print log -- the chart showed "a
      pattern" and no more.  Population splits 111 / 91, so half the
      information was being computed and thrown away at the screen. }
```

## The break bar outranks the formation body, and reuses the

*was lines 1642-1646*

```
{ The break bar outranks the formation body, and reuses the SAME PlotPaintBar
  name.  A second PlotPaintBar would claim four more plot numbers and collide
  with the trendlines at 5/6, the pivots at 7/8 and the state at 9 -- every one
  of them would have to be renumbered.  One plot group, colour chosen per bar,
  changes nothing else on the chart. }
```

## Line_Mode 2 keeps the old plots for comparison

*was lines 1673-1675*

```
{ Line_Mode 2 keeps the old plots for comparison.  It interpolates across
  gaps -- that is the defect, kept switchable rather than deleted so the
  difference can be seen side by side. }
```

## the acceptance test, printed rather than eyeballed

*was lines 1701-1703*

```
{ ---- the acceptance test, printed rather than eyeballed.  Against the full
  2019-01-02 to 2026-08-22 series these must read 202 / 75 / 88 / 39 / 0.
  Anything else means the port is wrong, not "close enough". ---- }
```

## the reference, measured from scripts/research/s16s_5min

*was lines 1705-1707*

```
    { the reference, measured from scripts/research/s16s_5min.csv:
      bars 421,513   first 20190102 0850   last 20260822 0500
      pivot_high 75,145   pivot_low 76,032 }
```
