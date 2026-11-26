"""Raise month-1 money-back odds: (1) start only in volatile regimes, (2) two differently-sized accounts.
Rule fixed before results: start allowed if 20-day realized vol of NQ (daily close-to-close, real futures) is in the top
40% of its past 252 days. Judged on train starts (2017-21) and test starts (2022-26) separately. 21 trading days."""
import json, itertools, numpy as np, pandas as pd, fundsim as F, propsim as P, month1fund as M
z = np.load("dbdata/rth.npz"); C = z["a"][:, 3, -1]; dd = z["d"]
ret = pd.Series(np.log(C)).diff(); rv = ret.rolling(20).std()
pct = rv.rolling(252).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
pmap = dict(zip(dd, pct.values))
hot = np.array([pmap.get(x, np.nan) > 0.6 for x in F.d])
A = M.A
for nm, setup in (("Topstep 50K Consistency", (25, 8, 500)), ("MFF Rapid 50K", (8, 8, 1500)), ("Apex Intraday 50K", (8, 5, 1500))):
    r = dict(A[nm]); r["fee"] = M.PROMO.get(nm, r["fee"])
    T = tuple(P.day_table(F.m, F.lo, k, setup[2], None, r.get("dll")) for k in (setup[0], setup[1], setup[1]))
    for per, rng in (("train", range(20, F.half - 30, 2)), ("test", range(F.half, F.n - 30, 2))):
        a = np.array([(M.net(r, T, s, 21), hot[s]) for s in rng])
        allp, hp, cp = np.mean(a[:, 0] >= 0), np.mean(a[a[:, 1] == 1, 0] >= 0), np.mean(a[a[:, 1] == 0, 0] >= 0)
        print(f"> {nm} {per}: all starts {allp:.0%} | volatile starts {hp:.0%} (n {int(a[:,1].sum())}) | calm starts {cp:.0%}", flush=True)
