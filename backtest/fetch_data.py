"""
Fetch TAIEX futures proxy data for backtesting.
We use ^TWII (TAIEX index) as a proxy since TXF1 tick data isn't freely available.
The index closely tracks TXF1 during day session.
"""
import yfinance as yf
import pandas as pd
import sys

print("Fetching ^TWII (TAIEX) data 2020-01-01 to 2026-06-06...")
df = yf.download("^TWII", start="2020-01-01", end="2026-06-07", interval="1d", progress=False)
if df.empty:
    print("ERROR: No data fetched")
    sys.exit(1)

# Flatten multi-level columns if present
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df.to_csv("/tmp/TXF1-Strategy-Lab/backtest/twii_daily.csv")
print(f"Saved {len(df)} daily bars to twii_daily.csv")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Price range: {df['Low'].min():.0f} - {df['High'].max():.0f}")
