"""Minute P&L paths of B on REAL ES futures (same rules as paths.py), $ per MES (5 $/pt) at today's price.
Saves dbdata/paths_es.npz (d, px, mtm, low in points; propsim-style)."""
import glob, numpy as np, pandas as pd, databento as db
from paths import path, N
import paths as PP
PP.RT = 0.35  # ES round trip in points (micro: comm + 1 tick)
df = pd.concat([db.DBNStore.from_file(f).to_df()[["open", "high", "low", "close"]] for f in sorted(glob.glob("dbdata/es_1m_*.dbn.zst"))])
df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()].sort_index()
days = []
for d, g in df.groupby(df.index.date):
    g = g.between_time("09:30", "15:59")
    if pd.Timestamp(d).weekday() > 4 or len(g) < N * 0.9: continue
    g = g.copy(); g.index = g.index.hour * 60 + g.index.minute - 570
    days.append((pd.Timestamp(d), g.reindex(range(N)).ffill().bfill()))
hist, D, P, M, W = [], [], [], [], []
for i, (d, m) in enumerate(days):
    o = m.open.iloc[0]
    if i >= 14:
        pc = days[i - 1][1].close.iloc[-1]
        if abs(pc / o - 1) > 0.03: pc = o
        mtm, low = path(m, o, pc, np.mean(np.vstack(hist[-14:]), axis=0))
        D.append(str(d.date())); P.append(o); M.append(mtm.astype(np.float32)); W.append(low.astype(np.float32))
    hist.append((m.close / o - 1).abs().values)
np.savez_compressed("dbdata/paths_es.npz", d=np.array(D), px=np.array(P), mtm=np.array(M), low=np.array(W))
f = np.array([x[-1] for x in M]) / np.array(P); print("ES-B days", len(D), "Sharpe %.2f" % (f.mean() / f.std() * np.sqrt(252)))
