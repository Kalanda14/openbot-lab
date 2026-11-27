"""Re-tune sizing (f, cap, band) for 21 and 31 days, EUR400, CFD swap-free + start rule. Must help all 3 periods."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("a8b.py").read().split("rules = {")[0])
rule = lambda s: (v[s] >= th) | (rt[s] >= np.nanpercentile(rt[SA], 66.7))
P("| days f cap band | 2020-26 | 2024-26 | 2017-19 | min |\n|---|---|---|---|---|")
for days in (21, 31):
    for f in (0.35, 0.5, 0.7, 1.0):
        for cap in (50, 100, 200):
            for band in (0.25, 0.5):
                kw = dict(real); kw.update(cap=cap, band=band, f=f, days=days); cells = []; hs = []
                for S in (SA, ST, S17):
                    s = S[rule(S)]; s = s[s + days < len(X) - 1]
                    W = sim(L, s, tr, ret_all=True, **kw)["W"]; hs.append((W >= 700).mean()); cells.append(f"{hs[-1]:.0%}/{(W<100).mean():.0%}")
                P(f"| {days} {f} {cap} {band} | " + " | ".join(cells) + f" | {min(hs):.0%} |")
open(f"{LAB}/audit/a10_tune.md", "w").write("\n".join(out))
