"""訂單狀態機與延遲模型。

兩者都是外部借鑑：
  訂單流      NautilusTrader —— RiskEngine 攔截時策略收到 OrderDenied
  延遲模型    hftbacktest    —— feed 與 order 延遲分開建模，從實盤錄後重放
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from txfcore.engine.orders import (
    EventKind, InvalidTransition, OrderBook, OrderStatus,
)
from txfcore.timing.latency import (
    FixedLatency, MeasuredLatency, ZeroLatency, stamps_with_latency,
)
from txfcore.types.orders import OrderIntent, OrderType, Side, SizedOrder

T0 = datetime(2026, 9, 7, 9, 45)


def _order(label="E", qty=2, seq=1, otype=OrderType.MARKET, price=None):
    return SizedOrder(
        intent=OrderIntent(
            strategy="L2", label=label, side=Side.SELL_SHORT,
            order_type=otype, price=price,
            signal_date=1260907, signal_time=945, seq=seq,
        ),
        quantity=qty,
    )


# ==================================================================
# 狀態機
# ==================================================================

def test_denied_is_terminal_and_never_reaches_venue():
    """風險層攔截 → 策略收到 OrderDenied → 訂單根本沒送出去。

    我們原本的模型是 OrderIntent → Fill，中間什麼都沒有，
    所以風險層攔截後策略不知道，會以為單送出去了。
    """
    bk = OrderBook()
    o, _ = bk.place(_order())
    e = o.deny(T0, "超過總口數上限")
    assert o.status is OrderStatus.DENIED
    assert o.status.is_terminal and not o.status.is_open
    assert e.kind is EventKind.DENIED and "上限" in e.reason
    with pytest.raises(InvalidTransition):
        o.submit(T0)          # 被否決的單不得再送出


def test_full_lifecycle():
    bk = OrderBook()
    o, _ = bk.place(_order())
    o.submit(T0)
    o.accept(T0 + timedelta(milliseconds=120), venue_order_id="V123")
    assert o.status is OrderStatus.ACCEPTED and o.venue_order_id == "V123"
    o.fill(T0 + timedelta(seconds=1), 2, 20000.0)
    assert o.status is OrderStatus.FILLED and o.leaves_qty == 0
    assert [e.kind for e in o.events] == [
        EventKind.SUBMITTED, EventKind.ACCEPTED, EventKind.FILL]


def test_partial_fill_tracks_leaves_and_average():
    """L5 的 Stage 2/3 判定完全靠 CurrentContracts —— 需要部分成交。"""
    bk = OrderBook()
    o, _ = bk.place(_order(qty=4))
    o.submit(T0); o.accept(T0)
    o.fill(T0, 1, 20000.0)
    assert o.status is OrderStatus.PARTIALLY_FILLED and o.leaves_qty == 3
    o.fill(T0, 3, 20100.0)
    assert o.status is OrderStatus.FILLED
    assert o.avg_fill_price == pytest.approx((20000 * 1 + 20100 * 3) / 4)


def test_overfill_is_rejected():
    bk = OrderBook()
    o, _ = bk.place(_order(qty=2))
    o.submit(T0); o.accept(T0)
    with pytest.raises(InvalidTransition):
        o.fill(T0, 3, 20000.0)


def test_venue_rejection_is_distinct_from_risk_denial():
    """DENIED 是我們攔的，REJECTED 是交易所拒的。對帳時必須分得開。"""
    bk = OrderBook()
    a, _ = bk.place(_order(seq=1)); a.deny(T0, "風控")
    b, _ = bk.place(_order(seq=2)); b.submit(T0); b.reject(T0, "保證金不足")
    assert a.status is OrderStatus.DENIED
    assert b.status is OrderStatus.REJECTED


def test_idempotent_placement():
    """同 idem_key 重送視為同一筆。冪等在這裡，不在通知層。"""
    bk = OrderBook()
    a, new_a = bk.place(_order(seq=7))
    b, new_b = bk.place(_order(seq=7))
    assert new_a is True and new_b is False
    assert a is b


def test_oco_cancels_siblings():
    """L3 的 bracket：TP limit 與 SL stop 同時掛出，一張成交另一張撤銷。"""
    bk = OrderBook()
    tp, _ = bk.place(_order("TP", seq=1, otype=OrderType.LIMIT, price=19800),
                     oco_group="g1")
    sl, _ = bk.place(_order("SL", seq=2, otype=OrderType.STOP, price=20200),
                     oco_group="g1")
    for o in (tp, sl):
        o.submit(T0); o.accept(T0)
    tp.fill(T0, 2, 19800.0)
    evs = bk.cancel_group_except("g1", tp.idem_key, T0)
    assert sl.status is OrderStatus.CANCELED
    assert len(evs) == 1 and evs[0].kind is EventKind.CANCELED


def test_purge_terminal_keeps_open_orders():
    bk = OrderBook()
    a, _ = bk.place(_order(seq=1)); a.deny(T0, "x")
    b, _ = bk.place(_order(seq=2)); b.submit(T0)
    assert bk.purge_terminal() == 1
    assert [o.idem_key for o in bk.open_orders()] == [b.idem_key]


# ==================================================================
# 延遲
# ==================================================================

def test_mc12_mode_must_have_zero_latency():
    """MC 沒有延遲概念。加了就對不上帳。"""
    z = ZeroLatency()
    assert z.feed_latency(T0) == timedelta(0)
    assert z.order_latency(T0) == timedelta(0)
    r, d = stamps_with_latency(T0, z)
    assert r == d == T0


def test_fixed_latency_is_flagged_as_unmeasured():
    """預設值是猜的不是量的。用它算出來的風險數字必須標註未經量測。"""
    f = FixedLatency()
    assert f.is_measured is False
    assert f.order_latency(T0) == timedelta(milliseconds=120)


def test_measured_latency_replays_recorded_samples():
    """hftbacktest 的做法：從實盤錄，回測時重放。

    MC12 正在實盤自動下單，下單時刻與回報時刻的差就是樣本。
    """
    m = MeasuredLatency()
    m.add(T0, 40, 100, 60)
    m.add(T0 + timedelta(hours=1), 200, 900, 400)   # 尖峰
    assert m.is_measured is True
    assert m.order_latency(T0) == timedelta(milliseconds=100)
    assert m.order_latency(T0 + timedelta(hours=1)) == timedelta(milliseconds=900)


def test_measured_latency_percentile_not_mean():
    """風險判斷要用 p99，不是平均——延遲分布是長尾的。"""
    m = MeasuredLatency()
    for i, v in enumerate([80, 90, 100, 110, 2000]):
        m.add(T0 + timedelta(minutes=i), v, v, v)
    assert m.percentile("order", 0.0) == 80
    assert m.percentile("order", 1.0) == 2000
    assert m.percentile("order", 0.5) == 100


def test_measured_latency_refuses_without_samples():
    """未量測前不得用於風險判斷。"""
    with pytest.raises(LookupError):
        MeasuredLatency().order_latency(T0)


def test_feed_latency_delays_visibility():
    """行情延遲決定策略「何時看得到」。三戳記因此才有意義。"""
    f = FixedLatency(feed_ms=50)
    receipt, decision = stamps_with_latency(T0, f)
    assert receipt == T0 + timedelta(milliseconds=50)
    assert decision >= receipt
