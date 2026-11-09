"""委託名稱檢查（verify.bat 的一步）：資料夾模式要能抓到重複名稱。L5 v19.9 曾有重複名稱，MC 會停掉策略。"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "check_order_names", Path(__file__).resolve().parent.parent / "tools" / "check_order_names.py")
con = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(con)


def test_folder_mode_finds_duplicate_names(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "ok.pla").write_text('Sell ("X1") next bar at market;\nSell ("X2") next bar at market;', encoding="ascii")
    assert con.main([str(tmp_path)]) == 0
    (tmp_path / "a" / "dup.pla").write_text('Sell ("Y") next bar at market;\nSell ("Y") next bar at 1 stop;', encoding="ascii")
    assert con.main([str(tmp_path)]) == 1


def test_empty_input_is_a_failure(tmp_path):
    assert con.main([str(tmp_path)]) == 1
