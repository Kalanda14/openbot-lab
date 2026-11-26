"""Scale with payouts: up to nmax copied accounts, extras bought from wallet only if `reserve` stays after.
Uses each firm's overlay picked earlier on 2017-21 (propsim.py). 12-month horizon. Cells: P(profit)/P(+1k)/P(+10k)/avg."""
import numpy as np, propsim as p
d, m, lo = p.load(); n = len(d); half = int(np.searchsorted(d, "2022-01-01"))
mu = m[:, -1].mean(); ramp = np.linspace(0, 1, m.shape[1])[None, :]; m0, lo0 = m - mu * ramp, lo - mu * ramp
PICK = {"APEX": (5, 2, 800, None), "TRADEIFY_LIGHTNING": (5, 2, 500, None), "LUCID_FLEX": (5, 1, 500, None),
        "TOPSTEP": (12, 2, 800, None)}
f = lambda z: f"{z[0]:.0%} / {z[1]:.0%} / {z[2]:.0%} / ${z[3]:+.0f}"
print("| firm | nmax | reserve | TRAIN 2017-21 | TEST 2022-26 | NO-EDGE test |\n|---|---|---|---|---|---|")
for firm, (ke, kf, tp, sl) in PICK.items():
    r = p.R[firm]; dll = r.get("dll")
    T = tuple(p.day_table(m, lo, k, tp, sl, dll) for k in (ke, kf, kf))
    T0 = tuple(p.day_table(m0, lo0, k, tp, sl, dll) for k in (ke, kf, kf))
    for nmax in (1, 2, 3, 5, 10):
        for res in ((0,) if nmax == 1 else (0, 300, 1000)):
            c = [p.stats(np.array([p.run(r, X, s, 252, nmax, res) for s in rg]))
                 for X, rg in ((T, range(20, half - 252, 6)), (T, range(half, n - 252, 3)), (T0, range(half, n - 252, 3)))]
            print(f"| {firm} | {nmax} | {res} | {f(c[0])} | {f(c[1])} | {f(c[2])} |", flush=True)
