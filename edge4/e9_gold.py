"""Best survivor check: gold overnight (GLD 16:00 -> 09:30 ET, dividend-adjusted). Cost sensitivity (swap-free CFD:
XAUUSD spread ~1-1.5 bp RT; with swap 2.5 bp), by-year table, intraday leg, and combination with the book's
vol-managed daily series (BOOK = sum of B/ON/TREND legs from audit build). Weight for gold = risk-parity on train
(1/std of the vol-managed series, same rule as audit/lib.build), then the combined book is rescaled to the old book's
train std, so Sharpe changes are like-for-like."""
import sys, json; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
exec(open(f"{LAB}/edge4/e7_etf_on.py").read().split("out = [HDR]")[0].split('"""', 2)[2])
df = yf("GLD"); on = (df.o / df.c.shift(1) - 1).where(lambda x: x.abs() < 0.15).fillna(0); day = (df.c / df.o - 1)
out = [HDR]
for cst in (1.0e-4, 1.5e-4, 2.5e-4):
    a = pd.Series(True, on.index); out.append(line(f"GLD night, cost {cst*1e4:.1f} bp", stats(on, pd.Series(cst, on.index), a)))
out.append(line("GLD day (open->close) long, cost 1.5 bp", stats(day, pd.Series(1.5e-4, day.index), pd.Series(True, day.index))))
out.append(line("GLD close->close (buy & hold reference), no cost", stats(on + day, pd.Series(0.0, day.index), pd.Series(True, day.index))))
out.append("\n| year | night bp/day | t | night Sharpe gross | day bp | close-close bp |\n|---|---|---|---|---|---|")
for y in range(2017, 2027):
    n = on[str(y)]; d_ = day[str(y)]
    out.append(f"| {y} | {n.mean()*1e4:+.2f} | {n.mean()/n.std()*np.sqrt(len(n)):+.2f} | {n.mean()/n.std()*np.sqrt(252):+.2f} | {d_.mean()*1e4:+.2f} | {(n+d_).mean()*1e4:+.2f} |")
# combination with the book (daily, gross of the CFD costs used in the month sim; gold net 1.5 bp)
bk = BOOK.copy(); X = bk.index; tr = (X >= "2017-01-01") & (X < "2022-01-01")
gn = (on - 1.5e-4).reindex(X).fillna(0)           # night ending morning t -> day t (same alignment as ON)
nz = gn.where(gn != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
gv = gn * (nz[tr].std() / vol).clip(0, 3).fillna(1)
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
out.append("\n| combination | train Sharpe | test Sharpe | all |\n|---|---|---|---|")
out.append(f"| BOOK (B+ON+TREND vol-managed, gross) | {sh(bk.BOOK[tr]):.2f} | {sh(bk.BOOK[~tr]):.2f} | {sh(bk.BOOK):.2f} |")
out.append(f"| gold night vol-managed (net 1.5 bp) | {sh(gv[tr]):.2f} | {sh(gv[~tr]):.2f} | {sh(gv):.2f} |")
out.append(f"| corr(gold, BOOK) train / test | {np.corrcoef(gv[tr], bk.BOOK[tr])[0,1]:+.3f} | {np.corrcoef(gv[~tr], bk.BOOK[~tr])[0,1]:+.3f} | |")
legstd = pd.DataFrame({k: bk[k] for k in ("B", "ON", "TREND")})[tr].std()
for nm, wg in (("risk-parity weight (gold vol = avg sleeve vol share)", bk.BOOK[tr].std() / gv[tr].std() / 3),
               ("half that weight", bk.BOOK[tr].std() / gv[tr].std() / 6), ("double", 2 * bk.BOOK[tr].std() / gv[tr].std() / 3)):
    c = bk.BOOK + wg * gv; c = c * bk.BOOK[tr].std() / c[tr].std()
    out.append(f"| BOOK + gold ({nm}, w={wg:.2f}) rescaled | {sh(c[tr]):.2f} | {sh(c[~tr]):.2f} | {sh(c):.2f} |")
pd.DataFrame({"gold_night_net": gn, "gold_vm": gv}).to_csv(f"{LAB}/edge4/gold_daily.csv")
print("\n".join(out)); open(f"{LAB}/edge4/e9_gold.md", "w").write("\n".join(out))
