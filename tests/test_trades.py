"""M2　交易統計層。每一條測試對應 `M2_TRADE_STATS.md` 的一項定案。"""
from __future__ import annotations

from datetime import date

import pytest

from txfcore.engine.accounting import ClosedTrade
from txfcore.instruments.spec import TMF, TXF
from txfcore.metrics.trades import (
    FLAT_EPS, Stats, by_direction, classify, compute, excursion, periodical, rows,
)
from txfcore.types.bar import Bar
from txfcore.types.orders import MarketPosition


def T(entry, exit_, direction=MarketPosition.LONG, qty=2,
      d0=1260602, t0=945, d1=1260602, t1=1145, label="X"):
    from txfcore.engine.accounting import trade_cost
    return ClosedTrade("S", "E", label, direction, qty, float(entry), float(exit_),
                       d0, t0, d1, t1, trade_cost(TMF, entry, exit_, qty))


# ==================================================================
# 平手：單獨一類，用毛損益定義
# ==================================================================

def test_flat_is_a_third_class_defined_by_gross():
    """**淨損益不可能恰為 0**（期交稅隨成交價變，是非整數），
    所以平手必須用毛損益定義。實測五支合計毛=0 僅 1 筆，淨=0 零筆。"""
    t = T(20000, 20000)
    assert classify(t) == "flat"
    assert t.net_ntd(TMF) < 0            # 淨損益是負的（扣了成本）
    assert abs(t.gross_points) < FLAT_EPS


def test_flat_counts_in_neither_win_nor_loss():
    """勝率的分子不含平手，分母含。"""
    s = compute([T(20000, 20100), T(20000, 19900), T(20000, 20000)], TMF, 60_000)
    assert (s.n_wins, s.n_losses, s.n_flat) == (1, 1, 1)
    assert s.win_rate == pytest.approx(100 / 3)
    assert s.n_trades == 3


def test_flat_does_not_break_a_losing_streak():
    """**平手不中斷也不累加**連續虧損。"""
    seq = [T(20000, 19900, t1=1000), T(20000, 20000, t1=1100),
           T(20000, 19900, t1=1200), T(20000, 20100, t1=1300)]
    assert compute(seq, TMF, 60_000).max_consec_losses == 2


# ==================================================================
# 判斷賺不賺 / 賺賠結構
# ==================================================================

def test_profit_factor_and_payoff():
    s = compute([T(20000, 20200), T(20000, 20100), T(20000, 19950)], TMF, 60_000)
    assert s.gross_profit > 0 and s.gross_loss < 0
    assert s.profit_factor == pytest.approx(s.gross_profit / -s.gross_loss)
    assert s.payoff_ratio == pytest.approx(abs(s.avg_win / s.avg_loss))


def test_profit_factor_zero_when_no_losses():
    """毛損為 0 時不得回傳無限大。"""
    s = compute([T(20000, 20100)], TMF, 60_000)
    assert s.profit_factor == 0.0


# ==================================================================
# 成本拆分
# ==================================================================

def test_commission_and_tax_are_split():
    """**微台的成本 72% 是固定手續費**。手續費與稅必須分開算。"""
    s = compute([T(23000, 23000, qty=2)], TMF, 60_000)
    assert s.total_commission == TMF.fee_per_side * 2 * 2      # 兩邊兩口
    assert s.total_tax > 0
    assert s.total_commission > s.total_tax                     # 微台手續費佔大宗


def test_slippage_total_from_parameter():
    s = compute([T(20000, 20100, qty=2)], TMF, 60_000, slippage_points_per_side=5)
    assert s.total_slippage_points == 5 * 2 * 2
    assert compute([T(20000, 20100)], TMF, 60_000).total_slippage_points == 0


# ==================================================================
# 資金效率：CAGR 日曆年、期間、變動口數
# ==================================================================

def test_cagr_uses_backtest_period_not_first_to_last_trade():
    """**策略閒置的那一年，資金一樣被綁著。** 年數用回測期間。"""
    t = [T(20000, 21000, d0=1250101, d1=1250131)]        # 只有一個月有交易
    a = compute(t, TMF, 60_000)                             # 沒給期間 → 首末筆
    b = compute(t, TMF, 60_000, period=(date(2024, 1, 1), date(2026, 1, 1)))
    assert a.period_is_backtest is False and b.period_is_backtest is True
    assert b.calendar_years == pytest.approx(2.0, abs=0.01)
    assert b.cagr < a.cagr                                  # 同樣的錢攤到兩年，年化變低


def test_cagr_undefined_when_wiped_out():
    """總報酬 ≤ −100% 時 CAGR 無定義。回傳 −100% 並標註，不拋錯。"""
    t = [T(20000, 15000, qty=2)]                            # 虧 5,000 點 × 20 = 100,000
    s = compute(t, TMF, 60_000)
    assert s.return_on_capital < -1
    assert s.cagr_defined is False and s.cagr == -1.0


def test_max_contracts_from_trades_not_settings():
    """**未來會有加減碼**，口數從交易紀錄讀，不從設定讀。"""
    s = compute([T(20000, 20100, qty=2), T(20000, 20100, qty=5)], TMF, 60_000)
    assert s.max_contracts_held == 5


def test_trading_days_is_independent_fact():
    s = compute([T(20000, 20100, d1=1260602), T(20000, 20100, d1=1260603)], TMF, 60_000)
    assert s.trading_days == 2


# ==================================================================
# 持倉時間：日曆分鐘為主、根數對 MC
# ==================================================================

def test_minutes_are_calendar_time_including_overnight():
    """**日曆時間才是真正暴露的時間**，含夜盤空檔與週末。"""
    # 週五 13:45 進，週一 09:45 出 → 跨週末
    t = T(20000, 20100, d0=1260605, t0=1345, d1=1260608, t1=945)
    s = compute([t], TMF, 60_000)
    assert s.avg_minutes_win > 24 * 60 * 2                  # 超過兩天


def test_bars_need_index_else_zero():
    t = T(20000, 20100, t0=945, t1=1145)
    assert compute([t], TMF, 60_000).avg_bars_win == 0
    idx = {(1260602, 945): 0, (1260602, 1045): 1, (1260602, 1145): 2}
    assert compute([t], TMF, 60_000, bar_index=idx).avg_bars_win == 2


# ==================================================================
# 多空拆分、年月表
# ==================================================================

def test_by_direction_three_columns_sum_to_total():
    ts = [T(20000, 20100), T(20000, 19900, MarketPosition.SHORT),
          T(20000, 20050, MarketPosition.SHORT)]
    d = by_direction(ts, TMF, 60_000)
    assert set(d) == {"Total", "Long", "Short"}
    assert d["Long"].n_trades + d["Short"].n_trades == d["Total"].n_trades
    assert d["Long"].net_profit + d["Short"].net_profit == pytest.approx(
        d["Total"].net_profit)


def test_periodical_uses_trading_day_so_night_session_lands_in_right_month():
    """夜盤 00:00–05:00 的損益要歸前一個交易日。"""
    t = T(20000, 20100, d0=1260731, t0=1600, d1=1260801, t1=300)   # 7/31 夜盤，8/1 凌晨出
    m = periodical([t], TMF, "month")
    assert m[0][0] == "2026-07"                              # 歸 7 月


# ==================================================================
# MAE / MFE：1 分 K，2×2
# ==================================================================

def test_excursion_is_two_by_two_in_points():
    mins = [Bar(1260602, 945 + i, 20000, 20000 + 50 * i, 20000 - 30 * i, 20000, 1)
            for i in range(0, 6)]
    idx = {(b.mc_date, b.mc_time): i for i, b in enumerate(mins)}
    win = T(20000, 20100, t0=945, t1=950)
    loss = T(20000, 19950, t0=945, t1=950)
    e = excursion([win, loss], TMF, mins, idx)
    assert e.sampling == "1min"
    assert e.n_win == 1 and e.n_loss == 1
    assert e.win_mfe == pytest.approx(250) and e.win_mae == pytest.approx(150)
    assert e.loss_mfe == pytest.approx(250) and e.loss_mae == pytest.approx(150)


def test_excursion_skips_flat():
    mins = [Bar(1260602, 945 + i, 20000, 20100, 19900, 20000, 1) for i in range(3)]
    idx = {(b.mc_date, b.mc_time): i for i, b in enumerate(mins)}
    e = excursion([T(20000, 20000, t0=945, t1=947)], TMF, mins, idx)
    assert e.n_win == 0 and e.n_loss == 0


def test_rows_follow_spec_grouping():
    """報表順序對齊 M2_TRADE_STATS.md 的六個分組。"""
    r = rows(compute([T(20000, 20100)], TMF, 60_000), TMF)
    heads = [k for k, v in r if v == ""]
    assert heads[:3] == ["── 判斷賺不賺 ──", "── 判斷賺賠結構 ──", "── 判斷撐不撐得住 ──"]
