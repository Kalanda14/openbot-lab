"""Cloudbet (public pages) vs Polymarket. Reuses ../../geobet (catalog parsing, matching, rows).
Edge = cloudbet_odds x PM_fair - 1, PM fair = de-vigged mid of best bid/ask.
NOTE 2026-11-28: gamma-api/clob.polymarket.com fail TLS from this network (blocked), so live /books could not be
read. Fallback: bestBid/bestAsk stored in geobet/data/pm_catalog.json (gamma, CLOB top of book, built 2026-11-27 23:31Z, ~45 min before the Cloudbet pull).
Results are therefore indicative only. Usage: python3 compare.py [--live]"""
import json, os, sys, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__)); GEO = os.path.join(HERE, "..", "..", "geobet")
sys.path.insert(0, GEO); sys.path.insert(0, HERE)
import snap, cloudbet
cat = json.load(open(os.path.join(GEO, "data", "pm_catalog.json")))
top = {}
for e in cat:
    for m in e["markets"]:
        tok = json.loads(m["clobTokenIds"])[0]
        if m.get("bestBid") is not None and m.get("bestAsk") is not None:
            top[tok] = {"bid": float(m["bestBid"]), "ask": float(m["bestAsk"]), "bidsz": 0, "asksz": 0}
pm = snap.pm_events()
cb = cloudbet.fetch_all()
pairs = snap.match(pm, cb)
books = snap.pm_books([q["tok"] for _, (sc, p, fl, d) in pairs for q in p["sels"]]) if "--live" in sys.argv else top
rows = []
for s, (sc, p, flip, dtm) in pairs:
    rows += snap.rows_for(s, sc, p, flip, dtm, books)
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump({"cloudbet": [{**e, "start": e["start"].isoformat(), "mk": {f"{k[0]}|{k[1]}": v for k, v in e["mk"].items()},
                         "maxstake": {f"{k[0]}|{k[1]}": v for k, v in e["maxstake"].items()}} for e in cb], "rows": rows},
          open(os.path.join(HERE, "data", f"{snap.TS}.json"), "w"))
# 1) Cloudbet margins (fact, from its own prices)
mg = collections.defaultdict(list)
for e in cb:
    for (k, L), d in e["mk"].items():
        mg[(e["league"].split("/")[-1], k if L is None else f"tot{L}")].append(sum(1 / x for x in d.values()) - 1)
print("CLOUDBET MARGINS (overround), all listed events")
for k, v in sorted(mg.items()):
    if len(v) >= 3: print(f"  {k[0]:45} {k[1]:7} n={len(v):3} median {st.median(v):.3f} min {min(v):.3f}")
allm = [x for v in mg.values() for x in v]; print("  ALL median", round(st.median(allm), 4))
# 2) vs PM
print(f"\nPM events {len(pm)}, Cloudbet events {len(cb)}, matched {len(pairs)}, outcomes {len(rows)}")
good = [r for r in rows if r["pm_spread"] <= 0.03 and r["fair"] >= 0.08]
print("clean (PM spread<=3c, fair>=0.08):", len(good))
if good:
    print("median edge", round(st.median(r["edge"] for r in good), 4), "| share>0", round(sum(r["edge"] > 0 for r in good) / len(good), 3),
          "| share>+2%", round(sum(r["edge"] > 0.02 for r in good) / len(good), 3))
    for r in sorted(good, key=lambda r: -r["edge"])[:10]:
        print(f'  {r["edge"]:+.3f} (lo {r["edge_lo"]:+.3f}) {r["event"][:40]:40} {r["kind"]} {r["line"]} {r["sel"]} odds {r["odds"]} fair {r["fair"]} start {r["start"][:16]}')
