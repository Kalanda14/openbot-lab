"""Audit prep (read-only on project data). Loads real CME NQ 1m OHLC (dbn) once and writes:
 audit/onlow.npz : per nqD roll-free night (15:55 -> 03:30 ET), 30-min-equivalent legs (20 legs, same cut as m2 on_paths):
                   r (close-to-close), wc (worst by 1m CLOSE, as m2), wl (worst by 1m LOW), plus whole-night min close/low.
 audit/paths_rt2.npz : B paths rebuilt exactly as nqreal.py but round-trip cost 2.0 pt (CFD-like) instead of 1.12."""
import glob, sys, time, numpy as np, pandas as pd, databento as db
sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab"); import os; os.chdir("/Users/churchxelachurchxela/Projects/openbot-lab")
t0 = time.time()
fs = sorted(glob.glob("dbdata/nq_1m_*.dbn.zst"))
df = pd.concat([db.DBNStore.from_file(f).to_df()[["instrument_id", "open", "high", "low", "close"]] for f in fs])
df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()].sort_index()
print("loaded", len(df), round(time.time() - t0), "s", flush=True)
# ---- ON legs with lows ----
D = pd.read_pickle("dbdata/nqD.pkl"); D = D[D.roll == 0]
ti = df.index; cl = df.close.values; lo = df.low.values; ins = df.instrument_id.values
nst = 20; n = len(D)
R = np.zeros((n, nst)); WC = np.zeros((n, nst)); WL = np.zeros((n, nst)); UP = np.zeros((n, nst)); ok = np.zeros(n, bool); mc = np.zeros(n); ml = np.zeros(n); P0 = np.zeros(n)
for t, (d, row) in enumerate(D.iterrows()):
    a = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=15, minutes=54)
    e = pd.Timestamp(row.nx).tz_localize("America/New_York") + pd.Timedelta(hours=3, minutes=29)
    i0, i1 = ti.searchsorted(a), ti.searchsorted(e, side="right")
    if i1 - i0 < 100 or ti[i0] != a: continue
    k = ins[i0:i1] == ins[i0]
    c = cl[i0:i1][k]; l = lo[i0:i1][k]; p0 = c[0]
    if abs(c[-1] / p0 - 1 - row.x0330) > 1e-6: continue
    ok[t] = True; P0[t] = p0; rel = c / p0 - 1; rl = l / p0 - 1
    mins = np.arange(len(c), dtype=float); bnd = [(len(c) - 1) * j / nst for j in range(nst + 1)]
    for j in range(nst):
        m = (mins > bnd[j]) & (mins <= bnd[j + 1]); s0 = rel[mins <= bnd[j]][-1]; s1 = rel[mins <= bnd[j + 1]][-1]
        R[t, j] = s1 - s0
        if m.any(): WC[t, j] = min(rel[m].min() - s0, 0); WL[t, j] = min(rl[m].min() - s0, 0); UP[t, j] = max(rel[m].max() - s0, 0)
    mc[t] = rel[1:].min(); ml[t] = rl[1:].min()
np.savez_compressed("audit/onlow.npz", d=np.array([str(x.date()) for x in D.index]), r=R, wc=WC, wl=WL, up=UP, ok=ok, mc=mc, ml=ml, px=P0)
print("ON nights ok", ok.sum(), "of", n, round(time.time() - t0), "s", flush=True)
# ---- B paths at 2.0 pt round trip ----
import paths as PM; PM.RT = 2.0
N = PM.N; days = []
for d, gdf in df.groupby(df.index.date):
    if pd.Timestamp(d).weekday() > 4: continue
    m = gdf.between_time("09:30", "15:59")
    if len(m) < N * 0.9: continue
    m = m.copy(); m.index = m.index.hour * 60 + m.index.minute - 570
    days.append((pd.Timestamp(d), m.reindex(range(N)).ffill().bfill()))
hist, Dd, P, M, W = [], [], [], [], []
for i, (d, m) in enumerate(days):
    o = m.open.iloc[0]
    if i >= 14:
        pc = days[i - 1][1].close.iloc[-1]
        if abs(pc / o - 1) > 0.03: pc = o
        mtm, low = PM.path(m, o, pc, np.mean(np.vstack(hist[-14:]), axis=0))
        Dd.append(str(d.date())); P.append(o); M.append(mtm.astype(np.float32)); W.append(low.astype(np.float32))
    hist.append((m.close / o - 1).abs().values)
np.savez_compressed("audit/paths_rt2.npz", d=np.array(Dd), px=np.array(P), mtm=np.array(M), low=np.array(W))
z = np.load("dbdata/paths_real.npz"); print("B days", len(Dd), "orig", len(z["d"]), "final pnl diff check (rt1.12 vs rt2) mean pt/day",
      np.mean(z["mtm"][:, -1]) if len(z["d"]) != len(Dd) else np.mean(z["mtm"][:, -1] - np.array(M)[:, -1]), round(time.time() - t0), "s")
