"""Can we reach 80% chance of EUR 10,000 in 1 year from EUR 400? Theory + real-data simulation.
Theory (Browne 1999, best possible over ALL strategies, continuous trading, no costs, no leverage limit):
  P_max = Phi( PhiInv(W_eff / G) + theta * sqrt(T) ),  W_eff = start + present value of future deposits.
Simulation: the LEVERAGEABLE book (real NQ B + jobs 2x, overnight NQ, BTC/ETH trend; risk parity, train-2020-21 vols),
deadline sizing each day: exposure = phi(PhiInv(W/G)) * G / (sigma * sqrt(days left)) using deposits-adjusted W,
cap on leverage, stop when goal reached; wiped if equity <= 0. All 252-day windows starting 2020-03..2025-11.
Edge cases: backtest as is, and 'forward' = same days with mean cut so Sharpe is 1.0.
"""
import numpy as np, pandas as pd
from statistics import NormalDist
class norm:
    _n = NormalDist()
    cdf = staticmethod(lambda x: NormalDist().cdf(x)); ppf = staticmethod(lambda p: NormalDist().inv_cdf(p)); pdf = staticmethod(lambda x: NormalDist().pdf(x))

G, X0 = 10000.0, 400.0
print("## Theory: best possible P(EUR 10k in time T), any strategy\n")
print("| leverageable Sharpe | 1 yr, no deposits | 1 yr, +100/mo | 1 yr, +250/mo | 1 yr, +350/mo | 2 yr, +100/mo | 3 yr, +100/mo |")
print("|---|---|---|---|---|---|---|")
for th in (1.0, 1.3, 1.6, 2.0, 2.6, 3.0):
    row = []
    for T, dep in ((1, 0), (1, 100), (1, 250), (1, 350), (2, 100), (3, 100)):
        w = X0 + dep * 12 * T * 0.5 ** 0  # deposits counted at face value (cash rate ~0 vs goal)
        row.append(f"{norm.cdf(norm.ppf(min(w / G, 0.999)) + th * np.sqrt(T)):.0%}")
    print(f"| {th} | " + " | ".join(row) + " |")
print(f"\nneeded for 80% in 1 year with no deposits: Sharpe x sqrt(T) >= {norm.ppf(0.8) - norm.ppf(X0 / G):.2f}")

S = pd.read_csv("/Users/churchxelachurchxela/Projects/openbot/stack4_daily.csv", index_col=0, parse_dates=True)
tr = S[:"2021"]; cols = ["B", "ON", "TREND"]; iv = 1 / tr[cols].std(); w = iv / iv.sum(); R = (S[cols] @ w).values
sig_tr = R[: (S.index < "2022").sum()].std()
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
print(f"\nleverageable book Sharpe: all {sh(R):.2f}, 2022-26 {sh(R[S.index >= '2022']):.2f}")


def sim(r, dep, cap, days=252):
    out = []
    for s in range(0, len(r) - days, 5):
        W = X0
        for i in range(days):
            left = days - i
            if i and i % 21 == 0: W += dep
            weff = W + dep * (left // 21)
            if weff >= G: W = G + 1; break
            z = norm.ppf(max(weff / G, 1e-6))
            lev = min(norm.pdf(z) * G / (sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            W *= 1 + lev * r[s + i]
            if W <= 1: W = 0; break
        out.append(W)
    o = np.array(out); return np.mean(o >= G), np.mean(o < 100), np.median(o)


print("\n## Simulation on real days (deadline sizing, leverage cap 30x)\n")
print("| edge | deposit/mo | P(10k in 1 yr) | P(end < 100) | median end |\n|---|---|---|---|---|")
fwd = R - R.mean() + 1.0 * R.std() / np.sqrt(252)
for nm, r in (("backtest", R), ("forward Sharpe 1.0", fwd)):
    for dep in (0, 100, 250, 350, 500):
        p, w0, md = sim(r, dep, 30)
        print(f"| {nm} | {dep} | {p:.0%} | {w0:.0%} | {md:,.0f} |", flush=True)
