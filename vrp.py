"""Volatility risk premium sleeve (rule fixed before results). CBOE VX futures settlements 2016-2026.
Front = nearest contract with >= 5 trading days to expiry. At close t-1: short if front/VIX >= 1.05 and VIX/VIX3M < 1.
Return day t = -(settle_t/settle_{t-1} - 1) of that same contract. Cost 0.05 pt (1 tick) per entry/exit/roll.
Train 2016-21 (has Feb-2018 and Mar-2020 crashes), test 2022-26. Then add to the stack book.
"""
import glob, numpy as np, pandas as pd
C = {}
for f in glob.glob("ext/vx/VX_*.csv"):
    d = pd.read_csv(f, parse_dates=["Trade Date"]).set_index("Trade Date").Settle
    C[pd.Timestamp(f.split("_")[1][:10])] = d[d > 0]
exp = sorted(C)
vix = pd.read_csv("ext/VIX.csv", parse_dates=["DATE"]).set_index("DATE").CLOSE
v3 = pd.read_csv("ext/VIX3M.csv", parse_dates=["DATE"]).set_index("DATE").CLOSE
days = vix.index[(vix.index >= "2016-02-01")]
r, pos_prev, held = [], 0, None
for i in range(1, len(days)):
    t0, t1 = days[i - 1], days[i]
    cand = [e for e in exp if (days[(days > t0) & (days <= e)].size >= 5)]
    if not cand: r.append(0.0); continue
    e = cand[0]; s = C[e]
    if t0 not in s.index or t1 not in s.index: r.append(0.0); continue
    sig = (s[t0] / vix[t0] >= 1.05) and (vix[t0] / v3.get(t0, np.nan) < 1)
    pos = 1 if sig else 0
    cost = (0.05 / s[t0]) * (abs(pos - pos_prev) + (pos and pos_prev and held != e))
    r.append(pos * -(s[t1] / s[t0] - 1) - cost); pos_prev, held = pos, e
R = pd.Series(r, index=days[1:])
sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
L = [f"VRP sleeve: in market {np.mean(R != 0):.0%} of days",
     f"TRAIN 2016-21 Sharpe {sh(R[:'2021']):+.2f} | TEST 2022-26 Sharpe {sh(R['2022':]):+.2f}, {R['2022':].mean()*252*100:+.0f}%/yr at 1x, vol {R['2022':].std()*np.sqrt(252)*100:.0f}%",
     "by year Sharpe: " + ", ".join(f"{y} {sh(g):+.1f}" for y, g in R.groupby(R.index.year)),
     f"worst day {R.min()*100:+.1f}% ({R.idxmin().date()}), worst 5 days sum {R.nsmallest(5).sum()*100:+.0f}%"]
R.to_frame("VRP").to_csv("dbdata/vrp.csv")
S = pd.read_csv("/Users/churchxelachurchxela/Projects/openbot/stack2_daily.csv", index_col=0, parse_dates=True)
S["VRP"] = R.reindex(S.index).fillna(0)
tr = S[:"2021"]
L.append("TEST corr of VRP with B/ON/TREND/CARRY: " + ", ".join(f"{c} {S['2022':][['VRP', c]].corr().iloc[0,1]:+.2f}" for c in ("B", "ON", "TREND", "CARRY")))
for nm, cols in (("base (B,ON,TREND)", ["B", "ON", "TREND"]), ("+VRP", ["B", "ON", "TREND", "VRP"])):
    iv = 1 / tr[cols].std(); w = iv / iv.sum(); Rk = S[cols] @ w; k = 0.15 / (Rk[:"2021"].std() * np.sqrt(252))
    bk = (k * Rk + 3 * S.CARRY)["2022":]
    L.append(f"{nm} + carry 3x: TEST Sharpe {sh(bk):+.2f}, {bk.mean()*252*100:+.1f}%/yr, by year " + str({y: round(sh(x), 1) for y, x in bk.groupby(bk.index.year)}))
open("vrp.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
