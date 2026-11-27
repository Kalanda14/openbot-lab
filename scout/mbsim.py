"""Monte Carlo for month-1 P(+EUR300) / P(lose >EUR300) from EUR400.
A) Spain matched betting over the 2026-11-25 apuestas-deportivas.es welcome list (values = my estimates, see REPORT.md).
B) Value betting soft books (flat edge per bet, quarter/full Kelly).
All inputs are assumptions; edit and rerun. Seeded."""
import numpy as np
rng = np.random.default_rng(7); N = 100_000
# (name, max bonus EUR usable with EUR400 capital, kind, extra cost as share of bonus)
# kind: fb = free bet after qualifying bet (keep ~70-78% via lay, minus qualifying loss)
#       ref = free bet only if first bet loses (matched EV ~ 55-65% of bonus)
#       roll = deposit bonus w/ rollover <=10x, cost = rollover x ~3.5% qual loss
OFF = [("Retabet", 200, "fb", .05), ("VERSUS", 200, "fb", .05), ("WilliamHill", 150, "fb", .06), ("Betfair sb", 200, "fb", .12),
       ("MARCA", 200, "fb", .12), ("bet365", 200, "fb", .05), ("Kirolbet", 100, "fb", .03), ("Paf", 70, "fb", .05),
       ("Winamax", 150, "ref", 0), ("Bwin", 100, "ref", 0), ("Betway", 200, "ref", 0), ("OlyBet", 100, "ref", 0),
       ("Interwetten", 50, "ref", .10), ("888", 110, "ref", .21), ("LeoVegas boosts", 40, "boost", 0),
       ("Sportium", 200, "roll", .05), ("Betsson", 220, "roll", .35), ("GoldenPark", 100, "roll", .35)]
def offer_ev(kind, b, cost, n):
    if kind == "fb":   v = b * rng.uniform(.68, .78, n) - b * cost
    elif kind == "ref": v = b * rng.uniform(.50, .65, n) - b * cost
    elif kind == "boost": v = b * rng.uniform(.4, .6, n)
    else:              v = b * rng.uniform(.85, .95, n) - b * cost
    return v
def spain(p_avail=.75, p_conf=.06, p_err=.03, max_offers=10):
    tot = np.zeros(N); done = np.zeros(N)
    order = sorted(OFF, key=lambda o: -o[1])  # biggest first
    for name, b, kind, cost in order:
        go = (rng.random(N) < p_avail) & (done < max_offers)
        v = offer_ev(kind, b, cost, N)
        conf = rng.random(N) < p_conf                 # bonus/winnings confiscated: lose bonus + qualifying loss
        err = rng.random(N) < p_err                   # execution error: lose up to half the stake
        v = np.where(conf, -0.05 * b, v) - np.where(err, rng.uniform(0, .5, N) * b, 0)
        tot += np.where(go, v, 0); done += go
    return tot
for lbl, kw in [("base: 75% offers usable, 10 offers max in 30d", {}),
                ("pessimistic: 50% usable, 6 offers, 10% confiscation, 5% errors", dict(p_avail=.5, max_offers=6, p_conf=.10, p_err=.05)),
                ("optimistic: 90% usable, 14 offers", dict(p_avail=.9, max_offers=14))]:
    t = spain(**kw)
    print(f"A Spain MB {lbl}: mean {t.mean():.0f} | P(>=300) {np.mean(t>=300):.2f} | P(loss>300) {np.mean(t<-300):.3f} | p5 {np.percentile(t,5):.0f}")
# B value betting
def vb(edge, odds, nbets, kfrac, bank=400.):
    p = (1 + edge) / odds; f = kfrac * edge / (odds - 1); w = np.full(N, bank)
    for _ in range(nbets): w *= 1 + f * np.where(rng.random(N) < p, odds - 1, -1)
    return w - bank
for e, n in [(.03, 300), (.05, 300), (.03, 1000)]:
    for k in (.25, 1.0):
        t = vb(e, 2.5, n, k)
        print(f"B value bet edge {e:.0%} odds 2.5 bets {n} kelly x{k}: mean {t.mean():.0f} | P(>=300) {np.mean(t>=300):.3f} | P(loss>300) {np.mean(t<-300):.3f}")
# capital-capped: with EUR400 split bookie/exchange, lay liability limits usable bonus to ~EUR150 per offer, one at a time
OFF[:] = [(n, min(b, 150), k, c) for n, b, k, c in OFF]
for lbl, kw in [("capped150 base", {}), ("capped150 pessimistic", dict(p_avail=.5, max_offers=6, p_conf=.10, p_err=.05)),
                ("capped150 very pessimistic: 40% usable, 5 offers, 15% confisc", dict(p_avail=.4, max_offers=5, p_conf=.15, p_err=.05))]:
    t = spain(**kw)
    print(f"A Spain MB {lbl}: mean {t.mean():.0f} | P(>=300) {np.mean(t>=300):.2f} | P(loss>300) {np.mean(t<-300):.3f} | p5 {np.percentile(t,5):.0f}")
