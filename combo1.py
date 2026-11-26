"""Month-1 money back with 2 accounts at once (different setups -> less identical outcomes). Shared $430 wallet; payouts fund
fees. 21 trading days, test starts 2022-26 (setups fixed from month1fund picks + one moderate variant)."""
import numpy as np, fundsim as F, propsim as P, month1fund as M
A = M.A
def mk(nm, ke, kf, tp):
    r = dict(A[nm]); r["fee"] = M.PROMO.get(nm, r["fee"])
    return nm, r, tuple(P.day_table(F.m, F.lo, k, tp, None, r.get("dll")) for k in (ke, kf, kf))
def run(books, s, D=21):
    w, acc = F.BUDGET, [None] * len(books)
    for i in range(s, s + D):
        for j, (nm, r, T) in enumerate(books):
            if acc[j] is None:
                if w < r["fee"] + (149 if "Topstep" in nm else 0): continue
                w -= r["fee"]; acc[j] = P.new_acct(r)
            if r.get("data") and (i - s) % 21 == 0: w -= r["data"]
            acc[j], w = P.step(acc[j], r, T, i, w)
    return w - F.BUDGET
C = {"TC25": mk("Topstep 50K Consistency", 25, 8, 500), "TC12": mk("Topstep 50K Consistency", 12, 5, 800),
     "MFF": mk("MFF Rapid 50K", 8, 8, 1500), "APXI": mk("Apex Intraday 50K", 8, 5, 1500)}
for combo in (["TC25"], ["TC25", "TC12"], ["TC25", "MFF"], ["TC25", "APXI"], ["MFF", "APXI"], ["TC25", "TC12", "APXI"]):
    x = np.array([run([C[k] for k in combo], s) for s in range(F.half, F.n - 30, 2)])
    print(f"> {' + '.join(combo)}: P(money back) {np.mean(x >= 0):.0%} | P(+$430) {np.mean(x >= 430):.0%} | avg {x.mean():+.0f}", flush=True)
