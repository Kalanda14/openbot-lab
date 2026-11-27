"""Locked-100 plan check: broker money must double in 21 days (300->600 = same ratio as 400->800).
Book = eubook (vol-managed B+jobs2x, ON_eu_down real CME, TREND). Cost stress on B: extra pts per B trading day (NQ ~ 0.5bp/pt at ~20k)."""
import numpy as np, goal80 as g, hybrid4 as H, m300b as M, eubook as E, eubook2 as E2
H.start0 = 40
B0 = g.S.B.copy(); half = len(g.S) // 2
for extra in (0.0, 1.12, 2.24):
    g.S["B"] = B0 - (B0 != 0) * extra * 0.5e-4
    R, WR = E.build(E.new)
    for f in (0.5, 0.75):
        a = M.run(R, WR, H.PA, 400, 100, 0, f, 0.0); b = M.run(E2.cut(R), WR, H.PA, 400, 100, 0, f, 0.0)
        print(f"cost +{extra}pt f {f}: double {a[0]:.0%} (halves {a[1]:.0%}/{a[2]:.0%}) | edge x0.7 {b[0]:.0%}", flush=True)
g.S["B"] = B0
