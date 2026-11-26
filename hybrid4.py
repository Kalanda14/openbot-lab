"""12-month route + perp-vs-perp funding spread at a FIXED multiple of equity (it cannot take deadline leverage).
Windows start 2023-06..2025-11 (spread data starts 2023-06). Same own book (cap 30x), +EUR100/mo, 2x Apex 50K (A2).
Cautious: spread return cut to its 2026 level (3.7%/yr) and the own edge cut to Sharpe 1.2."""
import numpy as np, pandas as pd, hybrid as h, goal80 as g
pa = pd.read_csv("dbdata/perparb.csv", index_col=0, parse_dates=True).PERPARB
idx = g.S.index; gi = np.clip(idx.searchsorted(pa.index), 0, len(idx) - 1)
PA = (1 + pa).groupby(idx[gi]).prod().sub(1).reindex(idx).fillna(0).values
PA26 = PA - PA[PA != 0].mean() + 0.037 / 252 * (PA != 0)
start0 = int(idx.searchsorted(pd.Timestamp("2023-06-05")))
T = h.tables(5, 2, 800)

def sim(r, pas, mult, nprop=2, dep=100, days=252, cap=30):
    out = []
    for s in range(start0, len(r) - days, 3):
        W, accts = g.X0, []
        for i in range(days):
            left = days - i
            if i and i % 21 == 0: W += dep
            weff = W + dep * (left // 21)
            if weff >= g.G: W = g.G + 1; break
            z = g.norm.ppf(max(weff / g.G, 1e-6))
            lev = min(g.norm.pdf(z) * g.G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            W *= 1 + lev * r[s + i] + mult * pas[s + i]
            if W <= 1: W = 0.0
            pi = h.pidx.get(h.dates[s + i])
            if nprop and pi is not None:
                while len(accts) < nprop and W >= h.r_ap["fee"] + h.r_ap["act"] + 300:
                    W -= h.r_ap["fee"]; accts.append(h.P.new_acct(h.r_ap))
                nxt = []
                for a in accts:
                    a, W = h.P.step(a, h.r_ap, T, pi, W)
                    if a is not None: nxt.append(a)
                accts = nxt
            if W <= 0 and not accts: break
        out.append(W)
    o = np.array(out); return np.mean(o >= g.G), np.mean(o < 100), len(o)

fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
for nm, r, pas in (("backtest", g.R, PA), ("cautious", fwd, PA26)):
    for mult in (0, 3, 5):
        for n in (0, 2):
            p, w0, k = sim(r, pas, mult, n)
            print(f"> {nm} | spread {mult}x | prop {n} | 12 mo P(10k) {p:.0%} | wipe {w0:.0%} | windows {k}", flush=True)
