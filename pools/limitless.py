"""Limitless (Base) liquidity rewards: public API, no key. Lists every active market's dailyReward
(Polymarket-style: minSize, maxSpread, c) and, for rewarded markets, the orderbook depth inside maxSpread
(= competing scored size). Output: data/limitless_YYYYMMDD.json + table."""
import json, urllib.request, time
B = "https://api.limitless.exchange"
def get(p):
    return json.load(urllib.request.urlopen(urllib.request.Request(B + p, headers={"User-Agent": "research"}), timeout=60))
ms, page = [], 1
while True:
    d = get(f"/markets/active?limit=25&page={page}"); ms += d["data"]
    if len(d["data"]) < 25 or page > 60: break
    page += 1
def num(x):
    try: return float(x)
    except: return 0.0
rew = []
def walk(m, parent=""):
    s = m.get("settings") or {}
    dr = num(s.get("effectiveDailyReward")) or num(s.get("dailyReward"))
    if dr > 0: m = dict(m, title=(parent + " / " + m.get("title", ""))[:60]); rew.append((m, s, dr))
    for sub in m.get("markets") or []: walk(sub, m.get("title", ""))   # group markets nest sub-markets
for m in ms: walk(m)
print(f"active markets {len(ms)}, rewardable flag {sum(1 for m in ms if m.get('isRewardable'))}, with dailyReward>0: {len(rew)}")
dec = 6
out = []
for m, s, dr in sorted(rew, key=lambda r: -r[2]):
    drv = dr   # dailyReward is in whole USDC (values 1-3 seen); minSize is in 1e6 base units
    row = dict(slug=m["slug"], title=m["title"][:60], daily=drv, minSize=num(s.get("minSize")) / 10**dec,
               maxSpread=s.get("maxSpread"), vol=m.get("volumeFormatted"), tradeType=m.get("tradeType"))
    try:
        ob = get(f"/markets/{m['slug']}/orderbook"); row["ob_keys"] = list(ob.keys())
        mid = num(ob.get("adjustedMidpoint") or ob.get("midpoint")); v = float(s.get("maxSpread") or 0)
        def depth(side):
            return sum(num(o.get("size")) / 10**dec for o in ob.get(side, []) if mid and abs(num(o.get("price")) - mid) <= v)
        row.update(mid=mid, bid_in=depth("bids"), ask_in=depth("asks"))
    except Exception as e:
        row["ob_err"] = str(e)[:80]
    out.append(row); time.sleep(0.2)
json.dump({"markets": len(ms), "rewarded": out}, open(f"data/limitless_{time.strftime('%Y%m%d')}.json", "w"), indent=1)
print(f"total daily reward ${sum(r['daily'] for r in out):,.2f}")
for r in out[:30]:
    print(f"${r['daily']:8.2f}/d | min {r['minSize']:6.0f} | spr {r['maxSpread']} | mid {r.get('mid')} | bid_in {r.get('bid_in',0):9.0f} | ask_in {r.get('ask_in',0):9.0f} | vol {r['vol']} | {r['title']}")
