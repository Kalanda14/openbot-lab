"""Market-specific setups, fixed before results. 1-min bars 9:30-16:00 New York. Costs: COSTPCT round trip.
 G1  short at 9:30 open, flat 16:00 (gold 'falls in US hours' pattern)
 G2  gap fade: z = (open/prev close - 1) / std of last 20 gaps; |z| > 1 -> trade against the gap 9:35 -> 16:00
 C1  setup B (noise-band breakout, 30-min checks)
 C2  Wednesdays only: side = sign(10:44 close - 10:29 close) (EIA report 10:30), enter 10:45, exit 14:30
Output: daily % of price for each setup + worst open P&L in the day. Prints Sharpe per half.
"""
import os, numpy as np, pandas as pd
from bt4 import load, day as bday

CPCT = float(os.environ.get("COSTPCT", "0.02"))


def hold(m, side, a, b, rt):
    """enter at close of minute a, exit at close of minute b. returns pnl, worst (price units)."""
    C, H, L = m.close.values, m.high.values, m.low.values
    e = C[a]
    adv = ((L[a + 1:b + 1] - e) if side == 1 else (e - H[a + 1:b + 1])).min() - rt
    return (C[b] - e) * side - rt, min(adv, 0)


if __name__ == "__main__":
    days = load(); rows, hist, gaps = [], [], []
    for i, (d, m) in enumerate(days):
        o = m.open.iloc[0]; rt = o * CPCT / 100
        mv = (m.close / o - 1).abs().values
        if i == 0: hist.append(mv); continue
        pc = days[i - 1][1].close.iloc[-1]; g = o / pc - 1
        r = dict(d=d, px=o)
        p, w = hold(m, -1, 0, 389, rt); r["p_G1"], r["w_G1"] = p / o * 100, w / o * 100
        r["p_G2"] = r["w_G2"] = 0.0
        if len(gaps) >= 20:
            z = g / (np.std(gaps[-20:]) + 1e-12)
            if abs(z) > 1:
                p, w = hold(m, -int(np.sign(z)), 5, 389, rt); r["p_G2"], r["w_G2"] = p / o * 100, w / o * 100
        r["p_C1"] = r["w_C1"] = 0.0
        if len(hist) >= 14:
            r["p_C1"], r["w_C1"] = bday(m, o, pc, np.mean(np.vstack(hist[-14:]), axis=0), rt, 30, None)
        r["p_C2"] = r["w_C2"] = 0.0
        if d.weekday() == 2:
            s = int(np.sign(m.close.iloc[74] - m.close.iloc[59]))
            if s:
                p, w = hold(m, s, 75, 300, rt); r["p_C2"], r["w_C2"] = p / o * 100, w / o * 100
        rows.append(r); hist.append(mv); gaps.append(g)
    df = pd.DataFrame(rows).set_index("d")
    df.to_csv(os.environ.get("DAILY", "bt5.csv"))
    for s in ("G1", "G2", "C1", "C2"):
        x = df["p_" + s]; h = x.index < pd.Timestamp("2022-01-01")
        sh = lambda y: y.mean() / y.std() * np.sqrt(252) if y.std() > 0 else 0
        print(f"{s}: n_trade_days={(x != 0).sum()} %/yr={x.mean()*252:+.1f} Sharpe all={sh(x):+.2f} "
              f"2017-21={sh(x[h]):+.2f} 2022-26={sh(x[~h]):+.2f} t={x.mean()/x.std()*np.sqrt(len(x)):+.1f}")
