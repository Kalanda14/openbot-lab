"""What do real makers earn? For a few watched markets: find maker wallets (data-api trades taker_only=false minus taker
rows) and print their daily REWARD payouts (data-api /v2/activity type=REWARD; rows are per wallet per day, all
markets together, so they can't be split per market). Public data only; wallets are shortened in the output.
usage: python pmlp/peers.py [n_markets=5] [makers_per_market=5]"""
import json, os, sys, collections, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
NM = int(sys.argv[1]) if len(sys.argv) > 1 else 5; NW = int(sys.argv[2]) if len(sys.argv) > 2 else 5
def g(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "pmlp-research/0.1"}), timeout=30))

meta = [json.loads(l) for l in open(os.path.join(D, "meta.jsonl"))]
watch = json.load(open(os.path.join(D, "state.json")))["watch"]
seen = set()
for m in [m for m in meta if m["c"] in watch][:NM]:
    base = f"https://data-api.polymarket.com/v2/trades?condition={m['c']}&limit=1000"
    tk = {(r["transaction_hash"], r["proxy_wallet"]) for r in g(base)["data"]}
    mk = collections.Counter()
    for r in g(base + "&taker_only=false")["data"]:
        if (r["transaction_hash"], r["proxy_wallet"]) not in tk: mk[r["proxy_wallet"]] += r["size"]
    print(f"{m['q'][:70]}  ({len(mk)} maker wallets in last 1000 fills)")
    for w, v in mk.most_common(NW):
        rows = g(f"https://data-api.polymarket.com/v2/activity?user={w}&type=REWARD&limit=60")["data"]
        day = collections.defaultdict(float)
        for x in rows: day[x["timestamp"] // 86400] += float(x.get("usdc_size") or 0)
        last7 = [round(day[k], 1) for k in sorted(day)[-7:]]
        print(f"   {w[:6]}..  maker fills {v:7.0f} sh | daily REWARD $ (last 7 paid days): {last7}")
