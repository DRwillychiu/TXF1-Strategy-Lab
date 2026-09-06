"""五支共用骨架 —— 策略層的介面契約。

規劃書層 2 的核心要求：策略必須是純函數

    (市場視圖, 狀態) -> (新狀態, 訂單意圖)

不是純函數的話，「同一根 K 棒 + 同一組狀態，重跑一萬次都一樣」
就無法證明，只能靠測試碰運氣。

狀態分兩類且**在型別上分開**（規劃書層 2 要求）：
  PerTradeState    每筆交易結束時必須回到初始值，會被斷言檢查
  PerSessionState  跨交易存活，例如 L2 的週線 SMA 陣列

模式（規劃書「三模式與優化的界線」）：
  MC12  完全照 MC 的邏輯與時序 —— 對帳專用，證明移植正確
  LIVE  MC12 邏輯 + 執行優化（立即下單、收盤前禁進場）
  V2    LIVE + 策略邏輯優化 —— 必須等 MC12 對帳通過才可啟用
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Generic, TypeVar

from txfcore.tradecal.gates import CalendarState
from txfcore.types.bar import BarSeries
from txfcore.types.orders import Decision, MarketPosition


class Mode(str, Enum):
    MC12 = "mc12"
    LIVE = "live"
    V2 = "v2"


@dataclass(frozen=True, slots=True)
class PositionView:
    """策略能看到的部位狀態。唯讀。"""

    market_position: MarketPosition = MarketPosition.FLAT
    entry_price: float = 0.0
    bars_since_entry: int = 0
    # 前一根的部位。CLAUDE.md Rule #8：在腳本最末行更新，
    # 所以策略內所有區塊讀到的都是前一根的值。
    prev_market_position: MarketPosition = MarketPosition.FLAT
    # 前一筆已平倉交易的損益（MC 的 PositionProfit(1)）
    prev_position_profit: float = 0.0
    current_contracts: int = 0
    max_contracts: int = 0

    @property
    def is_flat(self) -> bool:
        return self.market_position is MarketPosition.FLAT

    @property
    def is_long(self) -> bool:
        return self.market_position is MarketPosition.LONG

    @property
    def is_short(self) -> bool:
        return self.market_position is MarketPosition.SHORT


@dataclass(frozen=True, slots=True)
class MarketView:
    """策略在決策當下能看到的全部東西。

    data1/2/3 是 BarSeries，其索引語意保證取不到未來資料
    （負索引會拋 FutureDataError）。這把不變量 #13 從
    「事後斷言」升級為「寫不出來」。
    """

    data1: BarSeries
    position: PositionView
    calendar: CalendarState
    mc_date: int
    mc_time: int
    data2: BarSeries | None = None
    data3: BarSeries | None = None
    # 收盤棒回呼。IOG = false 的策略永遠為 True；
    # L1 需要區分 tick 與 bar close（BarStatus(1) = 2 守衛）。
    is_bar_close: bool = True


class PerTradeState:
    """每筆交易結束時必須全部回到初始值。

    子類用 @dataclass 宣告欄位並提供 reset()。
    `assert_clean()` 在平倉後被呼叫，抓「跨交易狀態殘留」這一類缺陷。
    """

    def reset(self) -> None:
        raise NotImplementedError

    def assert_clean(self) -> None:
        fresh = type(self)()
        for f in fields(self):  # type: ignore[arg-type]
            mine = getattr(self, f.name)
            theirs = getattr(fresh, f.name)
            if mine != theirs:
                raise AssertionError(
                    f"per-trade 狀態未清乾淨：{type(self).__name__}.{f.name} "
                    f"= {mine!r}，應為 {theirs!r}"
                )


class PerSessionState:
    """跨交易存活的狀態。永不隨平倉重置。"""


T = TypeVar("T", bound=PerTradeState)
S = TypeVar("S", bound=PerSessionState)


@dataclass(slots=True)
class StrategyState(Generic[T, S]):
    per_trade: T
    per_session: S
    # 上一根的 MarketPosition，由引擎在每根結束時寫入（Rule #8）
    prev_market_position: MarketPosition = MarketPosition.FLAT
    seq: int = 0

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq


@dataclass(slots=True)
class StrategyConfig:
    """所有 .pla 的 inputs 變成這個。不寫死在程式碼裡。"""

    name: str
    mode: Mode = Mode.MC12
    # 商品代碼。點值 / TickSize / 回測資金全部從 instruments 取，
    # 不掛在策略設定上 —— 那是商品屬性不是策略屬性。
    instrument: str = "TXF"
    # 每支不同，不是共用常數：L1=345 / L2=300 / L3,L4,L5=415
    holiday_flat_time: int = 415
    settlement_flat_time: int = 1230
    registry_valid_until: int = 1270101
    # MC 相容欄位：.pla 的 Manual_Kill_Switch 是 input，因為 MC 沒有控制平面，
    # 只能把停機塞成策略參數。mc12 模式必須照抄這個行為才對得上帳。
    # 真正的停機開關是 state/KillSwitch，由 runtime 檢查，優先於一切。
    # 兩者不是兩份真相：這個是「重現 MC」，那個是「實際控制」。
    mc_manual_kill_switch: bool = False
    params: dict = field(default_factory=dict)


class Strategy(ABC, Generic[T, S]):
    """五支的共同基底。

    on_bar 必須是純函數：不讀時鐘、不讀全域、不做 I/O。
    唯一的副作用是回傳新的 state。
    """

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    @abstractmethod
    def initial_state(self) -> StrategyState[T, S]:
        ...

    @abstractmethod
    def on_bar(
        self, view: MarketView, state: StrategyState[T, S]
    ) -> tuple[StrategyState[T, S], Decision]:
        """回傳（新狀態, 本根的決策）。"""

    def expected_trigger_range(self) -> tuple[int, int] | None:
        """事前登記的預期觸發次數區間。

        判官 (4)。L4 v18 零觸發、L2 停擺 443 天，都是因為沒有人
        登記過這個數字。回傳 None 代表尚未登記 —— 那本身就是缺口。
        """
        return None
