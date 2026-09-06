"""PowerLanguage 的變數歷史。

MC 的每一個 `variables:` 宣告都自帶歷史 —— `v_X[1]` 對任何變數都合法，
不需要額外宣告。五支策略全部依賴這個行為：

    L2   ZLEMA_Val[1]              C1_Bar[1]
    L3   v_is_in_consolidation[1]
    L4   v_Stop_Level[1]           MarketPosition[1]
    L5   v_is_in_consolidation[1]

其中 L4 的 `v_Stop_Level = MinList(v_Stop_Level[1], ...)` 最危險：
追蹤停損的棘輪整個掛在歷史值上，取錯了會整條錯掉而且不報錯。

手刻 `xxx_prev` 是特例不是機制 —— 每刻一次就是一個出錯的地方。
這個模組把它變成機制：宣告一次，歷史自動維護。
"""

from __future__ import annotations

from typing import Any, Generic, Iterator, TypeVar

from txfcore.types.bar import FutureDataError

T = TypeVar("T")


class Var(Generic[T]):
    """帶歷史的變數。索引語意與 PowerLanguage 相同。

        v[0]  當根（等同直接讀 .value）
        v[1]  前一根
        v[-1] 拋 FutureDataError

    `commit()` 由引擎在每根 K 棒結束時呼叫，把當根值推入歷史。
    策略程式碼永不呼叫它 —— 那是引擎的職責，與 MC 的行為一致。
    """

    __slots__ = ("_name", "_initial", "_value", "_history", "_maxlen")

    def __init__(self, name: str, initial: T, maxlen: int = 8) -> None:
        self._name = name
        self._initial = initial
        self._value: T = initial
        self._history: list[T] = []
        self._maxlen = maxlen

    # --- 當根值 ---
    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, v: T) -> None:
        self._value = v

    def set(self, v: T) -> T:
        self._value = v
        return v

    # --- 歷史 ---
    def __getitem__(self, offset: int) -> T:
        if offset < 0:
            raise FutureDataError(
                f"{self._name}[{offset}] 指向未來。PowerLanguage 的偏移只能 >= 0。"
            )
        if offset == 0:
            return self._value
        idx = offset - 1
        if idx >= len(self._history):
            # MC 的行為：歷史不足時回傳變數的初始值，不報錯。
            # 這一點必須照抄 —— 暖機期的行為差異會讓早期交易對不上。
            return self._initial
        return self._history[-1 - idx]

    def commit(self) -> None:
        """由引擎在每根 K 棒結束時呼叫。"""
        self._history.append(self._value)
        if len(self._history) > self._maxlen:
            del self._history[0]

    def reset(self) -> None:
        """回到初始值。歷史保留 —— MC 的變數不會因為平倉就失去歷史。"""
        self._value = self._initial

    def __repr__(self) -> str:
        return f"Var({self._name}={self._value!r})"


class VarBook:
    """一支策略的全部變數。引擎呼叫 commit_all()，策略只讀寫值。

    用法：

        vb = VarBook()
        stop = vb.declare("v_Stop_Level", 0.0)
        ...
        stop.set(min(stop[1], new_level))   # L4 的棘輪，語意與 .pla 相同
        ...
        vb.commit_all()                      # 引擎在每根結束時呼叫
    """

    __slots__ = ("_vars",)

    def __init__(self) -> None:
        self._vars: dict[str, Var[Any]] = {}

    def declare(self, name: str, initial: T, maxlen: int = 8) -> Var[T]:
        if name in self._vars:
            raise ValueError(f"變數 {name} 重複宣告")
        v: Var[T] = Var(name, initial, maxlen)
        self._vars[name] = v
        return v

    def __getitem__(self, name: str) -> Var[Any]:
        return self._vars[name]

    def __contains__(self, name: str) -> bool:
        return name in self._vars

    def __iter__(self) -> Iterator[Var[Any]]:
        return iter(self._vars.values())

    def commit_all(self) -> None:
        for v in self._vars.values():
            v.commit()

    def snapshot(self) -> dict[str, Any]:
        """給 state/ 持久化用。只存當根值，歷史由重放重建。"""
        return {name: v.value for name, v in self._vars.items()}

    def restore(self, snapshot: dict[str, Any]) -> None:
        for name, value in snapshot.items():
            if name in self._vars:
                self._vars[name].value = value
