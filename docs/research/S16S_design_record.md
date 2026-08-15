# S16_S_MACrossShort - Design Record

This file holds everything that used to sit inside
`strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.25.0.pla`.

The strategy was 4,460 lines of which 675 were code. The comments were
moved here on 2026-08-15 and **not a character of code changed** -- the
move was verified by stripping every comment from the before and after
files and asserting the remainder was byte-identical.

Read this alongside the .pla, not instead of it. Each `{ ===== Group X
===== }` divider still in the code carries the section number here that
explains it.

---

## 1. Current anchor

| | |
|---|---|
| net profit | 2,587,200 |
| trades | 180 |
| profit factor | 2.08 |
| max strategy drawdown | -364,800 |
| return on account | 898.33 |

Any edit to the .pla must reproduce those five numbers before its own
result is read. MC12 retains the previous run's input values rather than
reloading the file, and that has voided whole batches in this project.

---

## 2. Version history

Verbatim, newest first, exactly as it stood in the .pla header.

```text
================================================================================
S16_S - MOVING AVERAGE CROSS SHORT STRATEGY
Signal Name : S16_S_MACrossShort
MC Load Name: STRATEGY_GEN_S16_S_MACrossShort
Version     : v1.25.0 Hold-Cap Form (2026-08-15, base v1.24.0)

================================================================
v1.25.0  WHY THE HOLD CAP GETS A SECOND FORM
================================================================

ADOPTED 2026-08-15 AFTER A 90-CELL MC12 SWEEP. Form 2 ships ON:

M8_Form          2
MaxHold_Pct      2.40
MaxHoldingBars   24 -> 48
QS_MaxLoss_Pct   0.70 UNCHANGED (see the re-sweep below)

                      anchor v1.24.0      adopted        delta
net profit                 2,328,800    2,587,200     +258,400
trades                           180          180            0
profit factor                   1.98         2.08        +0.10
max strategy drawdown       -364,800     -364,800            0
return on account             806.33       898.33          +92
avg winning trade             83,971       90,575        +7.9%
win rate                      31.11%       30.56%      -0.55 pp
win/loss ratio                  4.35         4.73        +0.38

The trade COUNT and the DRAWDOWN are both unchanged, so the entry
population is identical and the two versions are entry-paired. The
whole +258,400 is exit-side. A lower win rate with a 7.9% larger
average winner is the signature this strategy is supposed to have.

THE BATCH WAS VALID BEFORE IT WAS READ

Anchor cell M8_Form=1 x MaxHoldingBars=24 returned 2,328,800 /
180 / PF 1.9811257162 / -364,800, matching v1.24.0 exactly. The
nine Form 0/1 cells carrying different MaxHold_Pct values all
returned the identical figure, which is the leak test: Form 1 does
not read MaxHold_Pct, and it demonstrably did not.

TWO-SIDED SUPPORT ON BOTH ADOPTED DIMENSIONS (at 48 bars / 0.70)

MaxHold_Pct        2.0  2,371,600   2.4  2,587,200   2.8  2,369,200
MaxHoldingBars      24  2,418,000    48  2,587,200    72  2,507,200

Neither is a boundary. Step was 0.2 on the percentage, which is
too coarse to tell a plateau from a spike -- a step-0.1 sweep is
queued for exactly that reason, and it also fills the 2.6 cell
that did not surface in the top 51.

QS_MaxLoss_Pct RE-SWEPT AND DELIBERATELY LEFT ALONE

B4 disabled this leg while Trail and ML were both still running.
B8 and B10 later removed both, so B4's premise -- that the leg was
redundant against three overlapping protections -- no longer held,
and the value was re-swept rather than inherited:

  0.70  2,587,200  180 trades  DD -364,800   <- kept
  0.65  2,584,000  180 trades  DD -364,800
  0.60  2,572,800  180 trades  DD -364,800
  0.55  2,446,400  181 trades  DD -442,000
  0.50  2,434,800  181 trades  DD -409,200

Monotone against lowering it, and below 0.60 the drawdown degrades
as the leg wakes up. B4's ruling survives its own premise being
withdrawn. Note the grid stopped at 0.50, so 0.25 -- the v1.7.1
optimum -- was not literally re-tested; the trend is unambiguous
in both net profit and drawdown, but that is inference, not a
measured cell.

WHAT THE OFFLINE STUDY GOT RIGHT AND WRONG

Predicted: Form 2 beats the anchor by +150,000 to +500,000.
  Correct. +258,400.
Predicted: the optimum sits at MaxHold_Pct 2.0.
  Wrong. MC12 puts it at 2.4. The 64-trade study detected touches
  with the bar LOW and assumed a fill at the target, and it ran
  the population in isolation with no competing exit legs. Its
  2.0 is NOT validated by this run; 2.4 is the measured answer and
  the offline figure should not be cited as confirmation.

STILL OPEN AT ADOPTION -- both are checks, not blockers

1. The mechanism is unverified. SX_MA_TimeStop_Pct must appear in
   the trade list and SX_MA_GoldenCross must fall from its 3
   trades / -79,200. Right net profit with the wrong mechanism is
   coincidence and would have to be withdrawn.
2. Struct_Lookback is now unclamped. The structure window is
   MinList(Lookback, BarsSince+1); at a 24-bar cap anything above
   25 was inert, and at 48 it is not. A2's "20 is optimal" was
   measured under the old cap and is now stale.

WHAT THE EXIT ATTRIBUTION FOUND

The strategy was described in its own notes as "91% exits on the
clock", and that was treated as one mechanism. It is two, doing
opposite jobs, and lumping them hid where the money is:

  SX_MA_QuickStop_Time   116 trades  -2,058,800   0.0% wins
  SX_MA_TimeStop          40 trades  +4,000,800  97.5% wins

116 small losses buy 40 large winners. This leg -- P5 -- is the
winner side, and it is the one whose FORM had never been tested.

WHY A PERCENTAGE, MEASURED RATHER THAN ASSUMED

Three candidate forms were compared on the 64 trades that survive
QuickStop, so both forms see the same population:

  dispersion of the quantity being held fixed
    bars to peak    mean 32.4   sd 27.4   CV 0.847
    percent to peak mean 1.536  sd 1.115  CV 0.725   <- steadier

  best value, fitted separately in each era
    2020-2022 (n=26)   60 bars    2.0%
    2023-2026 (n=38)   60 bars    2.0%
    both agree on both forms, so NEITHER form is era-fitted

  value at the optimum, all 64
    24 bars (current)   4,248,000
    60 bars             4,793,000
    2.0 percent         5,143,000   <- +895,000 over current

2.0% is an interior peak: 1.6% and 2.5% are both lower, in both
eras independently. It is not a boundary and not a lone spike.

WHAT WILL SHRINK THAT NUMBER, AND WHY IT IS STILL WORTH TESTING

+895,000 is GROSS. An offline curve cannot see mechanism handoff.
B5 measured the handoff directly when the cap moved 24 -> 30:
+495,200 from trades the time stop still caught, -360,800 from
trades passed to other legs, -215,200 of it to GoldenCross across
19 trades. Net +134,400 from a much larger gross.

Form 2 should suffer LESS of that than simply extending the bar
count, because it closes the winner AT a target instead of
letting it drift on until a golden cross takes it. That is the
structural claim, and it is what the sweep is for.

ALSO RECORDED HERE (documentation only, no code change)

SX_MA_QuickStop_Loss fires ZERO times in the 180-trade anchor, so
the loss side is NOT running on a percentage today whatever the
input name suggests. That is DELIBERATE, not an oversight, and the
distinction matters because an oversight invites a "fix":

  v1.7.1  MC12 sweep 0.05 ~ 0.30 step 0.025, adopted 0.25.
          At 0.25 the leg was live and firing.
  B4      0.25 -> 0.70, parking the threshold beyond what a trade
          can reach inside the 4-bar window that P1b terminates.
          0.70 / 0.75 / 0.80 return identical results, so this is
          SATURATION and not a truncated grid. QuickStop keeps
          only its TIME leg and the loss side reverts to SL_Pct.

So the optimiser was shown this leg twice and switched it off the
second time. DO NOT lower QS_MaxLoss_Pct to "wake it up" -- that
reverses a measured decision, and the price condition is still
served by a market order, which is a separate latent defect that
only stays dormant while the threshold is unreachable.

The live percentage on the loss side is SL_Pct = 1.00, capping the
ATR stop distance. SX_MA_SL takes 3 trades at -131,200.

THE PATTERN THIS COMPLETES, AND WHAT IT IMPLIES FOR FORM 2

Every giveback or loss-truncation mechanism this strategy has been
offered has been measured and switched OFF:

  Trail_On        -> 0    B8, worth +111,600 to remove
  ML_On           -> 0    B10
  QS_MaxLoss_Pct  -> off  B4, parked out of reach

What survives on the loss side is a BAR rule (P1b, 116 trades) and
a last-resort ATR stop (3 trades). The strategy has consistently
refused to have its losers cut on price and its winners protected
on giveback.

Form 2 is a profit TARGET, which is also a truncation -- of the
right tail. So there is a standing prior against it from three
independent measurements. The counter-evidence is that all three
of those tested the LOSS side or the giveback; a target on the
winner side has never been tested at all, and the 64-trade study
puts 2.0% ahead of every bar count in both eras. The sweep, not
this note, settles it.

            Gap_KB_Gate_On adopted 2026-08-15

ADOPTED 2026-08-15: Gap_KB_Gate_On 0 -> 1

The long-lower-wick filter goes live. It is the only rule out of
everything measured in the session-open programme that has
statistical support, and it costs nothing:

  support     3,669 session opens, ONE pre-registered grouping,
              permutation p = 0.0010 / 0.0164 / 0.0070 at +1/+2/+3
  cost        zero. MC12 confirmed 180 trades / 2,328,800 / PF
              1.9811257162 / DD -364,800, identical to the anchor,
              with all 35 checked inputs at their adopted values
  class       FILTER. Worst case is a forgone trade, bounded
  mechanism   a long lower wick means the low was bought back, so
              a short entered just after it is entering against
              demand that has already shown itself

IT WILL NOT MOVE ANY BACKTEST NUMBER. It is FORWARD protection.
The sample contains no trade in its window, and the reason is
arithmetic rather than luck -- see the ceiling below. Author's
ruling 2026-08-15: the strategy must handle these regimes in live
trading even where the sample never exercised them.

------------------------------------------------------------------
C MEASURED 2026-08-15: ACCUMULATION IS WORSE THAN THE SNAPSHOT
------------------------------------------------------------------

The open question was whether recording shape from the first bar
ONWARD -- an accumulator rather than a snapshot -- predicts better.
Measured on the 3,669 opens, tercile split, permutation tested,
forward movement taken from bar N's CLOSE so the bars that define
the group never enter the window being predicted:

  predictor                    +1 bar    +2 bars   +3 bars
  A1   first bar's wick        p=0.05    p=0.01    p=0.00
  Asum2/3/4/6  running sum     p=0.88    to        p=0.98
  Acnt2/3/4/6  running count   p=0.63    to        p=0.88

A1 is the only predictor significant across all three horizons,
and its effect GROWS with horizon (-0.0079% / -0.0136% /
-0.0245%). Every accumulator is weaker. Bars 2, 3 and 4 carry no
forward information, so adding them dilutes bar 1's signal instead
of reinforcing it.

So the snapshot form already in this file is the right form, and
the accumulator idea is closed on measurement rather than on the
faulty inference made earlier the same day (decay of "bar 1 ->
later bars" was wrongly read as evidence about "bar 2 -> later
bars", which is a different question).

------------------------------------------------------------------
THE CONTROL THAT MATTERED MOST: IT IS AN OPEN-BAR PHENOMENON
------------------------------------------------------------------

The same measurement was run on 11,470 RANDOM mid-session anchors.
If it had held there, this would not be a gap rule at all -- it
would be a per-bar rule with a population of 418,096 instead of
3,669, and the ceiling below would not apply.

It did not hold. Two of 27 cells fell under p = 0.05, against 1.35
expected by chance, and the two differences from the session-open
result are decisive:

  sign          session opens NEGATIVE (wick -> price rises)
                mid-session   POSITIVE (opposite direction)
  persistence   session opens STRENGTHEN with horizon
                              (p 0.05 -> 0.01 -> 0.00)
                mid-session   VANISH
                              (p 0.03 -> 0.36 -> 0.62)

Opposite sign and opposite persistence is not the same effect
weakening; it is a different thing, most likely noise. The
population stays at 3,669 and must not be extrapolated to every
bar.

------------------------------------------------------------------
THE CEILING, MEASURED THREE TIMES
------------------------------------------------------------------

A session runs about 120 bars. Any session-open rule reaches the
first 3 -- 2.5% of them -- and this strategy takes 180 trades in
6.4 years. 2.5% x 180 is between four and five trades, and that is
the whole capacity of the idea, independent of how well any rule
is written:

  v1.16.0 down-gap filter          1 trade
  v1.23.0 long lower wick          0 trades
  v1.24.0 up gap, both modes       0 trades (MC12, six cells)

------------------------------------------------------------------
COVERAGE: EVERY OPENING REGIME NOW HAS AN ANSWER
------------------------------------------------------------------

"Fully considered" was defined by the author as every regime being
MEASURED, not every regime having a rule. Blanks are what get
re-opened blindly; a measured null does not.

  down gap + first bar rose >= X   not significant (p 0.24-0.95)
                                   rule ON from v1.16.0, n=1 basis
  down gap + LONG LOWER WICK       p 0.001/0.016/0.007  RULE ON
  down gap + long upper wick       significant the other way, no rule
  down gap + no clear wick         flat, no rule
  up gap + first bar fell >= X     opposite direction to the
                                   hypothesis; MC12 six cells; no rule
  up gap + first bar rose >= X     p = 0.661; no rule
  flat open                        60% directionless; no rule
  bars 2/3 own shape               accumulator weaker than snapshot
  per-bar generalisation           control null, sign-flipped

ONE INVERSION REMAINS, and it is recorded rather than acted on.
Gap_Rise_Min_Pct = 0.20 has been live since v1.16.0 on n=1 evidence
and does not replicate on 3,669 opens; the long-wick rule that does
replicate was the one switched off. Turning it on fixes half of
that. Retiring the other half needs its own pre-registered test,
not a re-read of the sweep table that found it wanting.


v1.24.0 (2026-08-15) THE OTHER HALF OF THE GAP:

Every gap rule in this file has only ever looked at DOWN gaps.
v1.16.0 and v1.23.0 both open with "v_Sess_Gap_Pct <= -threshold".
An up gap has never been examined by the strategy at all.

THE HYPOTHESIS (author, 2026-08-15). After an up gap, a first bar
that closes BELOW its open by X% is a session that opened high and
was sold. Supply has shown itself, so a short should be MORE
willing to enter, not less.

TWO MODES, because "enter more" and "block" are not the same kind
of object and only one of them is a filter:

  Mode 1  RELAX. Up gap, first bar fell >= UpGap_Bar1_Pct: the
          slope threshold is multiplied by UpGap_Relax_Mult for
          the first UpGap_Scope_Bars bars. ADDS entries.
  Mode 2  MIRROR FILTER. Up gap, first bar rose >= UpGap_Bar1_Pct:
          block. REMOVES entries. The symmetric twin of v1.16.0.

MODE 1 IS A DIFFERENT CLASS OF CHANGE. Every gap rule to date has
been a filter: it can only remove trades, and its worst case is
forgone profit. Mode 1 lowers an entry gate, so it admits crosses
the strategy has never traded and its worst case is unbounded.
Judge it more harshly than a filter, and do not adopt it for a
small net gain.

WHAT THE OFFLINE MEASUREMENT SAID -- AND WHY IT IS NOT THE JUDGE.
On 3,669 session opens, after an up gap a first bar falling 0.20%
or more was followed by a RISE over the next bar: difference
-0.0298%, permutation p = 0.032, and at 0.30% it was -0.0726%,
p = 0.005. That reads as "the dip was bought" -- the same
mechanism v1.23.0's long-lower-wick group rests on -- and it
points the OPPOSITE way to the hypothesis.

It is recorded, not acted on, for three reasons. That offline
pipeline was caught with two separate bugs on 2026-08-15, one of
which put the scope test on the fill bar instead of the signal
bar. Its thresholds were swept, not pre-registered, so 45 cells
were examined and roughly two false positives are expected at
p < 0.05. And the standing rule on this desk is that offline work
generates hypotheses while MC12 returns verdicts.

So the prediction is written down here in order to be wrong in
public if it is wrong: Mode 1 should REDUCE net profit.

SHIPS OFF. UpGap_Gate_On defaults to 0, and the relaxation
resolves to v_MinSlope_Eff = MinSlope_Rate, so v1.24.0 must
reproduce v1.23.0 and v1.22.0 exactly: 180 trades / 2,328,800 /
PF 1.9811257162 / max strategy drawdown -364,800.

v1.23.0 First-Bar Shape Gate (2026-08-15, base v1.22.0)

v1.23.0 (2026-08-15) v_KB_TYPE FINALLY GETS READ:

The eighteen-shape taxonomy has existed since v1.16.0 and has
never been consulted -- written 18 times, read 0. This version
wires it into the gap decision as a second, independent rule.

WHAT THE OLD RULE CANNOT SEE. v1.16.0 asks whether the session's
first bar closed above its own open and by how much. That uses
Open and Close and discards High and Low -- and the wicks are
where the rejected prices are recorded. Two bars with the same
(Close - Open) / Open can be a bar that closed on its high with
no upper wick, or a bar that ran up and was sold back. For a
short entering just afterwards those are opposite situations,
and the old rule cannot tell them apart.

MEASURED ON 3,669 SESSION OPENS, NOT ON 180 TRADES. The 5-minute
series was rebuilt offline from the 1-minute export (418,096
bars), session opens were found with the same transition test the
strategy uses, and each first bar was classified with this file's
own thresholds. Forward movement was measured from that bar's
CLOSE only, so nothing is computed from the bar that defines the
group -- the circularity trap this file has warned about since
v1.16.0.

After a down gap of 0.10% or more:

  group              n     +1 bar    +2 bars   +3 bars   +4 bars
  long lower wick   263   -0.0252%  -0.0282%  -0.0449%  -0.0260%
  long upper wick   230   +0.0129%  +0.0100%  +0.0073%  +0.0197%
  no clear wick     238   +0.0017%  +0.0017%  +0.0117%  +0.0090%
  positive = price FELL = favourable to a short

Permutation test, 5,000 shuffles, on the SINGLE pre-registered
grouping rather than on seventeen types:

  +1 bar  p = 0.0010     +3 bars  p = 0.0070
  +2 bars p = 0.0164     +4 bars  p = 0.1204

Three consecutive horizons, one hypothesis. What makes it more
than a survivor of multiple comparisons is that the structure is
consistent in three directions at once: the opposite group runs
the opposite way and is also significant, and the null group sits
on zero. The mechanism reads directly -- a long lower wick means
the low was bought back, so a short entered just after it is
entering against demand that has already shown itself.

Gap_KB_Scope_Bars = 3 comes from where significance ENDS, not
from matching the neighbouring Gap_Scope_Bars.

------------------------------------------------------------------
THIS VERSION EXISTS TO BE FALSIFIED IN MC12
------------------------------------------------------------------

The offline reconstruction behind every number above has never
been checked against MC12. The ZLEMA rebuild was validated once
(7,778 crosses against 7,779, 127 passes against 127) but the
session walk and the shape classifier never have been. So the
six cells below are stated as exact predictions BEFORE they are
run, naming the trades that must disappear:

  Group Scope   trades      net      trades that must vanish
    --     --      180  2,328,800    anchor, gate off
     1      3      180  2,328,800    none
     1      6      178  2,342,800    2022-07-01 09:15 type 3 -5,200
                                     2022-10-31 09:10 type 9 -8,800
     2      3      179  2,319,600    2024-09-04 09:00 type 6 +9,200
     2      6      177  2,336,800    the above plus
                                     2021-03-11 09:15 type 12 -28,000
                                     2022-06-19 09:10 type 6 +10,800
     3      3      179  2,341,200    2020-03-30 15:15 type 14 -12,400
     3      6      174  2,248,400    six trades incl.
                                     2021-03-12 09:10 type 8 +109,200

If they match, the session walk, the gap arithmetic and the shape
classifier are all confirmed and the measurement above can be
relied on. If they do not, every conclusion drawn from the
offline rebuild is void and has to be redone.

Group 3 / scope 6 is the strongest of these: it names six trades
including a +109,200 winner, which a wrong implementation is very
unlikely to reproduce by accident.

GROUPS 2 AND 3 ARE NOT ADOPTION CANDIDATES. They exist to make
the reconstruction falsifiable in both directions and to give the
null group a control run.

SCOPE 6 IS NOT AN ADOPTION CANDIDATE EITHER. Significance ends at
bar 4 (p = 0.12). The two trades it would block are both losers
worth 14,000 together, and taking scope from 3 to 6 to collect
them would be fitting the rule to the 180 trades -- the exact
error this measurement was designed to avoid.

v1.22.0 Day Session Tail Rule (2026-08-13, base v1.21.0)
            Defaults carry B4-B10 as of 2026-08-14

DEFAULTS UPDATED 2026-08-14 AFTER B8 / B8b / B9 / B10:

Four values move. Every batch was run exhaustive and each result
was confirmed against the previous batch's adopted cell.

  Struct_Trigger_Pct   1.00 -> 0.60    B8   6,156 cells
  Struct_Buffer_Pts    20   -> 12      B9   2,240 cells
  BE_Trigger_Pct       0.60 -> 0.70    B9
  ML_On                1    -> 0       B10    504 cells

CURRENT ANCHOR (all defaults), measured 2026-08-14:
  180 trades / 2,328,800 / PF 1.9811257162 / adjusted PF 1.5744 /
  max strategy drawdown -364,800 (-14.02%) / Sharpe 0.1776 /
  Sortino 1.0780 / account return 806.37

Campaign: 748,000 -> 2,328,800, +211.3%, across B1 B2 B2b B3 B3b
B4 B5 B6 B7 B8 B8b B9 B10 plus the day-tail defect fix.

THREE EXIT MODULES ARE NOW OFF OR INERT, ALL BY MEASUREMENT:
  Trail_On  = 0   B7, 209 of 209 enabled cells lost. Gross loss was
                  identical with it on and off, so it never
                  prevented a loss in 6.4 years -- it only
                  truncated winners.
  ML_On     = 0   B10, 504 of 504 cells identical.
  Tier2_On  = 0   retired earlier, B12 will re-test it.
Trail_Trigger_Pct, Trail_Giveback_Pct and the six ML detector
inputs are LEFT UNCHANGED. Writing a measured-losing cell into a
disabled module plants a value in the file that looks adopted.

ONE THING IS STILL UNEXPLAINED. B9 records the cell
(Buffer 12, Struct 0.60, BE 0.70, Cost 20) at 2,276,400 while B10
returns 2,328,800 for the same configuration with ML at the file
default. The same inputs cannot give two outputs, so one run held
a value that its report does not show. It does not block adoption
-- ML_On = 0 lands on 2,328,800 under either reading -- and B11's
acceptance cell settles it: (ATR_Len 14, StopATRMult 4.0,
SL_Pct 1.00) must return 2,328,800.


v1.22.0 (2026-08-13) THE DAY SESSION GETS ITS OWN NO-ENTRY RULE,
                   AND B4/B6/B7 WINNERS GO INTO THE DEFAULTS:

------------------------------------------------------------------
B14 + B5b (2026-08-14): TIME GATES RE-SWEPT. ZERO CHANGE.
------------------------------------------------------------------

3,319 cells. Not one default moves. The output of this batch is
knowledge, not parameters, so it is recorded here rather than in
the input block.

B14, 3,300 cells exhaustive, QuickStop_MaxBars 2-12 step 1 x
QS_MaxLoss_Pct 0.10-0.80 step 0.05 x MaxHoldingBars 6-120 step 6.
Acceptance cell (4, 0.70, 24) returned 2,328,800 / 180 / PF 1.98 /
DD -364,800 -- five fields against the campaign baseline, PASS.

  QuickStop_MaxBars = 4 is an INTERIOR optimum. The top 28 rows all
  carry 4; the first 5 appears at row 29; 2 and 3 do not reach the
  top 50. No boundary extension owed.

  QS_MaxLoss_Pct is INERT above 0.70. Cells 0.70 / 0.75 / 0.80
  return identical net to the last dollar, which is saturation, not
  a plateau -- the threshold is never reached. Added to the inert
  registry. DO NOT lower it: B4's order-type defect (price
  condition executed as a market order, MAE overshooting the
  threshold) is dormant only because the threshold is unreachable.

B5b, 19 cells, MaxHoldingBars 18-36 STEP 1. Both acceptance cells
present and correct: 24 = 2,328,800 and 30 = 2,437,600.

NET PROFIT ON THIS PARAMETER IS NOISE. Mean absolute difference
between adjacent bar counts is 117,100 over the 18 gaps. The
24-vs-30 gap is 108,800 and the 24-vs-27 gap is 89,200. BOTH SIT
INSIDE THE NOISE BAND. B14's step-6 grid sampled 18/24/30/36 and
drew a clean single peak; step 1 shows a sawtooth. 19 -> 20 alone
swings 166,800.

DRAWDOWN IS WHERE THE STRUCTURE IS, and it is clean:

  18-27   -364,800   ten consecutive values, flat
  28-30   -370,800
  31      -390,000
  32      -512,400   cliff
  35      -581,600

THE CLIFF IS AT 31, not at 35 as the coarse grid implied. And the
mechanism is visible: at 36 the gross loss is IDENTICAL to 30
(-2,394,400) with the same 55/125 win/loss split. The extra
drawdown is OPEN-POSITION excursion, not realised loss -- a
position held longer simply sits deeper underwater before exiting.
That grows continuously with holding time, which is why 31 and 32
already carry it.

MaxHoldingBars STAYS AT 24. It is interior to the flat-drawdown
plateau with three bars of clearance; 27 sits on that plateau's
right edge with none, and 29/30 are already one bar from the cliff.
Their net advantage is inside the noise band, so there is nothing
to buy with that clearance.

24 is also the only value in the range with a written rationale:
the v0.5-FINAL design block calls it the momentum burst decay
window at 2hr. That is a design hypothesis rather than a measured
fact, but 27 and 30 have neither.

THE "AVOID THE CROWD" ARGUMENT WAS EVALUATED AND REJECTED. An odd
bar count could in principle be deliberate differentiation rather
than a curve fit, but not for this parameter, on three independent
grounds. It is a RELATIVE clock anchored to this strategy's own
entry, so two desks both holding 24 bars exit at different wall
clock times and never cluster. The entry signal is idiosyncratic
(ZLEMA 25/70 plus a bespoke slope gate, 28 trades a year), so there
is no shared entry to cluster from. And the exit is a MARKET order
(SX_MA_TimeStop, "next bar at market"), which does not exist in the
book until it fires and therefore cannot be hunted.

That question does belong somewhere: Struct, BE and SL exit on
"next bar at v_BE_Stop_Level stop" and "at v_SL_Level Stop", which
ARE resting orders at levels any reader of the same price series
can compute. ATR_Len = 14 is Wilder's default. If crowding is to be
considered anywhere in this strategy, it is B11, not here.

RE-ENTRY WAS NOT RE-TESTED AND DOES NOT NEED TO BE. v_ReEntry_Price
is assigned from v_Last_EntryPrice, so the trigger is anchored to
the PREVIOUS ENTRY price, never to an exit price. B4 through B14
changed exits only, so the anchor cannot have moved. B3's finding
stands: ReEntry_On / _Slope_Gate / _Close_Gate must all be 1, and
ReEntry_Structure_Gate is inert for the third independent time.
Trade count held at 180 across B8/B9/B10/B14, which is what a
decoupled leg looks like.

B11 (ATR/SL, 2,880 cells) and B13 (confirmation loop, ~85 cells)
are DEFERRED until after validation. B14 governs 156 of 180 trades
and B11 governs 4; roughly 28,000 cells have now been evaluated
against 14 adoptions on a sample whose profit leg is 40 trades and
whose top five trades are 67.5% of net, with zero OOS remaining.
Rule #13, Rule #18 and W4 have not been started. Cells spent before
a failed validation are cells wasted.

------------------------------------------------------------------
B7 ADDENDUM (2026-08-13): TRAIL IS TURNED OFF. 209 OF 209.
------------------------------------------------------------------

Trail_On 1 -> 0. Grid 2 x 19 x 11 = 418, Trail_Trigger_Pct swept
0.30-3.00 step 0.15 and Trail_Giveback_Pct 20-70 step 5.

AS REPORTED (see the correction below -- this grid ran on a stale
Tail_DayNoEntry_From, so every figure here is 18,400 too high):

  Trail OFF               182 / 2,165,600 / PF 1.884352 / DD -408,400
  best Trail ON (2.70/20) 182 / 2,134,400 / PF 1.871600 / DD -408,400
  previous default (2.00/40)  180 / 2,034,400 / PF 1.840106

NOT ONE of the 209 enabled cells reaches the disabled figure.
Turning it off is worth +131,200 against the shipped default and
the drawdown does not move: -408,400 either way.

THE TERRAIN POINTS ONE WAY FROM BOTH DIRECTIONS. Raising the
trigger makes Trail rarer and net rises, converging on 2,134,400
at 2.70 and above -- approaching the disabled value without ever
reaching it, which is saturation toward OFF and not a truncated
grid, so no boundary extension is owed. Loosening the giveback
also raises net: at Trigger 1.05, giveback 20 gives 1,668,400 and
giveback 70 gives 2,064,800, a spread of 396,400 in favour of
letting the position breathe.

THIRTEEN CELLS DO BEAT THE DISABLED DRAWDOWN. The best is
(0.45/20) at -355,200 against -408,400, a 13% improvement -- for a
net of 858,000. Paying 1,307,600 of profit for 53,200 of drawdown
is the textbook case feedback_trend_let_profits_run exists to
prevent, so it is recorded and rejected rather than treated as a
trade-off worth weighing.

This is the FOURTH measured failure of tightening exit-side
protection on this desk, after Trail_B at -385K, L5's five SP
variants and L5 Stage1_BE at -19K on L26. The memory rule already
calls the direction permanently closed; B7 is confirmation, not
discovery.

Trail_Trigger_Pct and Trail_Giveback_Pct are LEFT at 2.00 and 40.
They are inert with the switch off, and writing the best enabled
cell into them would plant a value in the file that was measured
to lose money. Same treatment as ReEntry_Structure_Gate: proven
inert, retained unchanged, because a neighbour moving can make it
bind again.

------------------------------------------------------------------
CORRECTION 2026-08-14: THE B7 GRID RAN ON A STALE DAY-TAIL VALUE
------------------------------------------------------------------

The anchor protocol below was written the same day and caught this
on its FIRST use. A plain backtest at the file defaults returns

    180 trades / 2,147,200 / PF 1.8866864883 / DD -408,400

not the 182 / 2,165,600 recorded above. The gap is exactly 2 trades
and 18,400 -- the day-tail rule's own documented cost. Adding those
two trades back to the measured run reproduces the B7 figure in
THREE fields at once:

    gross profit  4,568,800 + 45,600 = 4,614,400
    gross loss    2,421,600 + 27,200 = 2,448,800
    net                               2,165,600   exact
    PF            4,614,400/2,448,800 = 1.8843515  to 6 decimals
    trades        180 + 2             = 182        exact

So the B7 grid was run with Tail_DayNoEntry_From still at its
pre-1335 value. Same footgun as the five runs listed below: MC12
retains the previous run's inputs rather than reloading the file.

B7's CONCLUSION SURVIVES, CONFIRMED BY MEASUREMENT. All 418 cells
shared the same stale value, so the ranking is internally
consistent; only the level was uniformly high. That uniformity was
not assumed -- the top enabled cell was re-run at the corrected
defaults on 2026-08-14:

  Trail OFF                180 / 2,147,200 / PF 1.8866864883
  Trail ON 2.70/20         180 / 2,116,000 / PF 1.8738024447
  predicted 2,134,400 - 18,400 = 2,116,000        exact

The 31,200 margin is preserved to the point. Trail stays off.

AND THE RE-RUN STRENGTHENED THE FINDING. Gross loss is IDENTICAL
across the two cells, -2,421,600 either way; the entire difference
sits in gross profit, 4,568,800 against 4,537,600. Three trades
exited via Trail instead of TimeStop and gave back 31,200 between
them. Trail did not prevent a single loss in 6.4 years -- it has no
defensive value here at all, it only truncates winners. That is
feedback_trend_let_profits_run in its strongest measurable form.

CAMPAIGN BASELINE AFTER B7 (CORRECTED):
  180 trades / 2,147,200 / PF 1.8866864883 / DD -408,400 /
  account return 619.86

THIS BASELINE IS THE ANCHOR EVERY LATER BATCH MUST REPRODUCE. Run a
plain backtest at the file defaults BEFORE each optimization and
confirm all four fields. It is cheap and it is falsifiable: MC12
retains input values from the previous run rather than reloading the
file, and that footgun has voided five runs this week
(Tail_Signal_Lead_Bars=0, BE_Cost_Pts=5, MinSlope_ATRMult=0.35,
Slope_Z_K carrying MinSlope_Pct's value, and B8 below) plus the B7
grid above -- six.

------------------------------------------------------------------
B8 ATTEMPT 2026-08-13 13:24:54 -- VOID, NOT A RESULT
------------------------------------------------------------------

Report_2026-08-13_13-24-54.csv is discarded. Two independent
faults, either one sufficient to void it:

1. WITHDRAWN 2026-08-14 -- THIS TEST WAS ITSELF WRONG. It read:
   "All 256 rows carry 180 trades. At the file defaults the answer
   is 182. 180 is the signature of Trail_On=1." The file defaults
   return 180, not 182 (see the correction above), so 180 is the
   CORRECT signature and proves nothing either way. The trade count
   cannot separate Trail_On=1 from Trail_On=0 here: both return
   180. Nothing is known about that run's Trail setting.

   Kept visible rather than deleted, because a wrong test that is
   silently removed gets re-invented. Fault 2 is independent and
   sufficient on its own; the run stays void, on one ground.

2. THE MODE WAS GENETIC, NOT EXHAUSTIVE. Struct_On held a single
   value, Struct_Trigger_Pct sampled 6 of 19 points, and those 6
   are not a lattice: 0.20/0.30/0.40/0.50 carry 254 of the rows
   while 1.80 and 2.00 carry exactly one each -- a population
   converged on a high-fitness pocket with two survivors from the
   initial random draw. 256 = population x generations. An
   exhaustive sweep cannot produce that shape. The default cell
   (Trigger 1.00) was never sampled, so the run cannot even
   self-check against its own base.

The best cell reported, 1,956,000, is below the baseline on either
reading of it (2,165,600 as recorded, 2,147,200 as corrected), but
a genetic run that never sampled its own default cell cannot be
read as evidence about Struct in any direction. Nothing at all is
known about Struct yet.

B8 SPECIFICATION, UNCHANGED, TO BE RUN EXHAUSTIVE:
  Struct_On          0 -> 1    step 1     ( 2)
  Struct_Trigger_Pct 0.20 -> 2.00 step 0.10 (19)
  Struct_UseClose    0 -> 1    step 1     ( 2)
  Struct_Lookback    10 -> 50  step 5     ( 9)
  Struct_Buffer_Pts  10 -> 50  step 5     ( 9)
                               total  6,156 cells
Acceptance, both required:
  1. row count is exactly 6,156. Any other number means genetic
     mode or a truncated export -- discard and re-run.
  2. the cell (1, 1.00, 1, 20, 20) is present and returns
     180 / 2,147,200 / PF 1.8866864883, the CORRECTED baseline.
Check 2 is the run's self-test: it proves the base and the mode at
the same time. Note that trade count alone cannot detect a stale
Trail_On -- both settings return 180 -- so the net must be checked
too, which is the lesson from withdrawn fault 1 above.

Boundary watch: if the winner lands on Struct_Trigger_Pct 0.20 or
2.00, Struct_Lookback 50, or Struct_Buffer_Pts 50, that is a
truncated grid and not an optimum -- extend outward as B3 did into
B3b. Struct_Buffer_Pts 10 is a hard floor (the 10-point round-trip
slippage) and Struct_Lookback is capped at 99 by MaxBarsBack.

Prior: B7 has just closed the tighten-exit-protection direction for
the fourth time on this desk, and Struct writes to the same
v_BE_Stop_Level ratchet. Struct_On = 0 is a live possibility. Run
the full 6,156 anyway -- Struct triggers off a structural high
rather than a giveback percentage, so the analogy is suggestive,
not conclusive.

------------------------------------------------------------------
THE DEFECT: THE DAY SESSION NEVER HAD A TAIL RULE
------------------------------------------------------------------

v1.18.0's gate was

    v_Tail_Entry_OK = ( Time <= v_Tail_Cutoff or Time > 500 )

Every day bar carries Time > 500, so the second clause admits ALL
of them -- 0850 through 1345. Tail_NoEntry_From therefore governs
ONLY the post-midnight window. The day session's sole protection
was Sess_LastBar_Block_On stopping the 1345 signal, and that is a
SIDE EFFECT of a rule written for a different purpose.

So a 1335 signal filled at 1340, five minutes before the close,
and the position then sat through the 1345-1500 break with no exit
mechanism able to act. Nobody ever decided this. It was never
proposed, measured or written down -- the same failure mode as
Tail_NoEntry_From = 430, whose derivation lived only in the
author's head until it was questioned.

------------------------------------------------------------------
WHAT THE MEASUREMENT SAID -- AND IT SAID THE OPPOSITE
------------------------------------------------------------------

Trades spanning the 1345-1500 break, measured on the 182-trade
population:

    span the break      7 trades   +308,800   avg +44,114   71.4% win
    day session only   82 trades   +398,400   avg  +4,859   28.0% win
    night entries      93 trades +1,345,600   avg +14,469   32.3% win

The break-spanning trades average NINE TIMES the intraday average
and win at more than twice the base rate. Day entries from 1300
onward are 9 trades worth +12,400 in total.

THE DAY TAIL WAS NOT BLEEDING. Blocking it costs money in sample.

------------------------------------------------------------------
THE RULING, AND ITS COST, STATED PLAINLY
------------------------------------------------------------------

User ruling 2026-08-13: no position may be opened from 1335, so
that 1340, 1345 and 1505 can carry no new entry under any
circumstance.

Sample cost, exactly two trades:

    2024-11-29  filled 1335  exit 1655 TimeStop        +45,600
    2026-07-28  filled 1340  exit 1520 QuickStop_Time  -27,200
                                                net    -18,400

One winner and one loser. n = 2, so the SAMPLE CANNOT JUDGE THIS
RULE. It is adopted on principle -- a position opened in the last
ten minutes of a session cannot be managed by any exit mechanism
before the break -- and the -18,400 is recorded as the price of
that principle, not hidden inside a net figure.

------------------------------------------------------------------
THE RULE IS NOW SYMMETRIC AND EXPLICIT
------------------------------------------------------------------

  v_Tail_Entry_OK =
        ( v_In_Day   and Time <= v_Day_Cutoff )
     or ( v_In_Night and ( Time <= v_Tail_Cutoff or Time > 500 ) )

Each session states its own rule. The "Time > 500" clause no
longer leaks day bars past a night-only cutoff, because it is now
inside the night branch where it belongs.

Both cutoffs derive from their anchor the same way, using the
lead already justified in v1.18.0 -- market orders fill at the
next bar's open, stop orders are live for that whole bar, so the
stricter of the two is two bars:

  v_Day_Cutoff  = Tail_DayNoEntry_From - Lead bars   1335 -> 1325
  v_Tail_Cutoff = Tail_NoEntry_From    - Lead bars   0415 -> 0405

------------------------------------------------------------------
MEASURED 2026-08-13, THREE RUNS. ALL GATES PASS.
------------------------------------------------------------------

  1350  182 trades / 2,052,800 / PF 1.838288 / DD -408,400
        DEGENERATE ANCHOR, reproduced field for field.
  1345  182 trades / 2,052,800 / PF 1.838288 / DD -408,400
        IDENTICAL to 1350 across all 86 fields, and that is the
        derivation proving itself: 1345 puts the cutoff at 1335 so
        the last fill bar is 1340, and the sample holds no fill at
        1345 for it to block. A DIFFERENT result here would have
        meant the arithmetic was wrong.
  1335  180 trades / 2,034,400 / PF 1.840106 / DD -408,400  SHIPPED

Trade level, 1350 -> 1335: 2 gone, 0 new, 0 P&L drift. Slippage
falls exactly 8,000 = 2 trades x 2 lots x 1,000 x 2 sides, which
confirms nothing else moved.

THE PRICE IS SMALLER THAN THE HEADLINE. Net falls 18,400 (-0.9%),
but profit factor RISES 1.838288 -> 1.840106 and average win over
average loss rises 3.8984 -> 3.9385, because the blocked pair is
one winner and one loser and the loser was the larger share of its
own side. Max drawdown is UNCHANGED at -408,400 and the worst
losing streak is unchanged at 9 / -239,200 -- neither blocked trade
sat on the drawdown path, so the rule costs no resilience at all.

Sharpe 0.1615 -> 0.1583 and Sortino 0.8962 -> 0.8920 are a
two-fewer-trades denominator effect, not a quality change; PF and
the win/loss ratio both moved the other way.

DEGENERATE ANCHOR: Tail_DayNoEntry_From = 1350 restores v1.21.0
exactly. At 1350 the cutoff is 1340, so a 1340 signal still fills
at 1345 and the 1345 signal is blocked by Sess_LastBar_Block_On as
before. It MUST reproduce 182 trades / 2,052,800 / PF 1.838288.

------------------------------------------------------------------
ALSO IN THIS VERSION: B4 AND B6 WINNERS INTO THE DEFAULTS
------------------------------------------------------------------

Per feedback_param_must_sync. Until now these were adopted in the
campaign log but not in the file, which is exactly how a later
batch gets run against a stale freeze.

  QS_MaxLoss_Pct   0.25 -> 0.70   B4. The loss leg is disabled by
                                  a threshold it can never reach;
                                  QuickStop keeps only its TIME
                                  leg and the loss side goes back
                                  to SL_Pct. 0.70/0.75/0.80 are
                                  identical, so this is saturation
                                  and not a truncated grid.
  BE_Trigger_Pct   0.80 -> 0.60   B6
  BE_Cost_Pts      10   -> 20     B6. NOTE: at 20 this is no
                                  longer a breakeven, it locks 10
                                  points net of the 10-point round
                                  trip. The name now understates
                                  what it does.
  MaxHoldingBars   24 unchanged   B5 measured 30 as +134,400, but
                                  the decomposition showed the
                                  gain comes only from 13 trades
                                  the TIME stop still caught
                                  (+495,200) while every trade
                                  handed to another mechanism lost
                                  (-360,800, of which -215,200 to
                                  GoldenCross across 19 trades).
                                  User ruling: hold 24 until the
                                  ratchet (B7/B8) can catch the
                                  giveback, then re-sweep.

v1.21.0 (2026-08-12) TWO CHANGES, NEITHER OF THEM LOGIC:

1. SEVENTEEN TrueFalse INPUTS BECAME NUMERIC 0/1.
   MC12's optimizer enumerates numeric inputs only. A TrueFalse
   input is not merely awkward to sweep, it is absent from the
   optimization list entirely -- which is why the B1 and B2
   reports each carried three parameter columns instead of the
   six and four that were specified. Those switches were not
   held at their defaults by choice; they were excluded.
   See SECTION 2.5 for the decode and the convention.

2. B1 AND B2 WINNERS WRITTEN INTO THE DEFAULTS.
   Rule feedback_param_must_sync: an optimized value belongs in
   the input default so code, deployment and docs stay one
   thing. Mid-campaign this also means the file's defaults are
   always the current frozen state, so a later batch cannot be
   started against a stale freeze by accident.

     Slope_Form         1        -> 2          the rate form
     MinSlope_Rate      0.058027 -> 0.050      B1 #1 of 833
     Gap_Down_Min_Pct   0.00     -> 0.10       B2
     Gap_Rise_Min_Pct   0.00     -> 0.20       B2
     Gap_Scope_Bars     1        -> 3          B2
     ZLEMA_Fast         25       -> 25         B1 confirmed
     ZLEMA_Slow         70       -> 70         B1 confirmed

Slope_Form defaulting to 2 is the substantive line. Through
v1.20.0 the file still shipped the v1.18.0 anchor; from here
the rate form IS the strategy.

ANCHOR, as first written: 186 trades / 1,522,000 / PF 1.54 /
max intraday DD -548,800 / RoA 300.55. CONFIRMED in MC12 on
2026-08-12 -- the boolean conversion is proven bit-correct.

DEFAULTS UPDATED 2026-08-12 AFTER B2b / B3 / B3b:

B2b re-ran the gap batch with the three on/off switches finally
visible to the optimizer. It changed nothing: the adopted cell
was already right. What it added was the split -- the -27,600
trade it blocks is a DAY trade, and the +6,000 winner that
Gap_Rise_Min_Pct = 0.0 over-blocks is a NIGHT trade. See the
Group J comment for the full re-measured record.

B3 swept the tail-time and re-entry group. Two values moved:

  Tail_NoEntry_From    430 -> 415
  Tail_ForceExit_Time  440 -> 430

B3b existed because B3's winner sat on the grid's lower edge,
and a boundary optimum is a truncation rather than a plateau.
Extending the sweep down to 350 confirmed 430 as a real peak
with support on both sides. The full profile is recorded at
Tail_ForceExit_Time in Group I.

CURRENT ANCHOR (all defaults):
  184 trades / 1,678,000 / PF 1.61 / max intraday DD -548,400 /
  RoA 331.62

Campaign to date: 748,000 -> 1,678,000, +124.3%, across B1, B2,
B2b, B3 and B3b. The entry side is finished. Every EXIT
parameter still carries its v1.18.0-era value.

THE INERT REGISTER (measured, not assumed):

Each of these was swept and returned bit-identical results at
both settings, so it is dead weight at the current defaults.
All are HELD rather than removed -- each has a derivation that
binds again if a neighbouring parameter moves -- but they are
the first candidates if this file is ever simplified.

  Slope_Require_Adjacent   B3    the elapsed-time divisor in
                                 Slope_Form = 2 already drives
                                 session-first-bar entries to 0
  Tail_Signal_Lead_Bars    B3    all five values 0..4 identical
  ReEntry_Structure_Gate   B3    third independent confirmation;
                                 the state machine already
                                 implies Fast < Slow
  Gap_Night_On             B2b   identical across the adopted
                                 Gap_Rise_Min_Pct band

Confirmed LIVE and load-bearing, by contrast:
  Sess_LastBar_Block_On    +29,200. Its first measured action --
                           v1.17.0 recorded zero in-sample
                           triggers, which proved only that it
                           did not misfire.
  ReEntry_On / _Slope_Gate / _Close_Gate
                           all three must be 1; the re-entry leg
                           survives the population change.

WHAT THIS VERSION DOES NOT DO. Every exit parameter still
carries its v1.18.0-era value, tuned against a population that
overlaps the current one by 28 trades out of 118. Batches B4
through B12 exist to fix exactly that. Do not read the anchor
figure as a settled result.

SIDE EFFECT, DELIBERATE. v1.18.0's 118 trades / 3,098,400 is no
longer reachable by a single input change, because the gap
defaults moved with it. It is recoverable from git at commit
185cf66 (v1.20.0). The old anchor has done its job.


v1.20.0 (2026-08-12) THE SLOPE AS A RATE OF THE MARKET'S OWN MOVE:

Slope_Form = 2 is the author's formula, stated 2026-08-12:

    ( Close[1] - Close ) / Close / elapsed minutes

the market bar's decline, normalised by the index level, divided
by the time it took.

WHY THE NUMERATOR CHANGED. Every version to date differenced the
ZLEMA fast line. A 25-period EMA moves about 2/(25+1) of the gap
between its input and its previous value, so Fast[1] - Fast is a
damped derivative of a smoothed series, not the market's decline.
Close[1] - Close is the decline.

WHY THE TIME TERM IS BACK. v1.19.2 dropped it as a constant. That
was true of BarInterval and false of the measured elapsed time.
Ranked by this formula, ZERO of the top 127 crosses are session
first bars; ranked without the time term, 63 of 127 are. A gap
spanning 230 minutes divided by 230 instead of 5 collapses by 46x
and leaves the ranking on its own, so the formula handles the
boundary by construction.

Not settled by that: the market gapped, it did not fall gradually
across 230 minutes. Treating it as a low rate gets the right
answer for a reason that may not be the true one.

SHIPS OFF. Slope_Form defaults to 1, so the anchor must reproduce
v1.18.0 exactly: 118 trades / 3,098,400 / PF 2.0511602660.

MinSlope_Rate = 0.058027 is iso-count calibrated, admitting the
same 127 crosses MinSlope = 28 admits.

v1.19.2 (2026-08-11) THE FORMULA, RESTATED THE WAY IT WAS MEANT:

Same 2x2 as v1.19.1. Three corrections to how the formula is
written, all from the author's own statement of it, none of which
changes the default path -- Slope_Form = 1 and
Slope_Require_Adjacent = False must still reproduce v1.18.0
exactly: 118 trades / 3,098,400 / PF 2.0511602660.

------------------------------------------------------------------
1. dx IS THE TIME OF THE CHANGE, AND IT IS A GATE NOT A DIVISOR
------------------------------------------------------------------
The formula is ( points moved / index level ) / TIME, and the time
term is the time OF THE CHANGE: A time minus B time. v1.19.1 used
BarInterval, which is the chart's interval SETTING -- a constant.

Dividing every reading by a constant is exactly equivalent to
multiplying the threshold by it. The /time term added no
information at all:

    v_Slope_Pct > MinSlope_PctPerMin
    <=>  ( dy / Fast * 100 ) / 5  >  0.023316
    <=>  ( dy / Fast * 100 )      >  0.11658

v1.19.2 measures elapsed time for real -- TimeToMinutes(Time)
minus TimeToMinutes(Time[1]), plus a day when it wraps midnight --
and uses it as a VALIDITY TEST rather than a divisor:

    inside a session                 5 minutes    measure it
    0500 night close -> 0850         230 minutes  do not
    1345 day close   -> 1505         80 minutes   do not
    Friday 0500      -> Monday 0850  longer       do not

Dividing by 230 would assert the market fell gradually across 230
minutes. It did not -- there were no trades in that interval at
all. The quantity is UNDEFINED there, not compressed.

Once the gate forces dx = BarInterval on every measured bar, the
division is again by a constant, so it is dropped. THE TIME IS IN
THE GATE, NOT IN THE VALUE. Units are percent per bar, and every
measured bar is five minutes.

This replaces v1.19.1's "is this bar 1 of the session" test and is
strictly more general: it also catches the Monday open, a
post-holiday open, and any mid-session data gap or halt.

------------------------------------------------------------------
2. THE PERCENT BASE IS THE STARTING VALUE
------------------------------------------------------------------
v1.19.1 divided by v_ZLEMA_Fast, the ENDING value, which inflates
the reading on a fall because the denominator is the smaller
number. Percent change is defined against where the move started,
so v1.19.2 divides by v_ZLEMA_Fast[1]. About 0.1% relative, so it
changes no decision -- corrected because it is free to be correct.

Close is still not used. On a session first bar Close can gap away
from the fast line, which would add a second source of boundary
noise to the exact quantity being controlled here.

------------------------------------------------------------------
3. IT IS NOT "INSTANTANEOUS", AND THE COMMENT NOW SAYS SO
------------------------------------------------------------------
Fast[1] - Fast is the one-bar change of a 25-period ZLEMA. A
25-period EMA moves roughly 2/(25+1) of the distance between its
input and its previous value, so this is heavily damped relative
to raw price. It is the steepness of the smoothed trend, which is
what the strategy trades, but it is not a tick-level rate.

------------------------------------------------------------------
WHAT THIS VERSION DOES NOT CLAIM
------------------------------------------------------------------
That percent is better than points. The evidence points the other
way and the mechanism is now known:

  slippage    10 points, FIXED, does not scale with the index
  MinSlope    28 points -> cost coverage 2.80x in EVERY year
  0.11658%    -> 12.5 points in 2019 = 1.25x cost coverage
              -> 44.5 points in 2026 = 4.45x cost coverage

A points gate is in the SAME UNIT as the constraint it actually
enforces. The percentage form is scale-neutral against the INDEX
and therefore scale-WRONG against the COST, which is what the gate
is really defending. That is a mechanism for the bench's monotone
result -- more early-year trades, less money, four formulations,
no exception -- that neither of the two explanations on record
supplies.

And the market itself is the harder wall. Median 5-minute bar
range by year, against the same 10-point round trip:

  2019   4.0 points   cost is 250% of a typical bar's range
  2026  49.0 points   cost is  20% of it

For 2019 to enjoy 2026's 4.90x coverage the round trip would have
to be 0.82 points. One tick is 1 point. NO COST ASSUMPTION MAKES
2019 TRADEABLE ON THIS TIMEFRAME.

------------------------------------------------------------------
THE 2x2, AND WHICH CELL NOW MATTERS
------------------------------------------------------------------
  cell  Slope_Form  Require_Adjacent   what it answers
  1     1 points    False              ANCHOR = v1.18.0 exactly
  2     1 points    True               dx fixed in the right unit
  3     2 percent   False              DIAGNOSTIC ONLY, never ship
  4     2 percent   True               control

Cell 2 is the candidate, not cell 4. The two switches stay
independent precisely so that "points versus percent" is not
confounded with "contaminated versus clean".

CELL 2 IS LARGELY PREDICTABLE AND THAT IS THE POINT. v1.16.0's run
0b already blocked every session first bar and lost about 103,200
net while gaining about 0.036 Sharpe. The 8 first-bar trades are
worth -54,800 by themselves; the loss comes from 3 downstream
re-entries worth +158,000 that vanish with their parents. If cell
2 disagrees with that, the elapsed-time test is selecting a
different set from the ordinal test and the difference must be
explained before anything is adopted.

v1.19.1 (2026-08-11) THE SLOPE IS WRITTEN AS dy/dx, AND dx IS FIXED:

Numbered .1 because v1.19.0 was a BENCH, not a version, and is
now DEPRECATED. This is the one surviving idea from it, rebuilt on
the adopted v1.18.0 rather than on the bench. v1.20.0 stays
reserved for the gap scenarios.

------------------------------------------------------------------
THE USER'S FORMULA
------------------------------------------------------------------

    slope = ( instantaneous points / index points ) / time

which maps to:

    dy = ( ZLEMA_Fast[1] - ZLEMA_Fast ) / ZLEMA_Fast * 100   percent
    dx = BarInterval                                          minutes
    slope = dy / dx                                    percent/minute

Denominator is the fast line's own value, not Close, so numerator
and denominator come from the same series.

------------------------------------------------------------------
TWO SEPARATE DEFECTS, TWO SEPARATE SWITCHES
------------------------------------------------------------------

dy IS IN POINTS  (Slope_Form)
  28 points is 0.280% of the 2019 index and 0.062% of today's.
  The same ruler is 4.5x tighter in the early years. This is a
  design choice, and it has been measured before -- but only ever
  on data contaminated by the dx defect below, which is why it is
  being re-measured rather than assumed settled.

dx COUNTS BARS, NOT TIME  (Slope_Require_Adjacent)
  Within a session one bar is 5 minutes, always. At a session
  boundary one bar is 225 minutes (night close 0500 to day open
  0845) or 75 minutes (day close 1345 to night open 1500), and the
  code still counts it as 1.

  Measured consequence on 7,779 death crosses:

    session first bars      144 of 7,779    =  1.85% of the pool
    their median slope      9.35            vs 2.34 elsewhere
    their pass rate         13.89%          vs 1.40% elsewhere
    share of everything
      that passes           20 of 127       = 15.7%, a 8.5x excess

  THE FIX IS EXCLUSION, NOT RESCALING. Dividing by 45 would assert
  the market fell gradually across 225 minutes. It did not -- there
  were no trades at all in that interval. An intraday slope is
  UNDEFINED on a bar whose predecessor sits in another session.

------------------------------------------------------------------
WHY dx IS FIXED FIRST
------------------------------------------------------------------

The dx contamination is not constant across dy formulations -- it
grows as dy becomes more scale-neutral:

    points     20 of 127 passes are session first bars   15.7%
    percent    28 of 127                                 22.0%
    ATR        57 of 127                                 44.9%
    z-score    53 of 127                                 41.7%

A confound that varies with the treatment is the worst kind. On
contaminated data a dy comparison measures which formula swallows
the most garbage, not which formula is better. That is exactly what
the v1.19.0 bench did, which is why it is deprecated.

------------------------------------------------------------------
WHAT IS NOT IN THIS VERSION, AND WHY
------------------------------------------------------------------

ATR. The formula normalises by INDEX LEVEL, not by volatility.
v1.19.0's Mode 3 used ATR as a denominator and that conflated two
different questions. ATR belongs to the cost analysis -- the fixed
10-point round trip is 2.30 ATR in 2019 and 0.19 ATR in 2026 -- and
that is a market fact, not a slope parameter. It has no place here.

THE SMOOTHING. dy is the difference of a 25-period ZLEMA, not of
price: expanding the recursion,

    dy = 0.0769 * ( ZLEMA_Fast[1] + Close[12] - 2 * Close )

so the current bar's close carries only 15.4% weight and the close
twelve bars back enters with the opposite sign. That is ZLEMA
working as designed, not a defect. Recorded here because the file
never said it plainly and it is easy to read v_Slope as "this bar's
price change", which it is not.

------------------------------------------------------------------
THE 2x2
------------------------------------------------------------------

  Slope_Form  FirstBar_Block   meaning
     1           False         = v1.18.0 exactly. DEGENERATE ANCHOR.
                                 MUST give 118 / 3,098,400 /
                                 PF 2.0511602660 bit for bit.
     2           False         dy only
     1           True          dx only
     2           True          both

Two runs fill the two unknown cells. The anchor is run first and
nothing else is read until it passes.

MinSlope_Pct default 0.023316 is iso-count calibrated from
the 7,779-cross export: it admits the same 127 crosses that
MinSlope = 28 admits, so form 2 is compared to form 1 at equal
selectivity rather than at equal looseness.

v1.18.0 (2026-08-10) THE TAIL ENTRY RULE IS NOW DERIVED, NOT GUESSED:

------------------------------------------------------------------
WHAT WAS WRONG -- AND IT WAS NOT THE COMPARISON OPERATOR
------------------------------------------------------------------

v1.16.0 flagged Tail_LastEntry_Time as NOT COMPLIANT and v1.17.0
added Tail_FillSemantic_On to switch <= for <. Both were treating
the symptom: the input was named for the FILL but gated the
SIGNAL, so a 0430 cutoff permitted an 0435 fill. Arguing < versus
<= cannot close a one-bar offset.

CORRECTION 2026-08-10, on the author's own account of the design.
An earlier draft of this block asserted 430 "has no derivation"
and was "only ten minutes before 440". BOTH CLAIMS WERE WRONG.
430 and 440 are SIBLINGS, each measured back from the 0500 night
close, and neither is derived from the other:

    no new position from   0500 - 30 min = 0430
    force flat from        0500 - 20 min = 0440

The v1.15.0 audit graded 430 D for "v1.3 design judgement, never
swept". "Never swept" stands. "Design judgement" stands and is in
fact exactly right -- it is a risk decision about how close to the
close a position may still be opened. What did not stand was the
later inference that a design judgement with no written rationale
must be arbitrary.

The rationale had simply never been written into the repository,
so two separate readers saw a bare 430 and each concluded it was a
guess. AN INTENT THAT IS NOT WRITTEN DOWN DOES NOT EXIST. That is
the transferable lesson here, more than the time value itself.

This correction STRENGTHENS the change rather than undermining it.
The requirement was always "no position may be opened from 0430",
and the old code opened one at 0435. It violated a stated intent,
not an arbitrary constant. Nothing in the Tail_Signal_Lead_Bars
derivation below depends on where 430 came from -- that argument
is about signal-versus-fill and order type alone.

------------------------------------------------------------------
THE RULE, RESTATED THE WAY THE REQUIREMENT IS ACTUALLY MEANT
------------------------------------------------------------------

The requirement is one sentence: NO POSITION MAY BE OPENED FROM
Tail_NoEntry_From ONWARDS. That is a trading decision and it names
a wall-clock time.

Everything else is mechanical. Bars are stamped at their CLOSE, so
a bar stamped T covers wall-clock (T - BarInterval, T]. A signal is
evaluated at T and the order is a NEXT BAR order, so:

  death cross   next bar at market
                fills at the NEXT BAR'S OPEN, which is the first
                tick after T -- wall-clock fill is essentially T.
                Safe when  T <= NoEntryFrom - 1 bar.

  re-entry      next bar at v_ReEntry_Price stop
                the order is LIVE FOR THE WHOLE of the next bar,
                so it can fill as late as wall-clock T + 1 bar.
                Safe when  T <= NoEntryFrom - 2 bars.

Take the stricter of the two and one rule covers both paths:

    last permitted SIGNAL bar = Tail_NoEntry_From - 2 bars

On a 5-minute chart that is ten minutes. The lead is expressed in
BARS, not minutes, because ten minutes is only two bars at this
interval -- on a 10-minute chart the same ten minutes would be one
bar and the stop-order path would silently break. That is the same
class of defect as the hard-coded 430 it replaces.

The market-order path gets one bar more room than it strictly
needs. That is deliberate: one rule that cannot be wrong beats two
rules that each cover half. See the order-type evidence below.

------------------------------------------------------------------
ORDER-TYPE EVIDENCE (measured, not assumed)
------------------------------------------------------------------

Fill price minus the signal bar's close, over the adopted 119:

  death cross (market)   n=108   median   3 pts, 14% exactly 0
  re-entry    (stop)     n= 11   median  40 pts, max 165, and all
                                 eleven NEGATIVE

A market order landing within a tick or two of the signal bar's
close is a fill at the next bar's open. A stop order landing 40
points below it, every time, is a fill from inside the next bar
after price fell to the level. The two order types genuinely do
fill at different wall-clock times, which is why one shared
comparison operator could never be right for both.

------------------------------------------------------------------
WHAT CHANGES
------------------------------------------------------------------

Tail_LastEntry_Time  -> Tail_NoEntry_From   (renamed, same 430)
                        It now names the wall-clock time from
                        which no FILL may occur, which is what
                        v1.3 meant all along.
Tail_FillSemantic_On -> DELETED. Its job is done by the
                        derivation; there is no longer an operator
                        to choose.
Tail_Signal_Lead_Bars-> ADDED (2). Not a tuning knob -- see its
                        comment. It exists so the derivation is
                        visible and so Rule #1 is satisfied.

------------------------------------------------------------------
EXPECTED
------------------------------------------------------------------

  Tail_Signal_Lead_Bars = 0   MUST reproduce v1.17.0 defaults bit
                              for bit: 119 / 3,141,200 / PF
                              2.065680553670783. This is the
                              degenerate anchor -- at zero lead the
                              cutoff is 0430 and the gate is the
                              old <= gate exactly.
  Tail_Signal_Lead_Bars = 1   118 / 3,098,400 (cutoff 0425)
  Tail_Signal_Lead_Bars = 2   118 / 3,098,400 (cutoff 0420) SHIPPED

1 and 2 agree because the sample holds no post-midnight signal
between 0340 and 0430, so both cut the same single trade:
2026-03-07, signal 0430, fill 0435, +42,800, a death cross that
TailFlat closed at 0445.

COST, MEASURED, NOT ESTIMATED. That trade sat inside the drawdown
that troughs on 2026-03-27, so removing it deepens the trough by
exactly its own size:

  net           3,141,200 -> 3,098,400    -42,800  (-1.36%)
  gross loss   -2,947,600 -> -2,947,600   unchanged (only a
                                          winner was removed)
  max DD         -561,200 -> -604,000     -42,800
  max DD %        -20.987 -> -22.588      headroom to the 25%
                                          gate falls 4.01 -> 2.41pp
  Sharpe         0.165625 -> 0.162307     -2.0%
  Sortino        1.238782 -> 1.040448     -16.0%
  max losing streak    12 -> 16
  slippage        476,000 -> 472,000      -4,000, exactly one
                                          round trip of 2 lots,
                                          confirming a single
                                          trade moved and nothing
                                          else drifted

The drawdown result is itself a one-trade artifact -- that winner
happened to sit in the trough. Both directions of this argument
rest on n=1, which is why the decision was taken on the rule and
not on the number.

v1.17.0 (2026-08-08) SESSION BOUNDARY -- CLOSING THE FILL-SIDE HALF
                   OF THE GAP PROBLEM:

NOTE ON VERSION REUSE: an earlier v1.17.0 carried a MinSlope
percentage option that shipped OFF and was never validated. That
direction is unsettled and the file had no working content, so the
number was reused. The old file is preserved at
S16_S_MACrossShort_v1.17.0.pla.bak_20260808 and in git history.

------------------------------------------------------------------
A. SESSION LAST-BAR ENTRY BLOCK  (Sess_LastBar_Block_On, ships ON)
------------------------------------------------------------------

v1.16.0 established the repo-wide rule that an order placed on bar
N cannot be withdrawn on bar N+1, so any rule meant to prevent a
fill must be evaluated one bar EARLIER than the bar it protects.

The gap filter obeys that rule for SIGNALS: Gap_Scope_Bars = 1
blocks a signal on the session's first bar. It does NOT cover the
other direction. The day session's last bar is stamped 1345, and
the entry time gate reads

    ( Time <= Tail_LastEntry_Time or Time > 500 )

which at 1345 is TRUE via the second clause. So a signal is allowed
on the last day bar, and the resulting order fills on the FIRST
NIGHT BAR -- straight into the session opening gap. v_Gap_Block is
set True on that bar, but the order was placed a bar earlier and
cannot be withdrawn. The exact defect the rule describes.

Both entry paths carry it, death cross and re-entry alike.

The two mechanisms are a symmetric pair and only one half existed:
  Gap_Scope_Bars = 1     protects the first bar's SIGNAL   (v1.16.0)
  Sess_LastBar_Block_On  protects the first bar's FILL     (here)

MEASURED IN SAMPLE: zero occurrences. No signal timestamp is 1345
and no fill timestamp is 0850 or 1505 across all 119 trades. This
ships as a guard against something that has not happened yet, so
the acceptance test is that it changes NOTHING -- bit-identical to
v1.16.0 at 119 trades / 3,141,200 / PF 2.0657. A zero-change result
is the proof it is wired correctly and simply has not been needed.

HONEST LIMITATION. v1.16.0 detects the session's FIRST bar by
transition (v_In_Day and not v_In_Day[1]) and its comment states
why: a hard-coded stamp fails silently when the open is delayed,
and a protective filter that fails open is worse than none. The
LAST bar cannot be detected that way -- that would require seeing
the next bar. This guard therefore compares against Sess_Day_End /
Sess_Night_End and WILL FAIL OPEN on an irregular early close whose
final bar carries a different stamp. Settlement days and registered
holidays are already blocked upstream, so the residual exposure is
an unscheduled early close. Documented rather than papered over.

------------------------------------------------------------------
B. Gap_Down_Min_Pct  0.30 -> 0     (collapses the gap test to one)
------------------------------------------------------------------

The v1.16.0 block condition is a conjunction:

    session gap <= -Gap_Down_Min_Pct   AND   first bar closed up

The handoff describes the mechanism in one line -- "if the session's
first bar did not close below its open, do not enter" -- but the
code also requires the gap to exceed 0.30%. All 17 observed
first-bar entries had a median gap of -1.108%, so the threshold was
inert and was reported as such. Inert IN SAMPLE is not the same as
harmless: a -0.10% gap with an up-closing first bar slips through
today.

v1.16.0's own sweep already measured this. Run #4 set X = 0 and
came back BIT-IDENTICAL to the adopted 0.30 across all 119 trades
(run #3 at -999 likewise). So the change costs nothing in sample
and closes the small-gap hole going forward.

It also makes the code match its own description: with the
threshold at 0 the condition really is the single sentence the
documentation claims.

------------------------------------------------------------------
C. Tail_LastEntry_Time FILL SEMANTICS  (Tail_FillSemantic_On, OFF)
------------------------------------------------------------------

v1.16.0 marks this input NOT COMPLIANT in its own compliance list:
it is named as an entry time but gates the SIGNAL bar, so 0430
permits an 0435 fill. Observed once, 2026-03-07.

The fix is one comparison -- Time < Tail_LastEntry_Time instead of
<= -- so the last permitted signal is one bar earlier and the fill
lands ON the named time rather than after it.

THIS ONE COSTS MONEY. That 2026-03-07 trade entered 0435, was
force-flatted by TailFlat at 0445 two bars later, and made +42,800.
Correcting the semantics removes a winner.

Shipped OFF so the correctness fix and the trading decision stay
separate. Turning it on is a ruling, not a default: keeping it off
means retaining a behaviour the file itself labels non-compliant in
exchange for 42,800 of in-sample profit.

v1.16.0 (2026-08-08) SESSION OPENING GAP FILTER -- FIRST ENTRY-SIDE
                   CHANGE SINCE v1.6.2:

Exit side closed at v1.15.0 with all nine parameters measured.
This is the first entry-side work in nine versions. Everything
from v1.7 to v1.15 touched exits only, so the entry conditions
were last tuned against an exit architecture that no longer
exists.

STATUS: ADOPTED 2026-08-08 after nine measured runs.

  v1.15.0   129 trades / 2,761,600 / PF 1.8300 / Sharpe 0.1429
  v1.16.0   119 trades / 3,141,200 / PF 2.0657 / Sharpe 0.1656

  Net +13.7%, PF +12.9%, drawdown -23.07% -> -20.99%,
  win rate 27.91% -> 30.25%, and Sharpe clears the 0.15 floor
  in STRATEGY_SUCCESS_CRITERIA.md for the first time in seven
  versions. No metric regressed.

------------------------------------------------------------------
THE NINE RUNS
------------------------------------------------------------------
0   defaults, filter off      129T / 2,761,600 / PF 1.8300072133
                              bit-identical to v1.15.0 across
                              129 trades x 9 fields. The 132 new
                              lines touch nothing.

0b  structural test           DownMin=-999, RiseMin=-999 blocks
                              every session first bar. Entries at
                              0855 and 1510 both went 17->0 and
                              1->0, which is what proves MC stamps
                              bars at their CLOSE and that the
                              session detection is correct.
                              108T / 3,038,000 / Sharpe 0.2014

1   Y = +0.30                 123T / 2,956,800   blocks 6
2   Y =  0.00  <-- ADOPTED    119T / 3,141,200   blocks 10
3   X = -999                  bit-identical to run 2
4   X =  0                    bit-identical to run 2
5   Scope = 2                 118T / 3,144,400   +3,200 only
6   Night off                 bit-identical to run 2
7   MinSlope = 0              9,272T / -33,461,600
8   MinSlope = -99999        12,369T / -44,334,000

------------------------------------------------------------------
THE MODULE COLLAPSES TO ONE CONDITION
------------------------------------------------------------------
Runs 3 and 4 make Gap_Down_Min_Pct provably inert, and the reason
is structural rather than a sample accident:

  an UP gap raises Close, so v_ZLEMA_Fast rises, so
  v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast goes NEGATIVE and
  MinSlope rejects it -- and a death cross needs the fast line
  to cross BELOW, which an up gap cannot produce anyway.

An up gap therefore cannot generate a first-bar short entry at
all, which makes "require a down gap" redundant with conditions
the strategy already has.

Run 6 makes Gap_Night_On inert too: the sole night first-bar
entry (2026-03-17 15:10) closed DOWN, so Y=0.00 never blocked it.

What actually runs is one sentence:

  IF THE SESSION'S FIRST BAR DID NOT CLOSE BELOW ITS OWN OPEN,
  DO NOT ENTER.

Zero tuned thresholds. 0.00 is the natural boundary, not a swept
optimum, so there is no selection bias to discount.

------------------------------------------------------------------
WHY MinSlope STAYS (runs 7 and 8)
------------------------------------------------------------------
Removing the gate entirely costs 47,475,200 and takes drawdown to
-47,115,600, roughly 23x the account. But the interesting part is
what it reveals about the mechanism. Slippage is 4,000 per trade
(10 points x 200 x 2 lots), so backing it out:

  adopted     119 trades   gross 3,617,200
  MinSlope=0  9,272 trades gross 3,626,400

Nine thousand more trades produce 9,200 more gross profit -- one
NT dollar per trade. MinSlope adds no alpha whatsoever. It is a
COST-FLOOR SELECTOR: it discards the 99% of crosses whose gross
edge (about 2 points) cannot clear a 10-point cost.

This is why a candlestick-shape filter cannot replace it. Shape
ratios are dimensionless and cannot distinguish a long bearish
bar that fell 5 points from one that fell 500. Only a magnitude
measure can face a fixed cost floor. The correct fix for the
28-point scale problem is percentage normalisation, not
substitution.

------------------------------------------------------------------
SAMPLE VALIDITY WARNING SURFACED BY RUN 7
------------------------------------------------------------------
Candidate death crosses run about 1,200 per year with no trend.
Trades that clear MinSlope = 28 points do not:

  2019  0     2020  1     2021  0     2022  3
  2023  0     2024 11     2025 11     2026 93

Five years produced four trades. The 6.5-year backtest is really
2.5 years of data. 28 points was 0.28% of the 2019 index and is
0.062% today, so the gate was 4.5x tighter in the early years.

This is a SAMPLE problem, not a performance problem, and it makes
Rule #13's "sample >= 100" and "PF > 1.0 in three regimes" not
genuinely satisfiable on the current parameterisation. It must be
resolved before any promote.

------------------------------------------------------------------
THE DEFECT
------------------------------------------------------------------
v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast

On the first bar of a session [1] points at the last bar of the
PREVIOUS session. A 3h45m overnight gap is therefore measured as
one bar of momentum, and MinSlope = 28 cannot filter it. The gate
is structurally inert on exactly that bar.

------------------------------------------------------------------
THE EVIDENCE
------------------------------------------------------------------
MC stamps bars at their close, so a fill at 0855 comes from a
signal on the first day bar (0850). v1.15.0 has 17 such trades
and 1 night equivalent.

  all 17 followed a DOWN gap        base rate 44.7%,  p ~ 4.7e-7
  median gap on those days          -1.108%  (all days +0.022%)
  combined                          -393,200,  win rate 11.8%
  14 of 17 exited on QuickStop
  spread over 2020/2022/2024/2025/2026 -- NOT a recent-bias find

Splitting those 17 by whether the opening bar closed above or
below its own open:

  closed at/above its open   10 trades   -379,600   0 wins
  closed below its open       7 trades    -13,600   2 wins,
                                                    incl. +149,200

First-bar direction also separates the whole session's path with
no overlap on this sample: of the 10 that closed up, none went on
to a sustained decline; of the 7 that closed down, none went on to
a sustained advance.

------------------------------------------------------------------
WHY A DIRECTION TEST AND NOT A TIME BLOCK
------------------------------------------------------------------
Blocking the opening bar outright removes all 17 (+393,200 on a
first-order estimate) but also removes the class that produced
the +149,200 winner. Blocking only the bars that closed up
recovers +379,600 -- 97% of the benefit, 59% of the trades, and
the winning class survives. Per portfolio-role-design, keeping
the fat tail wins.

------------------------------------------------------------------
WHAT THIS VERSION DOES NOT FIX
------------------------------------------------------------------
2026-07-17 fell 3.45% on the session, its opening bar closed
DOWN, so this filter passes it -- and it still lost 85,200. The
entry moved 331 points against the position before reversing.
Direction right, timing wrong. That is a QuickStop tolerance
question, not a gap question, and it is not addressed here.

------------------------------------------------------------------
ALSO ADDED
------------------------------------------------------------------
- 18-type K-bar taxonomy of the session opening bar, computed and
  held but read by NOTHING. Awaiting 5-minute bar data for
  non-circular validation (a bar's own OHLC statistics cannot
  validate a classification derived from that same OHLC).
- Previous session's final bar OPEN is now recorded alongside its
  close, so a down gap after a declining bar can be told apart
  from one after an advancing bar.
- The signal/fill offset rule and the no-colour-names rule, both
  stated in Section 4.5.

v1.17.0 will fix Tail_LastEntry_Time, which names a fill time but
gates a signal bar. Kept out of this version so the gap filter's
attribution stays clean.
[v1.17.0 note: done, but behind Tail_FillSemantic_On shipped OFF --
 the fix costs a measured -42,800, so it is available rather than
 applied. The default still carries the defect.]

v1.15.0 (2026-08-06) PARAMETER PROVENANCE + ARCHITECTURE COLLAPSE:

Two exit parameters had no defensible provenance. Both were settled
by measurement, and the second turned out to be dead, which let the
percentage leg collapse from five inputs to three.

RESULT: Net 2,670,800 -> 2,761,600 / PF 1.8027 -> 1.8300
        129 trades, Gross Loss, MDD and Max Single Win all unchanged.

------------------------------------------------------------------
C1  Struct_Trigger_Pct 1.20 -> 1.00        (behaviour change)
------------------------------------------------------------------
1.20 was never swept. It was copied from the percentage leg at
v1.13.0 to keep that sweep two-dimensional, and the code said so.
"Copied from the other leg" is not an answer that survives a W5
ten-dimension review.

11-cell sweep, 0.00 to 2.00 step 0.20, everything else frozen.
The 1.20 cell reproduced 129T / 2,670,800 / PF 1.802717 exactly,
so the sweep is trustworthy.

  0.0      0.2       0.4       0.6       0.8      1.0      1.2      1.4-2.0
  1,382k   2,260k    2,309k    2,845k    2,726k   2,762k   2,671k   2,608k

THE GATE IS NOT REDUNDANT. At 0.00 net collapses 48% and drawdown
worsens to -812,000. The design doc had predicted 0.00-0.60 would be
identical to 1.20 on the theory that the lock formula self-gates
early in a trade. That theory is wrong -- see the A-1 note in the
structure leg block for why.

1.4 and above converge to 2,608,400, which IS the structure leg
contributing nothing. No separate Struct_On=False anchor needed.

CHOSE 1.00, NOT THE TOP-SCORING 0.60. 0.60 scores 2,844,800 with a
better drawdown (-492,000), but its left neighbour 0.40 sits at
2,309,200 -- a 535,600 cliff one grid step away. It also shows the
truncation signature: average winner -14%, winners holding 20 bars
instead of 23. 0.8/1.0/1.2 span just 3.3%; 1.00 is the plateau centre.
Same reasoning that rejected Trail 1.0/60 at v1.12.0.

EFFECT, back-solved from the exit-label deltas and matching the
sweep's net delta to the dollar: exactly 2 of 129 trades change.
  2026-07-08  entry 45085   GoldenCross +40,000 -> Struct +72,800
  2026-07-30  entry 40301   BE 0                -> Struct +58,000
Zero trades degrade. Gross Loss -3,327,200 untouched.

------------------------------------------------------------------
C2  Percentage leg collapsed 5 inputs -> 3   (NO behaviour change)
------------------------------------------------------------------
Trail_Giveback_Pct=80 governed only peaks in [1.2%, 2.0%); above
that Tier2's 40 took over. Failure test: raise it to 99 so the lock
in that band (peak x 1%) falls below BE_Cost_Pts and the leg cannot
bind. Result was BIT-IDENTICAL over 129 trades x 13 fields.

99 rather than the 95 originally proposed: at peak 1.2% of 45,000
the lock at 95 is still 27 points, well above BE's 10, so 95 only
loosens the parameter instead of disabling it. 99 gives 5.4 points,
and 9.5 points at the top of the band on the largest entry price in
the sample -- below BE everywhere, so the band is genuinely off.

PROOF THAT ALL FOUR TRAIL EXITS BELONG TO TIER2, independent of the
failure test. Back-solve each exit's lock from entry minus exit
price, then ask which giveback could have produced it:

  lock 383 -> Tier2(40) implies peak 3.13%, base(80) implies 9.38%
  lock 376 -> Tier2(40) implies peak 3.52%, base(80) implies 10.57%
  lock 263 -> Tier2(40) implies peak 2.22%, base(80) implies 6.66%
  lock 240 -> Tier2(40) implies peak 2.08%, base(80) implies 6.23%

Every base-80 figure exceeds that trade's own intrabar MFE, which is
impossible. Every Tier2-40 figure is under its MFE and lands above
2.0%. The base rate never determined an exit in 6.4 years.

COLLAPSE, verified bit-identical in a third run:
  Trail_Trigger_Pct   1.20 -> 2.00
  Trail_Giveback_Pct  80   -> 40
  Tier2_On            True -> False
Three configurations -- base, failure test, collapsed -- are all
bit-identical to each other. The tier parameters are RETIRED, not
deleted: the code stays for reversibility, but re-enabling Tier2
requires re-verification because the base trigger has moved to 2.00.

------------------------------------------------------------------
LIMITS
------------------------------------------------------------------
1. The C1 gain rests on 2 trades, +90,800, paired test 1.37 sigma.
   Below 2 sigma. Not statistically established.
2. Both changed trades are in 2026, so the pre-registered criterion
   "no year holds >50% of the benefit" fails again, for the same
   structural reason recorded at v1.13.0: MinSlope is a fixed 28
   points and loosens 5.2x as the index rises, so the trade
   population itself is skewed toward recent years. Re-test after
   MinSlope is percentage-normalised.
3. The C2 runs were executed at Struct_Trigger_Pct=1.00, not the
   1.20 that was current when the test was specified. That is the
   more relevant configuration given C1, and the only base-band
   trade under 1.20 also exits via Struct, so the conclusion carries
   -- but it was not directly measured under 1.20.
4. Audit of this file: docs/research/
   S16S_v1140_code_architecture_audit_20260806.md
   Nine compliance checks pass; eight findings, none of which change
   any current backtest number.

v1.14.0 (2026-08-05) B1 TIERED GIVEBACK (base v1.13.0):

STATUS: EXPERIMENTAL. Tier2_On defaults to False, which reproduces
v1.13.0 bit-for-bit. Nothing here is validated -- no MC12 run has
been made with it enabled.

WHY: Step 1 measured 1,690,000 of peak profit given back INSIDE the
holding window by the 27 trades that reach bar 25. A2 recovered
89,600 of it -- 5.3%. The other 94.7% is still on the table.

The latch diagnostic (2026-08-05) showed WHERE it sits. On the big
winners the binding leg is the percentage trail, not the structure
leg. Trade #84 at bar 21: peak 1594 pts, structure lock 134, trail
lock 319, structure binding flag 0. Structure locks on the distance
to the recent high, which stays small on a clean one-way move; the
trail locks a fraction of the peak, which grows with the peak. So
structure covers trades with tight structure and modest peaks, and
the trail covers the large-peak trades. The remaining giveback is
almost entirely in the trail's territory.

MECHANISM: a flat Trail_Giveback_Pct treats a 1.2% run and a 5% run
identically. Handing back 80% of the first costs 1% of index; of the
second, 4%. This tier lowers the allowed giveback once peak profit
clears a threshold. The user's framing: what is unacceptable is not
giving back 80%, it is giving back 80% OF A LARGE WIN.

ONE TIER, TWO PARAMETERS. The diagnostic counted 21 armed trades in
6.4 years -- not 24, which was the intraday-MFE upper bound. A
multi-tier table on 21 samples fits noise. Do not add tiers without
first enlarging the sample.

SWEEP: Tier2_Trigger_Pct 1.5/2.0/2.5/3.0/3.5
     x Tier2_Giveback_Pct 30/40/50/60/70 = 25 combos.
Tier2_Giveback_Pct must stay BELOW Trail_Giveback_Pct(80) or the
tier loosens protection instead of tightening it.

DEGENERATE ANCHORS -- all three must be bit-identical to v1.13.0
(129 trades / Net 2,646,400 / PF 1.7953835):
  A. Tier2_On = False               -> tier never evaluated
  B. Tier2_Trigger_Pct = 99         -> threshold unreachable
  C. Tier2_Giveback_Pct = 80        -> tier equals the base rate

PRIOR EXPECTATION, recorded before the run so it cannot be adjusted
afterwards: of the seven worst givebacks in the sample only three
ever armed (#75 peak 1.34%, #33 peak 1.40%, #8 peak 3.21%). Their
peaks straddle the whole range, so no single threshold catches all
three. A rough hand-calc puts the ceiling near 50,000-70,000 across
those three trades -- roughly 2% of net, and again resting on a
handful of trades. If the sweep returns much more than that,
suspect that winners are being cut rather than giveback recovered,
and check the bar-25 cohort before the net figure.

ACCEPTANCE: same nine pre-registered criteria as A2. Criterion 2 is
the bar-25 COHORT (29 trades / 5,355,200), and it is checked FIRST.

------------------------------------------------------------------
RESULT (2026-08-05 sweep, 2026-08-06 user ruling)
------------------------------------------------------------------

ADOPTED: Tier2_On=True, Tier2_Trigger_Pct=2.00, Giveback_Pct=40.
Baseline for every figure below is v1.13.0 FIRST VERSION
(Struct 20/20 Close-based): 129 trades / 2,646,400 / PF 1.7953835.

  Net          2,646,400 -> 2,670,800   (+24,400, +0.92%)
  Gross profit 5,973,600 -> 5,998,000   (+24,400)
  Gross loss  -3,327,200 -> -3,327,200  (unchanged to the dollar)
  PF             1.795384 -> 1.802717   (+0.41%)
  Adjusted PF    1.349643 -> 1.355156
  Return on cap    132.32% -> 133.54%
  Annual return    17.4637% -> 17.6248%
  MDD            -561,200 -> -575,200   (-14,000, 2.49% worse)
  Max single win  602,800 -> 602,800    (unchanged)
  Max closed loss -461,200 -> -461,200  (unchanged)
  Calmar          0.101070 -> 0.101070  (unchanged)
  Flat period    1Y10M13D -> unchanged
  Trades / W:L    129 / 35:90 -> unchanged

ALL THREE DEGENERATE ANCHORS PASSED before the sweep. Anchor C
(Tier2_On=True, Trigger=2, Giveback=80) matters most: the tier
executes on reachable trades but is mathematically inert at the
base rate, so it proves the wiring rather than the gate.

SWEEP: 25 cells. 2 beat baseline, 2 equalled it, 21 fell below.
The trigger axis has a cliff -- 2.00 down to 1.50 costs up to
1,020,000 at the same giveback. The giveback axis is flat by
comparison (the 2.00 row spans 2,586k-2,671k).

EFFECT: exactly 4 of 129 trades change.
  #8  2024-08-05 08:55  TimeStop    -> Trail   122,000 -> 149,200
  #9  2024-08-05 12:50  GoldenCross -> Trail    50,400 -> 101,200
  #10 2024-08-05 20:15  Struct      -> Trail    55,200 ->  92,000
  #23 2025-04-09 11:05  TimeStop    -> Trail   236,800 -> 146,400
Improvement +114,800, degradation -90,400, net +24,400. The single
degrading trade cancels 79% of the gain and drops #23 out of the
top-ten winners. All three improving trades fall on ONE DAY.

CRITERIA: 5 pass, 3 FAIL, 1 unverifiable. Adopted by explicit user
ruling 2026-08-06 with the failures recorded rather than reworded:

  FAIL 2 -- TimeStop cohort 27 trades / 5,187,200 -> 25 / 4,828,400,
    down 358,800. This is the criterion that was flagged at sweep
    time as the one to read before net profit.
  FAIL 4 -- MDD -561,200 -> -575,200. User ruling: criterion 4 as
    written governs "no regression", but the operative constraint
    is a per-contract risk ceiling, and -287,600 per contract
    (vs -280,600) sits inside it. The trade is 14,000 of drawdown
    for 24,400 of net, 1:1.74 in absolute terms. Note the honest
    counter-reading: in PERCENTAGE terms MDD worsens 2.49% while
    net improves only 0.92%, so the ratio favours adoption only on
    an absolute-dollar view.
  FAIL 9 -- concentration is not merely single-year, it is
    SINGLE-DAY. Every improving trade is 2024-08-05.

The pre-registered warning held: gross improvement 114,800 landed
in the predicted 50,000-70,000 band's neighbourhood and the bar-25
cohort did lose ground, exactly as the header said to expect.

LIMITS -- carry these into any report:
  1. Benefit rests on 4 trades, 3 of them on one calendar day.
     Not statistically established.
  2. Trigger 1.50 is a cliff (-38% net). 2.00 is one step away from
     it. Trigger is a percentage so it self-scales with index and
     will not drift, but the margin is one grid step.
  3. TimeStop cohort is now 25 trades, down from 27. Any later work
     that assumes "27 TimeStop trades" must be re-based.
  4. Effective sample is still ~7 months (Jan-Jul 2026 holds 76% of
     trades and 92.4% of profit). MinSlope percentage-normalisation
     will change the trade population and REQUIRES re-validation of
     all nine criteria.

v1.13.0 A2 Structure Trail (2026-08-04, base v1.12.0)

v1.13.0 (2026-08-04) A2 STRUCTURE TRAIL (base v1.12.0):

STATUS: ADOPTED. Struct_On now defaults to True at Lookback 20 /
Buffer 20. User ruling 2026-08-04 after the full anchor + sweep +
trade-list audit. Results in the RESULT block below.

WHY: Step 1 peak-path anatomy (docs/research/
S16S_step1_peak_anatomy_20260804.md) measured that the 27 trades
reaching bar 25 peaked at 6,985,200 gross and realised 5,295,200.
1,690,000 -- 24.2% of peak -- was given back INSIDE the existing
holding window. The percentage trail cannot recover it because at
any giveback tight enough to catch the fade it also decapitates the
winners (0.30/35 measured Net 1,026,800, Top-10 survival 1/10).

A percentage trail is blind: it cannot distinguish a breather before
the move resumes from the actual reversal. To avoid killing the
former it must be loose enough to miss the latter. Hence 80%.

MECHANISM: trail behind market structure instead of behind a
percentage. Stop sits just above the highest point of the recent
N bars. Price keeps falling -> old highs roll out of the window ->
stop follows down. A bounce that sets no new high leaves the stop
untouched, however deep it goes. Only a break of the recent high
exits. This is what a discretionary trader actually watches.

MANDATORY LATCH: a rolling N-bar high can move UP when a bounce
enters the window. Without a latch the lock would shrink and the
stop would retreat, which breaks the monotonicity that defines a
trailing stop. v_Struct_Lock therefore only ever increases.

WINDOW GUARD: the lookback is clamped to bars elapsed since entry,
so the window never reaches back into price structure that predates
this trade.

Struct_UseClose: High-based detection is faithful to where buyers
actually appeared, but one long upper wick in a thin night session
can manufacture a phantom high and push the stop out of reach --
and the night session is this strategy's alpha source. Close-based
filters wicks at the cost of reacting later. DEFAULT IS Close;
BOTH MUST BE SWEPT. Do not assume this default is correct.

SWEEP PLAN (see docs/research/
S16S_A2_structure_trail_experiment_20260804.md):
  P1  Struct_Lookback 5-40 step 5  x  Struct_Buffer_Pts 0/10/20/30/40
      = 40 combos, percentage trail OFF so attribution stays clean
  P2  winner neighbourhood with Struct_UseClose=False
  P3  head to head vs frozen-ATR and prior-day-range variants
  P4  coexistence with the percentage trail

DEGENERATE ANCHORS (run BOTH before trusting any sweep cell; each
must come back bit-identical to v1.12.0, else the wiring is wrong
and every sweep number is void no matter how good it looks):
  A. Struct_Trigger_Pct = 99  -> leg never arms
  B. Struct_Buffer_Pts  = 2000 -> lock stays negative, never latches
  Anchor A tests the arming gate, anchor B tests the lock maths.
  NOTE 2000, not 500: the lock is EntryPrice - (high + buffer), and
  in a large move the recent high sits far BELOW entry -- trade #84
  peaked 1652 pts. A 500 pt buffer would still bind on the big
  winners, which is precisely the population the anchor must not
  touch. 2000 clears the largest peak in the 6.4 year sample.

ACCEPTANCE (pre-registered, nine criteria in the design document).
Note criterion 2 is the bar-25 COHORT of 29 trades / 5,355,200, not
"TimeStop 27" -- Step 1 proved 2 of those exits are GoldenCross.

------------------------------------------------------------------
RESULT (2026-08-04, anchors + 80-cell sweep + trade-list audit)
------------------------------------------------------------------

ADOPTED: Struct_On=True, Lookback=20, Buffer_Pts=20, UseClose=True,
         Trigger_Pct=1.20, Trail_On left True.

  BE only (Trail off, Struct off) : 2,488,000 / PF 1.7478
  Trail 1.20/80 only              : 2,556,800 / PF 1.7685
  Struct 20/20 only               : 2,646,400 / PF 1.7954
  BOTH legs on                    : 2,646,400 / PF 1.7954

BOTH is BIT-IDENTICAL to Struct-only across all 129 trades:
SX_MA_Trail fires 0 times once Struct is on. Struct locks more on
every trade the percentage trail would have caught. Trail is kept
anyway because the code takes the MAX of the three locks, so it can
never make things worse and covers the untested path where a peak
is high while the recent structural high is also high.

DEGENERATE ANCHORS -- BOTH PASSED, bit-identical over 129 trades x
13 fields. Anchor B armed the leg on 24 trades, so
Highest(Close, v_Struct_Window) really did execute; the lock stayed
negative (max sample peak 1652 pts - 2000 buffer) and never latched.
NOTE anchor A was run with Struct_On=False, which makes
Trigger_Pct=99 unreachable -- it degenerated into a repeat of the
Struct_On=False baseline. Not re-run: anchor B strictly covers it
(24 armed + 105 unarmed trades in the same pass).

EFFECT: exactly 2 of 129 trades change. Both were BE exits at zero
and become Struct exits. Zero trades degrade.
  2026-06-25 entry 45901, peak 234,000 -> +103,200
  2024-08-05 entry 19260, peak 167,600 ->  +55,200
Gross Loss, MDD, Max Single Win, the Top-10 winners and the 27
TimeStop trades are all bit-identical to baseline.

CRITERIA: 8 of 9 pass, several perfectly (Top-10 survival 10/10 with
not one dollar moved; TimeStop 27/27 still TimeStop).

CRITERION 9 FAILED ON ITS FACE and was adopted anyway by explicit
user ruling. The rule is "no single year may hold >50% of the
benefit"; the split is 2024 34.8% / 2026 65.2%. Two reasons, both
recorded rather than argued away:
  (a) With n=2 firing trades the criterion is unsatisfiable by
      construction -- any two-trade split is at least 50/50 and in
      practice lumpier. It cannot discriminate a concentrated
      mechanism from a small sample.
  (b) User ruling: the concentration is a symptom of MinSlope being
      a fixed 28 points, which loosens as the index rises (0.32% at
      8,700 vs 0.061% at 46,000), so the trade population itself is
      skewed toward recent years. It is not a property of A2. And
      forward-looking the index will not return to 20,000-30,000,
      so future population resembles 2026, not 2020-2024.
This must be re-tested once MinSlope is percentage-normalised,
because that changes the trade population the criterion measures.

LIMITS -- state these in any report, do not drop them:
  1. Benefit rests on 2 trades, +158,400, paired test 1.36 sigma.
     Below the 2 sigma bar. Not statistically established.
  2. Struct_Lookback >= 25 is mathematically inert: the window is
     clamped by MinList(Lookback, BarsSince+1) and MaxHoldingBars
     is 24, so 25/30/35/40 are the same run. 20 was chosen as the
     smallest value reaching the maximum. REVISIT IF MaxHoldingBars
     CHANGES.
  3. Struct_Buffer_Pts protective value was never measured. Only 2
     trades fired, so the sweep only ever priced the buffer's COST
     (a perfectly linear -4,000 per +5 pts, which is just 2 trades
     x 5 pts x 400 NTD). Buffer=0 scored highest and must NOT be
     shipped: it puts the stop exactly on the recent high, where one
     tick sweeps it. 20 is an operational judgement, not an
     optimisation result.
  4. RESOLVED 2026-08-05. Struct_UseClose=False (High-based) was
     swept and LOST decisively. The High-based run is bit-identical
     to the Struct-off baseline to six decimals on every metric --
     SX_MA_Struct fires ZERO times, both trades revert to
     SX_MA_Trail, Net falls 2,646,400 -> 2,556,800. With highs read
     off High the structure lock never once exceeds the trail lock
     across all 129 trades, so the leg is not weakened, it is
     switched off. Both affected trades are night session (20:15,
     21:55) and 100% of the -89,600 lands in the 20:00-24:00
     bucket; all 83 day-session trades are untouched to the dollar.
     This is the wick hazard the design document predicted. Close
     is now a MEASURED result, not an assumption.
  5. Structure and trail COMPETE, they do not complement. The two
     structure exits fire one bar EARLIER than the trail would, at
     68 and 156 points better. That is why both-legs-on came back
     bit-identical to structure-only: the structure leg always wins
     the max comparison. Trail_On=True is harmless but, at these
     parameters, dead code.
  6. STILL UNVERIFIED: the latch (criterion 7). The performance
     report carries no bar-level lock series, so "v_Struct_Lock is
     monotonically non-decreasing" remains an assumption. See
     S16_S_MACrossShort_v1.13.0_DIAG.pla.

v1.12.0 (2026-08-03) PROFIT TRAIL + BE COST FIX (base v1.11.0):

G1 ARITHMETIC FIX -- BE_Cost_Pts 5 -> 10:
  Backtest settings: slippage 1000 NTD per contract PER SIDE.
  Per contract round trip = 2000 NTD = 10 points (2000 / 200).
  BE_Cost_Pts=5 exits at EntryPrice-5 = 1000 NTD gross vs 2000 NTD
  cost = -1000 NTD/contract. NOT breakeven.
  Evidence: all 5 BE exits in v1.11.0 netted exactly -2000 NTD (2 lots).
  Fix restores the stated design intent (true breakeven after costs).
  SHORT stop moves EP-5 -> EP-10, i.e. triggers EARLIER on retrace.

RESULT (2026-08-03, 42-combo exhaustive sweep + trade-list audit):
  Baseline (Trail_On=False)  : Net 2,488,000 / PF 1.7478 / 129T
  ADOPTED  (1.20 / 80)       : Net 2,556,800 / PF 1.77   / 129T
  All 5 pre-registered acceptance criteria PASS.
  Only 2 of 129 trades change, both from BE-at-zero to a partial
  lock (+40,800 and +28,000). Zero trades degrade.
  NOTE: an earlier single run at 0.30/35 was a disaster
  (Net 1,026,800, Top-10 survival 1/10) -- tight trails decapitate
  the TimeStop winners. The adopted setting is deliberately loose.

G2 NEW -- P3b Profit Trail:
  Problem quantified from v1.11.0 trade list (129 trades w/ MFE):
    - BE_Trigger_Pct=0.80 = 368 pts at index 46,000. Only 36/129
      trades (27.9%) ever reached it. 72.1% had zero protection.
    - 36 trades touched 3,350,000 NTD of open profit and realized
      -738,400. Of those, 25 died to QuickStop_Time (bars>=4 and
      Close>=EntryPrice) after running 139-397 pts in profit.
  Design: track running peak profit, stop at a fixed giveback pct.
    v_MaxProfit  = running max of (EntryPrice - Close)
    trail lock   = v_MaxProfit * (100 - Trail_Giveback_Pct) / 100
    stop level   = EntryPrice - MaxList(BE lock, trail lock)
  BE_Cost_Pts acts as the FLOOR, so the trail can never protect
  less than true breakeven. Trail_On=False reproduces v1.11.0
  behaviour exactly (plus the G1 cost fix).
  Stop order fires intrabar, so it preempts the QuickStop_Time
  market order that currently flushes these trades at ~0.
  Why this is NOT the L4/L5 StopProfit trap: S16_S top-10 winners
  have giveback 0.4%-28.5% (8 of 10 below 30%) with tiny MAE --
  clean one-way momentum bursts. 74.6% of gross winning P&L sits
  in trades a 30% trail would never touch. L5's winners retraced
  deeply mid-trade and were decapitated; these do not.
  RESIDUAL RISK (unprovable from MFE data): an INTERMEDIATE retrace
  beyond the giveback pct that later recovers to a new high is
  invisible in the trade list. Only a bar-by-bar MC12 run settles it.
  MC12 sweep: Trail_Trigger_Pct 0.10/0.20/0.30/0.40/0.60/0.80
            x Trail_Giveback_Pct 25/35/45/55 = 24 combos.
  HARD ACCEPTANCE (any fail -> Trail_On stays False permanently):
    1. Top-10 winner survival >= 80%
    2. Max single win >= 90% of 602,800
    3. Net > 2,478,000
    4. TimeStop 27-trade / 96.3% WR structure intact
    5. MDD no worse than -561,200
  Full analysis: docs/research/S16S_profit_exit_analysis_20260803.md

v1.11.0 (2026-08-02) TRUE BREAKEVEN REDESIGN (base v1.8.0):
BE module rewritten from ATR-based profit lock to true breakeven protection.
F1: ATR trigger (BE_Trigger_ATR * Frozen_ATR) -> fixed pct (BE_Trigger_Pct).
F2: True breakeven = EntryPrice - BE_Cost_Pts (covers commission/slippage).
    SHORT: exit guarantees no loss after costs (5 pts = 1000 NTD RT).
F3: Single tier (removed Tier2 complexity -- was never independently validated).
F4: Stop order replaces market order (catches intrabar violations).
F5: Per-entry reset (re-entry gets independent BE with fresh calculation).
F6: Removed all ATR dependency from BE module.
F7: Inputs simplified: BE_On + BE_Trigger_Pct + BE_Cost_Pts (was 5 inputs).
MC12 sweep result: BE_Trigger_Pct=0.80 BE_Cost_Pts=5 (80-combo sweep).
                   Plateau at 0.70-1.00, phase transition at 0.60->0.70.

v1.8.0 (2026-07-29) RE-ENTRY SL FIX Option 1: Inherit Frozen ATR (base v1.7.1):
ROOT CAUSE: After stop loss exit, ATR inflates from exit volatility.
Re-entry inherits inflated ATR, widening SL/BE/ML simultaneously.
FIX: Save v_Original_Frozen_ATR at main entry. Re-entry inherits
the original (pre-inflation) ATR for SL calc, BE thresholds, and
ML activation. Completely eliminates ATR inflation cascade.
ALSO: QS_MaxLoss_Pct default 0.15 -> 0.25 (v1.7.1 optimal).
Solves: A1 + A2 + A3. Does NOT solve: B1 (chain limit).

v1.7.1 (2026-07-29) QS_LOSS PERCENTAGE (base v1.6.2):
ROOT CAUSE: Fixed-point QS_Loss is index-level-dependent.
- QS_Loss 60 pts at 9,000  = 0.67% (rarely triggers, zero re-entries)
- QS_Loss 60 pts at 45,000 = 0.13% (trivially triggers, all re-entries)
CHANGE: QuickStop_MaxLoss_Pts (60) -> QS_MaxLoss_Pct (0.15%)
- Loss check: v_Loss > EntryPrice * QS_MaxLoss_Pct / 100
- Default 0.15% = 60/40000 (equivalent at current index level)
MinSlope UNCHANGED (still fixed 28 pts) -- see v1.7.
MC12 sweep: QS_MaxLoss_Pct 0.05 ~ 0.30, step 0.025

v1.5 (2026-07-26) INITIAL STOP HARDENING (SetStopContract + SL_Pct):
BUG FIX - SetStopContract MISSING (same issue as L2/L4/L5):
  SetStopLoss without SetStopContract = stop dollar amount
  is for the TOTAL POSITION, not per contract.
  S16_S trades 2 contracts -> engine stop was 2x tighter than
  designed. SetStopContract makes SetStopLoss PER-CONTRACT.
NEW - SL_Pct Percentage Stop Cap (SHORT):
  ATR can spike in volatile regimes (S16_S alpha zone),
  causing ATR*4.0 stop to exceed any reasonable risk budget.
  SL_Pct caps max stop distance as pct of entry price.
  For SHORT: ceiling = EntryPrice + EntryPrice * SL_Pct / 100.
  Applied to BOTH engine stop (P7) and custom stop (P6).
  MC sweep 0-5.0 step 0.25: converge at SL_Pct=1.00.
  1.00 is tightest non-degrading value. Below 0.75 degrades
  (0.25 = -6% net, MDD worsens -478K).
ENGINE STOP ARCHITECTURE CHANGE:
  v_Guard_Distance now computed EVERY BAR from current ATR
  (not frozen from previous trade). Fixes SetStopLoss(0) bug
  when flat, and eliminates stale ATR from different regime.
  Net +2,006,800 vs v1.4 +1,073,200 (+87%) primarily from this.

v1.4-BELATE (2026-07-18, G3 track result, user pre-test thesis CONFIRMED):
BE trailing tiers re-timed from early (1.0/1.5 ATR) to late
(2.5/3.5 ATR) activation with wider buffers (15/20 pts).
MC12 evidence (109T): Net 888,400 -> 1,073,200 (+20.8%),
PF 1.876, MDD -228,000 (-18.63%), Sortino 0.979, RecFactor 4.71,
TimeStop 21 -> 23 wins. Plateau verified: trigger 2.0/2.5/3.0
flat within 0.6%; boundary BE_Off = 1,022K. 2.5/3.5 = center.
Fast-loss response UNCHANGED (QuickStop/ML/SetStopLoss as before).
G2 same day: MaxHold 24 confirmed optimal (12/36/48 all worse).

v1.3-TIMEGUARD (2026-07-18, user design):
"Latest entry + latest exit" tail guard. Positions can NEVER
survive into any market closure (morning break 0500-0845,
weekend, holiday).
- Tail_LastEntry_Time (430): last entry SIGNAL bar 0430
  (fill 04:30). Entries allowed all night up to here.
  [v1.17.0 CORRECTION: "(fill 04:30)" is wrong and this is the
   original source of the defect. The signal bar is 0430 and the
   order is a next-bar order, so the fill is 04:35. The intent
   written here was right; the implementation was off by one bar
   and the comment recorded the intent rather than the behaviour.
   See Tail_FillSemantic_On.]
- Tail_ForceExit_Time (440): force-flat signal at 0440 bar
  close, fill 04:40 (445-bar open). 20-min buffer to close.
Verified vs 110-trade baseline (see research folder
S16_S_HOLIDAY_IMPACT_20260717.md for methodology):
- Blocks 2025-03-05 05:00 entry (-32,800 held across morning
  break) -> baseline +32.8K
- 2026-03-07 exit moves 04:50 -> 04:40 (delta tiny)
- 2026-06-06 +292,600 TimeStop at 04:35 untouched
Expected: ~109T / ~+866K, pending MC12 verify.
Version number unified with research .pla (both v1.3).

v1.0.1-HOLIDAY CHANGE (2026-07-16):
CRITICAL COMPLIANCE FIX - Rule #11 gap closure.
Prior v1.0-PROD had v_Holiday_Block hardcoded to False
(W2 draft placeholder never replaced before PROMOTE - promotion audit gap).
This patch installs the shared 63-entry HolidayFlat_v3 registry
identical to L1-L5 / S1 / S3_S / research S16_S v1.2-HOLIDAY.
Also changes Date arithmetic to EL-standard (Year - 1900) format
for cross-strategy alignment.
Behavior change: strategy now correctly blocks entry and force-flats
positions on the 63 registered TAIFEX holidays 2019-2027.
Alpha logic UNCHANGED - Config LOCKED (F25/S70/Slope28/QS60/MH24/StopATRx4).
Backtest re-run required to verify no change to core performance
(expected: minimal impact - most trades in normal sessions).

v1.0-PROD PROMOTE EVIDENCE (2026-07-10):

v1.0-PROD PROMOTE EVIDENCE (2026-07-10):
W4 WFA (9-window rolling IS 2y / OOS 6m): WFE 77.4% (>> 50% gate)
- 416 OOS trades / +1,737,800 aggregate profit
- 7/9 windows profitable (Bear/Volatile 100% win)
- W6 (2024 H2 Bull whipsaw) -347K acknowledged as insurance cost
- Parameter CV 21-25% MODERATE (no curve fit)
W5 Sniper-adapted 5-piece: 8/8 PASS
Baseline: 106T / +1.03M / PF 1.885 / MDD -17.97% / Sharpe +0.463

Config LOCKED:
  Fast=25, Slow=70, MinSlope=28 (pure points)
  QuickStop_MaxLoss_Pts=60, MaxHold=24, StopATRMult=4.0

Portfolio position: 3% cap, sniper sleeve for momentum burst hedge
Bull regime insurance cost accepted per 2026-07-08 Option A ruling

v0.6-REJECTED (2026-07-10):
ATR-based adaptive Slope threshold was tested and FAILED:
- Test 1 (ATRMult=0.7): Net -128K, 181 trades (over-entry)
- Test 2 (ATRMult=1.5): Net +59K, only 2 trades (over-filter)
- Root cause: ATR measures volatility (both directions),
  not directional slope. Wrong metric for slope filter.
Reverted to v0.5 pure-points MinSlope=28.
User insight confirmed: Slope filter should be absolute points
to reject "flat/upward" cross signals directly.
TXF1 real level ~47000 (not 25000 as initially assumed) means
MinSlope=28 pure points is even more conservative.

v0.5-FINAL EVIDENCE (2026-07-10 MC12 backtest):
Config: F25/S70/Slope28 + QS(4,60) MH24 StopATRx4
Result: Net +1,028,600 / PF 1.885 / MDD -271,600 (17.97%) / 106T / WR 22.64%
Sharpe +0.463 / Calmar ~3.8 / Sniper reward:risk profile
W5 Sniper-adapted validation: 8/8 PASS
  - Ruin probability 0.03%
  - Single trade max loss < 5% capital
  - Kelly criterion 11.2%
  - Expected value +10,547/trade
  - Bear PF 3.79 / Volatile PF 2.13 / Bull PF 0.70
  - Max consecutive loss 16.2% capital

v0.5 GA (2026-07-09, 1024-combo Genetic Algorithm):
Sensitivity: Fast+Slope=86% of total, 4 exit params all LOW (<0.06)
MinSlope 26->28: Slope26-28 plateau (-2.4%), Slope30 cliff (-27%)
ZLEMA_Slow 70: narrow peak (S80=-33.5%), documented
Calmar 3.961 / Avg Win:Loss 6.81:1

v0.4 EVIDENCE (2026-07-09 backtest):
Config: F25/S90/Slope26/QS45/MH24/StopATRx4
Result: Net +1,059,200 / PF 1.903 / MDD $-259K / 119T / WR 26.9%

v0.3-P0FIX (2026-07-08): F1/F2/F3 code bug fixes

PERFORMANCE (v1.5 Excel Report, MC12 backtest 2026-07-26, SL_Pct=1.00):
Net Profit    : 2,006,800 TWD
Gross Profit  : 4,595,600 TWD
Gross Loss    : -2,588,800 TWD
Profit Factor : 1.775
Win Rate      : 25.89% (29W / 83L)
MDD           : -456,000 (-18.31%)
Total Trades  : 112
Avg Trade     : 17,918 TWD
Win/Loss Ratio: 5.08
Avg Winner    : 158,469 TWD
Avg Loser     : -31,190 TWD
Max Single Win: 602,800 TWD
Max Single Loss: -85,200 TWD
Max Consec W  : 3
Max Consec L  : 10
Avg Bars W/L  : 24 / 5.9
Sharpe (ann.) : 0.718
Sortino       : 1.216
SL_Pct        : 1.00 (converge; MC sweep 0-5.0 step 0.25)
SetStopContract: YES (per-contract engine stop)

vs v1.4 (+1,073,200 / PF 1.876 / MDD -228K / 109T):
Net +87%, MDD% stable (18.6%->18.3%), PF -0.10, +3 trades.
Root cause: engine stop from stale frozen ATR -> current ATR every bar.

DESIGN PHILOSOPHY (v0.5-FINAL, evolved from W1 spec):
"Sniper style: entry selective, exit swift."
Strategy KNOWS what regime to trade (Bear + Volatile),
LOSES SMALL in unsuitable regime (Bull), stays profitable overall.
5M timeframe ZLEMA death cross + MinSlope selective entry.
TimeStop (24 bars = 2hr) captures momentum burst decay window.
NO Regime Filter (user 2026-07-08 ruling Option A: pure simple).
NO TP (feedback_trend_let_profits_run).

STRATEGY IDENTITY:
- Primary regime: Bear (PF 3.79) + Volatile (PF 2.13) = alpha zone
- Insurance cost: Bull regime (PF 0.70) = -106K over 35 trades
- Alpha structure: 20 TimeStop wins (100% WR, avg +105K)
  offset 72 QuickStop losses (small, avg -15K)
- Sniper profile: 22.6% WR + 6.8:1 reward:risk ratio

ARCHITECTURE:
Data1 = TXF1 5M (execution + signal)

W0 EVIDENCE (2026-07-08 daily proxy STRONG PASS):
- 40/216 combos 4/4 institutional gates
- Best: Fast=12, Slow=30, Fwd_N=3 -> WR 45.8% / RR 1.29 / Stability 57.1%
- 5M projected default: Fast=8, Slow=25

EXIT PRIORITY CHAIN (P0 to P7):
P0 : Rule #11/#12 compliance (Kill / Registry / Holiday / Settlement)
P1 : M5 Quick Stop (time-based OR loss-based)
P2 : M6 Multi-Layer 1M monitor (Rule #17, 5 categories 5 factors)
P3 : M7 True Breakeven + P3b Profit Trail (v1.12.0, single stop order)
P4 : Golden Cross (main exit)
P5 : M8 Time Stop (max holding bars)
P6 : ATR-based Frozen SL
P7 : SetStopContract + SetStopLoss + SL_Pct engine guard (Rule #12 backup)

RULE COMPLIANCE:
Rule #11 Settlement_Flat - YES (Priority 0 order)
Rule #12 SetStopContract + SetStopLoss + SL_Pct - YES (v1.5, short variant MP >= 0, SL_Pct=1.00 converge)
Rule #13 10-dim eval - to run at W5
Rule #14 OFFICIAL_ROADMAP - YES (S16_S is in Batch 04)
Rule #15 ASCII 100% - YES (verified via scripts/verify_pla_ascii.py)
Rule #16 5-pillar - YES (context/rules/verification/memory/format all met)
Rule #17 Multi-Layer SL - YES (implemented as M6)
Rule #18 Non-WFA 5 pack - to run at W5

LABEL CONVENTIONS:
SE_MA_DeathCross         : Entry (short on death cross)
SX_MA_GoldenCross        : Main exit (golden cross)
SX_MA_QuickStop_Time     : P1 M5 time-based quick stop
SX_MA_QuickStop_Loss     : P1 M5 loss-based quick stop
SX_MA_ML_Exit            : P2 M6 Multi-Layer trigger
SX_MA_BE                 : P3 M7 true breakeven (v1.11.0 stop order)
SX_MA_Trail              : P3b profit trail (v1.12.0, trail is binding)
SX_MA_TimeStop           : P5 M8 max holding time
SX_MA_SL                 : P6 frozen ATR SL
SX_MA_Kill               : P0 manual kill
SX_MA_Registry           : P0 registry expired
SX_MA_Holiday            : P0 holiday block
SX_MA_Settlement         : P0 settlement flat
SX_MA_TailFlat           : P0.5 tail force exit (v1.3 time guard)
SE_MA_ReEntry            : Re-entry short (v1.6 washout recovery)

CHART SETUP REQUIRED:
Data1 = TXF1 5M
IntrabarOrderGeneration = FALSE
MaxBarsBack >= 200 (covers all indicator warm-up)
================================================================================

[IntrabarOrderGeneration = False]


============================================================
SECTION 1 - INPUTS
============================================================
```

---

## 3. Per-block rationale

In file order. Section numbers match the pointers left in the code.

### 3.1  Group C: M6 Rule #17 Multi-Layer Monitor

```text
 ===== Group C: M6 Rule #17 Multi-Layer Monitor =====
 ML_On 1 -> 0, B10 2026-08-14.

 The batch swept ML_On x ActivationPct x ScoreTrigger x
 MinCategories, 2 x 7 x 9 x 4 = 504 cells exhaustive. EVERY CELL
 RETURNED THE SAME NET, 2,328,800 -- the four decision inputs
 are jointly inert at the post-B9 configuration.

 Two readings, and both land on the same number, which is why
 0 could be adopted without waiting for them to be separated:
   A  the module genuinely never fires here -- setting 0 changes
      nothing and removes a dead mechanism
   B  the module fires and every firing deepens a loss -- then
      0 is worth the +52,400 that separates this from B9

 The B9 winner and this batch agree on gross profit to the cent
 (4,702,400), on winners (56), losers (123) and drawdown
 (-364,800), and differ ONLY in gross loss: -2,426,000 against
 -2,373,600. Same trades, same winners, losers smaller by
 52,400. ML is a loss-side module (Rule #17), so that signature
 is its own contribution, and the sign is negative.

 CONFIRMED IN A PLAIN BACKTEST 2026-08-14: SX_MA_ML_Exit is
 absent from the exit list entirely.

 RULE #17 NOTE. This disables the multi-layer monitor. Fine in
 research; at PROMOTE, Rule #13's operational-risk dimension
 will ask about it, and the answer is this 504-cell measurement,
 not an omission. The six detector inputs below are untouched so
 the module can be re-enabled with one switch.
```

### 3.2  Group D: M7 True Breakeven - v1.11.0 redesign

```text
 ===== Group D: M7 True Breakeven - v1.11.0 redesign =====
 v1.11.0: ATR trigger -> fixed pct. True breakeven protection.
 BE_Trigger_Pct: profit as pct of EntryPrice to activate BE.
 0.80 = MC12 80-combo sweep optimum, plateau 0.70-1.00.
 BE_Cost_Pts: pts covering slippage. v1.12.0 G1: 5 -> 10.
   1000 NTD/contract/side x 2 sides = 2000 NTD = 10 pts.
   5 pts only recovered 1000 NTD -> every BE exit lost money.
 BE_Trigger_Pct 0.60 -> 0.70, B9 2026-08-14. Joint sweep with
 Struct, 8 x 5 x 8 x 7 = 2,240 cells exhaustive, because the two
 modules write the same v_BE_Stop_Level and are not separable.
   0.7  2,276,400   adopted
   0.8  2,274,400   2,000 below
   0.9  2,250,000
   1.0  2,245,200
   0.5  2,014,400
 Arming later leaves fewer positions pinned at breakeven: one
 winner became a loser (56 from 57) but the survivors ran
 further, average win 82,112 -> 83,971.
```

### 3.3  Group D2: P3b Profit Trail - v1.12.0

```text
 ===== Group D2: P3b Profit Trail - v1.12.0 =====
 Locks a pct of peak open profit once the trade proves itself.
 BE_Cost_Pts is the floor: trail never protects less than BE.
 Trail_On=False reproduces v1.11.0 exactly (plus G1 cost fix).
 Trail_Trigger_Pct : peak profit as pct of EntryPrice to arm.
 Trail_Giveback_Pct: pct of peak profit allowed to be given back
   e.g. peak 600 pts, giveback 80 -> stop locks 120 pts.
 1.20 / 80 SET BY 42-COMBO EXHAUSTIVE SWEEP (2026-08-03).
   Chosen for ROBUSTNESS, not peak: 1.0/60 scored higher
   (2,632,800) but its 4-cell neighbourhood averages 2,330,100
   -- below baseline -- because 0.8/60 collapses to 1,896,000.
   1.2/80 sits inside the flat region (trigger 1.0-1.2 x
   giveback 70-90, all cells 2.45M-2.59M).
 Sanity anchor 1.2/90 = 2,518,400 converged to baseline as
   predicted, confirming the module is wired correctly.
 Verified effect AT v1.12.0: 2 of 129 trades change, both
   improve, none degrade. Top-10 winners, TimeStop 27, Gross
   Loss and MDD all bit-identical. Net 2,488,000 -> 2,556,800.
 SUPERSEDED at v1.13.0: once the structure leg is on, this leg
   fires 0 times -- structure always wins the max comparison.
 SUPERSEDED AGAIN at v1.14.0: with Tier2 on, this leg fires 4
   times and TimeStop is down to 25 trades. The "TimeStop 27"
   above is the v1.12.0 figure, kept for the record, NOT the
   current baseline.
 CAVEATS: gain rests on 2 trades (+68,800, 1.40 sigma). Residual
   tail risk is a trade giving back 80% of a >=1.2% run then
   recovering to a new high -- never observed in 6.4 years.
 B7 2026-08-13: 0. All 209 enabled cells lose to the disabled
 figure; see the B7 addendum in the version block. Trigger and
 Giveback below are INERT while this is 0 and are deliberately
 left at their historical values rather than set to the best
 enabled cell, which was measured to lose money.
```

### 3.4  v1.15.0 C2: collapsed. The old 1.20/80 base band was measured dead

```text
 v1.15.0 C2: collapsed. The old 1.20/80 base band was measured dead
 -- raising the giveback to 99 changed nothing over 129 trades, and
 all four Trail exits back-solve to Tier2's rate. Moving the
 trigger to 2.00 with giveback 40 reproduces the whole leg with
 Tier2 switched off, verified bit-identical. See header C2.
```

### 3.5  Group D3: A2 Structure Trail - v1.13.0 (ADOPTED)

```text
 ===== Group D3: A2 Structure Trail - v1.13.0 (ADOPTED) =====
 Trails behind market structure rather than behind a percentage.
 Stop sits just above the highest point of the recent N bars.
 A retrace of any depth is tolerated as long as it sets no new
 high; only a break of recent structure exits.

 Struct_On=False still reproduces v1.12.0 bit-for-bit and remains
   the rollback path and the degenerate anchor.
 Struct_Lookback    : bars to scan for the structural high.
   Clamped to bars-since-entry, so the window never reaches back
   before this trade started. Swept 5-40 step 5.
   Upper bound 40 is safe against MaxBarsBack=100 (deepest
   existing lookback is ML_ATR_LongLen=90, leaving ~9 bars).
 Struct_Buffer_Pts  : points above that high to place the stop.
   Too small = swept by noise, too large = never binds.
   Swept 0-45 step 5. Set 2000 for degenerate anchor B.
 Struct_UseClose    : True = highs measured on Close (wick proof,
   reacts later), False = on High (faithful, wick exposed).
   SETTLED BY P2, 2026-08-05. Close wins decisively. Switching to
   High does not merely score worse -- it makes the leg INERT:
   the result matched the Struct-off baseline to six decimals,
   0 structure exits against 2. The predicted mechanism was
   confirmed exactly: both affected trades sit in the 20:00-24:00
   night block (-89,600 there, day session 83 trades unchanged to
   the dollar). One long upper wick in a thin night session
   manufactures a phantom high and pushes the stop out of reach,
   and the night session is this strategy's alpha source.
   Do not revisit without a reason that is not "faithfulness".
 Struct_Trigger_Pct : peak profit pct to arm, held at 1.20 for the
   first pass to keep the sweep two-dimensional. Unswept.
 ADOPTED 2026-08-04: Struct_On True, 20 / 20. See RESULT block in
 the header. Lookback 20 = smallest value reaching the maximum
 (25+ are clamped by MaxHoldingBars=24 and therefore identical).
 Buffer 20 is an OPERATIONAL choice, not the sweep optimum:
 Buffer 0 scored 2,662,400 but parks the stop exactly on the
 recent high where one tick sweeps it. The 16,000 (0.6%) given up
 buys a noise cushion the 2-trade sample could never price.
 Struct_Buffer_Pts 20 -> 12, B9 2026-08-14.

 B8 swept 10-50 and improved monotonically down to 10, the grid
 floor, so B8b extended to 0 -- and the trend REVERSED: 0 gives
 2,246,800 against 10's 2,258,800. Below 8 the surface is jitter
 with no structure (0/1/4/5/6/7 wander inside 222.8k-224.7k),
 above it a smooth monotone ridge runs 8 -> 20. So 10 was never
 a truncated boundary; the function turns over just below it.

 Then B9 moved it again. At BE_Trigger 0.6 the best buffer is
 10; at BE_Trigger 0.7 it is 12 (2,276,400, with 14 at
 2,264,400 and 16 at 2,258,800). The two modules share a stop
 level, so neither has a standalone optimum -- which is exactly
 what B9 exists to catch.

 Struct_Lookback stays 20: values 20 through 50 returned
 IDENTICAL results in B8, seven cells, because MaxHoldingBars=24
 is shorter than the window so it barely rolls. Inert register.
```

### 3.6  v1.15.0 C1: 1.20 -> 1.00. 11-cell sweep, plateau centre of

```text
 v1.15.0 C1: 1.20 -> 1.00. 11-cell sweep, plateau centre of
 0.8/1.0/1.2 (span 3.3%). NOT the top-scoring 0.60, which sits one
 grid step from a 535,600 cliff at 0.40. See header C1.

 SUPERSEDED 2026-08-14 BY B8. The reasoning above was measured on
 the v1.15.0 population under Slope_Form = 1; the entry population
 has since been replaced almost entirely (28 shared trades out of
 118), so the 0.40 cliff it avoids no longer exists in this form.
 Re-measured across 6,156 exhaustive cells, 0.60 and 0.65 return
 IDENTICAL results everywhere they appear, with 0.55 and 0.70 both
 about 45,000 lower -- a genuine two-sided plateau, not a peak
 beside a cliff. 0.60 is taken as the incumbent of the pair.
```

### 3.7  Group D4: B1 Tiered Giveback - v1.14.0 (DEFAULT OFF)

```text
 ===== Group D4: B1 Tiered Giveback - v1.14.0 (DEFAULT OFF) =====
 The flat Trail_Giveback_Pct treats a 1.2% run and a 5% run the
 same. Giving back 80% of the first costs 1% of index; of the
 second, 4%. This tier tightens the giveback once peak profit
 clears a threshold, so large winners are not handed back.

 Tier2_On=False reproduces v1.13.0 bit-for-bit -- shipped default
   and degenerate anchor A.
 Tier2_Trigger_Pct : peak profit pct at which the tier engages.
   Sweep 1.5 / 2.0 / 2.5 / 3.0 / 3.5.
   Set 99 for degenerate anchor B (unreachable threshold).
 Tier2_Giveback_Pct: giveback allowed above that threshold.
   Sweep 30 / 40 / 50 / 60 / 70. MUST be lower than
   Trail_Giveback_Pct or the tier loosens instead of tightening.
   Set equal to Trail_Giveback_Pct for degenerate anchor C.

 ONE TIER ONLY, TWO PARAMETERS. 21 armed trades in 6.4 years cannot
 support a multi-tier table -- it would fit noise. Do not add tiers
 without first enlarging the sample.
 ADOPTED 2026-08-06 by user ruling: True / 2.00 / 40.
   Net 2,646,400 -> 2,670,800. 4 trades change, 3 improve on a
   single day (2024-08-05), 1 degrades by -90,400.
   Criteria 2, 4 and 9 FAILED and were adopted anyway -- see the
   RESULT block in the header. Do not restate this as a clean
   pass.
   Tier2_On=False still reproduces v1.13.0 bit-for-bit.
 v1.15.0 C2: RETIRED, not deleted. With Trail now at 2.00/40 the
 tier is redundant -- the collapsed configuration was verified
 bit-identical over 129 trades x 13 fields. Code kept so the tier
 can be revived, but RE-ENABLING REQUIRES RE-VERIFICATION: the base
 trigger has moved to 2.00, so Tier2 at 2.00 would now be a no-op
 and any other value changes a band that was never swept.
```

### 3.8  Group E: M8 Time Stop - v0.5 (KEY ALPHA DRIVER)

```text
 ===== Group E: M8 Time Stop - v0.5 (KEY ALPHA DRIVER) =====
 ===== Group E: M8 Time Stop =====
 MaxHoldingBars=24 = 2hr. Thesis: a momentum burst self-resolves
 inside two hours; past that you are holding a random position.

 CURRENT COUNT (v1.14.0): 25 trades / 4,828,400. NOT the "31
   trades / 100% WR" the pre-v1.12.0 comment claimed -- that value
   is stale. It was 27 through v1.13.0 and B1 took two of them
   (#8, #23) by firing a stop order intrabar before this market
   order could evaluate at bar close.

 WHAT THIS LEG ACTUALLY DOES: it cuts WINNERS. QuickStop_Time
   (4 bars AND no profit) handles trades that never worked; this
   one exits trades that ARE working, purely on bar count.

 OPEN QUESTIONS -- none of these are settled:
  1. M8_On=False (no time limit at all) has NEVER been tested.
     The 2026-07-18 sweep covered 12/24/36/48 -- all finite.
  2. That sweep ran at v1.4-BELATE on 109 trades, BEFORE frozen
     ATR, true BE, the percentage trail and the structure trail
     existed. Its premise was "past 24 bars the position is
     unprotected", which no longer holds: three protective legs
     now run, and above a 2% peak the trail locks 60% of it.
  3. MaxHoldingBars is COUPLED to Struct_Lookback. The structure
     window is MinList(Lookback, BarsSince+1), so with a 24-bar
     cap it barely rolls and Lookback >= 25 is inert. CHANGING
     THIS VALUE INVALIDATES A2's "20 is optimal" finding.
  4. Interaction with Tail_ForceExit_Time is untested -- a longer
     hold pushes more positions toward the 0440 forced flat.
```

### 3.9  Group I: Tail Time Guard - v1.3, rebuilt v1.18.0

```text
 ===== Group I: Tail Time Guard - v1.3, rebuilt v1.18.0 =====
 Never hold into ANY closure. Both conditions are tail-only:
 bounded by Time <= 500 (MC 24hr pitfall rule).

 Tail_NoEntry_From (v1.18.0, was Tail_LastEntry_Time)
   Wall-clock time from which no position may be OPENED. Names
   the FILL, not the signal -- the signal cutoff is derived
   from it below and is not separately settable.

   WAS 430, DERIVED (author, 2026-08-10): the night session
   closes at 0500 and no new position may be opened inside the
   last 30 minutes. 0500 - 30 = 0430. A sibling of
   Tail_ForceExit_Time, not a derivative of it -- both measure
   back from the same close.

   NOW 415, MEASURED (B3 + B3b, 2026-08-12). At
   Tail_ForceExit_Time = 430 every value from 350 to 415 gives
   the identical 184 trades / 1,678,000; 425 admits two more
   entries worth -48,800. The plateau is ONE-SIDED: flat below,
   a cliff above. 415 is the widest value still on the flat
   side, and taking anything lower would extend the block into
   a window with zero observations in 6.4 years -- extrapolating
   "the tail is bad" to where there is no data. Untested gap:
   420, so the true edge lies somewhere in (415, 425].

   ENCODING PITFALL, recorded 2026-08-12. This input is read
   through TimeToMinutes(), which computes
       int(t/100)*60 + mod(t,100)
   so a value that is not a legal clock time is NOT rejected;
   it is quietly reinterpreted. 365 means 3*60+65 = 245 min =
   0405, 380 means 0420, 395 means 0435. B3b's sweep grid
   contained all three and they looked evenly spaced while
   actually jumping. ANY value adopted here must be a legal
   clock time, and any future time sweep must step so every
   grid point lands inside 00-59 minutes.

 Tail_ForceExit_Time
   Force-flat signal bar stamp; the fill lands one bar later.

   WAS 440 (0500 close - 20 min), unchanged since v1.3 and
   never swept. B3 swept 430..500 and B3b extended DOWN to 350
   because the B3 optimum sat on the grid's lower boundary --
   a boundary optimum is a truncation, not a plateau.

   MEASURED PROFILE at Tail_NoEntry_From <= 415:
       380   1,465,600   PF 1.53
       390   1,542,000   PF 1.56
       420   1,644,000   PF 1.60
       430   1,678,000   PF 1.61   <- adopted
       440   1,522,000   PF 1.54   (the old default)
   Supported on BOTH sides -- 420 is 2.0% below and 440 is 9.3%
   below, each far inside the 40% adjacent-cell rule. 430 costs
   5,200 more drawdown than 420 and returns 34,000 more net.

   MECHANISM. Moving the flat 10 minutes earlier RAISED gross
   profit (4,348,800 -> 4,427,200) as well as cutting gross
   loss, so this is not simply "fewer trades": positions held
   into 0430-0440 were giving profit back. The last half hour
   of the night session destroys value on both sides of the
   book.
```

### 3.10  Tail_DayNoEntry_From -- v1.22.0. THE DAY SESSION'S OWN RULE.

```text
 Tail_DayNoEntry_From -- v1.22.0. THE DAY SESSION'S OWN RULE.

 Names the FILL side, same convention as Tail_NoEntry_From: no
 position may be OPENED from this wall-clock time onward. The
 signal cutoff is derived in Section 4.5 with the same
 Tail_Signal_Lead_Bars and is not separately settable.

   1335 -> cutoff 1325 -> last fill bar 1330
   so 1335, 1340, 1345 and 1505 can carry no new entry.

 User ruling 2026-08-13. Adopted on principle, not on data: a
 position opened in the last ten minutes of the day session
 cannot be reached by any exit mechanism before the 1345-1500
 break. MEASURED SAMPLE COST -18,400 over exactly two trades
 (2024-11-29 fill 1335 +45,600 and 2026-07-28 fill 1340 -27,200),
 one winner and one loser, so n=2 cannot judge the rule.

 Before this input the day session had NO tail rule at all: every
 day bar satisfies "Time > 500", so Tail_NoEntry_From governed
 only the post-midnight window and the day side was protected
 solely by Sess_LastBar_Block_On as a side effect.

 DEGENERATE ANCHOR: 1350 restores v1.21.0 exactly and MUST give
 182 trades / 2,052,800 / PF 1.838288.
```

### 3.11  Tail_Signal_Lead_Bars -- NOT A TUNING KNOB.

```text
 Tail_Signal_Lead_Bars -- NOT A TUNING KNOB.

 How many bars EARLIER than Tail_NoEntry_From the last entry
 SIGNAL may sit. 2 is derived, not chosen:

   bars are stamped at their CLOSE, so bar T spans
   (T - BarInterval, T]

   death cross  next bar at market -> fills at the next bar's
                OPEN, wall-clock ~T.      needs T <= X - 1 bar
   re-entry     next bar at ... stop -> the order is live for
                the WHOLE next bar and can fill as late as
                wall-clock T + 1 bar.     needs T <= X - 2 bars

 2 is the stricter of the two, so ONE rule covers both entry
 paths and cannot be right for one and wrong for the other.
 The market path gets one bar more margin than it needs; that
 is the price of having a single rule, and it is deliberate.

 Changing this value requires redoing the order-type analysis
 above -- it is an input only because Rule #1 forbids hard
 constants, and to make the degenerate anchor runnable.

 MEASURED INERT (B3, 2026-08-12). All five values 0..4 return
 the identical 184 trades / 1,678,000 at the adopted
 Tail_NoEntry_From, so at this cutoff the lead has nothing left
 to suppress. Held at the DERIVED 2 rather than collapsed to 0:
 the derivation above covers both order types, and it will bind
 again the moment Tail_NoEntry_From moves later. Recorded in
 the inert register, first in line if the file is simplified.
```

### 3.12  Group J: Session Gap Filter - v1.16.0 (DEFAULT OFF)

```text
 ===== Group J: Session Gap Filter - v1.16.0 (DEFAULT OFF) =====
 Suppresses the entry SIGNAL on the opening bar(s) of a session
 when the session opened with a DOWN gap and that opening bar
 closed at or above its own open.

 WHY THIS EXISTS -- structural, not statistical:
   v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast
   On the first bar of a session [1] is the LAST BAR OF THE
   PREVIOUS SESSION, so an overnight gap is measured as if it
   were one bar of momentum. MinSlope cannot filter it.
   Evidence: all 17 day-open entries in v1.15.0 followed a DOWN
   gap (base rate 44.7%; p ~ 4.7e-7). The 10 whose opening bar
   closed at or above its open went 0 for 10, -379,600.

 SIGNAL / FILL MAPPING (see the offset rule in Section 4.5):
   Gap_Scope_Bars = N suppresses the SIGNAL on session bars
   1..N, therefore no entry FILL on session bars 2..N+1.

 Gap_Rise_Min_Pct semantics: the test is >=, so the default 0.00
 also blocks a bar that closed exactly at its open. Set 0.01 to
 require a strictly higher close.
 RE-MEASURED UNDER Slope_Form = 2 (B2 + B2b, 2026-08-12). The
 findings below SUPERSEDE the v1.16.0/v1.17.0 numbers, which
 were taken on a population overlapping this one by 28 trades
 out of 118.

 THE WHOLE MODULE IS WORTH ONE TRADE. Gap_Filter_On = 0 returns
 exactly the unfiltered 187 / 1,494,400, and so does any
 Gap_Scope_Bars <= 2. The gross-profit column proves what the
 one blocked trade was: at 187 and 186 trades gross profit is
 IDENTICAL while gross loss falls 27,600, so the filter removes
 a pure loser of exactly that size -- and nothing else.

 WHY SO LITTLE IS LEFT. The gap filter exists to block the
 session's first bar after a down gap. Under Slope_Form = 2 the
 elapsed-time divisor already drives session-first-bar entries
 to ZERO (Slope_Form = 1 had 8, worth -54,800). The filter has
 almost nothing left to block; the one trade it does catch
 enters on the session's THIRD bar, which is why Gap_Scope_Bars
 must be 3. The gap contamination was solved by the formula,
 not by this module.

 PARAMETER CHOICES, each on a flat band:
   Gap_Down_Min_Pct  0.0 and 0.1 identical, 0.2+ inert. Took
     0.1 because 0.0 is a degenerate boundary -- the test
     "<= -0.00" fires on any non-positive gap, which is the
     parameter switched off.
   Gap_Rise_Min_Pct  0.1 / 0.2 / 0.3 identical, 0.0 and 0.4
     both change it. Took the centre of the flat band.
   Gap_Scope_Bars    only 3 does anything. Forced.
   Gap_Day_On        must be 1; the blocked trade is a DAY
     trade.
   Gap_Night_On      INERT at the adopted cell -- 0 and 1 give
     identical results for every Gap_Rise_Min_Pct in the band.
     It has never blocked a losing night trade in 6.4 years,
     and the one time it acted it removed a +6,000 WINNER (at
     Gap_Rise_Min_Pct = 0.0, which is outside the adopted
     band). Held at 1 anyway: turning it off on one trade is
     the same n=1 fitting this file warns about elsewhere, and
     the author ruled on 2026-08-08 that night must be handled
     symmetrically. Inert register, cut when simplifying.

 EVIDENCE GRADE: n = 1. This is a 27,600 rounding correction
 on 1.5 million, NOT a validated module, and it must not be
 re-described as one later.
```

### 3.13  Group J2: First-Bar Shape Gate - v1.23.0

```text
 ===== Group J2: First-Bar Shape Gate - v1.23.0 =====

 A SECOND, INDEPENDENT gap rule. The v1.16.0 rule above asks one
 question about the session's first bar -- did it close above its
 own open, and by how much -- which uses only Open and Close and
 throws High and Low away. This one asks what SHAPE the bar was,
 which is where the wicks live, and a wick is the record of a
 price the market reached and then rejected.

 It is the first reader of v_KB_Type. That taxonomy has been
 computed since v1.16.0 and never consulted -- written 18 times,
 read zero.

 MEASURED OFFLINE 2026-08-15 on 3,669 session opens rebuilt from
 the 1-minute export -- NOT on the 180 trades, which are used to
 verify this rule and never to fit it.

 After a down gap of 0.10% or more, grouping the first bar by
 its wick and measuring only forward movement from that bar's
 CLOSE (so nothing is computed from the bar that defines the
 group -- the circularity trap):

   group              n     +1 bar    +2 bars   +3 bars
   long lower wick   263   -0.0252%  -0.0282%  -0.0449%
   long upper wick   230   +0.0129%  +0.0100%  +0.0073%
   no clear wick     238   +0.0017%  +0.0017%  +0.0117%
   (positive = price FELL = favourable to a short)

 Permutation test on the SINGLE pre-registered grouping, 5,000
 shuffles: p = 0.0010 / 0.0164 / 0.0070 at +1/+2/+3 bars, and
 0.1204 at +4. One hypothesis tested, not seventeen.

 The internal consistency is what makes it credible rather than
 a survivor of multiple comparisons: the OPPOSITE group runs the
 opposite way and is also significant, and the null group sits
 on zero. A long lower wick means the low was bought back, so a
 short entered just after it is entering against fresh demand.

 Gap_KB_Scope_Bars = 3 is set by where significance ENDS, not by
 matching the neighbouring Gap_Scope_Bars. Bar 4 returns 0.12.

 ADOPTED 2026-08-15: Gap_KB_Gate_On now defaults to 1. The rule
 is live and the anchor is UNCHANGED -- MC12 returns 180 trades
 / 2,328,800 / PF 1.9811257162 / DD -364,800 either way, because
 the sample holds no trade inside its window. This is forward
 protection, not a performance change, and the header records
 why that distinction is deliberate.

 Gap_KB_Group selects which wick class is blocked. Groups 2 and 3
 are not candidates for adoption -- they exist so the offline
 reconstruction can be falsified against MC12 in both directions,
 and so the null group can be run as a control.
   1  long lower wick   types  3, 4, 9, 10, 15
   2  long upper wick   types  5, 6, 11, 12, 16
   3  no clear wick     types  7, 8, 13, 14, 17
 Long-bodied bars (types 1 and 2) belong to NO group: the
 classifier assigns them on body alone without consulting wicks,
 so they were not in any tested group and must not be swept in
 here by a shape test.

 INDEPENDENT OF Gap_Filter_On BY DESIGN. The two rules must be
 measurable apart; chaining this one under the v1.16.0 master
 switch would make it impossible to tell which rule a result
 belongs to.
```

### 3.14  Group J3: Up-Gap Rule - v1.24.0

```text
 ===== Group J3: Up-Gap Rule - v1.24.0 =====

 EVERY GAP RULE IN THIS FILE SO FAR ONLY LOOKS AT DOWN GAPS.
 v1.16.0 and v1.23.0 both start "v_Sess_Gap_Pct <= -threshold".
 An up gap has never been examined by the strategy at all.

 The author's hypothesis, 2026-08-15: after an UP gap, a first
 bar that closes BELOW its open by X% is a session that opened
 high and was sold -- supply showing itself -- and a short
 should therefore be MORE willing to enter, not less.

 TWO MODES, because "should enter more" and "should block" are
 structurally different things and only one of them is a filter:

   Mode 1  RELAX. On an up-gap session whose first bar FELL by
           at least UpGap_Bar1_Pct, multiply the slope threshold
           by UpGap_Relax_Mult for the first UpGap_Scope_Bars
           bars, so death crosses that just missed the main gate
           are admitted. This ADDS entries.

   Mode 2  MIRROR FILTER. The symmetric counterpart of v1.16.0:
           on an up-gap session whose first bar ROSE by at least
           UpGap_Bar1_Pct, block. This REMOVES entries.

 MODE 1 IS A DIFFERENT CLASS OF CHANGE FROM EVERYTHING BEFORE
 IT. Every gap rule so far has been a filter -- it can only take
 trades away, and the worst case is lost profit. Mode 1 lowers
 an entry gate, so it admits crosses the strategy has never
 traded, and the worst case is unbounded. Treat its results with
 more suspicion than a filter's, and do not adopt it on a small
 net gain.

 Mode 1 only relaxes the RATE form (Slope_Form = 2). Form 1 is
 the frozen v1.18.0 anchor and is deliberately untouched.

 OFFLINE SAID THE OPPOSITE OF THE HYPOTHESIS, AND OFFLINE IS NOT
 THE JUDGE. Measured on 3,669 session opens, after an up gap a
 first bar falling 0.20% or more was followed by a RISE over the
 next bar (difference -0.0298%, permutation p = 0.032), and at
 0.30% the effect was larger (-0.0726%, p = 0.005) -- i.e. the
 mechanism reads as "the dip was bought", the same reading that
 v1.23.0's long-lower-wick group is built on. But that offline
 pipeline has already been caught with two bugs in one day, its
 thresholds were swept rather than pre-registered, and the whole
 point of this version is that MC12 decides. The prediction is
 recorded here so it can be wrong in public.
```

### 3.15  Session boundaries. Bars are stamped at their CLOSE time, so the

```text
 Session boundaries. Bars are stamped at their CLOSE time, so the
 first day bar carries 0850 and the first night bar 1505 on a
 5-minute chart. The tests below are written as open-lower /
 closed-upper so they hold for any bar interval, and the night
 test is an OR because that session spans midnight (MC 24hr rule).
```

### 3.16  v1.17.0 ITEM A -- session LAST-bar entry block. ON.

```text
 v1.17.0 ITEM A -- session LAST-bar entry block. ON.

 The gap filter protects the session's first bar from the
 SIGNAL side (Gap_Scope_Bars). This protects it from the FILL
 side. A signal on the last bar of a session fills on the first
 bar of the next one, straight into the opening gap, and by
 then v_Gap_Block is a bar too late to withdraw the order.
 Both entry paths carry it -- death cross and re-entry alike.

 Expected in-sample effect: ZERO. No signal timestamp is 1345
 and no fill timestamp is 0850 or 1505 across all 119 trades.
 A bit-identical result is the acceptance test, not a
 disappointment -- this guards a path that has not been taken.

 FAILS OPEN ON IRREGULAR SESSIONS. The first bar is detected by
 transition and needs no timestamp; the LAST bar cannot be, so
 this compares against Sess_Day_End / Sess_Night_End. An
 unscheduled early close whose final bar carries a different
 stamp is not covered. Settlement days and registered holidays
 are already blocked upstream.
```

### 3.17  Group K: K-bar classification - v1.16.0 (RECORD ONLY)

```text
 ===== Group K: K-bar classification - v1.16.0 (RECORD ONLY) =====
 Thresholds for the 18-type taxonomy in Section 4.5. Nothing in
 the entry or exit chain reads v_KB_Type yet -- it is computed and
 held so the type can be exported and validated against 5-minute
 bar data before any rule depends on it.
```

### 3.18  Group L: Re-Entry gates - v1.17.0 (ALL DEFAULT ON)

```text
 ===== Group L: Re-Entry gates - v1.17.0 (ALL DEFAULT ON) =====
  The re-entry leg has carried three conditions since v1.6.x and
  not one of them has ever been measured on its own, because none
  had a switch. These four inputs exist to make that measurable.
  Every default is the CURRENT behaviour, so the whole group is
  inert until one is flipped and the anchor must be unaffected.

  WHY THESE FOUR
    ReEntry_On             v1.6   whole-leg degenerate anchor
    ReEntry_Structure_Gate v1.6   v_ZLEMA_Fast < v_ZLEMA_Slow
    ReEntry_Slope_Gate     v1.6.1 v_Slope > MinSlope
    ReEntry_Close_Gate     v1.6.2 Close >= v_ReEntry_Price

  WHAT IS ALREADY KNOWN (v1.16.0 population, 119 trades)
    11 re-entries, +648,000 -- but +565,600 of it is one trade.
    Excluding each leg's own best trade, re-entry averages +8,240
    against the death cross path's +12,913. The leg's edge is not
    established.
    Chains form because v_ReEntry_Price = v_Last_EntryPrice, so a
    chain re-enters at its parent's price. Blocking a parent
    removes the whole chain -- measured at run 0b, where blocking
    every session first bar removed 3 re-entries worth +158,000.
    The longest chain observed is 3 (2026-07-17, all at 44,181).
    ReEntry_Max_Chain is deliberately NOT added (user ruling).

  SCOPE OF WHAT A MEASUREMENT CAN SETTLE
    The 2026-08-08 ruling is that re-entry is a DESIGN question --
    it exists so the original entry condition is honoured rather
    than abandoned on a washout. A weak measured edge therefore
    does not by itself remove the mechanism. Cross-strategy prior:
    L1_TrendLong shipped re-entry and withdrew it after an MC9 A/B
    test at -920,000. Recorded, not acted on.
```

### 3.19  Group M: Slope form - v1.20.0

```text
 ===== Group M: Slope form - v1.20.0 =====
 Slope_Form
   1  Fast[1] - Fast > MinSlope        v1.18.0, the anchor
   2  the rate form below              v1.20.0

 v1.19.2's percentage form is gone. Four independent layers
 closed it -- the cost-unit mechanism, the six-formulation
 bench, the 2x2, and a 26-cell sweep in which no cell beat the
 points form on net and profit factor together. It is recoverable
 from git if it is ever reopened.
```

### 3.20  MinSlope_Rate -- the threshold for Slope_Form = 2.

```text
 MinSlope_Rate -- the threshold for Slope_Form = 2.

     ( Close[1] - Close ) / Close / elapsed minutes  * 100

 decline in points, divided by the index level so the gate means
 the same thing at 10,000 and at 45,000, divided by the time the
 decline actually took.

 ISO-COUNT CALIBRATED: 0.058027 admits the same 127 death
 crosses that MinSlope = 28 admits, so the two forms are
 compared at equal selectivity rather than equal looseness.
 Solved on a rebuild validated against the v1.19.0 bench record
 -- 7,778 crosses against 7,779, and 127 passes against 127.

 The time term is the MEASURED elapsed time, not BarInterval. At
 a session's first bar it is 230 or 80 minutes rather than 5, so
 an overnight gap is divided by up to 46x more and drops out of
 the ranking on its own. Measured: of the top 127 by this
 formula, ZERO are session first bars, against 63 of 127 when
 the time term is left out.
```

### 3.21  Slope_Require_Adjacent -- the dx fix.

```text
 Slope_Require_Adjacent -- the dx fix.

 v1.19.2 implements this by MEASURED ELAPSED TIME rather than by
 "is this bar number 1 of the session". Measured between
 consecutive bars: 5 minutes inside a session, 230 across the
 night close to the day open, 80 across the day close to the
 night open, longer across a weekend or a holiday. dy accumulates
 over all of it while dx is counted as one bar either way, so the
 slope on that bar is inflated.

 EXCLUSION, NOT RESCALING. Dividing by 230 would assert that the
 market fell gradually across 230 minutes. It did not -- there
 were no trades in that interval at all. The quantity is
 UNDEFINED there, not compressed.

 WHY ELAPSED TIME AND NOT THE BAR ORDINAL. The elapsed test is
 strictly more general: it also catches the Monday open, a
 post-holiday open, and any mid-session data gap or unscheduled
 halt, none of which a session-ordinal test can see.

 Measured on 7,779 death crosses: session first bars are 1.85% of
 the pool but 15.7% of everything that passes MinSlope = 28, an
 8.5x excess. Their median slope is 9.35 against 2.34 elsewhere.
 The excess GROWS as the form becomes more scale-neutral --
 22.0% at percent, 44.9% at ATR, 41.7% at z-score -- because
 those denominators are taken from recent intraday movement,
 which is small, while the numerator carries an overnight jump,
 which is not.

 Ships FALSE so the degenerate anchor is v1.18.0 exactly.

 THE COST IS ALREADY KNOWN, ROUGHLY. On the v1.18.0 trade list
 the 8 trades whose signal sits on a session first bar are worth
 -54,800 by themselves, so removing them looks like a GAIN. But
 v1.16.0's run 0b, which blocked every session first bar, lost
 about 103,200 net, because it also removed 3 downstream
 re-entries worth +158,000 -- v_ReEntry_Price chains to its
 parent entry price, so blocking a parent deletes its chain.
 EXPECT A NET LOSS NEAR 103,200 AND A SHARPE GAIN NEAR 0.036. If
 the run disagrees, the elapsed-time test is selecting a
 different set from the ordinal test and that difference must be
 explained before anything is adopted.
```

### 3.22  SECTION 2.5 - SWITCH DECODE

```text
============================================================
SECTION 2.5 - SWITCH DECODE
Added v1.21.0.

WHY THIS SECTION EXISTS. MC12's optimizer enumerates numeric
inputs only; a TrueFalse input never appears in the optimization
list at all. Batches B1 and B2 silently ran WITHOUT their on/off
switches for exactly this reason -- each report carried three
parameter columns, not the six and four that were specified.
Those switches were not held at their defaults by choice; they
were excluded.

So every switch a batch needs to sweep is now a numeric input
taking 0 or 1, decoded here into a boolean mirror. The entry and
exit blocks are unchanged apart from the identifier: they still
compare against True and False, so the three "= False or" gates
in the re-entry chain keep their exact meaning. Rewriting those
in place as "= 0" would have inverted them on any careless pass,
and inverted them silently.

CONVENTION: 0 = off, 1 = on. Anything non-zero counts as on, so
an out-of-range optimizer value degrades to on rather than to
something undefined.

Manual_Kill_Switch is deliberately NOT converted. It is an
operational control a human flips under pressure, where a
True/False dropdown is unambiguous and 1/0 is not. It sits on
the do-not-optimize list, so it never needs sweeping.
============================================================
```

### 3.23  SECTION 3 - PRIORITY 0 COMPLIANCE CHECKS

```text
============================================================
SECTION 3 - PRIORITY 0 COMPLIANCE CHECKS
(Rule #11 registry + kill + holiday + settlement)
v1.0.1-HOLIDAY (2026-07-16): HolidayFlat_v3 registry patched in.
Registry synced with L1-L5 / S1 / S3_S (63 entries 2019-2027).
Rebuild from TAIFEX calendar before Registry_Valid_Until reached.
============================================================

---- Holiday Registry init (once on first bar) ----
```

### 3.24  SECTION 4 - INDICATORS (ZLEMA)

```text
============================================================
SECTION 4 - INDICATORS (ZLEMA)
ZLEMA formula: EMA(2*Price - Price[lag], N)
lag = int((N-1) / 2)
============================================================
```

### 3.25  SECTION 4.5 - SESSION BOUNDARY, OPENING GAP, K-BAR TYPE

```text
============================================================
SECTION 4.5 - SESSION BOUNDARY, OPENING GAP, K-BAR TYPE
Added v1.16.0. Everything here is pure measurement plus one
boolean verdict (v_Gap_Block). With Gap_Filter_On = False the
verdict is always False and the strategy is bit-identical to
v1.15.0.

------------------------------------------------------------
SIGNAL / FILL OFFSET RULE  (repo-wide, established 2026-08-08)
------------------------------------------------------------
Every entry order in this file is a NEXT BAR order: a signal
evaluated on bar N produces a fill on bar N+1. An order placed
on bar N CANNOT be withdrawn on bar N+1, so any rule intended
to prevent a fill must be evaluated one bar EARLIER than the
bar it protects.

Therefore every time or bar-count input must state, in its own
comment, whether it names the SIGNAL bar or the FILL bar.

Compliance in this file:
Gap_Scope_Bars        COMPLIANT - names signal bars, and the
                      resulting fill bars are stated in Group J.
Sess_LastBar_Block_On COMPLIANT (v1.17.0) - it is the fill-side
                      twin of Gap_Scope_Bars. Gap_Scope_Bars
                      stops a session first bar from SIGNALLING;
                      this stops a session last bar from
                      signalling, which is what would put a FILL
                      on the next session's first bar. The pair
                      is what makes the offset rule enforced in
                      both directions rather than just one.
Tail_NoEntry_From     COMPLIANT (v1.18.0) - it names the FILL
                      side outright: no position may be opened
                      from this wall-clock time onwards. The
                      signal cutoff is derived from it in
                      Section 4.5 and is not separately
                      settable, so the two can no longer drift.
                      The derivation uses the STRICTER of the
                      two order types, which is what closes the
                      last hole in this list -- a single shared
                      comparison could satisfy the market path
                      or the stop path but never both, because
                      they fill at different wall-clock times.
                      Predecessors, for the record: v1.16.0
                      marked Tail_LastEntry_Time NOT COMPLIANT
                      and v1.17.0 offered Tail_FillSemantic_On
                      to flip <= for <. Both aimed at the
                      operator; the defect was that 430 had no
                      derivation to be an operator ON.

With this entry the offset rule is enforced on every time and
bar-count input in the file. Any input added later must state
its side in its own comment, as above.

------------------------------------------------------------
BAR DIRECTION IS NEVER NAMED BY COLOUR
------------------------------------------------------------
Taiwan charting draws a RISING bar in one colour and a FALLING
bar in another, and the Western / MultiCharts defaults are the
exact reverse. Chart colours are also user-configurable. To make
misreading impossible, no identifier or comment in this file
names a colour. Direction is stated arithmetically only.
============================================================

---- Which session is this bar in ----------------------------
Bars are stamped at their CLOSE, so the first day bar is 0850
and the first night bar 1505 on a 5-minute chart. Using
open-lower / closed-upper keeps this correct at any interval.
The night test is an OR because the session crosses midnight
(memory rule: MC 24hr pitfall). ----------------------------
```

### 3.26  ---- First bar of a session ----------------------------------

```text
---- First bar of a session ----------------------------------
Detected as a transition into the session rather than by a
hard-coded stamp. A hard-coded stamp fails silently when the
open is delayed, and a protective filter that fails open is
worse than no filter. CurrentBar > 1 guards the [1] reference.
```

### 3.27  ---- Last bar of a session (v1.17.0, ITEM A) -----------------

```text
---- Last bar of a session (v1.17.0, ITEM A) -----------------
The first bar above is found by TRANSITION, which needs no
timestamp and so cannot be fooled by a delayed open. The last
bar cannot be found that way: knowing a bar is the last one
requires seeing the next one, which is a future reference.
So this compares against the session end stamps, and the
limitation is stated rather than hidden -- an unscheduled early
close whose final bar carries a different stamp is NOT caught
and this guard fails open there.

Why the guard is needed at all: a signal on the day session's
last bar (1345) passes the entry time gate through its
Time > 500 clause, and the resulting next-bar order fills at
1505 -- the first bar of the night session, inside the opening
gap. v_Gap_Block is computed correctly on that 1505 bar but the
order was already placed, and per the offset rule above it
cannot be withdrawn.

The night session's last bar (0500) is already blocked today,
incidentally, because the tail cutoff derived in Section 4.5
stops signals after 0420. That is a coincidence of the current
Tail_NoEntry_From value, not a guarantee, so both sessions are
handled here and this guard does not depend on where the tail
cutoff happens to land. -------------------------------------
```

### 3.28  ---- Latch the gap and the opening bar OHLC ------------------

```text
---- Latch the gap and the opening bar OHLC ------------------
On the session first bar, Open[1] and Close[1] are the open and
close of the LAST BAR OF THE PREVIOUS SESSION. Both are kept:
the close defines the gap, and the pair defines whether that
final bar was itself advancing or declining, which the gap size
alone cannot express (a down gap after a declining bar is a
continuation; after an advancing bar it is a reversal). The
direction is recorded now and read by nothing yet. ----------
```

### 3.29  ---- K-bar taxonomy of the session opening bar (RECORD ONLY) --

```text
---- K-bar taxonomy of the session opening bar (RECORD ONLY) --
18 mutually exclusive and collectively exhaustive types.
Normalised by the bar range R = High - Low:
  body + upper shadow + lower shadow == 1  (identity, exact)
so the shape is one point on a 2-simplex plus a direction bit.
The tree below partitions body over [0,1] and then partitions
the shadow ratio, hence every bar maps to exactly one type.
Verified over 3,197 TAIFEX sessions: 3,197 classified, no gaps,
no overlaps.

 0  no range              1  long body up     2  long body down
 3  mid  lower-shadow up  4  mid  lower-shadow down
 5  mid  upper-shadow up  6  mid  upper-shadow down
 7  mid  balanced up      8  mid  balanced down
 9  small lower-shadow up 10 small lower-shadow down (hammer pair)
11  small upper-shadow up 12 small upper-shadow down (star pair)
13  small balanced up     14 small balanced down
15  doji lower-shadow     16 doji upper-shadow      17 doji balanced

All functions used here are scalar (AbsValue / MaxList /
MinList), not series functions, so evaluating them inside a
conditional is safe -- unlike the A-3 finding on Lowest(RSI()).
-----------------------------------------------------------
```

### 3.30  ---- Gap filter verdict --------------------------------------

```text
---- Gap filter verdict --------------------------------------
Recomputed every bar so it cannot latch True and leak into a
later bar of the session. Blocks only while the bar ordinal is
inside the scope window, only in an enabled session, only after
a down gap of at least Gap_Down_Min_Pct, and only when the
opening bar advanced by at least Gap_Rise_Min_Pct.

Gap_Down_Min_Pct is a stability floor, not a tuned value: the
rise is compared against the bar's own open, but a near-zero
gap would still admit noise-sized recoveries as blocks. The
0.10-0.50 band tested identically on the 17 known cases.
-----------------------------------------------------------
```

### 3.31  ---- v1.23.0: the first-bar SHAPE gate -----------------------

```text
---- v1.23.0: the first-bar SHAPE gate -----------------------
Reads v_KB_Type, which Section 4.5 assigns once per session on
the first bar and which then holds for the rest of that session
-- so a bar-2 or bar-3 entry is judged on the shape of the bar
that OPENED the session, which is the quantity that was measured.
v_Sess_Gap_Pct is retained the same way.

Membership is written out as explicit type numbers rather than
re-deriving the wick test, because the classifier decides long-
bodied bars (types 1 and 2) on body alone before it ever looks at
a wick. Re-testing the wick here would pull those bars into the
group, and they were not in the group that was measured.

Type 0 (a bar with no range at all, 2 occurrences in 3,669) falls
into no group, which is correct -- it carries no shape.

This block only ever SETS the verdict true. It cannot un-block
what the v1.16.0 rule blocked, so the two rules compose as an OR
and each can be measured with the other switched off.
```

### 3.32  ---- v1.24.0: the UP-gap rule ---------------------------------

```text
---- v1.24.0: the UP-gap rule ---------------------------------
Placed here, in Section 4.5, because v_Sess_Gap_Pct and
v_First_Rise_Pct are assigned a few lines above on the session's
first bar and then held for the rest of the session. Section 5,
where the slope gate lives, runs AFTER this -- so Mode 1 can hand
the slope gate a modified threshold on the same bar, with no
look-back and no ordering hazard.

v_First_Rise_Pct is ( Close - Open ) / Open on the FIRST bar, so
a fall is simply its negation. Mode 1 tests the fall, Mode 2 the
rise; they are the two sides of the same measurement.

Mode 2 writes v_Gap_Block, joining the two existing gap rules as
an OR. Mode 1 writes only v_UpGap_Relax and touches nothing here
-- the relaxation itself happens at the slope gate.
```

### 3.33  ---- v1.17.0 ITEM A: fill-side twin of the gap filter ---------

```text
---- v1.17.0 ITEM A: fill-side twin of the gap filter ---------
Same shape as v_Gap_Block above -- a raw fact (v_Sess_LastBar)
measured in Section 4.5, then a switched verdict here, so the
measurement stays available for diagnostics even when the guard
is turned off. With Sess_LastBar_Block_On = False this is always
False and both entry paths behave exactly as v1.16.0. -------
```

### 3.34  ---- v1.18.0: DERIVE the signal cutoff from the entry rule -----

```text
---- v1.18.0: DERIVE the signal cutoff from the entry rule -----
The rule is one sentence: no position may be OPENED from
Tail_NoEntry_From onwards. The signal cutoff is not a second
decision, it is arithmetic on that sentence:

  cutoff = Tail_NoEntry_From - Tail_Signal_Lead_Bars bars

HHMM CANNOT BE SUBTRACTED DIRECTLY. 500 - 5 is 495, which is not
a time. Convert to minutes-since-midnight, subtract there, and
convert back. BarInterval carries the chart interval in minutes,
so the lead stays two BARS at any interval rather than a fixed
ten minutes that is only two bars on a 5-minute chart.

Recomputed every bar rather than latched: the inputs are
constant, so this costs two scalar calls and removes any
question about initialisation order.

The Time > 500 clause is unchanged from v1.3. It admits the day
session and the pre-midnight night bars; only post-midnight bars
are measured against the cutoff (MC 24hr pitfall rule).

RANGE NOTE. Tail_NoEntry_From must sit at least
Tail_Signal_Lead_Bars bars after midnight, otherwise the
subtraction wraps past 0000 and the cutoff lands in the previous
evening, where Time > 500 already admits everything. At 430 with
a 2-bar lead on a 5-minute chart the cutoff is 0420, far from
that boundary.

BarInterval NOTE. This trusts BarInterval to report the chart
interval in minutes, which holds for the minute charts this
strategy runs on -- a single 5-minute Data1, as the whole file
assumes elsewhere (MaxBarsBack, ML_ATR_LongLen = 90). On a chart
where BarInterval does not mean minutes the lead collapses
toward zero and the cutoff drifts LATE, i.e. this guard fails
OPEN. Confirm the cutoff after any chart change: at 5 minutes
with the shipped inputs it must read 420.

HOLIDAY INTERACTION. None. Holiday_Flat_Time (415) sits between
this cutoff and Tail_NoEntry_From, but v_Holiday_Block gates
both entry paths for the whole day, so no entry can occur on a
holiday-tail day at any time. -------------------------------
```

### 3.35  ---- v1.22.0: the day session's own cutoff ----

```text
---- v1.22.0: the day session's own cutoff ----
Derived from Tail_DayNoEntry_From exactly as the night cutoff is
derived from Tail_NoEntry_From, using the same lead. Same rule,
different anchor.
 1335 - 2 bars = 1325, so the last fill bar is 1330 and nothing
 can be opened at 1335, 1340, 1345 or 1505.
```

### 3.36  ---- v1.22.0: each session states its own rule ----

```text
---- v1.22.0: each session states its own rule ----
Through v1.21.0 this was

  ( Time <= v_Tail_Cutoff or Time > 500 )

and EVERY day bar satisfies Time > 500, so the second clause
admitted the whole day session and Tail_NoEntry_From governed only
the post-midnight window. The day side was protected solely by
Sess_LastBar_Block_On, which is a side effect of a rule written for
the fill-side gap problem, not a decision anyone made.

The Time > 500 clause is retained but moved INSIDE the night
branch, where it does what it was written for: admit the
pre-midnight night bars, which no post-midnight cutoff should
reach. It can no longer leak day bars.

v_In_Day and v_In_Night are mutually exclusive (Section 4.5), so
exactly one branch decides any given bar.
```

### 3.37  SECTION 5 - CROSS DETECTION

```text
============================================================
SECTION 5 - CROSS DETECTION
Death cross: Fast crosses BELOW Slow (short entry signal).
Golden cross: Fast crosses ABOVE Slow (main exit signal).
============================================================
```

### 3.38  SECTION 5.5 - RE-ENTRY STATE MANAGEMENT (v1.6)

```text
============================================================
SECTION 5.5 - RE-ENTRY STATE MANAGEMENT (v1.6)
After exit, if bearish structure (Fast < Slow) still intact,
allow re-entry via stop order at the original entry price.
Arms when position exits (v_Prev_MP -1 -> MP 0).
Resets on golden cross, bearish structure lost, or new death cross.
============================================================
```

### 3.39  SECTION 7 - FROZEN SL SETUP + SetStopContract + SetStopLoss + SL_Pct (Rule #12)

```text
============================================================
SECTION 7 - FROZEN SL SETUP + SetStopContract + SetStopLoss + SL_Pct (Rule #12)
Lock SL distance on entry bar. Reset when flat.
============================================================
```

### 3.40  Rule #12 SetStopContract + SetStopLoss + SL_Pct (short variant: MP >= 0 guard).

```text
Rule #12 SetStopContract + SetStopLoss + SL_Pct (short variant: MP >= 0 guard).
v1.5: SetStopContract makes SetStopLoss amount PER-CONTRACT (lot-invariant).
     SL_Pct caps engine stop distance as pct of Close.
v_Guard_Distance computed EVERY BAR (current ATR, not frozen) to avoid
SetStopLoss(0) when flat -- SetStopContract + SetStopLoss(0) = immediate stop.
```

### 3.41  SECTION 8 - M6 MULTI-LAYER INDICATOR PRECOMPUTE

```text
============================================================
SECTION 8 - M6 MULTI-LAYER INDICATOR PRECOMPUTE
5 categories, 1 factor each. Lightweight by design.
============================================================
```

### 3.42  SECTION 8.5 - SLOPE AS dy/dx (v1.19.1)

```text
============================================================
SECTION 8.5 - SLOPE AS dy/dx (v1.19.1)

Produces exactly one boolean for the momentum test
(v_Slope_Pass) and one for the dx guard (v_FirstBar_Block).
Both entry paths read those two and nothing else, so a form
cannot apply to the death cross and not to the re-entry.

Placed after Section 8 because it must be ready before
Section 9; it depends only on v_Slope and v_Bars_In_Sess,
both of which are computed in Section 4.5.
============================================================

---- dx: minutes actually elapsed between bar [1] and bar [0] ----
The user's statement of the formula is
  slope = ( change in points / index level ) / TIME
and the third term is the time OF THE CHANGE: A time minus B
time. Not the chart's interval setting, which is a constant and
therefore carries no information.

Negative across midnight, so add a day. CurrentBar > 1 because
Time[1] does not exist on the first bar of the run.
```

### 3.43  ---- is this a legitimate measurement at all ----

```text
---- is this a legitimate measurement at all ----
A slope is only defined over an interval the market was open
for. Measured elapsed time between consecutive bars:

  inside a session                 5 minutes
  0500 night close -> 0850         230 minutes
  1345 day close   -> 1505         80 minutes
  Friday 0500      -> Monday 0850  longer still

dx IS USED AS A VALIDITY TEST, NOT AS A DIVISOR. Dividing by 230
would assert that the market fell gradually over 230 minutes. It
did not -- there were no trades in that interval at all. The
quantity is UNDEFINED there, not compressed, so the bar is not
measured.

Because the test forces dx = BarInterval whenever it passes,
dividing by dx afterwards would be dividing by a constant. That
is why the formula below carries no /time term: the time is in
the gate, not in the value.

This test is strictly more general than "block bar 1 of the
session": it also catches post-holiday opens, the Monday open,
and any mid-session data gap or unscheduled halt.
BarInterval GUARD, restored 2026-08-11. v1.19.1 carried
"BarInterval > 0" because it divided by it; v1.19.2 dropped the
division and the guard went with it, which was a regression. On a
chart where BarInterval does not report minutes the comparison
below can never be true, so with the switch ON every entry is
blocked. That direction is safe but SILENT, and the same file
already warns about BarInterval for Tail_Signal_Lead_Bars -- the
two must be consistent. Guarded here so the failure is a hard
False rather than an accident of arithmetic.
```

### 3.44  ---- Slope_Form = 2 : the rate form --------------------------

```text
---- Slope_Form = 2 : the rate form --------------------------
( Close[1] - Close ) / Close / elapsed minutes, times 100.

Positive value = price FELL, same sign convention as v_Slope.

Every term is what it says: the numerator is the market bar's own
decline in points, Close normalises it to a percentage so the gate
carries across index levels, and v_Elapsed_Min is the time that
decline actually took.

Guards: Close is a futures price and cannot be zero in practice,
but v_Elapsed_Min IS zero on the first bar of the run by
construction.
```

### 3.45  ---- v1.24.0: the effective rate threshold ----

```text
---- v1.24.0: the effective rate threshold ----
Identical to MinSlope_Rate unless Section 4.5 armed the up-gap
relaxation, so with UpGap_Gate_On = 0 this line is a copy and the
comparison below is unchanged to the bit.

Only the RATE form is relaxed. Form 1 is the frozen v1.18.0
anchor; letting an up-gap rule reach into it would make that
anchor unreproducible.
```

### 3.46  ---- which form gates the entry ----

```text
---- which form gates the entry ----
Anything other than 2 falls through to form 1, so an out-of-range
input degrades to v1.18.0 rather than to something undefined. Both
comparisons are strict > , matching v1.18.0's "v_Slope > MinSlope"
exactly, so form 1 is bit identical rather than merely equivalent.
```

### 3.47  ---- the dx guard, as an entry block ----

```text
---- the dx guard, as an entry block ----
Independent of Slope_Form on purpose. Tying them together would
confound "points versus percent" with "contaminated versus
clean", which is the exact confound this file exists to
separate. Cell 3 of the 2x2 (percent, guard off) is a DIAGNOSTIC
ONLY and must never be shipped.
```

### 3.48  SECTION 9 - ENTRY (Death Cross + M1 Slope + Rule #11 gates)

```text
============================================================
SECTION 9 - ENTRY (Death Cross + M1 Slope + Rule #11 gates)
============================================================

v1.3: tail entry cutoff - allow evening/night entries up to the
LastEntry signal bar; block only the final pre-close window.
v1.17.0: the raw time test is now v_Tail_Entry_OK (Item C), and
v_Sess_LastBar_Block is added as the fill-side twin of
v_Gap_Block (Item A). The two Block flags sit together on
purpose: one stops a signal ON the session's first bar, the
other stops a signal that would FILL on it.
```

### 3.49  v1.6 Re-Entry: washout recovery via stop order at original entry price.

```text
v1.6 Re-Entry: washout recovery via stop order at original entry price.
Price must DROP to the level (stop order for short = trigger on price <= level).
v1.6.1: added v_Slope > MinSlope gate (same as main entry) to require
active bearish momentum before re-entry, not just structure.
v1.6.2: added Close >= v_ReEntry_Price gate to enforce directional entry --
stop order only placed when current bar closes at/above the re-entry level,
so the next bar must FALL to it (price descending through the level).

v1.17.0: carries the SAME two changes as the death cross path above.
This matters more here, not less. A stop order is WORKING through the
whole of the next bar rather than filling at its open, so a re-entry
armed on a session's last bar sits live across the entire opening bar
of the next session and any wick through v_ReEntry_Price fills it --
precisely the gap the filter was written to avoid. The two entry paths
are kept condition-for-condition identical on every protective gate so
that a rule can never be true of one and false of the other.
v1.17.0: the three v1.6.x conditions are now each behind a switch.
With every switch True, "( Switch = False or Cond )" reduces to Cond,
so this block is logically identical to v1.16.0 and the anchor must
reproduce 119 / 3,141,200 / PF 2.065681 bit for bit.
```

### 3.50  SECTION 10 - EXIT PRIORITY CHAIN (P0 to P7)

```text
============================================================
SECTION 10 - EXIT PRIORITY CHAIN (P0 to P7)
Fires in order. First hit wins per bar (ExitFired flag).
============================================================
```

### 3.51  ---- P0.5: Tail Force Exit (v1.3) - flat before session close ----

```text
 ---- P0.5: Tail Force Exit (v1.3) - flat before session close ----
 Signal at 0440 bar close -> fill 04:40 (445-bar open).
 Guarantees no position ever crosses morning break / weekend /
 holiday closure. Holiday flat at 0415 fires earlier as backstop
 on registered holiday tails. Required BEFORE any G2 MaxHold
 extension experiment (36/48 bars breaks 2hr self-resolution).
```

### 3.52  ---- P3: M7 True Breakeven + P3b Profit Trail (v1.12.0) ----

```text
 ---- P3: M7 True Breakeven + P3b Profit Trail (v1.12.0) ----
 Both mechanisms produce a protective lock in POINTS. The larger
 lock wins, and a single stop order is issued at
     EntryPrice - lock
 For a SHORT a bigger lock = lower price level = triggers earlier
 on the retrace = more profit retained. BE_Cost_Pts is the floor,
 so the trail can never protect less than true breakeven.
 Re-issued every bar, ExitFired NOT set (same pattern as P6).

 A-5 (audit 2026-08-06) -- PROGRAM ORDER IS NOT FILL ORDER.
 P3 sits above P4/P5 in the chain but does not set ExitFired, so a
 market order from GoldenCross or TimeStop can be live for the same
 next bar as this stop. Fill order is decided by order type:
     market order -> fills at the NEXT BAR'S OPEN
     stop order   -> fills intrabar when price touches the level
 The open comes first, so when both are issued on the same bar the
 MARKET ORDER WINS and P5 overrides P3. That is precisely why the
 25 TimeStop exits survive rather than being taken by this stop.

 Where this stop DOES preempt is ACROSS bars: issued on bar N, it
 can fill intrabar on bar N+1, ahead of the QuickStop_Time market
 order that is only evaluated at bar N+1's CLOSE. That is the case
 the original comment described, and it is only half the picture.

 Track running peak open profit (bar-close basis, IOG=False)
```

### 3.53  v1.14.0 B1 tiered giveback. One tier, two parameters -- with

```text
     v1.14.0 B1 tiered giveback. One tier, two parameters -- with
      only 21 armed trades in 6.4 years a multi-tier table would fit
      noise. Tier2_On=False reproduces v1.13.0 exactly.

      The rationale is the user's own: giving back 80% of a 1.2% run
      costs 1% of the index, but giving back 80% of a 5% run costs
      4%. It is the LARGE profits that must not be handed back, and
      a single flat giveback pct cannot express that.
```

### 3.54  v1.13.0 A2 structure leg.

```text
 v1.13.0 A2 structure leg.

  A-1 (audit 2026-08-06) -- WHAT THIS ACTUALLY COMPUTES.
  The name says "structure trail" and the design doc describes
  trailing behind a swing high. The algebra says otherwise.

  For a SHORT, profit at any bar is EntryPrice - Close, so a HIGHER
  close means LESS profit. Highest(Close, N) therefore picks the
  LEAST profitable bar in the window, and

      v_Struct_Raw = (minimum close-based profit in the window)
                     - Struct_Buffer_Pts

  And the window barely rolls: it is clamped to bars-since-entry
  while MaxHoldingBars is 24 and Struct_Lookback is 20, so the first
  bar only leaves the window on bar 20 of a trade that can live 24.

  So the real mechanism is A LOWEST-PROFIT-SINCE-ENTRY TRAIL, not a
  swing-high trail. Three independent measurements agree:
    - Lookback 25/30/35/40 are provably identical (all clamped)
    - Lookback 5/10/15, the ones that genuinely roll, score WORSE
    - Struct_Trigger_Pct=0 collapses net 48%, because on the entry
      bar the window is one bar and the reference is that bar's own
      close, making the lock equal current profit minus buffer

  DO NOT shrink Struct_Lookback expecting a more responsive
  structure read. It anchors the lock to a more recent, higher
  profit and produces a TIGHTER stop.

  Reference = highest close of the recent window. For a SHORT the
  protected amount is the distance from EntryPrice down to that
  close plus a buffer. Falling price rolls old closes out of the
  window, so the reference drops and the lock grows.

  Window is clamped to bars elapsed since entry: without this the
  lookback reaches back into price structure that predates the trade
  and has nothing to do with it.

  LATCH is mandatory. A bounce entering the window raises the
  reference, which would shrink the raw lock and retreat the stop.
  A trailing stop that retreats is not a trailing stop, so the lock
  is held at its running maximum and can only ever increase.
```

### 3.55  ---- P5: M8 Hold Cap -- v1.25.0 TWO FORMS ----

```text
 ---- P5: M8 Hold Cap -- v1.25.0 TWO FORMS ----
 Form 1 is the bar count that has been here since v0.5.
 Form 2 covers at a percentage profit target with a LIMIT order
 and KEEPS the bar count as a backstop. The backstop is not
 optional: a target alone can fail to fire for the whole session,
 and B5 measured what happens when this leg stops catching trades
 -- they get handed to GoldenCross at -215,200 over 19 trades.

 The limit order deliberately does NOT set ExitFired. It is
 conditional, so P6's ATR stop must stay armed underneath it:
 target above, stop below, which is the point.
```

---

## 4. Open items

1. **Mechanism unverified for v1.25.0 Form 2.** `SX_MA_TimeStop_Pct` must
   appear in the trade list and `SX_MA_GoldenCross` must fall from its 3
   trades / -79,200. Right net profit with the wrong mechanism is
   coincidence and the +258,400 would have to be withdrawn.
2. **`Struct_Lookback` is now unclamped.** The structure window is
   `MinList(Lookback, BarsSince+1)`; at a 24-bar cap anything above 25 was
   inert, and at 48 it is not. The "20 is optimal" finding is stale.
3. **`MaxHold_Pct` step-0.1 sweep queued.** Step 0.2 cannot tell a plateau
   from a spike.
4. **`QS_MaxLoss_Pct` re-sweep stopped at 0.50.** 0.25, the v1.7.1 optimum,
   was not literally re-tested. The trend is unambiguous but that part is
   inference, not a measured cell.
5. **Zero held-out data.** About 28,000 cells and 15 adoptions on one
   sample. Cross-period stability over nine windows, Rule #13 and Rule #18
   are all still outstanding.
