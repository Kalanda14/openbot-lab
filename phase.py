"""(1) Two-phase plan vs one-phase deadline plan (cautious, 12 mo, 400+100/mo, 2x Apex, spread 5x, cap 45).
Phase plan: first 63 days aim for 2x money (deadline sizing with goal = 2*(W0+deposits so far)), then aim for 10k.
(2) What spread multiple / risky Sharpe would cautious need for 80%."""
import numpy as np, hybrid4 as H, hybrid as h, goal80 as g

def sim(r, pas, mult, cap=45, phase=False, days=252, dep=100, nprop=2):
    out = []
    for s in range(H.start0, len(r) - days, 3):
        W, accts = g.X0, []
        for i in range(days):
            if i and i % 21 == 0: W += dep
            if phase and i < 63:
                G, left = 2 * (g.X0 + dep * (i // 21)), 63 - i; fut = dep * ((63 - i) // 21)
            else:
                G, left = g.G, days - i; fut = dep * (left // 21)
            weff = W + fut
            if weff < G:
                zz = g.norm.ppf(max(weff / G, 1e-6))
                lev = min(g.norm.pdf(zz) * G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            else: lev = 0.0
            if not phase and weff >= g.G: W = g.G + 1; break
            W *= 1 + lev * r[s + i] + mult * pas[s + i]
            if W <= 1: W = 0.0
            pi = h.pidx.get(h.dates[s + i])
            if nprop and pi is not None:
                while len(accts) < nprop and W >= h.r_ap["fee"] + h.r_ap["act"] + 300:
                    W -= h.r_ap["fee"]; accts.append(h.P.new_acct(h.r_ap))
                nxt = []
                for a in accts:
                    a, W = h.P.step(a, h.r_ap, H.T, pi, W)
                    if a is not None: nxt.append(a)
                accts = nxt
            if W >= g.G: W = g.G + 1; break
            if W <= 0 and not accts: break
        out.append(W)
    o = np.array(out); return np.mean(o >= g.G), np.mean(o < 100)

fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
for ph in (False, True):
    p, w = sim(fwd, H.PA26, 5, phase=ph); print(f"> cautious {'two-phase (2x in 3 mo first)' if ph else 'one-phase deadline'}: P {p:.0%} wipe {w:.0%}", flush=True)
for mult in (12, 20):
    p, w = sim(fwd, H.PA26, mult); print(f"> cautious spread {mult}x cap 45: P {p:.0%} wipe {w:.0%}", flush=True)
for shp in (1.6, 2.0, 2.4):
    rr = g.R - g.R.mean() + shp * g.R.std() / np.sqrt(252)
    p, w = sim(rr, H.PA26, 5); print(f"> risky edge Sharpe {shp} (spread 2026 level 5x, cap 45): P {p:.0%} wipe {w:.0%}", flush=True)
