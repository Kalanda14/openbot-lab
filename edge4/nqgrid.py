"""Build NQ 1m session grid from dbdata/nq.pkl (front contract, rolls on Sunday open).
Session date = calendar date of the 17:00 ET close; minute k = 18:00 ET prev evening + k (k=0..1379).
grid[d, k] = last close at or before bar k (bar labelled by start; ffill inside session). Price 'at time T' = grid[k(T)-1].
Saves edge4/nqgrid.npz: d, g (float32), iid (instrument per session)."""
import pandas as pd, numpy as np
d = pd.read_pickle("/Users/churchxelachurchxela/Projects/openbot-lab/dbdata/nq.pkl")
t = d.index.tz_localize(None)
sd = (t + pd.Timedelta(hours=6)).normalize()            # 18:00 -> next day
k = ((t - (sd - pd.Timedelta(hours=6))) / pd.Timedelta(minutes=1)).astype(int)
df = pd.DataFrame({"sd": sd, "k": k, "c": d.close.values, "iid": d.instrument_id.values})
df = df[(df.k >= 0) & (df.k < 1380) & (df.sd.dt.weekday < 5)]
days = pd.DatetimeIndex(sorted(df.sd.unique())); di = days.get_indexer(df.sd)
G = np.full((len(days), 1380), np.nan, np.float32); G[di, df.k.values] = df.c.values
G = pd.DataFrame(G).ffill(axis=1).values.astype(np.float32)
iid = df.groupby("sd").iid.last().reindex(days).values
np.savez_compressed("/Users/churchxelachurchxela/Projects/openbot-lab/edge4/nqgrid.npz", d=days.values.astype("datetime64[D]"), g=G, iid=iid)
print(len(days), days[0], days[-1], np.isnan(G[:, 930]).mean())
