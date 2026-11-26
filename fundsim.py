"""Funded-account odds with REAL current rules (from research bots -> rules2026.json, converted to propsim dicts).
Real CME NQ B paths (dbdata/paths_real.npz). Budget $430 (~EUR 400): buy a challenge, rebuy after a fail while money lasts;
payouts go to the wallet (and can fund rebuys). Overlays (eval MNQ, funded MNQ, daily take-profit) picked on starts
2017-21 by P(first payout <= 126 days), judged on starts 2022-26.
Reports: P(funded <= 63 d), P(first payout <= 63 / 126 d), avg wallet change after 126 d.
Usage: python fundsim.py  -> fundsim.md
"""
import json, os, itertools, numpy as np
os.environ["PATHS"] = "dbdata/paths_real.npz"
import propsim as P

BUDGET = 430.0
d, m, lo = P.load(); n = len(d); half = int(np.searchsorted(d, "2022-01-01"))


def one(r, T, s, days=126):
    w, a, funded_day, pay_day, spent = BUDGET, None, None, None, 0.0
    first = r["fee"] + (r["act"] if r["target"] is None else 0)
    for i in range(s, min(s + days, n)):
        if a is None:
            if w < first: break
            w -= r["fee"]; spent += r["fee"]; a = P.new_acct(r)
            if r["target"] is None:
                w -= r["act"]; spent += r["act"]
                if funded_day is None: funded_day = i - s
        if r.get("data") and (i - s) % 21 == 0: w -= r["data"]
        was_eval = a["ph"] == "eval"; np0 = a["np"]
        a, w = P.step(a, r, T, i, w)
        if a is not None and was_eval and a["ph"] == "fund" and funded_day is None: funded_day = i - s
        if a is not None and a["np"] > np0 and pay_day is None: pay_day = i - s
    return funded_day, pay_day, w - BUDGET


def score(r, T, rng):
    res = [one(r, T, s) for s in rng]
    f = np.array([x[0] if x[0] is not None else 999 for x in res]); p = np.array([x[1] if x[1] is not None else 999 for x in res])
    pnl = np.array([x[2] for x in res])
    return dict(f63=np.mean(f <= 63), p63=np.mean(p <= 63), p126=np.mean(p <= 126), pnl=pnl.mean())


def best(r):
    tr, te = range(20, half - 130, 5), range(half, n - 130, 3)
    cands = []
    for ke, kf, tp in itertools.product((3, 5, 8, 12), (1, 2, 3, 5), (None, 300, 500, 800, 1500)):
        if r["target"] is None and ke != 3: continue  # instant: no eval size
        T = tuple(P.day_table(m, lo, k, tp, None, r.get("dll")) for k in (ke, kf, kf))
        cands.append((score(r, T, tr)["p126"], ke, kf, tp, T))
    cands.sort(key=lambda x: -x[0]); _, ke, kf, tp, T = cands[0]
    return (ke, kf, tp), score(r, T, tr), score(r, T, te)


if __name__ == "__main__":
    import sys
    rules = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "rules2026.json"))
    L = ["| firm plan | fee | setup (eval->funded MNQ, tp) | TEST P(funded <=3 mo) | TEST P(1st payout <=3 mo) | TEST P(1st payout <=6 mo) | TEST avg $ after 6 mo | bots |",
         "|---|---|---|---|---|---|---|---|"]
    for nm, r in rules.items():
        setup, a, b = best(r)
        L.append(f"| {nm} | ${r['fee']}{'/mo' if r['monthly'] else ''} | {setup[0]}->{setup[1]}, tp {setup[2]} | {b['f63']:.0%} | {b['p63']:.0%} | {b['p126']:.0%} | {b['pnl']:+.0f} | {r.get('bots','?')} |")
        print(L[-1], flush=True)
    open(("fundsim_b.md" if len(sys.argv) > 1 else "fundsim.md"), "w").write("\n".join(L) + "\n")
