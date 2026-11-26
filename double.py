"""Month-1 doubling: EUR 400 -> 800 in 21 trading days (deadline sizing toward 800, spread 5x, 2 Apex; deposit 100 at day 21).
Then months 2-12: deadline sizing toward 10k. Report P(doubled in month 1), P(wiped in month 1), and P(10k by month 12)
split by whether month 1 doubled. Compared with the plain one-phase 10k plan."""
import numpy as np, hybrid4 as H, hybrid as h, goal80 as g

def run(r, pas, cap, mult=5, g1=800.0, d1=21, days=252, dep=100):
    res = []
    for s in range(H.start0, len(r) - days, 3):
        W, accts, dbl, wiped1 = g.X0, [], False, False
        for i in range(days):
            if i and i % 21 == 0: W += dep
            if i < d1: G, left, fut = g1, d1 - i, 0
            else: G, left, fut = g.G, days - i, dep * ((days - i) // 21)
            weff = W + fut
            lev = min(g.norm.pdf(g.norm.ppf(max(weff / G, 1e-6))) * G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap) if weff < G else 0.0
            W *= 1 + lev * r[s + i] + mult * pas[s + i]
            if W <= 1: W = 0.0
            pi = h.pidx.get(h.dates[s + i])
            if pi is not None:
                while len(accts) < 2 and W >= h.r_ap["fee"] + h.r_ap["act"] + 300:
                    W -= h.r_ap["fee"]; accts.append(h.P.new_acct(h.r_ap))
                nxt = []
                for a in accts:
                    a, W = h.P.step(a, h.r_ap, H.T, pi, W)
                    if a is not None: nxt.append(a)
                accts = nxt
            if i == d1 - 1: dbl, wiped1 = W >= g1, W < 100
            if i >= d1 and W >= g.G: W = g.G + 1; break
            if W <= 0 and not accts: break
        res.append((dbl, wiped1, W >= g.G))
    a = np.array(res, dtype=bool)
    return a[:, 0].mean(), a[:, 1].mean(), a[:, 2].mean(), a[a[:, 0], 2].mean() if a[:, 0].any() else 0, a[~a[:, 0], 2].mean()

fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
for nm, r, pas in (("backtest", g.R, H.PA), ("cautious", fwd, H.PA26)):
    for cap in (30, 45, 100):
        d, w, t, td, tn = run(r, pas, cap)
        print(f"> {nm} cap {cap}: P(800 in month 1) {d:.0%} | P(<100 after month 1) {w:.0%} | P(10k in 12 mo) {t:.0%} "
              f"[if doubled {td:.0%}, if not {tn:.0%}]", flush=True)
