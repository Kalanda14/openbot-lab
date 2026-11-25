"""Round 3: PUBLISHED intraday effects, tested exactly as published (no tuning). 3 tests only.
A1 intraday momentum (Gao et al 2018): at 15:30 take sign(prev close -> 10:00), hold to 16:00.
A2 hedging-flow momentum (Baltussen et al 2021): at 15:30 take sign(prev close -> 15:30), hold to 16:00.
B  noise-area breakout (Zarattini, Aziz, Barbon 2024): sigma(m) = 14-day avg |close(m)/open - 1| per minute.
   UB = max(open, prev close)*(1+sigma), LB = min(open, prev close)*(1-sigma). At :00/:30 from 10:00:
   close>UB -> long, close<LB -> short; long exits when close<UB, short when close>LB; flat 15:59.
Costs per MNQ round trip: 0.62 pt commission + 0.25 pt slip each side = 1.12 pt. 1 pt = $2 per MNQ.
Result per day in points per 1 contract. Writes results3.md
"""
import glob, numpy as np, pandas as pd

import os
RT = 0.62 + 0.5
CPCT = float(os.environ.get("COSTPCT", "0"))  # if set: round-trip cost as % of price instead of NQ points


def load():
    out = []
    for f in sorted(glob.glob("data/full/*.csv.gz")):
        b = pd.read_csv(f, index_col=0, parse_dates=True)
        if len(b) > 3000:
            m = b.resample("1min").agg(dict(open="first", high="max", low="min", close="last")).dropna()
            m.index = m.index.hour * 60 + m.index.minute - 570  # minute since 9:30
            out.append((b.index[0].normalize(), m))
    return out


def at(m, k):
    s = m.close[m.index <= k]
    return s.iloc[-1] if len(s) else np.nan


def run(days):
    rows = []
    hist = []  # per-day arrays of |move from open| by minute
    for i, (d, m) in enumerate(days):
        o = m.open.iloc[0]; c_end = m.close.iloc[-1]
        global RT
        if CPCT: RT = o * CPCT / 100
        mv = (m.close / o - 1).abs().reindex(range(390)).ffill()
        if i == 0:
            hist.append(mv.values); continue
        pc = days[i - 1][1].close.iloc[-1]
        c1530, c1000 = at(m, 360), at(m, 30)
        r = dict(d=d)
        for nm, sig in (("A1", np.sign(c1000 - pc)), ("A2", np.sign(c1530 - pc))):
            r[nm] = sig * (c_end - c1530) - (RT if sig else 0)
        # B
        if len(hist) >= 14:
            sg = np.nanmean(np.vstack(hist[-14:]), axis=0)
            ub, lb = max(o, pc) * (1 + sg), min(o, pc) * (1 - sg)
            pos, e, pnl, n, worst = 0, 0.0, 0.0, 0, 0.0
            lo_, hi_ = m.low.reindex(range(390)).ffill().values, m.high.reindex(range(390)).ffill().values
            for k in range(30, 390, 30):
                c = at(m, k)
                if pos:  # worst open P&L inside the last 30 min (intraday drawdown check)
                    adv = (lo_[k - 29:k + 1].min() - e) if pos == 1 else (e - hi_[k - 29:k + 1].max())
                    worst = min(worst, pnl + adv - RT)
                if pos == 1 and c < ub[k]: pnl += c - e - RT; pos = 0
                if pos == -1 and c > lb[k]: pnl += e - c - RT; pos = 0
                if pos == 0 and k < 389:
                    if c > ub[k]: pos, e, n = 1, c, n + 1
                    elif c < lb[k]: pos, e, n = -1, c, n + 1
            if pos:
                adv = (lo_[361:].min() - e) if pos == 1 else (e - hi_[361:].max())
                worst = min(worst, pnl + adv - RT); pnl += (c_end - e) * pos - RT
            r["B"] = pnl; r["Bn"] = n; r["Bpct"] = pnl / o * 100; r["Bworst"] = min(worst, pnl) / o * 100; r["px"] = o
        hist.append(mv.values)
        rows.append(r)
    return pd.DataFrame(rows).set_index("d")


def line(nm, x):
    x = x.dropna(); h = len(x) // 2
    def s(y): return y.mean() / y.std() * np.sqrt(252) if y.std() > 0 else np.nan
    t = x.mean() / x.std() * np.sqrt(len(x))
    act = x[x != 0]
    return (f"| {nm} | {len(x)} | {(act > 0).mean():.0%} | {x.mean():+.2f} | ${x.mean() * 2 * 21:+.0f} | {s(x):+.2f} | {t:+.1f} | "
            f"{s(x.iloc[:h]):+.2f} | {s(x.iloc[h:]):+.2f} | {(x.cumsum() - x.cumsum().cummax()).min() * 2:+.0f} |")


if __name__ == "__main__":
    days = load(); df = run(days)
    L = [f"# Round 3: published intraday effects (no tuning)\n\n{len(df)} days {df.index[0].date()} to {df.index[-1].date()}. "
         "Points per day per 1 MNQ, after costs. $/month = 1 MNQ contract. Pass = t > 2 and Sharpe > 0 in both halves.\n",
         "| rule | days | win (trade days) | pts/day | $/month (1 MNQ) | Sharpe | t | Sharpe yr1 | Sharpe yr2 | max DD $ |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for nm in ("A1", "A2", "B"):
        L.append(line(nm, df[nm]))
    if "Bn" in df: L.append(f"\nB trades per day: {df.Bn.mean():.2f}; days with a trade: {(df.Bn > 0).mean():.0%}")
    yr = df.groupby(df.index.year)[["A1", "A2", "B"]].sum().mul(2).round(0)
    L += ["\n## $ per year (1 MNQ)\n", yr.to_markdown()]
    df.to_csv(os.environ.get("DAILY", "daily_NQ.csv"))
    open("results3.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
