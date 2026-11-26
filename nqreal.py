"""Setup B on REAL CME Nasdaq futures 1-minute bars (Databento GLBX.MDP3 NQ.v.0, front month by volume).
Same rules as paths.py / bt4 v30. Data stays local (dbdata/, license: no redistribution).
Output: dbdata/paths_real.npz (same format as paths_*.npz) + Sharpe by year vs the free Dukascopy version."""
import glob, numpy as np, pandas as pd, databento as db
from paths import path, N

fs = sorted(glob.glob("dbdata/nq_1m_*.dbn.zst"))
df = pd.concat([db.DBNStore.from_file(f).to_df()[["open", "high", "low", "close"]] for f in fs])
df.index = df.index.tz_convert("America/New_York")
df = df[~df.index.duplicated()]
days = []
for d, g in df.groupby(df.index.date):
    if pd.Timestamp(d).weekday() > 4: continue
    m = g.between_time("09:30", "15:59")
    if len(m) < N * 0.9: continue
    m = m.copy(); m.index = m.index.hour * 60 + m.index.minute - 570
    days.append((pd.Timestamp(d), m.reindex(range(N)).ffill().bfill()))
hist, D, P, M, W = [], [], [], [], []
for i, (d, m) in enumerate(days):
    o = m.open.iloc[0]
    if i >= 14:
        pc = days[i - 1][1].close.iloc[-1]
        if abs(pc / o - 1) > 0.03: pc = o  # roll day: previous close is the old contract -> ignore the gap
        mtm, low = path(m, o, pc, np.mean(np.vstack(hist[-14:]), axis=0))
        D.append(str(d.date())); P.append(o); M.append(mtm.astype(np.float32)); W.append(low.astype(np.float32))
    hist.append((m.close / o - 1).abs().values)
np.savez_compressed("dbdata/paths_real.npz", d=np.array(D), px=np.array(P), mtm=np.array(M), low=np.array(W))
r = pd.Series(np.array([x[-1] for x in M]) / np.array(P) * 100, index=pd.to_datetime(D))
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
print(f"REAL NQ futures: days={len(r)} %/yr={r.mean()*252:+.1f} Sharpe={sh(r):+.2f}  "
      f"2017-21 {sh(r[:'2021']):+.2f}  2022-26 {sh(r['2022':]):+.2f}")
dk = {}
for f in glob.glob("pathsd/**/paths_*.npz", recursive=True):
    z = np.load(f); dk.update(zip(z["d"], z["mtm"][:, -1] / z["px"] * 100))
dk = pd.Series(dk); dk.index = pd.to_datetime(dk.index)
both = pd.concat([r.rename("real"), dk.rename("duka")], axis=1).dropna()
print(f"same days n={len(both)}: real Sharpe {sh(both.real):+.2f} vs free-data {sh(both.duka):+.2f}, corr {both.corr().iloc[0,1]:.2f}")
for y, g in r.groupby(r.index.year): print(y, f"{g.mean()*252:+6.1f}%  Sharpe {sh(g):+.2f}")
