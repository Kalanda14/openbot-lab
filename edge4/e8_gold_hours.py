"""Where in the night does the gold overnight drift sit? Hour-of-day (ET) mean log return:
PAXGUSDT 1h Binance spot (2020-08..), and Yahoo GC=F 60m (last ~730 days, real COMEX futures)."""
import sys, glob, zipfile, json; sys.path.insert(0, "/Users/churchxelachurchxela/Projects/openbot-lab/edge4")
from ev import *
L = []
for f in sorted(glob.glob(f"{LAB}/edge4/bnb/PAXGUSDT-1h-*.zip")):
    with zipfile.ZipFile(f) as z: L.append(pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 4]))
d = pd.concat(L); d.columns = ["t", "c"]; t = d.t.astype("int64"); t = np.where(t > 1e14, t // 1000, t)
d.index = pd.to_datetime(t, unit="ms", utc=True).tz_convert("America/New_York"); d = d[~d.index.duplicated()].sort_index()
r = np.log(d.c).diff(); r = r[r.abs() < 0.05]
j = json.load(open(f"{LAB}/edge4/yf/GC_60m.json"))["chart"]["result"][0]
g = pd.Series(j["indicators"]["quote"][0]["close"], pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert("America/New_York")).dropna()
rg = np.log(g).diff(); rg = rg[(rg.abs() < 0.05) & (rg.index.to_series().diff() <= pd.Timedelta("1h")).values]
wd = lambda x: x[x.index.weekday < 5]
r = wd(r); rg = wd(rg)
out = ["| hour ET (bar start) | PAXG 2020-08..21 bp | PAXG 2022-26 bp | t 22-26 | GC=F 60m (2024-11..) bp | t |", "|---|---|---|---|---|---|"]
for h in range(24):
    a = r[(r.index.hour == h) & (r.index.year <= 2021)]; b = r[(r.index.hour == h) & (r.index.year >= 2022)]; c = rg[rg.index.hour == h]
    tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
    out.append(f"| {h:02d} | {a.mean()*1e4:+.2f} | {b.mean()*1e4:+.2f} | {tt(b):+.1f} | {c.mean()*1e4:+.2f} | {tt(c):+.1f} |")
print("\n".join(out)); open(f"{LAB}/edge4/e8_gold_hours.md", "w").write("\n".join(out))
