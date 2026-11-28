"""Parse Cloudbet public competition pages (server-rendered HTML, no login, no API key) into std events.
Only plain page GETs, a few per run. std format matches ../../geobet/snap.py rows_for()."""
import json, re, sys, os, time, urllib.request, gzip, datetime as dt
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36"
COMPS = {  # cloudbet path -> sport label
    "soccer/england-premier-league": "soccer", "soccer/spain-laliga": "soccer", "soccer/italy-serie-a": "soccer",
    "soccer/germany-bundesliga": "soccer", "soccer/france-ligue-1": "soccer", "soccer/england-championship": "soccer",
    "soccer/international-clubs-uefa-champions-league": "soccer", "soccer/netherlands-eredivisie": "soccer",
    "soccer/portugal-primeira-liga": "soccer", "soccer/turkey-super-lig": "soccer",
    "basketball/usa-nba": "basketball", "ice-hockey/usa-nhl": "hockey", "american-football/usa-nfl": "nfl",
    "american-football/usa-ncaaf": "ncaaf", "basketball/usa-ncaab": "ncaab",
}

def page(path):
    req = urllib.request.Request("https://www.cloudbet.com/en/sports/" + path,
                                 headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
    time.sleep(1.0)
    return b.decode("utf-8", "ignore")

def events(html):
    dec = json.JSONDecoder(); out = {}
    for m in re.finditer(r'\{"sequence":"\d+","id":(\d+),"home":\{', html):
        try:
            obj, _ = dec.raw_decode(html, m.start())
        except Exception:
            continue
        if obj.get("markets") and obj.get("home") and obj.get("away"):
            out[obj["id"]] = obj
    return list(out.values())

def sel_map(mk, key, period="period=ft"):
    sub = (mk.get(key) or {}).get("submarkets", {})
    s = sub.get(period) or (next(iter(sub.values())) if sub else None)
    return (s or {}).get("selections", [])

def to_std(ev, sport, league):
    mk = ev["markets"]; std = {"book": "cloudbet", "sport": sport, "league": league, "home": ev["home"]["name"],
                              "away": ev["away"]["name"], "start": dt.datetime.fromisoformat(ev["startTime"].replace("Z", "+00:00")),
                              "mk": {}, "maxstake": {}}
    ok = lambda x: x.get("status") == "SELECTION_ENABLED" and x.get("side") == "BACK"
    if sport == "soccer":
        s = {x["outcome"]: x for x in sel_map(mk, "soccer.match_odds") if ok(x)}
        if {"home", "draw", "away"} <= set(s):
            std["mk"][("1x2", None)] = {"1": s["home"]["price"], "X": s["draw"]["price"], "2": s["away"]["price"]}
            std["maxstake"][("1x2", None)] = {"1": s["home"]["maxStake"], "X": s["draw"]["maxStake"], "2": s["away"]["maxStake"]}
        tot = {}
        for x in sel_map(mk, "soccer.total_goals"):
            if ok(x):
                L = float(x["params"].split("=")[1]); tot.setdefault(L, {})[x["outcome"].capitalize()] = x["price"]
        for L, d in tot.items():
            if len(d) == 2 and L % 1 == 0.5:
                std["mk"][("tot", L)] = d
        b = {x["outcome"]: x["price"] for x in sel_map(mk, "soccer.both_teams_to_score") if ok(x)}
        if {"yes", "no"} <= set(b):
            std["mk"][("btts", None)] = {"Yes": b["yes"], "No": b["no"]}
    else:
        for key in mk:
            if key.endswith(".moneyline"):
                sub = mk[key]["submarkets"]
                s = None
                for pk in ("period=ot&period=ft", "period=ft&period=ot", "period=ft", "period=match"):
                    if pk in sub: s = sub[pk]; break
                if s is None and len(sub) == 1: s = next(iter(sub.values()))
                if s:
                    d = {x["outcome"]: x["price"] for x in s["selections"] if ok(x)}
                    if {"home", "away"} <= set(d) and "draw" not in d:
                        std["mk"][("ml", None)] = {"1": d["home"], "2": d["away"]}
    return std

def fetch_all():
    out = []
    for path, sport in COMPS.items():
        try:
            evs = events(page(path))
        except Exception as e:
            print("fail", path, e, file=sys.stderr); continue
        for ev in evs:
            if ev.get("status") not in (None, "TRADING", "TRADING_LIVE") and "TRADING" not in str(ev.get("status")):
                pass
            out.append(to_std(ev, sport, path))
        print(path, len(evs), file=sys.stderr)
    return out

if __name__ == "__main__":
    std = fetch_all()
    print(len(std), "events")
