"""ROLL-FIXED overnight drift (instrument_id same at entry/exit/prev day; dbdata/nqD.pkl built by scratch frame.py).
Variants (03:30 exit fixed): base = down day; plus = base AND prior-day VIX/VIX3M > 0.864 (2017-21 median), 2x on 2nd+ down day, skip Friday.
Then book + month-1 +EUR300 odds (eubook build) and locked-100 doubling odds."""
import numpy as np, pandas as pd, goal80 as g, hybrid4 as H, m300b as M, eubook as E, eubook2 as E2
D = pd.read_pickle("dbdata/nqD.pkl"); D = D[D.roll == 0]
ld = lambda f: pd.read_csv(f, index_col=0, parse_dates=True)["CLOSE"].astype(float)
ts = (ld("ext/VIX.csv") / ld("ext/VIX3M.csv")).shift(1).reindex(D.index, method="ffill")
down = D.r55 < 0; down2 = down & (D.r55.shift(1) < 0)
base = (D.x0330 - 0.5e-4).where(down, 0)
plus = (D.x0330 - 0.5e-4).where(down & (ts > 0.864) & (D.index.weekday != 4), 0) * np.where(down2, 2, 1)
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
H.start0 = 40
for nm, s in (("base (roll-fixed)", base), ("plus (VIX filter, 2x streak, no Fri)", plus)):
    tr, te = s[:"2021"], s["2022":]
    print(f"{nm}: sleeve Sharpe train {sh(tr):.2f} test {sh(te):.2f} | by year " + " ".join(f"{y}:{sh(s[str(y)]):+.1f}" for y in range(2017, 2027)))
    on = s.shift(1).reindex(g.S.index).fillna(0)
    R, WR = E.build(on)
    for X, lab in ((300, "+300 from 400"), (400, "double (locked-100 plan)")):
        a = M.run(R, WR, H.PA, X, 100, 0, 0.5, 0.0); b = M.run(E2.cut(R), WR, H.PA, X, 100, 0, 0.5, 0.0)
        print(f"   {lab}: backtest {a[0]:.0%} (<100 {a[3]:.0%}) | edge x0.7 {b[0]:.0%}", flush=True)
