"""Read a MultiCharts strategy performance report exported to Excel (.xlsx, or .xls that is really xlsx)."""
import datetime, pathlib, shutil, tempfile, openpyxl

def _open(path):
    p = pathlib.Path(path)
    if p.suffix.lower() != ".xlsx":
        tmp = pathlib.Path(tempfile.mkdtemp()) / (p.stem + ".xlsx"); shutil.copy(p, tmp); p = tmp
    return openpyxl.load_workbook(p, read_only=True, data_only=True)

def _kv(ws):
    d = {}
    for r in ws.iter_rows(values_only=True):
        if r and r[0] is not None and len(r) > 1: d[str(r[0]).strip()] = r[1]
    return d

def _dt(x):
    if isinstance(x, datetime.datetime): return x
    try: return datetime.datetime.fromisoformat(str(x))
    except Exception: return None

def read(path):
    wb = _open(path)
    settings = {k: (v.isoformat() if isinstance(v, datetime.datetime) else v) for k, v in _kv(wb["設定"]).items()}
    summary = _kv(wb["策略分析"])
    rows = list(wb["交易明細"].iter_rows(values_only=True))[3:]
    trades, cur = [], None
    for r in rows:
        t = str(r[2]) if r[2] else ""
        if "進入" in t: cur = {"in": _dt(r[4]), "inp": r[6], "pnl": r[8] or 0}
        elif "離開" in t and cur:
            cur.update({"out": _dt(r[4]), "outp": r[6], "sig": str(r[3])}); trades.append(cur); cur = None
    wb.close()
    return {"settings": settings,
            "summary": {k: summary.get(k) for k in ("淨利", "最大策略虧損", "獲利因子")},
            "trades": [[t["in"].isoformat() if t["in"] else None, t["inp"], t["out"].isoformat() if t["out"] else None, t["outp"], t["sig"], t["pnl"]] for t in trades]}
