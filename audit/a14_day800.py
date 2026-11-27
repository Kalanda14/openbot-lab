"""Fake-money 'double in a day': EUR400 -> 800 within 1 trading day (ON night + B day), Browne sizing, broker 400:1, CFD swap-free costs."""
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a12_base.py").read())
allS = {"SA": SA, "ST": ST, "S17": S17}
P("| f cap | SA hit/<100 | ST | S17 |\n|---|---|---|---|")
for f in (0.3, 0.5, 1.0):
    for cp in (100, 200, 400):
        k = dict(r2, band=0.25, f=f, days=1, G=800.0, cap=cp, ncap=400); res = []
        for p, s in allS.items():
            W = sim2(L, s, tr, ret_all=True, **k)["W"]; res.append(f"{(W>=800-1e-9).mean():.0%}/{(W<100).mean():.0%}")
        P(f"| {f} {cp} | " + " | ".join(res) + " |")
open(f"{LAB}/audit/a14_day800.md", "w").write("\n".join(out))
for f in (0.2, 0.3):
    k = dict(r2, band=0.25, f=f, days=1, G=800.0, cap=1e6, ncap=400); res = []
    for p, s in allS.items():
        W = sim2(L, s, tr, ret_all=True, **k)["W"]; res.append(f"{(W>=800-1e-9).mean():.0%}/{(W<100).mean():.0%}/med {np.median(W):.0f}")
    P(f"| {f} nocap(400:1 only) | " + " | ".join(res) + " |")
open(f"{LAB}/audit/a14_day800.md", "w").write("\n".join(out))
