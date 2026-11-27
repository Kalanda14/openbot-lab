"""Swap-free overnight: CFD swap is charged at 17:00 NY rollover. Can the overnight bet enter AFTER rollover?
Down day = 15:55 < prev 15:55 (as before). Legs on real CME NQ 1m (roll-safe: same instrument_id at both ends):
 A 15:55->03:30 (current), B 15:55->16:59 (before rollover), C 18:00->03:30 (after rollover, no swap), D 18:30->03:30.
Cost 0.5bp per leg. Train 2017-21 / test 2022-26. Rule fixed before results."""
import pandas as pd, numpy as np
nq = pd.read_pickle("dbdata/nq.pkl"); m = nq.resample("1min").last().ffill(limit=30)
hm = m.index.strftime("%H:%M")
def at(t):
    s = m[hm == t].copy(); s.index = s.index.date; return s
c55, c1659, c1800, c1830, x0330 = at("15:54"), at("16:58"), at("18:00"), at("18:30"), at("03:29")
days = [d for d in c55.index if pd.Timestamp(d).weekday() < 5]
rows = []
for i in range(1, len(days) - 1):
    d, pv, nx = days[i], days[i - 1], days[i + 1]
    try: a, p, e, f1, f2, z = c55.loc[d], c55.loc[pv], c1659.loc[d], c1800.loc[d], c1830.loc[d], x0330.loc[nx]
    except KeyError: continue
    ids = {a.instrument_id, e.instrument_id, f1.instrument_id, f2.instrument_id, z.instrument_id}
    if len(ids) > 1 or a.instrument_id != p.instrument_id: continue
    if a.close >= p.close: continue
    rows.append((pd.Timestamp(d), z.close / a.close - 1, e.close / a.close - 1, z.close / f1.close - 1, z.close / f2.close - 1))
D = pd.DataFrame(rows, columns=["d", "A", "B", "C", "D"]).set_index("d") - 0.5e-4
sh = lambda x: x.mean() / x.std() * np.sqrt(252 * len(x) / max((x.index[-1] - x.index[0]).days / 365.25 * 252, 1))
for c, lab in (("A", "15:55->03:30 now"), ("B", "15:55->16:59"), ("C", "18:00->03:30 no swap"), ("D", "18:30->03:30 no swap")):
    tr, te = D[c][:"2021"], D[c]["2022":]
    print(f"{lab:22s} train win {np.mean(tr>0):.1%} mean {tr.mean()*100:+.3f}% | test win {np.mean(te>0):.1%} mean {te.mean()*100:+.3f}% n {len(te)} | by-year mean bp " + " ".join(f"{y}:{D[c][str(y)].mean()*1e4:+.0f}" for y in range(2017, 2027)))
