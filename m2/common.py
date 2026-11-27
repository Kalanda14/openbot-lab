"""m2 shared setup. Book = vol-managed sleeves B, ON (roll-fixed eudrift2 'base' or 'plus'), TREND, optional EOM3 Treasury.
B sleeve here = B rebuilt from the minute paths (pathsd Dukascopy, or dbdata/paths_real.npz real CME), jobs-Friday 2x,
so the daily book and the intraday sub-legs are the SAME numbers. Read-only use of existing project files."""
import sys, os, io, glob, contextlib
sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab"); sys.path.insert(1, "/Users/churchxelachurchxela/Projects/openbot-lab/m1")
os.chdir("/Users/churchxelachurchxela/Projects/openbot-lab")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import core as C  # m1 core: g, H (start0=40), ONS, STARTS, S_TR, S_TE
g, H, nd, idx = C.g, C.H, C.nd, C.idx
STARTS, S_TR, S_TE = C.STARTS, C.S_TR, C.S_TE
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
NTR = (idx < "2022").sum()
EOM = pd.read_csv("dbdata/eom3_daily.csv",
                  index_col=0, parse_dates=True)["r"].reindex(idx).fillna(0).values
JOBS = np.array([(t.weekday() == 4 and t.day <= 7) for t in idx]) * 1 + 1

def load_paths(src="duka"):
    if src == "duka":
        zs = [np.load(f) for f in sorted(glob.glob("pathsd/*/paths_*.npz"))]
        d = np.concatenate([z["d"] for z in zs]); px = np.concatenate([z["px"] for z in zs])
        mtm = np.vstack([z["mtm"] for z in zs]); low = np.vstack([z["low"] for z in zs])
    else:
        z = np.load("dbdata/paths_real.npz", allow_pickle=True); d, px, mtm, low = z["d"], z["px"], z["mtm"], z["low"]
    pos = pd.Index(pd.to_datetime(d)).get_indexer(idx)
    ok = pos >= 0; n = len(idx)
    M = np.zeros((n, 390)); L = np.zeros((n, 390)); P = np.full(n, 1e4)
    M[ok] = mtm[pos[ok]]; L[ok] = low[pos[ok]]; P[ok] = px[pos[ok]]
    M = M / P[:, None]; L = L / P[:, None]  # fraction of open price, per 1 unit, after costs
    opn = np.zeros_like(M, bool); opn[:, 1:] = (L[:, 1:] < M[:, 1:] - 1e-12) | (np.abs(np.diff(M, axis=1)) > 1e-12)
    return dict(M=M, L=L, px=P, opn=opn, ok=ok)

PATHS = {}
def paths(src):
    if src not in PATHS: PATHS[src] = load_paths(src)
    return PATHS[src]

def vscale(x):
    nz = pd.Series(x).where(x != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
    return (nz[:NTR].std() / vol).clip(0, 3).fillna(1).values

def build(on="base", eom=False, bsrc="duka", wmode="rp", shrink=0.5):
    """Returns dict with P (sleeve day returns, book units), WP (worst-intraday), cB (book units per 1 unit of raw B path frac)."""
    pt = paths(bsrc) if bsrc != "stack4" else None
    if bsrc == "stack4": braw = g.S.B.values; bw = C.M.bw
    else:
        braw = pt["M"][:, -1] * JOBS; bw = np.minimum(pt["L"].min(1), 0) * JOBS
    S = {"B": braw, "ON": C.ONS[on].shift(1).reindex(idx).fillna(0).values, "TREND": g.S.TREND.values}
    if eom: S["EOM"] = EOM
    sc = {c: vscale(S[c]) for c in S}
    V = pd.DataFrame({c: sc[c] * S[c] for c in S})
    rp = 1 / pd.DataFrame(S)[:NTR].std(); rp = rp / rp.sum()
    if wmode == "rp": w = rp
    else:  # train max-Sharpe on vol-managed sleeves (in rp units), long-only, shrunk toward rp
        X = V[:NTR] * rp; mu = X.mean().values; cv = X.cov().values
        ms = np.clip(np.linalg.solve(cv, mu), 0, None); ms = ms / ms.sum()
        w = rp * ((1 - shrink) * pd.Series(ms, index=V.columns) + shrink * 1 / len(rp)) * len(rp)
        w = w / w.sum()
    P = {c: w[c] * V[c].values for c in S}
    WP = {"B": w["B"] * sc["B"] * bw, "ON": w["ON"] * sc["ON"] * 1.5 * np.minimum(S["ON"], 0),
          "TREND": w["TREND"] * sc["TREND"] * 2 * np.minimum(S["TREND"], 0)}
    if eom: WP["EOM"] = w["EOM"] * sc["EOM"] * 1.5 * np.minimum(S["EOM"], 0)
    R = sum(P.values()); k = g.R.std() / R[:NTR].std()
    P = {c: v * k for c, v in P.items()}; WP = {c: v * k for c, v in WP.items()}
    cB = w["B"] * sc["B"] * k * (JOBS if bsrc != "stack4" else 1)
    return dict(P=P, WP=WP, cB=cB, w=dict(w.round(3)), bsrc=bsrc)

def browne(s): return nd.cdf(nd.ppf(400 / 700) + s * np.sqrt(21 / 252))

def legs(bk, step=30, first=30):
    """Intraday legs for B. Boundaries at minutes first, first+step, ..., last=389 (close). B is flat before minute 30.
    Returns per-day arrays: r[d,j], worst[d,j] (min path inside leg minus leg start), up[d,j] (max close inside leg - start),
    held[d,j] (position held through the boundary at leg start -> re-size costs), in book units per 1x lev."""
    pt = paths(bk["bsrc"]); M, L, opn = pt["M"], pt["L"], pt["opn"]
    b = list(range(first, 389, step)) + [389]
    if b[0] != 0: b = [0] + b
    cB = bk["cB"][:, None]
    r, wr, up, held = [], [], [], []
    for a, e in zip(b[:-1], b[1:]):
        r.append(M[:, e] - M[:, a]); wr.append(np.minimum(L[:, a + 1:e + 1].min(1) - M[:, a], 0))
        up.append(np.maximum(M[:, a + 1:e + 1].max(1) - M[:, a], 0)); held.append(opn[:, a - 1] & opn[:, min(a + 1, 389)] if a > 0 else np.zeros(len(M), bool))
    st = lambda x: np.array(x).T
    return dict(r=st(r) * cB, w=st(wr) * cB, up=st(up) * cB, held=st(held), cB=bk["cB"], px=pt["px"], bounds=b)

# ---------- ON (15:55 -> 03:30 ET) intraday legs from real CME 1m closes (roll-fixed days only) ----------
_ONP = {}
def on_paths(step=30):
    """Raw ON path per g.S day t (the night before t): list of sample points every `step` min from 15:55 to 03:30.
    Returns r[t,j], worst[t,j], up[t,j] as fractions of entry price (no cost), px entry, ok flag (path end matches x0330)."""
    if step in _ONP: return _ONP[step]
    NQ = pd.read_pickle("dbdata/nq.pkl")  # close + instrument_id, ET
    D = pd.read_pickle("dbdata/nqD.pkl"); D = D[D.roll == 0]
    dd = pd.Series(D.index, index=D.index).shift(1).reindex(idx); nx = D.nx.shift(1).reindex(idx); xe = D.x0330.shift(1).reindex(idx)
    nsteps = int(np.ceil(575 / step)); n = len(idx)
    r = np.zeros((n, nsteps)); w = np.zeros((n, nsteps)); up = np.zeros((n, nsteps)); P0 = np.full(n, 1e4); ok = np.zeros(n, bool); bad = 0
    ti = NQ.index; cl = NQ.close.values; ins = NQ.instrument_id.values
    for t in range(n):
        if pd.isna(dd.iloc[t]): continue
        a = pd.Timestamp(dd.iloc[t]).tz_localize("America/New_York") + pd.Timedelta(hours=15, minutes=54)  # bar label = start (frame.py)
        e = pd.Timestamp(nx.iloc[t]).tz_localize("America/New_York") + pd.Timedelta(hours=3, minutes=29)
        i0, i1 = ti.searchsorted(a), ti.searchsorted(e, side="right")
        if i1 - i0 < 100 or ti[i0] != a: bad += 1; continue
        k = ins[i0:i1] == ins[i0]  # same contract only (roll-safe)
        seg = pd.Series(cl[i0:i1][k], index=ti[i0:i1][k])
        if seg.index[-1] != ti[i1 - 1]: bad += 1; continue
        p0 = seg.iloc[0]; P0[t] = p0
        mins = np.arange(len(seg), dtype=float)  # trading time = bar count (weekends/holidays compressed)
        if abs(seg.iloc[-1] / p0 - 1 - xe.iloc[t]) > 1e-6: bad += 1; continue
        ok[t] = True; rel = seg.values / p0 - 1
        bnd = [(len(seg) - 1) * k / nsteps for k in range(nsteps + 1)]
        for j in range(nsteps):
            m = (mins > bnd[j]) & (mins <= bnd[j + 1]); s0 = rel[mins <= bnd[j]][-1]
            s1 = rel[mins <= bnd[j + 1]][-1]; r[t, j] = s1 - s0
            if m.any(): w[t, j] = min(rel[m].min() - s0, 0); up[t, j] = max(rel[m].max() - s0, 0)
    _ONP[step] = dict(r=r, w=w, up=up, px=P0, ok=ok, bad=bad); return _ONP[step]
