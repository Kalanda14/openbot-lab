"""Classic trend following on many markets (free Dukascopy daily candles). Rules fixed: 55-day breakout long/short,
exit on 3*ATR(20) trailing stop from best close, cost 0.03% per side. Output cta_daily.csv: daily return per market (1x)."""
import lzma, struct, requests, time, numpy as np, pandas as pd
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
SYMS = "XAUUSD XAGUSD LIGHTCMDUSD BRENTCMDUSD GASCMDUSD COPPERCMDUSD EURUSD USDJPY GBPUSD AUDUSD USDCAD USDCHF NZDUSD USTBONDTRUSD BUNDTREUR SOYBEANCMDUSX WHEATCMDUSX SUGARCMDUSD COCOACMDUSD COFFEECMDUSX".split()
def year(sym, y):
    u = f"https://datafeed.dukascopy.com/datafeed/{sym}/{y}/BID_candles_day_1.bi5"
    for k in range(4):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 404 or not r.content: return []
            if r.status_code == 200:
                rows = list(struct.iter_unpack(">IIIIIf", lzma.decompress(r.content)))
                base = pd.Timestamp(f"{y}-01-01")
                return [(base + pd.Timedelta(seconds=t), o, c, l, h, v) for t, o, c, l, h, v in rows if v > 0]
        except Exception: pass
        time.sleep(3)
    return []
out = {}
for s in SYMS:
    rows = [r for y in range(2015, 2027) for r in year(s, y)]
    if len(rows) < 500: print(s, "no data", len(rows), flush=True); continue
    d = pd.DataFrame(rows, columns=["t", "o", "c", "l", "h", "v"]).set_index("t").sort_index()
    c, h, l = d.c.astype(float), d.h.astype(float), d.l.astype(float)
    atr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1).rolling(20).mean()
    hi, lo = c.rolling(55).max().shift(1), c.rolling(55).min().shift(1)
    pos, best, P = 0, 0.0, []
    for i in range(len(c)):
        x = c.iloc[i]
        if pos == 0:
            if x > hi.iloc[i]: pos, best = 1, x
            elif x < lo.iloc[i]: pos, best = -1, x
        elif pos == 1:
            best = max(best, x)
            if x < best - 3 * atr.iloc[i]: pos = 0
        else:
            best = min(best, x)
            if x > best + 3 * atr.iloc[i]: pos = 0
        P.append(pos)
    P = pd.Series(P, index=c.index)
    out[s] = P.shift(1) * c.pct_change() - P.diff().abs().fillna(0) * 0.0003
    x = out[s].dropna(); print(f"{s}: {len(x)} days, Sharpe {x.mean()/x.std()*np.sqrt(252):+.2f}", flush=True)
pd.DataFrame(out).to_csv("cta_daily.csv")
