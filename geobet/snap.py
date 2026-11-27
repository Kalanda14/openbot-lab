"""One snapshot: Georgian soft books (Betlive, Crocobet) vs Polymarket CLOB books.

Usage: python3 snap.py [--first]
  --first : full Betlive scan (all leagues of chosen sports) and save which leagues matched.
Writes data/snaps/<ts>.json  (one row per comparable outcome).
Public, no-login endpoints only. Light polling (a few dozen requests per snapshot).
"""
import json, os, re, sys, time, unicodedata, datetime as dt
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net import get

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
NOW = dt.datetime.now(dt.timezone.utc)
TS = NOW.strftime("%Y%m%dT%H%M%SZ")

# ---------------------------------------------------------------- names
STOP = {"fc", "cf", "afc", "sc", "fk", "ac", "cd", "ud", "sd", "club", "de", "the", "srl", "bk", "if", "sk", "nk",
        "pfc", "kv", "kvc", "as", "ca", "se", "cs", "gd", "rc", "ss", "us", "sv", "vfl", "vfb", "tsg", "jk", "ff",
        "pfk", "w", "wom", "women", "u21", "u23", "u19", "u20", "bc", "hc", "bm", "hb", "esports", "team", "gaming", "y", "and", "1"}
ALIAS = {"utd": "united", "st": "saint", "intl": "international", "int": "inter"}


def norm_tokens(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [ALIAS.get(t, t) for t in s.split()]
    toks = [t for t in toks if t not in STOP and not re.fullmatch(r"\d{4}", t)]
    return toks


def tok_sim(a, b):
    A, B = norm_tokens(a), norm_tokens(b)
    if not A or not B:
        return 0.0
    seq = SequenceMatcher(None, " ".join(sorted(A)), " ".join(sorted(B))).ratio()
    small, big = (A, B) if len(A) <= len(B) else (B, A)
    hit = 0
    for t in small:
        if any(t == u or (len(t) >= 4 and len(u) >= 4 and SequenceMatcher(None, t, u).ratio() >= 0.85) or
               (len(t) >= 3 and (u.startswith(t) or t.startswith(u)) and min(len(t), len(u)) >= 3) for u in big):
            hit += 1
    cover = hit / len(small)
    return max(seq, cover * (0.85 + 0.15 * len(small) / len(big)))


def bad_name(s):
    s = s.lower()
    return any(w in s for w in ("srl", "virtual", "esoccer", "e-soccer", "cyber", "(e)"))


def women(s):
    s = " " + s.lower() + " "
    return any(w in s for w in ("(w)", " women", "(wom)", " wom ", "(f)", " ladies", "wnba", "(women)"))


def parse_ts(s):
    s = s.replace("Z", "").replace("+00:00", "").replace(" ", "T").split(".")[0]
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------- polymarket
def pm_events():
    cat = json.load(open(os.path.join(DATA, "pm_catalog.json")))
    ev = {}
    for e in cat:
        t = e["title"]
        t = re.sub(r"^[^:]{2,60}:\s+", "", t) if ":" in t.split(" vs")[0] else t
        t = re.sub(r"\s*-\s*More Markets$", "", t)
        t = re.sub(r"\s*\(BO\d\).*$", "", t)
        t = re.sub(r"\s*-\s*[^-]*$", "", t) if " vs" in t and " - " in t else t
        parts = re.split(r"\s+vs\.?\s+", t)
        if len(parts) != 2:
            continue
        key = (e["start"][:16], parts[0].strip(), parts[1].strip())
        x = ev.setdefault(key, {"sport": e["sport"], "a": parts[0].strip(), "b": parts[1].strip(),
                                "start": parse_ts(e["start"]), "sels": [], "slug": e["slug"]})
        for m in e["markets"]:
            toks = json.loads(m["clobTokenIds"]); outs = json.loads(m["outcomes"])
            smt = m["sportsMarketType"]
            if smt == "moneyline" and outs == ["Yes", "No"]:
                g = m["groupItemTitle"] or ""
                lab = "X" if g.startswith("Draw") else g
                x["sels"].append({"kind": "1x2", "line": None, "lab": lab, "tok": toks[0]})
            elif smt == "moneyline" and len(outs) == 2:
                x["sels"].append({"kind": "ml", "line": None, "lab": outs[0], "tok": toks[0], "lab2": outs[1]})
            elif smt in ("totals", "tennis_match_totals") and outs == ["Over", "Under"] and m.get("line") is not None:
                x["sels"].append({"kind": "tot", "line": float(m["line"]), "lab": "Over", "tok": toks[0]})
            elif smt == "both_teams_to_score" and outs == ["Yes", "No"]:
                x["sels"].append({"kind": "btts", "line": None, "lab": "Yes", "tok": toks[0]})
    return list(ev.values())


def pm_books(tokens):
    out = {}
    tokens = list(dict.fromkeys(tokens))
    for i in range(0, len(tokens), 400):
        chunk = tokens[i:i + 400]
        r = get("https://clob.polymarket.com/books", data=[{"token_id": t} for t in chunk], timeout=60)
        for b in r:
            bids = [(float(x["price"]), float(x["size"])) for x in b.get("bids", [])]
            asks = [(float(x["price"]), float(x["size"])) for x in b.get("asks", [])]
            bb = max(bids) if bids else None
            ba = min(asks) if asks else None
            out[b["asset_id"]] = {"bid": bb[0] if bb else None, "bidsz": bb[1] if bb else 0,
                                  "ask": ba[0] if ba else None, "asksz": ba[1] if ba else 0}
    return out


# ---------------------------------------------------------------- soft books -> std events
# std: {book, sport, league, home, away, start, mk: {('1x2',None): {'1':o,'X':o,'2':o}, ('ml',None):{'1','2'},
#        ('tot',L): {'Over','Under'}, ('btts',None): {'Yes','No'}}}
def croco():
    d = get("https://sport-gateway.crocobet.com/sport/en/rest/search/events/search-by-hours-ahead/36",
            headers={"Request-Language": "en"}, timeout=120)["data"]
    out = []
    for e in d:
        sp = e["category1Name"]
        if sp.startswith("E-") or bad_name(e["eventName"]):
            continue
        ps = e.get("participants") or []
        if len(ps) != 2:
            continue
        mk = {}
        for g in e["eventGames"]:
            os_ = {o["outcomeName"]: o["outcomeOdds"] for o in g["outcomes"] if o.get("status") == 100 and o.get("outcomeOdds", 0) > 1.0}
            gt = g["gameType"]
            if sp in ("Soccer",) and gt == 1 and set(os_) == {"1", "X", "2"}:
                mk[("1x2", None)] = os_
            elif sp == "Soccer" and gt == 8 and g.get("argument") is not None and set(os_) == {"Over", "Under"}:
                mk[("tot", float(g["argument"]))] = os_
            elif sp == "Soccer" and gt == 98 and set(os_) == {"Yes", "No"}:
                mk[("btts", None)] = os_
            elif sp == "Basketball" and gt == -2527 and set(os_) == {"1", "2"}:
                mk[("ml", None)] = os_
            elif sp in ("Tennis", "Table tennis", "Darts", "Volleyball") or sp.startswith("ES "):
                if gt == 6 and set(os_) == {"1", "2"}:
                    mk[("ml", None)] = os_
        if mk:
            out.append({"book": "crocobet", "sport": sp, "league": f'{e["category2Name"]} / {e["category3Name"]}',
                        "home": ps[0]["name"].strip(), "away": ps[1]["name"].strip(),
                        "start": dt.datetime.fromtimestamp(e["eventStart"] / 1000, dt.timezone.utc), "mk": mk})
    return out


BL = "https://websport.betlive.com"
BL_SPORTS = {1: "Soccer", 6: "Basketball", 5: "Tennis", 22: "Table tennis", 4: "Volleyball", 19: "Darts",
             799: "ES CS2", 816: "ES Dota", 866: "ES Valorant"}


def betlive(first):
    lf = os.path.join(DATA, "betlive_leagues.json")
    if first or not os.path.exists(lf):
        tree = get(BL + "/api/category/getSportsWithCountriesAndLeagues", timeout=60)
        ids = [l["id"] for s in tree if s.get("id") in BL_SPORTS for c in s.get("children", [])
               for l in c.get("children", []) if l.get("eventCount", 0) > 0 and "Special" not in (l.get("name") or "")]
    else:
        ids = json.load(open(lf))
    out = []
    for i in range(0, len(ids), 25):
        r = get(BL + "/api/event/getCategoryEvents?leagueIds=" + ",".join(map(str, ids[i:i + 25])) + "&page=1&take=600",
                timeout=120, pause=1.0)
        for spn in r:
            for l in spn.get("children", []):
                for e in l.get("events", []):
                    sid = e.get("sportId")
                    if sid not in BL_SPORTS or e.get("statusId") != 1:
                        continue
                    sp = BL_SPORTS[sid]
                    if bad_name(e.get("name", "")) or bad_name(l.get("name") or ""):
                        continue
                    mk = {}
                    for g in e.get("defaults", []):
                        for m in g["mkt"]:
                            if m.get("statusId") != 1 or not m.get("sel"):
                                continue
                            os_ = {o["name"]: o["odd"] for s in m["sel"] for o in s["out"]
                                   if o.get("statusId") == 1 and o.get("odd", 0) > 1.0}
                            nm = (m.get("name") or "").strip()
                            if sp == "Soccer" and nm in ("Fulltime Result", "1X2", "Full Time Result") and set(os_) == {"1", "X", "2"}:
                                mk[("1x2", None)] = os_
                            elif sp == "Soccer" and nm.startswith("Goals ") and m.get("arg") and set(os_) == {"Over", "Under"}:
                                mk[("tot", float(m["arg"]))] = os_
                            elif sp == "Soccer" and nm.lower().startswith("both teams to score") and set(os_) == {"Yes", "No"}:
                                mk[("btts", None)] = os_
                            elif sp == "Basketball" and "(OT)" in nm and ("Winner" in nm or nm.startswith("12")) and set(os_) == {"1", "2"}:
                                mk[("ml", None)] = os_
                            elif sp != "Soccer" and sp != "Basketball" and ("Winner" in nm or nm == "12") and set(os_) == {"1", "2"}:
                                mk[("ml", None)] = os_
                    if mk:
                        out.append({"book": "betlive", "sport": sp, "league": f'{l.get("countryName","")} / {l.get("name")}',
                                    "home": e["homeTeamName"], "away": e["awayTeamName"], "league_id": l["id"],
                                    "start": dt.datetime.fromtimestamp(e["startDate"] / 1000, dt.timezone.utc), "mk": mk})
    return out


# ---------------------------------------------------------------- matching + edges
def match(pm, soft):
    pairs = []
    for s in soft:
        best = None
        for p in pm:
            dtm = abs((p["start"] - s["start"]).total_seconds()) / 60
            if dtm > 150:
                continue
            if women(p["a"] + " " + p["b"] + " " + p["sport"] + (" (w)" if p["sport"] in ("cwbb", "wta", "wta-doubles", "setkawoua") else "")) != \
                    women(s["home"] + " " + s["away"] + " " + s["league"]):
                continue
            for flip in (False, True):
                a, b = (p["b"], p["a"]) if flip else (p["a"], p["b"])
                sc = min(tok_sim(a, s["home"]), tok_sim(b, s["away"]))
                need = 0.72 if dtm <= 20 else 0.88
                if sc >= need and (best is None or sc > best[0]):
                    best = (sc, p, flip, dtm)
        if best:
            pairs.append((s, best))
    return pairs


def rows_for(s, sc, p, flip, dtm, books):
    rows = []
    home_pm, away_pm = (p["b"], p["a"]) if flip else (p["a"], p["b"])

    def prob(tok):
        b = books.get(tok)
        if not b or b["bid"] is None or b["ask"] is None:
            return None
        return b

    def add(kind, line, lab, odds, fair, lo, hi, spread, extra):
        rows.append({"ts": TS, "book": s["book"], "sport": s["sport"], "pm_sport": p["sport"], "league": s["league"],
                     "event": f'{s["home"]} - {s["away"]}', "pm_event": f'{p["a"]} vs {p["b"]}', "match": round(sc, 3),
                     "dt_min": round(dtm), "start": s["start"].isoformat(), "kind": kind, "line": line, "sel": lab,
                     "odds": odds, "fair": round(fair, 4), "edge": round(odds * fair - 1, 4),
                     "edge_lo": round(odds * lo - 1, 4), "edge_hi": round(odds * hi - 1, 4), "pm_spread": round(spread, 4),
                     "overround": round(sum(1 / o for o in extra.values()) - 1, 4), "slug": p["slug"],
                     "book_fair": round((1 / odds) / sum(1 / o for o in extra.values()), 4),
                     "hours_to_start": round((s["start"] - NOW).total_seconds() / 3600, 2)})

    sels = p["sels"]
    # 1x2
    if ("1x2", None) in s["mk"]:
        x = [q for q in sels if q["kind"] == "1x2"]
        draw = [q for q in x if q["lab"] == "X"]
        teams = [q for q in x if q["lab"] != "X"]
        if len(draw) == 1 and len(teams) == 2:
            bh = max(teams, key=lambda q: tok_sim(q["lab"], home_pm))
            ba = [q for q in teams if q is not bh][0]
            bs = {"1": prob(bh["tok"]), "X": prob(draw[0]["tok"]), "2": prob(ba["tok"])}
            if all(bs.values()):
                mids = {k: (v["bid"] + v["ask"]) / 2 for k, v in bs.items()}
                tot = sum(mids.values())
                for k in "1X2":
                    o = s["mk"][("1x2", None)][k]
                    add("1x2", None, k, o, mids[k] / tot, bs[k]["bid"] / tot, bs[k]["ask"] / tot,
                        bs[k]["ask"] - bs[k]["bid"], s["mk"][("1x2", None)])
    # 2-way ml
    if ("ml", None) in s["mk"]:
        x = [q for q in sels if q["kind"] == "ml"]
        if len(x) == 1:
            q = x[0]; b = prob(q["tok"])
            if b:
                pa = (b["bid"] + b["ask"]) / 2  # prob of outcome q['lab']
                a_is_home = tok_sim(q["lab"], home_pm) >= tok_sim(q["lab"], away_pm)
                ph, lo, hi = (pa, b["bid"], b["ask"]) if a_is_home else (1 - pa, 1 - b["ask"], 1 - b["bid"])
                m = s["mk"][("ml", None)]
                add("ml", None, "1", m["1"], ph, lo, hi, b["ask"] - b["bid"], m)
                add("ml", None, "2", m["2"], 1 - ph, 1 - hi, 1 - lo, b["ask"] - b["bid"], m)
    # totals
    for q in sels:
        if q["kind"] == "tot" and ("tot", q["line"]) in s["mk"]:
            b = prob(q["tok"])
            if b:
                po = (b["bid"] + b["ask"]) / 2; m = s["mk"][("tot", q["line"])]
                add("tot", q["line"], "Over", m["Over"], po, b["bid"], b["ask"], b["ask"] - b["bid"], m)
                add("tot", q["line"], "Under", m["Under"], 1 - po, 1 - b["ask"], 1 - b["bid"], b["ask"] - b["bid"], m)
        if q["kind"] == "btts" and ("btts", None) in s["mk"]:
            b = prob(q["tok"])
            if b:
                py = (b["bid"] + b["ask"]) / 2; m = s["mk"][("btts", None)]
                add("btts", None, "Yes", m["Yes"], py, b["bid"], b["ask"], b["ask"] - b["bid"], m)
                add("btts", None, "No", m["No"], 1 - py, 1 - b["ask"], 1 - b["bid"], b["ask"] - b["bid"], m)
    return rows


def main():
    first = "--first" in sys.argv
    t0 = time.time()
    pm = pm_events()
    soft = []
    for fn, args in ((croco, ()), (betlive, (first,))):
        try:
            x = fn(*args); soft += x; print(fn.__name__, len(x), "events", round(time.time() - t0), "s", flush=True)
        except Exception as e:
            print("FAIL", fn.__name__, e, flush=True)
    soft = [s for s in soft if s["start"] > NOW]  # prematch only
    pairs = match(pm, soft)
    print("matched", len(pairs), flush=True)
    toks = [q["tok"] for _, (sc, p, f, d) in pairs for q in p["sels"]]
    books = pm_books(toks)
    rows = []
    for s, (sc, p, flip, dtm) in pairs:
        rows += rows_for(s, sc, p, flip, dtm, books)
    os.makedirs(os.path.join(DATA, "snaps"), exist_ok=True)
    json.dump(rows, open(os.path.join(DATA, "snaps", TS + ".json"), "w"))
    if first:
        lg = sorted({s["league_id"] for s, _ in pairs if s["book"] == "betlive"})
        json.dump(lg, open(os.path.join(DATA, "betlive_leagues.json"), "w"))
        print("betlive leagues kept", len(lg))
    print("rows", len(rows), "time", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
