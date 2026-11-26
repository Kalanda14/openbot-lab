"""Cautious 12-month route with a 3rd prop account trading B on ES (different trades) next to 2 NQ Apex accounts."""
import numpy as np, pandas as pd, hybrid4 as H, hybrid as h, goal80 as g
z = np.load("dbdata/paths_es.npz"); sc = (z["px"][-1] / z["px"])[:, None] * 5.0
mE, lE = z["mtm"].astype(float) * sc, z["low"].astype(float) * sc; eidx = {x: i for i, x in enumerate(z["d"])}
TE = tuple(h.P.day_table(mE, lE, k, 800, None, None) for k in (5, 2, 2))
fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)

def sim(r, pas, mult, cap, n_es, days=252, dep=100):
    out = []
    for s in range(H.start0, len(r) - days, 3):
        W, nq, es = g.X0, [], []
        for i in range(days):
            left = days - i
            if i and i % 21 == 0: W += dep
            weff = W + dep * (left // 21)
            if weff >= g.G: W = g.G + 1; break
            zz = g.norm.ppf(max(weff / g.G, 1e-6))
            lev = min(g.norm.pdf(zz) * g.G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            W *= 1 + lev * r[s + i] + mult * pas[s + i]
            if W <= 1: W = 0.0
            dt = h.dates[s + i]
            for book, cap_n, T, ix in ((nq, 2, H.T, h.pidx), (es, n_es, TE, eidx)):
                pi = ix.get(dt)
                if pi is None: continue
                while len(book) < cap_n and W >= h.r_ap["fee"] + h.r_ap["act"] + 300:
                    W -= h.r_ap["fee"]; book.append(h.P.new_acct(h.r_ap))
                keep = []
                for a in book:
                    a, W = h.P.step(a, h.r_ap, T, pi, W)
                    if a is not None: keep.append(a)
                book[:] = keep
            if W <= 0 and not nq and not es: break
        out.append(W)
    o = np.array(out); return np.mean(o >= g.G), np.mean(o < 100)

for mult, cap in ((5, 30), (5, 45)):
    for n_es in (0, 1):
        p, w0 = sim(fwd, H.PA26, mult, cap, n_es); print(f"> cautious | spread {mult}x cap {cap} | 2 NQ + {n_es} ES prop | P {p:.0%} wipe {w0:.0%}", flush=True)
