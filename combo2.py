"""Month-1 money back, realistic fees: 1st Topstep combine $25 (50% code, first purchase only), 2nd $49; activation $149 each;
API $29/mo. Optional own-account sleeve: idle cash above a $200 fee reserve is deadline-sized (cap 30x, B+ON+TREND book)
toward a wallet of $430 by day D. Test starts 2022-26 (own book series from goal80 aligned by date)."""
import numpy as np, fundsim as F, propsim as P, month1fund as M, goal80 as g
A = M.A
def mk(ke, kf, tp, fee):
    r = dict(A["Topstep 50K Consistency"]); r["fee"] = fee
    return r, tuple(P.day_table(F.m, F.lo, k, tp, None, None) for k in (ke, kf, kf))
gi = {str(x.date()): i for i, x in enumerate(g.S.index)}
def run(books, s, D, own):
    w, acc, cash = F.BUDGET, [None] * len(books), 0.0
    for t, i in enumerate(range(s, s + D)):
        for j, (r, T) in enumerate(books):
            if acc[j] is None and t == 0:
                w -= r["fee"]; acc[j] = P.new_acct(r)
            if acc[j] is None: continue
            if t % 21 == 0 and j == 0: w -= 29
            acc[j], w = P.step(acc[j], r, T, i, w)
        if own:
            k = gi.get(F.d[i])
            if t == 0: cash = max(w - 200, 0); w -= cash
            if k is not None and cash > 1:
                tot = w + cash; left = D - t
                if tot < F.BUDGET:
                    need = F.BUDGET - w
                    if cash < need:
                        z = g.norm.ppf(max(cash / need, 1e-6))
                        lev = min(g.norm.pdf(z) * need / (g.sig_tr * np.sqrt(left) * cash), 30)
                        cash *= 1 + lev * g.R[k]
        if own and t == D - 1: w += cash
    return w - F.BUDGET
for nm, books in (("1 acct 25->8", [mk(25, 8, 500, 25)]), ("2 accts 25->8 + 12->5", [mk(25, 8, 500, 25), mk(12, 5, 800, 49)]),
                  ("2 accts 25->8 + 8->3", [mk(25, 8, 500, 25), mk(8, 3, 800, 49)])):
    for own in (False, True):
        for D in (21, 26):
            x = np.array([run(books, s, D, own) for s in range(F.half, F.n - 30, 2)])
            print(f"> {nm}{' + own cash sleeve' if own else ''} {D}d: P(money back) {np.mean(x >= 0):.0%} | P(+$430) {np.mean(x >= 430):.0%} | avg {x.mean():+.0f}", flush=True)
