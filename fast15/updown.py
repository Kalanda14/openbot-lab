"""Short-horizon up/down test. Pre-registered (written before any result was seen):
 Instruments: BTCUSDT, ETHUSDT (Binance spot 1s; train 2025-07..09, test 2026-08..10), NQ (CME trades, RTH, mid proxy;
 train Apr-Jul 2026, test Aug-Nov 2026). Horizons H = 15, 30, 60, 300 s.
 Features (score s at end of second i, only past data):
  mom1/5/15/60 : log return over last N s
  ofi5/15/60   : (aggr buy - aggr sell)/(buy+sell) over last N s
  burst        : sign(r10) * max(0, log((n10+1)/(10*n600/600+1)))   (trade-count burst with direction)
  round        : sign(R-px)*(1-2|R-px|/step), R nearest round number (BTC 100$, ETH 10$, NQ 25 pt)
  z15          : r15 / (sd of 1s returns last 600 s * sqrt 15)   (vol-regime-normalised momentum)
  tod          : train up-rate of hour bucket (crypto UTC hour, NQ 30-min bucket) minus 0.5
  som          : train up-rate of second-of-minute minus 0.5
  logit        : logistic regression (numpy IRLS) on all 12 above, fit on train
 Rule: direction (with / against s) chosen on TRAIN. Subsets: 'all' (s != 0) and 'top10' (|s| > train 90th pct).
 Trades: greedy non-overlapping (next trade only after the previous expired). Ties (px equal) = refund, excluded
 from accuracy, tie rate reported. Baseline 'up' = always bet up every H s.
Output: res_*.csv. Usage: python updown.py [delay_s]
"""
import sys, json, numpy as np, pandas as pd
INSTS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["BTCUSDT", "ETHUSDT", "NQ"]
HS = (15, 30, 60, 300); LB = 600; RNG = np.random.default_rng(7)
FEATS = ["mom1", "mom5", "mom15", "mom60", "ofi5", "ofi15", "ofi60", "burst", "round", "z15", "tod", "som", "logit"]


def load(name, split):
    if name == "NQ":
        z = np.load("raw/nq_1s.npz"); t = z["t"]
        m = t < 1785542400 if split == "train" else t >= 1785542400        # 2026-08-01 00:00 UTC
        px = ((z["bpx"] + z["apx"]) / 2)[m]; buy, sell, n = z["buy"][m], z["sell"][m], z["n"][m]; t = t[m]
        day = t // 86400
        seg = pd.factorize(pd.Series(day).astype(str) + "_" + pd.Series(z["inst"][m]).astype(str))[0]
        hb = ((t % 86400) // 1800); step = 25.0
    else:
        months = ["2025-07", "2025-08", "2025-09"] if split == "train" else ["2026-08", "2026-09", "2026-10"]
        zs = [np.load(f"raw/{name}_{mo}.npz") for mo in months]
        t = np.concatenate([z["t"] for z in zs]); px = np.concatenate([z["close"] for z in zs])
        vol = np.concatenate([z["vol"] for z in zs]); buy = np.concatenate([z["buyvol"] for z in zs]); sell = vol - buy
        n = np.concatenate([z["n"] for z in zs]); seg = np.cumsum(np.r_[0, np.diff(t) != 1])
        hb = (t % 86400) // 3600; step = 100.0 if name == "BTCUSDT" else 10.0
    ndays = len(np.unique(t // 86400))
    return dict(t=t, px=px.astype("f8"), buy=buy.astype("f8"), sell=sell.astype("f8"), n=n.astype("f8"),
                seg=seg, hb=hb, sm=t % 60, step=step, ndays=ndays)


def win(x, w):
    c = np.r_[0.0, np.cumsum(x)]; out = np.zeros(len(x)); out[w:] = c[w + 1:] - c[1:-w]   # sum of x[i-w+1..i]
    return out


def features(d):
    lr = np.log(d["px"]); N = len(lr); F = {}
    for k in (1, 5, 15, 60):
        r = np.zeros(N); r[k:] = lr[k:] - lr[:-k]; F[f"mom{k}"] = r
    for k in (5, 15, 60):
        b, s = win(d["buy"], k), win(d["sell"], k); F[f"ofi{k}"] = np.where(b + s > 0, (b - s) / np.maximum(b + s, 1e-12), 0)
    r10 = np.zeros(N); r10[10:] = lr[10:] - lr[:-10]
    F["burst"] = np.sign(r10) * np.maximum(0, np.log((win(d["n"], 10) + 1) / (win(d["n"], 600) / 60 + 1)))
    px, st = d["px"], d["step"]; R = np.round(px / st) * st
    F["round"] = np.sign(R - px) * (1 - 2 * np.abs(R - px) / st)
    r1 = np.r_[0, np.diff(lr)]; sd = np.sqrt(np.maximum(win(r1 ** 2, 600) / 600, 1e-18))
    F["z15"] = F["mom15"] / (sd * np.sqrt(15))
    return F


def labels(d, H, D):
    px, seg = d["px"], d["seg"]; N = len(px); y = np.zeros(N); ok = np.zeros(N, bool)
    i = np.arange(LB, N - H - D)
    good = (seg[i - LB] == seg[i]) & (seg[i + H + D] == seg[i])
    y[i] = px[i + H + D] - px[i + D]; ok[i] = good
    return y, ok


def greedy(cand, gap, N):
    if len(cand) == 0: return np.array([], int)
    nxt = np.searchsorted(cand, np.arange(N + gap + 1)); out = []; j = nxt[0]; L = len(cand)
    while j < L:
        i = cand[j]; out.append(i); j = nxt[i + gap]
    return np.array(out, int)


def irls(X, y, it=8, lam=1e-3):
    X = np.c_[np.ones(len(X)), X]; w = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X @ w)); W = p * (1 - p)
        w += np.linalg.solve((X * W[:, None]).T @ X + lam * np.eye(len(w)), X.T @ (y - p))
    return w


def run(D=0):
    rows, picks = [], {}
    for name in INSTS:
        tr, te = load(name, "train"), load(name, "test")
        Ftr, Fte = features(tr), features(te)
        for H in HS:
            ytr, oktr = labels(tr, H, D); yte, okte = labels(te, H, D)
            # bucket scores fitted on train
            for f, key, nb in (("tod", "hb", 48), ("som", "sm", 60)):
                m = oktr & (ytr != 0); up = np.bincount(tr[key][m], (ytr[m] > 0), nb) / np.maximum(np.bincount(tr[key][m], None, nb), 1)
                sc = np.where(np.bincount(tr[key][m], None, nb) > 0, up - 0.5, 0)
                Ftr[f], Fte[f] = sc[tr[key]], sc[te[key]]
            base = [k for k in FEATS if k != "logit"]
            mu = {k: Ftr[k][oktr].mean() for k in base}; sdv = {k: Ftr[k][oktr].std() + 1e-18 for k in base}
            Xs = lambda F: np.column_stack([(F[k] - mu[k]) / sdv[k] for k in base])
            sub = np.flatnonzero(oktr & (ytr != 0))[::3]
            w = irls(Xs(Ftr)[sub], (ytr[sub] > 0).astype(float))
            lg = lambda F: 1 / (1 + np.exp(-(np.c_[np.ones(len(F["mom1"])), Xs(F)] @ w))) - 0.5
            Ftr["logit"], Fte["logit"] = lg(Ftr), lg(Fte)
            gap = H + D
            # baseline: always up
            for sp, d, y, ok in (("train", tr, ytr, oktr), ("test", te, yte, okte)):
                pk = greedy(np.flatnonzero(ok), gap, len(y)); picks[(name, "up", H, "all", sp)] = (pk, np.ones(len(pk)))
            for f in FEATS:
                s_tr, s_te = Ftr[f], Fte[f]
                thr = np.quantile(np.abs(s_tr[oktr & (s_tr != 0)]), 0.9)
                for subset, th in (("all", 0.0), ("top10", thr)):
                    ctr = np.flatnonzero(oktr & (np.abs(s_tr) > th)); pk = greedy(ctr, gap, len(ytr))
                    out = ytr[pk] * np.sign(s_tr[pk]); dirn = 1.0 if (out > 0).sum() >= (out < 0).sum() else -1.0
                    picks[(name, f, H, subset, "train")] = (pk, dirn * np.sign(s_tr[pk]))
                    cte = np.flatnonzero(okte & (np.abs(s_te) > th)); pk = greedy(cte, gap, len(yte))
                    picks[(name, f, H, subset, "test")] = (pk, dirn * np.sign(s_te[pk]))
            for (nm, f, h, subset, sp), (pk, dr) in list(picks.items()):
                if nm != name or h != H: continue
                d, y = (tr, ytr) if sp == "train" else (te, yte)
                o = y[pk] * dr; win_, loss = (o > 0).sum(), (o < 0).sum(); nn = win_ + loss
                acc = win_ / nn if nn else np.nan
                rel = o / d["px"][pk] * 1e4 if nm != "NQ" else o            # bps for crypto, points for NQ
                rows.append(dict(inst=nm, feat=f, H=H, subset=subset, split=sp, n=int(nn), acc=acc,
                                 se=np.sqrt(acc * (1 - acc) / nn) if nn else np.nan, z=(acc - .5) / (.5 / np.sqrt(nn)) if nn else np.nan,
                                 tie=1 - nn / max(len(pk), 1), perday=len(pk) / d["ndays"], edge=rel.mean() if len(pk) else np.nan,
                                 absmove=np.abs(y[pk]).mean() / (d["px"][pk].mean() / 1e4 if nm != "NQ" else 1) if len(pk) else np.nan))
            print(name, H, "done", flush=True)
        # null: circular-shift labels (>=1 day) using the same picks, best-of-N |z| on train and on test
        nul = {"train": [], "test": []}
        for sp, d in (("train", tr), ("test", te)):
            ys = {H: labels(d, H, D) for H in HS}
            for _ in range(40):
                sh = RNG.integers(86400 if name != "NQ" else 23400, len(d["px"]) - 86400); best = 0
                for (nm, f, h, subset, s2), (pk, dr) in picks.items():
                    if nm != name or s2 != sp or f == "up": continue
                    y = np.roll(ys[h][0], sh); o = y[pk] * dr; nn = (o != 0).sum()
                    if nn < 30: continue
                    z = abs(((o > 0).sum() / nn - .5) / (.5 / np.sqrt(nn))); best = max(best, z)
                nul[sp].append(best)
        json.dump(nul, open(f"null_{name}_D{D}.json", "w"))
        print(name, "null best|z| train p50/p95", np.percentile(nul["train"], [50, 95]), "test", np.percentile(nul["test"], [50, 95]), flush=True)
        del tr, te, Ftr, Fte
    r = pd.DataFrame(rows)
    r[r.split == "train"].to_csv(f"res_train_D{D}_{'-'.join(INSTS)}.csv", index=False); r[r.split == "test"].to_csv(f"res_test_D{D}_{'-'.join(INSTS)}.csv", index=False)


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
