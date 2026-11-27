"""Overnight drift (Boyarchenko-Larsen-Whelan 2023) on real CME NQ 1m (Databento). Rules fixed before results.
P(d,t) = close of the 1m bar ending at time t (NY). Overnight from 15:55 day d to t on next trading day.
Variants: ON_full (15:55->09:30), ON_eu (15:55->03:30), and *_down = only when 15:55 today < 15:55 previous day.
Cost 0.5 bp per round trip. Roll jumps (|leg| > 4%) dropped. Train 2017-21 / test 2022-26. Also hourly profile."""
import glob, numpy as np, pandas as pd, databento as db
try:
    px = pd.read_pickle("dbdata/nq_1m_close.pkl")
except FileNotFoundError:
    parts = []
    for f in sorted(glob.glob("dbdata/nq_1m_*.dbn.zst")):
        s = db.DBNStore.from_file(f).to_df()["close"]; parts.append(s)
    px = pd.concat(parts); px.index = px.index.tz_convert("America/New_York")
    px = px[~px.index.duplicated()].sort_index(); px.to_pickle("dbdata/nq_1m_close.pkl")
print("bars", len(px), px.index[0], px.index[-1], flush=True)
m = px.resample("1min").last().ffill(limit=30)
def at(hm):
    s = m[m.index.strftime("%H:%M") == hm]; s.index = s.index.date; return s
c1555, p0330, p0930 = at("15:54"), at("03:29"), at("09:30")  # bar labelled 15:54 closes at 15:55
days = [d for d in c1555.index if pd.Timestamp(d).weekday() < 5]
rows = []
for i in range(1, len(days) - 1):
    d, nx = days[i], days[i + 1]
    if nx not in p0930.index or nx not in p0330.index: continue
    a = c1555[d]; full = p0930[nx] / a - 1; eu = p0330[nx] / a - 1; rest = p0930[nx] / p0330[nx] - 1
    if max(abs(full), abs(eu)) > 0.04: continue
    rows.append((pd.Timestamp(d), full, eu, rest, a < c1555[days[i - 1]]))
D = pd.DataFrame(rows, columns=["d", "full", "eu", "rest", "down"]).set_index("d")
cost = 0.5e-4
sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
for nm, r in (("ON_full", D.full - cost), ("ON_eu", D.eu - cost), ("rest 03:30->09:30", D.rest),
              ("ON_full_down", (D.full - cost).where(D.down, 0)), ("ON_eu_down", (D.eu - cost).where(D.down, 0)),
              ("ON_eu_up", (D.eu - cost).where(~D.down, 0))):
    tr, te = r[:"2021"], r["2022":]
    print(f"{nm:18s} Sharpe train {sh(tr):+.2f} test {sh(te):+.2f} | mean bp train {tr.mean()*1e4:+.2f} test {te.mean()*1e4:+.2f} | by year " +
          " ".join(f"{y}:{sh(r[str(y)]):+.1f}" for y in range(2017, 2027)), flush=True)
for per in (slice(None, "2021"), slice("2022", None)):
    x = D[per]; dn, up = x.eu[x.down], x.eu[~x.down]
    t = (dn.mean() - up.mean()) / np.sqrt(dn.var() / len(dn) + up.var() / len(up))
    print(f"down vs up eu-leg {per.start or '2017'}-{per.stop or '2026'}: down {dn.mean()*1e4:+.2f}bp up {up.mean()*1e4:+.2f}bp t={t:+.2f}")
h = m.pct_change(60); h = h[h.index.minute == 0]; h = h[h.abs() < 0.03]
prof = pd.DataFrame({"train": h[:"2021"].groupby(h[:"2021"].index.hour).mean() * 1e4, "test": h["2022":].groupby(h["2022":].index.hour).mean() * 1e4}).round(2)
print("hourly mean bp (hour ending):\n", prof.T.to_string())
D.to_csv("dbdata/eudrift.csv")
