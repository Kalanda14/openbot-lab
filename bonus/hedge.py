"""Free-bet / qualifying-bet hedge on Polymarket using LIVE Crocobet odds + LIVE Polymarket CLOB books.

Hedge = buy NO on the backed outcome at the NO ask (= 1 - YES best bid), with the Polymarket sports taker fee
fee/share = 0.05 * p * (1-p) (docs.polymarket.com fees page), and the Georgian 5% tax on the amount withdrawn
from the bookmaker. Ramp cost (GEL -> USDC -> GEL) RAMP applied to money that passes through Polymarket.

  Free bet, stake not returned (SNR), size F, odds o:
     N = 0.95*F*(o-1) NO shares ; locked = 0.95*F*(o-1) - N*(a+fee) - ramp   (same in both outcomes)
  Qualifying bet (cash) stake S, odds o:
     N = 0.95*S*o ; result = 0.95*S*o - S - N*(a+fee) (if win) == -S + N*(1-a-fee) (if lose)
Usage: python3 hedge.py   (reads ../geobet/data/pm_catalog.json, live books, live Crocobet)
"""
import json, os, sys, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geobet"))
import snap
TAX, RAMP, FEE_RATE = 0.05, 0.01, 0.05

pm = snap.pm_events()
soft = [s for s in snap.croco() if s["start"] > snap.NOW and s["sport"] == "Soccer"]
pairs = snap.match(pm, soft)
toks = [q["tok"] for _, (sc, p, f, d) in pairs for q in p["sels"] if q["kind"] == "1x2"]
books = snap.pm_books(toks)
rows = []
for s, (sc, p, flip, dtm) in pairs:
    if ("1x2", None) not in s["mk"]:
        continue
    home_pm = p["b"] if flip else p["a"]
    x = [q for q in p["sels"] if q["kind"] == "1x2"]
    draw = [q for q in x if q["lab"] == "X"]; teams = [q for q in x if q["lab"] != "X"]
    if len(draw) != 1 or len(teams) != 2:
        continue
    bh = max(teams, key=lambda q: snap.tok_sim(q["lab"], home_pm)); ba = [q for q in teams if q is not bh][0]
    for k, q in (("1", bh), ("X", draw[0]), ("2", ba)):
        b = books.get(q["tok"])
        if not b or b["bid"] is None or b["ask"] is None or b["bidsz"] < 50:
            continue
        o = s["mk"][("1x2", None)][k]
        a = 1 - b["bid"]                      # NO ask
        fee = FEE_RATE * a * (1 - a)
        F = 100.0
        N = (1 - TAX) * F * (o - 1)
        free = N - N * (a + fee) - RAMP * N * (a + fee)          # locked, = outcome-lose branch
        S = 100.0; Nq = (1 - TAX) * S * o
        qual = -S + Nq * (1 - a - fee) - RAMP * Nq * (a + fee)
        rows.append({"event": f'{s["home"]} - {s["away"]}', "league": s["league"], "start": s["start"].isoformat()[:16],
                     "sel": k, "odds": o, "pm_yes_bid": b["bid"], "pm_yes_ask": b["ask"], "no_ask": round(a, 3),
                     "depth_sh": b["bidsz"], "freebet_lock_pct": round(free, 1), "qual_loss_pct": round(qual, 1)})
rows.sort(key=lambda r: -r["freebet_lock_pct"])
ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%MZ")
os.makedirs("results", exist_ok=True)
json.dump(rows, open(f"results/hedge_{ts}.json", "w"), indent=1)
print("matched soccer events", len(pairs), "rows", len(rows))
print("top free-bet conversions (per 100 GEL SNR free bet):")
for r in rows[:12]:
    print(r)
qs = sorted(r["qual_loss_pct"] for r in rows)
fs = sorted(r["freebet_lock_pct"] for r in rows)
if rows:
    print("free-bet lock %: median", fs[len(fs)//2], "best", fs[-1], "| qualifying-bet result %: median", qs[len(qs)//2], "best", qs[-1])
