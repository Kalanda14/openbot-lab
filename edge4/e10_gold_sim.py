"""Month sim (31 days, EUR400->700, CFD mid swap-free costs, start rule) with the gold-night sleeve added to ON leg 0
(like TREND in audit/lib.make): extra return a_t = wg * gold_vm_t (net 1.5 bp/night), wipe term 2*min(a,0).
Gold weight = risk-parity ratio from e9 (gold vol-managed series scaled to 1/3 of book train vol) and half/double.
Then EVERY leg (r, w, up, c) and gold are rescaled by s so the day-total train std equals the old book's (same risk),
which makes the comparison a pure Sharpe change. Also a 'no rescale' version (gold simply added, like a12 FOMC)."""
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a12_base.py").read())
gd = pd.read_csv(f"{LAB}/edge4/gold_daily.csv", index_col=0, parse_dates=True).gold_vm.reindex(X).fillna(0).values
tot = sum(l["r"] for l in L); bkd = pd.read_csv(f"{LAB}/edge4/book_daily.csv", index_col=0, parse_dates=True).BOOK.values
trm = np.asarray(tr)
P(f"sim legs day-total train std {tot[trm].std():.5f}; gold_vm train std {gd[trm].std():.5f}; corr(gold, legs total) {np.corrcoef(gd, tot)[0,1]:+.3f}")
sh = lambda x: x.mean() / x.std() * np.sqrt(252)
def gold_legs(mult, rescale=True):
    a = mult * gd * tot[trm].std() / gd[trm].std() / 3
    new = tot + a; s = tot[trm].std() / new[trm].std() if rescale else 1.0
    P(f"  gold x{mult} rescale={rescale}: s={s:.3f}; day-total Sharpe all {sh(tot):.2f} -> {sh(new * s):.2f}; 2017-21 {sh(tot[:len(X)][np.asarray(X.year <= 2021)]):.2f} -> {sh((new*s)[np.asarray(X.year <= 2021)]):.2f}; 2022-26 {sh(tot[np.asarray(X.year >= 2022)]):.2f} -> {sh((new*s)[np.asarray(X.year >= 2022)]):.2f}")
    LG = []
    for j, l in enumerate(L):
        l = dict(l); l["r"] = l["r"] * s; l["w"] = l["w"] * s; l["up"] = l["up"] * s; l["c"] = l["c"] * s
        if j == 0: l["r"] = l["r"] + a * s; l["w"] = l["w"] + 2 * np.minimum(a, 0) * s; l["up"] = l["up"] + np.maximum(a, 0) * s
        LG.append(l)
    return LG
smooth = lambda W, i, d, l, m: np.maximum(100 * np.clip((W - 100) / 300, 0, 1), 1)
P("| variant | SA hit/<100 | ST | S17 |\n|---|---|---|---|")
R = {}
for cn, kw in (("cap100", dict(cap=100)), ("smooth 100*(W-100)/300", dict(capf=smooth))):
    R[f"base {cn}"] = run(f"base {cn}", **kw)
    for m in (0.5, 1.0, 2.0): R[f"gold x{m} {cn}"] = run(f"gold x{m} rescaled {cn}", LG=gold_legs(m), **kw)
    R[f"gold x1 norescale {cn}"] = run(f"gold x1 NOT rescaled {cn}", LG=gold_legs(1.0, False), **kw)
import json; json.dump(R, open(f"{LAB}/edge4/e10_gold_sim.json", "w"))
open(f"{LAB}/edge4/e10_gold_sim.md", "w").write("\n".join(out))
