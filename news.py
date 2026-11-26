"""T1 without FRED: news days detected from real NQ futures volume (rule fixed before results).
news day = sum of 1m volume 08:30-08:34 ET >= 4 x (5 x median 1m volume 08:00-08:29 ET). Known before 09:30.
B (real NQ, 1 NQ cost 0.7, tranche.npz 'single') at 2x on news days, 1x otherwise. Jobs Fridays are a subset.
Success: news-day mean >= 1.5x other days with t>=2 on TEST 2022-26, book Sharpe +0.08 vs plain, both halves same sign.
"""
import glob, numpy as np, pandas as pd, databento as db
df = pd.concat([db.DBNStore.from_file(f).to_df()[["volume"]] for f in sorted(glob.glob("dbdata/nq_1m_*.dbn.zst"))])
df.index = df.index.tz_convert("America/New_York"); df = df[~df.index.duplicated()]
m = df.between_time("08:00", "08:34"); m = m.assign(d=m.index.date, hm=m.index.hour * 100 + m.index.minute)
pre = m[m.hm < 830].groupby("d").volume.median(); post = m[m.hm >= 830].groupby("d").volume.sum()
pre, post = pre.align(post, join="inner"); news = (post.astype(float) >= 20 * pre.astype(float)).rename("news")
t = np.load("dbdata/tranche.npz"); b = pd.Series(t["single"] / t["px"] * 100, index=pd.to_datetime(t["d"]))[14:]
nw = news.reindex(b.index.date).fillna(False).values.astype(bool)
jobs = np.array([(x.weekday() == 4 and x.day <= 7) for x in b.index])
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
tt = lambda x: x.mean() / x.std() * np.sqrt(len(x))
L = [f"news days: {nw.sum()} of {len(b)} ({nw.mean():.0%}); jobs Fridays flagged as news: {nw[jobs].mean():.0%}\n",
     "| period | news days mean %/day (n, t) | other days mean | plain Sharpe | news 2x Sharpe | jobs-only 2x Sharpe |", "|---|---|---|---|---|---|"]
for nm, s in (("TRAIN 2017-21", b.index < "2022"), ("TEST 2022-26", b.index >= "2022")):
    x, n, j = b[s], nw[s], jobs[s]
    L.append(f"| {nm} | {x[n].mean():+.3f} ({n.sum()}, {tt(x[n]):+.1f}) | {x[~n].mean():+.3f} | {sh(x):+.2f} | {sh(x * np.where(n, 2, 1)):+.2f} | {sh(x * np.where(j, 2, 1)):+.2f} |")
nn = nw & ~jobs
L.append(f"\nnews days EXCLUDING jobs Fridays: train mean {b[(b.index < '2022') & nn].mean():+.3f}, test mean {b[(b.index >= '2022') & nn].mean():+.3f} (n test {((b.index >= '2022') & nn).sum()})")
pd.Series(nw, index=b.index).to_csv("dbdata/newsdays.csv")
open("news.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
