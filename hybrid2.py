"""Tune the prop part of the 12-month route. Picked on windows STARTING 2020-03..2021-12, judged on starts 2022+.
Grid: ke (eval MNQ) 5/8/12, kf (funded MNQ) 2/3/5, tp $500/800/1500, 2 Apex accounts, reserve 300, own cap 30x.
"""
import itertools, numpy as np, hybrid as h, goal80 as g
split = int((g.S.index < "2022-01-01").sum())

def sim_split(r, T):
    res = {}
    for nm, rng in (("train", range(0, split - 0, 5)), ("test", range(split, len(r) - 252, 5))):
        out = []
        for s in rng:
            if s + 252 > len(r): continue
            out.append(one(r, s, T))
        o = np.array(out); res[nm] = (np.mean(o >= g.G), np.mean(o < 100))
    return res

def one(r, s, T, dep=100, nprop=2, reserve=300, cap=30, days=252):
    W, accts = g.X0, []
    for i in range(days):
        left = days - i
        if i and i % 21 == 0: W += dep
        weff = W + dep * (left // 21)
        if weff >= g.G: return g.G + 1
        z = g.norm.ppf(max(weff / g.G, 1e-6))
        lev = min(g.norm.pdf(z) * g.G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
        W *= 1 + lev * r[s + i]
        if W <= 1: W = 0.0
        pi = h.pidx.get(h.dates[s + i])
        if pi is not None:
            while len(accts) < nprop and W >= h.r_ap["fee"] + h.r_ap["act"] + reserve:
                W -= h.r_ap["fee"]; accts.append(h.P.new_acct(h.r_ap))
            nxt = []
            for a in accts:
                a, W = h.P.step(a, h.r_ap, T, pi, W)
                if a is not None: nxt.append(a)
            accts = nxt
        if W <= 0 and not accts: return 0.0
    return W

fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
rows = []
for ke, kf, tp in itertools.product((5, 8, 12), (2, 3, 5), (500, 800, 1500)):
    T = h.tables(ke, kf, tp); a = sim_split(g.R, T); rows.append((a["train"][0], ke, kf, tp, a, T))
    print(f"ke{ke} kf{kf} tp{tp}: train {a['train'][0]:.0%} test {a['test'][0]:.0%} (wipe {a['test'][1]:.0%})", flush=True)
rows.sort(key=lambda x: -x[0]); best = rows[0]
f = sim_split(fwd, best[5])
print(f"\nPICKED on train: ke{best[1]} kf{best[2]} tp{best[3]} -> backtest test-starts {best[4]['test'][0]:.0%}, forward-1.2 test-starts {f['test'][0]:.0%} (wipe {f['test'][1]:.0%})")
