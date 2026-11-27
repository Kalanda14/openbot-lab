"""Is the 63% (2024-26) fragile? (a) ext index minus the Jan-gap days; (b) odd vs even start days; (c) ext with Jan days, by parity."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
bk = build(); LG = make(bk); ix = bk["ix"]
for p in (40, 41):
    s = np.arange(p, len(ix) - 30, 2); print(f"m2 index, start parity {p%2}: all {fmt(sim(LG, s, bk['tr']))} | 24-26 {fmt(sim(LG, s[ix[s] >= '2024'], bk['tr']))}")
X = ext_index(); miss = X[(X >= ix[0]) & ~X.isin(ix)]
X2 = X[~X.isin(miss)]; b2 = build(X2, trend="stack4+crypto", ref=bk); L2 = make(b2)
for p in (0, 1):
    s = starts_for(X2, "2020-05-12", "2027", 30 + p); t = s[X2[s] >= "2024"]
    print(f"ext minus Jan-gap, parity {p}: all {fmt(sim(L2, s, b2['tr']))} | 24-26 {fmt(sim(L2, t, b2['tr']))}")
bx = build(X, trend="stack4+crypto", ref=bk); LX = make(bx)
for p in (0, 1):
    s = starts_for(X, "2020-05-12", "2027", 30 + p); t = s[X[s] >= "2024"]
    print(f"ext full (all real days), parity {p}: all {fmt(sim(LX, s, bx['tr']))} | 24-26 {fmt(sim(LX, t, bx['tr']))}")
