"""Shared setup: roll-fixed ON book (eudrift2 'base' or 'plus'), same build as eubook.build but keeps per-sleeve parts.
Generic 21-day deadline sim with pluggable sigma, legs, caps. Run from openbot-lab."""
import sys, os, io, contextlib
sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab"); os.chdir("/Users/churchxelachurchxela/Projects/openbot-lab")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import goal80 as g, hybrid4 as H, m300b as M
H.start0 = 40
nd = g.norm
D = pd.read_pickle("dbdata/nqD.pkl"); D = D[D.roll == 0]
ld = lambda f: pd.read_csv(f, index_col=0, parse_dates=True)["CLOSE"].astype(float)
ts = (ld("ext/VIX.csv") / ld("ext/VIX3M.csv")).shift(1).reindex(D.index, method="ffill")
down = D.r55 < 0; down2 = down & (D.r55.shift(1) < 0)
ONS = {"base": (D.x0330 - 0.5e-4).where(down, 0),
       "plus": (D.x0330 - 0.5e-4).where(down & (ts > 0.864) & (D.index.weekday != 4), 0) * np.where(down2, 2, 1)}
sh = lambda x: x.mean() / x.std() * np.sqrt(252)

def build(variant="base"):
    on = ONS[variant].shift(1).reindex(g.S.index).fillna(0)
    S = g.S[["B", "TREND"]].assign(ON=on.values)
    w = 1 / S[:"2021"].std(); w = w / w.sum(); sc = {}
    for c in S:
        nz = S[c].where(S[c] != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
        sc[c] = (nz[:"2021"].std() / vol).clip(0, 3).fillna(1).values
    P = {c: w[c] * sc[c] * S[c].values for c in S}
    WP = {"B": w["B"] * sc["B"] * M.bw, "ON": w["ON"] * sc["ON"] * 1.5 * np.minimum(S.ON.values, 0),
          "TREND": w["TREND"] * sc["TREND"] * 2 * np.minimum(S.TREND.values, 0)}
    n = (S.index < "2022").sum(); R = sum(P.values()); k = g.R.std() / R[:n].std()
    P = {c: v * k for c, v in P.items()}; WP = {c: v * k for c, v in WP.items()}
    return P, WP

idx = g.S.index
STARTS = np.arange(H.start0, len(idx) - 30, 2)
S_TR = STARTS[idx[STARTS] < "2024-01-01"]; S_TE = STARTS[idx[STARTS] >= "2024-01-01"]

def sim(R, WR, starts=STARTS, X=300, cap=100, f=0.5, sig=None, legs=None, wlegs=None, levfn=None, days=21):
    """R, WR: day arrays (or legs: list of (R_leg, WR_leg) traded in order within each day, re-sized between legs).
    sig: scalar or per-day array of daily book sigma used in sizing (default g.sig_tr). Leg sigma = sig * sqrt(leg share of var).
    levfn(lev, i_day, W) -> lev for extra caps."""
    G = 400.0 + X; out = []
    if legs is None: legs = [(R, WR)]
    lv = [np.var(l[0][: (idx < "2022").sum()]) for l in legs]; tv = sum(lv)
    for s in starts:
        W = 400.0
        for i in range(days):
            if W >= G: break
            sd = g.sig_tr if sig is None else (sig if np.isscalar(sig) else sig[s + i])
            dead = False
            for j, (r, wr) in enumerate(legs):
                if W >= G: break
                # time left in day units: remaining legs of today count by their variance share
                rem = (days - i - 1) + sum(lv[j:]) / tv
                z = nd.ppf(min(max(W / G, 1e-6), 0.999999))
                lev = nd.pdf(z) * G / (f * sd * np.sqrt(rem) * W)
                if levfn is not None: lev = levfn(lev, s + i, W)
                lev = min(lev, cap)
                if 1 + lev * wr[s + i] <= 0: W = 0.0; dead = True; break
                W *= 1 + lev * r[s + i]
                if W <= 1: W = 0.0; dead = True; break
            if dead: break
        out.append(W)
    o = np.array(out)
    return dict(hit=(o >= G).mean(), lt100=(o < 100).mean(), mid=((o >= 100) & (o < G)).mean(), med=np.median(o), n=len(o))

def browne(R):
    return nd.cdf(nd.ppf(400 / 700) + sh(R) * np.sqrt(21 / 252))

def fmt(d): return f"hit {d['hit']:.0%} <100 {d['lt100']:.0%} mid {d['mid']:.0%}"
