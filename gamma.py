"""T2 (critic, pre-registered): dealer gamma / VIX regime sizing for B. Real NQ, B single grid, cost 0.7 pt.
Signals from the PREVIOUS day only: GEX percentile in a rolling 252-day window (SqueezeMetrics DIX.csv),
VIX/VIX3M (CBOE). Monthly OPEX = 3rd Friday.
Rule fixed now: 1.5x if GEX pct < 30% or VIX/VIX3M >= 1; 0.5x if GEX pct > 70% or OPEX Friday; else 1x
(1.5x wins over 0.5x if both). Success: test Sharpe >= plain + 0.15 AND low-gamma mean > high-gamma mean in both halves.
"""
import numpy as np, pandas as pd

t = np.load("dbdata/tranche.npz"); b = pd.Series(t["single"] / t["px"] * 100, index=pd.to_datetime(t["d"]))[14:]
g = pd.read_csv("ext/DIX.csv", parse_dates=["date"]).set_index("date").gex
gp = g.rolling(252).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
v = pd.read_csv("ext/VIX.csv", parse_dates=["DATE"]).set_index("DATE").CLOSE
v3 = pd.read_csv("ext/VIX3M.csv", parse_dates=["DATE"]).set_index("DATE").CLOSE
ratio = (v / v3).dropna()
prev = lambda s: s.reindex(s.index.union(b.index)).ffill().shift(1).reindex(b.index)
GP, RT = prev(gp), prev(ratio)
opex = pd.Series([(x.weekday() == 4) and (15 <= x.day <= 21) for x in b.index], index=b.index)
low = (GP < 0.3) | (RT >= 1); high = ((GP > 0.7) | opex) & ~low
w = pd.Series(1.0, index=b.index); w[low] = 1.5; w[high] = 0.5
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
L = ["| | all | 2017-21 | 2022-26 |", "|---|---|---|---|"]
for nm, x in (("plain B", b), ("gamma/VIX sized", b * w)):
    L.append(f"| {nm} Sharpe | {sh(x):+.2f} | {sh(x[:'2021']):+.2f} | {sh(x['2022':]):+.2f} |")
for nm, m in (("low gamma / VIX inverted", low), ("high gamma or OPEX", high), ("middle", ~low & ~high)):
    L.append(f"| {nm}: days / mean %/day | {m.sum()} / {b[m].mean():+.3f} | {m[:'2021'].sum()} / {b[:'2021'][m[:'2021']].mean():+.3f} | "
             f"{m['2022':].sum()} / {b['2022':][m['2022':]].mean():+.3f} |")
L.append(f"\nOPEX Fridays alone: mean {b[opex].mean():+.3f}%/day (n {opex.sum()}) vs others {b[~opex].mean():+.3f}")
for nm, s in (("GEX pct", GP), ("VIX/VIX3M", RT)):
    q = pd.qcut(s.dropna(), 5, labels=False); L.append(f"{nm} quintiles mean %/day: " + ", ".join(f"Q{i+1} {b[q[q == i].index].mean():+.3f}" for i in range(5)))
open("gamma.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
