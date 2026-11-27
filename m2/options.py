"""(B) add-ons on the intraday re-sizing sim: goal-touch exit (tp, any minute close), no-trade band, bold last day,
book variants (plus ON, EOM3), cost stress. Real CME B + ON paths."""
from intraday import *
print("| book | legs | option | f | all | 2020-23 | 2024-26 | re-sizes | cost % |\n|---|---|---|---|---|---|---|---|---|")
for bnm, bkw in (("base", dict()), ("base+EOM3", dict(eom=True)), ("plus", dict(on="plus")), ("plus+EOM3", dict(on="plus", eom=True))):
    bk = build(bsrc="real", **bkw)
    for lnm, st, ost in (("2 legs", None, None), ("ON30/B30", 30, 30), ("ON5/B5", 5, 5)):
        LG = make(bk, st, ost)
        opts = (("-", {}), ("tp", dict(tp=True)), ("tp+band25%", dict(tp=True, band=0.25)), ("tp+bold", dict(tp=True, bold=True)), ("tp, cost x4 (1pt)", dict(tp=True, cost=1.0)))
        if bnm != "base" and lnm != "ON30/B30": opts = opts[:2]
        for onm, kw in opts:
            for f in (0.4, 0.5):
                a, b, c = sim(LG, STARTS, f, **kw), sim(LG, S_TR, f, **kw), sim(LG, S_TE, f, **kw)
                print(f"| {bnm} | {lnm} | {onm} | {f} | {fmt(a)} | {fmt(b)} | {fmt(c)} | {a['nres']:.0f} | {a['cost']*100:.2f} |", flush=True)
