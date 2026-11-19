"""MC 新匯出 12 欄 1 分 K（2026-11-16 起）：價格必須與 7 欄版完全相同。"""
import os
from datetime import date
from pathlib import Path

import pytest

from txfcore.quotes.history import ExportFormatError, MC12MinuteSource, _parse_header, _parse_line

H7 = "<Date>, <Time>, <Open>, <High>, <Low>, <Close>, <Volume>"
H12 = ("<Date>, <Time>, <Open>, <High>, <Low>, <Close>, <UpVolume>, <DownVolume>, "
       "<TotalVolume>, <UpTicks>, <DownTicks>, <TotalTicks>")


def test_header_12_columns_accepted():
    assert _parse_header(H7) == 7
    assert _parse_header(H12) == 12
    with pytest.raises(ExportFormatError):
        _parse_header(H12.replace("<TotalVolume>", "<Vol>"))


def test_12_column_line_equals_7_column_line():
    a = _parse_line("2026/11/16,12:16:00.000,41847,41900,41821,41823,392", 2, 7)
    b = _parse_line("2026/11/16,12:16:00.000,41847,41900,41821,41823,168,166,392,134,125,307", 2, 12)
    assert a == b
    with pytest.raises(ExportFormatError):
        _parse_line("2026/11/16,12:16:00.000,41847,41900,41821,41823,392", 2, 12)


def test_12_column_file_streams(tmp_path):
    p = tmp_path / "m.txt"
    p.write_text(H12 + "\r\n2026/11/16,12:15:00.000,41675,41856,41664,41853,390,244,823,269,188,548\r\n"
                 "2026/11/16,12:16:00.000,41847,41900,41821,41823,168,166,392,134,125,307\r\n",
                 encoding="utf-8", newline="")
    bars = list(MC12MinuteSource(p).stream())
    assert [(b.close, b.volume) for b in bars] == [(41853, 823), (41823, 392)]


OLD = os.environ.get("TXF1_MIN_DATA_OLD")
NEW = os.environ.get("TXF1_MIN_DATA_NEW")


@pytest.mark.skipif(not (OLD and NEW), reason="需 TXF1_MIN_DATA_OLD（7 欄）與 TXF1_MIN_DATA_NEW（12 欄）")
def test_real_files_same_prices_on_overlap():
    """同一段期間新舊格式 OHLC 完全相同（2026-06 整月抽查）。"""
    s, e = date(2026, 6, 1), date(2026, 6, 30)
    key = lambda b: (b.mc_date, b.mc_time, b.open, b.high, b.low, b.close)
    old = [key(b) for b in MC12MinuteSource(Path(OLD)).stream_between(s, e)]
    new = [key(b) for b in MC12MinuteSource(Path(NEW)).stream_between(s, e)]
    assert len(old) > 20000 and old == new
