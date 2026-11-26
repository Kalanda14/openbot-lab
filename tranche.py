"""T3 (critic, pre-registered): timing tranches + NQ costs, real CME NQ 1m (dbdata/rth.npz).
6 copies of B, check grid offset o = 0,5,..,25 min (entries from 10:00+o every 30 min, exits on the same grid,
flat 15:59), each 1/6 size. Costs per NQ-equivalent round trip: 1.12 pt (MNQ, old) vs 0.7 pt (1 NQ).
Success: Sharpe gain >= 0.05 in both halves, max drawdown not worse.
Saves daily P&L (points) to dbdata/tranche.npz for later tests.
"""
import numpy as np, pandas as pd

z = np.load("dbdata/rth.npz"); d = z["d"]; O, H, L, C = (z["a"][:, i, :] for i in range(4)); N = 390; nd = len(d)
o0 = O[:, 0]; pc = np.r_[o0[0], C[:-1, -1]]; pc = np.where(np.abs(pc / o0 - 1) > 0.03, o0, pc)
mv = np.abs(C / o0[:, None] - 1)
sg = pd.DataFrame(mv).rolling(14).mean().shift(1).values  # per minute, past 14 days only
ub = np.maximum(o0, pc)[:, None] * (1 + sg); lb = np.minimum(o0, pc)[:, None] * (1 - sg)


def b(off, rt):
    out = np.zeros(nd)
    for i in range(14, nd):
        pos, e, pn = 0, 0.0, 0.0
        for k in range(30 + off, N - 1, 30):
            c = C[i, k]
            if pos and ((pos == 1 and c < ub[i, k]) or (pos == -1 and c > lb[i, k])): pn += (c - e) * pos - rt; pos = 0
            if not pos:
                if c > ub[i, k]: pos, e = 1, c
                elif c < lb[i, k]: pos, e = -1, c
        if pos: pn += (C[i, -1] - e) * pos - rt
        out[i] = pn
    return out


sh = lambda x: x.mean() / x.std() * np.sqrt(252)
dd = lambda x: (np.cumsum(x) - np.maximum.accumulate(np.cumsum(x))).min()
tr = np.array([x < "2022" for x in d]); tr[:14] = False; te = np.array([x >= "2022" for x in d])
res = {"single 1.12": b(0, 1.12), "single 0.70": b(0, 0.70)}
cp = [b(o, 0.70) for o in range(0, 30, 5)]
res["6 tranches 0.70"] = np.mean(cp, axis=0)
L = ["| version | all Sharpe | 2017-21 | 2022-26 | max DD (pts, 1 NQ) | worst day |", "|---|---|---|---|---|---|"]
for k, x in res.items():
    a = x[14:]
    L.append(f"| {k} | {sh(a):+.2f} | {sh(x[tr]):+.2f} | {sh(x[te]):+.2f} | {dd(a):.0f} | {a.min():.0f} |")
L.append("\nsingle offsets (0.70): " + ", ".join(f"+{o}m {sh(x[14:]):+.2f}" for o, x in zip(range(0, 30, 5), cp)))
L.append(f"avg corr between offsets: {np.mean([np.corrcoef(cp[i][14:], cp[j][14:])[0,1] for i in range(6) for j in range(i+1,6)]):.2f}")
np.savez_compressed("dbdata/tranche.npz", d=d, single=res["single 0.70"], tr6=res["6 tranches 0.70"], px=o0)
open("tranche.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
