"""Check audit lib reproduces m2 final (71/63) on the original index, then ON 'up' approximation effect."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
bk = build(); LG = make(bk); ix = bk["ix"]
ST = np.arange(40, len(ix) - 30, 2); TE = ST[ix[ST] >= "2024"]
for nm, s in (("all", ST), ("24-26", TE)): print(nm, fmt(sim(LG, s, bk["tr"])))
print(bk["w"])
