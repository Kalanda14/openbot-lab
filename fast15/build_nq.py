"""NQ (Databento NQ.v.0 trades, side = aggressor) -> raw/nq_1s.npz, RTH 09:30:00-15:59:59 NY, one row per second.
Fields: t (unix s), last (last trade px, ffill in day), bpx/apx (last buy-/sell-aggressor px, ffill in day),
buy, sell (aggressor volume), n (trades), inst (instrument id, to drop horizons that cross a roll).
"""
import glob, numpy as np, pandas as pd, databento as db
parts = []
for f in sorted(glob.glob("../dbdata/nq_trades_2026-*.dbn.zst")):
    for ch in db.DBNStore.from_file(f).to_df(count=4_000_000):
        idx = ch["ts_event"].dt.tz_convert("America/New_York")
        ny = idx.dt.hour * 3600 + idx.dt.minute * 60 + idx.dt.second
        keep = ((ny >= 34200) & (ny < 57600)).values
        if not keep.any(): continue
        c = ch.loc[keep, ["price", "size", "side", "instrument_id"]].copy()
        c["sec"] = (ch["ts_event"].values[keep].astype("datetime64[s]").astype("int64"))
        c["buy"] = np.where(c.side == "B", c["size"], 0); c["sell"] = np.where(c.side == "A", c["size"], 0)
        c["bpx"] = np.where(c.side == "B", c.price, np.nan); c["apx"] = np.where(c.side == "A", c.price, np.nan)
        g = c.groupby("sec").agg(last=("price", "last"), bpx=("bpx", "last"), apx=("apx", "last"), buy=("buy", "sum"),
                                 sell=("sell", "sum"), n=("price", "size"), inst=("instrument_id", "last"))
        parts.append(g); print(f, len(g), flush=True)
g = pd.concat(parts).groupby(level=0).agg(dict(last="last", bpx="last", apx="last", buy="sum", sell="sum", n="sum", inst="last"))
day = pd.to_datetime(g.index, unit="s", utc=True).tz_convert("America/New_York").date
out = []
for d, gd in g.groupby(day):
    if len(gd) < 15000: continue                                   # skip half days / holidays
    t0 = int(pd.Timestamp(d).tz_localize("America/New_York").timestamp()) + 34200
    full = gd.reindex(np.arange(t0, t0 + 23400))
    for k in ("last", "bpx", "apx", "inst"): full[k] = full[k].ffill().bfill()
    out.append(full.fillna(0))
a = pd.concat(out)
np.savez("raw/nq_1s.npz", t=a.index.values, last=a["last"].values, bpx=a.bpx.values, apx=a.apx.values,
         buy=a.buy.values.astype("f4"), sell=a.sell.values.astype("f4"), n=a.n.values.astype("f4"), inst=a.inst.values.astype("i8"))
print("days", len(out), "rows", len(a))
