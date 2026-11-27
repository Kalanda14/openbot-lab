"""Idea 5: optimal DISCRETE sizing by dynamic programming (max P(hit 700 in 21 days)), days drawn iid from the
2020-23 book days (joint R and worst-intraday WR, wipe if 1+lev*WR<=0), cap 100. Table lev*(days_left, W/G) then
applied to the real day sequence. Optional 2 legs/day (ON+TREND, then B). Also DP on Gaussian days = discrete ceiling."""
import numpy as np, sys
from core import *
var = sys.argv[1] if len(sys.argv) > 1 else "base"
P, WP = build(var); R = sum(P.values()); WR = sum(WP.values())
tr = (idx >= idx[H.start0]) & (idx < "2024-01-01")
XG = np.linspace(0, 1, 401); LG = np.concatenate([[0], np.geomspace(0.5, 100, 60)])

def dp(stages, T=21):
    """stages: list of (r, wr) samples, one per sub-step of a day. Returns policy[step] (len T*len(stages)) arrays over XG."""
    V = (XG >= 1).astype(float); pol = []
    for t in range(T * len(stages) - 1, -1, -1):
        r, wr = stages[t % len(stages)]
        best = np.zeros_like(XG); arg = np.zeros_like(XG)
        for L in LG:
            x1 = XG[:, None] * (1 + L * r[None, :])
            v = np.interp(np.minimum(x1, 1), XG, V); v[x1 >= 1] = 1; v[:, 1 + L * wr <= 0] = 0
            ev = v.mean(1); m = ev > best + 1e-12; best[m] = ev[m]; arg[m] = L
        best[-1] = 1; V = best; pol.append(arg)
    return pol[::-1], V

def apply(pol, legs, starts, T=21):
    out = []
    for s in starts:
        W = 400.0; k = 0
        for i in range(T):
            for j, (r, wr) in enumerate(legs):
                if W >= 700 or W <= 1: break
                L = np.interp(W / 700, XG, pol[i * len(legs) + j])
                if 1 + L * wr[s + i] <= 0: W = 0.0; break
                W *= 1 + L * r[s + i]
        out.append(max(W, 0))
    o = np.array(out); return dict(hit=(o >= 700).mean(), lt100=(o < 100).mean(), mid=((o >= 100) & (o < 700)).mean(), med=np.median(o), n=len(o))
def row(nm, pol, legs):
    print(f"{nm:40s} all {fmt(apply(pol, legs, STARTS))} | 20-23 {fmt(apply(pol, legs, S_TR))} | 24-26 {fmt(apply(pol, legs, S_TE))}", flush=True)

print(f"ON {var}; train days {tr.sum()}")
rng = np.random.default_rng(0); mu, sd = R[tr].mean(), R[tr].std()
gz = mu + sd * rng.standard_normal(4000)
_, Vg = dp([(gz, np.full_like(gz, -1e-9))])
print(f"Gaussian (2020-23 mean/std) discrete daily DP ceiling: {np.interp(400/700, XG, Vg):.1%}; Browne {nd.cdf(nd.ppf(4/7) + mu/sd*np.sqrt(21)):.1%}")
pol1, V1 = dp([(R[tr], WR[tr])])
print(f"empirical iid DP value (1 step/day): {np.interp(400/700, XG, V1):.1%}")
row("5a: DP policy, 1 step/day", pol1, [(R, WR)])
legs = [(P["ON"] + P["TREND"], WP["ON"] + WP["TREND"]), (P["B"], WP["B"])]
pol2, V2 = dp([(l[0][tr], l[1][tr]) for l in legs])
print(f"empirical iid DP value (2 legs/day): {np.interp(400/700, XG, V2):.1%}")
row("5b: DP policy, 2 legs/day", pol2, legs)
for d in (21, 10, 5, 1):
    print(f"  1-step policy lev at days_left {d:2d}: " + " ".join(f"W={int(x*700)}:{np.interp(x, XG, pol1[21-d]):.0f}x" for x in (0.2, 0.4, 4/7, 0.8, 0.95)))
    # Browne f0.5 for comparison
    print(f"     Browne f0.5 cap100            : " + " ".join(f"W={int(x*700)}:{min(nd.pdf(nd.ppf(x))/(0.5*g.sig_tr*np.sqrt(d)*x),100):.0f}x" for x in (0.2, 0.4, 4/7, 0.8, 0.95)))
np.save("pol1_%s.npy" % var, np.array(pol1)); np.save("pol2_%s.npy" % var, np.array(pol2))
