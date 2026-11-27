"""What does it take to reach 70% with REAL costs (CFD swap-free) + start rule? Vary start money (via G, sim is scale-free) and days."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("a8b.py").read().split("rules = {")[0])
rule = lambda s: (v[s] >= th) | (rt[s] >= np.nanpercentile(rt[SA], 66.7))
real2 = dict(real); real2.pop("lot")  # lot rounding is not scale-free
P("| case | 2020-26 | 2024-26 | 2017-19 |\n|---|---|---|---|")
for w0 in (400, 500, 600, 800):
    for days in (21, 26, 31):
        G = 400 * (w0 + 300) / w0; cells = []
        for S in (SA, ST, S17):
            s = S[rule(S)]; s = s[s + days < len(X) - 1]
            W = sim(L, s, tr, ret_all=True, G=G, days=days, **real2)["W"]; cells.append(f"{(W>=G-1e-9).mean():.0%} /<25% {(W<100).mean():.0%}")
        P(f"| EUR {w0}, {days} days, start rule | " + " | ".join(cells) + " |")
open(f"{LAB}/audit/a9_reach70.md", "w").write("\n".join(out))
