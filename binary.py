"""Short-expiry up/down bets on 5-second Nasdaq bars (9:30-16:00 NY). Rules fixed before results.
For each strategy and expiry: count wins / losses / ties (price exactly equal at expiry).
 S1 mom5   : bet sign of last 5s move
 S2 mom30  : bet sign of last 30s move
 S3 spike  : last 5s move > 3x rolling sd (last 60 bars) -> bet the OPPOSITE way
 S4 Bdir   : while setup B holds a position (30-min checks, same rules as bt7), bet B's direction
 S5 drive  : at 9:35 bet the direction of the first 5 minutes (one bet per day)
Expiries in 5s bars: 1 (5s), 6 (30s), 12 (1 min), 60 (5 min). Output bin_YEAR.json
"""
import glob, json, os, sys, numpy as np, pandas as pd

EXP = (1, 6, 12, 60)
N5 = 4680  # 390 min * 12


def day_series(f):
    b = pd.read_csv(f, index_col=0, parse_dates=True)
    if len(b) < 3000: return None
    t0 = b.index[0].normalize() + pd.Timedelta("9h30min")
    k = ((b.index - t0).total_seconds() // 5).astype(int)
    c = pd.Series(b.close.values, index=k); c = c[~c.index.duplicated()].reindex(range(N5)).ffill().bfill().values
    return b.index[0].normalize(), c


def add(cnt, key, bet, out):
    w = int(((bet * out) > 0).sum()); l = int(((bet * out) < 0).sum()); t = int(((bet != 0) & (out == 0)).sum())
    a = cnt.setdefault(key, [0, 0, 0]); a[0] += w; a[1] += l; a[2] += t


if __name__ == "__main__":
    year = sys.argv[1]
    files = sorted(glob.glob("data/full/*.csv.gz"))
    cnt, hist, prev_close = {}, [], None
    for f in files:
        r = day_series(f)
        if r is None: continue
        d, c = r
        m1 = c[11::12]  # 1-min closes (390)
        o = c[0]
        # setup B position per 5s bar (decisions at 30-min marks on 1-min closes)
        posB = np.zeros(N5)
        if len(hist) >= 14 and prev_close is not None:
            sg = np.mean(np.vstack(hist[-14:]), axis=0)
            ub, lb = max(o, prev_close) * (1 + sg), min(o, prev_close) * (1 - sg)
            pos = 0
            for k in range(30, 390):
                if k % 30 == 0:
                    if pos == 1 and m1[k] < ub[k]: pos = 0
                    if pos == -1 and m1[k] > lb[k]: pos = 0
                    if pos == 0 and k < 389:
                        pos = 1 if m1[k] > ub[k] else -1 if m1[k] < lb[k] else 0
                posB[(k + 1) * 12:(k + 2) * 12] = pos
        hist.append(np.abs(m1 / o - 1)); prev_close = c[-1]
        dc = np.diff(c, prepend=c[0])
        sd = pd.Series(dc).rolling(60).std().values
        for E in EXP:
            fut = np.zeros(N5); fut[:-E] = c[E:] - c[:-E]
            valid = np.zeros(N5, bool); valid[60:N5 - E] = True
            s1 = np.sign(dc) * valid
            s2 = np.zeros(N5); s2[6:] = np.sign(c[6:] - c[:-6]); s2 *= valid
            s3 = np.where(np.abs(dc) > 3 * np.nan_to_num(sd, nan=1e9), -np.sign(dc), 0) * valid
            s4 = posB * valid
            add(cnt, f"S1_mom5_{E}", s1, fut); add(cnt, f"S2_mom30_{E}", s2, fut)
            add(cnt, f"S3_spike_{E}", s3, fut); add(cnt, f"S4_Bdir_{E}", s4, fut)
        k5 = 60  # 9:35 = bar 60
        dr = np.sign(c[k5 - 1] - c[0])
        if dr:
            out = c[k5 - 1 + 60] - c[k5 - 1]
            a = cnt.setdefault("S5_drive_60", [0, 0, 0]); a[0 if dr * out > 0 else 1 if dr * out < 0 else 2] += 1
    json.dump(cnt, open(f"bin_{year}.json", "w"))
    print(year, {k: v for k, v in cnt.items() if k.endswith("_12") or k.startswith("S5")})
