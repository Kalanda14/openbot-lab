"""a12 shared setup: same as a11_80 (a8b -> a8_starttime -> a6_exec), plus sim2 from lib2 and helper run()."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a8b.py").read().split("rules = {")[0])
from lib2 import sim2
rule = lambda s: (v[s] >= th) | (rt[s] >= np.nanpercentile(rt[SA], 66.7))
r2 = dict(real); r2.pop("lot")
BASE = dict(r2, band=0.5, f=0.5, days=31, G=700.0)
def starts(S, days=31):
    s = S[rule(S)]; return s[s + days < len(X) - 1]
SS = {"SA": starts(SA), "ST": starts(ST), "S17": starts(S17)}
def run(nm, LG=None, **kw):
    k = dict(BASE); k.update(kw); res = {}
    for p, s in SS.items():
        W = sim2(L if LG is None else LG, s, tr, ret_all=True, **k)["W"]; res[p] = ((W >= k["G"] - 1e-9).mean(), (W < 100).mean())
    P(f"| {nm} | " + " | ".join(f"{a:.0%}/{b:.0%}" for a, b in res.values()) + " |")
    return res
