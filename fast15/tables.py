"""Build the test tables for REPORT.md from res_{train,test}_D{0,1,2}_*.csv -> tables.md"""
import glob, pandas as pd
K = ["inst", "feat", "H", "subset"]
PICKS = [("BTCUSDT", "burst", 15, "all")] + [("BTCUSDT", "logit", h, "top10") for h in (30, 60, 300)] + \
        [("ETHUSDT", "logit", h, "top10") for h in (15, 30, 60, 300)] + [("NQ", "logit", h, "top10") for h in (15, 30, 60)] + [("NQ", "tod", 300, "all")]
COST = {"BTCUSDT": 15.0, "ETHUSDT": 15.0, "NQ": 1.0}   # cheapest round trip: 2x0.075% bps / 1.0 pt CFD
out = []
for D in (0, 1, 2):
    tr = pd.concat([pd.read_csv(f) for f in glob.glob(f"res_train_D{D}_*.csv")])
    te = pd.concat([pd.read_csv(f) for f in glob.glob(f"res_test_D{D}_*.csv")])
    m = te.merge(tr[K + ["acc", "z"]], on=K, suffixes=("", "_tr"))
    out.append(f"\n## Delay {D}s: pre-registered picks + always-up baseline (TEST)\n")
    out.append("| signal | H s | train acc | test acc ± se | n | trades/day | tie % | avg signed move | cost RT | >52.1%? | >55.6%? | beats cost? |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    sel = m[[tuple(x) in PICKS or x[1] == "up" for x in m[K].values]].sort_values(["inst", "feat", "H"])
    for _, r in sel.iterrows():
        u = "bps" if r.inst != "NQ" else "pt"
        out.append(f"| {r.inst} {r.feat}/{r.subset} | {r.H} | {r.acc_tr:.3f} | {r.acc:.4f} ± {r.se:.4f} | {r.n} | {r.perday:.0f} | {100*r.tie:.1f} | "
                   f"{r.edge:+.2f} {u} | {COST[r.inst]:.0f} {u} | {'yes' if r.acc - 2*r.se > .521 else 'no'} | {'yes' if r.acc - 2*r.se > .556 else 'no'} | "
                   f"{'yes' if r.edge > COST[r.inst] else 'no'} |")
    out.append(f"\nAll {len(m)} test variants at delay {D}s: |z|>3.8 in {(m.z.abs() > 3.8).sum()}; "
               f"acc-2se > 52.1%: {((m.acc - 2*m.se) > .521).sum()}; > 55.6%: {((m.acc - 2*m.se) > .556).sum()}; edge > cost: {(m.edge > m.inst.map(COST)).sum()}")
    best = m.sort_values("z", ascending=False).head(8)
    out.append("\nTop 8 test variants by z (not pre-registered, for context):\n\n| inst | feat/subset | H | test acc | n | trades/day | edge |\n|---|---|---|---|---|---|---|")
    for _, r in best.iterrows():
        out.append(f"| {r.inst} | {r.feat}/{r.subset} | {r.H} | {r.acc:.4f} | {r.n} | {r.perday:.0f} | {r.edge:+.2f} |")
open("tables.md", "w").write("\n".join(out)); print("\n".join(out))
