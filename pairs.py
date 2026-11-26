"""Nasdaq vs S&P intraday spread (stat arb) on real CME futures 1m bars (Databento NQ.v.0 + ES.v.0, 2017-26).
Rules fixed before results. Spread x_t = ln(NQ_t/NQ_open) - beta*ln(ES_t/ES_open); beta and sd from past 60 days only.
Decision every 30 min 10:00..15:30, z = x_t / sd(x at that minute, past 60 days).
 PR-rev-k : |z| > k -> bet the spread goes back (short NQ / long beta ES if z>0), hold 30 / 60 / to close
 PR-mom-k : same, bet it keeps going
 LL       : lead-lag, NQ only: if beta*ES 5-min move > NQ 5-min move by > 0.05% -> long NQ (catch-up), hold 5 / 30
Costs per round trip: NQ 1.12 pt, ES 0.62 pt (micro contracts, commission + 1 tick slip each side).
Train 2017-21, test 2022-26. Result in % of notional per day, Sharpe, t.
"""
import glob, numpy as np, pandas as pd, databento as db

N = 390


def rth(pat, out):
    try: return np.load(out)
    except FileNotFoundError: pass
    df = pd.concat([db.DBNStore.from_file(f).to_df()[["close"]] for f in sorted(glob.glob(pat))])
    df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()].sort_index()
    D, A = [], []
    for d, g in df.groupby(df.index.date):
        g = g.between_time("09:30", "15:59")
        if pd.Timestamp(d).weekday() > 4 or len(g) < N * 0.9: continue
        g = g.copy(); g.index = g.index.hour * 60 + g.index.minute - 570
        D.append(str(d)); A.append(g["close"].reindex(range(N)).ffill().bfill().values)
    np.savez_compressed(out, d=np.array(D), c=np.array(A)); return np.load(out)


nq = np.load("dbdata/rth.npz"); es = rth("dbdata/es_1m_*.dbn.zst", "dbdata/es_rth.npz")
common = np.intersect1d(nq["d"], es["d"])
iq = np.searchsorted(nq["d"], common); ie = np.searchsorted(es["d"], common)
Q = nq["a"][iq, 3, :]; E = es["c"][ie]; d = common; nd = len(d)
lq, le = np.log(Q / Q[:, :1]), np.log(E / E[:, :1])
cq, ce = 1.12 / Q[:, 0], 0.62 / E[:, 0]
# beta from past 60 days of 1-minute returns
rq, re_ = np.diff(lq, axis=1), np.diff(le, axis=1)
cov = np.array([(rq[i] * re_[i]).sum() for i in range(nd)]); var = np.array([(re_[i] ** 2).sum() for i in range(nd)])
beta = pd.Series(cov).rolling(60).sum().shift(1) / pd.Series(var).rolling(60).sum().shift(1)
beta = beta.values
X = lq - beta[:, None] * le
sd = pd.DataFrame(X).pow(2).rolling(60).mean().shift(1).pow(0.5).values
ok = ~np.isnan(beta) & (np.arange(nd) >= 61)
tr = ok & np.array([x < "2022-01-01" for x in d]); te = ok & ~tr
T = list(range(30, 361, 30))
sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0
tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0.0
res = {}
for k in (1.0, 1.5, 2.0):
    for h in (30, 60, "close"):
        rev = np.zeros(nd); mom = np.zeros(nd)
        for t in T:
            e = N - 1 if h == "close" else min(t + h, N - 1)
            z = np.nan_to_num(X[:, t] / np.where(sd[:, t] > 0, sd[:, t], np.nan))
            s = np.sign(z) * (np.abs(z) > k)
            dx = (lq[:, e] - lq[:, t]) - beta * (le[:, e] - le[:, t])
            cost = (cq + np.abs(beta) * ce) * (s != 0)
            rev += np.nan_to_num(-s * dx - cost); mom += np.nan_to_num(s * dx - cost)
        res[f"PR-rev-{k} hold {h}"] = rev; res[f"PR-mom-{k} hold {h}"] = mom
for h in (5, 30):
    ll = np.zeros(nd)
    for t in range(10, N - h, 5):
        g = np.nan_to_num(beta * (le[:, t] - le[:, t - 5]) - (lq[:, t] - lq[:, t - 5]))
        s = np.sign(g) * (np.abs(g) > 0.0005)
        ll += s * (lq[:, t + h] - lq[:, t]) - cq * (s != 0)
    res[f"LL hold {h}"] = ll
L = [f"# Nasdaq vs S&P spread tests ({nd} days; train {tr.sum()} / test {te.sum()})\n",
     f"{len(res)} rules. % of notional per day.\n", "| rule | train %/day | train Sharpe | t | TEST %/day | TEST Sharpe | t |",
     "|---|---|---|---|---|---|---|"]
for nm, p in sorted(res.items(), key=lambda x: -tt(x[1][tr])):
    L.append(f"| {nm} | {p[tr].mean()*100:+.3f} | {sh(p[tr]):+.2f} | {tt(p[tr]):+.1f} | {p[te].mean()*100:+.3f} | {sh(p[te]):+.2f} | {tt(p[te]):+.1f} |")
open("pairs.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
