"""
Daily-proxy backtest for TXF1 strategies against ^TWII.
This is a proxy — real intraday performance will differ. Metrics scaled to
1-point = 200 NTD, single contract, 1,000 NTD slippage per round trip.
"""
import json
import math
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

POINT_VALUE   = 200        # NTD per point
SLIPPAGE_NTD  = 1000       # per round trip
START         = "2020-01-01"
END           = datetime.today().strftime("%Y-%m-%d")

df = yf.download("^TWII", start=START, end=END, auto_adjust=False, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df.dropna().copy()
df["ret"] = df["Close"].pct_change().fillna(0)
df["tr"] = np.maximum(df["High"] - df["Low"],
                      np.maximum((df["High"] - df["Close"].shift(1)).abs(),
                                 (df["Low"]  - df["Close"].shift(1)).abs()))
df["atr14"] = df["tr"].rolling(14).mean()
df["sma20"] = df["Close"].rolling(20).mean()
df["sma50"] = df["Close"].rolling(50).mean()
df["sma60"] = df["Close"].rolling(60).mean()
df["std20"] = df["Close"].rolling(20).std()
df["bb_up"] = df["sma20"] + 2*df["std20"]
df["bb_dn"] = df["sma20"] - 2*df["std20"]
df["bb_bw"] = (df["bb_up"] - df["bb_dn"]) / df["sma20"]
df["bb_bw_lo60"] = df["bb_bw"].rolling(60).min()

# RSI 14
def rsi(series, n=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = (-delta.clip(upper=0)).rolling(n).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100/(1+rs)
df["rsi14"] = rsi(df["Close"], 14)

df["z50"] = (df["Close"] - df["Close"].rolling(50).mean()) / df["Close"].rolling(50).std()
df["mom10"] = df["Close"] - df["Close"].shift(10)
df = df.dropna().copy()


def simulate(entries: pd.Series, exits: pd.Series, direction: pd.Series, name: str):
    """Very simple next-bar-open fill simulator on daily bars."""
    trades = []
    pos = 0
    entry_px = 0.0
    entry_idx = None
    dir_ = 0
    px_open = df["Open"].values
    px_close = df["Close"].values
    dates = df.index

    for i in range(len(df)-1):
        if pos == 0 and entries.iloc[i]:
            pos = 1
            dir_ = int(direction.iloc[i])
            entry_px = px_open[i+1]
            entry_idx = i+1
        elif pos != 0 and (exits.iloc[i] or i - entry_idx > 15):
            exit_px = px_open[i+1]
            pnl_pts = (exit_px - entry_px) * dir_
            trades.append({
                "entry_date": str(dates[entry_idx].date()),
                "exit_date":  str(dates[i+1].date()),
                "dir": dir_,
                "pnl_pts": pnl_pts,
                "bars": i+1-entry_idx,
            })
            pos = 0
    return trades


strategies = {}

# ---- ORB proxy: previous 10-day HH/LL breakout, both sides, ATR exit ----
hh = df["High"].rolling(10).max().shift(1)
ll = df["Low"].rolling(10).min().shift(1)
long_cond  = (df["Close"] > hh) & (df["Close"] > df["sma20"])
short_cond = (df["Close"] < ll) & (df["Close"] < df["sma20"])
entries = long_cond | short_cond
direction = np.where(long_cond, 1, np.where(short_cond, -1, 0))
exits = (df["Close"] < df["sma20"]) & (df["Close"].shift(1) >= df["sma20"].shift(1))
trades = simulate(entries, exits, pd.Series(direction, index=df.index), "ORB")
strategies["STRATEGY_GEN_ORB"] = trades

# ---- VOL squeeze breakout ----
squeeze = df["bb_bw"] < df["bb_bw_lo60"]*1.3
long_cond = squeeze.shift(1).fillna(False) & (df["Close"] > df["bb_up"]) & (df["mom10"] > 0)
short_cond = squeeze.shift(1).fillna(False) & (df["Close"] < df["bb_dn"]) & (df["mom10"] < 0)
entries = long_cond | short_cond
direction = np.where(long_cond, 1, np.where(short_cond, -1, 0))
exits = (df["Close"] < df["sma20"]) & (df["Close"].shift(1) >= df["sma20"].shift(1)) \
      | (df["Close"] > df["sma20"]) & (df["Close"].shift(1) <= df["sma20"].shift(1))
trades = simulate(entries, exits, pd.Series(direction, index=df.index), "VOL")
strategies["STRATEGY_GEN_VOL"] = trades

# ---- MOMS momentum short ----
rsi_peaked = (df["rsi14"].shift(3) > 65) & (df["rsi14"] < 60)
short_cond = rsi_peaked & (df["sma20"] < df["sma50"]) & (df["Close"] < df["Close"].shift(3))
entries = short_cond
direction = pd.Series(np.where(short_cond, -1, 0), index=df.index)
exits = (df["sma20"] > df["sma50"]) | (df["Close"] > df["sma20"])
trades = simulate(entries, exits, direction, "MOMS")
strategies["STRATEGY_GEN_MOMS"] = trades

# ---- ZS mean reversion ----
long_cond = (df["z50"] < -2.0) & (df["sma20"] > df["sma20"].shift(5))
short_cond = (df["z50"] >  2.0) & (df["sma20"] < df["sma20"].shift(5))
entries = long_cond | short_cond
direction = np.where(long_cond, 1, np.where(short_cond, -1, 0))
exits = df["z50"].abs() < 0.3
trades = simulate(entries, exits, pd.Series(direction, index=df.index), "ZS")
strategies["STRATEGY_GEN_ZS"] = trades

# ---- MTF pullback long ----
daily_ok = (df["sma20"] > df["sma60"]) & (df["sma20"] > df["sma20"].shift(5))
pullback = df["Low"] <= df["sma20"] + 0.6*df["atr14"]
long_cond = daily_ok & pullback & (df["Close"] > df["Open"]) & (df["Close"] > df["sma20"])
entries = long_cond
direction = pd.Series(np.where(long_cond, 1, 0), index=df.index)
exits = df["Close"] < df["sma60"]
trades = simulate(entries, exits, direction, "MTF")
strategies["STRATEGY_GEN_MTF"] = trades


def summarize(trades):
    if not trades:
        return {"n":0, "win":0, "pf":0, "net_pts":0, "net_ntd":0, "mdd_ntd":0,
                "cagr":0, "annual_ntd":0, "avg_win":0, "avg_loss":0, "wl_ratio":0}
    pts = np.array([t["pnl_pts"] for t in trades])
    pnl_ntd = pts * POINT_VALUE - SLIPPAGE_NTD          # slippage subtracted per round trip
    equity = np.cumsum(pnl_ntd)
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    mdd = -dd.min() if len(dd) else 0
    wins = pnl_ntd[pnl_ntd > 0]
    losses = pnl_ntd[pnl_ntd <= 0]
    gross_win = wins.sum() if len(wins) else 0
    gross_loss = -losses.sum() if len(losses) else 0
    pf = gross_win/gross_loss if gross_loss > 0 else float('inf')
    win_rate = len(wins)/len(pnl_ntd)*100
    net_ntd = pnl_ntd.sum()
    years = (pd.Timestamp(trades[-1]["exit_date"]) - pd.Timestamp(trades[0]["entry_date"])).days/365.25
    years = max(years, 0.1)
    annual_ntd = net_ntd/years
    # CAGR on notional 500k NTD margin
    notional = 500000
    if net_ntd + notional > 0:
        cagr = ((net_ntd + notional)/notional)**(1/years) - 1
    else:
        cagr = -1
    avg_win = wins.mean() if len(wins) else 0
    avg_loss = losses.mean() if len(losses) else 0
    wl = abs(avg_win/avg_loss) if avg_loss != 0 else 0
    return {"n":len(pnl_ntd),
            "win":round(win_rate,1),
            "pf":round(pf,2) if pf != float('inf') else 999,
            "net_pts":round(pts.sum(),0),
            "net_ntd":int(net_ntd),
            "mdd_ntd":int(mdd),
            "cagr":round(cagr*100,1),
            "annual_ntd":int(annual_ntd),
            "avg_win":int(avg_win),
            "avg_loss":int(avg_loss),
            "wl_ratio":round(wl,2)}


results = {name: summarize(t) for name, t in strategies.items()}
print(json.dumps({"start": str(df.index[0].date()),
                  "end":   str(df.index[-1].date()),
                  "bars":  len(df),
                  "results": results}, indent=2, ensure_ascii=False))

with open("/sessions/quirky-focused-pasteur/mnt/outputs/batch01/results.json","w") as f:
    json.dump({"start": str(df.index[0].date()),
               "end":   str(df.index[-1].date()),
               "bars":  len(df),
               "results": results}, f, indent=2, ensure_ascii=False)
