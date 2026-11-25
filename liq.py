"""Crypto liquidation-flush reversal (rules fixed before results; from the reviewer's spec).
BTCUSDT / ETHUSDT perps, 5-minute bars (data.binance.vision futures/um klines + daily 'metrics' 5m open interest).
 OI   long : 60-min OI change <= -4% (ETH -6%) AND 60-min price change <= -3%  -> long next bar open
 OI   short: 60-min OI change <= -4% (ETH -6%) AND 60-min price change >= +3%  -> short (squeeze mirror)
 PX   long : 60-min return < -3 sigma (sigma of 60-min returns, trailing 30 days) -> long   (price only, from 2019)
 PX   short: 60-min return > +3 sigma -> short
Exit: 24h, or stop at 1.5x the trigger move. One position per coin per rule, 12h cooldown. Cost 0.14% round trip.
Output: liq_SYM.csv (one row per trade).
"""
import io, sys, zipfile, requests, numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor
sym = sys.argv[1]; S = requests.Session(); B = "https://data.binance.vision/data/futures/um"
def z(url):
    r = S.get(url, timeout=60)
    if r.status_code != 200: return None
    zf = zipfile.ZipFile(io.BytesIO(r.content)); return pd.read_csv(zf.open(zf.namelist()[0]), header=None)
months = [(y, m) for y in range(2019, 2027) for m in range(1, 13) if (y, m) >= (2019, 9) and (y, m) <= (2026, 10)]
with ThreadPoolExecutor(8) as ex:
    ks = list(ex.map(lambda ym: z(f"{B}/monthly/klines/{sym}/5m/{sym}-5m-{ym[0]}-{ym[1]:02d}.zip"), months))
k = pd.concat([x for x in ks if x is not None])
k = k[pd.to_numeric(k[0], errors="coerce").notna()].iloc[:, :6].astype(float); k.columns = ["t", "o", "h", "l", "c", "v"]
t = k.t.astype("int64"); k["t"] = pd.to_datetime(t.where(t < 10**14, t // 1000), unit="ms")
k = k.drop_duplicates("t").set_index("t").sort_index()
days = pd.date_range("2021-12-01", "2026-11-20", freq="D")
with ThreadPoolExecutor(8) as ex:
    ms = list(ex.map(lambda d: z(f"{B}/daily/metrics/{sym}/{sym}-metrics-{d:%Y-%m-%d}.zip"), days))
m = pd.concat([x for x in ms if x is not None])
m = m[m[0] != "create_time"]; m = pd.DataFrame({"t": pd.to_datetime(m[0]), "oi": m[2].astype(float)}).drop_duplicates("t").set_index("t").sort_index()
k = k.join(m.oi.resample("5min").last(), how="left")
c, o, h, l = k.c.values, k.o.values, k.h.values, k.l.values; oi = k.oi.values
r60 = pd.Series(c).pct_change(12).values
sig = pd.Series(r60).rolling(288 * 30).std().values
oich = pd.Series(oi).pct_change(12, fill_method=None).values
thr = -0.06 if sym.startswith("ETH") else -0.04
rules = {
    "OI_long": (oich <= thr) & (r60 <= -0.03), "OI_short": (oich <= thr) & (r60 >= 0.03),
    "PX_long": r60 < -3 * sig, "PX_short": r60 > 3 * sig,
}
rows = []
for nm, sigarr in rules.items():
    side = 1 if nm.endswith("long") else -1; nxt = 0
    for i in np.where(sigarr)[0]:
        if i < nxt or i + 1 >= len(c): continue
        e = o[i + 1]; stopd = 1.5 * abs(r60[i]) * e; stop = e - side * stopd
        end = min(i + 1 + 288, len(c) - 1); ex_p = c[end]; ex_i = end
        for j in range(i + 1, end + 1):
            if (side == 1 and l[j] <= stop) or (side == -1 and h[j] >= stop): ex_p, ex_i = stop, j; break
        ret = (ex_p / e - 1) * side - 0.0014
        rows.append(dict(rule=nm, t=k.index[i + 1], exit=k.index[ex_i], ret=ret))
        nxt = i + 144  # 12h cooldown
df = pd.DataFrame(rows); df.to_csv(f"liq_{sym}.csv", index=False)
for nm, g in df.groupby("rule"):
    h1 = g.t < "2025-01-01"
    print(f"{sym} {nm}: trades {len(g)} | win {np.mean(g.ret>0):.0%} | avg {g.ret.mean()*100:+.2f}% | to 2024 avg {g.ret[h1].mean()*100:+.2f}% (n {h1.sum()}) | 2025-26 avg {g.ret[~h1].mean()*100:+.2f}% (n {(~h1).sum()})", flush=True)
