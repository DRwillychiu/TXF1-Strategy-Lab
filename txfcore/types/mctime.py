"""MultiCharts 日期/時間語意。

MC 的 Date 是民國年格式的整數：YYYMMDD，其中 YYY = 西元年 - 1900。
    1260906 -> 2026-09-06
MC 的 Time 是 HHMM 整數，代表該 K 棒的**收盤**時刻：
    1245 -> 12:45      300 -> 03:00      500 -> 05:00

`trading_day()` 是全系統唯一的「交易日歸屬」函數。
規劃書層 0 要求：K 棒層與權益曲線層必須共用同一個實作，不得各自寫一份。
兩處若不一致，會產生無法追查的一天偏移。
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime, time, timedelta
from enum import IntEnum

# 夜盤跨日切點。00:00-05:00 的 K 棒戳記為「隔天」。
# L1 的 Holiday_Tail 整個模組建立在這一句上。
NIGHT_TAIL_END = 500  # HHMM，含

DAY_SESSION_OPEN = 845
DAY_SESSION_CLOSE = 1345
NIGHT_SESSION_OPEN = 1500
NIGHT_SESSION_CLOSE = 500


class DayOfWeek(IntEnum):
    """PowerLanguage 的 DayOfWeek 回傳 0-6，Sun=0。

    L5 v19.7 的 FIX 1 記錄了這件事：v19.6 有三處寫 DayOfWeek = 7，
    而 7 永遠不成立，是死碼。
    """

    SUN = 0
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6


def mc_date_to_date(mc_date: int) -> _date:
    """1260906 -> date(2026, 9, 6)"""
    year = 1900 + mc_date // 10000
    month = (mc_date // 100) % 100
    day = mc_date % 100
    return _date(year, month, day)


def date_to_mc_date(d: _date) -> int:
    """date(2026, 9, 6) -> 1260906"""
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def mc_time_to_time(mc_time: int) -> time:
    """1245 -> time(12, 45);  500 -> time(5, 0)"""
    return time(mc_time // 100, mc_time % 100)


def time_to_mc_time(t: time) -> int:
    """time(12, 45) -> 1245"""
    return t.hour * 100 + t.minute


def day_of_week(mc_date: int) -> DayOfWeek:
    """MC 語意：Sun=0 ... Sat=6。Python 的 weekday() 是 Mon=0 ... Sun=6。"""
    py = mc_date_to_date(mc_date).weekday()  # Mon=0 .. Sun=6
    return DayOfWeek((py + 1) % 7)


def day_of_month(mc_date: int) -> int:
    return mc_date % 100


def bar_stamp(dt: datetime) -> tuple[int, int]:
    """把一個 K 棒收盤時刻轉成 MC 的 (Date, Time) 戳記。

    夜盤 00:00-05:00 的 K 棒，日期戳為當下的曆日 —— 也就是「隔天」，
    因為那段時間在曆法上已經跨日。這與 MC 的行為一致。
    """
    return date_to_mc_date(dt.date()), time_to_mc_time(dt.time())


def trading_day(mc_date: int, mc_time: int) -> _date:
    """該 K 棒屬於哪一個「交易日」。

    夜盤 15:00 開盤到隔日 05:00 收盤屬於同一個交易日，而該交易日的
    名稱取「夜盤開盤那一天」。所以 00:00-05:00 的 K 棒（日期戳已是隔天）
    要往回退一個曆日。

    這是全系統唯一的實作。權益曲線的「每日」切點必須呼叫這個函數。
    """
    d = mc_date_to_date(mc_date)
    if mc_time <= NIGHT_TAIL_END:
        return d - timedelta(days=1)
    return d


def is_night_tail(mc_time: int) -> bool:
    """是否為 00:00-05:00 的夜盤尾段 K 棒。"""
    return mc_time <= NIGHT_TAIL_END
