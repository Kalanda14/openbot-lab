"""The mathematically BEST possible prop plan for a given edge (dynamic programming / Bellman).
Question: what is the highest possible chance of getting a first payout within D trading days, if each day you
may pick ANY size (0..40 MNQ, steps of 2) based on where you are? No rule-of-thumb: the exact optimum over all sizing plans.
Game (generous version of Apex 50K EOD; consistency, qualifying days and trailing floor IGNORED -> true answer
is LOWER, so this is an upper bound):
  evaluation: start 0, fail at -$2,000 (incl. worst open loss of the day), pass at +$3,000
  funded    : start 0, fail at -$2,000, first payout possible at +$2,600 (buffer $2,100 + $500 min)
Days = real B days on CME NQ futures (Databento 1m, 2017-26): close $ and worst open $ per MNQ, today's price.
Theory check (optional stopping theorem): with ZERO edge no plan can beat 2000/5000 = 40% for the evaluation
and 2000/4600 = 43% for funded -> about 17% for both, however clever the sizing.
"""
import numpy as np

z = np.load("dbdata/paths_real.npz")
sc = z["px"][-1] / z["px"] * 2.0
CL, WO = z["mtm"][:, -1] * sc, np.minimum(z["low"].min(1), 0) * sc
STEP, FL, TE, TF = 50.0, -2000.0, 3000.0, 2600.0
xe = np.arange(FL, TE, STEP); xf = np.arange(FL, TF, STEP)
K = np.arange(0, 41, 2)
sel = np.random.default_rng(0).choice(len(CL), 500, replace=False); mu0 = CL.mean(); CL, WO = CL[sel], WO[sel]  # 500 random real days
CL = CL - CL.mean() + mu0  # keep the true 10-year average edge


def solve(cl, wo, D):
    ve, vf = np.zeros(len(xe)), np.zeros(len(xf))
    for _ in range(D):
        def back(x, v, tgt, win_value):
            best = np.zeros(len(x))
            for k in K:
                x2 = x[:, None] + k * cl[None, :]
                dead = (x[:, None] + k * wo[None, :] <= FL) | (x2 <= FL)
                won = x2 >= tgt
                i = np.clip(((x2 - FL) / STEP).astype(int), 0, len(x) - 1)
                val = np.where(dead, 0.0, np.where(won, win_value, v[i])).mean(1)
                best = np.maximum(best, val)
            return best
        vf_new = back(xf, vf, TF, 1.0)
        ve = back(xe, ve, TE, vf[int((0 - FL) / STEP)])
        vf = vf_new
    return ve[int((0 - FL) / STEP)], vf[int((0 - FL) / STEP)]


mu = mu0; sh = mu / CL.std() * np.sqrt(252)
print(f"real B edge: ${mu:.1f}/day per MNQ, Sharpe {sh:.2f}\n")
print("| days | edge | best possible P(first payout) | funded alone: P(payout) |\n|---|---|---|---|")
for D in (21, 63, 126):
    for nm, add in (("zero edge", -mu), ("our edge B", 0.0), ("Sharpe 2x B", mu), ("Sharpe 4x B", 3 * mu)):
        pe, pf = solve(CL + add, WO + min(add, 0), D)
        print(f"| {D} | {nm} | {pe:.0%} | {pf:.0%} |", flush=True)
