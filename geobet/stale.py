"""Across snapshots: do soft odds lag Polymarket moves? Do positive edges persist?"""
import json, glob, os, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(HERE, "data", "snaps", "*.json")))[1:]  # skip pre-filter first run
ser = collections.defaultdict(list)
for f in files:
    for r in json.load(open(f)):
        if r["pm_spread"] > 0.03 or r["fair"] < 0.08 or r["match"] < 0.8 or abs(r["fair"] - r["book_fair"]) > 0.2:
            continue
        ser[(r["book"], r["slug"], r["kind"], r["line"], r["sel"])].append(r)
print("snapshots", len(files), "series", len(ser))
pm_moves = follow = soft_changes = pairs = 0
lags = []
for k, v in ser.items():
    for a, b in zip(v, v[1:]):
        pairs += 1
        soft_changed = a["odds"] != b["odds"]
        soft_changes += soft_changed
        if abs(b["fair"] - a["fair"]) >= 0.03:
            pm_moves += 1
            # soft followed if its no-vig prob moved the same direction by >= 1/3 of the PM move
            d_pm = b["fair"] - a["fair"]; d_bk = b["book_fair"] - a["book_fair"]
            follow += (d_bk * d_pm > 0 and abs(d_bk) >= abs(d_pm) / 3)
print(f"consecutive pairs {pairs}; soft odds changed in {soft_changes} ({soft_changes / max(pairs, 1):.1%})")
print(f"PM fair moved >=3pp: {pm_moves}; soft followed in same window: {follow} ({follow / max(pm_moves, 1):.1%})")
pos = {k: v for k, v in ser.items() if any(r["edge"] > 0.0 for r in v)}
print("series ever with edge>0:", len(pos))
for k, v in list(pos.items())[:20]:
    print("  ", k[0], v[0]["event"][:35], k[2], k[3], k[4], [round(r["edge"], 3) for r in v])
book = collections.defaultdict(list)
for f in files:
    rows = [r for r in json.load(open(f)) if r["pm_spread"] <= 0.03 and r["fair"] >= 0.08 and r["match"] >= 0.8
            and abs(r["fair"] - r["book_fair"]) <= 0.2]
    e = [r["edge"] for r in rows]
    print(os.path.basename(f), "n", len(e), "median", round(st.median(e), 3), ">0", sum(x > 0 for x in e),
          ">2%", sum(x > .02 for x in e), ">5%", sum(x > .05 for x in e))
