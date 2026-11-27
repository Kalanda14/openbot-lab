"""m300 + INTRADAY WIPE: worst-in-day book move = B worst intraday (bt7 w_v30, jobs 2x) + min(ON,0) + 2*min(TREND,0),
each times its vol-managed scale and book weight. If 1 + lev*worst <= stop -> wiped (stop 0 = Exness-style, 0.5 = 50% margin call)."""
import numpy as np, pandas as pd, glob, goal80 as g, hybrid4 as H
S = g.S[["B", "ON", "TREND"]]; tr = S[:"2021"]; w = 1 / tr.std(); w = w / w.sum()
us = pd.concat([pd.read_csv(f, index_col=0, parse_dates=True) for f in glob.glob("/Users/churchxelachurchxela/Projects/openbot/bt7d/**/bt7_us_*.csv", recursive=True)]).sort_index()
jobs = np.array([(t.weekday() == 4 and t.day <= 7) for t in S.index])
bw = (us.w_v30 / 100).reindex(S.index).fillna(0).values * np.where(jobs, 2, 1)
bw = np.minimum(bw, S.B.values)
sc = {}
for c in S:
    nz = S[c].where(S[c] != 0); vol = nz.rolling(20, min_periods=5).std().ffill().shift(1)
    sc[c] = (nz[:"2021"].std() / vol).clip(0, 3).fillna(1).values
R = sum(w[c] * sc[c] * S[c].values for c in S)
WR = w["B"] * sc["B"] * bw + w["ON"] * sc["ON"] * np.minimum(S.ON.values, 0) + w["TREND"] * sc["TREND"] * 2 * np.minimum(S.TREND.values, 0)
k = g.R.std() / R[: (S.index < "2022").sum()].std(); R, WR = R * k, WR * k
mu_cut = R.mean() - 1.2 * R.std() / np.sqrt(252); fwd = R - mu_cut
def run(R, WR, pas, X, cap, m, f, stop):
    G = 400.0 + X; out = []
    for s in range(H.start0, len(R) - 30, 2):
        W = 400.0
        for i in range(21):
            W *= 1 + m * pas[s + i]
            if W >= G: break
            lev = min(g.norm.pdf(g.norm.ppf(min(max(W / G, 1e-6), 0.999999))) * G / (f * g.sig_tr * np.sqrt(21 - i) * W), cap)
            if 1 + lev * WR[s + i] <= stop: W = W * max(stop, 0); break
            W *= 1 + lev * R[s + i]
            if W <= 1: W = 0.0; break
        out.append(W)
    o = np.array(out); h = len(o) // 2
    return (o >= G).mean(), (o[:h] >= G).mean(), (o[h:] >= G).mean(), (o < 100).mean(), np.median(o)
if __name__ == "__main__":
    for stop in (0.0, 0.5):
        for cap in (50, 100, 200):
            for f in (0.35, 0.5, 0.75):
                a = run(R, WR, H.PA, 300, cap, 3, f, stop); b = run(fwd, WR, H.PA26, 300, cap, 3, f, stop)
                print(f"stop {stop} cap {cap} f {f}: backtest {a[0]:.0%} (halves {a[1]:.0%}/{a[2]:.0%}, <100 {a[3]:.0%}) | cautious {b[0]:.0%} (<100 {b[3]:.0%})", flush=True)
