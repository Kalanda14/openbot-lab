"""Choppy-day setups on Nasdaq 1-min bars (from 5s data/full), 9:30-16:00 NY. Rules fixed before results.
Cost 1.12 pt per round trip (MNQ-style). Daily output in % of open price + worst open %.
 R1 range fade : 10:00-15:00, price touches open +/- 0.7*sigma(t) (sigma = B's 14-day noise profile) -> fade toward the
                 open; target = open, stop = open +/- 1.2*sigma(t); exit 15:55. Max one trade per side per day.
 R2 gap fill   : 0.1% < |open/prev close - 1| < 0.6% -> at 9:30 trade toward prev close; target prev close,
                 stop = open + gap size (away from close); exit 11:00.
 R3 lunch rev  : move 11:00->12:00 beyond 0.5*sigma(12:00) -> fade at 12:00, exit 13:30, stop 0.5*sigma beyond.
Also writes B (v30) for correlation. -> bt8_YEAR.csv
"""
import glob, sys, numpy as np, pandas as pd
RT = 1.12


def load():
    out = []
    for f in sorted(glob.glob("data/full/*.csv.gz")):
        b = pd.read_csv(f, index_col=0, parse_dates=True)
        if len(b) < 3000: continue
        m = b.resample("1min").agg(dict(open="first", high="max", low="min", close="last")).dropna()
        m.index = m.index.hour * 60 + m.index.minute - 570
        m = m.reindex(range(390)).ffill().bfill()
        out.append((b.index[0].normalize(), m))
    return out


def trade(H, L, C, k0, side, e, tgt, stop, kend):
    """enter at e on bar k0; returns pnl (pts, before cost) and worst open pnl."""
    worst = 0.0
    for k in range(k0 + 1, kend + 1):
        adv = (L[k] - e) if side == 1 else (e - H[k]); worst = min(worst, adv)
        if (side == 1 and L[k] <= stop) or (side == -1 and H[k] >= stop): return (stop - e) * side, min(worst, (stop - e) * side)
        if (side == 1 and H[k] >= tgt) or (side == -1 and L[k] <= tgt): return (tgt - e) * side, worst
    return (C[kend] - e) * side, worst


if __name__ == "__main__":
    days = load(); hist, rows = [], []
    for i, (d, m) in enumerate(days):
        O, H, L, C = m.open.values, m.high.values, m.low.values, m.close.values; o = O[0]
        mv = np.abs(C / o - 1)
        if i >= 14:
            pc = days[i - 1][1].close.iloc[-1]; sg = np.mean(np.vstack(hist[-14:]), axis=0)
            r = dict(d=d, px=o)
            # R1
            p1 = w1 = 0.0
            for side in (-1, 1):  # -1 = fade an up move (short), +1 = fade a down move (long)
                for k in range(30, 330):
                    lvl = o * (1 - side * 0.7 * sg[k])
                    if (side == -1 and H[k] >= lvl) or (side == 1 and L[k] <= lvl):
                        stop = o * (1 - side * 1.2 * sg[k])
                        p, w = trade(H, L, C, k, side, lvl, o, stop, 385); p1 += p - RT; w1 += w - RT; break
            r["R1"], r["wR1"] = p1 / o * 100, w1 / o * 100
            # R4 = early momentum (reverse of R1, realistic fill): price reaches open +/- 0.7*sigma -> go WITH it,
            # fill at the worse of level / bar open, target open +/- 1.2*sigma, stop at the open. One per side.
            p4 = w4 = 0.0; n4 = 0
            for side in (1, -1):
                for k in range(30, 330):
                    lvl = o * (1 + side * 0.7 * sg[k])
                    if (side == 1 and H[k] >= lvl) or (side == -1 and L[k] <= lvl):
                        e = max(O[k], lvl) if side == 1 else min(O[k], lvl)
                        tgt = o * (1 + side * 1.2 * sg[k])
                        if (side == 1 and e >= tgt) or (side == -1 and e <= tgt): break
                        p, w = trade(H, L, C, k, side, e, tgt, o, 385); p4 += p - RT; w4 += w - RT; n4 += 1; break
            r["R4"], r["wR4"], r["nR4"] = p4 / o * 100, w4 / o * 100, n4
            # R2
            g = o / pc - 1; p2 = w2 = 0.0
            if 0.001 < abs(g) < 0.006:
                side = -int(np.sign(g)); p, w = trade(H, L, C, 0, side, o, pc, o - side * abs(o - pc), 90); p2, w2 = p - RT, w - RT
            r["R2"], r["wR2"] = p2 / o * 100, w2 / o * 100
            # R3
            p3 = w3 = 0.0; mvl = C[150] - C[90]
            if abs(mvl) > 0.5 * sg[150] * o:
                side = -int(np.sign(mvl)); e = C[150]
                p, w = trade(H, L, C, 150, side, e, -1e9 if side == -1 else 1e9, e - side * 0.5 * sg[150] * o, 240); p3, w3 = p - RT, w - RT
            r["R3"], r["wR3"] = p3 / o * 100, w3 / o * 100
            # B (v30) for correlation
            ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg); pos = 0; e = 0.0; real = 0.0
            for k in range(30, 390):
                if pos and k % 30 == 0 and ((pos == 1 and C[k] < ub[k]) or (pos == -1 and C[k] > lb[k])): real += (C[k] - e) * pos - RT; pos = 0
                if not pos and k % 30 == 0 and k < 389:
                    if C[k] > ub[k]: pos, e = 1, C[k]
                    elif C[k] < lb[k]: pos, e = -1, C[k]
            if pos: real += (C[389] - e) * pos - RT
            r["B"] = real / o * 100
            rows.append(r)
        hist.append(mv)
    pd.DataFrame(rows).to_csv(f"bt8_{sys.argv[1]}.csv", index=False)
    print(sys.argv[1], len(rows), "days")
