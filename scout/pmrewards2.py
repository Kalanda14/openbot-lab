"""Polymarket liquidity rewards v2: top markets by rate_per_day (public API, sorted), corrected Q_min for competitors
(Q_min = max(min(q1,q2), max(q1,q2)/3) for mid in [0.10,0.90]), filters: mid in [0.10,0.90], end_date > 3 days.
Strategy modelled: min-size two-sided quote at D cents from mid in each market (spread capital across markets).
Crude adverse-selection haircut: loss = max(0, |1-day price change| - D) * size per side (as if run over once a day, no requote).
Run twice a few minutes apart to check that 'empty' markets stay empty."""
import json, sys, time, urllib.request, datetime as dt, concurrent.futures as cf
D = 1.0
def g(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=30))
ms, cur = [], ""
for _ in range(2):
    d = g("https://clob.polymarket.com/rewards/markets/multi?page_size=500&order_by=rate_per_day&position=DESC" + (f"&next_cursor={cur}" if cur else ""))
    ms += d["data"]; cur = d.get("next_cursor")
rate = lambda m: sum(c.get("rate_per_day", 0) for c in m["rewards_config"])
now = dt.datetime.now(dt.timezone.utc)
def days_left(m):
    try: return (dt.datetime.fromisoformat(m["end_date"].replace(" ", "T").replace("+00", "+00:00")) - now).days
    except Exception: return -1
ms = [m for m in ms if rate(m) > 0 and days_left(m) > 3]
print(f"top-1000 by rate: {len(ms)} pass end>3d | pool of these ${sum(map(rate, ms)):,.0f}/day")
def one(m):
    try: b = g("https://clob.polymarket.com/book?token_id=" + m["tokens"][0]["token_id"])
    except Exception: return None
    bids = [(float(x["price"]), float(x["size"])) for x in b["bids"]]; asks = [(float(x["price"]), float(x["size"])) for x in b["asks"]]
    if not bids or not asks: return None
    mid = (max(p for p, _ in bids) + min(p for p, _ in asks)) / 2; v = m["rewards_max_spread"]; mn = m["rewards_min_size"]
    if not (0.10 <= mid <= 0.90) or D >= v: return None
    sc = lambda side: sum(((v - abs(p - mid) * 100) / v) ** 2 * s for p, s in side if abs(p - mid) * 100 < v and s >= mn)
    q1, q2 = sc(bids), sc(asks); comp = max(min(q1, q2), max(q1, q2) / 3)
    size = mn; ours = ((v - D) / v) ** 2 * size
    share = ours / (comp + ours); rew = share * rate(m)
    cap = size * (mid - D / 100) + size * (1 - mid - D / 100)        # cost of YES bid + NO bid
    adv = max(0, abs(m.get("one_day_price_change") or 0) - D / 100) * size
    return dict(id=m["condition_id"], q=m["question"][:55], rate=rate(m), mid=round(mid, 3), v=v, minsz=mn, comp=round(comp), share=round(share, 3),
                rew=round(rew, 2), cap=round(cap), adv=round(adv, 2), net=round(rew - adv, 2), d1=m.get("one_day_price_change"), days=days_left(m))
with cf.ThreadPoolExecutor(8) as ex: res = [r for r in ex.map(one, ms) if r]
res.sort(key=lambda r: -r["net"] / max(r["cap"], 1))
out = sys.argv[1] if len(sys.argv) > 1 else "/dev/null"; json.dump(res, open(out, "w"), indent=0)
print(f"scored {len(res)} markets | min-size quotes, ranked by net $/day per $ capital:")
budget, tot, totrew, n = 460, 0, 0, 0
for r in res:
    if tot + r["cap"] > budget: continue
    tot += r["cap"]; totrew += r["net"]; n += 1
    if n <= 20: print(r)
print(f"\nGreedy fill of ${budget} (~EUR400): {n} markets, capital ${tot}, est NET reward ${totrew:.0f}/day (snapshot, before competition reacts)")
