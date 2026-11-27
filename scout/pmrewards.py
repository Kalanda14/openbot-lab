"""Polymarket liquidity-rewards snapshot (public endpoints, no account).
For each rewarded market: competing score-weighted depth within max spread (docs formula S=((v-s)/v)^2*size),
then our estimated daily reward if we add a two-sided quote of SHARES shares per side at distance D cents from mid.
Snapshot only: ignores time-variation of competitors and ignores adverse-selection losses when our quotes get filled.
"""
import json, sys, urllib.request, concurrent.futures as cf
SHARES, D, TOPN = 460, 1.0, 200      # ~EUR400 of two-sided quote (cost ~= shares*$1)
def g(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30))
allm, cur = [], ""
for _ in range(200):
    d = g("https://clob.polymarket.com/rewards/markets/multi?page_size=500" + (f"&next_cursor={cur}" if cur else ""))
    allm += d["data"]; cur = d.get("next_cursor")
    if not cur or cur == "LTE=": break
rate = lambda m: sum(c.get("rate_per_day", 0) for c in m["rewards_config"])
rw = sorted([m for m in allm if rate(m) > 0], key=rate, reverse=True)
print(f"markets listed {len(allm)} | rewarded {len(rw)} | total pool ${sum(map(rate, rw)):,.0f}/day")
def one(m):
    try: b = g("https://clob.polymarket.com/book?token_id=" + m["tokens"][0]["token_id"])
    except Exception: return None
    bids = [(float(x["price"]), float(x["size"])) for x in b["bids"]]; asks = [(float(x["price"]), float(x["size"])) for x in b["asks"]]
    if not bids or not asks: return None
    mid = (max(p for p, _ in bids) + min(p for p, _ in asks)) / 2; v = m["rewards_max_spread"]
    sc = lambda side: sum(((v - abs(p - mid) * 100) / v) ** 2 * s for p, s in side if abs(p - mid) * 100 < v and s >= m["rewards_min_size"])
    q1, q2 = sc(bids), sc(asks)
    ours = ((v - D) / v) ** 2 * SHARES if D < v else 0
    if not (0.10 <= mid <= 0.90): return None   # needs two-sided + extreme prices = skip
    qo, qt = min(q1, q2), min(q1, q2) + ours     # crude: competitors' Q_min vs ours added both sides
    share = ours / (qo + ours) if ours else 0
    return dict(q=m["question"][:60], rate=rate(m), mid=round(mid, 3), v=v, minsz=m["rewards_min_size"], comp=round(qo), share=round(share, 3),
                usd_day=round(share * rate(m), 2), vol24=round(m.get("volume_24hr") or 0))
with cf.ThreadPoolExecutor(8) as ex: res = [r for r in ex.map(one, rw[:TOPN]) if r]
res.sort(key=lambda r: -r["usd_day"])
print(f"\nTop by our est. $/day (one market at a time, {SHARES} sh/side at {D}c):")
for r in res[:15]: print(r)
import statistics as st
print("\nmedian est $/day over", len(res), "markets:", st.median(r["usd_day"] for r in res))
json.dump(res, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=0)
