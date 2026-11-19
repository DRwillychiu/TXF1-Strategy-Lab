"""MC12 回測報表（.xls 其實是 xlsx）→ 逐筆交易 CSV ＋ 設定頁參數向量。

用法：
    python -I scripts/research/s16_v1260_port/extract_mc_trades.py <MC報表.xls> <輸出.csv> [<參數輸出.txt>]

原始報表不動：先複製到暫存檔再讀。字串是 Big5 被當 latin-1 存，讀出後轉回。
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
import tempfile

import openpyxl


def fix(s):
    if isinstance(s, str):
        try:
            return s.encode("latin-1").decode("big5")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def load(path: str):
    tmp = os.path.join(tempfile.mkdtemp(), "report.xlsx")
    shutil.copyfile(path, tmp)
    return openpyxl.load_workbook(tmp, read_only=True, data_only=True)


def trades(wb) -> list[dict]:
    rows = list(wb.worksheets[1].iter_rows(values_only=True))
    out, cur = [], None
    for r in rows[3:]:
        if r is None or all(v is None for v in r):
            continue
        r = [fix(v) for v in r]
        if isinstance(r[0], (int, float)) and r[2] is not None and "進入" in str(r[2]):
            cur = {"no": int(r[0]), "entry_label": r[3],
                   "entry_dt": f"{r[4]:%Y-%m-%d} {r[5]:%H:%M}", "entry_px": r[6], "qty": r[7],
                   "net_ntd": r[8]}
        elif cur is not None and r[2] is not None and "離開" in str(r[2]):
            cur.update({"exit_label": r[3], "exit_dt": f"{r[4]:%Y-%m-%d} {r[5]:%H:%M}", "exit_px": r[6]})
            out.append(cur)
            cur = None
    return out


def settings(wb) -> dict:
    return {fix(r[0]): fix(r[1]) for r in wb.worksheets[4].iter_rows(values_only=True)
            if r and r[0] is not None and len(r) > 1}


def main() -> None:
    wb = load(sys.argv[1])
    tr = trades(wb)
    cols = ["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "qty", "net_ntd"]
    with open(sys.argv[2], "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(tr)
    st = settings(wb)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
            for k, v in st.items():
                f.write(f"{k}\t{v}\n")
    net = sum(float(t["net_ntd"]) for t in tr)
    print(f"{len(tr)} trades, net {net:,.0f}, first {tr[0]['entry_dt']}, last {tr[-1]['exit_dt']}")


if __name__ == "__main__":
    main()
