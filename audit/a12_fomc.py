"""a12 part 2: pre-FOMC drift (Lucca-Moench) on NQ 1-minute data. Scheduled statement days 2017-2026 (14:00 ET).
Windows: full = prev day 14:00 -> 13:55; rth = 09:30 -> 13:55 same day; on = prev 15:55 -> 09:30 (on1 = 15:55 -> 03:30, on2 = 03:30 -> 09:30). Each window needs one instrument at both ends.
Compared to all other days, same window. Train 2017-21, test 2022-26. Roll days dropped (instrument change in window)."""
import numpy as np, pandas as pd
LAB = "/Users/churchxelachurchxela/Projects/openbot-lab"
FOMC = """2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16 2026-10-28""".split()
FOMC = pd.DatetimeIndex(FOMC)
d = pd.read_pickle(f"{LAB}/dbdata/nq.pkl"); d.index = d.index.tz_localize(None)
out = []
def P(s): print(s, flush=True); out.append(s)
def at(day, hhmm):
    t = pd.Timestamp(f"{day.date()} {hhmm}"); i = d.index.searchsorted(t, side="right") - 1
    if i < 0 or (t - d.index[i]) > pd.Timedelta("10min"): return None
    return d.close.iloc[i], d.instrument_id.iloc[i]
days = pd.DatetimeIndex(sorted(set(d.index.normalize())))
days = days[days.weekday < 5]
rows = []
for k, day in enumerate(days[1:], 1):
    pv = days[k - 1]
    a, b, m, c, e = at(pv, "14:00"), at(pv, "15:55"), at(day, "03:30"), at(day, "09:30"), at(day, "13:55")
    if None in (a, b, m, c, e): continue
    rr = lambda u, w: (w[0] / u[0] - 1) if u[1] == w[1] else np.nan
    rows.append(dict(day=day, full=rr(a, e), rth=rr(c, e), on=rr(b, c), on1=rr(b, m), on2=rr(m, c), pt=(e[0] - c[0]) if c[1] == e[1] else np.nan, px=c[0]))
R = pd.DataFrame(rows).set_index("day"); R["fomc"] = R.index.isin(FOMC)
P(f"FOMC days found in data: {R.fomc.sum()} of {len(FOMC)}; with clean overnight window: {R[R.fomc].on.notna().sum()}")
P("| window | period | FOMC mean bp (n, t) | other days mean bp | diff bp | FOMC hit% |\n|---|---|---|---|---|---|")
for w in ("full", "rth", "on", "on1", "on2"):
    for nm, lo, hi in (("2017-21 train", "2017", "2022"), ("2022-26 test", "2022", "2027"), ("all", "2017", "2027")):
        s = R[(R.index >= lo) & (R.index < hi)]; x = s[s.fomc][w].dropna() * 1e4; y = s[~s.fomc][w].dropna() * 1e4
        t = x.mean() / (x.std() / np.sqrt(len(x)))
        P(f"| {w} | {nm} | {x.mean():.1f} ({len(x)}, t={t:.2f}) | {y.mean():.1f} | {x.mean()-y.mean():.1f} | {(x>0).mean():.0%} |")
x = R[R.fomc]; P(f"\nrth window in index points: mean {x.pt.dropna().mean():.1f} pt, median {x.pt.dropna().median():.1f}; CFD round trip ~1.5-2 pt => net ~{x.pt.dropna().mean()-1.75:.1f} pt")
P("per-year FOMC rth mean bp: " + ", ".join(f"{y}: {g.rth.mean()*1e4:.0f}" for y, g in x.groupby(x.index.year)))
P("per-year FOMC on (15:55->09:30) mean bp: " + ", ".join(f"{y}: {g.on.mean()*1e4:.0f}" for y, g in x.groupby(x.index.year)))
P("per-year FOMC full mean bp: " + ", ".join(f"{y}: {g.full.mean()*1e4:.0f}" for y, g in x.groupby(x.index.year)))
R.to_csv(f"{LAB}/audit/a12_fomc_days.csv")
open(f"{LAB}/audit/a12_fomc.md", "w").write("\n".join(out))
