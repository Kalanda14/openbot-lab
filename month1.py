"""First-month test: profit after 21 trading days (and 42 for context), $400 start, nmax accounts.
Setups picked on 2017-21 starts by P(profit >= $300 in 21 days); shown on 2022-26 + no-edge control."""
import itertools, numpy as np, propsim as p
d, m, lo = p.load(); n = len(d); half = int(np.searchsorted(d, "2022-01-01"))
mu = m[:, -1].mean(); ramp = np.linspace(0, 1, m.shape[1])[None, :]; m0, lo0 = m - mu * ramp, lo - mu * ramp
H = 21
def st(x): return f"{np.mean(x > 0):.0%} / {np.mean(x >= 300):.0%} / {np.mean(x >= 1000):.0%} / ${x.mean():+.0f}"
print("cells: P(profit) / P(+$300) / P(+$1k) / avg $, after 1 month\n\n| firm | ke kf tp sl nmax | TRAIN | TEST 2022-26 | NO-EDGE |\n|---|---|---|---|---|")
for firm, r in p.R.items():
    dll = r.get("dll"); C = {}
    def T(mm, ll, k, tp, sl, key):
        kk = (key, k, tp, sl)
        if kk not in C: C[kk] = p.day_table(mm, ll, k, tp, sl, dll)
        return C[kk]
    best = None
    for ke, kf, tp, sl, nm in itertools.product((5, 8, 12, 16, 25, 40), (1, 2, 3, 5, 8, 12), (None, 300, 500, 800, 1500),
                                                (None, 700, 1000), (1, 2)):
        X = (T(m, lo, ke, tp, sl, 0), T(m, lo, kf, tp, sl, 0), T(m, lo, kf, tp, sl, 0))
        a = np.array([p.run(r, X, s, H, nm, 0) for s in range(20, half - H, 4)])
        sc = (np.mean(a >= 300), a.mean())
        if best is None or sc > best[0]: best = (sc, (ke, kf, tp, sl, nm))
    ke, kf, tp, sl, nm = best[1]
    X = (T(m, lo, ke, tp, sl, 0), T(m, lo, kf, tp, sl, 0), T(m, lo, kf, tp, sl, 0))
    X0 = (T(m0, lo0, ke, tp, sl, 1), T(m0, lo0, kf, tp, sl, 1), T(m0, lo0, kf, tp, sl, 1))
    c = [np.array([p.run(r, Y, s, H, nm, 0) for s in rg]) for Y, rg in
         ((X, range(20, half - H, 2)), (X, range(half, n - H, 1)), (X0, range(half, n - H, 1)))]
    print(f"| {firm} | {ke} {kf} {tp} {sl} {nm} | {st(c[0])} | {st(c[1])} | {st(c[2])} |", flush=True)
