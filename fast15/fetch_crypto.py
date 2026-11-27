"""Download Binance spot 1s klines (free, data.binance.vision) -> raw/{SYM}_{YYYY-MM}.npz
Kept per second (gaps filled): t (unix s), close (ffill), vol, buyvol (taker buy base), n (trade count).
Usage: python fetch_crypto.py BTCUSDT 2025-07 2025-08 ...
"""
import io, os, sys, zipfile, urllib.request, numpy as np, pandas as pd
sym, months = sys.argv[1], sys.argv[2:]
os.makedirs("raw", exist_ok=True)
for m in months:
    out = f"raw/{sym}_{m}.npz"
    if os.path.exists(out): continue
    url = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1s/{sym}-1s-{m}.zip"
    zb = urllib.request.urlopen(url, timeout=600).read()
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 4, 5, 8, 9])
    df.columns = ["t", "close", "vol", "n", "buyvol"]
    t = df["t"].to_numpy()
    t = t // (1_000_000 if t[0] > 1e14 else 1000)          # 2025+ files are in microseconds
    full = np.arange(t[0], t[-1] + 1)
    s = pd.DataFrame({"close": df.close.values, "vol": df.vol.values, "buyvol": df.buyvol.values, "n": df.n.values},
                     index=t).groupby(level=0).last().reindex(full)
    s["close"] = s["close"].ffill()
    s = s.fillna(0)
    np.savez(out, t=full, close=s.close.values, vol=s.vol.values.astype("f4"),
             buyvol=s.buyvol.values.astype("f4"), n=s.n.values.astype("f4"))
    print(out, len(full), "missing secs", len(full) - len(t), flush=True)
