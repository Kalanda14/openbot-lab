"""a12 part 1: wealth / regime aware caps, stop-out, Browne target shrink, floor-on-cushion. EUR400 -> 700, 31d,
f0.5 band0.5, CFD swap-free costs, start rule. Every variant is logged (count = rows). Selection is made on SA only."""
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a12_base.py").read())
import json
R = {}
def go(nm, **kw): R[nm] = run(nm, **kw)
P("| variant | SA hit/<100 | ST | S17 |\n|---|---|---|---|")
for c in (100, 50, 30): go(f"base cap{c}", cap=c)
# A. step drawdown cap: cap hi while W >= w1 else lo
for hi in (100, 200):
    for w1 in (200, 250, 300, 350):
        for lo in (5, 10, 20, 30):
            go(f"A step hi{hi} W<{w1}->cap{lo}", capf=lambda W, i, d, l, m, hi=hi, w1=w1, lo=lo: np.where(W >= w1, hi, lo))
# B. stop-out: stop trading (cap 0) once W < X
for X_ in (150, 200, 250, 300):
    go(f"B stop-out W<{X_}", capf=lambda W, i, d, l, m, X_=X_: np.where(W >= X_, 100, 0.0))
# B2. stop-out permanent (once running min wealth < X, never trade again)
for X_ in (150, 200, 250):
    go(f"B2 perm stop minW<{X_}", capf=lambda W, i, d, l, m, X_=X_: np.where(m >= X_, 100, 0.0))
# C. smooth cap ~ cushion over 100
for hi in (100, 200):
    for p in (1, 2):
        go(f"C smooth hi{hi}*((W-100)/300)^{p}", capf=lambda W, i, d, l, m, hi=hi, p=p: np.maximum(hi * np.clip((W - 100) / 300, 0, 1) ** p, 1))
# D. regime cap by vol20 of the day (v known at day open, shift(1))
for hi in (100, 150):
    for lo in (30, 50):
        go(f"D vol cap hi{hi} (vol<24%) lo{lo}", capf=lambda W, i, d, l, m, hi=hi, lo=lo: np.where(np.nan_to_num(v[d], nan=0) < th, hi, lo))
# E. Browne target shrink when behind
for w1 in (250, 300):
    for gl in (400, 500):
        go(f"E target {gl} while W<{w1}", gbf=lambda W, i, w1=w1, gl=gl: np.where(W >= w1, 700.0, gl), cap=100)
# F. Browne on cushion over floor (related to dead-end floors; low floors only)
for F_ in (50, 100):
    go(f"F floor-cushion F{F_} cap100", F=F_, cap=100)
    go(f"F floor-cushion F{F_} cap200", F=F_, cap=200)
P(f"\nvariants tried in part 1: {len(R)}")
json.dump({k: v_ for k, v_ in R.items()}, open(f"{LAB}/audit/a12_sizing.json", "w"))
open(f"{LAB}/audit/a12_sizing.md", "w").write("\n".join(out))
