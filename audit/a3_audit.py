"""Main audit runs. Output: audit/a3_audit.md. Single process, light compute."""
import sys, time; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/audit")
from lib import *
t0 = time.time(); out = []
def P(s): print(s, flush=True); out.append(s)
bk = build(); LG = make(bk); ix = bk["ix"]; tr = bk["tr"]
ST = np.arange(40, len(ix) - 30, 2); TE = ST[ix[ST] >= "2024"]; TR0 = ST[ix[ST] < "2024"]
base = sim(LG, ST, tr, ret_all=True); bt = sim(LG, TE, tr, ret_all=True)
P(f"## 0. reproduce: all {fmt(base)} | 24-26 {fmt(bt)} | starts {len(ST)} / {len(TE)} | max NQ notional/equity median {base['maxn_med']:.0f}x p90 {base['maxn_p90']:.0f}x")
# ---------- 1. sample size / CI ----------
P("\n## 1. independence and confidence intervals")
hitv = (base["W"] >= 700).astype(float); hte = (bt["W"] >= 700).astype(float)
for nm, h in (("all", hitv), ("24-26", hte)):
    offs = [h[o::11].mean() for o in range(11)]  # every 11th start = 22 trading days apart = no overlap
    neff = len(h) / 11
    rng = np.random.default_rng(1); B = 33  # block = 33 starts ~ 3 months
    bs = []
    for _ in range(4000):
        k = rng.integers(0, len(h) - B, int(np.ceil(len(h) / B))); bs.append(np.concatenate([h[a:a + B] for a in k])[:len(h)].mean())
    lo, hi = np.percentile(bs, [2.5, 97.5]); se = np.sqrt(h.mean() * (1 - h.mean()) / neff)
    # autocorrelation of non-overlapping consecutive window outcomes
    ac = np.mean([np.corrcoef(h[o::11][:-1], h[o::11][1:])[0, 1] for o in range(11)])
    P(f"{nm}: p={h.mean():.1%}, independent windows ~{neff:.0f}, non-overlap subsets range {min(offs):.0%}-{max(offs):.0%}, "
      f"binomial 95% CI {h.mean()-1.96*se:.0%}-{h.mean()+1.96*se:.0%}, 3-month block bootstrap 95% CI {lo:.0%}-{hi:.0%}, lag-1 autocorr of next window {ac:+.2f}")
yrs = pd.Series(hitv, index=ix[ST]).groupby(ix[ST].year).mean()
P("hit by start year: " + " ".join(f"{y}:{v:.0%}" for y, v in yrs.items()))
# ---------- 2. 2017-19 out of sample ----------
P("\n## 2. earlier period on the extended index (calibration still 2020-21)")
X = ext_index(); bx = build(X, trend="stack4+crypto", ref=bk); LX = make(bx)
for lo_, hi_ in (("2020-05-12", "2027"), ("2024", "2027"), ("2017-03-01", "2020-01-01"), ("2017-03-01", "2018-01-01"), ("2018", "2019"), ("2019", "2020"),
                 ("2020-01-01", "2020-05-12"), ("2017-03-01", "2022")):
    s = starts_for(X, lo_, hi_, 30); r = sim(LX, s, bx["tr"])
    P(f"starts {lo_}..{hi_}: {fmt(r)} (n {len(s)})")
for c in ("B", "ON", "TREND"):
    x = pd.Series(bx["P"][c], index=X)
    P(f"sleeve {c} Sharpe by year: " + " ".join(f"{y}:{(v.mean()/v.std()*np.sqrt(252) if v.std()>0 else 0):+.1f}" for y, v in x.groupby(X.year)))
R = pd.Series(sum(bx["P"].values()), index=X); shr = lambda v: v.mean() / v.std() * np.sqrt(252)
P(f"book Sharpe 2017-19 {shr(R[:'2019']):.2f} | 2020-21 {shr(R['2020':'2021']):.2f} | 2022-26 {shr(R['2022':]):.2f} | book daily vol 2017-19 {R[:'2019'].std():.4f} vs sig_tr {g.sig_tr:.4f}")
P(f"TREND largest days (stack4, raw): {g.S.TREND.nlargest(3).round(3).to_dict()}")
bk0 = dict(bk); bk0["P"] = dict(bk["P"]); bk0["P"]["TREND"] = bk["P"]["TREND"] * 0; bk0["WP"] = {"TREND": bk["WP"]["TREND"] * 0}
r0 = sim(make(bk0), ST, tr); r0t = sim(make(bk0), TE, tr); P(f"TREND removed (still scaled same): all {fmt(r0)} | 24-26 {fmt(r0t)}")
# ---------- 3. selection ----------
P("\n## 3. selection: grid of nearby settings (cells all / 2020-23 / 2024-26 / 2017-19)")
S17 = starts_for(X, "2017-03-01", "2020-01-01", 30)
LGs = {"ON1/B30": None, "ON30/B30": LG, "ON30/B15": make(bk, 15, 30)}
grid = []
for f in (0.4, 0.5, 0.6):
    for cap in (50, 100, 200):
        for band in (0, 0.25):
            for tp in (False, True):
                a, b, c = sim(LG, ST, tr, f, cap, band, tp), sim(LG, TR0, tr, f, cap, band, tp), sim(LG, TE, tr, f, cap, band, tp)
                d = sim(LX, S17, bx["tr"], f, cap, band, tp)
                grid.append((f, cap, band, tp, a["hit"], b["hit"], c["hit"], d["hit"]))
G_ = pd.DataFrame(grid, columns=["f", "cap", "band", "tp", "all", "20_23", "24_26", "17_19"])
P(G_.round(3).to_string(index=False))
bst = G_.loc[G_["20_23"].idxmax()]
P(f"best-on-2020-23 config: f {bst.f} cap {bst.cap} band {bst.band} tp {bst.tp} -> 24-26 {bst['24_26']:.0%}; grid median 24-26 {G_['24_26'].median():.0%}, 17-19 median {G_['17_19'].median():.0%}")
P(f"time {time.time()-t0:.0f}s")
open("/Users/churchxelachurchxela/Projects/openbot-lab/audit/a3_audit.md", "w").write("\n".join(out))
