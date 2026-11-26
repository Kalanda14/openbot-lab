"""Month-1 with cheap discounted evals bought in bulk (Apex-style sales ~$20-35/eval). Same B paths, same rules,
fee/activation overridden. Picked on 2017-21 by P(profit in 21 days), shown on 2022-26."""
import itertools, numpy as np, propsim as p
d, m, lo = p.load(); n = len(d); half = int(np.searchsorted(d, "2022-01-01")); H = 21
def st(x): return f"{np.mean(x > 0):.0%} / {np.mean(x >= 300):.0%} / {np.mean(x >= 1000):.0%} / ${x.mean():+.0f}"
print("| firm fee act | ke kf tp nmax | TRAIN | TEST 2022-26 |\n|---|---|---|---|")
for firm, fee, act in (("APEX", 20, 85), ("APEX", 35, 129), ("MFF_RAPID", 40, 0), ("TOPSTEP", 25, 149), ("LUCID_FLEX", 40, 0)):
    r = dict(p.R[firm], fee=fee, act=act); C = {}
    def T(k, tp):
        if (k, tp) not in C: C[(k, tp)] = p.day_table(m, lo, k, tp, None, r.get("dll"))
        return C[(k, tp)]
    best = None
    for ke, kf, tp, nm in itertools.product((8, 16, 25, 40), (3, 5, 8, 12), (None, 500, 800, 1500), (1, 3, 5, 10)):
        X = (T(ke, tp), T(kf, tp), T(kf, tp))
        a = np.array([p.run(r, X, s, H, nm, 0) for s in range(20, half - H, 4)])
        sc = (np.mean(a > 0), a.mean())
        if best is None or sc > best[0]: best = (sc, (ke, kf, tp, nm))
    ke, kf, tp, nm = best[1]; X = (T(ke, tp), T(kf, tp), T(kf, tp))
    c = [np.array([p.run(r, X, s, H, nm, 0) for s in rg]) for rg in (range(20, half - H, 2), range(half, n - H))]
    print(f"| {firm} ${fee} ${act} | {ke} {kf} {tp} {nm} | {st(c[0])} | {st(c[1])} |", flush=True)
