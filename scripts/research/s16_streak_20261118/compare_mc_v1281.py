"""MC v1.28.1（B 預設）報表 vs Python 預測，逐筆比對（Python 資料只到 2026-11-16 12:20）。
Usage: python -I scripts/research/s16_streak_20261118/compare_mc_v1281.py <mc_trades.csv> <mc_settings.txt> <py_trades.csv>
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402

PY_END = "2026-11-16 12:20"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mc = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    vec = [ln.split("\t", 1)[1] for ln in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
           if ln.startswith("策略參數")][0]
    p_mc = s16.params_from_mc_vector(s16.PLA_2611191, vec)
    p_file = s16.pla_params(s16.PLA_2611191)
    diff = {k: (p_file[k], p_mc[k]) for k in p_file if p_file[k] != p_mc[k]}
    print("MC 參數與檔案預設不同的：", diff or "無（91 個全部是預設）")
    py = list(csv.DictReader(open(sys.argv[3], encoding="utf-8")))
    mc_in = [m for m in mc if m["exit_dt"] <= PY_END]
    mc_after = [m for m in mc if m["exit_dt"] > PY_END]
    print(f"MC 共 {len(mc)} 筆；Python 資料範圍內（平倉 ≤ {PY_END}）{len(mc_in)} 筆；Python 預測 {len(py)} 筆")
    bad = 0
    for i, (m, q) in enumerate(zip(mc_in, py), 1):
        km = (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19], round(float(m["net_ntd"])))
        kq = (q["entry_dt"], q["entry_label"], q["exit_dt"], q["exit_label"][:19], round(float(q["net_ntd"])))
        if km != kq:
            bad += 1
            print(f"  第 {i} 筆不同：MC {km}｜Python {kq}")
    if len(mc_in) != len(py):
        print("  筆數不同")
    s_mc = sum(float(m["net_ntd"]) for m in mc_in)
    s_py = sum(float(q["net_ntd"]) for q in py)
    print(f"逐筆不同 {bad} 筆；淨利 MC {s_mc:,.0f}｜Python {s_py:,.0f}")
    print("Python 資料以後的 MC 交易：")
    for m in mc_after:
        print(f"  {m['entry_dt']} {m['entry_label']} → {m['exit_dt']} {m['exit_label']} {float(m['net_ntd']):,.0f}")


if __name__ == "__main__":
    main()
