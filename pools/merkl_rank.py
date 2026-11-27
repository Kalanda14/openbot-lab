"""Only DUTCH_AUCTION (fixed budget split pro-rata) campaigns; TVL backed out of APR when API tvl~0.
Rank Merkl LIVE opportunities by what a $400 deposit would earn/month if pool and other TVL stay fixed.
earn = dailyRewards * 400/(tvl+400) * 30. Token rewards only (POINT campaigns have no $ value)."""
import json, sys, time, glob
f = sorted(glob.glob("data/merkl_*.json"))[-1]
d = json.load(open(f)); now = time.time()
rows = []
for o in d:
    if any(t.get("type") == "POINT" for t in o["tokens"]) or o["dailyRewards"] <= 0: continue
    dist = {b.get("distributionType") for b in (o.get("aprRecord") or {}).get("breakdowns", [])}
    if dist != {"DUTCH_AUCTION"}: continue   # only fixed-budget pools; FIX/MAX APR campaigns scale with capital
    tvl = o["tvl"]; dr = o["dailyRewards"]
    # ENCOMPASSING / off-chain campaigns often report tvl=0; back out TVL from the shown APR instead
    if o["apr"] > 0: tvl = max(tvl, dr * 365 / (o["apr"] / 100))
    elif tvl < 100: continue                 # no TVL and no APR -> cannot size, skip
    end = int(o.get("latestCampaignEnd") or 0); days_left = (end - now) / 86400
    earn = dr * 400 / (tvl + 400) * 30
    rows.append((earn, tvl, dr, o["apr"], days_left, o["action"], o["chain"]["name"], o["protocol"]["name"] if o.get("protocol") else "", o["name"][:70],
                 ",".join(t["symbol"] for t in o["tokens"])))
rows.sort(reverse=True)
print(f"file {f}, token campaigns {len(rows)}")
print("earn$/mo@400 | tvl$ | pool$/day | apr% | days_left | action | chain | protocol | name | reward")
for r in rows[:45]:
    print(f"{r[0]:8.0f} | {r[1]:10.0f} | {r[2]:7.1f} | {r[3]:9.0f} | {r[4]:5.1f} | {r[5]} | {r[6]} | {r[7]} | {r[8]} | {r[9]}")
tot = sum(r[2] for r in rows); small = [r for r in rows if r[1] < 20000]
print(f"\nall token campaigns: ${tot:,.0f}/day; TVL<$20k: {len(small)} campaigns, ${sum(r[2] for r in small):,.0f}/day total")
