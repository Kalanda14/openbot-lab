"""Ideas 2-4 on the roll-fixed base book. Pick on 2020-23 starts, report 2024-26 starts separately."""
import numpy as np, sys
from core import *
var = sys.argv[1] if len(sys.argv) > 1 else "base"
P, WP = build(var); R = sum(P.values()); WR = sum(WP.values())
def row(nm, **kw):
    a, b, c = sim(R, WR, **kw), sim(R, WR, starts=S_TR, **kw), sim(R, WR, starts=S_TE, **kw)
    print(f"{nm:40s} all {fmt(a)} | 20-23 {fmt(b)} | 24-26 {fmt(c)}", flush=True)
print(f"ON {var}")
row("baseline f0.5 cap100")
# Idea 2: trailing realized book vol (20d, lag 1) instead of fixed sig_tr
rv = pd.Series(R).rolling(20, min_periods=10).std().shift(1).bfill().values
for f in (0.5, 0.7, 1.0):
    row(f"2: sigma = trailing 20d vol, f{f}", sig=rv, f=f)
# Idea 3: re-size between legs (ON+TREND first, then B in the US day)
legs = [(P["ON"] + P["TREND"], WP["ON"] + WP["TREND"]), (P["B"], WP["B"])]
for f in (0.5, 0.7):
    row(f"3: two legs per day, f{f}", legs=legs, f=f)
# Idea 4: bounded loss: lev <= 0.9 / |worst intraday book move seen in 2020-21| (train)
wmin = -WR[idx < "2022"].min()
print(f"worst train WR {wmin:.4f} -> cap {0.9/wmin:.0f}x")
for frac in (0.9, 0.5):
    row(f"4: lev <= {frac}/|worst train WR|", cap=frac / wmin)
