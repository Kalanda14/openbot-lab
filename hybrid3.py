"""Bigger Apex accounts in the 12-month route (rules from 2026 guides, uncertain; activation assumed $129 like 50K).
APEX100: fee $159, target 6000, DD 3000, buffer 3100, caps 2000,2500,3000,4000..; APEX150: fee $249, target 9000, DD 4000,
buffer 4100, caps 2500,3000,4000,5000... Both 50% funded consistency, 5 qualifying days >= $250, max 6 payouts.
MNQ sizes scaled by DD vs 50K: x1.5 / x2. B overlay as plan A2 (5->2, tp $800 scaled the same).
"""
import numpy as np, hybrid as h, goal80 as g
base = dict(h.P.R["APEX"])
R100 = dict(base, fee=159, target=6000, dd=3000, buffer=3100, caps=[2000, 2500, 3000, 4000, 4000, 4000])
R150 = dict(base, fee=249, target=9000, dd=4000, buffer=4100, caps=[2500, 3000, 4000, 5000, 5000, 5000])
fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
for nm, rr, sc in (("50K", base, 1.0), ("100K", R100, 1.5), ("150K", R150, 2.0)):
    T = tuple(h.P.day_table(h.m, h.lo, int(round(k * sc)), 800 * sc, None, None) for k in (5, 2, 2))
    h.r_ap = rr
    for n in (1, 2):
        for en, r in (("backtest", g.R), ("forward1.2", fwd)):
            p, w0, md = h.sim(r, 100, n, T, 300)
            print(f"> {nm} x{n} {en}: 12 mo P(10k) {p:.0%}, wipe {w0:.0%}, median {md:,.0f}", flush=True)
