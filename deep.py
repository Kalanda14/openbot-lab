"""DEEP SEARCH on real CME NQ futures 1m bars (Databento, 2017-26, 9:30-16:00 NY). Rules fixed before results.
One trade per strategy per day: enter at the close of decision minute t, hold h minutes (or to 15:59), cost 1.12 pt.
Features at t (only data up to t): open-ret, ret30, ret5, gap, vwap-dist, range-pos, prev-day ret,
  open-ret x high-volume, ret30 x high-vol regime, open-ret x low-vol regime.
Strategy = feature x direction (with / against) x filter (all days / only top 30% |feature|, cut from train) x
  t in 10:00..15:30 every 30 min x h in (30, 60, close).
Train 2017-21 picks, test 2022-26 judges. Multiple-testing check: fraction surviving vs what pure luck gives.
Part 2: ridge model on all features, retrained each year on past years only (walk-forward).
Usage: python deep.py  -> deep.md
"""
import glob, numpy as np, pandas as pd, databento as db

N, RT = 390, 1.12


def load():
    try: return np.load("dbdata/rth.npz")
    except FileNotFoundError: pass
    df = pd.concat([db.DBNStore.from_file(f).to_df()[["open", "high", "low", "close", "volume"]]
                    for f in sorted(glob.glob("dbdata/nq_1m_*.dbn.zst"))])
    df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()].sort_index()
    D, A = [], []
    for d, g in df.groupby(df.index.date):
        g = g.between_time("09:30", "15:59")
        if pd.Timestamp(d).weekday() > 4 or len(g) < N * 0.9: continue
        g = g.copy(); g.index = g.index.hour * 60 + g.index.minute - 570
        g = g.reindex(range(N)); g["volume"] = g["volume"].fillna(0); g = g.ffill().bfill()
        D.append(str(d)); A.append(g[["open", "high", "low", "close", "volume"]].values.T)
    np.savez_compressed("dbdata/rth.npz", d=np.array(D), a=np.array(A, dtype=np.float64))
    return np.load("dbdata/rth.npz")


z = load(); d = z["d"]; O, H, L, C, V = (z["a"][:, i, :] for i in range(5))
nd = len(d); o0 = O[:, 0]
pc = np.r_[np.nan, C[:-1, -1]]; pc = np.where(np.abs(pc / o0 - 1) > 0.03, o0, pc)  # roll days
ppc = np.r_[np.nan, pc[:-1]]
cv = V.cumsum(1); vw = (C * V).cumsum(1) / np.maximum(cv, 1)
cvavg = pd.DataFrame(cv).rolling(14).mean().shift(1).values
r1 = np.abs(np.diff(np.log(C), axis=1, prepend=np.log(C[:, :1])))
rv30 = pd.DataFrame(r1.T).rolling(30).sum().T.values
rvavg = pd.DataFrame(rv30).rolling(14).mean().shift(1).values
hi, lo = np.maximum.accumulate(H, 1), np.minimum.accumulate(L, 1)
T = list(range(30, 361, 30)); HZ = (30, 60, "close")
tr = np.array([x < "2022-01-01" for x in d]); te = ~tr; tr[:20] = False


def feats(t):
    c = C[:, t]
    f = dict(openret=c / o0 - 1, ret30=c / C[:, t - 30] - 1, ret5=c / C[:, t - 5] - 1, gap=o0 / pc - 1,
             vwap=c / vw[:, t] - 1, rangepos=(c - lo[:, t]) / np.maximum(hi[:, t] - lo[:, t], 1e-9) - 0.5,
             prevday=pc / ppc - 1)
    hv = cv[:, t] > cvavg[:, t]; hr = rv30[:, t] > rvavg[:, t]
    f["openret_hivol"] = np.where(hv, f["openret"], 0); f["ret30_hirv"] = np.where(hr, f["ret30"], 0)
    f["openret_lorv"] = np.where(~hr, f["openret"], 0)
    return {k: np.nan_to_num(v) for k, v in f.items()}


def fwd(t, h):
    e = N - 1 if h == "close" else min(t + h, N - 1)
    return C[:, e] - C[:, t]


sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0
tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0.0
rows = []
for t in T:
    F = feats(t)
    for h in HZ:
        R = fwd(t, h)
        for nm, f in F.items():
            cut = np.quantile(np.abs(f[tr][f[tr] != 0]), 0.7) if (f[tr] != 0).any() else 0
            for filt in ("all", "top30"):
                s = np.sign(f) * ((np.abs(f) >= cut) if filt == "top30" else 1)
                for dr in (1, -1):
                    p = dr * s * R - RT * (s != 0)
                    rows.append(dict(feat=nm, filt=filt, dir="with" if dr == 1 else "against", t=f"{9 + (30 + t) // 60}:{(30 + t) % 60:02d}",
                                     h=h, trS=sh(p[tr]), trt=tt(p[tr]), teS=sh(p[te]), tet=tt(p[te]), p=p))
df = pd.DataFrame(rows)
n = len(df); good = df[df.trt > 2]; both = good[good.tet > 2]
L = [f"# Deep search on real NQ futures ({nd} days)\n", f"strategies tested: {n}",
     f"train t>2: {len(good)} (luck alone ~{0.023 * n:.0f}); of those also test t>2: {len(both)} (luck alone ~{0.023 * len(good):.1f})\n",
     "## Top 15 by TRAIN (what we would have picked), and how they did on unseen 2022-26\n",
     "| feature | filter | dir | time | hold | train Sharpe | train t | TEST Sharpe | test t |", "|---|---|---|---|---|---|---|---|---|"]
for _, r in df.sort_values("trt", ascending=False).head(15).iterrows():
    L.append(f"| {r.feat} | {r.filt} | {r.dir} | {r.t} | {r.h} | {r.trS:+.2f} | {r.trt:+.1f} | {r.teS:+.2f} | {r.tet:+.1f} |")
# portfolio of everything with train t>2 (equal weight, one unit each) - the honest 'combine all the good ones'
if len(good):
    P = np.vstack(good.p.values).mean(0)
    L.append(f"\nEqual-weight portfolio of all {len(good)} train-t>2 rules: train Sharpe {sh(P[tr]):+.2f}, TEST Sharpe {sh(P[te]):+.2f} (t {tt(P[te]):+.1f})")
# B on same data for reference
zb = np.load("dbdata/paths_real.npz"); bp = pd.Series(zb["mtm"][:, -1], index=zb["d"])
L.append(f"Reference B: train {sh(bp[bp.index < '2022'].values):+.2f}, test {sh(bp[bp.index >= '2022'].values):+.2f}")
corr = [np.corrcoef(r.p[te], bp.reindex(d[te]).fillna(0).values)[0, 1] for _, r in both.iterrows()] if len(both) else []

# Part 2: walk-forward ridge, one model per decision time, target = next-30-min move, trade sign if |pred| > train median
yrs = np.array([int(x[:4]) for x in d]); wf = np.zeros(nd)
for t in T[:-1]:
    F = feats(t); X = np.column_stack([v / (np.std(v[tr]) + 1e-12) for v in F.values()]); y = fwd(t, 30)
    for Y in range(2019, 2027):
        a = (yrs < Y) & (np.arange(nd) >= 20); b = yrs == Y
        if not b.any(): continue
        w = np.linalg.solve(X[a].T @ X[a] + 50 * np.eye(X.shape[1]), X[a].T @ y[a])
        pa, pb = X[a] @ w, X[b] @ w; th = np.median(np.abs(pa))
        s = np.sign(pb) * (np.abs(pb) > th); wf[b] += s * y[b] - RT * (s != 0)
m = yrs >= 2019
L.append(f"\n## Part 2: walk-forward ridge (all features, 11 decision times, hold 30 min)\n"
         f"2019-26 out-of-sample Sharpe {sh(wf[m]):+.2f} (t {tt(wf[m]):+.1f}); 2022-26 {sh(wf[yrs >= 2022]):+.2f}; by year: " +
         ", ".join(f"{Y} {sh(wf[yrs == Y]):+.1f}" for Y in range(2019, 2027)))
if len(both):
    L.append(f"\nSurvivors (train t>2 AND test t>2): {len(both)}; mean corr with B on test {np.nanmean(corr):+.2f}")
    for _, r in both.iterrows():
        L.append(f"- {r.feat} {r.filt} {r.dir} at {r.t} hold {r.h}: train {r.trS:+.2f} / test {r.teS:+.2f}")
open("deep.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
