"""Idea 1: where is the gap between Browne (~75%) and the real-day sim (~62%) lost?"""
import numpy as np
from core import *
import vnorm as SN

for var in ("base", "plus"):
    P, WP = build(var); R = sum(P.values()); WR = sum(WP.values())
    print(f"\n=== ON {var}: book Sharpe all {sh(R):.2f}, 2020-23 {sh(R[idx<'2024']):.2f}, 2024-26 {sh(R[idx>='2024']):.2f} | Browne(all) {browne(R):.1%}")
    chk = M.run(R, WR, H.PA, 300, 100, 0, 0.5, 0.0)
    print(f"check vs m300b.run: {chk[0]:.1%} <100 {chk[3]:.1%}")
    for nm, kw in (("real f0.5 cap100", {}), ("no wipe", dict(WR=np.zeros_like(R))), ("no cap", dict(cap=1e9)),
                   ("no wipe no cap", dict(WR=np.zeros_like(R), cap=1e9)), ("f1.0 (Browne exact)", dict(f=1.0)),
                   ("f1.0 no wipe no cap", dict(f=1.0, WR=np.zeros_like(R), cap=1e9))):
        a = dict(R=R, WR=WR); a.update(kw)
        print(f"  {nm:24s} all {fmt(sim(**a))} | 20-23 {fmt(sim(**a, starts=S_TR))} | 24-26 {fmt(sim(**a, starts=S_TE))}")
    # sigma misestimation: realized window std vs sig_tr
    rs = np.array([R[s:s + 21].std() for s in STARTS]); rm = np.array([R[s:s + 21].mean() for s in STARTS])
    print(f"  sig_tr {g.sig_tr:.4f}  full-sample std {R.std():.4f}  window std median {np.median(rs):.4f} (p10 {np.percentile(rs,10):.4f} p90 {np.percentile(rs,90):.4f})")
    print(f"  window Sharpe (ann) median {np.median(rm/rs)*np.sqrt(252):.2f}; frac windows mean<0 {np.mean(rm<0):.0%}")
    print(f"  kurtosis of R {((R-R.mean())**4).mean()/R.var()**2:.1f}; skew {((R-R.mean())**3).mean()/R.std()**3:.2f}; worst day {R.min()/R.std():.1f} sd; worst WR {WR.min()/R.std():.1f} sd")

# Gaussian iid with same mean/std as the base book: discreteness and cap effects only
P, WP = build("base"); R = sum(P.values()); mu, sd = R.mean(), R.std()
rng = np.random.default_rng(1)
def gsim(m=1, f=1.0, cap=1e9, N=20000, boot=None):
    G = 700.0; W = np.full(N, 400.0); alive = np.ones(N, bool)
    for i in range(21):
        for j in range(m):
            rem = (21 - i) - j / m
            z = SN.ppf(np.clip(W / G, 1e-6, 0.999999))
            lev = np.minimum(SN.pdf(z) * G / (f * sd * np.sqrt(rem) * np.maximum(W, 1e-9)), cap)
            if boot is None: r = mu / m + sd / np.sqrt(m) * rng.standard_normal(N)
            else: r = rng.choice(boot, N)
            act = alive & (W < G)
            W = np.where(act, W * (1 + lev * r), W); W = np.maximum(W, 0)
            alive &= W > 1
    return (W >= G).mean(), (W < 100).mean()
print("\n=== synthetic paths (base book mean/std) ===")
print(f"  Browne theory {browne(R):.1%}")
for nm, kw in (("Gauss continuous (50 steps/day) f1", dict(m=50)), ("Gauss daily f1 no cap", {}), ("Gauss daily f1 cap100", dict(cap=100)),
               ("Gauss daily f0.5 cap100", dict(f=0.5, cap=100)), ("iid bootstrap real days f1 nocap", dict(boot=R)),
               ("iid bootstrap f0.5 cap100", dict(boot=R, f=0.5, cap=100))):
    p, l = gsim(**kw); print(f"  {nm:36s} hit {p:.1%} <100 {l:.1%}")
