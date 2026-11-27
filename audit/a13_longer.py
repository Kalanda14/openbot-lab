"""Lead check after agent a12: wealth-aware caps (G, C) at longer horizons, EUR400. Agent theory said ~58 days needed for 80/5."""
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a12_base.py").read())
lvl = lambda a, b, c, w1, w2: (lambda W, i, d, l, m: np.where(W >= w1, a, np.where(W >= w2, b, c)))
rules_ = {"base cap100": dict(cap=100), "G 150/50/20 (350/250)": dict(capf=lvl(150, 50, 20, 350, 250)),
          "C smooth 100*(W-100)/300": dict(capf=lambda W, i, d, l, m: np.maximum(100 * np.clip((W - 100) / 300, 0, 1), 1)),
          "A cap100, cap30 if W<250": dict(capf=lambda W, i, d, l, m: np.where(W >= 250, 100, 30))}
P("| days | variant | SA | ST | S17 |\n|---|---|---|---|---|")
for days in (42, 52, 63):
    SS = {"SA": starts(SA, days), "ST": starts(ST, days), "S17": starts(S17, days)}
    for nm, kw in rules_.items():
        BASE["days"] = days; run(f"{days} | {nm}", **kw)
open(f"{LAB}/audit/a13_longer.md", "w").write("\n".join(out))
