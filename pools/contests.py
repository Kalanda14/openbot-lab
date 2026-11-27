"""Earnings distribution of audit-contest auditors from public leaderboards (no login).
Cantina: https://cantina.xyz/api/v0/leaderboard (all-time rewards, JSON)
Code4rena: https://code4rena.com/leaderboard (default page, awardTotal values embedded in Next.js payload)"""
import json, re, urllib.request, statistics as st, time
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research"}), timeout=60).read()
def dist(name, v):
    v = sorted(v, reverse=True); n = len(v); pos = [x for x in v if x > 0]
    q = lambda p: v[int(p * (n - 1))]
    print(f"\n{name}: n={n}, with >0 = {len(pos)}, total ${sum(v):,.0f}")
    print(f"  top1 ${v[0]:,.0f} | top10 avg ${sum(v[:10])/10:,.0f} | p10 ${q(.1):,.0f} | p25 ${q(.25):,.0f} | median ${q(.5):,.0f} | p75 ${q(.75):,.0f}")
    print(f"  share of total to top 10: {sum(v[:10])/sum(v):.0%}, top 50: {sum(v[:50])/sum(v):.0%}")
    for t in (1000, 10000, 50000, 100000): print(f"  earned >= ${t:,}: {sum(1 for x in v if x >= t)}")
    return v
c = json.loads(get("https://cantina.xyz/api/v0/leaderboard"))["ranking"]
cv = dist("Cantina all-time (reward)", [float(r["reward"] or 0) for r in c])
nf = [r for r in c if float(r["reward"] or 0) > 0]
print("  Cantina auditors with 0 H/M/C findings but >0 reward:", sum(1 for r in nf if r["highFindings"] + r["mediumFindings"] + r["criticalFindings"] == 0))
h = get("https://code4rena.com/leaderboard").decode()
a = [float(x) for x in re.findall(r'awardTotal\\":([0-9.]+)', h)]
dist("Code4rena leaderboard page (default range)", a)
json.dump({"cantina": cv, "c4": a, "fetched": time.strftime("%Y-%m-%d")}, open("data/contests_20261127.json", "w"))

# Cantina competitions list (public): pot, findings submitted, KYC, entry fee
comp = json.loads(get("https://cantina.xyz/api/v0/competitions"))
print(f"\nCantina competitions listed: {len(comp)}")
import collections
print("  status:", dict(collections.Counter(c.get("status") for c in comp)))
def pot(c):
    try: return float(c.get("totalRewardPot") or 0)
    except: return 0.0
rec = [c for c in comp if (c.get("createdAt") or "") >= "2026-05-27"]
print(f"  created last 6 months: {len(rec)}, sum of headline pots ${sum(pot(c) for c in rec):,.0f}"
      f" (= ${sum(pot(c) for c in rec)/6:,.0f}/month headline; many pots are 'up to' and shrink if no High/Medium)")
for c in sorted(rec, key=lambda c: c.get("createdAt") or "", reverse=True)[:15]:
    print(f"  {c['createdAt'][:10]} | {c.get('status')} | pot ${pot(c):>9,.0f} | findings {c.get('totalFindings')} | KYC {c.get('kycRequired')} | fee {c.get('entryFee')} | {c['name'][:45]}")
kyc = sum(1 for c in rec if c.get("kycRequired")); print(f"  KYC required: {kyc}/{len(rec)}")
by = collections.defaultdict(lambda: [0, 0.0, 0])
for c in comp:
    q = (c.get("createdAt") or "????-??")[:7]; q = q[:4] + "H" + ("1" if q[5:7] <= "06" else "2")
    by[q][0] += 1; by[q][1] += pot(c); by[q][2] += int(c.get("totalFindings") or 0)
print("  half-year | contests | headline pots | findings submitted | findings per $1k pot")
for k in sorted(by): n, p, f = by[k]; print(f"  {k} | {n} | ${p:,.0f} | {f} | {f/(p/1000) if p else 0:.1f}")
