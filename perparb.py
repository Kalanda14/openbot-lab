"""Perp-vs-perp funding spread (rule fixed before results): long Binance USDT-M perp, short Hyperliquid perp, BTC+ETH.
Return per unit notional per day = HL funding - Binance funding + (Binance perp ret - HL perp ret). Always on.
Capital = margin only -> leverageable. No cash deduction (margin capital is the only capital; costs: entry once ignored,
daily rebalancing of margin between venues assumed free). 2023-06..2026-11.
"""
import numpy as np, pandas as pd
TD = "/Users/churchxelachurchxela/Projects/trendbot/data"; legs = []
for c in ("BTC", "ETH"):
    bp = pd.read_csv(f"{TD}/um/{c}USDT.csv", index_col=0, parse_dates=True).close
    bf = pd.read_csv(f"{TD}/fundmaj/{c}USDT.csv"); bf = pd.Series(bf.fundingRate.astype(float).values, pd.to_datetime(bf.fundingTime, unit="ms")).resample("1D").sum()
    hp = pd.read_csv(f"ext/hl_1d_{c}.csv", parse_dates=["t"]).set_index("t").c.astype(float); hp.index = hp.index.normalize()
    hf = pd.read_csv(f"ext/hl_fund_{c}.csv", parse_dates=["t"]).set_index("t").fundingRate.astype(float).resample("1D").sum()
    x = pd.concat([bp.pct_change(), hp.pct_change(), bf, hf], axis=1, keys=["bp", "hp", "bf", "hf"]).dropna()["2023-06-01":]
    legs.append(x.hf - x.bf + x.bp - x.hp)
    print(c, "funding diff %/yr by year:", {y: round(g.mean() * 365 * 100, 1) for y, g in (x.hf - x.bf).groupby(x.index.year)})
r = pd.concat(legs, axis=1).mean(axis=1)
sh = lambda x: x.mean() / x.std() * np.sqrt(365)
print("spread return %/yr by year:", {y: round(g.mean() * 365 * 100, 1) for y, g in r.groupby(r.index.year)})
print("Sharpe by year:", {y: round(sh(g), 1) for y, g in r.groupby(r.index.year)}, "| all %.2f" % sh(r), "| vol %.2f%%/yr" % (r.std() * np.sqrt(365) * 100),
      "| worst day %.2f%% | worst 30d %.2f%%" % (r.min() * 100, r.rolling(30).sum().min() * 100))
print("max single-day BTC move (liquidation check):", round(pd.read_csv(f"{TD}/um/BTCUSDT.csv", index_col=0, parse_dates=True).close.pct_change()["2023-06":].abs().max() * 100, 1), "%")
r.to_frame("PERPARB").to_csv("dbdata/perparb.csv")
