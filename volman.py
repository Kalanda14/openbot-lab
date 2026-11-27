"""Vol-managed sleeves (Moreira-Muir): scale each sleeve by (2020-21 vol / trailing L-day vol), clip 0..3, lagged 1 day.
Then month-1 odds via maxx.prob (deadline sizing), same windows as maxx."""
import numpy as np, pandas as pd, maxx as M, goal80 as g, hybrid4 as H
S = g.S[["B", "ON", "TREND"]]; tr = S[:"2021"]; w = 1 / tr.std(); w = w / w.sum()
def vm(L):
    V = S.copy()
    for c in S:
        nz = S[c].where(S[c] != 0); vol = nz.rolling(L, min_periods=5).std().ffill().shift(1)
        V[c] = S[c] * (nz[:"2021"].std() / vol).clip(0, 3).fillna(1)
    return (V @ w).values
for L in (20, 60):
    R = vm(L); R = R * g.R.std() / R[: (S.index < "2022").sum()].std()  # same train vol as base so sig_tr matches
    fwd = R - R.mean() + 1.2 * R.std() / np.sqrt(252)
    for X in (40, 100, 200, 320):
        pb = M.prob(R, H.PA, X, 100, 3, False); pc = M.prob(fwd, H.PA26, X, 100, 3, False)
        pb0 = M.prob(g.R, H.PA, X, 100, 3, False); pc0 = M.prob(M.fwd, H.PA26, X, 100, 3, False)
        print(f"L={L} +EUR{X}: base {pb0:.0%}/{pc0:.0%} -> vol-managed {pb:.0%}/{pc:.0%}", flush=True)
