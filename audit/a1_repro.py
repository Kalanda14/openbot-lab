"""Audit step 1: reproduce final Browne plan (ON30/B30, f0.5 cap100, band25, tp) and time it."""
import sys, time; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/m2")
t0 = time.time()
from intraday import *
bk = build(on="base", bsrc="real"); LG = make(bk, 30, 30)
print("setup", round(time.time() - t0), "s, legs/day", len(LG), "weights", bk["w"], "sig_tr", g.sig_tr)
for nm, s in (("all", STARTS), ("20-23", S_TR), ("24-26", S_TE)):
    print(nm, len(s), fmt(sim(LG, s, 0.5, tp=True, band=0.25)))
print("total", round(time.time() - t0), "s")
