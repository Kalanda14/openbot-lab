"""B on REAL CME ES futures 1m (Databento), same rules as tranche.py single grid, cost 0.35 pt/RT (1 ES ~ 2 ticks+comm).
Then add to the stack (as its own sleeve) and report book Sharpe. Rule fixed before results."""
import glob, numpy as np, pandas as pd, databento as db
N = 390
df = pd.concat([db.DBNStore.from_file(f).to_df()[["open", "high", "low", "close"]] for f in sorted(glob.glob("dbdata/es_1m_*.dbn.zst"))])
df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()].sort_index()
D, A = [], []
for d, g in df.groupby(df.index.date):
    g = g.between_time("09:30", "15:59")
    if pd.Timestamp(d).weekday() > 4 or len(g) < N * 0.9: continue
    g = g.copy(); g.index = g.index.hour * 60 + g.index.minute - 570
    D.append(pd.Timestamp(d)); A.append(g.reindex(range(N)).ffill().bfill().values.T)
A = np.array(A); O, C = A[:, 0], A[:, 3]; nd = len(D)
o0 = O[:, 0]; pc = np.r_[o0[0], C[:-1, -1]]; pc = np.where(np.abs(pc / o0 - 1) > 0.03, o0, pc)
sg = pd.DataFrame(np.abs(C / o0[:, None] - 1)).rolling(14).mean().shift(1).values
ub = np.maximum(o0, pc)[:, None] * (1 + sg); lb = np.minimum(o0, pc)[:, None] * (1 - sg)
out = np.zeros(nd)
for i in range(14, nd):
    pos, e, pn = 0, 0.0, 0.0
    for k in range(30, N - 1, 30):
        c = C[i, k]
        if pos and ((pos == 1 and c < ub[i, k]) or (pos == -1 and c > lb[i, k])): pn += (c - e) * pos - 0.35; pos = 0
        if not pos:
            if c > ub[i, k]: pos, e = 1, c
            elif c < lb[i, k]: pos, e = -1, c
    if pos: pn += (C[i, -1] - e) * pos - 0.35
    out[i] = pn / o0[i]
E = pd.Series(out, index=D)[14:]
jobs = np.array([(t.weekday() == 4 and t.day <= 7) for t in E.index]); E = E * np.where(jobs, 2, 1)
sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
S = pd.read_csv("/Users/churchxelachurchxela/Projects/openbot/stack2_daily.csv", index_col=0, parse_dates=True)
S["ESB"] = E.reindex(S.index).fillna(0)
L = [f"ES-B real: all {sh(E):+.2f} | 2017-21 {sh(E[:'2021']):+.2f} | 2022-26 {sh(E['2022':]):+.2f}; corr with NQ-B (test) {S['2022':][['ESB','B']].corr().iloc[0,1]:+.2f}"]
tr = S[:"2021"]
for nm, cols in (("base", ["B", "ON", "TREND"]), ("+ESB", ["B", "ON", "TREND", "ESB"])):
    iv = 1 / tr[cols].std(); w = iv / iv.sum(); Rk = S[cols] @ w; k = 0.15 / (Rk[:"2021"].std() * np.sqrt(252))
    bk = (k * Rk + 3 * S.CARRY)["2022":]
    L.append(f"{nm} + carry 3x: TEST Sharpe {sh(bk):+.2f}, {bk.mean()*252*100:+.1f}%/yr")
E.to_frame("ESB").to_csv("dbdata/esb.csv")
open("esb.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
