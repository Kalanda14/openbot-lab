"""Audit library: rebuilds the m2 final plan (Browne f0.5 cap100, ON every 30 / B every 30 min, 25% band, goal-touch exit)
on ANY day index (so 2017-19 can be tested), with knobs for retail-CFD costs, real overnight lows, notional caps,
edge haircuts. Calibration (weights, vol scale, sig_tr, book scale) is ALWAYS from 2020-03..2021 as in m2.
Read-only use of project files."""
import sys, os, io, contextlib
sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/m2")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import common as CM
from statistics import NormalDist
g, C = CM.g, CM.C
_ppf = np.vectorize(NormalDist().inv_cdf); pdf = lambda z: np.exp(-z * z / 2) / np.sqrt(2 * np.pi)
LAB = "/Users/churchxelachurchxela/Projects/openbot-lab"

def to_days(s, ix):
    gi = np.clip(ix.searchsorted(s.index, side="left"), 0, len(ix) - 1)
    return (1 + s).groupby(ix[gi]).prod().sub(1).reindex(ix).fillna(0)

def ext_index():
    z = np.load(f"{LAB}/dbdata/paths_real.npz"); return pd.DatetimeIndex(pd.to_datetime(z["d"]))

def bpaths(ix, src="real"):
    f = f"{LAB}/dbdata/paths_real.npz" if src == "real" else f"{LAB}/audit/paths_rt2.npz"
    z = np.load(f); pos = pd.Index(pd.to_datetime(z["d"])).get_indexer(ix); ok = pos >= 0; n = len(ix)
    M = np.zeros((n, 390)); L = np.zeros((n, 390)); P = np.full(n, 1e4)
    M[ok] = z["mtm"][pos[ok]]; L[ok] = z["low"][pos[ok]]; P[ok] = z["px"][pos[ok]]
    M /= P[:, None]; L /= P[:, None]
    opn = np.zeros_like(M, bool); opn[:, 1:] = (L[:, 1:] < M[:, 1:] - 1e-12) | (np.abs(np.diff(M, axis=1)) > 1e-12)
    return M, L, P, opn

def onlegs(ix):
    z = np.load(f"{LAB}/audit/onlow.npz"); d = pd.to_datetime(z["d"])
    out = {}
    for k in ("r", "wc", "wl", "up", "px"):
        a = z[k]; a = a if a.ndim == 2 else a[:, None]
        df = pd.DataFrame(a, index=d).shift(1).reindex(ix)
        out[k] = df.fillna(0 if k != "px" else 2e4).values
    out["px"] = out["px"][:, 0]; return out

def build(ix=None, bsrc="real", trend="stack4", ref=None):
    """ref: an m2-index build whose calibration constants (weights, vol-scale normalisers, book scale k) are reused."""
    ix = g.S.index if ix is None else ix; n = len(ix)
    tr = (ix >= "2020-03-16") & (ix < "2022-01-01")
    M, L, P, opn = bpaths(ix, bsrc)
    jobs = np.array([(t.weekday() == 4 and t.day <= 7) for t in ix]) * 1 + 1
    if trend == "stack4": TR = g.S.TREND.reindex(ix).fillna(0).values
    else:
        t = pd.read_csv("/Users/churchxelachurchxela/Projects/openbot/crypto_daily.csv", index_col=0, parse_dates=True).TREND.fillna(0)
        TR = to_days(t, ix).values
        if trend == "stack4+crypto":  # stack4 where available, crypto before 2020-03-16
            s4 = g.S.TREND.copy(); s4.loc["2020-03-16"] = np.nan; s4 = s4.reindex(ix)  # 2020-03-16 = to_days glitch (all 2017-20 crypto compounded)
            TR = np.where(s4.notna(), s4.fillna(0).values, TR)
    S = {"B": M[:, -1] * jobs, "ON": C.ONS["base"].shift(1).reindex(ix).fillna(0).values, "TREND": TR}
    bw = np.minimum(L.min(1), 0) * jobs
    nstd = {c: pd.Series(S[c]).where(S[c] != 0)[tr].std() for c in S} if ref is None else ref["nstd"]
    def vs(c):
        nz = pd.Series(S[c]).where(S[c] != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
        return (nstd[c] / vol).clip(0, 3).fillna(1).values
    sc = {c: vs(c) for c in S}
    rp = 1 / pd.DataFrame(S)[tr].std(); w = rp / rp.sum()
    if ref is not None: w = ref["rp"]
    Pb = {c: w[c] * sc[c] * S[c] for c in S}
    R = sum(Pb.values()); k = g.R.std() / R[tr].std() if ref is None else ref["k"]
    Pb = {c: v * k for c, v in Pb.items()}
    WP = {"TREND": w["TREND"] * sc["TREND"] * 2 * np.minimum(S["TREND"], 0) * k}
    cB = w["B"] * sc["B"] * k * jobs
    o = onlegs(ix)
    return dict(ix=ix, P=Pb, WP=WP, cB=cB, M=M, L=L, opn=opn, px=P, on=o, w=dict(w.round(3)), nstd=nstd, tr=tr, S=S, sc=sc, k=k, rp=w)

def make(bk, step=30, on_step=30, wsrc="close", wmult=1.25, haircut=1.0):
    """Legs per day: 20 ON legs (TREND added to ON leg 0) then B legs every `step` min. haircut<1 lowers the mean of
    B and ON day returns to haircut x mean (constant subtracted on active days) -> 'forward edge' check."""
    P = bk["P"]; o = bk["on"]; n = len(bk["ix"])
    LG = []
    nz = P["ON"] != 0; x = o["r"].sum(1); craw = np.where(nz, P["ON"] / np.where(nz & (np.abs(x - 0.5e-4) > 1e-12), x - 0.5e-4, 1), 0)
    craw = np.where(nz & (np.abs(x - 0.5e-4) > 1e-12), craw, 0)
    dON = (1 - haircut) * P["ON"][nz].mean() if haircut != 1 else 0
    W = o["wc"] * wmult if wsrc == "close" else o["wl"] * wmult
    for j in range(o["r"].shape[1]):
        r = craw * o["r"][:, j] - (craw * 0.5e-4 if j == 0 else 0)
        if j == 0: r = r + P["TREND"] - np.where(nz, dON, 0)
        LG.append(dict(r=r, w=craw * W[:, j] + (bk["WP"]["TREND"] if j == 0 else 0), up=craw * np.maximum(0, o["r"][:, j]) * 0 + craw * 0,
                       held=nz & (j > 0), px=o["px"], c=craw, grp=0, on=True, j=j))
    # 'up' for ON legs: need best close inside leg; approximated by leg end (conservative for tp) -> tp only on close of leg
    for jj, l in enumerate(LG): l["up"] = craw * o["up"][:, jj]
    M, Lw, opn = bk["M"], bk["L"], bk["opn"]; cB = bk["cB"][:, None]
    b = [0] + list(range(30, 389, step)) + [389]
    act = M[:, -1] != 0; dB = (1 - haircut) * P["B"][act].mean() / np.where(bk["cB"] > 0, bk["cB"], 1) if haircut != 1 else 0
    for jj, (a, e) in enumerate(zip(b[:-1], b[1:])):
        r = (M[:, e] - M[:, a]) * cB[:, 0]
        if e == 389: r = r - np.where(act, dB * bk["cB"], 0)
        LG.append(dict(r=r, w=np.minimum(Lw[:, a + 1:e + 1].min(1) - M[:, a], 0) * cB[:, 0],
                       up=np.maximum(M[:, a + 1:e + 1].max(1) - M[:, a], 0) * cB[:, 0],
                       held=(opn[:, a - 1] & opn[:, min(a + 1, 389)]) if a > 0 else np.zeros(n, bool),
                       px=bk["px"], c=bk["cB"], grp=1, on=False, j=jj, opn=opn[:, min(a + 1, 389)]))
    return LG

def sim(LG, starts, tr, f=0.5, cap=100, band=0.25, tp=True, cost_b=0.25, cost_on=0.25, on_extra_pt=0.0, swap=0.0,
        swap_leg=4, spike_pt=0.0, ncap=None, lot=None, days=21, G=700.0, ret_all=False, tpfix=False):
    """on_extra_pt: extra round-trip points per ON night (entry 15:55 + exit 03:30) beyond the 1.05 pt in the data.
    swap: financing as fraction of ON notional charged at leg `swap_leg` (crosses 00:00 GMT). spike_pt: extra adverse
    bid move (points) inside leg `swap_leg` used only for the wipe test (spread blow-out at CFD rollover).
    ncap: max NQ notional / equity (broker leverage limit)."""
    trn = np.where(tr)[0]
    lv = np.array([np.var(l["r"][trn]) for l in LG]); tv = lv.sum(); tail = np.cumsum(lv[::-1])[::-1] / tv
    W = np.full(len(starts), 400.0); nres = np.zeros(len(starts)); costs = np.zeros(len(starts)); maxn = np.zeros(len(starts))
    swp = np.zeros(len(starts))
    for i in range(days):
        d = starts + i; prev = np.zeros(len(starts)); grp = -1
        for j, l in enumerate(LG):
            act = (W < G) & (W > 1)
            if not act.any(): break
            if l["grp"] != grp: prev = np.zeros(len(starts)); grp = l["grp"]
            rem = (days - i - 1) + tail[j]
            x = np.clip(W / G, 1e-6, 0.999999)
            lev = pdf(_ppf(x)) * G / (f * g.sig_tr * np.sqrt(rem) * np.maximum(W, 1e-9))
            lev = np.minimum(lev, cap)
            c = l["c"][d]
            if ncap is not None: lev = np.minimum(lev, ncap / np.maximum(c, 1e-12))
            if lot is not None:  # min lot granularity: lot = index units per min lot (EUR notional = lot*px/1.1)
                ln = lot * l["px"][d] / 1.1; nl = np.round(lev * c * W / ln)
                lev = np.where(c > 0, nl * ln / np.maximum(c * W, 1e-12), lev)
            h = l["held"][d] & act
            keep = h & (np.abs(lev - prev) <= band * np.maximum(prev, 1e-9)) if band > 0 else np.zeros_like(h)
            lev = np.where(keep, prev, lev)
            ch = h & ~keep & (np.abs(lev - prev) > 1e-9)
            cpt = cost_on if l["on"] else cost_b
            cc = np.where(ch, cpt / l["px"][d] * c * np.abs(lev - prev), 0)
            if l["on"] and l["j"] == 0: cc = cc + np.where(c > 0, on_extra_pt / l["px"][d] * c * lev, 0)
            if l["on"] and l["j"] == swap_leg: cc = cc + np.where(c > 0, swap * c * lev, 0); swp += np.where(act & (c > 0), swap * c * lev, 0)
            W = np.where(act, W * (1 - cc), W); nres += ch; costs += np.where(act, cc, 0)
            pos = (c > 0) if l["on"] else (c > 0) & l["opn"][d]
            maxn = np.where(act & pos, np.maximum(maxn, lev * c), maxn)
            r = l["r"][d]; wv = l["w"][d]
            if l["on"] and l["j"] == swap_leg and spike_pt: wv = wv - spike_pt / l["px"][d] * c
            wiped = act & (1 + lev * wv <= 0)
            hit = act & ~wiped & tp & (W * (1 + lev * l["up"][d]) >= G)
            W = np.where(act, W * (1 + lev * r), W)
            W = np.where(hit, G, W); W = np.where(wiped | (act & (W <= 1)), 0.0, W)
            prev = lev / np.maximum(1 + lev * r, 1e-9)
    o = W
    res = dict(hit=(o >= G).mean(), lt100=(o < 100).mean(), med=np.median(o), nres=nres.mean(), cost=costs.mean(),
               maxn_med=np.median(maxn), maxn_p90=np.percentile(maxn, 90), swap=swp.mean())
    if ret_all: res["W"] = o
    return res

def starts_for(ix, lo, hi, start0=40):
    s = np.arange(start0, len(ix) - 30, 2); d = ix[s]; return s[(d >= lo) & (d < hi)]

fmt = lambda d: f"{d['hit']:.0%} / {d['lt100']:.0%}"
