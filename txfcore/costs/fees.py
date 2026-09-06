"""交易成本模型。

規劃書要求：手續費與期交稅**分開計算**，且稅按契約金額課，不是常數。

實戰試算表目前用固定 42 NT$/口/來回，59 筆完全相同（標準差 0）。
但期交稅 = 契約金額 x 0.00002，契約金額隨價格變動，所以稅不可能是常數。
42 是扁平近似值。
"""

from __future__ import annotations

from txfcore.instruments.spec import MXF, TMF, TXF, Instrument  # noqa: F401

# 股價類期貨的期交稅率（十萬分之二）
FUTURES_TAX_RATE = 0.00002

Product = Instrument  # 相容別名


def contract_value(product: Instrument, price: float) -> float:
    return product.contract_value(price)


def tax(product: Instrument, price: float) -> float:
    """單邊期交稅。隨成交價變動。"""
    return product.contract_value(price) * FUTURES_TAX_RATE


def side_cost(product: Instrument, price: float) -> float:
    """單邊總成本 = 手續費 + 期交稅。"""
    return product.fee_per_side + tax(product, price)


def round_trip_cost(
    product: Instrument, entry_price: float, exit_price: float, lots: int = 1
) -> float:
    """來回總成本。進出場價格不同，稅額也不同 —— 分別計算。"""
    return lots * (side_cost(product, entry_price) + side_cost(product, exit_price))


def cost_in_points(
    product: Instrument, entry_price: float, exit_price: float
) -> float:
    """把單口來回成本換算成點數，方便與策略的門檻常數比較。"""
    return round_trip_cost(product, entry_price, exit_price, 1) / product.big_point_value
