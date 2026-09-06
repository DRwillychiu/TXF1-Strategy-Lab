"""部位帳。

單一部位（L1 L2 L3 L4）與多腿部位（L5）用同一個型別表達，
差別只在 `legs` 有幾條。這樣 `CurrentContracts` / `MaxContracts`
的語意對五支一致，不需要兩套。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.types.orders import MarketPosition, Side


@dataclass(slots=True)
class Leg:
    """一條進場腿。L5 有 Bot 與 Mid 兩條，其餘四支只有一條。

    `entry_label` 是 MC 的 `from Entry("...")` 綁定依據。
    L5 全案 28 處綁定，其餘四支零處。
    """

    entry_label: str
    entry_price: float
    quantity: int
    entry_date: int
    entry_time: int
    bars_since_entry: int = 0


@dataclass(slots=True)
class Position:
    strategy: str
    direction: MarketPosition = MarketPosition.FLAT
    legs: list[Leg] = field(default_factory=list)
    # 本輪持倉曾達到的最大口數。L5 的 Stage 判定靠它。
    max_contracts: int = 0
    # 上一筆已平倉交易的損益（MC 的 PositionProfit(1)）
    prev_position_profit: float = 0.0

    # ---- MC 相容的唯讀屬性 ----
    @property
    def current_contracts(self) -> int:
        return sum(l.quantity for l in self.legs)

    @property
    def is_flat(self) -> bool:
        return self.current_contracts == 0

    @property
    def entry_price(self) -> float:
        """MC 的 EntryPrice。多腿時取加權平均。"""
        n = self.current_contracts
        if n == 0:
            return 0.0
        return sum(l.entry_price * l.quantity for l in self.legs) / n

    @property
    def bars_since_entry(self) -> int:
        """MC 的 BarsSinceEntry。多腿時取最早那條。"""
        return max((l.bars_since_entry for l in self.legs), default=0)

    def leg(self, entry_label: str) -> Leg | None:
        for l in self.legs:
            if l.entry_label == entry_label:
                return l
        return None

    # ---- 變更 ----
    def open_leg(self, label: str, price: float, qty: int, d: int, t: int,
                 side: Side) -> None:
        existing = self.leg(label)
        if existing:
            total = existing.quantity + qty
            existing.entry_price = (
                existing.entry_price * existing.quantity + price * qty
            ) / total
            existing.quantity = total
        else:
            self.legs.append(Leg(label, price, qty, d, t))
        self.direction = (
            MarketPosition.LONG if side is Side.BUY else MarketPosition.SHORT
        )
        self.max_contracts = max(self.max_contracts, self.current_contracts)

    def close(self, qty: int, from_entry: str | None = None) -> int:
        """平倉。`from_entry` 指定腿時只平該腿；None 時依序平。

        回傳實際平掉的口數。
        """
        remaining = qty
        targets = (
            [l for l in self.legs if l.entry_label == from_entry]
            if from_entry else list(self.legs)
        )
        for l in targets:
            if remaining <= 0:
                break
            take = min(l.quantity, remaining)
            l.quantity -= take
            remaining -= take
        self.legs = [l for l in self.legs if l.quantity > 0]
        if not self.legs:
            self.direction = MarketPosition.FLAT
            self.max_contracts = 0
        return qty - remaining

    def advance_bar(self) -> None:
        for l in self.legs:
            l.bars_since_entry += 1


class PositionBook:
    """五支的部位總帳。風險層的總曝險與券商對帳都讀它。"""

    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}

    def get(self, strategy: str) -> Position:
        if strategy not in self._positions:
            self._positions[strategy] = Position(strategy)
        return self._positions[strategy]

    def total_contracts(self) -> int:
        """所有策略的口數總和。風險層的總曝險上限用它。"""
        return sum(p.current_contracts for p in self._positions.values())

    def net_contracts(self) -> int:
        """方向淨額。多為正、空為負。實戰紀錄顯示多空 56:3，
        這個數字會揭露組合實際上是單邊的。"""
        return sum(
            p.current_contracts * (1 if p.direction is MarketPosition.LONG else -1)
            for p in self._positions.values()
        )

    def snapshot(self) -> dict[str, int]:
        """給券商部位對帳迴路比對用。不一致即停機，且不自動修正。"""
        return {k: v.current_contracts for k, v in self._positions.items()}
