"""Month-1 money-back with REAL 2026 funded-account rules. Objective: wallet back to >= start (net >= 0) after D trading days,
all fees paid (eval, monthly, activation, API). Budget $430. Setups (eval MNQ, funded MNQ, daily tp) picked on 2017-21 starts,
judged on 2022-26 starts. Also P(net >= 0) with first-month promo prices."""
import json, itertools, numpy as np, fundsim as F, propsim as P
A = json.load(open("rules2026_all.json"))
A["Topstep 50K Standard"]["data"] = 29
PLANS = ["Topstep 50K Standard", "Topstep 50K Consistency", "Tradeify Select Flex 50K", "Tradeify Select Daily 50K", "FundedNext Flex 50K",
         "FundedNext Rapid Pro 50K", "Lucid Flex 50K", "Lucid Daily 50K (EOD)", "Apex EOD 50K", "Apex Intraday 50K", "MFF Rapid 50K",
         "Tradeify Lightning 50K", "Lucid Direct 50K (instant)"]
PROMO = {"Topstep 50K Standard": 25, "Topstep 50K Consistency": 25}  # 50% referral code until end of Nov (first month)

def net(r, T, s, D):
    w, a = F.BUDGET, None
    first = r["fee"] + (r["act"] if r["target"] is None else 0)
    for i in range(s, min(s + D, F.n)):
        if a is None:
            if w < first: break
            w -= r["fee"]; a = P.new_acct(r)
            if r["target"] is None: w -= r["act"]
        if r.get("data") and (i - s) % 21 == 0: w -= r["data"]
        a, w = P.step(a, r, T, i, w)
    return w - F.BUDGET

out = []
for D in (21, 26):
    for nm in PLANS:
        r = dict(A[nm])
        if nm in PROMO: r["fee"] = PROMO[nm]
        best = None
        for ke, kf, tp in itertools.product((3, 5, 8, 12, 16, 25), (1, 2, 3, 5, 8), (None, 500, 800, 1500)):
            if r["target"] is None and ke != 3: continue
            T = tuple(P.day_table(F.m, F.lo, k, tp, None, r.get("dll")) for k in (ke, kf, kf))
            tr = np.array([net(r, T, s, D) for s in range(20, F.half - 30, 4)])
            sc = (np.mean(tr >= 0), tr.mean())
            if best is None or sc > best[0]: best = (sc, ke, kf, tp, T)
        _, ke, kf, tp, T = best
        te = np.array([net(r, T, s, D) for s in range(F.half, F.n - 30, 2)])
        line = f"| {D} d | {nm} | ${r['fee']} | {ke}->{kf} tp {tp} | {np.mean(te >= 0):.0%} | {np.mean(te >= 430):.0%} | {te.mean():+.0f} | {r.get('bots')} |"
        print(line, flush=True); out.append(line)
open("month1fund.md", "w").write("| days | plan | fee | setup | TEST P(money back, net>=0) | TEST P(net >= +$430) | avg $ | bots |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(out) + "\n")
