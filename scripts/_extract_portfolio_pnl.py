"""Extract daily PnL time series from 6 MC backtest reports for portfolio correlation."""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd

FILES = {
    "L1": "C:/Users/User/Downloads/TXF1  WILLY_ATR_LONG_60M 策略回測績效報告.xlsx",
    "L2": "C:/Users/User/Downloads/TXF1  Trendbearish_V1 策略回測績效報告.xlsx",
    "L3": "C:/Users/User/Downloads/TXF1  STRATEGY_WILLY_LONG_C 策略回測績效報告.xlsx",
    "L4": "C:/Users/User/Downloads/TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告.xlsx",
    "L5": "C:/Users/User/Downloads/TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告.xlsx",
    "S1": "C:/Users/User/Downloads/TXF1  STRATEGY_GEN_NightMomentum 策略回測績效報告.xlsx",
}

OUT_PATH = "C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json"

def find_trade_sheet(path):
    """Find sheet whose first cell contains '交易明細'."""
    xl = pd.ExcelFile(path)
    for i, _ in enumerate(xl.sheet_names):
        df_head = pd.read_excel(path, sheet_name=i, header=None, nrows=3)
        if df_head.shape[0] >= 1:
            v = df_head.iloc[0, 0]
            if isinstance(v, str) and '交易明細' in v:
                return i
    # fallback: sheet 1 (second sheet) typically
    return 1

def extract_strategy(name, path):
    sheet_idx = find_trade_sheet(path)
    # Read raw to locate header row
    raw = pd.read_excel(path, sheet_name=sheet_idx, header=None)
    header_row = None
    for r in range(min(20, len(raw))):
        v = raw.iloc[r, 0]
        if isinstance(v, str) and v.strip() == '交易編號':
            header_row = r
            break
    if header_row is None:
        raise RuntimeError(f"{name}: cannot find '交易編號' header row")

    # Re-read with proper header
    df = pd.read_excel(path, sheet_name=sheet_idx, header=header_row)

    # Identify the relevant columns
    cols = list(df.columns)
    # Expect: 交易編號, 委託單編號, 類型, 訊號, 日期, 時間, 價格, 數量, 獲利(¤), ...
    col_type = '類型'
    col_date = '日期'
    # PnL column - could be '獲利(¤)' or contain '獲利' with currency symbol
    col_pnl = None
    for c in cols:
        if isinstance(c, str) and c.startswith('獲利(') and '%' not in c:
            col_pnl = c
            break
    if col_pnl is None:
        # Fallback to 9th column by position (index 8)
        col_pnl = cols[8]

    print(f"[{name}] sheet_idx={sheet_idx} header_row={header_row} pnl_col={col_pnl!r}")

    # Walk rows in order, pair entries with exits
    daily = {}  # date_str -> sum pnl
    n_trades = 0
    pending_entry_pnl = None
    for _, row in df.iterrows():
        t = row[col_type]
        if not isinstance(t, str):
            continue
        if '進入' in t:
            pnl_val = row[col_pnl]
            if pd.isna(pnl_val):
                pending_entry_pnl = None
            else:
                pending_entry_pnl = float(pnl_val)
        elif '離開' in t:
            if pending_entry_pnl is None:
                continue
            d = row[col_date]
            if pd.isna(d):
                pending_entry_pnl = None
                continue
            # Convert to date string YYYY-MM-DD
            try:
                ts = pd.to_datetime(d)
                ds = ts.strftime('%Y-%m-%d')
            except Exception:
                pending_entry_pnl = None
                continue
            daily[ds] = daily.get(ds, 0.0) + pending_entry_pnl
            n_trades += 1
            pending_entry_pnl = None

    total = sum(daily.values())
    dates_sorted = sorted(daily.keys())
    return {
        'daily': daily,
        'meta': {
            'trading_days': len(daily),
            'n_trades': n_trades,
            'date_min': dates_sorted[0] if dates_sorted else None,
            'date_max': dates_sorted[-1] if dates_sorted else None,
            'total_pnl': total,
        }
    }

def main():
    out = {}
    meta = {}
    for name, path in FILES.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name}: {path}")
        res = extract_strategy(name, path)
        out[name] = res['daily']
        meta[name] = res['meta']
        m = res['meta']
        print(f"  {name}: trades={m['n_trades']}, trading_days={m['trading_days']}, "
              f"range={m['date_min']}..{m['date_max']}, total_pnl={m['total_pnl']:.2f}")

    # Write JSON
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\nWrote {OUT_PATH}")
    print(f"meta_json={json.dumps(meta, ensure_ascii=False)}")

if __name__ == '__main__':
    main()
