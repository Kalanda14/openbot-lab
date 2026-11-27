"""DP policy (as m1/dp.py) with finer legs: lev*(step, W/G) maximizing P(hit 700 in 21 days), sub-legs drawn iid from
2020-23 per stage (joint r and worst per leg; wipe if 1+lev*worst<=0), cap 100. Applied to the real sequence with
re-size cost 0.25 pt, optional tp (goal touch) and 25% band. NOTE iid draw ignores within-day dependence of sub-legs."""
import sys, time
from intraday import *
st, ost = (int(sys.argv[1]) if sys.argv[1] != "None" else None), (int(sys.argv[2]) if sys.argv[2] != "None" else None)
bk = build(bsrc="real"); LG = make(bk, st, ost); ns = len(LG)
tr = np.where((idx >= idx[H.start0]) & (idx < "2024-01-01"))[0]
rng = np.random.default_rng(0); smp = rng.choice(tr, min(500, len(tr)), replace=False)
XG = np.linspace(0, 1, 201); LV = np.concatenate([[0], np.geomspace(0.5, 100, 40)])
t0 = time.time(); V = (XG >= 1).astype(float); pol = []
for t in range(21 * ns - 1, -1, -1):
    l = LG[t % ns]; r, wr = l["r"][smp], l["w"][smp]
    best = np.zeros_like(XG); arg = np.zeros_like(XG)
    for L in LV:
        x1 = XG[:, None] * (1 + L * r[None, :])
        v = np.interp(np.minimum(x1, 1), XG, V); v[x1 >= 1] = 1; v[:, 1 + L * wr <= 0] = 0
        ev = v.mean(1); m = ev > best + 1e-12; best[m] = ev[m]; arg[m] = L
    best[-1] = 1; V = best; pol.append(arg)
pol = pol[::-1]; print(f"legs/day {ns}, DP value {np.interp(4/7, XG, V):.1%}, {time.time()-t0:.0f}s")

def apply(starts, tp=True, band=0.25, cost=0.25, G=700.0):
    W = np.full(len(starts), 400.0)
    for i in range(21):
        d = starts + i; prev = np.zeros(len(starts)); grp = -1
        for j, l in enumerate(LG):
            act = (W < G) & (W > 1)
            if l["grp"] != grp: prev[:] = 0; grp = l["grp"]
            lev = np.interp(W / G, XG, pol[i * ns + j])
            h = l["held"][d] & act
            keep = h & (np.abs(lev - prev) <= band * np.maximum(prev, 1e-9)); lev = np.where(keep, prev, lev)
            ch = h & ~keep & (np.abs(lev - prev) > 1e-9)
            W = np.where(ch, W * (1 - cost / l["px"][d] * l["c"][d] * np.abs(lev - prev)), W)
            wiped = act & (1 + lev * l["w"][d] <= 0); hit = act & ~wiped & tp & (W * (1 + lev * l["up"][d]) >= G)
            W = np.where(act, W * (1 + lev * l["r"][d]), W); W = np.where(hit, G, W); W = np.where(wiped | (act & (W <= 1)), 0.0, W)
            prev = lev / np.maximum(1 + lev * l["r"][d], 1e-9)
    return dict(hit=(W >= G).mean(), lt100=(W < 100).mean())
for nm, kw in (("DP, no tp, no band", dict(tp=False, band=0)), ("DP + tp + band25%", {})):
    print(f"| DP B{st}/ON{ost} | {nm} | {fmt(apply(STARTS, **kw))} | {fmt(apply(S_TR, **kw))} | {fmt(apply(S_TE, **kw))} |", flush=True)
