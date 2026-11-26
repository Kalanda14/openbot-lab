"""BTC hour-of-day effect (rule fixed before results). Binance BTCUSDT 15m -> 1h returns (UTC).
TRAIN 2018-2021: per UTC hour mean and t. Trade in TEST 2022-26: long hours with train t>2, short hours with t<-2,
flat otherwise. Cost 0.07% per side (perp taker 0.05% + 0.02% slip), charged per hour traded (enter+exit if isolated).
Then daily P&L added to the stack."""
import numpy as np, pandas as pd
d = pd.read_csv("/Users/churchxelachurchxela/Projects/trendbot/data/BTCUSDT_15m.csv", index_col=0, parse_dates=True).close
h = d.resample("1h").last().pct_change().dropna()
tr, te = h[:"2021"], h["2022":]
st = tr.groupby(tr.index.hour).agg(["mean", "std", "count"]); st["t"] = st["mean"] / st["std"] * np.sqrt(st["count"])
pos_h = {hr: (1 if t > 2 else -1 if t < -2 else 0) for hr, t in st.t.items()}
print("train t by UTC hour:", {k: round(v, 1) for k, v in st.t.items()})
print("chosen:", {k: v for k, v in pos_h.items() if v})
pos = pd.Series([pos_h[x.hour] for x in h.index], index=h.index)
pnl = pos * h - pos.diff().abs().fillna(0) * 0.0007
day = pnl.resample("1D").sum()
sh = lambda x: x.mean() / x.std() * np.sqrt(365) if x.std() > 0 else 0
te_t = te.groupby(te.index.hour).mean() / te.groupby(te.index.hour).std() * np.sqrt(te.groupby(te.index.hour).count())
print("same hours in TEST (t):", {k: round(te_t[k], 1) for k, v in pos_h.items() if v})
print(f"strategy daily Sharpe TRAIN {sh(day[:'2021']):+.2f} TEST {sh(day['2022':]):+.2f}, TEST %/yr {day['2022':].mean()*365*100:+.1f}")
day.to_frame("HOURS").to_csv("dbdata/hours.csv")
