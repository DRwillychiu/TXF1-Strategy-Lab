"""共用模組單元測試（規則手冊 R7）：每個模組獨立驗輸入→輸出，含邊界。"""
from txfcore.config.loader import check_against_pla, load_strategy
from txfcore.modules.exits.core import (
    PeakGivebackShort, forced_exit, retrace_tp_short, time_exit, time_exit_raw, tp1_price_short,
)
from txfcore.modules.gates.basic import Cooldown, in_closed_window, in_window
from txfcore.modules.gates.loss_streak import SkipNextRun, StreakSkip
from txfcore.modules.signals.core import TrapZone, channel_breakdown, spring_trigger
from txfcore.modules.stops.core import (
    TwoBarArm, cap_short, engine_stop_distance, hard_stop_short, ratchet_lowest_low_short,
)


def test_configs_equal_pla_defaults():
    for key in ("L2_v5.11", "L4_v14.10"):
        assert check_against_pla(load_strategy(key)) == [], key


def test_engine_stop_distance_takes_tightest():
    assert engine_stop_distance(20500, 20000) == 500
    assert engine_stop_distance(20500, 20000, pct=1.25) == 250          # 1.25% × 20000
    assert engine_stop_distance(20500, 20000, pct=5, max_pts=450) == 450
    assert engine_stop_distance(19900, 20000) == 100                    # 錨點在下方也取絕對值


def test_cap_short_price_takes_lower():
    assert cap_short(50000, 40000, pct=0.8, max_pts=450) == 40320       # 0.8% 先綁
    assert cap_short(70000, 60000, pct=0.8, max_pts=450) == 60450       # 指數 ≥ 56,250 由 450 綁
    assert cap_short(40100, 40000, pct=0.8, max_pts=450) == 40100       # 原本就比上限緊
    assert hard_stop_short(40000, 450) == 40450


def test_ratchet_only_moves_down():
    assert ratchet_lowest_low_short(999999.0, 100, 10, 1.0) == 110
    assert ratchet_lowest_low_short(105, 100, 10, 1.0) == 105


def test_time_exit_zero_semantics():
    assert not time_exit(100, 0)                                        # L2：0 ＝ 關
    assert time_exit_raw(0, 0)                                          # L4：照 .pla，0 每根成立
    assert time_exit(60, 60) and not time_exit(59, 60)


def test_forced_exit_priority_and_times():
    assert forced_exit("CS", True, True, True, True, 1300, 415, 1230) == "CS_Kill"
    assert forced_exit("CS", False, True, True, True, 1300, 415, 1230) == "CS_RegistryEnd"
    assert forced_exit("CS", False, False, True, False, 400, 415, 1230) is None    # 未到 04:15
    assert forced_exit("CS", False, False, True, False, 415, 415, 1230) == "CS_Holiday"
    assert forced_exit("TS", False, False, False, True, 1245, 300, 1230) == "TS_Settlement"


def test_windows_edges():
    assert in_window(200, 200, 500) and not in_window(500, 200, 500)
    assert in_closed_window(1245, 845, 1245) and not in_closed_window(1345, 845, 1245)


def test_cooldown_counts_from_exit_bar():
    c = Cooldown()
    assert c.update(False, True) == 0          # 持倉中
    assert c.update(True, False) == 1          # 出場那根
    assert c.update(True, True) == 2


def test_trap_zone_lives_limit_bars():
    z = TrapZone()
    z.update(101, 100, 2); assert z.active and z.n == 1
    z.update(99, 100, 2); assert z.active and z.n == 2
    z.update(99, 100, 2); assert not z.active
    assert spring_trigger(95, 100, 10, 0.4) and not spring_trigger(96, 100, 10, 0.4)
    assert channel_breakdown(90, 100, 10, 0.45) and not channel_breakdown(96, 100, 10, 0.45)


def test_skip_next_run_skips_whole_run_then_resets():
    s = SkipNextRun()
    for tt in (1, 2, 3):                       # 三筆空頭單虧損
        s.count(tt, -1000.0 * tt, True, 3, 1, 1, tt)
    assert s.skip_left == 1
    assert s.allow(True, True, True) is False  # 這一段被跳過
    assert s.allow(True, True, True) is False  # 同一段仍跳過
    assert s.allow(False, True, True) is True  # 段落結束
    assert s.allow(True, True, True) is True   # 下一段可進場


def test_skip_ignores_uncounted_trades():
    s = SkipNextRun()
    for tt in (1, 2, 3):
        s.count(tt, -1000.0 * tt, False, 3, 1, 1, tt)   # 暴跌單不計
    assert s.skip_left == 0


def test_streak_skip_off_when_zero():
    s = StreakSkip()
    for tt in (1, 2, 3, 4):
        s.update(True, tt, -100.0 * tt, 1261001, 0)
    assert not s.consume()


def test_two_bar_arm_needs_consecutive_and_min_bars():
    a = TwoBarArm()
    a.update(True, 1, 3); a.update(True, 2, 3); assert not a.armed      # 未滿 3 根
    a.update(True, 3, 3); assert a.armed
    b = TwoBarArm()
    b.update(True, 5, 3); b.update(False, 6, 3); b.update(True, 7, 3); assert not b.armed


def test_profit_exits():
    pg = PeakGivebackShort()
    assert pg.update(20000, 19900, 150, 55) == 0                        # 未達門檻
    assert round(pg.update(20000, 19800, 150, 55), 6) == 19910          # 保留 45%
    assert tp1_price_short(20000, 19500, 20) == 19900
    assert tp1_price_short(20000, 0, 20) == 0                           # 沒有箱底
    assert retrace_tp_short(20000, 19000, 19300, 100, 4, 1.5)
    assert not retrace_tp_short(20000, 19700, 20000, 100, 4, 1.5)       # 波段不足 4 ATR


# ---- 2026-10-09 審查 M7 補：預設值沒走到的模組路徑 ----
from types import SimpleNamespace as NS

from txfcore.modules.gates.trend_filter import DailyMaBlock, WeeklySmaFilter
from txfcore.modules.signals.core import CloseInvalidatedBox, CrashLeg
from txfcore.modules.stops.core import LowestCloseTrail
from txfcore.types.bar import Series


def _series(vals):
    s = Series()
    for v in vals:
        s.push(v)
    return s


class _Bars(list):
    """bars[0] ＝ 最新一根，與 BarSeries 索引語意相同。"""
    def __getitem__(self, i):
        return list.__getitem__(self, len(self) - 1 - i)


def test_weekly_sma_filter_samples_friday_1245_only():
    f = WeeklySmaFilter(2)
    fri, sat = 1261009, 1261010           # 2026/10/9 週五
    def feed(prev_date, prev_time, close):
        f.update(_Bars([NS(mc_date=prev_date, mc_time=prev_time, close=close), NS(mc_date=prev_date, mc_time=1345, close=0)]))
    feed(fri, 1145, 100); assert f.count == 0          # 不是 12:45
    feed(sat, 1245, 100); assert f.count == 0          # 不是週五
    feed(fri, 1245, 100); assert f.count == 1 and not f.ok   # 暖機未滿
    feed(1261016, 1245, 90); assert f.ready and f.ok and f.sma == 95


def test_daily_ma_block_modes_and_f6():
    closes = _series([100.0] * 59 + [110.0])
    b = DailyMaBlock()
    first = b.update(closes, 20, 60, 0)          # 第一次：MA慢[1] ＝ 0 → A 成立
    assert first and b.slow_prev == 0
    assert b.update(closes, 20, 60, 0)           # 同一根日 K 再算：MA慢 ＝ MA慢[1]，A 仍成立（F6）
    assert b.update(closes, 20, 60, 3) is False  # mode 3 不封鎖
    assert b.update(closes, 20, 60, 2) == (closes[0] > b.slow)


def test_crash_leg_one_entry_per_leg_and_reset():
    c = CrashLeg()
    highs = _series([110.0] * 20)
    args = dict(lookback=20, drop_pct=3.0, body_atr=1.0, atr_pct_min=0.6,
                sl_pct=1.0, max_pts=450, leg_max=1)
    assert c.check(True, 100, 102, 1.0, highs, bar_no=1, **args)        # 跌 9%、實體 2 ≥ ATR
    assert not c.check(True, 100, 102, 1.0, highs, bar_no=2, **args)    # 同一腿第二次被擋
    c.update_leg(105, 3, 0); assert c.leg_active                        # 未回到腿高
    c.update_leg(110, 4, 0); assert not c.leg_active                    # 回到腿高 → 腿結束
    c2 = CrashLeg(); c2.check(True, 100, 102, 1.0, highs, bar_no=1, **args)
    c2.update_leg(105, 6, 5); assert not c2.leg_active                  # reset_bars ＝ 5 到期
    assert c2.dist == 1.0                                              # 1% × 100，小於 450


def test_close_invalidated_box_forms_and_breaks_on_close():
    def bars(rows):
        return NS(high=_series([r[0] for r in rows]), low=_series([r[1] for r in rows]),
                  close=_series([r[2] for r in rows]))
    hist = [(110, 90, 100)] * 15
    b = CloseInvalidatedBox()
    b.update(bars(hist + [(104, 96, 100)]), 15, 0.7); assert b.valid and b.top == 110
    b.update(bars(hist + [(112, 96, 111)]), 15, 0.7); assert not b.active   # 收盤離開箱子


def test_lowest_close_trail_compares_line_uses_line_plus_ratio():
    t = LowestCloseTrail()
    closes = _series([100.0, 98.0, 99.0])
    stop, src = t.active_stop(False, closes, 2, 1.0, 10, 1.1, 150)
    assert (stop, src) == (150, 2) and t.line == 0                      # 未啟動 → 用初始
    stop, src = t.active_stop(True, closes, 2, 1.0, 10, 1.1, 150)
    assert t.line == 108 and (stop, src) == (119, 1)                    # 線 108 < 150 → 用 線＋11


def test_streak_skip_counts_from_start_date():
    s = StreakSkip()
    s.update(True, 1, -100.0, 1261001, 2, 1261005)                      # 起算日前不計
    s.update(True, 2, -200.0, 1261006, 2, 1261005)
    s.update(True, 3, -300.0, 1261007, 2, 1261005)
    assert s.consume() and not s.consume()                              # 只跳一次
