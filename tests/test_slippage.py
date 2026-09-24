"""滑價模型與包裝層。

裁決 2026-09-09：5 tick/邊/口 · 一律不利方向 · **全部單型含限價** ·
做成開關可對照。
"""
from __future__ import annotations

import pytest

from txfcore.costs.slippage import CANDIDATES, DEFAULT_TICKS, OFF, STRESS, SlippageModel
from txfcore.engine.fill_mc12 import Fill, MC12FillModel
from txfcore.engine.fill_slippage import SlippageFill
from txfcore.instruments.spec import MXF, TMF, TXF
from txfcore.types.bar import Bar
from txfcore.types.orders import OrderIntent, OrderType, Side, SizedOrder

BAR = Bar(1260602, 945, 20000, 20200, 19800, 20050)


def _o(label, side, otype, price=None, qty=2):
    return SizedOrder(
        intent=OrderIntent(strategy="X", label=label, side=side,
                           order_type=otype, price=price),
        quantity=qty)


# ==================================================================
# 點數與金額
# ==================================================================

def test_five_ticks_is_five_points_for_all_three_products():
    """**5 tick = 5 點，三商品皆同。**

    大台 5 點 = 1,000 元，與 CLAUDE.md 的「1,000 NTD/邊/口」吻合——
    所以原意確實是點數，1,000 只是它在大台的金額表示。
    """
    assert DEFAULT_TICKS == 5
    for inst, money in ((TMF, 50), (MXF, 250), (TXF, 1000)):
        assert inst.tick_size == 1
        pts = STRESS.points(inst, OrderType.MARKET)
        assert pts == 5
        assert pts * inst.big_point_value == money


def test_round_trip_cost_is_twenty_points_at_two_lots():
    """來回 = 5 點 × 2 邊 × 2 口 = 20 點。

    對照實測的平均獲利：L5 139 點（滑價佔 14%）· L3 159 點（12.6%）。
    """
    for inst, money in ((TMF, 200), (MXF, 1000), (TXF, 4000)):
        assert STRESS.round_trip_points(inst, 2) == 20
        assert STRESS.round_trip_money(inst, 2) == money


# ==================================================================
# 方向與單型
# ==================================================================

def test_slippage_always_moves_against_you():
    """**一律不利方向。** 買進加、賣出減。"""
    for side in (Side.BUY, Side.BUY_TO_COVER):
        assert STRESS.adjust(20000, side, TXF, OrderType.MARKET) == 20005
    for side in (Side.SELL, Side.SELL_SHORT):
        assert STRESS.adjust(20000, side, TXF, OrderType.MARKET) == 19995


def test_limit_orders_also_slip_by_design():
    """**限價單理論上不會有不利滑價，但這裡刻意加。**

    理由是壓力測試：假設市場流動性非常差的嚴苛情況下，
    策略是否仍然賺錢。**在最嚴苛的假設下仍然賺錢，才是可信的。**
    """
    assert STRESS.apply_to_limit is True
    assert STRESS.points(TXF, OrderType.LIMIT) == 5
    # 可關閉，供對照
    lenient = SlippageModel(enabled=True, apply_to_limit=False)
    assert lenient.points(TXF, OrderType.LIMIT) == 0
    assert lenient.points(TXF, OrderType.STOP) == 5


def test_off_is_the_default():
    """**預設關閉**，讓兩組數字可並排對照。"""
    assert OFF.enabled is False
    assert SlippageModel().enabled is False
    assert OFF.points(TXF, OrderType.MARKET) == 0.0


# ==================================================================
# 這是設定值，不是量測值
# ==================================================================

def test_slippage_is_marked_as_assumed_not_measured():
    """**真實滑價要從實戰紀錄量（訊號價 vs 成交價）。**

    量到之前，任何用它算出的數字都要標註。
    """
    assert STRESS.is_measured is False
    assert "assumed" in STRESS.name
    measured = SlippageModel(enabled=True, is_measured=True)
    assert "measured" in measured.name


def test_policy_name_shows_both_layers():
    """報告上看得出這份數字是哪一組假設跑出來的。"""
    fm = SlippageFill(MC12FillModel(), TXF, STRESS)
    assert fm.name.startswith("fill_mc12+")
    assert "5tick" in fm.name and "limit" in fm.name
    assert SlippageFill(MC12FillModel(), TXF, OFF).name.endswith("slip=off")


# ==================================================================
# 包裝層：fill_mc12 必須保持純粹
# ==================================================================

def test_fill_mc12_stays_zero_slippage():
    """**`fill_mc12` 的身分是「MC 的樂觀假設：觸價即成交、零滑價」。**

    把滑價塞進去會污染它的定位——它就不再是 MC 的複製品，
    而對帳的基準也就消失了。
    """
    import inspect
    from txfcore.engine import fill_mc12
    assert "零滑價" in inspect.getsource(fill_mc12.MC12FillModel)
    assert "slippage" not in inspect.getsource(fill_mc12).lower()
    raw = MC12FillModel().fill([_o("市價買", Side.BUY, OrderType.MARKET)], BAR)
    assert raw[0].price == BAR.open           # 零滑價


def test_wrapper_applies_slippage_to_every_order_type():
    fm = SlippageFill(MC12FillModel(), TXF, STRESS)
    cases = (("市價買", Side.BUY, OrderType.MARKET, None, 20005),
             ("停損賣", Side.SELL, OrderType.STOP, 19900, 19895),
             ("限價賣", Side.SELL, OrderType.LIMIT, 20100, 20095),
             ("回補", Side.BUY_TO_COVER, OrderType.STOP, 20100, 20105))
    for label, side, otype, px, want in cases:
        got = fm.fill([_o(label, side, otype, px)], BAR)
        assert got and got[0].price == want, label


def test_engine_stop_also_slips():
    """**引擎停損同樣是一張真實的單**，流動性差時一樣會滑。"""
    fm = SlippageFill(MC12FillModel(), TXF, STRESS)
    f = fm.engine_stop_fill(19900, Side.SELL, 2, BAR, "X")
    assert f is not None and f.is_engine_stop and f.price == 19895


def test_candidates_cover_both_sides():
    """對照組：兩組都跑，並排顯示影響。"""
    assert len(CANDIDATES) == 2
    assert {c.enabled for c in CANDIDATES} == {False, True}
