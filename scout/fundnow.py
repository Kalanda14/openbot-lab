"""Live snapshot: Binance USDT-M funding rates now (public). How much would EUR400 delta-neutral earn at current top rates?"""
import json, urllib.request
d = json.load(urllib.request.urlopen("https://fapi.binance.com/fapi/v1/premiumIndex", timeout=30))
r = sorted(((float(x["lastFundingRate"]), x["symbol"]) for x in d if x["lastFundingRate"]), reverse=True)
n = len(r); pos = [x for x in r if x[0] > 0]
print(f"{n} perps | median funding/8h {sorted(x[0] for x in r)[n//2]*100:.4f}% | top 10:")
for f, s in r[:10]: print(f"  {s:14s} {f*100:+.4f}%/8h = {f*3*365*100:+.0f}%/yr")
top = sum(f for f, _ in r[:5]) / 5
print(f"avg of top-5 now {top*100:.3f}%/8h -> EUR400 at 1x hedge (200 spot+200 perp margin) = EUR {200*top*3*30:.1f}/30d IF it persisted 30d (it never does)")
