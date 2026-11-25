"""Month-end flow trades on free Dukascopy daily candles. Rules fixed before results.
P1 pension rebalancing (Harvey-Mazzoleni-Melone 2025): at the close 5 trading days before month-end,
   d = MTD(US500) - MTD(UST bond). d > +2% -> short US500 + long bond (equal) for the last 4 days; d < -2% -> reverse.
P2 month-end FX hedge (Melvin-Prins 2015): on the last trading day, for (EUR: Euro Stoxx, JPY: Nikkei, GBP: FTSE):
   foreign index MTD > S&P MTD -> short that currency vs USD for the day (close-to-close); else long it. Equal weight.
Cost 0.03% per side. Output flows_daily.csv."""
import lzma, struct, requests, time, numpy as np, pandas as pd
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
def year(sym, y):
    u = f"https://datafeed.dukascopy.com/datafeed/{sym}/{y}/BID_candles_day_1.bi5"
    for k in range(4):
        try:
            r = S.get(u, timeout=40)
            if r.status_code == 404 or not r.content: return []
            if r.status_code == 200:
                base = pd.Timestamp(f"{y}-01-01")
                return [(base + pd.Timedelta(seconds=t), c) for t, o, c, l, h, v in struct.iter_unpack(">IIIIIf", lzma.decompress(r.content)) if v > 0]
        except Exception: pass
        time.sleep(3)
    return []
def series(sym):
    rows = [r for y in range(2015, 2027) for r in year(sym, y)]
    s = pd.Series([c for _, c in rows], index=pd.DatetimeIndex([t for t, _ in rows]).normalize(), dtype=float)
    return s[~s.index.duplicated()]
P = {k: series(k) for k in ["USA500IDXUSD", "USTBONDTRUSD", "EUSIDXEUR", "JPNIDXJPY", "GBRIDXGBP", "EURUSD", "USDJPY", "GBPUSD"]}
df = pd.DataFrame(P).dropna(subset=["USA500IDXUSD"]).ffill()
r = df.pct_change()
mon = df.index.to_period("M")
first = df.groupby(mon).transform("first")
mtd = df / df.groupby(mon).shift(0).groupby(mon).transform(lambda x: x.iloc[0]) - 1
rank_back = pd.Series(range(len(df)), index=df.index).groupby(mon).transform(lambda x: len(x) - 1 - (x - x.iloc[0]))
out = pd.DataFrame(index=df.index); out["P1"] = 0.0; out["P2"] = 0.0
for m_, g in df.groupby(mon):
    idx = g.index
    if len(idx) < 8: continue
    sig_day = idx[-5]
    d = mtd.loc[sig_day, "USA500IDXUSD"] - mtd.loc[sig_day, "USTBONDTRUSD"]
    side = -1 if d > 0.02 else 1 if d < -0.02 else 0
    if side:
        for t in idx[-4:]:
            out.loc[t, "P1"] = side * 0.5 * (r.loc[t, "USA500IDXUSD"] - r.loc[t, "USTBONDTRUSD"])
        out.loc[idx[-4], "P1"] -= 0.0006; out.loc[idx[-1], "P1"] -= 0.0006
    last, prev = idx[-1], idx[-2]
    legs = []
    for fx, ind, inv in (("EURUSD", "EUSIDXEUR", False), ("USDJPY", "JPNIDXJPY", True), ("GBPUSD", "GBRIDXGBP", False)):
        if pd.isna(df.loc[prev, ind]) or pd.isna(df.loc[prev, fx]): continue
        beat = mtd.loc[prev, ind] > mtd.loc[prev, "USA500IDXUSD"]
        cur_side = -1 if beat else 1                       # short foreign currency if foreign stocks beat
        fx_ret = r.loc[last, fx] * (-1 if inv else 1)      # return of foreign ccy vs USD
        legs.append(cur_side * fx_ret - 0.0006)
    if legs: out.loc[last, "P2"] = np.mean(legs)
out.to_csv("flows_daily.csv")
sh = lambda y: y.mean() / y.std() * np.sqrt(252) if y.std() > 0 else 0
for c in ("P1", "P2"):
    x = out[c]; h = x.index < "2022-01-01"; act = x[x != 0]
    print(f"{c}: active days {len(act)} | win {np.mean(act>0):.0%} | %/yr {x.mean()*252*100:+.2f} | Sharpe {sh(x):+.2f} | 2015-21 {sh(x[h]):+.2f} | 2022-26 {sh(x[~h]):+.2f}")
