"""Minute-by-minute P&L path of setup B (noise-area breakout, original v30 rules, same as bt4.py v30).
For each day: px (open), mtm[k] = closed + open P&L at the close of minute k, low[k] = worst P&L inside minute k
(both in points of NQ, after costs 1.12 pt round trip; an open trade already pays its exit cost).
Overlays (daily take-profit / daily stop) are applied later in propsim.py on these paths.
Usage: python paths.py YEAR   -> paths_YEAR.npz
"""
import sys, numpy as np
from bt4 import load, N

RT = 1.12


def path(m, o, pc, sg):
    C, H, L = m.close.values, m.high.values, m.low.values
    ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg)
    pos, e, real = 0, 0.0, 0.0
    mtm, low = np.zeros(N), np.zeros(N)
    for k in range(N):
        if pos and k % 30 == 0 and ((pos == 1 and C[k] < ub[k]) or (pos == -1 and C[k] > lb[k])):
            real += (C[k] - e) * pos - RT; pos = 0
        if not pos and k >= 30 and k % 30 == 0 and k < N - 1:
            if C[k] > ub[k]: pos, e = 1, C[k]
            elif C[k] < lb[k]: pos, e = -1, C[k]
        if pos:
            mtm[k] = real + (C[k] - e) * pos - RT
            low[k] = real + ((L[k] - e) if pos == 1 else (e - H[k])) - RT
        else:
            mtm[k] = low[k] = real
    return mtm, np.minimum(low, mtm)


if __name__ == "__main__":
    days = load(); hist, D, P, M, W = [], [], [], [], []
    for i, (d, m) in enumerate(days):
        o = m.open.iloc[0]
        if i >= 14:
            mtm, low = path(m, o, days[i - 1][1].close.iloc[-1], np.mean(np.vstack(hist[-14:]), axis=0))
            D.append(str(d.date())); P.append(o); M.append(mtm.astype(np.float32)); W.append(low.astype(np.float32))
        hist.append((m.close / o - 1).abs().values)
    np.savez_compressed(f"paths_{sys.argv[1]}.npz", d=np.array(D), px=np.array(P), mtm=np.array(M), low=np.array(W))
    f = np.array([x[-1] for x in M]) / np.array(P) * 100
    print(f"{sys.argv[1]} days={len(D)} %/yr={f.mean()*252:+.1f} Sharpe={f.mean()/f.std()*np.sqrt(252):+.2f}")
