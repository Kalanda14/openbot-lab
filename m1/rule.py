"""Simple closed-form rule distilled from the DP: Browne deadline sizing re-sized per leg (ON+TREND, then B),
sigma factor f, plus 'bold play' on the last day (lev = cap on both legs). Base and plus ON."""
import numpy as np
from core import *
def run(P, WP, starts, f=0.5, cap=100, bold=True):
    legs = [(P["ON"] + P["TREND"], WP["ON"] + WP["TREND"]), (P["B"], WP["B"])]
    n = (idx < "2022").sum(); lv = [np.var(l[0][:n]) for l in legs]; tv = sum(lv); out = []
    for s in starts:
        W = 400.0
        for i in range(21):
            for j, (r, wr) in enumerate(legs):
                if W >= 700 or W <= 1: break
                rem = (20 - i) + sum(lv[j:]) / tv
                lev = cap if (bold and i == 20) else min(nd.pdf(nd.ppf(min(max(W / 700, 1e-6), 0.999999))) * 700 / (f * g.sig_tr * np.sqrt(rem) * W), cap)
                if 1 + lev * wr[s + i] <= 0: W = 0.0; break
                W *= 1 + lev * r[s + i]
        out.append(max(W, 0))
    o = np.array(out); return dict(hit=(o >= 700).mean(), lt100=(o < 100).mean(), mid=((o >= 100) & (o < 700)).mean())
for var in ("base", "plus"):
    P, WP = build(var)
    for f, bold in ((0.5, False), (0.5, True), (0.4, True)):
        print(f"{var} legs f{f} bold={bold}: all {fmt(run(P, WP, STARTS, f, bold=bold))} | 20-23 {fmt(run(P, WP, S_TR, f, bold=bold))} | 24-26 {fmt(run(P, WP, S_TE, f, bold=bold))}", flush=True)
