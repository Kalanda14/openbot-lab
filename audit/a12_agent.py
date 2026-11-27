"""a12 summary: merge part 1/3/4 results, pick on SA only, confirm on ST/S17, plus a theory bound
(complete-market, lognormal: best P(hit) subject to P(end<100)<=5%, Sharpe implied by the unconstrained result)."""
import json, numpy as np
from statistics import NormalDist
N = NormalDist(); LAB = "/Users/churchxelachurchxela/Projects/openbot-lab/audit"
R = {}
for f in ("a12_sizing", "a12_fomc_sim", "a12_more"):
    for k, v in json.load(open(f"{LAB}/{f}.json")).items(): R.setdefault(k, v)
R31 = {k: v for k, v in R.items() if not k.startswith("ref 21d")}
base = [k for k in R31 if k.startswith("base")]; nvar = len(R31) - len(base)
c = lambda v: f"{v[0]:.0%} / {v[1]:.0%}"
row = lambda k: f"| {k} | " + " | ".join(c(R[k][p]) for p in ("SA", "ST", "S17")) + " |"
pick1 = max((k for k in R31 if R31[k]["SA"][1] <= 0.05), key=lambda k: (round(R31[k]["SA"][0], 4), -R31[k]["SA"][1]))
pick2 = min((k for k in R31 if R31[k]["SA"][0] >= 0.75), key=lambda k: (R31[k]["SA"][1], -R31[k]["SA"][0]))
all5 = [k for k in R31 if max(R31[k][p][1] for p in R31[k]) <= 0.05]
pick3 = max(all5, key=lambda k: min(R31[k][p][0] for p in R31[k]))
# theory: terminal G on top-p states, 0 on bottom eps, 100 in between; budget 700 Q(A) + 100 Q(B) = 400
def best_p(s, eps=0.05, W0=400, G=700, Fl=100):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        p = (lo + hi) / 2; zp = N.inv_cdf(1 - p); QA = 1 - N.cdf(zp + s); QC = N.cdf(N.inv_cdf(eps) + s) if eps > 0 else 0
        cost = G * QA + Fl * (1 - QA - QC)
        lo, hi = (p, hi) if cost <= W0 else (lo, p)
    return p
s_imp = N.inv_cdf(3 / 7) - N.inv_cdf(1 - 0.77)  # unconstrained Browne P = 77% (SA cap100)
s_need = next(s for s in np.arange(0.3, 1.5, 0.005) if best_p(s) >= 0.80)
L = ["# a12 (research agent): bending the hit / big-loss frontier, EUR400 -> 700 in 31 trading days",
     "", "Setup = a11_80 exactly (a8b -> a8_starttime -> a6_exec; CFD swap-free costs spike 10pt, cost_b 0.75, cost_on 1.5, "
     "on_extra 1.5; start rule vol20 high | ret60 top third; f 0.5, band 0.5). New sim copy: audit/lib2.py `sim2` "
     "(hooks: wealth/regime cap function, Browne target function, floor F; lib.py untouched; reproduces a11 cap100/50/30 exactly).",
     "Cells = P(hit 700) / P(end < 100). SA = starts 2020-05..2026 (n=480, overlapping), ST = 2024-26 (n=168, subset of SA), S17 = 2017-19 (n=105).",
     f"Variants tried (31 days, excluding 3 baselines): **{nvar}**, plus 2 21-day reference rows and 1 FOMC event study. Selection always on SA only.",
     "", "## Key rows", "| variant | SA hit/<100 | ST | S17 |", "|---|---|---|---|"]
for k in base + ["A step hi100 W<200->cap30", "A step hi100 W<250->cap30", "A step hi100 W<300->cap30", "A step hi200 W<200->cap10",
                 "B stop-out W<150", "C smooth hi100*((W-100)/300)^1", "G 3-level 150 (W>=350) / 50 (>=250) / 20",
                 "J late-game only: cap10 if W<250 and day>=21", "D vol cap hi100 (vol<24%) lo50", "E target 500 while W<250",
                 "F floor-cushion F100 cap100", "FOMC kF1 cap100", "FOMC kF1 cap30", "FOMC kF1 + A step hi100 W<250->cap30",
                 "ref 21d base cap100", "ref 21d step hi100 W<250->cap30"]:
    L.append(row(k))
L += ["", "## Picks (made on SA, then read off ST / S17)",
      f"- best SA hit with SA <100 <= 5%: **{pick1}** -> " + row(pick1)[2:],
      f"- lowest SA <100 with SA hit >= 75%: **{pick2}** -> " + row(pick2)[2:],
      "  (J late-game cap shows 75% / 14% but its SA hit is just under 75% unrounded, so it is not eligible; either way the tail stays >= 14%.)",
      f"- best worst-period hit with <100 <= 5% in ALL three periods (uses all periods, so in-sample): **{pick3}** -> " + row(pick3)[2:],
      "", "## Theory bound (why 80% / 5% is not reachable by sizing alone)",
      f"Complete-market lognormal model: unconstrained deadline (Browne) P(hit)=77% implies theta*sqrt(T) = {s_imp:.3f}. "
      f"The best possible P(hit) with P(end<100) <= 5% (payoff 700 / 100 / 0) at that edge is **{best_p(s_imp):.1%}**. "
      f"80% at 5% needs theta*sqrt(T) >= {s_need:.3f}, i.e. Sharpe x{s_need/s_imp:.2f} or time x{(s_need/s_imp)**2:.2f} "
      f"(~{31*(s_need/s_imp)**2:.0f} trading days). Empirical best at <=5% (69%) is already close to the {best_p(s_imp):.0%} bound, "
      "and the bound ignores gaps, costs and lot size.",
      "", "## What failed", "- D regime cap by vol20: no help (tail comes from grinding losses, not only high-vol days).",
      "- E smaller Browne target when behind: no help (cap binds anyway).",
      "- F Browne on cushion over a 50/100 floor: worse tail (cap still binds, gaps).",
      "- B2 permanent stop / I path-drawdown trigger: safe but costs too much hit.",
      "- H f 0.35/0.7 with step cap: no better than f 0.5.",
      "- FOMC sleeve: the pre-FOMC overnight drift is REAL in the data (15:55->03:30 before statements: train 2017-21 +29 bp t=3.6, "
      "test 2022-26 +19.5 bp t=2.25 vs +5.5/+1.8 bp other nights; RTH 09:30->13:55 part is zero), but adding it to the ON legs "
      "at kF 0.5-3 x ON notional HURTS SA and ST at every cap (helps only S17). Rejected. Only ~1.3 events per 31-day window and added "
      "variance at capped leverage outweigh +20 bp.",
      "", "## What worked (a bit)", "- Wealth-aware step cap (cap 100 while W >= 200-300, cap 20-30 below) beats a flat cap at the same tail: "
      "flat cap30 = 54/1, 49/4, 61/0 vs 3-level 150/50/20 = 68/2, 64/4, 72/1. That bends the frontier ~+14 hit points at the safe end, "
      "but tops out near 69% at <=5% tail, under the 80% goal.",
      "", "Files: lib2.py, a12_base.py, a12_sizing.py/.md/.json, a12_fomc.py/.md, a12_fomc_days.csv, a12_fomc_sim.py/.md/.json, a12_more.py/.md/.json, a12_agent.py."]
open(f"{LAB}/a12_agent.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
