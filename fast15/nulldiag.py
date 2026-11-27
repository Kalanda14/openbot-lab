"""Why is the shifted-label best-of-N |z| so large? Per-feature null z (BTC train, H=15, 'all' + top10)."""
import numpy as np, updown as u
d = u.load("BTCUSDT", "train"); F = u.features(d); y, ok = u.labels(d, 15, 0)
rng = np.random.default_rng(1)
for f in ["mom1", "mom15", "mom60", "ofi60", "burst", "round", "z15"]:
    s = F[f]; thr = np.quantile(np.abs(s[ok & (s != 0)]), 0.9)
    for sub, th in (("all", 0), ("top10", thr)):
        pk = u.greedy(np.flatnonzero(ok & (np.abs(s) > th)), 15, len(y)); dr = np.sign(s[pk]); zs = []
        for _ in range(10):
            o = np.roll(y, rng.integers(86400, len(y) - 86400))[pk] * dr; nn = (o != 0).sum()
            zs.append(((o > 0).sum() / nn - .5) / (.5 / np.sqrt(nn)))
        print(f, sub, len(pk), "mean dr %.3f" % dr.mean(), "null z:", np.round(zs, 1), flush=True)
