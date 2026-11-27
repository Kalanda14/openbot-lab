"""a12 part 3: add a pre-FOMC sleeve to the ON legs: on the night before each scheduled FOMC statement, hold extra long NQ
notional kF x (median active ON notional) over the same 15:55->03:30 ON path (real 1m lows for wipe, same CFD costs).
Roll-week nights with no clean path get 0 (as the ON sleeve). Window fixed a priori (the existing ON window);
FOMC stat in a12_fomc.md: train 2017-21 +29bp t3.6, test 2022-26 +19.5bp t2.25 (other nights +5.5 / +1.8)."""
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a12_base.py").read())
exec(open(f"{LAB}/audit/a12_fomc.py").read().split("d = pd.read_pickle")[0].split('"""', 2)[2])  # FOMC list only
o = B["rt2"]["on"]; nON = o["r"].shape[1]
mask = np.asarray(X.isin(FOMC))
craw0 = np.array(L[0]["c"]); cref = np.median(craw0[(craw0 > 0) & tr])
P(f"FOMC eves in sim index: {mask.sum()}, with clean ON path: {(mask & (np.abs(o['r']).sum(1) > 0)).sum()}; ON active on those nights: {(mask & (craw0 > 0)).sum()}")
def fomc_legs(kF, only_down=False):
    add = np.where(mask, kF * cref, 0.0)
    LG = [dict(l) for l in L]
    for j in range(nON):
        l = LG[j]; assert l["on"] and l["j"] == j
        l["r"] = l["r"] + add * o["r"][:, j] - (add * 0.5e-4 if j == 0 else 0)
        l["w"] = l["w"] + add * o["wl"][:, j]; l["up"] = l["up"] + add * o["up"][:, j]
        l["c"] = l["c"] + add; l["held"] = (l["c"] > 0) & (j > 0)
    return LG
P("| variant | SA hit/<100 | ST | S17 |\n|---|---|---|---|")
R = {}
for cap in (100, 50, 30):
    R[f"base cap{cap}"] = run(f"base cap{cap}", cap=cap)
    for kF in (0.5, 1, 2, 3):
        R[f"FOMC kF{kF} cap{cap}"] = run(f"FOMC kF{kF} cap{cap}", LG=fomc_legs(kF), cap=cap)
step = lambda W, i, d, l, m: np.where(W >= 250, 100, 30)
for kF in (1, 2):
    R[f"FOMC kF{kF} + A step hi100 W<250->cap30"] = run(f"FOMC kF{kF} + A step hi100 W<250->cap30", LG=fomc_legs(kF), capf=step)
import json; json.dump(R, open(f"{LAB}/audit/a12_fomc_sim.json", "w"))
P(f"variants tried in part 3: {len(R) - 3} (+3 baselines)")
open(f"{LAB}/audit/a12_fomc_sim.md", "w").write("\n".join(out))
