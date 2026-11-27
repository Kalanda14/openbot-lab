"""30-day bankroll Monte Carlo for value betting at a Georgian book.
EUR400 start, fractional Kelly on edge estimate shrunk 50%, 5% Georgian withdrawal tax applied at the end
(tax is on the amount withdrawn, so we report balance after withdrawing everything).
Scenarios are explicit; the 'measured' one uses the snapshot result (no bets pass the filter)."""
import numpy as np

rng = np.random.default_rng(7)
N = 20000
DAYS = 30


def run(bets_per_day, raw_edge, odds, true_edge, kelly, tax=0.05):
    bank = np.full(N, 400.0)
    nbets = rng.poisson(bets_per_day * DAYS, N)
    est = raw_edge * 0.5                      # shrink snapshot edge 50%
    f = kelly * est / (odds - 1) if est > 0 else 0.0
    p = (1 + true_edge) / odds               # real win prob
    for i in range(nbets.max()):
        act = nbets > i
        stake = bank * f
        win = rng.random(N) < p
        bank = np.where(act, bank + np.where(win, stake * (odds - 1), -stake), bank)
    out = bank * (1 - tax)
    return (np.mean(out >= 700), np.mean(out < 100), np.median(out), np.percentile(out, 5), np.percentile(out, 95))


SC = [
    # name, bets/day, raw edge seen, odds, TRUE edge
    ("MEASURED: 0 clean bets/day > 2%", 0.0, 0.00, 2.0, 0.00),
    ("Generous: 2/day, seen +4%, true +2%", 2, 0.04, 2.0, 0.02),
    ("Generous: 2/day, seen +4%, true 0% (noise)", 2, 0.04, 2.0, 0.00),
    ("Optimistic: 5/day, seen +6%, true +3%", 5, 0.06, 2.2, 0.03),
    ("Realistic if gaps are noise: 5/day, seen +6%, true -3%", 5, 0.06, 2.2, -0.03),
    ("Dream: 10/day, seen +10%, true +5%", 10, 0.10, 2.5, 0.05),
]
print("| scenario | Kelly | P(>= EUR700 after tax) | P(< EUR100) | median | 5%..95% |")
print("|---|---|---|---|---|---|")
for name, b, re_, o, te in SC:
    for k in (0.25, 0.5):
        a, bb, med, lo, hi = run(b, re_, o, te, k)
        print(f"| {name} | {k} | {a:.1%} | {bb:.1%} | EUR{med:.0f} | {lo:.0f}..{hi:.0f} |")
