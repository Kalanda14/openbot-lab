"""Adverse-selection backfill (no book history needed): for the markets collect.py watches, replay the last
DAYS days of real taker trades against a hypothetical hourly quote at price-history +/- 1 cent (min size, YES bid +
NO bid), fills first in queue, inventory cap 2 x size, mark at the latest price. Rewards are NOT estimated here
(no historical books); this only answers "what do the fills cost per day?". Coarser than sim.py: quotes are
refreshed hourly (sim/live: every 10 min), and price-history is Polymarket's displayed price, not the adjusted mid.
usage: python pmlp/fillcheck.py [days=7]"""
import json, os, sys, time, math, urllib.request, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data"); DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
def get(u):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "pmlp-research/0.1"}), timeout=30))
        except Exception:
            if i == 2: raise
            time.sleep(3)

meta = {}
for l in open(os.path.join(D, "meta.jsonl")): m = json.loads(l); meta[m["c"]] = m
watch = json.load(open(os.path.join(D, "state.json")))["watch"]
last_book = {}
for l in open(sorted(__import__("glob").glob(os.path.join(D, "books", "*.jsonl")))[-1]): b = json.loads(l); last_book[b["c"]] = b
now = int(time.time()); t0 = now - DAYS * 86400


def one(c):
    m = meta.get(c); b = last_book.get(c)
    if not m or not b: return None
    h = get(f"https://clob.polymarket.com/prices-history?market={m['tok'][0]}&startTs={t0}&endTs={now}&fidelity=60")["history"]
    rows, cur = [], None
    for _ in range(5):
        d = get(f"https://data-api.polymarket.com/v2/trades?condition={c}&limit=1000" + (f"&cursor={cur}" if cur else ""))
        rows += d["data"]; cur = d["pagination"].get("next_cursor")
        if not cur or rows[-1]["timestamp"] < t0: break
    tr = sorted((x["timestamp"], (x["side"] == "BUY") == (x["outcome_index"] == 0),
                 x["price"] if x["outcome_index"] == 0 else 1 - x["price"], x["size"]) for x in rows if x["timestamp"] >= t0)
    if len(h) < 2: return None
    size, k = b["n"], b["k"]; yes = no = cash = 0.0; nf = 0; j = 0; vol = 0.0
    start = max(t0, h[0]["t"])
    for i in range(len(h) - 1):
        fair = h[i]["p"]; bid = math.floor(round((fair - .01) / k, 6)) * k; ask = math.ceil(round((fair + .01) / k, 6)) * k
        net = yes - no; rb = size if (bid > 0.005 and net < 2 * size) else 0; ra = size if (ask < 0.995 and net > -2 * size) else 0
        while j < len(tr) and tr[j][0] < h[i]["t"]: j += 1
        while j < len(tr) and tr[j][0] < h[i + 1]["t"]:
            t, buy, p, z = tr[j]; j += 1; vol += z
            if buy and ra and p >= ask - 1e-9:
                q = min(ra, z); ra -= q; nf += 1
                if yes >= q: yes -= q; cash += ask * q
                else: no += q; cash -= (1 - ask) * q
            elif not buy and rb and p <= bid + 1e-9:
                q = min(rb, z); rb -= q; nf += 1
                if no >= q: no -= q; cash += (1 - bid) * q
                else: yes += q; cash -= bid * q
        kk = min(yes, no); yes -= kk; no -= kk; cash += kk
    mark = h[-1]["p"]; pnl = cash + yes * mark + no * (1 - mark); days = max((h[-1]["t"] - start) / 86400, 0.04)
    return dict(c=c, q=m["q"][:55], days=days, fills=nf, pnl_day=pnl / days, rate=b["r"], size=size, trades=len(tr),
                inv=yes - no, move=h[-1]["p"] - h[0]["p"])


with cf.ThreadPoolExecutor(4) as ex: R = [r for r in ex.map(one, list(watch)) if r]
R.sort(key=lambda r: r["pnl_day"])
print(f"{len(R)} markets, last {DAYS} d (or since listing), quote = hourly price +/- 1c, min size, filled first")
for r in R:
    print(f"  {r['q']:55s} days {r['days']:4.1f} trades {r['trades']:4d} fills {r['fills']:3d} "
          f"fillPnL/day {r['pnl_day']:+7.2f}  pool/day {r['rate']:5.0f}  move {r['move']:+.2f} inv {r['inv']:+.0f}")
tot = sum(r["pnl_day"] for r in R)
print(f"TOTAL fill PnL/day across all {len(R)} markets (one min-size quote each): {tot:+.2f}; "
      f"median per market {sorted(r['pnl_day'] for r in R)[len(R)//2]:+.2f}; markets losing > $5/day: {sum(r['pnl_day'] < -5 for r in R)}")
