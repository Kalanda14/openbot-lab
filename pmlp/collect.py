"""Polymarket liquidity-rewards paper test - collector (public read-only endpoints, no keys, no orders).

Every run:
  1. read the top reward markets (clob /rewards/markets/multi, sorted by rate_per_day),
  2. keep a sticky watch list of <= MAX_WATCH markets (high pool, thin qualifying book, adjusted mid 0.10-0.90,
     market end > 7 days); a market stays watched until it leaves the reward list, closes, or has been watched 10 days,
  3. append for each watched market: one book snapshot (YES token; the YES book already mirrors NO orders),
     new trades since last run (data-api /v2/trades, taker rows only), and resolution once it closes.

Files (pmlp/data/, plain jsonl, one file per UTC day so git deltas stay small, files older than KEEP_DAYS deleted):
  meta.jsonl          one line per market when first watched (question, tokens, tick, neg_risk, end)
  books/DAY.jsonl     {t, c(cid), r(rate/day), v(max spread c), n(min size), k(tick), mc(Polymarket's own
                      'market_competitiveness' field, meaning undocumented), b[[p,s]..], a[[p,s]..]}
                      only levels within v+10 cents of the raw mid are kept, plus the best level each side
  trades/DAY.jsonl    {t, c, o(outcome index 0=YES), s(taker side B/S), p, z(size), h(tx hash prefix)}
  resolved.jsonl      {t, c, closed, winner(outcome index or null)}
  state.json          watch list + last trade timestamp per market
"""
import json, os, time, datetime as dt, urllib.request, concurrent.futures as cf, glob

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")
MAX_WATCH, PREFILTER, KEEP_DAYS, WATCH_DAYS = 45, 200, 10, 10
UA = {"User-Agent": "pmlp-research/0.1", "Content-Type": "application/json"}


def get(u, body=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(u, data=json.dumps(body).encode() if body is not None else None, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 + 3 * i)


def now(): return dt.datetime.now(dt.timezone.utc)
def pdate(s):
    try: return dt.datetime.fromisoformat(s.replace(" ", "T").replace("+00", "+00:00").replace("Z", "+00:00"))
    except Exception: return None


def rate(m):  # only allocations active today
    today = now().date().isoformat()
    return sum(float(c.get("rate_per_day") or 0) for c in m.get("rewards_config") or []
               if (c.get("start_date") or "") <= today <= (c.get("end_date") or "9999"))


def lv(side): return [(float(x["price"]), float(x["size"])) for x in side]


def adj_mid(bids, asks, mn):
    """Size-cutoff-adjusted midpoint: best bid / best ask ignoring orders smaller than min size (our reading)."""
    b = [p for p, s in bids if s >= mn]; a = [p for p, s in asks if s >= mn]
    if not b or not a: return None
    return (max(b) + min(a)) / 2


def qual(bids, asks, mid, v, mn):
    """Aggregate qualifying score of the book: (Q_one from YES bids, Q_two from YES asks)."""
    f = lambda side: sum(((v - abs(p - mid) * 100) / v) ** 2 * s for p, s in side if abs(p - mid) * 100 < v and s >= mn)
    return f(bids), f(asks)


def main():
    os.makedirs(os.path.join(D, "books"), exist_ok=True); os.makedirs(os.path.join(D, "trades"), exist_ok=True)
    sp = os.path.join(D, "state.json")
    st = json.load(open(sp)) if os.path.exists(sp) else {"watch": {}, "last": {}}
    t0 = now(); ts = int(t0.timestamp()); day = t0.date().isoformat()

    ms, cur = [], ""
    for _ in range(2):
        d = get("https://clob.polymarket.com/rewards/markets/multi?page_size=500&order_by=rate_per_day&position=DESC"
                + (f"&next_cursor={cur}" if cur else ""))
        ms += d["data"]; cur = d.get("next_cursor")
        if not cur or cur == "LTE=": break
    by = {m["condition_id"]: m for m in ms}
    ok = lambda m: rate(m) > 0 and (pdate(m.get("end_date") or "") or t0) > t0 + dt.timedelta(days=7)
    cands = [m for m in ms if ok(m)][:PREFILTER]
    watch = st["watch"]

    # drop markets that left the reward list / ended / watched long enough; record resolution if closed
    for cid in list(watch):
        m = by.get(cid)
        if m is None or rate(m) <= 0 or ts - watch[cid]["since"] > WATCH_DAYS * 86400:
            try:
                mk = get("https://clob.polymarket.com/markets/" + cid)
                win = next((i for i, t in enumerate(mk.get("tokens", [])) if t.get("winner")), None)
                with open(os.path.join(D, "resolved.jsonl"), "a") as f:
                    f.write(json.dumps({"t": ts, "c": cid, "closed": mk.get("closed"), "winner": win,
                                        "px": [t.get("price") for t in mk.get("tokens", [])]}) + "\n")
            except Exception: pass
            del watch[cid]

    # books for watched + candidates (batch endpoint, YES token only; NO orders appear mirrored in it)
    need = {cid: by[cid] for cid in watch if cid in by}
    for m in cands: need.setdefault(m["condition_id"], m)
    toks = {m["tokens"][0]["token_id"]: cid for cid, m in need.items() if m.get("tokens")}
    books, tl = {}, list(toks)
    for i in range(0, len(tl), 40):
        try:
            for b in get("https://clob.polymarket.com/books", [{"token_id": t} for t in tl[i:i + 40]]):
                books[toks[b["asset_id"]]] = b
        except Exception as e: print("books batch failed", e)

    # rank new candidates by naive expected pool share if we added a min-size 2-sided quote 1c from mid
    scored = []
    for m in cands:
        cid = m["condition_id"]; b = books.get(cid)
        if cid in watch or not b: continue
        bids, asks = lv(b["bids"]), lv(b["asks"]); v, mn = float(m["rewards_max_spread"]), float(m["rewards_min_size"])
        mid = adj_mid(bids, asks, mn)
        if mid is None or not (0.10 <= mid <= 0.90) or v <= 1: continue
        q1, q2 = qual(bids, asks, mid, v, mn); comp = max(min(q1, q2), max(q1, q2) / 3)
        ours = ((v - 1) / v) ** 2 * mn
        cap = mn * 1.0  # ~ cost of YES bid + NO bid
        scored.append((rate(m) * ours / (ours + comp) / cap, cid))
    scored.sort(reverse=True)
    for _, cid in scored[:max(0, MAX_WATCH - len(watch))]:
        m = by[cid]; watch[cid] = {"since": ts}
        with open(os.path.join(D, "meta.jsonl"), "a") as f:
            f.write(json.dumps({"t": ts, "c": cid, "q": m["question"][:90], "end": m.get("end_date"),
                                "tok": [x["token_id"] for x in m["tokens"]], "slug": m.get("market_slug"),
                                "neg": books[cid].get("neg_risk"), "cfg": m.get("rewards_config")}) + "\n")

    # snapshots
    with open(os.path.join(D, "books", day + ".jsonl"), "a") as f:
        for cid in watch:
            m, b = by.get(cid), books.get(cid)
            if not m or not b: continue
            bids, asks = lv(b["bids"]), lv(b["asks"]); v = float(m["rewards_max_spread"])
            if bids and asks:
                raw = (max(p for p, _ in bids) + min(p for p, _ in asks)) / 2; w = (v + 10) / 100
                bb, ba = max(bids), min(asks)
                bids = sorted({x for x in bids if abs(x[0] - raw) <= w} | {bb}, reverse=True)
                asks = sorted({x for x in asks if abs(x[0] - raw) <= w} | {ba})
            r = lambda L: [[p, round(s, 1)] for p, s in L]
            f.write(json.dumps({"t": ts, "c": cid, "r": rate(m), "v": v, "n": float(m["rewards_min_size"]),
                                "k": float(b.get("tick_size") or 0.01), "mc": round(m.get("market_competitiveness") or 0, 2),
                                "b": r(bids), "a": r(asks)},
                               separators=(",", ":")) + "\n")

    # trades since last run (taker rows only, so each fill once)
    def tr(cid):
        try: return cid, get(f"https://data-api.polymarket.com/v2/trades?condition={cid}&limit=500")["data"]
        except Exception: return cid, None
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(tr, list(watch)))
    nt = 0
    with open(os.path.join(D, "trades", day + ".jsonl"), "a") as f:
        for cid, rows in res:
            if rows is None: continue
            last = st["last"].get(cid, {"t": ts - 900, "h": []})  # first run: only last 15 min
            new = [x for x in rows if x["timestamp"] > last["t"] or
                   (x["timestamp"] == last["t"] and x["transaction_hash"][:12] not in last["h"])]
            for x in sorted(new, key=lambda x: x["timestamp"]):
                f.write(json.dumps({"t": x["timestamp"], "c": cid, "o": x.get("outcome_index"), "s": x["side"][0],
                                    "p": x["price"], "z": round(x["size"], 2), "h": x["transaction_hash"][:12]},
                                   separators=(",", ":")) + "\n"); nt += 1
            if rows:
                mt = max(x["timestamp"] for x in rows)
                st["last"][cid] = {"t": mt, "h": [x["transaction_hash"][:12] for x in rows if x["timestamp"] == mt]}
    st["last"] = {k: v for k, v in st["last"].items() if k in watch}

    # rotate
    cut = (t0 - dt.timedelta(days=KEEP_DAYS)).date().isoformat()
    for p in glob.glob(os.path.join(D, "*", "*.jsonl")):
        if os.path.basename(p)[:10] < cut: os.remove(p)
    json.dump(st, open(sp, "w"), indent=0)
    print(f"{t0:%F %H:%M} reward markets {len(ms)}, candidates {len(cands)}, watched {len(watch)}, new trades {nt}")


if __name__ == "__main__":
    main()
