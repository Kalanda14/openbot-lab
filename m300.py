"""+EUR300 in 21 trading days from EUR400. Vol-managed book (volman L=20), deadline sizing with sigma factor f, cap, spread m.
Reports P(hit) backtest / cautious, split by window half, and P(end < EUR100)."""
import numpy as np, sys, goal80 as g, hybrid4 as H
from volman import vm
R = vm(20); R = R * g.R.std() / R[: (g.S.index < "2022").sum()].std()
fwd = R - R.mean() + 1.2 * R.std() / np.sqrt(252)
def run(R, pas, X, cap, m, f):
    G = 400.0 + X; out = []
    for s in range(H.start0, len(R) - 30, 2):
        W = 400.0
        for i in range(21):
            W *= 1 + m * pas[s + i]
            if W >= G: break
            lev = min(g.norm.pdf(g.norm.ppf(min(max(W / G, 1e-6), 0.999999))) * G / (f * g.sig_tr * np.sqrt(21 - i) * W), cap)
            W *= 1 + lev * R[s + i]
            if W <= 1: W = 0.0; break
        out.append(W)
    o = np.array(out); h = len(o) // 2
    return (o >= G).mean(), (o[:h] >= G).mean(), (o[h:] >= G).mean(), (o < 100).mean()
if __name__ == "__main__":
    for cap in (100, 200):
        for f in (0.35, 0.5, 0.75, 1.0, 1.5):
            a = run(R, H.PA, 300, cap, 3, f); b = run(fwd, H.PA26, 300, cap, 3, f)
            print(f"cap {cap} f {f}: backtest {a[0]:.0%} (halves {a[1]:.0%}/{a[2]:.0%}, <100 {a[3]:.0%}) | cautious {b[0]:.0%} (<100 {b[3]:.0%})", flush=True)
