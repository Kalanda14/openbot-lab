"""Stability check: simplest rule (bet sign of last-1s return when |r1| > train 90th pct), delay 2 s, per test month."""
import numpy as np, updown as u
for name in ("BTCUSDT", "ETHUSDT"):
    tr = u.load(name, "train"); r = np.abs(np.diff(np.log(tr["px"]))); thr = np.quantile(r[r > 0], 0.9)
    for mo in ("2026-08", "2026-09", "2026-10"):
        z = np.load(f"raw/{name}_{mo}.npz"); px = z["close"]; lr = np.log(px); r1 = np.r_[0, np.diff(lr)]
        for H in (15, 30, 60):
            D = 2; N = len(px); cand = np.flatnonzero((np.abs(r1) > thr) & (np.arange(N) >= 600) & (np.arange(N) < N - H - D))
            pk = u.greedy(cand, H + D, N); o = (px[pk + H + D] - px[pk + D]) * np.sign(r1[pk]); w, l = (o > 0).sum(), (o < 0).sum()
            print(name, mo, H, "acc %.4f n %d ties %.3f edge %.2f bps" % (w / (w + l), w + l, 1 - (w + l) / len(pk), (o / px[pk]).mean() * 1e4))
