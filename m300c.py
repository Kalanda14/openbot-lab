"""+EUR300 from 400 with a FLOOR F (only W-F is risked; deadline sizing on (W-F) toward (G-F)) over D trading days.
Intraday wipe check as m300b (stop 0). No carry. Reports P(hit), P(end<400 = loss), P(end<F), median end."""
import numpy as np, m300b as M, goal80 as g, hybrid4 as H
def run(R, WR, D, F, cap=100, f=0.5, X=300):
    G = 400.0 + X; out = []
    for s in range(H.start0, len(R) - D - 2, 2):
        W = 400.0
        for i in range(D):
            if W >= G: break
            c = W - F
            if c <= 1: break
            z = g.norm.ppf(min(max(c / (G - F), 1e-6), 0.999999))
            lev = min(g.norm.pdf(z) * (G - F) / (f * g.sig_tr * np.sqrt(D - i) * W), cap)
            if 1 + lev * WR[s + i] <= 0: W = 0.0; break
            W *= 1 + lev * R[s + i]
        out.append(max(W, 0))
    o = np.array(out); return (o >= G).mean(), (o < 400).mean(), (o < max(F, 100)).mean(), np.median(o), len(o)
if __name__ == "__main__":
    for D in (21, 42, 63, 84):
        for F in (0, 200, 300):
            for f in (0.5, 1.0):
                a = run(M.R, M.WR, D, F, f=f); b = run(M.fwd, M.WR, D, F, f=f)
                print(f"{D//21} mo floor {F} f {f}: backtest hit {a[0]:.0%} loss {a[1]:.0%} below-floor {a[2]:.0%} | cautious hit {b[0]:.0%} loss {b[1]:.0%} below-floor {b[2]:.0%} (n {a[4]})", flush=True)
