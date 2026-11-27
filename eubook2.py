"""eubook with ALL start windows since 2020-05 (no carry -> no need for 2023-06 start) and a fair cautious case:
each book's own Sharpe cut by the same factor (x0.7) instead of a fixed 1.2."""
import numpy as np, goal80 as g, hybrid4 as H, m300b as M, eubook as E
H.start0 = 40
def cut(R, fac=0.7):
    s = R.mean() / R.std(); return R - R.mean() + fac * s * R.std()
for nm, on in (("old ON (free data)", g.S.ON), ("ON_eu_down (real CME)", E.new)):
    print(nm); R, WR = E.build(on)
    for f in (0.5, 0.75):
        a = M.run(R, WR, H.PA, 300, 100, 0, f, 0.0); b = M.run(cut(R), WR, H.PA, 300, 100, 0, f, 0.0)
        print(f"  1 mo f {f}: backtest hit {a[0]:.0%} (<100 {a[3]:.0%}, halves {a[1]:.0%}/{a[2]:.0%}) | edge x0.7 hit {b[0]:.0%} (<100 {b[3]:.0%})", flush=True)
