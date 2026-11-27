"""80% hit AND low P(end<100): grid days x cap x start money. Swap-free CFD + start rule, f0.5 band0.5."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("a8b.py").read().split("rules = {")[0])
rule = lambda s: (v[s] >= th) | (rt[s] >= np.nanpercentile(rt[SA], 66.7))
r2 = dict(real); r2.pop("lot")
P("| start, days, cap | 2020-26 | 2024-26 | 2017-19 | worst hit | worst <25% |\n|---|---|---|---|---|---|")
for w0 in (400, 600):
    G = 400 * (w0 + 300) / w0
    for days in (31, 42, 63):
        for cap in (20, 30, 50, 100):
            kw = dict(r2); kw.update(cap=cap, band=0.5, f=0.5, days=days, G=G); c = []; hs = []; ls = []
            for S in (SA, ST, S17):
                s = S[rule(S)]; s = s[s + days < len(X) - 1]
                W = sim(L, s, tr, ret_all=True, **kw)["W"]; hs.append((W >= G - 1e-9).mean()); ls.append((W < 100).mean()); c.append(f"{hs[-1]:.0%}/{ls[-1]:.0%}")
            P(f"| EUR{w0} {days}d cap{cap} | " + " | ".join(c) + f" | {min(hs):.0%} | {max(ls):.0%} |")
open(f"{LAB}/audit/a11_80.md", "w").write("\n".join(out))
