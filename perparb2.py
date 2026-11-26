"""Perp-vs-perp funding spread on all big coins on both venues (rule fixed before results).
Coins: BTC ETH SOL BNB XRP DOGE ADA AVAX LINK LTC DOT BCH TRX XLM. Drop a coin if its daily (Binance perp - HL perp)
return std over its first 120 days > 0.5% (bad data / illiquid). Equal weight over coins with data that day."""
import numpy as np, pandas as pd
TD = "/Users/churchxelachurchxela/Projects/trendbot/data"; legs = {}
for c in "BTC ETH SOL BNB XRP DOGE ADA AVAX LINK LTC DOT BCH TRX XLM".split():
    try:
        bp = pd.read_csv(f"{TD}/um/{c}USDT.csv", index_col=0, parse_dates=True).close
        bf = pd.read_csv(f"{TD}/fundmaj/{c}USDT.csv"); bf = pd.Series(bf.fundingRate.astype(float).values, pd.to_datetime(bf.fundingTime, unit="ms")).resample("1D").sum()
        hp = pd.read_csv(f"ext/hl_1d_{c}.csv", parse_dates=["t"]).set_index("t").c.astype(float); hp.index = hp.index.normalize()
        hf = pd.read_csv(f"ext/hl_fund_{c}.csv", parse_dates=["t"]).set_index("t").fundingRate.astype(float).resample("1D").sum()
    except Exception as e: print(c, "missing", e); continue
    x = pd.concat([bp.pct_change(), hp.pct_change(), bf, hf], axis=1, keys=["bp", "hp", "bf", "hf"]).dropna()["2023-06-01":]
    if len(x) < 150 or (x.bp - x.hp).iloc[:120].std() > 0.005: print(c, "dropped (noisy/short)"); continue
    legs[c] = x.hf - x.bf + x.bp - x.hp
L = pd.concat(legs, axis=1); r = L.mean(axis=1)
sh = lambda x: x.mean() / x.std() * np.sqrt(365)
print("coins:", list(legs))
print("per coin %/yr:", {c: round(v.mean() * 365 * 100, 1) for c, v in legs.items()})
print("basket %/yr by year:", {y: round(g.mean() * 365 * 100, 1) for y, g in r.groupby(r.index.year)},
      "| Sharpe by year:", {y: round(sh(g), 1) for y, g in r.groupby(r.index.year)}, "| all %.2f | worst day %.2f%% | worst 30d %.2f%%" % (sh(r), r.min() * 100, r.rolling(30).sum().min() * 100))
r.to_frame("PERPARB").to_csv("dbdata/perparb2.csv")
