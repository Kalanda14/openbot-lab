"""Setup B on BTC/ETH during US stock hours (9:30-16:00 New York), Binance spot 1-min archive (data.binance.vision).
Same rules as the Nasdaq B (bt7.day, mode v30). Cost 0.12% round trip (futures taker + slippage). -> cb_SYM.csv"""
import io, sys, zipfile, requests, numpy as np, pandas as pd
from zoneinfo import ZoneInfo
import bt7
sym = sys.argv[1]; S = requests.Session()
parts = []
for y in range(2018, 2027):
    for mo in range(1, 13):
        u = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{y}-{mo:02d}.zip"
        r = S.get(u, timeout=60)
        if r.status_code != 200: continue
        z = zipfile.ZipFile(io.BytesIO(r.content)); d = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 1, 2, 3, 4, 5])
        parts.append(d)
k = pd.concat(parts); k.columns = ["t", "open", "high", "low", "close", "vol"]
k["t"] = pd.to_datetime(k.t.astype("int64") // (1000 if k.t.max() > 1e14 else 1), unit="ms", utc=True).dt.tz_convert(ZoneInfo("America/New_York"))
k = k.set_index("t").sort_index()
days = []
for d, g in k.groupby(k.index.date):
    if pd.Timestamp(d).weekday() >= 5: continue
    s = g.between_time("09:30", "15:59")
    if len(s) < 300: continue
    m = s.copy(); m.index = (m.index.hour * 60 + m.index.minute - 570)
    m = m.reindex(range(390)).ffill().bfill()
    days.append((pd.Timestamp(d), m))
rows, hist, rets = [], [], []
for i, (d, m) in enumerate(days):
    o = m.open.iloc[0]; mv = (m.close / o - 1).abs().values
    if i >= 15:
        pc = days[i - 1][1].close.iloc[-1]; sg = np.mean(np.vstack(hist[-14:]), axis=0)
        p, w, _ = bt7.day(m, o, pc, sg, o * 0.12 / 100, "v30", np.std(rets[-14:]))
        rows.append(dict(d=d, p=p, w=w))
    if i: rets.append(m.close.iloc[-1] / days[i - 1][1].close.iloc[-1] - 1)
    hist.append(mv)
df = pd.DataFrame(rows).set_index("d"); df.to_csv(f"cb_{sym}.csv")
x = df.p; h = x.index < "2022-01-01"; sh = lambda y: y.mean() / y.std() * np.sqrt(252)
print(f"{sym}: {len(x)} days, %/yr {x.mean()*252:+.1f}, Sharpe {sh(x):+.2f} | to 2021 {sh(x[h]):+.2f} | 2022-26 {sh(x[~h]):+.2f}")
