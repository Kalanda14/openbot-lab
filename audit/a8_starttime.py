"""NEW idea: pick WHEN to start the month. Hit rate by start-day state (pre-registered buckets), CFD mid swap-free costs.
Check 2020-26 and 2017-19 separately: a rule only counts if it helps in BOTH."""
import sys; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
exec(open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a6_exec.py").read().split('P("\\n| scenario')[0])
real = dict(spike_pt=10, cost_b=0.75, cost_on=1.5, on_extra_pt=1.5, lot=0.01, swap=0.0)
L = lg("rt2", "low", 1.0, 1.0); tr = B["rt2"]["tr"]
px = np.asarray(B["rt2"]["px"], float)
if px.ndim == 2: px = np.array([r[np.isfinite(r)][-1] if np.isfinite(r).any() else np.nan for r in px])
px = pd.Series(px, index=X).ffill(); dr = np.log(px).diff()
feat = {"vol20": dr.rolling(20).std().shift(1).values, "ret60": px.pct_change(60).shift(1).values,
        "dd": (px / px.rolling(120, min_periods=20).max() - 1).shift(1).values,
        "vol5/20": (dr.rolling(5).std() / dr.rolling(20).std()).shift(1).values}
for nm, S in (("2020-26", SA), ("2017-19", S17)):
    r = sim(L, S, tr, ret_all=True, **real); W = r["W"]; hit = W >= 700
    P(f"\n## {nm}: all starts {hit.mean():.0%} (n={len(S)})")
    for k, v in feat.items():
        x = v[S]; q = np.nanpercentile(x, [33.3, 66.7])
        b = np.digitize(x, q)
        P(f"{k:8s} low/mid/high third: " + "  ".join(f"{hit[b==i].mean():.0%} (<100: {(W[b==i]<100).mean():.0%})" for i in range(3)))
open(f"{LAB}/audit/a8_starttime.md", "w").write("\n".join(out))
