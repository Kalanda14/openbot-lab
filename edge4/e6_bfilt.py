"""Candidate 6: pre-registered regime filters on B (book B daily returns, real CME paths, incl. data costs).
Features known before 09:30 ET; thresholds = TRAIN (2017-21) percentiles only. A filter must raise B's Sharpe in
train AND test. Sharpe on all days (zeros when flat/skipped)."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
Bd = BOOK.B; X = Bd.index; tr = X.year <= 2021
D, G, iid = nqgrid(); same = np.r_[False, iid[1:] == iid[:-1]]
c16 = pd.Series(G[:, K(16, 0)], D); o930 = pd.Series(G[:, K(9, 30)], D)
gap = (o930 / c16.shift(1) - 1).where(same).reindex(X)
vol20 = np.log(c16).diff().rolling(20).std().shift(1).reindex(X)
vix = pd.read_csv(f"{LAB}/ext/VIX.csv", parse_dates=["DATE"], index_col="DATE").CLOSE.shift(1).reindex(X, method="ffill")
B5 = Bd.rolling(5).sum().shift(1)
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
F = {"base (no filter)": pd.Series(True, X),
     "vol20 >= train p33": vol20 >= vol20[tr].quantile(1 / 3),
     "vol20 <= train p67": vol20 <= vol20[tr].quantile(2 / 3),
     "|gap| <= train p90": gap.abs() <= gap.abs()[tr].quantile(0.9),
     "|gap| >= train p10": gap.abs() >= gap.abs()[tr].quantile(0.1),
     "VIX(t-1) >= train median": vix >= vix[tr].median(),
     "skip Mondays": pd.Series(X.weekday != 0, X),
     "prior 5d B pnl > 0": B5 > 0, "prior 5d B pnl <= 0": B5 <= 0}
out = ["| filter | days kept train | B Sh train | days kept test | B Sh test |", "|---|---|---|---|---|"]
for nm, m in F.items():
    m = m.fillna(True).astype(bool); b = Bd.where(m, 0)
    out.append(f"| {nm} | {m[tr].mean():.0%} | {sh(b[tr]):.2f} | {m[~tr].mean():.0%} | {sh(b[~tr]):.2f} |")
out.append(f"\nvariants: {len(F) - 1}")
print("\n".join(out)); open(f"{LAB}/edge4/e6_bfilt.md", "w").write("\n".join(out))
