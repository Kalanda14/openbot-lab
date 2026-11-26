"""Push month-1 money-back odds: sleeve cap 30/45/60/80, sleeve + funding spread 3x, Topstep vs MFF Rapid prop.
Spread series (HL-Binance) aligned to the US days used by the own book; before 2023-06 spread = 0."""
import numpy as np, pandas as pd, combo2 as K, fundsim as F, propsim as P, goal80 as g, month1fund as M
pa = pd.read_csv("dbdata/perparb.csv", index_col=0, parse_dates=True).PERPARB
idx = g.S.index; gi2 = np.clip(idx.searchsorted(pa.index), 0, len(idx) - 1)
PA = (1 + pa).groupby(idx[gi2]).prod().sub(1).reindex(idx).fillna(0).values
def prop(which):
    if which == "topstep": return K.mk(25, 8, 500, 25)
    r = dict(M.A["MFF Rapid 50K"]); return r, tuple(P.day_table(F.m, F.lo, k, 1500, None, None) for k in (8, 8, 8))
def run(s, D, cap, spread, which, R):
    r, T = prop(which); w = F.BUDGET - r["fee"]; a = P.new_acct(r); cash = 0.0
    for t, i in enumerate(range(s, s + D)):
        if which == "topstep" and t % 21 == 0: w -= 29
        if t == 0: cash = max(w - 100, 0); w -= cash
        if a is not None:
            if a["ph"] == "eval" and w < r["act"] and cash > 0: top = min(r["act"] - w, cash); w += top; cash -= top
            a, w = P.step(a, r, T, i, w)
        k = K.gi.get(F.d[i])
        if k is not None and cash > 1:
            if spread: cash *= 1 + 3 * PA[k]
            if w + cash < F.BUDGET:
                need = F.BUDGET - w
                if cash < need:
                    z = g.norm.ppf(max(cash / need, 1e-6)); lev = min(g.norm.pdf(z) * need / (g.sig_tr * np.sqrt(D - t) * cash), cap)
                    cash *= 1 + lev * R[k]
    return w + cash - F.BUDGET
fwd = g.R - g.R.mean() + 1.2 * g.R.std() / np.sqrt(252)
for which in ("topstep", "mff"):
    for cap in (45, 60, 80):
        for spread in (False, True):
            for nm, R in (("backtest", g.R), ("cautious", fwd)):
                x = np.array([run(s, 21, cap, spread, which, R) for s in range(F.half, F.n - 30, 2)])
                print(f"> {which} | cap {cap} | spread {spread} | {nm}: P(money back) {np.mean(x >= 0):.0%} | P(+$430) {np.mean(x >= 430):.0%} | P(lose>$200) {np.mean(x < -200):.0%}", flush=True)
