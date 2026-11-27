import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
src = open("a8_starttime.py").read().split("for nm, S in")[0]; exec(src)
ST = SA[X[SA] >= "2024"]
v = feat["vol20"]; rt = feat["ret60"]; th = np.nanpercentile(v[SA], 66.7)
P(f"vol20 threshold (fixed from 2020-26) = {th*np.sqrt(252):.0%} yearly")
rules = {"all": lambda s: np.ones(len(s), bool), "vol high": lambda s: v[s] >= th, "ret60>0": lambda s: rt[s] > 0,
         "vol high & ret60>0": lambda s: (v[s] >= th) & (rt[s] > 0), "vol high | ret60 top": lambda s: (v[s] >= th) | (rt[s] >= np.nanpercentile(rt[SA], 66.7))}
for nm, S in (("2020-26", SA), ("2024-26", ST), ("2017-19", S17)):
    W = sim(L, S, tr, ret_all=True, **real)["W"]
    P(f"## {nm}: " + " | ".join(f"{k}: {(W[m:=f(S)]>=700).mean():.0%} /<100 {(W[m]<100).mean():.0%} (share {m.mean():.0%})" for k, f in rules.items()))
open(f"{LAB}/audit/a8b.md", "w").write("\n".join(out))
