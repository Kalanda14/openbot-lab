"""Build a catalog of Polymarket sports game markets starting in the next H hours.
Public gamma-api only. Output: data/pm_catalog.json"""
import json, sys, datetime as dt, os
sys.path.insert(0, os.path.dirname(__file__))
from net import get

H = float(sys.argv[1]) if len(sys.argv) > 1 else 36
KEEP = {"moneyline", "totals", "both_teams_to_score", "child_moneyline", "tennis_match_totals"}
now = dt.datetime.now(dt.timezone.utc)
sports = get("https://gamma-api.polymarket.com/sports")
out = []
for s in sports:
    sid = s.get("series")
    if not sid:
        continue
    try:
        evs = get(f"https://gamma-api.polymarket.com/events?series_id={sid}&closed=false&limit=200", pause=0.15)
    except Exception as e:
        print("fail", s["sport"], e); continue
    for e in evs:
        st = e.get("startTime") or e.get("endDate")
        if not st:
            continue
        st2 = st.replace("Z", "").replace("+00:00", "").replace(" ", "T").split(".")[0]
        try:
            t = dt.datetime.fromisoformat(st2).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
        if not (now - dt.timedelta(hours=1) < t < now + dt.timedelta(hours=H)):
            continue
        mk = []
        for m in e.get("markets", []):
            if m.get("closed") or not m.get("clobTokenIds"):
                continue
            if m.get("sportsMarketType") not in KEEP:
                continue
            mk.append({k: m.get(k) for k in ["question", "sportsMarketType", "groupItemTitle", "line", "outcomes",
                                             "clobTokenIds", "bestBid", "bestAsk", "liquidity", "volume"]})
        if mk:
            out.append({"sport": s["sport"], "slug": e["slug"], "title": e["title"], "start": st, "markets": mk})
    print(s["sport"], len(out), flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "data", "pm_catalog.json"), "w"))
print("events", len(out), "markets", sum(len(e["markets"]) for e in out))
