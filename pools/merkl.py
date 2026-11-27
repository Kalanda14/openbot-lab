"""Pull all LIVE Merkl opportunities (public API, no key) and find tiny pools where $400 gets a big share.
Usage: python3 merkl.py  -> data/merkl_YYYYMMDD.json + table printed."""
import json, urllib.request, time, sys
U = "https://api.merkl.xyz/v4/opportunities?status=LIVE&items=100&page=%d"
out = []
for p in range(200):
    for t in range(3):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(U % p, headers={"User-Agent": "research"}), timeout=60)); break
        except Exception as e:
            time.sleep(2); r = None
    if not r: break
    out += r
    if len(r) < 100: break
day = time.strftime("%Y%m%d")
json.dump(out, open(f"data/merkl_{day}.json", "w"))
print("opportunities", len(out), file=sys.stderr)
