"""Solve: X* = max X  s.t.  min(P_backtest, P_cautious)[ W_21 >= 400 + X ] >= 0.5,
over strategies S = deadline sizing toward 400+X (Browne-optimal for a fixed target) with cap in {30,60,100},
funding spread m in {0,3}, and optionally one Topstep $25 test (25->8 MNQ, tp $500, alerts, activation deferred).
Real days, windows starting 2023-06..; 21 trading days. Bisection on X for each strategy, then take the best."""
import numpy as np, hybrid4 as H, goal80 as g, combo2 as K, fundsim as F, propsim as P

fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
fidx = {d: i for i, d in enumerate(F.d)}
dates = [str(x.date()) for x in g.S.index]
r_t, T_t = K.mk(25, 8, 500, 25); r_t = dict(r_t, act=0)  # activation deferred to month 2


def prob(R, pas, X, cap, m, prop):
    G = 400.0 + X; hits = []
    for s in range(H.start0, len(R) - 30, 2):
        W = 400.0; a = None; pw = 0.0
        if prop: W -= 25; a = P.new_acct(r_t)
        for i in range(21):
            if prop and a is not None:
                pi = fidx.get(dates[s + i])
                if pi is not None: a, pw = P.step(a, r_t, T_t, pi, pw)
            W *= 1 + m * pas[s + i]
            tot = W + pw
            if tot >= G: break
            need = G - pw
            if W > 1:
                lev = min(g.norm.pdf(g.norm.ppf(min(max(W / need, 1e-6), 0.999999))) * need / (g.sig_tr * np.sqrt(21 - i) * W), cap)
                W *= 1 + lev * R[s + i]
            if W <= 1: W = 0.0
        hits.append(W + pw >= G)
    return np.mean(hits)


def solve(cap, m, prop):
    lo, hi = 0.0, 400.0
    for _ in range(9):
        X = (lo + hi) / 2
        p = min(prob(g.R, H.PA, X, cap, m, prop), prob(fwd, H.PA26, X, cap, m, prop))
        lo, hi = (X, hi) if p >= 0.5 else (lo, X)
    return lo


if __name__ == "__main__":
    best = (0, None)
    for cap in (30, 60, 100):
        for m in (0, 3):
            for prop in (False, True):
                X = solve(cap, m, prop)
                pb = prob(g.R, H.PA, X, cap, m, prop); pc = prob(fwd, H.PA26, X, cap, m, prop)
                print(f"> cap {cap} spread {m}x prop {prop}: X* = +EUR {X:.0f}  (backtest {pb:.0%}, cautious {pc:.0%})", flush=True)
                if X > best[0]: best = (X, (cap, m, prop))
    print(f">> SOLUTION: X* = +EUR {best[0]:.0f} with cap {best[1][0]}, spread {best[1][1]}x, Topstep test {best[1][2]}")
