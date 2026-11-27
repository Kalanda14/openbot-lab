"""(B) Re-size MORE OFTEN inside the B session, on real intraday B paths.
Each day: leg 0 = overnight (ON + TREND [+ EOM3]), then B in sub-legs cut at check times (every `step` minutes from 10:00).
Browne deadline sizing per leg with remaining-variance time (as m1/rule.py), sigma factor f, cap; wipe if 1+lev*worst<=0
(worst = path minimum inside the leg); re-size cost 0.25 pt per MNQ-equivalent of notional change when B holds a position
through a check; optional goal-touch exit (tp) at any minute close inside a B leg; optional no-trade band."""
from statistics import NormalDist
from common import *
_ppf = np.vectorize(NormalDist().inv_cdf); pdf = lambda z: np.exp(-z * z / 2) / np.sqrt(2 * np.pi)

def make(bk, step, on_step=None, on_worst=1.25):
    """step: B check interval in minutes (None -> one B leg, 0 -> whole day one leg). on_step: ON check interval
    (None -> one ON leg). Each leg: r, w (worst), up (best close), held (position carried through leg start),
    px, c (book units per 1 unit raw -> re-size cost), grp (0 = ON block, 1 = B block)."""
    P, WP = bk["P"], bk["WP"]; n = len(idx); Z = np.zeros(n); F = np.zeros(n, bool)
    oth = sum(P[c] for c in P if c not in ("B", "ON")); othw = sum(WP[c] for c in WP if c not in ("B", "ON"))
    if step == 0:
        R = sum(P.values()); return [dict(r=R, w=sum(WP.values()), up=Z, held=F, px=np.full(n, 1e4), c=Z, grp=0)]
    LG = []
    if on_step is None:
        LG.append(dict(r=P["ON"] + oth, w=WP["ON"] + othw, up=Z, held=F, px=np.full(n, 1e4), c=Z, grp=0))
    else:
        o = on_paths(on_step); nz = P["ON"] != 0
        x = o["r"].sum(1); craw = np.where(nz, P["ON"] / np.where(nz, x - 0.5e-4, 1), 0)
        for j in range(o["r"].shape[1]):
            r = craw * o["r"][:, j] - (craw * 0.5e-4 if j == 0 else 0)
            LG.append(dict(r=r + (oth if j == 0 else 0), w=on_worst * craw * o["w"][:, j] + (othw if j == 0 else 0),
                           up=craw * o["up"][:, j], held=nz & (j > 0), px=o["px"], c=craw, grp=0))
    L = legs(bk, 389 if step is None else step)
    for j in range(L["r"].shape[1]):
        LG.append(dict(r=L["r"][:, j], w=L["w"][:, j], up=L["up"][:, j], held=L["held"][:, j], px=L["px"], c=L["cB"], grp=1))
    return LG

def sim(LG, starts, f=0.5, cap=100, cost=0.25, tp=False, band=0.0, bold=False, days=21, G=700.0):
    lv = np.array([np.var(l["r"][:NTR]) for l in LG]); tv = lv.sum(); tail = np.cumsum(lv[::-1])[::-1] / tv
    W = np.full(len(starts), 400.0); nres = np.zeros(len(starts)); costs = np.zeros(len(starts))
    for i in range(days):
        d = starts + i; prev = np.zeros(len(starts)); grp = -1
        for j, l in enumerate(LG):
            act = (W < G) & (W > 1)
            if not act.any(): break
            if l["grp"] != grp: prev = np.zeros(len(starts)); grp = l["grp"]
            rem = (days - i - 1) + tail[j]
            x = np.clip(W / G, 1e-6, 0.999999)
            lev = pdf(_ppf(x)) * G / (f * g.sig_tr * np.sqrt(rem) * np.maximum(W, 1e-9))
            if bold and i == days - 1: lev[:] = cap
            lev = np.minimum(lev, cap)
            h = l["held"][d] & act
            if band > 0:
                keep = h & (np.abs(lev - prev) <= band * np.maximum(prev, 1e-9)); lev = np.where(keep, prev, lev)
            else: keep = np.zeros_like(h)
            ch = h & ~keep & (np.abs(lev - prev) > 1e-9)
            c = np.where(ch, cost / l["px"][d] * l["c"][d] * np.abs(lev - prev), 0)
            W = np.where(act, W * (1 - c), W); nres += ch; costs += np.where(act, c, 0)
            r = l["r"][d]
            wiped = act & (1 + lev * l["w"][d] <= 0)
            hit = act & ~wiped & tp & (W * (1 + lev * l["up"][d]) >= G)
            W = np.where(act, W * (1 + lev * r), W)
            W = np.where(hit, G, W); W = np.where(wiped | (act & (W <= 1)), 0.0, W)
            prev = lev / np.maximum(1 + lev * r, 1e-9)  # fixed contracts -> notional/W drifts with W
    o = W
    return dict(hit=(o >= G).mean(), lt100=(o < 100).mean(), med=np.median(o), nres=nres.mean(), cost=costs.mean())

def fmt(d): return f"{d['hit']:.0%} / {d['lt100']:.0%}"

if __name__ == "__main__":
    import sys
    on = sys.argv[1] if len(sys.argv) > 1 else "base"
    bk = build(on=on, bsrc="real")
    print(f"ON {on}, real CME B paths + real CME ON paths. cells = P(hit 700) / P(end<100). Settings picked on 2020-23 starts; 2024-26 = check.\n")
    print("| sizing | f | all | 2020-23 | 2024-26 | re-sizes/window | cost % |\n|---|---|---|---|---|---|---|")
    for nm, st, ost in (("1 leg/day (daily)", 0, None), ("2 legs/day (ON, B)", None, None), ("ON 1 leg, B every 30 min", 30, None),
                        ("ON 1 leg, B every 5 min", 5, None), ("ON every 60, B every 30 min", 30, 60), ("ON every 30, B every 30 min", 30, 30),
                        ("ON every 15, B every 15 min", 15, 15), ("ON every 5, B every 5 min", 5, 5)):
        LG = make(bk, st, ost)
        for f in (0.4, 0.5):
            a, b, c = sim(LG, STARTS, f), sim(LG, S_TR, f), sim(LG, S_TE, f)
            print(f"| {nm} | {f} | {fmt(a)} | {fmt(b)} | {fmt(c)} | {a['nres']:.0f} | {a['cost']*100:.2f} |", flush=True)
