"""L6 停單線檢查（tools/l6_stopline_check.py）：歷史重播＋人工碰線情境。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import l6_stopline_check as sl  # noqa: E402

FX = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_trades.csv"


def test_history_replay_2023_never_hits_18000():
    """MC 報表交易 2023 起重播：最大回落 16,727（＝研究數字），最長連虧 5，不碰 18,000 線。"""
    r = sl.check(sl.read(str(FX), "2023-01-01"), [])
    t16 = [x for x in sl.read(str(FX), "2023-01-01") if x[0] <= "2026-11-16 12:20"]
    r16 = sl.check(t16, [])
    assert round(-r16["l6_max_dd"]) == 16727 and r16["l6_max_streak"] == 5
    assert -r["l6_max_dd"] < 18000


def test_synthetic_breaches():
    ok = sl.check([("2026-11-23", 1000.0)], [])
    assert ok["level"] == 0
    dd = sl.check([("a", 20000.0), ("b", -18000.0)], [])
    assert dd["level"] == 2 and any("回落" in m for m in dd["msgs"])
    warn = sl.check([("a", 10000.0), ("b", -15000.0)], [])
    assert warn["level"] == 1
    streak = sl.check([(f"{i:02d}", -100.0) for i in range(10)], [])
    assert streak["level"] == 2 and any("連虧" in m for m in streak["msgs"])
    acct = sl.check([("a", -5000.0)], [[("a", -10000.0)], [("b", -7500.0)]])
    assert acct["level"] == 2 and acct["acct"] == -22500


def test_cli_exit_code(tmp_path):
    f = tmp_path / "l6.csv"
    f.write_text("exit_dt,net\n2026-11-24 10:00,-9000\n2026-11-25 10:00,-9000\n", encoding="utf-8")
    assert sl.main(["--start", "2026-11-23", "--l6", str(f)]) == 2
