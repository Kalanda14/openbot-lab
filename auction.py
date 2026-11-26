"""T4 (critic, pre-registered): Treasury auction cycle on ZN (10y note futures, CME, real Databento daily).
Auctions: 5y/7y/10y notes, 20y/30y bonds from fiscaldata.treasury.gov (all, incl. reopenings).
Position held over each day's close-to-close: short from close A-5 business days to close A-1 (dealers cheapen
before supply), long from close A to close A+2 (recovery). Overlaps netted to the sign of the sum, size 1 contract.
Costs: 1 tick (1/64 pt) slip each side + $5 per round trip, charged per position change. $1000 per point.
Roll days (instrument changes) count 0 return. Train 2010-2017, test 2018-2026. Success: test Sharpe >= 0.4, t >= 1.5,
corr with B < 0.2.
"""
import numpy as np, pandas as pd, requests, databento as db

rows, page = [], 1
while True:
    j = requests.get("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query",
                     params={"fields": "auction_date,security_type,security_term", "filter": "auction_date:gte:2010-01-01",
                             "page[size]": 1000, "page[number]": page}, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).json()
    rows += j["data"]
    if page >= j["meta"]["total-pages"]: break
    page += 1
a = pd.DataFrame(rows)
a = a[a.security_type.isin(["Note", "Bond"]) & a.security_term.str.contains(r"^(5|7|10|20|30)-Year", regex=True)]
A = sorted(pd.to_datetime(a.auction_date).unique())
z = db.DBNStore.from_file("dbdata/zn_1d.dbn.zst").to_df()
z.index = z.index.tz_localize(None).normalize()
z = z[~z.index.duplicated(keep="last")]
ret = z.close.diff() * 1000.0
ret[z.instrument_id != z.instrument_id.shift(1)] = 0.0  # roll day
days = z.index
pos = pd.Series(0.0, index=days)
for ad in A:
    i = days.searchsorted(ad)
    if i >= len(days) or i < 6: continue
    # position for day k = held from close k-1 to close k
    pos.iloc[i - 4:i] -= 1      # closes A-5 .. A-1  -> days A-4 .. A-1 earn the short
    pos.iloc[i + 1:i + 3] += 1  # close A -> A+2
pos = np.sign(pos)
cost = pos.diff().abs().fillna(0) * (15.625 + 2.5)
pnl = pos * ret - cost
sh = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
tt = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0
tr, te = pnl[:"2017"], pnl["2018":]
L = [f"auctions used: {len(A)}; days in market {int((pos != 0).sum())} of {len(pos)}\n",
     "| | $/yr per contract | Sharpe | t |", "|---|---|---|---|"]
for nm, x in (("TRAIN 2010-17", tr), ("TEST 2018-26", te), ("all", pnl)):
    L.append(f"| {nm} | {x.mean()*252:+,.0f} | {sh(x):+.2f} | {tt(x):+.1f} |")
L.append("\nby year $: " + ", ".join(f"{y} {g.sum():+,.0f}" for y, g in pnl.groupby(pnl.index.year)))
short, long = pnl[pos < 0], pnl[pos > 0]
L.append(f"short leg: mean ${short.mean():+.0f}/day (t {tt(short):+.1f}); long leg: mean ${long.mean():+.0f}/day (t {tt(long):+.1f})")
try:
    t = np.load("dbdata/tranche.npz"); bb = pd.Series(t["single"], index=pd.to_datetime(t["d"]))
    j = pd.concat([pnl, bb], axis=1).dropna(); L.append(f"corr with B: {j.corr().iloc[0, 1]:+.2f}")
except Exception as e: L.append(str(e))
pnl.to_frame("zn").to_csv("dbdata/auction_pnl.csv")
open("auction.md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
