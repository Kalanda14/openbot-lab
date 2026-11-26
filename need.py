"""How strong must the edge be for a reliable month-1 prop profit? Keep B's real day shapes, add extra drift
per day (ramp through the day) until annual Sharpe hits a target, then search setups for P(profit in 21 days).
All starts 2017-26 (this is a what-if, not a backtest of a real edge)."""
import itertools, numpy as np, propsim as p
d, m, lo = p.load(); n = len(d); H = 21
ramp = np.linspace(0, 1, m.shape[1])[None, :]
f = m[:, -1]; sd = f.std(); base = f.mean() / sd * np.sqrt(252)
print(f"B now: Sharpe {base:.2f}\n\n| annual Sharpe | best firm + setup | P(profit 1 mo) | P(+$1k) | avg $ |\n|---|---|---|---|---|")
for S in (1.2, 2, 3, 4, 6):
    add = (S - base) * sd / np.sqrt(252) if S > base else 0
    mm, ll = m + add * ramp, lo + add * ramp
    best = None
    for firm in ("APEX", "MFF_RAPID", "TOPSTEP", "LUCID_FLEX", "TRADEIFY_LIGHTNING"):
        r = dict(p.R[firm]); C = {}
        def T(k, tp):
            if (k, tp) not in C: C[(k, tp)] = p.day_table(mm, ll, k, tp, None, r.get("dll"))
            return C[(k, tp)]
        for ke, kf, tp in itertools.product((5, 8, 16, 25, 40), (2, 5, 8, 12), (None, 500, 1500)):
            a = np.array([p.run(r, (T(ke, tp), T(kf, tp), T(kf, tp)), s, H) for s in range(20, n - H, 5)])
            sc = (np.mean(a > 0), np.mean(a >= 1000), a.mean())
            if best is None or sc > best[0]: best = (sc, f"{firm} {ke}->{kf} tp {tp}")
    (a, b, c), nm = best
    print(f"| {S} | {nm} | {a:.0%} | {b:.0%} | ${c:+.0f} |", flush=True)
