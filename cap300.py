"""How much starting capital gives >=80% odds of +EUR300 in 21 days? Same ratio trick: from W0, +300 == from 400, +400*300/W0.
eubook book, deadline sizing, cap 100, intraday wipe. Reports hit and P(lose > 25% of W0)."""
import numpy as np, goal80 as g, hybrid4 as H, m300b as M, eubook as E, eubook2 as E2
H.start0 = 40
R, WR = E.build(E.new); Rc = E2.cut(R)
for W0 in (400, 800, 1200, 1500, 2000, 3000):
    X = 400 * 300 / W0; best = None
    for f in (0.5, 0.75, 1.0, 1.5, 2.0):
        a = M.run(R, WR, H.PA, X, 100, 0, f, 0.0); b = M.run(Rc, WR, H.PA, X, 100, 0, f, 0.0)
        print(f"start EUR{W0} (+{300/W0:.0%}) f {f}: hit {a[0]:.0%} / weaker edge {b[0]:.0%}", flush=True)
