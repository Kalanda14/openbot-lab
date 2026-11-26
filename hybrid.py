"""12-month route: own account (deadline sizing, cap 30x, +EUR100/mo) PLUS prop accounts running B on real NQ paths.
Same calendar days for both. Prop fees come out of the own account wallet; payouts go into it (treated $=EUR).
Prop accounts are bought whenever the wallet can pay fee + reserve, up to NPROP at once (copies of the same trades).
Plans fixed before results: Apex 50K EOD with B overlays picked earlier on 2017-21 real data
  A1 = ke 5, kf 3, tp $1500 ; A2 = ke 5, kf 2, tp $800.   Fees from propsim.R['APEX'] (eval $47, activation $129).
Own book: B+ON+TREND risk parity (as goal80), backtest edge and a 'forward' version cut to Sharpe 1.2.
"""
import os, numpy as np, pandas as pd
os.environ["PATHS"] = "dbdata/paths_real.npz"
import propsim as P, goal80 as g

d, m, lo = P.load(); pidx = {x: i for i, x in enumerate(d)}
S = g.S; dates = [str(x.date()) for x in S.index]
r_ap = P.R["APEX"]


def tables(ke, kf, tp): return tuple(P.day_table(m, lo, k, tp, None, r_ap.get("dll")) for k in (ke, kf, kf))


def sim(r, dep, nprop, T, reserve, days=252, cap=30):
    out = []
    for s in range(0, len(r) - days, 5):
        W, accts = g.X0, []
        for i in range(days):
            left = days - i
            if i and i % 21 == 0: W += dep
            weff = W + dep * (left // 21)
            if weff >= g.G: W = g.G + 1; break
            z = g.norm.ppf(max(weff / g.G, 1e-6))
            lev = min(g.norm.pdf(z) * g.G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            W *= 1 + lev * r[s + i]
            if W <= 1: W = 0.0
            pi = pidx.get(dates[s + i])
            if nprop and pi is not None:
                while len(accts) < nprop and W >= r_ap["fee"] + r_ap["act"] + reserve:
                    W -= r_ap["fee"]; accts.append(P.new_acct(r_ap))
                nxt = []
                for a in accts:
                    a, W = P.step(a, r_ap, T, pi, W)
                    if a is not None: nxt.append(a)
                accts = nxt
            if W <= 0 and not accts: break
        out.append(W)
    o = np.array(out); return np.mean(o >= g.G), np.mean(o < 100), np.median(o)


if __name__ == "__main__":
    fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
    L = ["| own edge | prop plan | prop accts | P(10k in 12 mo) | P(end<100) | median |", "|---|---|---|---|---|---|"]
    for nm, r in (("backtest", g.R), ("forward 1.2", fwd)):
        for pn, (ke, kf, tp) in (("A1 5->3 tp1500", (5, 3, 1500)), ("A2 5->2 tp800", (5, 2, 800))):
            T = tables(ke, kf, tp)
            for n in (0, 1, 2, 3):
                if n == 0 and pn.startswith("A2"): continue
                p, w0, md = sim(r, 100, n, T, 100)
                L.append(f"| {nm} | {pn if n else '-'} | {n} | {p:.0%} | {w0:.0%} | {md:,.0f} |"); print(L[-1], flush=True)
    open("hybrid.md", "w").write("\n".join(L) + "\n")
