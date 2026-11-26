"""Full 12-month plan with the REAL 2026 prop rules (rules2026_all.json). Windows start 2023-06..2025-11 (spread data).
Own account: deadline sizing toward EUR 10k (cap), +100/mo, funding spread at fixed multiple. Prop: up to NPROP accounts of one
plan; a new one is bought when wallet >= fee + activation + reserve. Payouts into the wallet. 'api' = $29/mo while a bot account runs.
Compares prop engines: Apex EOD (old plan), Topstep Standard, Topstep Consistency, Tradeify Select Flex, FundedNext Flex.
"""
import json, numpy as np, pandas as pd, propsim as P, hybrid as h, hybrid4 as H, goal80 as g

A = json.load(open("rules2026_all.json"))
ENG = {"Apex EOD": ("Apex EOD 50K", (5, 2, 800), 0), "Topstep Std": ("Topstep 50K Standard", (5, 1, 1500), 29),
       "Topstep Cons": ("Topstep 50K Consistency", (25, 8, 500), 29), "Topstep Std alerts": ("Topstep 50K Standard", (5, 1, 1500), 0),
       "Tradeify Flex": ("Tradeify Select Flex 50K", (3, 1, 500), 0), "FundedNext Flex": ("FundedNext Flex 50K", (3, 1, 500), 0)}


def tables(r, ke, kf, tp): return tuple(P.day_table(h.m, h.lo, k, tp, None, r.get("dll")) for k in (ke, kf, kf))


def sim(R, pas, eng, nprop, mult=5, cap=45, dep=100, days=252, reserve=300):
    nm, (ke, kf, tp), api = ENG[eng]; r = A[nm]; T = tables(r, ke, kf, tp)
    out = []
    for s in range(H.start0, len(R) - days, 3):
        W, accts = g.X0, []
        for i in range(days):
            left = days - i
            if i and i % 21 == 0:
                W += dep
                if accts and api: W -= api
            weff = W + dep * (left // 21)
            if weff >= g.G: W = g.G + 1; break
            z = g.norm.ppf(max(weff / g.G, 1e-6))
            lev = min(g.norm.pdf(z) * g.G / (g.sig_tr * np.sqrt(left) * max(W, 1e-9)), cap)
            W *= 1 + lev * R[s + i] + mult * pas[s + i]
            if W <= 1: W = 0.0
            pi = h.pidx.get(h.dates[s + i])
            if pi is not None:
                while len(accts) < nprop and W >= r["fee"] + r["act"] + reserve:
                    W -= r["fee"]; accts.append(P.new_acct(r))
                nxt = []
                for a in accts:
                    a, W = P.step(a, r, T, pi, W)
                    if a is not None: nxt.append(a)
                accts = nxt
            if W >= g.G: W = g.G + 1; break
            if W <= 0 and not accts: break
        out.append(W)
    o = np.array(out); return np.mean(o >= g.G), np.mean(o < 100)


if __name__ == "__main__":
    fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
    L = ["| prop engine | accounts | backtest P(10k in 12 mo) | cautious | wipe (bt/caut) |", "|---|---|---|---|---|"]
    for eng in ENG:
        for n in (1, 2):
            a = sim(g.R, H.PA, eng, n); b = sim(fwd, H.PA26, eng, n)
            L.append(f"| {eng} | {n} | {a[0]:.0%} | {b[0]:.0%} | {a[1]:.0%} / {b[1]:.0%} |"); print(L[-1], flush=True)
    open("fullplan.md", "w").write("\n".join(L) + "\n")
