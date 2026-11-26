"""Cross-venue carry: long Binance spot, short Hyperliquid perp, earn HL funding; minus cash (T-bill).
Rule fixed before results: always on, BTC+ETH equal weight, 0.2% one-time entry ignored. Daily UTC closes.
Book: B/ON/TREND risk parity at 15% vol + carry at 3x (Binance carry before 2023-06, HL carry after)."""
import numpy as np, pandas as pd
TD = "/Users/churchxelachurchxela/Projects/trendbot/data"; TB = {2023: 5.1, 2024: 5.0, 2025: 4.2, 2026: 3.8}
legs = []
for c in ("BTC", "ETH"):
    sp = pd.read_csv(f"{TD}/{c}USDT_1d.csv", index_col=0, parse_dates=True).close
    hp = pd.read_csv(f"ext/hl_1d_{c}.csv", parse_dates=["t"]).set_index("t").c.astype(float); hp.index = hp.index.normalize()
    fr = pd.read_csv(f"ext/hl_fund_{c}.csv", parse_dates=["t"]).set_index("t").fundingRate.astype(float).resample("1D").sum()
    x = pd.concat([sp.pct_change(), hp.pct_change(), fr], axis=1, keys=["s", "p", "f"]).dropna()["2023-06-01":]
    legs.append(x.s - x.p + x.f)
c = pd.concat(legs, axis=1).mean(axis=1); rf = pd.Series([TB[t.year] / 100 / 365 for t in c.index], index=c.index); hx = c - rf
sh365 = lambda x: x.mean() / x.std() * np.sqrt(365)
print("HL carry excess: %/yr by year", {y: round(g.mean() * 365 * 100, 1) for y, g in hx.groupby(hx.index.year)},
      "| Sharpe", {y: round(sh365(g), 1) for y, g in hx.groupby(hx.index.year)}, "| worst day %.2f%%" % (hx.min() * 100),
      "| spot-perp daily std %.4f" % (pd.concat(legs, axis=1).mean(axis=1) - c.mean()).std())
S = pd.read_csv("/Users/churchxelachurchxela/Projects/openbot/stack2_daily.csv", index_col=0, parse_dates=True)
g = np.clip(S.index.searchsorted(hx.index), 0, len(S) - 1)
hlS = (1 + hx).groupby(S.index[g]).prod().sub(1).reindex(S.index)
S["CARRY_HL"] = hlS.where(hlS.notna(), S.CARRY).fillna(0)
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
tr = S[:"2021"]; cols = ["B", "ON", "TREND"]; iv = 1 / tr[cols].std(); w = iv / iv.sum(); Rk = S[cols] @ w
k = 0.15 / (Rk[:"2021"].std() * np.sqrt(252))
for nm, cc, lev in (("Binance carry 3x", "CARRY", 3), ("HL carry 3x", "CARRY_HL", 3), ("HL carry 2x", "CARRY_HL", 2), ("HL carry 5x", "CARRY_HL", 5)):
    bk = k * Rk + lev * S[cc]
    for per, a in (("2022-26", "2022"), ("2023-06..", "2023-06")):
        b = bk[a:]; print(f"{nm} | {per}: Sharpe {sh(b):+.2f}, {b.mean()*252*100:+.1f}%/yr", {y: round(sh(x), 1) for y, x in b.groupby(b.index.year)} if per == "2022-26" else "")
S.to_csv("/Users/churchxelachurchxela/Projects/openbot/stack4_daily.csv")
