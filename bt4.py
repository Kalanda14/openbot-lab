"""B variants for prop-firm survival. Rules fixed before results.
 v30   : original (entry + exit checks every 30 min)
 v5    : entries every 30 min, exit check every 5 min
 v1    : entries every 30 min, exit check every 1 min
 v30ds : original + daily stop: flat for the day when open+closed P&L <= -0.3% of the open price
 v5ds  : v5 + same daily stop
Worst open P&L is tracked minute by minute (1-min highs/lows). Output: daily % of price per variant.
Env: COSTPCT (round trip % of price; default NQ 1.12 pt), DAILY (output csv).
"""
import glob, os, numpy as np, pandas as pd

CPCT = float(os.environ.get("COSTPCT", "0"))
N = int(os.environ.get("MINUTES", "390"))
OH, OM = (int(x) for x in os.environ.get("OPEN", "09:30").split(":"))
VARS = {"v30": (30, None), "v5": (5, None), "v1": (1, None), "v30ds": (30, 0.003), "v5ds": (5, 0.003)}


def load():
    out = []
    for f in sorted(glob.glob("data/full/*.csv.gz")):
        b = pd.read_csv(f, index_col=0, parse_dates=True)
        if len(b) > N * 12 * 0.6:
            m = b.resample("1min").agg(dict(open="first", high="max", low="min", close="last")).dropna()
            m.index = m.index.hour * 60 + m.index.minute - (OH * 60 + OM)
            m = m.reindex(range(N)).ffill().bfill()
            out.append((b.index[0].normalize(), m))
    return out


def day(m, o, pc, sg, rt, ex_every, ds):
    C, H, L = m.close.values, m.high.values, m.low.values
    ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg)
    pos, e, real, worst, stopped = 0, 0.0, 0.0, 0.0, False
    dlim = -ds * o if ds else None
    for k in range(30, N):
        if pos:
            adv = (L[k] - e) if pos == 1 else (e - H[k])
            run_low = real + adv - rt
            if dlim is not None and run_low <= dlim:
                real = dlim - 0.5; worst = min(worst, real); pos = 0; stopped = True; continue
            worst = min(worst, run_low)
            if k % ex_every == 0 and ((pos == 1 and C[k] < ub[k]) or (pos == -1 and C[k] > lb[k])):
                real += (C[k] - e) * pos - rt; pos = 0
        if not pos and not stopped and k % 30 == 0 and k < N - 1:
            if C[k] > ub[k]: pos, e = 1, C[k]
            elif C[k] < lb[k]: pos, e = -1, C[k]
    if pos: real += (C[N - 1] - e) * pos - rt
    return real / o * 100, min(worst, real) / o * 100


if __name__ == "__main__":
    days = load(); hist, rows = [], []
    for i, (d, m) in enumerate(days):
        o = m.open.iloc[0]
        mv = (m.close / o - 1).abs().values
        if i >= 14:
            pc = days[i - 1][1].close.iloc[-1]
            sg = np.mean(np.vstack(hist[-14:]), axis=0)
            rt = o * CPCT / 100 if CPCT else 1.12
            r = dict(d=d, px=o)
            for v, (ex, ds) in VARS.items():
                r["p_" + v], r["w_" + v] = day(m, o, pc, sg, rt, ex, ds)
            rows.append(r)
        hist.append(mv)
    df = pd.DataFrame(rows).set_index("d")
    df.to_csv(os.environ.get("DAILY", "bt4_NQ.csv"))
    for v in VARS:
        x = df["p_" + v]
        print(f"{v:6s} days={len(x)} %/yr={x.mean()*252:+.1f} Sharpe={x.mean()/x.std()*np.sqrt(252):+.2f} "
              f"median worst-in-day={df['w_'+v].median():+.3f}% p5 worst={df['w_'+v].quantile(.05):+.3f}%")
